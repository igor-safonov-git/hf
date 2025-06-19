"""
Process chart data from report JSON for visualization - Version 2
Improved with better error handling, validation, and maintainability
"""

import logging
from typing import Dict, Any, List, Optional, TypedDict, Union, Callable
from collections import Counter
from functools import wraps
from huntflow_local_client import HuntflowLocalClient
from metrics_calculator import MetricsCalculator
import asyncio

# Import modular configurations
from entity_configs import get_entity_handlers, get_legacy_mappings
from entity_configs.legacy_mappings import METRIC_METHOD_CONFIG
import entity_configs.simple_entities as simple_entities
import entity_configs.grouped_entities as grouped_entities  
import entity_configs.special_handlers as special_handlers

# Configure logging
logger = logging.getLogger(__name__)

# Constants for magic strings
HANDLER_KEY = "handler"
GROUPINGS_KEY = "groupings"
DEFAULT_KEY = "default"
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

class MainMetricValue(TypedDict):
    entity: str
    operation: Optional[str]

class MainMetricConfig(TypedDict):
    value: MainMetricValue

class ReportJson(TypedDict, total=False):
    chart: ChartConfig
    main_metric: MainMetricConfig


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
    
    # Validate chart section if present
    if "chart" in report_json:
        _validate_chart_section(report_json["chart"])
    
    # Validate main_metric section if present
    if "main_metric" in report_json:
        _validate_main_metric_section(report_json["main_metric"])
    
    return report_json


def _validate_chart_section(chart: Any) -> None:
    """Validate chart section structure."""
    if not isinstance(chart, dict):
        raise ChartProcessingError("Chart must be a dictionary")
    
    # Validate y_axis (required for chart processing)
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
    
    # Validate value (required for metric processing)
    if "value" not in main_metric:
        raise ChartProcessingError("Main metric must have a value")
    
    value = main_metric["value"]
    if not isinstance(value, dict):
        raise ChartProcessingError("Main metric value must be a dictionary")
    
    # Entity is required
    if ENTITY_KEY not in value:
        raise ChartProcessingError("Main metric value must have an entity")
    
    if not isinstance(value[ENTITY_KEY], str):
        raise ChartProcessingError("Main metric entity must be a string")
    
    # Validate operation if present
    if OPERATION_KEY in value:
        operation = value[OPERATION_KEY]
        if operation is not None and not isinstance(operation, str):
            raise ChartProcessingError("Operation must be a string or null")
        
        # Check if operation is valid
        valid_operations = {COUNT_OPERATION, SUM_OPERATION, AVG_OPERATION}
        if operation and operation not in valid_operations:
            raise ChartProcessingError(f"Operation must be one of: {', '.join(valid_operations)}")
    
    # Validate optional fields
    if "label" in main_metric and not isinstance(main_metric["label"], (str, type(None))):
        raise ChartProcessingError("Main metric label must be a string or null")


# Allowed methods for security
ALLOWED_CALCULATOR_METHODS = {
    # Basic entity methods
    "applicants_all", "vacancies_all", "vacancies_open", "vacancies_closed",
    "vacancies_last_6_months", "vacancies_last_year", "applicants_hired",
    "divisions_all", "sources_all", "hiring_managers", "stages",
    "recruiters_all", "statuses_all", "hires", "actions",
    "applicants", "vacancies", "recruiters", "sources", "divisions",
    
    # Grouping methods
    "applicants_by_status", "applicants_by_source", "applicants_by_recruiter",
    "applicants_by_hiring_manager", "applicants_by_division", "applicants_by_month",
    "vacancies_by_state", "vacancies_by_recruiter", "vacancies_by_hiring_manager",
    "vacancies_by_division", "vacancies_by_stage", "vacancies_by_priority",
    "vacancies_by_month", "recruiters_by_hirings", "recruiters_by_vacancies",
    "recruiters_by_applicants", "recruiters_by_divisions", "hires_by_source",
    "hires_by_stage", "hires_by_division", "hires_by_month", "hires_by_day", "hires_by_year", 
    "actions_by_recruiter", "actions_by_month",
    "moves_by_recruiter", "moves_by_recruiter_detailed", "applicants_added_by_recruiter",
    "rejections_by_recruiter", "rejections_by_stage", "rejections_by_reason",
    "rejections", "statuses_by_type", "statuses_list",
    
    # Special methods
    "vacancy_conversion_rates", "vacancy_conversion_by_status", "vacancy_conversion_summary",
    "status_groups", "recruiter_add", "recruiter_comment", "recruiter_mail",
    "recruiter_agreement"
}


