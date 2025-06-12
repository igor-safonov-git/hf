#!/usr/bin/env python3
"""
Test for AI retry mechanism with validation feedback.
This test will initially FAIL until we implement the retry feature.
"""
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import pytest
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the app module to test
try:
    from app import chat_endpoint_with_retry
except ImportError:
    # Function doesn't exist yet - that's expected in TDD
    async def chat_endpoint_with_retry(*args, **kwargs):
        raise NotImplementedError("chat_endpoint_with_retry not implemented yet")


class TestRetryMechanism:
    """Test AI retry mechanism with validation feedback"""
    
    @pytest.mark.asyncio
    async def test_function_exists(self):
        """Test that chat_endpoint_with_retry function exists"""
        # This will fail until we implement the function
        from app import chat_endpoint_with_retry
        assert callable(chat_endpoint_with_retry)
        
    @pytest.mark.asyncio
    async def test_retry_returns_conversation_log(self):
        """Test that the function returns a conversation log"""
        # This will fail until implemented
        result = await chat_endpoint_with_retry(
            message="Test message",
            model="deepseek",
            max_retries=2,
            show_debug=True
        )
        
        # Expected structure
        assert "response" in result or "error" in result
        assert "conversation_log" in result
        assert "attempts" in result
        assert isinstance(result["conversation_log"], list)
        
    @pytest.mark.asyncio
    async def test_retry_on_validation_error(self):
        """Test that validation errors trigger retry"""
        # This test describes the expected behavior:
        # 1. First AI response has validation error (e.g., uses 'logs' entity)
        # 2. System sends error feedback to AI
        # 3. AI retries with corrected response
        # 4. System returns success with full conversation log
        
        result = await chat_endpoint_with_retry(
            message="Какой менеджер оставляет больше всего комментариев?",
            model="deepseek",
            max_retries=2,
            show_debug=True
        )
        
        # Should have multiple attempts due to retry
        assert result["attempts"] > 1
        
        # Conversation log should show the retry process
        conv_log = result["conversation_log"]
        assert any("Invalid entity: logs" in str(msg) for msg in conv_log)
        assert any("ENTITY ERROR" in str(msg) for msg in conv_log)
        
    @pytest.mark.asyncio
    async def test_specific_error_messages(self):
        """Test that different errors get specific feedback messages"""
        # Test entity error
        result_entity = await chat_endpoint_with_retry(
            message="query that triggers logs entity usage",
            model="deepseek"
        )
        assert any("Valid entities ONLY:" in str(msg) for msg in result_entity["conversation_log"])
        
        # Test field error  
        result_field = await chat_endpoint_with_retry(
            message="query that triggers stay_duration on vacancies",
            model="deepseek"
        )
        assert any("stay_duration only exists in status_mapping" in str(msg) 
                  for msg in result_field["conversation_log"])


if __name__ == "__main__":
    # Run the tests - they should FAIL initially
    pytest.main([__file__, "-v", "-s"])