#!/usr/bin/env python3
"""
Test 100 challenging HR analytics queries to validate the retry mechanism
and overall system robustness.
"""
import asyncio
import json
import httpx
from datetime import datetime, timedelta
import random

# Challenging queries that test various aspects of the system
CHALLENGING_QUERIES = [
    # 1-10: Complex time-based queries
    "Сравни эффективность рекрутеров за последние 3 месяца с предыдущими 3 месяцами по конверсии в найм",
    "Какая динамика времени закрытия вакансий по кварталам текущего года?",
    "Покажи топ-5 источников кандидатов за последние 30 дней с конверсией выше 20%",
    "Сколько кандидатов мы наняли за последние 2 недели из разных источников?",
    "Какие вакансии открыты дольше 60 дней и почему?",
    "Сравни скорость найма между отделами за последний год",
    "Какая средняя зарплата нанятых кандидатов по месяцам за последние полгода?",
    "Покажи воронку найма за вчерашний день по часам",
    "Какие рекрутеры закрыли больше всего вакансий за последнюю неделю?",
    "Сколько кандидатов отказались от оффера за последние 45 дней?",
    
    # 11-20: Multi-criteria filtering
    "Найди кандидатов с зарплатными ожиданиями от 100000 до 150000 на позиции разработчика",
    "Покажи вакансии с приоритетом 1, открытые больше месяца, по которым меньше 5 кандидатов",
    "Какие источники приводят кандидатов с зарплатой выше 200000 на технические позиции?",
    "Сколько кандидатов из LinkedIn дошли до оффера на senior позиции?",
    "Найди рекрутеров, которые работают с вакансиями приоритета 1 и имеют конверсию ниже 10%",
    "Покажи кандидатов, которые были отклонены на этапе технического интервью за последний месяц",
    "Какие вакансии в IT отделе имеют больше 20 кандидатов в работе?",
    "Найди источники с конверсией выше 30% для вакансий с зарплатой выше 150000",
    "Сколько кандидатов с опытом больше 5 лет мы рассматриваем сейчас?",
    "Покажи активные вакансии без назначенного рекрутера с высоким приоритетом",
    
    # 21-30: Complex aggregations and calculations
    "Какая средняя скорость прохождения каждого этапа воронки найма?",
    "Рассчитай ROI каждого источника кандидатов с учетом стоимости и конверсии",
    "Какой процент кандидатов отваливается на каждом этапе воронки?",
    "Покажи медианную зарплату по каждому отделу среди нанятых",
    "Какая корреляция между временем закрытия вакансии и количеством кандидатов?",
    "Рассчитай среднее время от первого контакта до оффера по источникам",
    "Какой процент вакансий закрывается в срок по отделам?",
    "Покажи распределение кандидатов по зарплатным ожиданиям с шагом 50000",
    "Какая средняя конверсия из просмотра резюме в приглашение на интервью?",
    "Рассчитай стоимость найма одного сотрудника по источникам",
    
    # 31-40: Russian terminology and business logic
    "Покажи воронку найма с группировкой по хантерам",
    "Какие соискатели находятся в статусе 'думает над оффером'?",
    "Сколько отказов по причине 'не устроила зарплата' за последний квартал?",
    "Покажи конверсию от скрининга до технического собеседования",
    "Какие вакансии находятся на холде и почему?",
    "Сколько кандидатов мы потеряли из-за долгого принятия решения?",
    "Покажи эффективность работы с рекомендациями сотрудников",
    "Какой процент кандидатов проваливает тестовое задание?",
    "Сколько вакансий закрыто по причине 'нашли внутреннего кандидата'?",
    "Покажи динамику отказов кандидатов по месяцам",
    
    # 41-50: Edge cases and potential errors
    "Какие комментарии оставляют менеджеры по отклоненным кандидатам?",
    "Покажи активность рекрутеров по количеству действий в системе",
    "Сколько дубликатов кандидатов в базе и как они распределены?",
    "Какие вакансии не имеют описания или требований?",
    "Покажи историю изменения статусов по конкретному кандидату",
    "Какие источники не приводили кандидатов последние 3 месяца?",
    "Найди вакансии с нулевым количеством просмотров за неделю",
    "Покажи кандидатов без контактной информации",
    "Какие рекрутеры не закрыли ни одной вакансии за последние 2 месяца?",
    "Найди вакансии с некорректными зарплатными вилками",
    
    # 51-60: Performance and efficiency metrics
    "Рассчитай производительность каждого рекрутера по закрытым вакансиям в месяц",
    "Какая средняя нагрузка на рекрутера по активным вакансиям?",
    "Покажи эффективность источников по стоимости привлечения одного кандидата",
    "Какой рекрутер имеет лучшее соотношение скорости и качества найма?",
    "Сравни производительность команд рекрутинга по отделам",
    "Какая оптимальная нагрузка на рекрутера для максимальной эффективности?",
    "Покажи тренд производительности рекрутеров за последние 6 месяцев",
    "Какие источники дают лучшее качество кандидатов при минимальных затратах?",
    "Рассчитай среднее количество интервью на одного нанятого",
    "Какая команда имеет лучшие показатели по времени закрытия вакансий?",
    
    # 61-70: Comparative analysis
    "Сравни качество кандидатов из разных источников по проценту прохождения интервью",
    "Какой источник лучше для найма junior vs senior специалистов?",
    "Сравни эффективность найма между Москвой и регионами",
    "Какие отделы быстрее всего принимают решения по кандидатам?",
    "Сравни зарплатные ожидания кандидатов по источникам привлечения",
    "Какой канал привлечения эффективнее для массовых позиций?",
    "Сравни время закрытия вакансий между техническими и административными позициями",
    "Какие рекрутеры лучше работают с senior позициями?",
    "Сравни конверсию в найм между внутренними и внешними кандидатами",
    "Какой источник дает кандидатов с наименьшим процентом отказов от офферов?",
    
    # 71-80: Predictive and trend analysis
    "Какой прогноз закрытия текущих вакансий based on исторических данных?",
    "Покажи тренд изменения зарплатных ожиданий кандидатов за последний год",
    "Какие позиции станут наиболее востребованными в следующем квартале?",
    "Спрогнозируй количество необходимых рекрутеров на следующий месяц",
    "Какой тренд по времени закрытия вакансий в IT департаменте?",
    "Покажи сезонность в количестве откликов кандидатов",
    "Какие источники показывают растущую эффективность?",
    "Спрогнозируй процент принятия офферов на следующий месяц",
    "Какой тренд по количеству отказов на разных этапах воронки?",
    "Покажи динамику изменения требований к кандидатам за последний год",
    
    # 81-90: Complex business questions
    "Какие вакансии требуют пересмотра зарплатной вилки based on рыночных данных?",
    "Оцени эффективность реферальной программы по привлечению кандидатов",
    "Какие компетенции наиболее сложно найти на рынке сейчас?",
    "Покажи анализ причин отказов кандидатов с разбивкой по этапам",
    "Какие улучшения в процессе найма дадут максимальный эффект?",
    "Оцени влияние скорости обратной связи на процент принятия офферов",
    "Какие этапы воронки найма требуют оптимизации в первую очередь?",
    "Покажи корреляцию между источником кандидата и его успешностью после найма",
    "Какие метрики найма коррелируют с долгосрочной успешностью сотрудников?",
    "Оцени ROI инвестиций в различные каналы привлечения кандидатов",
    
    # 91-100: Edge cases and stress tests
    "Покажи все метрики по вакансиям, которые были переоткрыты после закрытия",
    "Какие кандидаты проходили собеседование больше 3 раз на разные позиции?",
    "Найди аномалии в данных по времени прохождения этапов найма",
    "Покажи кандидатов, которые были наняты, уволены и снова наняты",
    "Какие вакансии имеют подозрительно высокую конверсию?",
    "Найди все случаи, когда кандидат был принят без прохождения всех этапов",
    "Покажи статистику по кандидатам, которые отказались после принятия оффера",
    "Какие источники имеют 100% конверсию (возможная ошибка данных)?",
    "Найди вакансии с противоречивыми данными по статусам",
    "Покажи все нестандартные случаи в процессе найма за последний месяц"
]


