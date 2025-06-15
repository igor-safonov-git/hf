#!/usr/bin/env python3
"""
Test the new impossible query response mechanism
"""
import asyncio
import json
import httpx
from datetime import datetime

# Test queries that should trigger impossible query responses
IMPOSSIBLE_QUERIES = [
    "Какой у нас гендерный баланс среди нанятых сотрудников?",
    "Покажи уровень английского у наших кандидатов",
    "Анализ изменений в резюме кандидатов за месяц",
    "Сколько времени рекрутер тратит на каждую вакансию?",
    "Статистика по внутренним перемещениям сотрудников",
    "Webhook события за последнюю неделю",
    "Заполненные анкеты кандидатов",
    "История изменений статусов по кандидатам"
]

async def test_impossible_query(client: httpx.AsyncClient, query: str) -> dict:
    """Test a single impossible query"""
    try:
        response = await client.post(
            "http://localhost:8001/chat-retry",
            json={
                "message": query,
                "model": "deepseek",
                "show_debug": True,
                "max_retries": 1,
                "temperature": 0.1,
                "use_real_data": False
            },
            timeout=20.0
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "query": query,
                "success": True,
                "query_type": result.get("query_type", "unknown"),
                "response": result.get("response", "")[:200] + "..." if len(result.get("response", "")) > 200 else result.get("response", ""),
                "conversation_log": result.get("conversation_log", [])
            }
        else:
            return {
                "query": query,
                "success": False,
                "error": f"HTTP {response.status_code}"
            }
    except Exception as e:
        return {
            "query": query,
            "success": False,
            "error": str(e)
        }

async def main():
    """Test impossible query mechanism"""
    print("🧪 Testing Impossible Query Response Mechanism")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        results = []
        
        for i, query in enumerate(IMPOSSIBLE_QUERIES, 1):
            print(f"Testing {i}/{len(IMPOSSIBLE_QUERIES)}: {query[:50]}...")
            result = await test_impossible_query(client, query)
            results.append(result)
            
            if result["success"]:
                query_type = result.get("query_type", "normal")
                status = "✅ IMPOSSIBLE" if query_type == "impossible" else "❌ NORMAL"
                print(f"  {status}")
            else:
                print(f"  💥 ERROR: {result.get('error', 'Unknown')}")
            
            await asyncio.sleep(0.5)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    
    impossible_count = sum(1 for r in results if r.get("query_type") == "impossible")
    successful_count = sum(1 for r in results if r.get("success", False))
    
    print(f"Total queries: {len(results)}")
    print(f"Successful: {successful_count}")
    print(f"Correctly identified as impossible: {impossible_count}")
    print(f"Success rate: {impossible_count}/{len(results)} = {impossible_count/len(results)*100:.1f}%")
    
    # Detailed results
    print(f"\n📋 DETAILED RESULTS:")
    for result in results:
        if result["success"]:
            query_type = result.get("query_type", "normal")
            icon = "✅" if query_type == "impossible" else "❌"
            print(f"{icon} {result['query'][:60]}...")
            if query_type == "impossible":
                print(f"   Response: {result['response'][:100]}...")
        else:
            print(f"💥 {result['query'][:60]}... (ERROR: {result.get('error', 'Unknown')})")
    
    # Save results
    with open('impossible_query_test_results.json', 'w', encoding='utf-8') as f:
        json.dump({
            'test_time': datetime.now().isoformat(),
            'summary': {
                'total': len(results),
                'successful': successful_count,
                'impossible_detected': impossible_count,
                'success_rate': impossible_count/len(results)*100
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Results saved to impossible_query_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())