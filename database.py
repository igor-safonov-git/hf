"""
Direct SQLite database interface for Huntflow cache.
Provides simple query methods without API endpoint simulation.
"""

import sqlite3
import json
from typing import Dict, List, Any, Optional
from contextlib import contextmanager


class HuntflowDB:
    def __init__(self, db_path: str = "huntflow_cache.db"):
        self.db_path = db_path
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with proper cleanup."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def query(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a query and return results as list of dicts."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            results = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                # Parse raw_data JSON if present
                if 'raw_data' in row_dict and row_dict['raw_data']:
                    try:
                        parsed = json.loads(row_dict['raw_data'])
                        row_dict.update(parsed)
                        del row_dict['raw_data']
                    except json.JSONDecodeError:
                        pass
                results.append(row_dict)
            return results
    
    def query_one(self, sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Execute a query and return first result or None."""
        results = self.query(sql, params)
        return results[0] if results else None
    
    def count(self, table: str, where: str = "", params: tuple = ()) -> int:
        """Count rows in a table with optional WHERE clause."""
        sql = f"SELECT COUNT(*) as count FROM {table}"
        if where:
            sql += f" WHERE {where}"
        result = self.query_one(sql, params)
        return result['count'] if result else 0
    
    # Direct table access methods
    
    def get_vacancies(self, state: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get vacancies, optionally filtered by state."""
        if state:
            return self.query("SELECT * FROM vacancies WHERE state = ?", (state,))
        return self.query("SELECT * FROM vacancies")
    
    def get_applicants(self, limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """Get applicants with pagination."""
        sql = "SELECT * FROM applicants"
        if limit:
            sql += f" LIMIT {limit} OFFSET {offset}"
        return self.query(sql)
    
    def get_vacancy_statuses(self) -> List[Dict[str, Any]]:
        """Get all vacancy statuses ordered by order_number."""
        return self.query("SELECT * FROM vacancy_statuses ORDER BY order_number")
    
    def get_coworkers(self) -> List[Dict[str, Any]]:
        """Get all coworkers."""
        return self.query("SELECT * FROM coworkers")
    
    def get_sources(self) -> List[Dict[str, Any]]:
        """Get all applicant sources."""
        return self.query("SELECT * FROM applicant_sources")
    
    def get_applicant_logs(self, applicant_id: int) -> List[Dict[str, Any]]:
        """Get logs for a specific applicant."""
        return self.query(
            "SELECT * FROM applicant_logs WHERE applicant_id = ? ORDER BY created DESC",
            (applicant_id,)
        )
    
    def get_vacancy_distribution(self) -> Dict[str, int]:
        """Get count of vacancies by state."""
        results = self.query("""
            SELECT state, COUNT(*) as count 
            FROM vacancies 
            GROUP BY state
        """)
        return {r['state']: r['count'] for r in results}
    
    def get_applicant_status_distribution(self) -> Dict[str, int]:
        """Get distribution of applicants by their current status."""
        # Since we don't have proper status data in logs, return empty
        # In a real implementation, this would join with applicant_logs
        return {}
    
    def get_top_recruiters(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top recruiters. Since we don't have hiring data, return coworkers."""
        return self.query(f"SELECT * FROM coworkers LIMIT {limit}")
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get counts for all major tables."""
        tables = ['vacancies', 'applicants', 'vacancy_statuses', 'coworkers', 
                  'divisions', 'regions', 'rejection_reasons', 'applicant_sources']
        stats = {}
        for table in tables:
            stats[table] = self.count(table)
        return stats