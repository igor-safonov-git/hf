#!/usr/bin/env python3
"""
Test the newly added groupings (moves, rejections, time-based, priority)
"""

import asyncio
from chart_data_processor import process_chart_data
from huntflow_local_client import HuntflowLocalClient

async def test_new_groupings():
    client = HuntflowLocalClient()
    
    # Define new test cases
    test_cases = [
        # Moves groupings
        ("moves", "recruiters", "Moves by Recruiters"),
        ("moves", "type", "Moves by Type"),
        ("moves", None, "Total Moves"),
        
        # Rejections groupings (with group_by)
        ("rejections", "recruiters", "Rejections by Recruiters"),
        ("rejections", "reasons", "Rejections by Reasons"),
        ("rejections", "stages", "Rejections by Stages"),
        
        # Time-based groupings
        ("applicants", "month", "Applicants by Month"),
        ("vacancies", "month", "Vacancies by Month"),
        ("actions", "month", "Actions by Month"),
        
        # Priority grouping
        ("vacancies", "priority", "Vacancies by Priority"),
        
        # Previously working entities that should also work
        ("moves_by_recruiter", None, "Moves by Recruiter (entity)"),
        ("added_applicants_by_recruiter", None, "Applicants Added by Recruiter"),
        ("rejections_by_recruiter", None, "Rejections by Recruiter (entity)"),
        ("rejections_by_stage", None, "Rejections by Stage (entity)"),
        ("rejections_by_reason", None, "Rejections by Reason (entity)"),
    ]
    
    print("Testing newly added groupings...")
    print("=" * 60)
    
    for entity, group_by, description in test_cases:
        # Build test report
        test_report = {
            "report_title": description,
            "chart": {
                "graph_description": description,
                "chart_type": "bar",
                "x_axis_name": "Item",
                "y_axis_name": "Count",
                "y_axis": {
                    "entity": entity,
                    "group_by": {"field": group_by} if group_by else None
                }
            }
        }
        
        try:
            # Process the chart data
            result = await process_chart_data(test_report, client)
            real_data = result["chart"].get("real_data", {})
            
            # Check if we got meaningful data
            labels = real_data.get("labels", [])
            values = real_data.get("values", [])
            
            if labels and values:
                print(f"✓ {description}: {len(labels)} items, total: {sum(values)}")
                # Show first 3 items
                for i in range(min(3, len(labels))):
                    print(f"  - {labels[i]}: {values[i]}")
            else:
                print(f"✗ {description}: No data")
                
        except Exception as e:
            print(f"✗ {description}: Error - {str(e)}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test_new_groupings())