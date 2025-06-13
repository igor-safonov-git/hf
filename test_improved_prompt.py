#!/usr/bin/env python3
"""
Test the improved prompt with problematic query
"""
import asyncio
import httpx
import time

async def test_single_query():
    """Test the specific problematic query with improved prompt"""
    query = "Покажи среднее stay_duration для вакансий по отделам"
    
    print(f"🔍 Testing improved prompt with query: {query}")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            start_time = time.time()
            
            response = await client.post(
                "http://localhost:8001/chat-retry",
                json={
                    "message": query,
                    "model": "deepseek",
                    "show_debug": True,
                    "max_retries": 2,
                    "temperature": 0.1
                },
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                success = result.get('validation_success', False)
                attempts = result.get('attempts', 1)
                conversation_log = result.get('conversation_log', [])
                
                print(f"✅ Response received after {duration:.1f}s")
                print(f"📊 Success: {success} | Attempts: {attempts}")
                
                print(f"\n📋 Conversation Log:")
                for i, log in enumerate(conversation_log):
                    if "🔵 User:" in log:
                        print(f"  {log}")
                    elif "🤖 AI Attempt" in log:
                        # Show just the first part of AI response
                        ai_response = log[log.find(":")+1:].strip()
                        print(f"  🤖 AI Attempt {i}: {ai_response[:100]}...")
                    elif "❌ Validation Failed:" in log:
                        error = log.split("❌ Validation Failed:")[-1].strip()
                        print(f"  ❌ Validation Error: {error}")
                    elif "✅ Validation: SUCCESS" in log:
                        print(f"  ✅ VALIDATION PASSED!")
                    elif "🔧 Error Feedback:" in log:
                        print(f"  🔧 AI received error feedback")
                        
                if success:
                    print(f"\n🎉 SUCCESS: Improved prompt fixed the query!")
                    print(f"   The AI now handles this problematic pattern correctly")
                else:
                    print(f"\n❌ STILL FAILING: Need further prompt improvements")
                    
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
    except Exception as e:
        print(f"💥 Exception: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_single_query())