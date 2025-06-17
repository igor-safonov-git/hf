#!/usr/bin/env python3
"""
Debug what interview and offer statuses actually exist in the system
"""
import asyncio
import logging
from virtual_engine import HuntflowVirtualEngine
from app import hf_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_interview_offer_statuses():
    """Check what interview and offer statuses exist"""
    print("🔍 Debugging Interview & Offer Statuses")
    print("=" * 50)
    
    try:
        # Setup
        engine = HuntflowVirtualEngine(hf_client)
        
        # Get status mapping
        status_mapping = await engine._get_status_mapping()
        
        # Find interview statuses by name patterns
        interview_keywords = ['интервью', 'interview', 'собеседование']
        interview_statuses = []
        
        for status_id, status_info in status_mapping.items():
            status_name = status_info.get('name', '').lower()
            if any(word in status_name for word in interview_keywords):
                interview_statuses.append({
                    'id': status_id,
                    'name': status_info.get('name'),
                    'type': status_info.get('type')
                })
        
        print(f"\n📊 INTERVIEW STATUSES FOUND: {len(interview_statuses)}")
        for status in interview_statuses:
            print(f"   ID {status['id']}: '{status['name']}' (type: {status['type']})")
        
        # Find offer statuses by name patterns
        offer_keywords = ['оффер', 'offer', 'предложение']
        offer_statuses = []
        
        for status_id, status_info in status_mapping.items():
            status_name = status_info.get('name', '').lower()
            if any(word in status_name for word in offer_keywords):
                offer_statuses.append({
                    'id': status_id,
                    'name': status_info.get('name'),
                    'type': status_info.get('type')
                })
        
        print(f"\n📊 OFFER STATUSES FOUND: {len(offer_statuses)}")
        for status in offer_statuses:
            print(f"   ID {status['id']}: '{status['name']}' (type: {status['type']})")
        
        # Check if any applicants have these statuses
        applicants_data = await engine._get_applicants_data()
        
        interview_ids = {s['id'] for s in interview_statuses}
        offer_ids = {s['id'] for s in offer_statuses}
        
        interview_count = 0
        offer_count = 0
        
        for applicant in applicants_data:
            status_id = applicant.get('status_id')
            if status_id in interview_ids:
                interview_count += 1
            if status_id in offer_ids:
                offer_count += 1
        
        print(f"\n🎯 APPLICANTS IN THESE STATUSES:")
        print(f"   Interview statuses: {interview_count} applicants")
        print(f"   Offer statuses: {offer_count} applicants")
        
        # Also check links for status usage
        interview_links = 0
        offer_links = 0
        
        for applicant in applicants_data:
            links = applicant.get('links', [])
            for link in links:
                link_status = link.get('status')
                if link_status in interview_ids:
                    interview_links += 1
                if link_status in offer_ids:
                    offer_links += 1
        
        print(f"\n🔗 LINKS IN THESE STATUSES:")
        print(f"   Interview links: {interview_links}")
        print(f"   Offer links: {offer_links}")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(debug_interview_offer_statuses())
    exit(0 if success else 1)