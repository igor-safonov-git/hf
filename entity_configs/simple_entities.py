"""
Simple entity configurations - count, dict, and list entities
"""

from typing import Dict, Any

# Import will be handled by parent module
HANDLER_KEY = "handler"

# These will be set by the main module after importing handler factories
create_count_handler = None
create_dict_handler = None  
create_list_handler = None

def _init_handlers(count_factory, dict_factory, list_factory):
    """Initialize handler factories - called by main module."""
    global create_count_handler, create_dict_handler, create_list_handler
    create_count_handler = count_factory
    create_dict_handler = dict_factory
    create_list_handler = list_factory

# Simple count entities
SIMPLE_COUNT_ENTITIES = {
    "applicants_all": {
        "method": "applicants_all",
        "label": "All Applicants"
    },
    "vacancies_all": {
        "method": "vacancies_all", 
        "label": "All Vacancies"
    },
    "vacancies_open": {
        "method": "vacancies_open",
        "label": "Open Vacancies"
    },
    "vacancies_closed": {
        "method": "vacancies_closed",
        "label": "Closed Vacancies"
    },
    "vacancies_last_6_months": {
        "method": "vacancies_last_6_months",
        "label": "Vacancies Last 6 Months"
    },
    "vacancies_last_year": {
        "method": "vacancies_last_year",
        "label": "Vacancies Last Year"
    },
    "hired_applicants": {
        "method": "applicants_hired",
        "label": "Hired Applicants"
    },
    "successful_closures": {
        "method": "vacancies_closed",
        "label": "Successful Closures"
    },
}

# Dict-based entities 
SIMPLE_DICT_ENTITIES = {
    "applicants_by_status": {
        "method": "applicants_by_status"
    },
    "applicants_by_source": {
        "method": "applicants_by_source"
    },
    "applicants_by_recruiter": {
        "method": "applicants_by_recruiter"
    },
    "applicants_by_hiring_manager": {
        "method": "applicants_by_hiring_manager"
    },
    "actions_by_recruiter": {
        "method": "actions_by_recruiter"
    },
    "recruiter_add": {
        "method": "recruiter_add"
    },
    "recruiter_comment": {
        "method": "recruiter_comment"
    },
    "recruiter_mail": {
        "method": "recruiter_mail"
    },
    "recruiter_agreement": {
        "method": "recruiter_agreement"
    },
    "moves_by_recruiter": {
        "method": "moves_by_recruiter"
    },
    "added_applicants_by_recruiter": {
        "method": "applicants_added_by_recruiter"
    },
    "rejections_by_recruiter": {
        "method": "rejections_by_recruiter"
    },
    "rejections_by_stage": {
        "method": "rejections_by_stage"
    },
    "rejections_by_reason": {
        "method": "rejections_by_reason"
    },
    "vacancy_conversion_rates": {
        "method": "vacancy_conversion_rates"
    },
    "vacancy_conversion_by_status": {
        "method": "vacancy_conversion_by_status"
    },
}

# List entities
SIMPLE_LIST_ENTITIES = {
    "divisions_all": {
        "method": "divisions_all",
        "entity_type": "Division"
    },
    "sources_all": {
        "method": "sources_all", 
        "entity_type": "Source"
    },
    "hiring_managers": {
        "method": "hiring_managers",
        "entity_type": "Manager"
    },
    "stages": {
        "method": "stages",
        "entity_type": "Stage"
    },
}

# Proxy entities (dict handlers with different names)
PROXY_ENTITIES = {
    "recruiter_performance": {
        "method": "actions_by_recruiter"
    },
    "time_in_status": {
        "method": "applicants_by_status"
    },
    "applicant_activity_trends": {
        "method": "applicants_by_recruiter"
    },
}

def get_simple_entity_configs():
    """Build the simple entity configurations with handlers."""
    if not create_count_handler:
        raise RuntimeError("Handler factories not initialized")
        
    configs = {}
    
    # Add count entities
    for entity, config in SIMPLE_COUNT_ENTITIES.items():
        configs[entity] = {
            HANDLER_KEY: create_count_handler(config["method"], config["label"])
        }
    
    # Add dict entities
    for entity, config in SIMPLE_DICT_ENTITIES.items():
        configs[entity] = {
            HANDLER_KEY: create_dict_handler(config["method"])
        }
    
    # Add list entities
    for entity, config in SIMPLE_LIST_ENTITIES.items():
        configs[entity] = {
            HANDLER_KEY: create_list_handler(config["method"], config["entity_type"])
        }
    
    # Add proxy entities
    for entity, config in PROXY_ENTITIES.items():
        configs[entity] = {
            HANDLER_KEY: create_dict_handler(config["method"])
        }
    
    return configs

# This will be populated by get_simple_entity_configs() after handler initialization
SIMPLE_ENTITY_CONFIGS = {}