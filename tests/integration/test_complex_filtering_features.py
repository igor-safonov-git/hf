import pytest
from enhanced_metrics_calculator import EnhancedMetricsCalculator
from huntflow_local_client import HuntflowLocalClient
from unittest.mock import Mock

class TestComplexFilteringFeatures:
    """Test complex filtering features including logical operators and advanced syntax"""
    
    @pytest.fixture
    def calculator(self):
        """Enhanced calculator with real data"""
        client = HuntflowLocalClient()
        return EnhancedMetricsCalculator(client, Mock())
    
    @pytest.mark.asyncio
    async def test_advanced_operator_syntax(self, calculator):
        """Test advanced operator syntax like {'operator': 'in', 'value': [...]}"""
        # RED: This will fail - advanced operators not implemented yet
        
        # Test 'in' operator for multiple values
        applicants_with_in = await calculator.get_applicants({
            "sources": {"operator": "in", "value": ["linkedin", "hh", "direct"]}
        })
        assert isinstance(applicants_with_in, list)
        
        # Test 'not_in' operator  
        applicants_with_not_in = await calculator.get_applicants({
            "sources": {"operator": "not_in", "value": ["spam", "invalid"]}
        })
        assert isinstance(applicants_with_not_in, list)
        
        # Test 'contains' operator for partial matching
        vacancies_with_contains = await calculator.get_vacancies({
            "title": {"operator": "contains", "value": "developer"}
        })
        assert isinstance(vacancies_with_contains, list)
    
    @pytest.mark.asyncio
    async def test_numeric_comparison_operators(self, calculator):
        """Test numeric comparison operators (gt, lt, gte, lte, between)"""
        # RED: This will fail - numeric operators not implemented yet
        
        # Test greater than operator
        high_performing = await calculator.get_recruiters({
            "hires_count": {"operator": "gt", "value": 5}
        })
        assert isinstance(high_performing, list)
        
        # Test less than operator
        low_volume = await calculator.get_vacancies({
            "applicant_count": {"operator": "lt", "value": 10}
        })
        assert isinstance(low_volume, list)
        
        # Test between operator for ranges
        medium_range = await calculator.get_applicants({
            "experience_years": {"operator": "between", "value": [2, 5]}
        })
        assert isinstance(medium_range, list)
        
        # Test greater than or equal
        senior_level = await calculator.get_applicants({
            "experience_years": {"operator": "gte", "value": 3}
        })
        assert isinstance(senior_level, list)
    
    @pytest.mark.asyncio
    async def test_logical_and_operator(self, calculator):
        """Test AND logical operator for combining conditions"""
        # RED: This will fail - AND operator not implemented yet
        
        complex_filter = {
            "and": [
                {"period": "3 month"},
                {"recruiters": "12345"},
                {"sources": {"operator": "in", "value": ["linkedin", "hh"]}}
            ]
        }
        
        filtered_applicants = await calculator.get_applicants(complex_filter)
        assert isinstance(filtered_applicants, list)
        
        # Results should be more restrictive than individual filters
        period_only = await calculator.get_applicants({"period": "3 month"})
        assert len(filtered_applicants) <= len(period_only)
    
    @pytest.mark.asyncio
    async def test_logical_or_operator(self, calculator):
        """Test OR logical operator for alternative conditions"""
        # RED: This will fail - OR operator not implemented yet
        
        complex_filter = {
            "or": [
                {"recruiters": "12345"},
                {"sources": "linkedin"},
                {"period": "1 month"}
            ]
        }
        
        filtered_vacancies = await calculator.get_vacancies(complex_filter)
        assert isinstance(filtered_vacancies, list)
        
        # Results should be less restrictive than individual filters
        recruiter_only = await calculator.get_vacancies({"recruiters": "12345"})
        assert len(filtered_vacancies) >= len(recruiter_only)
    
    @pytest.mark.asyncio
    async def test_nested_logical_operators(self, calculator):
        """Test nested AND/OR combinations"""
        # RED: This will fail - nested operators not implemented yet
        
        complex_nested_filter = {
            "and": [
                {"period": "6 month"},
                {
                    "or": [
                        {"recruiters": "12345"},
                        {"sources": {"operator": "in", "value": ["linkedin", "hh"]}}
                    ]
                }
            ]
        }
        
        result = await calculator.get_applicants(complex_nested_filter)
        assert isinstance(result, list)
        
        # Verify logical consistency
        period_filter = await calculator.get_applicants({"period": "6 month"})
        assert len(result) <= len(period_filter)
    
    @pytest.mark.asyncio
    async def test_complex_entity_field_filtering(self, calculator):
        """Test filtering by specific entity fields with operators"""
        # RED: This will fail - entity field filtering not implemented yet
        
        # Filter by specific vacancy fields
        complex_vacancy_filter = {
            "vacancies": {
                "field": "state", 
                "operator": "equals", 
                "value": "open"
            }
        }
        
        applicants_for_open_vacancies = await calculator.get_applicants(complex_vacancy_filter)
        assert isinstance(applicants_for_open_vacancies, list)
        
        # Filter by recruiter performance metrics
        performance_filter = {
            "recruiters": {
                "field": "performance_score",
                "operator": "gt", 
                "value": 0.8
            }
        }
        
        high_performer_hires = await calculator.get_hires(performance_filter)
        assert isinstance(high_performer_hires, list)
    
    @pytest.mark.asyncio
    async def test_real_world_complex_scenario(self, calculator):
        """Test realistic complex filtering scenario combining multiple features"""
        # RED: This will fail - complex scenarios not supported yet
        
        # Realistic HR analytics query:
        # "Show me applicants from the last 3 months, hired by top recruiters,
        #  from linkedin or hh, for open engineering positions"
        real_world_filter = {
            "and": [
                {"period": "3 month"},
                {
                    "or": [
                        {"sources": "linkedin"},
                        {"sources": "hh"}
                    ]
                },
                {
                    "recruiters": {
                        "field": "performance_score",
                        "operator": "gt",
                        "value": 0.7
                    }
                },
                {
                    "vacancies": {
                        "and": [
                            {"field": "state", "value": "open"},
                            {"field": "division", "operator": "contains", "value": "engineering"}
                        ]
                    }
                }
            ]
        }
        
        result = await calculator.get_applicants(real_world_filter)
        assert isinstance(result, list)
        
        # Should be a highly filtered result
        all_applicants = await calculator.get_applicants()
        assert len(result) <= len(all_applicants)
        
        print(f"✅ Complex filtering scenario: {len(result)}/{len(all_applicants)} applicants matched")
    
    @pytest.mark.asyncio
    async def test_filter_operator_validation(self, calculator):
        """Test validation of filter operators and syntax"""
        # RED: This will fail - validation not implemented yet
        
        # Test invalid operator handling
        try:
            await calculator.get_applicants({
                "sources": {"operator": "invalid_op", "value": "test"}
            })
            assert False, "Should have raised an error for invalid operator"
        except ValueError as e:
            assert "invalid_op" in str(e).lower()
        
        # Test missing required fields
        try:
            await calculator.get_vacancies({
                "sources": {"operator": "contains"}  # Missing 'value'
            })
            assert False, "Should have raised an error for missing value"
        except ValueError as e:
            assert "value" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_performance_with_complex_filters(self, calculator):
        """Test that complex filters maintain performance standards"""
        # RED: This will fail - performance not optimized for complex filters yet
        
        import time
        
        complex_filter = {
            "and": [
                {"period": "6 month"},
                {
                    "or": [
                        {"recruiters": "12345"},
                        {"sources": {"operator": "in", "value": ["linkedin", "hh", "direct"]}}
                    ]
                }
            ]
        }
        
        start_time = time.time()
        result = await calculator.get_applicants(complex_filter)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        assert processing_time < 2.0, f"Complex filtering took {processing_time:.2f}s, should be <2s"
        assert isinstance(result, list)
        
        print(f"✅ Complex filter performance: {processing_time:.3f}s for {len(result)} results")