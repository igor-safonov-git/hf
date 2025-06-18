import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from openai import AsyncOpenAI
import aiofiles
from hr_analytics_prompt import get_unified_prompt
from huntflow_local_client import HuntflowLocalClient
from chart_data_processor import process_chart_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Validate critical environment variables
def validate_environment():
    """Validate that required environment variables are present"""
    missing_vars = []
    
    if not os.getenv("DEEPSEEK_API_KEY"):
        missing_vars.append("DEEPSEEK_API_KEY")
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
        logger.warning("Application will run with limited functionality")
    else:
        logger.info("All required environment variables are present")

validate_environment()

# Initialize FastAPI app
app = FastAPI(title="Huntflow Analytics Bot")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DeepSeek client
deepseek_client = AsyncOpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY", ""), 
    base_url="https://api.deepseek.com"
)

# Initialize local Huntflow client
hf_client = HuntflowLocalClient()

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    model: Optional[str] = "deepseek"
    temperature: Optional[float] = 0.1
    messages: Optional[List[Dict[str, str]]] = []


class ChatResponse(BaseModel):
    response: str
    thread_id: str


def validate_json_response(response_content: str) -> tuple[bool, str]:
    """Basic JSON validation"""
    try:
        # Extract JSON from markdown if present
        json_content = response_content
        json_match = response_content.find('```json')
        if json_match != -1:
            end_match = response_content.find('```', json_match + 7)
            if end_match != -1:
                json_content = response_content[json_match + 7:end_match].strip()
        
        # Try to parse JSON
        json.loads(json_content)
        return True, "Valid JSON"
        
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {str(e)}"


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint with DeepSeek that generates JSON reports"""
    try:
        # Check if DeepSeek API key is available
        if not deepseek_client.api_key:
            raise HTTPException(
                status_code=503,
                detail="DeepSeek API key not configured"
            )
        
        # Build context from local cache
        huntflow_context = {
            "vacancy_statuses": await hf_client.get_vacancy_statuses(),
            "sources": (await hf_client._req("GET", f"/v2/accounts/{hf_client.account_id}/applicants/sources")).get("items", []),
            "divisions": (await hf_client._req("GET", f"/v2/accounts/{hf_client.account_id}/divisions")).get("items", []),
            "coworkers": (await hf_client._req("GET", f"/v2/accounts/{hf_client.account_id}/coworkers")).get("items", []),
            "rejection_reasons": (await hf_client._req("GET", f"/v2/accounts/{hf_client.account_id}/rejection_reasons")).get("items", []),
            "organizations": [],  # We can get this from accounts table if needed
            "tags": [],  # Not commonly used
            "additional_fields": [],  # Not commonly used  
            "dictionaries": [],  # Not commonly used
            "open_vacancies": [],  # We can filter vacancies if needed
            "recently_closed_vacancies": []  # We can filter vacancies if needed
        }
        
        # Build messages with system prompt for local cache
        system_prompt = get_unified_prompt(huntflow_context=huntflow_context, account_id=hf_client.account_id, use_local_cache=True)
        
        # Save system prompt to file for debugging (async)
        if os.getenv("DEBUG_MODE"):
            try:
                prompt_file_path = os.path.join(os.getcwd(), "current_system_prompt.txt")
                logger.debug(f"Saving system prompt to: {prompt_file_path}")
                
                content = (
                    "=== SYSTEM PROMPT ===\n"
                    f"Generated at: {datetime.now().isoformat()}\n"
                    f"User message: {request.message}\n"
                    f"Working directory: {os.getcwd()}\n"
                    + "="*50 + "\n\n"
                    + system_prompt
                    + "\n\n" + "="*50 + "\n"
                    + "Additional system message: Return only valid JSON. No markdown formatting or explanations.\n"
                )
                
                async with aiofiles.open(prompt_file_path, "w", encoding="utf-8") as f:
                    await f.write(content)
                
                logger.info(f"System prompt saved successfully to {prompt_file_path}")
            except Exception as e:
                logger.error(f"Error saving system prompt: {e}")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": "Return only valid JSON. No markdown formatting or explanations."}
        ]
        
        # Add conversation history if provided
        if request.messages:
            messages.extend(request.messages)
        
        # Add current user message
        messages.append({"role": "user", "content": request.message})
        
        # Call DeepSeek API
        response = await deepseek_client.chat.completions.create(
            messages=messages,
            model="deepseek-chat",
            temperature=request.temperature,
            response_format={'type': 'json_object'},
            max_tokens=4000
        )
        
        ai_response = response.choices[0].message.content
        
        # Basic JSON validation
        is_valid, validation_msg = validate_json_response(ai_response)
        
        if not is_valid:
            raise HTTPException(
                status_code=502,
                detail=f"Invalid JSON response from AI: {validation_msg}"
            )
        
        # Parse and enrich JSON response with real data
        try:
            response_data = json.loads(ai_response)
            
            # If it's a report with a chart, enrich with real data
            if response_data.get("chart") or response_data.get("main_metric"):
                response_data = await process_chart_data(response_data, hf_client)
                ai_response = json.dumps(response_data, ensure_ascii=False, indent=2)
        
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing failed: {e}")
            # Continue with original response if parsing fails
        except Exception as e:
            logger.warning(f"Real data enrichment failed: {e}")
            # Continue with original response if enrichment fails
        
        return ChatResponse(
            response=ai_response,
            thread_id=request.thread_id or f"chat_{int(asyncio.get_event_loop().time())}"
        )
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


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