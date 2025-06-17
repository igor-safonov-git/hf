#!/usr/bin/env python3
"""
Test the fixed metrics with minimal API calls
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import HuntflowClient
from virtual_engine import HuntflowVirtualEngine
from huntflow_metrics import HuntflowComputedMetrics

async def main():
    """Test fixed metrics"""
    print("=== TESTING FIXED METRICS ===")
    
    hf_client = HuntflowClient()
    engine = HuntflowVirtualEngine(hf_client)
    metrics = HuntflowComputedMetrics(engine)
    
    print("\n1. Testing Time to Fill (fixed):")
    try:
        result = await metrics.time_to_fill()
        print(f"✅ Time to Fill: {result} days")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    print("\n2. Testing Source Effectiveness (fixed):")
    try:
        result = await metrics.source_effectiveness()
        print(f"✅ Source Effectiveness: {len(result)} sources")
        if result:
            print(f"Sample: {result[0]}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    print("\n3. Testing Applicants per Opening:")
    try:
        result = await metrics.applicants_per_opening()
        print(f"✅ Applicants per Opening: {len(result)} vacancies")
        if result:
            print(f"Sample: {result[0]}")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n4. Testing Interview Ratios:")
    try:
        result = await metrics.application_to_interview_ratio()
        print(f"✅ Application-to-Interview: {len(result)} vacancies")
        if result:
            print(f"Sample: {result[0]}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())