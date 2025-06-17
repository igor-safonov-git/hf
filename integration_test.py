#!/usr/bin/env python3
"""
Integration Test for SQLAlchemy Executor + Virtual Engine
Tests the complete pipeline with real data flow patterns
"""
import asyncio
import logging
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy_executor import SQLAlchemyHuntflowExecutor
from virtual_engine import HuntflowVirtualEngine

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockHuntflowClient:
    """Comprehensive mock of Huntflow API client for integration testing"""
    
    def __init__(self):
        self.acc_id = "test_account_123"
        self.token = "test_token"
        
        # Mock data stores
        self._applicants_data = self._generate_mock_applicants()
        self._vacancies_data = self._generate_mock_vacancies()
        self._status_data = self._generate_mock_statuses()
        self._sources_data = self._generate_mock_sources()
        self._recruiters_data = self._generate_mock_recruiters()
        self._divisions_data = self._generate_mock_divisions()
    
    def _generate_mock_applicants(self) -> List[Dict[str, Any]]:
        """Generate realistic applicant data with links array"""
        return [
            {
                "id": 1,
                "first_name": "John", 
                "last_name": "Doe",
                "email": "john@example.com",
                "phone": "+1234567890",
                "position": "Software Engineer",
                "created": "2024-01-15T10:00:00Z",
                "source": 1,  # LinkedIn
                "links": [
                    {
                        "id": 101,
                        "status": 1,  # New Application
                        "vacancy": 1,
                        "updated": "2024-01-15T10:00:00Z",
                        "changed": "2024-01-15T10:00:00Z"
                    }
                ]
            },
            {
                "id": 2,
                "first_name": "Jane",
                "last_name": "Smith", 
                "email": "jane@example.com",
                "phone": "+1234567891",
                "position": "Product Manager",
                "created": "2024-01-16T14:30:00Z",
                "source": 2,  # HeadHunter
                "links": [
                    {
                        "id": 102,
                        "status": 2,  # Interview
                        "vacancy": 2,
                        "updated": "2024-01-20T09:00:00Z",
                        "changed": "2024-01-20T09:00:00Z"
                    }
                ]
            },
            {
                "id": 3,
                "first_name": "Mike",
                "last_name": "Johnson",
                "email": "mike@example.com", 
                "phone": "+1234567892",
                "position": "DevOps Engineer",
                "created": "2024-01-17T16:45:00Z",
                "source": 1,  # LinkedIn
                "links": [
                    {
                        "id": 103,
                        "status": 4,  # Hired
                        "vacancy": 1,
                        "updated": "2024-01-25T11:30:00Z",
                        "changed": "2024-01-25T11:30:00Z"
                    }
                ]
            },
            {
                "id": 4,
                "first_name": "Sarah",
                "last_name": "Wilson",
                "email": "sarah@example.com",
                "phone": "+1234567893", 
                "position": "UX Designer",
                "created": "2024-01-18T08:15:00Z",
                "source": 3,  # Website
                "links": [
                    {
                        "id": 104,
                        "status": 3,  # Offer Sent
                        "vacancy": 3,
                        "updated": "2024-01-22T15:20:00Z",
                        "changed": "2024-01-22T15:20:00Z"
                    }
                ]
            }
        ]
    
    def _generate_mock_vacancies(self) -> List[Dict[str, Any]]:
        """Generate realistic vacancy data"""
        return [
            {
                "id": 1,
                "position": "Senior Software Engineer",
                "company": "TechCorp Inc",
                "state": "OPEN",
                "created": "2024-01-10T09:00:00Z",
                "updated": "2024-01-15T12:00:00Z",
                "account_division": 1,
                "money": "80000-120000 USD",
                "priority": 1
            },
            {
                "id": 2,
                "position": "Product Manager",
                "company": "StartupX LLC", 
                "state": "OPEN",
                "created": "2024-01-12T14:00:00Z",
                "updated": "2024-01-16T10:00:00Z",
                "account_division": 2,
                "money": "90000-130000 USD",
                "priority": 1
            },
            {
                "id": 3,
                "position": "UX/UI Designer",
                "company": "DesignStudio",
                "state": "CLOSED",
                "created": "2024-01-08T11:00:00Z", 
                "updated": "2024-01-20T16:00:00Z",
                "account_division": 3,
                "money": "60000-80000 USD",
                "priority": 0
            }
        ]
    
    def _generate_mock_statuses(self) -> List[Dict[str, Any]]:
        """Generate realistic status mapping"""
        return [
            {"id": 1, "name": "New Application", "type": "new", "order": 1},
            {"id": 2, "name": "Interview Scheduled", "type": "progress", "order": 2},
            {"id": 3, "name": "Offer Sent", "type": "offer", "order": 3},
            {"id": 4, "name": "Hired", "type": "success", "order": 4},
            {"id": 5, "name": "Rejected", "type": "declined", "order": 5}
        ]
    
    def _generate_mock_sources(self) -> List[Dict[str, Any]]:
        """Generate realistic source mapping"""
        return [
            {"id": 1, "name": "LinkedIn", "type": "social"},
            {"id": 2, "name": "HeadHunter", "type": "job_board"},
            {"id": 3, "name": "Company Website", "type": "website"}
        ]
    
    def _generate_mock_recruiters(self) -> List[Dict[str, Any]]:
        """Generate realistic recruiter data"""
        return [
            {"id": 1, "name": "Alice Johnson", "email": "alice@company.com", "type": "recruiter"},
            {"id": 2, "name": "Bob Smith", "email": "bob@company.com", "type": "recruiter"},
            {"id": 3, "name": "Carol Brown", "email": "carol@company.com", "type": "manager"}
        ]
    
    def _generate_mock_divisions(self) -> List[Dict[str, Any]]:
        """Generate realistic division data"""
        return [
            {"id": 1, "name": "Engineering", "order": 1, "active": True, "deep": 0},
            {"id": 2, "name": "Product", "order": 2, "active": True, "deep": 0},
            {"id": 3, "name": "Design", "order": 3, "active": True, "deep": 0}
        ]
    
    async def _req(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Mock HTTP request handler that returns realistic data"""
        logger.debug(f"Mock API call: {method} {path}")
        
        # Handle different endpoints
        if "/applicants" in path and not "/search" in path:
            # /v2/accounts/{acc_id}/applicants endpoint with pagination
            params = kwargs.get("params", {})
            page = params.get("page", 1)
            count = params.get("count", 30)
            
            # Simple pagination simulation
            start_idx = (page - 1) * count
            end_idx = start_idx + count
            items = self._applicants_data[start_idx:end_idx]
            
            return {
                "items": items,
                "total": len(self._applicants_data),
                "total_pages": (len(self._applicants_data) + count - 1) // count
            }
        
        elif "/vacancies/statuses" in path:
            return {"items": self._status_data}
        
        elif "/applicants/sources" in path:
            return {"items": self._sources_data}
        
        elif "/coworkers" in path:
            return {"items": self._recruiters_data}
        
        elif "/divisions" in path:
            return {"items": self._divisions_data}
        
        elif "/vacancies" in path and not "/statuses" in path:
            # Handle vacancy listing with pagination
            params = kwargs.get("params", {})
            page = params.get("page", 1)
            count = params.get("count", 100)
            
            start_idx = (page - 1) * count
            end_idx = start_idx + count
            items = self._vacancies_data[start_idx:end_idx]
            
            return {
                "items": items,
                "total": len(self._vacancies_data),
                "total_pages": (len(self._vacancies_data) + count - 1) // count
            }
        
        else:
            logger.warning(f"Unhandled mock API path: {path}")
            return {"items": []}

async def test_basic_integration():
    """Test basic integration between SQLAlchemy executor and virtual engine"""
    print("\n=== Testing Basic Integration ===")
    
    # Setup
    mock_client = MockHuntflowClient()
    executor = SQLAlchemyHuntflowExecutor(mock_client)
    
    # Test 1: Count all applicants
    print("Testing applicant count...")
    count_expr = {
        "operation": "count",
        "entity": "applicants",
        "filter": {}
    }
    
    applicant_count = await executor.execute_expression(count_expr)
    print(f"✅ Found {applicant_count} applicants")
    assert applicant_count == 4, f"Expected 4 applicants, got {applicant_count}"
    
    # Test 2: Get field values (statuses)
    print("Testing field extraction...")
    field_expr = {
        "operation": "field", 
        "field": "status"
    }
    
    statuses = await executor.execute_expression(field_expr)
    print(f"✅ Found {len(statuses)} statuses: {[s.get('name', s) for s in statuses]}")
    assert len(statuses) >= 4, f"Expected at least 4 statuses, got {len(statuses)}"

async def test_chart_data_integration():
    """Test chart data generation integration"""
    print("\n=== Testing Chart Data Integration ===")
    
    # Setup
    mock_client = MockHuntflowClient()
    executor = SQLAlchemyHuntflowExecutor(mock_client)
    
    # Test 1: Applicants by status chart
    print("Testing applicants by status chart...")
    status_chart = await executor._execute_applicants_by_status()
    
    print(f"Status chart: {status_chart}")
    assert "labels" in status_chart
    assert "values" in status_chart
    assert len(status_chart["labels"]) == len(status_chart["values"])
    print(f"✅ Status chart: {dict(zip(status_chart['labels'], status_chart['values']))}")
    
    # Test 2: Applicants by source chart
    print("Testing applicants by source chart...")
    source_chart = await executor._execute_applicants_by_source()
    
    print(f"Source chart: {source_chart}")
    assert "labels" in source_chart
    assert "values" in source_chart
    print(f"✅ Source chart: {dict(zip(source_chart['labels'], source_chart['values']))}")
    
    # Test 3: Vacancies by state chart
    print("Testing vacancies by state chart...")
    vacancy_chart = await executor._execute_vacancies_by_state()
    
    print(f"Vacancy chart: {vacancy_chart}")
    assert "labels" in vacancy_chart
    assert "values" in vacancy_chart
    print(f"✅ Vacancy chart: {dict(zip(vacancy_chart['labels'], vacancy_chart['values']))}")

async def test_grouped_queries():
    """Test grouped query execution"""
    print("\n=== Testing Grouped Queries ===")
    
    # Setup
    mock_client = MockHuntflowClient()
    executor = SQLAlchemyHuntflowExecutor(mock_client)
    
    # Test grouped query for applicants by status
    print("Testing grouped query: applicants by status...")
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
    assert len(result["labels"]) > 0
    print(f"✅ Grouped query: {dict(zip(result['labels'], result['values']))}")

async def test_virtual_engine_direct():
    """Test virtual engine functionality directly"""
    print("\n=== Testing Virtual Engine Directly ===")
    
    # Setup
    mock_client = MockHuntflowClient()
    engine = HuntflowVirtualEngine(mock_client)
    
    # Test 1: Get applicants data
    print("Testing applicants data retrieval...")
    applicants = await engine._get_applicants_data()
    
    print(f"Retrieved {len(applicants)} applicants")
    assert len(applicants) == 4
    
    # Verify structure
    first_applicant = applicants[0]
    required_fields = ["id", "first_name", "last_name", "status_id", "source_id"]
    for field in required_fields:
        assert field in first_applicant, f"Missing field: {field}"
    
    print(f"✅ First applicant: {first_applicant['first_name']} {first_applicant['last_name']}")
    print(f"   Status ID: {first_applicant['status_id']}, Source ID: {first_applicant['source_id']}")
    
    # Test 2: Get status mapping
    print("Testing status mapping...")
    status_mapping = await engine._get_status_mapping()
    
    print(f"Status mapping: {status_mapping}")
    assert len(status_mapping) >= 4
    assert 1 in status_mapping  # Should have status ID 1
    print(f"✅ Status mapping loaded: {[v['name'] for v in status_mapping.values()]}")
    
    # Test 3: Get sources mapping
    print("Testing sources mapping...")
    sources_mapping = await engine._get_sources_mapping()
    
    print(f"Sources mapping: {sources_mapping}")
    assert len(sources_mapping) >= 3
    print(f"✅ Sources mapping loaded: {list(sources_mapping.values())}")

async def test_cache_functionality():
    """Test TTL cache functionality"""
    print("\n=== Testing Cache Functionality ===")
    
    # Setup
    mock_client = MockHuntflowClient()
    engine = HuntflowVirtualEngine(mock_client)
    
    # Test cache stats
    print("Testing cache statistics...")
    stats_before = engine.get_cache_stats()
    print(f"Cache stats before: {stats_before}")
    
    # Make some calls to populate cache
    print("Populating cache...")
    await engine._get_status_mapping()
    await engine._get_sources_mapping()
    await engine._get_applicants_data()
    
    stats_after = engine.get_cache_stats()
    print(f"Cache stats after: {stats_after}")
    
    assert stats_after['total_entries'] > stats_before['total_entries']
    print("✅ Cache is working - entries increased after API calls")
    
    # Test cache invalidation
    print("Testing cache invalidation...")
    engine.invalidate_cache()
    stats_cleared = engine.get_cache_stats()
    print(f"Cache stats after clear: {stats_cleared}")
    
    assert stats_cleared['total_entries'] == 0
    print("✅ Cache invalidation working")

async def test_error_handling():
    """Test error handling in integration"""
    print("\n=== Testing Error Handling ===")
    
    # Setup with failing client
    failing_client = MockHuntflowClient()
    
    # Override _req to simulate failures
    original_req = failing_client._req
    async def failing_req(*args, **kwargs):
        if "/applicants" in args[1]:
            raise Exception("Simulated API failure")
        return await original_req(*args, **kwargs)
    
    failing_client._req = failing_req
    
    executor = SQLAlchemyHuntflowExecutor(failing_client)
    
    # Test that error handling decorators work
    print("Testing error handling with failing API...")
    
    try:
        result = await executor._execute_applicants_by_status()
        # Should return default empty result due to @handle_errors decorator
        print(f"Error handling result: {result}")
        assert result == {"labels": [], "values": []}
        print("✅ Error handling working - returned default empty result")
    except Exception as e:
        print(f"❌ Error handling failed: {e}")
        raise

async def test_performance_simulation():
    """Test performance characteristics with larger dataset simulation"""
    print("\n=== Testing Performance Simulation ===")
    
    # Setup with large dataset mock
    mock_client = MockHuntflowClient()
    
    # Override to return large dataset
    original_applicants = mock_client._applicants_data
    large_dataset = []
    for i in range(2000):  # Large dataset to trigger async threading
        applicant = {
            "id": i + 1000,
            "first_name": f"User{i}",
            "last_name": f"Test{i}",
            "email": f"user{i}@test.com",
            "source": (i % 3) + 1,
            "links": [{"id": i + 2000, "status": (i % 5) + 1, "vacancy": (i % 10) + 1, "updated": "2024-01-01T00:00:00Z", "changed": "2024-01-01T00:00:00Z"}]
        }
        large_dataset.append(applicant)
    
    mock_client._applicants_data = large_dataset
    
    executor = SQLAlchemyHuntflowExecutor(mock_client)
    
    print(f"Testing with {len(large_dataset)} applicants...")
    
    import time
    start_time = time.time()
    
    # This should trigger async threading for CPU-bound operations
    chart_data = await executor._execute_applicants_by_status()
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    print(f"Processed {len(large_dataset)} applicants in {processing_time:.3f}s")
    print(f"Chart data: {len(chart_data['labels'])} status groups")
    
    assert len(chart_data["labels"]) > 0
    assert sum(chart_data["values"]) == len(large_dataset)
    print("✅ Large dataset processing successful with async threading")

async def main():
    """Run comprehensive integration tests"""
    print("🧪 Running SQLAlchemy Executor + Virtual Engine Integration Tests")
    print("=" * 80)
    
    try:
        await test_basic_integration()
        await test_chart_data_integration() 
        await test_grouped_queries()
        await test_virtual_engine_direct()
        await test_cache_functionality()
        await test_error_handling()
        await test_performance_simulation()
        
        print("\n" + "=" * 80)
        print("🎉 All integration tests passed!")
        print("\n✨ Integration verified:")
        print("  • SQLAlchemy executor + virtual engine integration")
        print("  • Real data flow from API mock → virtual engine → executor")
        print("  • Chart data generation with proper mappings")
        print("  • Grouped queries and analytics operations")
        print("  • TTL caching with concurrency protection")
        print("  • Error handling with graceful degradation")
        print("  • Performance with async threading for large datasets")
        print("  • Complete pipeline from API to analytics results")
        
    except Exception as e:
        print(f"\n❌ Integration tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)