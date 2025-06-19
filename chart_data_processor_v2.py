"""
Process chart data from report JSON for visualization - Version 2
Improved with better error handling, validation, and maintainability
"""

import logging
from typing import Dict, Any, List, Optional, TypedDict, Union, Callable
from collections import Counter
from huntflow_local_client import HuntflowLocalClient
from metrics_calculator import MetricsCalculator
import asyncio

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
class ChartData(TypedDict):
    labels: List[str]
    values: List[Union[int, float]]
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


# Input validation
def validate_report_json(report_json: Any) -> ReportJson:
    """Validate the structure of the report JSON."""
    if not isinstance(report_json, dict):
        raise ChartProcessingError("Report JSON must be a dictionary")
    
    # Validate chart section if present
    if "chart" in report_json:
        chart = report_json["chart"]
        if not isinstance(chart, dict):
            raise ChartProcessingError("Chart must be a dictionary")
        
        if "y_axis" in chart:
            y_axis = chart["y_axis"]
            if not isinstance(y_axis, dict):
                raise ChartProcessingError("Y-axis must be a dictionary")
            
            if ENTITY_KEY not in y_axis:
                raise ChartProcessingError("Y-axis must have an entity")
    
    # Validate main_metric section if present
    if "main_metric" in report_json:
        main_metric = report_json["main_metric"]
        if not isinstance(main_metric, dict):
            raise ChartProcessingError("Main metric must be a dictionary")
        
        if "value" in main_metric:
            value = main_metric["value"]
            if not isinstance(value, dict):
                raise ChartProcessingError("Main metric value must be a dictionary")
            
            if ENTITY_KEY not in value:
                raise ChartProcessingError("Main metric value must have an entity")
    
    return report_json


# Helper function to safely get method
async def safe_method_call(calc: MetricsCalculator, method_name: str) -> Any:
    """Safely call a method on the calculator."""
    if not hasattr(calc, method_name):
        raise ChartProcessingError(f"Method {method_name} not found in MetricsCalculator")
    
    method = getattr(calc, method_name)
    if not callable(method):
        raise ChartProcessingError(f"{method_name} is not a callable method")
    
    return await method()


# Named handler functions (replacing lambdas)
async def handle_count_entities(calc: MetricsCalculator, method_name: str, label: str) -> ChartData:
    """Handler for counting entities."""
    try:
        data = await safe_method_call(calc, method_name)
        return {
            "labels": [label],
            "values": [len(data)],
            "title": label
        }
    except Exception as e:
        logger.error(f"Error in handle_count_entities for {method_name}: {e}")
        raise ChartProcessingError(f"Failed to count {label}")


async def handle_dict_to_chart(calc: MetricsCalculator, method_name: str) -> ChartData:
    """Handler for converting dict results to chart data."""
    try:
        data = await safe_method_call(calc, method_name)
        if not isinstance(data, dict):
            raise ChartProcessingError(f"Expected dict from {method_name}, got {type(data)}")
        
        return {
            "labels": list(data.keys()),
            "values": list(data.values()),
            "title": ""
        }
    except Exception as e:
        logger.error(f"Error in handle_dict_to_chart for {method_name}: {e}")
        raise ChartProcessingError(f"Failed to process {method_name}")


async def handle_list_entities(calc: MetricsCalculator, method_name: str, 
                              name_field: str = "name", 
                              id_field: str = "id",
                              entity_type: str = "Item") -> ChartData:
    """Handler for processing list of entities."""
    try:
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
    except Exception as e:
        logger.error(f"Error in handle_list_entities for {method_name}: {e}")
        raise ChartProcessingError(f"Failed to process {entity_type} list")


async def handle_conversion_summary(calc: MetricsCalculator, top_n: int = 10) -> ChartData:
    """Handler for vacancy conversion summary."""
    try:
        summary_data = await safe_method_call(calc, "vacancy_conversion_summary")
        if not isinstance(summary_data, dict) or "best_performing_vacancies" not in summary_data:
            raise ChartProcessingError("Invalid conversion summary data")
        
        top_vacancies = summary_data["best_performing_vacancies"][:top_n]
        return {
            "labels": [v["vacancy_title"] for v in top_vacancies],
            "values": [v["conversion_rate"] for v in top_vacancies],
            "title": ""
        }
    except Exception as e:
        logger.error(f"Error in handle_conversion_summary: {e}")
        raise ChartProcessingError("Failed to process conversion summary")


