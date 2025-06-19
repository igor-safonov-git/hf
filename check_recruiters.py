#!/usr/bin/env python3
"""
Check recruiter data to see why they appear as "Unknown"
"""

import asyncio
from huntflow_local_client import HuntflowLocalClient
from enhanced_metrics_calculator import EnhancedMetricsCalculator

async def main():
    client = HuntflowLocalClient()
    calc = EnhancedMetricsCalculator(client, None)
    
    print("=== COWORKERS DATA ===")
    coworkers = await calc.recruiters_all()
    for i, coworker in enumerate(coworkers[:10]):
        print(f"{i+1}. {coworker}")
    
    print("\n=== APPLICANTS BY RECRUITER ===")
    applicants_by_recruiter = await calc.applicants_by_recruiter()
    for recruiter_name, count in applicants_by_recruiter.items():
        print(f"  {recruiter_name}: {count}")
    
    print("\n=== LOG ANALYSIS ===")
    from analyze_logs import LogAnalyzer
    analyzer = LogAnalyzer(client.db_path)
    logs = analyzer.get_merged_logs()[:5]  # First 5 logs
    
    for i, log in enumerate(logs):
        account_info = log.get('account_info', {})
        print(f"Log {i+1}: {account_info}")

if __name__ == "__main__":
    asyncio.run(main())