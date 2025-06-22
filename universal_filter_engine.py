from typing import Dict, List, Any, Optional, Union
from universal_filter import UniversalFilter, FilterSet, PeriodFilter, EntityType, FilterOperator, LogicalFilter
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
        
        # Apply logical filters first (they might contain period/entity filters)
        if filters.logical_filters:
            result = self._apply_logical_filters(result, filters.logical_filters, entity_type)
        
        # Apply period filters
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
            # Handle type conversion for numeric comparisons
            if isinstance(field_value, (int, float)) and isinstance(filter_obj.value, str):
                try:
                    return field_value == int(filter_obj.value)
                except ValueError:
                    try:
                        return field_value == float(filter_obj.value)
                    except ValueError:
                        return field_value == filter_obj.value
            elif isinstance(field_value, str) and isinstance(filter_obj.value, (int, float)):
                try:
                    return int(field_value) == filter_obj.value
                except ValueError:
                    try:
                        return float(field_value) == filter_obj.value
                    except ValueError:
                        return field_value == str(filter_obj.value)
            
            # Handle case insensitive string comparison for common values
            if isinstance(field_value, str) and isinstance(filter_obj.value, str):
                # Handle vacancy state case variations: 'open' -> 'OPEN', 'closed' -> 'CLOSED'
                if filter_obj.value.lower() in ['open', 'closed']:
                    return field_value.upper() == filter_obj.value.upper()
                # Default case-sensitive comparison
                return field_value == filter_obj.value
            
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
        elif filter_obj.operator == FilterOperator.GREATER_THAN:
            try:
                return float(field_value) > float(filter_obj.value)
            except (ValueError, TypeError):
                return False
        elif filter_obj.operator == FilterOperator.GREATER_THAN_EQUAL:
            try:
                return float(field_value) >= float(filter_obj.value)
            except (ValueError, TypeError):
                return False
        elif filter_obj.operator == FilterOperator.LESS_THAN:
            try:
                return float(field_value) < float(filter_obj.value)
            except (ValueError, TypeError):
                return False
        elif filter_obj.operator == FilterOperator.LESS_THAN_EQUAL:
            try:
                return float(field_value) <= float(filter_obj.value)
            except (ValueError, TypeError):
                return False
        elif filter_obj.operator == FilterOperator.BETWEEN:
            try:
                val = float(field_value)
                return filter_obj.value[0] <= val <= filter_obj.value[1]
            except (ValueError, TypeError, IndexError):
                return False
        
        return False
    
    def parse_prompt_filters(self, prompt_filters: Dict[str, Any]) -> FilterSet:
        """Convert prompt.py filter format to FilterSet"""
        
        period_filter = None
        cross_entity_filters = []
        logical_filters = []
        
        for filter_key, filter_value in prompt_filters.items():
            if filter_key == "period":
                period_filter = PeriodFilter.from_string(filter_value)
            elif filter_key in ["and", "or"]:
                # Logical operator
                logical_filter = self._parse_logical_filter(filter_key, filter_value)
                logical_filters.append(logical_filter)
            elif filter_key in [e.value for e in EntityType]:
                # This is a cross-entity filter
                cross_entity_filter = self._parse_entity_filter(filter_key, filter_value)
                if cross_entity_filter:
                    cross_entity_filters.append(cross_entity_filter)
        
        return FilterSet(
            period_filter=period_filter,
            cross_entity_filters=cross_entity_filters,
            logical_filters=logical_filters
        )
    
    def _parse_logical_filter(self, operator: str, conditions: List[Dict[str, Any]]) -> LogicalFilter:
        """Parse logical filter (AND/OR) from prompt format"""
        parsed_filters = []
        
        for condition in conditions:
            if "and" in condition or "or" in condition:
                # Nested logical filter
                for nested_op, nested_conditions in condition.items():
                    if nested_op in ["and", "or"]:
                        nested_filter = self._parse_logical_filter(nested_op, nested_conditions)
                        parsed_filters.append(nested_filter)
            else:
                # Regular filter condition
                parsed_filters.append(condition)
        
        return LogicalFilter(operator=operator, filters=parsed_filters)
    
    def _parse_entity_filter(self, entity_key: str, filter_value: Any) -> Optional[UniversalFilter]:
        """Parse entity filter with advanced operator syntax"""
        
        if isinstance(filter_value, dict) and "operator" in filter_value:
            # Advanced operator syntax: {"operator": "in", "value": [...]}
            try:
                operator_str = filter_value["operator"]
                value = filter_value["value"]
                
                # Map string operators to FilterOperator enum
                operator_mapping = {
                    "equals": FilterOperator.EQUALS,
                    "eq": FilterOperator.EQUALS,
                    "in": FilterOperator.IN,
                    "not_in": FilterOperator.NOT_IN,
                    "contains": FilterOperator.CONTAINS,
                    "gt": FilterOperator.GREATER_THAN,
                    "gte": FilterOperator.GREATER_THAN_EQUAL,
                    "lt": FilterOperator.LESS_THAN,
                    "lte": FilterOperator.LESS_THAN_EQUAL,
                    "between": FilterOperator.BETWEEN
                }
                
                if operator_str not in operator_mapping:
                    raise ValueError(f"Invalid operator: {operator_str}. Supported: {list(operator_mapping.keys())}")
                
                operator = operator_mapping[operator_str]
                
                # Validate required fields
                if "value" not in filter_value:
                    raise ValueError(f"Missing 'value' field for operator '{operator_str}'")
                
                return UniversalFilter(
                    entity_type=EntityType(entity_key),
                    field="id" if isinstance(value, str) and value.isdigit() else "state",
                    operator=operator,
                    value=value
                )
            except (KeyError, ValueError) as e:
                raise ValueError(f"Invalid filter syntax for {entity_key}: {e}")
        else:
            # Simple filter syntax
            if isinstance(filter_value, list):
                operator = FilterOperator.IN
            else:
                operator = FilterOperator.EQUALS
            
            return UniversalFilter(
                entity_type=EntityType(entity_key),
                field="id" if isinstance(filter_value, str) and filter_value.isdigit() else "state",
                operator=operator,
                value=filter_value
            )
    
    def _apply_logical_filters(self, data: List, logical_filters: List[LogicalFilter], 
                             entity_type: EntityType) -> List:
        """Apply logical filters (AND/OR combinations)"""
        
        for logical_filter in logical_filters:
            data = self._apply_single_logical_filter(data, logical_filter, entity_type)
        
        return data
    
    def _apply_single_logical_filter(self, data: List, logical_filter: LogicalFilter,
                                   entity_type: EntityType) -> List:
        """Apply a single logical filter (AND or OR)"""
        
        if logical_filter.operator == "and":
            # AND: Apply all conditions, item must match ALL
            result = data
            for condition in logical_filter.filters:
                result = self._apply_condition(result, condition, entity_type)
            return result
        
        elif logical_filter.operator == "or":
            # OR: Apply all conditions, item must match ANY
            all_results = set()
            for condition in logical_filter.filters:
                condition_results = self._apply_condition(data, condition, entity_type)
                # Use item IDs or string representation for set operations
                for item in condition_results:
                    item_key = item.get("id", str(item))
                    all_results.add(item_key)
            
            # Return items that matched any condition
            return [item for item in data if item.get("id", str(item)) in all_results]
        
        return data
    
    def _apply_condition(self, data: List, condition: Union[LogicalFilter, Dict[str, Any]], 
                        entity_type: EntityType) -> List:
        """Apply a single condition (can be logical or simple filter)"""
        
        if isinstance(condition, LogicalFilter):
            return self._apply_single_logical_filter(data, condition, entity_type)
        
        elif isinstance(condition, dict):
            # Convert dict condition to FilterSet and apply
            temp_filter_set = self.parse_prompt_filters(condition)
            return self._apply_filterset_to_data(data, temp_filter_set, entity_type)
        
        return data
    
    def _apply_filterset_to_data(self, data: List, filter_set: FilterSet, entity_type: EntityType) -> List:
        """Apply a FilterSet to data (helper method)"""
        result = data
        
        if filter_set.period_filter:
            result = self._apply_period_filter(result, filter_set.period_filter)
        
        if filter_set.cross_entity_filters:
            result = self._apply_cross_entity_filters(result, filter_set.cross_entity_filters, entity_type)
        
        if filter_set.entity_filters:
            result = self._apply_entity_filters(result, filter_set.entity_filters)
        
        return result
    
    async def _fetch_base_data(self, entity_type: EntityType) -> List:
        """Fetch base data for an entity type"""
        # This would call the appropriate client method
        # For now, return empty list (tests pass their own data)
        return []