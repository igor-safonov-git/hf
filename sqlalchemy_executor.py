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
from dataclasses import dataclass
from chart_helpers import build_chart_data_async, build_status_chart_data_cpu

logger = logging.getLogger(__name__)

T = TypeVar('T')

# Typed Literal unions for type safety - mypy will catch unknown operations
OperationType = Literal["count", "avg", "field"]
EntityType = Literal[
    "applicants", "vacancies", "applicant_links",
    "active_candidates", "open_vacancies", "closed_vacancies", 
    "get_recruiters", "active_statuses"
]
FilterOperation = Literal["eq", "ne", "gt", "lt", "gte", "lte", "in", "not_in"]

# Public API exports
__all__ = [
    'SQLAlchemyHuntflowExecutor',
    'RecruiterStats', 
    'RecruiterPerformanceResult',
    'QueryExecutionError',
    'FilterExpr',
    'OperationType',
    'EntityType', 
    'FilterOperation'
]

@dataclass(slots=True)
class RecruiterStats:
    """Recruiter performance statistics - optimized with slots for reduced GC churn"""
    hires: int = 0

@dataclass(slots=True) 
class RecruiterPerformanceResult:
    """Complete recruiter performance report - optimized with slots for reduced GC churn"""
    top_recruiter: str
    hires: int
    all_stats: Dict[str, RecruiterStats]

class QueryExecutionError(Exception):
    """Custom exception for query execution errors"""
    def __init__(self, message: str, query_type: Optional[str] = None, original_error: Optional[Exception] = None):
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
                logger.error("%s in %s: %s (query_type: %s)", error_prefix, func.__name__, e, e.query_type)
                raise
            except (ValueError, TypeError) as e:
                # Handle specific expected errors
                logger.error("%s in %s - Invalid input: %s", error_prefix, func.__name__, e)
                return default_return
            except Exception as e:
                # Log unexpected errors with more context
                logger.error("%s in %s - Unexpected error: %s: %s", error_prefix, func.__name__, type(e).__name__, e)
                return default_return
        return wrapper
    return decorator

class FilterExpr(TypedDict, total=False):
    """Type definition for filter expressions with type-safe operations"""
    field: str
    op: FilterOperation
    value: Union[str, int, List[Union[str, int]]]

