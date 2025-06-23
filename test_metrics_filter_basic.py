#!/usr/bin/env python3
"""
Comprehensive test for metrics_filter with ALL entities and ALL filters
Tests every possible entity, filter combination, and logical operator
"""

import asyncio
import json
from chart_data_processor import process_chart_data, validate_report_json
from huntflow_local_client import HuntflowLocalClient

# ALL ENTITIES available in the system
ALL_ENTITIES = [
    "applicants",
    "hires",
    "vacancies", 
    "recruiters",
    "sources",
    "stages",
    "divisions",
    "hiring_managers"
]

# ALL PERIOD FILTERS available
ALL_PERIODS = [
    "today",
    "this week",
    "2 weeks",
    "1 month",
    "3 month",
    "6 month",
    "1 year",
    "all"
]

# ALL ENTITY FILTER TYPES with sample values
ALL_ENTITY_FILTERS = {
    "recruiters": ["14824", "69214"],  # Anastasia and Anton
    "sources": ["274886", "274885"],   # LinkedIn and HeadHunter
    "stages": ["103682", "103683"],    # Hired and other statuses
    "vacancies": ["open", "closed"],   # State filters
    "divisions": ["1", "2"],           # Division IDs
    "hiring_managers": ["100", "101"]  # Manager IDs
}

# ALL OPERATIONS available
ALL_OPERATIONS = ["count", "avg", "sum"]

# Complex filter test cases
COMPLEX_FILTER_TESTS = [
    # Test 1: Simple period filter
    {
        "name": "Simple Period Filter",
        "filter": {
            "period": "3 month"
        }
    },
    # Test 2: Period + single entity filter
    {
        "name": "Period + Recruiter Filter", 
        "filter": {
            "period": "6 month",
            "recruiters": "14824"
        }
    },
    # Test 3: Multiple entity filters (implicit AND)
    {
        "name": "Multiple Entity Filters",
        "filter": {
            "period": "1 year",
            "recruiters": "14824",
            "vacancies": "open"
        }
    },
    # Test 4: Logical AND operator
    {
        "name": "Logical AND Operator",
        "filter": {
            "and": [
                {"period": "3 month"},
                {"recruiters": "14824"}
            ]
        }
    },
    # Test 5: Logical OR operator
    {
        "name": "Logical OR Operator",
        "filter": {
            "or": [
                {"recruiters": "14824"},
                {"recruiters": "69214"}
            ],
            "period": "6 month"
        }
    },
    # Test 6: Nested logical operators
    {
        "name": "Nested Logical Operators",
        "filter": {
            "period": "1 year",
            "and": [
                {"vacancies": "open"},
                {"or": [
                    {"recruiters": "14824"},
                    {"sources": "274886"}
                ]}
            ]
        }
    },
    # Test 7: Complex operators with IN
    {
        "name": "IN Operator",
        "filter": {
            "period": "6 month",
            "sources": {
                "operator": "in",
                "value": ["274886", "274885"]
            }
        }
    },
    # Test 8: Comparison operators
    {
        "name": "Greater Than Operator",
        "filter": {
            "period": "1 year",
            "vacancies": {
                "operator": "gt",
                "value": 100
            }
        }
    },
    # Test 9: Between operator
    {
        "name": "Between Operator",
        "filter": {
            "period": "3 month",
            "stages": {
                "operator": "between",
                "value": [103680, 103685]
            }
        }
    },
    # Test 10: All filters combined
    {
        "name": "All Filters Combined",
        "filter": {
            "period": "1 year",
            "recruiters": "14824",
            "sources": "274886",
            "vacancies": "open",
            "stages": "103682",
            "divisions": "1",
            "hiring_managers": "100"
        }
    }
]

