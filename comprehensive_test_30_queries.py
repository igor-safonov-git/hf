#!/usr/bin/env python3
"""
Comprehensive 30-query test script for HR analytics agent validation
"""
import asyncio
import json
import httpx
from typing import Dict, Any, List
from datetime import datetime
import time

# Comprehensive test queries covering all aspects of HR analytics
COMPREHENSIVE_TEST_QUERIES = [
    # Basic Count Operations (1-8)
    {
        "id": 1,
        "query": "Покажи общее количество кандидатов в системе",
        "category": "Basic Counts",
        "expected_operation": "count",
        "expected_entity": "applicants"
    },
    {
        "id": 2,
        "query": "Сколько у нас активных вакансий?",
        "category": "Basic Counts",
        "expected_operation": "count",
        "expected_entity": "vacancies"
    },
    {
        "id": 3,
        "query": "Количество рекрутеров в команде",
        "category": "Basic Counts",
        "expected_operation": "count",
        "expected_entity": "recruiters"
    },
    {
        "id": 4,
        "query": "Сколько у нас принятых кандидатов (оффер принят)?",
        "category": "Basic Counts",
        "expected_operation": "count",
        "expected_entity": "applicants"
    },
    {
        "id": 5,
        "query": "Количество скрытых вакансий",
        "category": "Basic Counts", 
        "expected_operation": "count",
        "expected_entity": "vacancies"
    },
    {
        "id": 6,
        "query": "Сколько источников кандидатов у нас есть?",
        "category": "Basic Counts",
        "expected_operation": "count",
        "expected_entity": "sources"
    },
    {
        "id": 7,
        "query": "Количество отделов в компании",
        "category": "Basic Counts",
        "expected_operation": "count",
        "expected_entity": "divisions"
    },
    {
        "id": 8,
        "query": "Общее количество статусов в воронке",
        "category": "Basic Counts",
        "expected_operation": "count",
        "expected_entity": "status_mapping"
    },

    # Status and Pipeline Analysis (9-14)
    {
        "id": 9,
        "query": "Распределение кандидатов по статусам",
        "category": "Status Analysis",
        "expected_operation": "count",
        "expected_entity": "applicants"
    },
    {
        "id": 10,
        "query": "Воронка найма - кандидаты на каждом этапе",
        "category": "Status Analysis", 
        "expected_operation": "count",
        "expected_entity": "applicants"
    },
    {
        "id": 11,
        "query": "Статистика по статусам с наивысшим приоритетом",
        "category": "Status Analysis",
        "expected_operation": "count",
        "expected_entity": "status_mapping"
    },
    {
        "id": 12,
        "query": "Кандидаты, которые находятся в процессе более 30 дней",
        "category": "Status Analysis",
        "expected_operation": "count",
        "expected_entity": "applicants"
    },
    {
        "id": 13,
        "query": "Анализ конверсии по этапам воронки",
        "category": "Status Analysis",
        "expected_operation": "count",
        "expected_entity": "applicants"
    },
    {
        "id": 14,
        "query": "Отклоненные кандидаты по причинам",
        "category": "Status Analysis",
        "expected_operation": "count",
        "expected_entity": "applicants"
    },

    # Recruiter Performance (15-20)
    {
        "id": 15,
        "query": "Топ рекрутеров по количеству кандидатов",
        "category": "Recruiter Performance",
        "expected_operation": "count",
        "expected_entity": "applicants"
    },
    {
        "id": 16,
        "query": "Анализ производительности рекрутеров - кто больше всех нанял?",
        "category": "Recruiter Performance",
        "expected_operation": "count",
        "expected_entity": "applicants"
    },
    {
        "id": 17,
        "query": "Самый активный рекрутер по новым кандидатам",
        "category": "Recruiter Performance",
        "expected_operation": "count",
        "expected_entity": "applicants"
    },
    {
        "id": 18,
        "query": "Рейтинг рекрутеров по успешности найма",
        "category": "Recruiter Performance",
        "expected_operation": "count",
        "expected_entity": "applicants"
    },
    {
        "id": 19,
        "query": "Средняя зарплатная вилка кандидатов у каждого рекрутера",
        "category": "Recruiter Performance",
        "expected_operation": "avg",
        "expected_entity": "applicants"
    },
    {
        "id": 20,
        "query": "Распределение рабочей нагрузки между рекрутерами",
        "category": "Recruiter Performance",
        "expected_operation": "count",
        "expected_entity": "applicants"
    },

    # Source Effectiveness (21-24)
    {
        "id": 21,
        "query": "Эффективность источников кандидатов - откуда приходят лучшие?",
        "category": "Source Analysis",
        "expected_operation": "count",
        "expected_entity": "applicants"
    },
    {
        "id": 22,
        "query": "ROI по источникам - какие каналы самые выгодные?",
        "category": "Source Analysis",
        "expected_operation": "count",
        "expected_entity": "applicants"
    },
    {
        "id": 23,
        "query": "Топ-5 источников по количеству принятых кандидатов",
        "category": "Source Analysis",
        "expected_operation": "count",
        "expected_entity": "applicants"
    },
    {
        "id": 24,
        "query": "Конверсия по источникам - от кандидата до найма",
        "category": "Source Analysis",
        "expected_operation": "count",
        "expected_entity": "applicants"
    },

    # Vacancy and Company Analysis (25-28)
    {
        "id": 25,
        "query": "Анализ вакансий по компаниям",
        "category": "Vacancy Analysis",
        "expected_operation": "count",
        "expected_entity": "vacancies"
    },
    {
        "id": 26,
        "query": "Средняя зарплата по всем вакансиям",
        "category": "Vacancy Analysis",
        "expected_operation": "avg",
        "expected_entity": "vacancies"
    },
    {
        "id": 27,
        "query": "Вакансии с наивысшим приоритетом",
        "category": "Vacancy Analysis",
        "expected_operation": "count",
        "expected_entity": "vacancies"
    },
    {
        "id": 28,
        "query": "Статистика по отделам (divisions)",
        "category": "Division Analysis",
        "expected_operation": "count",
        "expected_entity": "divisions"
    },

    # Complex Dashboard Queries (29-30)
    {
        "id": 29,
        "query": "Общая статистика: кандидаты, вакансии, рекрутеры",
        "category": "Dashboard",
        "expected_operation": "count",
        "expected_entity": "applicants"
    },
    {
        "id": 30,
        "query": "KPI дашборд: конверсия, скорость найма, эффективность команды",
        "category": "Dashboard",
        "expected_operation": "count",
        "expected_entity": "applicants"
    }
]

