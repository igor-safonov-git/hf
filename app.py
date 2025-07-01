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
from langchain_groq import ChatGroq
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

# Configure logging with file output
from datetime import datetime
log_filename = f"server_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()  # Also log to console
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Validate critical environment variables
def validate_environment():
    """Validate that required environment variables are present"""
    missing_vars = []
    
    if not os.getenv("GROQ_API_KEY"):
        missing_vars.append("GROQ_API_KEY")
    
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

# Initialize Groq client for tool function
groq_client = ChatGroq(
    model="deepseek-r1-distill-llama-70b",
    temperature=0.1,
    max_tokens=4000,
    api_key=os.getenv("GROQ_API_KEY")
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
    
    logger.info(f"🔧 TOOL CALLED: generate_hr_analytics_report with question: {question}")
    
    try:
        # Get fresh context
        logger.info("🔧 Getting dynamic context...")
        context = await get_dynamic_context(hf_client)
        logger.info(f"🔧 Context retrieved: {len(str(context))} chars")
        
        # Use existing prompt
        logger.info("🔧 Getting comprehensive prompt...")
        system_prompt = get_comprehensive_prompt(huntflow_context=context)
        logger.info(f"🔧 System prompt length: {len(system_prompt)} chars")
        
        # Call Groq API
        logger.info("🔧 Calling Groq API...")
        from langchain_core.messages import SystemMessage, HumanMessage
        
        messages = [
            SystemMessage(content=system_prompt),
            SystemMessage(content="Return only valid JSON. No markdown formatting or explanations."),
            HumanMessage(content=question)
        ]
        
        response = await groq_client.ainvoke(messages)
        logger.info(f"🔧 Groq response received: {len(response.content)} chars")
        logger.info(f"🔧 Groq response preview: {response.content[:200]}")
        
        # Parse and enrich with real data
        logger.info("🔧 Parsing JSON response...")
        ai_response = response.content
        
        # Handle DeepSeek R1 reasoning format - extract JSON from <think> tags or find JSON blocks
        json_content = ai_response
        if ai_response.startswith('<think>'):
            # Extract content after </think> tag
            think_end = ai_response.find('</think>')
            if think_end != -1:
                json_content = ai_response[think_end + 8:].strip()
            logger.info(f"🔧 Extracted JSON from reasoning: {json_content[:200]}")
        
        # Try to find JSON block in response
        if not json_content.startswith('{'):
            import re
            json_match = re.search(r'\{.*\}', json_content, re.DOTALL)
            if json_match:
                json_content = json_match.group(0)
                logger.info(f"🔧 Found JSON block: {json_content[:200]}")
        
        response_data = json.loads(json_content)
        logger.info(f"🔧 JSON parsed successfully: {list(response_data.keys())}")
        
        logger.info("🔧 Processing chart data...")
        enriched_data = await process_chart_data(response_data, hf_client)
        logger.info(f"🔧 Chart data processed: {list(enriched_data.keys())}")
        
        logger.info("🔧 TOOL COMPLETED SUCCESSFULLY")
        return enriched_data
        
    except Exception as e:
        logger.error(f"🔧 TOOL ERROR: {type(e).__name__}: {str(e)}")
        logger.error(f"🔧 TOOL ERROR TRACEBACK:", exc_info=True)
        raise e

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

ОБЯЗАТЕЛЬНО ИСПОЛЬЗУЙ ИНСТРУМЕНТ generate_hr_analytics_report ДЛЯ ВСЕХ ВОПРОСОВ ПРО ДАННЫЕ!

ДЛЯ ВОПРОСА "Кто наш лучший рекрутер?" - ОБЯЗАТЕЛЬНО вызови generate_hr_analytics_report!

ВАЖНО: ВЫЗЫВАЙ ИНСТРУМЕНТ ТОЛЬКО ОДИН РАЗ! Не делай повторных вызовов для одного вопроса.

ТОЛЬКО для "привет", "спасибо" отвечай без инструментов.

ПЕРВЫЙ ОТВЕТ + ВЫЗОВ ИНСТРУМЕНТА:
- Текст: "Анализирую воронку найма и создаю график..."
- Инструмент: generate_hr_analytics_report с question="Покажи воронку найма"

ФИНАЛЬНЫЙ ОТВЕТ (когда уже есть результат инструмента):
- "Готово! Кандидатов в воронке: 14. Создал график по этапам. Хотите по отделам?"

Отвечай на русском языке, будь кратким."""),
        ("placeholder", "{messages}"),
    ])
    
    llm = ChatGroq(
        model="deepseek-r1-distill-llama-70b",
        temperature=0.2,
        max_tokens=2048,
        streaming=True,
        api_key=os.getenv("GROQ_API_KEY")
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
    if graph is None and os.getenv("GROQ_API_KEY"):
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
                logger.info(f"📡 SSE Event received: {list(event.keys())}")
                if "messages" in event:
                    current_messages = event["messages"]
                    logger.info(f"📡 Total messages in event: {len(current_messages)}")
                    
                    # Process only new messages
                    new_messages = current_messages[processed_count:]
                    logger.info(f"📡 New messages to process: {len(new_messages)}")
                    
                    for i, msg in enumerate(new_messages):
                        logger.info(f"📡 Processing message {i}: {type(msg).__name__}, tool_calls: {getattr(msg, 'tool_calls', None)}")
                        logger.info(f"📡 Message content preview: {getattr(msg, 'content', '')[:100]}")
                        if isinstance(msg, AIMessage):
                            if msg.tool_calls:
                                # AI message with tool calls - send the content
                                logger.info(f"Sending ai_message with tool calls: {msg.content[:100]}")
                                stream_data = {
                                    "type": "ai_message",
                                    "content": msg.content,
                                    "has_tool_calls": True
                                }
                                yield f"data: {json.dumps(stream_data, ensure_ascii=False)}\n\n"
                            else:
                                # Final AI message without tool calls
                                logger.info(f"Sending ai_message_final: {msg.content[:100]}")
                                stream_data = {
                                    "type": "ai_message_final", 
                                    "content": msg.content,
                                    "has_tool_calls": False
                                }
                                yield f"data: {json.dumps(stream_data, ensure_ascii=False)}\n\n"
                        
                        elif isinstance(msg, ToolMessage):
                            # Tool result - send chart data
                            logger.info(f"🔍 DEBUGGING: Received ToolMessage")
                            logger.info(f"🔍 Tool content length: {len(msg.content)}")
                            logger.info(f"🔍 Tool content preview: {msg.content[:300]}")
                            logger.info(f"🔍 Tool content type: {type(msg.content)}")
                            
                            if "Error:" in msg.content:
                                logger.error(f"🔍 Tool execution failed: {msg.content}")
                                continue
                                
                            try:
                                tool_result = json.loads(msg.content)
                                logger.info(f"🔍 JSON parsing SUCCESS")
                                logger.info(f"🔍 Tool result keys: {list(tool_result.keys()) if isinstance(tool_result, dict) else 'Not a dict'}")
                                
                                stream_data = {
                                    "type": "tool_result",
                                    "chart_data": tool_result
                                }
                                logger.info("🔍 Sending tool_result via SSE")
                                yield f"data: {json.dumps(stream_data, ensure_ascii=False)}\n\n"
                                
                            except json.JSONDecodeError as e:
                                logger.error(f"🔍 JSON parsing FAILED: {e}")
                                logger.error(f"🔍 Raw tool content: {repr(msg.content[:500])}")
                            except Exception as e:
                                logger.error(f"🔍 Other error processing tool result: {e}")
                                logger.error(f"🔍 Tool content: {msg.content[:500]}")
                    
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


@app.get("/debug/logs")
async def get_debug_logs():
    """Get recent debug logs"""
    try:
        with open(log_filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Return last 50 lines
            recent_logs = lines[-50:] if len(lines) > 50 else lines
            return {"logs": recent_logs, "total_lines": len(lines), "log_file": log_filename}
    except FileNotFoundError:
        return {"logs": [], "total_lines": 0, "log_file": log_filename}


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