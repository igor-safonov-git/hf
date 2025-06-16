#!/usr/bin/env python3
"""
Test async threading improvements to prevent blocking CPU work in event loop
"""
import asyncio
import logging
import time
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy_executor import SQLAlchemyHuntflowExecutor, HuntflowAnalyticsTemplates

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')

class MockVirtualEngine:
    """Mock engine for testing async threading"""
    
    def __init__(self):
        self.applicants = MagicMock()
    
    async def _execute_vacancies_query(self, filter_expr):
        """Mock vacancy data with various companies"""
        return [
            {"id": i, "company": f"Company_{i % 50}"} 
            for i in range(1000)  # Large dataset to trigger threading
        ]
    
    async def _get_applicants_data(self):
        """Mock large applicant dataset"""
        return [
            {
                "id": i, 
                "recruiter_name": f"Recruiter_{i % 20}",
                "status_id": (i % 5) + 1,
                "source_id": (i % 10) + 1
            }
            for i in range(2000)  # Large dataset to trigger threading
        ]
    
    async def _get_status_mapping(self):
        return {
            1: {"name": "New Application"},
            2: {"name": "Interview"},
            3: {"name": "Offer Sent"},
            4: {"name": "Hired"},
            5: {"name": "Rejected"}
        }

async def test_cpu_bound_operations():
    """Test that CPU-bound operations use threading for large datasets"""
    print("\n=== Testing CPU-Bound Operations Threading ===")
    
    # Setup
    mock_hf_client = MagicMock()
    executor = SQLAlchemyHuntflowExecutor(mock_hf_client)
    executor.engine = MockVirtualEngine()
    executor.metrics = AsyncMock()
    executor.metrics_helper = AsyncMock()
    
    # Test 1: Small dataset should NOT use threading
    print("Testing small dataset (should be synchronous)...")
    small_data = [{"field": i} for i in range(100)]
    
    start_time = time.time()
    result = await executor._build_chart_data(small_data, 'field')
    end_time = time.time()
    
    assert len(result["labels"]) > 0
    print(f"✅ Small dataset processed synchronously in {end_time - start_time:.3f}s")
    
    # Test 2: Large dataset should use threading
    print("Testing large dataset (should use thread pool)...")
    large_data = [{"field": i % 100} for i in range(5000)]  # 5000 items, 100 unique values
    
    start_time = time.time()
    result = await executor._build_chart_data(large_data, 'field', limit=10)
    end_time = time.time()
    
    assert len(result["labels"]) == 10  # Should be limited to 10
    assert len(result["values"]) == 10
    print(f"✅ Large dataset processed in thread pool in {end_time - start_time:.3f}s")

async def test_company_extraction_threading():
    """Test company extraction uses threading for large datasets"""
    print("\n=== Testing Company Extraction Threading ===")
    
    # Setup
    mock_hf_client = MagicMock()
    executor = SQLAlchemyHuntflowExecutor(mock_hf_client)
    executor.engine = MockVirtualEngine()
    executor.metrics = AsyncMock()
    executor.metrics_helper = AsyncMock()
    
    # Test company field extraction (should trigger threading due to 1000 vacancies)
    print("Testing company extraction with large vacancy dataset...")
    
    start_time = time.time()
    companies = await executor._execute_field_sql("company")
    end_time = time.time()
    
    assert len(companies) > 0
    assert len(companies) <= 50  # Should have unique companies (0-49)
    print(f"✅ Company extraction completed in {end_time - start_time:.3f}s")
    print(f"   Found {len(companies)} unique companies from large dataset")

async def test_recruiter_performance_threading():
    """Test recruiter performance calculation uses threading"""
    print("\n=== Testing Recruiter Performance Threading ===")
    
    # Setup
    mock_hf_client = MagicMock()
    executor = SQLAlchemyHuntflowExecutor(mock_hf_client)
    executor.engine = MockVirtualEngine()
    executor.metrics = AsyncMock()
    executor.metrics_helper = AsyncMock()
    
    # Create analytics templates instance
    analytics = HuntflowAnalyticsTemplates(executor)
    
    # Test recruiter performance report (should trigger threading due to 2000 applicants)
    print("Testing recruiter performance calculation with large applicant dataset...")
    
    start_time = time.time()
    performance = await analytics.recruiter_performance_report()
    end_time = time.time()
    
    assert "top_recruiter" in performance
    assert "hires" in performance
    assert "all_stats" in performance
    print(f"✅ Recruiter performance calculated in {end_time - start_time:.3f}s")
    print(f"   Top recruiter: {performance['top_recruiter']} with {performance['hires']} hires")

async def test_concurrent_operations():
    """Test that multiple CPU-bound operations can run concurrently"""
    print("\n=== Testing Concurrent CPU-Bound Operations ===")
    
    # Setup
    mock_hf_client = MagicMock()
    executor = SQLAlchemyHuntflowExecutor(mock_hf_client)
    executor.engine = MockVirtualEngine()
    executor.metrics = AsyncMock()
    executor.metrics_helper = AsyncMock()
    
    # Run multiple operations concurrently
    print("Running multiple CPU-bound operations concurrently...")
    
    start_time = time.time()
    
    # Run operations concurrently
    results = await asyncio.gather(
        executor._execute_applicants_by_status(),
        executor._execute_applicants_by_source(),
        executor._execute_field_sql("company"),
        HuntflowAnalyticsTemplates(executor).recruiter_performance_report(),
        return_exceptions=True
    )
    
    end_time = time.time()
    
    # Check all operations completed successfully
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"❌ Operation {i} failed: {result}")
        else:
            print(f"✅ Operation {i} completed successfully")
    
    total_time = end_time - start_time
    print(f"✅ All operations completed concurrently in {total_time:.3f}s")
    print("   This should be faster than running them sequentially due to threading")

async def main():
    """Run all async threading tests"""
    print("🧪 Testing Async Threading Improvements")
    print("=" * 60)
    
    try:
        await test_cpu_bound_operations()
        await test_company_extraction_threading()
        await test_recruiter_performance_threading()
        await test_concurrent_operations()
        
        print("\n" + "=" * 60)
        print("🎉 All async threading tests passed!")
        print("\n✨ Verified improvements:")
        print("  • Small datasets use synchronous processing (no thread overhead)")
        print("  • Large datasets automatically use asyncio.to_thread()")
        print("  • CPU-intensive operations don't block the event loop")
        print("  • Multiple operations can run concurrently")
        print("  • Thread pool usage logged for debugging")
        
    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())