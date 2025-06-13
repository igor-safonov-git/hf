#!/usr/bin/env python3
"""
Comprehensive test of 100 challenging HR analytics queries
"""
import asyncio
import json
import httpx
from datetime import datetime
import time

# 100 challenging queries designed to test various edge cases and retry scenarios
COMPREHENSIVE_QUERIES = [
    # 1-15: Invalid entity usage (should trigger retries)
    "Какие комментарии оставляют менеджеры по отклоненным кандидатам?",
    "Покажи активность рекрутеров по количеству действий в системе",
    "Какая история изменения статусов по кандидатам за последнюю неделю?",
    "Сколько записей в логах по каждому рекрутеру?",
    "Покажи все заметки менеджеров по кандидатам",
    "Какие rejection reasons используются чаще всего?",
    "Анализ активности пользователей в системе",
    "Покажи все webhook события за последний месяц",
    "Какие организации создали больше всего вакансий?",
    "Статистика по responses от кандидатов",
    "Какие questionary заполнили кандидаты?",
    "Покажи все status_groups и их использование",
    "Анализ coworkers по отделам",
    "Какие logs содержат информацию об отказах?",
    "Покажи все notes по собеседованиям",
    
    # 16-30: Invalid field usage (should trigger retries)
    "Покажи среднее stay_duration для вакансий по отделам",
    "Какие вакансии имеют максимальное stay_duration?",
    "Анализ stay_duration кандидатов по источникам",
    "Покажи order поля для всех вакансий",
    "Какие кандидаты имеют removed статус?",
    "Анализ type поля для источников кандидатов",
    "Покажи foreign связи между вакансиями",
    "Какие рекрутеры имеют максимальный head показатель?",
    "Анализ meta информации по отделам",
    "Покажи permissions всех пользователей",
    "Какие вакансии имеют blocks в описании?",
    "Анализ vacancy_request для активных позиций",
    "Покажи pdf_url для всех офферов",
    "Какие кандидаты имеют deep связи?",
    "Анализ parent структуры вакансий",
    
    # 31-45: Missing group_by for distribution queries (should trigger retries)
    "Распределение кандидатов по статусам",
    "Топ источников по количеству кандидатов",
    "Распределение вакансий по приоритетам",
    "Топ рекрутеров по активности",
    "Распределение кандидатов по зарплатным ожиданиям",
    "Топ отделов по количеству открытых вакансий",
    "Распределение офферов по статусам",
    "Топ источников по конверсии",
    "Распределение кандидатов по создателям",
    "Топ вакансий по количеству кандидатов",
    "Распределение тегов среди кандидатов",
    "Топ регионов по вакансиям",
    "Распределение кандидатов по возрасту",
    "Топ позиций по популярности",
    "Распределение времени создания вакансий",
    
    # 46-60: Complex time-based queries
    "Сравни эффективность рекрутеров за последние 3 месяца с предыдущими 3 месяцами",
    "Какие вакансии открыты дольше 60 дней?",
    "Покажи динамику найма по месяцам текущего года",
    "Кандидаты, добавленные за последние 2 недели",
    "Вакансии, созданные в понедельник",
    "Сравни конверсию за Q1 и Q2",
    "Какие офферы были сделаны в пятницу?",
    "Анализ сезонности по кварталам",
    "Покажи активность по дням недели",
    "Какие кандидаты были обновлены вчера?",
    "Вакансии, закрытые в выходные",
    "Сравни скорость найма по месяцам",
    "Какие теги добавлены в последний месяц?",
    "Анализ трендов по полугодиям",
    "Покажи пики активности по часам",
    
    # 61-75: Multi-criteria filtering
    "Кандидаты с зарплатой выше 150000 на senior позиции",
    "Вакансии приоритета 1 без назначенного рекрутера",
    "Активные кандидаты из LinkedIn с опытом 5+ лет",
    "Закрытые вакансии с более чем 10 кандидатами",
    "Рекрутеры с конверсией выше 20% в IT отделе",
    "Кандидаты-дубликаты с одинаковым email",
    "Вакансии в Москве с зарплатой выше 200000",
    "Скрытые вакансии с активными кандидатами",
    "Множественные вакансии одного родителя",
    "Кандидаты без фото из рекомендаций",
    "Офферы со статусом принят в IT",
    "Теги красного цвета созданные в 2025",
    "Источники типа referral с высокой конверсией",
    "Отделы с порядком меньше 10 и активные",
    "Кандидаты с внешними данными и соглашениями",
    
    # 76-90: Complex aggregations and calculations
    "Средняя зарплата нанятых кандидатов по отделам",
    "Медианное время от создания до найма",
    "Процент конверсии по каждому источнику",
    "Корреляция между приоритетом и скоростью закрытия",
    "ROI источников с учетом стоимости привлечения",
    "Среднее количество кандидатов на вакансию",
    "Процент принятых офферов по рекрутерам",
    "Стандартное отклонение зарплат по позициям",
    "Коэффициент оборачиваемости кандидатов",
    "Средний возраст кандидатов по источникам",
    "Процент вакансий, закрытых в срок",
    "Средняя нагрузка на рекрутера",
    "Конверсия воронки по этапам",
    "Процент кандидатов с фото",
    "Средняя длина описания вакансий",
    
    # 91-100: Edge cases and stress tests
    "Найди аномалии в данных по времени создания",
    "Вакансии с противоречивыми статусами",
    "Кандидаты без обязательных полей",
    "Дубликаты кандидатов по телефону и email",
    "Офферы без связанных кандидатов",
    "Теги без названий или цветов",
    "Источники без типа или с пустым именем",
    "Рекрутеры без email или имени",
    "Вакансии с нулевой зарплатной вилкой",
    "Кандидаты с будущей датой рождения"
]


