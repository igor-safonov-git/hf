import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from openai import AsyncOpenAI
from huntflow_local_client import HuntflowLocalClient
from hr_analytics_prompt import get_unified_prompt
from chart_data_processor import process_chart_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Validate required environment variables
required_vars = ["OPENAI_API_KEY"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Initialize clients
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
hf_client = HuntflowLocalClient()

# FastAPI app setup
app = FastAPI(title="Huntflow Analytics Bot (Local Cache)")

# Enable CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Check if the service is running and local database is accessible."""
    try:
        # Test database connection
        statuses = await hf_client.get_vacancy_statuses()
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "data_source": "local_cache",
            "vacancy_statuses_count": len(statuses)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

# Request/Response models
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    timestamp: str

# Main chat endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process user message and return AI response using local cache data."""
    try:
        logger.info(f"Received chat request: {request.message}")
        
        # Define tools for OpenAI
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "hf_fetch",
                    "description": "Fetch data from local Huntflow cache. Supports the same endpoints as the API but queries local SQLite database instead.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "endpoint": {
                                "type": "string",
                                "description": "API endpoint path (e.g., '/v2/accounts/{account_id}/vacancies')"
                            },
                            "method": {
                                "type": "string",
                                "enum": ["GET"],
                                "description": "HTTP method (only GET supported for local cache)"
                            },
                            "params": {
                                "type": "object",
                                "description": "Query parameters"
                            }
                        },
                        "required": ["endpoint", "method"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "make_chart",
                    "description": "Create a bar chart visualization",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "data": {
                                "type": "object",
                                "description": "Dictionary with labels as keys and values as numbers"
                            },
                            "title": {
                                "type": "string",
                                "description": "Chart title"
                            },
                            "xlabel": {
                                "type": "string",
                                "description": "X-axis label"
                            },
                            "ylabel": {
                                "type": "string",
                                "description": "Y-axis label"
                            }
                        },
                        "required": ["data", "title"]
                    }
                }
            }
        ]
        
        # Prepare messages with system prompt
        messages = [
            {
                "role": "system",
                "content": get_unified_prompt(account_id=hf_client.account_id, use_local_cache=True)
            },
            {
                "role": "user",
                "content": request.message
            }
        ]
        
        # Call OpenAI with tools
        response = await openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.7,
            max_tokens=4000
        )
        
        assistant_message = response.choices[0].message
        
        # Handle tool calls if any
        if assistant_message.tool_calls:
            messages.append(assistant_message)
            
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                logger.info(f"Executing tool: {function_name} with args: {function_args}")
                
                try:
                    if function_name == "hf_fetch":
                        # Use local client to fetch data
                        result = await hf_client._req(
                            method=function_args.get("method", "GET"),
                            endpoint=function_args["endpoint"],
                            params=function_args.get("params", {})
                        )
                        tool_result = json.dumps(result)
                    
                    elif function_name == "make_chart":
                        # Import here to avoid loading matplotlib unless needed
                        from chart_generator import make_chart as generate_chart
                        chart_data_uri = await asyncio.to_thread(
                            generate_chart,
                            data=function_args["data"],
                            title=function_args["title"],
                            xlabel=function_args.get("xlabel", ""),
                            ylabel=function_args.get("ylabel", "Count")
                        )
                        tool_result = json.dumps({"chart": chart_data_uri})
                    
                    else:
                        tool_result = json.dumps({"error": f"Unknown function: {function_name}"})
                
                except Exception as e:
                    logger.error(f"Tool execution error: {e}")
                    tool_result = json.dumps({"error": str(e)})
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })
            
            # Get final response after tool execution
            final_response = await openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                temperature=0.7,
                max_tokens=4000
            )
            
            final_content = final_response.choices[0].message.content
        else:
            final_content = assistant_message.content
        
        # Process chart data if the response is a JSON report
        try:
            if final_content and final_content.strip().startswith("{"):
                report_json = json.loads(final_content)
                if "chart" in report_json:
                    # Process the chart data with real values
                    report_json = await process_chart_data(report_json, hf_client)
                    final_content = json.dumps(report_json, ensure_ascii=False, indent=2)
        except json.JSONDecodeError:
            # Not JSON, return as is
            pass
        
        return ChatResponse(
            response=final_content,
            timestamp=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Serve the frontend
@app.get("/")
async def read_index():
    """Serve the main HTML file."""
    return FileResponse("index.html")

# Prefetch data endpoint
@app.get("/api/prefetch-data")
async def prefetch_data():
    """Prefetch common data for the frontend."""
    try:
        statuses = await hf_client.get_vacancy_statuses()
        vacancies = await hf_client._req("GET", f"/v2/accounts/{hf_client.account_id}/vacancies")
        
        # Get some sample data for summary
        coworkers = await hf_client._req("GET", f"/v2/accounts/{hf_client.account_id}/coworkers")
        coworker_items = coworkers.get("items", [])
        
        # Pick a sample recruiter and status
        top_recruiter = coworker_items[0].get("name", "Unknown") if coworker_items else "No recruiters"
        top_status = statuses[0].get("name", "Unknown") if statuses else "No statuses"
        
        return {
            "status": "success",
            "summary": {
                "total_applicants": await hf_client.get_applicants_count(),
                "total_vacancies": len(vacancies.get("items", [])),
                "total_statuses": len(statuses),
                "total_recruiters": len(coworker_items),
                "top_status": top_status,
                "top_recruiter": top_recruiter
            },
            "context": {
                "vacancy_statuses": statuses[:10],  # First 10 statuses
                "organizations": [],
                "tags": [],
                "sources": []
            }
        }
    except Exception as e:
        logger.error(f"Prefetch error: {e}")
        return {"status": "error", "message": str(e)}

# Database info endpoint
@app.get("/db-info")
async def database_info():
    """Get information about the cached data."""
    try:
        # Get counts from various tables
        info = {
            "data_source": "local_sqlite_cache",
            "database_path": hf_client.db_path,
            "account_id": hf_client.account_id,
            "stats": {
                "vacancies": len((await hf_client._req("GET", f"/v2/accounts/{hf_client.account_id}/vacancies")).get("items", [])),
                "applicants": await hf_client.get_applicants_count(),
                "vacancy_statuses": len(await hf_client.get_vacancy_statuses()),
            },
            "status_distribution": await hf_client.get_status_distribution()
        }
        return info
    except Exception as e:
        logger.error(f"Database info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Huntflow Analytics Bot with LOCAL CACHE...")
    logger.info(f"Using database: {hf_client.db_path}")
    logger.info(f"Account ID: {hf_client.account_id}")
    uvicorn.run(app, host="0.0.0.0", port=8001)