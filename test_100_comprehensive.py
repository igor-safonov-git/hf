#!/usr/bin/env python3
"""
Comprehensive test of 200 challenging conversational HR analytics queries
"""
import asyncio
import json
import httpx
from datetime import datetime
import time

# 200 challenging queries in conversational Russian style like "глянь сколько у нас кандидатов в воронке?"
COMPREHENSIVE_QUERIES = [
    # 1-15: Invalid entity usage (should trigger retries)
    "Глянь какие комментарии оставляют наши менеджеры по отклоненным кандидатам?",
    "Покажи мне активность рекрутеров, сколько у них действий в системе",
    "Интересно посмотреть историю изменений статусов кандидатов за неделю",
    "Сколько записей в логах накопилось у каждого рекрутера?",
    "Можешь показать все заметки менеджеров по кандидатам?",
    "Какие причины отказов используются чаще всего у нас?",
    "Давай глянем активность пользователей в системе",
    "Покажи все webhook события за прошлый месяц",
    "Какие организации у нас больше всего вакансий создали?",
    "Интересна статистика по ответам от кандидатов",
    "Какие анкеты заполнили наши кандидаты?",
    "Покажи все группы статусов и как они используются",
    "Давай проанализируем коллег по отделам",
    "Какие логи содержат инфу об отказах?",
    "Можешь показать все заметки по собеседованиям?",
    
    # 16-30: Invalid field usage (should trigger retries)
    "Покажи среднее время в статусе для вакансий по отделам",
    "Какие вакансии имеют максимальное время в статусе?",
    "Давай проанализируем время в статусе кандидатов по источникам",
    "Покажи порядок для всех наших вакансий",
    "Какие кандидаты имеют статус удаленных?",
    "Проанализируй тип для источников кандидатов",
    "Покажи внешние связи между вакансиями",
    "Какие рекрутеры имеют максимальный показатель руководителя?",
    "Давай глянем мета информацию по отделам",
    "Покажи права доступа всех пользователей",
    "Какие вакансии имеют блоки в описании?",
    "Проанализируй запросы вакансий для активных позиций",
    "Покажи PDF ссылки для всех офферов",
    "Какие кандидаты имеют глубокие связи?",
    "Давай проанализируем родительскую структуру вакансий",
    
    # 31-45: Missing group_by for distribution queries (should trigger retries)
    "Как у нас распределены кандидаты по статусам?",
    "Покажи топ источников по количеству кандидатов",
    "Как распределяются вакансии по приоритетам?",
    "Кто из рекрутеров самые активные?",
    "Как распределены кандидаты по зарплатным ожиданиям?",
    "Какие отделы лидируют по открытым вакансиям?",
    "Как распределяются офферы по статусам?",
    "Топ источников по конверсии - покажи",
    "Как распределены кандидаты по создателям?",
    "Какие вакансии самые популярные по кандидатам?",
    "Как распределены теги среди кандидатов?",
    "Топ регионов по вакансиям - интересно глянуть",
    "Как распределены кандидаты по возрасту?",
    "Какие позиции самые популярные?",
    "Как распределено время создания вакансий?",
    
    # 46-60: Complex time-based queries
    "Сравни эффективность рекрутеров за последние 3 месяца с предыдущими",
    "Какие вакансии висят открытыми дольше 60 дней?",
    "Покажи динамику найма по месяцам этого года",
    "Глянь кандидатов, которых добавили за последние 2 недели",
    "Какие вакансии создавались в понедельник?",
    "Сравни конверсию за первый и второй квартал",
    "Какие офферы делали в пятницу?",
    "Давай проанализируем сезонность по кварталам",
    "Покажи активность по дням недели",
    "Каких кандидатов обновляли вчера?",
    "Какие вакансии закрывались в выходные?",
    "Сравни скорость найма по месяцам",
    "Какие теги добавляли в последний месяц?",
    "Давай глянем тренды по полугодиям",
    "Покажи пики активности по часам",
    
    # 61-75: Multi-criteria filtering
    "Найди кандидатов с зарплатой выше 150к на сеньорские позиции",
    "Вакансии первого приоритета без назначенного рекрутера",
    "Активные кандидаты из LinkedIn с опытом больше 5 лет",
    "Закрытые вакансии где было больше 10 кандидатов",
    "Рекрутеры с конверсией выше 20% в IT отделе",
    "Найди дубликаты кандидатов с одинаковым email",
    "Вакансии в Москве с зарплатой выше 200к",
    "Скрытые вакансии где есть активные кандидаты",
    "Множественные вакансии одного родителя",
    "Кандидаты без фото из рекомендаций",
    "Офферы со статусом принят в IT",
    "Красные теги которые создали в 2025 году",
    "Источники типа рекомендации с высокой конверсией",
    "Отделы с порядком меньше 10 и активные",
    "Кандидаты с внешними данными и соглашениями",
    
    # 76-90: Complex aggregations and calculations
    "Какая средняя зарплата нанятых кандидатов по отделам?",
    "Медианное время от создания до найма",
    "Процент конверсии по каждому источнику",
    "Есть ли корреляция между приоритетом и скоростью закрытия?",
    "ROI источников с учетом стоимости привлечения",
    "Среднее количество кандидатов на вакансию",
    "Процент принятых офферов у каждого рекрутера",
    "Стандартное отклонение зарплат по позициям",
    "Коэффициент оборачиваемости кандидатов",
    "Средний возраст кандидатов по источникам",
    "Процент вакансий которые закрыли в срок",
    "Средняя нагрузка на рекрутера",
    "Конверсия воронки по этапам - давай глянем",
    "Процент кандидатов с фотографиями",
    "Средняя длина описания наших вакансий",
    
    # 91-100: Edge cases and stress tests
    "Найди аномалии в данных по времени создания",
    "Есть ли вакансии с противоречивыми статусами?",
    "Кандидаты без обязательных полей",
    "Дубликаты кандидатов по телефону и email",
    "Офферы без привязанных кандидатов",
    "Теги без названий или цветов",
    "Источники без типа или с пустым названием",
    "Рекрутеры без email или имени",
    "Вакансии с нулевой зарплатной вилкой",
    "Кандидаты с будущей датой рождения",
    
    # 101-200: Additional conversational HR questions
    "Сколько у нас кандидатов сейчас в воронке?",
    "А сколько у нас новых заявок за эту неделю?",
    "Какое среднее время отклика на отклик кандидата?",
    "Сколько кандидатов прошло до этапа интервью?",
    "А сколько людей мы наняли за последний месяц?",
    "Какой процент кандидатов отваливается на первом этапе?",
    "Какой у нас средний срок закрытия вакансии?",
    "А сколько всего сейчас открытых вакансий?",
    "Какие вакансии у нас самые долгоиграющие?",
    "Сколько людей отказались после оффера?",
    "Какое среднее количество этапов проходит кандидат?",
    "А сколько у нас заявок с каждого источника?",
    "Какой канал самый эффективный для найма?",
    "На каком этапе чаще всего отсеиваем кандидатов?",
    "Какой средний возраст нанятых сотрудников?",
    "Какой у нас гендерный баланс среди нанятых?",
    "Сколько людей уволилось за год?",
    "А сколько человек у нас работает больше 3 лет?",
    "Какое среднее время прохождения этапа интервью?",
    "Какая воронка по конкретной вакансии?",
    "Сколько кандидатов пришло по рекомендации?",
    "А сколько рекомендованных наняли?",
    "На каком этапе чаще всего дают отказ кандидаты?",
    "Какой средний срок от оффера до выхода?",
    "А сколько человек вышло в прошлом месяце?",
    "Какой у нас средний оффер-рейт?",
    "А сколько людей отклоняет оффер?",
    "Какая зарплата у новых сотрудников?",
    "Какая средняя зарплата по отделам?",
    "Сколько офферов сейчас в процессе согласования?",
    "Какой процент вакансий закрылся вовремя?",
    "А сколько сейчас просроченных вакансий?",
    "Какая конверсия на каждом этапе?",
    "Какой у нас NPS среди кандидатов?",
    "Какие причины отказов кандидатов самые частые?",
    "Сколько времени уходит на адаптацию новых сотрудников?",
    "А сколько стажеров перешло в штат?",
    "Какой процент возвращается через год после ухода?",
    "На каких этапах самые большие потери?",
    "Какое среднее количество интервью на кандидата?",
    "А сколько времени рекрутер тратит на вакансию?",
    "Какой у нас средний response rate на рассылку?",
    "Какой у нас средний time to fill?",
    "А сколько людей работает удаленно?",
    "Сколько людей в каждом городе?",
    "Какой процент сотрудников перевели на другие позиции?",
    "А сколько офферов мы сделали за месяц?",
    "Какой процент офферов был принят?",
    "Какие вакансии закрыли быстрее всего?",
    "На какие вакансии самый большой отклик?",
    "А сколько у нас собеседований было за неделю?",
    "Сколько кандидатов приняли участие в асессменте?",
    "Какой процент кандидатов не доходит до финального этапа?",
    "Какой средний опыт работы у новых сотрудников?",
    "Какие языки чаще всего указаны в резюме?",
    "Сколько человек в команде рекрутинга?",
    "А сколько новых ролей открыли за год?",
    "Какой процент сотрудников прошел внутреннее обучение?",
    "А сколько сотрудников получили повышение?",
    "Какой у нас средний возраст среди уволившихся?",
    "Какой процент женщин среди топ-менеджмента?",
    "Сколько дней сотрудник работает у нас в среднем?",
    "Какой процент сотрудников с профильным образованием?",
    "А сколько вакансий пришлось закрывать повторно?",
    "Какие причины увольнения самые частые?",
    "Какой процент сотрудников остался после испытательного срока?",
    "Сколько заявок приходит через карьерный сайт?",
    "Какая доля кандидатов из социальных сетей?",
    "А сколько кандидатов в базе всего?",
    "Сколько человек вышло из отпуска по уходу за ребенком?",
    "Какой процент вакансий закрыт внутренним перемещением?",
    "Сколько кандидатов на одну вакансию в среднем?",
    "Какой процент кандидатов доходит до оффера?",
    "Какой у нас средний уровень английского у сотрудников?",
    "А сколько людей проходят асессмент онлайн?",
    "Какая у нас медианная зарплата по департаментам?",
    "Сколько сотрудников прошли обучение за квартал?",
    "Какой процент сотрудников получает бонусы?",
    "Какой процент кандидатов уходит на этапе ожидания обратной связи?",
    "Сколько сотрудников работает не полный рабочий день?",
    "Какой у нас уровень текучести кадров?",
    "Какой процент кандидатов возвращается после отказа?",
    "Сколько заявок отклонено автоматом?",
    "Сколько людей в команде адаптации?",
    "Какой процент сотрудников с релокацией?",
    "Какой средний срок работы до увольнения?",
    "Какой у нас процент выхода на работу после оффера?",
    "Сколько кандидатов завершили все этапы отбора?",
    "Какой процент кандидатов вносит изменения в резюме после отклика?",
    "Какой процент новых сотрудников остался через полгода?",
    "Сколько сотрудников работает на аутсорсе?",
    "Какой у нас уровень удовлетворенности рекрутингом?",
    "Какой процент кандидатов дают фидбек после собеседования?",
    "Сколько сотрудников завершили все тренинги?",
    "Какой процент вакансий закрыли внутренними рекомендациями?",
    "Какой процент кандидатов перешли из стажеров?",
    "Какой процент кандидатов сменили решение после оффера?",
    "Сколько кандидатов отказались по причине зарплаты?",
    "Какой у нас средний возраст кандидатов на технические позиции?",
    "Сколько сотрудников работает по гибкому графику?",
    "Сколько новых позиций планируется открыть в этом году?",
    "Какой процент вакансий закрыт по графику?"
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
        """Run all 200 tests with progress tracking"""
        print("🚀 Starting 200 Comprehensive Conversational HR Analytics Queries Test")
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
            "Edge cases (91-100)": self.results[90:100],
            "Conversational HR (101-200)": self.results[100:200] if len(self.results) > 100 else []
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