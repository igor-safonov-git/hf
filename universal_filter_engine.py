from typing import Dict, List, Any, Optional, Union
from universal_filter import UniversalFilter, FilterSet, PeriodFilter, EntityType, FilterOperator, LogicalFilter
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class UniversalFilterEngine:
    """Centralized engine for processing all filters"""
    
    def __init__(self, db_client, log_analyzer, calculator=None):
        self.db_client = db_client
        self.log_analyzer = log_analyzer
        self.calculator = calculator  # Reference to parent calculator to avoid circular imports
        self.entity_relationships = self._build_entity_relationships()
    
    def _build_entity_relationships(self) -> Dict[str, Dict[str, str]]:
        """Define how entities relate to each other"""
        return {
            "applicants": {
                "recruiters": "recruiter_id",
                "vacancies": "vacancy_id",
                "sources": "source_id",
                "stages": "stage_id",
                "divisions": "division_id",
                "hiring_managers": "hiring_manager_id"
            },
            "vacancies": {
                "recruiters": "recruiter_id",
                "hiring_managers": "hiring_manager_id",
                "divisions": "division_id",
                "sources": "source_id",
                "stages": "stage_id",
                "vacancies": "state"  # Special case for vacancy state filtering
            },
            "hires": {
                "recruiters": "recruiter_id",
                "sources": "source_id",
                "vacancies": "vacancy_id",
                "stages": "stage_id",
                "divisions": "division_id",
                "hiring_managers": "hiring_manager_id"
            },
            "sources": {
                # Sources can be filtered by entities that use them
                "recruiters": "recruiter_id",  # Sources used by specific recruiters
                "vacancies": "vacancy_id",     # Sources for specific vacancies
                "stages": "stage_id",          # Sources at specific stages
                "divisions": "division_id",    # Sources used in divisions
                "hiring_managers": "hiring_manager_id",
                "sources": "id"  # Self-reference for source filtering
            },
            "recruiters": {
                # Recruiters can be filtered by their activity
                "vacancies": "vacancy_id",     # Recruiters working on specific vacancies
                "sources": "source_id",        # Recruiters using specific sources
                "divisions": "division_id",    # Recruiters in specific divisions
                "stages": "stage_id",          # Recruiters with applicants at stages
                "hiring_managers": "hiring_manager_id",
                "recruiters": "id"  # Self-reference for recruiter filtering
            },
            "stages": {
                "vacancies": "vacancy_id",
                "recruiters": "recruiter_id",
                "sources": "source_id",
                "divisions": "division_id",
                "hiring_managers": "hiring_manager_id",
                "stages": "id"  # Self-reference
            },
            "divisions": {
                "vacancies": "vacancy_id",
                "recruiters": "recruiter_id",
                "sources": "source_id",
                "stages": "stage_id",
                "hiring_managers": "hiring_manager_id",
                "divisions": "id"  # Self-reference
            },
            "hiring_managers": {
                "vacancies": "vacancy_id",
                "recruiters": "recruiter_id",
                "sources": "source_id",
                "stages": "stage_id",
                "divisions": "division_id",
                "hiring_managers": "id"  # Self-reference
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
            result = await self._apply_logical_filters(result, filters.logical_filters, entity_type)
        
        # Apply period filters
        if filters.period_filter:
            result = self._apply_period_filter(result, filters.period_filter)
        
        # Apply cross-entity filters (relationships)
        if filters.cross_entity_filters:
            result = await self._apply_cross_entity_filters(result, filters.cross_entity_filters, entity_type)
        
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
    
    async def _apply_cross_entity_filters(self, data: List, filters: List[UniversalFilter], 
                                  target_entity: EntityType) -> List:
        """Apply filters based on entity relationships"""
        
        for filter_obj in filters:
            data = await self._apply_cross_entity_filter(data, filter_obj, target_entity)
        
        return data
    
    async def _apply_cross_entity_filter(self, data: List, filter_obj: UniversalFilter, 
                                        target_entity: EntityType) -> List:
        """Apply a single cross-entity filter with proper entity lookup"""
        
        logger.debug(f"Applying cross-entity filter: {target_entity.value} filtered by {filter_obj.entity_type.value}.{filter_obj.field} = {filter_obj.value}")
        
        # Get the relationship field (e.g., "vacancy_id" for applicants->vacancies)
        relationship_key = self.entity_relationships.get(
            target_entity.value, {}
        ).get(filter_obj.entity_type.value)
        
        if not relationship_key:
            logger.warning(f"No relationship defined between {target_entity.value} and {filter_obj.entity_type.value}")
            return data  # No relationship defined, return unfiltered
        
        logger.debug(f"Using relationship key: {relationship_key}")
        
        # Special handling for complex cross-entity relationships
        
        # 1. For vacancy state filtering, we need to look up vacancy IDs that match the criteria
        if filter_obj.entity_type == EntityType.VACANCIES and filter_obj.field == "state":
            matching_vacancy_ids = await self._get_matching_vacancy_ids(filter_obj)
            logger.info(f"Found {len(matching_vacancy_ids)} vacancies with state={filter_obj.value}")
            
            # Filter data by those vacancy IDs
            filtered_data = []
            for item in data:
                vacancy_id = item.get(relationship_key)
                if vacancy_id in matching_vacancy_ids:
                    filtered_data.append(item)
            
            logger.info(f"Filtered {len(data)} items to {len(filtered_data)} items based on vacancy state")
            return filtered_data
        
        # 2. For sources/recruiters filtering, we need reverse lookup through logs
        elif target_entity in [EntityType.SOURCES, EntityType.RECRUITERS]:
            return await self._apply_reverse_entity_filter(data, filter_obj, target_entity)
        
        # 3. For filtering applicants by recruiters, extract recruiter info from account_info
        elif target_entity == EntityType.APPLICANTS and filter_obj.entity_type == EntityType.RECRUITERS:
            filtered_data = []
            for item in data:
                account_info = item.get('account_info', {})
                if isinstance(account_info, dict):
                    recruiter_id = account_info.get('id')
                    # Check if recruiter_id matches the filter
                    if self._matches_filter(recruiter_id, filter_obj):
                        filtered_data.append(item)
            
            logger.info(f"Filtered {len(data)} applicants to {len(filtered_data)} by recruiter {filter_obj.value}")
            return filtered_data
        
        # 4. For filtering applicants by sources, extract source info from source field
        elif target_entity == EntityType.APPLICANTS and filter_obj.entity_type == EntityType.SOURCES:
            filtered_data = []
            for item in data:
                source_id = item.get('source')
                # Check if source_id matches the filter
                if self._matches_filter(source_id, filter_obj):
                    filtered_data.append(item)
            
            logger.info(f"Filtered {len(data)} applicants to {len(filtered_data)} by source {filter_obj.value}")
            return filtered_data
        
        # For other cross-entity filters, use the simple field matching approach
        return self._apply_single_filter(data, filter_obj, relationship_key)
    
    async def _apply_reverse_entity_filter(self, data: List, filter_obj: UniversalFilter,
                                           target_entity: EntityType) -> List:
        """Apply filtering for sources/recruiters through reverse lookup in logs"""
        
        if not self.log_analyzer:
            logger.warning("No log analyzer available for reverse entity filtering")
            return data
        
        # Get all logs to find relationships
        all_logs = self.log_analyzer.get_merged_logs()
        
        # Build a mapping of entity IDs that match the filter
        matching_entity_ids = set()
        
        if target_entity == EntityType.SOURCES:
            # Find sources that match the filter criteria
            if filter_obj.entity_type == EntityType.VACANCIES:
                # Find sources used for specific vacancies
                target_vacancy_id = filter_obj.value
                for log in all_logs:
                    if (log.get('vacancy_id') == target_vacancy_id or 
                        str(log.get('vacancy_id')) == str(target_vacancy_id)):
                        source_id = log.get('source_id')
                        if source_id:
                            matching_entity_ids.add(source_id)
            
            elif filter_obj.entity_type == EntityType.RECRUITERS:
                # Find sources used by specific recruiters
                target_recruiter_id = filter_obj.value
                for log in all_logs:
                    account_info = log.get('account_info', {})
                    if isinstance(account_info, dict):
                        recruiter_id = account_info.get('id')
                        if (recruiter_id == target_recruiter_id or 
                            str(recruiter_id) == str(target_recruiter_id)):
                            source_id = log.get('source_id')
                            if source_id:
                                matching_entity_ids.add(source_id)
        
        elif target_entity == EntityType.RECRUITERS:
            # Find recruiters that match the filter criteria
            if filter_obj.entity_type == EntityType.VACANCIES:
                # Find recruiters working on specific vacancies
                if filter_obj.field == "state":
                    # Get vacancies with the specified state
                    matching_vacancy_ids = await self._get_matching_vacancy_ids(filter_obj)
                    for log in all_logs:
                        if log.get('vacancy_id') in matching_vacancy_ids:
                            account_info = log.get('account_info', {})
                            if isinstance(account_info, dict):
                                recruiter_id = account_info.get('id')
                                if recruiter_id:
                                    matching_entity_ids.add(recruiter_id)
                else:
                    # Direct vacancy ID filter
                    target_vacancy_id = filter_obj.value
                    for log in all_logs:
                        if (log.get('vacancy_id') == target_vacancy_id or 
                            str(log.get('vacancy_id')) == str(target_vacancy_id)):
                            account_info = log.get('account_info', {})
                            if isinstance(account_info, dict):
                                recruiter_id = account_info.get('id')
                                if recruiter_id:
                                    matching_entity_ids.add(recruiter_id)
            
            elif filter_obj.entity_type == EntityType.SOURCES:
                # Find recruiters using specific sources
                target_source_id = filter_obj.value
                for log in all_logs:
                    if (log.get('source_id') == target_source_id or 
                        str(log.get('source_id')) == str(target_source_id)):
                        account_info = log.get('account_info', {})
                        if isinstance(account_info, dict):
                            recruiter_id = account_info.get('id')
                            if recruiter_id:
                                matching_entity_ids.add(recruiter_id)
        
        # Filter the data based on matching entity IDs
        filtered_data = []
        for item in data:
            item_id = item.get('id')
            if item_id in matching_entity_ids or str(item_id) in {str(id) for id in matching_entity_ids}:
                filtered_data.append(item)
        
        logger.info(f"Reverse filtered {len(data)} {target_entity.value} to {len(filtered_data)} items")
        return filtered_data
    
    async def _get_matching_vacancy_ids(self, filter_obj: UniversalFilter) -> set:
        """Get vacancy IDs that match the given filter criteria"""
        try:
            # Use the parent calculator if available
            if self.calculator:
                calc = self.calculator
            else:
                # Fallback: create a temporary calculator if none provided
                from enhanced_metrics_calculator import EnhancedMetricsCalculator
                calc = EnhancedMetricsCalculator(self.db_client, self.log_analyzer)
            
            # Get all vacancies and filter by the criteria
            all_vacancies = await calc.vacancies_all()
            matching_vacancies = []
            
            for vacancy in all_vacancies:
                field_value = vacancy.get(filter_obj.field)
                if self._matches_filter(field_value, filter_obj):
                    matching_vacancies.append(vacancy)
            
            # Return the set of matching vacancy IDs
            return {v.get('id') for v in matching_vacancies if v.get('id')}
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting matching vacancy IDs: {e}")
            return set()
    
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
    
    def _determine_filter_field(self, entity_key: str, filter_value: Any) -> str:
        """Determine the appropriate field name based on entity type and filter value"""
        
        # For numeric IDs, always use 'id' field
        if isinstance(filter_value, str) and filter_value.isdigit():
            return "id"
        
        # Special cases for specific entity types
        if entity_key == "vacancies":
            # For vacancies, 'open' and 'closed' refer to the 'state' field
            if isinstance(filter_value, str) and filter_value.lower() in ['open', 'closed']:
                return "state"
        
        elif entity_key == "recruiters":
            # For recruiters, non-digit strings would be names
            if isinstance(filter_value, str) and not filter_value.isdigit():
                return "name"
        
        elif entity_key == "sources":
            # For sources, non-digit strings would be names
            if isinstance(filter_value, str) and not filter_value.isdigit():
                return "name"
        
        elif entity_key == "stages":
            # For stages, non-digit strings would be names
            if isinstance(filter_value, str) and not filter_value.isdigit():
                return "name"
        
        # Default to 'id' for unrecognized patterns
        return "id"
    
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
                
                # Determine the appropriate field based on entity type and filter value
                field = self._determine_filter_field(entity_key, value)
                
                return UniversalFilter(
                    entity_type=EntityType(entity_key),
                    field=field,
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
            
            # Determine the appropriate field based on entity type and filter value
            field = self._determine_filter_field(entity_key, filter_value)
            
            return UniversalFilter(
                entity_type=EntityType(entity_key),
                field=field,
                operator=operator,
                value=filter_value
            )
    
    async def _apply_logical_filters(self, data: List, logical_filters: List[LogicalFilter], 
                             entity_type: EntityType) -> List:
        """Apply logical filters (AND/OR combinations)"""
        
        for logical_filter in logical_filters:
            data = await self._apply_single_logical_filter(data, logical_filter, entity_type)
        
        return data
    
    async def _apply_single_logical_filter(self, data: List, logical_filter: LogicalFilter,
                                   entity_type: EntityType) -> List:
        """Apply a single logical filter (AND or OR)"""
        
        if logical_filter.operator == "and":
            # AND: Apply all conditions, item must match ALL
            result = data
            for condition in logical_filter.filters:
                result = await self._apply_condition(result, condition, entity_type)
            return result
        
        elif logical_filter.operator == "or":
            # OR: Apply all conditions, item must match ANY
            all_results = set()
            for condition in logical_filter.filters:
                condition_results = await self._apply_condition(data, condition, entity_type)
                # Use item IDs or string representation for set operations
                for item in condition_results:
                    item_key = item.get("id", str(item))
                    all_results.add(item_key)
            
            # Return items that matched any condition
            return [item for item in data if item.get("id", str(item)) in all_results]
        
        return data
    
    async def _apply_condition(self, data: List, condition: Union[LogicalFilter, Dict[str, Any]], 
                        entity_type: EntityType) -> List:
        """Apply a single condition (can be logical or simple filter)"""
        
        if isinstance(condition, LogicalFilter):
            return await self._apply_single_logical_filter(data, condition, entity_type)
        
        elif isinstance(condition, dict):
            # Convert dict condition to FilterSet and apply
            temp_filter_set = self.parse_prompt_filters(condition)
            return await self._apply_filterset_to_data(data, temp_filter_set, entity_type)
        
        return data
    
    async def _apply_filterset_to_data(self, data: List, filter_set: FilterSet, entity_type: EntityType) -> List:
        """Apply a FilterSet to data (helper method)"""
        result = data
        
        if filter_set.period_filter:
            result = self._apply_period_filter(result, filter_set.period_filter)
        
        if filter_set.cross_entity_filters:
            result = await self._apply_cross_entity_filters(result, filter_set.cross_entity_filters, entity_type)
        
        if filter_set.entity_filters:
            result = self._apply_entity_filters(result, filter_set.entity_filters)
        
        return result
    
    async def _fetch_base_data(self, entity_type: EntityType) -> List:
        """Fetch base data for an entity type"""
        # This would call the appropriate client method
        # For now, return empty list (tests pass their own data)
        return []