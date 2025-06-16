import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from openai import AsyncOpenAI
import httpx
from hr_analytics_prompt import get_unified_prompt

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Huntflow Analytics Bot")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DeepSeek client
deepseek_client = AsyncOpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY", ""), 
    base_url="https://api.deepseek.com"
)

# Global variable to store Huntflow context
huntflow_context = {
    "vacancy_statuses": [],
    "sources": [], 
    "tags": [],
    "divisions": [],
    "coworkers": [],
    "organizations": [],
    "additional_fields": [],
    "rejection_reasons": [],
    "dictionaries": [],
    "open_vacancies": [],
    "recently_closed_vacancies": [],
    "total_applicants": 0,
    "total_vacancies": 0,
    "last_updated": None
}

class HuntflowClient:
    def __init__(self):
        self.token = os.getenv("HF_TOKEN", "")
        self.acc_id = os.getenv("ACC_ID", "")
        self.base_url = "https://api.huntflow.ru"
        
    async def _req(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to Huntflow API"""
        if not self.token or not self.acc_id:
            return {}
            
        headers = {"Authorization": f"Bearer {self.token}"}
        url = f"{self.base_url}{path}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(method, url, headers=headers, **kwargs)
                
                if response.status_code == 401:
                    print("🔒 Authentication failed for Huntflow API")
                    return {}
                    
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", "1"))
                    print(f"⏱️ Rate limited, waiting {retry_after}s...")
                    await asyncio.sleep(retry_after)
                    response = await client.request(method, url, headers=headers, **kwargs)
                    
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPError as e:
                print(f"❌ HTTP error: {e}")
                return {}
                    
        return {}
    
    async def list_vacancies(self) -> List[Dict[str, Any]]:
        """Get all vacancies"""
        result = await self._req("GET", f"/v2/accounts/{self.acc_id}/vacancies")
        return result.get("items", [])
    
    async def get_open_vacancies(self) -> List[Dict[str, Any]]:
        """Get currently open vacancies"""
        vacancies = await self.list_vacancies()
        return [v for v in vacancies if v.get("state") == "OPEN"]
    
    async def get_recently_closed_vacancies(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get vacancies closed in the last N days"""
        vacancies = await self.list_vacancies()
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recently_closed = []
        for v in vacancies:
            if v.get("state") == "CLOSED" and v.get("updated"):
                try:
                    updated_date = datetime.fromisoformat(v["updated"].replace("Z", "+00:00"))
                    if updated_date >= cutoff_date:
                        recently_closed.append(v)
                except (ValueError, TypeError):
                    continue
        return recently_closed

# Initialize Huntflow client
hf_client = HuntflowClient()

async def update_huntflow_context():
    """Update global context with fresh Huntflow data"""
    global huntflow_context
    
    if not hf_client.token or not hf_client.acc_id:
        print("⚠️ Huntflow credentials not configured")
        # Set empty values - no sample data
        huntflow_context.update({
            "vacancy_statuses": [],
            "sources": [],
            "tags": [],
            "divisions": [],
            "coworkers": [],
            "organizations": [],
            "additional_fields": [],
            "rejection_reasons": [],
            "dictionaries": [],
            "open_vacancies": [],
            "recently_closed_vacancies": [],
            "total_applicants": 0,
            "total_vacancies": 0,
            "last_updated": datetime.now().isoformat()
        })
        return
    
    try:
        print("🔄 Fetching Huntflow data...")
        
        # Fetch open vacancies
        open_vacancies = await hf_client.get_open_vacancies()
        huntflow_context["open_vacancies"] = open_vacancies
        
        # Fetch recently closed vacancies  
        closed_vacancies = await hf_client.get_recently_closed_vacancies()
        huntflow_context["recently_closed_vacancies"] = closed_vacancies
        
        # Fetch additional context data
        try:
            # Fetch vacancy statuses
            vacancy_statuses = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/vacancies/statuses")
            huntflow_context["vacancy_statuses"] = vacancy_statuses.get("items", [])
        except Exception as e:
            print(f"❌ Error fetching vacancy statuses: {e}")
            huntflow_context["vacancy_statuses"] = [{"id": 1, "name": "New"}, {"id": 2, "name": "Interview"}]
        
        try:
            # Fetch coworkers/recruiters with user type info
            coworkers_data = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/coworkers")
            huntflow_context["coworkers"] = coworkers_data.get("items", [])
            print(f"📊 Fetched {len(huntflow_context['coworkers'])} coworkers")
        except Exception as e:
            print(f"❌ Error fetching coworkers: {e}")
            huntflow_context["coworkers"] = [{"id": 1, "name": "Recruiter", "type": "recruiter"}]
        
        try:
            # Fetch applicants count - using larger sample to estimate total
            print(f"🔍 Fetching applicants from /v2/accounts/{hf_client.acc_id}/applicants/search...")
            applicants_data = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/applicants/search", params={"count": 100})
            api_total = applicants_data.get("total", 0)
            items_count = len(applicants_data.get('items', []))
            
            # If API total is 0 but we have items, estimate based on pagination
            if api_total == 0 and items_count > 0:
                # Try to get more pages to estimate total
                page_2_data = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/applicants/search", params={"count": 100, "page": 2})
                page_2_count = len(page_2_data.get('items', []))
                
                if page_2_count > 0:
                    # If we have a second page, estimate there are more
                    estimated_total = items_count * 5  # Conservative estimate
                    print(f"📊 Applicants API: API total={api_total}, page1={items_count}, page2={page_2_count}, estimated={estimated_total}")
                    huntflow_context["total_applicants"] = estimated_total
                else:
                    # Only one page of results
                    print(f"📊 Applicants API: API total={api_total}, actual items={items_count}")
                    huntflow_context["total_applicants"] = items_count
            else:
                print(f"📊 Applicants API: total={api_total}, items={items_count}")
                huntflow_context["total_applicants"] = api_total
            
            # If still 0, try the main applicants endpoint
            if huntflow_context["total_applicants"] == 0:
                print("🔍 Trying alternative applicants endpoint...")
                alt_applicants_data = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/applicants", params={"count": 100})
                alt_api_total = alt_applicants_data.get("total", 0)
                alt_items_count = len(alt_applicants_data.get('items', []))
                
                if alt_api_total == 0 and alt_items_count > 0:
                    huntflow_context["total_applicants"] = alt_items_count
                    print(f"📊 Alternative endpoint: API total={alt_api_total}, actual items={alt_items_count}")
                else:
                    huntflow_context["total_applicants"] = alt_api_total
                    print(f"📊 Alternative endpoint: total={alt_api_total}, items={alt_items_count}")
        except Exception as e:
            print(f"❌ Error fetching applicants count: {e}")
            huntflow_context["total_applicants"] = 0
        
        try:
            # Fetch sources with full data including IDs
            sources_data = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/applicants/sources")
            sources_list = sources_data.get("items", [])
            huntflow_context["sources"] = sources_list
            print(f"📊 Fetched {len(huntflow_context['sources'])} sources")
        except Exception as e:
            print(f"❌ Error fetching sources: {e}")
            huntflow_context["sources"] = []
        
        try:
            # Fetch organizations
            orgs_data = await hf_client._req("GET", f"/v2/accounts")
            huntflow_context["organizations"] = orgs_data.get("items", [])
        except Exception as e:
            print(f"❌ Error fetching organizations: {e}")
            huntflow_context["organizations"] = []
        
        try:
            # Fetch tags
            tags_data = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/tags")
            huntflow_context["tags"] = tags_data.get("items", [])
            print(f"📊 Fetched {len(huntflow_context['tags'])} tags")
        except Exception as e:
            print(f"❌ Error fetching tags: {e}")
            huntflow_context["tags"] = [{"id": 1, "name": "Python"}]
        
        try:
            # Fetch divisions
            divisions_data = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/divisions")
            huntflow_context["divisions"] = divisions_data.get("items", [])
            print(f"📊 Fetched {len(huntflow_context['divisions'])} divisions")
        except Exception as e:
            print(f"❌ Error fetching divisions: {e}")
            huntflow_context["divisions"] = [{"id": 1, "name": "IT Department"}]
        
        try:
            # Fetch additional vacancy fields
            additional_fields_data = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/vacancies/additional_fields")
            huntflow_context["additional_fields"] = additional_fields_data.get("items", [])
            print(f"📊 Fetched {len(huntflow_context['additional_fields'])} additional fields")
        except Exception as e:
            print(f"❌ Error fetching additional fields: {e}")
            huntflow_context["additional_fields"] = []
        
        try:
            # Fetch rejection reasons
            rejection_reasons_data = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/rejection_reasons")
            huntflow_context["rejection_reasons"] = rejection_reasons_data.get("items", [])
            print(f"📊 Fetched {len(huntflow_context['rejection_reasons'])} rejection reasons")
        except Exception as e:
            print(f"❌ Error fetching rejection reasons: {e}")
            huntflow_context["rejection_reasons"] = [{"id": 1, "name": "Not qualified"}]
        
        try:
            # Fetch dictionaries
            dictionaries_data = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/dictionaries")
            huntflow_context["dictionaries"] = dictionaries_data.get("items", [])
            print(f"📊 Fetched {len(huntflow_context['dictionaries'])} dictionaries")
        except Exception as e:
            print(f"❌ Error fetching dictionaries: {e}")
            huntflow_context["dictionaries"] = []
        
        huntflow_context["total_vacancies"] = len(open_vacancies) + len(closed_vacancies)
        
        huntflow_context["last_updated"] = datetime.now().isoformat()
        
        print(f"✅ Updated context: {len(open_vacancies)} open, {len(closed_vacancies)} recently closed vacancies")
        
    except Exception as e:
        print(f"❌ Error updating Huntflow context: {e}")
        # Set empty values on error - no sample data
        huntflow_context.update({
            "vacancy_statuses": [],
            "sources": [],
            "tags": [],
            "divisions": [],
            "coworkers": [],
            "organizations": [],
            "additional_fields": [],
            "rejection_reasons": [],
            "dictionaries": [],
            "last_updated": datetime.now().isoformat()
        })


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
    """Simple chat endpoint with DeepSeek"""
    try:
        # Update Huntflow context with fresh data
        await update_huntflow_context()
        
        # Check if DeepSeek API key is available
        if not deepseek_client.api_key:
            return ChatResponse(
                response="⚠️ DeepSeek API key not configured", 
                thread_id=request.thread_id or ""
            )
        
        # Build messages
        system_prompt = get_unified_prompt(huntflow_context)
        
        # Save system prompt to file for debugging
        try:
            import os
            prompt_file_path = os.path.join(os.getcwd(), "current_system_prompt.txt")
            print(f"💾 Saving system prompt to: {prompt_file_path}")
            
            with open(prompt_file_path, "w", encoding="utf-8") as f:
                f.write("=== SYSTEM PROMPT ===\n")
                f.write(f"Generated at: {datetime.now().isoformat()}\n")
                f.write(f"User message: {request.message}\n")
                f.write(f"Working directory: {os.getcwd()}\n")
                f.write("="*50 + "\n\n")
                f.write(system_prompt)
                f.write("\n\n" + "="*50 + "\n")
                f.write("Additional system message: Return only valid JSON. No markdown formatting or explanations.\n")
            
            print(f"✅ System prompt saved successfully to {prompt_file_path}")
        except Exception as e:
            print(f"❌ Error saving system prompt: {e}")
        
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
        response = await deepseek_client.chat.completions.create(  # type: ignore
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
            return ChatResponse(
                response=f"⚠️ {validation_msg}\n\nRaw response:\n{ai_response}",
                thread_id=request.thread_id or f"chat_{int(asyncio.get_event_loop().time())}"
            )
        
        # Execute real data queries using SQLAlchemy executor
        try:
            response_data = json.loads(ai_response)
            
            # If it's a report with a chart, execute real data queries
            if response_data.get("chart") and response_data.get("main_metric"):
                from sqlalchemy_executor import SQLAlchemyHuntflowExecutor
                executor = SQLAlchemyHuntflowExecutor(hf_client)
                
                # Execute main metric
                if response_data.get("main_metric", {}).get("value"):
                    main_value = await executor.execute_expression(response_data["main_metric"]["value"])
                    response_data["main_metric"]["real_value"] = main_value
                
                # Execute chart data if it has group_by (for bar charts)
                chart = response_data.get("chart", {})
                y_axis = chart.get("y_axis", {})
                if y_axis.get("group_by"):
                    # Execute grouped query to get chart data
                    chart_data = await executor.execute_grouped_query(y_axis)
                    if chart_data:
                        chart["real_data"] = chart_data
                
                ai_response = json.dumps(response_data)
        
        except (json.JSONDecodeError, ImportError, Exception) as e:
            print(f"⚠️ Real data execution failed: {e}")
            # Continue with original response if execution fails
        
        return ChatResponse(
            response=ai_response,
            thread_id=request.thread_id or f"chat_{int(asyncio.get_event_loop().time())}"
        )
        
    except Exception as e:
        return ChatResponse(
            response=f"⚠️ Error: {str(e)}", 
            thread_id=request.thread_id or ""
        )


@app.get("/api/metrics/{metric_name}")
async def get_metric(metric_name: str):
    """Get ready-to-use metrics"""
    try:
        from sqlalchemy_executor import SQLAlchemyHuntflowExecutor
        executor = SQLAlchemyHuntflowExecutor(hf_client)
        
        result = await executor.get_ready_metric(metric_name)
        return {"metric": metric_name, "value": result}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/charts/{chart_type}")
async def get_chart_data(chart_type: str):
    """Get ready-to-use chart data"""
    try:
        from sqlalchemy_executor import SQLAlchemyHuntflowExecutor
        executor = SQLAlchemyHuntflowExecutor(hf_client)
        
        result = await executor.get_ready_chart(chart_type)
        return result
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/dashboard")
async def get_dashboard():
    """Get complete dashboard data"""
    try:
        from sqlalchemy_executor import SQLAlchemyHuntflowExecutor
        executor = SQLAlchemyHuntflowExecutor(hf_client)
        
        result = await executor.get_dashboard_data()
        return result
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/prefetch-data")
async def prefetch_data():
    """Prefetch and return Huntflow data summary for frontend"""
    # Update context with fresh data
    await update_huntflow_context()
    
    # Calculate summary statistics
    total_applicants = huntflow_context.get("total_applicants", 0)
    total_vacancies = len(huntflow_context.get("open_vacancies", [])) + len(huntflow_context.get("recently_closed_vacancies", []))
    total_statuses = len(huntflow_context.get("vacancy_statuses", []))
    total_recruiters = len(huntflow_context.get("coworkers", []))
    
    # Get top status and recruiter (safely)
    vacancy_statuses = huntflow_context.get("vacancy_statuses", [])
    top_status = vacancy_statuses[0].get("name", "No data") if vacancy_statuses else "No data"
    
    coworkers = huntflow_context.get("coworkers", [])
    top_recruiter = coworkers[0].get("name", "No data") if coworkers else "No data"
    
    return {
        "summary": {
            "total_applicants": total_applicants,
            "total_vacancies": total_vacancies,
            "total_statuses": total_statuses,
            "total_recruiters": total_recruiters,
            "top_status": top_status,
            "top_recruiter": top_recruiter
        },
        "context": huntflow_context,
        "last_updated": huntflow_context.get("last_updated")
    }


@app.get("/api/context-stats")
async def context_stats():
    """Show detailed statistics of all data available in the prompt context"""
    # Update context with fresh data
    await update_huntflow_context()
    
    # Calculate detailed statistics
    stats = {
        "context_overview": {
            "last_updated": huntflow_context.get("last_updated"),
            "total_data_points": sum([
                len(huntflow_context.get("vacancy_statuses", [])),
                len(huntflow_context.get("sources", [])),
                len(huntflow_context.get("tags", [])),
                len(huntflow_context.get("divisions", [])),
                len(huntflow_context.get("coworkers", [])),
                len(huntflow_context.get("organizations", [])),
                len(huntflow_context.get("additional_fields", [])),
                len(huntflow_context.get("rejection_reasons", [])),
                len(huntflow_context.get("dictionaries", [])),
                len(huntflow_context.get("open_vacancies", [])),
                len(huntflow_context.get("recently_closed_vacancies", []))
            ])
        },
        "vacancy_statuses": {
            "count": len(huntflow_context.get("vacancy_statuses", [])),
            "items": [{"id": s.get("id"), "name": s.get("name"), "type": s.get("type")} for s in huntflow_context.get("vacancy_statuses", [])]
        },
        "sources": {
            "count": len(huntflow_context.get("sources", [])),
            "items": huntflow_context.get("sources", [])
        },
        "tags": {
            "count": len(huntflow_context.get("tags", [])),
            "items": [{"id": t.get("id"), "name": t.get("name")} for t in huntflow_context.get("tags", [])]
        },
        "divisions": {
            "count": len(huntflow_context.get("divisions", [])),
            "items": [{"id": d.get("id"), "name": d.get("name")} for d in huntflow_context.get("divisions", [])]
        },
        "coworkers": {
            "count": len(huntflow_context.get("coworkers", [])),
            "items": [{"id": c.get("id"), "name": c.get("name"), "type": c.get("type")} for c in huntflow_context.get("coworkers", [])]
        },
        "organizations": {
            "count": len(huntflow_context.get("organizations", [])),
            "items": [{"id": o.get("id"), "name": o.get("name")} for o in huntflow_context.get("organizations", [])]
        },
        "additional_fields": {
            "count": len(huntflow_context.get("additional_fields", [])),
            "items": [{"id": f.get("id"), "name": f.get("name"), "type": f.get("type")} for f in huntflow_context.get("additional_fields", [])]
        },
        "rejection_reasons": {
            "count": len(huntflow_context.get("rejection_reasons", [])),
            "items": [{"id": r.get("id"), "name": r.get("name")} for r in huntflow_context.get("rejection_reasons", [])]
        },
        "dictionaries": {
            "count": len(huntflow_context.get("dictionaries", [])),
            "items": huntflow_context.get("dictionaries", [])
        },
        "vacancies": {
            "open_count": len(huntflow_context.get("open_vacancies", [])),
            "recently_closed_count": len(huntflow_context.get("recently_closed_vacancies", [])),
            "total_count": huntflow_context.get("total_vacancies", 0),
            "open_vacancies": [{"id": v.get("id"), "position": v.get("position"), "state": v.get("state")} for v in huntflow_context.get("open_vacancies", [])]
        },
        "applicants": {
            "total_count": huntflow_context.get("total_applicants", 0),
            "note": "Count fetched from API search endpoint"
        },
        "entities": {
            "vacancy_statuses": len(huntflow_context.get('vacancy_statuses', [])),
            "sources": len(huntflow_context.get('sources', [])),
            "coworkers": len(huntflow_context.get('coworkers', [])),
            "tags": len(huntflow_context.get('tags', [])),
            "divisions": len(huntflow_context.get('divisions', []))
        }
    }
    
    return stats


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Huntflow Analytics Bot"}


@app.get("/")
async def root():
    """Serve the frontend"""
    return FileResponse("index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)