#!/usr/bin/env python3
"""
Basic test for new metrics_filter structure
"""

import asyncio
import json
from chart_data_processor import process_chart_data, validate_report_json
from huntflow_local_client import HuntflowLocalClient

# Test report with new metrics_filter structure
basic_test_report = {
    "report_title": "Basic Metrics Filter Test",
    "metrics_filter": {
        "period": "3 month"
    },
    "main_metric": {
        "label": "Total Hires",
        "value": {
            "operation": "count",
            "entity": "hires"
        }
    },
    "secondary_metrics": [
        {
            "label": "Total Applicants",
            "value": {
                "operation": "count",
                "entity": "applicants"
            }
        },
        {
            "label": "Open Vacancies",
            "value": {
                "operation": "count",
                "entity": "vacancies"
            }
        }
    ],
    "chart": {
        "label": "Pipeline by Stages",
        "type": "bar",
        "x_label": "Stages",
        "y_label": "Number of Candidates",
        "x_axis": {
            "operation": "count",
            "entity": "stages",
            "group_by": {"field": "stages"}
        },
        "y_axis": {
            "operation": "count",
            "entity": "applicants",
            "group_by": {"field": "stages"}
        }
    }
}

async def test_basic_metrics_filter():
    """Test basic metrics_filter functionality"""
    print("🚀 Testing Basic Metrics Filter Structure\n")
    
    try:
        # 1. Schema Validation
        print("📋 Testing schema validation...")
        validate_report_json(basic_test_report)
        print("✅ Schema validation: PASSED")
        
        # 2. Data Processing
        print("⚙️  Testing data processing...")
        client = HuntflowLocalClient()
        processed = await process_chart_data(basic_test_report.copy(), client)
        
        print("✅ Processing completed: PASSED")
        
        # 3. Structure Check
        print("🔍 Checking result structure...")
        
        # Check required fields
        assert "metrics_filter" in processed, "Missing metrics_filter"
        assert "main_metric" in processed, "Missing main_metric"
        assert "secondary_metrics" in processed, "Missing secondary_metrics"
        
        # Check metrics values
        main_metric = processed["main_metric"]
        assert "real_value" in main_metric, "Missing main_metric.real_value"
        
        print(f"📊 Results:")
        print(f"   - Main metric value: {main_metric.get('real_value', 'N/A')}")
        print(f"   - Metrics filter: {processed.get('metrics_filter', 'N/A')}")
        
        # Check if grouped breakdown exists
        if "grouped_breakdown" in main_metric:
            breakdown = main_metric["grouped_breakdown"]
            print(f"   - Grouped breakdown: {len(breakdown)} entities found")
        else:
            print("   - No grouped breakdown (aggregated result)")
        
        print("\n🎉 Basic metrics filter test COMPLETED!")
        return True
        
    except Exception as e:
        print(f"❌ Basic test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    async def main():
        success = await test_basic_metrics_filter()
        
        if success:
            print("\n✅ BASIC METRICS FILTER TEST PASSED!")
            exit(0)
        else:
            print("\n❌ BASIC METRICS FILTER TEST FAILED!")
            exit(1)
    
    asyncio.run(main())