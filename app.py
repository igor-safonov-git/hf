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
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.responses import Response
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

# Assistant function using proper LangGraph tool calling pattern
# Assistant class following the LangGraph tutorial pattern
class Assistant:
    def __init__(self, runnable):
        self.runnable = runnable

    async def __call__(self, state: State, config):
        """Assistant that follows proper LangGraph pattern for tool usage."""
        
        # Log current state for debugging
        logger.info(f"=== Assistant called with {len(state['messages'])} messages ===")
        for i, msg in enumerate(state['messages']):
            msg_type = type(msg).__name__
            content_preview = str(msg.content)[:100] + "..." if len(str(msg.content)) > 100 else str(msg.content)
            logger.info(f"Message {i}: {msg_type} - {content_preview}")
        
        while True:
            # Call the LLM runnable
            result = await self.runnable.ainvoke(state)
            
            # If empty response, re-prompt (following tutorial pattern)
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [HumanMessage(content="Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        
        return {"messages": [result]}

# Create the assistant runnable with proper system prompt
def create_assistant_runnable():
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    
    # Single system prompt that handles both scenarios
    system_prompt = ChatPromptTemplate.from_messages([
        ("system", """Ты - разговорный ассистент HR-аналитики для системы Huntflow.

КРИТИЧЕСКИ ВАЖНО: Для ЛЮБОГО вопроса об аналитике (воронка, рекрутеры, источники, статистика, отчеты) ты ОБЯЗАН:
1. Дать короткий ответ "Анализирую [что]..."
2. НЕМЕДЛЕННО вызвать generate_hr_analytics_report с точным вопросом пользователя

ПРИМЕРЫ АНАЛИТИЧЕСКИХ ВОПРОСОВ:
- "Покажи воронку найма" → используй generate_hr_analytics_report
- "Кто лучший рекрутер" → используй generate_hr_analytics_report  
- "Статистика по источникам" → используй generate_hr_analytics_report
- "Отчет по вакансиям" → используй generate_hr_analytics_report

ЕСЛИ НЕ ВЫЗОВЕШЬ ИНСТРУМЕНТ - ЭТО ОШИБКА!

ТОЛЬКО для приветствий/общих вопросов отвечай без инструментов.

ПЕРВЫЙ ОТВЕТ + ВЫЗОВ ИНСТРУМЕНТА:
- Текст: "Анализирую воронку найма и создаю график..."
- Инструмент: generate_hr_analytics_report с question="Покажи воронку найма"

ФИНАЛЬНЫЙ ОТВЕТ (когда уже есть результат инструмента):
- "Готово! Кандидатов в воронке: 14. Создал график по этапам. Хотите по отделам?"

Отвечай на русском языке, будь кратким."""),
        ("placeholder", "{messages}"),
    ])
    
    llm = ChatOpenAI(
        model="deepseek-chat",
        temperature=0,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com"
    )
    
    # Bind tools to LLM
    llm_with_tools = llm.bind_tools([generate_hr_analytics_report])
    
    return system_prompt | llm_with_tools

# Build the graph following the tutorial pattern
def build_graph():
    from langgraph.prebuilt import ToolNode, tools_condition
    
    builder = StateGraph(State)
    
    # Create assistant instance with the runnable
    assistant_runnable = create_assistant_runnable()
    assistant_instance = Assistant(assistant_runnable)
    
    # Add nodes
    builder.add_node("assistant", assistant_instance)
    builder.add_node("tools", ToolNode([generate_hr_analytics_report]))
    
    # Add edges following tutorial pattern
    builder.add_edge(START, "assistant")
    builder.add_conditional_edges(
        "assistant",
        tools_condition,  # This checks if the AI message has tool_calls
    )
    builder.add_edge("tools", "assistant")  # After tools, go back to assistant
    
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
            
        # Use streaming to capture sequential messages (like the tutorial)
        all_messages = []
        tool_result = None
        
        logger.info("=== Starting LangGraph streaming ===")
        
        # Stream events to see the sequential flow  
        async for event in graph_instance.astream(initial_state, config, stream_mode="values"):
            logger.info(f"Stream event: {len(event.get('messages', []))} messages")
            
            # Get the latest messages from this event
            if "messages" in event:
                current_messages = event["messages"]
                
                # Log new messages
                for i, msg in enumerate(current_messages[len(all_messages):]):
                    msg_type = type(msg).__name__
                    content_preview = str(msg.content)[:100] + "..." if len(str(msg.content)) > 100 else str(msg.content)
                    
                    # Show tool calls more clearly
                    if isinstance(msg, AIMessage) and msg.tool_calls:
                        logger.info(f"  New message {len(all_messages) + i}: {msg_type} with tool_calls - {content_preview}")
                        logger.info(f"    Tool calls: {[tc.get('name', 'unknown') for tc in msg.tool_calls]}")
                    else:
                        logger.info(f"  New message {len(all_messages) + i}: {msg_type} - {content_preview}")
                
                all_messages = current_messages
        
        logger.info(f"=== Streaming complete: {len(all_messages)} total messages ===")
        
        # Extract the final AI message and any tool results
        final_ai_message = None
        
        for msg in reversed(all_messages):
            if isinstance(msg, AIMessage):
                final_ai_message = msg
                break
        
        # Find any tool result
        for msg in all_messages:
            if isinstance(msg, ToolMessage):
                try:
                    tool_result = json.loads(msg.content)
                    break
                except:
                    pass
        
        if not final_ai_message:
            raise HTTPException(
                status_code=500,
                detail="No final response from assistant"
            )
        
        # Format response based on what we have
        if tool_result and final_ai_message:
            # We have both conversational summary and chart data
            conversational_response = {
                "conversational_text": final_ai_message.content,
                "chart_data": tool_result
            }
            return ChatResponse(
                response=json.dumps(conversational_response, ensure_ascii=False),
                thread_id=config["configurable"]["thread_id"]
            )
        elif tool_result:
            # Only tool result, no conversational summary (shouldn't happen with new flow)
            return ChatResponse(
                response=json.dumps(tool_result, ensure_ascii=False),
                thread_id=config["configurable"]["thread_id"]
            )
        else:
            # Only conversational response, no chart data
            return ChatResponse(
                response=final_ai_message.content,
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


@app.get("/test-stream")
async def test_stream():
    """Simple test SSE endpoint"""
    async def generate():
        for i in range(3):
            yield f"data: {{\"message\": \"Test {i}\"}}\n\n"
            await asyncio.sleep(1)
        yield f"data: {{\"complete\": true}}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.get("/chat-stream")
async def chat_stream(
    message: str,
    thread_id: Optional[str] = None,
    model: Optional[str] = "deepseek",
    temperature: Optional[float] = 0.1
):
    """SSE streaming chat endpoint powered by LangGraph"""
    import time
    
    async def generate_stream():
        try:
            config = {
                "configurable": {
                    "thread_id": thread_id or f"chat_{int(time.time())}"
                }
            }
            
            # Create initial state
            initial_state = {
                "messages": [HumanMessage(content=message)],
                "context": {},
                "current_report": None
            }
            
            # Get and run the graph
            graph_instance = get_graph()
            if not graph_instance:
                yield f"data: {json.dumps({'error': 'LangGraph not initialized'})}\n\n"
                return
                
            logger.info("=== Starting LangGraph SSE streaming ===")
            
            # Track processed messages to avoid duplicates
            processed_count = 0
            
            # Stream events to see the sequential flow
            async for event in graph_instance.astream(initial_state, config, stream_mode="values"):
                if "messages" in event:
                    current_messages = event["messages"]
                    
                    # Process only new messages
                    new_messages = current_messages[processed_count:]
                    
                    for msg in new_messages:
                        if isinstance(msg, AIMessage):
                            if msg.tool_calls:
                                # AI message with tool calls - send the content
                                stream_data = {
                                    "type": "ai_message",
                                    "content": msg.content,
                                    "has_tool_calls": True
                                }
                                yield f"data: {json.dumps(stream_data, ensure_ascii=False)}\n\n"
                            else:
                                # Final AI message without tool calls
                                stream_data = {
                                    "type": "ai_message_final", 
                                    "content": msg.content,
                                    "has_tool_calls": False
                                }
                                yield f"data: {json.dumps(stream_data, ensure_ascii=False)}\n\n"
                        
                        elif isinstance(msg, ToolMessage):
                            # Tool result - send chart data
                            try:
                                tool_result = json.loads(msg.content)
                                stream_data = {
                                    "type": "tool_result",
                                    "chart_data": tool_result
                                }
                                yield f"data: {json.dumps(stream_data, ensure_ascii=False)}\n\n"
                            except:
                                logger.warning("Failed to parse tool result as JSON")
                    
                    processed_count = len(current_messages)
            
            # Send completion signal
            completion_data = {
                "type": "complete",
                "thread_id": config["configurable"]["thread_id"]
            }
            yield f"data: {json.dumps(completion_data, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logger.error(f"SSE streaming error: {e}")
            error_data = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "Content-Type",
        }
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
    
    # Development mode - use port 8000
    logger.info("Starting development server on port 8000...")
    uvicorn.run(app, host="127.0.0.1", port=8000)