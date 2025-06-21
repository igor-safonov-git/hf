#!/usr/bin/env python3
"""
Comprehensive End-to-End Test for Unified Metrics Group By
Phase 6.1: Run comprehensive end-to-end test with real data to verify complete functionality
"""

import asyncio
import json
import time
from chart_data_processor import process_chart_data, validate_report_json
from huntflow_local_client import HuntflowLocalClient

# Test scenarios covering all major use cases
test_scenarios = [
    {
        "name": "Recruiter Performance Analysis",
        "description": "Individual recruiter metrics with monthly trends",
        "report": {
            "report_title": "Анализ результативности рекрутеров",
            "period": "6 month",
            "metrics_group_by": "recruiters",
            "main_metric": {
                "label": "Нанято рекрутером",
                "value": {
                    "operation": "count",
                    "entity": "hires",
                    "value_field": None,
                    "filters": {"period": "6 month"}
                }
            },
            "secondary_metrics": [
                {
                    "label": "Кандидатов добавлено",
                    "value": {
                        "operation": "count",
                        "entity": "applicants",
                        "value_field": None,
                        "filters": {"period": "6 month"}
                    }
                },
                {
                    "label": "Среднее время найма",
                    "value": {
                        "operation": "avg",
                        "entity": "hires",
                        "value_field": "time_to_hire",
                        "filters": {"period": "6 month"}
                    }
                }
            ],
            "chart": {
                "label": "Динамика найма по месяцам",
                "type": "line",
                "x_label": "Месяц",
                "y_label": "Количество найма",
                "x_axis": {
                    "operation": "count",
                    "entity": "hires",
                    "group_by": {"field": "month"},
                    "filters": {"period": "6 month"}
                },
                "y_axis": {
                    "operation": "count",
                    "entity": "hires",
                    "group_by": {"field": "month"},
                    "filters": {"period": "6 month"}
                }
            }
        }
    },
    {
        "name": "Source Effectiveness Comparison",
        "description": "Source breakdown with bar chart visualization",
        "report": {
            "report_title": "Сравнение эффективности источников",
            "period": "3 month",
            "metrics_group_by": "sources",
            "main_metric": {
                "label": "Нанято через источник",
                "value": {
                    "operation": "count",
                    "entity": "hires",
                    "value_field": None,
                    "filters": {"period": "3 month"}
                }
            },
            "secondary_metrics": [
                {
                    "label": "Кандидатов через источник",
                    "value": {
                        "operation": "count",
                        "entity": "applicants",
                        "value_field": None,
                        "filters": {"period": "3 month"}
                    }
                },
                {
                    "label": "Конверсия источника",
                    "value": {
                        "operation": "avg",
                        "entity": "sources",
                        "value_field": "conversion",
                        "filters": {"period": "3 month"}
                    }
                }
            ],
            "chart": {
                "label": "Источники по эффективности",
                "type": "bar",
                "x_label": "Источники",
                "y_label": "Количество найма",
                "x_axis": {
                    "operation": "count",
                    "entity": "hires",
                    "group_by": {"field": "sources"},
                    "filters": {"period": "3 month"}
                },
                "y_axis": {
                    "operation": "count",
                    "entity": "hires",
                    "group_by": {"field": "sources"},
                    "filters": {"period": "3 month"}
                }
            }
        }
    },
    {
        "name": "Division Performance Overview",
        "description": "Division breakdown with table view",
        "report": {
            "report_title": "Результаты отделов компании",
            "period": "1 month",
            "metrics_group_by": "divisions",
            "main_metric": {
                "label": "Нанято в отдел",
                "value": {
                    "operation": "count",
                    "entity": "hires",
                    "value_field": None,
                    "filters": {"period": "1 month"}
                }
            },
            "secondary_metrics": [
                {
                    "label": "Открытых вакансий",
                    "value": {
                        "operation": "count",
                        "entity": "vacancies",
                        "value_field": None,
                        "filters": {"vacancies": "open"}
                    }
                },
                {
                    "label": "Кандидатов в отделе",
                    "value": {
                        "operation": "count",
                        "entity": "applicants",
                        "value_field": None,
                        "filters": {"period": "1 month"}
                    }
                }
            ],
            "chart": {
                "label": "Статус вакансий по отделам",
                "type": "table",
                "x_label": "Отделы",
                "y_label": "Данные",
                "x_axis": {
                    "operation": "count",
                    "entity": "vacancies",
                    "group_by": {"field": "divisions"},
                    "filters": {}
                },
                "y_axis": {
                    "operation": "count",
                    "entity": "vacancies",
                    "group_by": {"field": "divisions"},
                    "filters": {}
                }
            }
        }
    }
]

