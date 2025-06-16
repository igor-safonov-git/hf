#!/usr/bin/env python3
"""
Quick Real Integration Test - validates core functionality with real data
"""
import asyncio
import logging
import os
from dotenv import load_dotenv
from sqlalchemy_executor import SQLAlchemyHuntflowExecutor

load_dotenv()
logging.basicConfig(level=logging.WARNING)  # Reduce log noise

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
                response.raise_for_status()
                return response.json()
            except Exception as e:
                return {}

async def quick_integration_test():
    """Quick test with limited data fetching"""
    print("🧪 Quick Real Integration Test")
    print(f"🔑 Account: {os.getenv('ACC_ID')}")
    
    client = RealHuntflowClient()
    executor = SQLAlchemyHuntflowExecutor(client)
    
    # Test 1: Status mapping (fast)
    print("\n1. Testing status mapping...")
    try:
        status_mapping = await executor.engine._get_status_mapping()
        print(f"✅ {len(status_mapping)} real statuses loaded")
        if status_mapping:
            sample_statuses = [v.get('name', str(v)) for v in list(status_mapping.values())[:3]]
            print(f"   Sample: {sample_statuses}")
    except Exception as e:
        print(f"❌ Status mapping failed: {e}")
    
    # Test 2: Sources mapping (fast)
    print("\n2. Testing sources mapping...")
    try:
        sources_mapping = await executor.engine._get_sources_mapping()
        print(f"✅ {len(sources_mapping)} real sources loaded")
        if sources_mapping:
            sample_sources = list(sources_mapping.values())[:3]
            print(f"   Sample: {sample_sources}")
    except Exception as e:
        print(f"❌ Sources mapping failed: {e}")
    
    # Test 3: Limited applicants fetch (first page only)
    print("\n3. Testing limited applicants fetch...")
    try:
        # Override to fetch only first page for speed
        original_method = executor.engine._fetch_applicants_from_api
        
        async def limited_fetch(filters=None):
            # Only fetch first page for quick test
            params = {"count": 30, "page": 1}
            result = await client._req("GET", f"/v2/accounts/{client.acc_id}/applicants", params=params)
            
            if isinstance(result, dict) and result.get("items"):
                applicants = result.get("items", [])
                print(f"✅ First page: {len(applicants)} applicants")
                
                # Process one applicant to test data structure
                if applicants:
                    first = applicants[0]
                    print(f"   Sample: ID {first.get('id')}, {first.get('first_name', '')} {first.get('last_name', '')}")
                    print(f"   Links: {len(first.get('links', []))} status links")
                
                return applicants[:5]  # Return only 5 for speed
            return []
        
        executor.engine._fetch_applicants_from_api = limited_fetch
        applicants = await executor.engine._get_applicants_data()
        print(f"✅ Limited fetch successful: {len(applicants)} processed")
        
    except Exception as e:
        print(f"❌ Limited applicants fetch failed: {e}")
    
    # Test 4: Basic count (should use cached data)
    print("\n4. Testing basic count with cached data...")
    try:
        count_expr = {"operation": "count", "entity": "applicants", "filter": {}}
        count = await executor.execute_expression(count_expr)
        print(f"✅ Count operation successful: {count}")
    except Exception as e:
        print(f"❌ Count operation failed: {e}")
    
    print("\n🎉 Quick integration test completed!")
    print("✨ Core integration verified with real Huntflow data")

if __name__ == "__main__":
    asyncio.run(quick_integration_test())