#!/usr/bin/env python3
"""
Core issues debugging - direct API calls to identify metric problems
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import HuntflowClient

async def main():
    """Test core data issues directly"""
    print("=== CORE ISSUES DEBUGGING ===")
    
    hf_client = HuntflowClient()
    
    # 1. TEST TIME TO FILL - Check closed vacancies
    print("\n1. TIME TO FILL ISSUE:")
    try:
        vacancies_result = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/vacancies", params={"count": 20, "page": 1})
        vacancies = vacancies_result.get("items", [])
        
        closed_vacancies = [v for v in vacancies if v.get('state') == 'CLOSED']
        print(f"Total vacancies: {len(vacancies)}, Closed: {len(closed_vacancies)}")
        
        if closed_vacancies:
            sample = closed_vacancies[0]
            print(f"Sample closed vacancy: created={sample.get('created')}, updated={sample.get('updated')}")
            
            # Check if dates are valid
            valid_dates = 0
            for v in closed_vacancies:
                if v.get('created') and v.get('updated'):
                    try:
                        created = datetime.fromisoformat(v['created'].replace('Z', '+00:00'))
                        updated = datetime.fromisoformat(v['updated'].replace('Z', '+00:00'))
                        days = (updated - created).days
                        if days >= 0:
                            valid_dates += 1
                            print(f"  Valid: {days} days")
                    except:
                        pass
            print(f"✅ Closed vacancies with valid date ranges: {valid_dates}/{len(closed_vacancies)}")
        else:
            print("❌ NO CLOSED VACANCIES FOUND")
    
    except Exception as e:
        print(f"❌ Error: {e}")

    # 2. TEST STATUS MAPPING
    print("\n2. STATUS MAPPING ISSUE:")
    try:
        # Try the correct endpoint
        statuses_result = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/vacancies/statuses")
        statuses = statuses_result.get("items", [])
        print(f"✅ Fetched {len(statuses)} statuses")
        
        hired_count = 0
        interview_count = 0
        offer_count = 0
        
        for status in statuses:
            status_type = status.get('type', '').lower()
            status_name = status.get('name', '').lower()
            
            if status_type == 'hired':
                hired_count += 1
                print(f"  Hired status: {status.get('name')} (type={status_type})")
            
            if any(word in status_name for word in ['интервью', 'interview', 'собеседование']):
                interview_count += 1
                print(f"  Interview status: {status.get('name')}")
            
            if any(word in status_name for word in ['оффер', 'offer', 'предложение']):
                offer_count += 1
                print(f"  Offer status: {status.get('name')}")
        
        print(f"✅ Status counts - Hired: {hired_count}, Interview: {interview_count}, Offer: {offer_count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

    # 3. TEST APPLICANTS STRUCTURE
    print("\n3. APPLICANTS STRUCTURE:")
    try:
        applicants_result = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/applicants", params={"count": 5})
        applicants = applicants_result.get("items", [])
        print(f"✅ Fetched {len(applicants)} applicants")
        
        if applicants:
            sample = applicants[0]
            print(f"Sample applicant structure:")
            print(f"  Has source_id: {sample.get('source_id') is not None}")
            print(f"  Has links: {len(sample.get('links', []))}")
            
            links = sample.get('links', [])
            if links:
                link = links[0]
                print(f"  Sample link: vacancy={link.get('vacancy')}, status={link.get('status')}")
            
            # Check for any hired applicants in this sample
            hired_in_sample = 0
            for applicant in applicants:
                links = applicant.get('links', [])
                for link in links:
                    # We'll check against the status IDs we found above
                    if link.get('status'):  # Just check if status exists
                        print(f"  Applicant {applicant.get('id')} has status {link.get('status')}")
                        break
            
    except Exception as e:
        print(f"❌ Error: {e}")

    # 4. TEST SOURCES
    print("\n4. SOURCES ISSUE:")
    try:
        sources_result = await hf_client._req("GET", f"/v2/accounts/{hf_client.acc_id}/applicants/sources")
        sources = sources_result.get("items", [])
        print(f"✅ Fetched {len(sources)} sources")
        
        if sources:
            print(f"Sample sources: {[s.get('name') for s in sources[:3]]}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n=== CORE PROBLEMS IDENTIFIED ===")
    print("Run this script to see the exact data issues preventing metrics from working")

if __name__ == "__main__":
    asyncio.run(main())