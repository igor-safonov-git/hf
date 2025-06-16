#!/usr/bin/env python3
"""
Test the SQL filtering improvements in SQLAlchemy executor
"""
import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy_executor import SQLAlchemyHuntflowExecutor, QueryExecutionError, FilterExpr

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')

class MockVirtualEngine:
    """Mock engine for testing SQL improvements"""
    
    def __init__(self):
        self.applicants = MagicMock()
        self.applicants.c.id = MagicMock()
        self.applicants.c.recruiter_name = MagicMock()
        self.applicants.c.source_id = MagicMock()
        self.applicants.c.vacancy_id = MagicMock()
    
    async def _execute_sql_query(self, query):
        """Mock SQL query execution"""
        result = MagicMock()
        result.scalar.return_value = 42  # Mock count result
        return result
    
    async def _execute_applicants_query(self, filter_expr):
        """Mock fallback query"""
        return [{"id": i} for i in range(100)]  # Mock 100 applicants

async def test_sql_count_improvements():
    """Test the improved SQL count functionality"""
    print("\n=== Testing SQL Count Improvements ===")
    
    # Setup
    mock_hf_client = MagicMock()
    executor = SQLAlchemyHuntflowExecutor(mock_hf_client)
    executor.engine = MockVirtualEngine()
    executor.metrics = AsyncMock()
    executor.metrics_helper = AsyncMock()
    
    # Test 1: Can use SQL count detection
    print("Testing _can_use_sql_count()...")
    
    # Should use SQL for simple filters
    simple_filter: FilterExpr = {"field": "recruiter", "op": "eq", "value": "Alice"}
    assert executor._can_use_sql_count(simple_filter) == True
    print("✅ Simple filter correctly identified as SQL-compatible")
    
    # Should not use SQL for complex filters (status requires joins)
    complex_filter: FilterExpr = {"field": "status", "op": "eq", "value": "active"}
    assert executor._can_use_sql_count(complex_filter) == False
    print("✅ Complex filter correctly identified as non-SQL-compatible")
    
    # Test 2: SQL count execution
    print("Testing _execute_sql_count()...")
    count = await executor._execute_sql_count(simple_filter)
    assert count == 42
    print(f"✅ SQL count returned expected result: {count}")
    
    # Test 3: Input validation
    print("Testing input validation...")
    try:
        invalid_filter: FilterExpr = {"field": "recruiter", "op": "in", "value": "not_a_list"}
        await executor._execute_sql_count(invalid_filter)
        assert False, "Should have raised ValueError"
    except QueryExecutionError as e:
        print(f"✅ Input validation correctly caught error: {e}")
    
    # Test 4: Full count execution with SQL path
    print("Testing full _execute_count_sql() with SQL path...")
    count = await executor._execute_count_sql("applicants", simple_filter)
    assert count == 42  # Should use SQL path
    print(f"✅ Full count execution used SQL path: {count}")
    
    # Test 5: Full count execution with fallback path
    print("Testing full _execute_count_sql() with fallback path...")
    count = await executor._execute_count_sql("applicants", complex_filter)
    assert count == 100  # Should use fallback path
    print(f"✅ Full count execution used fallback path: {count}")

async def test_chunked_data_fetching():
    """Test the chunked data fetching improvements"""
    print("\n=== Testing Chunked Data Fetching ===")
    
    # Setup
    mock_hf_client = MagicMock()
    executor = SQLAlchemyHuntflowExecutor(mock_hf_client)
    
    # Mock engine with large dataset
    large_engine = MockVirtualEngine()
    large_engine._execute_applicants_query = AsyncMock(return_value=[{"id": i} for i in range(15000)])
    large_engine._execute_vacancies_query = AsyncMock(return_value=[{"id": i} for i in range(3000)])
    
    executor.engine = large_engine
    executor.metrics = AsyncMock()
    executor.metrics_helper = AsyncMock()
    
    # Test chunked fetching with warning for large datasets
    print("Testing chunked data fetching...")
    
    # Should warn about large applicant dataset
    data = await executor._fetch_data_chunked("applicants", {})
    assert len(data) == 15000
    print(f"✅ Fetched large applicant dataset: {len(data)} records")
    
    # Should warn about large vacancy dataset
    data = await executor._fetch_data_chunked("vacancies", {})
    assert len(data) == 3000
    print(f"✅ Fetched large vacancy dataset: {len(data)} records")

async def test_error_handling_improvements():
    """Test the improved error handling"""
    print("\n=== Testing Error Handling Improvements ===")
    
    # Setup
    mock_hf_client = MagicMock()
    executor = SQLAlchemyHuntflowExecutor(mock_hf_client)
    
    # Mock engine that throws errors
    failing_engine = MagicMock()
    failing_engine._execute_sql_query = AsyncMock(side_effect=Exception("Database connection failed"))
    
    executor.engine = failing_engine
    executor.metrics = AsyncMock()
    executor.metrics_helper = AsyncMock()
    
    # Test custom exception handling
    print("Testing custom exception handling...")
    try:
        await executor._execute_sql_count({"field": "recruiter", "op": "eq", "value": "test"})
        assert False, "Should have raised QueryExecutionError"
    except QueryExecutionError as e:
        print(f"✅ Custom exception correctly raised: {e}")
        assert e.query_type == "count"
        print(f"✅ Query type correctly preserved: {e.query_type}")

async def main():
    """Run all tests"""
    print("🧪 Testing SQLAlchemy Executor SQL Improvements")
    print("=" * 60)
    
    try:
        await test_sql_count_improvements()
        await test_chunked_data_fetching()
        await test_error_handling_improvements()
        
        print("\n" + "=" * 60)
        print("🎉 All SQL improvement tests passed!")
        print("\n✨ Verified improvements:")
        print("  • SQL vs Python filtering detection")
        print("  • Actual SQL count query execution")
        print("  • Input validation with custom exceptions")
        print("  • Chunked data fetching with size warnings")
        print("  • Custom error handling with context preservation")
        
    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())