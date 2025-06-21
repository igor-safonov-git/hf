"""
Process chart data from report JSON for visualization - Version 2
Improved with better error handling, validation, and maintainability
"""

import logging
from typing import Dict, Any, List, Optional, TypedDict, Union, Callable
from collections import Counter
from functools import wraps
from huntflow_local_client import HuntflowLocalClient
from enhanced_metrics_calculator import EnhancedMetricsCalculator
from universal_chart_processor import process_chart_via_universal_engine
import asyncio

# Removed old entity configuration system - now using Universal Chart Processor

# Configure logging
logger = logging.getLogger(__name__)

# Constants
FIELD_KEY = "field"
ENTITY_KEY = "entity"
OPERATION_KEY = "operation"
COUNT_OPERATION = "count"
SUM_OPERATION = "sum"
AVG_OPERATION = "avg"

# Default values
DEFAULT_CONVERSION_RATE = 6.3
UNKNOWN_LABEL = "Unknown"
NO_DATA_LABEL = "No Data"
ERROR_LABEL = "Error"

# Type definitions
class ChartPoint(TypedDict):
    x: Union[int, float]
    y: Union[int, float]

class ChartData(TypedDict, total=False):
    labels: List[str]
    values: List[Union[int, float]]
    points: List[ChartPoint]
    title: str

class GroupByConfig(TypedDict, total=False):
    field: Optional[str]

class YAxisConfig(TypedDict):
    entity: str
    group_by: Optional[Union[GroupByConfig, str]]

class ChartConfig(TypedDict):
    y_axis: YAxisConfig
    graph_description: Optional[str]

class MetricsQuery(TypedDict):
    operation: str
    entity: str
    value_field: Optional[str]
    filters: Dict[str, Any]
    # No group_by field - uses report-level metrics_group_by

class ChartQuery(TypedDict):
    operation: str
    entity: str
    value_field: Optional[str]
    group_by: Optional[Union[GroupByConfig, str]]
    filters: Dict[str, Any]

class MainMetricConfig(TypedDict):
    label: str
    value: MetricsQuery

class SecondaryMetricConfig(TypedDict):
    label: str
    value: MetricsQuery

class ReportJson(TypedDict, total=False):
    report_title: str
    period: str
    metrics_group_by: Optional[str]  # NEW
    main_metric: MainMetricConfig
    secondary_metrics: List[SecondaryMetricConfig]
    chart: ChartConfig


# Error handling
class ChartProcessingError(Exception):
    """Custom exception for chart processing errors."""
    pass


