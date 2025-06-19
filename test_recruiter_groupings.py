#!/usr/bin/env python3
"""
Test the final recruiter groupings (by vacancies, applicants, divisions)
"""

import asyncio
from metrics_calculator import MetricsCalculator
from huntflow_local_client import HuntflowLocalClient
from chart_data_processor import process_chart_data

async def test_recruiter_groupings():
    client = HuntflowLocalClient()
    calc = MetricsCalculator(client)
    
    print("Testing recruiter groupings...")
    print("=" * 60)
    
    # Test direct methods first
    print("\n1. DIRECT METHOD TESTS:")
    
    print("\n  Recruiters by Vacancies:")
    result = await calc.recruiters_by_vacancies()
    for group, count in result.items():
        print(f"    {group}: {count} recruiters")
    
    print("\n  Recruiters by Applicants:")
    result = await calc.recruiters_by_applicants()
    for group, count in result.items():
        print(f"    {group}: {count} recruiters")
    
    print("\n  Recruiters by Divisions:")
    result = await calc.recruiters_by_divisions()
    for group, count in result.items():
        print(f"    {group}: {count} recruiters")
    
    # Test through chart processor
    print("\n\n2. CHART PROCESSOR TESTS:")
    
    test_cases = [
        ("recruiters", "vacancies", "Recruiters by Vacancies"),
        ("recruiters", "applicants", "Recruiters by Applicants"),
        ("recruiters", "divisions", "Recruiters by Divisions"),
    ]
    
    for entity, group_by, description in test_cases:
        test_report = {
            "report_title": description,
            "chart": {
                "graph_description": description,
                "chart_type": "bar",
                "x_axis_name": "Group",
                "y_axis_name": "Number of Recruiters",
                "y_axis": {
                    "entity": entity,
                    "group_by": {"field": group_by}
                }
            }
        }
        
        try:
            result = await process_chart_data(test_report, client)
            real_data = result["chart"].get("real_data", {})
            
            labels = real_data.get("labels", [])
            values = real_data.get("values", [])
            
            if labels and values:
                print(f"\n  ✓ {description}:")
                for i in range(len(labels)):
                    print(f"    {labels[i]}: {values[i]} recruiters")
            else:
                print(f"\n  ✗ {description}: No data")
                
        except Exception as e:
            print(f"\n  ✗ {description}: Error - {str(e)}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test_recruiter_groupings())