#!/usr/bin/env python3
"""
Debug Status Groups API Response
Let's see what the status groups endpoint actually returns
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

class RealHuntflowClient:
    def __init__(self):
        self.token = os.getenv("HF_TOKEN", "")
        self.acc_id = os.getenv("ACC_ID", "")
        self.base_url = "https://api.huntflow.ru"
    
    async def _req(self, method: str, path: str, **kwargs):
        import httpx
        headers = {"Authorization": f"Bearer {self.token}"}
        url = f"{self.base_url}{path}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(method, url, headers=headers, **kwargs)
                print(f"API Response Status: {response.status_code}")
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"API call failed: {e}")
                return {}

async def debug_status_groups():
    """Debug what the status groups API actually returns"""
    print("🔍 Debugging Status Groups API")
    print("=" * 50)
    
    client = RealHuntflowClient()
    
    # Test the status groups endpoint
    print("1. Testing /vacancies/status_groups endpoint...")
    try:
        status_groups_result = await client._req(
            "GET",
            f"/v2/accounts/{client.acc_id}/vacancies/status_groups"
        )
        
        print(f"Response type: {type(status_groups_result)}")
        print(f"Response: {status_groups_result}")
        
        if isinstance(status_groups_result, dict):
            print(f"Keys: {list(status_groups_result.keys())}")
            
            if "items" in status_groups_result:
                items = status_groups_result["items"]
                print(f"Items count: {len(items)}")
                for i, group in enumerate(items):
                    print(f"  Group {i+1}: {group}")
            else:
                print("No 'items' key found")
        
    except Exception as e:
        print(f"Status groups API call failed: {e}")
    
    # Also test the regular statuses to see if they have group_id fields
    print(f"\n2. Checking if statuses have group_id fields...")
    try:
        statuses_result = await client._req(
            "GET",
            f"/v2/accounts/{client.acc_id}/vacancies/statuses"
        )
        
        if isinstance(statuses_result, dict) and "items" in statuses_result:
            statuses = statuses_result["items"]
            print(f"Checking {len(statuses)} statuses for group_id field...")
            
            group_ids_found = []
            for status in statuses[:5]:  # Check first 5
                print(f"  Status: {status}")
                if "group_id" in status:
                    group_ids_found.append(status["group_id"])
                elif "status_group_id" in status:
                    group_ids_found.append(status["status_group_id"])
            
            print(f"Group IDs found: {group_ids_found}")
    
    except Exception as e:
        print(f"Statuses API call failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_status_groups())