async def test_query(client: httpx.AsyncClient, query: str, index: int) -> dict:
    """Test a single query and return results"""
    print(f"\n{'='*60}")
    print(f"Query {index + 1}/100: {query}")
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
            if had_retry:
                for log in conversation_log:
                    if "❌ Validation Failed:" in log:
                        retry_reason = log.split("❌ Validation Failed:")[-1].strip()
                        break
            
            # Extract final response structure
            final_response = {}
            if 'response' in result:
                try:
                    final_response = json.loads(result['response'])
                except:
                    final_response = {"error": "Failed to parse response"}
            
            return {
                "query": query,
                "success": success,
                "attempts": attempts,
                "had_retry": had_retry,
                "retry_reason": retry_reason,
                "duration": duration,
                "entities_used": extract_entities(final_response),
                "operations_used": extract_operations(final_response),
                "has_grouping": check_grouping(final_response),
                "has_filtering": check_filtering(final_response),
                "response_structure": get_response_structure(final_response)
            }
        else:
            return {
                "query": query,
                "success": False,
                "error": f"HTTP {response.status_code}",
                "duration": duration
            }
            
    except Exception as e:
        return {
            "query": query,
            "success": False,
            "error": str(e),
            "duration": 0
        }


def extract_entities(response: dict) -> set:
    """Extract all entities used in the response"""
    entities = set()
    
    def extract_from_value(value):
        if isinstance(value, dict):
            if 'entity' in value:
                entities.add(value['entity'])
            for v in value.values():
                if isinstance(v, (dict, list)):
                    extract_from_value(v)
        elif isinstance(value, list):
            for item in value:
                extract_from_value(item)
    
    extract_from_value(response)
    return entities


def extract_operations(response: dict) -> set:
    """Extract all operations used in the response"""
    operations = set()
    
    def extract_from_value(value):
        if isinstance(value, dict):
            if 'operation' in value:
                operations.add(value['operation'])
            for v in value.values():
                if isinstance(v, (dict, list)):
                    extract_from_value(v)
        elif isinstance(value, list):
            for item in value:
                extract_from_value(item)
    
    extract_from_value(response)
    return operations


