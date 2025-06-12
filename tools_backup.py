# BACKUP OF CURRENT WORKING TOOLS
# These tools are working correctly with OpenAI function calling

import os
import json
import base64
import asyncio
from io import BytesIO
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

import httpx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


class HuntflowClient:
    def __init__(self):
        self.token = os.getenv("HF_TOKEN", "")
        self.acc_id = os.getenv("ACC_ID", "")
        self.base_url = "https://api.huntflow.ru"
        self.token_expires = datetime.now()
        
    async def _req(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with auto retry on 401/429"""
        headers = {"Authorization": f"Bearer {self.token}"}
        url = f"{self.base_url}{path}"
        
        async with httpx.AsyncClient() as client:
            for attempt in range(3):
                try:
                    response = await client.request(method, url, headers=headers, **kwargs)
                    
                    if response.status_code == 401 and attempt < 2:
                        # Token expired, refresh and retry
                        await self._refresh_token()
                        headers["Authorization"] = f"Bearer {self.token}"
                        continue
                        
                    if response.status_code == 429 and attempt < 2:
                        # Rate limited, wait and retry
                        retry_after = int(response.headers.get("Retry-After", "1"))
                        await asyncio.sleep(retry_after)
                        continue
                        
                    response.raise_for_status()
                    return response.json()
                    
                except httpx.HTTPError as e:
                    if attempt == 2:
                        raise HTTPException(status_code=500, detail=str(e))
                    
        return {}
    
    async def _refresh_token(self):
        """Placeholder for token refresh - in real app would call auth endpoint"""
        # In production, this would call the actual refresh endpoint
        # For now, just use the existing token
        pass
    
    async def list_statuses(self) -> List[Dict[str, Any]]:
        """Get vacancy statuses"""
        if not self.token or not self.acc_id:
            return []
        result = await self._req("GET", f"/v2/accounts/{self.acc_id}/vacancy_statuses")
        return result.get("items", result if isinstance(result, list) else [])
    
    async def list_vacancies(self, status_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get vacancies, optionally filtered by status"""
        if not self.token or not self.acc_id:
            return []
        params = {}
        if status_id:
            params["status"] = status_id
        result = await self._req("GET", f"/v2/accounts/{self.acc_id}/vacancies", params=params)
        return result.get("items", [])
    
    async def search_applicants(self, vacancy_id: Optional[int] = None, status: Optional[int] = None, 
                               limit: int = 30, **kwargs) -> List[Dict[str, Any]]:
        """Search applicants with filters (REAL Huntflow endpoint)"""
        if not self.token or not self.acc_id:
            return []
        params = {"limit": min(limit, 100)}  # Huntflow limit
        if vacancy_id:
            params["vacancy"] = vacancy_id
        if status:
            params["status"] = status
        params.update(kwargs)
        result = await self._req("GET", f"/v2/accounts/{self.acc_id}/applicants/search", params=params)
        return result.get("items", [])
    
    async def get_applicant_logs(self, applicant_id: int) -> List[Dict[str, Any]]:
        """Get applicant status change logs (REAL Huntflow endpoint)"""
        if not self.token or not self.acc_id:
            return []
        result = await self._req("GET", f"/v2/accounts/{self.acc_id}/applicants/{applicant_id}/logs")
        return result.get("items", [])
    
    async def get_vacancy_statuses(self) -> List[Dict[str, Any]]:
        """Get vacancy statuses (REAL Huntflow endpoint)"""
        if not self.token or not self.acc_id:
            return []
        result = await self._req("GET", f"/v2/accounts/{self.acc_id}/vacancies/statuses")
        return result.get("items", [])
    
    async def get_status_groups(self) -> List[Dict[str, Any]]:
        """Get vacancy status groups (REAL Huntflow endpoint)"""
        if not self.token or not self.acc_id:
            return []
        result = await self._req("GET", f"/v2/accounts/{self.acc_id}/vacancies/status_groups")
        return result.get("items", [])
    
    async def search_applicants_by_cursor(self, cursor: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Search applicants with cursor pagination (REAL Huntflow endpoint)"""
        if not self.token or not self.acc_id:
            return {}
        params = {}
        if cursor:
            params["cursor"] = cursor
        params.update(kwargs)
        result = await self._req("GET", f"/v2/accounts/{self.acc_id}/applicants/search_by_cursor", params=params)
        return result


def make_chart(stage_counts: Dict[str, int]) -> str:
    """Create bar chart from stage counts and return markdown image"""
    # Sort stages by count
    sorted_stages = sorted(stage_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Handle case with many stages
    if len(sorted_stages) > 7:
        top_6 = sorted_stages[:6]
        other_count = sum(count for _, count in sorted_stages[6:])
        stages = [name for name, _ in top_6] + ["Other"]
        counts = [count for _, count in top_6] + [other_count]
    else:
        stages = [name for name, _ in sorted_stages]
        counts = [count for _, count in sorted_stages]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(stages, counts)
    
    # Styling
    ax.set_xlabel('Stage', fontsize=12)
    ax.set_ylabel('Count', fontsize=12)
    ax.set_title('Candidates by Stage', fontsize=14, fontweight='bold')
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom')
    
    # Rotate x labels if needed
    if len(stages) > 5:
        plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    
    # Convert to base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=100)
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close(fig)
    
    # Return just the data URI - model will format as markdown
    return f"data:image/png;base64,{image_base64}"


async def execute_function(name: str, arguments: Dict[str, Any]) -> Any:
    """Execute a function call"""
    print(f"🔧 Executing function: {name} with args: {arguments}")
    
    # Initialize HuntflowClient (you'll need to pass this in properly)
    hf_client = HuntflowClient()
    
    try:
        if name == "hf_fetch":
            path = arguments.get("path", "")
            params = arguments.get("params", {})
            
            # Replace {acc_id} in path
            if "{acc_id}" in path and hf_client.acc_id:
                path = path.replace("{acc_id}", hf_client.acc_id)
            
            result = await hf_client._req("GET", path, params=params)
            return result
        
        elif name == "hf_search_applicants":
            vacancy_id = arguments.get("vacancy_id")
            status = arguments.get("status")
            limit = arguments.get("limit", 30)
            return await hf_client.search_applicants(vacancy_id=vacancy_id, status=status, limit=limit)
            
        elif name == "hf_get_applicant_logs":
            applicant_id = arguments.get("applicant_id")
            if not applicant_id:
                return {"error": "applicant_id is required"}
            return await hf_client.get_applicant_logs(applicant_id)
            
        elif name == "hf_get_vacancy_statuses":
            return await hf_client.get_vacancy_statuses()
            
        elif name == "hf_get_status_groups":
            return await hf_client.get_status_groups()
        
        elif name == "make_chart":
            stage_counts = arguments.get("stage_counts", {})
            print(f"📊 Creating chart with data: {stage_counts}")
            result = make_chart(stage_counts)
            print(f"📊 Chart created, length: {len(result)} chars")
            return result
        
        else:
            raise ValueError(f"Unknown function: {name}")
            
    except Exception as e:
        # Return detailed error for debugging
        error_msg = f"{type(e).__name__}: {str(e)}"
        if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
            error_msg += f" (HTTP {e.response.status_code})"
        return {"error": error_msg, "path": arguments.get("path", ""), "params": arguments.get("params", {})}


# Tool definitions for OpenAI function calling
HUNTFLOW_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "hf_fetch",
            "description": f"Fetch data from Huntflow API - use this to get real hiring data",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": f"API path to fetch. Examples: /v2/accounts/{{acc_id}}/vacancies or /v2/accounts/{{acc_id}}/vacancy_statuses"
                    },
                    "params": {
                        "type": "object",
                        "description": "Query parameters as key-value pairs",
                        "properties": {},
                        "additionalProperties": True
                    }
                },
                "required": ["path"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hf_search_applicants",
            "description": "Search applicants with filters - REAL Huntflow endpoint for funnel analysis",
            "parameters": {
                "type": "object",
                "properties": {
                    "vacancy_id": {
                        "type": "integer",
                        "description": "Filter applicants by specific vacancy ID (optional)"
                    },
                    "status": {
                        "type": "integer",
                        "description": "Filter by specific status ID (optional)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max number of applicants to return (default: 30, max: 100)",
                        "minimum": 1,
                        "maximum": 100
                    }
                },
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hf_get_applicant_logs",
            "description": "Get status change history for a specific applicant",
            "parameters": {
                "type": "object",
                "properties": {
                    "applicant_id": {
                        "type": "integer",
                        "description": "The ID of the applicant to get logs for"
                    }
                },
                "required": ["applicant_id"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hf_get_vacancy_statuses",
            "description": "Get all hiring stages/statuses for funnel mapping",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hf_get_status_groups",
            "description": "Get vacancy status groups - REAL Huntflow endpoint for broader recruitment phases",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "make_chart",
            "description": "Create a bar chart from hiring stage counts - use this after getting data",
            "parameters": {
                "type": "object",
                "properties": {
                    "stage_counts": {
                        "type": "object",
                        "description": "Dictionary mapping stage names to candidate counts",
                        "properties": {},
                        "additionalProperties": {"type": "integer"}
                    }
                },
                "required": ["stage_counts"],
                "additionalProperties": False
            }
        }
    }
]