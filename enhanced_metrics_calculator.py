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