"""
Grouped entity configurations - entities with multiple grouping options
"""

from typing import Dict, Any

# Import constants
HANDLER_KEY = "handler"
GROUPINGS_KEY = "groupings"
DEFAULT_KEY = "default"

# These will be set by the main module after importing handler factories
create_count_handler = None
create_dict_handler = None
handle_actions_by_type = None

def _init_handlers(count_factory, dict_factory, actions_type_handler=None):
    """Initialize handler factories - called by main module."""
    global create_count_handler, create_dict_handler, handle_actions_by_type
    create_count_handler = count_factory
    create_dict_handler = dict_factory
    handle_actions_by_type = actions_type_handler

# Entity configurations with explicit method mappings
GROUPED_ENTITY_SPECS = {
    "applicants": {
        "default": {
            "method": "applicants_all",
            "label": "Total Applicants"
        },
        "groupings": {
            "source": "applicants_by_source",
            "source_id": "applicants_by_source", 
            "sources": "applicants_by_source",
            "stage": "applicants_by_status",
            "stages": "applicants_by_status",
            "status": "applicants_by_status",
            "status_id": "applicants_by_status",
            "recruiter": "applicants_by_recruiter",
            "recruiters": "applicants_by_recruiter",
            "hiring_manager": "applicants_by_hiring_manager",
            "hiring_managers": "applicants_by_hiring_manager",
            "division": "applicants_by_division",
            "divisions": "applicants_by_division",
            "month": "applicants_by_month",
            "monthly": "applicants_by_month",
            "time": "applicants_by_month",
        }
    },
    
    "vacancies": {
        "default": {
            "method": "vacancies_all",
            "label": "Total Vacancies"
        },
        "groupings": {
            "state": "vacancies_by_state",
            "recruiter": "vacancies_by_recruiter", 
            "recruiters": "vacancies_by_recruiter",
            "hiring_manager": "vacancies_by_hiring_manager",
            "hiring_managers": "vacancies_by_hiring_manager",
            "division": "vacancies_by_division",
            "divisions": "vacancies_by_division",
            "stage": "vacancies_by_stage",
            "stages": "vacancies_by_stage",
            "priority": "vacancies_by_priority",
            "priorities": "vacancies_by_priority",
            "month": "vacancies_by_month",
            "monthly": "vacancies_by_month",
            "time": "vacancies_by_month",
        }
    },
    
    "recruiters": {
        "default": {
            "method": "recruiters_all",
            "label": "Total Recruiters"
        },
        "groupings": {
            "hirings": "recruiters_by_hirings",
            "vacancy": "recruiters_by_vacancies",
            "vacancies": "recruiters_by_vacancies",
            "applicant": "recruiters_by_applicants",
            "applicants": "recruiters_by_applicants",
            "division": "recruiters_by_divisions",
            "divisions": "recruiters_by_divisions",
        }
    },
    
    "vacancy_statuses": {
        "default": {
            "method": "statuses_all",
            "label": "Total Vacancy Statuses"
        },
        "groupings": {
            "type": "statuses_by_type",
            "id": "statuses_list",
            "name": "statuses_list",
        }
    },
    
    "active_candidates": {
        "default": {
            "method": "applicants_all",
            "label": "Active Candidates"
        },
        "groupings": {
            "status_id": "applicants_by_status",
        }
    },
    
    "hires": {
        "default": {
            "method": "hires",
            "label": "Hired Candidates"
        },
        "groupings": {
            "recruiter": "recruiters_by_hirings",
            "recruiters": "recruiters_by_hirings",
            "source": "hires_by_source",
            "sources": "hires_by_source", 
            "stage": "hires_by_stage",
            "stages": "hires_by_stage",
            "division": "hires_by_division",
            "divisions": "hires_by_division",
        }
    },
    
    "actions": {
        "default": {
            "method": "actions",
            "label": "Total Actions"
        },
        "groupings": {
            "recruiter": "actions_by_recruiter",
            "recruiters": "actions_by_recruiter",
            "month": "actions_by_month",
            "monthly": "actions_by_month", 
            "time": "actions_by_month",
        },
        "special_groupings": {
            "type": "handle_actions_by_type",
            "action_type": "handle_actions_by_type",
        }
    },
    
    "rejections": {
        "default": {
            "method": "rejections",
            "label": "Total Rejections"
        },
        "groupings": {
            "recruiter": "rejections_by_recruiter",
            "recruiters": "rejections_by_recruiter",
            "reason": "rejections_by_reason",
            "reasons": "rejections_by_reason",
            "stage": "rejections_by_stage",
            "stages": "rejections_by_stage",
        }
    },
}

def get_grouped_entity_configs():
    """Build the grouped entity configurations with handlers."""
    if not create_count_handler:
        raise RuntimeError("Handler factories not initialized")
        
    configs = {}
    
    for entity, spec in GROUPED_ENTITY_SPECS.items():
        entity_config = {}
        
        # Add default handler
        if "default" in spec:
            default_spec = spec["default"]
            entity_config[DEFAULT_KEY] = create_count_handler(
                default_spec["method"], 
                default_spec["label"]
            )
        
        # Add grouping handlers
        if "groupings" in spec:
            groupings = {}
            for group_key, method_name in spec["groupings"].items():
                groupings[group_key] = create_dict_handler(method_name)
            
            # Add special groupings if they exist
            if "special_groupings" in spec and handle_actions_by_type:
                for group_key, handler_name in spec["special_groupings"].items():
                    if handler_name == "handle_actions_by_type":
                        groupings[group_key] = handle_actions_by_type
            
            entity_config[GROUPINGS_KEY] = groupings
        
        configs[entity] = entity_config
    
    return configs

# This will be populated by get_grouped_entity_configs() after handler initialization  
GROUPED_ENTITY_CONFIGS = {}