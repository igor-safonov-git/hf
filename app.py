import os
import json
import base64
import asyncio
from io import BytesIO
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

# Load environment variables from .env file
load_dotenv()

import httpx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from openai import AsyncOpenAI
# Removed huntflow_query_executor - using only SQLAlchemy executor
from sqlalchemy_executor import SQLAlchemyHuntflowExecutor, HuntflowAnalyticsTemplates


class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    model: Optional[str] = "deepseek"  # "openai" or "deepseek"
    use_real_data: Optional[bool] = True  # Whether to fetch real Huntflow data
    messages: Optional[List[Dict[str, str]]] = []  # Conversation history
    temperature: Optional[float] = 0.1  # Temperature for AI models


class ChatResponse(BaseModel):
    response: str
    thread_id: str


# Validation models for JSON structure
class ValueExpression(BaseModel):
    operation: str
    entity: Optional[str] = None
    field: Optional[str] = None
    filter: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
    group_by: Optional[Dict[str, str]] = None

class Metric(BaseModel):
    label: str
    value: ValueExpression

class ChartData(BaseModel):
    labels: List[str]
    values: List[Union[int, float]]

class Chart(BaseModel):
    graph_description: str
    chart_type: str
    x_axis_name: str
    y_axis_name: str
    x_axis: ValueExpression
    y_axis: ValueExpression

class AnalyticsReport(BaseModel):
    report_title: str
    main_metric: Metric
    secondary_metrics: List[Metric]
    chart: Chart


def validate_analytics_json(json_data: dict) -> tuple[bool, str, Optional[AnalyticsReport]]:
    """Validate JSON structure and business logic"""
    try:
        # First validate basic structure
        report = AnalyticsReport(**json_data)
        
        # Validate business logic
        validation_errors = []
        
        # Check entities (per huntflow_schema.py virtual tables)
        valid_entities = {"applicants", "recruiters", "vacancies", "status_mapping", "sources", "divisions", "applicant_tags", "offers", "applicant_links"}
        for metric in [report.main_metric] + report.secondary_metrics:
            if metric.value.entity and metric.value.entity not in valid_entities:
                validation_errors.append(f"Invalid entity: {metric.value.entity}")
        
        # Check chart entities
        if report.chart.y_axis.entity and report.chart.y_axis.entity not in valid_entities:
            validation_errors.append(f"Invalid chart entity: {report.chart.y_axis.entity}")
        
        # Check operations
        valid_operations = {"count", "sum", "avg", "max", "min", "field"}
        for metric in [report.main_metric] + report.secondary_metrics:
            if metric.value.operation not in valid_operations:
                validation_errors.append(f"Invalid operation: {metric.value.operation}")
        
        if report.chart.x_axis.operation not in valid_operations:
            validation_errors.append(f"Invalid chart x_axis operation: {report.chart.x_axis.operation}")
        if report.chart.y_axis.operation not in valid_operations:
            validation_errors.append(f"Invalid chart y_axis operation: {report.chart.y_axis.operation}")
        
        # Check chart types
        valid_chart_types = {"bar", "line", "scatter"}
        if report.chart.chart_type not in valid_chart_types:
            validation_errors.append(f"Invalid chart type: {report.chart.chart_type}")
        
        # Check secondary metrics count
        if len(report.secondary_metrics) > 2:
            validation_errors.append("Too many secondary metrics (max 2)")
        
        # Demo data validation removed - no longer using demo data
        
        # Check field operations logic
        for metric in [report.main_metric] + report.secondary_metrics:
            if metric.value.operation in ["sum", "avg"] and not metric.value.field:
                validation_errors.append(f"Operation '{metric.value.operation}' requires a field (e.g., numeric field for calculations)")
        
        if validation_errors:
            return False, "; ".join(validation_errors), None
        
        return True, "Valid", report
        
    except ValidationError as e:
        return False, f"Schema validation error: {str(e)}", None
    except Exception as e:
        return False, f"Validation error: {str(e)}", None