# Helper function to safely get method
async def safe_method_call(calc: MetricsCalculator, method_name: str) -> Any:
    """Safely call a method on the calculator with security checks."""
    # Security check - only allow whitelisted methods
    if method_name not in ALLOWED_CALCULATOR_METHODS:
        logger.error(f"Attempted to call unauthorized method: {method_name}")
        raise ChartProcessingError(f"Method {method_name} is not authorized")
    
    if not hasattr(calc, method_name):
        raise ChartProcessingError(f"Method {method_name} not found in MetricsCalculator")
    
    method = getattr(calc, method_name)
    if not callable(method):
        raise ChartProcessingError(f"{method_name} is not a callable method")
    
    return await method()


# Named handler functions (replacing lambdas)
@handle_chart_errors
async def handle_count_entities(calc: MetricsCalculator, method_name: str, label: str) -> ChartData:
    """Handler for counting entities."""
    data = await safe_method_call(calc, method_name)
    return {
        "labels": [label],
        "values": [len(data)],
        "title": label
    }


@handle_chart_errors
async def handle_dict_to_chart(calc: MetricsCalculator, method_name: str) -> ChartData:
    """Handler for converting dict results to chart data."""
    data = await safe_method_call(calc, method_name)
    if not isinstance(data, dict):
        raise ChartProcessingError(f"Expected dict from {method_name}, got {type(data)}")
    
    chart_data = {
        "labels": list(data.keys()),
        "values": list(data.values()),
        "title": ""
    }
    return round_chart_values(chart_data)


@handle_chart_errors
async def handle_list_entities(calc: MetricsCalculator, method_name: str, 
                              name_field: str = "name", 
                              id_field: str = "id",
                              entity_type: str = "Item") -> ChartData:
    """Handler for processing list of entities."""
    data = await safe_method_call(calc, method_name)
    if not isinstance(data, list):
        raise ChartProcessingError(f"Expected list from {method_name}, got {type(data)}")
    
    labels = [
        item.get(name_field, f"{entity_type} {item.get(id_field, UNKNOWN_LABEL)}")
        for item in data
    ]
    values = [1 for _ in data]
    
    return {
        "labels": labels,
        "values": values,
        "title": ""
    }


@handle_chart_errors
async def handle_conversion_summary(calc: MetricsCalculator, top_n: int = 10) -> ChartData:
    """Handler for vacancy conversion summary."""
    summary_data = await safe_method_call(calc, "vacancy_conversion_summary")
    if not isinstance(summary_data, dict) or "best_performing_vacancies" not in summary_data:
        raise ChartProcessingError("Invalid conversion summary data")
    
    top_vacancies = summary_data["best_performing_vacancies"][:top_n]
    chart_data = {
        "labels": [v["vacancy_title"] for v in top_vacancies],
        "values": [v["conversion_rate"] for v in top_vacancies],
        "title": ""
    }
    return round_chart_values(chart_data)


@handle_chart_errors
async def handle_status_groups(calc: MetricsCalculator) -> ChartData:
    """Handler for status groups."""
    groups_data = await safe_method_call(calc, "status_groups")
    if not isinstance(groups_data, list):
        raise ChartProcessingError("Invalid status groups data")
    
    return {
        "labels": [group["name"] for group in groups_data],
        "values": [group["status_count"] for group in groups_data],
        "title": ""
    }


@handle_chart_errors
async def handle_actions_by_type(calc: MetricsCalculator) -> ChartData:
    """Handler for actions grouped by type."""
    actions_data = await safe_method_call(calc, "actions")
    if not isinstance(actions_data, list):
        raise ChartProcessingError("Invalid actions data")
    
    # Use Counter for cleaner counting
    type_counts = Counter(action.get("type", UNKNOWN_LABEL) for action in actions_data)
    
    return {
        "labels": list(type_counts.keys()),
        "values": list(type_counts.values()),
        "title": ""
    }


