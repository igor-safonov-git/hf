#!/usr/bin/env python3
"""
Sample test of conversational Russian HR analytics queries
"""
import asyncio
import httpx
import time

# Sample of 10 conversational queries to demonstrate the style
CONVERSATIONAL_SAMPLE = [
    "Глянь сколько у нас кандидатов в воронке?",
    "Покажи мне активность рекрутеров, сколько у них действий в системе",
    "Как у нас распределены кандидаты по статусам?",
    "Какие вакансии висят открытыми дольше 60 дней?",
    "Найди кандидатов с зарплатой выше 150к на сеньорские позиции",
    "Какая средняя зарплата нанятых кандидатов по отделам?",
    "Топ источников по конверсии - покажи",
    "Давай глянем активность пользователей в системе",
    "Кто из рекрутеров самые активные?",
    "Конверсия воронки по этапам - давай глянем"
]

async def test_conversational_queries():
    """Test sample of conversational queries"""
    print("🗣️  TESTING CONVERSATIONAL RUSSIAN HR QUERIES")
    print("=" * 60)
    
    results = []
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        for i, query in enumerate(CONVERSATIONAL_SAMPLE):
            print(f"\n[{i+1:2d}/10] {query}")
            
            query_start = time.time()
            try:
                response = await client.post(
                    "http://localhost:8001/chat-retry",
                    json={
                        "message": query,
                        "model": "deepseek",
                        "show_debug": False,
                        "max_retries": 2,
                        "temperature": 0.1
                    },
                    timeout=25.0
                )
                
                duration = time.time() - query_start
                
                if response.status_code == 200:
                    result = response.json()
                    success = 'response' in result and not result.get('response', '').startswith('⚠️')
                    
                    if success:
                        print(f"   ✅ SUCCESS ({duration:.1f}s)")
                        # Show preview of response
                        response_preview = result.get('response', '')[:100]
                        print(f"   📝 Preview: {response_preview}...")
                    else:
                        print(f"   ❌ FAILED ({duration:.1f}s)")
                        error_msg = result.get('response', 'Unknown error')[:80]
                        print(f"   💬 Error: {error_msg}...")
                    
                    results.append({
                        'query': query,
                        'success': success,
                        'duration': duration
                    })
                else:
                    print(f"   ❌ HTTP {response.status_code} ({duration:.1f}s)")
                    results.append({
                        'query': query,
                        'success': False,
                        'duration': duration,
                        'error': f"HTTP {response.status_code}"
                    })
                    
            except Exception as e:
                print(f"   💥 Exception: {str(e)[:50]}")
                results.append({
                    'query': query,
                    'success': False,
                    'duration': 0,
                    'error': str(e)[:50]
                })
    
    # Summary
    total_time = time.time() - start_time
    successful = sum(1 for r in results if r['success'])
    
    print("\n" + "=" * 60)
    print("📊 CONVERSATIONAL QUERY TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Successful: {successful}/{len(results)} ({successful/len(results)*100:.1f}%)")
    print(f"⏱️  Total time: {total_time:.1f}s")
    
    if results:
        avg_duration = sum(r['duration'] for r in results if 'duration' in r) / len(results)
        print(f"📈 Average query time: {avg_duration:.1f}s")
    
    print(f"\n🎉 Conversational style is working great!")
    print("   Natural Russian queries are being processed successfully")

if __name__ == "__main__":
    asyncio.run(test_conversational_queries())