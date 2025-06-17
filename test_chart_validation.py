#!/usr/bin/env python3
"""
Test Chart Helpers Input Validation
Validates that proper input validation prevents invalid inputs
"""
from chart_helpers import build_chart_data_cpu, build_chart_data_async, build_status_chart_data_cpu, ChartDataBuilder

def test_build_chart_data_cpu_validation():
    """Test input validation for build_chart_data_cpu"""
    valid_items = [{"status": "new", "count": 5}, {"status": "hired", "count": 3}]
    
    # Test valid inputs work
    result = build_chart_data_cpu(valid_items, "status")
    assert "labels" in result and "values" in result
    
    # Test invalid items type
    try:
        build_chart_data_cpu("not a list", "status")
        assert False, "Should raise ValueError for non-list items"
    except ValueError as e:
        assert "items must be a list" in str(e)
    
    # Test empty field
    try:
        build_chart_data_cpu(valid_items, "")
        assert False, "Should raise ValueError for empty field"
    except ValueError as e:
        assert "field parameter is required" in str(e)
    
    # Test non-string field
    try:
        build_chart_data_cpu(valid_items, 123)
        assert False, "Should raise ValueError for non-string field"
    except ValueError as e:
        assert "field must be a string" in str(e)
    
    # Test invalid limit
    try:
        build_chart_data_cpu(valid_items, "status", limit=0)
        assert False, "Should raise ValueError for zero limit"
    except ValueError as e:
        assert "limit must be a positive integer" in str(e)
    
    # Test invalid mapping type
    try:
        build_chart_data_cpu(valid_items, "status", mapping="not a dict")
        assert False, "Should raise ValueError for non-dict mapping"
    except ValueError as e:
        assert "mapping must be a dict" in str(e)
    
    # Test invalid sort_by_count type
    try:
        build_chart_data_cpu(valid_items, "status", sort_by_count="not a bool")
        assert False, "Should raise ValueError for non-bool sort_by_count"
    except ValueError as e:
        assert "sort_by_count must be a boolean" in str(e)

def test_build_status_chart_data_cpu_validation():
    """Test input validation for build_status_chart_data_cpu"""
    valid_counts = {1: 5, 2: 3}
    valid_mapping = {1: {"name": "New"}, 2: {"name": "Hired"}}
    
    # Test valid inputs work
    result = build_status_chart_data_cpu(valid_counts, valid_mapping)
    assert "labels" in result and "values" in result
    
    # Test invalid status_counts type
    try:
        build_status_chart_data_cpu("not a dict", valid_mapping)
        assert False, "Should raise ValueError for non-dict status_counts"
    except ValueError as e:
        assert "status_counts must be a dict" in str(e)
    
    # Test invalid status_mapping type
    try:
        build_status_chart_data_cpu(valid_counts, "not a dict")
        assert False, "Should raise ValueError for non-dict status_mapping"
    except ValueError as e:
        assert "status_mapping must be a dict" in str(e)
    
    # Test invalid status_counts key type
    try:
        build_status_chart_data_cpu({"string_key": 5}, valid_mapping)
        assert False, "Should raise ValueError for non-int status_counts keys"
    except ValueError as e:
        assert "status_counts keys must be integers" in str(e)
    
    # Test negative count value
    try:
        build_status_chart_data_cpu({1: -5}, valid_mapping)
        assert False, "Should raise ValueError for negative count"
    except ValueError as e:
        assert "status_counts values must be non-negative integers" in str(e)

def test_chart_data_builder_validation():
    """Test input validation for ChartDataBuilder methods"""
    valid_items = [{"status": "new", "count": 5}, {"status": "hired", "count": 3}]
    
    # Test pie_chart validation
    try:
        ChartDataBuilder.pie_chart(valid_items, "status", limit=0)
        assert False, "Should raise ValueError for zero limit"
    except ValueError as e:
        assert "limit must be a positive integer" in str(e)
    
    # Test time_series_prep validation
    try:
        ChartDataBuilder.time_series_prep("not a list", "date", "value")
        assert False, "Should raise ValueError for non-list items"
    except ValueError as e:
        assert "items must be a list" in str(e)
    
    try:
        ChartDataBuilder.time_series_prep(valid_items, "", "value")
        assert False, "Should raise ValueError for empty date_field"
    except ValueError as e:
        assert "date_field must be a non-empty string" in str(e)
    
    # Test top_performers validation
    try:
        ChartDataBuilder.top_performers(valid_items, "performer", "metric", limit=0)
        assert False, "Should raise ValueError for zero limit"
    except ValueError as e:
        assert "limit must be a positive integer" in str(e)

if __name__ == "__main__":
    try:
        test_build_chart_data_cpu_validation()
        print("✅ build_chart_data_cpu validation tests passed")
        
        test_build_status_chart_data_cpu_validation()
        print("✅ build_status_chart_data_cpu validation tests passed")
        
        test_chart_data_builder_validation()
        print("✅ ChartDataBuilder validation tests passed")
        
        print("\n🎉 All input validation tests passed!")
        
    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        import traceback
        traceback.print_exc()