async def handle_status_groups(calc: MetricsCalculator) -> ChartData:
    """Handler for status groups."""
    try:
        groups_data = await safe_method_call(calc, "status_groups")
        if not isinstance(groups_data, list):
            raise ChartProcessingError("Invalid status groups data")
        
        return {
            "labels": [group["name"] for group in groups_data],
            "values": [group["status_count"] for group in groups_data],
            "title": ""
        }
    except Exception as e:
        logger.error(f"Error in handle_status_groups: {e}")
        raise ChartProcessingError("Failed to process status groups")


async def handle_actions_by_type(calc: MetricsCalculator) -> ChartData:
    """Handler for actions grouped by type."""
    try:
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
    except Exception as e:
        logger.error(f"Error in handle_actions_by_type: {e}")
        raise ChartProcessingError("Failed to process actions by type")


async def handle_moves_by_type(calc: MetricsCalculator) -> ChartData:
    """Handler for moves grouped by type."""
    try:
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
    except Exception as e:
        logger.error(f"Error in handle_moves_by_type: {e}")
        raise ChartProcessingError("Failed to process moves by type")


async def handle_total_moves(calc: MetricsCalculator) -> ChartData:
    """Handler for total moves count."""
    try:
        moves_data = await safe_method_call(calc, "moves_by_recruiter")
        if not isinstance(moves_data, dict):
            raise ChartProcessingError("Invalid moves data")
        
        total_moves = sum(moves_data.values())
        return {
            "labels": ["Total Moves"],
            "values": [total_moves],
            "title": ""
        }
    except Exception as e:
        logger.error(f"Error in handle_total_moves: {e}")
        raise ChartProcessingError("Failed to process total moves")


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


