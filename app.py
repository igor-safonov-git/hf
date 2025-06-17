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
import httpx
import aiofiles
from hr_analytics_prompt import get_unified_prompt

# Custom exceptions for better error handling
class HuntflowAPIError(Exception):
    """Base exception for Huntflow API related errors"""
    pass

class HuntflowAuthenticationError(HuntflowAPIError):
    """Raised when authentication fails"""
    pass

class HuntflowRateLimitError(HuntflowAPIError):
    """Raised when rate limit is exceeded"""
    pass

class HuntflowConnectionError(HuntflowAPIError):
    """Raised when connection to Huntflow API fails"""
    pass

class HuntflowDataError(HuntflowAPIError):
    """Raised when API returns malformed data"""
    pass

class HuntflowConfigurationError(Exception):
    """Raised when configuration is invalid or missing"""
    pass

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
    if not os.getenv("HF_TOKEN"):
        missing_vars.append("HF_TOKEN") 
    if not os.getenv("ACC_ID"):
        missing_vars.append("ACC_ID")
    
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
    allow_origins=["http://localhost:8000", "http://localhost:8001", "http://127.0.0.1:8000", "http://127.0.0.1:8001"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Initialize DeepSeek client
deepseek_client = AsyncOpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY", ""), 
    base_url="https://api.deepseek.com"
)

