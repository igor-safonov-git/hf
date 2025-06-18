from query_huntflow_cache import HuntflowCache

cache = HuntflowCache()

# Check status distribution
print("Status Distribution:")
dist = cache.get_applicant_distribution_by_status()
if dist:
    for status, count in dist.items():
        print(f"  {status}: {count}")
else:
    print("  No status data found")

# Check raw logs
logs = cache._query("SELECT COUNT(*) as total, COUNT(status_id) as with_status FROM applicant_logs")
print(f"\nLogs: {logs[0]['total']} total, {logs[0]['with_status']} with status")

# Look for logs with status changes
status_logs = cache._query("""
    SELECT applicant_id, raw_data 
    FROM applicant_logs 
    WHERE raw_data LIKE '%"status":{%' 
    LIMIT 5
""")
print(f"\nFound {len(status_logs)} logs with status data")
print("\nSample logs with status:")
for log in status_logs:
    import json
    try:
        data = json.loads(log['raw_data'])
        print(f"\n  Applicant {log['applicant_id']}:")
        print(f"    Type: {data.get('type', 'N/A')}")
        print(f"    Status: {data.get('status', 'N/A')}")
        print(f"    Vacancy: {data.get('vacancy', 'N/A')}")
        print(f"    Keys: {list(data.keys())}")
    except:
        print(f"  Failed to parse log for applicant {log['applicant_id']}")