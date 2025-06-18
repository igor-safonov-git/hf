"""
Local Huntflow client that queries SQLite cache instead of API.
Provides the same interface as HuntflowClient but uses local data.
"""

import json
import sqlite3
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime


class HuntflowLocalClient:
    def __init__(self, db_path: str = "huntflow_cache.db"):
        self.db_path = db_path
        self.account_id = self._get_account_id()
    
    def _get_account_id(self) -> str:
        """Get the account ID from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM accounts LIMIT 1")
        result = cursor.fetchone()
        conn.close()
        return str(result[0]) if result else "55477"
    
    def _query(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute query and return results as list of dicts."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql, params)
        results = []
        for row in cursor.fetchall():
            row_dict = dict(row)
            # Parse raw_data JSON if it exists
            if 'raw_data' in row_dict and row_dict['raw_data']:
                try:
                    parsed = json.loads(row_dict['raw_data'])
                    # Merge parsed data with row data
                    row_dict.update(parsed)
                    del row_dict['raw_data']
                except json.JSONDecodeError:
                    pass
            results.append(row_dict)
        conn.close()
        return results
    
    async def _req(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Simulate API request by querying local database.
        Maps API endpoints to database queries.
        """
        # Remove /v2 prefix if present
        endpoint = endpoint.replace("/v2", "")
        
        # Handle different endpoints
        if endpoint == "/accounts":
            results = self._query("SELECT * FROM accounts")
            return {"items": results}
        
        elif endpoint == f"/accounts/{self.account_id}/vacancies":
            # Handle pagination
            params = kwargs.get("params", {})
            page = params.get("page", 1)
            count = params.get("count", 100)
            offset = (page - 1) * count
            
            results = self._query(
                "SELECT * FROM vacancies LIMIT ? OFFSET ?",
                (count, offset)
            )
            return {"items": results}
        
        elif endpoint == f"/accounts/{self.account_id}/vacancies/statuses":
            results = self._query("SELECT * FROM vacancy_statuses ORDER BY order_number")
            return {"items": results}
        
        elif endpoint == f"/accounts/{self.account_id}/applicants/search":
            # Handle pagination
            params = kwargs.get("params", {})
            page = params.get("page", 1)
            count = params.get("count", 100)
            offset = (page - 1) * count
            
            # Build query based on filters
            where_clauses = []
            query_params = []
            
            if params.get("vacancy"):
                # Need to join with logs to filter by vacancy
                sql = """
                    SELECT DISTINCT a.* 
                    FROM applicants a
                    JOIN applicant_logs al ON a.id = al.applicant_id
                    WHERE al.vacancy_id = ?
                    LIMIT ? OFFSET ?
                """
                query_params = [params["vacancy"], count, offset]
            else:
                sql = "SELECT * FROM applicants LIMIT ? OFFSET ?"
                query_params = [count, offset]
            
            results = self._query(sql, tuple(query_params))
            return {"items": results}
        
        elif "/applicants/" in endpoint and "/logs" in endpoint:
            # Extract applicant ID from endpoint
            parts = endpoint.split("/")
            applicant_id = None
            for i, part in enumerate(parts):
                if part == "applicants" and i + 1 < len(parts):
                    applicant_id = parts[i + 1]
                    break
            
            if applicant_id:
                results = self._query(
                    """
                    SELECT al.*, vs.name as status_name, v.position as vacancy_position
                    FROM applicant_logs al
                    LEFT JOIN vacancy_statuses vs ON al.status_id = vs.id
                    LEFT JOIN vacancies v ON al.vacancy_id = v.id
                    WHERE al.applicant_id = ?
                    ORDER BY al.created DESC
                    """,
                    (applicant_id,)
                )
                
                # Format results to match API structure
                items = []
                for r in results:
                    item = {
                        "id": r.get("id"),
                        "created": r.get("created"),
                        "type": "STATUS",
                        "employment_date": None
                    }
                    
                    # Add status info if available
                    if r.get("status_id"):
                        item["status"] = {
                            "id": r.get("status_id"),
                            "name": r.get("status_name", "Unknown")
                        }
                    
                    # Add vacancy info if available
                    if r.get("vacancy_id"):
                        item["vacancy"] = {
                            "id": r.get("vacancy_id"),
                            "position": r.get("vacancy_position", "Unknown")
                        }
                    
                    items.append(item)
                
                return {"items": items}
            
            return {"items": []}
        
        elif endpoint == f"/accounts/{self.account_id}/divisions":
            results = self._query("SELECT * FROM divisions")
            return {"items": results}
        
        elif endpoint == f"/accounts/{self.account_id}/coworkers":
            results = self._query("SELECT * FROM coworkers")
            return {"items": results}
        
        elif endpoint == f"/accounts/{self.account_id}/rejection_reasons":
            results = self._query("SELECT * FROM rejection_reasons")
            return {"items": results}
        
        elif endpoint == f"/accounts/{self.account_id}/applicants/sources":
            results = self._query("SELECT * FROM applicant_sources")
            return {"items": results}
        
        elif "recruiters" in endpoint:
            # Virtual recruiters entity - generate from coworkers
            coworkers = self._query("SELECT * FROM coworkers")
            recruiters = []
            for coworker in coworkers:
                # Simulate recruiter metrics
                recruiters.append({
                    "id": coworker.get("id"),
                    "name": coworker.get("name", "Unknown"),
                    "email": coworker.get("email"),
                    "hirings": 0,  # We don't have actual hiring data
                    "active_candidates": 0,
                    "avg_time_to_hire": 0
                })
            return {"items": recruiters}
        
        else:
            # Default: return empty items
            return {"items": []}
    
    async def get_vacancy_statuses(self) -> List[Dict[str, Any]]:
        """Get all vacancy statuses from local cache."""
        response = await self._req("GET", f"/v2/accounts/{self.account_id}/vacancies/statuses")
        return response.get("items", [])
    
    async def get_applicants_count(self, vacancy_id: Optional[int] = None) -> int:
        """Get count of applicants, optionally filtered by vacancy."""
        if vacancy_id:
            result = self._query(
                """
                SELECT COUNT(DISTINCT a.id) as count
                FROM applicants a
                JOIN applicant_logs al ON a.id = al.applicant_id
                WHERE al.vacancy_id = ?
                """,
                (vacancy_id,)
            )
        else:
            result = self._query("SELECT COUNT(*) as count FROM applicants")
        
        return result[0]["count"] if result else 0
    
    async def get_status_distribution(self, vacancy_id: Optional[int] = None) -> Dict[str, int]:
        """Get distribution of applicants by their current status."""
        if vacancy_id:
            sql = """
            WITH latest_status AS (
                SELECT 
                    al.applicant_id,
                    al.status_id,
                    MAX(al.created) as last_update
                FROM applicant_logs al
                WHERE al.vacancy_id = ? AND al.status_id IS NOT NULL
                GROUP BY al.applicant_id
            )
            SELECT 
                vs.name as status_name,
                COUNT(ls.applicant_id) as count
            FROM latest_status ls
            JOIN vacancy_statuses vs ON vs.id = ls.status_id
            GROUP BY vs.name
            ORDER BY count DESC
            """
            results = self._query(sql, (vacancy_id,))
        else:
            sql = """
            WITH latest_status AS (
                SELECT 
                    al.applicant_id,
                    al.status_id,
                    MAX(al.created) as last_update
                FROM applicant_logs al
                WHERE al.status_id IS NOT NULL
                GROUP BY al.applicant_id
            )
            SELECT 
                vs.name as status_name,
                COUNT(ls.applicant_id) as count
            FROM latest_status ls
            JOIN vacancy_statuses vs ON vs.id = ls.status_id
            GROUP BY vs.name
            ORDER BY count DESC
            """
            results = self._query(sql)
        
        return {row["status_name"]: row["count"] for row in results if row["status_name"]}