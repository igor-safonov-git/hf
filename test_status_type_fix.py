#!/usr/bin/env python3
"""
Test the status type fix in huntflow_metrics.py
Validates that hired status detection now uses robust type field instead of keyword matching
"""
import asyncio
import logging
from huntflow_metrics import HuntflowComputedMetrics

logging.basicConfig(level=logging.INFO)

class MockHuntflowEngine:
    def __init__(self):
        # Mock the required attributes
        self.applicants = None
        self.vacancies = None
        self.applicant_links = None
        self.recruiters = None
        self.sources = None
    
    async def _get_status_mapping(self):
        # Mock status mapping that tests the fix
        return {
            1: {"name": "Interview", "type": "user", "order": 1},
            2: {"name": "Hired Successfully", "type": "user", "order": 2},  # Name suggests hired but type is user
            3: {"name": "Job Offer", "type": "hired", "order": 3},          # Should be detected (type=hired)
            4: {"name": "Принят на работу", "type": "user", "order": 4},    # Russian "hired" but type is user
            5: {"name": "Success", "type": "hired", "order": 5},            # Should be detected (type=hired)
            6: {"name": "Offer", "type": "user", "order": 6},               # Offer status - user type
            7: {"name": "Rejected", "type": "trash", "order": 7}            # Rejection
        }
    
    async def _execute_vacancies_query(self, query):
        return [{"id": 1, "state": "OPEN"}]
    
    async def _get_applicants_data(self):
        return [
            {"id": 1, "vacancy_id": 1, "status_id": 2, "links": [{"vacancy": 1, "status": 2}]},  # Should NOT be counted as hired
            {"id": 2, "vacancy_id": 1, "status_id": 3, "links": [{"vacancy": 1, "status": 3}]},  # Should be counted as hired
            {"id": 3, "vacancy_id": 1, "status_id": 4, "links": [{"vacancy": 1, "status": 4}]},  # Should NOT be counted as hired  
            {"id": 4, "vacancy_id": 1, "status_id": 5, "links": [{"vacancy": 1, "status": 5}]}   # Should be counted as hired
        ]

async def test_hired_status_fix():
    """Test that hired status detection uses type field correctly"""
    print("🎯 Testing Hired Status Type Field Fix")
    print("=" * 50)
    
    engine = MockHuntflowEngine()
    metrics = HuntflowComputedMetrics(engine)
    
    # Test hirings_by_recruiter method which uses hired status detection
    print("\n1. Testing hirings_by_recruiter method...")
    
    # Mock the recruiter-specific data  
    async def mock_vacancies_query(q):
        return [{"id": 1, "state": "OPEN", "coworkers": "[123]"}]
    engine._execute_vacancies_query = mock_vacancies_query
    
    hirings = await metrics.hirings_by_recruiter(123)
    
    print(f"   Hirings detected: {hirings}")
    print(f"   Expected: 2 (only status IDs 3 and 5 have type='hired')")
    
    if hirings == 2:
        print("   ✅ SUCCESS: Only statuses with type='hired' counted")
        print("   ✅ ROBUST: Keyword matching patterns ignored")
    else:
        print("   ❌ FAILURE: Incorrect hired count detected")
        print("   Analysis:")
        print("     Status ID 2 ('Hired Successfully', type='user') should NOT count")
        print("     Status ID 3 ('Job Offer', type='hired') should count")
        print("     Status ID 4 ('Принят на работу', type='user') should NOT count")  
        print("     Status ID 5 ('Success', type='hired') should count")
        return False
    
    return True

