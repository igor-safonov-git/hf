#!/usr/bin/env python3
"""
Deep debugging script to investigate why all metrics return zero.
Tests each metric step by step with detailed logging.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy_executor import SQLAlchemyHuntflowExecutor
from virtual_engine import HuntflowVirtualEngine
from huntflow_metrics import HuntflowComputedMetrics, HuntflowMetricsHelper
from app import HuntflowClient

async def debug_underlying_data():
    """Debug the underlying data that metrics depend on"""
    print("=== DEBUGGING UNDERLYING DATA ===")
    
    hf_client = HuntflowClient()
    engine = HuntflowVirtualEngine(hf_client)
    executor = SQLAlchemyHuntflowExecutor(engine)
    
    metrics = HuntflowComputedMetrics(engine)
    
    print("\n1. VACANCIES DATA:")
    vacancies_data = await engine._execute_vacancies_query(None)
    print(f"Total vacancies: {len(vacancies_data)}")
    
    if vacancies_data:
        # Check states
        states = {}
        created_dates = []
        updated_dates = []
        
        for v in vacancies_data:
            state = v.get('state', 'Unknown')
            states[state] = states.get(state, 0) + 1
            
            if v.get('created'):
                created_dates.append(v['created'])
            if v.get('updated'):
                updated_dates.append(v['updated'])
        
        print(f"States distribution: {states}")
        print(f"Sample vacancy: {vacancies_data[0]}")
        print(f"Created dates range: {min(created_dates) if created_dates else 'None'} to {max(created_dates) if created_dates else 'None'}")
        print(f"Updated dates range: {min(updated_dates) if updated_dates else 'None'} to {max(updated_dates) if updated_dates else 'None'}")
    
    print("\n2. APPLICANTS DATA:")
    applicants_data = await engine._get_applicants_data()
    print(f"Total applicants: {len(applicants_data)}")
    
    if applicants_data:
        # Check sources, statuses, links
        sources = {}
        statuses = {}
        has_links = 0
        links_count = 0
        
        for a in applicants_data:
            source_id = a.get('source_id')
            if source_id:
                sources[source_id] = sources.get(source_id, 0) + 1
            
            status_id = a.get('status_id')
            if status_id:
                statuses[status_id] = statuses.get(status_id, 0) + 1
            
            links = a.get('links', [])
            if links:
                has_links += 1
                links_count += len(links)
        
        print(f"Source IDs found: {list(sources.keys())[:10]}...")  # First 10
        print(f"Status IDs found: {list(statuses.keys())[:10]}...")  # First 10
        print(f"Applicants with links: {has_links}/{len(applicants_data)}")
        print(f"Total links: {links_count}")
        print(f"Sample applicant: {applicants_data[0]}")
    
    print("\n3. STATUS MAPPING:")
    status_mapping = await engine._get_status_mapping()
    print(f"Status mapping entries: {len(status_mapping)}")
    
    if status_mapping:
        print("Sample statuses:")
        for i, (status_id, status_info) in enumerate(list(status_mapping.items())[:5]):
            print(f"  {status_id}: {status_info}")
        
        # Check for hired statuses
        hired_statuses = []
        for status_id, status_info in status_mapping.items():
            if isinstance(status_info, dict):
                status_type = status_info.get('type', '').lower()
                if status_type == 'hired':
                    hired_statuses.append((status_id, status_info))
        print(f"Hired statuses found: {hired_statuses}")
    
    print("\n4. SOURCES MAPPING:")
    sources_mapping = await engine._get_sources_mapping()
    print(f"Sources mapping entries: {len(sources_mapping)}")
    
    if sources_mapping:
        print("Sample sources:")
        for i, (source_id, source_name) in enumerate(list(sources_mapping.items())[:5]):
            print(f"  {source_id}: {source_name}")
    
    # No explicit cleanup needed

async def debug_time_to_fill():
    """Debug Time to Fill metric specifically"""
    print("\n=== DEBUGGING TIME TO FILL ===")
    
    hf_client = HuntflowClient()
    engine = HuntflowVirtualEngine(hf_client)
    executor = SQLAlchemyHuntflowExecutor(engine)
    
    metrics = HuntflowComputedMetrics(engine)
    
    # Get the raw data
    vacancies_data = await engine._execute_vacancies_query(None)
    
    print(f"Total vacancies: {len(vacancies_data)}")
    
    # Check closed vacancies
    closed_vacancies = [v for v in vacancies_data if v.get('state') == 'CLOSED']
    print(f"Closed vacancies: {len(closed_vacancies)}")
    
    if closed_vacancies:
        print(f"Sample closed vacancy: {closed_vacancies[0]}")
        
        # Check date parsing
        valid_date_pairs = 0
        for v in closed_vacancies:
            created_str = v.get('created')
            updated_str = v.get('updated')
            
            if created_str and updated_str:
                try:
                    created_date = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                    closed_date = datetime.fromisoformat(updated_str.replace('Z', '+00:00'))
                    days_diff = (closed_date - created_date).days
                    if days_diff >= 0:
                        valid_date_pairs += 1
                        print(f"Valid date pair: {created_str} -> {updated_str} ({days_diff} days)")
                        if valid_date_pairs >= 3:  # Show first 3
                            break
                except Exception as e:
                    print(f"Date parsing error: {e}")
        
        print(f"Valid date pairs: {valid_date_pairs}/{len(closed_vacancies)}")
    
    # Test the metric
    result = await metrics.time_to_fill()
    print(f"Time to Fill result: {result}")
    
    # No explicit cleanup needed

async def debug_time_to_hire():
    """Debug Time to Hire metric specifically"""
    print("\n=== DEBUGGING TIME TO HIRE ===")
    
    hf_client = HuntflowClient()
    engine = HuntflowVirtualEngine(hf_client)
    executor = SQLAlchemyHuntflowExecutor(engine)
    
    metrics = HuntflowComputedMetrics(engine)
    
    # Get status mapping and find hired statuses
    status_mapping = await engine._get_status_mapping()
    hired_status_ids = set()
    
    for status_id, status_info in status_mapping.items():
        if isinstance(status_info, dict):
            status_type = status_info.get('type', '').lower()
            if status_type == 'hired':
                hired_status_ids.add(status_id)
    
    print(f"Hired status IDs: {hired_status_ids}")
    
    # Get applicants data
    applicants_data = await engine._get_applicants_data()
    
    # Find hired applicants
    hired_applicants = []
    cutoff_date = datetime.now() - timedelta(days=90)
    
    for applicant in applicants_data:
        current_status = applicant.get('status_id')
        if current_status in hired_status_ids:
            hired_applicants.append(applicant)
    
    print(f"Hired applicants found: {len(hired_applicants)}")
    
    if hired_applicants:
        print(f"Sample hired applicant: {hired_applicants[0]}")
        
        # Check for recent hires
        recent_hires = 0
        for applicant in hired_applicants:
            links = applicant.get('links', [])
            for link in links:
                if link.get('status') in hired_status_ids:
                    link_updated = link.get('updated') or link.get('changed')
                    if link_updated:
                        try:
                            link_date = datetime.fromisoformat(link_updated.replace('Z', '+00:00'))
                            if link_date >= cutoff_date:
                                recent_hires += 1
                                print(f"Recent hire found: {link_updated}")
                                break
                        except Exception as e:
                            print(f"Date parsing error: {e}")
        
        print(f"Recent hires (last 90 days): {recent_hires}")
    
    # Test the metric
    result = await metrics.time_to_hire()
    print(f"Time to Hire result: {result}")
    
    # No explicit cleanup needed

async def debug_source_effectiveness():
    """Debug Source Effectiveness metric"""
    print("\n=== DEBUGGING SOURCE EFFECTIVENESS ===")
    
    hf_client = HuntflowClient()
    engine = HuntflowVirtualEngine(hf_client)
    executor = SQLAlchemyHuntflowExecutor(engine)
    
    metrics = HuntflowComputedMetrics(engine)
    
    # Get applicants and mappings
    applicants_data = await engine._get_applicants_data()
    status_mapping = await engine._get_status_mapping()
    sources_mapping = await engine._get_sources_mapping()
    
    print(f"Applicants: {len(applicants_data)}")
    print(f"Status mapping: {len(status_mapping)}")
    print(f"Sources mapping: {len(sources_mapping)}")
    
    # Find hired status IDs
    hired_status_ids = set()
    for status_id, status_info in status_mapping.items():
        if isinstance(status_info, dict):
            status_type = status_info.get('type', '').lower()
            if status_type == 'hired':
                hired_status_ids.add(status_id)
    
    print(f"Hired status IDs: {hired_status_ids}")
    
    # Check source data
    applicants_with_sources = 0
    hired_applicants = 0
    
    for applicant in applicants_data:
        source_id = applicant.get('source_id', 0)
        status_id = applicant.get('status_id', 0)
        
        if source_id and source_id in sources_mapping:
            applicants_with_sources += 1
        
        if status_id in hired_status_ids:
            hired_applicants += 1
    
    print(f"Applicants with valid sources: {applicants_with_sources}")
    print(f"Hired applicants: {hired_applicants}")
    
    # Test the metric
    result = await metrics.source_effectiveness()
    print(f"Source Effectiveness result: {len(result)} sources")
    
    if result:
        print(f"Sample result: {result[0]}")
    
    # No explicit cleanup needed

async def debug_applicants_per_opening():
    """Debug Applicants per Opening metric"""
    print("\n=== DEBUGGING APPLICANTS PER OPENING ===")
    
    hf_client = HuntflowClient()
    engine = HuntflowVirtualEngine(hf_client)
    executor = SQLAlchemyHuntflowExecutor(engine)
    
    metrics = HuntflowComputedMetrics(engine)
    
    # Get open vacancies
    vacancies_data = await engine._execute_vacancies_query(None)
    open_vacancies = [v for v in vacancies_data if v.get('state') == 'OPEN']
    open_vacancy_ids = {v['id'] for v in open_vacancies}
    
    print(f"Open vacancies: {len(open_vacancies)}")
    print(f"Open vacancy IDs: {list(open_vacancy_ids)[:10]}...")
    
    # Get applicants with links
    applicants_data = await engine._get_applicants_data()
    
    # Check links
    total_links = 0
    links_to_open_vacancies = 0
    
    for applicant in applicants_data:
        links = applicant.get('links', [])
        total_links += len(links)
        
        for link in links:
            vacancy_id = link.get('vacancy')
            if vacancy_id in open_vacancy_ids:
                links_to_open_vacancies += 1
    
    print(f"Total links: {total_links}")
    print(f"Links to open vacancies: {links_to_open_vacancies}")
    
    # Test the metric
    result = await metrics.applicants_per_opening()
    print(f"Applicants per Opening result: {len(result)} vacancies")
    
    if result:
        print(f"Sample result: {result[0]}")
    
    # No explicit cleanup needed

async def debug_interview_ratios():
    """Debug Interview-related metrics"""
    print("\n=== DEBUGGING INTERVIEW RATIOS ===")
    
    hf_client = HuntflowClient()
    engine = HuntflowVirtualEngine(hf_client)
    executor = SQLAlchemyHuntflowExecutor(engine)
    
    metrics = HuntflowComputedMetrics(engine)
    
    # Get status mapping
    status_mapping = await engine._get_status_mapping()
    
    # Find interview and offer status IDs
    interview_status_ids = set()
    offer_status_ids = set()
    
    for status_id, status_info in status_mapping.items():
        status_name = status_info.get('name', '').lower()
        if any(word in status_name for word in ['интервью', 'interview', 'собеседование']):
            interview_status_ids.add(status_id)
        elif any(word in status_name for word in ['оффер', 'offer', 'предложение']):
            offer_status_ids.add(status_id)
    
    print(f"Interview status IDs: {interview_status_ids}")
    print(f"Offer status IDs: {offer_status_ids}")
    
    # Get applicants data
    applicants_data = await engine._get_applicants_data()
    
    # Count applicants in these statuses
    interview_applicants = 0
    offer_applicants = 0
    
    for applicant in applicants_data:
        current_status = applicant.get('status_id')
        
        if current_status in interview_status_ids:
            interview_applicants += 1
        if current_status in offer_status_ids:
            offer_applicants += 1
        
        # Also check links
        links = applicant.get('links', [])
        for link in links:
            link_status = link.get('status')
            if link_status in interview_status_ids:
                interview_applicants += 1
            if link_status in offer_status_ids:
                offer_applicants += 1
    
    print(f"Applicants in interview statuses: {interview_applicants}")
    print(f"Applicants in offer statuses: {offer_applicants}")
    
    # Test metrics
    app_to_int_result = await metrics.application_to_interview_ratio()
    int_to_off_result = await metrics.interview_to_offer_ratio()
    
    print(f"Application-to-Interview result: {len(app_to_int_result)} vacancies")
    print(f"Interview-to-Offer result: {len(int_to_off_result)} vacancies")
    
    if app_to_int_result:
        print(f"Sample App-to-Int result: {app_to_int_result[0]}")
    if int_to_off_result:
        print(f"Sample Int-to-Off result: {int_to_off_result[0]}")
    
    # No explicit cleanup needed

async def debug_offer_acceptance_rate():
    """Debug Offer Acceptance Rate metric"""
    print("\n=== DEBUGGING OFFER ACCEPTANCE RATE ===")
    
    hf_client = HuntflowClient()
    engine = HuntflowVirtualEngine(hf_client)
    executor = SQLAlchemyHuntflowExecutor(engine)
    
    metrics = HuntflowComputedMetrics(engine)
    
    # Get status mapping
    status_mapping = await engine._get_status_mapping()
    
    # Find offer and hired status IDs
    offer_status_ids = set()
    hired_status_ids = set()
    
    for status_id, status_info in status_mapping.items():
        if isinstance(status_info, dict):
            status_name = status_info.get('name', '').lower()
            status_type = status_info.get('type', '').lower()
            
            if status_type == 'hired':
                hired_status_ids.add(status_id)
            elif any(word in status_name for word in ['оффер', 'offer', 'предложение']):
                offer_status_ids.add(status_id)
    
    print(f"Offer status IDs: {offer_status_ids}")
    print(f"Hired status IDs: {hired_status_ids}")
    
    # Get applicants data
    applicants_data = await engine._get_applicants_data()
    
    # Check recent activity (last 12 months)
    cutoff_date = datetime.now() - timedelta(days=365)
    monthly_activity = {}
    
    for applicant in applicants_data:
        links = applicant.get('links', [])
        
        for link in links:
            link_updated = link.get('updated') or link.get('changed')
            if not link_updated:
                continue
            
            try:
                update_date = datetime.fromisoformat(link_updated.replace('Z', '+00:00'))
                if update_date >= cutoff_date:
                    month_key = update_date.strftime('%Y-%m')
                    if month_key not in monthly_activity:
                        monthly_activity[month_key] = 0
                    monthly_activity[month_key] += 1
            except Exception as e:
                continue
    
    print(f"Monthly activity (last 12 months): {len(monthly_activity)} months")
    if monthly_activity:
        print(f"Sample months: {list(monthly_activity.keys())[:5]}")
    
    # Test the metric
    result = await metrics.offer_acceptance_rate()
    print(f"Offer Acceptance Rate result: {len(result)} months")
    
    if result:
        print(f"Sample result: {result[0]}")
    
    # No explicit cleanup needed

async def main():
    """Run all debugging tests"""
    print("Starting deep metric debugging...")
    
    try:
        await debug_underlying_data()
        await debug_time_to_fill()
        await debug_time_to_hire()
        await debug_source_effectiveness()
        await debug_applicants_per_opening()
        await debug_interview_ratios()
        await debug_offer_acceptance_rate()
        
        print("\n=== DEBUGGING COMPLETE ===")
        
    except Exception as e:
        print(f"Error during debugging: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())