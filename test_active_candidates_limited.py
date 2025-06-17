#!/usr/bin/env python3
"""
Test active candidates with a limited sample to see if some applicants have links
"""
import asyncio
import os
from app import HuntflowClient
from virtual_engine import HuntflowVirtualEngine
from huntflow_metrics import HuntflowComputedMetrics

async def test_active_candidates_limited():
    """Test with a limited sample of applicants"""
    
    # Initialize client and engine
    hf_client = HuntflowClient()
    
    if not hf_client.token or not hf_client.acc_id:
        print("❌ Missing HF_TOKEN or ACC_ID environment variables")
        return
    
    # Get open vacancies
    open_vacancies_result = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/vacancies")
    open_vacancies = open_vacancies_result.get('items', [])
    open_vacancy_ids = {v['id'] for v in open_vacancies if v.get('state') == 'OPEN'}
    print(f"🏢 Found {len(open_vacancy_ids)} open vacancies")
    
    # Test with first few pages of applicants
    all_active_candidates = set()
    total_links_found = 0
    
    for page in range(1, 6):  # Test first 5 pages (150 applicants max)
        print(f"\n📄 Testing page {page}...")
        
        applicants_result = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/applicants", 
                                                params={"count": 30, "page": page})
        applicants = applicants_result.get('items', [])
        
        page_links = 0
        page_active = 0
        
        for applicant in applicants:
            applicant_id = applicant.get('id')
            links = applicant.get('links', [])
            
            if links:
                page_links += len(links)
                total_links_found += len(links)
                
                # Check if any links are to open vacancies
                for link in links:
                    link_vacancy_id = link.get('vacancy')
                    if link_vacancy_id in open_vacancy_ids:
                        all_active_candidates.add(applicant_id)
                        page_active += 1
                        break  # Count each applicant only once
        
        print(f"   Applicants: {len(applicants)}")
        print(f"   Links found: {page_links}")
        print(f"   Active candidates: {page_active}")
        
        # If we found no links on this page, maybe we can stop
        if page_links == 0:
            print(f"   No links found on page {page}, stopping...")
            break
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"   Total links found: {total_links_found}")
    print(f"   Total active candidates: {len(all_active_candidates)}")
    
    # If we found active candidates, test the computed metric
    if all_active_candidates:
        print(f"\n🧪 TESTING WITH ACTUAL DATA:")
        engine = HuntflowVirtualEngine(hf_client)
        
        # Monkey patch the engine to only look at first few pages
        original_method = engine._get_applicants_data
        
        async def limited_applicants_data():
            limited_applicants = []
            for page in range(1, 6):  # Same 5 pages
                result = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/applicants", 
                                            params={"count": 30, "page": page})
                applicants = result.get('items', [])
                limited_applicants.extend(applicants)
                
                # Stop if no links found
                if not any(a.get('links', []) for a in applicants):
                    break
            return limited_applicants
        
        engine._get_applicants_data = limited_applicants_data
        
        metrics = HuntflowComputedMetrics(engine)
        active_count = await metrics.active_candidates()
        print(f"   Active candidates (computed): {active_count}")
    else:
        print(f"   No active candidates found in sample")

if __name__ == "__main__":
    asyncio.run(test_active_candidates_limited())