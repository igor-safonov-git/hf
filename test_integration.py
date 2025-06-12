#!/usr/bin/env python3
"""
Integration Tests for Huntflow Schema with Mock API

Tests the complete schema behavior with realistic API interactions
"""

import asyncio
import sys
import os
from unittest.mock import patch, AsyncMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from huntflow_schema import HuntflowVirtualEngine
from test_api_mocks import HuntflowAPIMocks
from app import HuntflowClient


class MockHuntflowClient:
    """Mock Huntflow client that uses realistic API responses"""
    
    def __init__(self):
        self.acc_id = "test_account_123"
        self.mock_router = HuntflowAPIMocks.get_mock_router()
    
    async def _req(self, method: str, url: str, params=None, **kwargs):
        """Mock request method that returns realistic responses"""
        return await self.mock_router(method, url, params, **kwargs)


async def test_schema_integration():
    """Test complete schema integration with mock API"""
    
    print("🔧 Running Schema Integration Tests...")
    print("=" * 50)
    
    # Create mock client and schema engine
    mock_client = MockHuntflowClient()
    schema_engine = HuntflowVirtualEngine(mock_client)
    
    print("\n1️⃣ Testing Status Mapping...")
    
    # Test status mapping
    status_map = await schema_engine._get_status_mapping()
    
    assert len(status_map) > 0, "Status mapping should not be empty"
    assert 1 in status_map, "Status ID 1 should exist"
    assert status_map[1] == "Новые", f"Expected 'Новые', got '{status_map[1]}'"
    assert status_map[5] == "Оффер принят", f"Expected 'Оффер принят', got '{status_map[5]}'"
    
    print(f"✅ Status mapping loaded: {len(status_map)} statuses")
    print(f"   Sample: {dict(list(status_map.items())[:3])}")
    
    print("\n2️⃣ Testing Recruiters Mapping...")
    
    # Test recruiters mapping
    recruiters_map = await schema_engine._get_recruiters_mapping()
    
    assert len(recruiters_map) > 0, "Recruiters mapping should not be empty"
    assert 301 in recruiters_map, "Recruiter ID 301 should exist"
    assert recruiters_map[301] == "Jane Smith", f"Expected 'Jane Smith', got '{recruiters_map[301]}'"
    
    print(f"✅ Recruiters mapping loaded: {len(recruiters_map)} recruiters")
    print(f"   Sample: {dict(list(recruiters_map.items())[:2])}")
    
    print("\n3️⃣ Testing Sources Mapping...")
    
    # Test sources mapping
    sources_map = await schema_engine._get_sources_mapping()
    
    assert len(sources_map) > 0, "Sources mapping should not be empty"
    assert 201 in sources_map, "Source ID 201 should exist"
    assert sources_map[201] == "LinkedIn", f"Expected 'LinkedIn', got '{sources_map[201]}'"
    
    print(f"✅ Sources mapping loaded: {len(sources_map)} sources")
    print(f"   Sample: {dict(list(sources_map.items())[:3])}")
    
    print("\n4️⃣ Testing Status from Logs...")
    
    # Test status retrieval from logs
    status_id, status_name = await schema_engine._get_applicant_status_from_logs(12345)
    
    assert status_id == 2, f"Expected status_id 2, got {status_id}"
    assert status_name == "Скрининг (Телефонное интервью)", f"Expected 'Скрининг (Телефонное интервью)', got '{status_name}'"
    
    print(f"✅ Status from logs: ID={status_id}, Name='{status_name}'")
    
    # Test different applicant
    status_id2, status_name2 = await schema_engine._get_applicant_status_from_logs(12346)
    assert status_id2 == 5, f"Expected status_id 5, got {status_id2}"
    assert status_name2 == "Оффер принят", f"Expected 'Оффер принят', got '{status_name2}'"
    
    print(f"✅ Status from logs (applicant 2): ID={status_id2}, Name='{status_name2}'")
    
    print("\n5️⃣ Testing Complete Applicants Data Flow...")
    
    # Test complete applicants data enrichment
    applicants_data = await schema_engine._get_applicants_data()
    
    assert len(applicants_data) == 3, f"Expected 3 applicants, got {len(applicants_data)}"
    
    # Check first applicant
    applicant = applicants_data[0]
    
    # Verify direct API fields
    assert applicant['id'] == 12345, f"Expected ID 12345, got {applicant['id']}"
    assert applicant['first_name'] == "Иван", f"Expected 'Иван', got '{applicant['first_name']}'"
    assert applicant['vacancy'] == 1001, f"Expected vacancy 1001, got {applicant['vacancy']}"
    assert applicant['source'] == 201, f"Expected source 201, got {applicant['source']}"
    assert applicant['recruiter'] == 301, f"Expected recruiter 301, got {applicant['recruiter']}"
    
    # Verify computed fields
    assert applicant['recruiter_name'] == "Jane Smith", f"Expected 'Jane Smith', got '{applicant['recruiter_name']}'"
    assert applicant['source_name'] == "LinkedIn", f"Expected 'LinkedIn', got '{applicant['source_name']}'"
    
    # Status should be Unknown since not computed from logs in bulk fetch
    assert applicant['status_name'] == "Unknown", f"Expected 'Unknown', got '{applicant['status_name']}'"
    
    print(f"✅ Applicants data enrichment successful")
    print(f"   First applicant: {applicant['first_name']} {applicant['last_name']}")
    print(f"   Recruiter: {applicant['recruiter_name']}")
    print(f"   Source: {applicant['source_name']}")
    
    print("\n6️⃣ Testing Field Name Compliance...")
    
    # Test that old field names are NOT used
    for applicant in applicants_data:
        # Should NOT have old field names
        assert 'vacancy_id' not in applicant, "Found forbidden field 'vacancy_id'"
        assert 'source_id' not in applicant, "Found forbidden field 'source_id'"
        assert 'recruiter_id' not in applicant, "Found forbidden field 'recruiter_id'"
        assert 'time_to_hire_days' not in applicant, "Found forbidden field 'time_to_hire_days'"
        
        # Should have correct API field names
        assert 'vacancy' in applicant, "Missing required field 'vacancy'"
        assert 'source' in applicant, "Missing required field 'source'"
        assert 'recruiter' in applicant, "Missing required field 'recruiter'"
    
    print("✅ Field name compliance validated")
    
    print("\n🎉 All Integration Tests Passed!")
    print(f"✅ Schema correctly implements CLAUDE.md specification")
    print(f"✅ API field mappings are accurate")
    print(f"✅ Status retrieval from logs works correctly")
    print(f"✅ Data enrichment functions properly")
    
    return True


