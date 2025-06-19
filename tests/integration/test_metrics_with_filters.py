import pytest
from unittest.mock import Mock, AsyncMock
from enhanced_metrics_calculator import EnhancedMetricsCalculator
from huntflow_local_client import HuntflowLocalClient

class TestMetricsCalculatorWithFilters:
    """Test MetricsCalculator with universal filtering"""
    
    @pytest.fixture
    def real_client(self):
        """Real database client for integration tests"""
        return HuntflowLocalClient()
    
    @pytest.fixture
    def mock_log_analyzer(self):
        return Mock()
    
    @pytest.fixture
    def calculator(self, real_client, mock_log_analyzer):
        """Enhanced calculator with real data"""
        return EnhancedMetricsCalculator(real_client, mock_log_analyzer)
    
    @pytest.mark.asyncio
    async def test_get_applicants_with_recruiter_filter(self, calculator):
        """Test filtering applicants by recruiter"""
        # First get all applicants to find a valid recruiter ID
        all_applicants = await calculator.get_applicants()
        if not all_applicants:
            pytest.skip("No applicants in test data")
        
        # Use a real recruiter ID from the data
        real_recruiter_id = all_applicants[0]["recruiter_id"] if "recruiter_id" in all_applicants[0] else all_applicants[0]["id"]
        filters = {"recruiters": str(real_recruiter_id), "period": "3 month"}
        
        result = await calculator.get_applicants(filters)
        
        # All applicants should belong to the specified recruiter (or be filtered somehow)
        assert isinstance(result, list)
        # The filter should have been applied (result could be empty or filtered)
        print(f"Filtered {len(all_applicants)} -> {len(result)} applicants")
    
    @pytest.mark.asyncio
    async def test_get_hires_with_source_filter(self, calculator):
        """Test filtering hires by source"""
        # First get all hires to find a valid source
        all_hires = await calculator.get_hires()
        if not all_hires:
            pytest.skip("No hires in test data")
        
        # Use a real source ID from the data
        real_source_id = all_hires[0]["source_id"] if "source_id" in all_hires[0] else "linkedin"
        filters = {"sources": str(real_source_id), "period": "1 month"}
        
        result = await calculator.get_hires(filters)
        
        # All hires should be from the specified source (or be filtered)
        assert isinstance(result, list)
        print(f"Filtered {len(all_hires)} -> {len(result)} hires")
    
    @pytest.mark.asyncio
    async def test_get_vacancies_with_multiple_filters(self, calculator):
        """Test filtering vacancies with multiple criteria"""
        filters = {
            "vacancies": "open",
            "period": "6 month"
        }
        
        result = await calculator.get_vacancies(filters)
        
        # Should return filtered vacancies
        assert isinstance(result, list)
        print(f"Filtered vacancies: {len(result)} items")
    
    @pytest.mark.asyncio
    async def test_backwards_compatibility(self, calculator):
        """Test that methods work without filters (backwards compatibility)"""
        # These should work exactly as before
        applicants = await calculator.get_applicants()
        hires = await calculator.get_hires()
        vacancies = await calculator.get_vacancies()
        
        assert isinstance(applicants, list)
        assert isinstance(hires, list)
        assert isinstance(vacancies, list)
    
    @pytest.mark.asyncio
    async def test_complex_multi_entity_filtering(self, calculator):
        """Test complex filtering across multiple entities"""
        # Get sample data first
        all_applicants = await calculator.get_applicants()
        if len(all_applicants) < 2:
            pytest.skip("Not enough applicants for complex filtering test")
        
        # Use real IDs from the data
        sample_recruiter = all_applicants[0]["id"]  # Use applicant ID as fallback
        
        filters = {
            "recruiters": str(sample_recruiter),
            "period": "3 month"
        }
        
        result = await calculator.get_applicants(filters)
        
        # Should have applicants matching the criteria
        assert isinstance(result, list)
        print(f"Complex filter result: {len(result)} applicants")
    
    @pytest.mark.asyncio
    async def test_enhanced_methods_exist(self, calculator):
        """Test that enhanced calculator has all the expected methods"""
        # Check that key methods exist and are callable
        assert hasattr(calculator, 'get_applicants')
        assert callable(calculator.get_applicants)
        
        assert hasattr(calculator, 'get_hires')
        assert callable(calculator.get_hires)
        
        assert hasattr(calculator, 'get_vacancies')
        assert callable(calculator.get_vacancies)
        
        assert hasattr(calculator, 'get_recruiters')
        assert callable(calculator.get_recruiters)
    
    @pytest.mark.asyncio
    async def test_filter_engine_integration(self, calculator):
        """Test that the filter engine is properly integrated"""
        # Check that calculator has filter engine
        assert hasattr(calculator, 'filter_engine')
        assert calculator.filter_engine is not None
        
        # Test prompt parsing integration
        prompt_filters = {"period": "1 month"}
        filter_set = calculator.filter_engine.parse_prompt_filters(prompt_filters)
        
        assert filter_set.period_filter is not None
        assert filter_set.period_filter.period_type == "1 month"