def validate_huntflow_fields(expression: ValueExpression) -> List[str]:
    """Validate field names against Huntflow API structure"""
    errors = []
    
    # Valid fields by entity - based on huntflow_schema.py (CLAUDE.md compliant)
    valid_fields = {
        "applicants": {"id", "first_name", "last_name", "middle_name", "birthday", "phone", "skype", "email", 
                      "money", "position", "company", "photo", "photo_url", "created", "account", "tags", 
                      "external", "agreement", "doubles", "social", "source_id", "recruiter_id", 
                      "recruiter_name", "source_name", "status_id", "status_name", "vacancy_id"},  # Per OpenAPI schema
        "vacancies": {"id", "position", "company", "account_division", "account_region", "money", "priority", 
                     "hidden", "state", "created", "updated", "multiple", "parent", "account_vacancy_status_group",
                     "additional_fields_list", "body", "requirements", "conditions", "files", "coworkers", 
                     "source", "blocks", "vacancy_request"},  # Per OpenAPI VacancyResponse
        "coworkers": {"id", "name", "email", "member", "type", "head", "meta", "permissions", "full_name"},  # Per OpenAPI CoworkerResponse
        "offers": {"id", "offer_id", "applicant_id", "vacancy_frame_id", "status", "created", "updated", 
                  "values", "pdf_url"},
        "tags": {"id", "tag_id", "name", "color", "created", "updated"},
        "sources": {"id", "name", "type", "foreign"},  # Per OpenAPI ApplicantSource
        "statuses": {"id", "name", "type", "order", "stay_duration", "removed"},  # Per OpenAPI VacancyStatus
        "status_groups": {"id", "name", "type", "statuses"},
        "questionary": {"current_salary", "expected_salary", "position", "relocation", "availability"},
        "responses": {"id", "applicant_id", "status", "date_received", "source"},
        "rejections": {"id", "applicant_id", "reason", "reason_id", "created", "updated"},
        "organizations": {"id", "name", "nick", "member_type", "production", "created"},
        "divisions": {"id", "name", "order", "active", "deep", "parent", "foreign", "meta"},  # Per OpenAPI Division
        "webhooks": {"id", "url", "active", "created", "updated"},
        "logs": {"id", "type", "applicant", "vacancy", "status", "rejection_reason", "created", "author"}
    }
    
    if expression.entity and expression.field:
        entity_fields = valid_fields.get(expression.entity, set())
        if expression.field not in entity_fields:
            errors.append(f"Field '{expression.field}' not valid for entity '{expression.entity}'")
    
    # Validate filter fields (support both single filter and array of filters)
    if expression.filter and expression.entity:
        entity_fields = valid_fields.get(expression.entity, set())
        
        # Handle array of filters
        if isinstance(expression.filter, list):
            for i, filter_obj in enumerate(expression.filter):
                if isinstance(filter_obj, dict):
                    filter_field = filter_obj.get("field")
                    if filter_field and filter_field not in entity_fields:
                        errors.append(f"Filter {i+1} field '{filter_field}' not valid for entity '{expression.entity}'")
        # Handle single filter
        elif isinstance(expression.filter, dict):
            filter_field = expression.filter.get("field")
            if filter_field and filter_field not in entity_fields:
                errors.append(f"Filter field '{filter_field}' not valid for entity '{expression.entity}'")
    
    # Validate group_by fields
    if expression.group_by and expression.entity:
        group_field = expression.group_by.get("field")
        if group_field:
            entity_fields = valid_fields.get(expression.entity, set())
            if group_field not in entity_fields:
                errors.append(f"Group by field '{group_field}' not valid for entity '{expression.entity}'")
    
    return errors


async def validate_and_enhance_response(response_content: str, use_real_data: bool = False, hf_client = None) -> str:
    """Validate AI response and optionally fetch real data"""
    try:
        # Extract JSON from markdown if present
        json_content = response_content
        json_match = response_content.find('```json')
        if json_match != -1:
            end_match = response_content.find('```', json_match + 7)
            if end_match != -1:
                json_content = response_content[json_match + 7:end_match].strip()
        
        # Parse and validate JSON
        try:
            json_data = json.loads(json_content)
            
            # REMOVE any demo fields that AI might have included
            if "main_metric" in json_data and "demo_value" in json_data["main_metric"]:
                del json_data["main_metric"]["demo_value"]
            
            if "secondary_metrics" in json_data:
                for metric in json_data["secondary_metrics"]:
                    if "demo_value" in metric:
                        del metric["demo_value"]
            
            if "chart" in json_data and "demo_data" in json_data["chart"]:
                del json_data["chart"]["demo_data"]
                
        except json.JSONDecodeError as e:
            return f"⚠️ Invalid JSON response: {str(e)}\n\nOriginal response:\n{response_content}"
        
        # Validate structure and business logic
        is_valid, error_msg, validated_report = validate_analytics_json(json_data)
        
        if not is_valid:
            return f"⚠️ Validation failed: {error_msg}\n\nOriginal response:\n{response_content}"
        
        # Additional field validation
        field_errors = []
        field_errors.extend(validate_huntflow_fields(validated_report.main_metric.value))
        for metric in validated_report.secondary_metrics:
            field_errors.extend(validate_huntflow_fields(metric.value))
        field_errors.extend(validate_huntflow_fields(validated_report.chart.x_axis))
        field_errors.extend(validate_huntflow_fields(validated_report.chart.y_axis))
        
        if field_errors:
            return f"⚠️ Field validation warnings: {'; '.join(field_errors)}\n\nResponse (proceeding anyway):\n{response_content}"
        
        # Fetch real data if requested and inject into JSON
        if use_real_data and hf_client:
            print(f"🔄 Attempting to fetch real data for report: {validated_report.report_title}")
            real_data = await fetch_real_data_for_report(validated_report, hf_client)
            
            if real_data:
                print(f"✅ Real data fetched successfully: {real_data}")
                # Update JSON with ONLY real data (no demo data)
                json_data["main_metric"]["real_value"] = real_data["main_metric_value"]
                json_data["_data_source"] = "real"
                
                for i, metric_data in enumerate(real_data["secondary_metrics_values"]):
                    if i < len(json_data["secondary_metrics"]):
                        json_data["secondary_metrics"][i]["real_value"] = metric_data["value"]
                
                json_data["chart"]["real_data"] = real_data["chart_data"]
                
                # Return updated JSON
                updated_response = json.dumps(json_data, indent=2, ensure_ascii=False)
                if json_match != -1:
                    return f"```json\n{updated_response}\n```"
                return updated_response
            else:
                print("❌ Real data fetch failed")
                json_data["_data_source"] = "no_data"
        
        # All validations passed - return cleaned JSON
        cleaned_response = json.dumps(json_data, indent=2, ensure_ascii=False)
        if json_match != -1:
            return f"```json\n{cleaned_response}\n```"
        return cleaned_response
        
    except Exception as e:
        return f"⚠️ Validation error: {str(e)}\n\nOriginal response:\n{response_content}"


