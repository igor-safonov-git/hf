#!/usr/bin/env python3
"""
Test the updated ID-based filtering system
"""

import asyncio
from huntflow_local_client import HuntflowLocalClient
from enhanced_metrics_calculator import EnhancedMetricsCalculator

async def main():
    client = HuntflowLocalClient()
    calc = EnhancedMetricsCalculator(client, None)
    
    print("=== TESTING UPDATED ID-BASED FILTERING ===")
    print("Testing with Анастасия Богач ID: 14824")
    
    print("\n1. Test hires filtering by ID:")
    id_hires = await calc.hires({"recruiters": "14824"})
    print(f"   Hires for ID 14824: {len(id_hires)}")
    
    if id_hires:
        print("   ✅ SUCCESS! Sample hire:")
        sample = id_hires[0]
        print(f"     {sample.get('first_name')} {sample.get('last_name')} - {sample.get('hired_date', 'No date')}")
    
    print("\n2. Test applicants filtering by ID:")
    id_applicants = await calc.applicants_all({"recruiters": "14824"})
    print(f"   Applicants for ID 14824: {len(id_applicants)}")
    
    if id_applicants:
        print("   ✅ SUCCESS! Sample applicant:")
        sample = id_applicants[0]
        print(f"     {sample.get('first_name')} {sample.get('last_name')}")
    
    print("\n3. Test vacancies filtering by ID:")
    id_vacancies = await calc.vacancies_all({"recruiters": "14824"})
    print(f"   Vacancies for ID 14824: {len(id_vacancies)}")
    
    if id_vacancies:
        print("   ✅ SUCCESS! Sample vacancy:")
        sample = id_vacancies[0]
        print(f"     {sample.get('position')} - Recruiter ID: {sample.get('recruiter_id')}")
    
    print("\n4. Compare with name-based filtering:")
    name_hires = await calc.hires({"recruiters": "Анастасия Богач"})
    print(f"   Hires by name: {len(name_hires)}")
    print(f"   Hires by ID:   {len(id_hires)}")
    
    if len(id_hires) == len(name_hires):
        print("   ✅ Perfect match! ID filtering works correctly.")
    else:
        print("   ⚠️ Mismatch - need to investigate")

if __name__ == "__main__":
    asyncio.run(main())