#!/usr/bin/env python3
"""
Test 20 most challenging HR analytics queries to validate the retry mechanism
"""
import asyncio
import json
import httpx
from datetime import datetime
import sys

# 20 most challenging queries that test edge cases
CHALLENGING_QUERIES = [
    # Complex time-based with multiple filters
    "Сравни эффективность рекрутеров за последние 3 месяца с предыдущими 3 месяцами по конверсии в найм",
    "Какие вакансии с приоритетом 1 открыты дольше 60 дней и имеют меньше 5 кандидатов?",
    
    # Queries that might trigger "logs" entity
    "Какие комментарии оставляют менеджеры по отклоненным кандидатам?",
    "Покажи активность рекрутеров по количеству действий в системе",
    "Какая история изменения статусов по кандидатам за последнюю неделю?",
    
    # Complex aggregations
    "Рассчитай среднюю скорость прохождения каждого этапа воронки найма",
    "Какой процент кандидатов отваливается на каждом этапе с группировкой по источникам?",
    
    # Salary-based complex queries
    "Покажи распределение кандидатов по зарплатным ожиданиям с шагом 50000 для senior позиций",
    "Кандидаты из каких источников хотят больше денег и почему?",
    
    # Russian terminology edge cases
    "Сколько соискателей находятся в статусе 'думает над оффером' по хантерам?",
    "Покажи конверсию от скрининга до технического собеседования по командам",
    
    # Queries using "stay_duration" incorrectly
    "Какие вакансии закрываются быстрее всего используя stay_duration?",
    "Покажи среднее stay_duration для вакансий по отделам",
    
    # Complex filtering with rejections
    "Почему отваливаются кандидаты на технических интервью в IT отделе?",
    "Анализ причин отказов кандидатов с зарплатой выше 200000",
    
    # Distribution queries that need group_by
    "Распределение кандидатов по статусам",
    "Топ источников по количеству кандидатов",
    
    # Edge cases with multiple entities
    "Сравни производительность рекрутеров по закрытым вакансиям и принятым офферам",
    "Какая корреляция между источником кандидата и временем закрытия вакансии?",
    
    # Very complex business logic
    "Оцени ROI каждого источника с учетом стоимости привлечения, конверсии и средней зарплаты нанятых"
]


