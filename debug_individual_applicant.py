#!/usr/bin/env python3
"""
Debug an individual applicant to compare with bulk data
"""
import asyncio
import os
import json
from app import HuntflowClient

async def debug_individual_applicant():
    """Debug an individual applicant vs bulk data"""
    
    # Initialize client
    hf_client = HuntflowClient()
    
    if not hf_client.token or not hf_client.acc_id:
        print("❌ Missing HF_TOKEN or ACC_ID environment variables")
        return
    
    # Get a specific applicant ID from bulk query
    bulk_result = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/applicants", params={"count": 5})
    bulk_applicants = bulk_result.get('items', [])
    
    if not bulk_applicants:
        print("❌ No applicants found in bulk query")
        return
    
    applicant_id = bulk_applicants[0]['id']
    print(f"🔍 Testing applicant ID: {applicant_id}")
    
    # Get bulk data for this applicant
    bulk_applicant = bulk_applicants[0]
    print(f"\n📋 BULK QUERY DATA:")
    print(f"   links array: {bulk_applicant.get('links', [])}")
    print(f"   keys in applicant: {list(bulk_applicant.keys())}")
    
    # Get individual applicant data
    individual_result = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/applicants/{applicant_id}")
    
    print(f"\n👤 INDIVIDUAL QUERY DATA:")
    print(f"   links array: {individual_result.get('links', [])}")
    print(f"   keys in applicant: {list(individual_result.keys())}")
    
    # Compare the structures
    if individual_result.get('links'):
        print(f"\n🔗 INDIVIDUAL APPLICANT HAS LINKS:")
        for i, link in enumerate(individual_result['links'][:3]):  # Show first 3
            print(f"   Link {i+1}: {json.dumps(link, indent=6)}")
    else:
        print(f"\n❌ Individual applicant also has no links")
    
    # Check if it's a parameter issue - try with different parameters
    print(f"\n🧪 TESTING WITH PARAMETERS:")
    
    # Try with 'with_links' parameter
    bulk_with_links = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/applicants", 
                                          params={"count": 1, "with_links": True})
    if bulk_with_links.get('items'):
        print(f"   with_links=True: {len(bulk_with_links['items'][0].get('links', []))} links")
    
    # Try with 'expand' parameter  
    bulk_expanded = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/applicants", 
                                       params={"count": 1, "expand": "links"})
    if bulk_expanded.get('items'):
        print(f"   expand=links: {len(bulk_expanded['items'][0].get('links', []))} links")
    
    # Try with 'include' parameter
    bulk_include = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/applicants", 
                                      params={"count": 1, "include": "links"})
    if bulk_include.get('items'):
        print(f"   include=links: {len(bulk_include['items'][0].get('links', []))} links")

if __name__ == "__main__":
    asyncio.run(debug_individual_applicant())