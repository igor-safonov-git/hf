"""
Huntflow Virtual Schema using SQLAlchemy Core
Maps Huntflow API endpoints to virtual SQL tables
"""
from sqlalchemy import MetaData, Table, Column, Integer, String, DateTime, Boolean, Float
from sqlalchemy.sql import select, func, and_, or_
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime

class HuntflowVirtualEngine:
    """Virtual SQL engine that translates SQLAlchemy expressions to Huntflow API calls"""
    
    def __init__(self, hf_client):
        self.hf_client = hf_client
        self.metadata = MetaData()
        
        # Define virtual tables that map to Huntflow API endpoints
        # Based on CLAUDE.md: /applicants/search does NOT return status field (line 136)
        self.applicants = Table('applicants', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('first_name', String),
            Column('last_name', String),
            Column('vacancy', Integer),  # API field name per CLAUDE.md
            Column('source', Integer),   # API field name per CLAUDE.md
            Column('created', DateTime),
            Column('updated', DateTime),
            Column('recruiter', Integer), # API field name per CLAUDE.md
            # Note: status and time_to_hire_days must be calculated from logs
            # These are computed fields, not direct API fields
            Column('status_id', Integer),  # Computed from logs
            Column('status_name', String), # Computed from logs  
            Column('recruiter_name', String), # Computed from coworkers mapping
            Column('source_name', String), # Computed from sources mapping
        )
        
        self.vacancies = Table('vacancies', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('position', String),
            Column('department', String),
            Column('status', String),
            Column('state', String),
            Column('quota', Integer),
            Column('created', DateTime),
            Column('updated', DateTime)
        )
        
        self.status_mapping = Table('status_mapping', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String)
        )
        
        self.recruiters = Table('recruiters', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('first_name', String),
            Column('last_name', String),
            Column('full_name', String),
            Column('type', String)
        )
        
        # Add sources table per CLAUDE.md line 121
        self.sources = Table('sources', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String),
            Column('type', String)
        )
        
        # Add divisions table per CLAUDE.md line 124
        self.divisions = Table('divisions', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String)
        )
        
        # Cache for API data
        self._applicants_cache = None
        self._status_cache = None
        self._recruiters_cache = None
        self._sources_cache = None
    
    async def execute(self, query) -> List[Dict[str, Any]]:
        """Execute SQLAlchemy query by translating to API calls"""
        
        # Determine which table is being queried
        if self._is_table_in_query(query, 'applicants'):
            return await self._execute_applicants_query(query)
        elif self._is_table_in_query(query, 'recruiters'):
            return await self._execute_recruiters_query(query)
        elif self._is_table_in_query(query, 'vacancies'):
            return await self._execute_vacancies_query(query)
        else:
            return []
    
    def _is_table_in_query(self, query, table_name: str) -> bool:
        """Check if a specific table is referenced in the query"""
        query_str = str(query)
        return table_name in query_str.lower()
    
    async def _get_applicants_data(self) -> List[Dict[str, Any]]:
        """Fetch and cache applicants data from API"""
        if self._applicants_cache is not None:
            return self._applicants_cache
        
        print("🔄 Fetching applicants data for virtual table...")
        
        # Get applicants from API using correct pagination (CLAUDE.md line 169)
        all_applicants = []
        page = 1
        while True:
            params = {"count": 100, "page": page}
            result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/applicants/search", params=params)
            
            if isinstance(result, dict):
                items = result.get("items", [])
                if not items:
                    break
                all_applicants.extend(items)
                page += 1
            else:
                break
        
        # If no real data, we have no applicants
        if not all_applicants:
            print("❌ No applicants data available from API")
            all_applicants = []
        
        # Enrich with recruiter and source info
        enriched_applicants = []
        recruiters_map = await self._get_recruiters_mapping()
        sources_map = await self._get_sources_mapping()
        
        for applicant in all_applicants:
            # Map to correct API field names (CLAUDE.md line 136: status not in /applicants/search)
            enriched = {
                'id': applicant.get('id', 0),
                'first_name': applicant.get('first_name', ''),
                'last_name': applicant.get('last_name', ''),
                'vacancy': applicant.get('vacancy', 0),  # Direct API field
                'source': applicant.get('source', 0),   # Direct API field  
                'created': applicant.get('created', ''),
                'updated': applicant.get('updated', ''),
                'recruiter': applicant.get('recruiter', 0), # Direct API field
                # Computed fields (require additional API calls):
                'status_id': 0,  # Must be computed from logs per CLAUDE.md lines 138-151
                'status_name': 'Unknown', # Must be computed from logs
                'recruiter_name': recruiters_map.get(applicant.get('recruiter', 0), 'Unknown'),
                'source_name': sources_map.get(applicant.get('source', 0), 'Unknown'),
            }
            enriched_applicants.append(enriched)
        
        self._applicants_cache = enriched_applicants
        print(f"✅ Cached {len(enriched_applicants)} applicants")
        return enriched_applicants
    
    # Removed demo applicants generation - using real API only
    
    async def _get_status_mapping(self) -> Dict[int, str]:
        """Get status ID to name mapping from actual API response"""
        if self._status_cache is not None:
            return self._status_cache
        
        print("🔄 Fetching actual status mapping from API...")
        # Use correct endpoint from CLAUDE.md line 109
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/vacancies/statuses")
        
        # If that fails, try the alternative endpoint mentioned in CLAUDE.md line 110
        if not result or result.get("errors"):
            print("🔄 Trying alternative vacancy_statuses endpoint...")
            result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/vacancy_statuses")
        
        print(f"🔍 Debug - API response: {result}")
        
        if isinstance(result, dict):
            if result.get("items"):
                statuses = result.get("items", [])
                self._status_cache = {s.get("id"): s.get("name") for s in statuses if s.get("id") and s.get("name")}
                print(f"✅ Got {len(self._status_cache)} actual statuses from API: {list(self._status_cache.values())}")
            else:
                print(f"❌ API failed to return status data. Response: {result}")
                print("🔄 API authentication or endpoint issue - no statuses available")
                self._status_cache = {}
        else:
            print(f"⚠️ API response is not dict, type: {type(result)}")
            self._status_cache = {}
        
        return self._status_cache
    
    async def _get_recruiters_mapping(self) -> Dict[int, str]:
        """Get recruiter ID to name mapping from actual API response"""
        if self._recruiters_cache is not None:
            return self._recruiters_cache
        
        print("🔄 Fetching actual recruiters from API...")
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/coworkers")
        
        print(f"🔍 Debug - Recruiters API response: {result}")
        
        if isinstance(result, dict):
            if result.get("items"):
                recruiters = result.get("items", [])
                self._recruiters_cache = {
                    r.get("id"): f"{r.get('first_name', '')} {r.get('last_name', '')}".strip()
                    for r in recruiters if r.get('id') and (r.get('first_name') or r.get('last_name'))
                }
                print(f"✅ Got {len(self._recruiters_cache)} actual recruiters from API: {list(self._recruiters_cache.values())}")
            else:
                print(f"❌ API failed to return recruiter data. Response: {result}")
                print("🔄 API authentication or endpoint issue - no recruiters available")
                self._recruiters_cache = {}
        else:
            print(f"⚠️ Recruiters API response is not dict, type: {type(result)}")
            self._recruiters_cache = {}
        
        return self._recruiters_cache
    
    async def _get_sources_mapping(self) -> Dict[int, str]:
        """Get source ID to name mapping from actual API response"""
        if self._sources_cache is not None:
            return self._sources_cache
        
        print("🔄 Fetching actual sources from API...")
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/applicants/sources")
        
        print(f"🔍 Debug - Sources API response: {result}")
        
        if isinstance(result, dict):
            if result.get("items"):
                sources = result.get("items", [])
                self._sources_cache = {
                    s.get("id"): s.get("name", "Unknown")
                    for s in sources if s.get('id') and s.get('name')
                }
                print(f"✅ Got {len(self._sources_cache)} actual sources from API: {list(self._sources_cache.values())}")
            else:
                print(f"❌ API failed to return source data. Response: {result}")
                self._sources_cache = {}
        else:
            print(f"⚠️ Sources API response is not dict, type: {type(result)}")
            self._sources_cache = {}
        
        return self._sources_cache
    
    async def _get_applicant_status_from_logs(self, applicant_id: int) -> tuple[int, str]:
        """Get current status from applicant logs per CLAUDE.md lines 138-151"""
        try:
            # Get applicant activity logs
            logs = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/applicants/{applicant_id}/logs")
            
            if isinstance(logs, dict) and logs.get("items"):
                # Find most recent status change
                for log_entry in logs.get("items", []):
                    if log_entry.get("status"):
                        status_id = log_entry.get("status")
                        status_map = await self._get_status_mapping()
                        status_name = status_map.get(status_id, "Unknown")
                        return status_id, status_name
                        
            return 0, "Unknown"
        except Exception as e:
            print(f"⚠️ Failed to get status from logs for applicant {applicant_id}: {e}")
            return 0, "Unknown"
    
    async def _execute_applicants_query(self, query) -> List[Dict[str, Any]]:
        """Execute query against applicants virtual table"""
        applicants_data = await self._get_applicants_data()
        
        # For now, return raw data - we'll add filtering/aggregation next
        # This would be where we parse the SQLAlchemy query and apply filters
        
        return applicants_data
    
    async def _execute_recruiters_query(self, query) -> List[Dict[str, Any]]:
        """Execute query against recruiters virtual table"""
        recruiters_map = await self._get_recruiters_mapping()
        
        return [
            {
                'id': rid,
                'full_name': name,
                'first_name': name.split()[0] if name else '',
                'last_name': name.split()[-1] if len(name.split()) > 1 else '',
                'type': 'recruiter'
            }
            for rid, name in recruiters_map.items()
        ]
    
    async def _execute_vacancies_query(self, query) -> List[Dict[str, Any]]:
        """Execute query against vacancies virtual table"""
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/vacancies", params={"count": 100})
        
        if isinstance(result, dict):
            return result.get("items", [])
        else:
            # No fallback data - return empty list when API fails
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
    
    def department_metrics(self):
        """Build query for department hiring metrics"""
        return select(
            self.vacancies.c.department,
            func.count(self.vacancies.c.id).label('vacancy_count')
        ).group_by(self.vacancies.c.department)