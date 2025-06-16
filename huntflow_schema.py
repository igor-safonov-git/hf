"""
Huntflow Virtual Schema using SQLAlchemy Core
Maps Huntflow API endpoints to virtual SQL tables
"""
from sqlalchemy import MetaData, Table, Column, Integer, String, DateTime, Boolean, Float
from sqlalchemy.sql import select, func, and_, or_
from sqlalchemy.sql.visitors import traverse
from sqlalchemy.sql.elements import BinaryExpression, BindParameter
from sqlalchemy.sql.operators import eq, in_op, gt, lt, ge, le
from typing import Dict, Any, List, Optional, Set
import asyncio
import logging
import time
from datetime import datetime

# Configure logging for this module
logger = logging.getLogger(__name__)

# Example logging configuration (users can customize):
# logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
# To see debug details: logging.getLogger('huntflow_schema').setLevel(logging.DEBUG)


class TTLCache:
    """Thread-safe cache with TTL (Time To Live) and concurrency protection"""
    
    def __init__(self, ttl_seconds: int = 300):  # 5 minutes default TTL
        self.ttl = ttl_seconds
        self._data = {}
        self._timestamps = {}
        self._locks = {}  # Per-key locks to prevent duplicate API calls
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired"""
        if key not in self._timestamps:
            return True
        return time.time() - self._timestamps[key] > self.ttl
    
    async def get_or_fetch(self, key: str, fetch_func):
        """Get cached value or fetch using provided async function with concurrency protection"""
        # Check if we have valid cached data
        if key in self._data and not self._is_expired(key):
            logger.debug(f"Cache HIT for {key}")
            return self._data[key]
        
        # Get or create lock for this key to prevent duplicate API calls
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        
        lock = self._locks[key]
        
        async with lock:
            # Double-check after acquiring lock (another coroutine might have fetched)
            if key in self._data and not self._is_expired(key):
                logger.debug(f"Cache HIT after lock for {key}")
                return self._data[key]
            
            # Cache miss or expired - fetch new data
            logger.debug(f"Cache MISS for {key} - fetching...")
            try:
                data = await fetch_func()
                self._data[key] = data
                self._timestamps[key] = time.time()
                logger.debug(f"Cache STORED for {key}")
                return data
            except Exception as e:
                logger.error(f"Failed to fetch data for cache key {key}: {e}")
                # Return stale data if available, otherwise raise
                if key in self._data:
                    logger.warning(f"Using stale cache data for {key}")
                    return self._data[key]
                raise
    
    def invalidate(self, key: str = None):
        """Invalidate cache entry or entire cache"""
        if key:
            self._data.pop(key, None)
            self._timestamps.pop(key, None)
            logger.debug(f"Cache invalidated for {key}")
        else:
            self._data.clear()
            self._timestamps.clear()
            logger.debug("Entire cache invalidated")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        now = time.time()
        expired_count = sum(1 for ts in self._timestamps.values() if now - ts > self.ttl)
        return {
            'total_entries': len(self._data),
            'expired_entries': expired_count,
            'valid_entries': len(self._data) - expired_count,
            'ttl_seconds': self.ttl
        }

class HuntflowVirtualEngine:
    """Virtual SQL engine that translates SQLAlchemy expressions to Huntflow API calls"""
    
    def __init__(self, hf_client):
        self.hf_client = hf_client
        self.metadata = MetaData()
        
        # Define virtual tables that map to Huntflow API endpoints
        # Based on OpenAPI spec: applicants/search returns ApplicantSearchItem - NO STATUS FIELDS
        self.applicants = Table('applicants', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('first_name', String),
            Column('last_name', String),
            Column('middle_name', String),  # Available in search response
            Column('birthday', String),     # Available in search response
            Column('phone', String),        # Available in search response
            Column('skype', String),        # Available in search response
            Column('email', String),        # Available in search response
            Column('money', String),        # Salary expectation in search response
            Column('position', String),     # Available in search response
            Column('company', String),      # Available in search response
            Column('photo', Integer),       # Photo ID in search response
            Column('photo_url', String),    # Available in search response
            Column('created', DateTime),
            # Required ApplicantItem fields from individual /applicants/{id} calls
            Column('account', Integer),           # Organization ID
            Column('tags', String),              # List of tags (JSON string)
            Column('external', String),          # Resume data (JSON string)
            Column('agreement', String),         # Agreement state (JSON string)
            Column('doubles', String),           # List of duplicates (JSON string)
            Column('social', String),            # Social accounts (JSON string)
            # Computed fields from logs or individual calls
            Column('source_id', Integer),      # From logs or individual call
            Column('recruiter_id', Integer),   # From logs or individual call
            Column('recruiter_name', String),  # Computed from coworkers mapping
            Column('source_name', String),     # Computed from sources mapping
        )
        
        self.vacancies = Table('vacancies', self.metadata,
            Column('id', Integer, primary_key=True),     # Required field per OpenAPI
            Column('position', String),                  # Required field per OpenAPI spec
            Column('company', String),                   # Optional field per OpenAPI
            Column('account_division', Integer),         # Optional field per OpenAPI
            Column('account_region', Integer),           # Optional field per OpenAPI  
            Column('money', String),                     # Optional field per OpenAPI
            Column('priority', Integer),                 # Optional field: 0-1 range per OpenAPI
            Column('hidden', Boolean),                   # Optional field: default false per OpenAPI
            Column('state', String),                     # Optional field per OpenAPI
            Column('created', DateTime),                 # Required field per OpenAPI
            Column('multiple', Boolean),                 # Optional field per OpenAPI
            Column('parent', Integer),                   # Optional field per OpenAPI
            Column('account_vacancy_status_group', Integer),  # Optional field per OpenAPI
            Column('additional_fields_list', String),   # Optional field per OpenAPI spec
            # Additional fields from VacancyItem that were missing
            Column('updated', DateTime),                 # Optional field per OpenAPI
            Column('body', String),                      # Optional field: responsibilities in HTML
            Column('requirements', String),              # Optional field: requirements in HTML
            Column('conditions', String),                # Optional field: conditions in HTML
            Column('files', String),                     # Optional field: list as JSON string
            Column('coworkers', String),                 # Optional field: list as JSON string
            Column('source', Integer),                   # Optional field: vacancy source ID
            Column('blocks', String),                    # Optional field: affiliate vacancies as JSON
            Column('vacancy_request', Integer)           # Optional field: vacancy request ID
        )
        
        self.status_mapping = Table('status_mapping', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String),
            Column('type', String),                      # Required per OpenAPI VacancyStatus
            Column('removed', String),                   # Optional per OpenAPI VacancyStatus
            Column('order', Integer),                    # Required per OpenAPI VacancyStatus  
            Column('stay_duration', Integer)             # Optional per OpenAPI VacancyStatus (null=unlimited)
        )
        
        self.recruiters = Table('recruiters', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String),           # Correct field name per OpenAPI CoworkerResponse
            Column('email', String),          # Correct field name per OpenAPI
            Column('member', Integer),        # User ID per OpenAPI CoworkerResponse
            Column('type', String),           # Correct field name (not 'role') per OpenAPI
            Column('head', Integer),          # Head user ID per OpenAPI
            Column('meta', String),           # Additional meta information (JSON string)
            Column('permissions', String),    # Coworker permissions (JSON string)
            Column('full_name', String)       # Computed field
        )
        
        # Add sources table per CLAUDE.md line 121 - Updated per OpenAPI spec
        self.sources = Table('sources', self.metadata,
            Column('id', Integer, primary_key=True),     # Required per OpenAPI
            Column('name', String),                      # Required per OpenAPI
            Column('type', String),                      # Required per OpenAPI
            Column('foreign', String)                    # Missing field from OpenAPI spec
        )
        
        # Add divisions table per CLAUDE.md line 124 - Updated per OpenAPI spec
        self.divisions = Table('divisions', self.metadata,
            Column('id', Integer, primary_key=True),     # Required per OpenAPI
            Column('name', String),                      # Required per OpenAPI
            Column('order', Integer),                    # Required per OpenAPI
            Column('active', Boolean),                   # Required per OpenAPI
            Column('deep', Integer),                     # Required per OpenAPI
            Column('parent', Integer),                   # Optional per OpenAPI
            Column('foreign', String),                   # Optional per OpenAPI
            Column('meta', String)                       # Optional per OpenAPI (object as JSON string)
        )
        
        # Add applicant tags table per OpenAPI spec
        self.applicant_tags = Table('applicant_tags', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String),
            Column('color', String)
        )
        
        # Add offers table per OpenAPI spec
        self.offers = Table('offers', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('applicant_id', Integer),
            Column('vacancy_id', Integer),
            Column('status', String),
            Column('created', DateTime),
            Column('updated', DateTime)
        )
        
        # Add applicant links virtual table for status tracking per OpenAPI ApplicantLink schema
        self.applicant_links = Table('applicant_links', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('applicant_id', Integer),
            Column('status', Integer),            # Required per OpenAPI
            Column('updated', DateTime),          # Required per OpenAPI  
            Column('changed', DateTime),          # Required per OpenAPI
            Column('vacancy', Integer)            # Required per OpenAPI
        )
        
        # Add regions table per short-spec.md
        self.regions = Table('regions', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String),
            Column('order', Integer),
            Column('foreign', String)
        )
        
        # Add rejection reasons table per short-spec.md
        self.rejection_reasons = Table('rejection_reasons', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String),
            Column('order', Integer)
        )
        
        # Add dictionaries table per short-spec.md
        self.dictionaries = Table('dictionaries', self.metadata,
            Column('code', String, primary_key=True),
            Column('name', String),
            Column('items', String)  # JSON string of dictionary items
        )
        
        # Add applicant responses table per short-spec.md
        self.applicant_responses = Table('applicant_responses', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('applicant_id', Integer),
            Column('vacancy_id', Integer),
            Column('source', String),
            Column('created', DateTime),
            Column('response_data', String)  # JSON string
        )
        
        # Add vacancy logs table per short-spec.md  
        self.vacancy_logs = Table('vacancy_logs', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('vacancy_id', Integer),
            Column('type', String),
            Column('created', DateTime),
            Column('account_info', String),  # JSON string
            Column('data', String)  # JSON string of log data
        )
        
        # Add status groups table per short-spec.md
        self.status_groups = Table('status_groups', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String),
            Column('order', Integer),
            Column('statuses', String)  # JSON array of status IDs
        )
        
        # Add missing vacancy detail tables per your analysis
        self.vacancy_periods = Table('vacancy_periods', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('vacancy_id', Integer),
            Column('period_type', String),  # work, hold, closed
            Column('start_date', DateTime),
            Column('end_date', DateTime),
            Column('duration_days', Integer)
        )
        
        self.vacancy_frames = Table('vacancy_frames', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('vacancy_id', Integer),
            Column('created', DateTime),
            Column('is_current', Boolean),
            Column('data', String)  # JSON string of frame data
        )
        
        self.vacancy_quotas = Table('vacancy_quotas', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('vacancy_id', Integer),
            Column('frame_id', Integer),
            Column('quota_value', Integer),
            Column('filled', Integer),
            Column('created', DateTime)
        )
        
        # Add account action logs table
        self.action_logs = Table('action_logs', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('type', String),
            Column('created', DateTime),
            Column('account_info', String),  # JSON string
            Column('data', String)  # JSON string of log data
        )
        
        # TTL Cache with concurrency protection (5 min TTL by default)
        self._cache = TTLCache(ttl_seconds=300)
        
        # Cache invalidation methods for users
        self.invalidate_cache = self._cache.invalidate
        self.get_cache_stats = self._cache.get_stats
        
        # Legacy cache attributes (for methods not yet converted to TTL cache)
        self._sources_cache = None
        self._divisions_cache = None
        self._tags_cache = None
        self._regions_cache = None
        self._rejection_reasons_cache = None
        self._dictionaries_cache = None
        self._status_groups_cache = None
        self._action_logs_cache = None
    
    async def execute(self, query) -> List[Dict[str, Any]]:
        """Execute SQLAlchemy query by translating to API calls"""
        
        # Determine which table is being queried
        if self._query_references_table(query, 'applicants'):
            return await self._execute_applicants_query(query)
        elif self._query_references_table(query, 'recruiters'):
            return await self._execute_recruiters_query(query)
        elif self._query_references_table(query, 'vacancies'):
            return await self._execute_vacancies_query(query)
        elif self._query_references_table(query, 'divisions'):
            return await self._execute_divisions_query(query)
        elif self._query_references_table(query, 'applicant_tags'):
            return await self._execute_tags_query(query)
        elif self._query_references_table(query, 'sources'):
            return await self._execute_sources_query(query)
        elif self._query_references_table(query, 'regions'):
            return await self._execute_regions_query(query)
        elif self._query_references_table(query, 'rejection_reasons'):
            return await self._execute_rejection_reasons_query(query)
        elif self._query_references_table(query, 'dictionaries'):
            return await self._execute_dictionaries_query(query)
        elif self._query_references_table(query, 'status_groups'):
            return await self._execute_status_groups_query(query)
        elif self._query_references_table(query, 'applicant_responses'):
            return await self._execute_applicant_responses_query(query)
        elif self._query_references_table(query, 'vacancy_logs'):
            return await self._execute_vacancy_logs_query(query)
        elif self._query_references_table(query, 'vacancy_periods'):
            return await self._execute_vacancy_periods_query(query)
        elif self._query_references_table(query, 'vacancy_frames'):
            return await self._execute_vacancy_frames_query(query)
        elif self._query_references_table(query, 'vacancy_quotas'):
            return await self._execute_vacancy_quotas_query(query)
        elif self._query_references_table(query, 'action_logs'):
            return await self._execute_action_logs_query(query)
        else:
            return []
    
    def _query_references_table(self, query, table_name: str) -> bool:
        """Check if a specific table is referenced in the query using proper AST traversal"""
        table_names = set()
        
        def visit_table(element):
            if hasattr(element, 'name'):
                table_names.add(element.name)
        
        # Traverse the query AST to find all table references
        traverse(query, {}, {'table': visit_table})
        return table_name in table_names
    
    def _extract_filters_from_query(self, query) -> Dict[str, Any]:
        """Extract WHERE clause filters from SQLAlchemy query using proper AST traversal"""
        filters = {}
        
        def visit_binary_expr(element):
            """Visit binary expressions (comparisons) in the WHERE clause"""
            if isinstance(element, BinaryExpression):
                # Get the left side (column) and right side (value)
                left = element.left
                right = element.right
                operator = element.operator
                
                # Extract column name
                column_name = None
                if hasattr(left, 'name'):
                    column_name = left.name
                elif hasattr(left, 'key'):
                    column_name = left.key
                
                # Extract value
                value = None
                if isinstance(right, BindParameter):
                    value = right.value
                elif hasattr(right, 'value'):
                    value = right.value
                else:
                    # Try to get the actual value
                    try:
                        value = right
                    except:
                        pass
                
                if column_name and value is not None:
                    # Handle different operators
                    if operator is eq:
                        filters[column_name] = value
                    elif operator is in_op:
                        # Handle IN clauses
                        if isinstance(value, (list, tuple)):
                            filters[f"{column_name}s"] = list(value)  # plural for IN
                        else:
                            filters[column_name] = value
                    elif operator in (gt, ge):
                        filters[f"{column_name}_min"] = value
                    elif operator in (lt, le):
                        filters[f"{column_name}_max"] = value
                        
                    logger.debug(f"Extracted filter: {column_name} {operator} {value}")
        
        # Traverse the query AST to find all binary expressions
        traverse(query, {}, {'binary': visit_binary_expr})
        
        # Handle WHERE clause specifically if it exists
        if hasattr(query, 'whereclause') and query.whereclause is not None:
            traverse(query.whereclause, {}, {'binary': visit_binary_expr})
        
        logger.debug(f"Extracted filters from query: {filters}")
        return filters
    
    async def _get_all_vacancy_ids(self) -> List[int]:
        """Get all vacancy IDs for queries that don't specify vacancy_id"""
        vacancies_data = await self._execute_vacancies_query(None)
        return [v.get('id') for v in vacancies_data if v.get('id')]
    
    async def _get_all_applicant_ids_simple(self) -> List[int]:
        """Get all applicant IDs - now much more efficient thanks to /applicants endpoint"""
        applicants_data = await self._get_applicants_data()
        return [a.get('id') for a in applicants_data if a.get('id')]
    
    async def _get_applicants_data(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """OPTIMAL ARCHITECTURAL FIX: Use /applicants endpoint with rich ApplicantItem data.
        This eliminates the N+1 problem by getting links array for ALL applicants in ~100 calls instead of ~10,000.
        """
        cache_key = f"applicants_{hash(str(filters))}"
        
        async def fetch_applicants():
            return await self._fetch_applicants_from_api(filters)
            
        return await self._cache.get_or_fetch(cache_key, fetch_applicants)
    
    async def _fetch_applicants_from_api(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        
        logger.info("Using OPTIMAL endpoint: /applicants (includes links array for ALL applicants)")
        
        # 1. CALL THE ARCHITECTURALLY SUPERIOR ENDPOINT
        all_applicants = []
        page = 1
        while True:
            params = {"count": 100, "page": page}
            
            # NOTE: /applicants has less filtering than /applicants/search, 
            # but returns rich ApplicantItem data with links array
            if filters:
                # Support basic filtering available on /applicants endpoint
                for param in ['status', 'vacancy', 'agreement_state']:
                    if param in filters:
                        params[param] = filters[param]
            
            # KEY INSIGHT: Use /applicants instead of /applicants/search
            result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/applicants", params=params)
            
            if isinstance(result, dict):
                items = result.get("items", [])
                if not items:
                    break
                all_applicants.extend(items)
                
                # Standard pagination check
                if len(items) < 100:
                    break
                page += 1
            else:
                break
        
        if not all_applicants:
            logger.warning("No applicants data available from API")
            return []
        
        logger.info(f"Retrieved {len(all_applicants)} applicants with COMPLETE data (no N+1 calls needed)")
        
        # 2. PROCESS THE RICH DATA (NO ADDITIONAL API CALLS NEEDED!)
        enriched_applicants = []
        status_map = await self._get_status_mapping()
        recruiters_map = await self._get_recruiters_mapping()
        sources_map = await self._get_sources_mapping()
        
        for applicant in all_applicants:
            # The 'applicant' object is already the rich ApplicantItem model with links array!
            links = applicant.get('links', [])
            latest_link = max(links, key=lambda x: x.get('updated', ''), default={})
            
            # Extract status data directly from the links array
            status_id = latest_link.get('status', 0)
            vacancy_id = latest_link.get('vacancy', 0)
            status_info = status_map.get(status_id, {'name': 'Unknown'})
            
            enriched = {
                'id': applicant.get('id', 0),
                'first_name': applicant.get('first_name', ''),
                'last_name': applicant.get('last_name', ''),
                'middle_name': applicant.get('middle_name', ''),
                'birthday': applicant.get('birthday', ''),
                'phone': applicant.get('phone', ''),
                'skype': applicant.get('skype', ''),
                'email': applicant.get('email', ''),
                'money': applicant.get('money', ''),
                'position': applicant.get('position', ''),
                'company': applicant.get('company', ''),
                'photo': applicant.get('photo', 0),
                'photo_url': applicant.get('photo_url', ''),
                'created': applicant.get('created', ''),
                # Rich ApplicantItem fields (already available!)
                'account': applicant.get('account', self.hf_client.acc_id),
                'tags': str(applicant.get('tags', [])),
                'external': str(applicant.get('external', [])),
                'agreement': str(applicant.get('agreement', {})),
                'doubles': str(applicant.get('doubles', [])),
                'social': str(applicant.get('social', [])),
                # Status data directly from links array - ALL applicants have this!
                'status_id': status_id,
                'vacancy_id': vacancy_id,
                'status_name': status_info.get('name', 'Unknown'),
                # Additional computed fields
                'source_id': applicant.get('source', 0),
                'recruiter_id': 0,  # Could extract from logs if needed
                'recruiter_name': 'Unknown',
                'source_name': sources_map.get(applicant.get('source', 0), 'Unknown'),
            }
            enriched_applicants.append(enriched)
        
        logger.info(f"PERFORMANCE WIN: Fetched {len(enriched_applicants)} applicants with ~{page} API calls instead of ~{len(all_applicants)} calls!")
        return enriched_applicants
    
    # REMOVED: Complex N+1 methods no longer needed thanks to architectural fix!
    # The /applicants endpoint provides links array directly, eliminating the need for:
    # - _get_all_applicant_ids_with_cursor()
    # - _get_all_applicant_links() 
    # This reduces API calls from ~10,000 to ~100 - a 100x performance improvement!
    
    # Removed demo applicants generation - using real API only
    
    async def _get_status_mapping(self) -> Dict[int, str]:
        """Get status ID to name mapping from actual API response"""
        async def fetch_statuses():
            return await self._fetch_status_mapping_from_api()
            
        return await self._cache.get_or_fetch("status_mapping", fetch_statuses)
    
    async def _fetch_status_mapping_from_api(self) -> Dict[int, str]:
        
        logger.debug("Fetching actual status mapping from API")
        # Use correct endpoint from official API specification
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/vacancies/statuses")
        
        logger.debug(f"Status API response: {result}")
        
        if isinstance(result, dict):
            if result.get("items"):
                statuses = result.get("items", [])
                # Create complete status mapping with all OpenAPI fields
                status_cache = {}
                for s in statuses:
                    if s.get("id") and s.get("name"):
                        status_cache[s.get("id")] = {
                            'name': s.get("name"),
                            'type': s.get("type", ""),                    # Required per OpenAPI
                            'removed': s.get("removed", ""),             # Optional per OpenAPI  
                            'order': s.get("order", 0),                  # Required per OpenAPI
                            'stay_duration': s.get("stay_duration", 0)   # Optional per OpenAPI
                        }
                logger.info(f"Got {len(status_cache)} actual statuses from API: {[s['name'] for s in status_cache.values()]}")
            else:
                logger.error(f"API failed to return status data. Response: {result}")
                logger.error("API authentication or endpoint issue - no statuses available")
                status_cache = {}
        else:
            logger.error(f"API response is not dict, type: {type(result)}")
            status_cache = {}
        
        return status_cache
    
    async def _get_recruiters_mapping(self) -> Dict[int, str]:
        """Get recruiter ID to name mapping from actual API response"""
        async def fetch_recruiters():
            return await self._fetch_recruiters_mapping_from_api()
            
        return await self._cache.get_or_fetch("recruiters_mapping", fetch_recruiters)
    
    async def _fetch_recruiters_mapping_from_api(self) -> Dict[int, str]:
        
        logger.debug("Fetching actual recruiters from API")
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/coworkers")
        
        logger.debug(f"Recruiters API response: {result}")
        
        recruiters_cache = {}
        if isinstance(result, dict):
            if result.get("items"):
                recruiters = result.get("items", [])
                recruiters_cache = {
                    r.get("id"): r.get('name', 'Unknown')  # Use name field per OpenAPI
                    for r in recruiters if r.get('id')
                }
                logger.info(f"Got {len(recruiters_cache)} actual recruiters from API: {list(recruiters_cache.values())}")
            else:
                logger.error(f"API failed to return recruiter data. Response: {result}")
                logger.error("API authentication or endpoint issue - no recruiters available")
                recruiters_cache = {}
        else:
            logger.error(f"Recruiters API response is not dict, type: {type(result)}")
            recruiters_cache = {}
        
        return recruiters_cache
    
    async def _get_sources_mapping(self) -> Dict[int, str]:
        """Get source ID to name mapping from actual API response"""
        async def fetch_sources():
            return await self._fetch_sources_mapping_from_api()
            
        return await self._cache.get_or_fetch("sources_mapping", fetch_sources)
    
    async def _fetch_sources_mapping_from_api(self) -> Dict[int, str]:
        
        logger.debug("Fetching actual sources from API")
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/applicants/sources")
        
        logger.debug(f"Sources API response: {result}")
        
        if isinstance(result, dict):
            if result.get("items"):
                sources = result.get("items", [])
                self._sources_cache = {
                    s.get("id"): s.get("name", "Unknown")
                    for s in sources if s.get('id') and s.get('name')
                }
                logger.info(f"Got {len(self._sources_cache)} actual sources from API: {list(self._sources_cache.values())}")
            else:
                logger.error(f"API failed to return source data. Response: {result}")
                self._sources_cache = {}
        else:
            logger.error(f"Sources API response is not dict, type: {type(result)}")
            self._sources_cache = {}
        
        return self._sources_cache
    
    async def _get_divisions_mapping(self) -> Dict[int, str]:
        """Get division ID to name mapping from actual API response"""
        if self._divisions_cache is not None:
            return self._divisions_cache
        
        logger.debug("Fetching actual divisions from API")
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/divisions")
        
        if isinstance(result, dict) and result.get("items"):
            divisions = result.get("items", [])
            self._divisions_cache = {
                d.get("id"): d.get("name", "Unknown")
                for d in divisions if d.get('id') and d.get('name')
            }
            logger.info(f"Got {len(self._divisions_cache)} divisions from API")
        else:
            self._divisions_cache = {}
        
        return self._divisions_cache
    
    async def _get_tags_mapping(self) -> Dict[int, str]:
        """Get applicant tags from actual API response"""
        if self._tags_cache is not None:
            return self._tags_cache
        
        logger.debug("Fetching applicant tags from API")
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/applicants/tags")
        
        if isinstance(result, dict) and result.get("items"):
            tags = result.get("items", [])
            self._tags_cache = {
                t.get("id"): t.get("name", "Unknown")
                for t in tags if t.get('id') and t.get('name')
            }
            logger.info(f"Got {len(self._tags_cache)} applicant tags from API")
        else:
            self._tags_cache = {}
        
        return self._tags_cache
    
    async def _get_applicant_data_from_logs(self, applicant_id: int) -> dict:
        """Get current status, vacancy, source, and recruiter from applicant logs"""
        try:
            # Get applicant activity logs
            logs = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/applicants/{applicant_id}/logs")
            
            result = {
                'status_id': 0,
                'status_name': 'Unknown',
                'vacancy_id': 0,
                'source_id': 0,
                'recruiter_id': 0
            }
            
            if isinstance(logs, dict) and logs.get("items"):
                # Find most recent entry with each type of info
                for log_entry in logs.get("items", []):
                    # Extract status
                    if log_entry.get("status") and result['status_id'] == 0:
                        result['status_id'] = log_entry.get("status")
                        status_map = await self._get_status_mapping()
                        status_info = status_map.get(result['status_id'], {'name': 'Unknown'})
                        result['status_name'] = status_info.get('name', 'Unknown')
                    
                    # Extract vacancy relationship
                    if log_entry.get("vacancy") and result['vacancy_id'] == 0:
                        result['vacancy_id'] = log_entry.get("vacancy")
                    
                    # Extract source (may be string in logs)
                    if log_entry.get("source") and result['source_id'] == 0:
                        source = log_entry.get("source")
                        if isinstance(source, int):
                            result['source_id'] = source
                        # If source is string, we'd need to map it back to ID
                    
                    # Extract recruiter from account_info
                    if log_entry.get("account_info") and result['recruiter_id'] == 0:
                        account_info = log_entry.get("account_info")
                        if isinstance(account_info, dict) and account_info.get("id"):
                            result['recruiter_id'] = account_info.get("id")
                        
            return result
        except Exception as e:
            logger.warning(f"Failed to get data from logs for applicant {applicant_id}: {e}")
            return {
                'status_id': 0,
                'status_name': 'Unknown',
                'vacancy_id': 0,
                'source_id': 0,
                'recruiter_id': 0
            }
    
    async def _get_applicant_links_from_individual_call(self, applicant_id: int) -> List[Dict[str, Any]]:
        """Get complete links array from individual applicant API call per OpenAPI ApplicantItem schema"""
        try:
            # Get individual applicant data which includes links array per OpenAPI spec
            applicant = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/applicants/{applicant_id}")
            
            if isinstance(applicant, dict) and applicant.get("links"):
                # Return complete links array with all ApplicantLink fields per OpenAPI:
                # - id, status (required), updated (required), changed (required), vacancy (required)
                links = []
                for link in applicant.get("links", []):
                    links.append({
                        'id': link.get('id', 0),
                        'status': link.get('status', 0),        # Required per OpenAPI
                        'updated': link.get('updated', ''),     # Required per OpenAPI  
                        'changed': link.get('changed', ''),     # Required per OpenAPI
                        'vacancy': link.get('vacancy', 0)       # Required per OpenAPI
                    })
                return links
                        
            return []
        except Exception as e:
            logger.warning(f"Failed to get links from individual call for applicant {applicant_id}: {e}")
            return []
    
    async def _execute_applicants_query(self, query) -> List[Dict[str, Any]]:
        """Execute query against applicants virtual table"""
        applicants_data = await self._get_applicants_data()
        
        # For now, return raw data - we'll add filtering/aggregation next
        # This would be where we parse the SQLAlchemy query and apply filters
        
        return applicants_data
    
    async def _execute_recruiters_query(self, query, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute query against recruiters virtual table with optional filters"""
        recruiters_map = await self._get_recruiters_mapping()
        
        # Prepare parameters with filters from short-spec.md
        params = {}
        if filters:
            # Support documented coworkers parameters: type, vacancy_id, fetch_permissions, count, page
            for param in ['type', 'vacancy_id', 'fetch_permissions', 'count', 'page']:
                if param in filters:
                    params[param] = filters[param]
        
        # Get actual coworkers data to return proper fields
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/coworkers", params=params if params else None)
        
        if isinstance(result, dict) and result.get("items"):
            return [
                {
                    'id': r.get('id', 0),
                    'name': r.get('name', ''),             # Correct field per OpenAPI
                    'email': r.get('email', ''),
                    'member': r.get('member', 0),          # User ID per OpenAPI
                    'type': r.get('type', ''),             # Correct field name (not 'role')
                    'head': r.get('head', 0),              # Head user ID per OpenAPI
                    'meta': str(r.get('meta', {})),        # Additional meta information as JSON string
                    'permissions': str(r.get('permissions', [])),  # Coworker permissions as JSON string
                    'full_name': r.get('name', '')         # Use name field directly
                }
                for r in result.get("items", []) if r.get('id')
            ]
        else:
            return []
    
    async def _execute_vacancies_query(self, query, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute query against vacancies virtual table with optional filters"""
        # Get all vacancies with proper pagination
        all_vacancies = []
        page = 1
        while True:
            params = {"count": 100, "page": page}
            
            # Add filters from short-spec.md if provided
            if filters:
                # Support documented vacancy parameters: mine, state
                for param in ['mine', 'state']:
                    if param in filters:
                        params[param] = filters[param]
            
            result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/vacancies", params=params)
            
            if isinstance(result, dict):
                items = result.get("items", [])
                if not items:
                    break
                all_vacancies.extend(items)
                
                # Check if we have more pages
                total_pages = result.get("total_pages", 0)
                if page >= total_pages:
                    break
                    
                page += 1
            else:
                break
        
        # Map API response to schema fields per OpenAPI VacancyItem spec
        mapped_vacancies = []
        for vacancy in all_vacancies:
            mapped_vacancy = {
                'id': vacancy.get('id', 0),
                'position': vacancy.get('position', ''),                     # Required
                'company': vacancy.get('company', ''),                       # Optional
                'account_division': vacancy.get('account_division', 0),      # Optional
                'account_region': vacancy.get('account_region', 0),          # Optional
                'money': vacancy.get('money', ''),                           # Optional
                'priority': vacancy.get('priority', 0),                      # Optional: 0-1
                'hidden': vacancy.get('hidden', False),                      # Optional: default false
                'state': vacancy.get('state', 'OPEN'),                       # Optional: default OPEN
                'created': vacancy.get('created', ''),                       # Required
                'multiple': vacancy.get('multiple', False),                  # Optional
                'parent': vacancy.get('parent', 0),                          # Optional
                'account_vacancy_status_group': vacancy.get('account_vacancy_status_group', 0),  # Optional
                'additional_fields_list': str(vacancy.get('additional_fields_list', [])),  # Convert list to string
                # New fields from complete VacancyItem schema
                'updated': vacancy.get('updated', ''),                       # Optional
                'body': vacancy.get('body', ''),                             # Optional: HTML responsibilities
                'requirements': vacancy.get('requirements', ''),             # Optional: HTML requirements
                'conditions': vacancy.get('conditions', ''),                 # Optional: HTML conditions
                'files': str(vacancy.get('files', [])),                      # Optional: convert list to JSON string
                'coworkers': str(vacancy.get('coworkers', [])),               # Optional: convert list to JSON string
                'source': vacancy.get('source', 0),                          # Optional: source ID
                'blocks': str(vacancy.get('blocks', [])),                     # Optional: affiliate vacancies as JSON
                'vacancy_request': vacancy.get('vacancy_request', 0)         # Optional: vacancy request ID
            }
            mapped_vacancies.append(mapped_vacancy)
        
        return mapped_vacancies
    
    async def _execute_divisions_query(self, query, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute query against divisions virtual table with optional filters"""
        # Prepare parameters with filters from short-spec.md
        params = {}
        if filters:
            # Support documented divisions parameters: only_available
            for param in ['only_available']:
                if param in filters:
                    params[param] = filters[param]
        
        # Get full divisions data from API to return all OpenAPI fields
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/divisions", params=params if params else None)
        
        if isinstance(result, dict) and result.get("items"):
            return [
                {
                    'id': d.get('id', 0),
                    'name': d.get('name', ''),                    # Required
                    'order': d.get('order', 0),                  # Required
                    'active': d.get('active', True),             # Required
                    'deep': d.get('deep', 0),                    # Required
                    'parent': d.get('parent', 0),                # Optional
                    'foreign': d.get('foreign', ''),             # Optional
                    'meta': str(d.get('meta', {}))               # Optional: convert object to string
                }
                for d in result.get("items", []) if d.get('id')
            ]
        else:
            return []
    
    async def _execute_tags_query(self, query) -> List[Dict[str, Any]]:
        """Execute query against applicant_tags virtual table"""
        tags_map = await self._get_tags_mapping()
        
        # Get full tag data from API
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/applicants/tags")
        
        if isinstance(result, dict) and result.get("items"):
            return [
                {
                    'id': t.get('id', 0),
                    'name': t.get('name', ''),
                    'color': t.get('color', '')
                }
                for t in result.get("items", []) if t.get('id')
            ]
        else:
            return []
    
    async def _execute_sources_query(self, query) -> List[Dict[str, Any]]:
        """Execute query against sources virtual table"""
        # Get full sources data from API to return all OpenAPI fields  
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/applicants/sources")
        
        if isinstance(result, dict) and result.get("items"):
            return [
                {
                    'id': s.get('id', 0),
                    'name': s.get('name', ''),                    # Required
                    'type': s.get('type', ''),                    # Required
                    'foreign': s.get('foreign', '')               # Optional per OpenAPI
                }
                for s in result.get("items", []) if s.get('id')
            ]
        else:
            return []
    
    # New endpoint methods from short-spec.md
    
    async def _execute_regions_query(self, query, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute query against regions virtual table"""
        if self._regions_cache is not None:
            return list(self._regions_cache.values())
        
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/regions")
        
        if isinstance(result, dict) and result.get("items"):
            regions = [
                {
                    'id': r.get('id', 0),
                    'name': r.get('name', ''),
                    'order': r.get('order', 0),
                    'foreign': r.get('foreign', '')
                }
                for r in result.get("items", []) if r.get('id')
            ]
            self._regions_cache = {r['id']: r for r in regions}
            return regions
        else:
            self._regions_cache = {}
            return []
    
    async def _execute_rejection_reasons_query(self, query, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute query against rejection_reasons virtual table"""
        if self._rejection_reasons_cache is not None:
            return list(self._rejection_reasons_cache.values())
        
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/rejection_reasons")
        
        if isinstance(result, dict) and result.get("items"):
            reasons = [
                {
                    'id': r.get('id', 0),
                    'name': r.get('name', ''),
                    'order': r.get('order', 0)
                }
                for r in result.get("items", []) if r.get('id')
            ]
            self._rejection_reasons_cache = {r['id']: r for r in reasons}
            return reasons
        else:
            self._rejection_reasons_cache = {}
            return []
    
    async def _execute_dictionaries_query(self, query, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute query against dictionaries virtual table"""
        if self._dictionaries_cache is not None:
            return list(self._dictionaries_cache.values())
        
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/dictionaries")
        
        if isinstance(result, dict) and result.get("items"):
            dictionaries = [
                {
                    'code': d.get('code', ''),
                    'name': d.get('name', ''),
                    'items': str(d.get('items', []))
                }
                for d in result.get("items", []) if d.get('code')
            ]
            self._dictionaries_cache = {d['code']: d for d in dictionaries}
            return dictionaries
        else:
            self._dictionaries_cache = {}
            return []
    
    async def _execute_status_groups_query(self, query, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute query against status_groups virtual table"""
        if self._status_groups_cache is not None:
            return list(self._status_groups_cache.values())
        
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/vacancies/status_groups")
        
        if isinstance(result, dict) and result.get("items"):
            groups = [
                {
                    'id': g.get('id', 0),
                    'name': g.get('name', ''),
                    'order': g.get('order', 0),
                    'statuses': str(g.get('statuses', []))
                }
                for g in result.get("items", []) if g.get('id')
            ]
            self._status_groups_cache = {g['id']: g for g in groups}
            return groups
        else:
            self._status_groups_cache = {}
            return []
    
    async def _execute_applicant_responses_query(self, query, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute query against applicant_responses virtual table"""
        # Extract filters from SQL query
        sql_filters = self._extract_filters_from_query(query)
        if filters:
            sql_filters.update(filters)
        
        # Handle single applicant_id or multiple applicant_ids
        applicant_id = sql_filters.get('applicant_id')
        applicant_ids = sql_filters.get('applicant_ids', [])
        
        if applicant_id:
            applicant_ids = [applicant_id]
        elif not applicant_ids:
            # Without applicant_id(s), return empty result
            return []
        
        # Aggregate results from multiple applicants
        all_responses = []
        for aid in applicant_ids:
            responses = await self.get_applicant_responses(aid)
            all_responses.extend(responses)
        
        return all_responses
    
    async def _execute_vacancy_logs_query(self, query, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute query against vacancy_logs virtual table"""
        # Extract filters from SQL query
        sql_filters = self._extract_filters_from_query(query)
        if filters:
            sql_filters.update(filters)
        
        # Handle single vacancy_id or multiple vacancy_ids
        vacancy_id = sql_filters.get('vacancy_id')
        vacancy_ids = sql_filters.get('vacancy_ids', [])
        
        if vacancy_id:
            vacancy_ids = [vacancy_id]
        elif not vacancy_ids:
            # Without vacancy_id(s), return empty result
            return []
        
        date_begin = sql_filters.get('date_begin')
        date_end = sql_filters.get('date_end')
        
        # Aggregate results from multiple vacancies
        all_logs = []
        for vid in vacancy_ids:
            logs = await self.get_vacancy_logs(vid, date_begin, date_end)
            all_logs.extend(logs)
        
        return all_logs
    
    # Enhanced methods for individual entity access
    
    async def get_applicant_responses(self, applicant_id: int, count: int = 100, next_page_cursor: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get applicant responses from job sites per short-spec.md"""
        params = {'count': count}
        if next_page_cursor:
            params['next_page_cursor'] = next_page_cursor
        
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/applicants/{applicant_id}/responses", params=params)
        
        if isinstance(result, dict) and result.get("items"):
            return [
                {
                    'id': r.get('id', 0),
                    'applicant_id': applicant_id,
                    'vacancy_id': r.get('vacancy_id', 0),
                    'source': r.get('source', ''),
                    'created': r.get('created', ''),
                    'response_data': str(r)
                }
                for r in result.get("items", [])
            ]
        return []
    
    async def get_vacancy_logs(self, vacancy_id: int, date_begin: Optional[str] = None, date_end: Optional[str] = None, count: int = 100, page: int = 1) -> List[Dict[str, Any]]:
        """Get vacancy event logs per short-spec.md"""
        params = {'count': count, 'page': page}
        if date_begin:
            params['date_begin'] = date_begin
        if date_end:
            params['date_end'] = date_end
        
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/vacancies/{vacancy_id}/logs", params=params)
        
        if isinstance(result, dict) and result.get("items"):
            return [
                {
                    'id': log.get('id', 0),
                    'vacancy_id': vacancy_id,
                    'type': log.get('type', ''),
                    'created': log.get('created', ''),
                    'account_info': str(log.get('account_info', {})),
                    'data': str(log)
                }
                for log in result.get("items", [])
            ]
        return []
    
    async def get_applicant_tags_for_individual(self, applicant_id: int) -> List[Dict[str, Any]]:
        """Get tags for specific applicant per short-spec.md"""
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/applicants/{applicant_id}/tags")
        
        if isinstance(result, dict) and result.get("items"):
            return [
                {
                    'id': t.get('id', 0),
                    'name': t.get('name', ''),
                    'color': t.get('color', '')
                }
                for t in result.get("items", [])
            ]
        return []
    
    async def get_applicant_external_resume(self, applicant_id: int, external_id: str) -> Dict[str, Any]:
        """Get specific parsed resume per short-spec.md"""
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/applicants/{applicant_id}/externals/{external_id}")
        
        if isinstance(result, dict):
            return result
        return {}
    
    # Implement missing vacancy detail endpoints identified in analysis
    
    async def _execute_vacancy_periods_query(self, query, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute query against vacancy_periods virtual table"""
        # Extract filters from SQL query
        sql_filters = self._extract_filters_from_query(query)
        if filters:
            sql_filters.update(filters)
        
        # Handle single vacancy_id or multiple vacancy_ids
        vacancy_id = sql_filters.get('vacancy_id')
        vacancy_ids = sql_filters.get('vacancy_ids', [])
        
        if vacancy_id:
            vacancy_ids = [vacancy_id]
        elif not vacancy_ids:
            # Without vacancy_id(s), return empty result
            return []
        
        date_begin = sql_filters.get('date_begin')
        date_end = sql_filters.get('date_end')
        
        if not date_begin or not date_end:
            # Use default date range if not specified
            from datetime import datetime, timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)  # Last year
            date_begin = start_date.strftime('%Y-%m-%d')
            date_end = end_date.strftime('%Y-%m-%d')
        
        # Aggregate results from multiple vacancies
        all_periods = []
        for vid in vacancy_ids:
            periods = await self.get_vacancy_periods(vid, date_begin, date_end)
            all_periods.extend(periods)
        
        return all_periods
    
    async def get_vacancy_periods(self, vacancy_id: int, date_begin: str, date_end: str) -> List[Dict[str, Any]]:
        """Get vacancy periods (work, hold, closed) per API spec"""
        params = {'date_begin': date_begin, 'date_end': date_end}
        
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/vacancies/{vacancy_id}/periods", params=params)
        
        if isinstance(result, dict) and result.get("items"):
            return [
                {
                    'id': p.get('id', 0),
                    'vacancy_id': vacancy_id,
                    'period_type': p.get('type', ''),
                    'start_date': p.get('start_date', ''),
                    'end_date': p.get('end_date', ''),
                    'duration_days': p.get('duration_days', 0)
                }
                for p in result.get("items", [])
            ]
        return []
    
    async def _execute_vacancy_frames_query(self, query, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute query against vacancy_frames virtual table"""
        # Extract filters from SQL query
        sql_filters = self._extract_filters_from_query(query)
        if filters:
            sql_filters.update(filters)
        
        # Handle single vacancy_id or multiple vacancy_ids
        vacancy_id = sql_filters.get('vacancy_id')
        vacancy_ids = sql_filters.get('vacancy_ids', [])
        
        if vacancy_id:
            vacancy_ids = [vacancy_id]
        elif not vacancy_ids:
            # Without vacancy_id(s), return empty result
            return []
        
        # Aggregate results from multiple vacancies
        all_frames = []
        for vid in vacancy_ids:
            frames = await self.get_vacancy_frames(vid)
            all_frames.extend(frames)
        
        return all_frames
    
    async def get_vacancy_frames(self, vacancy_id: int) -> List[Dict[str, Any]]:
        """Get all historical activity frames for a vacancy"""
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/vacancies/{vacancy_id}/frames")
        
        if isinstance(result, dict) and result.get("items"):
            return [
                {
                    'id': f.get('id', 0),
                    'vacancy_id': vacancy_id,
                    'created': f.get('created', ''),
                    'is_current': f.get('is_current', False),
                    'data': str(f)
                }
                for f in result.get("items", [])
            ]
        return []
    
    async def get_vacancy_current_frame(self, vacancy_id: int) -> Dict[str, Any]:
        """Get the most recent activity frame for a vacancy"""
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/vacancies/{vacancy_id}/frame")
        
        if isinstance(result, dict):
            return {
                'id': result.get('id', 0),
                'vacancy_id': vacancy_id,
                'created': result.get('created', ''),
                'is_current': True,
                'data': str(result)
            }
        return {}
    
    async def _execute_vacancy_quotas_query(self, query, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute query against vacancy_quotas virtual table"""
        # Extract filters from SQL query
        sql_filters = self._extract_filters_from_query(query)
        if filters:
            sql_filters.update(filters)
        
        # Handle single vacancy_id or multiple vacancy_ids
        vacancy_id = sql_filters.get('vacancy_id')
        vacancy_ids = sql_filters.get('vacancy_ids', [])
        frame_id = sql_filters.get('frame_id')
        
        if vacancy_id:
            vacancy_ids = [vacancy_id]
        elif not vacancy_ids:
            # Without vacancy_id(s), return empty result
            return []
        
        # Aggregate results from multiple vacancies
        all_quotas = []
        for vid in vacancy_ids:
            if frame_id:
                # Query quotas for specific frame
                quotas = await self.get_frame_quotas(vid, frame_id)
            else:
                # Query all quotas for vacancy
                quotas = await self.get_vacancy_quotas(vid)
            all_quotas.extend(quotas)
        
        return all_quotas
    
    async def get_vacancy_quotas(self, vacancy_id: int, count: int = 100, page: int = 1) -> List[Dict[str, Any]]:
        """Get hiring quotas for a vacancy"""
        params = {'count': count, 'page': page}
        
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/vacancies/{vacancy_id}/quotas", params=params)
        
        if isinstance(result, dict) and result.get("items"):
            return [
                {
                    'id': q.get('id', 0),
                    'vacancy_id': vacancy_id,
                    'frame_id': q.get('frame_id', 0),
                    'quota_value': q.get('quota_value', 0),
                    'filled': q.get('filled', 0),
                    'created': q.get('created', '')
                }
                for q in result.get("items", [])
            ]
        return []
    
    async def get_frame_quotas(self, vacancy_id: int, frame_id: int) -> List[Dict[str, Any]]:
        """Get hiring quotas within a specific historical frame"""
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/vacancies/{vacancy_id}/frames/{frame_id}/quotas")
        
        if isinstance(result, dict) and result.get("items"):
            return [
                {
                    'id': q.get('id', 0),
                    'vacancy_id': vacancy_id,
                    'frame_id': frame_id,
                    'quota_value': q.get('quota_value', 0),
                    'filled': q.get('filled', 0),
                    'created': q.get('created', '')
                }
                for q in result.get("items", [])
            ]
        return []
    
    async def _execute_action_logs_query(self, query, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute query against action_logs virtual table"""
        if self._action_logs_cache is not None:
            return list(self._action_logs_cache.values())
        
        params = {}
        if filters:
            # Support documented action_logs parameters: type, count, next_id, previous_id
            for param in ['type', 'count', 'next_id', 'previous_id']:
                if param in filters:
                    params[param] = filters[param]
        
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/action_logs", params=params if params else None)
        
        if isinstance(result, dict) and result.get("items"):
            logs = [
                {
                    'id': log.get('id', 0),
                    'type': log.get('type', ''),
                    'created': log.get('created', ''),
                    'account_info': str(log.get('account_info', {})),
                    'data': str(log)
                }
                for log in result.get("items", [])
            ]
            self._action_logs_cache = {log['id']: log for log in logs}
            return logs
        else:
            self._action_logs_cache = {}
            return []


# Query Builder Helper Functions
class HuntflowQueryBuilder:
    """Helper class to build common queries using SQLAlchemy expressions"""
    
    def __init__(self, engine: HuntflowVirtualEngine):
        self.engine = engine
        self.applicants = engine.applicants
        self.recruiters = engine.recruiters
        self.vacancies = engine.vacancies
    
    def recruiter_performance(self, status_filter: Optional[str] = None):
        """Build query for recruiter performance"""
        # Note: time_to_hire_days removed from schema - must be calculated from logs
        query = select(
            self.applicants.c.recruiter_name,
            func.count(self.applicants.c.id).label('hire_count')
            # avg(time_to_hire_days) removed - calculate from logs separately
        ).group_by(self.applicants.c.recruiter_name)
        
        if status_filter:
            query = query.where(self.applicants.c.status_name == status_filter)
        
        return query
    
    def status_distribution(self):
        """Build query for status distribution"""
        return select(
            self.applicants.c.status_name,
            func.count(self.applicants.c.id).label('count')
        ).group_by(self.applicants.c.status_name)
    
    def company_metrics(self):
        """Build query for company hiring metrics"""
        return select(
            self.vacancies.c.company,
            func.count(self.vacancies.c.id).label('vacancy_count')
        ).group_by(self.vacancies.c.company)