class HuntflowClient:
    def __init__(self):
        self.token = os.getenv("HF_TOKEN", "")
        self.refresh_token = os.getenv("HF_REFRESH_TOKEN", "")
        self.acc_id = os.getenv("ACC_ID", "")
        self.base_url = "https://api.huntflow.ru"
        self.token_expires = datetime.now()
        
    async def _req(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with automatic token refresh"""
        headers = {"Authorization": f"Bearer {self.token}"}
        url = f"{self.base_url}{path}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(method, url, headers=headers, **kwargs)
                
                if response.status_code == 401:
                    # Token expired - try to refresh
                    print(f"🔄 Token expired, attempting refresh...")
                    refreshed = await self._refresh_token()
                    
                    if refreshed:
                        # Retry with new token
                        headers = {"Authorization": f"Bearer {self.token}"}
                        response = await client.request(method, url, headers=headers, **kwargs)
                        
                        if response.status_code == 401:
                            print(f"🎭 Refresh failed, using demo data from Huntflow")
                            try:
                                return response.json()
                            except:
                                return {}
                    else:
                        # Refresh failed, use demo data from 401 response
                        print(f"🎭 Refresh not available, using demo data from Huntflow")
                        try:
                            return response.json()
                        except:
                            return {}
                        
                if response.status_code == 429:
                    # Rate limited, wait and retry once
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
    
    async def _refresh_token(self):
        """Refresh access token using refresh token"""
        if not self.refresh_token:
            print("❌ No refresh token available")
            return False
            
        try:
            print(f"🔄 Refreshing token using refresh token...")
            async with httpx.AsyncClient() as client:
                # Use the correct Huntflow v2 token refresh endpoint from CLAUDE.md
                endpoint = f"{self.base_url}/token/refresh"
                
                response = await client.post(
                    endpoint,
                    json={
                        "refresh_token": self.refresh_token
                    }
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    new_access_token = token_data.get("access_token")
                    new_refresh_token = token_data.get("refresh_token")
                    
                    print(f"🔍 Token refresh response: {token_data}")
                    
                    if new_access_token:
                        # Update tokens in memory
                        self.token = new_access_token
                        if new_refresh_token:
                            self.refresh_token = new_refresh_token
                        
                        # Calculate expiry time (Huntflow tokens last 7 days)
                        self.token_expires = datetime.now() + timedelta(days=7)
                        
                        print(f"✅ Token refreshed successfully")
                        print(f"📝 New access token: {new_access_token[:20]}...")
                        if new_refresh_token:
                            print(f"📝 New refresh token: {new_refresh_token[:20]}...")
                        
                        # TODO: Optionally persist new tokens to .env file
                        return True
                    else:
                        print(f"❌ No access_token in refresh response")
                        return False
                else:
                    print(f"❌ Token refresh failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"❌ Token refresh error: {e}")
            return False
    
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
        # Add other filter parameters
        params.update(kwargs)
        result = await self._req("GET", f"/v2/accounts/{self.acc_id}/applicants/search", params=params)
        return result.get("items", [])
    
    async def get_applicant_logs(self, applicant_id: int) -> List[Dict[str, Any]]:
        """Get applicant logs/status changes (REAL Huntflow endpoint)"""
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


async def fetch_real_data_for_report(report: AnalyticsReport, hf_client: HuntflowClient) -> Dict[str, Any]:
    """Fetch real data from Huntflow API for the report using SQLAlchemy approach"""
    
    # Try SQLAlchemy executor first for better reliability
    try:
        print(f"🔍 Starting SQLAlchemy data fetch for: {report.report_title}")
        sqlalchemy_executor = SQLAlchemyHuntflowExecutor(hf_client)
        analytics_templates = HuntflowAnalyticsTemplates(sqlalchemy_executor)
        
        # Check if this is a recruiter performance query
        if "recruiter" in report.report_title.lower() or "рекрутер" in report.report_title.lower():
            print("🎯 Detected recruiter performance query, using optimized template")
            recruiter_report = await analytics_templates.recruiter_performance_report()
            
            return {
                "main_metric_value": recruiter_report["hires"],
                "secondary_metrics_values": [{"label": "Average Time to Hire (Days)", "value": recruiter_report["avg_time"]}],
                "chart_data": {
                    "labels": [recruiter_report["top_recruiter"]],
                    "values": [recruiter_report["hires"]]
                }
            }
        
        # For other queries, use the SQLAlchemy executor
        main_metric_expr = report.main_metric.value.model_dump()
        print(f"📊 SQLAlchemy main metric expression: {main_metric_expr}")
        main_value = await sqlalchemy_executor.execute_expression(main_metric_expr)
        print(f"📈 SQLAlchemy main metric result: {main_value}")
        
        # Fetch secondary metrics
        secondary_values = []
        for i, metric in enumerate(report.secondary_metrics):
            metric_expr = metric.value.model_dump()
            print(f"📊 SQLAlchemy secondary metric {i+1} expression: {metric_expr}")
            value = await sqlalchemy_executor.execute_expression(metric_expr)
            print(f"📈 SQLAlchemy secondary metric {i+1} result: {value}")
            secondary_values.append({
                "label": metric.label,
                "value": value
            })
        
        # Fetch chart data
        chart_spec = {
            "x_axis": report.chart.x_axis.model_dump(),
            "y_axis": report.chart.y_axis.model_dump()
        }
        print(f"📊 SQLAlchemy chart specification: {chart_spec}")
        chart_data = await sqlalchemy_executor.execute_chart_data(chart_spec)
        print(f"📈 SQLAlchemy chart data result: {chart_data}")
        
        return {
            "main_metric_value": main_value,
            "secondary_metrics_values": secondary_values,
            "chart_data": chart_data
        }
        
    except Exception as e:
        print(f"⚠️ SQLAlchemy executor failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None


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


# Initialize FastAPI app
app = FastAPI(title="Huntflow Demo Bot")

# Enable CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Fetch Huntflow context data on server startup"""
    await fetch_huntflow_context()

# Initialize clients
hf_client = HuntflowClient()
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
deepseek_client = AsyncOpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY", ""), 
    base_url="https://api.deepseek.com"
)

