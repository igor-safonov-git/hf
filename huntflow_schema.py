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
        
        # Cache for API data
        self._applicants_cache = None
        self._status_cache = None
        self._recruiters_cache = None
        self._sources_cache = None
        self._divisions_cache = None
        self._tags_cache = None
    
    async def execute(self, query) -> List[Dict[str, Any]]:
        """Execute SQLAlchemy query by translating to API calls"""
        
        # Determine which table is being queried
        if self._is_table_in_query(query, 'applicants'):
            return await self._execute_applicants_query(query)
        elif self._is_table_in_query(query, 'recruiters'):
            return await self._execute_recruiters_query(query)
        elif self._is_table_in_query(query, 'vacancies'):
            return await self._execute_vacancies_query(query)
        elif self._is_table_in_query(query, 'divisions'):
            return await self._execute_divisions_query(query)
        elif self._is_table_in_query(query, 'applicant_tags'):
            return await self._execute_tags_query(query)
        elif self._is_table_in_query(query, 'sources'):
            return await self._execute_sources_query(query)
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
        
        # Get applicants from API using correct pagination per OpenAPI spec
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
                
                # Check if we have more pages using total count
                total = result.get("total", 0)
                current_count = len(all_applicants)
                if current_count >= total:
                    break
                    
                page += 1
            else:
                break
        
        # If no real data, we have no applicants
        if not all_applicants:
            print("❌ No applicants data available from API")
            all_applicants = []
        
        # Enrich with recruiter and source info + CRITICAL: Get real status data
        enriched_applicants = []
        recruiters_map = await self._get_recruiters_mapping()
        sources_map = await self._get_sources_mapping()
        
        # Sample first 30 applicants for individual API calls to get real status data
        sample_size = min(30, len(all_applicants))
        print(f"🔄 Enriching {sample_size} of {len(all_applicants)} applicants with individual API calls...")
        
        for i, applicant in enumerate(all_applicants):
            # Map to actual API fields available in search response per OpenAPI spec
            # CRITICAL: NO status fields in ApplicantSearchItem per OpenAPI
            enriched = {
                'id': applicant.get('id', 0),
                'first_name': applicant.get('first_name', ''),
                'last_name': applicant.get('last_name', ''),
                'middle_name': applicant.get('middle_name', ''),
                'birthday': applicant.get('birthday', ''),        # Available in search
                'phone': applicant.get('phone', ''),
                'skype': applicant.get('skype', ''),              # Available in search
                'email': applicant.get('email', ''),
                'money': applicant.get('money', ''),              # Salary expectation
                'position': applicant.get('position', ''),       # Available in search
                'company': applicant.get('company', ''),         # Available in search
                'photo': applicant.get('photo', 0),              # Photo ID
                'photo_url': applicant.get('photo_url', ''),     # Available in search
                'created': applicant.get('created', ''),
                # Required ApplicantItem fields from individual /applicants/{id} calls
                'account': applicant.get('account', self.hf_client.acc_id),  # Organization ID
                'tags': str(applicant.get('tags', [])),                      # List of tags as JSON string
                'external': str(applicant.get('external', {})),              # Resume data as JSON string
                'agreement': str(applicant.get('agreement', {})),            # Agreement state as JSON string
                'doubles': str(applicant.get('doubles', [])),                # List of duplicates as JSON string
                'social': str(applicant.get('social', [])),                  # Social accounts as JSON string
                # Computed fields from logs or individual calls
                'source_id': 0,         # Must be fetched from individual call
                'recruiter_id': 0,      # Must be computed from logs
                'recruiter_name': 'Unknown',
                'source_name': 'Unknown',
            }
            
            # For first 30 applicants, make individual API calls to get real status data
            if i < sample_size:
                try:
                    real_data = await self._get_applicant_links_from_individual_call(applicant.get('id', 0))
                    if real_data:
                        # Get most recent link (highest status activity)
                        latest_link = max(real_data, key=lambda x: x.get('updated', ''), default={})
                        if latest_link:
                            enriched['status_id'] = latest_link.get('status', 0)
                            enriched['vacancy_id'] = latest_link.get('vacancy', 0)
                            
                            # Map status ID to name
                            status_map = await self._get_status_mapping()
                            status_info = status_map.get(enriched['status_id'], {'name': 'Unknown'})
                            enriched['status_name'] = status_info.get('name', 'Unknown')
                except Exception as e:
                    print(f"⚠️ Failed to enrich applicant {applicant.get('id')}: {e}")
            
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
        # Use correct endpoint from official API specification
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/vacancies/statuses")
        
        print(f"🔍 Debug - API response: {result}")
        
        if isinstance(result, dict):
            if result.get("items"):
                statuses = result.get("items", [])
                # Create complete status mapping with all OpenAPI fields
                self._status_cache = {}
                for s in statuses:
                    if s.get("id") and s.get("name"):
                        self._status_cache[s.get("id")] = {
                            'name': s.get("name"),
                            'type': s.get("type", ""),                    # Required per OpenAPI
                            'removed': s.get("removed", ""),             # Optional per OpenAPI  
                            'order': s.get("order", 0),                  # Required per OpenAPI
                            'stay_duration': s.get("stay_duration", 0)   # Optional per OpenAPI
                        }
                print(f"✅ Got {len(self._status_cache)} actual statuses from API: {[s['name'] for s in self._status_cache.values()]}")
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
                    r.get("id"): r.get('name', 'Unknown')  # Use name field per OpenAPI
                    for r in recruiters if r.get('id')
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
    
    async def _get_divisions_mapping(self) -> Dict[int, str]:
        """Get division ID to name mapping from actual API response"""
        if self._divisions_cache is not None:
            return self._divisions_cache
        
        print("🔄 Fetching actual divisions from API...")
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/divisions")
        
        if isinstance(result, dict) and result.get("items"):
            divisions = result.get("items", [])
            self._divisions_cache = {
                d.get("id"): d.get("name", "Unknown")
                for d in divisions if d.get('id') and d.get('name')
            }
            print(f"✅ Got {len(self._divisions_cache)} divisions from API")
        else:
            self._divisions_cache = {}
        
        return self._divisions_cache
    
    async def _get_tags_mapping(self) -> Dict[int, str]:
        """Get applicant tags from actual API response"""
        if self._tags_cache is not None:
            return self._tags_cache
        
        print("🔄 Fetching applicant tags from API...")
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/applicants/tags")
        
        if isinstance(result, dict) and result.get("items"):
            tags = result.get("items", [])
            self._tags_cache = {
                t.get("id"): t.get("name", "Unknown")
                for t in tags if t.get('id') and t.get('name')
            }
            print(f"✅ Got {len(self._tags_cache)} applicant tags from API")
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
            print(f"⚠️ Failed to get data from logs for applicant {applicant_id}: {e}")
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
            print(f"⚠️ Failed to get links from individual call for applicant {applicant_id}: {e}")
            return []
    
    async def _execute_applicants_query(self, query) -> List[Dict[str, Any]]:
        """Execute query against applicants virtual table"""
        applicants_data = await self._get_applicants_data()
        
        # For now, return raw data - we'll add filtering/aggregation next
        # This would be where we parse the SQLAlchemy query and apply filters
        
        return applicants_data
    
    async def _execute_recruiters_query(self, query) -> List[Dict[str, Any]]:
        """Execute query against recruiters virtual table"""
        recruiters_map = await self._get_recruiters_mapping()
        
        # Get actual coworkers data to return proper fields
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/coworkers")
        
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
    
    async def _execute_vacancies_query(self, query) -> List[Dict[str, Any]]:
        """Execute query against vacancies virtual table"""
        # Get all vacancies with proper pagination
        all_vacancies = []
        page = 1
        while True:
            params = {"count": 100, "page": page}
            result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/vacancies", params=params)
            
            if isinstance(result, dict):
                items = result.get("items", [])
                if not items:
                    break
                all_vacancies.extend(items)
                
                # Check if we have more pages
                total = result.get("total", 0)
                if len(all_vacancies) >= total:
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
    
    async def _execute_divisions_query(self, query) -> List[Dict[str, Any]]:
        """Execute query against divisions virtual table"""
        # Get full divisions data from API to return all OpenAPI fields
        result = await self.hf_client._req("GET", f"/v2/accounts/{self.hf_client.acc_id}/divisions")
        
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