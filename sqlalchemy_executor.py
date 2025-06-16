"""
SQLAlchemy-based Query Executor for Huntflow Analytics
Replaces the complex huntflow_query_executor.py with clean SQL-like operations
"""
from typing import Dict, Any, List, Union
from virtual_engine import HuntflowVirtualEngine, HuntflowQueryBuilder
from huntflow_metrics import HuntflowComputedMetrics, HuntflowMetricsHelper
from sqlalchemy.sql import select, func
import asyncio

class SQLAlchemyHuntflowExecutor:
    """Execute analytics expressions using SQLAlchemy virtual tables"""
    
    def __init__(self, hf_client):
        self.engine = HuntflowVirtualEngine(hf_client)
        self.builder = HuntflowQueryBuilder(self.engine)
        self.metrics = HuntflowComputedMetrics(self.engine)
        self.metrics_helper = HuntflowMetricsHelper(self)
    
    async def execute_expression(self, expression: Dict[str, Any]) -> Union[int, float, List[Any]]:
        """Execute analytics expression using SQL approach"""
        operation = expression.get("operation", "")
        entity = expression.get("entity", "")
        field = expression.get("field")
        filter_expr = expression.get("filter", {})
        
        print(f"🔧 SQLAlchemy executing: {operation} on {entity}")
        
        # Check if this is a computed metric entity
        if entity in ["active_candidates", "open_vacancies", "closed_vacancies", "get_recruiters", "active_statuses"]:
            return await self._execute_computed_metric(entity, operation)
        
        if operation == "count":
            return await self._execute_count_sql(entity, filter_expr)
        elif operation == "avg":
            return await self._execute_avg_sql(entity, field, filter_expr)
        elif operation == "field":
            return await self._execute_field_sql(field)
        else:
            print(f"⚠️ Unsupported operation: {operation}")
            return 0
    
    async def _execute_computed_metric(self, entity: str, operation: str) -> Union[int, float, List[Any]]:
        """Execute computed metric as virtual entity"""
        if operation == "count":
            if entity == "active_candidates":
                return await self.metrics.active_candidates()
            elif entity == "open_vacancies":
                return await self.metrics.open_vacancies()
            elif entity == "closed_vacancies":
                return await self.metrics.closed_vacancies()
            elif entity == "get_recruiters":
                recruiters = await self.metrics.get_recruiters()
                return len(recruiters)
            elif entity == "active_statuses":
                statuses = await self.metrics.active_statuses()
                return len(statuses)
        elif operation == "field":
            if entity == "get_recruiters":
                return await self.metrics.get_recruiters()
            elif entity == "active_statuses":
                return await self.metrics.active_statuses()
        
        print(f"⚠️ Unsupported computed metric: {operation} on {entity}")
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
                    # Status information now comes from applicant_links table
                    # For now, skip status filtering since it requires joins
                    pass
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
                # Status information now comes from applicant_links table
                # For now, return total count since status filtering requires joins
                return len(applicants_data)
            elif field == "recruiter" and op == "eq":
                return len([a for a in applicants_data if a['recruiter_name'] == value])
            else:
                return len(applicants_data)
        
        elif entity == "applicant_links":
            # Handle applicant_links entity for pipeline status queries
            return await self._execute_applicant_links_count(filter_expr)
        
        return 0
    
    async def _execute_avg_sql(self, entity: str, field: str, filter_expr: Dict[str, Any]) -> float:
        """Execute average using SQL approach"""
        
        # time_to_hire_days field has been removed from schema per CLAUDE.md
        # All time calculations must now be done via logs parsing
        print(f"⚠️ Field '{field}' no longer supported in schema. Use logs-based calculations instead.")
        return 0.0
    
    async def _execute_field_sql(self, field: str) -> List[str]:
        """Execute field extraction using SQL approach"""
        
        if field == "status":
            status_map = await self.engine._get_status_mapping()
            return list(status_map.values())
        elif field == "recruiter" or field == "coworkers":
            recruiters_map = await self.engine._get_recruiters_mapping()
            return list(recruiters_map.values())
        elif field == "company":
            # Get unique company values from vacancies
            vacancies_data = await self.engine._execute_vacancies_query(None)
            companies = list(set(v.get('company', 'Unknown') for v in vacancies_data if v.get('company')))
            return companies or ["Unknown"]
        elif field == "divisions" or field == "account_division":
            divisions_map = await self.engine._get_divisions_mapping()
            return list(divisions_map.values())
        elif field == "tags":
            tags_map = await self.engine._get_tags_mapping()
            return list(tags_map.values())
        
        return []
    
    async def _execute_applicant_links_count(self, filter_expr: Dict[str, Any]) -> int:
        """Execute count on applicant_links with filtering"""
        try:
            # Get all applicants with their links
            applicants_data = await self.engine._get_applicants_data()
            
            # Extract all links and apply filters
            all_links = []
            for applicant in applicants_data:
                # Check if applicant has status_id (from enriched individual calls)
                if 'status_id' in applicant and applicant['status_id']:
                    # Create synthetic link from enriched applicant data
                    synthetic_link = {
                        'id': f"synthetic_{applicant['id']}",
                        'applicant': applicant['id'],
                        'status_id': applicant['status_id'],
                        'vacancy': applicant.get('vacancy_id', 0)
                    }
                    all_links.append(synthetic_link)
            
            # Apply filters
            if not filter_expr:
                return len(all_links)
            
            field = filter_expr.get("field")
            op = filter_expr.get("op")
            value = filter_expr.get("value")
            
            if field == "vacancy.state" and op == "eq" and value == "OPEN":
                # Filter to only links connected to open vacancies
                open_vacancies = await self.engine._execute_vacancies_query(None)
                open_vacancy_ids = {v['id'] for v in open_vacancies if v.get('state') == 'OPEN'}
                
                filtered_links = [link for link in all_links if link.get('vacancy') in open_vacancy_ids]
                return len(filtered_links)
            
            return len(all_links)
            
        except Exception as e:
            print(f"❌ Error in applicant_links count: {e}")
            return 0
    
    async def execute_grouped_query(self, query_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Execute grouped query for chart data"""
        try:
            operation = query_spec.get("operation", "count")
            entity = query_spec.get("entity", "")
            group_by_field = query_spec.get("group_by", {}).get("field", "")
            filter_expr = query_spec.get("filter", {})
            
            print(f"🔧 Executing grouped query: {operation} on {entity} grouped by {group_by_field}")
            
            # Check for computed chart entities
            if entity == "active_candidates" and group_by_field == "status_id":
                return await self.metrics.active_candidates_by_status_chart()
            elif entity == "vacancies" and group_by_field == "state":
                return await self.metrics.vacancy_states_chart()
            elif entity == "applicants" and group_by_field == "source_id":
                return await self.metrics.applicants_by_source_chart()
            elif entity == "recruiters" and group_by_field == "hirings":
                return await self.metrics.recruiter_performance_chart()
            
            # Regular entity queries
            elif entity == "applicants" and group_by_field == "status_id":
                return await self._execute_applicants_by_status()
            elif entity == "applicants" and group_by_field == "source_id":
                return await self._execute_applicants_by_source()
            elif entity == "applicant_links" and group_by_field == "status_id":
                return await self._execute_applicant_links_by_status(filter_expr)
            elif entity == "vacancies" and group_by_field == "state":
                return await self._execute_vacancies_by_state()
            else:
                print(f"⚠️ Unsupported grouped query: {entity} by {group_by_field}")
                return {"labels": [], "values": []}
                
        except Exception as e:
            print(f"❌ Error in grouped query: {e}")
            return {"labels": [], "values": []}
    
    async def _execute_applicants_by_status(self) -> Dict[str, Any]:
        """Get applicant counts by status"""
        try:
            # Get vacancy statuses for labels
            status_map = await self.engine._get_status_mapping()
            
            # Get all applicants data
            applicants_data = await self.engine._execute_applicants_query({})
            
            # Count by status_id (using virtual field from schema)
            status_counts = {}
            for applicant in applicants_data:
                status_id = applicant.get('status_id', 'Unknown')
                status_counts[status_id] = status_counts.get(status_id, 0) + 1
            
            # Convert to chart format
            labels = []
            values = []
            for status_id, count in status_counts.items():
                status_name = status_map.get(status_id, f"Status {status_id}")
                labels.append(status_name)
                values.append(count)
            
            return {"labels": labels, "values": values}
            
        except Exception as e:
            print(f"❌ Error getting applicants by status: {e}")
            return {"labels": [], "values": []}
    
    async def _execute_applicants_by_source(self) -> Dict[str, Any]:
        """Get applicant counts by source"""
        try:
            # Get sources for labels
            sources_map = await self.engine._get_sources_mapping()
            
            # Get all applicants data
            applicants_data = await self.engine._execute_applicants_query({})
            
            # Count by source_id
            source_counts = {}
            for applicant in applicants_data:
                source_id = applicant.get('source_id', 'Unknown')
                source_counts[source_id] = source_counts.get(source_id, 0) + 1
            
            # Convert to chart format
            labels = []
            values = []
            for source_id, count in source_counts.items():
                source_name = sources_map.get(source_id, f"Source {source_id}")
                labels.append(source_name)
                values.append(count)
            
            return {"labels": labels, "values": values}
            
        except Exception as e:
            print(f"❌ Error getting applicants by source: {e}")
            return {"labels": [], "values": []}
    
    async def _execute_applicant_links_by_status(self, filter_expr: Dict[str, Any]) -> Dict[str, Any]:
        """Get applicant link counts by status (for pipeline analysis)"""
        try:
            # Get vacancy statuses for labels
            status_map = await self.engine._get_status_mapping()
            
            # Get all applicants with their links/status info
            applicants_data = await self.engine._get_applicants_data()
            
            # Extract links and apply filters
            all_links = []
            for applicant in applicants_data:
                if 'status_id' in applicant and applicant['status_id']:
                    synthetic_link = {
                        'status_id': applicant['status_id'],
                        'vacancy_id': applicant.get('vacancy_id', 0)
                    }
                    all_links.append(synthetic_link)
            
            # Apply vacancy.state = "OPEN" filter if specified
            if filter_expr and filter_expr.get("field") == "vacancy.state" and filter_expr.get("value") == "OPEN":
                # Get open vacancy IDs
                open_vacancies = await self.engine._execute_vacancies_query(None)
                open_vacancy_ids = {v['id'] for v in open_vacancies if v.get('state') == 'OPEN'}
                
                # Filter links to only those connected to open vacancies
                all_links = [link for link in all_links if link.get('vacancy_id') in open_vacancy_ids]
                print(f"🎯 Filtered to {len(all_links)} links from open vacancies")
            
            # Count by status_id
            status_counts = {}
            for link in all_links:
                status_id = link.get('status_id', 'Unknown')
                status_counts[status_id] = status_counts.get(status_id, 0) + 1
            
            # Convert to chart format using status names instead of raw status objects
            labels = []
            values = []
            for status_id, count in status_counts.items():
                if status_id == 'Unknown':
                    labels.append("Status Unknown")
                else:
                    status_info = status_map.get(status_id, {'name': f'Status {status_id}'})
                    labels.append(status_info.get('name', f'Status {status_id}'))
                values.append(count)
            
            print(f"📊 Pipeline status distribution: {dict(zip(labels, values))}")
            return {"labels": labels, "values": values}
            
        except Exception as e:
            print(f"❌ Error getting applicant links by status: {e}")
            return {"labels": [], "values": []}
    
    async def _execute_vacancies_by_state(self) -> Dict[str, Any]:
        """Get vacancy counts by state"""
        try:
            # Get all vacancies data
            vacancies_data = await self.engine._execute_vacancies_query({})
            
            # Count by state
            state_counts = {}
            for vacancy in vacancies_data:
                state = vacancy.get('state', 'Unknown')
                state_counts[state] = state_counts.get(state, 0) + 1
            
            # Convert to chart format
            labels = list(state_counts.keys())
            values = list(state_counts.values())
            
            return {"labels": labels, "values": values}
            
        except Exception as e:
            print(f"❌ Error getting vacancies by state: {e}")
            return {"labels": [], "values": []}
    
    async def execute_chart_data(self, chart_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Execute chart data generation using SQL approach"""
        x_axis_spec = chart_spec.get("x_axis", {})
        y_axis_spec = chart_spec.get("y_axis", {})
        
        x_field = x_axis_spec.get("field")
        
        if x_field == "status":
            return await self._status_chart_sql()
        elif x_field in ["recruiter", "coworkers"]:
            return await self._recruiter_chart_sql(y_axis_spec)
        elif x_field == "company":
            return await self._company_chart_sql()
        elif x_field in ["divisions", "account_division"]:
            return await self._divisions_chart_sql()
        
        return {"labels": [], "values": []}
    
    async def _status_chart_sql(self) -> Dict[str, Any]:
        """Generate status distribution chart using SQL approach"""
        
        # Status information now comes from applicant_links table
        # Get status distribution from applicants with status info
        applicants_data = await self.engine._get_applicants_data()
        status_mapping = await self.engine._get_status_mapping()
        
        status_counts = {}
        for applicant in applicants_data:
            if 'status_id' in applicant and applicant['status_id']:
                status_id = applicant['status_id']
                status_info = status_mapping.get(status_id, {'name': f'Status {status_id}'})
                status_name = status_info.get('name', f'Status {status_id}')
                status_counts[status_name] = status_counts.get(status_name, 0) + 1
        
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
                # Status information now comes from applicant_links table
                # For now, skip status filtering since it requires joins
                filtered_data = applicants_data
        
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
    
    async def _company_chart_sql(self) -> Dict[str, Any]:
        """Generate company distribution chart using SQL approach"""
        
        vacancies_data = await self.engine._execute_vacancies_query(None)
        
        company_counts = {}
        for vacancy in vacancies_data:
            company = vacancy.get('company', 'Unknown')
            if company:
                company_counts[company] = company_counts.get(company, 0) + 1
        
        # Sort by count
        sorted_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        labels = [company for company, count in sorted_companies]
        values = [count for company, count in sorted_companies]
        
        print(f"📊 SQLAlchemy company chart: {dict(zip(labels, values))}")
        
        return {"labels": labels, "values": values}
    
    async def _divisions_chart_sql(self) -> Dict[str, Any]:
        """Generate divisions distribution chart using SQL approach"""
        
        divisions_map = await self.engine._get_divisions_mapping()
        
        # Count applicants or vacancies by division - simplified approach
        labels = list(divisions_map.values())[:10]  # Top 10 divisions
        values = [1] * len(labels)  # Placeholder counts
        
        print(f"📊 SQLAlchemy divisions chart: {dict(zip(labels, values))}")
        
        return {"labels": labels, "values": values}
    
    # ==================== READY-TO-USE METRICS ====================
    
    async def get_ready_metric(self, metric_name: str, **kwargs) -> Union[int, float, List[Any], Dict[str, Any]]:
        """Execute ready-to-use metrics"""
        return await self.metrics_helper.execute_metric(metric_name, **kwargs)
    
    async def get_ready_chart(self, chart_type: str) -> Dict[str, Any]:
        """Get ready-to-use chart data"""
        return await self.metrics_helper.get_metric_chart_data(chart_type)
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get all dashboard data in one call"""
        key_metrics = await self.metrics.get_all_key_metrics()
        chart_data = await self.metrics.get_all_chart_data()
        
        return {
            "metrics": key_metrics,
            "charts": chart_data
        }


# Predefined Query Templates for Common Analytics
class HuntflowAnalyticsTemplates:
    """Pre-built analytics queries using SQLAlchemy expressions"""
    
    def __init__(self, executor: SQLAlchemyHuntflowExecutor):
        self.executor = executor
        self.builder = executor.builder
    
    async def recruiter_performance_report(self) -> Dict[str, Any]:
        """Generate complete recruiter performance report"""
        
        # Get recruiter hire counts from applicants with hired status
        # Status information now comes from applicant_links table
        applicants_data = await self.executor.engine._get_applicants_data()
        status_mapping = await self.executor.engine._get_status_mapping()
        
        # Find hired status ID (assuming "Оффер принят" maps to a specific status ID)
        hired_status_ids = [sid for sid, status_info in status_mapping.items() if 'принят' in status_info.get('name', '').lower() or 'hired' in status_info.get('name', '').lower()]
        hired_applicants = [app for app in applicants_data if app.get('status_id') in hired_status_ids]
        
        recruiter_stats = {}
        for applicant in hired_applicants:
            recruiter = applicant.get('recruiter_name', 'Unknown')
            if recruiter and recruiter != 'Unknown':
                if recruiter not in recruiter_stats:
                    recruiter_stats[recruiter] = {'hires': 0, 'times': []}
                recruiter_stats[recruiter]['hires'] += 1
                
                # Note: time_to_hire_days removed from schema per CLAUDE.md
                # Time calculations would be done via log parsing if implemented
                pass
        
        # Note: avg_time calculation removed since time_to_hire_days field removed
        for recruiter in recruiter_stats:
            recruiter_stats[recruiter]['avg_time'] = 0  # Placeholder
        
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