#!/usr/bin/env python3
"""
Debug script to compare API endpoints for applicant fetching
"""
import asyncio
import os
import json
from app import HuntflowClient

async def compare_applicant_endpoints():
    """Compare /applicants vs /applicants/search vs individual applicant calls"""
    
    # Initialize client
    hf_token = os.getenv('HF_TOKEN')
    acc_id = os.getenv('ACC_ID')
    
    if not hf_token or not acc_id:
        print("❌ Missing HF_TOKEN or ACC_ID environment variables")
        return
    
    hf_client = HuntflowClient()
    
    print("🔍 Testing different applicant endpoints...")
    print("=" * 60)
    
    # 1. Test /applicants endpoint (bulk)
    print("\n1️⃣ Testing /applicants endpoint (bulk query):")
    print("-" * 40)
    
    params = {"count": 5, "page": 1}  # Small sample
    bulk_result = await hf_client._req("GET", f"/v2/accounts/{acc_id}/applicants", params=params)
    
    if isinstance(bulk_result, dict) and bulk_result.get("items"):
        bulk_applicants = bulk_result.get("items", [])
        print(f"✅ Retrieved {len(bulk_applicants)} applicants from /applicants")
        
        first_bulk = bulk_applicants[0]
        print(f"📝 First bulk applicant structure:")
        print(f"   - ID: {first_bulk.get('id')}")
        print(f"   - Name: {first_bulk.get('first_name')} {first_bulk.get('last_name')}")
        print(f"   - Has 'links' field: {'links' in first_bulk}")
        
        if 'links' in first_bulk:
            links = first_bulk.get('links', [])
            print(f"   - Links array length: {len(links)}")
            if links:
                print(f"   - First link structure: {json.dumps(links[0], indent=6)}")
        else:
            print(f"   - ❌ No 'links' field in bulk response")
    else:
        print("❌ No data from /applicants endpoint")
        return
    
    # 2. Test /applicants/search endpoint
    print("\n2️⃣ Testing /applicants/search endpoint:")
    print("-" * 40)
    
    search_params = {"count": 5, "page": 1}
    search_result = await hf_client._req("GET", f"/v2/accounts/{acc_id}/applicants/search", params=search_params)
    
    if isinstance(search_result, dict) and search_result.get("items"):
        search_applicants = search_result.get("items", [])
        print(f"✅ Retrieved {len(search_applicants)} applicants from /applicants/search")
        
        first_search = search_applicants[0]
        print(f"📝 First search applicant structure:")
        print(f"   - ID: {first_search.get('id')}")
        print(f"   - Name: {first_search.get('first_name')} {first_search.get('last_name')}")
        print(f"   - Has 'links' field: {'links' in first_search}")
        
        if 'links' in first_search:
            links = first_search.get('links', [])
            print(f"   - Links array length: {len(links)}")
            if links:
                print(f"   - First link structure: {json.dumps(links[0], indent=6)}")
        else:
            print(f"   - ❌ No 'links' field in search response")
    else:
        print("❌ No data from /applicants/search endpoint")
    
    # 3. Test individual applicant call
    print("\n3️⃣ Testing individual applicant call:")
    print("-" * 40)
    
    # Use first applicant ID from bulk result
    if bulk_applicants:
        test_id = first_bulk.get('id')
        individual_result = await hf_client._req("GET", f"/v2/accounts/{acc_id}/applicants/{test_id}")
        
        if isinstance(individual_result, dict):
            print(f"✅ Retrieved individual applicant {test_id}")
            print(f"📝 Individual applicant structure:")
            print(f"   - ID: {individual_result.get('id')}")
            print(f"   - Name: {individual_result.get('first_name')} {individual_result.get('last_name')}")
            print(f"   - Has 'links' field: {'links' in individual_result}")
            
            if 'links' in individual_result:
                links = individual_result.get('links', [])
                print(f"   - Links array length: {len(links)}")
                if links:
                    print(f"   - First link structure: {json.dumps(links[0], indent=6)}")
            else:
                print(f"   - ❌ No 'links' field in individual response")
        else:
            print("❌ No data from individual applicant call")
    
    # 4. Compare data structures
    print("\n4️⃣ Summary & Recommendations:")
    print("-" * 40)
    
    bulk_has_links = 'links' in first_bulk if bulk_applicants else False
    search_has_links = 'links' in first_search if 'first_search' in locals() else False
    individual_has_links = 'links' in individual_result if 'individual_result' in locals() else False
    
    print(f"📊 Links field availability:")
    print(f"   - /applicants (bulk): {'✅' if bulk_has_links else '❌'}")
    print(f"   - /applicants/search: {'✅' if search_has_links else '❌'}")
    print(f"   - /applicants/{{id}} (individual): {'✅' if individual_has_links else '❌'}")
    
    if not bulk_has_links and individual_has_links:
        print(f"\n💡 RECOMMENDATION:")
        print(f"   The current code uses /applicants (bulk) but this endpoint doesn't include")
        print(f"   the 'links' array needed for status/vacancy information.")
        print(f"   Consider switching to /applicants/search or individual calls.")
    
    # 5. Test parameters that might include links
    print("\n5️⃣ Testing /applicants with different parameters:")
    print("-" * 40)
    
    # Check if there are parameters that might include links data
    test_params = [
        {"count": 5, "page": 1},
        {"count": 5, "page": 1, "status": 1},  # Try with status filter
        {"count": 5, "page": 1, "vacancy": 1}, # Try with vacancy filter
    ]
    
    for i, params in enumerate(test_params):
        print(f"   Test {i+1} - params: {params}")
        result = await hf_client._req("GET", f"/v2/accounts/{acc_id}/applicants", params=params)
        
        if isinstance(result, dict) and result.get("items"):
            items = result.get("items", [])
            if items:
                has_links = 'links' in items[0]
                print(f"      - Has links: {'✅' if has_links else '❌'}")
                if has_links and items[0].get('links'):
                    print(f"      - Links count: {len(items[0].get('links', []))}")
            else:
                print(f"      - No items returned")
        else:
            print(f"      - Request failed or no data")

if __name__ == "__main__":
    asyncio.run(compare_applicant_endpoints())