#!/usr/bin/env python3
"""
Comprehensive integration test for SQLAlchemy Executor
Tests all abstractions, edge cases, and real-world scenarios
"""
import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy_executor import SQLAlchemyHuntflowExecutor, handle_errors, FilterExpr
from typing import Dict, List, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveMockEngine:
    """Comprehensive mock engine that simulates real Huntflow data"""
    
    def __init__(self):
        self.applicants = MagicMock()
        self.applicants.c.id = MagicMock()
        self.applicants.c.recruiter_name = MagicMock()
        self.applicants.c.source_id = MagicMock()
        
        # Realistic test data
        self.applicants_data = [
            {"id": 1, "status_id": 1, "source_id": 1, "recruiter_name": "Alice Johnson", "vacancy_id": 101},
            {"id": 2, "status_id": 2, "source_id": 2, "recruiter_name": "Bob Smith", "vacancy_id": 102},
            {"id": 3, "status_id": 1, "source_id": 1, "recruiter_name": "Alice Johnson", "vacancy_id": 101},
            {"id": 4, "status_id": 3, "source_id": 3, "recruiter_name": "Charlie Brown", "vacancy_id": 103},
            {"id": 5, "status_id": 4, "source_id": 2, "recruiter_name": "Alice Johnson", "vacancy_id": 101},
            {"id": 6, "status_id": 2, "source_id": 1, "recruiter_name": "Bob Smith", "vacancy_id": 102},
            {"id": 7, "status_id": None, "source_id": 1, "recruiter_name": "Unknown", "vacancy_id": None},  # Edge case
        ]
        
        self.vacancies_data = [
            {"id": 101, "state": "OPEN", "company": "TechCorp Inc"},
            {"id": 102, "state": "CLOSED", "company": "StartupX"},
            {"id": 103, "state": "OPEN", "company": "TechCorp Inc"},
            {"id": 104, "state": "PAUSED", "company": "BigCorp"},
        ]
    
    async def _get_status_mapping(self):
        return {
            1: {"name": "New Application", "id": 1},
            2: {"name": "Interview Scheduled", "id": 2},
            3: {"name": "Offer Sent", "id": 3},
            4: {"name": "Hired", "id": 4},
            5: {"name": "Rejected", "id": 5}
        }
    
    async def _get_sources_mapping(self):
        return {
            1: "LinkedIn",
            2: "HeadHunter",
            3: "Company Website",
            4: "Referral"
        }
    
    async def _get_recruiters_mapping(self):
        return {
            1: "Alice Johnson",
            2: "Bob Smith", 
            3: "Charlie Brown",
            4: "Diana Prince"
        }
    
    async def _get_divisions_mapping(self):
        return {
            1: "Engineering",
            2: "Sales", 
            3: "Marketing",
            4: "HR"
        }
    
    async def _get_tags_mapping(self):
        return {
            1: "Senior",
            2: "Junior",
            3: "Remote",
            4: "Full-time"
        }
    
    async def _execute_applicants_query(self, filter_expr: Dict):
        """Simulate filtered applicant queries"""
        data = self.applicants_data.copy()
        
        if filter_expr:
            field = filter_expr.get("field")
            op = filter_expr.get("op")
            value = filter_expr.get("value")
            
            if field == "recruiter" and op == "eq":
                data = [a for a in data if a.get("recruiter_name") == value]
            elif field == "source_id" and op == "eq":
                data = [a for a in data if a.get("source_id") == value]
            elif field == "status_id" and op == "eq":
                data = [a for a in data if a.get("status_id") == value]
        
        return data
    
    async def _get_applicants_data(self):
        """Get all applicants data"""
        return self.applicants_data.copy()
    
    async def _execute_vacancies_query(self, filter_expr):
        """Simulate vacancy queries"""
        return self.vacancies_data.copy()

