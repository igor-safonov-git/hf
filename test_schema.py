#!/usr/bin/env python3
"""
Automated Schema Validation Tests for Huntflow API Integration

Tests schema correctness against official API specification in CLAUDE.md
"""

try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    # Define minimal pytest-like decorators for basic testing
    def pytest_fixture(func):
        return func
    class pytest:
        fixture = staticmethod(pytest_fixture)
        class mark:
            @staticmethod
            def asyncio(func):
                return func

import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any, List
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from huntflow_schema import HuntflowVirtualEngine, HuntflowQueryBuilder
from app import HuntflowClient


class TestHuntflowSchemaValidation:
    """Test suite for validating Huntflow schema against official API spec"""
    
    @pytest.fixture
    def mock_hf_client(self):
        """Create a mock Huntflow client"""
        client = MagicMock()
        client.acc_id = "test_account_123"
        client._req = AsyncMock()
        return client
    
    @pytest.fixture
    def schema_engine(self, mock_hf_client):
        """Create schema engine with mocked client"""
        return HuntflowVirtualEngine(mock_hf_client)
    
    def test_applicants_table_structure(self, schema_engine):
        """Test applicants table matches API field structure"""
        applicants_table = schema_engine.applicants
        
        # Check required API fields exist
        column_names = [col.name for col in applicants_table.columns]
        
        # Direct API fields per CLAUDE.md
        required_api_fields = [
            'id', 'first_name', 'last_name', 'vacancy', 'source', 
            'created', 'updated', 'recruiter'
        ]
        
        for field in required_api_fields:
            assert field in column_names, f"Missing required API field: {field}"
        
        # Computed fields should be present but marked as such
        computed_fields = ['status_id', 'status_name', 'recruiter_name', 'source_name']
        
        for field in computed_fields:
            assert field in column_names, f"Missing computed field: {field}"
        
        # Fields that should NOT exist (not in API)
        forbidden_fields = ['time_to_hire_days', 'status', 'vacancy_id', 'source_id', 'recruiter_id']
        
        for field in forbidden_fields:
            assert field not in column_names, f"Forbidden field found in schema: {field}"
    
    def test_correct_api_endpoints(self, schema_engine):
        """Test that schema uses correct API endpoints from CLAUDE.md"""
        
        # Mock the _req method to capture endpoint calls
        endpoint_calls = []
        
        async def mock_req(method, url, **kwargs):
            endpoint_calls.append(url)
            if 'vacancies/statuses' in url:
                return {"items": [{"id": 1, "name": "Test Status"}]}
            elif 'applicants/sources' in url:
                return {"items": [{"id": 1, "name": "Test Source"}]}
            elif 'coworkers' in url:
                return {"items": [{"id": 1, "first_name": "Test", "last_name": "User"}]}
            return {"items": []}
        
        schema_engine.hf_client._req = mock_req
        
        # Test status endpoint
        asyncio.run(schema_engine._get_status_mapping())
        
        # Should use correct endpoint from CLAUDE.md line 109
        status_calls = [call for call in endpoint_calls if 'statuses' in call]
        assert any('vacancies/statuses' in call for call in status_calls), \
            "Should use /vacancies/statuses endpoint first"
        
        # Reset for sources test
        endpoint_calls.clear()
        
        # Test sources endpoint
        asyncio.run(schema_engine._get_sources_mapping())
        
        # Should use endpoint from CLAUDE.md line 121
        assert any('applicants/sources' in call for call in endpoint_calls), \
            "Should use /applicants/sources endpoint"
    
    @pytest.mark.asyncio
    async def test_applicants_search_pagination(self, schema_engine):
        """Test applicants search uses correct pagination per CLAUDE.md line 169"""
        
        # Mock response with pagination
        call_count = 0
        
        async def mock_req(method, url, params=None, **kwargs):
            nonlocal call_count
            call_count += 1
            
            # Verify correct pagination parameters
            if 'applicants/search' in url and params:
                assert 'count' in params, "Should use 'count' parameter"
                assert 'page' in params, "Should use 'page' parameter"
                assert params['count'] == 100, "Should request 100 items per page"
                
                # Return empty on second call to stop pagination
                if call_count == 1:
                    return {"items": [{"id": 1, "first_name": "Test"}]}
                else:
                    return {"items": []}
            return {"items": []}
        
        schema_engine.hf_client._req = mock_req
        
        # Test applicants data fetch
        await schema_engine._get_applicants_data()
        
        assert call_count >= 1, "Should make at least one API call"
    
    @pytest.mark.asyncio
    async def test_status_from_logs_logic(self, schema_engine):
        """Test status retrieval from logs per CLAUDE.md lines 138-151"""
        
        # Mock logs response
        mock_logs = {
            "items": [
                {"id": 1, "status": 5, "created": "2024-01-01T00:00:00Z"},
                {"id": 2, "message": "Other activity", "created": "2024-01-02T00:00:00Z"},
                {"id": 3, "status": 3, "created": "2024-01-03T00:00:00Z"}  # Most recent
            ]
        }
        
        async def mock_req(method, url, **kwargs):
            if 'logs' in url:
                return mock_logs
            elif 'vacancies/statuses' in url:
                return {"items": [{"id": 3, "name": "Interview"}, {"id": 5, "name": "Applied"}]}
            return {"items": []}
        
        schema_engine.hf_client._req = mock_req
        
        # Test status extraction
        status_id, status_name = await schema_engine._get_applicant_status_from_logs(123)
        
        # Should get the first status found (most recent in logs)
        assert status_id == 5, f"Expected status_id 5, got {status_id}"
        assert status_name == "Applied", f"Expected 'Applied', got '{status_name}'"
    
    def test_schema_tables_exist(self, schema_engine):
        """Test all required tables exist in schema"""
        
        required_tables = ['applicants', 'vacancies', 'status_mapping', 'recruiters', 'sources', 'divisions']
        
        for table_name in required_tables:
            assert hasattr(schema_engine, table_name), f"Missing table: {table_name}"
            table = getattr(schema_engine, table_name)
            assert table is not None, f"Table {table_name} is None"
    
    @pytest.mark.asyncio
    async def test_field_mapping_accuracy(self, schema_engine):
        """Test that API response fields are mapped correctly"""
        
        # Mock API response with realistic field structure
        mock_applicant_response = {
            "items": [
                {
                    "id": 123,
                    "first_name": "John",
                    "last_name": "Doe", 
                    "vacancy": 456,      # API field name
                    "source": 789,       # API field name
                    "recruiter": 101,    # API field name
                    "created": "2024-01-01T00:00:00Z",
                    "updated": "2024-01-02T00:00:00Z"
                }
            ]
        }
        
        mock_recruiters = {
            "items": [{"id": 101, "first_name": "Jane", "last_name": "Smith"}]
        }
        
        mock_sources = {
            "items": [{"id": 789, "name": "LinkedIn"}]
        }
        
        async def mock_req(method, url, **kwargs):
            if 'applicants/search' in url:
                return mock_applicant_response
            elif 'coworkers' in url:
                return mock_recruiters
            elif 'applicants/sources' in url:
                return mock_sources
            return {"items": []}
        
        schema_engine.hf_client._req = mock_req
        
        # Get enriched applicants data
        applicants = await schema_engine._get_applicants_data()
        
        assert len(applicants) == 1, "Should return one applicant"
        
        applicant = applicants[0]
        
        # Test direct API field mapping
        assert applicant['id'] == 123
        assert applicant['first_name'] == "John"
        assert applicant['last_name'] == "Doe"
        assert applicant['vacancy'] == 456, "Should use 'vacancy' not 'vacancy_id'"
        assert applicant['source'] == 789, "Should use 'source' not 'source_id'"
        assert applicant['recruiter'] == 101, "Should use 'recruiter' not 'recruiter_id'"
        
        # Test computed field mapping
        assert applicant['recruiter_name'] == "Jane Smith", "Should map recruiter name from coworkers"
        assert applicant['source_name'] == "LinkedIn", "Should map source name from sources"
        assert applicant['status_name'] == "Unknown", "Status should be Unknown (not computed from logs yet)"


