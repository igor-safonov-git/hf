"""
Test LogAnalyzer directly
"""

from analyze_logs import LogAnalyzer

def test_log_analyzer():
    print("🔍 Testing LogAnalyzer source data")
    
    try:
        analyzer = LogAnalyzer("huntflow_cache.db")
        source_data = analyzer.get_applicant_sources()
        
        print(f"Source data: {source_data}")
        print(f"Type: {type(source_data)}")
        print(f"Length: {len(source_data) if source_data else 0}")
        
        if source_data:
            print("✅ LogAnalyzer has source data")
        else:
            print("❌ LogAnalyzer returns empty")
            
        # Try alternative - check if we have applicants table data for sources
        import sqlite3
        conn = sqlite3.connect("huntflow_cache.db")
        cursor = conn.cursor()
        
        # Check what source-related data we have
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"\nAvailable tables: {[t[0] for t in tables]}")
        
        # Check applicants table structure
        cursor.execute("PRAGMA table_info(applicants);")
        columns = cursor.fetchall()
        print(f"\nApplicants columns: {[col[1] for col in columns]}")
        
        # Check if we have source data in applicants
        cursor.execute("SELECT COUNT(*), json_extract(raw_data, '$.source') as source FROM applicants GROUP BY source LIMIT 10;")
        sources = cursor.fetchall()
        print(f"\nSource distribution from applicants: {sources}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_log_analyzer()