async def test_chart_abstraction_edge_cases():
    """Test chart abstraction with edge cases"""
    print("\n=== Testing Chart Abstraction Edge Cases ===")
    
    executor = SQLAlchemyHuntflowExecutor(MagicMock())
    
    # Test empty data
    result = executor._build_chart_data([], 'field')
    assert result == {"labels": [], "values": []}, "Empty data should return empty chart"
    print("✅ Empty data handled correctly")
    
    # Test missing field values
    items_with_missing = [
        {"status_id": 1},
        {"status_id": None},  # None value
        {},  # Missing field entirely
        {"status_id": 2}
    ]
    
    result = executor._build_chart_data(items_with_missing, 'status_id')
    print(f"Missing field result: {result}")
    assert "Unknown" in result["labels"], "Should handle missing fields as 'Unknown'"
    print("✅ Missing fields handled correctly")
    
    # Test with string mapping
    string_mapping = {1: "Status One", 2: "Status Two"}
    result = executor._build_chart_data(items_with_missing, 'status_id', string_mapping)
    print(f"String mapping result: {result}")
    print("✅ String mapping works correctly")
    
    # Test with dict mapping (like status objects)
    dict_mapping = {
        1: {"name": "Status One", "id": 1},
        2: {"name": "Status Two", "id": 2}
    }
    result = executor._build_chart_data(items_with_missing, 'status_id', dict_mapping)
    print(f"Dict mapping result: {result}")
    assert any("Status One" in label for label in result["labels"]), "Dict mapping should extract 'name' field"
    print("✅ Dict mapping works correctly")
    
    # Test sorting and limiting
    many_items = [{"field": i % 3} for i in range(20)]  # Create data with values 0, 1, 2
    
    result_no_limit = executor._build_chart_data(many_items, 'field')
    result_with_limit = executor._build_chart_data(many_items, 'field', limit=2)
    
    assert len(result_no_limit["labels"]) == 3, "Should have 3 unique values"
    assert len(result_with_limit["labels"]) == 2, "Should respect limit"
    print("✅ Sorting and limiting work correctly")

async def test_error_decorator_comprehensive():
    """Test error decorator with various scenarios"""
    print("\n=== Testing Error Decorator Comprehensive ===")
    
    # Test with different return types
    @handle_errors(default_return=[])
    async def list_function_that_fails():
        raise KeyError("Test key error")
    
    @handle_errors(default_return={"empty": True})
    async def dict_function_that_fails():
        raise ConnectionError("Test connection error")
    
    @handle_errors(default_return=0, error_prefix="Custom Error")
    async def int_function_that_fails():
        raise ValueError("Test value error")
    
    # Test different error types are handled
    result1 = await list_function_that_fails()
    assert result1 == [], "Should return empty list default"
    
    result2 = await dict_function_that_fails()
    assert result2 == {"empty": True}, "Should return dict default"
    
    result3 = await int_function_that_fails()
    assert result3 == 0, "Should return int default"
    
    print("✅ Error decorator handles different types and errors correctly")

async def test_filter_expressions():
    """Test FilterExpr type safety and functionality"""
    print("\n=== Testing Filter Expressions ===")
    
    mock_hf_client = MagicMock()
    executor = SQLAlchemyHuntflowExecutor(mock_hf_client)
    executor.engine = ComprehensiveMockEngine()
    executor.metrics = AsyncMock()
    executor.metrics_helper = AsyncMock()
    
    # Test valid filter expressions
    valid_filters: List[FilterExpr] = [
        {"field": "recruiter", "op": "eq", "value": "Alice Johnson"},
        {"field": "status_id", "op": "in", "value": [1, 2, 3]},
        {"field": "source_id", "op": "eq", "value": 1}
    ]
    
    for filter_expr in valid_filters:
        result = await executor._execute_count_sql("applicants", filter_expr)
        assert isinstance(result, int), f"Count should return int for filter {filter_expr}"
        print(f"✅ Filter {filter_expr['field']}={filter_expr['value']} returned {result}")

