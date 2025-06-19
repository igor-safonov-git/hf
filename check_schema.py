import sqlite3
conn = sqlite3.connect("huntflow_cache.db")
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(vacancies)")
columns = cursor.fetchall()
print("Vacancies columns:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")
conn.close()