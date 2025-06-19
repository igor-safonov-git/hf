#!/usr/bin/env python3
"""
Test all entity grouping combinations
"""

import asyncio
from chart_data_processor import process_chart_data
from huntflow_local_client import HuntflowLocalClient

async def test_all_groupings():
    client = HuntflowLocalClient()
    
    # Define all test cases
    test_cases = [
        # Applicants groupings
        ("applicants", "source", "Applicants by Source"),
        ("applicants", "stages", "Applicants by Stages"),
        ("applicants", "recruiters", "Applicants by Recruiters"),
        ("applicants", "hiring_managers", "Applicants by Hiring Managers"),
        ("applicants", "divisions", "Applicants by Divisions"),
        
        # Vacancies groupings
        ("vacancies", "state", "Vacancies by State"),
        ("vacancies", "recruiters", "Vacancies by Recruiters"),
        ("vacancies", "hiring_managers", "Vacancies by Hiring Managers"),
        ("vacancies", "divisions", "Vacancies by Divisions"),
        ("vacancies", "stages", "Vacancies by Stages"),
        
        # Recruiters groupings
        ("recruiters", "hirings", "Recruiters by Hirings"),
        ("recruiters", "vacancies", "Recruiters by Vacancies"),
        ("recruiters", "applicants", "Recruiters by Applicants"),
        ("recruiters", "divisions", "Recruiters by Divisions"),
        
        # Hires groupings
        ("hires", "recruiters", "Hires by Recruiters"),
        ("hires", "sources", "Hires by Sources"),
        ("hires", "stages", "Hires by Stages"), 
        ("hires", "divisions", "Hires by Divisions"),
        
        # Actions groupings
        ("actions", "type", "Actions by Type"),
        ("actions", "recruiters", "Actions by Recruiters"),
        
        # Vacancy statuses groupings
        ("vacancy_statuses", "type", "Vacancy Statuses by Type"),
        ("vacancy_statuses", "name", "Vacancy Statuses by Name"),
        
        # Active candidates
        ("active_candidates", "status_id", "Active Candidates by Status"),
        
        # Additional new entities from prompt
        ("divisions", None, "All Divisions"),
        ("sources", None, "All Sources"),
        ("rejections", None, "All Rejections"),
        
        # Specialized entities 
        ("applicants_by_status", None, "Applicants by Status Distribution"),
        ("applicants_by_source", None, "Applicants by Source Distribution"),
        ("applicants_by_recruiter", None, "Applicants by Recruiter Distribution"),
    ]
    
    working = []
    not_working = []
    
    print("Testing all entity grouping combinations...")
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
            
            if labels and values and not (labels == ["No Data"] or labels == ["Total " + entity.title()]):
                # Check if it's actually grouped data (more than 1 item or meaningful labels)
                if len(labels) > 1 or (len(labels) == 1 and not labels[0].startswith("Total") and not labels[0].startswith("All")):
                    working.append(f"{entity} by {group_by or 'none'}: {description}")
                    print(f"✓ {description}: {len(labels)} items")
                else:
                    not_working.append(f"{entity} by {group_by or 'none'}: {description} (single total)")
                    print(f"✗ {description}: Single total only")
            else:
                not_working.append(f"{entity} by {group_by or 'none'}: {description}")
                print(f"✗ {description}: No data")
                
        except Exception as e:
            not_working.append(f"{entity} by {group_by or 'none'}: {description} (Error: {str(e)})")
            print(f"✗ {description}: Error - {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"\nSUMMARY:")
    print(f"Working: {len(working)}")
    print(f"Not Working: {len(not_working)}")
    
    if not_working:
        print(f"\nNOT WORKING ({len(not_working)}):")
        for item in not_working:
            print(f"  - {item}")

if __name__ == "__main__":
    asyncio.run(test_all_groupings())