#!/usr/bin/env python3
"""
Final test results summary for the retry mechanism
"""
import asyncio
import httpx
import time
import json

# 25 strategically chosen queries representing all challenge categories
STRATEGIC_TEST_QUERIES = [
    # Invalid entities (5 queries)
    "Какие комментарии оставляют менеджеры по отклоненным кандидатам?",
    "Покажи активность рекрутеров по количеству действий в системе", 
    "Какие logs содержат информацию об отказах?",
    "Анализ rejection reasons по частоте использования",
    "Статистика по webhook событиям",
    
    # Invalid fields (5 queries)  
    "Покажи среднее stay_duration для вакансий по отделам",
    "Какие кандидаты имеют removed статус?",
    "Анализ order поля для всех вакансий",
    "Покажи permissions всех пользователей",
    "Какие вакансии имеют blocks в описании?",
    
    # Missing group_by (5 queries)
    "Распределение кандидатов по статусам",
    "Топ источников по количеству кандидатов", 
    "Распределение вакансий по приоритетам",
    "Топ рекрутеров по активности",
    "Распределение офферов по статусам",
    
    # Complex time-based (5 queries)
    "Сравни эффективность рекрутеров за Q1 и Q2",
    "Какие вакансии открыты дольше 60 дней?",
    "Покажи динамику найма по месяцам текущего года",
    "Кандидаты, добавленные за последние 2 недели", 
    "Анализ сезонности по кварталам",
    
    # Complex business logic (5 queries)
    "Кандидаты с зарплатой выше 150000 на senior позиции",
    "Средняя зарплата нанятых кандидатов по отделам",
    "Процент конверсии по каждому источнику",
    "ROI источников с учетом стоимости привлечения",
    "Корреляция между приоритетом и скоростью закрытия"
]


