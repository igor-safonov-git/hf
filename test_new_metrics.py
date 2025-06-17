#!/usr/bin/env python3
"""
Quick test for the new advanced calculated metrics
"""
import asyncio
import logging
from huntflow_metrics import HuntflowComputedMetrics
from virtual_engine import HuntflowVirtualEngine
from app import hf_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_new_metrics():
    """Test all 9 new advanced metrics"""
    print("🧪 Testing All 9 New Advanced Metrics")
    print("=" * 60)
    
    try:
        # Setup
        engine = HuntflowVirtualEngine(hf_client)
        metrics = HuntflowComputedMetrics(engine)
        
        # Test 1: Time to Fill
        print("\n📊 1. Time to Fill...")
        time_to_fill = await metrics.time_to_fill()
        print(f"✅ Average days from vacancy start to close: {time_to_fill:.1f} days")
        
        # Test 2: Time to Hire  
        print("\n📊 2. Time to Hire...")
        time_to_hire = await metrics.time_to_hire()
        print(f"✅ Average days from application to hire (last 90 days): {time_to_hire:.1f} days")
        
        # Test 3: Source Effectiveness
        print("\n📊 3. Source/Channel Effectiveness...")
        source_effectiveness = await metrics.source_effectiveness()
        print(f"✅ Found {len(source_effectiveness)} sources with conversion data")
        for i, source in enumerate(source_effectiveness[:5], 1):  # Show top 5
            print(f"   {i}. {source['source_name']}: {source['conversion_rate']}% conversion ({source['hires']}/{source['total_applicants']})")
        
        # Test 4: Applicants per Opening
        print("\n📊 4. Applicants per Opening...")
        applicants_per_opening = await metrics.applicants_per_opening()
        print(f"✅ Found {len(applicants_per_opening)} open vacancies with applicants")
        for i, vacancy in enumerate(applicants_per_opening[:5], 1):  # Show top 5
            print(f"   {i}. {vacancy['position'][:50]}...: {vacancy['applicant_count']} applicants")
        
        # Test 5: Application-to-Interview Ratio
        print("\n📊 5. Application-to-Interview Ratio...")
        app_to_interview = await metrics.application_to_interview_ratio()
        print(f"✅ Found {len(app_to_interview)} vacancies with interview data")
        for i, vacancy in enumerate(app_to_interview[:3], 1):  # Show top 3
            print(f"   {i}. {vacancy['position'][:40]}...: {vacancy['interview_ratio']}% ({vacancy['interviewed']}/{vacancy['total_applicants']})")
        
        # Test 6: Interview-to-Offer Ratio
        print("\n📊 6. Interview-to-Offer Ratio...")
        interview_to_offer = await metrics.interview_to_offer_ratio()
        print(f"✅ Found {len(interview_to_offer)} vacancies with offer data")
        for i, vacancy in enumerate(interview_to_offer[:3], 1):  # Show top 3
            print(f"   {i}. {vacancy['position'][:40]}...: {vacancy['offer_ratio']}% ({vacancy['offers']}/{vacancy['interviews']})")
        
        # Test 7: Offer Acceptance Rate
        print("\n📊 7. Offer Acceptance Rate...")
        offer_acceptance = await metrics.offer_acceptance_rate(months_back=6)
        print(f"✅ Found {len(offer_acceptance)} months with offer data")
        for month_data in offer_acceptance[:3]:  # Show last 3 months
            print(f"   {month_data['month']}: {month_data['acceptance_rate']}% ({month_data['offers_accepted']}/{month_data['offers_sent']})")
        
        # Test 8: Selection Ratio
        print("\n📊 8. Selection Ratio (Applicant-to-Hire)...")
        selection_ratio = await metrics.selection_ratio()
        print(f"✅ Overall hire rate: {selection_ratio:.2%}")
        
        # Test 9: Vacancy Rate
        print("\n📊 9. Vacancy Rate (Open Reqs)...")
        vacancy_rate = await metrics.vacancy_rate()
        print(f"✅ Ratio of open to total vacancies: {vacancy_rate:.2%}")
        
        print("\n" + "=" * 60)
        print("🎉 ALL 9 NEW ADVANCED METRICS WORKING SUCCESSFULLY!")
        print("=" * 60)
        
        # Summary
        print("\n📈 METRICS SUMMARY:")
        print(f"   • Time to Fill: {time_to_fill:.1f} days")
        print(f"   • Time to Hire: {time_to_hire:.1f} days") 
        print(f"   • Selection Ratio: {selection_ratio:.2%}")
        print(f"   • Vacancy Rate: {vacancy_rate:.2%}")
        print(f"   • Sources analyzed: {len(source_effectiveness)}")
        print(f"   • Vacancies with applicants: {len(applicants_per_opening)}")
        print(f"   • Interview conversion data: {len(app_to_interview)} vacancies")
        print(f"   • Offer conversion data: {len(interview_to_offer)} vacancies")
        print(f"   • Monthly acceptance data: {len(offer_acceptance)} months")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_new_metrics())
    exit(0 if success else 1)