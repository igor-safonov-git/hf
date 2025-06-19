"""
Universal Chart Processor - Direct JSON to Data via UniversalFilterEngine
Eliminates the need for specific methods like hires_by_recruiter()
"""

from typing import Dict, List, Any, Optional, Union
from universal_filter_engine import UniversalFilterEngine
from universal_filter import EntityType
from enhanced_metrics_calculator import EnhancedMetricsCalculator
import logging

logger = logging.getLogger(__name__)

class UniversalChartProcessor:
    """Processes any chart configuration directly through UniversalFilterEngine"""
    
    def __init__(self, calc: EnhancedMetricsCalculator):
        self.calc = calc
        self.filter_engine = calc.filter_engine
    
    async def process_chart_request(self, entity: str, operation: str = "count", 
                                  group_by: Optional[str] = None, 
                                  filters: Optional[Dict[str, Any]] = None,
                                  value_field: Optional[str] = None) -> Dict[str, Any]:
        """
        Universal chart processor - handles any entity/operation/grouping combination
        
        Args:
            entity: Target entity (applicants, hires, vacancies, etc.)
            operation: count, avg, sum
            group_by: Field to group by (recruiters, sources, stages, etc.)
            filters: Filter conditions (period, entity filters, etc.)
            
        Returns:
            Chart-ready data: {"labels": [...], "values": [...]}
        """
        try:
            # Step 1: Get base entity data with filtering
            entity_type = self._map_entity_to_type(entity)
            base_data = await self._get_filtered_entity_data(entity_type, filters)
            
            # Step 2: Apply grouping if specified
            if group_by:
                grouped_data = await self._group_data(base_data, group_by, entity_type, filters)
            else:
                # No grouping - single value
                grouped_data = {entity: base_data}
            
            # Step 3: Apply operation (count, avg, sum)
            result_data = self._apply_operation(grouped_data, operation)
            
            # Step 4: Format for charts
            return self._format_for_chart(result_data)
            
        except Exception as e:
            logger.error(f"Universal chart processing error: {e}")
            return {"labels": ["Error"], "values": [0], "title": f"Error processing {entity}"}
    
    def _map_entity_to_type(self, entity: str) -> EntityType:
        """Map entity string to EntityType enum"""
        mapping = {
            "applicants": EntityType.APPLICANTS,
            "hires": EntityType.HIRES,
            "vacancies": EntityType.VACANCIES,
            "recruiters": EntityType.RECRUITERS,
            "sources": EntityType.SOURCES,
            "stages": EntityType.STAGES,
            "actions": EntityType.ACTIONS
        }
        return mapping.get(entity, EntityType.APPLICANTS)
    
    async def _get_filtered_entity_data(self, entity_type: EntityType, 
                                      filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get entity data with filters applied via UniversalFilterEngine"""
        
        # Get base data using the calculator with filters passed through
        if entity_type == EntityType.APPLICANTS:
            base_data = await self.calc.applicants_all(filters)
        elif entity_type == EntityType.HIRES:
            base_data = await self.calc.hires(filters)
        elif entity_type == EntityType.VACANCIES:
            base_data = await self.calc.vacancies_all(filters)
        elif entity_type == EntityType.RECRUITERS:
            base_data = await self.calc.recruiters_all(filters)
        elif entity_type == EntityType.SOURCES:
            base_data = await self.calc.sources_all(filters)
        else:
            base_data = []
        
        # Enhanced metrics calculator methods already handle filtering
        # No need for additional UniversalFilterEngine filtering
        return base_data
    
    async def _group_data(self, data: List[Dict[str, Any]], group_by: str, 
                         entity_type: EntityType, filters: Optional[Dict[str, Any]]) -> Dict[str, List]:
        """Group data by the specified field"""
        
        if group_by == "recruiters":
            return await self._group_by_recruiters(data, entity_type)
        elif group_by == "sources":
            return await self._group_by_sources(data)
        elif group_by == "stages" or group_by == "status":
            return await self._group_by_stages(data, entity_type, filters)
        elif group_by == "vacancies":
            return self._group_by_vacancies(data)
        elif group_by == "month" or group_by == "date":
            return self._group_by_date(data, entity_type, group_by)
        else:
            # Generic grouping by field name
            return self._group_by_field(data, group_by)
    
    async def _group_by_recruiters(self, data: List[Dict[str, Any]], 
                                 entity_type: EntityType) -> Dict[str, List]:
        """Group data by recruiters using log analysis"""
        from analyze_logs import LogAnalyzer
        
        # For hires and applicants, get recruiter from logs
        if entity_type in [EntityType.HIRES, EntityType.APPLICANTS]:
            analyzer = LogAnalyzer(self.calc.client.db_path)
            all_logs = analyzer.get_merged_logs()
            
            groups = {}
            for item in data:
                # Get applicant_id from item (different field names for different entities)
                applicant_id = item.get('applicant_id') or item.get('id')
                recruiter_name = 'Unknown'
                
                # Find recruiter from logs
                applicant_logs = [log for log in all_logs if log.get('applicant_id') == applicant_id]
                if applicant_logs:
                    recent_log = max(applicant_logs, key=lambda x: x.get('created', ''))
                    account_info = recent_log.get('account_info', {})
                    if isinstance(account_info, dict):
                        recruiter_name = account_info.get('name', 'Unknown')
                
                if recruiter_name not in groups:
                    groups[recruiter_name] = []
                groups[recruiter_name].append(item)
            
            return groups
        
        # For other entities, try to use recruiter field directly
        return self._group_by_field(data, 'recruiter')
    
    async def _group_by_sources(self, data: List[Dict[str, Any]]) -> Dict[str, List]:
        """Group data by sources using logs and API mapping"""
        
        # Get source mapping from API
        try:
            api_sources = await self.calc.sources_all()
            source_map = {str(src['id']): src['name'] for src in api_sources}
        except:
            source_map = {}
        
        # Add common source name patterns for better mapping
        source_patterns = {
            'headhunter': 'HeadHunter',
            'hh': 'HeadHunter', 
            'superjob': 'SuperJob',
            'linkedin': 'LinkedIn',
            'habr': 'Хабр карьера',
            'github': 'Github',
            'work.ua': 'Work.ua',
            'robota.ua': 'Robota.ua',
            'avito': 'Avito',
            'vk': 'VK',
            'facebook': 'Facebook'
        }
        
        # Get logs for source information
        analyzer = self.calc.cached_log_analyzer
        all_logs = analyzer.get_merged_logs()
        
        groups = {}
        for item in data:
            # Get applicant ID from either 'applicant_id' or 'id' field
            applicant_id = item.get('applicant_id') or item.get('id')
            source_name = 'Unknown'
            
            # Find source from logs for this applicant
            if applicant_id:
                applicant_logs = [log for log in all_logs if log.get('applicant_id') == applicant_id]
                for log in applicant_logs:
                    if log.get('source'):
                        source_id = str(log['source'])
                        
                        # Try API mapping first
                        if source_id in source_map:
                            source_name = source_map[source_id]
                        else:
                            # Try pattern matching for common sources
                            source_lower = source_id.lower()
                            matched = False
                            for pattern, name in source_patterns.items():
                                if pattern in source_lower:
                                    source_name = name
                                    matched = True
                                    break
                            
                            # If no pattern match, use a cleaner name
                            if not matched:
                                if len(source_id) > 10:  # Long IDs get shortened
                                    source_name = f'External Source #{source_id[-6:]}'
                                else:
                                    source_name = f'Source {source_id}'
                        break
            
            if source_name not in groups:
                groups[source_name] = []
            groups[source_name].append(item)
        
        return groups
    
    async def _group_by_stages(self, data: List[Dict[str, Any]], 
                             entity_type: EntityType, filters: Optional[Dict[str, Any]]) -> Dict[str, List]:
        """Group data by stages/status using log data"""
        from analyze_logs import LogAnalyzer
        
        analyzer = LogAnalyzer(self.calc.client.db_path)
        all_logs = analyzer.get_merged_logs()
        status_logs = [log for log in all_logs if log.get('type') == 'STATUS']
        
        # Apply period filtering to logs if specified
        if filters and 'period' in filters:
            period_str = filters['period']
            status_logs = self.calc._apply_period_filter(status_logs, period_str)
        
        # Group by status name
        groups = {}
        for log in status_logs:
            status_name = log.get('status_name', 'Unknown')
            if status_name not in groups:
                groups[status_name] = []
            groups[status_name].append(log)
        
        return groups
    
    def _group_by_date(self, data: List[Dict[str, Any]], entity_type: EntityType, group_by: str) -> Dict[str, List]:
        """Group data by date periods (month, week, etc.) with complete time series"""
        from datetime import datetime, timedelta
        from dateutil.relativedelta import relativedelta
        
        groups = {}
        
        # First, create a complete set of month buckets for the period
        now = datetime.now()
        period_months = []
        
        for i in range(12):  # 12 months back (1 year)
            month_date = now - relativedelta(months=i)
            month_label = month_date.strftime("%B %Y")
            period_months.append(month_label)
            groups[month_label] = []
        
        # Reverse to show chronological order
        period_months.reverse()
        
        for item in data:
            # Determine the date field to use based on entity type
            date_field = None
            if entity_type == EntityType.HIRES:
                date_field = item.get('hired_date') or item.get('created')
            elif entity_type == EntityType.APPLICANTS:
                date_field = item.get('created')
            else:
                date_field = item.get('created')
            
            if not date_field:
                continue
                
            try:
                # Parse the date
                if isinstance(date_field, str):
                    if 'T' in date_field and '+' in date_field:
                        date_part = date_field.split('+')[0]
                        parsed_date = datetime.fromisoformat(date_part)
                    else:
                        parsed_date = datetime.fromisoformat(date_field)
                else:
                    continue
                
                # Group by month
                if group_by == "month":
                    month_label = parsed_date.strftime("%B %Y")  # e.g., "January 2024"
                else:
                    # Default to month grouping
                    month_label = parsed_date.strftime("%B %Y")
                
                # Only add to groups if it's within our period months
                if month_label in groups:
                    groups[month_label].append(item)
                
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse date '{date_field}': {e}")
                continue
        
        # Ensure chronological order and return only period months
        sorted_groups = {}
        for month in period_months:
            sorted_groups[month] = groups[month]
        
        return sorted_groups if any(groups.values()) else {"No Date Data": data}
    
    def _group_by_vacancies(self, data: List[Dict[str, Any]]) -> Dict[str, List]:
        """Group data by vacancies"""
        groups = {}
        for item in data:
            vacancy_name = 'Unknown'
            if 'vacancy_position' in item:
                vacancy_name = item['vacancy_position']
            elif 'position' in item:
                vacancy_name = item['position']
            
            if vacancy_name not in groups:
                groups[vacancy_name] = []
            groups[vacancy_name].append(item)
        
        return groups
    
    def _group_by_field(self, data: List[Dict[str, Any]], field_name: str) -> Dict[str, List]:
        """Generic grouping by any field with intelligent fallbacks"""
        
        # Special handling for problematic groupings
        if field_name == "hires" and data:
            # If trying to group hires by "hires" field, create time-based groups instead
            return self._group_by_time_ranges(data)
        
        groups = {}
        for item in data:
            field_value = item.get(field_name, 'Unknown')
            if isinstance(field_value, dict):
                field_value = field_value.get('name', 'Unknown')
            
            field_key = str(field_value)
            if field_key not in groups:
                groups[field_key] = []
            groups[field_key].append(item)
        
        # If all items are "Unknown", try alternative grouping strategies
        if len(groups) == 1 and "Unknown" in groups:
            logger.warning(f"All items grouped as 'Unknown' for field '{field_name}', trying alternative grouping")
            return self._try_alternative_grouping(data, field_name)
        
        return groups
    
    def _group_by_time_ranges(self, data: List[Dict[str, Any]]) -> Dict[str, List]:
        """Group data by time-to-hire ranges for time distribution charts"""
        groups = {
            "0-10 days": [],
            "11-30 days": [],
            "31-60 days": [],
            "60+ days": []
        }
        
        for item in data:
            time_to_hire = item.get('time_to_hire', 0)
            if isinstance(time_to_hire, str):
                try:
                    time_to_hire = float(time_to_hire)
                except ValueError:
                    time_to_hire = 0
            
            if time_to_hire <= 10:
                groups["0-10 days"].append(item)
            elif time_to_hire <= 30:
                groups["11-30 days"].append(item)
            elif time_to_hire <= 60:
                groups["31-60 days"].append(item)
            else:
                groups["60+ days"].append(item)
        
        return groups
    
    def _try_alternative_grouping(self, data: List[Dict[str, Any]], original_field: str) -> Dict[str, List]:
        """Try alternative grouping strategies when original field fails"""
        
        # Try common alternative fields based on data type
        alternative_fields = []
        
        if data:
            sample_item = data[0]
            
            # For hire data, try recruiter-based grouping
            if 'hired_date' in sample_item or 'time_to_hire' in sample_item:
                alternative_fields = ['recruiter_name', 'source_name', 'vacancy_position']
            
            # For applicant data, try status-based grouping  
            elif 'status' in sample_item or 'applicant_id' in sample_item:
                alternative_fields = ['status_name', 'source_name', 'vacancy_position']
        
        # Try each alternative field
        for alt_field in alternative_fields:
            groups = {}
            unknown_count = 0
            
            for item in data:
                field_value = item.get(alt_field, 'Unknown')
                if isinstance(field_value, dict):
                    field_value = field_value.get('name', 'Unknown')
                
                field_key = str(field_value)
                if field_key == 'Unknown':
                    unknown_count += 1
                
                if field_key not in groups:
                    groups[field_key] = []
                groups[field_key].append(item)
            
            # If this alternative produces meaningful groups (not all unknown), use it
            if len(groups) > 1 or unknown_count < len(data) * 0.8:
                logger.info(f"Using alternative grouping '{alt_field}' instead of '{original_field}'")
                return groups
        
        # If all alternatives fail, return a single group
        logger.warning(f"No meaningful grouping found for field '{original_field}', returning single group")
        return {"All Items": data}
    
    def _apply_operation(self, grouped_data: Dict[str, List], operation: str) -> Dict[str, Union[int, float]]:
        """Apply count/avg/sum operations to grouped data"""
        result = {}
        
        for group_name, group_items in grouped_data.items():
            if operation == "count":
                result[group_name] = len(group_items)
            elif operation == "avg":
                # Calculate average of time_to_hire (in days)
                numeric_values = []
                for item in group_items:
                    # Prioritize time_to_hire field (in days) over time_to_hire_hours
                    if 'time_to_hire' in item and isinstance(item['time_to_hire'], (int, float)):
                        numeric_values.append(item['time_to_hire'])
                    else:
                        # Fallback to any numeric field with 'time' in name
                        for key, value in item.items():
                            if isinstance(value, (int, float)) and 'time' in key.lower() and 'hour' not in key.lower():
                                numeric_values.append(value)
                                break
                
                if numeric_values:
                    result[group_name] = sum(numeric_values) / len(numeric_values)
                else:
                    result[group_name] = 0
            elif operation == "sum":
                # Sum numeric values
                total = 0
                for item in group_items:
                    for key, value in item.items():
                        if isinstance(value, (int, float)):
                            total += value
                            break
                result[group_name] = total
            else:
                # Default to count
                result[group_name] = len(group_items)
        
        return result
    
    def _format_for_chart(self, data: Dict[str, Union[int, float]]) -> Dict[str, Any]:
        """Format data for chart consumption"""
        return {
            "labels": list(data.keys()),
            "values": list(data.values()),
            "title": ""
        }

# Convenience function for easy integration
async def process_chart_via_universal_engine(entity: str, operation: str = "count",
                                           group_by: Optional[str] = None,
                                           filters: Optional[Dict[str, Any]] = None,
                                           calc: EnhancedMetricsCalculator = None,
                                           value_field: Optional[str] = None) -> Dict[str, Any]:
    """
    Main entry point for universal chart processing
    
    Usage:
        result = await process_chart_via_universal_engine(
            entity="hires",
            operation="count", 
            group_by="recruiters",
            filters={"period": "1 year"}
        )
    """
    processor = UniversalChartProcessor(calc)
    return await processor.process_chart_request(entity, operation, group_by, filters, value_field)