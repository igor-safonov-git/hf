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
        return
    
    try:
        print("🔄 Fetching Huntflow data...")
        
        # Fetch open vacancies
        open_vacancies = await hf_client.get_open_vacancies()
        huntflow_context["open_vacancies"] = open_vacancies
        
        # Fetch recently closed vacancies  
        closed_vacancies = await hf_client.get_recently_closed_vacancies()
        huntflow_context["recently_closed_vacancies"] = closed_vacancies
        
        huntflow_context["last_updated"] = datetime.now().isoformat()
        
        print(f"✅ Updated context: {len(open_vacancies)} open, {len(closed_vacancies)} recently closed vacancies")
        
    except Exception as e:
        print(f"❌ Error updating Huntflow context: {e}")


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
        messages = [
            {"role": "system", "content": get_unified_prompt(huntflow_context)},
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
        
        return ChatResponse(
            response=ai_response,
            thread_id=request.thread_id or f"chat_{int(asyncio.get_event_loop().time())}"
        )
        
    except Exception as e:
        return ChatResponse(
            response=f"⚠️ Error: {str(e)}", 
            thread_id=request.thread_id or ""
        )


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