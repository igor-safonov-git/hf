#!/usr/bin/env python3
"""
Integration test for the retry mechanism with real API calls
"""
import asyncio
import json
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import chat_endpoint_with_retry


async def test_retry_with_logs_entity():
    """Test the retry mechanism with a query that triggers 'logs' entity error"""
    print("\n🧪 Testing: Query that uses invalid 'logs' entity")
    print("Query: 'Какой менеджер оставляет больше всего комментариев?'")
    
    result = await chat_endpoint_with_retry(
        message="Какой менеджер оставляет больше всего комментариев?",
        model="deepseek",
        temperature=0.1,
        max_retries=2,
        show_debug=True,
        use_real_data=False
    )
    
    print(f"\n📊 Results:")
    print(f"- Attempts: {result['attempts']}")
    print(f"- Success: {result.get('validation_success', False)}")
    
    if 'conversation_log' in result:
        print("\n📝 Conversation Log:")
        for i, msg in enumerate(result['conversation_log']):
            print(f"  {i+1}. {msg}")
    
    if 'error' in result:
        print(f"\n❌ Final Error: {result['error']}")
    elif 'response' in result:
        print(f"\n✅ Final Response: {result['response'][:200]}...")
    
    return result


async def test_retry_with_field_error():
    """Test with a query that uses invalid field"""
    print("\n\n🧪 Testing: Query that uses invalid field 'stay_duration' on vacancies")
    print("Query: 'Какие вакансии закрываются быстрее всего используя stay_duration'")
    
    result = await chat_endpoint_with_retry(
        message="Какие вакансии закрываются быстрее всего используя stay_duration поле",
        model="deepseek",
        temperature=0.1,
        max_retries=2,
        show_debug=True,
        use_real_data=False
    )
    
    print(f"\n📊 Results:")
    print(f"- Attempts: {result['attempts']}")
    print(f"- Success: {result.get('validation_success', False)}")
    
    if 'conversation_log' in result:
        print("\n📝 Key Log Entries:")
        for msg in result['conversation_log']:
            if any(keyword in str(msg) for keyword in ['❌', '✅', '🔧', 'FIELD ERROR']):
                print(f"  - {msg[:150]}...")


async def test_successful_query():
    """Test with a query that should succeed on first attempt"""
    print("\n\n🧪 Testing: Valid query that should succeed immediately")
    print("Query: 'Сколько кандидатов в системе'")
    
    result = await chat_endpoint_with_retry(
        message="Сколько кандидатов в системе",
        model="deepseek", 
        temperature=0.1,
        max_retries=2,
        show_debug=True,
        use_real_data=False
    )
    
    print(f"\n📊 Results:")
    print(f"- Attempts: {result['attempts']}")
    print(f"- Success: {result.get('validation_success', False)}")
    
    if result['attempts'] == 1:
        print("✅ Succeeded on first attempt as expected!")
    else:
        print("⚠️ Took multiple attempts - unexpected")


async def main():
    """Run all integration tests"""
    print("=" * 60)
    print("RETRY MECHANISM INTEGRATION TESTS")
    print("=" * 60)
    
    # Test 1: Logs entity error
    await test_retry_with_logs_entity()
    
    # Test 2: Field error
    await test_retry_with_field_error()
    
    # Test 3: Successful query
    await test_successful_query()
    
    print("\n" + "=" * 60)
    print("TESTS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())