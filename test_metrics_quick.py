"""
Quick integration test for metrics.py with limited API calls
Tests key functionality without exhaustive API calls
"""

import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import MetaData
from metrics import HuntflowViews
from schema import create_huntflow_tables
from virtual_engine import HuntflowVirtualEngine
from app import HuntflowClient
from async_engine_adapter import AsyncEngineAdapter

load_dotenv()


async def test_key_metrics():
    """Run quick integration tests for key metrics functions"""
    # Setup
    hf_token = os.getenv("HF_TOKEN")
    acc_id = os.getenv("ACC_ID")
    
    if not hf_token or not acc_id:
        print("❌ HF_TOKEN or ACC_ID not found in environment")
        return
    
    print("🔧 Setting up test environment...")
    
    # Create components
    hf_client = HuntflowClient()
    virtual_engine = HuntflowVirtualEngine(hf_client)
    engine = AsyncEngineAdapter(virtual_engine)
    metadata = MetaData()
    tables = create_huntflow_tables(metadata)
    views = HuntflowViews(engine, tables)
    
    print("\n📊 Running quick integration tests...")
    
    results = {
        "passed": 0,
        "failed": 0,
        "errors": []
    }
    
    # Test 1: vacancies_by_state with OPEN
    print("\n1. Testing vacancies_by_state('OPEN')...")
    try:
        open_vacancies = await views.vacancies_by_state('OPEN')
        print(f"   ✅ Found {len(open_vacancies)} OPEN vacancies")
        if open_vacancies:
            print(f"   Sample: {open_vacancies[0].get('position', 'N/A')}")
        results["passed"] += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results["failed"] += 1
        results["errors"].append(f"vacancies_by_state: {str(e)}")
    
    # Test 2: Invalid state should raise ValueError
    print("\n2. Testing vacancies_by_state with invalid state...")
    try:
        await views.vacancies_by_state('INVALID_STATE')
        print("   ❌ Should have raised ValueError")
        results["failed"] += 1
    except ValueError:
        print("   ✅ Correctly raised ValueError")
        results["passed"] += 1
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        results["failed"] += 1
    
    # Test 3: vacancies_by_date_range
    print("\n3. Testing vacancies_by_date_range...")
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        recent_vacancies = await views.vacancies_by_date_range(start_date, end_date)
        print(f"   ✅ Found {len(recent_vacancies)} vacancies in last 7 days")
        results["passed"] += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results["failed"] += 1
        results["errors"].append(f"vacancies_by_date_range: {str(e)}")
    
    # Test 4: Invalid date range
    print("\n4. Testing invalid date range...")
    try:
        await views.vacancies_by_date_range(datetime.now(), datetime.now() - timedelta(days=1))
        print("   ❌ Should have raised ValueError")
        results["failed"] += 1
    except ValueError:
        print("   ✅ Correctly raised ValueError")
        results["passed"] += 1
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        results["failed"] += 1
    
    # Test 5: applicants_by_source with invalid ID
    print("\n5. Testing applicants_by_source with invalid ID...")
    try:
        await views.applicants_by_source(-1)
        print("   ❌ Should have raised ValueError")
        results["failed"] += 1
    except ValueError:
        print("   ✅ Correctly raised ValueError")
        results["passed"] += 1
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        results["failed"] += 1
    
    # Test 6: offers_by_status with empty string
    print("\n6. Testing offers_by_status with empty string...")
    try:
        await views.offers_by_status("")
        print("   ❌ Should have raised ValueError")
        results["failed"] += 1
    except ValueError:
        print("   ✅ Correctly raised ValueError")
        results["passed"] += 1
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        results["failed"] += 1
    
    # Test 7: sources_by_type
    print("\n7. Testing sources_by_type...")
    try:
        user_sources = await views.sources_by_type('user')
        print(f"   ✅ Found {len(user_sources)} user sources")
        results["passed"] += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results["failed"] += 1
        results["errors"].append(f"sources_by_type: {str(e)}")
    
    # Test 8: rejections_by_reason (should raise NotImplementedError)
    print("\n8. Testing rejections_by_reason...")
    try:
        await views.rejections_by_reason(1)
        print("   ❌ Should have raised NotImplementedError")
        results["failed"] += 1
    except NotImplementedError:
        print("   ✅ Correctly raised NotImplementedError")
        results["passed"] += 1
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        results["failed"] += 1
    
    # Test 9: vacancy_funnel with invalid ID
    print("\n9. Testing vacancy_funnel with invalid ID...")
    try:
        await views.vacancy_funnel(0)
        print("   ❌ Should have raised ValueError")
        results["failed"] += 1
    except ValueError:
        print("   ✅ Correctly raised ValueError")
        results["passed"] += 1
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        results["failed"] += 1
    
    # Test 10: recruiter_performance with future date
    print("\n10. Testing recruiter_performance with future date...")
    try:
        future_date = datetime.now() + timedelta(days=30)
        await views.recruiter_performance(start_date=future_date)
        print("   ❌ Should have raised ValueError")
        results["failed"] += 1
    except ValueError:
        print("   ✅ Correctly raised ValueError")
        results["passed"] += 1
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        results["failed"] += 1
    
    # Summary
    print(f"\n📊 Test Summary:")
    print(f"   ✅ Passed: {results['passed']}")
    print(f"   ❌ Failed: {results['failed']}")
    
    if results["errors"]:
        print(f"\n⚠️  Errors encountered:")
        for error in results["errors"]:
            print(f"   - {error}")
    
    if results["failed"] == 0:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {results['failed']} tests failed")
    
    return results


if __name__ == "__main__":
    asyncio.run(test_key_metrics())