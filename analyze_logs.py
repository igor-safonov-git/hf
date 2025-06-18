#!/usr/bin/env python3
"""
Comprehensive log analysis for Huntflow data.
Merges all applicant logs with applicant data for real metrics.
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime


class LogAnalyzer:
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
    
    def get_merged_logs(self) -> List[Dict[str, Any]]:
        """Get all logs merged with applicant and vacancy data."""
        sql = """
        SELECT 
            al.*,
            a.first_name,
            a.last_name,
            a.email,
            a.phone,
            v.position as vacancy_position,
            vs.name as status_name,
            vs.type as status_type
        FROM applicant_logs al
        LEFT JOIN applicants a ON al.applicant_id = a.id
        LEFT JOIN vacancies v ON al.vacancy_id = v.id
        LEFT JOIN vacancy_statuses vs ON al.status_id = vs.id
        ORDER BY al.created DESC
        """
        
        rows = self._query(sql)
        
        # Parse raw_data JSON for each log
        for row in rows:
            if row.get("raw_data"):
                try:
                    parsed_data = json.loads(row["raw_data"])
                    # Merge parsed data into row
                    row.update(parsed_data)
                except json.JSONDecodeError:
                    pass
        
        return rows
    
    def get_current_status_distribution(self) -> Dict[str, int]:
        """Get real current status distribution from logs."""
        sql = """
        WITH latest_status AS (
            SELECT 
                al.applicant_id,
                al.status_id,
                vs.name as status_name,
                vs.type as status_type,
                MAX(al.created) as last_update
            FROM applicant_logs al
            LEFT JOIN vacancy_statuses vs ON al.status_id = vs.id
            WHERE al.status_id IS NOT NULL
            GROUP BY al.applicant_id
        )
        SELECT 
            status_name,
            COUNT(*) as count
        FROM latest_status
        WHERE status_name IS NOT NULL
        GROUP BY status_name
        ORDER BY count DESC
        """
        
        results = self._query(sql)
        return {row["status_name"]: row["count"] for row in results}
    
    def get_recruiter_activity(self) -> Dict[str, Dict[str, Any]]:
        """Get comprehensive recruiter activity analysis."""
        logs = self.get_merged_logs()
        
        recruiter_stats = {}
        
        for log in logs:
            # Extract recruiter info from account_info
            account_info = log.get("account_info", {})
            if isinstance(account_info, dict):
                recruiter_name = account_info.get("name")
            else:
                recruiter_name = None
            
            if not recruiter_name:
                continue
            
            if recruiter_name not in recruiter_stats:
                recruiter_stats[recruiter_name] = {
                    "total_actions": 0,
                    "action_types": {},
                    "applicants_added": 0,
                    "status_changes": 0,
                    "unique_applicants": set(),
                    "unique_vacancies": set()
                }
            
            stats = recruiter_stats[recruiter_name]
            stats["total_actions"] += 1
            
            # Track action type
            action_type = log.get("type", "UNKNOWN")
            stats["action_types"][action_type] = stats["action_types"].get(action_type, 0) + 1
            
            # Track ADD actions (new applicants)
            if action_type == "ADD":
                stats["applicants_added"] += 1
            
            # Track status changes
            if log.get("status_id"):
                stats["status_changes"] += 1
            
            # Track unique applicants and vacancies
            if log.get("applicant_id"):
                stats["unique_applicants"].add(log["applicant_id"])
            if log.get("vacancy_id"):
                stats["unique_vacancies"].add(log["vacancy_id"])
        
        # Convert sets to counts
        for recruiter, stats in recruiter_stats.items():
            stats["unique_applicants"] = len(stats["unique_applicants"])
            stats["unique_vacancies"] = len(stats["unique_vacancies"])
        
        return recruiter_stats
    
    def get_applicant_sources(self) -> Dict[str, int]:
        """Get real applicant source distribution from logs."""
        # Look for source information in logs
        sql = """
        SELECT 
            json_extract(al.raw_data, '$.source.name') as source_name,
            COUNT(DISTINCT al.applicant_id) as count
        FROM applicant_logs al
        WHERE json_extract(al.raw_data, '$.source.name') IS NOT NULL
        GROUP BY source_name
        ORDER BY count DESC
        """
        
        results = self._query(sql)
        distribution = {row["source_name"]: row["count"] for row in results if row["source_name"]}
        
        # If no source data in logs, check applicants table
        if not distribution:
            applicant_sources_sql = """
            SELECT 
                json_extract(a.raw_data, '$.source.name') as source_name,
                COUNT(*) as count
            FROM applicants a
            WHERE json_extract(a.raw_data, '$.source.name') IS NOT NULL
            GROUP BY source_name
            ORDER BY count DESC
            """
            results = self._query(applicant_sources_sql)
            distribution = {row["source_name"]: row["count"] for row in results if row["source_name"]}
        
        return distribution
    
    def get_hired_applicants(self) -> List[Dict[str, Any]]:
        """Get all applicants who reached 'hired' status."""
        sql = """
        SELECT DISTINCT
            al.applicant_id,
            a.first_name,
            a.last_name,
            a.email,
            a.phone,
            vs.name as hired_status,
            al.created as hired_date,
            v.position as vacancy_position
        FROM applicant_logs al
        JOIN applicants a ON al.applicant_id = a.id
        LEFT JOIN vacancy_statuses vs ON al.status_id = vs.id
        LEFT JOIN vacancies v ON al.vacancy_id = v.id
        WHERE vs.type = 'hired'
        ORDER BY al.created DESC
        """
        
        return self._query(sql)
    
    def get_pipeline_progression(self) -> Dict[str, Any]:
        """Analyze how applicants move through the pipeline."""
        sql = """
        SELECT 
            al.applicant_id,
            al.vacancy_id,
            al.status_id,
            vs.name as status_name,
            vs.type as status_type,
            vs.order_number,
            al.created,
            json_extract(al.raw_data, '$.account_info.name') as recruiter_name
        FROM applicant_logs al
        LEFT JOIN vacancy_statuses vs ON al.status_id = vs.id
        WHERE al.status_id IS NOT NULL
        ORDER BY al.applicant_id, al.created
        """
        
        logs = self._query(sql)
        
        # Group by applicant to track progression
        applicant_progressions = {}
        for log in logs:
            applicant_id = log["applicant_id"]
            if applicant_id not in applicant_progressions:
                applicant_progressions[applicant_id] = []
            applicant_progressions[applicant_id].append(log)
        
        # Analyze progression patterns
        progression_stats = {
            "total_applicants_with_progression": len(applicant_progressions),
            "average_stages_per_applicant": 0,
            "common_progressions": {},
            "dropoff_points": {}
        }
        
        total_stages = 0
        for applicant_id, progression in applicant_progressions.items():
            total_stages += len(progression)
            
            # Track common progression patterns
            if len(progression) > 1:
                pattern = " -> ".join([stage["status_name"] for stage in progression if stage["status_name"]])
                progression_stats["common_progressions"][pattern] = progression_stats["common_progressions"].get(pattern, 0) + 1
            
            # Track final status (potential dropoff points)
            if progression:
                final_status = progression[-1]["status_name"]
                progression_stats["dropoff_points"][final_status] = progression_stats["dropoff_points"].get(final_status, 0) + 1
        
        if len(applicant_progressions) > 0:
            progression_stats["average_stages_per_applicant"] = total_stages / len(applicant_progressions)
        
        return progression_stats
    
    def print_summary(self):
        """Print comprehensive analysis summary."""
        print("=" * 60)
        print("COMPREHENSIVE LOG ANALYSIS")
        print("=" * 60)
        
        # Basic counts
        logs = self.get_merged_logs()
        print(f"Total logs: {len(logs)}")
        
        # Status distribution
        print("\n📊 CURRENT STATUS DISTRIBUTION:")
        print("-" * 40)
        status_dist = self.get_current_status_distribution()
        for status, count in status_dist.items():
            print(f"{status:30} {count:5}")
        
        # Recruiter activity
        print("\n👥 RECRUITER ACTIVITY:")
        print("-" * 40)
        recruiter_stats = self.get_recruiter_activity()
        for recruiter, stats in recruiter_stats.items():
            print(f"\n{recruiter}:")
            print(f"  Total actions: {stats['total_actions']}")
            print(f"  Applicants added: {stats['applicants_added']}")
            print(f"  Status changes: {stats['status_changes']}")
            print(f"  Unique applicants: {stats['unique_applicants']}")
            print(f"  Action breakdown: {stats['action_types']}")
        
        # Source distribution
        print("\n📍 APPLICANT SOURCES:")
        print("-" * 40)
        sources = self.get_applicant_sources()
        for source, count in sources.items():
            print(f"{source:30} {count:5}")
        
        # Hired applicants
        print("\n🎯 HIRED APPLICANTS:")
        print("-" * 40)
        hired = self.get_hired_applicants()
        print(f"Total hired: {len(hired)}")
        for applicant in hired[:5]:  # Show first 5
            name = f"{applicant['first_name']} {applicant['last_name']}"
            print(f"  {name} - {applicant['hired_status']} on {applicant['hired_date']}")
        
        # Pipeline progression
        print("\n🔄 PIPELINE PROGRESSION:")
        print("-" * 40)
        pipeline = self.get_pipeline_progression()
        print(f"Applicants with progression: {pipeline['total_applicants_with_progression']}")
        print(f"Average stages per applicant: {pipeline['average_stages_per_applicant']:.1f}")
        
        print("\nTop progression patterns:")
        for pattern, count in list(pipeline['common_progressions'].items())[:5]:
            print(f"  {pattern} ({count} times)")
        
        print("\nFinal status distribution:")
        for status, count in list(pipeline['dropoff_points'].items())[:5]:
            print(f"  {status}: {count}")


if __name__ == "__main__":
    analyzer = LogAnalyzer()
    analyzer.print_summary()