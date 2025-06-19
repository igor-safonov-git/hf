from typing import Dict, Any, List, Optional
from metrics_calculator import MetricsCalculator
from universal_filter_engine import UniversalFilterEngine
from universal_filter import EntityType

class EnhancedMetricsCalculator(MetricsCalculator):
    """Enhanced MetricsCalculator with universal filtering support"""
    
    def __init__(self, client, log_analyzer):
        super().__init__(client)
        self.log_analyzer = log_analyzer
        self.filter_engine = UniversalFilterEngine(client, log_analyzer)
    
    async def get_applicants(self, filters: Optional[Dict[str, Any]] = None) -> List:
        """Get applicants with universal filtering support"""
        
        # Get base data using parent method
        base_data = await super().get_applicants()
        
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
        
        base_data = await super().hires()
        
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
        
        base_data = await super().vacancies_all()
        
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
        
        base_data = await super().recruiters_all()
        
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
        
        base_data = await super().sources_all()
        
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