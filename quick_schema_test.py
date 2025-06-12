#!/usr/bin/env python3
"""
Quick Schema Validation Test

Fast validation of schema compliance with CLAUDE.md
"""

import os
import re
from typing import Dict, List


def test_schema_compliance() -> Dict[str, bool]:
    """Test schema compliance with CLAUDE.md specification"""
    
    # Read schema file
    try:
        with open('huntflow_schema.py', 'r') as f:
            schema_content = f.read()
    except FileNotFoundError:
        return {"error": "huntflow_schema.py not found"}
    
    tests = {}
    
    # 1. Test correct API endpoints
    tests['uses_vacancies_statuses_endpoint'] = '/vacancies/statuses' in schema_content
    tests['uses_applicants_search_endpoint'] = '/applicants/search' in schema_content
    tests['uses_applicants_sources_endpoint'] = '/applicants/sources' in schema_content
    tests['uses_coworkers_endpoint'] = '/coworkers' in schema_content
    
    # 2. Test forbidden old field names are removed
    tests['no_time_to_hire_days_field'] = "Column('time_to_hire_days'" not in schema_content
    tests['no_vacancy_id_field'] = "Column('vacancy_id'" not in schema_content
    tests['no_source_id_field'] = "Column('source_id'" not in schema_content
    tests['no_recruiter_id_field'] = "Column('recruiter_id'" not in schema_content
    
    # 3. Test correct API field names exist
    tests['has_vacancy_field'] = "Column('vacancy'" in schema_content
    tests['has_source_field'] = "Column('source'" in schema_content
    tests['has_recruiter_field'] = "Column('recruiter'" in schema_content
    
    # 4. Test logs-based status retrieval exists
    tests['has_logs_status_method'] = '_get_applicant_status_from_logs' in schema_content
    tests['has_logs_endpoint_call'] = '/logs' in schema_content
    
    # 5. Test pagination uses correct params
    tests['uses_count_param'] = '"count": 100' in schema_content
    tests['uses_page_param'] = '"page": page' in schema_content
    
    # 6. Test required tables exist
    tests['has_sources_table'] = "self.sources = Table('sources'" in schema_content
    tests['has_divisions_table'] = "self.divisions = Table('divisions'" in schema_content
    
    return tests


def test_demo_data_removed() -> Dict[str, bool]:
    """Test that hardcoded demo data is removed"""
    
    tests = {}
    
    # Check for hardcoded demo data in schema files
    demo_patterns = [
        'Анна Смирнова',
        'demo_value',
        'demo_data',
        'fallback.*recruiter',  # Fallback recruiter patterns
    ]
    
    files_to_check = [
        'huntflow_schema.py',
        'sqlalchemy_executor.py'
    ]
    
    for pattern in demo_patterns:
        found_in_files = []
        
        for filename in files_to_check:
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    content = f.read()
                    if re.search(pattern, content, re.IGNORECASE):
                        found_in_files.append(filename)
        
        tests[f'no_{pattern.replace(".*", "_")}_in_code'] = len(found_in_files) == 0
        
        if found_in_files:
            print(f"⚠️  Found '{pattern}' in: {', '.join(found_in_files)}")
    
    return tests


def main():
    """Run quick schema validation"""
    
    print("⚡ Quick Schema Validation")
    print("=" * 40)
    
    print("\n📋 Testing Schema Compliance...")
    compliance_tests = test_schema_compliance()
    
    if 'error' in compliance_tests:
        print(f"❌ {compliance_tests['error']}")
        return False
    
    passed = 0
    total = len(compliance_tests)
    
    for test_name, result in compliance_tests.items():
        status = "✅" if result else "❌"
        print(f"  {status} {test_name.replace('_', ' ').title()}")
        if result:
            passed += 1
    
    print(f"\n📊 Compliance Score: {passed}/{total} ({passed/total*100:.1f}%)")
    
    print("\n🔍 Testing Demo Data Removal...")
    demo_tests = test_demo_data_removed()
    
    demo_passed = 0
    demo_total = len(demo_tests)
    
    for test_name, result in demo_tests.items():
        status = "✅" if result else "❌"
        print(f"  {status} {test_name.replace('_', ' ').title()}")
        if result:
            demo_passed += 1
    
    print(f"\n🧹 Demo Data Removal Score: {demo_passed}/{demo_total} ({demo_passed/demo_total*100:.1f}%)")
    
    # Overall score
    total_tests = total + demo_total
    total_passed = passed + demo_passed
    overall_score = total_passed / total_tests * 100
    
    print(f"\n🎯 Overall Score: {total_passed}/{total_tests} ({overall_score:.1f}%)")
    
    if overall_score >= 90:
        print("🎉 Schema is excellent!")
        return True
    elif overall_score >= 75:
        print("✅ Schema is good with minor issues")
        return True
    else:
        print("⚠️  Schema needs improvement")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)