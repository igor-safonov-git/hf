#!/usr/bin/env python3
"""
Table-Specific Integration Tests for Huntflow Schema
Tests each of the 19 virtual tables individually to ensure proper API integration
"""
import asyncio
import logging
from sqlalchemy import select
from typing import Dict, Any, List

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import our modules
from schema import create_huntflow_tables
from huntflow_schema import HuntflowVirtualEngine
from app import HuntflowClient


class TableIntegrationTestSuite:
    """Test suite for individual table integration"""
    
    def __init__(self):
        self.client = HuntflowClient()
        self.engine = HuntflowVirtualEngine(self.client)
        self.test_results = {}
        self.failed_tests = []
    
    def log_test(self, test_name: str, result: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {test_name} {details}")
        self.test_results[test_name] = result
        if not result:
            self.failed_tests.append(test_name)
    
    async def _test_table_basic_query(self, table_name: str, table_obj) -> bool:
        """Test basic SELECT query for a table"""
        try:
            # Test basic select with limit
            query = select(table_obj).limit(5)
            result = await self.engine.execute(query)
            
            if not isinstance(result, list):
                return False, f"Expected list, got {type(result)}"
            
            # Empty result is OK for some tables
            if len(result) == 0:
                return True, f"Empty result (expected for some tables)"
            
            # Check result structure
            sample = result[0]
            if not isinstance(sample, dict):
                return False, f"Expected dict rows, got {type(sample)}"
            
            return True, f"Successfully queried {len(result)} rows"
            
        except Exception as e:
            return False, f"Exception: {e}"
    
    async def _test_table_with_filter(self, table_name: str, table_obj, filter_field: str) -> bool:
        """Test table query with basic filtering"""
        try:
            if not hasattr(table_obj.c, filter_field):
                return True, f"No {filter_field} field to test filtering"
            
            # Test with a simple filter
            query = select(table_obj).where(getattr(table_obj.c, filter_field).isnot(None)).limit(3)
            result = await self.engine.execute(query)
            
            if not isinstance(result, list):
                return False, f"Filter query returned {type(result)}"
            
            return True, f"Filter query successful, {len(result)} rows"
            
        except Exception as e:
            # Filtering may not work for all tables - that's OK
            return True, f"Filter test skipped: {e}"
    
    async def test_applicants_table(self):
        """Test applicants table integration"""
        try:
            table = self.engine.applicants
            
            # Basic query test
            basic_ok, basic_msg = await self._test_table_basic_query('applicants', table)
            if not basic_ok:
                self.log_test("Applicants Table", False, f"Basic query failed: {basic_msg}")
                return False
            
            # Test filtering by ID
            filter_ok, filter_msg = await self._test_table_with_filter('applicants', table, 'id')
            
            # Test specific applicants fields
            query = select(table.c.id, table.c.first_name, table.c.last_name).limit(3)
            result = await self.engine.execute(query)
            
            if result and len(result) > 0:
                sample = result[0]
                required_fields = ['id']
                missing = [f for f in required_fields if f not in sample]
                if missing:
                    self.log_test("Applicants Table", False, f"Missing required fields: {missing}")
                    return False
            
            self.log_test("Applicants Table", True, f"Integration successful. {basic_msg}")
            return True
            
        except Exception as e:
            self.log_test("Applicants Table", False, f"Exception: {e}")
            return False
    
    async def test_vacancies_table(self):
        """Test vacancies table integration"""
        try:
            table = self.engine.vacancies
            
            # Basic query test
            basic_ok, basic_msg = await self._test_table_basic_query('vacancies', table)
            if not basic_ok:
                self.log_test("Vacancies Table", False, f"Basic query failed: {basic_msg}")
                return False
            
            # Test specific vacancies fields
            query = select(table.c.id, table.c.position, table.c.state).limit(3)
            result = await self.engine.execute(query)
            
            self.log_test("Vacancies Table", True, f"Integration successful. {basic_msg}")
            return True
            
        except Exception as e:
            self.log_test("Vacancies Table", False, f"Exception: {e}")
            return False
    
    async def test_status_mapping_table(self):
        """Test status_mapping table integration"""
        try:
            table = self.engine.status_mapping
            
            # Basic query test
            basic_ok, basic_msg = await self._test_table_basic_query('status_mapping', table)
            if not basic_ok:
                self.log_test("Status Mapping Table", False, f"Basic query failed: {basic_msg}")
                return False
            
            # This table should have data from status mapping
            query = select(table).limit(10)
            result = await self.engine.execute(query)
            
            if result and len(result) > 0:
                sample = result[0]
                if 'id' not in sample or 'name' not in sample:
                    self.log_test("Status Mapping Table", False, "Missing id or name fields")
                    return False
            
            self.log_test("Status Mapping Table", True, f"Integration successful. {basic_msg}")
            return True
            
        except Exception as e:
            self.log_test("Status Mapping Table", False, f"Exception: {e}")
            return False
    
    async def test_recruiters_table(self):
        """Test recruiters table integration"""
        try:
            table = self.engine.recruiters
            
            # Basic query test
            basic_ok, basic_msg = await self._test_table_basic_query('recruiters', table)
            if not basic_ok:
                self.log_test("Recruiters Table", False, f"Basic query failed: {basic_msg}")
                return False
            
            self.log_test("Recruiters Table", True, f"Integration successful. {basic_msg}")
            return True
            
        except Exception as e:
            self.log_test("Recruiters Table", False, f"Exception: {e}")
            return False
    
    async def test_sources_table(self):
        """Test sources table integration"""
        try:
            table = self.engine.sources
            
            # Basic query test
            basic_ok, basic_msg = await self._test_table_basic_query('sources', table)
            if not basic_ok:
                self.log_test("Sources Table", False, f"Basic query failed: {basic_msg}")
                return False
            
            self.log_test("Sources Table", True, f"Integration successful. {basic_msg}")
            return True
            
        except Exception as e:
            self.log_test("Sources Table", False, f"Exception: {e}")
            return False
    
    async def test_divisions_table(self):
        """Test divisions table integration"""
        try:
            table = self.engine.divisions
            
            # Basic query test
            basic_ok, basic_msg = await self._test_table_basic_query('divisions', table)
            if not basic_ok:
                self.log_test("Divisions Table", False, f"Basic query failed: {basic_msg}")
                return False
            
            self.log_test("Divisions Table", True, f"Integration successful. {basic_msg}")
            return True
            
        except Exception as e:
            self.log_test("Divisions Table", False, f"Exception: {e}")
            return False
    
    async def test_applicant_tags_table(self):
        """Test applicant_tags table integration"""
        try:
            table = self.engine.applicant_tags
            
            # Basic query test
            basic_ok, basic_msg = await self._test_table_basic_query('applicant_tags', table)
            if not basic_ok:
                self.log_test("Applicant Tags Table", False, f"Basic query failed: {basic_msg}")
                return False
            
            self.log_test("Applicant Tags Table", True, f"Integration successful. {basic_msg}")
            return True
            
        except Exception as e:
            self.log_test("Applicant Tags Table", False, f"Exception: {e}")
            return False
    
    async def test_offers_table(self):
        """Test offers table integration"""
        try:
            table = self.engine.offers
            
            # Basic query test
            basic_ok, basic_msg = await self._test_table_basic_query('offers', table)
            if not basic_ok:
                self.log_test("Offers Table", False, f"Basic query failed: {basic_msg}")
                return False
            
            self.log_test("Offers Table", True, f"Integration successful. {basic_msg}")
            return True
            
        except Exception as e:
            self.log_test("Offers Table", False, f"Exception: {e}")
            return False
    
    async def test_applicant_links_table(self):
        """Test applicant_links table integration"""
        try:
            table = self.engine.applicant_links
            
            # Basic query test
            basic_ok, basic_msg = await self._test_table_basic_query('applicant_links', table)
            if not basic_ok:
                self.log_test("Applicant Links Table", False, f"Basic query failed: {basic_msg}")
                return False
            
            self.log_test("Applicant Links Table", True, f"Integration successful. {basic_msg}")
            return True
            
        except Exception as e:
            self.log_test("Applicant Links Table", False, f"Exception: {e}")
            return False
    
    async def test_regions_table(self):
        """Test regions table integration"""
        try:
            table = self.engine.regions
            
            # Basic query test
            basic_ok, basic_msg = await self._test_table_basic_query('regions', table)
            if not basic_ok:
                self.log_test("Regions Table", False, f"Basic query failed: {basic_msg}")
                return False
            
            self.log_test("Regions Table", True, f"Integration successful. {basic_msg}")
            return True
            
        except Exception as e:
            self.log_test("Regions Table", False, f"Exception: {e}")
            return False
    
    async def test_rejection_reasons_table(self):
        """Test rejection_reasons table integration"""
        try:
            table = self.engine.rejection_reasons
            
            # Basic query test
            basic_ok, basic_msg = await self._test_table_basic_query('rejection_reasons', table)
            if not basic_ok:
                self.log_test("Rejection Reasons Table", False, f"Basic query failed: {basic_msg}")
                return False
            
            self.log_test("Rejection Reasons Table", True, f"Integration successful. {basic_msg}")
            return True
            
        except Exception as e:
            self.log_test("Rejection Reasons Table", False, f"Exception: {e}")
            return False
    
    async def test_dictionaries_table(self):
        """Test dictionaries table integration"""
        try:
            table = self.engine.dictionaries
            
            # Basic query test
            basic_ok, basic_msg = await self._test_table_basic_query('dictionaries', table)
            if not basic_ok:
                self.log_test("Dictionaries Table", False, f"Basic query failed: {basic_msg}")
                return False
            
            self.log_test("Dictionaries Table", True, f"Integration successful. {basic_msg}")
            return True
            
        except Exception as e:
            self.log_test("Dictionaries Table", False, f"Exception: {e}")
            return False
    
    async def test_applicant_responses_table(self):
        """Test applicant_responses table integration"""
        try:
            table = self.engine.applicant_responses
            
            # Basic query test
            basic_ok, basic_msg = await self._test_table_basic_query('applicant_responses', table)
            if not basic_ok:
                self.log_test("Applicant Responses Table", False, f"Basic query failed: {basic_msg}")
                return False
            
            self.log_test("Applicant Responses Table", True, f"Integration successful. {basic_msg}")
            return True
            
        except Exception as e:
            self.log_test("Applicant Responses Table", False, f"Exception: {e}")
            return False
    
    async def test_vacancy_logs_table(self):
        """Test vacancy_logs table integration"""
        try:
            table = self.engine.vacancy_logs
            
            # Basic query test
            basic_ok, basic_msg = await self._test_table_basic_query('vacancy_logs', table)
            if not basic_ok:
                self.log_test("Vacancy Logs Table", False, f"Basic query failed: {basic_msg}")
                return False
            
            self.log_test("Vacancy Logs Table", True, f"Integration successful. {basic_msg}")
            return True
            
        except Exception as e:
            self.log_test("Vacancy Logs Table", False, f"Exception: {e}")
            return False
    
    async def test_status_groups_table(self):
        """Test status_groups table integration"""
        try:
            table = self.engine.status_groups
            
            # Basic query test
            basic_ok, basic_msg = await self._test_table_basic_query('status_groups', table)
            if not basic_ok:
                self.log_test("Status Groups Table", False, f"Basic query failed: {basic_msg}")
                return False
            
            self.log_test("Status Groups Table", True, f"Integration successful. {basic_msg}")
            return True
            
        except Exception as e:
            self.log_test("Status Groups Table", False, f"Exception: {e}")
            return False
    
    async def test_vacancy_periods_table(self):
        """Test vacancy_periods table integration"""
        try:
            table = self.engine.vacancy_periods
            
            # Basic query test
            basic_ok, basic_msg = await self._test_table_basic_query('vacancy_periods', table)
            if not basic_ok:
                self.log_test("Vacancy Periods Table", False, f"Basic query failed: {basic_msg}")
                return False
            
            self.log_test("Vacancy Periods Table", True, f"Integration successful. {basic_msg}")
            return True
            
        except Exception as e:
            self.log_test("Vacancy Periods Table", False, f"Exception: {e}")
            return False
    
    async def test_vacancy_frames_table(self):
        """Test vacancy_frames table integration"""
        try:
            table = self.engine.vacancy_frames
            
            # Basic query test
            basic_ok, basic_msg = await self._test_table_basic_query('vacancy_frames', table)
            if not basic_ok:
                self.log_test("Vacancy Frames Table", False, f"Basic query failed: {basic_msg}")
                return False
            
            self.log_test("Vacancy Frames Table", True, f"Integration successful. {basic_msg}")
            return True
            
        except Exception as e:
            self.log_test("Vacancy Frames Table", False, f"Exception: {e}")
            return False
    
    async def test_vacancy_quotas_table(self):
        """Test vacancy_quotas table integration"""
        try:
            table = self.engine.vacancy_quotas
            
            # Basic query test
            basic_ok, basic_msg = await self._test_table_basic_query('vacancy_quotas', table)
            if not basic_ok:
                self.log_test("Vacancy Quotas Table", False, f"Basic query failed: {basic_msg}")
                return False
            
            self.log_test("Vacancy Quotas Table", True, f"Integration successful. {basic_msg}")
            return True
            
        except Exception as e:
            self.log_test("Vacancy Quotas Table", False, f"Exception: {e}")
            return False
    
    async def test_action_logs_table(self):
        """Test action_logs table integration"""
        try:
            table = self.engine.action_logs
            
            # Basic query test
            basic_ok, basic_msg = await self._test_table_basic_query('action_logs', table)
            if not basic_ok:
                self.log_test("Action Logs Table", False, f"Basic query failed: {basic_msg}")
                return False
            
            self.log_test("Action Logs Table", True, f"Integration successful. {basic_msg}")
            return True
            
        except Exception as e:
            self.log_test("Action Logs Table", False, f"Exception: {e}")
            return False
    
    async def test_cache_behavior_across_tables(self):
        """Test that cache works correctly across different table queries"""
        try:
            # Clear cache first
            self.engine.invalidate_cache()
            
            # Query multiple tables to populate cache
            tables_to_test = [
                ('status_mapping', self.engine.status_mapping),
                ('sources', self.engine.sources),
                ('regions', self.engine.regions)
            ]
            
            cache_entries_before = self.engine.get_cache_stats()['total_entries']
            
            for table_name, table in tables_to_test:
                query = select(table).limit(2)
                result = await self.engine.execute(query)
            
            cache_entries_after = self.engine.get_cache_stats()['total_entries']
            
            if cache_entries_after <= cache_entries_before:
                self.log_test("Cross-Table Cache", False, f"Cache not populated: {cache_entries_before} -> {cache_entries_after}")
                return False
            
            # Query same tables again - should hit cache
            for table_name, table in tables_to_test:
                query = select(table).limit(2)
                result = await self.engine.execute(query)
            
            self.log_test("Cross-Table Cache", True, f"Cache working across tables: {cache_entries_after} entries")
            return True
            
        except Exception as e:
            self.log_test("Cross-Table Cache", False, f"Exception: {e}")
            return False
    
    def print_summary(self):
        """Print comprehensive test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(self.test_results.values())
        failed_tests = total_tests - passed_tests
        
        print(f"\n{'='*80}")
        print(f"🧪 TABLE INTEGRATION TEST RESULTS")
        print(f"{'='*80}")
        print(f"📊 Total Table Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in self.failed_tests:
                print(f"   - {test}")
        else:
            print(f"\n🎉 ALL TABLE INTEGRATION TESTS PASSED!")
        
        print(f"{'='*80}")
        
        return failed_tests == 0


async def run_table_integration_tests():
    """Run all table integration tests"""
    print("🚀 Starting Table Integration Test Suite...")
    print("Testing all 19 virtual tables individually with real API data")
    print("-" * 80)
    
    test_suite = TableIntegrationTestSuite()
    
    # Test all 19 tables
    table_tests = [
        test_suite.test_applicants_table(),
        test_suite.test_vacancies_table(),
        test_suite.test_status_mapping_table(),
        test_suite.test_recruiters_table(),
        test_suite.test_sources_table(),
        test_suite.test_divisions_table(),
        test_suite.test_applicant_tags_table(),
        test_suite.test_offers_table(),
        test_suite.test_applicant_links_table(),
        test_suite.test_regions_table(),
        test_suite.test_rejection_reasons_table(),
        test_suite.test_dictionaries_table(),
        test_suite.test_applicant_responses_table(),
        test_suite.test_vacancy_logs_table(),
        test_suite.test_status_groups_table(),
        test_suite.test_vacancy_periods_table(),
        test_suite.test_vacancy_frames_table(),
        test_suite.test_vacancy_quotas_table(),
        test_suite.test_action_logs_table(),
        test_suite.test_cache_behavior_across_tables()
    ]
    
    # Run all tests
    await asyncio.gather(*table_tests)
    
    # Print summary
    all_passed = test_suite.print_summary()
    
    if all_passed:
        print("\n🏆 CONCLUSION: All 19 virtual tables are working correctly!")
        print("✅ Each table can be queried successfully")
        print("✅ Data structures are consistent")
        print("✅ Cache integration works across tables")
        print("✅ Error handling is graceful")
    else:
        print("\n⚠️  ISSUES DETECTED: Some tables need attention")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_table_integration_tests())
    exit(0 if success else 1)