@handle_chart_errors
async def handle_moves_by_type(calc: MetricsCalculator) -> ChartData:
    """Handler for moves grouped by type."""
    detailed_moves = await safe_method_call(calc, "moves_by_recruiter_detailed")
    if not isinstance(detailed_moves, dict):
        raise ChartProcessingError("Invalid moves data")
    
    # Use Counter for aggregation
    type_counts = Counter()
    for recruiter_actions in detailed_moves.values():
        if isinstance(recruiter_actions, dict):
            type_counts.update(recruiter_actions)
    
    return {
        "labels": list(type_counts.keys()),
        "values": list(type_counts.values()),
        "title": ""
    }


@handle_chart_errors
async def handle_total_moves(calc: MetricsCalculator) -> ChartData:
    """Handler for total moves count."""
    moves_data = await safe_method_call(calc, "moves_by_recruiter")
    if not isinstance(moves_data, dict):
        raise ChartProcessingError("Invalid moves data")
    
    total_moves = sum(moves_data.values())
    return {
        "labels": ["Total Moves"],
        "values": [total_moves],
        "title": ""
    }


# Handler factories to create specific handlers
def create_count_handler(method_name: str, label: str) -> Callable:
    """Factory to create count handlers."""
    async def handler(calc: MetricsCalculator) -> ChartData:
        return await handle_count_entities(calc, method_name, label)
    return handler


def create_dict_handler(method_name: str) -> Callable:
    """Factory to create dict handlers."""
    async def handler(calc: MetricsCalculator) -> ChartData:
        return await handle_dict_to_chart(calc, method_name)
    return handler


def create_list_handler(method_name: str, entity_type: str) -> Callable:
    """Factory to create list handlers."""
    async def handler(calc: MetricsCalculator) -> ChartData:
        return await handle_list_entities(calc, method_name, entity_type=entity_type)
    return handler


# Initialize modular entity configurations
def _initialize_entity_configs():
    """Initialize the modular entity configuration system."""
    # Initialize handler factories in each module
    simple_entities._init_handlers(create_count_handler, create_dict_handler, create_list_handler)
    grouped_entities._init_handlers(create_count_handler, create_dict_handler, handle_actions_by_type)
    special_handlers._init_handlers(
        handle_conversion_summary, handle_status_groups, handle_actions_by_type,
        handle_moves_by_type, handle_total_moves, create_dict_handler, create_list_handler
    )
    
    # Build configurations
    simple_entities.SIMPLE_ENTITY_CONFIGS.update(simple_entities.get_simple_entity_configs())
    grouped_entities.GROUPED_ENTITY_CONFIGS.update(grouped_entities.get_grouped_entity_configs())
    special_handlers.SPECIAL_HANDLER_CONFIGS.update(special_handlers.get_special_handler_configs())


# Entity configuration - will be populated after initialization
ENTITY_HANDLERS: Dict[str, Dict[str, Any]] = {}

# Initialize the configuration system
_initialize_entity_configs()
ENTITY_HANDLERS = get_entity_handlers()
LEGACY_MAPPINGS = get_legacy_mappings()


def normalize_group_by(group_by_obj: Optional[Union[GroupByConfig, str]]) -> Optional[str]:
    """Normalize group_by from various formats to a simple string."""
    if isinstance(group_by_obj, dict):
        return group_by_obj.get(FIELD_KEY)
    elif isinstance(group_by_obj, str):
        return group_by_obj
    return None


async def get_scatter_chart_data(x_axis_config: dict, y_axis_config: dict, calc: MetricsCalculator) -> ChartData:
    """Get data for scatter charts by correlating x_axis and y_axis data."""
    try:
        # Extract entity and group_by for both axes
        x_entity = x_axis_config.get(ENTITY_KEY, "")
        x_group_by = normalize_group_by(x_axis_config.get("group_by"))
        
        y_entity = y_axis_config.get(ENTITY_KEY, "")
        y_group_by = normalize_group_by(y_axis_config.get("group_by"))
        
        # Get data for both axes
        x_data = await get_entity_data(x_entity, x_group_by, calc)
        y_data = await get_entity_data(y_entity, y_group_by, calc)
        
        # Check if either axis returned an error
        if x_data.get("labels") == [ERROR_LABEL] or y_data.get("labels") == [ERROR_LABEL]:
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