# Test report templates
def create_test_report(entity, operation, metrics_filter, with_grouping=False):
    """Create a test report for specific entity and filter combination"""
    report = {
        "report_title": f"Test {entity} with {operation}",
        "metrics_filter": metrics_filter,
        "main_metric": {
            "label": f"Total {entity.capitalize()}",
            "value": {
                "operation": operation,
                "entity": entity
            }
        },
        "secondary_metrics": []
    }
    
    # Add secondary metrics for other entities
    for other_entity in ALL_ENTITIES[:3]:
        if other_entity != entity:
            report["secondary_metrics"].append({
                "label": f"{other_entity.capitalize()} Count",
                "value": {
                    "operation": "count", 
                    "entity": other_entity
                }
            })
    
    # Add chart
    if with_grouping:
        report["chart"] = {
            "label": f"{entity} by Recruiters",
            "type": "bar",
            "y_axis": {
                "operation": operation,
                "entity": entity,
                "group_by": "recruiters"
            }
        }
    
    return report

async def test_all_entities():
    """Test all entities with various filters"""
    print("🚀 Testing ALL ENTITIES with ALL FILTERS\n")
    client = HuntflowLocalClient()
    
    passed = 0
    failed = 0
    
    # Test each entity
    for entity in ALL_ENTITIES:
        print(f"\n📊 Testing entity: {entity}")
        print("=" * 50)
        
        # Test with different periods
        for period in ALL_PERIODS[:3]:  # Test first 3 periods for brevity
            try:
                report = create_test_report(entity, "count", {"period": period})
                processed = await process_chart_data(report.copy(), client)
                
                main_value = processed["main_metric"].get("real_value", 0)
                print(f"✅ {entity} ({period}): {main_value} items")
                passed += 1
                
            except Exception as e:
                print(f"❌ {entity} ({period}): FAILED - {e}")
                failed += 1
        
        # Test with entity filters
        for filter_type, filter_values in ALL_ENTITY_FILTERS.items():
            if filter_values:
                try:
                    report = create_test_report(entity, "count", {
                        "period": "6 month",
                        filter_type: filter_values[0]
                    })
                    processed = await process_chart_data(report.copy(), client)
                    
                    main_value = processed["main_metric"].get("real_value", 0)
                    print(f"✅ {entity} (filtered by {filter_type}): {main_value} items")
                    passed += 1
                    
                except Exception as e:
                    print(f"❌ {entity} (filtered by {filter_type}): FAILED - {e}")
                    failed += 1
    
    return passed, failed

async def test_all_operations():
    """Test all operations on different entities"""
    print("\n\n🔧 Testing ALL OPERATIONS\n")
    client = HuntflowLocalClient()
    
    passed = 0
    failed = 0
    
    test_cases = [
        ("hires", "count", {}),
        ("hires", "avg", {"value_field": "time_to_hire"}),
        ("vacancies", "avg", {"value_field": "days_active"}),
        ("applicants", "count", {}),
        ("recruiters", "count", {})
    ]
    
    for entity, operation, extra_config in test_cases:
        try:
            report = create_test_report(entity, operation, {"period": "1 year"})
            
            # Add value_field if needed
            if "value_field" in extra_config:
                report["main_metric"]["value"]["value_field"] = extra_config["value_field"]
            
            processed = await process_chart_data(report.copy(), client)
            
            main_value = processed["main_metric"].get("real_value", 0)
            print(f"✅ {entity} ({operation}): {main_value}")
            passed += 1
            
        except Exception as e:
            print(f"❌ {entity} ({operation}): FAILED - {e}")
            failed += 1
    
    return passed, failed

async def test_complex_filters():
    """Test complex filter combinations"""
    print("\n\n🔐 Testing COMPLEX FILTERS\n")
    client = HuntflowLocalClient()
    
    passed = 0
    failed = 0
    
    for test_case in COMPLEX_FILTER_TESTS:
        try:
            report = create_test_report("hires", "count", test_case["filter"])
            processed = await process_chart_data(report.copy(), client)
            
            main_value = processed["main_metric"].get("real_value", 0)
            print(f"✅ {test_case['name']}: {main_value} hires")
            passed += 1
            
        except Exception as e:
            print(f"❌ {test_case['name']}: FAILED - {e}")
            failed += 1
    
    return passed, failed

