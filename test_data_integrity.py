#!/usr/bin/env python3
"""
Test data integrity and relationships in the actual database
Verifies that all necessary data for cross-entity filtering exists
"""

import asyncio
import json
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Set, Tuple
from huntflow_local_client import HuntflowLocalClient
from enhanced_metrics_calculator import EnhancedMetricsCalculator
from analyze_logs import LogAnalyzer

class DataIntegrityTester:
    """Tests data integrity and relationships in the database"""
    
    def __init__(self):
        self.client = HuntflowLocalClient()
        self.calc = EnhancedMetricsCalculator(self.client, None)
        self.log_analyzer = LogAnalyzer(self.client.db_path)
        self.issues = []
        self.warnings = []
        self.stats = defaultdict(int)
    
    async def run_all_tests(self):
        """Run all data integrity tests"""
        print("=" * 70)
        print("🔍 DATA INTEGRITY AND RELATIONSHIP TEST")
        print("=" * 70)
        
        # Test 1: Log Analyzer Initialization
        print("\n📊 Test 1: Log Analyzer Initialization")
        self.test_log_analyzer_init()
        
        # Test 2: Log Data Completeness
        print("\n📊 Test 2: Log Data Completeness")
        self.test_log_data_completeness()
        
        # Test 3: Entity Relationships in Logs
        print("\n📊 Test 3: Entity Relationships in Logs")
        self.test_entity_relationships()
        
        # Test 4: Cross-Reference API vs Logs
        print("\n📊 Test 4: Cross-Reference API vs Logs")
        await self.test_api_vs_logs()
        
        # Test 5: Hire Data Integrity
        print("\n📊 Test 5: Hire Data Integrity")
        await self.test_hire_data_integrity()
        
        # Test 6: Source-Recruiter Mappings
        print("\n📊 Test 6: Source-Recruiter Mappings")
        self.test_source_recruiter_mappings()
        
        # Test 7: Vacancy State Consistency
        print("\n📊 Test 7: Vacancy State Consistency")
        await self.test_vacancy_states()
        
        # Summary
        self.print_summary()
    
    def test_log_analyzer_init(self):
        """Test if log analyzer is properly initialized"""
        try:
            # Check if log analyzer exists
            if not self.log_analyzer:
                self.issues.append("❌ Log analyzer is not initialized")
                return
            
            # Check if database path is valid
            db_path = self.client.db_path
            import os
            if not os.path.exists(db_path):
                self.issues.append(f"❌ Database file not found: {db_path}")
                return
            
            # Check if we can get logs
            all_logs = self.log_analyzer.get_merged_logs()
            if not all_logs:
                self.issues.append("❌ No logs found in database")
                return
            
            print(f"✅ Log analyzer initialized successfully")
            print(f"   - Database path: {db_path}")
            print(f"   - Total logs: {len(all_logs)}")
            self.stats['total_logs'] = len(all_logs)
            
        except Exception as e:
            self.issues.append(f"❌ Log analyzer initialization error: {e}")
    
    def test_log_data_completeness(self):
        """Test completeness of log data"""
        all_logs = self.log_analyzer.get_merged_logs()
        
        # Track missing fields
        missing_fields = defaultdict(int)
        logs_with_complete_data = 0
        
        required_fields = {
            'STATUS': ['applicant_id', 'vacancy_id', 'status_id', 'created'],
            'ADD': ['applicant_id', 'vacancy_id', 'source_id', 'created'],
            'COMMENT': ['applicant_id', 'account_info', 'created']
        }
        
        for log in all_logs:
            log_type = log.get('type', 'UNKNOWN')
            has_all_fields = True
            
            # Check required fields based on log type
            if log_type in required_fields:
                for field in required_fields[log_type]:
                    if field not in log or log[field] is None:
                        missing_fields[f"{log_type}.{field}"] += 1
                        has_all_fields = False
            
            # Check account_info structure
            if 'account_info' in log:
                account_info = log['account_info']
                if isinstance(account_info, dict):
                    if 'id' not in account_info:
                        missing_fields['account_info.id'] += 1
                        has_all_fields = False
                    if 'name' not in account_info:
                        missing_fields['account_info.name'] += 1
                        has_all_fields = False
                else:
                    missing_fields['account_info.invalid_type'] += 1
                    has_all_fields = False
            
            if has_all_fields:
                logs_with_complete_data += 1
        
        # Report findings
        total_logs = len(all_logs)
        completeness_pct = (logs_with_complete_data / total_logs * 100) if total_logs > 0 else 0
        
        print(f"✅ Log data completeness: {completeness_pct:.1f}%")
        print(f"   - Complete logs: {logs_with_complete_data}/{total_logs}")
        
        if missing_fields:
            print("\n   ⚠️  Missing fields detected:")
            for field, count in sorted(missing_fields.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"      - {field}: {count} logs")
                if count > total_logs * 0.1:  # More than 10% missing
                    self.warnings.append(f"Field '{field}' missing in {count} logs ({count/total_logs*100:.1f}%)")
    
    def test_entity_relationships(self):
        """Test entity relationships in logs"""
        all_logs = self.log_analyzer.get_merged_logs()
        
        # Track relationships
        relationships = {
            'applicant_to_vacancy': set(),
            'applicant_to_recruiter': set(),
            'applicant_to_source': set(),
            'vacancy_to_recruiter': set(),
            'source_to_recruiter': set(),
            'vacancy_to_source': set()
        }
        
        # Track orphaned entities
        orphaned = {
            'applicants_without_vacancy': set(),
            'applicants_without_recruiter': set(),
            'logs_without_account_info': 0
        }
        
        for log in all_logs:
            applicant_id = log.get('applicant_id')
            vacancy_id = log.get('vacancy_id') or log.get('vacancy')
            source_id = log.get('source_id') or log.get('source')
            
            # Extract recruiter info
            recruiter_id = None
            account_info = log.get('account_info', {})
            if isinstance(account_info, dict):
                recruiter_id = account_info.get('id')
            else:
                orphaned['logs_without_account_info'] += 1
            
            # Build relationships
            if applicant_id and vacancy_id:
                relationships['applicant_to_vacancy'].add((applicant_id, vacancy_id))
            elif applicant_id:
                orphaned['applicants_without_vacancy'].add(applicant_id)
            
            if applicant_id and recruiter_id:
                relationships['applicant_to_recruiter'].add((applicant_id, recruiter_id))
            elif applicant_id:
                orphaned['applicants_without_recruiter'].add(applicant_id)
            
            if applicant_id and source_id:
                relationships['applicant_to_source'].add((applicant_id, source_id))
            
            if vacancy_id and recruiter_id:
                relationships['vacancy_to_recruiter'].add((vacancy_id, recruiter_id))
            
            if source_id and recruiter_id:
                relationships['source_to_recruiter'].add((source_id, recruiter_id))
            
            if vacancy_id and source_id:
                relationships['vacancy_to_source'].add((vacancy_id, source_id))
        
        # Report findings
        print("✅ Entity relationships found:")
        for rel_type, rel_set in relationships.items():
            print(f"   - {rel_type}: {len(rel_set)} unique pairs")
            self.stats[f'rel_{rel_type}'] = len(rel_set)
        
        print("\n   ⚠️  Orphaned entities:")
        print(f"   - Applicants without vacancy: {len(orphaned['applicants_without_vacancy'])}")
        print(f"   - Applicants without recruiter: {len(orphaned['applicants_without_recruiter'])}")
        print(f"   - Logs without account_info: {orphaned['logs_without_account_info']}")
        
        # Check for critical issues
        if len(orphaned['applicants_without_recruiter']) > len(relationships['applicant_to_recruiter']) * 0.5:
            self.issues.append("❌ More than 50% of applicants have no recruiter information")
    
    async def test_api_vs_logs(self):
        """Cross-reference API data with log data"""
        print("\n   Comparing API data with logs...")
        
        # Get data from both sources
        api_recruiters = await self.calc.recruiters_all()
        api_sources = await self.calc.sources_all()
        api_vacancies = await self.calc.vacancies_all()
        
        # Get unique IDs from logs
        all_logs = self.log_analyzer.get_merged_logs()
        log_recruiter_ids = set()
        log_source_ids = set()
        log_vacancy_ids = set()
        
        for log in all_logs:
            # Recruiter IDs
            account_info = log.get('account_info', {})
            if isinstance(account_info, dict) and 'id' in account_info:
                log_recruiter_ids.add(account_info['id'])
            
            # Source IDs
            source_id = log.get('source_id') or log.get('source')
            if source_id:
                log_source_ids.add(source_id)
            
            # Vacancy IDs
            vacancy_id = log.get('vacancy_id') or log.get('vacancy')
            if vacancy_id:
                log_vacancy_ids.add(vacancy_id)
        
        # Compare
        api_recruiter_ids = {r['id'] for r in api_recruiters}
        api_source_ids = {s['id'] for s in api_sources}
        api_vacancy_ids = {v['id'] for v in api_vacancies}
        
        # Find mismatches
        recruiters_only_in_logs = log_recruiter_ids - api_recruiter_ids
        recruiters_only_in_api = api_recruiter_ids - log_recruiter_ids
        
        sources_only_in_logs = log_source_ids - api_source_ids
        sources_only_in_api = api_source_ids - log_source_ids
        
        print(f"\n   Recruiter comparison:")
        print(f"   - In API: {len(api_recruiter_ids)}")
        print(f"   - In logs: {len(log_recruiter_ids)}")
        print(f"   - Only in logs: {len(recruiters_only_in_logs)}")
        print(f"   - Only in API: {len(recruiters_only_in_api)}")
        
        print(f"\n   Source comparison:")
        print(f"   - In API: {len(api_source_ids)}")
        print(f"   - In logs: {len(log_source_ids)}")
        print(f"   - Only in logs: {len(sources_only_in_logs)}")
        print(f"   - Only in API: {len(sources_only_in_api)}")
        
        if len(sources_only_in_logs) > 10:
            self.warnings.append(f"⚠️  {len(sources_only_in_logs)} sources found in logs but not in API")
    
    async def test_hire_data_integrity(self):
        """Test integrity of hire data"""
        hired_applicants = self.log_analyzer.get_hired_applicants()
        
        print(f"\n   Total hires found: {len(hired_applicants)}")
        
        # Check hire data completeness
        complete_hires = 0
        missing_recruiter = 0
        missing_source = 0
        missing_time_to_hire = 0
        
        for hire in hired_applicants:
            has_all_data = True
            
            if not hire.get('recruiter_id') and not hire.get('recruiter_name'):
                missing_recruiter += 1
                has_all_data = False
            
            if not hire.get('source_id') and not hire.get('source'):
                missing_source += 1
                has_all_data = False
            
            if not hire.get('time_to_hire'):
                missing_time_to_hire += 1
                has_all_data = False
            
            if has_all_data:
                complete_hires += 1
        
        completeness_pct = (complete_hires / len(hired_applicants) * 100) if hired_applicants else 0
        
        print(f"   - Complete hire records: {complete_hires}/{len(hired_applicants)} ({completeness_pct:.1f}%)")
        print(f"   - Missing recruiter info: {missing_recruiter}")
        print(f"   - Missing source info: {missing_source}")
        print(f"   - Missing time_to_hire: {missing_time_to_hire}")
        
        if missing_recruiter > len(hired_applicants) * 0.2:
            self.issues.append(f"❌ {missing_recruiter}/{len(hired_applicants)} hires missing recruiter info")
        
        if missing_source > len(hired_applicants) * 0.3:
            self.warnings.append(f"⚠️  {missing_source}/{len(hired_applicants)} hires missing source info")
    
    def test_source_recruiter_mappings(self):
        """Test source-recruiter relationship mappings"""
        all_logs = self.log_analyzer.get_merged_logs()
        
        # Build source-recruiter mapping
        source_recruiters = defaultdict(set)
        recruiter_sources = defaultdict(set)
        
        for log in all_logs:
            source_id = log.get('source_id') or log.get('source')
            account_info = log.get('account_info', {})
            
            if isinstance(account_info, dict) and 'id' in account_info and source_id:
                recruiter_id = account_info['id']
                source_recruiters[source_id].add(recruiter_id)
                recruiter_sources[recruiter_id].add(source_id)
        
        print(f"\n   Source-Recruiter mappings:")
        print(f"   - Sources with recruiters: {len(source_recruiters)}")
        print(f"   - Recruiters with sources: {len(recruiter_sources)}")
        
        # Find sources used by multiple recruiters
        shared_sources = {s: len(r) for s, r in source_recruiters.items() if len(r) > 1}
        if shared_sources:
            print(f"   - Sources used by multiple recruiters: {len(shared_sources)}")
            top_shared = sorted(shared_sources.items(), key=lambda x: x[1], reverse=True)[:5]
            for source_id, recruiter_count in top_shared:
                print(f"     • Source {source_id}: used by {recruiter_count} recruiters")
        
        # Find recruiters using multiple sources
        multi_source_recruiters = {r: len(s) for r, s in recruiter_sources.items() if len(s) > 1}
        if multi_source_recruiters:
            print(f"   - Recruiters using multiple sources: {len(multi_source_recruiters)}")
    
    async def test_vacancy_states(self):
        """Test vacancy state consistency"""
        vacancies = await self.calc.vacancies_all()
        
        state_counts = defaultdict(int)
        for vacancy in vacancies:
            state = vacancy.get('state', 'UNKNOWN')
            state_counts[state] += 1
        
        print(f"\n   Vacancy states:")
        for state, count in state_counts.items():
            print(f"   - {state}: {count} vacancies")
        
        # Check for inconsistencies
        if 'UNKNOWN' in state_counts:
            self.warnings.append(f"⚠️  {state_counts['UNKNOWN']} vacancies have unknown state")
        
        # Check if closed vacancies have hires
        closed_vacancies = [v for v in vacancies if v.get('state') == 'CLOSED']
        closed_with_hires = sum(1 for v in closed_vacancies if v.get('hire_count', 0) > 0)
        
        print(f"\n   Closed vacancy analysis:")
        print(f"   - Total closed: {len(closed_vacancies)}")
        print(f"   - With hires: {closed_with_hires}")
        print(f"   - Without hires: {len(closed_vacancies) - closed_with_hires}")
        
        if closed_with_hires < len(closed_vacancies) * 0.8:
            self.warnings.append(f"⚠️  Only {closed_with_hires}/{len(closed_vacancies)} closed vacancies have hires")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 DATA INTEGRITY TEST SUMMARY")
        print("=" * 70)
        
        if not self.issues and not self.warnings:
            print("\n✅ ALL DATA INTEGRITY TESTS PASSED!")
            print("   The database has all necessary data for cross-entity filtering.")
        else:
            if self.issues:
                print(f"\n❌ CRITICAL ISSUES FOUND ({len(self.issues)}):")
                for issue in self.issues:
                    print(f"   {issue}")
            
            if self.warnings:
                print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
                for warning in self.warnings:
                    print(f"   {warning}")
        
        print("\n📈 Key Statistics:")
        print(f"   - Total logs: {self.stats.get('total_logs', 0)}")
        print(f"   - Applicant-Recruiter pairs: {self.stats.get('rel_applicant_to_recruiter', 0)}")
        print(f"   - Source-Recruiter pairs: {self.stats.get('rel_source_to_recruiter', 0)}")
        print(f"   - Vacancy-Recruiter pairs: {self.stats.get('rel_vacancy_to_recruiter', 0)}")
        
        if self.issues:
            print("\n🔧 RECOMMENDATIONS:")
            print("   1. Add recruiter extraction to hire records in analyze_logs.py")
            print("   2. Ensure all logs have proper account_info structure")
            print("   3. Map source IDs between logs and API responses")
            print("   4. Add fallback logic for missing relationships")

async def main():
    tester = DataIntegrityTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())