"""
SQLAlchemy-based Query Executor for Huntflow Analytics
Replaces the complex huntflow_query_executor.py with clean SQL-like operations
"""
from typing import Dict, Any, List, Union, TypedDict, Literal, Callable, TypeVar, Optional
from virtual_engine import HuntflowVirtualEngine, HuntflowQueryBuilder
from huntflow_metrics import HuntflowComputedMetrics, HuntflowMetricsHelper
from sqlalchemy.sql import select, func
import asyncio
import logging
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')

class QueryExecutionError(Exception):
    """Custom exception for query execution errors"""
    def __init__(self, message: str, query_type: str = None, original_error: Exception = None):
        self.query_type = query_type
        self.original_error = original_error
        super().__init__(message)

def handle_errors(default_return: Optional[T] = None, error_prefix: str = "Error") -> Callable:
    """Decorator to handle common error patterns in async methods"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except QueryExecutionError as e:
                # Re-raise our custom errors to preserve context
                logger.error(f"{error_prefix} in {func.__name__}: {e} (query_type: {e.query_type})")
                raise
            except (ValueError, TypeError) as e:
                # Handle specific expected errors
                logger.error(f"{error_prefix} in {func.__name__} - Invalid input: {e}")
                return default_return
            except Exception as e:
                # Log unexpected errors with more context
                logger.error(f"{error_prefix} in {func.__name__} - Unexpected error: {type(e).__name__}: {e}")
                return default_return
        return wrapper
    return decorator

class FilterExpr(TypedDict, total=False):
    """Type definition for filter expressions"""
    field: str
    op: Literal["eq", "ne", "gt", "lt", "gte", "lte", "in", "not_in"]
    value: Union[str, int, List[Union[str, int]]]

class SQLAlchemyHuntflowExecutor:
    """Execute analytics expressions using SQLAlchemy virtual tables"""
    
    def __init__(self, hf_client):
        self.engine = HuntflowVirtualEngine(hf_client)
        self.builder = HuntflowQueryBuilder(self.engine)
        self.metrics = HuntflowComputedMetrics(self.engine)
        self.metrics_helper = HuntflowMetricsHelper(self)
    
    async def execute_expression(self, expression: Dict[str, Any]) -> Union[int, List[str]]:
        """Execute analytics expression using SQL approach"""
        operation = expression.get("operation", "")
        entity = expression.get("entity", "")
        field = expression.get("field")
        filter_expr = expression.get("filter", {})
        
        logger.info(f"Executing {operation} on {entity}")
        
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
            logger.warning(f"Unsupported operation: {operation}")
            return 0
    
    async def _execute_computed_metric(self, entity: str, operation: str) -> Union[int, List[str]]:
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
        
        logger.warning(f"Unsupported computed metric: {operation} on {entity}")
        return 0
    
    async def _execute_count_sql(self, entity: str, filter_expr: FilterExpr) -> int:
        """Execute count using SQL approach"""
        
        if entity == "applicants":
            # Check if we can use pure SQL counting
            if self._can_use_sql_count(filter_expr):
                return await self._execute_sql_count(filter_expr)
            else:
                # Fall back to Python filtering for complex cases
                applicants_data = await self.engine._execute_applicants_query(filter_expr or {})
                return len(applicants_data)
        
        elif entity == "applicant_links":
            # Handle applicant_links entity for pipeline status queries
            return await self._execute_applicant_links_count(filter_expr)
        
        return 0
    
    def _can_use_sql_count(self, filter_expr: FilterExpr) -> bool:
        """Check if we can use pure SQL for counting (no complex joins needed)"""
        if not filter_expr:
            return True
            
        field = filter_expr.get("field")
        # Simple fields that don't require joins
        sql_compatible_fields = {"recruiter", "source_id", "vacancy_id"}
        
        # Status filtering requires joins with applicant_links, so not SQL-compatible yet
        return field in sql_compatible_fields
    
    async def _execute_sql_count(self, filter_expr: FilterExpr) -> int:
        """Execute actual SQL count query"""
        try:
            query = select(func.count(self.engine.applicants.c.id))
            
            if filter_expr:
                field = filter_expr.get("field")
                op = filter_expr.get("op")
                value = filter_expr.get("value")
                
                # Validate inputs
                if not field or not op:
                    raise ValueError(f"Invalid filter expression: missing field or op")
                
                if op in ["in", "not_in"] and not isinstance(value, list):
                    raise ValueError(f"Operator '{op}' requires list value, got {type(value)}")
                
                # Build where clauses
                if field == "recruiter":
                    if op == "eq":
                        query = query.where(self.engine.applicants.c.recruiter_name == value)
                    elif op == "in":
                        query = query.where(self.engine.applicants.c.recruiter_name.in_(value))
                elif field == "source_id":
                    if op == "eq":
                        query = query.where(self.engine.applicants.c.source_id == value)
                    elif op == "in":
                        query = query.where(self.engine.applicants.c.source_id.in_(value))
                elif field == "vacancy_id":
                    if op == "eq":
                        query = query.where(self.engine.applicants.c.vacancy_id == value)
                    elif op == "in":
                        query = query.where(self.engine.applicants.c.vacancy_id.in_(value))
                else:
                    raise ValueError(f"Unsupported field for SQL count: {field}")
            
            # Execute the SQL query directly
            result = await self.engine._execute_sql_query(query)
            count = result.scalar() if result else 0
            
            logger.debug(f"SQL count query returned: {count}")
            return count
            
        except Exception as e:
            raise QueryExecutionError(
                f"Failed to execute SQL count query: {e}",
                query_type="count",
                original_error=e
            )
    
    async def _execute_avg_sql(self, entity: str, field: str, filter_expr: FilterExpr) -> float:
        """Execute average using SQL approach - no longer supported"""
        logger.warning("Average calculations not supported - use logs-based calculations instead")
        return 0.0
    
    async def _fetch_data_chunked(self, entity: str, filter_expr: FilterExpr, chunk_size: int = 1000) -> List[Dict[str, Any]]:
        """Fetch data in chunks to prevent memory overload"""
        if entity == "applicants":
            # For now, delegate to engine but add size limit awareness
            data = await self.engine._execute_applicants_query(filter_expr or {})
            if len(data) > chunk_size * 10:  # If more than 10 chunks worth
                logger.warning(f"Large dataset detected: {len(data)} records. Consider adding pagination.")
            return data
        elif entity == "vacancies":
            data = await self.engine._execute_vacancies_query(filter_expr or {})
            if len(data) > chunk_size * 5:  # Vacancies typically smaller
                logger.warning(f"Large vacancy dataset: {len(data)} records.")
            return data
        else:
            return []
    
    @handle_errors(default_return=[])
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
    
    def _build_chart_data(self, items: List[Dict[str, Any]], field: str, 
                          mapping: Optional[Dict[str, Any]] = None, sort_by_count: bool = True, 
                          limit: Optional[int] = None) -> Dict[str, Any]:
        """Convert item counts by field into chart format"""
        # Count by field
        field_counts: Dict[Any, int] = {}
        for item in items:
            field_value = item.get(field, 'Unknown')
            # Convert None to 'Unknown' as well
            if field_value is None:
                field_value = 'Unknown'
            field_counts[field_value] = field_counts.get(field_value, 0) + 1
        
        # Convert to chart format with mapping
        chart_items = []
        for field_id, count in field_counts.items():
            if mapping and field_id != 'Unknown':
                if isinstance(mapping.get(field_id), dict):
                    # Handle mapping values that are dicts (like status objects)
                    field_name = mapping.get(field_id, {}).get('name', f"{field} {field_id}")
                else:
                    # Handle mapping values that are strings
                    field_name = mapping.get(field_id, f"{field} {field_id}")
            else:
                field_name = str(field_id) if field_id != 'Unknown' else "Unknown"
            
            chart_items.append((field_name, count))
        
        # Sort and limit if specified
        if sort_by_count:
            chart_items.sort(key=lambda x: x[1], reverse=True)
        
        if limit:
            chart_items = chart_items[:limit]
        
        labels = [item[0] for item in chart_items]
        values = [item[1] for item in chart_items]
        
        return {"labels": labels, "values": values}

    @handle_errors(default_return=0)
    async def _execute_applicant_links_count(self, filter_expr: FilterExpr) -> int:
        """Execute count on applicant_links with filtering"""
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
    
    @handle_errors(default_return={"labels": [], "values": []})
    async def execute_grouped_query(self, query_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Execute grouped query for chart data"""
        operation = query_spec.get("operation", "count")
        entity = query_spec.get("entity", "")
        group_by_field = query_spec.get("group_by", {}).get("field", "")
        filter_expr = query_spec.get("filter", {})
        
        logger.info(f"Executing grouped query: {operation} on {entity} grouped by {group_by_field}")
        
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
            logger.warning(f"Unsupported grouped query: {entity} by {group_by_field}")
            return {"labels": [], "values": []}
    
    @handle_errors(default_return={"labels": [], "values": []})
    async def _execute_applicants_by_status(self) -> Dict[str, Any]:
        """Get applicant counts by status"""
        # Get vacancy statuses for labels
        status_map = await self.engine._get_status_mapping()
        
        # Use chunked data fetching with size awareness
        applicants_data = await self._fetch_data_chunked("applicants", {})
        
        # Use helper to build chart data
        return self._build_chart_data(applicants_data, 'status_id', status_map)
    
    @handle_errors(default_return={"labels": [], "values": []})
    async def _execute_applicants_by_source(self) -> Dict[str, Any]:
        """Get applicant counts by source"""
        # Get sources for labels
        sources_map = await self.engine._get_sources_mapping()
        
        # Use chunked data fetching with size awareness
        applicants_data = await self._fetch_data_chunked("applicants", {})
        
        # Use helper to build chart data
        return self._build_chart_data(applicants_data, 'source_id', sources_map)
    
    @handle_errors(default_return={"labels": [], "values": []})
    async def _execute_applicant_links_by_status(self, filter_expr: FilterExpr) -> Dict[str, Any]:
        """Get applicant link counts by status (for pipeline analysis)"""
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
            logger.debug(f"Filtered to {len(all_links)} links from open vacancies")
        
        # Use helper to build chart data
        chart_data = self._build_chart_data(all_links, 'status_id', status_map)
        
        logger.debug(f"Pipeline status distribution: {dict(zip(chart_data['labels'], chart_data['values']))}")
        return chart_data
    
    @handle_errors(default_return={"labels": [], "values": []})
    async def _execute_vacancies_by_state(self) -> Dict[str, Any]:
        """Get vacancy counts by state"""
        # Get all vacancies data
        vacancies_data = await self.engine._execute_vacancies_query({})
        
        # Use helper to build chart data (no mapping needed for state)
        return self._build_chart_data(vacancies_data, 'state')
    
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
    
    @handle_errors(default_return={"labels": [], "values": []})
    async def _status_chart_sql(self) -> Dict[str, Any]:
        """Generate status distribution chart using SQL approach"""
        
        # Status information now comes from applicant_links table
        # Get status distribution from applicants with status info
        applicants_data = await self.engine._get_applicants_data()
        status_mapping = await self.engine._get_status_mapping()
        
        # Filter to only applicants with status info
        applicants_with_status = [app for app in applicants_data if 'status_id' in app and app['status_id']]
        
        # Use helper to build chart data
        chart_data = self._build_chart_data(applicants_with_status, 'status_id', status_mapping)
        
        logger.debug(f"Status chart data: {dict(zip(chart_data['labels'], chart_data['values']))}")
        
        return chart_data
    
    @handle_errors(default_return={"labels": [], "values": []})
    async def _recruiter_chart_sql(self, y_axis_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recruiter performance chart using SQL approach"""
        
        applicants_data = await self.engine._get_applicants_data()
        
        # Build base query with filters from y_axis_spec
        filter_expr = y_axis_spec.get("filter", {})
        applicants_data = await self.engine._execute_applicants_query(filter_expr)
        
        # Filter out unknown recruiters
        valid_applicants = [app for app in applicants_data if app.get('recruiter_name') and app.get('recruiter_name') != 'Unknown']
        
        # Use helper to build chart data with limit
        chart_data = self._build_chart_data(valid_applicants, 'recruiter_name', limit=5)
        
        logger.debug(f"Recruiter chart data: {dict(zip(chart_data['labels'], chart_data['values']))}")
        
        return chart_data
    
    @handle_errors(default_return={"labels": [], "values": []})
    async def _company_chart_sql(self) -> Dict[str, Any]:
        """Generate company distribution chart using SQL approach"""
        
        vacancies_data = await self.engine._execute_vacancies_query(None)
        
        # Filter out vacancies without company
        valid_vacancies = [vac for vac in vacancies_data if vac.get('company')]
        
        # Use helper to build chart data with limit
        chart_data = self._build_chart_data(valid_vacancies, 'company', limit=10)
        
        logger.debug(f"Company chart data: {dict(zip(chart_data['labels'], chart_data['values']))}")
        
        return chart_data
    
    @handle_errors(default_return={"labels": [], "values": []})
    async def _divisions_chart_sql(self) -> Dict[str, Any]:
        """Generate divisions distribution chart using SQL approach"""
        
        divisions_map = await self.engine._get_divisions_mapping()
        
        # Count applicants or vacancies by division - simplified approach
        labels = list(divisions_map.values())[:10]  # Top 10 divisions
        values = [1] * len(labels)  # Placeholder counts
        
        logger.debug(f"Divisions chart data: {dict(zip(labels, values))}")
        
        return {"labels": labels, "values": values}
    
    # ==================== READY-TO-USE METRICS ====================
    
    async def get_ready_metric(self, metric_name: str, **kwargs) -> Union[int, List[str], Dict[str, Any]]:
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
                    recruiter_stats[recruiter] = {'hires': 0}
                recruiter_stats[recruiter]['hires'] += 1
        
        # Find top performer
        if recruiter_stats:
            top_recruiter = max(recruiter_stats.items(), key=lambda x: x[1]['hires'])
            return {
                "top_recruiter": top_recruiter[0],
                "hires": top_recruiter[1]['hires'],
                "all_stats": recruiter_stats
            }
        
        return {"top_recruiter": "No Data", "hires": 0, "all_stats": {}}