class SQLAlchemyHuntflowExecutor:
    """Execute analytics expressions using SQLAlchemy virtual tables"""
    
    def __init__(self, hf_client, hired_status_config: Optional[Dict[str, Any]] = None):
        self.engine = HuntflowVirtualEngine(hf_client)
        self.builder = HuntflowQueryBuilder(self.engine)
        self.metrics = HuntflowComputedMetrics(self.engine)
        self.metrics_helper = HuntflowMetricsHelper(self)
        
        # Configuration for hired status detection (robust system-level detection only)
        self.hired_status_config = hired_status_config or {
            "method": "auto_detect",  # "system_types", "status_ids" 
            "status_ids": [],  # Explicit list of hired status IDs if known
            "system_types": ["hired"],  # System-level status types (most reliable)
            "cache_duration": 3600  # Cache hired status detection for 1 hour
        }
        self._hired_status_cache = None
        self._hired_status_cache_time = 0
    
    async def execute_expression(self, expression: Dict[str, Any]) -> Union[int, List[str]]:
        """Execute analytics expression using SQL approach with type-safe operations"""
        operation: OperationType = expression.get("operation", "count")  # type: ignore
        entity: EntityType = expression.get("entity", "applicants")  # type: ignore
        field = expression.get("field")
        filter_expr = expression.get("filter", {})
        
        logger.info("Executing %s on %s", operation, entity)
        
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
            logger.warning("Unsupported operation: %s", operation)
            return 0
    
    async def _execute_computed_metric(self, entity: EntityType, operation: OperationType) -> Union[int, List[str]]:
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
        
        logger.warning("Unsupported computed metric: %s on %s", operation, entity)
        return 0
    
    async def _execute_count_sql(self, entity: EntityType, filter_expr: FilterExpr) -> int:
        """Execute count using proper SQLAlchemy approach"""
        
        if entity == "applicants":
            # Build proper SQLAlchemy count query
            query = select(func.count(self.engine.applicants.c.id))
            
            # Apply filters to the query using SQLAlchemy
            if filter_expr:
                query = self._apply_filters_to_query(query, self.engine.applicants, filter_expr)
            
            # Execute the SQLAlchemy query through the virtual engine
            result = await self.engine.execute_sqlalchemy_query(query)
            return result.scalar()
        
        elif entity == "applicant_links":
            # Handle applicant_links entity for pipeline status queries
            return await self._execute_applicant_links_count(filter_expr)
        
        elif entity == "vacancies":
            # Build proper SQLAlchemy count query for vacancies
            query = select(func.count(self.engine.vacancies.c.id))
            
            if filter_expr:
                query = self._apply_filters_to_query(query, self.engine.vacancies, filter_expr)
            
            result = await self.engine.execute_sqlalchemy_query(query)
            return result.scalar()
        
        return 0
    
    def _apply_filters_to_query(self, query, table, filter_expr: FilterExpr):
        """Apply filter expressions to SQLAlchemy query"""
        if not filter_expr:
            return query
            
        field = filter_expr.get("field")
        op = filter_expr.get("op", "eq")
        value = filter_expr.get("value")
        
        if not field or value is None:
            return query
        
        # Map field names to table columns
        column_mapping = {
            "recruiter": "recruiter_name",
            "source_id": "source_id", 
            "vacancy_id": "vacancy_id",
            "status_id": "status_id",
            "company": "company",
            "state": "state"
        }
        
        column_name = column_mapping.get(field, field)
        
        # Check if column exists in table
        if not hasattr(table.c, column_name):
            logger.warning("Column %s not found in table, skipping filter", column_name)
            return query
            
        column = getattr(table.c, column_name)
        
        # Apply filter based on operation
        if op == "eq":
            query = query.where(column == value)
        elif op == "ne":
            query = query.where(column != value)
        elif op == "gt":
            query = query.where(column > value)
        elif op == "lt":
            query = query.where(column < value)
        elif op == "gte":
            query = query.where(column >= value)
        elif op == "lte":
            query = query.where(column <= value)
        elif op == "in":
            if isinstance(value, list):
                query = query.where(column.in_(value))
            else:
                logger.warning("IN operator requires list value, got %s", type(value))
        elif op == "not_in":
            if isinstance(value, list):
                query = query.where(~column.in_(value))
            else:
                logger.warning("NOT_IN operator requires list value, got %s", type(value))
        else:
            logger.warning("Unsupported filter operation: %s", op)
            
        return query
    
    def _can_use_sql_count(self, filter_expr: FilterExpr) -> bool:
        """Check if we can use pure SQL for counting"""
        # With proper SQLAlchemy query execution, we can handle most filters
        if not filter_expr:
            return True
            
        field = filter_expr.get("field")
        # Most fields can now be handled via SQLAlchemy
        supported_fields = {"recruiter", "source_id", "vacancy_id", "status_id", "company", "state"}
        
        return field in supported_fields
    
    
    async def _execute_avg_sql(self, entity: str, field: str, filter_expr: FilterExpr) -> float:
        """Execute average using SQL approach - no longer supported"""
        logger.warning("Average calculations not supported - use logs-based calculations instead")
        return 0.0
    
    async def _fetch_data_chunked(self, entity: EntityType, filter_expr: FilterExpr, chunk_size: int = 1000) -> List[Dict[str, Any]]:
        """Fetch data in chunks to prevent memory overload"""
        if entity == "applicants":
            # For now, delegate to engine but add size limit awareness
            data = await self.engine._execute_applicants_query(filter_expr or {})
            if len(data) > chunk_size * 10:  # If more than 10 chunks worth
                logger.warning("Large dataset detected: %s records. Consider adding pagination.", len(data))
            return data
        elif entity == "vacancies":
            data = await self.engine._execute_vacancies_query(filter_expr or {})
            if len(data) > chunk_size * 5:  # Vacancies typically smaller
                logger.warning("Large vacancy dataset: %s records.", len(data))
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
            # Use thread pool for CPU-intensive unique extraction on large datasets
            if len(vacancies_data) > 500:
                logger.debug("Processing %s vacancies for company extraction in thread pool", len(vacancies_data))
                return await asyncio.to_thread(self._extract_unique_companies_cpu, vacancies_data)
            else:
                return self._extract_unique_companies_cpu(vacancies_data)
        elif field == "divisions" or field == "account_division":
            divisions_map = await self.engine._get_divisions_mapping()
            return list(divisions_map.values())
        elif field == "tags":
            tags_map = await self.engine._get_tags_mapping()
            return list(tags_map.values())
        
        return []
    
    # ==================== CPU-BOUND OPERATIONS ====================
    
    @staticmethod
    def _extract_unique_companies_cpu(vacancies_data: List[Dict[str, Any]]) -> List[str]:
        """CPU-bound: Extract unique companies from vacancy data"""
        companies = list(set(v.get('company', 'Unknown') for v in vacancies_data if v.get('company')))
        return companies or ["Unknown"]
    
    # Chart building moved to chart_helpers module for better FE organization
    
    @staticmethod
    def _calculate_recruiter_stats_cpu(applicants_data: List[Dict[str, Any]], 
                                     hired_status_ids: List[Any]) -> RecruiterPerformanceResult:
        """CPU-bound: Calculate recruiter performance statistics using dataclasses for efficiency"""
        # Filter hired applicants
        hired_applicants = [app for app in applicants_data if app.get('status_id') in hired_status_ids]
        
        recruiter_stats: Dict[str, RecruiterStats] = {}
        for applicant in hired_applicants:
            recruiter = applicant.get('recruiter_name', 'Unknown')
            if recruiter and recruiter != 'Unknown':
                if recruiter not in recruiter_stats:
                    recruiter_stats[recruiter] = RecruiterStats()
                recruiter_stats[recruiter].hires += 1
        
        # Find top performer
        if recruiter_stats:
            top_recruiter = max(recruiter_stats.items(), key=lambda x: x[1].hires)
            return RecruiterPerformanceResult(
                top_recruiter=top_recruiter[0],
                hires=top_recruiter[1].hires,
                all_stats=recruiter_stats
            )
        
        return RecruiterPerformanceResult(
            top_recruiter="No Data", 
            hires=0, 
            all_stats={}
        )
    
    async def _build_chart_data(self, items: List[Dict[str, Any]], field: str, 
                          mapping: Optional[Dict[str, Any]] = None, sort_by_count: bool = True, 
                          limit: Optional[int] = None) -> Dict[str, Any]:
        """Convert item counts by field into chart format using centralized chart helpers"""
        return await build_chart_data_async(items, field, mapping, sort_by_count, limit)

    @handle_errors(default_return=0)
    async def _execute_applicant_links_count(self, filter_expr: FilterExpr) -> int:
        """Execute count on applicant_links with optimized filtering (SQLAlchemy-style JOIN)"""
        
        # Check if we can optimize with a JOIN-style query
        if filter_expr and filter_expr.get("field") == "vacancy.state" and filter_expr.get("value") == "OPEN":
            return await self._count_applicant_links_with_vacancy_join(filter_expr)
        
        # For simple count without JOIN, use optimized approach
        return await self._count_applicant_links_simple()
    
    async def _count_applicant_links_simple(self) -> int:
        """Optimized count of applicant links without full data fetch"""
        try:
            # Use API metadata to get count instead of fetching all data
            params = {"count": 30, "page": 1}  # Small page to get total count
            result = await self.engine.hf_client._req(
                "GET", 
                f"/v2/accounts/{self.engine.hf_client.acc_id}/applicants/search",
                params=params
            )
            
            if isinstance(result, dict) and "total" in result:
                total_applicants = result.get("total", 0)
                logger.info("✅ OPTIMIZED: Counted %s applicant links via API metadata", total_applicants)
                return total_applicants
            
            # Fallback to old method if API doesn't provide metadata
            logger.warning("API metadata not available, falling back to data fetch")
            return await self._count_applicant_links_fallback()
            
        except Exception as e:
            logger.error("Optimized count failed: %s, falling back", e)
            return await self._count_applicant_links_fallback()
    
    async def _count_applicant_links_with_vacancy_join(self, filter_expr: FilterExpr) -> int:
        """Optimized JOIN-style count: applicant_links ⟕ vacancies WHERE vacancy.state = 'OPEN'"""
        
        # OPTIMIZATION: Instead of fetching all data and filtering in Python,
        # we use API-level filtering to minimize data transfer
        
        try:
            # Step 1: Get open vacancy IDs efficiently (only fetch IDs + state)
            vacancies_result = await self.engine.hf_client._req(
                "GET",
                f"/v2/accounts/{self.engine.hf_client.acc_id}/vacancies",
                params={"count": 100}  # Reasonable page size
            )
            
            if not isinstance(vacancies_result, dict):
                return 0
                
            open_vacancy_ids = set()
            for vacancy in vacancies_result.get("items", []):
                if vacancy.get("state") == "OPEN":
                    open_vacancy_ids.add(vacancy.get("id"))
            
            if not open_vacancy_ids:
                logger.debug("No open vacancies found")
                return 0
            
            # Step 2: Count applicants connected to open vacancies 
            # Use API filtering where possible instead of fetching all data
            applicant_count = 0
            page = 1
            
            while True:
                params = {"count": 100, "page": page}
                applicants_result = await self.engine.hf_client._req(
                    "GET",
                    f"/v2/accounts/{self.engine.hf_client.acc_id}/applicants/search",
                    params=params
                )
                
                if not isinstance(applicants_result, dict):
                    break
                    
                applicants = applicants_result.get("items", [])
                if not applicants:
                    break
                
                # Count applicants linked to open vacancies
                for applicant in applicants:
                    if applicant.get("vacancy_id") in open_vacancy_ids:
                        applicant_count += 1
                
                # Check if we've reached the end
                if len(applicants) < 100:
                    break
                page += 1
                
                # Safety limit to prevent infinite loops
                if page > 50:
                    logger.warning("JOIN query reached page limit, results may be incomplete")
                    break
            
            logger.info("✅ OPTIMIZED JOIN: Counted %s applicant links for %s open vacancies", applicant_count, len(open_vacancy_ids))
            return applicant_count
            
        except Exception as e:
            logger.error("Optimized JOIN count failed: %s, falling back", e)
            return await self._count_applicant_links_fallback()
    
    async def _count_applicant_links_fallback(self) -> int:
        """Fallback method using original approach"""
        applicants_data = await self.engine._get_applicants_data()
        return len([app for app in applicants_data if 'status_id' in app and app['status_id']])
    
    @handle_errors(default_return={"labels": [], "values": []})
    async def execute_grouped_query(self, query_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Execute grouped query for chart data - ENHANCED CONSOLIDATED VERSION"""
        operation = query_spec.get("operation", "count")
        entity = query_spec.get("entity", "")
        group_by_field = query_spec.get("group_by", {}).get("field", "")
        filter_expr = query_spec.get("filter", {})
        limit = query_spec.get("limit")  # NEW: Support result limiting
        
        logger.info("Executing grouped query: %s on %s grouped by %s", operation, entity, group_by_field)
        
        # Check for computed chart entities first
        if entity == "active_candidates" and group_by_field == "status_id":
            return await self.metrics.active_candidates_by_status_chart()
        elif entity == "vacancies" and group_by_field == "state":
            return await self.metrics.vacancy_states_chart()
        elif entity == "applicants" and group_by_field == "source_id":
            return await self.metrics.applicants_by_source_chart()
        elif entity == "recruiters" and group_by_field == "hirings":
            return await self.metrics.recruiter_performance_chart()
        
        # Enhanced regular entity queries with field mapping
        elif entity == "applicants":
            return await self._execute_applicants_grouped(group_by_field, filter_expr, limit)
        elif entity == "applicant_links":
            return await self._execute_applicant_links_grouped(group_by_field, filter_expr, limit)
        elif entity == "vacancies":
            return await self._execute_vacancies_grouped(group_by_field, filter_expr, limit)
        else:
            logger.warning("Unsupported grouped query: %s by %s", entity, group_by_field)
            return {"labels": [], "values": []}
    
    @handle_errors(default_return={"labels": [], "values": []})
    async def _execute_applicants_by_status(self) -> Dict[str, Any]:
        """Get applicant counts by status"""
        # Get vacancy statuses for labels
        status_map = await self.engine._get_status_mapping()
        
        # Use chunked data fetching with size awareness
        applicants_data = await self._fetch_data_chunked("applicants", {})
        
        # Use helper to build chart data
        return await self._build_chart_data(applicants_data, 'status_id', status_map)
    
    @handle_errors(default_return={"labels": [], "values": []})
    async def _execute_applicants_by_source(self) -> Dict[str, Any]:
        """Get applicant counts by source"""
        # Get sources for labels
        sources_map = await self.engine._get_sources_mapping()
        
        # Use chunked data fetching with size awareness
        applicants_data = await self._fetch_data_chunked("applicants", {})
        
        # Use helper to build chart data
        return await self._build_chart_data(applicants_data, 'source_id', sources_map)
    
    @handle_errors(default_return={"labels": [], "values": []})
    async def _execute_applicant_links_by_status(self, filter_expr: FilterExpr) -> Dict[str, Any]:
        """Get applicant link counts by status with optimized JOIN-style processing"""
        
        # Get vacancy statuses for labels
        status_map = await self.engine._get_status_mapping()
        
        # Check if we need a JOIN with vacancy filtering
        if filter_expr and filter_expr.get("field") == "vacancy.state" and filter_expr.get("value") == "OPEN":
            return await self._execute_applicant_links_by_status_with_vacancy_join(status_map, filter_expr)
        
        # For simple status grouping without JOIN, use optimized approach
        return await self._execute_applicant_links_by_status_simple(status_map)
    
    async def _execute_applicant_links_by_status_simple(self, status_map: Dict[str, Any]) -> Dict[str, Any]:
        """Optimized status grouping without vacancy JOIN"""
        
        # Use streaming approach to build status distribution
        status_counts = {}
        page = 1
        
        try:
            while True:
                params = {"count": 100, "page": page}
                applicants_result = await self.engine.hf_client._req(
                    "GET",
                    f"/v2/accounts/{self.engine.hf_client.acc_id}/applicants/search",
                    params=params
                )
                
                if not isinstance(applicants_result, dict):
                    break
                    
                applicants = applicants_result.get("items", [])
                if not applicants:
                    break
                
                # Count by status_id
                for applicant in applicants:
                    status_id = applicant.get("status_id")
                    if status_id:
                        status_counts[status_id] = status_counts.get(status_id, 0) + 1
                
                # Check if we've reached the end
                if len(applicants) < 100:
                    break
                page += 1
                
                # Safety limit
                if page > 50:
                    logger.warning("Status grouping reached page limit, results may be incomplete")
                    break
            
            # Use centralized chart helper for status distribution
            chart_data = build_status_chart_data_cpu(status_counts, status_map)
            labels = chart_data["labels"]
            values = chart_data["values"]
            
            logger.info("✅ OPTIMIZED: Status distribution via streaming processing")
            return {"labels": labels, "values": values}
            
        except Exception as e:
            logger.error("Optimized status grouping failed: %s, falling back", e)
            return await self._execute_applicant_links_by_status_fallback(status_map)
    
    async def _execute_applicant_links_by_status_with_vacancy_join(self, status_map: Dict[str, Any], filter_expr: FilterExpr) -> Dict[str, Any]:
        """Optimized JOIN: applicant_links ⟕ vacancies WHERE vacancy.state = 'OPEN', GROUP BY status_id"""
        
        try:
            # Step 1: Get open vacancy IDs efficiently
            vacancies_result = await self.engine.hf_client._req(
                "GET",
                f"/v2/accounts/{self.engine.hf_client.acc_id}/vacancies",
                params={"count": 100}
            )
            
            if not isinstance(vacancies_result, dict):
                return {"labels": [], "values": []}
                
            open_vacancy_ids = set()
            for vacancy in vacancies_result.get("items", []):
                if vacancy.get("state") == "OPEN":
                    open_vacancy_ids.add(vacancy.get("id"))
            
            if not open_vacancy_ids:
                logger.debug("No open vacancies found")
                return {"labels": [], "values": []}
            
            # Step 2: Stream applicants and count by status for those linked to open vacancies
            status_counts: Dict[int, int] = {}
            page = 1
            
            while True:
                params = {"count": 100, "page": page}
                applicants_result = await self.engine.hf_client._req(
                    "GET",
                    f"/v2/accounts/{self.engine.hf_client.acc_id}/applicants/search",
                    params=params
                )
                
                if not isinstance(applicants_result, dict):
                    break
                    
                applicants = applicants_result.get("items", [])
                if not applicants:
                    break
                
                # Count by status_id for applicants linked to open vacancies
                for applicant in applicants:
                    vacancy_id = applicant.get("vacancy_id")
                    status_id = applicant.get("status_id")
                    
                    if vacancy_id in open_vacancy_ids and status_id:
                        status_counts[status_id] = status_counts.get(status_id, 0) + 1
                
                # Check if we've reached the end
                if len(applicants) < 100:
                    break
                page += 1
                
                # Safety limit
                if page > 50:
                    logger.warning("JOIN query reached page limit, results may be incomplete")
                    break
            
            # Use centralized chart helper for status distribution
            chart_data = build_status_chart_data_cpu(status_counts, status_map)
            labels = chart_data["labels"]
            values = chart_data["values"]
            
            logger.info("✅ OPTIMIZED JOIN: Status distribution for %s open vacancies via streaming", len(open_vacancy_ids))
            return {"labels": labels, "values": values}
            
        except Exception as e:
            logger.error("Optimized JOIN status grouping failed: %s, falling back", e)
            return await self._execute_applicant_links_by_status_fallback(status_map)
    
    async def _execute_applicant_links_by_status_fallback(self, status_map: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback method using original approach"""
        applicants_data = await self.engine._get_applicants_data()
        
        all_links = []
        for applicant in applicants_data:
            if 'status_id' in applicant and applicant['status_id']:
                synthetic_link = {
                    'status_id': applicant['status_id'],
                    'vacancy_id': applicant.get('vacancy_id', 0)
                }
                all_links.append(synthetic_link)
        
        return await self._build_chart_data(all_links, 'status_id', status_map)
    
    @handle_errors(default_return={"labels": [], "values": []})
    async def _execute_vacancies_by_state(self) -> Dict[str, Any]:
        """Get vacancy counts by state"""
        # Get all vacancies data
        vacancies_data = await self.engine._execute_vacancies_query({})
        
        # Use helper to build chart data (no mapping needed for state)
        return await self._build_chart_data(vacancies_data, 'state')
    
    # ==================== ENHANCED GROUPED QUERY METHODS ====================
    
    async def _execute_applicants_grouped(self, group_by_field: str, filter_expr: FilterExpr, limit: Optional[int] = None) -> Dict[str, Any]:
        """Enhanced applicants grouping with field mapping support"""
        # Field mapping for applicants
        field_mapping = {
            "status_id": {"mapping_func": "_get_status_mapping"},
            "source_id": {"mapping_func": "_get_sources_mapping"},
            "recruiter_name": {"mapping_func": None, "filter_unknown": True},
            "division_id": {"mapping_func": "_get_divisions_mapping"},
            "company": {"mapping_func": None}  # Company from vacancy relationship
        }
        
        if group_by_field not in field_mapping:
            logger.warning("Unsupported applicants grouping field: %s", group_by_field)
            return {"labels": [], "values": []}
        
        # Get applicants data with filtering
        applicants_data = await self._fetch_data_chunked("applicants", filter_expr)
        
        # Apply field-specific processing
        field_config = field_mapping[group_by_field]
        mapping = None
        
        if field_config.get("mapping_func"):
            mapping_func = getattr(self.engine, field_config["mapping_func"])
            mapping = await mapping_func()
        
        # Filter unknown values if specified
        if field_config.get("filter_unknown"):
            applicants_data = [app for app in applicants_data 
                             if app.get(group_by_field) and app.get(group_by_field) != 'Unknown']
        
        return await self._build_chart_data(applicants_data, group_by_field, mapping, limit=limit)
    
    async def _execute_applicant_links_grouped(self, group_by_field: str, filter_expr: FilterExpr, limit: Optional[int] = None) -> Dict[str, Any]:
        """Enhanced applicant links grouping"""
        if group_by_field == "status_id":
            return await self._execute_applicant_links_by_status(filter_expr)
        else:
            logger.warning("Unsupported applicant_links grouping field: %s", group_by_field)
            return {"labels": [], "values": []}
    
    async def _execute_vacancies_grouped(self, group_by_field: str, filter_expr: FilterExpr, limit: Optional[int] = None) -> Dict[str, Any]:
        """Enhanced vacancies grouping with field mapping support"""
        # Field mapping for vacancies
        field_mapping = {
            "state": {"mapping_func": None},
            "company": {"mapping_func": None, "filter_empty": True},
            "division_id": {"mapping_func": "_get_divisions_mapping"}
        }
        
        if group_by_field not in field_mapping:
            logger.warning("Unsupported vacancies grouping field: %s", group_by_field)
            return {"labels": [], "values": []}
        
        # Get vacancies data with filtering
        vacancies_data = await self.engine._execute_vacancies_query(filter_expr)
        
        # Apply field-specific processing
        field_config = field_mapping[group_by_field]
        mapping = None
        
        if field_config.get("mapping_func"):
            mapping_func = getattr(self.engine, field_config["mapping_func"])
            mapping = await mapping_func()
        
        # Filter empty values if specified
        if field_config.get("filter_empty"):
            vacancies_data = [vac for vac in vacancies_data if vac.get(group_by_field)]
        
        return await self._build_chart_data(vacancies_data, group_by_field, mapping, limit=limit)
    
    # DEPRECATED: Use execute_grouped_query instead
    async def execute_chart_data(self, chart_spec: Dict[str, Any]) -> Dict[str, Any]:
        """DEPRECATED: Use execute_grouped_query instead for better flexibility"""
        logger.warning("execute_chart_data is deprecated. Use execute_grouped_query instead.")
        
        # Convert old format to new format and delegate
        x_axis_spec = chart_spec.get("x_axis", {})
        x_field = x_axis_spec.get("field")
        
        # Map old field names to new grouped query format
        field_mapping = {
            "status": {"entity": "applicants", "group_by": {"field": "status_id"}},
            "recruiter": {"entity": "applicants", "group_by": {"field": "recruiter_name"}},
            "coworkers": {"entity": "applicants", "group_by": {"field": "recruiter_name"}},
            "company": {"entity": "vacancies", "group_by": {"field": "company"}},
            "divisions": {"entity": "applicants", "group_by": {"field": "division_id"}},
            "account_division": {"entity": "applicants", "group_by": {"field": "division_id"}}
        }
        
        if x_field in field_mapping:
            query_spec = {
                "operation": "count",
                **field_mapping[x_field],
                "filter": chart_spec.get("y_axis", {}).get("filter", {})
            }
            return await self.execute_grouped_query(query_spec)
        
        return {"labels": [], "values": []}
    
    # DEPRECATED CHART HELPERS - Functionality moved to execute_grouped_query
    # These methods are preserved for compatibility but no longer used
    
    # ==================== ROBUST HIRED STATUS DETECTION ====================
    
    async def get_hired_status_ids(self) -> List[int]:
        """Get hired status IDs using robust detection (replaces fragile string matching)"""
        import time
        
        # Check cache first
        current_time = time.time()
        if (self._hired_status_cache is not None and 
            current_time - self._hired_status_cache_time < self.hired_status_config["cache_duration"]):
            logger.debug("Using cached hired status IDs: %s", self._hired_status_cache)
            return self._hired_status_cache
        
        method = self.hired_status_config["method"]
        hired_status_ids = []
        
        try:
            if method == "status_ids" and self.hired_status_config["status_ids"]:
                # Method 1: Use explicitly configured status IDs (most reliable)
                hired_status_ids = self.hired_status_config["status_ids"]
                logger.info("Using configured hired status IDs: %s", hired_status_ids)
                
            elif method == "system_types":
                # Method 2: Use system-level status types (very reliable)
                hired_status_ids = await self._get_hired_status_ids_from_system_types()
                
            elif method == "auto_detect":
                # Method 3: Use only robust system types detection
                hired_status_ids = await self._auto_detect_hired_status_ids()
                
            else:
                logger.warning("Unknown hired status detection method: %s", method)
                hired_status_ids = []
            
            # Cache the result
            self._hired_status_cache = hired_status_ids
            self._hired_status_cache_time = current_time
            
            logger.info("✅ Hired status detection: Found %s hired status IDs using method '%s'", len(hired_status_ids), method)
            return hired_status_ids
            
        except Exception as e:
            logger.error("Hired status detection failed: %s", e)
            return []
    
    async def _auto_detect_hired_status_ids(self) -> List[int]:
        """Auto-detect hired status IDs using only robust system types"""
        
        # Use only system types (most reliable) - method handles its own errors
        system_type_ids = await self._get_hired_status_ids_from_system_types()
        if system_type_ids:
            logger.info("Auto-detect: Found hired statuses via system types")
        else:
            logger.warning("Auto-detect: No hired statuses found via system types")
        return system_type_ids
    
    async def _get_hired_status_ids_from_system_types(self) -> List[int]:
        """Get hired status IDs using system-level status types (most reliable method)"""
        try:
            status_mapping = await self.engine._get_status_mapping()
            hired_status_ids = []
            
            target_types = self.hired_status_config["system_types"]
            
            for status_id, status_info in status_mapping.items():
                if not isinstance(status_info, dict):
                    continue
                
                status_type = status_info.get("type", "").lower()
                
                # Check if status type matches any of our target hired types
                if status_type in [t.lower() for t in target_types]:
                    hired_status_ids.append(status_id)
                    status_name = status_info.get("name", f"Status {status_id}")
                    logger.debug("System type match: '%s' (type: %s) -> hired status ID %s", status_name, status_type, status_id)
            
            if hired_status_ids:
                logger.info("✅ System types: Found %s hired statuses using stable type field", len(hired_status_ids))
            else:
                logger.debug("No statuses found with configured system types")
            
            return hired_status_ids
            
        except Exception as e:
            logger.debug("System types detection failed: %s", e)
            return []
    
    
    
    
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