class TestRunner:
    def __init__(self):
        self.results = []
        self.start_time = None
        self.failed_count = 0
        self.retry_count = 0
        self.success_count = 0
        
    async def test_single_query(self, client: httpx.AsyncClient, query: str, index: int) -> dict:
        """Test a single query with timeout and error handling"""
        query_start = time.time()
        
        try:
            response = await client.post(
                "http://localhost:8001/chat-retry",
                json={
                    "message": query,
                    "model": "deepseek",
                    "show_debug": False,  # Reduced to speed up
                    "max_retries": 2,
                    "temperature": 0.1,
                    "use_real_data": False
                },
                timeout=30.0  # Reduced timeout
            )
            
            duration = time.time() - query_start
            
            if response.status_code == 200:
                result = response.json()
                
                # Quick analysis
                success = 'response' in result and not result.get('response', '').startswith('⚠️')
                attempts = 1  # Since show_debug=False, we don't get detailed info
                
                if success:
                    self.success_count += 1
                else:
                    self.failed_count += 1
                
                return {
                    "index": index + 1,
                    "query": query[:80] + "..." if len(query) > 80 else query,
                    "success": success,
                    "duration": round(duration, 2),
                    "status": "✅" if success else "❌"
                }
            else:
                self.failed_count += 1
                return {
                    "index": index + 1,
                    "query": query[:80] + "..." if len(query) > 80 else query,
                    "success": False,
                    "duration": round(duration, 2),
                    "error": f"HTTP {response.status_code}",
                    "status": "❌"
                }
                
        except asyncio.TimeoutError:
            self.failed_count += 1
            return {
                "index": index + 1,
                "query": query[:80] + "..." if len(query) > 80 else query,
                "success": False,
                "duration": 30.0,
                "error": "Timeout",
                "status": "⏰"
            }
        except Exception as e:
            self.failed_count += 1
            return {
                "index": index + 1,
                "query": query[:80] + "..." if len(query) > 80 else query,
                "success": False,
                "duration": 0,
                "error": str(e)[:50],
                "status": "💥"
            }
    
    def print_progress(self, current: int, total: int, result: dict):
        """Print progress with result"""
        percent = (current / total) * 100
        bar_length = 30
        filled = int(bar_length * current / total)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        print(f"\r[{bar}] {percent:5.1f}% | {current:3d}/{total} | "
              f"{result['status']} {result['index']:3d}: {result['query'][:50]:50s} "
              f"({result['duration']:4.1f}s)", end="", flush=True)
    
    async def run_all_tests(self):
        """Run all 100 tests with progress tracking"""
        print("🚀 Starting 100 Comprehensive HR Analytics Queries Test")
        print(f"📅 Start time: {datetime.now()}")
        print("=" * 100)
        
        self.start_time = time.time()
        
        async with httpx.AsyncClient() as client:
            # Test queries in small batches with progress
            batch_size = 5
            for i in range(0, len(COMPREHENSIVE_QUERIES), batch_size):
                batch = COMPREHENSIVE_QUERIES[i:i+batch_size]
                
                # Process batch concurrently
                tasks = [
                    self.test_single_query(client, query, i + j)
                    for j, query in enumerate(batch)
                ]
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for result in batch_results:
                    if isinstance(result, dict):
                        self.results.append(result)
                        self.print_progress(len(self.results), len(COMPREHENSIVE_QUERIES), result)
                
                # Small pause between batches
                await asyncio.sleep(0.5)
        
        print("\n" + "=" * 100)
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive test summary"""
        total_time = time.time() - self.start_time if self.start_time else 0
        
        print(f"\n📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        print(f"⏱️  Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
        print(f"📈 Total queries: {len(self.results)}")
        print(f"✅ Successful: {self.success_count} ({self.success_count/len(self.results)*100:.1f}%)")
        print(f"❌ Failed: {self.failed_count} ({self.failed_count/len(self.results)*100:.1f}%)")
        
        # Performance stats
        durations = [r['duration'] for r in self.results if 'duration' in r]
        if durations:
            print(f"\n⚡ Performance:")
            print(f"   Average: {sum(durations)/len(durations):.2f}s per query")
            print(f"   Fastest: {min(durations):.2f}s")
            print(f"   Slowest: {max(durations):.2f}s")
            print(f"   Throughput: {len(self.results)/total_time:.1f} queries/second")
        
        # Error analysis
        failed_results = [r for r in self.results if not r['success']]
        if failed_results:
            print(f"\n💥 Error Analysis:")
            error_types = {}
            for r in failed_results:
                error = r.get('error', 'Unknown')
                error_types[error] = error_types.get(error, 0) + 1
            
            for error, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                print(f"   {error}: {count} times")
        
        # Query categories analysis
        categories = {
            "Invalid entities (1-15)": self.results[0:15],
            "Invalid fields (16-30)": self.results[15:30],
            "Missing group_by (31-45)": self.results[30:45],
            "Time-based (46-60)": self.results[45:60],
            "Multi-criteria (61-75)": self.results[60:75],
            "Aggregations (76-90)": self.results[75:90],
            "Edge cases (91-100)": self.results[90:100]
        }
        
        print(f"\n📋 Category Performance:")
        for category, results in categories.items():
            if results:
                success_rate = sum(1 for r in results if r['success']) / len(results) * 100
                avg_time = sum(r['duration'] for r in results) / len(results)
                print(f"   {category:25s}: {success_rate:5.1f}% success, {avg_time:4.1f}s avg")
        
        # Save detailed results
        with open('comprehensive_test_results.json', 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total_queries': len(self.results),
                    'successful': self.success_count,
                    'failed': self.failed_count,
                    'total_time': total_time,
                    'success_rate': self.success_count/len(self.results)*100
                },
                'results': self.results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Detailed results saved to comprehensive_test_results.json")
        print(f"✅ Test completed at {datetime.now()}")


async def main():
    """Main test runner"""
    runner = TestRunner()
    await runner.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())