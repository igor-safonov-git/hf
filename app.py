import os
import json
import asyncio
import logging
import tempfile
from typing import Dict, Any, Optional, List
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from openai import AsyncOpenAI
import aiofiles
from prompt import get_comprehensive_prompt
from context_data_injector import get_dynamic_context
from huntflow_local_client import HuntflowLocalClient
from chart_data_processor import process_chart_data
from enhanced_metrics_calculator import EnhancedMetricsCalculator

# LangGraph imports
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langgraph.graph.message import AnyMessage, add_messages

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
    
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY not found - voice transcription will be limited")
    
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

# Initialize local Huntflow client and metrics calculator
hf_client = HuntflowLocalClient()
metrics_calc = EnhancedMetricsCalculator(hf_client, None)

# ==================== LangGraph Components ====================

# State definition
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    context: dict  # Huntflow context
    current_report: Optional[dict]

# Single powerful tool wrapping existing logic
@tool
async def generate_hr_analytics_report(question: str) -> dict:
    """Generate comprehensive HR analytics report from natural language question.
    Understands Russian and returns structured data with charts and metrics."""
    
    # Get fresh context
    context = await get_dynamic_context(hf_client)
    
    # Use existing prompt
    system_prompt = get_comprehensive_prompt(huntflow_context=context)
    
    # Call DeepSeek (existing logic)
    response = await deepseek_client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": "Return only valid JSON. No markdown formatting or explanations."},
            {"role": "user", "content": question}
        ],
        model="deepseek-chat",
        temperature=0.1,
        response_format={'type': 'json_object'},
        max_tokens=4000
    )
    
    # Parse and enrich with real data
    ai_response = response.choices[0].message.content
    response_data = json.loads(ai_response)
    enriched_data = await process_chart_data(response_data, hf_client)
    
    return enriched_data

# Assistant class with proper LangGraph memory usage
class Assistant:
    def __init__(self, llm):
        self.llm = llm
        
    async def __call__(self, state: State, config):
        # Log current state
        logger.info(f"=== Assistant called with {len(state['messages'])} messages ===")
        for i, msg in enumerate(state['messages']):
            msg_type = type(msg).__name__
            content_preview = str(msg.content)[:100] + "..." if len(str(msg.content)) > 100 else str(msg.content)
            logger.info(f"Message {i}: {msg_type} - {content_preview}")
        
        # System prompt that helps the LLM understand the conversation context
        system_message = SystemMessage(content="""Ты - ассистент HR-аналитики для системы Huntflow. 
Ты анализируешь историю сообщений и понимаешь контекст разговора.
Если пользователь задает уточняющий вопрос (например, "а что с отделом разработки?"), 
ты должен учесть предыдущий контекст и сформулировать полный вопрос для системы аналитики.

Примеры:
- Пользователь: "Покажи воронку найма"
- Ты формулируешь: "Покажи воронку найма"

- Пользователь: "А что с отделом разработки?"
- Ты формулируешь: "Покажи воронку найма для отдела разработки"

- Пользователь: "Покажи только новых кандидатов"
- Ты формулируешь: "Покажи только новых кандидатов в воронке найма для отдела разработки"

Всегда отвечай на русском языке.""")
        
        # Add system message to state messages, but filter out ToolMessages for LLM
        # DeepSeek doesn't accept ToolMessages without preceding tool_calls
        filtered_messages = []
        for msg in state["messages"]:
            if isinstance(msg, ToolMessage):
                # Convert tool message to AIMessage to preserve context
                try:
                    tool_content = json.loads(msg.content)
                    summary = f"[Результат анализа: {tool_content.get('report_title', 'Отчет создан')}]"
                    filtered_messages.append(AIMessage(content=summary))
                except:
                    pass
            else:
                filtered_messages.append(msg)
        
        messages = [system_message] + filtered_messages
        
        # Use LLM to understand context and reformulate the question
        context_prompt = """Проанализируй историю разговора и последний вопрос пользователя.
Если это уточняющий вопрос, сформулируй полный вопрос с учетом контекста.
Если это новый вопрос, просто повтори его.

Ответь ТОЛЬКО переформулированным вопросом, без объяснений."""
        
        messages_for_llm = messages + [HumanMessage(content=context_prompt)]
        
        # Get LLM to understand context and reformulate question
        llm_response = await self.llm.ainvoke(messages_for_llm)
        enhanced_question = llm_response.content.strip()
        logger.info(f"LLM reformulated question: {enhanced_question}")
        
        # Provide immediate feedback before tool execution
        initial_response = "Понял ваш запрос! Анализирую данные и создаю отчет..."
        
        # Call the analytics tool with the enhanced question
        result = await generate_hr_analytics_report.ainvoke({"question": enhanced_question})
        
        # Create conversational response based on the report
        report_title = result.get("report_title", "")
        main_metric = result.get("main_metric", {})
        chart_type = result.get("chart", {}).get("type", "chart")
        
        # Generate engaging conversational response
        if main_metric and "real_value" in main_metric:
            metric_value = main_metric["real_value"]
            metric_label = main_metric.get("label", "показатель")
            
            # Format the value nicely
            if isinstance(metric_value, (int, float)):
                formatted_value = f"{metric_value:,}".replace(",", " ")
            else:
                formatted_value = str(metric_value)
            
            # Create conversational response based on chart type
            if "воронка" in enhanced_question.lower() or "funnel" in chart_type.lower():
                response_text = f"Анализирую воронку найма... Готово! Основной показатель: {metric_label} = {formatted_value}. Создал визуализацию с детальной разбивкой по этапам."
            elif "таблица" in enhanced_question.lower() or chart_type == "table":
                response_text = f"Создаю таблицу с данными... Готово! {metric_label}: {formatted_value}. Таблица отображает детальную информацию с возможностью сортировки."
            elif "график" in enhanced_question.lower() or chart_type in ["line", "bar"]:
                response_text = f"Строю график для анализа... Завершено! {metric_label}: {formatted_value}. График показывает динамику и тренды в данных."
            else:
                response_text = f"Анализирую ваш запрос... Готово! {metric_label}: {formatted_value}. Создал {chart_type} для наглядного представления данных."
                
            # Add helpful follow-up suggestion
            response_text += " Могу показать разбивку по отделам или за другой период времени."
        else:
            # Fallback response
            response_text = f"Создал отчет «{report_title}». Визуализация готова! Хотите посмотреть данные за другой период или по конкретному отделу?"
        
        # Return conversational response and tool result
        return {
            "messages": [
                AIMessage(content=response_text),
                ToolMessage(content=json.dumps(result, ensure_ascii=False), tool_call_id="report_generation")
            ]
        }

