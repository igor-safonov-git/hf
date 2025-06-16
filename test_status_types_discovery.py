#!/usr/bin/env python3
"""
Discover actual Huntflow status types from real API
This will help us understand what the real system-level status types are
"""
import asyncio
import logging
import os
from dotenv import load_dotenv
from sqlalchemy_executor import SQLAlchemyHuntflowExecutor

load_dotenv()
logging.basicConfig(level=logging.INFO)

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
                print(f"API call failed: {e}")
                return {}

async def discover_status_types():
    """Discover what status types actually exist in a real Huntflow account"""
    print("🔍 Discovering Real Huntflow Status Types")
    print("=" * 50)
    
    if not os.getenv("HF_TOKEN") or not os.getenv("ACC_ID"):
        print("❌ Missing HF_TOKEN or ACC_ID environment variables")
        print("This test requires real Huntflow API access to discover status types")
        return False
    
    client = RealHuntflowClient()
    executor = SQLAlchemyHuntflowExecutor(client)
    
    try:
        # Get status mapping with full details
        print("📊 Fetching status mapping from real API...")
        status_mapping = await executor.engine._get_status_mapping()
        
        if not status_mapping:
            print("❌ No status data retrieved")
            return False
        
        print(f"✅ Found {len(status_mapping)} statuses")
        
        # Analyze status types
        status_types = {}
        print(f"\n📋 Status Type Analysis:")
        print("-" * 60)
        
        for status_id, status_info in status_mapping.items():
            if isinstance(status_info, dict):
                status_type = status_info.get("type", "unknown")
                status_name = status_info.get("name", f"Status {status_id}")
                
                if status_type not in status_types:
                    status_types[status_type] = []
                status_types[status_type].append((status_id, status_name))
                
                print(f"ID {status_id:3d} | Type: {status_type:12s} | Name: {status_name}")
        
        print(f"\n🎯 Status Type Summary:")
        print("-" * 40)
        for status_type, statuses in status_types.items():
            print(f"Type '{status_type}': {len(statuses)} statuses")
            for status_id, status_name in statuses[:3]:  # Show first 3 examples
                print(f"  └─ {status_name}")
            if len(statuses) > 3:
                print(f"  └─ ... and {len(statuses) - 3} more")
        
        # Check if there's a hired type
        if "hired" in status_types:
            print(f"\n✅ CONFIRMED: 'hired' status type exists!")
            print(f"   Hired statuses: {[name for _, name in status_types['hired']]}")
        else:
            print(f"\n⚠️ No 'hired' status type found")
            print(f"   Available types: {list(status_types.keys())}")
            
            # Look for other potential hired indicators
            potential_hired = []
            for status_type, statuses in status_types.items():
                if any(keyword in status_type.lower() for keyword in ['success', 'final', 'complete', 'accept']):
                    potential_hired.extend(statuses)
            
            if potential_hired:
                print(f"   Potential hired statuses by type: {[name for _, name in potential_hired]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Status type discovery failed: {e}")
        return False

async def test_robust_detection():
    """Test the robust hired status detection"""
    print(f"\n🧪 Testing Robust Hired Status Detection")
    print("=" * 50)
    
    client = RealHuntflowClient()
    
    # Test with different configurations
    configs = [
        {"method": "system_types", "system_types": ["hired"]},
        {"method": "system_types", "system_types": ["hired", "successful", "final"]}, 
        {"method": "auto_detect"},
        {"method": "status_groups"}
    ]
    
    for i, config in enumerate(configs, 1):
        print(f"\n{i}. Testing config: {config}")
        executor = SQLAlchemyHuntflowExecutor(client, hired_status_config=config)
        
        try:
            hired_status_ids = await executor.get_hired_status_ids()
            print(f"   ✅ Found {len(hired_status_ids)} hired status IDs: {hired_status_ids}")
            
            if hired_status_ids:
                # Get names for these IDs
                status_mapping = await executor.engine._get_status_mapping()
                names = []
                for status_id in hired_status_ids:
                    if status_id in status_mapping:
                        status_info = status_mapping[status_id]
                        if isinstance(status_info, dict):
                            names.append(status_info.get("name", f"Status {status_id}"))
                print(f"   Status names: {names}")
            
        except Exception as e:
            print(f"   ❌ Config failed: {e}")

if __name__ == "__main__":
    async def main():
        await discover_status_types()
        await test_robust_detection()
        
        print("\n" + "=" * 50) 
        print("🎉 Status Type Discovery Complete!")
        print("\n💡 Recommendations:")
        print("  • Use system-level 'type' field for most reliable detection")
        print("  • Configure explicit status IDs for production systems")
        print("  • No fragile string matching - only robust API-based detection")
    
    asyncio.run(main())