class TestSchemaValidationRunner:
    """Test runner that validates schema against CLAUDE.md specification"""
    
    def validate_endpoint_compliance(self) -> Dict[str, bool]:
        """Validate endpoints match CLAUDE.md specification"""
        
        # Read CLAUDE.md to extract endpoint specifications
        try:
            with open('/home/igor/hf/CLAUDE.md', 'r') as f:
                claude_content = f.read()
        except FileNotFoundError:
            return {"error": "CLAUDE.md not found"}
        
        # Extract documented endpoints
        documented_endpoints = [
            '/accounts/{account_id}/vacancies/statuses',
            '/accounts/{account_id}/applicants/search',
            '/accounts/{account_id}/applicants/sources',
            '/accounts/{account_id}/coworkers',
            '/accounts/{account_id}/divisions'
        ]
        
        # Check if endpoints are used in schema
        with open('/home/igor/hf/huntflow_schema.py', 'r') as f:
            schema_content = f.read()
        
        compliance = {}
        
        for endpoint in documented_endpoints:
            # Remove {account_id} placeholder for matching
            endpoint_pattern = endpoint.replace('{account_id}', '')
            compliance[endpoint] = endpoint_pattern in schema_content
        
        return compliance
    
    def validate_field_compliance(self) -> Dict[str, Any]:
        """Validate field names match API specification"""
        
        # Expected field mapping based on CLAUDE.md
        expected_fields = {
            'applicants': {
                'direct_api_fields': ['id', 'first_name', 'last_name', 'vacancy', 'source', 'recruiter', 'created', 'updated'],
                'computed_fields': ['status_id', 'status_name', 'recruiter_name', 'source_name'],
                'forbidden_fields': ['time_to_hire_days', 'vacancy_id', 'source_id', 'recruiter_id']
            }
        }
        
        # Read schema file
        with open('/home/igor/hf/huntflow_schema.py', 'r') as f:
            schema_content = f.read()
        
        compliance = {}
        
        # Check applicants table fields
        for field in expected_fields['applicants']['direct_api_fields']:
            compliance[f"applicants.{field}_exists"] = f"Column('{field}'" in schema_content
        
        for field in expected_fields['applicants']['forbidden_fields']:
            compliance[f"applicants.{field}_forbidden"] = f"Column('{field}'" not in schema_content
        
        return compliance