# Build the graph
def build_graph():
    builder = StateGraph(State)
    
    # Initialize LLM - use DeepSeek via OpenAI compatible interface
    from langchain_openai import ChatOpenAI
    
    llm = ChatOpenAI(
        model="deepseek-chat",
        temperature=0,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com"
    )
    
    # Add single node - our assistant handles everything
    builder.add_node("assistant", Assistant(llm))
    
    # Simple flow: START -> assistant -> END
    builder.add_edge(START, "assistant")
    builder.add_edge("assistant", END)
    
    # Compile with memory
    memory = MemorySaver()
    return builder.compile(checkpointer=memory)

# Initialize graph lazily
graph = None

def get_graph():
    """Get or create the graph instance."""
    global graph
    if graph is None and os.getenv("DEEPSEEK_API_KEY"):
        graph = build_graph()
    return graph

# ==================== End LangGraph Components ====================

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    model: Optional[str] = "deepseek"
    temperature: Optional[float] = 0.1
    messages: Optional[List[Dict[str, str]]] = []


class ChatResponse(BaseModel):
    response: str
    thread_id: str


class TranscriptionResponse(BaseModel):
    text: str
    success: bool
    error: Optional[str] = None


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
    """Chat endpoint powered by LangGraph"""
    import time
    
    try:
        # Always use LangGraph
        
        config = {
            "configurable": {
                "thread_id": request.thread_id or f"chat_{int(time.time())}"
            }
        }
        
        # Create initial state
        initial_state = {
            "messages": [HumanMessage(content=request.message)],
            "context": {},
            "current_report": None
        }
        
        # Get and run the graph
        graph_instance = get_graph()
        if not graph_instance:
            raise HTTPException(
                status_code=503,
                detail="LangGraph not initialized - DeepSeek API key required"
            )
            
        final_state = await graph_instance.ainvoke(initial_state, config)
        
        # Extract the last AI message
        last_message = None
        for msg in reversed(final_state["messages"]):
            if isinstance(msg, AIMessage):
                last_message = msg
                break
        
        if not last_message:
            raise HTTPException(
                status_code=500,
                detail="No response from assistant"
            )
        
        # Check if there was a tool call and get the report
        report = None
        summary = last_message.content
        
        # Find tool response
        for msg in final_state["messages"]:
            if isinstance(msg, ToolMessage):
                try:
                    report = json.loads(msg.content)
                    break
                except:
                    pass
        
        # Format response for conversational interaction with chart data
        if report and summary:
            # Create a conversational response that includes both the chat message and chart data
            # The frontend will parse JSON if present, otherwise show the conversational text
            conversational_response = {
                "conversational_text": summary,
                "chart_data": report
            }
            return ChatResponse(
                response=json.dumps(conversational_response, ensure_ascii=False),
                thread_id=config["configurable"]["thread_id"]
            )
        elif report:
            # Fallback: just return the report JSON
            return ChatResponse(
                response=json.dumps(report, ensure_ascii=False),
                thread_id=config["configurable"]["thread_id"]
            )
        else:
            # Direct conversational response without tool call
            return ChatResponse(
                response=summary,
                thread_id=config["configurable"]["thread_id"]
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {str(e)}"
        )