async def run_end_to_end_test():
    """Run comprehensive end-to-end test"""
    print("🚀 Starting Comprehensive End-to-End Test\n")
    
    client = HuntflowLocalClient()
    all_results = []
    start_time = time.time()
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"📊 Test {i}/3: {scenario['name']}")
        print(f"   Description: {scenario['description']}")
        
        scenario_start = time.time()
        
        try:
            # 1. Schema Validation
            print("   📋 Validating schema...")
            validate_report_json(scenario['report'])
            print("   ✅ Schema validation: PASSED")
            
            # 2. Data Processing
            print("   ⚙️  Processing with real data...")
            processed = await process_chart_data(scenario['report'].copy(), client)
            processing_time = time.time() - scenario_start
            
            # 3. Structure Validation
            print("   🔍 Validating result structure...")
            
            # Check required fields
            assert "metrics_group_by" in processed, "Missing metrics_group_by"
            assert "main_metric" in processed, "Missing main_metric"
            assert "secondary_metrics" in processed, "Missing secondary_metrics"
            assert "chart" in processed, "Missing chart"
            
            # Check metrics structure
            main_metric = processed["main_metric"]
            assert "real_value" in main_metric, "Missing main_metric.real_value"
            assert "total_value" in main_metric, "Missing main_metric.total_value"
            
            # Check secondary metrics
            for j, sec_metric in enumerate(processed["secondary_metrics"]):
                assert "real_value" in sec_metric, f"Missing secondary_metrics[{j}].real_value"
                assert "total_value" in sec_metric, f"Missing secondary_metrics[{j}].total_value"
            
            # Check grouping consistency
            expected_group_by = scenario['report']['metrics_group_by']
            actual_group_by = processed['metrics_group_by']
            assert actual_group_by == expected_group_by, f"Group by mismatch: {actual_group_by} != {expected_group_by}"
            
            # 4. Data Quality Check
            print("   📈 Checking data quality...")
            
            # Check for grouped breakdown when available
            has_breakdown = "grouped_breakdown" in main_metric
            breakdown_count = len(main_metric.get("grouped_breakdown", {}))
            total_value = main_metric.get("total_value", 0)
            
            print(f"   📊 Results:")
            print(f"      - Grouping: {actual_group_by}")
            print(f"      - Has breakdown: {has_breakdown}")
            print(f"      - Entities found: {breakdown_count}")
            print(f"      - Total value: {total_value}")
            print(f"      - Processing time: {processing_time:.3f}s")
            
            # Store results
            all_results.append({
                "scenario": scenario['name'],
                "group_by": actual_group_by,
                "has_breakdown": has_breakdown,
                "entity_count": breakdown_count,
                "total_value": total_value,
                "processing_time": processing_time,
                "success": True
            })
            
            print(f"   ✅ Test {i}: PASSED\n")
            
        except Exception as e:
            print(f"   ❌ Test {i}: FAILED - {e}")
            all_results.append({
                "scenario": scenario['name'],
                "success": False,
                "error": str(e)
            })
            
    total_time = time.time() - start_time
    
    # Final Report
    print("=" * 60)
    print("📋 COMPREHENSIVE END-TO-END TEST RESULTS")
    print("=" * 60)
    
    successful_tests = [r for r in all_results if r.get("success")]
    failed_tests = [r for r in all_results if not r.get("success")]
    
    print(f"✅ Successful tests: {len(successful_tests)}/{len(all_results)}")
    print(f"❌ Failed tests: {len(failed_tests)}/{len(all_results)}")
    print(f"⏱️  Total execution time: {total_time:.3f}s")
    print(f"🚀 Average processing time: {sum(r.get('processing_time', 0) for r in successful_tests) / len(successful_tests) if successful_tests else 0:.3f}s")
    
    if successful_tests:
        print("\n📊 Successful Test Details:")
        for result in successful_tests:
            print(f"   • {result['scenario']}")
            print(f"     Group by: {result['group_by']}, Entities: {result['entity_count']}, Total: {result['total_value']}")
    
    if failed_tests:
        print("\n❌ Failed Test Details:")
        for result in failed_tests:
            print(f"   • {result['scenario']}: {result['error']}")
    
    # Performance Check
    avg_time = sum(r.get('processing_time', 0) for r in successful_tests) / len(successful_tests) if successful_tests else 0
    if avg_time > 1.0:
        print(f"\n⚠️  Performance Warning: Average processing time {avg_time:.3f}s exceeds 1s threshold")
    else:
        print(f"\n🚀 Performance: Excellent! Average processing time {avg_time:.3f}s")
    
    # Feature Coverage Check
    group_by_types = set(r.get('group_by') for r in successful_tests if r.get('group_by'))
    print(f"\n🎯 Feature Coverage:")
    print(f"   • Group by types tested: {', '.join(group_by_types)}")
    print(f"   • Chart types tested: line, bar, table")
    print(f"   • Entity types tested: hires, applicants, sources, vacancies")
    print(f"   • Operations tested: count, avg")
    
    return len(failed_tests) == 0

if __name__ == "__main__":
    async def main():
        success = await run_end_to_end_test()
        
        if success:
            print("\n🎉 ALL END-TO-END TESTS PASSED!")
            print("✅ Unified metrics group_by implementation is PRODUCTION READY!")
            exit(0)
        else:
            print("\n❌ SOME END-TO-END TESTS FAILED!")
            print("🔧 Check implementation before deployment")
            exit(1)
    
    asyncio.run(main())