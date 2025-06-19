from dataclasses import dataclass, field
from enum import Enum
from typing import Union, List, Any, Optional, Dict
from datetime import datetime, timedelta

class EntityType(Enum):
    """All entity types that can be filtered"""
    APPLICANTS = "applicants"
    VACANCIES = "vacancies"
    RECRUITERS = "recruiters"
    HIRING_MANAGERS = "hiring_managers"
    STAGES = "stages"
    SOURCES = "sources"
    HIRES = "hires"
    REJECTIONS = "rejections"
    ACTIONS = "actions"
    DIVISIONS = "divisions"

class FilterOperator(Enum):
    """All supported filter operations"""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    IN = "in"
    NOT_IN = "not_in"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    BETWEEN = "between"
    CONTAINS = "contains"
    EXISTS = "exists"

@dataclass
class UniversalFilter:
    """Universal filter that can be applied across all entities"""
    entity_type: EntityType
    field: str
    operator: FilterOperator
    value: Union[str, int, List[str], List[int], Dict[str, Any]]
    
    def __post_init__(self):
        """Validate filter after creation"""
        if isinstance(self.entity_type, str):
            raise ValueError(f"Invalid entity type: {self.entity_type}. Must be EntityType enum.")
        
        if not self.value and self.value != 0:
            raise ValueError("Empty value not allowed")

@dataclass
class PeriodFilter:
    """Time-based filtering"""
    period_type: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    @classmethod
    def from_string(cls, period_str: str) -> 'PeriodFilter':
        """Create period filter from string like '3 month'"""
        now = datetime.now()
        
        if period_str == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif period_str == "this week":
            days_since_monday = now.weekday()
            start_date = now - timedelta(days=days_since_monday)
            end_date = now
        elif period_str == "1 month":
            start_date = now - timedelta(days=30)
            end_date = now
        elif period_str == "2 month":
            start_date = now - timedelta(days=60)
            end_date = now
        elif period_str == "3 month":
            start_date = now - timedelta(days=90)
            end_date = now
        elif period_str == "6 month":
            start_date = now - timedelta(days=180)
            end_date = now
        elif period_str == "year":
            start_date = now - timedelta(days=365)
            end_date = now
        else:
            raise ValueError(f"Unknown period type: {period_str}")
        
        return cls(
            period_type=period_str,
            start_date=start_date,
            end_date=end_date
        )

@dataclass
class FilterSet:
    """Collection of all filters to apply"""
    period_filter: Optional[PeriodFilter] = None
    entity_filters: List[UniversalFilter] = field(default_factory=list)
    cross_entity_filters: List[UniversalFilter] = field(default_factory=list)