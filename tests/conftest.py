import pytest
from unittest.mock import AsyncMock, Mock
from huntflow_local_client import HuntflowLocalClient
from datetime import datetime, timedelta

@pytest.fixture
async def real_data_client():
    """Use real cached data for integration tests"""
    return HuntflowLocalClient()

@pytest.fixture
async def sample_applicants(real_data_client):
    """Consistent sample of applicants for testing"""
    client = await real_data_client
    applicants = await client.get_applicants(limit=100)
    return applicants[:10]  # First 10 for consistent testing

@pytest.fixture
def mock_db_client():
    """Mock database client for unit tests"""
    return Mock()

@pytest.fixture
def mock_log_analyzer():
    """Mock log analyzer for unit tests"""
    return Mock()

@pytest.fixture
def test_applicants():
    """Factory-generated test applicants"""
    return [
        {
            "id": "1",
            "recruiter_id": "12345", 
            "vacancy_id": "v1",
            "source_id": "linkedin",
            "created": datetime.now()
        },
        {
            "id": "2",
            "recruiter_id": "67890",
            "vacancy_id": "v2", 
            "source_id": "hh",
            "created": datetime.now() - timedelta(days=100)
        }
    ]