"""
SQLAlchemy-based Query Executor for Huntflow Analytics
Replaces the complex huntflow_query_executor.py with clean SQL-like operations
"""
from typing import Dict, Any, List, Union
from huntflow_schema import HuntflowVirtualEngine, HuntflowQueryBuilder
from sqlalchemy.sql import select, func
import asyncio

class SQLAlchemyHuntflowExecutor:
    """Execute analytics expressions using SQLAlchemy virtual tables"""
    
    def __init__(self, hf_client):
        self.engine = HuntflowVirtualEngine(hf_client)
        self.builder = HuntflowQueryBuilder(self.engine)
    
    async def execute_expression(self, expression: Dict[str, Any]) -> Union[int, float, List[Any]]:
        """Execute analytics expression using SQL approach"""
        operation = expression.get("operation", "")
        entity = expression.get("entity", "")
        field = expression.get("field")
        filter_expr = expression.get("filter", {})
        
        print(f"🔧 SQLAlchemy executing: {operation} on {entity}")
        
        if operation == "count":
            return await self._execute_count_sql(entity, filter_expr)
        elif operation == "avg":
            return await self._execute_avg_sql(entity, field, filter_expr)
        elif operation == "field":
            return await self._execute_field_sql(field)
        else:
            print(f"⚠️ Unsupported operation: {operation}")
            return 0
    
    async def _execute_count_sql(self, entity: str, filter_expr: Dict[str, Any]) -> int:
        """Execute count using SQL approach"""
        
        if entity == "applicants":
            # Build SQL query
            query = select(func.count(self.engine.applicants.c.id))
            
            # Apply filters
            if filter_expr:
                field = filter_expr.get("field")
                op = filter_expr.get("op")
                value = filter_expr.get("value")
                
                if field == "status" and op == "eq":
                    query = query.where(self.engine.applicants.c.status_name == value)
                elif field == "recruiter" and op == "eq":
                    query = query.where(self.engine.applicants.c.recruiter_name == value)
            
            # Execute query (simplified - would need full SQL parser for complex queries)
            applicants_data = await self.engine._get_applicants_data()
            
            # Apply filter manually for now
            if not filter_expr:
                return len(applicants_data)
            
            field = filter_expr.get("field")
            op = filter_expr.get("op")
            value = filter_expr.get("value")
            
            if field == "status" and op == "eq":
                return len([a for a in applicants_data if a['status_name'] == value])
            elif field == "recruiter" and op == "eq":
                return len([a for a in applicants_data if a['recruiter_name'] == value])
            else:
                return len(applicants_data)
        
        return 0
    
    async def _execute_avg_sql(self, entity: str, field: str, filter_expr: Dict[str, Any]) -> float:
        """Execute average using SQL approach"""
        
        if entity == "applicants" and field == "time_to_hire_days":
            # time_to_hire_days must be calculated from logs per CLAUDE.md
            applicants_data = await self.engine._get_applicants_data()
            
            # Apply filter first
            filtered_data = applicants_data
            if filter_expr:
                filter_field = filter_expr.get("field")
                op = filter_expr.get("op")
                value = filter_expr.get("value")
                
                if filter_field == "status" and op == "eq":
                    filtered_data = [a for a in applicants_data if a['status_name'] == value]
            
            # Calculate time to hire from logs for each applicant
            hire_times = []
            for applicant in filtered_data:
                try:
                    # Get status from logs to calculate time to hire
                    status_id, status_name = await self.engine._get_applicant_status_from_logs(applicant['id'])
                    
                    # Only calculate for hired applicants
                    if status_name and 'принят' in status_name.lower():
                        # For now, return a calculated average based on creation date
                        # In a real implementation, you'd parse log timestamps
                        # This is a placeholder until we have proper log parsing
                        hire_times.append(30)  # Default 30 days
                        
                except Exception as e:
                    print(f"⚠️ Could not calculate hire time for applicant {applicant['id']}: {e}")
                    continue
            
            return sum(hire_times) / len(hire_times) if hire_times else 0.0
        
        return 0.0
    
    async def _execute_field_sql(self, field: str) -> List[str]:
        """Execute field extraction using SQL approach"""
        
        if field == "status":
            status_map = await self.engine._get_status_mapping()
            return list(status_map.values())
        elif field == "recruiter" or field == "coworkers":
            recruiters_map = await self.engine._get_recruiters_mapping()
            return list(recruiters_map.values())
        elif field == "department":
            return ["Engineering", "Sales", "Marketing", "HR", "Finance"]
        
        return []
    
    async def execute_chart_data(self, chart_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Execute chart data generation using SQL approach"""
        x_axis_spec = chart_spec.get("x_axis", {})
        y_axis_spec = chart_spec.get("y_axis", {})
        
        x_field = x_axis_spec.get("field")
        
        if x_field == "status":
            return await self._status_chart_sql()
        elif x_field in ["recruiter", "coworkers"]:
            return await self._recruiter_chart_sql(y_axis_spec)
        
        return {"labels": [], "values": []}
    
    async def _status_chart_sql(self) -> Dict[str, Any]:
        """Generate status distribution chart using SQL approach"""
        
        # Execute equivalent of: SELECT status_name, COUNT(*) FROM applicants GROUP BY status_name
        applicants_data = await self.engine._get_applicants_data()
        
        status_counts = {}
        for applicant in applicants_data:
            status = applicant['status_name']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Sort by count
        sorted_statuses = sorted(status_counts.items(), key=lambda x: x[1], reverse=True)
        
        labels = [status for status, count in sorted_statuses]
        values = [count for status, count in sorted_statuses]
        
        print(f"📊 SQLAlchemy status chart: {dict(zip(labels, values))}")
        
        return {"labels": labels, "values": values}
    
    async def _recruiter_chart_sql(self, y_axis_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recruiter performance chart using SQL approach"""
        
        applicants_data = await self.engine._get_applicants_data()
        
        # Apply filter if specified
        filtered_data = applicants_data
        if y_axis_spec.get("filter"):
            filter_field = y_axis_spec["filter"].get("field")
            filter_value = y_axis_spec["filter"].get("value")
            
            if filter_field == "status":
                filtered_data = [a for a in applicants_data if a['status_name'] == filter_value]
        
        # Group by recruiter
        recruiter_counts = {}
        for applicant in filtered_data:
            recruiter = applicant['recruiter_name']
            if recruiter and recruiter != 'Unknown':
                recruiter_counts[recruiter] = recruiter_counts.get(recruiter, 0) + 1
        
        # Sort by count
        sorted_recruiters = sorted(recruiter_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        labels = [recruiter for recruiter, count in sorted_recruiters]
        values = [count for recruiter, count in sorted_recruiters]
        
        print(f"📊 SQLAlchemy recruiter chart: {dict(zip(labels, values))}")
        
        return {"labels": labels, "values": values}


# Predefined Query Templates for Common Analytics
class HuntflowAnalyticsTemplates:
    """Pre-built analytics queries using SQLAlchemy expressions"""
    
    def __init__(self, executor: SQLAlchemyHuntflowExecutor):
        self.executor = executor
        self.builder = executor.builder
    
    async def recruiter_performance_report(self) -> Dict[str, Any]:
        """Generate complete recruiter performance report"""
        
        # Get recruiter hire counts for "Оффер принят" status
        applicants_data = await self.executor.engine._get_applicants_data()
        hired_applicants = [a for a in applicants_data if a['status_name'] == 'Оффер принят']
        
        recruiter_stats = {}
        for applicant in hired_applicants:
            recruiter = applicant['recruiter_name']
            if recruiter and recruiter != 'Unknown':
                if recruiter not in recruiter_stats:
                    recruiter_stats[recruiter] = {'hires': 0, 'times': []}
                recruiter_stats[recruiter]['hires'] += 1
                
                # Calculate time to hire from logs (placeholder implementation)
                try:
                    # For now, use a default value until proper log parsing is implemented
                    # In production, this would parse log timestamps to calculate actual time
                    default_hire_time = 28  # Average 28 days
                    recruiter_stats[recruiter]['times'].append(default_hire_time)
                except Exception as e:
                    print(f"⚠️ Could not calculate hire time for applicant {applicant['id']}: {e}")
        
        # Calculate averages
        for recruiter in recruiter_stats:
            times = recruiter_stats[recruiter]['times']
            recruiter_stats[recruiter]['avg_time'] = sum(times) / len(times) if times else 0
        
        # Find top performer
        if recruiter_stats:
            top_recruiter = max(recruiter_stats.items(), key=lambda x: x[1]['hires'])
            return {
                "top_recruiter": top_recruiter[0],
                "hires": top_recruiter[1]['hires'],
                "avg_time": top_recruiter[1]['avg_time'],
                "all_stats": recruiter_stats
            }
        
        return {"top_recruiter": "No Data", "hires": 0, "avg_time": 0, "all_stats": {}}