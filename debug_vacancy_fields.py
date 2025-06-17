#!/usr/bin/env python3
"""
Debug vacancy fields to understand available date fields
"""

import asyncio
import sys
import os
import json

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import HuntflowClient

async def main():
    """Check all fields in vacancies"""
    print("=== VACANCY FIELDS DEBUGGING ===")
    
    hf_client = HuntflowClient()
    
    # Get a larger sample of vacancies
    try:
        vacancies_result = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/vacancies", params={"count": 50, "page": 1})
        vacancies = vacancies_result.get("items", [])
        
        print(f"Total vacancies: {len(vacancies)}")
        
        # Find closed vacancies
        closed_vacancies = [v for v in vacancies if v.get('state') == 'CLOSED']
        open_vacancies = [v for v in vacancies if v.get('state') == 'OPEN']
        
        print(f"Closed vacancies: {len(closed_vacancies)}")
        print(f"Open vacancies: {len(open_vacancies)}")
        
        if closed_vacancies:
            print("\n=== CLOSED VACANCY FIELDS ===")
            sample_closed = closed_vacancies[0]
            print("All fields in closed vacancy:")
            for key, value in sample_closed.items():
                print(f"  {key}: {value}")
        
        if open_vacancies:
            print("\n=== OPEN VACANCY FIELDS ===")
            sample_open = open_vacancies[0]
            print("All fields in open vacancy:")
            for key, value in sample_open.items():
                print(f"  {key}: {value}")
        
        # Check if any closed vacancies have useful date fields
        print("\n=== DATE FIELD ANALYSIS ===")
        for i, vacancy in enumerate(closed_vacancies):
            print(f"Closed vacancy {i+1}:")
            print(f"  created: {vacancy.get('created')}")
            print(f"  updated: {vacancy.get('updated')}")
            print(f"  changed: {vacancy.get('changed')}")
            print(f"  state: {vacancy.get('state')}")
            
            # Look for other potential date fields
            for key, value in vacancy.items():
                if isinstance(value, str) and ('202' in str(value) or 'T' in str(value)):
                    if key not in ['created', 'updated', 'changed']:
                        print(f"  Other date field {key}: {value}")
            print()
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())