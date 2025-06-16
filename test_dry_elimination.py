#!/usr/bin/env python3
"""
Test that DRY violation elimination is working correctly
Tests both _collect_ids helper and enhanced fan_out with extra_filters
"""
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from virtual_engine import HuntflowVirtualEngine
from app import HuntflowClient


async def test_dry_elimination():
    """Test DRY violation elimination helpers"""
    print("🧪 Testing DRY elimination helpers...")
    
    client = HuntflowClient()
    engine = HuntflowVirtualEngine(client)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: _collect_ids helper with single ID
    tests_total += 1
    try:
        sql_filters = {'vacancy_id': 123}
        ids = engine._collect_ids(sql_filters, 'vacancy_id')
        if ids == [123]:
            print(f"✅ _collect_ids single ID works: {ids}")
            tests_passed += 1
        else:
            print(f"❌ _collect_ids single ID failed: expected [123], got {ids}")
    except Exception as e:
        print(f"❌ _collect_ids single ID failed: {e}")
    
    # Test 2: _collect_ids helper with multiple IDs
    tests_total += 1
    try:
        sql_filters = {'vacancy_ids': [1, 2, 3]}
        ids = engine._collect_ids(sql_filters, 'vacancy_id')
        if ids == [1, 2, 3]:
            print(f"✅ _collect_ids multiple IDs works: {ids}")
            tests_passed += 1
        else:
            print(f"❌ _collect_ids multiple IDs failed: expected [1, 2, 3], got {ids}")
    except Exception as e:
        print(f"❌ _collect_ids multiple IDs failed: {e}")
    
    # Test 3: _collect_ids helper with no IDs
    tests_total += 1
    try:
        sql_filters = {}
        ids = engine._collect_ids(sql_filters, 'vacancy_id')
        if ids == []:
            print(f"✅ _collect_ids no IDs works: {ids}")
            tests_passed += 1
        else:
            print(f"❌ _collect_ids no IDs failed: expected [], got {ids}")
    except Exception as e:
        print(f"❌ _collect_ids no IDs failed: {e}")
    
    # Test 4: fan_out with extra_filters
    tests_total += 1
    try:
        test_ids = [1, 2]
        extra_filters = {'date_begin': '2024-01-01', 'date_end': '2024-12-31'}
        
        async def mock_fetch_with_dates(entity_id, date_begin=None, date_end=None):
            return {
                'id': entity_id, 
                'data': f'test_{entity_id}', 
                'date_begin': date_begin, 
                'date_end': date_end
            }
        
        results = await engine.fan_out(
            ids=test_ids,
            fetch_fn=mock_fetch_with_dates,
            cache_key='test_extra_filters',
            extra_filters=extra_filters
        )
        
        if len(results) == 2 and results[0]['date_begin'] == '2024-01-01':
            print(f"✅ fan_out with extra_filters works: {len(results)} results with dates")
            tests_passed += 1
        else:
            print(f"❌ fan_out with extra_filters failed: {results}")
    except Exception as e:
        print(f"❌ fan_out with extra_filters failed: {e}")
    
    # Test 5: fan_out with mapper function
    tests_total += 1
    try:
        test_ids = [1, 2]
        
        async def mock_fetch(entity_id):
            return {'raw_id': entity_id, 'raw_data': f'raw_{entity_id}'}
        
        def transform_mapper(item):
            return {
                'id': item['raw_id'],
                'transformed_data': item['raw_data'].upper()
            }
        
        results = await engine.fan_out(
            ids=test_ids,
            fetch_fn=mock_fetch,
            mapper=transform_mapper
        )
        
        if len(results) == 2 and results[0]['transformed_data'] == 'RAW_1':
            print(f"✅ fan_out with mapper works: {results}")
            tests_passed += 1
        else:
            print(f"❌ fan_out with mapper failed: {results}")
    except Exception as e:
        print(f"❌ fan_out with mapper failed: {e}")
    
    # Summary
    print(f"\n📊 DRY elimination test results:")
    print(f"✅ Passed: {tests_passed}/{tests_total}")
    print(f"📈 Success rate: {(tests_passed/tests_total*100):.1f}%")
    
    if tests_passed == tests_total:
        print("🎉 All DRY elimination tests passed!")
        print("✅ _collect_ids helper eliminates ID extraction boilerplate")
        print("✅ enhanced fan_out supports extra_filters and mappers")
        return True
    else:
        print("⚠️  Some DRY elimination tests failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_dry_elimination())
    exit(0 if success else 1)