def handle_chart_errors(func):
    """Decorator to handle common chart processing errors."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ChartProcessingError:
            # Re-raise our custom exceptions as-is
            raise
        except (AttributeError, TypeError) as e:
            # Extract useful context from function
            context = f"{func.__name__}"
            if args and hasattr(args[0], '__class__'):
                context = f"{args[0].__class__.__name__}.{func.__name__}"
            logger.error(f"Type error in {context}: {e}")
            raise ChartProcessingError(f"Invalid data type in {context}")
        except KeyError as e:
            context = f"{func.__name__}"
            logger.error(f"Missing key in {context}: {e}")
            raise ChartProcessingError(f"Missing required field: {e}")
        except (ValueError, IndexError) as e:
            context = f"{func.__name__}"
            logger.error(f"Data error in {context}: {e}")
            raise ChartProcessingError(f"Invalid data in {context}")
    return wrapper


def create_error_response(message: str = "Error loading data") -> ChartData:
    """Create a consistent error response."""
    return {
        "labels": [ERROR_LABEL],
        "values": [0],
        "title": message
    }


def create_no_data_response(entity: str = "") -> ChartData:
    """Create a consistent no-data response."""
    return {
        "labels": [NO_DATA_LABEL],
        "values": [0],
        "title": f"No data for {entity}" if entity else "No data available"
    }


def round_chart_values(chart_data: ChartData) -> ChartData:
    """Round numeric values in chart data to 1 decimal place."""
    if "values" in chart_data:
        rounded_values = []
        for value in chart_data["values"]:
            if isinstance(value, float):
                rounded_values.append(round(value, 1))
            else:
                rounded_values.append(value)
        chart_data["values"] = rounded_values
    
    if "points" in chart_data:
        rounded_points = []
        for point in chart_data["points"]:
            rounded_point = {}
            for key, value in point.items():
                if isinstance(value, float):
                    rounded_point[key] = round(value, 1)
                else:
                    rounded_point[key] = value
            rounded_points.append(rounded_point)
        chart_data["points"] = rounded_points
    
    return chart_data


# Input validation
def validate_report_json(report_json: Any) -> ReportJson:
    """Validate the complete structure of the report JSON."""
    if not isinstance(report_json, dict):
        raise ChartProcessingError("Report JSON must be a dictionary")
    
    # Validate required metrics_group_by field
    if "metrics_group_by" not in report_json:
        raise ChartProcessingError("metrics_group_by field is required")
    _validate_metrics_group_by(report_json["metrics_group_by"])
    
    # Validate chart section if present
    if "chart" in report_json:
        _validate_chart_section(report_json["chart"])
    
    # Validate main_metric section if present
    if "main_metric" in report_json:
        _validate_main_metric_section(report_json["main_metric"])
    
    # Validate secondary_metrics section if present
    if "secondary_metrics" in report_json:
        _validate_secondary_metrics_section(report_json["secondary_metrics"])
    
    return report_json


def _validate_chart_section(chart: Any) -> None:
    """Validate chart section structure."""
    if not isinstance(chart, dict):
        raise ChartProcessingError("Chart must be a dictionary")
    
    # Get chart type (default to 'bar' if not specified)
    chart_type = chart.get("type", "bar")
    
    # Table charts have different validation requirements
    if chart_type == "table":
        # Tables still need y_axis for entity/filters for now (to maintain compatibility)
        if "y_axis" not in chart:
            raise ChartProcessingError("Chart must have a y_axis")
        y_axis = chart["y_axis"]
        if not isinstance(y_axis, dict):
            raise ChartProcessingError("Y-axis must be a dictionary")
    else:
        # Validate y_axis (required for non-table charts)
        if "y_axis" not in chart:
            raise ChartProcessingError("Chart must have a y_axis")
        
        y_axis = chart["y_axis"]
        if not isinstance(y_axis, dict):
            raise ChartProcessingError("Y-axis must be a dictionary")
    
    # Entity is required
    if ENTITY_KEY not in y_axis:
        raise ChartProcessingError("Y-axis must have an entity")
    
    if not isinstance(y_axis[ENTITY_KEY], str):
        raise ChartProcessingError("Entity must be a string")
    
    # Validate group_by if present
    if "group_by" in y_axis and y_axis["group_by"] is not None:
        group_by = y_axis["group_by"]
        if isinstance(group_by, dict):
            if FIELD_KEY not in group_by:
                raise ChartProcessingError("group_by dict must have a field")
            if not isinstance(group_by[FIELD_KEY], (str, type(None))):
                raise ChartProcessingError("group_by field must be a string or null")
        elif not isinstance(group_by, str):
            raise ChartProcessingError("group_by must be a string, dict, or null")
    
    # Validate optional fields
    if "graph_description" in chart and not isinstance(chart["graph_description"], (str, type(None))):
        raise ChartProcessingError("graph_description must be a string or null")
    
    if "chart_type" in chart and not isinstance(chart["chart_type"], str):
        raise ChartProcessingError("chart_type must be a string")


def _validate_main_metric_section(main_metric: Any) -> None:
    """Validate main metric section structure."""
    if not isinstance(main_metric, dict):
        raise ChartProcessingError("Main metric must be a dictionary")
    
    # Validate label
    if "label" not in main_metric:
        raise ChartProcessingError("Main metric must have a label")
    if not isinstance(main_metric["label"], str):
        raise ChartProcessingError("Main metric label must be a string")
    
    # Validate value (required for metric processing)
    if "value" not in main_metric:
        raise ChartProcessingError("Main metric must have a value")
    
    value = main_metric["value"]
    if not isinstance(value, dict):
        raise ChartProcessingError("Main metric value must be a dictionary")
    
    # Use the metrics query validation
    _validate_metrics_query(value, "Main metric")


def _validate_metrics_group_by(metrics_group_by: Any) -> None:
    """Validate metrics_group_by field."""
    if metrics_group_by is None:
        raise ChartProcessingError("metrics_group_by is required and cannot be null")
    
    if not isinstance(metrics_group_by, str):
        raise ChartProcessingError("metrics_group_by must be a string")
    
    # Validate that it's a valid grouping field
    valid_groupings = {
        "recruiters", "sources", "stages", "vacancies", "divisions", 
        "hiring_managers"
    }
    if metrics_group_by not in valid_groupings:
        raise ChartProcessingError(f"metrics_group_by must be one of: {', '.join(valid_groupings)}")


def _validate_secondary_metrics_section(secondary_metrics: Any) -> None:
    """Validate secondary metrics section structure."""
    if not isinstance(secondary_metrics, list):
        raise ChartProcessingError("Secondary metrics must be a list")
    
    for i, metric in enumerate(secondary_metrics):
        if not isinstance(metric, dict):
            raise ChartProcessingError(f"Secondary metric {i} must be a dictionary")
        
        # Validate label
        if "label" not in metric:
            raise ChartProcessingError(f"Secondary metric {i} must have a label")
        if not isinstance(metric["label"], str):
            raise ChartProcessingError(f"Secondary metric {i} label must be a string")
        
        # Validate value
        if "value" not in metric:
            raise ChartProcessingError(f"Secondary metric {i} must have a value")
        
        value = metric["value"]
        if not isinstance(value, dict):
            raise ChartProcessingError(f"Secondary metric {i} value must be a dictionary")
        
        # Use same validation as main metric value
        _validate_metrics_query(value, f"Secondary metric {i}")


def _validate_metrics_query(query: Dict[str, Any], context: str = "Metrics query") -> None:
    """Validate a metrics query structure (used by main and secondary metrics)."""
    # Entity is required
    if ENTITY_KEY not in query:
        raise ChartProcessingError(f"{context} must have an entity")
    
    if not isinstance(query[ENTITY_KEY], str):
        raise ChartProcessingError(f"{context} entity must be a string")
    
    # Operation is required
    if OPERATION_KEY not in query:
        raise ChartProcessingError(f"{context} must have an operation")
    
    operation = query[OPERATION_KEY]
    if not isinstance(operation, str):
        raise ChartProcessingError(f"{context} operation must be a string")
    
    # Check if operation is valid
    valid_operations = {COUNT_OPERATION, SUM_OPERATION, AVG_OPERATION, "date_trunc"}
    if operation not in valid_operations:
        raise ChartProcessingError(f"{context} operation must be one of: {', '.join(valid_operations)}")
    
    # Filters are required
    if "filters" not in query:
        raise ChartProcessingError(f"{context} must have filters")
    
    if not isinstance(query["filters"], dict):
        raise ChartProcessingError(f"{context} filters must be a dictionary")
    
    # value_field is optional
    if "value_field" in query and query["value_field"] is not None:
        if not isinstance(query["value_field"], str):
            raise ChartProcessingError(f"{context} value_field must be a string or null")


# Removed old method whitelist system - Universal Chart Processor handles all requests


# Removed old handler system - Universal Chart Processor handles all chart requests


def normalize_group_by(group_by_obj: Optional[Union[GroupByConfig, str]]) -> Optional[str]:
    """Normalize group_by from various formats to a simple string."""
    if isinstance(group_by_obj, dict):
        return group_by_obj.get(FIELD_KEY)
    elif isinstance(group_by_obj, str):
        return group_by_obj
    return None


async def get_scatter_chart_data(x_axis_config: dict, y_axis_config: dict, calc: EnhancedMetricsCalculator, filters: Optional[Dict[str, Any]] = None) -> ChartData:
    """Get data for scatter charts using Universal Chart Processor."""
    try:
        # Extract configuration for both axes
        x_entity = x_axis_config.get(ENTITY_KEY, "")
        x_group_by = normalize_group_by(x_axis_config.get("group_by"))
        x_operation = x_axis_config.get("operation", "count")
        
        y_entity = y_axis_config.get(ENTITY_KEY, "")
        y_group_by = normalize_group_by(y_axis_config.get("group_by"))
        y_operation = y_axis_config.get("operation", "count")
        y_value_field = y_axis_config.get("value_field")
        
        logger.info(f"Scatter chart: X={x_entity}:{x_group_by}:{x_operation}, Y={y_entity}:{y_group_by}:{y_operation}")
        
        # Use Universal Chart Processor for both axes
        x_data = await process_chart_via_universal_engine(
            entity=x_entity,
            operation=x_operation,
            group_by=x_group_by,
            filters=filters,
            calc=calc
        )
        
        y_data = await process_chart_via_universal_engine(
            entity=y_entity,
            operation=y_operation,
            group_by=y_group_by,
            filters=filters,
            calc=calc,
            value_field=y_value_field
        )
        
        # Check for errors
        if x_data.get("labels") == ["Error"] or y_data.get("labels") == ["Error"]:
            return create_error_response("Failed to get scatter chart data")
        
        # Convert to coordinate pairs
        points = []
        
        # Handle case where both datasets have labels (common grouping keys)
        if "labels" in x_data and "labels" in y_data and "values" in x_data and "values" in y_data:
            # Create lookup dictionaries
            x_lookup = dict(zip(x_data["labels"], x_data["values"]))
            y_lookup = dict(zip(y_data["labels"], y_data["values"]))
            
            # Find common keys and create points
            common_keys = set(x_lookup.keys()) & set(y_lookup.keys())
            
            for key in common_keys:
                points.append({
                    "x": x_lookup[key],
                    "y": y_lookup[key]
                })
        
        # Handle case where we need to zip values directly (same ordering)
        elif len(x_data.get("values", [])) == len(y_data.get("values", [])):
            for x_val, y_val in zip(x_data["values"], y_data["values"]):
                points.append({
                    "x": x_val,
                    "y": y_val
                })
        
        chart_data = {
            "points": points,
            "title": ""
        }
        return round_chart_values(chart_data)
        
    except Exception as e:
        logger.error(f"Error creating scatter chart data: {e}")
        return create_error_response("Failed to create scatter chart")


async def get_entity_data(entity: str, group_by: Optional[str], calc: EnhancedMetricsCalculator, 
                         filters: Optional[Dict[str, Any]] = None, chart_type: str = "bar") -> ChartData:
    """Get data for an entity using Universal Chart Processor - handles any entity/grouping combination"""
    try:
        # Use Universal Chart Processor for all requests
        logger.info(f"Processing chart request via Universal Engine: entity={entity}, group_by={group_by}, chart_type={chart_type}")
        
        result = await process_chart_via_universal_engine(
            entity=entity,
            operation="count",  # Default operation for charts
            group_by=group_by,
            filters=filters,
            calc=calc,
            chart_type=chart_type
        )
        
        # Add round_chart_values for consistency only for non-table charts
        if chart_type == "table":
            return result
        else:
            return round_chart_values(result)
        
    except Exception as e:
        logger.error(f"Universal chart processing error for {entity}: {e}")
        return create_error_response(f"Failed to process {entity} chart data")


async def process_chart_data(report_json: ReportJson, client: HuntflowLocalClient) -> ReportJson:
    """
    Process report JSON and fetch actual data for charts.
    
    Args:
        report_json: The report JSON from OpenAI
        client: HuntflowLocalClient instance
        
    Returns:
        Updated report JSON with real_data populated
    """
    try:
        # Validate input
        report_json = validate_report_json(report_json)
        
        # Initialize metrics calculator
        metrics_calc = EnhancedMetricsCalculator(client, None)
        
        # Process chart data if present
        if "chart" in report_json:
            chart = report_json["chart"]
            chart_type = chart.get("type", "bar")
            
            # Extract filters from y_axis (main data source)
            y_axis_config = chart.get("y_axis", {})
            filters = y_axis_config.get("filters", {})
            
            try:
                # Handle different chart types
                if chart_type == "scatter":
                    x_axis_config = chart.get("x_axis", {})
                    y_axis_config = chart.get("y_axis", {})
                    
                    real_data = await get_scatter_chart_data(x_axis_config, y_axis_config, metrics_calc, filters)
                elif chart_type == "table":
                    # Handle table charts - tables don't need x/y axis, just entity and filters
                    # Use y_axis as the primary data source for consistency
                    entity = y_axis_config.get(ENTITY_KEY, "")
                    group_by = normalize_group_by(y_axis_config.get("group_by"))
                    
                    real_data = await get_entity_data(entity, group_by, metrics_calc, filters, chart_type="table")
                else:
                    # Handle regular bar/line charts
                    entity = y_axis_config.get(ENTITY_KEY, "")
                    group_by = normalize_group_by(y_axis_config.get("group_by"))
                    
                    real_data = await get_entity_data(entity, group_by, metrics_calc, filters, chart_type=chart_type)
                
                # Add title from chart label or description if not set
                if not real_data.get("title"):
                    real_data["title"] = chart.get("label", chart.get("graph_description", "Chart"))
                
                # Update the report with real data
                report_json["chart"]["real_data"] = real_data
                
            except ChartProcessingError as e:
                logger.error(f"Chart processing error for {chart_type} chart: {e}")
                report_json["chart"]["real_data"] = create_error_response(str(e))
        
        # Process main metric if present
        if "main_metric" in report_json:
            await process_main_metric(report_json, metrics_calc)
        
        # Process secondary metrics if present
        if "secondary_metrics" in report_json:
            await process_secondary_metrics(report_json, metrics_calc)
        
        return report_json
        
    except ChartProcessingError as e:
        logger.error(f"Validation error: {e}")
        # Return original with error data
        if "chart" in report_json:
            report_json["chart"]["real_data"] = create_error_response("Invalid input")
        return report_json
    except (KeyError, TypeError, ValueError) as e:
        logger.error(f"Data structure error in process_chart_data: {e}", exc_info=True)
        if "chart" in report_json:
            report_json["chart"]["real_data"] = create_error_response("Invalid data structure")
        return report_json


async def resolve_entity_name_by_id(entity_type: str, entity_id: str, calc: EnhancedMetricsCalculator) -> Optional[str]:
    """Resolve entity name by ID from database."""
    try:
        if entity_type == "recruiters":
            recruiters = await calc.recruiters_all()
            for recruiter in recruiters:
                if str(recruiter.get('id')) == str(entity_id):
                    return recruiter.get('name')
        elif entity_type == "sources":
            sources = await calc.sources_all()
            for source in sources:
                if str(source.get('id')) == str(entity_id):
                    return source.get('name')
        elif entity_type == "vacancies":
            vacancies = await calc.vacancies_all()
            for vacancy in vacancies:
                if str(vacancy.get('id')) == str(entity_id):
                    return vacancy.get('position', vacancy.get('name'))
        elif entity_type == "stages" or entity_type == "statuses":
            statuses = await calc.statuses_all()
            for status in statuses:
                if str(status.get('id')) == str(entity_id):
                    return status.get('name')
    except Exception as e:
        logger.warning(f"Error resolving {entity_type} name for ID {entity_id}: {e}")
    
    return None


def enhance_metric_label_with_filter_names(original_label: str, filters: Dict[str, Any], resolved_names: Dict[str, str]) -> str:
    """Enhance metric label by appending resolved entity names from filters."""
    if not filters or not resolved_names:
        return original_label
    
    # Append resolved names to the label
    name_parts = []
    for filter_key, entity_name in resolved_names.items():
        if entity_name:
            name_parts.append(entity_name)
    
    if name_parts:
        return f"{original_label} ({', '.join(name_parts)})"
    
    return original_label


async def process_main_metric(report_json: ReportJson, calc: EnhancedMetricsCalculator) -> None:
    """Process main metric value updates with enhanced labels for ID filters."""
    try:
        metric = report_json["main_metric"]["value"]
        entity = metric.get(ENTITY_KEY, "")
        operation = metric.get(OPERATION_KEY, COUNT_OPERATION)
        filters = metric.get("filters", {})
        metrics_group_by = report_json.get("metrics_group_by")  # NEW: Extract metrics grouping
        
        real_value = await calculate_main_metric_value(entity, operation, calc, filters, metrics_group_by)
        
        # Always store as grouped metrics (metrics_group_by is now required)
        if isinstance(real_value, dict):
            # Grouped metrics: store breakdown and total
            report_json["main_metric"]["grouped_breakdown"] = real_value
            report_json["main_metric"]["total_value"] = sum(real_value.values())
            report_json["main_metric"]["real_value"] = sum(real_value.values())
        else:
            # Handle edge case where no grouped data returned - store as single total
            if isinstance(real_value, float):
                real_value = round(real_value, 1)
            report_json["main_metric"]["real_value"] = real_value
            report_json["main_metric"]["total_value"] = real_value
        
        # Enhance label with resolved entity names from filters
        if filters:
            resolved_names = {}
            for filter_key, filter_value in filters.items():
                if filter_key != "period" and isinstance(filter_value, str) and filter_value.isdigit():
                    # This looks like an ID filter
                    entity_name = await resolve_entity_name_by_id(filter_key, filter_value, calc)
                    if entity_name:
                        resolved_names[filter_key] = entity_name
            
            if resolved_names:
                original_label = report_json["main_metric"].get("label", "")
                enhanced_label = enhance_metric_label_with_filter_names(original_label, filters, resolved_names)
                report_json["main_metric"]["enhanced_label"] = enhanced_label
        
    except ChartProcessingError as e:
        logger.error(f"Metric processing error for entity '{entity}': {e}")
        report_json["main_metric"]["real_value"] = 0
    except (KeyError, TypeError, ValueError) as e:
        logger.error(f"Data access error in process_main_metric for entity '{entity}': {e}")
        report_json["main_metric"]["real_value"] = 0


async def process_secondary_metrics(report_json: ReportJson, calc: EnhancedMetricsCalculator) -> None:
    """Process secondary metrics value updates with enhanced labels for ID filters."""
    if not isinstance(report_json.get("secondary_metrics"), list):
        return
    
    metrics_group_by = report_json.get("metrics_group_by")  # NEW: Use same grouping as main metric
    
    for i, metric in enumerate(report_json["secondary_metrics"]):
        try:
            value_config = metric.get("value", {})
            entity = value_config.get(ENTITY_KEY, "")
            operation = value_config.get(OPERATION_KEY, COUNT_OPERATION)
            filters = value_config.get("filters", {})
            
            real_value = await calculate_main_metric_value(entity, operation, calc, filters, metrics_group_by)
            
            # Always store as grouped metrics (same logic as main metric)
            if isinstance(real_value, dict):
                # Grouped metrics: store breakdown and total
                report_json["secondary_metrics"][i]["grouped_breakdown"] = real_value
                report_json["secondary_metrics"][i]["total_value"] = sum(real_value.values())
                report_json["secondary_metrics"][i]["real_value"] = sum(real_value.values())
            else:
                # Handle edge case where no grouped data returned - store as single total
                if isinstance(real_value, float):
                    real_value = round(real_value, 1)
                report_json["secondary_metrics"][i]["real_value"] = real_value
                report_json["secondary_metrics"][i]["total_value"] = real_value
            
            # Enhance label with resolved entity names from filters
            if filters:
                resolved_names = {}
                for filter_key, filter_value in filters.items():
                    if filter_key != "period" and isinstance(filter_value, str) and filter_value.isdigit():
                        # This looks like an ID filter
                        entity_name = await resolve_entity_name_by_id(filter_key, filter_value, calc)
                        if entity_name:
                            resolved_names[filter_key] = entity_name
                
                if resolved_names:
                    original_label = metric.get("label", "")
                    enhanced_label = enhance_metric_label_with_filter_names(original_label, filters, resolved_names)
                    report_json["secondary_metrics"][i]["enhanced_label"] = enhanced_label
            
        except ChartProcessingError as e:
            logger.error(f"Secondary metric processing error for index {i}, entity '{entity}': {e}")
            report_json["secondary_metrics"][i]["real_value"] = 0
        except (KeyError, TypeError, ValueError) as e:
            logger.error(f"Data access error in process_secondary_metrics for index {i}: {e}")
            report_json["secondary_metrics"][i]["real_value"] = 0


async def calculate_main_metric_value(
    entity: str, 
    operation: str, 
    calc: EnhancedMetricsCalculator, 
    filters: Optional[Dict[str, Any]] = None,
    metrics_group_by: Optional[str] = None
) -> Union[int, float, Dict[str, Any]]:
    """Calculate main metric value - grouped or aggregated based on metrics_group_by."""
    try:
        # Use Universal Chart Processor with optional grouping
        result = await process_chart_via_universal_engine(
            entity=entity,
            operation=operation,
            group_by=metrics_group_by,  # Use report-level grouping
            filters=filters,
            calc=calc
        )
        
        if metrics_group_by:
            # Return grouped data: {"Nastya": 5, "Igor": 3, "Maria": 8}
            labels = result.get("labels", [])
            values = result.get("values", [])
            if labels and values and len(labels) == len(values):
                return dict(zip(labels, values))
            else:
                return {}
        else:
            # Return single aggregated value: 16
            if isinstance(result.get("values"), list) and result["values"]:
                if operation == COUNT_OPERATION:
                    return sum(result["values"])
                elif operation == AVG_OPERATION:
                    # For average, return the average of all values
                    values = result["values"]
                    return sum(values) / len(values) if values else 0
                elif operation == SUM_OPERATION:
                    return sum(result["values"])
            return 0
        
    except Exception as e:
        logger.error(f"Main metric calculation error for entity '{entity}': {e}")
        return {} if metrics_group_by else 0


# Test function
async def test_processing():
    """Test function to verify chart data processing."""
    client = HuntflowLocalClient()
    
    # Configure logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test report for recruiters
    test_report: ReportJson = {
        "report_title": "Top Recruiter by Hirings",
        "main_metric": {
            "label": "Total Recruiters",
            "value": {
                "operation": "count",
                "entity": "recruiters"
            }
        },
        "chart": {
            "graph_description": "Recruiters ranked by their number of successful hirings",
            "chart_type": "bar",
            "x_axis_name": "Recruiter",
            "y_axis_name": "Number of Hirings",
            "x_axis": {
                "operation": "field",
                "field": "name"
            },
            "y_axis": {
                "operation": "count",
                "entity": "recruiters",
                "group_by": {
                    "field": "hirings"
                }
            }
        }
    }
    
    import json
    processed = await process_chart_data(test_report, client)
    print(json.dumps(processed, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(test_processing())