# Entity configuration using named handlers
ENTITY_HANDLERS: Dict[str, Dict[str, Any]] = {
    # Simple count entities
    "applicants_all": {
        HANDLER_KEY: create_count_handler("applicants_all", "All Applicants")
    },
    "vacancies_all": {
        HANDLER_KEY: create_count_handler("vacancies_all", "All Vacancies")
    },
    "vacancies_open": {
        HANDLER_KEY: create_count_handler("vacancies_open", "Open Vacancies")
    },
    "vacancies_closed": {
        HANDLER_KEY: create_count_handler("vacancies_closed", "Closed Vacancies")
    },
    "vacancies_last_6_months": {
        HANDLER_KEY: create_count_handler("vacancies_last_6_months", "Vacancies Last 6 Months")
    },
    "vacancies_last_year": {
        HANDLER_KEY: create_count_handler("vacancies_last_year", "Vacancies Last Year")
    },
    "hired_applicants": {
        HANDLER_KEY: create_count_handler("applicants_hired", "Hired Applicants")
    },
    "successful_closures": {
        HANDLER_KEY: create_count_handler("vacancies_closed", "Successful Closures")
    },
    
    # Dict-based entities
    "applicants_by_status": {
        HANDLER_KEY: create_dict_handler("applicants_by_status")
    },
    "applicants_by_source": {
        HANDLER_KEY: create_dict_handler("applicants_by_source")
    },
    "applicants_by_recruiter": {
        HANDLER_KEY: create_dict_handler("applicants_by_recruiter")
    },
    "applicants_by_hiring_manager": {
        HANDLER_KEY: create_dict_handler("applicants_by_hiring_manager")
    },
    "actions_by_recruiter": {
        HANDLER_KEY: create_dict_handler("actions_by_recruiter")
    },
    "recruiter_add": {
        HANDLER_KEY: create_dict_handler("recruiter_add")
    },
    "recruiter_comment": {
        HANDLER_KEY: create_dict_handler("recruiter_comment")
    },
    "recruiter_mail": {
        HANDLER_KEY: create_dict_handler("recruiter_mail")
    },
    "recruiter_agreement": {
        HANDLER_KEY: create_dict_handler("recruiter_agreement")
    },
    "moves_by_recruiter": {
        HANDLER_KEY: create_dict_handler("moves_by_recruiter")
    },
    "added_applicants_by_recruiter": {
        HANDLER_KEY: create_dict_handler("applicants_added_by_recruiter")
    },
    "rejections_by_recruiter": {
        HANDLER_KEY: create_dict_handler("rejections_by_recruiter")
    },
    "rejections_by_stage": {
        HANDLER_KEY: create_dict_handler("rejections_by_stage")
    },
    "rejections_by_reason": {
        HANDLER_KEY: create_dict_handler("rejections_by_reason")
    },
    "vacancy_conversion_rates": {
        HANDLER_KEY: create_dict_handler("vacancy_conversion_rates")
    },
    "vacancy_conversion_by_status": {
        HANDLER_KEY: create_dict_handler("vacancy_conversion_by_status")
    },
    
    # List entities
    "divisions_all": {
        HANDLER_KEY: create_list_handler("divisions_all", "Division")
    },
    "sources_all": {
        HANDLER_KEY: create_list_handler("sources_all", "Source")
    },
    "hiring_managers": {
        HANDLER_KEY: create_list_handler("hiring_managers", "Manager")
    },
    "stages": {
        HANDLER_KEY: create_list_handler("stages", "Stage")
    },
    
    # Special handlers
    "vacancy_conversion_summary": {
        HANDLER_KEY: handle_conversion_summary
    },
    "status_groups": {
        HANDLER_KEY: handle_status_groups
    },
    
    # Proxy entities
    "recruiter_performance": {
        HANDLER_KEY: create_dict_handler("actions_by_recruiter")
    },
    "time_in_status": {
        HANDLER_KEY: create_dict_handler("applicants_by_status")
    },
    "applicant_activity_trends": {
        HANDLER_KEY: create_dict_handler("applicants_by_recruiter")
    },
    
    # Entities with groupings
    "applicants": {
        DEFAULT_KEY: create_count_handler("applicants_all", "Total Applicants"),
        GROUPINGS_KEY: {
            "source": create_dict_handler("applicants_by_source"),
            "source_id": create_dict_handler("applicants_by_source"),
            "sources": create_dict_handler("applicants_by_source"),
            "stage": create_dict_handler("applicants_by_status"),
            "stages": create_dict_handler("applicants_by_status"),
            "status": create_dict_handler("applicants_by_status"),
            "status_id": create_dict_handler("applicants_by_status"),
            "recruiter": create_dict_handler("applicants_by_recruiter"),
            "recruiters": create_dict_handler("applicants_by_recruiter"),
            "hiring_manager": create_dict_handler("applicants_by_hiring_manager"),
            "hiring_managers": create_dict_handler("applicants_by_hiring_manager"),
            "division": create_dict_handler("applicants_by_division"),
            "divisions": create_dict_handler("applicants_by_division"),
            "month": create_dict_handler("applicants_by_month"),
            "monthly": create_dict_handler("applicants_by_month"),
            "time": create_dict_handler("applicants_by_month"),
        }
    },
    
    "vacancies": {
        DEFAULT_KEY: create_count_handler("vacancies_all", "Total Vacancies"),
        GROUPINGS_KEY: {
            "state": create_dict_handler("vacancies_by_state"),
            "recruiter": create_dict_handler("vacancies_by_recruiter"),
            "recruiters": create_dict_handler("vacancies_by_recruiter"),
            "hiring_manager": create_dict_handler("vacancies_by_hiring_manager"),
            "hiring_managers": create_dict_handler("vacancies_by_hiring_manager"),
            "division": create_dict_handler("vacancies_by_division"),
            "divisions": create_dict_handler("vacancies_by_division"),
            "stage": create_dict_handler("vacancies_by_stage"),
            "stages": create_dict_handler("vacancies_by_stage"),
            "priority": create_dict_handler("vacancies_by_priority"),
            "priorities": create_dict_handler("vacancies_by_priority"),
            "month": create_dict_handler("vacancies_by_month"),
            "monthly": create_dict_handler("vacancies_by_month"),
            "time": create_dict_handler("vacancies_by_month"),
        }
    },
    
    "recruiters": {
        DEFAULT_KEY: create_count_handler("recruiters_all", "Total Recruiters"),
        GROUPINGS_KEY: {
            "hirings": create_dict_handler("recruiters_by_hirings"),
            "vacancy": create_dict_handler("recruiters_by_vacancies"),
            "vacancies": create_dict_handler("recruiters_by_vacancies"),
            "applicant": create_dict_handler("recruiters_by_applicants"),
            "applicants": create_dict_handler("recruiters_by_applicants"),
            "division": create_dict_handler("recruiters_by_divisions"),
            "divisions": create_dict_handler("recruiters_by_divisions"),
        }
    },
    
    "vacancy_statuses": {
        DEFAULT_KEY: create_count_handler("statuses_all", "Total Vacancy Statuses"),
        GROUPINGS_KEY: {
            "type": create_dict_handler("statuses_by_type"),
            "id": create_dict_handler("statuses_list"),
            "name": create_dict_handler("statuses_list"),
        }
    },
    
    "active_candidates": {
        DEFAULT_KEY: create_count_handler("applicants_all", "Active Candidates"),
        GROUPINGS_KEY: {
            "status_id": create_dict_handler("applicants_by_status"),
        }
    },
    
    "hires": {
        DEFAULT_KEY: create_count_handler("hires", "Hired Candidates"),
        GROUPINGS_KEY: {
            "recruiter": create_dict_handler("recruiters_by_hirings"),
            "recruiters": create_dict_handler("recruiters_by_hirings"),
            "source": create_dict_handler("hires_by_source"),
            "sources": create_dict_handler("hires_by_source"),
            "stage": create_dict_handler("hires_by_stage"),
            "stages": create_dict_handler("hires_by_stage"),
            "division": create_dict_handler("hires_by_division"),
            "divisions": create_dict_handler("hires_by_division"),
        }
    },
    
    "actions": {
        DEFAULT_KEY: create_count_handler("actions", "Total Actions"),
        GROUPINGS_KEY: {
            "recruiter": create_dict_handler("actions_by_recruiter"),
            "recruiters": create_dict_handler("actions_by_recruiter"),
            "type": handle_actions_by_type,
            "action_type": handle_actions_by_type,
            "month": create_dict_handler("actions_by_month"),
            "monthly": create_dict_handler("actions_by_month"),
            "time": create_dict_handler("actions_by_month"),
        }
    },
    
    "sources": {
        HANDLER_KEY: create_list_handler("sources", "Source")
    },
    
    "divisions": {
        HANDLER_KEY: create_list_handler("divisions", "Division")
    },
    
    "moves": {
        DEFAULT_KEY: handle_total_moves,
        GROUPINGS_KEY: {
            "recruiter": create_dict_handler("moves_by_recruiter"),
            "recruiters": create_dict_handler("moves_by_recruiter"),
            "type": handle_moves_by_type,
            "detailed": handle_moves_by_type,
        }
    },
    
    "rejections": {
        DEFAULT_KEY: create_dict_handler("rejections"),
        GROUPINGS_KEY: {
            "recruiter": create_dict_handler("rejections_by_recruiter"),
            "recruiters": create_dict_handler("rejections_by_recruiter"),
            "reason": create_dict_handler("rejections_by_reason"),
            "reasons": create_dict_handler("rejections_by_reason"),
            "stage": create_dict_handler("rejections_by_stage"),
            "stages": create_dict_handler("rejections_by_stage"),
        }
    },
}