async def test_performance_characteristics():
    """Test performance aspects of the schema"""
    
    print("\n⚡ Testing Performance Characteristics...")
    print("=" * 40)
    
    mock_client = MockHuntflowClient()
    schema_engine = HuntflowVirtualEngine(mock_client)
    
    # Track API calls
    call_count = 0
    original_req = mock_client._req
    
    async def counting_req(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return await original_req(*args, **kwargs)
    
    mock_client._req = counting_req
    
    # Test caching behavior
    print("🔄 Testing caching behavior...")
    
    # First call should hit API
    call_count = 0
    await schema_engine._get_status_mapping()
    first_call_count = call_count
    
    # Second call should use cache
    call_count = 0
    await schema_engine._get_status_mapping()
    second_call_count = call_count
    
    assert first_call_count > 0, "First call should hit API"
    assert second_call_count == 0, "Second call should use cache"
    
    print(f"✅ Caching works: {first_call_count} API calls → 0 API calls")
    
    # Test bulk data fetch efficiency
    print("🔄 Testing bulk data fetch...")
    
    call_count = 0
    applicants_data = await schema_engine._get_applicants_data()
    
    # Should make minimal API calls for bulk fetch
    # Expected: applicants/search, coworkers, sources
    expected_max_calls = 6  # Reasonable limit for bulk operation
    
    assert call_count <= expected_max_calls, f"Too many API calls: {call_count} > {expected_max_calls}"
    
    print(f"✅ Bulk fetch efficient: {call_count} API calls for {len(applicants_data)} applicants")
    
    return True


def run_all_tests():
    """Run all integration tests"""
    
    try:
        # Run basic integration tests
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already in async context, create new loop
            import threading
            result = [None]
            exception = [None]
            
            def run_tests():
                try:
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    result[0] = new_loop.run_until_complete(test_schema_integration())
                    new_loop.run_until_complete(test_performance_characteristics())
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=run_tests)
            thread.start()
            thread.join()
            
            if exception[0]:
                raise exception[0]
            
            return result[0]
        else:
            # Standard execution
            success1 = loop.run_until_complete(test_schema_integration())
            success2 = loop.run_until_complete(test_performance_characteristics())
            return success1 and success2
    
    except Exception as e:
        print(f"\n❌ Integration tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    
    if success:
        print(f"\n🏆 All integration tests completed successfully!")
        exit(0)
    else:
        print(f"\n💥 Integration tests failed!")
        exit(1)