async def test_query(client: httpx.AsyncClient, query: str, index: int) -> dict:
    """Test a single query and return results"""
    print(f"\n{'='*60}")
    print(f"Query {index + 1}/20: {query}")
    print('='*60)
    
    start_time = datetime.now()
    
    try:
        response = await client.post(
            "http://localhost:8001/chat-retry",
            json={
                "message": query,
                "model": "deepseek",
                "show_debug": True,
                "max_retries": 2,
                "temperature": 0.1,
                "use_real_data": False
            },
            timeout=60.0
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if response.status_code == 200:
            result = response.json()
            
            # Extract key information
            attempts = result.get('attempts', 0)
            success = result.get('validation_success', False)
            conversation_log = result.get('conversation_log', [])
            
            # Check for retries
            had_retry = attempts > 1
            retry_reason = ""
            error_feedback = ""
            
            if had_retry:
                for i, log in enumerate(conversation_log):
                    if "❌ Validation Failed:" in log:
                        retry_reason = log.split("❌ Validation Failed:")[-1].strip()
                    if "🔧 Error Feedback:" in log:
                        # Get the actual feedback message
                        if i + 1 < len(conversation_log):
                            error_feedback = conversation_log[i].split("🔧 Error Feedback:")[-1].strip()
            
            # Print conversation flow
            print("\n📝 Conversation Flow:")
            for log in conversation_log:
                if any(marker in log for marker in ['🔵', '❌', '✅', '🔧', '🔄', '💀']):
                    # Truncate long messages
                    if len(log) > 150:
                        print(f"  {log[:150]}...")
                    else:
                        print(f"  {log}")
            
            # Extract final response
            final_response = {}
            if 'response' in result:
                try:
                    final_response = json.loads(result['response'])
                except:
                    final_response = {"error": "Failed to parse response"}
            
            # Summary
            status = "✅ SUCCESS" if success else "❌ FAILED"
            if had_retry:
                status += f" (after {attempts} attempts)"
            
            print(f"\n{status} | Duration: {duration:.2f}s")
            
            if had_retry:
                print(f"\n🔄 Retry Details:")
                print(f"  - Reason: {retry_reason[:200]}...")
                if error_feedback:
                    print(f"  - Feedback given: {error_feedback[:200]}...")
            
            return {
                "query": query,
                "success": success,
                "attempts": attempts,
                "had_retry": had_retry,
                "retry_reason": retry_reason,
                "duration": duration,
                "final_response": final_response
            }
        else:
            print(f"\n❌ HTTP Error: {response.status_code}")
            return {
                "query": query,
                "success": False,
                "error": f"HTTP {response.status_code}",
                "duration": duration
            }
            
    except Exception as e:
        print(f"\n❌ Exception: {str(e)}")
        return {
            "query": query,
            "success": False,
            "error": str(e),
            "duration": 0
        }


async def main():
    """Run all 20 tests"""
    print("🚀 Testing 20 Most Challenging HR Analytics Queries")
    print(f"Time: {datetime.now()}")
    print("="*80)
    
    async with httpx.AsyncClient() as client:
        results = []
        
        for i, query in enumerate(CHALLENGING_QUERIES):
            result = await test_query(client, query, i)
            results.append(result)
            
            # Brief pause between queries
            if i < len(CHALLENGING_QUERIES) - 1:
                await asyncio.sleep(1)
    
    # Generate summary report
    print("\n" + "="*80)
    print("📊 FINAL SUMMARY")
    print("="*80)
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    with_retry = [r for r in results if r.get('had_retry')]
    
    print(f"\nTotal queries: {len(results)}")
    print(f"✅ Successful: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
    print(f"❌ Failed: {len(failed)} ({len(failed)/len(results)*100:.1f}%)")
    print(f"🔄 Required retry: {len(with_retry)} ({len(with_retry)/len(results)*100:.1f}%)")
    
    # Analyze retry patterns
    if with_retry:
        print(f"\n🔄 Retry Patterns:")
        retry_categories = {
            'Invalid entity': 0,
            'Invalid field': 0,
            'Missing group_by': 0,
            'Multiple filters': 0,
            'Other': 0
        }
        
        for r in with_retry:
            reason = r.get('retry_reason', '')
            if 'Invalid entity' in reason:
                retry_categories['Invalid entity'] += 1
            elif 'Field' in reason and 'not valid' in reason:
                retry_categories['Invalid field'] += 1
            elif 'group_by' in reason:
                retry_categories['Missing group_by'] += 1
            elif 'filter' in reason and '[' in reason:
                retry_categories['Multiple filters'] += 1
            else:
                retry_categories['Other'] += 1
        
        for category, count in retry_categories.items():
            if count > 0:
                print(f"  - {category}: {count} times")
    
    # Show failed queries
    if failed:
        print(f"\n❌ Failed Queries:")
        for i, r in enumerate(failed):
            print(f"  {i+1}. {r['query'][:80]}...")
            if 'error' in r:
                print(f"     Error: {r['error']}")
    
    # Performance stats
    durations = [r['duration'] for r in results if 'duration' in r and r['duration'] > 0]
    if durations:
        print(f"\n⏱️  Performance Stats:")
        print(f"  - Average duration: {sum(durations)/len(durations):.2f}s")
        print(f"  - Min duration: {min(durations):.2f}s")
        print(f"  - Max duration: {max(durations):.2f}s")
        
        # Separate stats for queries with retry
        retry_durations = [r['duration'] for r in with_retry if 'duration' in r]
        if retry_durations:
            print(f"  - Average duration with retry: {sum(retry_durations)/len(retry_durations):.2f}s")
    
    # Save results
    with open('test_20_challenging_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Detailed results saved to test_20_challenging_results.json")
    print(f"✅ Test completed at {datetime.now()}")


if __name__ == "__main__":
    asyncio.run(main())