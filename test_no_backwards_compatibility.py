#!/usr/bin/env python3
"""
Test that backward compatibility is removed and metrics_group_by is required
"""

import asyncio
import json
from chart_data_processor import process_chart_data, validate_report_json
from huntflow_local_client import HuntflowLocalClient

# Test report without metrics_group_by (should fail)
report_without_grouping = {
    "report_title": "Test Report",
    "period": "1 month", 
    "main_metric": {
        "label": "Total Hires",
        "value": {
            "operation": "count",
            "entity": "hires",
            "filters": {"period": "1 month"}
        }
    },
    "secondary_metrics": [
        {
            "label": "Total Applicants",
            "value": {
                "operation": "count", 
                "entity": "applicants",
                "filters": {"period": "1 month"}
            }
        },
        {
            "label": "Open Vacancies",
            "value": {
                "operation": "count",
                "entity": "vacancies", 
                "filters": {"vacancies": "open"}
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
            "group_by": {"field": "stages"},
            "filters": {"period": "1 month"}
        },
        "y_axis": {
            "operation": "count", 
            "entity": "applicants",
            "group_by": {"field": "stages"},
            "filters": {"period": "1 month"}
        }
    }
}

# Test report with null metrics_group_by (should fail)
report_with_null_grouping = {
    **report_without_grouping,
    "metrics_group_by": None
}

# Test report with valid metrics_group_by (should pass)
report_with_valid_grouping = {
    **report_without_grouping,
    "metrics_group_by": "recruiters"
}

async def test_no_backwards_compatibility():
    """Test that backward compatibility is completely removed"""
    print("🚫 Testing No Backward Compatibility...")
    
    # Test 1: Missing metrics_group_by should fail
    print("\n📋 Test 1: Missing metrics_group_by...")
    try:
        validate_report_json(report_without_grouping)
        print("❌ FAILED: Should have rejected missing metrics_group_by")
        return False
    except Exception as e:
        print(f"✅ PASSED: Correctly rejected missing field - {e}")
    
    # Test 2: Null metrics_group_by should fail
    print("\n📋 Test 2: Null metrics_group_by...")
    try:
        validate_report_json(report_with_null_grouping)
        print("❌ FAILED: Should have rejected null metrics_group_by")
        return False
    except Exception as e:
        print(f"✅ PASSED: Correctly rejected null field - {e}")
    
    # Test 3: Valid metrics_group_by should pass
    print("\n📋 Test 3: Valid metrics_group_by...")
    try:
        validate_report_json(report_with_valid_grouping)
        print("✅ PASSED: Accepted valid metrics_group_by")
    except Exception as e:
        print(f"❌ FAILED: Should have accepted valid field - {e}")
        return False
    
    # Test 4: Process report with grouping
    print("\n⚙️  Test 4: Processing report with metrics_group_by...")
    try:
        client = HuntflowLocalClient()
        processed = await process_chart_data(report_with_valid_grouping.copy(), client)
        
        # Check that it always produces grouped structure
        main_metric = processed.get("main_metric", {})
        has_grouped_breakdown = "grouped_breakdown" in main_metric
        has_total_value = "total_value" in main_metric
        
        print(f"✅ Processing completed successfully")
        print(f"   - Has grouped_breakdown: {has_grouped_breakdown}")
        print(f"   - Has total_value: {has_total_value}")
        print(f"   - metrics_group_by: {processed.get('metrics_group_by')}")
        
        if processed.get('metrics_group_by') != 'recruiters':
            print("❌ FAILED: metrics_group_by not preserved")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: Processing error - {e}")
        return False
    
    print("\n🎉 All no-backward-compatibility tests PASSED!")
    return True

if __name__ == "__main__":
    async def main():
        print("🚀 Testing Removal of Backward Compatibility\n")
        
        success = await test_no_backwards_compatibility()
        
        if success:
            print("\n✅ NO BACKWARD COMPATIBILITY VERIFIED!")
            exit(0)
        else:
            print("\n❌ BACKWARD COMPATIBILITY REMOVAL FAILED!")
            exit(1)
    
    asyncio.run(main())