#!/usr/bin/env python3
"""
Debug active candidates matching logic
"""
import asyncio
import os
from app import HuntflowClient
from virtual_engine import HuntflowVirtualEngine
from huntflow_metrics import HuntflowComputedMetrics

async def debug_active_candidates_detailed():
    """Debug why active_candidates returns 0"""
    
    # Initialize client and engine
    hf_client = HuntflowClient()
    
    if not hf_client.token or not hf_client.acc_id:
        print("❌ Missing HF_TOKEN or ACC_ID environment variables")
        return
    
    engine = HuntflowVirtualEngine(hf_client)
    metrics = HuntflowComputedMetrics(engine)
    
    print("🏢 Getting open vacancies...")
    open_vacancies = await engine._execute_vacancies_query(None)
    open_vacancy_ids = {v['id'] for v in open_vacancies if v.get('state') == 'OPEN'}
    print(f"   Found {len(open_vacancy_ids)} open vacancies")
    if open_vacancy_ids:
        print(f"   Sample open vacancy IDs: {list(open_vacancy_ids)[:5]}...")
    
    print("\n👥 Getting applicants data...")
    applicants_data = await engine._get_applicants_data()
    print(f"   Found {len(applicants_data)} total applicants")
    
    # Count links and check if any match open vacancies
    total_links = 0
    links_to_open_vacancies = 0
    active_candidate_ids = set()
    
    sample_links = []
    
    for applicant in applicants_data:
        applicant_id = applicant.get('id')
        links = applicant.get('links', [])
        
        if links:
            total_links += len(links)
            
            # Check each link
            for link in links:
                link_vacancy_id = link.get('vacancy')
                if link_vacancy_id in open_vacancy_ids:
                    links_to_open_vacancies += 1
                    active_candidate_ids.add(applicant_id)
                
                # Collect sample links for analysis
                if len(sample_links) < 10:
                    sample_links.append({
                        'applicant_id': applicant_id,
                        'link_vacancy_id': link_vacancy_id,
                        'is_open': link_vacancy_id in open_vacancy_ids,
                        'status': link.get('status'),
                        'link': link
                    })
    
    print(f"\n📊 RESULTS:")
    print(f"   Total links: {total_links}")
    print(f"   Links to open vacancies: {links_to_open_vacancies}")
    print(f"   Active candidates: {len(active_candidate_ids)}")
    
    print(f"\n🔗 SAMPLE LINKS:")
    for i, sample in enumerate(sample_links):
        print(f"   {i+1}. Applicant {sample['applicant_id']} → Vacancy {sample['link_vacancy_id']} (Open: {sample['is_open']})")
    
    # Check if the issue is with vacancy state filtering
    print(f"\n🏢 VACANCY STATE ANALYSIS:")
    all_vacancies = await engine._execute_vacancies_query(None)
    state_counts = {}
    for vacancy in all_vacancies:
        state = vacancy.get('state')
        state_counts[state] = state_counts.get(state, 0) + 1
    
    for state, count in state_counts.items():
        print(f"   {state}: {count} vacancies")
    
    # Test the actual active_candidates method
    print(f"\n🧪 TESTING ACTIVE_CANDIDATES METHOD:")
    active_count = await metrics.active_candidates()
    print(f"   Result: {active_count}")

if __name__ == "__main__":
    asyncio.run(debug_active_candidates_detailed())