def run_schema_validation():
    """Run comprehensive schema validation"""
    
    print("🔍 Running Huntflow Schema Validation Tests...")
    print("=" * 50)
    
    # Run endpoint compliance check
    validator = TestSchemaValidationRunner()
    
    print("\n📋 Endpoint Compliance Check:")
    endpoint_compliance = validator.validate_endpoint_compliance()
    
    for endpoint, compliant in endpoint_compliance.items():
        status = "✅" if compliant else "❌"
        print(f"  {status} {endpoint}")
    
    print("\n🏗️  Field Compliance Check:")
    field_compliance = validator.validate_field_compliance()
    
    for field_check, compliant in field_compliance.items():
        status = "✅" if compliant else "❌"
        print(f"  {status} {field_check}")
    
    # Calculate overall score
    total_checks = len(endpoint_compliance) + len(field_compliance)
    passed_checks = sum(endpoint_compliance.values()) + sum(field_compliance.values())
    score = (passed_checks / total_checks) * 100
    
    print(f"\n📊 Overall Schema Compliance: {score:.1f}% ({passed_checks}/{total_checks})")
    
    if score >= 90:
        print("🎉 Schema is highly compliant with CLAUDE.md specification!")
    elif score >= 70:
        print("⚠️  Schema has minor compliance issues that should be addressed.")
    else:
        print("❌ Schema has significant compliance issues requiring immediate attention.")
    
    return score


if __name__ == "__main__":
    # Run validation
    run_schema_validation()
    
    # Run basic tests without pytest
    if not PYTEST_AVAILABLE:
        print("\n🧪 Running basic tests without pytest...")
        
        # Create test instance
        test_class = TestHuntflowSchemaValidation()
        
        # Create mock client
        mock_client = MagicMock()
        mock_client.acc_id = "test_account_123"
        mock_client._req = AsyncMock()
        
        # Create schema engine
        schema_engine = HuntflowVirtualEngine(mock_client)
        
        try:
            # Run basic tests
            print("  🔍 Testing applicants table structure...")
            test_class.test_applicants_table_structure(schema_engine)
            print("  ✅ Applicants table structure test passed")
            
            print("  🔍 Testing schema tables exist...")
            test_class.test_schema_tables_exist(schema_engine)
            print("  ✅ Schema tables existence test passed")
            
            print("  🔍 Testing correct API endpoints...")
            test_class.test_correct_api_endpoints(schema_engine)
            print("  ✅ API endpoints test passed")
            
            print("\n🎉 Basic tests completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Basic tests failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\n🧪 Running detailed unit tests with pytest...")
        pytest.main([__file__, "-v"])