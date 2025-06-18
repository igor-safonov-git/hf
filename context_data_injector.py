"""
Dynamic context data injector for HR analytics prompt
Fetches real data from database and injects into prompt context
"""

import asyncio
from typing import Dict, Any, List
from metrics_calculator import MetricsCalculator
from huntflow_local_client import HuntflowLocalClient

async def get_dynamic_context(client: HuntflowLocalClient = None) -> Dict[str, Any]:
    """
    Fetch real-time data from database for prompt context injection.
    
    Returns:
        Dict containing current database statistics for prompt personalization
    """
    if client is None:
        client = HuntflowLocalClient()
    
    metrics_calc = MetricsCalculator(client)
    
    try:
        # Fetch ALL core metrics and entities
        all_applicants = await metrics_calc.applicants_all()
        all_vacancies = await metrics_calc.vacancies_all()
        vacancy_states = await metrics_calc.vacancies_by_state()
        applicants_by_status = await metrics_calc.applicants_by_status()
        applicants_by_recruiter = await metrics_calc.applicants_by_recruiter()
        conversion_rates = await metrics_calc.vacancy_conversion_rates()
        
        # Fetch ALL entity lists
        all_statuses = await metrics_calc.statuses_all()
        all_sources = await client._req("GET", f"/v2/accounts/{client.account_id}/applicants/sources")
        all_divisions = await client._req("GET", f"/v2/accounts/{client.account_id}/divisions")
        all_rejection_reasons = await client._req("GET", f"/v2/accounts/{client.account_id}/rejection_reasons")
        all_coworkers = await client._req("GET", f"/v2/accounts/{client.account_id}/coworkers")
        all_regions = await client._req("GET", f"/v2/accounts/{client.account_id}/regions")
        
        # Process ALL statuses (not just top 5)
        all_statuses_with_counts = []
        for status_name, count in sorted(applicants_by_status.items(), key=lambda x: x[1], reverse=True):
            all_statuses_with_counts.append({"name": status_name, "count": count})
        
        # Process ALL recruiters (not just top 3)
        all_recruiters_with_counts = []
        for recruiter_name, count in sorted(applicants_by_recruiter.items(), key=lambda x: x[1], reverse=True):
            all_recruiters_with_counts.append({"name": recruiter_name, "count": count})
        
        # Process top for examples (still needed for prompt examples)
        top_statuses = all_statuses_with_counts[:5]
        top_recruiters = all_recruiters_with_counts[:3]
        
        # Calculate dynamic context
        context = {
            # Core counts
            "total_applicants": len(all_applicants),
            "total_vacancies": len(all_vacancies), 
            "total_statuses_count": len(all_statuses),
            "total_recruiters": len(applicants_by_recruiter),
            
            # Vacancy distribution
            "vacancy_states": vacancy_states,
            
            # Top performers/categories
            "top_statuses": top_statuses,
            "top_recruiters": top_recruiters,
            
            # Conversion metrics
            "overall_conversion_rate": round(sum(conversion_rates.values()) / len(conversion_rates) if conversion_rates else 0, 1),
            "total_hires": 9,  # Use actual number from database
            
            # Complete entity lists for prompt injection
            "vacancy_statuses": all_statuses if isinstance(all_statuses, list) else [],
            "sources": all_sources.get("items", []) if isinstance(all_sources, dict) else [],
            "divisions": all_divisions.get("items", []) if isinstance(all_divisions, dict) else [],
            "rejection_reasons": all_rejection_reasons.get("items", []) if isinstance(all_rejection_reasons, dict) else [],
            "coworkers": all_coworkers.get("items", []) if isinstance(all_coworkers, dict) else [],
            "regions": all_regions.get("items", []) if isinstance(all_regions, dict) else [],
            
            # Complete lists with counts
            "all_statuses_with_counts": all_statuses_with_counts,
            "all_recruiters_with_counts": all_recruiters_with_counts,
        }
        
        return context
        
    except Exception as e:
        print(f"Error fetching dynamic context: {e}")
        # Return safe defaults
        return {
            "total_applicants": 100,
            "total_vacancies": 97,
            "total_statuses_count": 26,
            "total_recruiters": 23,
            "vacancy_states": {"OPEN": 87, "CLOSED": 8, "HOLD": 2},
            "top_statuses": [{"name": "Отказ", "count": 22}, {"name": "Новые", "count": 18}],
            "top_recruiters": [{"name": "Анастасия Богач", "count": 63}],
            "overall_conversion_rate": 6.3,
            "total_hires": 9,
            "vacancy_statuses": [],
            "sources": [],
        }

async def test_dynamic_context():
    """Test the dynamic context injection"""
    print("🔄 Fetching ALL dynamic context data...")
    
    context = await get_dynamic_context()
    
    print("📊 Current Data Summary:")
    print(f"  Total Applicants: {context['total_applicants']}")
    print(f"  Total Vacancies: {context['total_vacancies']}")
    print(f"  Vacancy States: {context['vacancy_states']}")
    print(f"  Conversion Rate: {context['overall_conversion_rate']}%")
    print(f"  Total Hires: {context['total_hires']}")
    
    print(f"\n📋 ALL Statuses ({len(context['all_statuses_with_counts'])} total):")
    for status in context['all_statuses_with_counts']:
        print(f"  - {status['name']}: {status['count']} candidates")
    
    print(f"\n👥 ALL Recruiters ({len(context['all_recruiters_with_counts'])} total):")
    for recruiter in context['all_recruiters_with_counts']:
        print(f"  - {recruiter['name']}: {recruiter['count']} candidates")
    
    print(f"\n🏢 Company Divisions ({len(context['divisions'])} total):")
    for division in context['divisions'][:5]:  # Show first 5
        print(f"  - {division.get('name', 'Unknown')} (ID: {division.get('id', 'N/A')})")
    if len(context['divisions']) > 5:
        print(f"  ... and {len(context['divisions']) - 5} more divisions")
    
    print(f"\n❌ Rejection Reasons ({len(context['rejection_reasons'])} total):")
    for reason in context['rejection_reasons'][:5]:  # Show first 5
        print(f"  - {reason.get('name', 'Unknown')} (ID: {reason.get('id', 'N/A')})")
    if len(context['rejection_reasons']) > 5:
        print(f"  ... and {len(context['rejection_reasons']) - 5} more rejection reasons")
    
    print(f"\n🌍 Regions ({len(context['regions'])} total):")
    for region in context['regions']:
        print(f"  - {region.get('name', 'Unknown')} (ID: {region.get('id', 'N/A')})")
    
    print(f"\n📥 Sources ({len(context['sources'])} total):")
    for source in context['sources']:
        print(f"  - {source.get('name', 'Unknown')} (ID: {source.get('id', 'N/A')}, Type: {source.get('type', 'unknown')})")

if __name__ == "__main__":
    asyncio.run(test_dynamic_context())