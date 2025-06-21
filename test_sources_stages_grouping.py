#!/usr/bin/env python3
"""
Test sources and stages grouping functionality
Phase 5.5: Test with sources grouping and stages grouping to ensure generic grouping logic works
"""

import asyncio
import json
from chart_data_processor import process_chart_data, validate_report_json
from huntflow_local_client import HuntflowLocalClient

# Test report with sources grouping
sources_grouped_report = {
    "report_title": "Эффективность источников кандидатов",
    "period": "6 month",
    "metrics_group_by": "sources", 
    "main_metric": {
        "label": "Нанято через источник",
        "value": {
            "operation": "count",
            "entity": "hires", 
            "value_field": None,
            "filters": {
                "period": "6 month"
            }
        }
    },
    "secondary_metrics": [
        {
            "label": "Кандидатов через источник",
            "value": {
                "operation": "count",
                "entity": "applicants",
                "value_field": None,
                "filters": {
                    "period": "6 month"
                }
            }
        },
        {
            "label": "Конверсия источника",
            "value": {
                "operation": "avg",
                "entity": "sources",
                "value_field": "conversion",
                "filters": {
                    "period": "6 month"
                }
            }
        }
    ],
    "chart": {
        "label": "Источники по количеству кандидатов",
        "type": "bar",
        "x_label": "Источники",
        "y_label": "Количество кандидатов",
        "x_axis": {
            "operation": "count",
            "entity": "applicants",
            "value_field": None,
            "group_by": {"field": "sources"},
            "filters": {
                "period": "6 month"
            }
        },
        "y_axis": {
            "operation": "count", 
            "entity": "applicants",
            "value_field": None,
            "group_by": {"field": "sources"},
            "filters": {
                "period": "6 month"
            }
        }
    }
}

# Test report with stages grouping
stages_grouped_report = {
    "report_title": "Анализ воронки по этапам",
    "period": "3 month",
    "metrics_group_by": "stages", 
    "main_metric": {
        "label": "Кандидатов на этапе",
        "value": {
            "operation": "count",
            "entity": "applicants", 
            "value_field": None,
            "filters": {
                "period": "3 month"
            }
        }
    },
    "secondary_metrics": [
        {
            "label": "Нанято с этапа",
            "value": {
                "operation": "count",
                "entity": "hires",
                "value_field": None,
                "filters": {
                    "period": "3 month"
                }
            }
        },
        {
            "label": "Конверсия этапа",
            "value": {
                "operation": "avg",
                "entity": "stages",
                "value_field": "conversion",
                "filters": {
                    "period": "3 month"
                }
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
            "value_field": None,
            "group_by": {"field": "month"},
            "filters": {
                "period": "3 month"
            }
        },
        "y_axis": {
            "operation": "count", 
            "entity": "hires",
            "value_field": None,
            "group_by": {"field": "month"},
            "filters": {
                "period": "3 month"
            }
        }
    }
}

async def test_sources_grouping():
    """Test sources grouping functionality"""
    print("🎯 Testing Sources Grouping...")
    
    try:
        # Validate schema
        print("📋 Validating sources grouping schema...")
        validated = validate_report_json(sources_grouped_report)
        print("✅ Schema validation: PASSED")
        
        # Process with client
        print("⚙️  Processing sources grouping report...")
        client = HuntflowLocalClient()
        processed = await process_chart_data(sources_grouped_report.copy(), client)
        
        print("✅ Processing completed: PASSED")
        
        # Check structure
        print("📊 Checking sources grouped data structure...")
        
        assert processed.get("metrics_group_by") == "sources", "metrics_group_by should be 'sources'"
        print("✅ metrics_group_by field: CORRECT")
        
        # Check main metric breakdown
        main_metric = processed.get("main_metric", {})
        if main_metric.get("grouped_breakdown"):
            breakdown = main_metric["grouped_breakdown"]
            print(f"✅ Sources breakdown found: {len(breakdown)} sources")
            print(f"   Sample sources: {list(breakdown.keys())[:3]}...")
            print(f"   Total hires from sources: {main_metric.get('total_value', 0)}")
        else:
            print("ℹ️  Sources breakdown: EMPTY (no data available)")
        
        return True
        
    except Exception as e:
        print(f"❌ Sources grouping test FAILED: {e}")
        return False

async def test_stages_grouping():
    """Test stages grouping functionality"""
    print("\n🎯 Testing Stages Grouping...")
    
    try:
        # Validate schema
        print("📋 Validating stages grouping schema...")
        validated = validate_report_json(stages_grouped_report)
        print("✅ Schema validation: PASSED")
        
        # Process with client
        print("⚙️  Processing stages grouping report...")
        client = HuntflowLocalClient()
        processed = await process_chart_data(stages_grouped_report.copy(), client)
        
        print("✅ Processing completed: PASSED")
        
        # Check structure
        print("📊 Checking stages grouped data structure...")
        
        assert processed.get("metrics_group_by") == "stages", "metrics_group_by should be 'stages'"
        print("✅ metrics_group_by field: CORRECT")
        
        # Check main metric breakdown
        main_metric = processed.get("main_metric", {})
        if main_metric.get("grouped_breakdown"):
            breakdown = main_metric["grouped_breakdown"]
            print(f"✅ Stages breakdown found: {len(breakdown)} stages")
            print(f"   Pipeline stages: {list(breakdown.keys())}")
            print(f"   Total applicants in pipeline: {main_metric.get('total_value', 0)}")
        else:
            print("ℹ️  Stages breakdown: EMPTY (no data available)")
        
        return True
        
    except Exception as e:
        print(f"❌ Stages grouping test FAILED: {e}")
        return False

async def test_generic_grouping_logic():
    """Test that grouping logic works generically for different entity types"""
    print("\n🔧 Testing Generic Grouping Logic...")
    
    try:
        client = HuntflowLocalClient()
        
        # Process both reports
        sources_result = await process_chart_data(sources_grouped_report.copy(), client)
        stages_result = await process_chart_data(stages_grouped_report.copy(), client)
        
        # Check that both have consistent structure
        for name, result in [("Sources", sources_result), ("Stages", stages_result)]:
            print(f"\n📋 Checking {name} result structure:")
            
            # Should always have these fields
            assert "metrics_group_by" in result, f"{name}: Missing metrics_group_by"
            assert "main_metric" in result, f"{name}: Missing main_metric"
            assert "secondary_metrics" in result, f"{name}: Missing secondary_metrics"
            
            main_metric = result["main_metric"]
            assert "real_value" in main_metric, f"{name}: Missing real_value"
            assert "total_value" in main_metric, f"{name}: Missing total_value"
            
            # Secondary metrics should have same structure
            for i, sec_metric in enumerate(result.get("secondary_metrics", [])):
                assert "real_value" in sec_metric, f"{name}: Secondary {i} missing real_value"
                assert "total_value" in sec_metric, f"{name}: Secondary {i} missing total_value"
            
            print(f"✅ {name}: Consistent structure verified")
        
        print("\n🎉 Generic grouping logic test COMPLETED successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Generic grouping logic test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    async def main():
        print("🚀 Starting Sources & Stages Grouping Tests\n")
        
        sources_success = await test_sources_grouping()
        stages_success = await test_stages_grouping()
        generic_success = await test_generic_grouping_logic()
        
        if sources_success and stages_success and generic_success:
            print("\n✅ ALL GROUPING TESTS PASSED!")
            exit(0)
        else:
            print("\n❌ SOME GROUPING TESTS FAILED!")
            exit(1)
    
    asyncio.run(main())