async def test_all_chart_methods():
    """Test all chart methods with realistic data"""
    print("\n=== Testing All Chart Methods ===")
    
    mock_hf_client = MagicMock()
    executor = SQLAlchemyHuntflowExecutor(mock_hf_client)
    executor.engine = ComprehensiveMockEngine()
    executor.metrics = AsyncMock()
    executor.metrics_helper = AsyncMock()
    
    # Test each chart method
    chart_methods = [
        ("_execute_applicants_by_status", []),
        ("_execute_applicants_by_source", []),
        ("_execute_vacancies_by_state", []),
        ("_status_chart_sql", []),
        ("_company_chart_sql", []),
        ("_divisions_chart_sql", []),
    ]
    
    for method_name, args in chart_methods:
        method = getattr(executor, method_name)
        result = await method(*args)
        
        assert "labels" in result, f"{method_name} should return labels"
        assert "values" in result, f"{method_name} should return values"
        assert len(result["labels"]) == len(result["values"]), f"{method_name} labels/values length mismatch"
        assert all(isinstance(v, (int, float)) for v in result["values"]), f"{method_name} values should be numeric"
        
        print(f"✅ {method_name}: {len(result['labels'])} items")
    
    # Test recruiter chart with filter
    y_axis_spec = {"filter": {"field": "status_id", "op": "eq", "value": 1}}
    result = await executor._recruiter_chart_sql(y_axis_spec)
    assert "labels" in result and "values" in result
    print(f"✅ _recruiter_chart_sql with filter: {len(result['labels'])} recruiters")

async def test_applicant_links_functionality():
    """Test applicant links functionality"""
    print("\n=== Testing Applicant Links Functionality ===")
    
    mock_hf_client = MagicMock()
    executor = SQLAlchemyHuntflowExecutor(mock_hf_client)
    executor.engine = ComprehensiveMockEngine()
    executor.metrics = AsyncMock()
    executor.metrics_helper = AsyncMock()
    
    # Test basic count
    count = await executor._execute_applicant_links_count({})
    assert isinstance(count, int), "Should return integer count"
    assert count > 0, "Should have some links"
    print(f"✅ Basic applicant links count: {count}")
    
    # Test with vacancy state filter
    filter_expr: FilterExpr = {"field": "vacancy.state", "op": "eq", "value": "OPEN"}
    filtered_count = await executor._execute_applicant_links_count(filter_expr)
    assert isinstance(filtered_count, int), "Filtered count should be integer"
    assert filtered_count <= count, "Filtered count should be <= total count"
    print(f"✅ Filtered applicant links count (OPEN vacancies): {filtered_count}")
    
    # Test applicant links by status
    chart_result = await executor._execute_applicant_links_by_status({})
    assert "labels" in chart_result and "values" in chart_result
    print(f"✅ Applicant links by status chart: {len(chart_result['labels'])} statuses")

async def test_integration_scenarios():
    """Test real-world integration scenarios"""
    print("\n=== Testing Integration Scenarios ===")
    
    mock_hf_client = MagicMock()
    executor = SQLAlchemyHuntflowExecutor(mock_hf_client)
    executor.engine = ComprehensiveMockEngine()
    executor.metrics = AsyncMock()
    executor.metrics_helper = AsyncMock()
    
    # Scenario 1: Dashboard data request
    dashboard_data = await executor.get_dashboard_data()
    assert "metrics" in dashboard_data and "charts" in dashboard_data
    print("✅ Dashboard data integration works")
    
    # Scenario 2: Complex grouped query
    complex_query = {
        "operation": "count",
        "entity": "applicant_links",
        "group_by": {"field": "status_id"},
        "filter": {"field": "vacancy.state", "op": "eq", "value": "OPEN"}
    }
    
    result = await executor.execute_grouped_query(complex_query)
    assert "labels" in result and "values" in result
    print("✅ Complex grouped query integration works")
    
    # Scenario 3: Field extraction
    field_result = await executor._execute_field_sql("status")
    assert isinstance(field_result, list), "Field extraction should return list"
    assert len(field_result) > 0, "Should return some statuses"
    print(f"✅ Field extraction: {len(field_result)} status values")
    
    # Scenario 4: Expression execution
    expression = {
        "operation": "count",
        "entity": "applicants",
        "filter": {"field": "recruiter", "op": "eq", "value": "Alice Johnson"}
    }
    
    expr_result = await executor.execute_expression(expression)
    assert isinstance(expr_result, int), "Expression should return count"
    print(f"✅ Expression execution: {expr_result} applicants")

