from query_huntflow_cache import HuntflowCache
import json
from collections import Counter

cache = HuntflowCache()

# Get all logs
all_logs = cache._query("SELECT raw_data FROM applicant_logs")

# Analyze log types
log_types = Counter()
logs_with_status = 0
logs_with_vacancy = 0

for log in all_logs:
    try:
        data = json.loads(log['raw_data'])
        log_types[data.get('type', 'UNKNOWN')] += 1
        
        if data.get('status') and isinstance(data['status'], dict):
            logs_with_status += 1
        
        if data.get('vacancy') and isinstance(data['vacancy'], dict):
            logs_with_vacancy += 1
            
    except:
        log_types['PARSE_ERROR'] += 1

print("Log Type Distribution:")
for log_type, count in log_types.most_common():
    print(f"  {log_type}: {count}")

print(f"\nLogs with status dict: {logs_with_status}")
print(f"Logs with vacancy dict: {logs_with_vacancy}")

# Check if we need to look at a different table
print("\n\nChecking applicant_links table:")
links = cache._query("SELECT COUNT(*) as count FROM sqlite_master WHERE type='table' AND name='applicant_links'")
if links[0]['count'] > 0:
    print("applicant_links table exists")
    link_count = cache._query("SELECT COUNT(*) as count FROM applicant_links")
    print(f"Total links: {link_count[0]['count']}")
else:
    print("No applicant_links table found")