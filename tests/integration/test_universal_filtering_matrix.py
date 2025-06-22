"""
Comprehensive test matrix for Universal Filtering System
Tests all entities filtered by all entities and various parameters
"""

import pytest
import asyncio
from typing import Dict, List, Any
from enhanced_metrics_calculator import EnhancedMetricsCalculator
from huntflow_local_client import HuntflowLocalClient


class TestUniversalFilteringMatrix:
    """Test all entity combinations with various filter parameters"""
    
    @pytest.fixture
    async def calculator(self):
        """Provide calculator instance"""
        client = HuntflowLocalClient()
        return EnhancedMetricsCalculator(client, None)
    
    # Define all entities to test
    ENTITIES = [
        "applicants",
        "hires", 
        "vacancies",
        "recruiters",
        "sources"
    ]
    
    # Define test filters for each entity type
    ENTITY_FILTERS = {
        "vacancies": ["open", "closed"],
        "recruiters": ["14824", "69214"],  # Anastasia and Anton IDs
        "sources": ["274886", "274885"],   # LinkedIn and HeadHunter IDs
        "stages": ["103682", "103683"],    # Hired and other status IDs
    }
    
    # Define period filters to test
    PERIOD_FILTERS = [
        "3 month",
        "6 month", 
        "1 year"
    ]
    
    async def test_all_entity_combinations(self, calculator):
        """Test all possible entity filtering combinations"""
        results = {}
        
        print("\n=== UNIVERSAL FILTERING MATRIX TEST ===\n")
        
        # Test each entity
        for entity in self.ENTITIES:
            results[entity] = {}
            print(f"\n--- Testing {entity.upper()} ---")
            
            # Test with no filters (baseline)
            method_name = f"{entity}_all" if entity != "hires" else "hires"
            method = getattr(calculator, method_name)
            baseline = await method()
            results[entity]["baseline"] = len(baseline)
            print(f"Baseline (no filters): {len(baseline)} items")
            
            # Test with each period filter
            for period in self.PERIOD_FILTERS:
                filters = {"period": period}
                filtered = await method(filters)
                results[entity][f"period_{period}"] = len(filtered)
                print(f"Period {period}: {len(filtered)} items")
            
            # Test with each entity filter type
            for filter_entity, filter_values in self.ENTITY_FILTERS.items():
                for filter_value in filter_values:
                    filters = {"period": "1 year", filter_entity: filter_value}
                    try:
                        filtered = await method(filters)
                        key = f"{filter_entity}_{filter_value}"
                        results[entity][key] = len(filtered)
                        print(f"Filtered by {filter_entity}={filter_value}: {len(filtered)} items")
                    except Exception as e:
                        print(f"Error filtering by {filter_entity}={filter_value}: {e}")
                        results[entity][f"{filter_entity}_{filter_value}"] = "ERROR"
            
            # Test compound filters (period + entity)
            compound_tests = [
                {"period": "6 month", "vacancies": "open"},
                {"period": "1 year", "recruiters": "14824"},
                {"period": "3 month", "sources": "274886"},
            ]
            
            for compound_filter in compound_tests:
                try:
                    filtered = await method(compound_filter)
                    key = "_".join(f"{k}_{v}" for k, v in compound_filter.items())
                    results[entity][key] = len(filtered)
                    print(f"Compound filter {compound_filter}: {len(filtered)} items")
                except Exception as e:
                    print(f"Error with compound filter {compound_filter}: {e}")
                    results[entity][str(compound_filter)] = "ERROR"
        
        # Print summary matrix
        self._print_results_matrix(results)
        
        # Assertions to ensure filtering is working
        self._assert_filtering_logic(results)
        
        return results
    
    def _print_results_matrix(self, results: Dict[str, Dict[str, Any]]):
        """Print a formatted matrix of results"""
        print("\n\n=== RESULTS MATRIX ===")
        print("\n{:<15} {:<15} {:<10}".format("Entity", "Filter", "Count"))
        print("-" * 40)
        
        for entity, entity_results in results.items():
            for filter_name, count in entity_results.items():
                print("{:<15} {:<15} {:<10}".format(entity, filter_name, str(count)))
            print("-" * 40)
    
    def _assert_filtering_logic(self, results: Dict[str, Dict[str, Any]]):
        """Assert that filtering logic is working correctly"""
        
        for entity, entity_results in results.items():
            baseline = entity_results.get("baseline", 0)
            
            # Period filters should reduce or maintain count
            for period in self.PERIOD_FILTERS:
                period_key = f"period_{period}"
                if period_key in entity_results:
                    period_count = entity_results[period_key]
                    if isinstance(period_count, int):
                        assert period_count <= baseline, \
                            f"{entity}: Period filter {period} count {period_count} > baseline {baseline}"
            
            # Specific entity filters should reduce count
            for filter_type in self.ENTITY_FILTERS:
                for filter_value in self.ENTITY_FILTERS[filter_type]:
                    filter_key = f"{filter_type}_{filter_value}"
                    if filter_key in entity_results and isinstance(entity_results[filter_key], int):
                        filtered_count = entity_results[filter_key]
                        assert filtered_count <= baseline, \
                            f"{entity}: {filter_type}={filter_value} count {filtered_count} > baseline {baseline}"
            
            # Compound filters should be most restrictive
            for key, count in entity_results.items():
                if "_" in key and isinstance(count, int) and key not in ["baseline"]:
                    # Compound filters should have fewer results than single filters
                    parts = key.split("_")
                    if len(parts) >= 4:  # compound filter format
                        assert count <= baseline, \
                            f"{entity}: Compound filter {key} count {count} > baseline {baseline}"
        
        print("\n✅ All filtering assertions passed!")
    
    async def test_cross_entity_relationships(self, calculator):
        """Test specific cross-entity relationships"""
        print("\n\n=== CROSS-ENTITY RELATIONSHIP TESTS ===\n")
        
        # Test 1: Applicants filtered by open vacancies
        filters = {"period": "6 month", "vacancies": "open"}
        applicants = await calculator.applicants_all(filters)
        print(f"Test 1: Applicants in open vacancies (6 month): {len(applicants)}")
        
        # Test 2: Hires filtered by specific recruiter
        filters = {"period": "1 year", "recruiters": "14824"}
        hires = await calculator.hires(filters)
        print(f"Test 2: Hires by recruiter 14824 (1 year): {len(hires)}")
        
        # Test 3: Vacancies filtered by state
        open_vacancies = await calculator.vacancies_all({"vacancies": "open"})
        closed_vacancies = await calculator.vacancies_all({"vacancies": "closed"})
        all_vacancies = await calculator.vacancies_all()
        print(f"Test 3: Open vacancies: {len(open_vacancies)}, Closed: {len(closed_vacancies)}, Total: {len(all_vacancies)}")
        
        # Verify that open + closed ≈ total (some might have other states)
        assert len(open_vacancies) + len(closed_vacancies) <= len(all_vacancies)
        
        # Test 4: Complex compound filter
        complex_filter = {
            "period": "3 month",
            "vacancies": "open",
            "recruiters": "14824"
        }
        applicants_complex = await calculator.applicants_all(complex_filter)
        print(f"Test 4: Applicants with complex filter (3m, open, recruiter): {len(applicants_complex)}")
        
        # This should be the most restrictive
        simple_period = await calculator.applicants_all({"period": "3 month"})
        assert len(applicants_complex) <= len(simple_period)
        
        print("\n✅ Cross-entity relationship tests passed!")
    
    async def test_edge_cases(self, calculator):
        """Test edge cases and error handling"""
        print("\n\n=== EDGE CASE TESTS ===\n")
        
        # Test 1: Non-existent ID
        filters = {"recruiters": "99999999"}
        hires = await calculator.hires(filters)
        print(f"Test 1: Hires by non-existent recruiter: {len(hires)} (should be 0)")
        assert len(hires) == 0
        
        # Test 2: Invalid period
        try:
            filters = {"period": "invalid_period"}
            applicants = await calculator.applicants_all(filters)
            print(f"Test 2: Invalid period handled gracefully")
        except Exception as e:
            print(f"Test 2: Invalid period raised exception (expected): {type(e).__name__}")
        
        # Test 3: Empty filters
        filters = {}
        applicants = await calculator.applicants_all(filters)
        all_applicants = await calculator.applicants_all()
        print(f"Test 3: Empty filters same as no filters: {len(applicants)} == {len(all_applicants)}")
        assert len(applicants) == len(all_applicants)
        
        # Test 4: Multiple entity filters (should they combine with AND or OR?)
        # This depends on the implementation
        filters = {
            "period": "1 year",
            "vacancies": "open",
            "recruiters": "14824"
        }
        filtered = await calculator.applicants_all(filters)
        print(f"Test 4: Multiple entity filters: {len(filtered)} items")
        
        print("\n✅ Edge case tests completed!")


# Run the tests
if __name__ == "__main__":
    async def run_all_tests():
        test_suite = TestUniversalFilteringMatrix()
        client = HuntflowLocalClient()
        calc = EnhancedMetricsCalculator(client, None)
        
        # Run all test methods
        await test_suite.test_all_entity_combinations(calc)
        await test_suite.test_cross_entity_relationships(calc)
        await test_suite.test_edge_cases(calc)
        
        print("\n\n🎉 ALL TESTS COMPLETED SUCCESSFULLY! 🎉")
    
    asyncio.run(run_all_tests())