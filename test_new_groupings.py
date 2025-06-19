#!/usr/bin/env python3
"""
Test the newly implemented groupings
"""

import asyncio
from metrics_calculator import MetricsCalculator
from huntflow_local_client import HuntflowLocalClient

async def test_new_groupings():
    client = HuntflowLocalClient()
    calc = MetricsCalculator(client)
    
    print("Testing newly implemented groupings...")
    print("=" * 60)
    
    # Test applicants by division
    print("\n1. APPLICANTS BY DIVISION:")
    result = await calc.applicants_by_division()
    for division, count in result.items():
        print(f"  {division}: {count}")
    
    # Test vacancies groupings
    print("\n2. VACANCIES BY RECRUITER:")
    result = await calc.vacancies_by_recruiter()
    for recruiter, count in list(result.items())[:5]:
        print(f"  {recruiter}: {count}")
    
    print("\n3. VACANCIES BY HIRING MANAGER:")
    result = await calc.vacancies_by_hiring_manager()
    for manager, count in list(result.items())[:5]:
        print(f"  {manager}: {count}")
    
    print("\n4. VACANCIES BY DIVISION:")
    result = await calc.vacancies_by_division()
    for division, count in list(result.items())[:5]:
        print(f"  {division}: {count}")
    
    print("\n5. VACANCIES BY STAGE:")
    result = await calc.vacancies_by_stage()
    for stage, count in result.items():
        print(f"  {stage}: {count}")
    
    # Test hires groupings
    print("\n6. HIRES BY SOURCE:")
    result = await calc.hires_by_source()
    for source, count in result.items():
        print(f"  {source}: {count}")
    
    print("\n7. HIRES BY STAGE:")
    result = await calc.hires_by_stage()
    for stage, count in result.items():
        print(f"  {stage}: {count}")
    
    print("\n8. HIRES BY DIVISION:")
    result = await calc.hires_by_division()
    for division, count in result.items():
        print(f"  {division}: {count}")

if __name__ == "__main__":
    asyncio.run(test_new_groupings())