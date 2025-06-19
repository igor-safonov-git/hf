#!/usr/bin/env python3
"""
Test if the fixed ID (14824) now works for filtering
"""

import asyncio
from huntflow_local_client import HuntflowLocalClient
from enhanced_metrics_calculator import EnhancedMetricsCalculator

async def main():
    client = HuntflowLocalClient()
    calc = EnhancedMetricsCalculator(client, None)
    
    print("=== TESTING FIXED RECRUITER ID FILTERING ===")
    
    print("\n1. Test with OLD (wrong) ID 68691:")
    old_id_hires = await calc.hires({"recruiters": "68691"})
    print(f"   Hires with ID 68691: {len(old_id_hires)}")
    
    print("\n2. Test with NEW (correct) ID 14824:")
    new_id_hires = await calc.hires({"recruiters": "14824"})
    print(f"   Hires with ID 14824: {len(new_id_hires)}")
    
    if new_id_hires:
        print("   ✅ SUCCESS! Found hires for Анастасия Богач")
        print(f"   Sample hire: {new_id_hires[0].get('first_name')} {new_id_hires[0].get('last_name')}")
    else:
        print("   ❌ Still no hires found")
    
    print("\n3. Test applicants with correct ID:")
    new_id_applicants = await calc.applicants_all({"recruiters": "14824"})
    print(f"   Applicants with ID 14824: {len(new_id_applicants)}")
    
    if new_id_applicants:
        print("   ✅ SUCCESS! Found applicants for Анастасия Богач")

if __name__ == "__main__":
    asyncio.run(main())