# Legacy entity mappings
LEGACY_MAPPINGS = {
    "open_vacancies": "vacancies_open",
    "closed_vacancies": "vacancies_closed",
    "all_applicants": "applicants_all",
}

# Method operation mappings for consolidated metric calculation
METRIC_METHOD_CONFIG = {
    # Count operations - return len(data)
    "count_methods": {
        "applicants_all", "vacancies_all", "vacancies_open", "vacancies_closed",
        "vacancies_last_6_months", "vacancies_last_year", "applicants_hired",
        "divisions_all", "sources_all", "hiring_managers", "stages",
        "recruiters_all", "hires", "actions", "applicants", "vacancies",
        "recruiters", "sources", "divisions"
    },
    
    # Dict operations - return dict with values to sum/average
    "dict_methods": {
        "applicants_by_status", "applicants_by_source", "applicants_by_recruiter",
        "applicants_by_hiring_manager", "actions_by_recruiter", "moves_by_recruiter",
        "applicants_added_by_recruiter", "rejections_by_stage", "recruiter_add",
        "recruiter_comment", "recruiter_mail", "recruiter_agreement", "rejections"
    },
    
    # Special cases
    "special_cases": {
        "vacancy_conversion_summary": {
            AVG_OPERATION: lambda data: data.get("overall_conversion_rate", DEFAULT_CONVERSION_RATE)
        }
    }
}