@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transcribe audio using OpenAI Whisper API"""
    try:
        # Check if OpenAI API key is available (using DeepSeek client key for now)
        if not deepseek_client.api_key:
            raise HTTPException(
                status_code=503,
                detail="OpenAI API key not configured"
            )
        
        # Validate file type
        if not audio.content_type or not audio.content_type.startswith('audio/'):
            return TranscriptionResponse(
                text="",
                success=False,
                error="Invalid file type. Please upload an audio file."
            )
        
        # Read audio file content
        audio_content = await audio.read()
        
        # Create OpenAI client for transcription
        openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
        
        # If no OpenAI key, try using DeepSeek key (might not work)
        if not openai_client.api_key:
            logger.warning("No OPENAI_API_KEY found, attempting with DEEPSEEK_API_KEY")
            openai_client = AsyncOpenAI(api_key=os.getenv("DEEPSEEK_API_KEY", ""))
        
        # Create a temporary file for the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
            temp_file.write(audio_content)
            temp_file_path = temp_file.name
        
        try:
            # Call OpenAI Whisper API
            with open(temp_file_path, "rb") as audio_file:
                transcript = await openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="ru"  # Russian language for better recognition
                )
            
            logger.info(f"Transcription successful: {transcript.text[:100]}...")
            
            return TranscriptionResponse(
                text=transcript.text,
                success=True
            )
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")
        
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return TranscriptionResponse(
            text="",
            success=False,
            error=f"Transcription failed: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Check if the service is running and local database is accessible."""
    try:
        # Test database connection
        statuses = await metrics_calc.statuses_all()
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

@app.get("/index.html")
async def read_index_html():
    """Serve the main HTML file."""
    return FileResponse("index.html")


# Prefetch data endpoint
@app.get("/api/prefetch-data")
async def prefetch_data():
    """Prefetch common data for the frontend."""
    try:
        # Get data using metrics calculator
        statuses = await hf_client.get_vacancy_statuses()
        coworkers = await hf_client._req("GET", f"/v2/accounts/{hf_client.account_id}/coworkers")
        coworker_items = coworkers.get("items", [])
        
        # Pick a sample recruiter and status
        top_recruiter = coworker_items[0].get("name", "Unknown") if coworker_items else "No recruiters"
        top_status = statuses[0].get("name", "Unknown") if statuses else "No statuses"
        
        return {
            "status": "success",
            "summary": {
                "total_applicants": len(await metrics_calc.get_applicants()),
                "total_vacancies": len(await metrics_calc.get_vacancies()),
                "total_statuses": len(await metrics_calc.statuses_all()),
                "total_recruiters": len(await metrics_calc.get_recruiters()),
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
        # Get counts using metrics calculator
        info = {
            "data_source": "local_sqlite_cache",
            "database_path": hf_client.db_path,
            "account_id": hf_client.account_id,
            "stats": {
                "vacancies": len(await metrics_calc.get_vacancies()),
                "applicants": len(await metrics_calc.get_applicants()),
                "vacancy_statuses": len(await metrics_calc.statuses_all()),
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
    
    # Check if SSL certificates exist for HTTPS
    ssl_keyfile = "key.pem"
    ssl_certfile = "cert.pem"
    
    if os.path.exists(ssl_keyfile) and os.path.exists(ssl_certfile):
        logger.info("Starting HTTPS server on port 443...")
        logger.info("🔒 HTTPS URL: https://safonov.live (with speech-to-text)")
        
        # Start HTTPS server on port 443
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=443,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile,
            log_level="info"
        )
    else:
        logger.info("No SSL certificates found - starting HTTP server on port 80")
        logger.info("⚠️  Speech-to-text requires HTTPS")
        uvicorn.run(app, host="0.0.0.0", port=80)