async def test_source_effectiveness_fix():
    """Test source effectiveness method uses correct hired detection"""
    print("\n2. Testing source_effectiveness method...")
    
    engine = MockHuntflowEngine()
    metrics = HuntflowComputedMetrics(engine)
    
    # Mock sources mapping
    async def mock_sources_mapping():
        return {1: "LinkedIn", 2: "Website"}
    engine._get_sources_mapping = mock_sources_mapping
    
    # Mock applicants with source data
    async def mock_applicants_data():
        return [
            {"id": 1, "source_id": 1, "status_id": 2},  # LinkedIn, NOT hired (type=user)
            {"id": 2, "source_id": 1, "status_id": 3},  # LinkedIn, hired (type=hired)
            {"id": 3, "source_id": 2, "status_id": 4},  # Website, NOT hired (type=user)
            {"id": 4, "source_id": 2, "status_id": 5}   # Website, hired (type=hired)
        ]
    engine._get_applicants_data = mock_applicants_data
    
    effectiveness = await metrics.source_effectiveness()
    
    print(f"   Source effectiveness results: {len(effectiveness)} sources")
    
    # Should have 2 sources each with 1 hire out of 2 applicants (50% conversion)
    expected_results = {
        "LinkedIn": {"total_applicants": 2, "hires": 1, "conversion_rate": 50.0},
        "Website": {"total_applicants": 2, "hires": 1, "conversion_rate": 50.0}
    }
    
    success = True
    for result in effectiveness:
        source_name = result["source_name"]
        if source_name in expected_results:
            expected = expected_results[source_name]
            if (result["total_applicants"] == expected["total_applicants"] and 
                result["hires"] == expected["hires"] and
                result["conversion_rate"] == expected["conversion_rate"]):
                print(f"   ✅ {source_name}: {result['hires']}/{result['total_applicants']} = {result['conversion_rate']}%")
            else:
                print(f"   ❌ {source_name}: Expected {expected}, got {result}")
                success = False
        else:
            print(f"   ❌ Unexpected source: {source_name}")
            success = False
    
    return success

async def test_time_to_hire_fix():
    """Test time to hire method uses correct hired detection"""
    print("\n3. Testing time_to_hire method...")
    
    engine = MockHuntflowEngine()
    metrics = HuntflowComputedMetrics(engine)
    
    # Mock applicants with hire dates
    from datetime import datetime, timedelta
    base_date = datetime.now()
    
    async def mock_applicants_time_data():
        return [
            {
                "id": 1, 
                "status_id": 2,  # NOT hired (type=user) 
                "created": (base_date - timedelta(days=30)).isoformat(),
                "links": [{"status": 2, "updated": base_date.isoformat()}]
            },
            {
                "id": 2, 
                "status_id": 3,  # Hired (type=hired)
                "created": (base_date - timedelta(days=20)).isoformat(), 
                "links": [{"status": 3, "updated": base_date.isoformat()}]
            },
            {
                "id": 3,
                "status_id": 5,  # Hired (type=hired)
                "created": (base_date - timedelta(days=10)).isoformat(),
                "links": [{"status": 5, "updated": base_date.isoformat()}]
            }
        ]
    engine._get_applicants_data = mock_applicants_time_data
    
    avg_time = await metrics.time_to_hire(days_back=90)
    
    print(f"   Average time to hire: {avg_time:.1f} days")
    print(f"   Expected: ~15 days (average of 20 and 10 days, excluding non-hired)")
    
    # Should average 20 and 10 days = 15 days (excluding the non-hired applicant)
    if 14 <= avg_time <= 16:
        print("   ✅ SUCCESS: Only hired applicants included in calculation")
        return True
    else:
        print("   ❌ FAILURE: Time calculation incorrect")
        return False

async def main():
    print("🔧 Testing Status Type Fix Implementation")
    print("Testing that huntflow_metrics.py now uses robust type field detection")
    print("=" * 70)
    
    test_results = []
    
    test_results.append(await test_hired_status_fix())
    test_results.append(await test_source_effectiveness_fix())
    test_results.append(await test_time_to_hire_fix())
    
    print("\n" + "=" * 70)
    print("📊 Test Results Summary")
    print("-" * 30)
    
    passed = sum(test_results)
    total = len(test_results)
    
    for i, result in enumerate(test_results, 1):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"Test {i}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Status type fix is working correctly.")
        print("\n✨ Key improvements:")
        print("  • Hired status detection now uses robust 'type' field")
        print("  • No more fragile keyword matching for hired statuses")
        print("  • Language-independent detection")
        print("  • Reduced false positives from misleading status names")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Fix needed.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())