from typing import Dict, Any, List, Optional
from huntflow_local_client import HuntflowLocalClient
from universal_filter_engine import UniversalFilterEngine
from universal_filter import EntityType

class EnhancedMetricsCalculator:
    """Standalone MetricsCalculator with universal filtering support"""
    
    def __init__(self, client, log_analyzer):
        self.client = client or HuntflowLocalClient()
        self.log_analyzer = log_analyzer
        self.filter_engine = UniversalFilterEngine(client, log_analyzer)
    
    # === Core Entity Methods ===
    
    async def applicants_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all applicants data with pagination and filtering support"""
        all_applicants = []
        page = 1
        count = 100  # Records per page
        
        while True:
            data = await self.client._req(
                "GET", 
                f"/v2/accounts/{self.client.account_id}/applicants/search",
                params={"page": page, "count": count}
            )
            items = data.get("items", [])
            
            if not items:  # No more records
                break
                
            all_applicants.extend(items)
            
            # If we got fewer than the page size, we're on the last page
            if len(items) < count:
                break
                
            page += 1
        
        # Apply Universal Filtering if filters provided
        if filters:
            filter_set = self.filter_engine.parse_prompt_filters(filters)
            return await self.filter_engine.apply_filters(
                EntityType.APPLICANTS,
                filter_set,
                all_applicants
            )
        
        return all_applicants
    
    async def recruiters_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get recruiters data (from coworkers endpoint)"""
        data = await self.client._req("GET", f"/v2/accounts/{self.client.account_id}/coworkers")
        recruiters = data.get("items", [])
        
        # Apply Universal Filtering if filters provided
        if filters:
            filter_set = self.filter_engine.parse_prompt_filters(filters)
            return await self.filter_engine.apply_filters(
                EntityType.RECRUITERS,
                filter_set,
                recruiters
            )
        
        return recruiters
    
    async def recruiters_by_hirings(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
        """Get recruiters ranked by hiring activity - CRITICAL FOR SCATTER CHARTS"""
        from analyze_logs import LogAnalyzer
        analyzer = LogAnalyzer(self.client.db_path)
        recruiter_stats = analyzer.get_recruiter_activity()
        
        # Calculate hiring potential based on AGREEMENT actions (final closing actions)
        hiring_rankings = {}
        for name, stats in recruiter_stats.items():
            agreement_count = stats["action_types"].get("AGREEMENT", 0)
            # Also factor in total candidate management
            total_activity = stats["total_actions"]
            # Hiring score = agreements + (total_activity / 10) for comprehensive evaluation
            hiring_score = agreement_count + (total_activity // 10)
            hiring_rankings[name] = hiring_score
        
        # Apply Universal Filtering if filters provided
        if filters:
            # For grouped data, we need to filter the underlying data first
            filter_set = self.filter_engine.parse_prompt_filters(filters)
            # This is a dict result, so we'll return as-is for now
            # TODO: Implement dict filtering for grouped results
        
        return hiring_rankings
    
    async def vacancies_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all vacancies data"""
        data = await self.client._req("GET", f"/v2/accounts/{self.client.account_id}/vacancies")
        vacancies = data.get("items", [])
        
        # Apply Universal Filtering if filters provided
        if filters:
            filter_set = self.filter_engine.parse_prompt_filters(filters)
            return await self.filter_engine.apply_filters(
                EntityType.VACANCIES,
                filter_set,
                vacancies
            )
        
        return vacancies
    
    async def sources_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all applicant sources"""
        data = await self.client._req("GET", f"/v2/accounts/{self.client.account_id}/applicants/sources")
        sources = data.get("items", [])
        
        # Apply Universal Filtering if filters provided
        if filters:
            filter_set = self.filter_engine.parse_prompt_filters(filters)
            return await self.filter_engine.apply_filters(
                EntityType.SOURCES,
                filter_set,
                sources
            )
        
        return sources
    
    async def hires(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get hired applicants with optional filtering"""
        from analyze_logs import LogAnalyzer
        analyzer = LogAnalyzer(self.client.db_path)
        hired = analyzer.get_hired_applicants()
        
        # Apply Universal Filtering if filters provided
        if filters:
            filter_set = self.filter_engine.parse_prompt_filters(filters)
            return await self.filter_engine.apply_filters(
                EntityType.HIRES,
                filter_set,
                hired
            )
        
        return hired
    
    async def get_applicants(self, filters: Optional[Dict[str, Any]] = None) -> List:
        """Get applicants with universal filtering support"""
        
        # Get base data using applicants_all method
        base_data = await self.applicants_all()
        
        # Apply filters if provided
        if filters:
            filter_set = self.filter_engine.parse_prompt_filters(filters)
            return await self.filter_engine.apply_filters(
                EntityType.APPLICANTS, 
                filter_set, 
                base_data
            )
        
        return base_data
    
    async def get_hires(self, filters: Optional[Dict[str, Any]] = None) -> List:
        """Get hires with universal filtering support"""
        
        base_data = await self.hires()
        
        if filters:
            filter_set = self.filter_engine.parse_prompt_filters(filters)
            return await self.filter_engine.apply_filters(
                EntityType.HIRES,
                filter_set,
                base_data
            )
        
        return base_data
    
    async def get_vacancies(self, filters: Optional[Dict[str, Any]] = None) -> List:
        """Get vacancies with universal filtering support"""
        
        base_data = await self.vacancies_all()
        
        if filters:
            filter_set = self.filter_engine.parse_prompt_filters(filters)
            return await self.filter_engine.apply_filters(
                EntityType.VACANCIES,
                filter_set,
                base_data
            )
        
        return base_data
    
    async def get_recruiters(self, filters: Optional[Dict[str, Any]] = None) -> List:
        """Get recruiters with universal filtering support"""
        
        base_data = await self.recruiters_all()
        
        if filters:
            filter_set = self.filter_engine.parse_prompt_filters(filters)
            return await self.filter_engine.apply_filters(
                EntityType.RECRUITERS,
                filter_set,
                base_data
            )
        
        return base_data
    
    async def get_sources(self, filters: Optional[Dict[str, Any]] = None) -> List:
        """Get sources with universal filtering support"""
        
        base_data = await self.sources_all()
        
        if filters:
            filter_set = self.filter_engine.parse_prompt_filters(filters)
            return await self.filter_engine.apply_filters(
                EntityType.SOURCES,
                filter_set,
                base_data
            )
        
        return base_data
    
    # === Core Entity Methods with Universal Filtering ===
    
    async def applicants_all(self, filters: Optional[Dict[str, Any]] = None) -> List:
        """Get all applicants with universal filtering support"""
        
        base_data = await super().applicants_all(filters)  # This already supports filters
        
        # Apply additional universal filters if provided and not already handled
        if filters and not any(key in filters for key in ['recruiters']):  # Only apply if not already filtered
            filter_set = self.filter_engine.parse_prompt_filters(filters)
            return await self.filter_engine.apply_filters(
                EntityType.APPLICANTS,
                filter_set,
                base_data
            )
        
        return base_data
    
    async def vacancies_all(self, filters: Optional[Dict[str, Any]] = None) -> List:
        """Get all vacancies with universal filtering support"""
        
        base_data = await super().vacancies_all()
        
        if filters:
            filter_set = self.filter_engine.parse_prompt_filters(filters)
            return await self.filter_engine.apply_filters(
                EntityType.VACANCIES,
                filter_set,
                base_data
            )
        
        return base_data
    
    async def recruiters_all(self, filters: Optional[Dict[str, Any]] = None) -> List:
        """Get all recruiters with universal filtering support"""
        
        base_data = await super().recruiters_all()
        
        if filters:
            filter_set = self.filter_engine.parse_prompt_filters(filters)
            return await self.filter_engine.apply_filters(
                EntityType.RECRUITERS,
                filter_set,
                base_data
            )
        
        return base_data
    
    async def sources_all(self, filters: Optional[Dict[str, Any]] = None) -> List:
        """Get all sources with universal filtering support"""
        
        base_data = await super().sources_all()
        
        if filters:
            filter_set = self.filter_engine.parse_prompt_filters(filters)
            return await self.filter_engine.apply_filters(
                EntityType.SOURCES,
                filter_set,
                base_data
            )
        
        return base_data
    
    async def divisions_all(self, filters: Optional[Dict[str, Any]] = None) -> List:
        """Get all divisions with universal filtering support"""
        
        base_data = await super().divisions_all()
        
        if filters:
            filter_set = self.filter_engine.parse_prompt_filters(filters)
            return await self.filter_engine.apply_filters(
                EntityType.DIVISIONS,
                filter_set,
                base_data
            )
        
        return base_data
    
    async def statuses_all(self, filters: Optional[Dict[str, Any]] = None) -> List:
        """Get all statuses with universal filtering support"""
        
        base_data = await super().statuses_all()
        
        if filters:
            filter_set = self.filter_engine.parse_prompt_filters(filters)
            return await self.filter_engine.apply_filters(
                EntityType.STAGES,  # Statuses are related to stages
                filter_set,
                base_data
            )
        
        return base_data
    
    # === Specific Vacancy Methods ===
    
    async def get_open_vacancies(self, filters: Optional[Dict[str, Any]] = None) -> List:
        """Get open vacancies with universal filtering support"""
        
        base_data = await super().get_open_vacancies()
        
        if filters:
            filter_set = self.filter_engine.parse_prompt_filters(filters)
            return await self.filter_engine.apply_filters(
                EntityType.VACANCIES,
                filter_set,
                base_data
            )
        
        return base_data
    
    async def get_closed_vacancies(self, filters: Optional[Dict[str, Any]] = None) -> List:
        """Get closed vacancies with universal filtering support"""
        
        base_data = await super().get_closed_vacancies()
        
        if filters:
            filter_set = self.filter_engine.parse_prompt_filters(filters)
            return await self.filter_engine.apply_filters(
                EntityType.VACANCIES,
                filter_set,
                base_data
            )
        
        return base_data
    
    # === Hire and Applicant Methods ===
    
    async def get_hired_applicants(self, filters: Optional[Dict[str, Any]] = None) -> List:
        """Get hired applicants with universal filtering support"""
        
        base_data = await super().get_hired_applicants()
        
        if filters:
            filter_set = self.filter_engine.parse_prompt_filters(filters)
            return await self.filter_engine.apply_filters(
                EntityType.HIRES,
                filter_set,
                base_data
            )
        
        return base_data
    
    async def hires(self, filters: Optional[Dict[str, Any]] = None) -> List:
        """Get hires with universal filtering support"""
        
        base_data = await super().hires(filters)  # This already supports some filtering
        
        # Apply additional universal filters if provided
        if filters:
            filter_set = self.filter_engine.parse_prompt_filters(filters)
            return await self.filter_engine.apply_filters(
                EntityType.HIRES,
                filter_set,
                base_data
            )
        
        return base_data
    
    # === Action and Activity Methods ===
    
    async def actions(self, filters: Optional[Dict[str, Any]] = None) -> List:
        """Get actions with universal filtering support"""
        
        base_data = await super().actions()
        
        if filters:
            filter_set = self.filter_engine.parse_prompt_filters(filters)
            return await self.filter_engine.apply_filters(
                EntityType.ACTIONS,
                filter_set,
                base_data
            )
        
        return base_data