def check_grouping(response: dict) -> bool:
    """Check if response uses grouping"""
    def has_group_by(value):
        if isinstance(value, dict):
            if 'group_by' in value and value['group_by']:
                return True
            for v in value.values():
                if isinstance(v, (dict, list)) and has_group_by(v):
                    return True
        elif isinstance(value, list):
            for item in value:
                if has_group_by(item):
                    return True
        return False
    
    return has_group_by(response)


def check_filtering(response: dict) -> bool:
    """Check if response uses filtering"""
    def has_filter(value):
        if isinstance(value, dict):
            if 'filter' in value and value['filter']:
                return True
            for v in value.values():
                if isinstance(v, (dict, list)) and has_filter(v):
                    return True
        elif isinstance(value, list):
            for item in value:
                if has_filter(item):
                    return True
        return False
    
    return has_filter(response)


def get_response_structure(response: dict) -> str:
    """Get a simple description of response structure"""
    if 'error' in response:
        return "error"
    elif 'report_title' in response:
        metrics_count = len(response.get('secondary_metrics', []))
        return f"report_with_{metrics_count}_secondary_metrics"
    else:
        return "unknown"


async def main():
    """Run all 100 tests"""
    print("🚀 Starting 100 Challenging HR Analytics Queries Test")
    print(f"Time: {datetime.now()}")
    print("="*80)
    
    async with httpx.AsyncClient() as client:
        results = []
        
        # Test queries in batches to avoid overwhelming the system
        batch_size = 10
        for i in range(0, len(CHALLENGING_QUERIES), batch_size):
            batch = CHALLENGING_QUERIES[i:i+batch_size]
            batch_results = []
            
            for j, query in enumerate(batch):
                result = await test_query(client, query, i + j)
                results.append(result)
                batch_results.append(result)
                
                # Brief summary after each query
                if result['success']:
                    status = "✅ SUCCESS"
                    if result['had_retry']:
                        status += f" (after {result['attempts']} attempts)"
                else:
                    status = "❌ FAILED"
                    
                print(f"\n{status} | Duration: {result['duration']:.2f}s")
                if result.get('had_retry'):
                    print(f"Retry reason: {result['retry_reason'][:100]}...")
                if result.get('entities_used'):
                    print(f"Entities: {', '.join(result['entities_used'])}")
            
            # Brief pause between batches
            if i + batch_size < len(CHALLENGING_QUERIES):
                print(f"\n⏸️  Completed batch {i//batch_size + 1}, pausing briefly...")
                await asyncio.sleep(2)
    
    # Generate summary report
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    with_retry = [r for r in results if r.get('had_retry')]
    
    print(f"\nTotal queries: {len(results)}")
    print(f"✅ Successful: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
    print(f"❌ Failed: {len(failed)} ({len(failed)/len(results)*100:.1f}%)")
    print(f"🔄 Required retry: {len(with_retry)} ({len(with_retry)/len(results)*100:.1f}%)")
    
    # Analyze retry reasons
    if with_retry:
        print(f"\n🔄 Retry Analysis:")
        retry_reasons = {}
        for r in with_retry:
            reason = r.get('retry_reason', 'Unknown')
            # Categorize retry reasons
            if 'Invalid entity' in reason:
                category = 'Invalid entity'
            elif 'Field' in reason and 'not valid' in reason:
                category = 'Invalid field'
            elif 'group_by' in reason:
                category = 'Missing group_by'
            elif 'Schema' in reason:
                category = 'Schema error'
            else:
                category = 'Other'
                
            retry_reasons[category] = retry_reasons.get(category, 0) + 1
        
        for reason, count in sorted(retry_reasons.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {reason}: {count} times")
    
    # Analyze entities usage
    all_entities = set()
    for r in successful:
        all_entities.update(r.get('entities_used', set()))
    
    print(f"\n📊 Entities Used:")
    for entity in sorted(all_entities):
        count = sum(1 for r in successful if entity in r.get('entities_used', set()))
        print(f"  - {entity}: {count} times")
    
    # Analyze operations
    all_operations = set()
    for r in successful:
        all_operations.update(r.get('operations_used', set()))
    
    print(f"\n🔧 Operations Used:")
    for op in sorted(all_operations):
        count = sum(1 for r in successful if op in r.get('operations_used', set()))
        print(f"  - {op}: {count} times")
    
    # Performance analysis
    durations = [r['duration'] for r in results if 'duration' in r]
    if durations:
        print(f"\n⏱️  Performance:")
        print(f"  - Average duration: {sum(durations)/len(durations):.2f}s")
        print(f"  - Min duration: {min(durations):.2f}s")
        print(f"  - Max duration: {max(durations):.2f}s")
    
    # Save detailed results
    with open('test_100_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Detailed results saved to test_100_results.json")
    print(f"\n✅ Test completed at {datetime.now()}")


if __name__ == "__main__":
    asyncio.run(main())