# Global variable to store fetched Huntflow data
huntflow_context = {
    "vacancy_statuses": [],
    "sources": [], 
    "departments": [],
    "vacancy_names": [],
    "total_applicants": 0,
    "total_vacancies": 0,
    "last_updated": None
}


async def fetch_huntflow_context():
    """Fetch real Huntflow data to inject into system prompts"""
    global huntflow_context
    
    try:
        print("🔄 Fetching Huntflow context data...")
        
        # Fetch vacancy statuses
        try:
            status_result = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/vacancies/statuses")
            if isinstance(status_result, dict):
                huntflow_context["vacancy_statuses"] = [
                    {"id": s.get("id"), "name": s.get("name")} 
                    for s in status_result.get("items", [])
                ]
        except Exception as e:
            print(f"Failed to fetch vacancy statuses: {e}")
        
        # Fetch applicant sources
        try:
            sources_result = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/applicants/sources")
            if isinstance(sources_result, dict):
                huntflow_context["sources"] = [
                    s.get("name") for s in sources_result.get("items", [])
                ][:10]  # Limit to top 10
        except Exception as e:
            print(f"Failed to fetch sources: {e}")
        
        # Get total applicants count
        try:
            applicants_result = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/applicants/search", 
                                                   params={"count": 1})
            if isinstance(applicants_result, dict):
                huntflow_context["total_applicants"] = applicants_result.get("total", 0)
        except Exception as e:
            print(f"Failed to fetch applicant count: {e}")
        
        # Get total vacancies count
        try:
            vacancies_result = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/vacancies", 
                                                  params={"count": 1})
            if isinstance(vacancies_result, dict):
                huntflow_context["total_vacancies"] = len(vacancies_result.get("items", []))
        except Exception as e:
            print(f"Failed to fetch vacancy count: {e}")
        
        # Try to extract departments and vacancy names from recent vacancies
        try:
            recent_vacancies = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/vacancies", 
                                                  params={"count": 50})
            if isinstance(recent_vacancies, dict):
                departments = set()
                vacancy_names = []
                for vacancy in recent_vacancies.get("items", []):
                    if vacancy.get("department"):
                        departments.add(vacancy.get("department"))
                    if vacancy.get("position"):
                        vacancy_names.append(vacancy.get("position"))
                
                huntflow_context["departments"] = list(departments)[:10]
                huntflow_context["vacancy_names"] = vacancy_names[:15]  # Top 15 vacancy names
        except Exception as e:
            print(f"Failed to fetch departments/vacancies: {e}")
        
        huntflow_context["last_updated"] = datetime.now().isoformat()
        print(f"✅ Huntflow context updated: {len(huntflow_context['vacancy_statuses'])} statuses, {len(huntflow_context['sources'])} sources, {huntflow_context['total_applicants']} applicants")
        
    except Exception as e:
        print(f"❌ Failed to fetch Huntflow context: {e}")