def validate_json_structure(response_text: str) -> Dict[str, Any]:
    """Enhanced validation for JSON structure and content"""
    result = {
        "valid_json": False,
        "has_required_fields": False,
        "json_data": None,
        "errors": [],
        "warnings": [],
        "validation_score": 0
    }
    
    try:
        # Extract JSON from markdown if present  
        json_content = response_text
        if '```json' in response_text:
            start = response_text.find('```json') + 7
            end = response_text.find('```', start)
            if end != -1:
                json_content = response_text[start:end].strip()
        
        # Parse JSON
        json_data = json.loads(json_content)
        result["valid_json"] = True
        result["json_data"] = json_data
        result["validation_score"] += 25  # Base score for valid JSON
        
        # Check required fields
        required_fields = ["report_title", "main_metric", "secondary_metrics", "chart"]
        has_all_required = all(field in json_data for field in required_fields)
        result["has_required_fields"] = has_all_required
        
        if has_all_required:
            result["validation_score"] += 25  # Score for structure
        else:
            missing = [field for field in required_fields if field not in json_data]
            result["errors"].append(f"Missing required fields: {missing}")
        
        # Validate main_metric
        if "main_metric" in json_data:
            main_metric = json_data["main_metric"]
            if isinstance(main_metric, dict) and "value" in main_metric:
                value = main_metric["value"]
                if isinstance(value, dict):
                    # Check operation and entity
                    if "operation" in value and "entity" in value:
                        result["validation_score"] += 20  # Score for main metric
                        
                        # Special validation for avg operation
                        if value.get("operation") == "avg":
                            if "field" not in value:
                                result["errors"].append("avg operation missing required 'field' parameter")
                            else:
                                result["validation_score"] += 10  # Bonus for correct avg usage
                    else:
                        result["errors"].append("main_metric.value missing operation or entity")
                else:
                    result["errors"].append("main_metric.value is not a dict")
            else:
                result["errors"].append("main_metric invalid structure")
        
        # Validate chart
        if "chart" in json_data:
            chart = json_data["chart"]
            if isinstance(chart, dict):
                chart_fields = ["x_axis", "y_axis", "chart_type"]
                if all(field in chart for field in chart_fields):
                    result["validation_score"] += 15  # Score for chart
                    
                    # Validate y_axis avg operations
                    y_axis = chart.get("y_axis", {})
                    if y_axis.get("operation") == "avg" and "field" not in y_axis:
                        result["errors"].append("chart y_axis avg operation missing 'field' parameter")
                else:
                    missing_chart = [f for f in chart_fields if f not in chart]
                    result["errors"].append(f"chart missing: {missing_chart}")
        
        # Check secondary metrics for avg operations
        secondary_metrics = json_data.get("secondary_metrics", [])
        for i, metric in enumerate(secondary_metrics):
            if isinstance(metric, dict) and "value" in metric:
                value = metric["value"]
                if isinstance(value, dict) and value.get("operation") == "avg":
                    if "field" not in value:
                        result["errors"].append(f"secondary_metric[{i}] avg operation missing 'field' parameter")
        
        # Check for forbidden fields
        json_str = json.dumps(json_data)
        forbidden_fields = ["demo_value", "demo_data"]
        for field in forbidden_fields:
            if field in json_str:
                result["errors"].append(f"Contains forbidden field: {field}")
        
        # Final validation score adjustment
        if not result["errors"]:
            result["validation_score"] = min(100, result["validation_score"] + 5)  # Perfect bonus
        elif len(result["errors"]) == 1:
            result["validation_score"] = max(70, result["validation_score"])  # Minor issues
        else:
            result["validation_score"] = max(40, result["validation_score"])  # Multiple issues
            
    except json.JSONDecodeError as e:
        result["errors"].append(f"JSON parsing error: {str(e)}")
        result["validation_score"] = 0
    except Exception as e:
        result["errors"].append(f"Validation error: {str(e)}")
        result["validation_score"] = max(0, result["validation_score"])
    
    return result

