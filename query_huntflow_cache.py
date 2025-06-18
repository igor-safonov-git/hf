#!/usr/bin/env python3
"""
Query helper for the Huntflow cache database.
Provides easy access to cached data with common queries.
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional


class HuntflowCache:
    def __init__(self, db_path: str = "huntflow_cache.db"):
        self.db_path = db_path
    
    def _query(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute query and return results as list of dicts."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def get_vacancies(self) -> List[Dict[str, Any]]:
        """Get all vacancies with parsed data."""
        rows = self._query("SELECT * FROM vacancies")
        for row in rows:
            if row.get("raw_data"):
                row["data"] = json.loads(row["raw_data"])
                del row["raw_data"]
        return rows
    
    def get_applicants(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get applicants with parsed data."""
        sql = "SELECT * FROM applicants"
        if limit:
            sql += f" LIMIT {limit}"
        
        rows = self._query(sql)
        for row in rows:
            if row.get("raw_data"):
                row["data"] = json.loads(row["raw_data"])
                del row["raw_data"]
        return rows
    
    def get_applicant_with_logs(self, applicant_id: int) -> Dict[str, Any]:
        """Get applicant with their activity logs."""
        applicant = self._query("SELECT * FROM applicants WHERE id = ?", (applicant_id,))
        if not applicant:
            return None
        
        applicant = applicant[0]
        if applicant.get("raw_data"):
            applicant["data"] = json.loads(applicant["raw_data"])
            del applicant["raw_data"]
        
        # Get logs
        logs = self._query(
            "SELECT * FROM applicant_logs WHERE applicant_id = ? ORDER BY created DESC",
            (applicant_id,)
        )
        
        for log in logs:
            if log.get("raw_data"):
                log["data"] = json.loads(log["raw_data"])
                del log["raw_data"]
        
        applicant["logs"] = logs
        return applicant
    
    def get_vacancy_statuses(self) -> List[Dict[str, Any]]:
        """Get all vacancy statuses (recruitment stages)."""
        rows = self._query("SELECT * FROM vacancy_statuses ORDER BY order_number")
        for row in rows:
            if row.get("raw_data"):
                row["data"] = json.loads(row["raw_data"])
                del row["raw_data"]
        return rows
    
    def get_applicant_distribution_by_status(self) -> Dict[str, int]:
        """Get count of applicants by their current status."""
        # Get the latest status for each applicant from logs
        sql = """
        WITH latest_status AS (
            SELECT 
                applicant_id,
                status_id,
                MAX(created) as last_update
            FROM applicant_logs
            WHERE status_id IS NOT NULL
            GROUP BY applicant_id
        )
        SELECT 
            vs.name as status_name,
            COUNT(DISTINCT ls.applicant_id) as count
        FROM latest_status ls
        JOIN vacancy_statuses vs ON vs.id = ls.status_id
        GROUP BY vs.name
        ORDER BY COUNT(DISTINCT ls.applicant_id) DESC
        """
        
        results = self._query(sql)
        return {row["status_name"]: row["count"] for row in results}
    
    def get_applicants_by_vacancy(self, vacancy_id: int) -> List[Dict[str, Any]]:
        """Get all applicants for a specific vacancy."""
        sql = """
        SELECT DISTINCT a.*
        FROM applicants a
        JOIN applicant_logs al ON a.id = al.applicant_id
        WHERE al.vacancy_id = ?
        """
        
        rows = self._query(sql, (vacancy_id,))
        for row in rows:
            if row.get("raw_data"):
                row["data"] = json.loads(row["raw_data"])
                del row["raw_data"]
        return rows
    
    def search_applicants(self, query: str) -> List[Dict[str, Any]]:
        """Search applicants by name, email, or phone."""
        sql = """
        SELECT * FROM applicants
        WHERE first_name LIKE ? 
           OR last_name LIKE ?
           OR email LIKE ?
           OR phone LIKE ?
        LIMIT 100
        """
        
        search_term = f"%{query}%"
        rows = self._query(sql, (search_term, search_term, search_term, search_term))
        
        for row in rows:
            if row.get("raw_data"):
                row["data"] = json.loads(row["raw_data"])
                del row["raw_data"]
        return rows
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics of the cached data."""
        summary = {}
        
        tables = [
            "accounts", "vacancies", "applicants", "applicant_logs",
            "vacancy_statuses", "divisions", "regions", "coworkers",
            "rejection_reasons", "applicant_sources"
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            
            cursor.execute(
                "SELECT last_downloaded FROM download_meta WHERE entity_type = ?", 
                (table,)
            )
            result = cursor.fetchone()
            
            summary[table] = {
                "count": count,
                "last_downloaded": result[0] if result else None
            }
        
        conn.close()
        return summary
    
    def export_to_csv(self, table: str, output_file: str):
        """Export table to CSV file."""
        import csv
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table}")
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            if cursor.description:
                writer = csv.DictWriter(f, fieldnames=[d[0] for d in cursor.description])
                writer.writeheader()
                
                for row in cursor:
                    writer.writerow(dict(row))
        
        conn.close()
        print(f"Exported {table} to {output_file}")


# Example usage
if __name__ == "__main__":
    cache = HuntflowCache()
    
    print("Cache Summary:")
    print("-" * 50)
    summary = cache.get_summary()
    for table, info in summary.items():
        print(f"{table:20} {info['count']:8} records")
    
    print("\nApplicant Status Distribution:")
    print("-" * 50)
    distribution = cache.get_applicant_distribution_by_status()
    for status, count in distribution.items():
        print(f"{status:30} {count:8}")
    
    print("\nSample Vacancies:")
    print("-" * 50)
    vacancies = cache.get_vacancies()[:5]
    for v in vacancies:
        print(f"- {v.get('position', 'Unknown')} (ID: {v['id']})")