def get_unified_prompt():
    """Get unified HR analytics prompt for both OpenAI and DeepSeek"""
    
    # Inject real Huntflow data into prompt
    context_section = ""
    if huntflow_context.get("last_updated"):
        statuses_list = chr(10).join([f"  - {s['name']} (ID: {s['id']})" for s in huntflow_context.get('vacancy_statuses', [])])
        sources_list = chr(10).join([f"  - {source}" for source in huntflow_context.get('sources', [])])
        departments_list = chr(10).join([f"  - {dept}" for dept in huntflow_context.get('departments', [])])
        vacancies_list = chr(10).join([f"  - {pos}" for pos in huntflow_context.get('vacancy_names', [])])
        
        context_section = f"""

⸻

REAL HUNTFLOW ACCOUNT DATA (Use this for accurate responses):

• Total Applicants: {huntflow_context.get('total_applicants', 'Unknown')}
• Total Vacancies: {huntflow_context.get('total_vacancies', 'Unknown')}

• Available Status Names & IDs:
{statuses_list}

• Available Sources:
{sources_list}

• Available Departments:
{departments_list}

• Recent Vacancy Positions:
{vacancies_list}

• Last Updated: {huntflow_context.get('last_updated')}

IMPORTANT: Use these EXACT status names and source names in your queries to match the real account.

⸻

"""
    
    # Prepare dynamic examples
    source_examples = ", ".join(huntflow_context.get('sources', ['LinkedIn', 'Referral', 'Direct', 'Agency'])[:5])
    status_examples = ", ".join([s['name'] for s in huntflow_context.get('vacancy_statuses', [])][:8])
    
    prompt_base = """You are an HR-analytics expert with full knowledge of Huntflow API's entities and data structure.
Always answer user requests only with a single valid JSON object strictly following the schema below.
Never return explanations or text outside the JSON.

CRITICAL: Do NOT include any demo_value, demo_data, or placeholder values in your JSON response. The system fetches real data automatically.

⸻

1. JSON Output Schema

{
  "report_title": "Short human-readable title",
  "main_metric": {
    "label": "Main metric caption",
    "value": {
      "operation": "count|sum|avg|max|min",
      "entity": "applicants|recruiters|vacancies|status_mapping|sources|divisions",
      "filter": { "field": "<field_name>", "op": "eq|ne|gt|lt|in", "value": "<value>" } | [{ "field": "<field1>", "op": "eq", "value": "<val1>" }, { "field": "<field2>", "op": "gte", "value": "<val2>" }],
      "group_by": { "field": "<field_name>" }
    }
  },
  "secondary_metrics": [
    {
      "label": "Secondary metric name",
      "value": { /* same as main_metric.value */ }
    }
  ],
  "chart": {
    "graph_description": "What this chart shows (1-2 lines)",
    "chart_type": "bar|line|scatter",
    "x_axis_name": "X-axis label (human readable)",
    "y_axis_name": "Y-axis label (human readable)",
    "x_axis": { "operation": "field", "field": "<see fields below>" },
    "y_axis": {
      "operation": "count|sum|avg",
      "entity": "applicants|recruiters|vacancies|status_mapping|sources|divisions",
      "filter": { "field": "<field_name>", "op": "eq|ne|gt|lt|in", "value": "<value>" } | [{ "field": "<field1>", "op": "eq", "value": "<val1>" }, { "field": "<field2>", "op": "gte", "value": "<val2>" }],
      "group_by": { "field": "<field_name>" }
    }
  }
}

EXAMPLE OUTPUT (no demo values):
{
  "report_title": "Recruiter Performance Analysis",
  "main_metric": {
    "label": "Top Hires by Recruiter",
    "value": {
      "operation": "count",
      "entity": "applicants",
      "filter": {"field": "status_name", "op": "eq", "value": "Оффер принят"},
      "group_by": {"field": "recruiter_name"}
    }
  },
  "secondary_metrics": [
    {
      "label": "Total Hired Applicants",
      "value": {
        "operation": "count",
        "entity": "applicants",
        "filter": {"field": "status_name", "op": "eq", "value": "Оффер принят"}
      }
    }
  ],
  "chart": {
    "graph_description": "Hires by recruiter performance",
    "chart_type": "bar", 
    "x_axis_name": "Recruiter",
    "y_axis_name": "Number of Hires",
    "x_axis": {"operation": "field", "field": "recruiter_name"},
    "y_axis": {
      "operation": "count",
      "entity": "applicants",
      "filter": {"field": "status_name", "op": "eq", "value": "Оффер принят"},
      "group_by": {"field": "recruiter_name"}
    }
  }
}

⸻

2. Supported Entities (based on huntflow_schema.py virtual tables):
    •    applicants: candidates tracked in the pipeline
    •    vacancies: open positions; include hiring quotas, statuses
    •    recruiters: internal users (recruiters, managers, etc.) - mapped from coworkers API
    •    status_mapping: hiring pipeline stages and status tracking
    •    sources: recruitment sources (LinkedIn, referrals, etc.)
    •    divisions: company departments/divisions
    •    applicant_tags: labels assigned to applicants for categorization
    •    offers: job offers made to candidates
    •    applicant_links: applicant-vacancy status relationships

CRITICAL: Use ONLY the entities listed above. For rejection analysis, use "applicants" entity with status_name filters, NOT "rejections" entity.

⸻

3. Allowed Field Names
    •    applicants:
    •    id, first_name, last_name, middle_name, birthday, phone, skype, email, money, position, company, photo, photo_url, created, account, tags, external, agreement, doubles, social, source_id, recruiter_id, recruiter_name, source_name, status_id, status_name, vacancy_id
    •    vacancies:
    •    id, position, company, account_division, account_region, money, priority, hidden, state, created, updated, multiple, parent, account_vacancy_status_group, additional_fields_list, body, requirements, conditions, files, coworkers, source, blocks, vacancy_request
    •    recruiters:
    •    id, name, email, member, type, head, meta, permissions, full_name
    •    offers:
    •    id, offer_id, applicant_id, vacancy_frame_id, status, created, updated, values
    •    tags:
    •    id, tag_id, name, color, created, updated
    •    sources:
    •    id, name, type, foreign
    •    status_mapping:
    •    id, name, type, order, stay_duration, removed
    •    divisions:
    •    id, name, order, active, deep, parent, foreign, meta
    •    questionary:
    •    current_salary, expected_salary, position, relocation, availability
    •    rejections:
    •    id, applicant_id, reason, reason_id, created, updated
    •    responses:
    •    id, applicant_id, status, date_received, source
    •    logs:
    •    id, type, applicant, vacancy, status, rejection_reason, created, author
    •    General:
    •    department, source, status, current_stage, date

Valid Filters/Groups:
    •    department: e.g., Engineering, Sales, Marketing, HR, Finance
    •    source: e.g., {source_examples}
    •    status: e.g., {status_examples}
    •    current_stage: same as status
    •    date: date fields are filterable/groupable
    •    rejection_reason_id: filter/group rejected candidates

⸻

4. Operation Definitions & Field Usage

CRITICAL: Understand the difference between "field" and "group_by":
    •    "field": WHAT to calculate (the numeric field you're averaging/summing)
    •    "group_by": HOW to group the results (what to group by)

Operations:
    •    count: number of items (e.g. applicants, vacancies) - NO field needed
    •    sum: total value for numeric fields - REQUIRES "field" parameter (e.g. "money")
    •    avg: average value of a numeric field - REQUIRES "field" parameter (e.g. "money")
    •    max/min: highest/lowest value - REQUIRES "field" parameter (e.g. "money")
    •    field: used only for grouping (x_axis)

IMPORTANT: When using "avg", "sum", "max", or "min" operations, you MUST specify the "field" parameter with a numeric field name. Valid numeric fields include:
    •    For applicants: "money" (salary expectation)
    •    For vacancies: "money" (salary), "priority" (0-1)
    •    For status_mapping: "order", "stay_duration"
    •    For divisions: "order", "deep"

EXAMPLES - Pay attention to field vs group_by:

✅ CORRECT - Count hired applicants:
{
  "operation": "count",
  "entity": "applicants",
  "filter": {"field": "status_name", "op": "eq", "value": "Оффер принят"}
}

✅ CORRECT - Count applicants BY status:
{
  "operation": "count", 
  "entity": "applicants",
  "group_by": {"field": "status_name"}
}

✅ CORRECT - Count applicants:
{
  "operation": "count",
  "entity": "applicants"
}

✅ CORRECT - Average salary of vacancies:
{
  "operation": "avg",
  "entity": "vacancies",
  "field": "money"
}

✅ CORRECT - Average salary expectation by recruiter:
{
  "operation": "avg",
  "entity": "applicants", 
  "field": "money",
  "group_by": {"field": "recruiter_name"}
}

❌ WRONG - Missing field parameter for avg:
{
  "operation": "avg",
  "entity": "applicants",
  "group_by": {"field": "recruiter_name"}
}

✅ CORRECT - Distribution query with grouping:
{
  "operation": "count",
  "entity": "applicants",
  "group_by": {"field": "status_name"}
}

✅ CORRECT - Top/ranking query with grouping:
{
  "operation": "count", 
  "entity": "applicants",
  "group_by": {"field": "recruiter_name"}
}

❌ WRONG - Distribution query without grouping:
{
  "operation": "count",
  "entity": "applicants"
}

CRITICAL REMINDER: Your JSON must NOT contain:
- demo_value fields
- demo_data objects
- placeholder or example values
- Any field not in the schema above

CRITICAL: Do NOT use "avg" operation without a valid numeric field. If you need to calculate averages of counts (e.g., "average candidates per recruiter"), use "count" with group_by instead. Only use "avg" when averaging actual numeric values like money/salary.

IMPORTANT: For DISTRIBUTION and RANKING queries, always use group_by in the main metric:
- "распределение по X" (distribution by X) → main_metric should use group_by: {"field": "X"}
- "топ X по Y" (top X by Y) → main_metric should use group_by: {"field": "X"}  
- "рейтинг X" (ranking of X) → main_metric should use group_by: {"field": "X"}
- "кто больше всех" (who has the most) → main_metric should use group_by to compare entities

⸻

5. Real Data Only
    •    No demo values required - system fetches real Huntflow data
    •    Focus on accurate query structure for API data retrieval
    •    All metrics and charts populated from actual API responses

⸻

6. Common HR Analytics Patterns & Business Examples

IMPORTANT: Use these real-world patterns for typical HR analytics queries:

## CONVERSION METRICS:
• Funnel conversion rate: Count by status with filters at each stage
• Source conversion: Compare hired vs total by source_name
• Recruiter conversion: Compare hired vs total by recruiter_name

## TIME-BASED METRICS:
• Time to hire: Use created field for date-based analysis
• Pipeline aging: Filter by date ranges (e.g., "created" field)
• Monthly/weekly trends: Group by time periods
• Recent activity: Use filters like {"field": "created", "op": "gte", "value": "2025-11-22"} for "last 2 weeks"
• Time ranges: "за неделю", "за месяц", "за квартал" → use date filters with created field

## FILTERING PATTERNS:
• By hiring stage: filter: {"field": "status_name", "op": "eq", "value": "Собеседование"}
• By success: filter: {"field": "status_name", "op": "eq", "value": "Оффер принят"}
• By rejection: filter: {"field": "status_name", "op": "eq", "value": "Отказ"}
• By recruiter: filter: {"field": "recruiter_name", "op": "eq", "value": "John Smith"}
• By source: filter: {"field": "source_name", "op": "eq", "value": "LinkedIn"}
• By active vacancies: filter: {"field": "state", "op": "eq", "value": "OPEN"}
• By salary range: filter: {"field": "money", "op": "gt", "value": "100000"}

## PERFORMANCE METRICS:
• Recruiter efficiency: Count hired applicants by recruiter_name
• Source ROI: Count hired vs total applicants by source_name  
• Offer acceptance rate: Count accepted vs offered by any dimension
• Pipeline velocity: Count applicants at each status stage

## EXAMPLES FOR COMPLEX QUERIES:

✅ Conversion rate by source:
{
  "operation": "count",
  "entity": "applicants", 
  "filter": {"field": "status_name", "op": "eq", "value": "Оффер принят"},
  "group_by": {"field": "source_name"}
}

✅ Recruiter performance (hires):
{
  "operation": "count",
  "entity": "applicants",
  "filter": {"field": "status_name", "op": "eq", "value": "Оффер принят"},
  "group_by": {"field": "recruiter_name"}
}

✅ Pipeline by stage:
{
  "operation": "count", 
  "entity": "applicants",
  "group_by": {"field": "status_name"}
}

✅ Active vacancy analysis:
{
  "operation": "count",
  "entity": "vacancies", 
  "filter": {"field": "state", "op": "eq", "value": "OPEN"},
  "group_by": {"field": "company"}
}

✅ Salary analysis by recruiter:
{
  "operation": "avg",
  "entity": "applicants",
  "field": "money",
  "group_by": {"field": "recruiter_name"}
}

✅ High-priority vacancies:
{
  "operation": "count",
  "entity": "vacancies",
  "filter": {"field": "priority", "op": "eq", "value": "1"}
}

✅ Recent hires (last 2 weeks):
{
  "operation": "count",
  "entity": "applicants",
  "filter": [
    {"field": "status_name", "op": "eq", "value": "Оффер принят"},
    {"field": "created", "op": "gte", "value": "2025-11-22"}
  ]
}

✅ Rejection analysis (why candidates drop out):
{
  "operation": "count",
  "entity": "applicants",
  "filter": {"field": "status_name", "op": "in", "value": ["Отказ", "Не подошел", "Отклонен"]},
  "group_by": {"field": "status_name"}
}

✅ Dropout analysis by source:
{
  "operation": "count",
  "entity": "applicants",
  "filter": {"field": "status_name", "op": "eq", "value": "Отказ"},
  "group_by": {"field": "source_name"}
}

## FILTER USAGE PATTERNS:

IMPORTANT: Use appropriate filter patterns based on query complexity:

✅ SINGLE FILTER - For simple conditions:
{
  "filter": {"field": "status_name", "op": "eq", "value": "Оффер принят"}
}

✅ MULTIPLE FILTERS (Array) - For complex conditions with time ranges, multiple criteria:
{
  "filter": [
    {"field": "status_name", "op": "eq", "value": "Оффер принят"},
    {"field": "created", "op": "gte", "value": "2025-04-01"},
    {"field": "created", "op": "lt", "value": "2025-07-01"}
  ]
}

✅ IN OPERATOR - For multiple values of same field:
{
  "filter": {"field": "status_name", "op": "in", "value": ["Отказ", "Не подошел", "Отклонен"]}
}

WHEN TO USE MULTIPLE FILTERS:
• Time period analysis (quarterly, monthly comparisons)
• Complex business logic requiring multiple conditions
• Status + date range combinations
• Recruiter + time period analysis
• Source + outcome filtering

## COMMON RUSSIAN HR QUERIES & TRANSLATIONS:

• "конверсия" / "конверсия воронки" → conversion rate analysis with status filtering
• "время найма" / "скорость найма" → time to hire using created field analysis  
• "принятие оффера" / "принятые офферы" → offer acceptance with "Оффер принят" filter
• "эффективность рекрутеров" → recruiter performance with hired status filter
• "ROI источников" → source effectiveness comparing hired vs total
• "воронка найма" → hiring funnel with status distribution
• "активность по вакансиям" → vacancy metrics with state filtering
• "зарплатная вилка" → salary analysis using money field
• "отклоненные кандидаты" → rejected candidates with rejection status filter
• "средний чек" / "средняя зарплата" → average salary using avg operation on money field
• "производительность команды" → team performance with recruiter grouping
• "качество источников" → source quality with conversion analysis
• "почему отваливаются" / "причины отказов" → rejection analysis using status_name filtering
• "дропаут кандидатов" → dropout analysis with rejection status filters
• "узкие места воронки" → funnel bottleneck analysis with status distribution

⸻

7. Final Output Rules
    •    Output only valid JSON, no commentary
    •    Use only field/entity names from above
    •    Always include "report_title", KPI(s), and chart
    •    Max 2 secondary metrics
    •    NEVER include demo_value, demo_data, or any placeholder fields
    •    If a metric/filter/group not supported, answer using nearest possible Huntflow structure/field
    •    Do not invent fields or entities

⸻

FINAL REMINDER: Your response must be ONLY the JSON schema shown above. NO demo_value, NO demo_data, NO additional fields.

⸻"""
    
    # Replace placeholders with actual values
    full_prompt = prompt_base + context_section
    full_prompt = full_prompt.replace("{source_examples}", source_examples)
    full_prompt = full_prompt.replace("{status_examples}", status_examples)
    
    return full_prompt