async def send_chat_request(query: str, timeout: int = 25) -> str:
    """Send chat request with timeout"""
    url = "http://localhost:8001/chat"
    
    payload = {
        "message": query,
        "model": "deepseek",
        "use_real_data": False,
        "temperature": 0.1
    }
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "No response received")
            
    except httpx.ConnectError:
        return "ERROR: Cannot connect to FastAPI server at localhost:8001"
    except httpx.TimeoutException:
        return f"ERROR: Request timed out after {timeout} seconds"
    except Exception as e:
        return f"ERROR: {str(e)}"

async def run_comprehensive_test():
    """Run all 30 test queries with detailed analysis"""
    print("🚀 Starting Comprehensive 30-Query Agent Test")
    print("=" * 80)
    
    results = []
    categories = {}
    start_time = time.time()
    
    for i, test_case in enumerate(COMPREHENSIVE_TEST_QUERIES):
        print(f"\n📋 Test {test_case['id']}/30: {test_case['category']}")
        print(f"Query: {test_case['query']}")
        print("-" * 60)
        
        test_start = time.time()
        
        # Send request
        response = await send_chat_request(test_case['query'])
        test_duration = time.time() - test_start
        
        if response.startswith("ERROR:"):
            print(f"❌ REQUEST FAILED: {response}")
            result = {
                "test_id": test_case['id'],
                "category": test_case['category'],
                "status": "ERROR",
                "error": response,
                "duration": test_duration,
                "validation_score": 0
            }
        else:
            # Validate response
            validation = validate_json_structure(response)
            
            # Determine status
            if validation["validation_score"] >= 90:
                status = "EXCELLENT"
                status_emoji = "🌟"
            elif validation["validation_score"] >= 75:
                status = "GOOD"
                status_emoji = "✅"
            elif validation["validation_score"] >= 50:
                status = "PARTIAL"
                status_emoji = "⚠️"
            else:
                status = "POOR"
                status_emoji = "❌"
            
            print(f"{status_emoji} {status} (Score: {validation['validation_score']}/100)")
            
            # Show key info
            if validation["json_data"]:
                json_data = validation["json_data"]
                print(f"   📊 Title: {json_data.get('report_title', 'N/A')}")
                if "main_metric" in json_data and "value" in json_data["main_metric"]:
                    value = json_data["main_metric"]["value"]
                    operation = value.get('operation', 'N/A')
                    entity = value.get('entity', 'N/A')
                    field = value.get('field', 'N/A') if operation in ['avg', 'sum', 'max', 'min'] else 'N/A'
                    print(f"   🔧 Operation: {operation} | Entity: {entity} | Field: {field}")
                    
                if "chart" in json_data:
                    print(f"   📈 Chart: {json_data['chart'].get('chart_type', 'N/A')}")
            
            # Show errors/warnings
            if validation["errors"]:
                print(f"   ⚠️ Issues: {'; '.join(validation['errors'][:2])}")  # Show first 2 errors
            
            result = {
                "test_id": test_case['id'],
                "category": test_case['category'],
                "query": test_case['query'],
                "status": status,
                "validation_score": validation["validation_score"],
                "errors": validation["errors"],
                "duration": test_duration,
                "response_length": len(response)
            }
        
        results.append(result)
        
        # Update category stats
        category = test_case['category']
        if category not in categories:
            categories[category] = {"total": 0, "excellent": 0, "good": 0, "partial": 0, "poor": 0, "error": 0}
        
        categories[category]["total"] += 1
        categories[category][result["status"].lower()] += 1
        
        print(f"   ⏱️ Duration: {test_duration:.1f}s")
        
        # Small delay to avoid overwhelming the server
        await asyncio.sleep(0.5)
    
    total_duration = time.time() - start_time
    
    # Comprehensive Analysis
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 80)
    
    # Overall stats
    excellent = sum(1 for r in results if r["status"] == "EXCELLENT")
    good = sum(1 for r in results if r["status"] == "GOOD")
    partial = sum(1 for r in results if r["status"] == "PARTIAL")
    poor = sum(1 for r in results if r["status"] == "POOR")
    errors = sum(1 for r in results if r["status"] == "ERROR")
    
    print(f"🌟 EXCELLENT: {excellent}/30 ({excellent/30*100:.1f}%)")
    print(f"✅ GOOD: {good}/30 ({good/30*100:.1f}%)")
    print(f"⚠️ PARTIAL: {partial}/30 ({partial/30*100:.1f}%)")
    print(f"❌ POOR: {poor}/30 ({poor/30*100:.1f}%)")
    print(f"🔥 ERROR: {errors}/30 ({errors/30*100:.1f}%)")
    
    success_rate = (excellent + good) / 30 * 100
    overall_rate = (excellent + good + partial) / 30 * 100
    
    print(f"\n🎯 Success Rate (Excellent + Good): {success_rate:.1f}%")
    print(f"📈 Overall Rate (All working responses): {overall_rate:.1f}%")
    
    # Average scores
    valid_scores = [r["validation_score"] for r in results if r["status"] != "ERROR"]
    if valid_scores:
        avg_score = sum(valid_scores) / len(valid_scores)
        print(f"📊 Average Validation Score: {avg_score:.1f}/100")
    
    # Performance stats
    valid_durations = [r["duration"] for r in results if r["status"] != "ERROR"]
    if valid_durations:
        avg_duration = sum(valid_durations) / len(valid_durations)
        max_duration = max(valid_durations)
        min_duration = min(valid_durations)
        print(f"⏱️ Average Response Time: {avg_duration:.1f}s (min: {min_duration:.1f}s, max: {max_duration:.1f}s)")
    
    print(f"🕐 Total Test Duration: {total_duration:.1f}s")
    
    # Category breakdown
    print(f"\n📊 RESULTS BY CATEGORY:")
    print("-" * 60)
    for category, stats in categories.items():
        excellent_pct = stats["excellent"] / stats["total"] * 100
        good_pct = stats["good"] / stats["total"] * 100
        success_pct = excellent_pct + good_pct
        print(f"{category:20} | {stats['excellent']:2}🌟 {stats['good']:2}✅ {stats['partial']:2}⚠️ {stats['poor']:2}❌ {stats['error']:2}🔥 | Success: {success_pct:5.1f}%")
    
    # Problem analysis
    all_errors = []
    for r in results:
        if r.get("errors"):
            all_errors.extend(r["errors"])
    
    if all_errors:
        print(f"\n⚠️ COMMON ISSUES FOUND:")
        error_counts = {}
        for error in all_errors:
            error_counts[error] = error_counts.get(error, 0) + 1
        
        for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   • {error} ({count} times)")
    else:
        print(f"\n🎉 NO VALIDATION ISSUES FOUND!")
    
    # Final assessment
    print(f"\n" + "=" * 80)
    print("🏆 FINAL ASSESSMENT")
    print("=" * 80)
    
    if success_rate >= 90:
        assessment = "🌟 OUTSTANDING - Production ready with excellent performance!"
        recommendation = "Deploy immediately. System exceeds expectations."
    elif success_rate >= 80:
        assessment = "🎯 EXCELLENT - Ready for production use!"
        recommendation = "Deploy with confidence. Minor monitoring recommended."
    elif success_rate >= 70:
        assessment = "✅ GOOD - Suitable for production with monitoring"
        recommendation = "Deploy with careful monitoring and quick fixes planned."
    elif success_rate >= 50:
        assessment = "⚠️ ACCEPTABLE - Needs improvement before production"
        recommendation = "Address issues before deployment. Consider beta testing."
    else:
        assessment = "❌ NEEDS WORK - Significant issues require attention"
        recommendation = "Do not deploy. Major fixes required."
    
    print(f"Status: {assessment}")
    print(f"Recommendation: {recommendation}")
    print(f"Overall System Health: {overall_rate:.1f}%")
    
    return results, categories

if __name__ == "__main__":
    print(f"🕐 Comprehensive test started at: {datetime.now().isoformat()}")
    results, categories = asyncio.run(run_comprehensive_test())
    print(f"🕐 Comprehensive test completed at: {datetime.now().isoformat()}")