async def get_entity_data(entity: str, group_by: Optional[str], calc: MetricsCalculator) -> ChartData:
    """Get data for an entity, handling groupings if specified."""
    try:
        # Handle legacy mappings
        if entity in LEGACY_MAPPINGS:
            entity = LEGACY_MAPPINGS[entity]
        
        # Check if entity exists in handlers
        if entity not in ENTITY_HANDLERS:
            logger.warning(f"Unknown entity: {entity}")
            return create_error_response(f"Unknown entity: {entity}")
        
        handler_config = ENTITY_HANDLERS[entity]
        
        # If it's a simple handler (no groupings)
        if HANDLER_KEY in handler_config:
            return await handler_config[HANDLER_KEY](calc)
        
        # If it has groupings and group_by is specified
        if group_by:
            if GROUPINGS_KEY in handler_config and group_by in handler_config[GROUPINGS_KEY]:
                return await handler_config[GROUPINGS_KEY][group_by](calc)
            else:
                # Invalid grouping field
                logger.warning(f"Invalid grouping '{group_by}' for entity '{entity}'")
                return create_error_response(f"Invalid grouping '{group_by}' for {entity}")
        
        # Use default handler if available
        if DEFAULT_KEY in handler_config:
            return await handler_config[DEFAULT_KEY](calc)
        
        # No handler found
        return create_error_response(f"No handler available for {entity}")
        
    except ChartProcessingError:
        raise
    except (AttributeError, KeyError, TypeError) as e:
        logger.error(f"Configuration error in get_entity_data for {entity}: {e}")
        raise ChartProcessingError(f"Failed to get data for {entity}")


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
        metrics_calc = MetricsCalculator(client)
        
        # Process chart data if present
        if "chart" in report_json:
            chart = report_json["chart"]
            chart_type = chart.get("type", "bar")
            
            try:
                # Handle scatter charts differently
                if chart_type == "scatter":
                    x_axis_config = chart.get("x_axis", {})
                    y_axis_config = chart.get("y_axis", {})
                    
                    real_data = await get_scatter_chart_data(x_axis_config, y_axis_config, metrics_calc)
                else:
                    # Handle regular bar/line charts
                    entity = chart.get("y_axis", {}).get(ENTITY_KEY, "")
                    group_by = normalize_group_by(chart.get("y_axis", {}).get("group_by"))
                    
                    real_data = await get_entity_data(entity, group_by, metrics_calc)
                
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


async def process_main_metric(report_json: ReportJson, calc: MetricsCalculator) -> None:
    """Process main metric value updates."""
    try:
        metric = report_json["main_metric"]["value"]
        entity = metric.get(ENTITY_KEY, "")
        operation = metric.get(OPERATION_KEY, COUNT_OPERATION)
        
        # Handle legacy mappings
        if entity in LEGACY_MAPPINGS:
            entity = LEGACY_MAPPINGS[entity]
        
        real_value = await calculate_main_metric_value(entity, operation, calc)
        # Round to 1 decimal place if float, keep as int if already int
        if isinstance(real_value, float):
            real_value = round(real_value, 1)
        report_json["main_metric"]["real_value"] = real_value
        
    except ChartProcessingError as e:
        logger.error(f"Metric processing error for entity '{entity}': {e}")
        report_json["main_metric"]["real_value"] = 0
    except (KeyError, TypeError, ValueError) as e:
        logger.error(f"Data access error in process_main_metric for entity '{entity}': {e}")
        report_json["main_metric"]["real_value"] = 0


async def process_secondary_metrics(report_json: ReportJson, calc: MetricsCalculator) -> None:
    """Process secondary metrics value updates."""
    if not isinstance(report_json.get("secondary_metrics"), list):
        return
    
    for i, metric in enumerate(report_json["secondary_metrics"]):
        try:
            entity = metric.get("value", {}).get(ENTITY_KEY, "")
            operation = metric.get("value", {}).get(OPERATION_KEY, COUNT_OPERATION)
            
            # Handle legacy mappings
            if entity in LEGACY_MAPPINGS:
                entity = LEGACY_MAPPINGS[entity]
            
            real_value = await calculate_main_metric_value(entity, operation, calc)
            # Round to 1 decimal place if float, keep as int if already int
            if isinstance(real_value, float):
                real_value = round(real_value, 1)
            report_json["secondary_metrics"][i]["real_value"] = real_value
            
        except ChartProcessingError as e:
            logger.error(f"Secondary metric processing error for index {i}, entity '{entity}': {e}")
            report_json["secondary_metrics"][i]["real_value"] = 0
        except (KeyError, TypeError, ValueError) as e:
            logger.error(f"Data access error in process_secondary_metrics for index {i}: {e}")
            report_json["secondary_metrics"][i]["real_value"] = 0


