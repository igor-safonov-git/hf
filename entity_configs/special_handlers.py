"""
Special handler configurations - entities requiring custom processing
"""

from typing import Dict, Any

# Import constants
HANDLER_KEY = "handler"
GROUPINGS_KEY = "groupings"
DEFAULT_KEY = "default"

# These will be set by the main module after importing special handlers
handle_conversion_summary = None
handle_status_groups = None
handle_actions_by_type = None
handle_moves_by_type = None
handle_total_moves = None
create_dict_handler = None
create_list_handler = None

def _init_handlers(conversion_handler, status_handler, actions_type_handler, 
                  moves_type_handler, total_moves_handler, dict_factory, list_factory):
    """Initialize special handlers - called by main module."""
    global handle_conversion_summary, handle_status_groups, handle_actions_by_type
    global handle_moves_by_type, handle_total_moves, create_dict_handler, create_list_handler
    handle_conversion_summary = conversion_handler
    handle_status_groups = status_handler
    handle_actions_by_type = actions_type_handler
    handle_moves_by_type = moves_type_handler
    handle_total_moves = total_moves_handler
    create_dict_handler = dict_factory
    create_list_handler = list_factory

def get_special_handler_configs():
    """Build the special handler configurations."""
    if not handle_conversion_summary:
        raise RuntimeError("Special handlers not initialized")
    
    return {
        # Special function-based handlers
        "vacancy_conversion_summary": {
            HANDLER_KEY: handle_conversion_summary
        },
        "status_groups": {
            HANDLER_KEY: handle_status_groups
        },
        
        # Simple list handlers (could be in simple_entities but placed here for organization)
        "sources": {
            HANDLER_KEY: create_list_handler("sources", "Source")
        },
        "divisions": {
            HANDLER_KEY: create_list_handler("divisions", "Division")
        },
        
        # Complex entities with special grouping handlers
        "moves": {
            DEFAULT_KEY: handle_total_moves,
            GROUPINGS_KEY: {
                "recruiter": create_dict_handler("moves_by_recruiter"),
                "recruiters": create_dict_handler("moves_by_recruiter"),
                "type": handle_moves_by_type,
                "detailed": handle_moves_by_type,
            }
        }
    }

# This will be populated by get_special_handler_configs() after handler initialization
SPECIAL_HANDLER_CONFIGS = {}