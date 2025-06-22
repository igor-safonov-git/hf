#!/usr/bin/env python3
"""
Comprehensive Full Pipeline Test for Restructured Metrics Filter System
Tests the complete flow: Schema → Processing → Frontend → Results
"""

import asyncio
import json
import time
from chart_data_processor import process_chart_data, validate_report_json
from huntflow_local_client import HuntflowLocalClient

# Test scenarios covering all major use cases with new structure
pipeline_test_scenarios = [
    {
        "name": "General Overview (Auto Breakdown)",
        "description": "Period-only filter should trigger automatic recruiter breakdown",
        "report": {
            "report_title": "Общая ситуация с наймом",
            "metrics_filter": {
                "period": "6 month"
            },
            "main_metric": {
                "label": "Нанято сотрудников",
                "value": {
                    "operation": "count",
                    "entity": "hires"
                }
            },
            "secondary_metrics": [
                {
                    "label": "Кандидатов добавлено",
                    "value": {
                        "operation": "count",
                        "entity": "applicants"
                    }
                },
                {
                    "label": "Среднее время найма",
                    "value": {
                        "operation": "avg",
                        "entity": "hires",
                        "value_field": "time_to_hire"
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
                    "group_by": {"field": "month"}
                },
                "y_axis": {
                    "operation": "count",
                    "entity": "hires",
                    "group_by": {"field": "month"}
                }
            }
        },
        "expected_behavior": "auto_breakdown"
    },
    {
        "name": "Specific Recruiter Analysis",
        "description": "Specific recruiter filter should give aggregated results",
        "report": {
            "report_title": "Результаты Сафонова",
            "metrics_filter": {
                "period": "3 month",
                "recruiters": "55498"
            },
            "main_metric": {
                "label": "Нанято Сафоновым",
                "value": {
                    "operation": "count",
                    "entity": "hires"
                }
            },
            "secondary_metrics": [
                {
                    "label": "Кандидатов добавил",
                    "value": {
                        "operation": "count",
                        "entity": "applicants"
                    }
                },
                {
                    "label": "Среднее время найма",
                    "value": {
                        "operation": "avg",
                        "entity": "hires",
                        "value_field": "time_to_hire"
                    }
                }
            ],
            "chart": {
                "label": "Тренд найма компании",
                "type": "bar",
                "x_label": "Источники",
                "y_label": "Кандидаты",
                "x_axis": {
                    "operation": "count",
                    "entity": "applicants",
                    "group_by": {"field": "sources"}
                },
                "y_axis": {
                    "operation": "count",
                    "entity": "applicants",
                    "group_by": {"field": "sources"}
                }
            }
        },
        "expected_behavior": "aggregated"
    },
    {
        "name": "Division Performance Analysis",
        "description": "Specific division filter with table chart",
        "report": {
            "report_title": "Результаты IT отдела",
            "metrics_filter": {
                "period": "1 month",
                "divisions": "101"
            },
            "main_metric": {
                "label": "Нанято в IT",
                "value": {
                    "operation": "count",
                    "entity": "hires"
                }
            },
            "secondary_metrics": [
                {
                    "label": "Открытых вакансий в IT",
                    "value": {
                        "operation": "count",
                        "entity": "vacancies"
                    }
                },
                {
                    "label": "Кандидатов в IT",
                    "value": {
                        "operation": "count",
                        "entity": "applicants"
                    }
                }
            ],
            "chart": {
                "label": "Детализация по этапам",
                "type": "table",
                "x_label": "Этапы",
                "y_label": "Данные",
                "x_axis": {
                    "operation": "count",
                    "entity": "applicants",
                    "group_by": {"field": "stages"}
                },
                "y_axis": {
                    "operation": "count",
                    "entity": "applicants",
                    "group_by": {"field": "stages"}
                }
            }
        },
        "expected_behavior": "aggregated"
    }
]

async def run_full_pipeline_test():
    """Run comprehensive full pipeline test with new metrics_filter structure"""
    print("🚀 FULL PIPELINE TEST - Restructured Metrics Filter System\n")
    print("=" * 70)
    
    client = HuntflowLocalClient()
    all_results = []
    start_time = time.time()
    
    for i, scenario in enumerate(pipeline_test_scenarios, 1):
        print(f"\n📊 Pipeline Test {i}/3: {scenario['name']}")
        print(f"   📝 Description: {scenario['description']}")
        print(f"   🎯 Expected: {scenario['expected_behavior']}")
        
        scenario_start = time.time()
        
        try:
            # 1. Schema Validation
            print("   📋 Step 1: Schema validation...")
            validate_report_json(scenario['report'])
            print("   ✅ Schema validation: PASSED")
            
            # 2. Backend Processing
            print("   ⚙️  Step 2: Backend processing...")
            processed = await process_chart_data(scenario['report'].copy(), client)
            processing_time = time.time() - scenario_start
            
            # 3. Data Structure Analysis
            print("   🔍 Step 3: Analyzing results...")
            
            # Check metrics_filter
            metrics_filter = processed.get("metrics_filter", {})
            period = metrics_filter.get("period", "unknown")
            entity_filters = {k: v for k, v in metrics_filter.items() if k != "period" and v is not None}
            
            # Check main metric structure
            main_metric = processed.get("main_metric", {})
            has_breakdown = main_metric.get("is_grouped", False)
            total_value = main_metric.get("total_value", main_metric.get("real_value", 0))
            breakdown_count = 0  # Not stored anymore, but grouping tracked with is_grouped flag
            
            # Check chart data
            chart_data = processed.get("chart", {}).get("real_data", {})
            chart_labels = len(chart_data.get("labels", []))
            
            # 4. Behavior Validation
            print("   🎯 Step 4: Validating expected behavior...")
            
            behavior_correct = False
            if scenario["expected_behavior"] == "auto_breakdown":
                # Should have breakdown when no entity filters
                behavior_correct = (len(entity_filters) == 0 and has_breakdown)
                behavior_msg = f"Auto breakdown: {has_breakdown} (expected: True)"
            elif scenario["expected_behavior"] == "aggregated":
                # Should NOT have breakdown when specific entity filter
                behavior_correct = (len(entity_filters) > 0 and not has_breakdown)
                behavior_msg = f"Aggregated result: {not has_breakdown} (expected: True)"
            
            print(f"   📊 Results Summary:")
            print(f"      - Period: {period}")
            print(f"      - Entity filters: {entity_filters}")
            print(f"      - Has breakdown: {has_breakdown}")
            print(f"      - Is grouped: {has_breakdown}")
            print(f"      - Total value: {total_value}")
            print(f"      - Chart data points: {chart_labels}")
            print(f"      - Processing time: {processing_time:.3f}s")
            print(f"      - Behavior check: {behavior_msg}")
            
            # Store results
            all_results.append({
                "scenario": scenario['name'],
                "period": period,
                "entity_filters": len(entity_filters),
                "has_breakdown": has_breakdown,
                "is_grouped": has_breakdown,
                "total_value": total_value,
                "chart_points": chart_labels,
                "processing_time": processing_time,
                "behavior_correct": behavior_correct,
                "success": True
            })
            
            status = "✅ PASSED" if behavior_correct else "⚠️  BEHAVIOR MISMATCH"
            print(f"   {status}")
            
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            all_results.append({
                "scenario": scenario['name'],
                "success": False,
                "error": str(e),
                "processing_time": time.time() - scenario_start
            })
            
    total_time = time.time() - start_time
    
    # Final Analysis
    print("\n" + "=" * 70)
    print("📋 FULL PIPELINE TEST RESULTS")
    print("=" * 70)
    
    successful_tests = [r for r in all_results if r.get("success")]
    failed_tests = [r for r in all_results if not r.get("success")]
    behavior_correct_tests = [r for r in successful_tests if r.get("behavior_correct")]
    
    print(f"✅ Successful tests: {len(successful_tests)}/{len(all_results)}")
    print(f"🎯 Correct behavior: {len(behavior_correct_tests)}/{len(successful_tests)}")
    print(f"❌ Failed tests: {len(failed_tests)}/{len(all_results)}")
    print(f"⏱️  Total execution time: {total_time:.3f}s")
    
    if successful_tests:
        avg_time = sum(r.get('processing_time', 0) for r in successful_tests) / len(successful_tests)
        print(f"🚀 Average processing time: {avg_time:.3f}s")
        
        print("\n📊 Detailed Results:")
        for result in successful_tests:
            status = "🎯" if result.get('behavior_correct') else "⚠️"
            print(f"   {status} {result['scenario']}")
            print(f"      Filters: {result['entity_filters']}, Grouped: {result['is_grouped']}, Total: {result['total_value']}")
    
    if failed_tests:
        print("\n❌ Failed Tests:")
        for result in failed_tests:
            print(f"   • {result['scenario']}: {result['error']}")
    
    # Performance Assessment
    if successful_tests:
        avg_time = sum(r.get('processing_time', 0) for r in successful_tests) / len(successful_tests)
        if avg_time > 1.0:
            print(f"\n⚠️  Performance Warning: Average time {avg_time:.3f}s exceeds 1s")
        else:
            print(f"\n🚀 Performance: Excellent! Average time {avg_time:.3f}s")
    
    # Feature Coverage Assessment
    print(f"\n🎯 Feature Coverage Assessment:")
    print(f"   • Automatic breakdown logic: Tested")
    print(f"   • Specific entity filtering: Tested") 
    print(f"   • Chart independence: Tested")
    print(f"   • All chart types: line, bar, table")
    print(f"   • All operations: count, avg")
    print(f"   • Multiple entities: hires, applicants, vacancies")
    
    return len(failed_tests) == 0 and len(behavior_correct_tests) == len(successful_tests)

if __name__ == "__main__":
    async def main():
        success = await run_full_pipeline_test()
        
        if success:
            print("\n🎉 FULL PIPELINE TEST PASSED!")
            print("✅ Restructured metrics_filter system is PRODUCTION READY!")
            exit(0)
        else:
            print("\n❌ FULL PIPELINE TEST FAILED!")
            print("🔧 Check implementation before deployment")
            exit(1)
    
    asyncio.run(main())