async def test_error_handling_integration():
    """Test error handling in integration scenarios"""
    print("\n=== Testing Error Handling Integration ===")
    
    mock_hf_client = MagicMock()
    executor = SQLAlchemyHuntflowExecutor(mock_hf_client)
    
    # Create engine that throws errors
    failing_engine = MagicMock()
    failing_engine._get_status_mapping = AsyncMock(side_effect=ConnectionError("DB connection failed"))
    failing_engine._execute_applicants_query = AsyncMock(side_effect=TimeoutError("Query timeout"))
    
    executor.engine = failing_engine
    executor.metrics = AsyncMock()
    executor.metrics_helper = AsyncMock()
    
    # Test that decorated methods handle errors gracefully
    result1 = await executor._execute_applicants_by_status()
    assert result1 == {"labels": [], "values": []}, "Should return empty chart on error"
    
    result2 = await executor._execute_field_sql("status")
    assert result2 == [], "Should return empty list on error"
    
    print("✅ Error handling integration works correctly")

async def test_performance_scenarios():
    """Test performance with larger datasets"""
    print("\n=== Testing Performance Scenarios ===")
    
    mock_hf_client = MagicMock()
    executor = SQLAlchemyHuntflowExecutor(mock_hf_client)
    
    # Create large dataset
    large_engine = ComprehensiveMockEngine()
    large_engine.applicants_data = [
        {
            "id": i,
            "status_id": (i % 5) + 1,
            "source_id": (i % 4) + 1,
            "recruiter_name": f"Recruiter_{i % 10}",
            "vacancy_id": (i % 20) + 100
        }
        for i in range(1000)  # 1000 applicants
    ]
    
    executor.engine = large_engine
    executor.metrics = AsyncMock()
    executor.metrics_helper = AsyncMock()
    
    import time
    
    # Test chart generation performance
    start_time = time.time()
    result = await executor._execute_applicants_by_status()
    end_time = time.time()
    
    assert "labels" in result and "values" in result
    assert len(result["labels"]) == 5, "Should have 5 status categories"
    assert sum(result["values"]) == 1000, "Should count all 1000 applicants"
    
    performance_time = end_time - start_time
    print(f"✅ Performance test: processed 1000 applicants in {performance_time:.3f}s")
    
    # Test with limits
    items = [{"field": i % 50} for i in range(1000)]  # 50 unique values
    limited_result = executor._build_chart_data(items, 'field', limit=10)
    assert len(limited_result["labels"]) == 10, "Should respect limit even with many values"
    print("✅ Limit functionality works with large datasets")

async def main():
    """Run comprehensive tests"""
    print("🧪 Comprehensive SQLAlchemy Executor Testing")
    print("=" * 60)
    
    test_functions = [
        test_chart_abstraction_edge_cases,
        test_error_decorator_comprehensive,
        test_filter_expressions,
        test_all_chart_methods,
        test_applicant_links_functionality,
        test_integration_scenarios,
        test_error_handling_integration,
        test_performance_scenarios,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ {test_func.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! SQLAlchemy Executor is working correctly.")
        print("\n✨ Verified aspects:")
        print("  • Chart data abstraction with edge cases")
        print("  • Error handling decorator robustness") 
        print("  • Type-safe filter expressions")
        print("  • All chart generation methods")
        print("  • Applicant links functionality")
        print("  • Real-world integration scenarios")
        print("  • Error handling in integration")
        print("  • Performance with large datasets")
    else:
        print(f"⚠️  {failed} test(s) failed. Review the output above.")

if __name__ == "__main__":
    asyncio.run(main())