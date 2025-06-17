#!/usr/bin/env python3
"""
Quick metrics debugging - minimal API calls to identify core issues
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import HuntflowClient

async def debug_basic_data():
    """Debug basic data with minimal API calls"""
    print("=== QUICK METRICS DEBUGGING ===")
    
    hf_client = HuntflowClient()
    
    # 1. Check vacancies (should be quick)
    print("\n1. TESTING VACANCIES:")
    try:
        vacancies_result = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/vacancies", params={"count": 10, "page": 1})
        vacancies = vacancies_result.get("items", [])
        print(f"✅ Fetched {len(vacancies)} vacancies (sample)")
        
        if vacancies:
            sample_vacancy = vacancies[0]
            print(f"Sample vacancy: ID={sample_vacancy.get('id')}, State={sample_vacancy.get('state')}, Created={sample_vacancy.get('created')}")
            
            # Check states
            states = {}
            for v in vacancies:
                state = v.get('state', 'Unknown')
                states[state] = states.get(state, 0) + 1
            print(f"States in sample: {states}")
            
            # Check for closed vacancies with dates
            closed_with_dates = 0
            for v in vacancies:
                if v.get('state') == 'CLOSED' and v.get('created') and v.get('updated'):
                    closed_with_dates += 1
            print(f"Closed vacancies with dates: {closed_with_dates}/{len(vacancies)}")
            
    except Exception as e:
        print(f"❌ Error fetching vacancies: {e}")

    # 2. Check applicants (very limited sample)
    print("\n2. TESTING APPLICANTS (LIMITED SAMPLE):")
    try:
        applicants_result = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/applicants", params={"count": 5, "page": 1})
        applicants = applicants_result.get("items", [])
        print(f"✅ Fetched {len(applicants)} applicants (tiny sample)")
        
        if applicants:
            sample_applicant = applicants[0]
            print(f"Sample applicant: ID={sample_applicant.get('id')}")
            print(f"Has source_id: {sample_applicant.get('source_id') is not None}")
            print(f"Has links: {len(sample_applicant.get('links', []))}")
            
            # Check links structure
            links = sample_applicant.get('links', [])
            if links:
                sample_link = links[0]
                print(f"Sample link: vacancy={sample_link.get('vacancy')}, status={sample_link.get('status')}")
        
    except Exception as e:
        print(f"❌ Error fetching applicants: {e}")

    # 3. Check status mapping
    print("\n3. TESTING STATUS MAPPING:")
    try:
        statuses_result = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/vacancy_statuses")
        statuses = statuses_result.get("items", [])
        print(f"✅ Fetched {len(statuses)} statuses")
        
        if statuses:
            # Check for hired statuses
            hired_statuses = []
            interview_statuses = []
            offer_statuses = []
            
            for status in statuses:
                status_name = status.get('name', '').lower()
                status_type = status.get('type', '').lower()
                
                if status_type == 'hired':
                    hired_statuses.append(status)
                
                if any(word in status_name for word in ['интервью', 'interview', 'собеседование']):
                    interview_statuses.append(status)
                
                if any(word in status_name for word in ['оффер', 'offer', 'предложение']):
                    offer_statuses.append(status)
            
            print(f"Hired statuses found: {len(hired_statuses)} - {[s.get('name') for s in hired_statuses]}")
            print(f"Interview statuses found: {len(interview_statuses)} - {[s.get('name') for s in interview_statuses]}")
            print(f"Offer statuses found: {len(offer_statuses)} - {[s.get('name') for s in offer_statuses]}")
        
    except Exception as e:
        print(f"❌ Error fetching statuses: {e}")

    # 4. Check sources
    print("\n4. TESTING SOURCES:")
    try:
        sources_result = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/applicants/sources")
        sources = sources_result.get("items", [])
        print(f"✅ Fetched {len(sources)} sources")
        
        if sources:
            print(f"Sample sources: {[s.get('name') for s in sources[:5]]}")
        
    except Exception as e:
        print(f"❌ Error fetching sources: {e}")

    print("\n=== DIAGNOSIS ===")
    print("Based on this minimal test, the likely issues are:")
    print("1. Time to Fill: Needs closed vacancies with valid created/updated dates")
    print("2. Time to Hire: Needs applicants in 'hired' status with recent activity")
    print("3. Source Effectiveness: Needs applicants with source_id AND hired status")
    print("4. Applicants per Opening: Needs open vacancies with applicant links")
    print("5. Interview/Offer Ratios: Needs status names matching interview/offer patterns")
    print("6. Offer Acceptance: Needs recent activity in offer->hired status transitions")

async def test_single_metric(metric_name):
    """Test a single metric with minimal data fetching"""
    print(f"\n=== TESTING {metric_name.upper()} ===")
    
    # Import here to avoid loading all data
    from virtual_engine import HuntflowVirtualEngine
    from huntflow_metrics import HuntflowComputedMetrics
    
    hf_client = HuntflowClient()
    engine = HuntflowVirtualEngine(hf_client)
    metrics = HuntflowComputedMetrics(engine)
    
    try:
        if metric_name == "time_to_fill":
            result = await metrics.time_to_fill()
            print(f"Result: {result} days")
            
        elif metric_name == "time_to_hire":
            result = await metrics.time_to_hire(days_back=30)  # Shorter period
            print(f"Result: {result} days")
            
        elif metric_name == "source_effectiveness":
            result = await metrics.source_effectiveness()
            print(f"Result: {len(result)} sources with data")
            if result:
                print(f"Sample: {result[0]}")
                
        elif metric_name == "applicants_per_opening":
            result = await metrics.applicants_per_opening()
            print(f"Result: {len(result)} vacancies with applicants")
            if result:
                print(f"Sample: {result[0]}")
        
    except Exception as e:
        print(f"❌ Error in {metric_name}: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run quick debugging"""
    print("Starting quick metrics debugging...")
    
    try:
        # First, basic data check
        await debug_basic_data()
        
        # Then test individual metrics
        metrics_to_test = [
            "time_to_fill",
            "time_to_hire", 
            "source_effectiveness",
            "applicants_per_opening"
        ]
        
        for metric in metrics_to_test:
            await test_single_metric(metric)
        
        print("\n=== DEBUGGING COMPLETE ===")
        
    except Exception as e:
        print(f"Error during debugging: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())