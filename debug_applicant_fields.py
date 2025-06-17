#!/usr/bin/env python3
"""
Debug applicant fields to understand source data structure
"""

import asyncio
import sys
import os
import json

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import HuntflowClient

async def main():
    """Check applicant fields to understand source data"""
    print("=== APPLICANT FIELDS DEBUGGING ===")
    
    hf_client = HuntflowClient()
    
    try:
        applicants_result = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/applicants", params={"count": 10})
        applicants = applicants_result.get("items", [])
        
        print(f"Total applicants: {len(applicants)}")
        
        if applicants:
            print("\n=== APPLICANT FIELDS ===")
            sample = applicants[0]
            print("All fields in sample applicant:")
            for key, value in sample.items():
                print(f"  {key}: {value}")
            
            print("\n=== SOURCE DATA ANALYSIS ===")
            for i, applicant in enumerate(applicants):
                print(f"Applicant {i+1} (ID: {applicant.get('id')}):")
                print(f"  source_id: {applicant.get('source_id')}")
                print(f"  source: {applicant.get('source')}")
                print(f"  account_source: {applicant.get('account_source')}")
                
                # Check if there's source info in links or elsewhere
                links = applicant.get('links', [])
                if links:
                    print(f"  links: {len(links)} links")
                    for j, link in enumerate(links):
                        print(f"    Link {j+1}: vacancy={link.get('vacancy')}, status={link.get('status')}")
                print()
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())