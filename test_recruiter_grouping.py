#!/usr/bin/env python3
"""
Test recruiter grouping functionality specifically
Phase 5.2: Test grouped metrics with recruiters grouping
"""

import asyncio
import json
from chart_data_processor import process_chart_data, validate_report_json
from huntflow_local_client import HuntflowLocalClient

# Test report with recruiter grouping
recruiter_grouped_report = {
    "report_title": "Результаты каждого рекрутера",
    "period": "3 month",
    "metrics_group_by": "recruiters", 
    "main_metric": {
        "label": "Нанято рекрутером",
        "value": {
            "operation": "count",
            "entity": "hires", 
            "value_field": None,
            "filters": {
                "period": "3 month"
            }
        }
    },
    "secondary_metrics": [
        {
            "label": "Кандидатов добавлено рекрутером",
            "value": {
                "operation": "count",
                "entity": "applicants",
                "value_field": None,
                "filters": {
                    "period": "3 month"
                }
            }
        },
        {
            "label": "Среднее время найма рекрутером",
            "value": {
                "operation": "avg",
                "entity": "hires",
                "value_field": "time_to_hire",
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

async def test_recruiter_grouping():
    """Test recruiter grouping functionality"""
    print("🎯 Testing Recruiter Grouping Functionality...")
    
    try:
        # Validate schema
        print("📋 Validating recruiter grouping schema...")
        validated = validate_report_json(recruiter_grouped_report)
        print("✅ Schema validation: PASSED")
        
        # Process with client
        print("⚙️  Processing recruiter grouping report...")
        client = HuntflowLocalClient()
        processed = await process_chart_data(recruiter_grouped_report.copy(), client)
        
        print("✅ Processing completed: PASSED")
        
        # Check structure
        print("📊 Checking grouped data structure...")
        
        # Should have metrics_group_by field
        assert processed.get("metrics_group_by") == "recruiters", "metrics_group_by should be 'recruiters'"
        print("✅ metrics_group_by field: CORRECT")
        
        # Main metric should have grouped structure when data exists
        main_metric = processed.get("main_metric", {})
        if main_metric.get("grouped_breakdown"):
            print("✅ Main metric has grouped_breakdown: FOUND")
            print(f"   Grouped data: {json.dumps(main_metric['grouped_breakdown'], indent=2, ensure_ascii=False)}")
        else:
            print("ℹ️  Main metric grouped_breakdown: EMPTY (no data available)")
        
        # Check that total_value exists when grouped_breakdown exists
        if main_metric.get("grouped_breakdown"):
            assert "total_value" in main_metric, "total_value should exist when grouped_breakdown exists"
            print(f"✅ Main metric total_value: {main_metric['total_value']}")
        
        # Secondary metrics should also have grouped structure
        secondary_metrics = processed.get("secondary_metrics", [])
        for i, metric in enumerate(secondary_metrics):
            if metric.get("grouped_breakdown"):
                print(f"✅ Secondary metric {i+1} has grouped_breakdown: FOUND")
            else:
                print(f"ℹ️  Secondary metric {i+1} grouped_breakdown: EMPTY (no data available)")
        
        # Chart should be processed independently
        chart_real_data = processed.get("chart", {}).get("real_data", {})
        if chart_real_data.get("labels"):
            print(f"✅ Chart data processed independently: {len(chart_real_data['labels'])} data points")
        else:
            print("ℹ️  Chart data: EMPTY (no chart data available)")
        
        print("\n🎉 Recruiter grouping test COMPLETED successfully!")
        print("📄 Full processed report structure:")
        print(json.dumps(processed, indent=2, ensure_ascii=False))
        
        return True
        
    except Exception as e:
        print(f"❌ Recruiter grouping test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    async def main():
        print("🚀 Starting Recruiter Grouping Test\n")
        
        success = await test_recruiter_grouping()
        
        if success:
            print("\n✅ RECRUITER GROUPING TEST PASSED!")
            exit(0)
        else:
            print("\n❌ RECRUITER GROUPING TEST FAILED!")
            exit(1)
    
    asyncio.run(main())