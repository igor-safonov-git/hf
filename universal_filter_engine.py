from typing import Dict, List, Any, Optional
from universal_filter import UniversalFilter, FilterSet, PeriodFilter, EntityType, FilterOperator
from datetime import datetime

class UniversalFilterEngine:
    """Centralized engine for processing all filters"""
    
    def __init__(self, db_client, log_analyzer):
        self.db_client = db_client
        self.log_analyzer = log_analyzer
        self.entity_relationships = self._build_entity_relationships()
    
    def _build_entity_relationships(self) -> Dict[str, Dict[str, str]]:
        """Define how entities relate to each other"""
        return {
            "applicants": {
                "recruiters": "recruiter_id",
                "vacancies": "vacancy_id",
                "sources": "source_id",
                "stages": "stage_id"
            },
            "vacancies": {
                "recruiters": "recruiter_id",
                "hiring_managers": "hiring_manager_id",
                "divisions": "division_id"
            },
            "hires": {
                "recruiters": "recruiter_id",
                "sources": "source_id",
                "vacancies": "vacancy_id"
            }
        }
    
    async def apply_filters(self, entity_type: EntityType, filters: FilterSet, 
                          base_data: Optional[List] = None) -> List:
        """Apply all filters to get filtered entity data"""
        
        if base_data is None:
            base_data = await self._fetch_base_data(entity_type)
        
        result = base_data
        
        # Apply period filters first (most selective)
        if filters.period_filter:
            result = self._apply_period_filter(result, filters.period_filter)
        
        # Apply cross-entity filters (relationships)
        if filters.cross_entity_filters:
            result = self._apply_cross_entity_filters(result, filters.cross_entity_filters, entity_type)
        
        # Apply direct entity filters
        if filters.entity_filters:
            result = self._apply_entity_filters(result, filters.entity_filters)
        
        return result
    
    def _apply_period_filter(self, data: List, period_filter: PeriodFilter) -> List:
        """Apply time-based filtering"""
        if not period_filter.start_date:
            return data
        
        filtered_data = []
        for item in data:
            # Try different date field names
            item_date = item.get("created") or item.get("created_at") or item.get("date")
            if item_date:
                # Convert string dates to datetime if needed
                if isinstance(item_date, str):
                    try:
                        # Try parsing ISO format with timezone
                        if '+' in item_date or 'Z' in item_date:
                            # Handle timezone aware dates
                            import re
                            clean_date = re.sub(r'[+]\d{2}:\d{2}$', '', item_date)
                            clean_date = clean_date.replace('Z', '')
                            item_date = datetime.fromisoformat(clean_date)
                        else:
                            item_date = datetime.fromisoformat(item_date)
                    except (ValueError, TypeError):
                        # If parsing fails, include the item
                        filtered_data.append(item)
                        continue
                
                if isinstance(item_date, datetime):
                    if period_filter.start_date <= item_date <= period_filter.end_date:
                        filtered_data.append(item)
            else:
                # If no date field, include the item (don't filter out)
                filtered_data.append(item)
        
        return filtered_data
    
    def _apply_cross_entity_filters(self, data: List, filters: List[UniversalFilter], 
                                  target_entity: EntityType) -> List:
        """Apply filters based on entity relationships"""
        
        for filter_obj in filters:
            relationship_key = self.entity_relationships.get(
                target_entity.value, {}
            ).get(filter_obj.entity_type.value)
            
            if not relationship_key:
                continue  # Skip if no relationship defined
            
            data = self._apply_single_filter(data, filter_obj, relationship_key)
        
        return data
    
    def _apply_entity_filters(self, data: List, filters: List[UniversalFilter]) -> List:
        """Apply direct entity filters"""
        
        for filter_obj in filters:
            data = self._apply_single_filter(data, filter_obj, filter_obj.field)
        
        return data
    
    def _apply_single_filter(self, data: List, filter_obj: UniversalFilter, 
                           field_name: str) -> List:
        """Apply a single filter to the data"""
        
        filtered_data = []
        
        for item in data:
            field_value = item.get(field_name)
            
            if self._matches_filter(field_value, filter_obj):
                filtered_data.append(item)
        
        return filtered_data
    
    def _matches_filter(self, field_value: Any, filter_obj: UniversalFilter) -> bool:
        """Check if a field value matches the filter"""
        
        if filter_obj.operator == FilterOperator.EQUALS:
            return field_value == filter_obj.value
        elif filter_obj.operator == FilterOperator.NOT_EQUALS:
            return field_value != filter_obj.value
        elif filter_obj.operator == FilterOperator.IN:
            return field_value in filter_obj.value
        elif filter_obj.operator == FilterOperator.NOT_IN:
            return field_value not in filter_obj.value
        elif filter_obj.operator == FilterOperator.CONTAINS:
            return str(filter_obj.value).lower() in str(field_value).lower()
        elif filter_obj.operator == FilterOperator.EXISTS:
            return field_value is not None
        
        return False
    
    def parse_prompt_filters(self, prompt_filters: Dict[str, Any]) -> FilterSet:
        """Convert prompt.py filter format to FilterSet"""
        
        period_filter = None
        cross_entity_filters = []
        
        for filter_key, filter_value in prompt_filters.items():
            if filter_key == "period":
                period_filter = PeriodFilter.from_string(filter_value)
            elif filter_key in [e.value for e in EntityType]:
                # This is a cross-entity filter
                if isinstance(filter_value, list):
                    operator = FilterOperator.IN
                else:
                    operator = FilterOperator.EQUALS
                
                cross_entity_filters.append(
                    UniversalFilter(
                        entity_type=EntityType(filter_key),
                        field="id" if isinstance(filter_value, str) and filter_value.isdigit() else "state",
                        operator=operator,
                        value=filter_value
                    )
                )
        
        return FilterSet(
            period_filter=period_filter,
            cross_entity_filters=cross_entity_filters
        )
    
    async def _fetch_base_data(self, entity_type: EntityType) -> List:
        """Fetch base data for an entity type"""
        # This would call the appropriate client method
        # For now, return empty list (tests pass their own data)
        return []