#!/usr/bin/env python3
"""
Debug a single applicant to see link structure
"""
import asyncio
import os
import json
from app import HuntflowClient
from virtual_engine import HuntflowVirtualEngine

async def debug_single_applicant():
    """Debug a single applicant's links structure"""
    
    # Initialize client and engine
    hf_client = HuntflowClient()
    
    if not hf_client.token or not hf_client.acc_id:
        print("❌ Missing HF_TOKEN or ACC_ID environment variables")
        return
    
    engine = HuntflowVirtualEngine(hf_client)
    
    print("👥 Getting first few applicants...")
    applicants_data = await engine._get_applicants_data()
    
    if not applicants_data:
        print("❌ No applicants found")
        return
    
    print(f"Found {len(applicants_data)} total applicants")
    
    # Examine the first few applicants
    for i, applicant in enumerate(applicants_data[:5]):
        print(f"\n🔍 Applicant {i+1}: ID {applicant.get('id')}")
        
        # Check if this applicant has links
        links = applicant.get('links', [])
        print(f"   Links array length: {len(links)}")
        
        if links:
            print(f"   First link structure:")
            first_link = links[0]
            print(f"     Full link: {json.dumps(first_link, indent=4)}")
            
            # Check for both field name variations
            status_field = first_link.get('status')
            status_id_field = first_link.get('status_id')
            vacancy_field = first_link.get('vacancy')
            vacancy_id_field = first_link.get('vacancy_id')
            
            print(f"     status: {status_field}")
            print(f"     status_id: {status_id_field}")
            print(f"     vacancy: {vacancy_field}")
            print(f"     vacancy_id: {vacancy_id_field}")
        else:
            print(f"   No links found for this applicant")
            
    # Check if there are any applicants with non-empty links
    applicants_with_links = 0
    total_links = 0
    for applicant in applicants_data:
        links = applicant.get('links', [])
        if links:
            applicants_with_links += 1
            total_links += len(links)
    
    print(f"\n📊 SUMMARY:")
    print(f"   Total applicants: {len(applicants_data)}")
    print(f"   Applicants with links: {applicants_with_links}")
    print(f"   Total links across all applicants: {total_links}")

if __name__ == "__main__":
    asyncio.run(debug_single_applicant())