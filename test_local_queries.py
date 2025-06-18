"""Test local database queries and JSON generation"""

import asyncio
import json
from huntflow_local_client import HuntflowLocalClient
from query_huntflow_cache import HuntflowCache

async def test_queries():
    client = HuntflowLocalClient()
    cache = HuntflowCache()
    
    print("=== Testing Local Database ===\n")
    
    # 1. Test basic counts
    print("1. Basic counts:")
    vacancies = await client._req("GET", f"/v2/accounts/{client.account_id}/vacancies")
    print(f"   Total vacancies: {len(vacancies.get('items', []))}")
    
    applicants = await client._req("GET", f"/v2/accounts/{client.account_id}/applicants/search")
    print(f"   Total applicants: {len(applicants.get('items', []))}")
    
    statuses = await client._req("GET", f"/v2/accounts/{client.account_id}/vacancies/statuses")
    print(f"   Total statuses: {len(statuses.get('items', []))}")
    
    # 2. Test vacancy data
    print("\n2. Sample vacancy data:")
    if vacancies.get('items'):
        vacancy = vacancies['items'][0]
        print(f"   ID: {vacancy.get('id')}")
        print(f"   Position: {vacancy.get('position')}")
        print(f"   State: {vacancy.get('state')}")
        print(f"   Created: {vacancy.get('created')}")
    
    # 3. Test applicant data
    print("\n3. Sample applicant data:")
    if applicants.get('items'):
        applicant = applicants['items'][0]
        print(f"   ID: {applicant.get('id')}")
        print(f"   Name: {applicant.get('first_name')} {applicant.get('last_name')}")
        print(f"   Email: {applicant.get('email')}")
        print(f"   Created: {applicant.get('created')}")
    
    # 4. Test status distribution
    print("\n4. Status distribution:")
    dist = await client.get_status_distribution()
    if dist:
        for status, count in list(dist.items())[:5]:
            print(f"   {status}: {count}")
    else:
        print("   No status distribution data")
    
    # 5. Test chart data generation
    print("\n5. Chart data for vacancies by state:")
    vacancy_states = {}
    for v in vacancies.get('items', []):
        state = v.get('state', 'Unknown')
        vacancy_states[state] = vacancy_states.get(state, 0) + 1
    
    chart_data = {
        "labels": list(vacancy_states.keys()),
        "values": list(vacancy_states.values())
    }
    print(f"   {json.dumps(chart_data, indent=2)}")
    
    # 6. Test applicant sources
    print("\n6. Applicant sources:")
    sources = await client._req("GET", f"/v2/accounts/{client.account_id}/applicants/sources")
    if sources.get('items'):
        for source in sources['items'][:5]:
            print(f"   {source.get('name')} (ID: {source.get('id')}, Type: {source.get('type')})")
    
    # 7. Test virtual entities (recruiters)
    print("\n7. Virtual entities test (recruiters):")
    # Since we don't have a recruiters table, we'll simulate it
    coworkers = await client._req("GET", f"/v2/accounts/{client.account_id}/coworkers")
    if coworkers.get('items'):
        print(f"   Total coworkers: {len(coworkers['items'])}")
        for coworker in coworkers['items'][:3]:
            print(f"   - {coworker.get('name')} (ID: {coworker.get('id')})")
    
    # 8. Generate sample report JSON
    print("\n8. Sample report JSON for applicants by source:")
    
    # Count applicants by source (simulated since we don't have source data in applicants)
    report = {
        "report_title": "Applicants by Source",
        "main_metric": {
            "label": "Total Applicants",
            "value": {
                "operation": "count",
                "entity": "applicants"
            },
            "real_value": len(applicants.get('items', []))
        },
        "chart": {
            "graph_description": "Distribution of applicants across different sources",
            "chart_type": "bar",
            "x_axis_name": "Source",
            "y_axis_name": "Number of Applicants",
            "x_axis": {
                "operation": "field",
                "field": "name"
            },
            "y_axis": {
                "operation": "count",
                "entity": "applicants",
                "group_by": {
                    "field": "source_id"
                }
            },
            "real_data": {
                "labels": [s.get('name', 'Unknown') for s in sources.get('items', [])[:5]],
                "values": [10, 25, 15, 30, 20],  # Simulated data
                "title": "Applicants by Source"
            }
        }
    }
    
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    asyncio.run(test_queries())