"""
Entity configuration modules for chart data processor
"""

from .simple_entities import SIMPLE_ENTITY_CONFIGS
from .grouped_entities import GROUPED_ENTITY_CONFIGS  
from .special_handlers import SPECIAL_HANDLER_CONFIGS
from .legacy_mappings import LEGACY_ENTITY_MAPPINGS

# Combine all configurations
def get_entity_handlers():
    """Get the complete entity handlers configuration."""
    handlers = {}
    handlers.update(SIMPLE_ENTITY_CONFIGS)
    handlers.update(GROUPED_ENTITY_CONFIGS)
    handlers.update(SPECIAL_HANDLER_CONFIGS)
    return handlers

def get_legacy_mappings():
    """Get legacy entity mappings."""
    return LEGACY_ENTITY_MAPPINGS

__all__ = [
    'get_entity_handlers',
    'get_legacy_mappings',
    'SIMPLE_ENTITY_CONFIGS',
    'GROUPED_ENTITY_CONFIGS', 
    'SPECIAL_HANDLER_CONFIGS',
    'LEGACY_ENTITY_MAPPINGS'
]