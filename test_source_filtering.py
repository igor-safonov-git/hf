#!/usr/bin/env python3
"""
Test that source filtering now works correctly for hires
"""

import asyncio
from enhanced_metrics_calculator import EnhancedMetricsCalculator
from huntflow_local_client import HuntflowLocalClient

async def test_source_filtering():
    """Test source filtering for hires"""
    print("=" * 70)
    print("🧪 TESTING SOURCE FILTERING FOR HIRES")
    print("=" * 70)
    
    client = HuntflowLocalClient()
    calc = EnhancedMetricsCalculator(client, None)
    
    # Test 1: Get all hires (baseline)
    print("\n📊 Test 1: All hires (no filter)")
    all_hires = await calc.hires()
    print(f"Total hires: {len(all_hires)}")
    
    # Check how many have source info
    hires_with_source = sum(1 for h in all_hires if h.get('source_id') or h.get('source'))
    print(f"Hires with source info: {hires_with_source}/{len(all_hires)} ({hires_with_source/len(all_hires)*100:.1f}%)")
    
    # Test 2: Get all sources
    print("\n📊 Test 2: Available sources")
    all_sources = await calc.sources_all()
    print(f"Total sources: {len(all_sources)}")
    
    # Show top 5 sources
    print("\nTop sources:")
    for source in all_sources[:5]:
        print(f"  - {source['name']} (ID: {source['id']})")
    
    # Test 3: Filter hires by specific sources
    print("\n📊 Test 3: Hires filtered by source")
    
    # Test with first few sources
    test_sources = all_sources[:3] if len(all_sources) >= 3 else all_sources
    
    for source in test_sources:
        source_id = str(source['id'])
        source_name = source['name']
        
        # Filter hires by this source
        filters = {"sources": source_id}
        filtered_hires = await calc.hires(filters)
        
        print(f"\n  Source: {source_name} (ID: {source_id})")
        print(f"  Hires from this source: {len(filtered_hires)}")
        
        # Verify the filtering is correct
        if filtered_hires:
            # Check first hire has correct source
            first_hire = filtered_hires[0]
            hire_source_id = str(first_hire.get('source_id', ''))
            if hire_source_id == source_id:
                print(f"  ✅ Filter working correctly")
            else:
                print(f"  ❌ Filter mismatch: expected {source_id}, got {hire_source_id}")
    
    # Test 4: Compound filter (source + period)
    print("\n📊 Test 4: Compound filter (source + period)")
    
    if test_sources:
        source = test_sources[0]
        filters = {
            "period": "6 month",
            "sources": str(source['id'])
        }
        filtered_hires = await calc.hires(filters)
        print(f"Hires from {source['name']} in last 6 months: {len(filtered_hires)}")
    
    # Test 5: Cross-entity - recruiters filtered by source
    print("\n📊 Test 5: Cross-entity filtering (recruiters by source)")
    
    if test_sources:
        source = test_sources[0]
        filters = {"sources": str(source['id'])}
        
        # This should return recruiters who have used this source
        filtered_recruiters = await calc.recruiters_all(filters)
        print(f"Recruiters who used {source['name']}: {len(filtered_recruiters)}")
        
        if filtered_recruiters:
            print("First few recruiters:")
            for recruiter in filtered_recruiters[:3]:
                print(f"  - {recruiter.get('name', 'Unknown')}")
    
    print("\n" + "=" * 70)
    print("✅ SOURCE FILTERING TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_source_filtering())