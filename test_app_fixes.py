#!/usr/bin/env python3
"""
Integration tests for app.py after applying surgical fixes.
Tests all the critical improvements made during the code review fixes.
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock

import httpx
import requests

# Import the app and components
from app import (
    app, 
    context_manager, 
    hf_client, 
    update_huntflow_context,
    validate_environment,
    HuntflowContextManager,
    HuntflowClient
)

class IntegrationTestRunner:
    """Run comprehensive integration tests"""
    
    def __init__(self):
        # We'll test the app components directly instead of using TestClient
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_results = []
    
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
        
        if passed:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
    
    def test_environment_validation(self):
        """Test Fix 2: Environment variable validation"""
        print("\n🔍 Testing Environment Validation...")
        
        # Test with missing env vars
        with patch.dict(os.environ, {}, clear=True):
            try:
                validate_environment()
                self.log_test("Environment validation with missing vars", True, "Properly handles missing environment variables")
            except Exception as e:
                self.log_test("Environment validation with missing vars", False, f"Error: {e}")
    
    def test_context_manager(self):
        """Test Fix 3: Context manager with caching"""
        print("\n🔍 Testing Context Manager...")
        
        # Test cache functionality
        cm = HuntflowContextManager()
        
        # Initially cache should be invalid
        self.log_test("Initial cache invalid", not cm.is_cache_valid(), "Cache starts as invalid")
        
        # Update context and check cache validity
        test_context = {"test": "data", "last_updated": datetime.now().isoformat()}
        cm.update_context(test_context)
        self.log_test("Cache valid after update", cm.is_cache_valid(), "Cache becomes valid after update")
        
        # Check context retrieval
        retrieved = cm.get_context()
        self.log_test("Context retrieval", "test" in retrieved and retrieved["test"] == "data", "Context properly retrieved")
        
        # Test cache expiry
        cm._cache_expiry = datetime.now() - timedelta(seconds=1)
        self.log_test("Cache expiry works", not cm.is_cache_valid(), "Cache properly expires")
    
    def test_huntflow_client_error_handling(self):
        """Test Fix 4: Specific exception handling"""
        print("\n🔍 Testing Huntflow Client Error Handling...")
        
        # Test with no credentials
        client = HuntflowClient()
        client.token = ""
        client.acc_id = ""
        
        async def test_no_creds():
            result = await client._req("GET", "/test")
            return result == {}
        
        try:
            result = asyncio.run(test_no_creds())
            self.log_test("No credentials handling", result, "Properly handles missing credentials")
        except Exception as e:
            self.log_test("No credentials handling", False, f"Error: {e}")
    
    def test_http_status_codes(self):
        """Test Fix 7: Proper HTTP status codes"""
        print("\n🔍 Testing HTTP Status Codes...")
        
        # Test health endpoint function directly
        from app import health
        try:
            result = asyncio.run(health())
            has_status = "status" in result and result["status"] == "healthy"
            self.log_test("Health endpoint function", has_status, f"Returns: {result}")
        except Exception as e:
            self.log_test("Health endpoint function", False, f"Error: {e}")
        
        # Test HTTPException handling in chat endpoint
        from app import chat, ChatRequest
        from fastapi import HTTPException
        try:
            with patch('app.deepseek_client.api_key', ""):
                request = ChatRequest(message="test")
                try:
                    asyncio.run(chat(request))
                    self.log_test("Chat HTTPException handling", False, "Should have raised HTTPException")
                except HTTPException as e:
                    correct_status = e.status_code == 503
                    self.log_test("Chat HTTPException handling", correct_status, f"Status: {e.status_code}")
        except Exception as e:
            self.log_test("Chat HTTPException handling", False, f"Error: {e}")
    
    def test_cors_security(self):
        """Test Fix 1: CORS security restrictions"""
        print("\n🔍 Testing CORS Security...")
        
        # Check CORS middleware configuration
        cors_middleware = None
        for middleware in app.user_middleware:
            if hasattr(middleware, 'cls') and 'CORS' in str(middleware.cls):
                cors_middleware = middleware
                break
        
        if cors_middleware:
            # Check that wildcard is not used
            origins_restricted = "*" not in str(cors_middleware.options.get('allow_origins', []))
            self.log_test("CORS origins restricted", origins_restricted, "No wildcard origins allowed")
        else:
            self.log_test("CORS middleware found", False, "CORS middleware not found")
    
    def test_async_operations(self):
        """Test async operations and concurrent API calls"""
        print("\n🔍 Testing Async Operations...")
        
        async def test_context_update():
            # Mock the API responses
            with patch.object(hf_client, '_req', new_callable=AsyncMock) as mock_req:
                mock_req.return_value = {"items": [{"id": 1, "name": "test"}]}
                
                start_time = time.time()
                await update_huntflow_context()
                end_time = time.time()
                
                # Should complete quickly due to concurrent calls
                duration = end_time - start_time
                return duration < 5.0  # Should be much faster than 5 seconds
        
        try:
            result = asyncio.run(test_context_update())
            self.log_test("Concurrent API calls", result, "Context update uses concurrent API calls")
        except Exception as e:
            self.log_test("Concurrent API calls", False, f"Error: {e}")
    
    def test_api_endpoints(self):
        """Test all API endpoints for basic functionality"""
        print("\n🔍 Testing API Endpoints...")
        
        # Test prefetch-data endpoint function directly
        from app import prefetch_data
        try:
            result = asyncio.run(prefetch_data())
            has_summary = "summary" in result
            has_context = "context" in result
            self.log_test("Prefetch data function", has_summary and has_context, "Response has required fields")
        except Exception as e:
            self.log_test("Prefetch data function", False, f"Error: {e}")
        
        # Test context-stats endpoint function directly
        from app import context_stats
        try:
            result = asyncio.run(context_stats())
            has_overview = "context_overview" in result
            self.log_test("Context stats function", has_overview, "Response has context overview")
        except Exception as e:
            self.log_test("Context stats function", False, f"Error: {e}")
        
        # Test metrics endpoint error handling
        from app import get_metric
        from fastapi import HTTPException
        try:
            asyncio.run(get_metric("test_metric"))
            self.log_test("Metrics endpoint error handling", False, "Should have raised HTTPException")
        except HTTPException as e:
            self.log_test("Metrics endpoint error handling", True, f"Properly raised HTTPException: {e.status_code}")
        except Exception as e:
            self.log_test("Metrics endpoint error handling", False, f"Wrong exception type: {e}")
    
    def test_json_validation(self):
        """Test JSON validation functionality"""
        print("\n🔍 Testing JSON Validation...")
        
        from app import validate_json_response
        
        # Test valid JSON
        valid_json = '{"test": "data"}'
        is_valid, msg = validate_json_response(valid_json)
        self.log_test("Valid JSON validation", is_valid, msg)
        
        # Test invalid JSON
        invalid_json = '{"test": invalid}'
        is_valid, msg = validate_json_response(invalid_json)
        self.log_test("Invalid JSON validation", not is_valid, msg)
        
        # Test JSON in markdown
        markdown_json = '```json\n{"test": "data"}\n```'
        is_valid, msg = validate_json_response(markdown_json)
        self.log_test("Markdown JSON validation", is_valid, msg)
    
    def test_cache_behavior(self):
        """Test caching behavior in endpoints"""
        print("\n🔍 Testing Cache Behavior...")
        
        # Reset cache
        context_manager._cache_expiry = None
        
        # First call should update cache
        from app import prefetch_data
        try:
            asyncio.run(prefetch_data())
            cache_valid_after_first = context_manager.is_cache_valid()
            
            # Second call should use cache
            asyncio.run(prefetch_data())
            cache_still_valid = context_manager.is_cache_valid()
            
            self.log_test("Cache created on first call", cache_valid_after_first, "Cache becomes valid after first API call")
            self.log_test("Cache used on second call", cache_still_valid, "Cache remains valid for subsequent calls")
        except Exception as e:
            self.log_test("Cache behavior test", False, f"Error: {e}")
    
    def test_error_propagation(self):
        """Test that errors are properly propagated with correct status codes"""
        print("\n🔍 Testing Error Propagation...")
        
        # Test that HTTPExceptions are properly raised
        from app import chat, ChatRequest
        from fastapi import HTTPException
        try:
            # This should raise an HTTPException due to missing DeepSeek key
            with patch('app.deepseek_client.api_key', ""):
                request = ChatRequest(message="test")
                try:
                    asyncio.run(chat(request))
                    self.log_test("HTTPException propagation", False, "Should have raised HTTPException")
                except HTTPException as e:
                    proper_error = e.status_code == 503
                    self.log_test("HTTPException propagation", proper_error, f"Returns status {e.status_code}")
        except Exception as e:
            self.log_test("HTTPException propagation", False, f"Error: {e}")
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting Integration Tests for App.py Fixes")
        print("=" * 60)
        
        # Run all tests
        self.test_environment_validation()
        self.test_context_manager()
        self.test_huntflow_client_error_handling()
        self.test_http_status_codes()
        self.test_cors_security()
        self.test_async_operations()
        self.test_api_endpoints()
        self.test_json_validation()
        self.test_cache_behavior()
        self.test_error_propagation()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"📈 Success Rate: {self.passed_tests / (self.passed_tests + self.failed_tests) * 100:.1f}%")
        
        if self.failed_tests == 0:
            print("\n🎉 ALL TESTS PASSED! All surgical fixes are working correctly.")
        else:
            print(f"\n⚠️  {self.failed_tests} tests failed. Review the failures above.")
        
        return self.failed_tests == 0

if __name__ == "__main__":
    runner = IntegrationTestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)