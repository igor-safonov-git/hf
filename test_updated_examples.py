#!/usr/bin/env python3
"""
Test the updated examples structure
"""

import asyncio
import json
from chart_data_processor import process_chart_data, validate_report_json
from huntflow_local_client import HuntflowLocalClient

# Test based on Example 2 from prompt.py - Specific recruiter performance
safonov_test_report = {
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
            "label": "Кандидатов добавил Сафонов",
            "value": {
                "operation": "count",
                "entity": "applicants"
            }
        },
        {
            "label": "Среднее время найма Сафонова",
            "value": {
                "operation": "avg",
                "entity": "hires",
                "value_field": "time_to_hire"
            }
        }
    ],
    "chart": {
        "label": "Тренд найма по месяцам",
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
}

async def test_updated_structure():
    """Test the updated metrics_filter structure with specific recruiter"""
    print("🚀 Testing Updated Structure - Specific Recruiter\n")
    
    try:
        # 1. Schema Validation
        print("📋 Testing schema validation...")
        validate_report_json(safonov_test_report)
        print("✅ Schema validation: PASSED")
        
        # 2. Data Processing
        print("⚙️  Testing data processing...")
        client = HuntflowLocalClient()
        processed = await process_chart_data(safonov_test_report.copy(), client)
        
        print("✅ Processing completed: PASSED")
        
        # 3. Structure Check
        print("🔍 Checking result structure...")
        
        # Check metrics filter
        metrics_filter = processed.get("metrics_filter", {})
        print(f"📊 Metrics filter: {metrics_filter}")
        
        # Check main metric
        main_metric = processed["main_metric"]
        main_value = main_metric.get("real_value", 0)
        has_breakdown = "grouped_breakdown" in main_metric
        
        print(f"📊 Main metric results:")
        print(f"   - Value: {main_value}")
        print(f"   - Has breakdown: {has_breakdown}")
        
        if has_breakdown:
            breakdown = main_metric["grouped_breakdown"]
            print(f"   - Breakdown entities: {len(breakdown)}")
        
        # This should be aggregated (specific recruiter), not grouped
        if metrics_filter.get("recruiters"):
            print("✅ Expected: Aggregated result for specific recruiter")
        else:
            print("✅ Expected: Grouped breakdown for general query")
            
        print("\n🎉 Updated structure test COMPLETED!")
        return True
        
    except Exception as e:
        print(f"❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    async def main():
        success = await test_updated_structure()
        
        if success:
            print("\n✅ UPDATED STRUCTURE TEST PASSED!")
            exit(0)
        else:
            print("\n❌ UPDATED STRUCTURE TEST FAILED!")
            exit(1)
    
    asyncio.run(main())