def normalize_group_by(group_by_obj: Optional[Union[GroupByConfig, str]]) -> Optional[str]:
    """Normalize group_by from various formats to a simple string."""
    if isinstance(group_by_obj, dict):
        return group_by_obj.get(FIELD_KEY)
    elif isinstance(group_by_obj, str):
        return group_by_obj
    return None


async def get_entity_data(entity: str, group_by: Optional[str], calc: MetricsCalculator) -> ChartData:
    """Get data for an entity, handling groupings if specified."""
    try:
        # Handle legacy mappings
        if entity in LEGACY_MAPPINGS:
            entity = LEGACY_MAPPINGS[entity]
        
        # Check if entity exists in handlers
        if entity not in ENTITY_HANDLERS:
            logger.warning(f"Unknown entity: {entity}")
            return create_no_data_response(entity)
        
        handler_config = ENTITY_HANDLERS[entity]
        
        # If it's a simple handler (no groupings)
        if HANDLER_KEY in handler_config:
            return await handler_config[HANDLER_KEY](calc)
        
        # If it has groupings
        if GROUPINGS_KEY in handler_config and group_by and group_by in handler_config[GROUPINGS_KEY]:
            return await handler_config[GROUPINGS_KEY][group_by](calc)
        
        # Use default handler if available
        if DEFAULT_KEY in handler_config:
            return await handler_config[DEFAULT_KEY](calc)
        
        # No handler found
        return create_no_data_response(entity)
        
    except ChartProcessingError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_entity_data for {entity}: {e}")
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
            entity = chart.get("y_axis", {}).get(ENTITY_KEY, "")
            group_by = normalize_group_by(chart.get("y_axis", {}).get("group_by"))
            
            try:
                # Get entity data using configuration
                real_data = await get_entity_data(entity, group_by, metrics_calc)
                
                # Add title from chart description if not set
                if not real_data.get("title"):
                    real_data["title"] = chart.get("graph_description", "Chart")
                
                # Update the report with real data
                report_json["chart"]["real_data"] = real_data
                
            except ChartProcessingError as e:
                logger.error(f"Chart processing error for entity '{entity}': {e}")
                report_json["chart"]["real_data"] = create_error_response(str(e))
            except Exception as e:
                logger.error(f"Unexpected error processing chart for entity '{entity}': {e}", exc_info=True)
                report_json["chart"]["real_data"] = create_error_response()
        
        # Process main metric if present
        if "main_metric" in report_json:
            await process_main_metric(report_json, metrics_calc)
        
        return report_json
        
    except ChartProcessingError as e:
        logger.error(f"Validation error: {e}")
        # Return original with error data
        if "chart" in report_json:
            report_json["chart"]["real_data"] = create_error_response("Invalid input")
        return report_json
    except Exception as e:
        logger.error(f"Unexpected error in process_chart_data: {e}", exc_info=True)
        if "chart" in report_json:
            report_json["chart"]["real_data"] = create_error_response()
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
        report_json["main_metric"]["real_value"] = real_value
        
    except ChartProcessingError as e:
        logger.error(f"Metric processing error for entity '{entity}': {e}")
        report_json["main_metric"]["real_value"] = 0
    except Exception as e:
        logger.error(f"Unexpected error in process_main_metric for entity '{entity}': {e}", exc_info=True)
        report_json["main_metric"]["real_value"] = 0


async def calculate_main_metric_value(entity: str, operation: str, calc: MetricsCalculator) -> Union[int, float]:
    """Calculate the real value for a main metric using consolidated logic."""
    try:
        # Check special cases first
        if entity in METRIC_METHOD_CONFIG["special_cases"]:
            special_config = METRIC_METHOD_CONFIG["special_cases"][entity]
            if operation in special_config:
                handler = special_config[operation]
                if callable(handler):
                    data = await safe_method_call(calc, entity.replace("_summary", "_summary"))
                    return handler(data)
        
        # Determine method name from entity
        method_name = get_method_name_for_entity(entity)
        
        # Get data
        data = await safe_method_call(calc, method_name)
        
        # Process based on operation and data type
        if isinstance(data, list):
            if operation == COUNT_OPERATION:
                return len(data)
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
    except Exception as e:
        logger.error(f"Error calculating metric for {entity} with {operation}: {e}")
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