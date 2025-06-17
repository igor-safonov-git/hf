#!/usr/bin/env python3
"""
Debug script to examine status distribution
"""
import asyncio
import os
from app import HuntflowClient
from virtual_engine import HuntflowVirtualEngine
from huntflow_metrics import HuntflowComputedMetrics

async def debug_status_distribution():
    """Debug the actual status distribution"""
    
    # Initialize client and engine
    hf_token = os.getenv('HF_TOKEN')
    acc_id = os.getenv('ACC_ID')
    
    if not hf_token or not acc_id:
        print("❌ Missing HF_TOKEN or ACC_ID environment variables")
        return
    
    hf_client = HuntflowClient()
    engine = HuntflowVirtualEngine(hf_client)
    metrics = HuntflowComputedMetrics(engine)
    
    print("🔍 Getting status mapping...")
    status_mapping = await engine._get_status_mapping()
    
    print("📊 Getting open vacancies...")
    open_vacancies = await engine._execute_vacancies_query(None)
    open_vacancy_ids = {v['id'] for v in open_vacancies if v.get('state') == 'OPEN'}
    print(f"Found {len(open_vacancy_ids)} open vacancies")
    
    print("👥 Getting applicants data...")
    applicants_data = await engine._get_applicants_data()
    print(f"Found {len(applicants_data)} total applicants")
    
    # Count by status ID (not name) for accuracy
    status_id_counts = {}
    total_active_links = 0
    
    for applicant in applicants_data:
        links = applicant.get('links', [])
        for link in links:
            link_vacancy_id = link.get('vacancy')
            link_status_id = link.get('status')
            
            if link_vacancy_id in open_vacancy_ids and link_status_id:
                status_id_counts[link_status_id] = status_id_counts.get(link_status_id, 0) + 1
                total_active_links += 1
    
    print(f"\n📈 Found {total_active_links} total active links")
    print(f"🎯 Top 10 statuses by count:")
    
    # Convert to names and sort
    status_name_counts = {}
    for status_id, count in status_id_counts.items():
        status_info = status_mapping.get(status_id, {'name': f'Unknown {status_id}'})
        if isinstance(status_info, dict):
            name = status_info.get('name', f'Status {status_id}')
        else:
            name = str(status_info)
        status_name_counts[name] = status_name_counts.get(name, 0) + count
    
    sorted_statuses = sorted(status_name_counts.items(), key=lambda x: x[1], reverse=True)
    
    for i, (name, count) in enumerate(sorted_statuses[:10]):
        percentage = (count / total_active_links) * 100
        print(f"{i+1:2d}. {name}: {count} ({percentage:.1f}%)")
    
    # Look specifically for security check statuses
    print(f"\n🔍 All security-related statuses:")
    security_total = 0
    for name, count in sorted_statuses:
        if 'СБ' in name or 'проверк' in name.lower() or 'security' in name.lower():
            print(f"   - {name}: {count}")
            security_total += count
    
    print(f"\n📊 Total in security-related statuses: {security_total}")

if __name__ == "__main__":
    asyncio.run(debug_status_distribution())