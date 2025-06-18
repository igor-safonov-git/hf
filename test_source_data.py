"""
Test if applicants_by_source returns data
"""

import asyncio
from huntflow_local_client import HuntflowLocalClient
from metrics_calculator import MetricsCalculator

async def test_source_data():
    client = HuntflowLocalClient()
    metrics_calc = MetricsCalculator(client)
    
    print("🔍 Testing applicants_by_source data")
    
    try:
        source_data = await metrics_calc.applicants_by_source()
        print(f"Source data: {source_data}")
        print(f"Type: {type(source_data)}")
        print(f"Length: {len(source_data) if source_data else 0}")
        print(f"Keys: {list(source_data.keys()) if source_data else []}")
        print(f"Values: {list(source_data.values()) if source_data else []}")
        
        if source_data:
            print("✅ Has data")
        else:
            print("❌ Empty or None")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_source_data())