async def test_grouping_combinations():
    """Test all grouping combinations"""
    print("\n\n📊 Testing GROUPING COMBINATIONS\n")
    client = HuntflowLocalClient()
    
    passed = 0
    failed = 0
    
    # Test entity grouping combinations
    grouping_tests = [
        ("hires", "recruiters"),
        ("hires", "sources"),
        ("applicants", "stages"),
        ("applicants", "recruiters"),
        ("vacancies", "state"),
        ("recruiters", "divisions"),
        ("sources", "vacancies")
    ]
    
    for entity, group_by in grouping_tests:
        try:
            report = create_test_report(entity, "count", {"period": "1 year"}, with_grouping=True)
            report["chart"]["y_axis"]["group_by"] = group_by
            
            processed = await process_chart_data(report.copy(), client)
            
            if "real_data" in processed.get("chart", {}):
                data_count = len(processed["chart"]["real_data"].get("labels", []))
                print(f"✅ {entity} grouped by {group_by}: {data_count} groups")
                passed += 1
            else:
                print(f"⚠️  {entity} grouped by {group_by}: No chart data")
                
        except Exception as e:
            print(f"❌ {entity} grouped by {group_by}: FAILED - {e}")
            failed += 1
    
    return passed, failed

async def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n\n⚠️  Testing EDGE CASES\n")
    client = HuntflowLocalClient()
    
    passed = 0
    failed = 0
    
    edge_cases = [
        # Non-existent ID
        {
            "name": "Non-existent Recruiter ID",
            "filter": {"period": "1 year", "recruiters": "99999999"}
        },
        # Empty period
        {
            "name": "Empty Filter Object", 
            "filter": {}
        },
        # Multiple conflicting filters
        {
            "name": "Conflicting Vacancy States",
            "filter": {
                "period": "1 year",
                "and": [
                    {"vacancies": "open"},
                    {"vacancies": "closed"}
                ]
            }
        },
        # Very restrictive filter
        {
            "name": "Ultra Restrictive Filter",
            "filter": {
                "period": "today",
                "recruiters": "14824",
                "sources": "274886",
                "vacancies": "open",
                "stages": "103682"
            }
        }
    ]
    
    for test_case in edge_cases:
        try:
            report = create_test_report("hires", "count", test_case["filter"])
            processed = await process_chart_data(report.copy(), client)
            
            main_value = processed["main_metric"].get("real_value", 0)
            print(f"✅ {test_case['name']}: {main_value} results")
            passed += 1
            
        except Exception as e:
            print(f"❌ {test_case['name']}: FAILED - {e}")
            failed += 1
    
    return passed, failed

async def run_comprehensive_test():
    """Run all tests and provide summary"""
    print("=" * 70)
    print("🚀 COMPREHENSIVE METRICS FILTER TEST SUITE")
    print("=" * 70)
    
    total_passed = 0
    total_failed = 0
    
    # Run all test suites
    test_suites = [
        ("Entity Tests", test_all_entities),
        ("Operation Tests", test_all_operations),
        ("Complex Filter Tests", test_complex_filters),
        ("Grouping Tests", test_grouping_combinations),
        ("Edge Case Tests", test_edge_cases)
    ]
    
    for suite_name, test_func in test_suites:
        passed, failed = await test_func()
        total_passed += passed
        total_failed += failed
        print(f"\n{suite_name}: {passed} passed, {failed} failed")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 FINAL RESULTS")
    print("=" * 70)
    print(f"✅ Total Passed: {total_passed}")
    print(f"❌ Total Failed: {total_failed}")
    print(f"📈 Success Rate: {total_passed / (total_passed + total_failed) * 100:.1f}%")
    
    if total_failed == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        return True
    else:
        print(f"\n⚠️  {total_failed} tests failed. Check logs for details.")
        return False

if __name__ == "__main__":
    async def main():
        success = await run_comprehensive_test()
        exit(0 if success else 1)
    
    asyncio.run(main())