async def calculate_main_metric_value(entity: str, operation: str, calc: MetricsCalculator) -> Union[int, float]:
    """Calculate the real value for a main metric using consolidated logic."""
    try:
        # Check special cases first
        if entity in METRIC_METHOD_CONFIG["special_cases"]:
            special_config = METRIC_METHOD_CONFIG["special_cases"][entity]
            if operation in special_config:
                handler = special_config[operation]
                if callable(handler):
                    data = await safe_method_call(calc, entity)
                    return handler(data)
        
        # Determine method name from entity
        method_name = get_method_name_for_entity(entity)
        
        # Get data
        data = await safe_method_call(calc, method_name)
        
        # Process based on operation and data type
        if isinstance(data, list):
            if operation == COUNT_OPERATION:
                return len(data)
            elif operation == AVG_OPERATION:
                # For avg operations on list data, calculate average of numeric values
                numeric_values = []
                for item in data:
                    if isinstance(item, (int, float)):
                        numeric_values.append(item)
                    elif isinstance(item, dict):
                        # Extract numeric fields that might represent time_to_hire, etc.
                        for key, value in item.items():
                            if isinstance(value, (int, float)) and any(field in key.lower() for field in ['time', 'days', 'duration', 'hours']):
                                numeric_values.append(value)
                                break
                
                if numeric_values:
                    return sum(numeric_values) / len(numeric_values)
                else:
                    logger.warning(f"No numeric values found for avg operation on {entity}")
                    return 0
            elif operation == SUM_OPERATION:
                # For sum operations on list data, sum all numeric values
                numeric_values = []
                for item in data:
                    if isinstance(item, (int, float)):
                        numeric_values.append(item)
                    elif isinstance(item, dict):
                        for value in item.values():
                            if isinstance(value, (int, float)):
                                numeric_values.append(value)
                                break
                
                return sum(numeric_values) if numeric_values else 0
            else:
                logger.warning(f"Unsupported operation {operation} for list data from {entity}")
                return 0
                
        elif isinstance(data, dict):
            if operation == SUM_OPERATION or operation == COUNT_OPERATION:
                return sum(data.values()) if data else 0
            elif operation == AVG_OPERATION:
                return sum(data.values()) / len(data) if data else 0
            else:
                logger.warning(f"Unsupported operation {operation} for dict data from {entity}")
                return 0
        
        else:
            logger.warning(f"Unexpected data type from {entity}: {type(data)}")
            return 0
            
    except ChartProcessingError:
        raise
    except (TypeError, ValueError, AttributeError) as e:
        logger.error(f"Calculation error for {entity} with {operation}: {e}")
        raise ChartProcessingError(f"Failed to calculate metric for {entity}")


def get_method_name_for_entity(entity: str) -> str:
    """Get the appropriate method name for an entity."""
    # Direct mappings
    direct_mappings = {
        "hired_applicants": "applicants_hired",
        "successful_closures": "vacancies_closed",
        "added_applicants_by_recruiter": "applicants_added_by_recruiter",
        "recruiter_performance": "actions_by_recruiter",
        "time_in_status": "applicants_by_status",
        "applicant_activity_trends": "applicants_by_recruiter",
    }
    
    if entity in direct_mappings:
        return direct_mappings[entity]
    
    # For entities that match their method names
    if entity in ENTITY_HANDLERS:
        # Check if it's a simple entity with a handler
        handler_config = ENTITY_HANDLERS[entity]
        if HANDLER_KEY in handler_config:
            # Try to extract method name from handler
            # This is a simplified approach - in production, store method names explicitly
            return entity
    
    # Default case - use entity name as method name
    return entity


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