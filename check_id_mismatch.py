#!/usr/bin/env python3
"""
Check the ID mismatch between coworkers API and logs account_info
"""

import asyncio
from huntflow_local_client import HuntflowLocalClient
from enhanced_metrics_calculator import EnhancedMetricsCalculator

async def main():
    client = HuntflowLocalClient()
    calc = EnhancedMetricsCalculator(client, None)
    
    print("=== ID MISMATCH ANALYSIS ===")
    
    # Get coworkers data
    coworkers = await calc.recruiters_all()
    nastya_coworker = None
    for coworker in coworkers:
        if 'Анастасия Богач' in coworker.get('name', ''):
            nastya_coworker = coworker
            break
    
    if nastya_coworker:
        print(f"COWORKERS API - Анастасия Богач:")
        print(f"  ID: {nastya_coworker['id']}")
        print(f"  Name: {nastya_coworker['name']}")
        print(f"  Member: {nastya_coworker.get('member', 'N/A')}")
    
    # Get logs data
    from analyze_logs import LogAnalyzer
    analyzer = LogAnalyzer(client.db_path)
    all_logs = analyzer.get_merged_logs()
    
    nastya_log = None
    for log in all_logs:
        account_info = log.get('account_info', {})
        if account_info.get('name') == 'Анастасия Богач':
            nastya_log = log
            break
    
    if nastya_log:
        account_info = nastya_log['account_info']
        print(f"\nLOGS ACCOUNT_INFO - Анастасия Богач:")
        print(f"  ID: {account_info['id']}")
        print(f"  Name: {account_info['name']}")
    
    print(f"\n=== SOLUTION ===")
    print(f"The filter should use account_info.id ({account_info['id']}) not coworkers.id ({nastya_coworker['id']})")
    print(f"Or we need to map between these ID systems")

if __name__ == "__main__":
    asyncio.run(main())