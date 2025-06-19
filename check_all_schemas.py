import sqlite3

conn = sqlite3.connect("huntflow_cache.db")
cursor = conn.cursor()

tables = ['applicants', 'applicant_logs', 'vacancy_statuses', 'accounts']

for table in tables:
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    print(f"\n{table.upper()} columns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")

conn.close()