# Context manager for Huntflow data
class HuntflowContextManager:
    def __init__(self):
        self._context = {
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
        self._cache_expiry = None
        self._cache_ttl = 300  # 5 minutes
    
    def is_cache_valid(self) -> bool:
        """Check if cached data is still valid"""
        if self._cache_expiry is None:
            return False
        return datetime.now() < self._cache_expiry
    
    def get_context(self) -> Dict[str, Any]:
        """Get the current context"""
        return self._context.copy()
    
    def update_context(self, new_context: Dict[str, Any]):
        """Update the context and refresh cache expiry"""
        self._context.update(new_context)
        self._cache_expiry = datetime.now() + timedelta(seconds=self._cache_ttl)

# Global context manager instance
context_manager = HuntflowContextManager()

class HuntflowClient:
    def __init__(self):
        self.token = os.getenv("HF_TOKEN", "")
        self.acc_id = os.getenv("ACC_ID", "")
        self.base_url = "https://api.huntflow.ru"
        
    async def _req(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to Huntflow API"""
        if not self.token or not self.acc_id:
            raise HuntflowConfigurationError("Huntflow token or account ID not configured")
            
        headers = {"Authorization": f"Bearer {self.token}"}
        url = f"{self.base_url}{path}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(method, url, headers=headers, **kwargs)
                
                if response.status_code == 401:
                    logger.error("Authentication failed for Huntflow API")
                    raise HuntflowAuthenticationError("Authentication failed for Huntflow API")
                    
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", "1"))
                    logger.warning(f"Rate limited, waiting {retry_after}s...")
                    await asyncio.sleep(retry_after)
                    # Retry once
                    response = await client.request(method, url, headers=headers, **kwargs)
                    if response.status_code == 429:
                        raise HuntflowRateLimitError(f"Rate limit exceeded, retry after {retry_after}s")
                    
                response.raise_for_status()
                
                try:
                    return response.json()
                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"Invalid JSON response from {url}: {e}")
                    raise HuntflowDataError(f"Invalid JSON response from API: {e}")
                
            except httpx.ConnectError as e:
                logger.error(f"Connection error to {url}: {e}")
                raise HuntflowConnectionError(f"Failed to connect to Huntflow API: {e}")
            except httpx.TimeoutException as e:
                logger.error(f"Timeout error for {url}: {e}")
                raise HuntflowConnectionError(f"Timeout connecting to Huntflow API: {e}")
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP status error {e.response.status_code} for {url}: {e}")
                raise HuntflowAPIError(f"HTTP {e.response.status_code} error: {e}")
            except httpx.RequestError as e:
                logger.error(f"Request error for {url}: {e}")
                raise HuntflowConnectionError(f"Request failed: {e}")
    
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
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse date for vacancy {v.get('id')}: {e}")
                    continue
        return recently_closed

# Initialize Huntflow client
hf_client = HuntflowClient()

async def update_huntflow_context():
    """Update context with fresh Huntflow data"""
    
    # Check configuration first
    try:
        # This will raise HuntflowConfigurationError if credentials are missing
        await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/vacancies", params={"count": 1})
    except HuntflowConfigurationError:
        logger.warning("Huntflow credentials not configured")
        # Set empty values - no sample data
        context_manager.update_context({
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
    except (HuntflowAuthenticationError, HuntflowConnectionError) as e:
        logger.error(f"Cannot connect to Huntflow API: {e}")
        # Set empty context with error indicator
        context_manager.update_context({
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
            "last_updated": datetime.now().isoformat(),
            "error": str(e)
        })
        return
    
    try:
        logger.info("Fetching Huntflow data...")
        
        # Get current context
        current_context = context_manager.get_context()
        
        # Fetch vacancies concurrently
        vacancy_tasks = await asyncio.gather(
            hf_client.get_open_vacancies(),
            hf_client.get_recently_closed_vacancies(),
            return_exceptions=True
        )
        
        open_vacancies = vacancy_tasks[0] if not isinstance(vacancy_tasks[0], Exception) else []
        closed_vacancies = vacancy_tasks[1] if not isinstance(vacancy_tasks[1], Exception) else []
        
        current_context["open_vacancies"] = open_vacancies
        current_context["recently_closed_vacancies"] = closed_vacancies
        
        # Define concurrent API fetch tasks
        async def fetch_vacancy_statuses():
            try:
                result = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/vacancies/statuses")
                items = result.get("items", [])
                if not isinstance(items, list):
                    raise HuntflowDataError("vacancy_statuses response is not a list")
                return items
            except HuntflowAPIError:
                # Re-raise Huntflow API errors
                raise
            except (KeyError, TypeError) as e:
                logger.error(f"Data format error fetching vacancy statuses: {e}")
                raise HuntflowDataError(f"Invalid vacancy statuses data format: {e}")
        
        async def fetch_coworkers():
            try:
                result = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/coworkers")
                items = result.get("items", [])
                if not isinstance(items, list):
                    raise HuntflowDataError("coworkers response is not a list")
                logger.info(f"Fetched {len(items)} coworkers")
                return items
            except HuntflowAPIError:
                # Re-raise Huntflow API errors
                raise
            except (KeyError, TypeError) as e:
                logger.error(f"Data format error fetching coworkers: {e}")
                raise HuntflowDataError(f"Invalid coworkers data format: {e}")
        
        async def fetch_applicants_count():
            try:
                logger.info(f"Fetching applicants from /v2/accounts/{hf_client.acc_id}/applicants/search...")
                applicants_data = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/applicants/search", params={"count": 100})
                
                if not isinstance(applicants_data, dict):
                    raise HuntflowDataError("applicants response is not a dict")
                
                api_total = applicants_data.get("total", 0)
                items = applicants_data.get('items', [])
                
                if not isinstance(items, list):
                    raise HuntflowDataError("applicants items is not a list")
                
                items_count = len(items)
                
                # If API total is 0 but we have items, estimate based on pagination
                if api_total == 0 and items_count > 0:
                    # Try to get more pages to estimate total
                    page_2_data = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/applicants/search", params={"count": 100, "page": 2})
                    page_2_items = page_2_data.get('items', [])
                    
                    if not isinstance(page_2_items, list):
                        raise HuntflowDataError("applicants page 2 items is not a list")
                    
                    page_2_count = len(page_2_items)
                    
                    if page_2_count > 0:
                        # If we have a second page, estimate there are more
                        estimated_total = items_count * 5  # Conservative estimate
                        logger.debug(f"Applicants API: API total={api_total}, page1={items_count}, page2={page_2_count}, estimated={estimated_total}")
                        return estimated_total
                    else:
                        # Only one page of results
                        logger.debug(f"Applicants API: API total={api_total}, actual items={items_count}")
                        return items_count
                else:
                    logger.info(f"Applicants API: total={api_total}, items={items_count}")
                    return api_total
                    
            except HuntflowAPIError:
                # Re-raise Huntflow API errors
                raise
            except (KeyError, TypeError, ValueError) as e:
                logger.error(f"Data processing error fetching applicants count: {e}")
                raise HuntflowDataError(f"Invalid applicants data format: {e}")
        
        async def fetch_sources():
            try:
                result = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/applicants/sources")
                sources_list = result.get("items", [])
                if not isinstance(sources_list, list):
                    raise HuntflowDataError("sources response is not a list")
                logger.info(f"Fetched {len(sources_list)} sources")
                return sources_list
            except HuntflowAPIError:
                raise
            except (KeyError, TypeError) as e:
                logger.error(f"Data format error fetching sources: {e}")
                raise HuntflowDataError(f"Invalid sources data format: {e}")
        
        async def fetch_organizations():
            try:
                result = await hf_client._req("GET", f"/v2/accounts")
                items = result.get("items", [])
                if not isinstance(items, list):
                    raise HuntflowDataError("organizations response is not a list")
                return items
            except HuntflowAPIError:
                raise
            except (KeyError, TypeError) as e:
                logger.error(f"Data format error fetching organizations: {e}")
                raise HuntflowDataError(f"Invalid organizations data format: {e}")
        
        async def fetch_tags():
            try:
                result = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/tags")
                items = result.get("items", [])
                if not isinstance(items, list):
                    raise HuntflowDataError("tags response is not a list")
                logger.info(f"Fetched {len(items)} tags")
                return items
            except HuntflowAPIError:
                raise
            except (KeyError, TypeError) as e:
                logger.error(f"Data format error fetching tags: {e}")
                raise HuntflowDataError(f"Invalid tags data format: {e}")
        
        async def fetch_divisions():
            try:
                result = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/divisions")
                items = result.get("items", [])
                if not isinstance(items, list):
                    raise HuntflowDataError("divisions response is not a list")
                logger.info(f"Fetched {len(items)} divisions")
                return items
            except HuntflowAPIError:
                raise
            except (KeyError, TypeError) as e:
                logger.error(f"Data format error fetching divisions: {e}")
                raise HuntflowDataError(f"Invalid divisions data format: {e}")
        
        async def fetch_additional_fields():
            try:
                result = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/vacancies/additional_fields")
                items = result.get("items", [])
                if not isinstance(items, list):
                    raise HuntflowDataError("additional_fields response is not a list")
                logger.info(f"Fetched {len(items)} additional fields")
                return items
            except HuntflowAPIError:
                raise
            except (KeyError, TypeError) as e:
                logger.error(f"Data format error fetching additional fields: {e}")
                raise HuntflowDataError(f"Invalid additional fields data format: {e}")
        
        async def fetch_rejection_reasons():
            try:
                result = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/rejection_reasons")
                items = result.get("items", [])
                if not isinstance(items, list):
                    raise HuntflowDataError("rejection_reasons response is not a list")
                logger.info(f"Fetched {len(items)} rejection reasons")
                return items
            except HuntflowAPIError:
                raise
            except (KeyError, TypeError) as e:
                logger.error(f"Data format error fetching rejection reasons: {e}")
                raise HuntflowDataError(f"Invalid rejection reasons data format: {e}")
        
        async def fetch_dictionaries():
            try:
                result = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/dictionaries")
                items = result.get("items", [])
                if not isinstance(items, list):
                    raise HuntflowDataError("dictionaries response is not a list")
                logger.info(f"Fetched {len(items)} dictionaries")
                return items
            except HuntflowAPIError:
                raise
            except (KeyError, TypeError) as e:
                logger.error(f"Data format error fetching dictionaries: {e}")
                raise HuntflowDataError(f"Invalid dictionaries data format: {e}")
        
        # Execute all API calls concurrently
        api_results = await asyncio.gather(
            fetch_vacancy_statuses(),
            fetch_coworkers(),
            fetch_applicants_count(),
            fetch_sources(),
            fetch_organizations(),
            fetch_tags(),
            fetch_divisions(),
            fetch_additional_fields(),
            fetch_rejection_reasons(),
            fetch_dictionaries(),
            return_exceptions=True
        )
        
        # Assign results to context, logging any exceptions
        def safe_assign(result, default_value, field_name):
            if isinstance(result, Exception):
                logger.warning(f"API call failed for {field_name}: {result}")
                return default_value
            return result
        
        current_context["vacancy_statuses"] = safe_assign(api_results[0], [], "vacancy_statuses")
        current_context["coworkers"] = safe_assign(api_results[1], [], "coworkers")
        current_context["total_applicants"] = safe_assign(api_results[2], 0, "total_applicants")
        current_context["sources"] = safe_assign(api_results[3], [], "sources")
        current_context["organizations"] = safe_assign(api_results[4], [], "organizations")
        current_context["tags"] = safe_assign(api_results[5], [], "tags")
        current_context["divisions"] = safe_assign(api_results[6], [], "divisions")
        current_context["additional_fields"] = safe_assign(api_results[7], [], "additional_fields")
        current_context["rejection_reasons"] = safe_assign(api_results[8], [], "rejection_reasons")
        current_context["dictionaries"] = safe_assign(api_results[9], [], "dictionaries")
        
        current_context["total_vacancies"] = len(open_vacancies) + len(closed_vacancies)
        
        current_context["last_updated"] = datetime.now().isoformat()
        
        # Update the context manager with all changes
        context_manager.update_context(current_context)
        
        logger.info(f"Updated context: {len(open_vacancies)} open, {len(closed_vacancies)} recently closed vacancies")
        
    except (HuntflowAPIError, HuntflowConnectionError, HuntflowDataError) as e:
        logger.error(f"Huntflow API error updating context: {e}")
        # Set empty values on API error - no sample data
        context_manager.update_context({
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
            "last_updated": datetime.now().isoformat(),
            "error": str(e)
        })
    except Exception as e:
        logger.error(f"Unexpected error updating Huntflow context: {e}")
        # Set empty values on unexpected error
        context_manager.update_context({
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
            "last_updated": datetime.now().isoformat(),
            "error": f"Unexpected error: {str(e)}"
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
        # Update Huntflow context with fresh data if cache is invalid
        if not context_manager.is_cache_valid():
            await update_huntflow_context()
        
        # Check if DeepSeek API key is available
        if not deepseek_client.api_key:
            raise HTTPException(
                status_code=503,
                detail="DeepSeek API key not configured"
            )
        
        # Build messages
        system_prompt = get_unified_prompt(context_manager.get_context())
        
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
            raise HTTPException(
                status_code=502,
                detail=f"Invalid JSON response from AI: {validation_msg}"
            )
        
        # Execute real data queries using SQLAlchemy executor
        try:
            response_data = json.loads(ai_response)
            
            # If it's a report with a chart, execute real data queries
            if response_data.get("chart") and response_data.get("main_metric"):
                from sqlalchemy_executor import SQLAlchemyHuntflowExecutor
                from virtual_engine import HuntflowVirtualEngine
                engine = HuntflowVirtualEngine(hf_client)
                executor = SQLAlchemyHuntflowExecutor(engine)
                
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
        
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing failed: {e}")
            # Continue with original response if execution fails
        except ImportError as e:
            logger.warning(f"Module import failed: {e}")
            # Continue with original response if execution fails
        except Exception as e:
            logger.warning(f"Real data execution failed: {e}")
            # Continue with original response if execution fails
        
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


@app.get("/api/metrics/{metric_name}")
async def get_metric(metric_name: str):
    """Get ready-to-use metrics"""
    try:
        from sqlalchemy_executor import SQLAlchemyHuntflowExecutor
        from virtual_engine import HuntflowVirtualEngine
        engine = HuntflowVirtualEngine(hf_client)
        executor = SQLAlchemyHuntflowExecutor(engine)
        
        result = await executor.get_ready_metric(metric_name)
        return {"metric": metric_name, "value": result}
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Module import error: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting metric {metric_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metric: {str(e)}")


@app.get("/api/charts/{chart_type}")
async def get_chart_data(chart_type: str):
    """Get ready-to-use chart data"""
    try:
        from sqlalchemy_executor import SQLAlchemyHuntflowExecutor
        from virtual_engine import HuntflowVirtualEngine
        engine = HuntflowVirtualEngine(hf_client)
        executor = SQLAlchemyHuntflowExecutor(engine)
        
        result = await executor.get_ready_chart(chart_type)
        return result
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Module import error: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting chart {chart_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get chart: {str(e)}")


@app.get("/api/advanced-metrics/{metric_name}")
async def get_advanced_metric(metric_name: str, start_date: Optional[str] = None, end_date: Optional[str] = None, 
                            days_back: Optional[int] = None, months_back: Optional[int] = None):
    """Get advanced calculated metrics with optional parameters"""
    try:
        from huntflow_metrics import HuntflowComputedMetrics
        from virtual_engine import HuntflowVirtualEngine
        engine = HuntflowVirtualEngine(hf_client)
        metrics = HuntflowComputedMetrics(engine)
        
        # Build kwargs based on provided parameters
        kwargs = {}
        if start_date:
            kwargs['start_date'] = start_date
        if end_date:
            kwargs['end_date'] = end_date
        if days_back:
            kwargs['days_back'] = days_back
        if months_back:
            kwargs['months_back'] = months_back
        
        # Call the appropriate metric method
        if hasattr(metrics, metric_name):
            method = getattr(metrics, metric_name)
            result = await method(**kwargs)
            return {"metric": metric_name, "result": result, "parameters": kwargs}
        else:
            raise HTTPException(status_code=404, detail=f"Unknown metric: {metric_name}")
            
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Module import error: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting advanced metric {metric_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metric: {str(e)}")


@app.get("/api/dashboard")
async def get_dashboard():
    """Get complete dashboard data"""
    try:
        from sqlalchemy_executor import SQLAlchemyHuntflowExecutor
        from virtual_engine import HuntflowVirtualEngine
        engine = HuntflowVirtualEngine(hf_client)
        executor = SQLAlchemyHuntflowExecutor(engine)
        
        result = await executor.get_dashboard_data()
        return result
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Module import error: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard: {str(e)}")


@app.get("/api/prefetch-data")
async def prefetch_data():
    """Prefetch and return Huntflow data summary for frontend"""
    # Update context with fresh data if cache is invalid
    if not context_manager.is_cache_valid():
        await update_huntflow_context()
    
    # Get current context
    current_context = context_manager.get_context()
    
    # Calculate summary statistics
    total_applicants = current_context.get("total_applicants", 0)
    total_vacancies = len(current_context.get("open_vacancies", [])) + len(current_context.get("recently_closed_vacancies", []))
    total_statuses = len(current_context.get("vacancy_statuses", []))
    total_recruiters = len(current_context.get("coworkers", []))
    
    # Get top status and recruiter (safely)
    vacancy_statuses = current_context.get("vacancy_statuses", [])
    top_status = vacancy_statuses[0].get("name", "No data") if vacancy_statuses else "No data"
    
    coworkers = current_context.get("coworkers", [])
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
        "context": current_context,
        "last_updated": current_context.get("last_updated")
    }


@app.get("/api/context-stats")
async def context_stats():
    """Show detailed statistics of all data available in the prompt context"""
    # Update context with fresh data if cache is invalid
    if not context_manager.is_cache_valid():
        await update_huntflow_context()
    
    # Get current context
    current_context = context_manager.get_context()
    
    # Calculate detailed statistics
    stats = {
        "context_overview": {
            "last_updated": current_context.get("last_updated"),
            "total_data_points": sum([
                len(current_context.get("vacancy_statuses", [])),
                len(current_context.get("sources", [])),
                len(current_context.get("tags", [])),
                len(current_context.get("divisions", [])),
                len(current_context.get("coworkers", [])),
                len(current_context.get("organizations", [])),
                len(current_context.get("additional_fields", [])),
                len(current_context.get("rejection_reasons", [])),
                len(current_context.get("dictionaries", [])),
                len(current_context.get("open_vacancies", [])),
                len(current_context.get("recently_closed_vacancies", []))
            ])
        },
        "vacancy_statuses": {
            "count": len(current_context.get("vacancy_statuses", [])),
            "items": [{"id": s.get("id"), "name": s.get("name"), "type": s.get("type")} for s in current_context.get("vacancy_statuses", [])]
        },
        "sources": {
            "count": len(current_context.get("sources", [])),
            "items": current_context.get("sources", [])
        },
        "tags": {
            "count": len(current_context.get("tags", [])),
            "items": [{"id": t.get("id"), "name": t.get("name")} for t in current_context.get("tags", [])]
        },
        "divisions": {
            "count": len(current_context.get("divisions", [])),
            "items": [{"id": d.get("id"), "name": d.get("name")} for d in current_context.get("divisions", [])]
        },
        "coworkers": {
            "count": len(current_context.get("coworkers", [])),
            "items": [{"id": c.get("id"), "name": c.get("name"), "type": c.get("type")} for c in current_context.get("coworkers", [])]
        },
        "organizations": {
            "count": len(current_context.get("organizations", [])),
            "items": [{"id": o.get("id"), "name": o.get("name")} for o in current_context.get("organizations", [])]
        },
        "additional_fields": {
            "count": len(current_context.get("additional_fields", [])),
            "items": [{"id": f.get("id"), "name": f.get("name"), "type": f.get("type")} for f in current_context.get("additional_fields", [])]
        },
        "rejection_reasons": {
            "count": len(current_context.get("rejection_reasons", [])),
            "items": [{"id": r.get("id"), "name": r.get("name")} for r in current_context.get("rejection_reasons", [])]
        },
        "dictionaries": {
            "count": len(current_context.get("dictionaries", [])),
            "items": current_context.get("dictionaries", [])
        },
        "vacancies": {
            "open_count": len(current_context.get("open_vacancies", [])),
            "recently_closed_count": len(current_context.get("recently_closed_vacancies", [])),
            "total_count": current_context.get("total_vacancies", 0),
            "open_vacancies": [{"id": v.get("id"), "position": v.get("position"), "state": v.get("state")} for v in current_context.get("open_vacancies", [])]
        },
        "applicants": {
            "total_count": current_context.get("total_applicants", 0),
            "note": "Count fetched from API search endpoint"
        },
        "entities": {
            "vacancy_statuses": len(current_context.get('vacancy_statuses', [])),
            "sources": len(current_context.get('sources', [])),
            "coworkers": len(current_context.get('coworkers', [])),
            "tags": len(current_context.get('tags', [])),
            "divisions": len(current_context.get('divisions', []))
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
    uvicorn.run(app, host="0.0.0.0", port=8001)