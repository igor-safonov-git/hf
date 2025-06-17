#!/usr/bin/env python3
"""
Test script for SQLAlchemy Executor improvements
Tests the chart data abstraction and error handling decorator
"""
import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy_executor import SQLAlchemyHuntflowExecutor, handle_errors

# Set up logging to see our decorator in action
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockEngine:
    """Mock virtual engine for testing"""
    
    def __init__(self):
        self.applicants = MagicMock()
        self.applicants.c.id = MagicMock()
        self.applicants.c.recruiter_name = MagicMock()
        self.applicants.c.source_id = MagicMock()
    
    async def _get_status_mapping(self):
        return {
            1: {"name": "New Application"},
            2: {"name": "Interview Scheduled"},
            3: {"name": "Offer Sent"},
            4: {"name": "Hired"}
        }
    
    async def _get_sources_mapping(self):
        return {
            1: "LinkedIn",
            2: "HeadHunter",
            3: "Website"
        }
    
    async def _execute_applicants_query(self, filter_expr):
        return [
            {"id": 1, "status_id": 1, "source_id": 1, "recruiter_name": "Alice"},
            {"id": 2, "status_id": 2, "source_id": 2, "recruiter_name": "Bob"},
            {"id": 3, "status_id": 1, "source_id": 1, "recruiter_name": "Alice"},
            {"id": 4, "status_id": 3, "source_id": 3, "recruiter_name": "Charlie"}
        ]
    
    async def _execute_vacancies_query(self, filter_expr):
        return [
            {"id": 1, "state": "OPEN", "company": "TechCorp"},
            {"id": 2, "state": "CLOSED", "company": "StartupX"},
            {"id": 3, "state": "OPEN", "company": "TechCorp"}
        ]

async def test_chart_data_abstraction():
    """Test the _build_chart_data helper method"""
    print("\n=== Testing Chart Data Abstraction ===")
    
    mock_hf_client = MagicMock()
    executor = SQLAlchemyHuntflowExecutor(mock_hf_client)
    executor.engine = MockEngine()
    executor.metrics = AsyncMock()
    executor.metrics_helper = AsyncMock()
    
    # Test data
    test_items = [
        {"status_id": 1, "name": "John"},
        {"status_id": 2, "name": "Jane"},
        {"status_id": 1, "name": "Bob"},
        {"status_id": 3, "name": "Alice"}
    ]
    
    test_mapping = {
        1: {"name": "New"},
        2: {"name": "In Progress"},
        3: {"name": "Completed"}
    }
    
    # Test basic functionality
    result = await executor._build_chart_data(test_items, 'status_id', test_mapping)
    
    print(f"Chart data result: {result}")
    
    # Verify the result
    expected_labels = ["New", "In Progress", "Completed"]  # Should be sorted by count
    expected_values = [2, 1, 1]
    
    assert result["labels"][0] == "New"  # Most frequent should be first
    assert result["values"][0] == 2
    print("✅ Chart data abstraction working correctly")

async def test_error_handling_decorator():
    """Test the @handle_errors decorator"""
    print("\n=== Testing Error Handling Decorator ===")
    
    @handle_errors(default_return={"error": "handled"})
    async def failing_function():
        raise ValueError("This is a test error")
    
    @handle_errors(default_return=0)
    async def working_function():
        return 42
    
    # Test error case
    result1 = await failing_function()
    print(f"Error case result: {result1}")
    assert result1 == {"error": "handled"}
    print("✅ Error handling working correctly")
    
    # Test success case
    result2 = await working_function()
    print(f"Success case result: {result2}")
    assert result2 == 42
    print("✅ Success case working correctly")

async def test_chart_methods():
    """Test the refactored chart methods"""
    print("\n=== Testing Chart Methods ===")
    
    mock_hf_client = MagicMock()
    executor = SQLAlchemyHuntflowExecutor(mock_hf_client)
    executor.engine = MockEngine()
    executor.metrics = AsyncMock()
    executor.metrics_helper = AsyncMock()
    
    # Test applicants by status
    result = await executor._execute_applicants_by_status()
    print(f"Applicants by status: {result}")
    
    # Should have labels and values
    assert "labels" in result
    assert "values" in result
    assert len(result["labels"]) == len(result["values"])
    print("✅ Applicants by status chart working")
    
    # Test applicants by source
    result = await executor._execute_applicants_by_source()
    print(f"Applicants by source: {result}")
    
    assert "labels" in result
    assert "values" in result
    print("✅ Applicants by source chart working")
    
    # Test vacancies by state
    result = await executor._execute_vacancies_by_state()
    print(f"Vacancies by state: {result}")
    
    assert "labels" in result
    assert "values" in result
    print("✅ Vacancies by state chart working")

async def test_integration():
    """Test full integration"""
    print("\n=== Testing Integration ===")
    
    mock_hf_client = MagicMock()
    executor = SQLAlchemyHuntflowExecutor(mock_hf_client)
    executor.engine = MockEngine()
    executor.metrics = AsyncMock()
    executor.metrics_helper = AsyncMock()
    
    # Test grouped query
    query_spec = {
        "operation": "count",
        "entity": "applicants",
        "group_by": {"field": "status_id"},
        "filter": {}
    }
    
    result = await executor.execute_grouped_query(query_spec)
    print(f"Grouped query result: {result}")
    
    assert "labels" in result
    assert "values" in result
    print("✅ Integration test passed")

async def main():
    """Run all tests"""
    print("🧪 Testing SQLAlchemy Executor Improvements")
    
    try:
        await test_chart_data_abstraction()
        await test_error_handling_decorator()
        await test_chart_methods()
        await test_integration()
        
        print("\n🎉 All tests passed! The abstractions are working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())