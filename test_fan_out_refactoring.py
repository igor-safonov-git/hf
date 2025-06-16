#!/usr/bin/env python3
"""
Test that the fan_out refactoring is working correctly
"""
import asyncio
import logging
from sqlalchemy import select

logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from huntflow_schema import HuntflowVirtualEngine
from app import HuntflowClient


async def test_fan_out_refactoring():
    """Test that refactored methods using fan_out work correctly"""
    print("🧪 Testing fan_out refactoring...")
    
    client = HuntflowClient()
    engine = HuntflowVirtualEngine(client)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: applicant_responses query (should return empty but not crash)
    tests_total += 1
    try:
        query = select(engine.applicant_responses).limit(1)
        result = await engine.execute(query)
        print(f"✅ applicant_responses query works: {len(result)} results")
        tests_passed += 1
    except Exception as e:
        print(f"❌ applicant_responses query failed: {e}")
    
    # Test 2: vacancy_logs query (should return empty but not crash)
    tests_total += 1
    try:
        query = select(engine.vacancy_logs).limit(1)
        result = await engine.execute(query)
        print(f"✅ vacancy_logs query works: {len(result)} results")
        tests_passed += 1
    except Exception as e:
        print(f"❌ vacancy_logs query failed: {e}")
    
    # Test 3: vacancy_periods query (should return empty but not crash)
    tests_total += 1
    try:
        query = select(engine.vacancy_periods).limit(1)
        result = await engine.execute(query)
        print(f"✅ vacancy_periods query works: {len(result)} results")
        tests_passed += 1
    except Exception as e:
        print(f"❌ vacancy_periods query failed: {e}")
    
    # Test 4: vacancy_frames query (should return empty but not crash)
    tests_total += 1
    try:
        query = select(engine.vacancy_frames).limit(1)
        result = await engine.execute(query)
        print(f"✅ vacancy_frames query works: {len(result)} results")
        tests_passed += 1
    except Exception as e:
        print(f"❌ vacancy_frames query failed: {e}")
    
    # Test 5: vacancy_quotas query (should return empty but not crash)
    tests_total += 1
    try:
        query = select(engine.vacancy_quotas).limit(1)
        result = await engine.execute(query)
        print(f"✅ vacancy_quotas query works: {len(result)} results")
        tests_passed += 1
    except Exception as e:
        print(f"❌ vacancy_quotas query failed: {e}")
    
    # Summary
    print(f"\n📊 Fan-out refactoring test results:")
    print(f"✅ Passed: {tests_passed}/{tests_total}")
    print(f"📈 Success rate: {(tests_passed/tests_total*100):.1f}%")
    
    if tests_passed == tests_total:
        print("🎉 All fan_out refactoring tests passed!")
        return True
    else:
        print("⚠️  Some fan_out tests failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_fan_out_refactoring())
    exit(0 if success else 1)