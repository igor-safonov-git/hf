#!/usr/bin/env python3
"""
Test filtering by name vs ID to understand the expected format
"""

import asyncio
from huntflow_local_client import HuntflowLocalClient
from enhanced_metrics_calculator import EnhancedMetricsCalculator

async def main():
    client = HuntflowLocalClient()
    calc = EnhancedMetricsCalculator(client, None)
    
    print("=== TESTING NAME VS ID FILTERING ===")
    
    print("\n1. Test filtering by NAME:")
    name_hires = await calc.hires({"recruiters": "Анастасия Богач"})
    print(f"   Hires filtered by name 'Анастасия Богач': {len(name_hires)}")
    
    print("\n2. Test filtering by ID (current approach):")
    id_hires = await calc.hires({"recruiters": "14824"})
    print(f"   Hires filtered by ID '14824': {len(id_hires)}")
    
    print("\n3. Check what the enhanced metrics calculator expects:")
    print("   Looking at the code:")
    print("   Line 372-373: log.get('account_info', {}).get('name') == recruiter_name")
    print("   ↳ This expects a NAME, not an ID!")
    
    print("\n4. Test applicants by name:")
    name_applicants = await calc.applicants_all({"recruiters": "Анастасия Богач"})
    print(f"   Applicants filtered by name: {len(name_applicants)}")

if __name__ == "__main__":
    asyncio.run(main())