async def run_comprehensive_test():
    """Run comprehensive test with detailed analysis"""
    print("🎯 FINAL COMPREHENSIVE RETRY MECHANISM TEST")
    print("=" * 80)
    print(f"📅 Start: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔢 Testing {len(STRATEGIC_TEST_QUERIES)} strategic queries")
    print("=" * 80)
    
    results = []
    category_results = {
        "Invalid entities": [],
        "Invalid fields": [], 
        "Missing group_by": [],
        "Complex time-based": [],
        "Complex business": []
    }
    
    categories = [
        ("Invalid entities", 0, 5),
        ("Invalid fields", 5, 10),
        ("Missing group_by", 10, 15), 
        ("Complex time-based", 15, 20),
        ("Complex business", 20, 25)
    ]
    
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        for i, query in enumerate(STRATEGIC_TEST_QUERIES):
            print(f"\n[{i+1:2d}/25] {query[:70]}...")
            
            query_start = time.time()
            try:
                response = await client.post(
                    "http://localhost:8001/chat-retry",
                    json={
                        "message": query,
                        "model": "deepseek", 
                        "show_debug": True,  # Get full details for analysis
                        "max_retries": 2,
                        "temperature": 0.1
                    },
                    timeout=25.0
                )
                
                duration = time.time() - query_start
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Analyze result
                    success = result.get('validation_success', False)
                    attempts = result.get('attempts', 1)
                    had_retry = attempts > 1
                    conversation_log = result.get('conversation_log', [])
                    
                    # Extract retry reason if any
                    retry_reason = ""
                    if had_retry:
                        for log in conversation_log:
                            if "❌ Validation Failed:" in log:
                                retry_reason = log.split("❌ Validation Failed:")[-1].strip()[:100]
                                break
                    
                    # Categorize result
                    for cat_name, start_idx, end_idx in categories:
                        if start_idx <= i < end_idx:
                            category_results[cat_name].append({
                                'success': success,
                                'had_retry': had_retry,
                                'duration': duration
                            })
                            break
                    
                    # Print result
                    status = "✅ SUCCESS" if success else "❌ FAILED"
                    if had_retry:
                        status += f" (retry: {attempts} attempts)"
                    
                    print(f"    {status} | {duration:.1f}s")
                    if retry_reason:
                        print(f"    🔧 Retry reason: {retry_reason}")
                    
                    results.append({
                        'query': query,
                        'success': success,
                        'attempts': attempts,
                        'duration': duration,
                        'had_retry': had_retry,
                        'retry_reason': retry_reason
                    })
                    
                else:
                    print(f"    ❌ HTTP {response.status_code} | {duration:.1f}s")
                    results.append({
                        'query': query,
                        'success': False,
                        'duration': duration,
                        'error': f"HTTP {response.status_code}"
                    })
                    
            except Exception as e:
                print(f"    💥 ERROR: {str(e)[:50]} | {time.time() - query_start:.1f}s")
                results.append({
                    'query': query,
                    'success': False,
                    'duration': 0,
                    'error': str(e)
                })
    
    total_time = time.time() - start_time
    
    # Generate comprehensive analysis
    print("\n" + "=" * 80)
    print("📊 FINAL ANALYSIS")
    print("=" * 80)
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    with_retry = [r for r in results if r.get('had_retry')]
    
    print(f"\n🎯 Overall Performance:")
    print(f"   Total queries: {len(results)}")
    print(f"   ✅ Successful: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
    print(f"   ❌ Failed: {len(failed)} ({len(failed)/len(results)*100:.1f}%)")
    print(f"   🔄 Required retry: {len(with_retry)} ({len(with_retry)/len(results)*100:.1f}%)")
    print(f"   ⏱️  Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    
    # Category analysis
    print(f"\n📋 Category Performance:")
    for category, cat_results in category_results.items():
        if cat_results:
            success_rate = sum(1 for r in cat_results if r['success']) / len(cat_results)
            retry_rate = sum(1 for r in cat_results if r.get('had_retry')) / len(cat_results)
            avg_duration = sum(r['duration'] for r in cat_results) / len(cat_results)
            
            print(f"   {category:20s}: {success_rate*100:5.1f}% success | {retry_rate*100:5.1f}% retry | {avg_duration:5.1f}s avg")
    
    # Retry analysis
    if with_retry:
        print(f"\n🔄 Retry Pattern Analysis:")
        retry_categories = {}
        for r in with_retry:
            reason = r.get('retry_reason', '')
            if 'Invalid entity' in reason:
                category = 'Invalid entity usage'
            elif 'Field' in reason and 'not valid' in reason:
                category = 'Invalid field usage'  
            elif 'group_by' in reason.lower():
                category = 'Missing group_by'
            elif 'Schema' in reason:
                category = 'Schema/structure error'
            else:
                category = 'Other validation error'
                
            retry_categories[category] = retry_categories.get(category, 0) + 1
        
        for category, count in sorted(retry_categories.items(), key=lambda x: x[1], reverse=True):
            print(f"   - {category}: {count} times")
    
    # Performance insights
    durations = [r['duration'] for r in results if 'duration' in r and r['duration'] > 0]
    if durations:
        print(f"\n⚡ Performance Insights:")
        print(f"   Average query time: {sum(durations)/len(durations):.1f}s")
        print(f"   Fastest query: {min(durations):.1f}s")
        print(f"   Slowest query: {max(durations):.1f}s")
        
        if with_retry:
            retry_durations = [r['duration'] for r in with_retry if 'duration' in r]
            no_retry_durations = [r['duration'] for r in results if not r.get('had_retry') and 'duration' in r and r['duration'] > 0]
            
            if retry_durations and no_retry_durations:
                print(f"   With retry avg: {sum(retry_durations)/len(retry_durations):.1f}s")
                print(f"   No retry avg: {sum(no_retry_durations)/len(no_retry_durations):.1f}s")
                overhead = (sum(retry_durations)/len(retry_durations)) - (sum(no_retry_durations)/len(no_retry_durations))
                print(f"   Retry overhead: +{overhead:.1f}s per retry")
    
    # Save results
    final_report = {
        'test_info': {
            'total_queries': len(results),
            'test_duration': total_time,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        },
        'summary': {
            'success_rate': len(successful)/len(results)*100,
            'retry_rate': len(with_retry)/len(results)*100,
            'average_duration': sum(durations)/len(durations) if durations else 0
        },
        'category_performance': {
            cat: {
                'success_rate': sum(1 for r in results if r['success']) / len(results) * 100,
                'retry_rate': sum(1 for r in results if r.get('had_retry')) / len(results) * 100
            } for cat, results in category_results.items()
        },
        'detailed_results': results
    }
    
    with open('final_comprehensive_test.json', 'w', encoding='utf-8') as f:
        json.dump(final_report, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Complete results saved to final_comprehensive_test.json")
    print(f"\n🎉 RETRY MECHANISM VALIDATION COMPLETE!")
    print(f"   The system successfully handles {len(successful)}/{len(results)} queries")
    print(f"   With automatic retry fixing {len(with_retry)} problematic queries")
    print(f"✅ Test completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(run_comprehensive_test())