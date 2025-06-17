#!/usr/bin/env python3
"""
Test a single metric with the fixes
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import HuntflowClient

async def test_source_effectiveness_directly():
    """Test source effectiveness directly with API calls"""
    print("=== TESTING SOURCE EFFECTIVENESS DIRECTLY ===")
    
    hf_client = HuntflowClient()
    
    # 1. Get a small sample of applicants
    print("1. Getting applicants...")
    try:
        applicants_result = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/applicants", params={"count": 10})
        applicants = applicants_result.get("items", [])
        print(f"✅ Got {len(applicants)} applicants")
    except Exception as e:
        print(f"❌ Error: {e}")
        return

    # 2. Get status mapping
    print("2. Getting status mapping...")
    try:
        statuses_result = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/vacancies/statuses")
        statuses = statuses_result.get("items", [])
        print(f"✅ Got {len(statuses)} statuses")
        
        # Find hired status IDs
        hired_status_ids = set()
        for status in statuses:
            if status.get('type', '').lower() == 'hired':
                hired_status_ids.add(status.get('id'))
        print(f"✅ Found {len(hired_status_ids)} hired statuses: {hired_status_ids}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return

    # 3. Get sources mapping
    print("3. Getting sources...")
    try:
        sources_result = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/applicants/sources")
        sources = sources_result.get("items", [])
        sources_mapping = {s.get('id'): s.get('name') for s in sources}
        print(f"✅ Got {len(sources)} sources")
    except Exception as e:
        print(f"❌ Error: {e}")
        return

    # 4. Analyze source effectiveness
    print("4. Analyzing source effectiveness...")
    
    source_stats = {}
    
    for applicant in applicants:
        # Extract source_id from external array (fixed approach)
        source_id = None
        external_array = applicant.get('external', [])
        if external_array and isinstance(external_array, list):
            for external in external_array:
                if external.get('account_source'):
                    source_id = external.get('account_source')
                    break
        
        # Get current status from links
        status_id = None
        links = applicant.get('links', [])
        if links:
            status_id = links[0].get('status')
        
        print(f"  Applicant {applicant.get('id')}: source_id={source_id}, status_id={status_id}")
        
        if not source_id or source_id not in sources_mapping:
            print(f"    -> Skipping (no valid source)")
            continue
        
        source_name = sources_mapping[source_id]
        
        if source_name not in source_stats:
            source_stats[source_name] = {'total_applicants': 0, 'hires': 0}
        
        source_stats[source_name]['total_applicants'] += 1
        
        if status_id in hired_status_ids:
            source_stats[source_name]['hires'] += 1
            print(f"    -> {source_name}: HIRED!")
        else:
            print(f"    -> {source_name}: not hired")
    
    # 5. Calculate results
    print("5. Results:")
    if source_stats:
        for source_name, stats in source_stats.items():
            conversion_rate = stats['hires'] / stats['total_applicants'] if stats['total_applicants'] > 0 else 0
            print(f"  {source_name}: {stats['hires']}/{stats['total_applicants']} = {conversion_rate:.2%}")
        print(f"✅ SUCCESS: {len(source_stats)} sources have conversion data")
    else:
        print("❌ NO SOURCE DATA FOUND")

if __name__ == "__main__":
    asyncio.run(test_source_effectiveness_directly())