async def create_assistant():
    """Create a new assistant with our HR analytics prompt"""
    try:
        assistant = await openai_client.beta.assistants.create(
            name="HR Analytics Expert",
            instructions=get_unified_prompt(),
            model="gpt-4o",
            tools=[]
        )
        return assistant.id
    except Exception as e:
        print(f"Error creating assistant: {e}")
        return None


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process chat message with selected AI model"""
    try:
        # Check if HF_TOKEN is available
        if not hf_client.token:
            return ChatResponse(response="⚠️ Huntflow API token not configured")
        
        # Handle DeepSeek models
        if request.model in ["deepseek", "deepseek-r1", "deepseek-reasoner"]:
            return await chat_with_deepseek(request)
        
        # Handle OpenAI model (default)
        return await chat_with_openai(request)
        
    except Exception as e:
        return ChatResponse(
            response=f"⚠️ Error: {str(e)}", 
            thread_id=request.thread_id or ""
        )


async def chat_with_deepseek(request: ChatRequest):
    """Handle chat with DeepSeek model"""
    
    # Map model names to actual API model names
    model_mapping = {
        "deepseek": "deepseek-chat",
        "deepseek-r1": "deepseek-r1",
        "deepseek-reasoner": "deepseek-reasoner"
    }
    
    model_name = model_mapping.get(request.model, "deepseek-chat")
    
    try:
        # Build conversation history
        messages = [
            {"role": "system", "content": get_unified_prompt()},
            {"role": "system", "content": "ABSOLUTE REQUIREMENT: Your JSON response must NOT contain demo_value, demo_data, or any placeholder fields. Only return the exact schema shown in the instructions."}
        ]
        
        # Add conversation history if provided
        if request.messages:
            messages.extend(request.messages)
        
        # Add current user message
        messages.append({"role": "user", "content": request.message})
        
        response = await deepseek_client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=request.temperature,
            response_format={'type': 'json_object'},
            max_tokens=4000
        )
        
        # Validate the response and optionally fetch real data
        validated_response = await validate_and_enhance_response(
            response.choices[0].message.content,
            use_real_data=request.use_real_data,
            hf_client=hf_client
        )
        
        return ChatResponse(
            response=validated_response,
            thread_id=request.thread_id or f"deepseek_{int(asyncio.get_event_loop().time())}"
        )
    except Exception as e:
        return ChatResponse(
            response=f"⚠️ DeepSeek error: {str(e)}",
            thread_id=request.thread_id or ""
        )


async def chat_with_openai(request: ChatRequest):
    """Handle chat with OpenAI Assistant API"""
    # Get assistant ID from environment
    assistant_id = os.getenv("OPENAI_ASSISTANT_ID")
    if not assistant_id:
        # Create a new assistant
        assistant_id = await create_assistant()
        if not assistant_id:
            return ChatResponse(response="⚠️ Failed to create OpenAI Assistant", thread_id="")
        print(f"Created new assistant: {assistant_id}")
    
    # Try to use the assistant, create new one if it doesn't exist
    try:
        await openai_client.beta.assistants.retrieve(assistant_id)
    except Exception as e:
        if "No assistant found" in str(e):
            print(f"Assistant {assistant_id} not found, creating new one...")
            assistant_id = await create_assistant()
            if not assistant_id:
                return ChatResponse(response="⚠️ Failed to create OpenAI Assistant", thread_id="")
            print(f"Created new assistant: {assistant_id}")
        else:
            return ChatResponse(response=f"⚠️ Error accessing assistant: {str(e)}", thread_id="")
    
    # Use existing thread or create a new one
    if request.thread_id:
        thread_id = request.thread_id
        try:
            # Verify thread exists
            await openai_client.beta.threads.retrieve(thread_id)
        except Exception:
            # Thread doesn't exist, create new one
            thread = await openai_client.beta.threads.create()
            thread_id = thread.id
    else:
        # No thread provided, create new one
        thread = await openai_client.beta.threads.create()
        thread_id = thread.id
    
    # Add the user message to the thread
    await openai_client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=request.message
    )
    
    # Create and poll the run until completion
    run = await openai_client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=assistant_id
    )
    
    # Get the assistant's response
    if run.status == "completed":
        # Get messages from the thread
        messages = await openai_client.beta.threads.messages.list(
            thread_id=thread_id,
            order="desc",
            limit=1
        )
        
        if messages.data and messages.data[0].role == "assistant":
            # Extract text content from the assistant's message
            message_content = messages.data[0].content[0]
            if hasattr(message_content, 'text'):
                response_text = message_content.text.value
            else:
                response_text = str(message_content)
            
            # Validate the response and optionally fetch real data
            validated_response = await validate_and_enhance_response(
                response_text,
                use_real_data=request.use_real_data,
                hf_client=hf_client
            )
            
            return ChatResponse(response=validated_response, thread_id=thread_id)
        else:
            return ChatResponse(response="⚠️ No assistant response found", thread_id=thread_id)
    else:
        return ChatResponse(response=f"⚠️ Assistant run failed with status: {run.status}", thread_id=thread_id)


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "hf_configured": bool(hf_client.token),
        "openai_configured": bool(os.getenv("OPENAI_API_KEY"))
    }

@app.get("/api/prefetch-data")
async def prefetch_huntflow_data():
    """Prefetch all Huntflow metadata for faster analytics"""
    try:
        print("🔄 API prefetch request received")
        
        # Initialize the virtual engine to prefetch data
        from sqlalchemy_executor import SQLAlchemyHuntflowExecutor
        sqlalchemy_executor = SQLAlchemyHuntflowExecutor(hf_client)
        
        # Prefetch all the core data
        print("🔄 Prefetching statuses...")
        statuses = await sqlalchemy_executor.engine._get_status_mapping()
        
        print("🔄 Prefetching recruiters...")
        recruiters = await sqlalchemy_executor.engine._get_recruiters_mapping()
        
        print("🔄 Prefetching applicants data...")
        applicants_data = await sqlalchemy_executor.engine._get_applicants_data()
        
        # Calculate some basic stats
        total_applicants = len(applicants_data)
        status_distribution = {}
        recruiter_distribution = {}
        
        for applicant in applicants_data:
            status = applicant.get('status_name', 'Unknown')
            recruiter = applicant.get('recruiter_name', 'Unknown')
            
            status_distribution[status] = status_distribution.get(status, 0) + 1
            if recruiter != 'Unknown':
                recruiter_distribution[recruiter] = recruiter_distribution.get(recruiter, 0) + 1
        
        # Sort distributions
        top_statuses = sorted(status_distribution.items(), key=lambda x: x[1], reverse=True)[:10]
        top_recruiters = sorted(recruiter_distribution.items(), key=lambda x: x[1], reverse=True)[:5]
        
        prefetch_data = {
            "statuses": {
                "mapping": statuses,
                "list": list(statuses.values()),
                "distribution": dict(top_statuses)
            },
            "recruiters": {
                "mapping": recruiters,
                "list": list(recruiters.values()),
                "distribution": dict(top_recruiters)
            },
            "summary": {
                "total_applicants": total_applicants,
                "total_statuses": len(statuses),
                "total_recruiters": len(recruiters),
                "top_status": top_statuses[0][0] if top_statuses else "N/A",
                "top_recruiter": top_recruiters[0][0] if top_recruiters else "N/A"
            },
            "cache_time": datetime.now().isoformat(),
            "data_source": "huntflow_demo" if total_applicants > 0 else "empty"
        }
        
        print(f"✅ Prefetch complete: {total_applicants} applicants, {len(statuses)} statuses, {len(recruiters)} recruiters")
        
        return prefetch_data
        
    except Exception as e:
        print(f"❌ Prefetch error: {e}")
        return {
            "error": str(e),
            "statuses": {"mapping": {}, "list": [], "distribution": {}},
            "recruiters": {"mapping": {}, "list": [], "distribution": {}},
            "summary": {"total_applicants": 0, "total_statuses": 0, "total_recruiters": 0},
            "cache_time": datetime.now().isoformat(),
            "data_source": "error"
        }

@app.get("/")
async def serve_frontend():
    """Serve the frontend HTML file"""
    return FileResponse("index.html")


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Huntflow bot server...")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")