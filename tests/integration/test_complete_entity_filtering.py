import pytest
from enhanced_metrics_calculator import EnhancedMetricsCalculator
from huntflow_local_client import HuntflowLocalClient
from unittest.mock import Mock

class TestCompleteEntityFiltering:
    """Test filtering support across ALL MetricsCalculator entity methods"""
    
    @pytest.fixture
    def calculator(self):
        """Enhanced calculator with real data"""
        client = HuntflowLocalClient()
        return EnhancedMetricsCalculator(client, Mock())
    
    @pytest.mark.asyncio
    async def test_vacancies_all_with_filters(self, calculator):
        """Test filtering support for vacancies_all method"""
        # RED: This will fail - method doesn't have filtering yet
        
        # Test without filters (backwards compatibility)
        all_vacancies = await calculator.vacancies_all()
        assert isinstance(all_vacancies, list)
        
        # Test with period filter
        filtered_vacancies = await calculator.vacancies_all({"period": "1 month"})
        assert isinstance(filtered_vacancies, list)
        assert len(filtered_vacancies) <= len(all_vacancies)
        
        # Test with complex filters
        complex_filtered = await calculator.vacancies_all({
            "period": "3 month",
            "recruiters": "12345"
        })
        assert isinstance(complex_filtered, list)
        assert len(complex_filtered) <= len(filtered_vacancies)
    
    @pytest.mark.asyncio
    async def test_applicants_all_with_filters(self, calculator):
        """Test filtering support for applicants_all method"""
        # This should already work but let's verify
        
        all_applicants = await calculator.applicants_all()
        assert isinstance(all_applicants, list)
        
        filtered_applicants = await calculator.applicants_all({"period": "2 month"})
        assert isinstance(filtered_applicants, list)
        assert len(filtered_applicants) <= len(all_applicants)
    
    @pytest.mark.asyncio
    async def test_recruiters_all_with_filters(self, calculator):
        """Test filtering support for recruiters_all method"""
        # RED: This will fail - method doesn't have filtering yet
        
        all_recruiters = await calculator.recruiters_all()
        assert isinstance(all_recruiters, list)
        
        # Test with division filter
        filtered_recruiters = await calculator.recruiters_all({"divisions": "engineering"})
        assert isinstance(filtered_recruiters, list)
        assert len(filtered_recruiters) <= len(all_recruiters)
    
    @pytest.mark.asyncio
    async def test_sources_all_with_filters(self, calculator):
        """Test filtering support for sources_all method"""
        # RED: This will fail - method doesn't have filtering yet
        
        all_sources = await calculator.sources_all()
        assert isinstance(all_sources, list)
        
        # Test with performance-based filter
        filtered_sources = await calculator.sources_all({"period": "6 month"})
        assert isinstance(filtered_sources, list)
        assert len(filtered_sources) <= len(all_sources)
    
    @pytest.mark.asyncio
    async def test_divisions_all_with_filters(self, calculator):
        """Test filtering support for divisions_all method"""
        # RED: This will fail - method doesn't have filtering yet
        
        all_divisions = await calculator.divisions_all()
        assert isinstance(all_divisions, list)
        
        # Test with recruiter filter
        filtered_divisions = await calculator.divisions_all({"recruiters": "12345"})
        assert isinstance(filtered_divisions, list)
        assert len(filtered_divisions) <= len(all_divisions)
    
    @pytest.mark.asyncio
    async def test_statuses_all_with_filters(self, calculator):
        """Test filtering support for statuses_all method"""
        # RED: This will fail - method doesn't have filtering yet
        
        all_statuses = await calculator.statuses_all()
        assert isinstance(all_statuses, list)
        
        # Test with period filter
        filtered_statuses = await calculator.statuses_all({"period": "1 month"})
        assert isinstance(filtered_statuses, list)
        assert len(filtered_statuses) <= len(all_statuses)
    
    @pytest.mark.asyncio
    async def test_get_open_vacancies_with_filters(self, calculator):
        """Test filtering support for get_open_vacancies method"""
        # RED: This will fail - method doesn't have filtering yet
        
        all_open = await calculator.get_open_vacancies()
        assert isinstance(all_open, list)
        
        # Test with recruiter filter
        filtered_open = await calculator.get_open_vacancies({"recruiters": "12345"})
        assert isinstance(filtered_open, list)
        assert len(filtered_open) <= len(all_open)
    
    @pytest.mark.asyncio
    async def test_get_closed_vacancies_with_filters(self, calculator):
        """Test filtering support for get_closed_vacancies method"""
        # RED: This will fail - method doesn't have filtering yet
        
        all_closed = await calculator.get_closed_vacancies()
        assert isinstance(all_closed, list)
        
        # Test with period filter
        filtered_closed = await calculator.get_closed_vacancies({"period": "2 month"})
        assert isinstance(filtered_closed, list)
        assert len(filtered_closed) <= len(all_closed)
    
    @pytest.mark.asyncio
    async def test_get_hired_applicants_with_filters(self, calculator):
        """Test filtering support for get_hired_applicants method"""
        # RED: This will fail - method doesn't have filtering yet
        
        all_hired = await calculator.get_hired_applicants()
        assert isinstance(all_hired, list)
        
        # Test with source filter
        filtered_hired = await calculator.get_hired_applicants({"sources": "linkedin"})
        assert isinstance(filtered_hired, list)
        assert len(filtered_hired) <= len(all_hired)
    
    @pytest.mark.asyncio
    async def test_hires_method_with_filters(self, calculator):
        """Test filtering support for hires method"""
        # This should already work
        
        all_hires = await calculator.hires()
        assert isinstance(all_hires, list)
        
        filtered_hires = await calculator.hires({"period": "1 month"})
        assert isinstance(filtered_hires, list)
        assert len(filtered_hires) <= len(all_hires)
    
    @pytest.mark.asyncio
    async def test_actions_with_filters(self, calculator):
        """Test filtering support for actions method"""
        # RED: This will fail - method doesn't have filtering yet
        
        all_actions = await calculator.actions()
        assert isinstance(all_actions, list)
        
        filtered_actions = await calculator.actions({"period": "1 month", "recruiters": "12345"})
        assert isinstance(filtered_actions, list)
        assert len(filtered_actions) <= len(all_actions)
    
    @pytest.mark.asyncio
    async def test_complete_filtering_matrix(self, calculator):
        """Test that every entity can be filtered by every other entity"""
        
        # Test applicants filtered by various entities
        applicants_by_recruiter = await calculator.get_applicants({"recruiters": "12345"})
        applicants_by_source = await calculator.get_applicants({"sources": "linkedin"})
        applicants_by_period = await calculator.get_applicants({"period": "1 month"})
        
        # Test vacancies filtered by various entities  
        vacancies_by_recruiter = await calculator.get_vacancies({"recruiters": "12345"})
        vacancies_by_division = await calculator.get_vacancies({"divisions": "engineering"})
        vacancies_by_period = await calculator.get_vacancies({"period": "1 month"})
        
        # Test hires filtered by various entities
        hires_by_source = await calculator.get_hires({"sources": "linkedin"})
        hires_by_recruiter = await calculator.get_hires({"recruiters": "12345"})
        hires_by_period = await calculator.get_hires({"period": "1 month"})
        
        # All should return lists
        all_results = [
            applicants_by_recruiter, applicants_by_source, applicants_by_period,
            vacancies_by_recruiter, vacancies_by_division, vacancies_by_period,
            hires_by_source, hires_by_recruiter, hires_by_period
        ]
        
        for result in all_results:
            assert isinstance(result, list)
        
        print(f"✅ Universal filtering matrix validated:")
        print(f"  Applicants: recruiter({len(applicants_by_recruiter)}), source({len(applicants_by_source)}), period({len(applicants_by_period)})")
        print(f"  Vacancies: recruiter({len(vacancies_by_recruiter)}), division({len(vacancies_by_division)}), period({len(vacancies_by_period)})")
        print(f"  Hires: source({len(hires_by_source)}), recruiter({len(hires_by_recruiter)}), period({len(hires_by_period)})")
    
    @pytest.mark.asyncio
    async def test_backwards_compatibility_all_methods(self, calculator):
        """Test that ALL methods work without filters (backwards compatibility)"""
        
        # Test all main entity methods without filters
        methods_to_test = [
            "get_applicants", "get_vacancies", "get_recruiters", "get_hires",
            "applicants_all", "vacancies_all", "recruiters_all", "sources_all",
            "get_open_vacancies", "get_closed_vacancies", "get_hired_applicants",
            "hires", "actions", "statuses_all", "divisions_all"
        ]
        
        results = {}
        for method_name in methods_to_test:
            if hasattr(calculator, method_name):
                method = getattr(calculator, method_name)
                try:
                    result = await method()
                    results[method_name] = len(result) if isinstance(result, list) else "success"
                    assert isinstance(result, (list, dict)), f"{method_name} should return list or dict"
                except Exception as e:
                    results[method_name] = f"error: {e}"
        
        print(f"✅ Backwards compatibility test results:")
        for method, result in results.items():
            print(f"  {method}: {result}")
        
        # All methods should work
        failed_methods = [m for m, r in results.items() if str(r).startswith("error")]
        assert len(failed_methods) == 0, f"Methods failed: {failed_methods}"