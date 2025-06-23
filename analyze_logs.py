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
    
    def get_applicant_source_mapping(self) -> Dict[int, Dict[str, Any]]:
        """Get comprehensive applicant-source mapping from ADD logs."""
        sql = """
        SELECT 
            al.applicant_id,
            json_extract(al.raw_data, '$.source') as source_id,
            json_extract(al.raw_data, '$.type') as log_type,
            s.name as source_name
        FROM applicant_logs al
        LEFT JOIN applicant_sources s ON json_extract(al.raw_data, '$.source') = s.id
        WHERE json_extract(al.raw_data, '$.type') = 'ADD'
        """
        
        add_logs = self._query(sql)
        applicant_source_map = {}
        
        for log in add_logs:
            applicant_id = log['applicant_id']
            source_id = log.get('source_id')
            
            if applicant_id and source_id:
                applicant_source_map[applicant_id] = {
                    'source_id': source_id,
                    'source_name': log.get('source_name', f'Source {source_id}')
                }
        
        return applicant_source_map
    
    def get_applicant_sources(self) -> Dict[str, int]:
        """Get real applicant source distribution from logs with proper source mapping."""
        # Get source mapping first
        source_map_sql = """
        SELECT id, name FROM applicant_sources
        """
        source_mapping = self._query(source_map_sql)
        source_map = {str(row["id"]): row["name"] for row in source_mapping}
        
        # Look for source information in logs using numeric source IDs
        sql = """
        SELECT 
            json_extract(al.raw_data, '$.source') as source_id,
            COUNT(DISTINCT al.applicant_id) as count
        FROM applicant_logs al
        WHERE json_extract(al.raw_data, '$.source') IS NOT NULL
            AND json_extract(al.raw_data, '$.source') != 'null'
        GROUP BY source_id
        ORDER BY count DESC
        """
        
        results = self._query(sql)
        distribution = {}
        
        for row in results:
            source_id = str(row["source_id"]) if row["source_id"] else None
            if source_id and source_id in source_map:
                source_name = source_map[source_id]
                distribution[source_name] = row["count"]
        
        # If still no data, try different approach - look in merged logs
        if not distribution:
            merged_logs = self.get_merged_logs()
            source_counts = {}
            
            for log in merged_logs:
                if log.get('source'):
                    source_id = str(log['source'])
                    source_name = source_map.get(source_id, f'Source {source_id}')
                    source_counts[source_name] = source_counts.get(source_name, 0) + 1
            
            if source_counts:
                return source_counts
        
        return distribution
    
    def get_hired_applicants(self) -> List[Dict[str, Any]]:
        """Get all applicants who reached 'hired' status with time_to_hire calculation."""
        sql = """
        SELECT DISTINCT
            al.applicant_id,
            a.first_name,
            a.last_name,
            a.email,
            a.phone,
            vs.name as hired_status,
            al.created as hired_date,
            al.vacancy_id,
            v.position as vacancy_position,
            al.raw_data
        FROM applicant_logs al
        JOIN applicants a ON al.applicant_id = a.id
        LEFT JOIN vacancy_statuses vs ON al.status_id = vs.id
        LEFT JOIN vacancies v ON al.vacancy_id = v.id
        WHERE vs.type = 'hired'
        ORDER BY al.created DESC
        """
        
        hired_applicants = self._query(sql)
        
        # Extract recruiter information from raw_data and add to each hire record
        for applicant in hired_applicants:
            if applicant.get("raw_data"):
                try:
                    parsed_data = json.loads(applicant["raw_data"])
                    account_info = parsed_data.get("account_info", {})
                    if isinstance(account_info, dict):
                        applicant["recruiter_id"] = account_info.get("id")
                        applicant["recruiter_name"] = account_info.get("name")
                except json.JSONDecodeError:
                    # If parsing fails, set default values
                    applicant["recruiter_id"] = None
                    applicant["recruiter_name"] = None
            else:
                applicant["recruiter_id"] = None
                applicant["recruiter_name"] = None
        
        # Get applicant-source mapping once for all hired applicants
        applicant_source_map = self.get_applicant_source_mapping()
        
        # Add source information to each hired applicant
        for applicant in hired_applicants:
            applicant_id = applicant['applicant_id']
            
            if applicant_id in applicant_source_map:
                source_info = applicant_source_map[applicant_id]
                applicant["source_id"] = source_info['source_id']
                applicant["source_name"] = source_info['source_name']
                
                # Also add source as dict for compatibility
                applicant["source"] = {
                    "id": source_info['source_id'],
                    "name": source_info['source_name']
                }
            else:
                applicant["source_id"] = None
                applicant["source_name"] = None
                applicant["source"] = None
        
        # Add stage information from the hire status
        for applicant in hired_applicants:
            # The hired status ID is the stage they were hired at
            if applicant.get('raw_data'):
                try:
                    parsed_data = json.loads(applicant['raw_data'])
                    status_id = parsed_data.get('status')
                    if status_id:
                        applicant["stage_id"] = status_id
                        
                        # Get stage name from vacancy_statuses
                        stage_sql = "SELECT name FROM vacancy_statuses WHERE id = ?"
                        stage_result = self._query(stage_sql, (status_id,))
                        if stage_result:
                            applicant["stage_name"] = stage_result[0].get('name', f'Stage {status_id}')
                        else:
                            applicant["stage_name"] = f'Stage {status_id}'
                    else:
                        applicant["stage_id"] = None
                        applicant["stage_name"] = None
                except:
                    applicant["stage_id"] = None
                    applicant["stage_name"] = None
            else:
                applicant["stage_id"] = None
                applicant["stage_name"] = None
        
        # Add division and hiring manager info from vacancy
        vacancy_division_map = {}
        for applicant in hired_applicants:
            vacancy_id = applicant.get('vacancy_id')
            
            if vacancy_id and vacancy_id not in vacancy_division_map:
                # Get vacancy details
                vacancy_sql = """
                SELECT raw_data FROM vacancies WHERE id = ?
                """
                vacancy_result = self._query(vacancy_sql, (vacancy_id,))
                
                if vacancy_result and vacancy_result[0].get('raw_data'):
                    try:
                        vacancy_data = json.loads(vacancy_result[0]['raw_data'])
                        division_id = vacancy_data.get('account_division')
                        
                        vacancy_info = {
                            'division_id': division_id,
                            'division_name': None,
                            'hiring_manager_id': None,
                            'hiring_manager_name': None
                        }
                        
                        # Get division name
                        if division_id:
                            div_sql = "SELECT name FROM divisions WHERE id = ?"
                            div_result = self._query(div_sql, (division_id,))
                            if div_result:
                                vacancy_info['division_name'] = div_result[0].get('name')
                        
                        # Get hiring manager from coworkers
                        coworkers = vacancy_data.get('coworkers', [])
                        if coworkers and isinstance(coworkers, list):
                            # First coworker is usually the hiring manager
                            hiring_manager_id = coworkers[0] if coworkers else None
                            if hiring_manager_id:
                                vacancy_info['hiring_manager_id'] = hiring_manager_id
                                
                                # Get manager name
                                mgr_sql = "SELECT name FROM coworkers WHERE id = ?"
                                mgr_result = self._query(mgr_sql, (hiring_manager_id,))
                                if mgr_result:
                                    vacancy_info['hiring_manager_name'] = mgr_result[0].get('name')
                        
                        vacancy_division_map[vacancy_id] = vacancy_info
                    except:
                        vacancy_division_map[vacancy_id] = None
                else:
                    vacancy_division_map[vacancy_id] = None
            
            # Apply division and hiring manager info to applicant
            if vacancy_id and vacancy_id in vacancy_division_map and vacancy_division_map[vacancy_id]:
                info = vacancy_division_map[vacancy_id]
                applicant["division_id"] = info['division_id']
                applicant["division_name"] = info['division_name']
                applicant["hiring_manager_id"] = info['hiring_manager_id']
                applicant["hiring_manager_name"] = info['hiring_manager_name']
            else:
                applicant["division_id"] = None
                applicant["division_name"] = None
                applicant["hiring_manager_id"] = None
                applicant["hiring_manager_name"] = None
        
        # Calculate time_to_hire for each hired applicant
        for applicant in hired_applicants:
            try:
                applicant_id = applicant['applicant_id']
                hired_date = applicant['hired_date']
                
                # Get the earliest log entry for this applicant (when they were first added)
                first_log_sql = """
                SELECT MIN(created) as first_activity
                FROM applicant_logs
                WHERE applicant_id = ?
                """
                first_activity = self._query(first_log_sql, (applicant_id,))
                
                if first_activity and first_activity[0]['first_activity'] and hired_date:
                    # Parse dates and calculate difference in days
                    from datetime import datetime
                    
                    # Handle different date formats
                    def parse_date(date_str):
                        if 'T' in date_str:
                            return datetime.fromisoformat(date_str.replace('Z', '+00:00')).replace(tzinfo=None)
                        else:
                            return datetime.strptime(date_str, '%Y-%m-%d')
                    
                    try:
                        hired_dt = parse_date(hired_date)
                        first_dt = parse_date(first_activity[0]['first_activity'])
                        
                        # Calculate difference in days
                        time_diff = hired_dt - first_dt
                        time_to_hire_days = max(0, time_diff.days)  # Ensure non-negative
                        
                        applicant['time_to_hire'] = time_to_hire_days
                        applicant['time_to_hire_hours'] = max(0, time_diff.total_seconds() / 3600)
                        
                    except (ValueError, TypeError) as e:
                        # If date parsing fails, set default values
                        applicant['time_to_hire'] = 0
                        applicant['time_to_hire_hours'] = 0
                else:
                    # No first activity found or dates are None
                    applicant['time_to_hire'] = 0
                    applicant['time_to_hire_hours'] = 0
                    
            except Exception as e:
                # If any error occurs, set default values
                applicant['time_to_hire'] = 0
                applicant['time_to_hire_hours'] = 0
        
        return hired_applicants
    
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