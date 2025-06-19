#!/usr/bin/env python3
"""
Check if Анастасия Богач actually has zero hires or if there's a filtering issue
"""

import asyncio
from huntflow_local_client import HuntflowLocalClient
from enhanced_metrics_calculator import EnhancedMetricsCalculator

async def main():
    client = HuntflowLocalClient()
    calc = EnhancedMetricsCalculator(client, None)
    
    print("=== CHECKING АНАСТАСИЯ БОГАЧ DATA ===")
    print(f"Recruiter ID: 68691")
    print(f"Alternative names: Настя Богач, Анастасия Богач, Настя")
    
    print("\n1. ALL HIRES (no filters):")
    all_hires = await calc.hires()
    print(f"   Total hires in system: {len(all_hires)}")
    if all_hires:
        print("   Sample hire record:")
        for key, value in list(all_hires[0].items())[:5]:
            print(f"     {key}: {value}")
    
    print("\n2. HIRES WITH RECRUITER FILTER:")
    nastya_hires = await calc.hires({"recruiters": "68691"})
    print(f"   Hires for recruiter ID 68691: {len(nastya_hires)}")
    
    print("\n3. ALL APPLICANTS (no filters):")
    all_applicants = await calc.applicants_all()
    print(f"   Total applicants: {len(all_applicants)}")
    
    print("\n4. APPLICANTS WITH RECRUITER FILTER:")
    nastya_applicants = await calc.applicants_all({"recruiters": "68691"})
    print(f"   Applicants for recruiter ID 68691: {len(nastya_applicants)}")
    
    print("\n5. CHECKING LOGS FOR АНАСТАСИЯ БОГАЧ:")
    from analyze_logs import LogAnalyzer
    analyzer = LogAnalyzer(client.db_path)
    all_logs = analyzer.get_merged_logs()
    
    # Find logs with Анастасия Богач
    nastya_logs = []
    for log in all_logs:
        account_info = log.get('account_info', {})
        if account_info.get('name') in ['Анастасия Богач', 'Настя Богач', 'Настя']:
            nastya_logs.append(log)
    
    print(f"   Total logs by Анастасия Богач: {len(nastya_logs)}")
    
    if nastya_logs:
        print("   Sample log entries:")
        for i, log in enumerate(nastya_logs[:3]):
            print(f"     Log {i+1}: {log.get('type')} - {log.get('status_name')} - {log.get('created', '')[:10]}")
    
    print("\n6. CHECKING HIRED APPLICANTS:")
    hired_applicants = analyzer.get_hired_applicants()
    print(f"   Total hired applicants: {len(hired_applicants)}")
    
    if hired_applicants:
        print("   Sample hired record:")
        for key, value in list(hired_applicants[0].items())[:5]:
            print(f"     {key}: {value}")
    
    print("\n7. RECRUITER ACTIVITY STATS:")
    recruiter_stats = analyzer.get_recruiter_activity()
    for name, stats in recruiter_stats.items():
        if 'Анастасия' in name or 'Настя' in name:
            print(f"   {name}: {stats}")

if __name__ == "__main__":
    asyncio.run(main())