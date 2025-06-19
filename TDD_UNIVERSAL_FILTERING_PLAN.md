# Test-Driven Development Plan for Universal HR Analytics Filtering System

## Executive Summary

This document outlines a comprehensive Test-Driven Development (TDD) approach for implementing a universal filtering system that enables **every entity to be filtered by every other entity** in the HR analytics platform. The current system has limited, distributed filtering capabilities that only work for specific entity combinations. This TDD plan ensures we build a robust, maintainable, and thoroughly tested universal filtering system.

## Current State Analysis

### Existing Testing Infrastructure

**✅ Strengths:**
- **Real Data Focus**: Tests use actual SQLite database (`huntflow_cache.db`) with production data
- **Async-First Architecture**: All tests properly handle async operations with `asyncio.run()`
- **Integration Testing**: Comprehensive tests covering 60+ entity/grouping combinations
- **Error Handling**: Basic try/catch patterns with descriptive error messages
- **Data Validation**: Tests verify data quality and meaningful results

**❌ Current Limitations:**
- **No pytest Framework**: Tests are standalone scripts, not pytest-compatible
- **No Unit Testing**: All tests are integration tests without isolation
- **Manual Verification**: Results are printed for visual inspection, no assertions
- **No Test Fixtures**: Direct database queries without consistent test data
- **No Mocking**: No isolation of external dependencies
- **No Coverage Reporting**: No visibility into test coverage

### Filtering System Assessment

**Current Capabilities:**
```python
# Limited filtering support - only 5 out of 15+ methods
filters = {
    "recruiters": "12345",     # Only for applicants
    "sources": "202",          # Only for hires  
    "period": "3 month"        # Not implemented
}
```

**Target Capabilities:**
```python
# Universal filtering - any entity filtered by any other entity
filters = {
    "period": "3 month",
    "recruiters": "12345",
    "vacancies": ["open", "paused"],
    "divisions": "engineering",
    "sources": {"operator": "in", "value": ["linkedin", "hh"]},
    "complex": {
        "and": [
            {"entity": "vacancies", "field": "state", "value": "open"},
            {"entity": "recruiters", "field": "performance", "operator": "gt", "value": 0.8}
        ]
    }
}
```

## TDD Strategy Overview

### Why TDD for This Project?

1. **Complex Domain Logic**: Filtering involves intricate relationships between entities
2. **High Risk of Regression**: Changes to filtering logic could break existing functionality
3. **Integration Complexity**: Multiple components (MetricsCalculator, ChartProcessor, API) must work together
4. **Real Data Constraints**: Must work with actual production data patterns
5. **AI Integration**: Must integrate seamlessly with the prompt.py AI interface

### TDD Benefits for Universal Filtering

1. **Design Clarity**: Tests force us to think about interfaces before implementation
2. **Regression Safety**: Comprehensive test suite prevents breaking existing functionality
3. **Documentation**: Tests serve as living documentation of filtering capabilities
4. **Confidence**: Every feature is validated against real data before deployment
5. **Refactoring Safety**: Can safely improve code structure with test coverage

## Implementation Phases

### Phase 1: Foundation Setup (Days 1-2)

**Objective**: Establish professional testing infrastructure

#### Day 1: Testing Framework Setup

**Tasks:**
```bash
# Install comprehensive testing stack
pip install pytest pytest-asyncio pytest-cov faker httpx pytest-mock
```

**Create pytest.ini:**
```ini
[tool:pytest]
testpaths = tests
asyncio_mode = auto
addopts = --cov=. --cov-report=html --cov-report=term-missing -v
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

**Directory Structure:**
```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── unit/                         # Isolated unit tests
│   ├── test_universal_filter.py   # Filter data classes
│   ├── test_filter_engine.py     # Core filtering logic
│   └── test_filter_parser.py     # Prompt parsing logic
├── integration/                  # Component integration tests
│   ├── test_metrics_with_filters.py
│   ├── test_chart_processing.py
│   └── test_real_data_filtering.py
├── api/                         # FastAPI endpoint tests
│   └── test_filtering_endpoints.py
└── fixtures/                    # Test data and utilities
    ├── test_data.py
    ├── mock_responses.py
    └── data_factories.py
```

**Commentary**: This structure separates concerns clearly - unit tests for individual components, integration tests for component interactions, and API tests for endpoint behavior. The fixtures directory provides reusable test data.

#### Day 2: Core Test Fixtures

**Create conftest.py:**
```python
import pytest
from unittest.mock import AsyncMock, Mock
from huntflow_local_client import HuntflowLocalClient
from datetime import datetime, timedelta

@pytest.fixture
async def real_data_client():
    """Use real cached data for integration tests"""
    return HuntflowLocalClient()

@pytest.fixture
async def sample_applicants(real_data_client):
    """Consistent sample of applicants for testing"""
    client = await real_data_client
    applicants = await client.get_applicants(limit=100)
    return applicants[:10]  # First 10 for consistent testing

@pytest.fixture
def mock_db_client():
    """Mock database client for unit tests"""
    return Mock()

@pytest.fixture
def mock_log_analyzer():
    """Mock log analyzer for unit tests"""
    return Mock()

@pytest.fixture
def test_applicants():
    """Factory-generated test applicants"""
    return [
        {
            "id": "1",
            "recruiter_id": "12345", 
            "vacancy_id": "v1",
            "source_id": "linkedin",
            "created": datetime.now()
        },
        {
            "id": "2",
            "recruiter_id": "67890",
            "vacancy_id": "v2", 
            "source_id": "hh",
            "created": datetime.now() - timedelta(days=100)
        }
    ]
```

**Commentary**: These fixtures provide both real data (for integration tests) and controlled test data (for unit tests). Real data ensures compatibility with production data patterns, while controlled data enables precise testing of edge cases.

### Phase 2: Core Filter Classes (Days 3-5)

**Objective**: Build the foundation data structures using TDD

#### TDD Cycle 1: Filter Data Classes

**Step 1: Write Failing Tests (RED)**

```python
# tests/unit/test_universal_filter.py
import pytest
from universal_filter import UniversalFilter, FilterOperator, EntityType, FilterSet, PeriodFilter

class TestUniversalFilter:
    """Test the core UniversalFilter data class"""
    
    def test_create_simple_equality_filter(self):
        """Test creating a basic equality filter"""
        # RED: This will fail - classes don't exist yet
        filter_obj = UniversalFilter(
            entity_type=EntityType.RECRUITERS,
            field="id",
            operator=FilterOperator.EQUALS,
            value="12345"
        )
        
        assert filter_obj.entity_type == EntityType.RECRUITERS
        assert filter_obj.field == "id"
        assert filter_obj.operator == FilterOperator.EQUALS
        assert filter_obj.value == "12345"
    
    def test_create_list_filter(self):
        """Test creating a filter with multiple values"""
        # RED: This will fail
        filter_obj = UniversalFilter(
            entity_type=EntityType.VACANCIES,
            field="state",
            operator=FilterOperator.IN,
            value=["open", "paused"]
        )
        
        assert filter_obj.operator == FilterOperator.IN
        assert len(filter_obj.value) == 2
        assert "open" in filter_obj.value
        assert "paused" in filter_obj.value
    
    def test_invalid_entity_type_raises_error(self):
        """Test that invalid entity types are rejected"""
        # RED: This will fail
        with pytest.raises(ValueError, match="Invalid entity type"):
            UniversalFilter(
                entity_type="invalid_entity",
                field="id",
                operator=FilterOperator.EQUALS,
                value="123"
            )
    
    def test_filter_validation(self):
        """Test filter value validation"""
        # RED: This will fail
        with pytest.raises(ValueError, match="Empty value not allowed"):
            UniversalFilter(
                entity_type=EntityType.RECRUITERS,
                field="id",
                operator=FilterOperator.EQUALS,
                value=""
            )

class TestPeriodFilter:
    """Test period-based filtering"""
    
    def test_create_period_filter_from_string(self):
        """Test creating period filter from string"""
        # RED: This will fail
        period_filter = PeriodFilter.from_string("3 month")
        
        assert period_filter.period_type == "3 month"
        assert period_filter.start_date is not None
        assert period_filter.end_date is not None
    
    def test_period_filter_date_calculation(self):
        """Test that period filters calculate correct date ranges"""
        # RED: This will fail
        period_filter = PeriodFilter.from_string("1 month")
        
        # Should be approximately 30 days ago
        days_diff = (datetime.now() - period_filter.start_date).days
        assert 28 <= days_diff <= 32  # Allow some variance

class TestFilterSet:
    """Test the FilterSet container"""
    
    def test_create_empty_filter_set(self):
        """Test creating an empty filter set"""
        # RED: This will fail
        filter_set = FilterSet()
        
        assert filter_set.period_filter is None
        assert filter_set.entity_filters == []
        assert filter_set.cross_entity_filters == []
    
    def test_filter_set_with_multiple_filters(self):
        """Test filter set with various filter types"""
        # RED: This will fail
        period_filter = PeriodFilter.from_string("3 month")
        entity_filter = UniversalFilter(
            entity_type=EntityType.RECRUITERS,
            field="id",
            operator=FilterOperator.EQUALS,
            value="12345"
        )
        
        filter_set = FilterSet(
            period_filter=period_filter,
            entity_filters=[entity_filter]
        )
        
        assert filter_set.period_filter == period_filter
        assert len(filter_set.entity_filters) == 1
        assert filter_set.entity_filters[0] == entity_filter
```

**Commentary**: These tests define the exact interface we want for our filter classes. They test both happy paths and error conditions. The tests are written to fail initially, driving us to implement exactly what's needed.

**Step 2: Implement Minimal Code (GREEN)**

```python
# universal_filter.py
from dataclasses import dataclass, field
from enum import Enum
from typing import Union, List, Any, Optional
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
            raise ValueError(f"Invalid entity type: {self.entity_type}")
        
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
```

**Commentary**: This implementation provides exactly what the tests require - no more, no less. The validation logic ensures filters are created correctly, and the PeriodFilter handles the time-based filtering logic that was missing from the original system.

**Step 3: Refactor (BLUE)**

```python
# Enhanced version with better validation and type safety
@dataclass
class UniversalFilter:
    """Universal filter with enhanced validation"""
    entity_type: EntityType
    field: str
    operator: FilterOperator
    value: Union[str, int, List[str], List[int], Dict[str, Any]]
    
    def __post_init__(self):
        """Enhanced validation with specific error messages"""
        if isinstance(self.entity_type, str):
            raise ValueError(f"Invalid entity type: {self.entity_type}. Must be EntityType enum.")
        
        if not self.field or not self.field.strip():
            raise ValueError("Field name cannot be empty")
        
        if not self._is_valid_value():
            raise ValueError(f"Invalid value for operator {self.operator.value}")
    
    def _is_valid_value(self) -> bool:
        """Validate value based on operator"""
        if self.operator in [FilterOperator.IN, FilterOperator.NOT_IN]:
            return isinstance(self.value, list) and len(self.value) > 0
        elif self.operator == FilterOperator.BETWEEN:
            return isinstance(self.value, list) and len(self.value) == 2
        else:
            return self.value is not None and self.value != ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert filter to dictionary for serialization"""
        return {
            "entity_type": self.entity_type.value,
            "field": self.field,
            "operator": self.operator.value,
            "value": self.value
        }
```

**Commentary**: The refactoring phase improves the code without changing its interface. We add better validation, type safety, and utility methods while keeping all tests passing.

### Phase 3: Filter Engine Core (Days 6-8)

**Objective**: Build the core filtering logic using TDD

#### TDD Cycle 2: Filter Engine Implementation

**Step 1: Write Failing Tests (RED)**

```python
# tests/unit/test_filter_engine.py
import pytest
from unittest.mock import AsyncMock, Mock
from universal_filter_engine import UniversalFilterEngine
from universal_filter import UniversalFilter, FilterSet, PeriodFilter, EntityType, FilterOperator

class TestUniversalFilterEngine:
    """Test the core filtering engine"""
    
    @pytest.fixture
    def mock_db_client(self):
        return Mock()
    
    @pytest.fixture
    def mock_log_analyzer(self):
        return Mock()
    
    @pytest.fixture
    def filter_engine(self, mock_db_client, mock_log_analyzer):
        return UniversalFilterEngine(mock_db_client, mock_log_analyzer)
    
    @pytest.fixture
    def sample_applicants(self):
        """Sample applicant data for testing"""
        return [
            {
                "id": "1",
                "recruiter_id": "12345",
                "vacancy_id": "v1",
                "source_id": "linkedin",
                "created": datetime.now()
            },
            {
                "id": "2", 
                "recruiter_id": "67890",
                "vacancy_id": "v2",
                "source_id": "hh",
                "created": datetime.now() - timedelta(days=100)
            },
            {
                "id": "3",
                "recruiter_id": "12345",
                "vacancy_id": "v3", 
                "source_id": "linkedin",
                "created": datetime.now() - timedelta(days=30)
            }
        ]
    
    @pytest.mark.asyncio
    async def test_apply_simple_recruiter_filter(self, filter_engine, sample_applicants):
        """Test filtering applicants by specific recruiter"""
        # RED: This will fail - method doesn't exist
        filter_set = FilterSet(
            cross_entity_filters=[
                UniversalFilter(
                    entity_type=EntityType.RECRUITERS,
                    field="id",
                    operator=FilterOperator.EQUALS,
                    value="12345"
                )
            ]
        )
        
        result = await filter_engine.apply_filters(
            EntityType.APPLICANTS,
            filter_set,
            sample_applicants
        )
        
        # Should return only applicants from recruiter 12345
        assert len(result) == 2
        for applicant in result:
            assert applicant["recruiter_id"] == "12345"
    
    @pytest.mark.asyncio
    async def test_apply_period_filter(self, filter_engine, sample_applicants):
        """Test filtering by time period"""
        # RED: This will fail
        filter_set = FilterSet(
            period_filter=PeriodFilter.from_string("1 month")
        )
        
        result = await filter_engine.apply_filters(
            EntityType.APPLICANTS,
            filter_set,
            sample_applicants
        )
        
        # Should return only recent applicants (not the 100-day old one)
        assert len(result) == 2
        for applicant in result:
            days_old = (datetime.now() - applicant["created"]).days
            assert days_old <= 30
    
    @pytest.mark.asyncio
    async def test_apply_multiple_filters(self, filter_engine, sample_applicants):
        """Test combining multiple filter types"""
        # RED: This will fail
        filter_set = FilterSet(
            period_filter=PeriodFilter.from_string("2 month"),
            cross_entity_filters=[
                UniversalFilter(
                    entity_type=EntityType.SOURCES,
                    field="id", 
                    operator=FilterOperator.EQUALS,
                    value="linkedin"
                )
            ]
        )
        
        result = await filter_engine.apply_filters(
            EntityType.APPLICANTS,
            filter_set,
            sample_applicants
        )
        
        # Should return only recent LinkedIn applicants
        assert len(result) == 1
        assert result[0]["id"] == "1"
        assert result[0]["source_id"] == "linkedin"
    
    @pytest.mark.asyncio
    async def test_apply_list_filter(self, filter_engine, sample_applicants):
        """Test filtering with list of values"""
        # RED: This will fail
        filter_set = FilterSet(
            cross_entity_filters=[
                UniversalFilter(
                    entity_type=EntityType.SOURCES,
                    field="id",
                    operator=FilterOperator.IN,
                    value=["linkedin", "hh"]
                )
            ]
        )
        
        result = await filter_engine.apply_filters(
            EntityType.APPLICANTS,
            filter_set,
            sample_applicants
        )
        
        # Should return all applicants (all are from linkedin or hh)
        assert len(result) == 3
    
    @pytest.mark.asyncio
    async def test_empty_filter_set_returns_all_data(self, filter_engine, sample_applicants):
        """Test that empty filters return all data"""
        # RED: This will fail
        filter_set = FilterSet()
        
        result = await filter_engine.apply_filters(
            EntityType.APPLICANTS,
            filter_set,
            sample_applicants
        )
        
        assert len(result) == 3
        assert result == sample_applicants
    
    def test_parse_prompt_filters_simple(self, filter_engine):
        """Test parsing simple prompt filters"""
        # RED: This will fail
        prompt_filters = {
            "period": "3 month",
            "recruiters": "12345"
        }
        
        filter_set = filter_engine.parse_prompt_filters(prompt_filters)
        
        assert filter_set.period_filter is not None
        assert filter_set.period_filter.period_type == "3 month"
        assert len(filter_set.cross_entity_filters) == 1
        
        recruiter_filter = filter_set.cross_entity_filters[0]
        assert recruiter_filter.entity_type == EntityType.RECRUITERS
        assert recruiter_filter.value == "12345"
    
    def test_parse_prompt_filters_complex(self, filter_engine):
        """Test parsing complex prompt filters"""
        # RED: This will fail
        prompt_filters = {
            "period": "1 month",
            "vacancies": ["open", "paused"],
            "divisions": "engineering"
        }
        
        filter_set = filter_engine.parse_prompt_filters(prompt_filters)
        
        assert filter_set.period_filter.period_type == "1 month"
        assert len(filter_set.cross_entity_filters) == 2
        
        vacancy_filter = next(f for f in filter_set.cross_entity_filters 
                             if f.entity_type == EntityType.VACANCIES)
        assert vacancy_filter.operator == FilterOperator.IN
        assert vacancy_filter.value == ["open", "paused"]
```

**Commentary**: These tests define the exact behavior we want from the filter engine. They test single filters, multiple filters, edge cases, and the critical prompt parsing functionality that integrates with the AI system.

**Step 2: Implement Filter Engine (GREEN)**

```python
# universal_filter_engine.py
from typing import Dict, List, Any, Optional
from universal_filter import UniversalFilter, FilterSet, PeriodFilter, EntityType, FilterOperator
from datetime import datetime

class UniversalFilterEngine:
    """Centralized engine for processing all filters"""
    
    def __init__(self, db_client, log_analyzer):
        self.db_client = db_client
        self.log_analyzer = log_analyzer
        self.entity_relationships = self._build_entity_relationships()
    
    def _build_entity_relationships(self) -> Dict[str, Dict[str, str]]:
        """Define how entities relate to each other"""
        return {
            "applicants": {
                "recruiters": "recruiter_id",
                "vacancies": "vacancy_id",
                "sources": "source_id",
                "stages": "stage_id"
            },
            "vacancies": {
                "recruiters": "recruiter_id",
                "hiring_managers": "hiring_manager_id",
                "divisions": "division_id"
            },
            "hires": {
                "recruiters": "recruiter_id",
                "sources": "source_id",
                "vacancies": "vacancy_id"
            }
        }
    
    async def apply_filters(self, entity_type: EntityType, filters: FilterSet, 
                          base_data: Optional[List] = None) -> List:
        """Apply all filters to get filtered entity data"""
        
        if base_data is None:
            base_data = await self._fetch_base_data(entity_type)
        
        result = base_data
        
        # Apply period filters first (most selective)
        if filters.period_filter:
            result = self._apply_period_filter(result, filters.period_filter)
        
        # Apply cross-entity filters (relationships)
        if filters.cross_entity_filters:
            result = self._apply_cross_entity_filters(result, filters.cross_entity_filters, entity_type)
        
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
            if item_date and isinstance(item_date, datetime):
                if period_filter.start_date <= item_date <= period_filter.end_date:
                    filtered_data.append(item)
            else:
                # If no date field, include the item (don't filter out)
                filtered_data.append(item)
        
        return filtered_data
    
    def _apply_cross_entity_filters(self, data: List, filters: List[UniversalFilter], 
                                  target_entity: EntityType) -> List:
        """Apply filters based on entity relationships"""
        
        for filter_obj in filters:
            relationship_key = self.entity_relationships.get(
                target_entity.value, {}
            ).get(filter_obj.entity_type.value)
            
            if not relationship_key:
                continue  # Skip if no relationship defined
            
            data = self._apply_single_filter(data, filter_obj, relationship_key)
        
        return data
    
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
        
        return False
    
    def parse_prompt_filters(self, prompt_filters: Dict[str, Any]) -> FilterSet:
        """Convert prompt.py filter format to FilterSet"""
        
        period_filter = None
        cross_entity_filters = []
        
        for filter_key, filter_value in prompt_filters.items():
            if filter_key == "period":
                period_filter = PeriodFilter.from_string(filter_value)
            elif filter_key in [e.value for e in EntityType]:
                # This is a cross-entity filter
                if isinstance(filter_value, list):
                    operator = FilterOperator.IN
                else:
                    operator = FilterOperator.EQUALS
                
                cross_entity_filters.append(
                    UniversalFilter(
                        entity_type=EntityType(filter_key),
                        field="id" if isinstance(filter_value, str) and filter_value.isdigit() else "state",
                        operator=operator,
                        value=filter_value
                    )
                )
        
        return FilterSet(
            period_filter=period_filter,
            cross_entity_filters=cross_entity_filters
        )
    
    async def _fetch_base_data(self, entity_type: EntityType) -> List:
        """Fetch base data for an entity type"""
        # This would call the appropriate client method
        # For now, return empty list (tests pass their own data)
        return []
```

**Commentary**: This implementation provides the core filtering logic. It handles relationships between entities, supports multiple filter types, and can parse the prompt format. The relationship mapping is crucial for cross-entity filtering.

### Phase 4: MetricsCalculator Integration (Days 9-11)

**Objective**: Integrate universal filtering with existing metrics system

#### TDD Cycle 3: Enhanced MetricsCalculator

**Step 1: Write Integration Tests (RED)**

```python
# tests/integration/test_metrics_with_filters.py
import pytest
from unittest.mock import Mock, AsyncMock
from enhanced_metrics_calculator import EnhancedMetricsCalculator
from huntflow_local_client import HuntflowLocalClient

class TestMetricsCalculatorWithFilters:
    """Test MetricsCalculator with universal filtering"""
    
    @pytest.fixture
    async def real_client(self):
        """Real database client for integration tests"""
        return HuntflowLocalClient()
    
    @pytest.fixture
    def mock_log_analyzer(self):
        return Mock()
    
    @pytest.fixture
    async def calculator(self, real_client, mock_log_analyzer):
        """Enhanced calculator with real data"""
        return EnhancedMetricsCalculator(real_client, mock_log_analyzer)
    
    @pytest.mark.asyncio
    async def test_get_applicants_with_recruiter_filter(self, calculator):
        """Test filtering applicants by recruiter"""
        # RED: This will fail - enhanced method doesn't exist
        filters = {"recruiters": "12345", "period": "3 month"}
        
        # First get all applicants to find a valid recruiter ID
        all_applicants = await calculator.get_applicants()
        if not all_applicants:
            pytest.skip("No applicants in test data")
        
        # Use a real recruiter ID from the data
        real_recruiter_id = all_applicants[0]["recruiter_id"]
        filters["recruiters"] = real_recruiter_id
        
        result = await calculator.get_applicants(filters)
        
        # All applicants should belong to the specified recruiter
        assert len(result) > 0
        for applicant in result:
            assert applicant["recruiter_id"] == real_recruiter_id
    
    @pytest.mark.asyncio
    async def test_get_hires_with_source_filter(self, calculator):
        """Test filtering hires by source"""
        # RED: This will fail
        
        # First get all hires to find a valid source
        all_hires = await calculator.get_hires()
        if not all_hires:
            pytest.skip("No hires in test data")
        
        # Use a real source ID from the data
        real_source_id = all_hires[0]["source_id"]
        filters = {"sources": real_source_id, "period": "1 month"}
        
        result = await calculator.get_hires(filters)
        
        # All hires should be from the specified source
        assert len(result) > 0
        for hire in result:
            assert hire["source_id"] == real_source_id
    
    @pytest.mark.asyncio
    async def test_get_vacancies_with_multiple_filters(self, calculator):
        """Test filtering vacancies with multiple criteria"""
        # RED: This will fail
        filters = {
            "vacancies": "open",
            "period": "6 month"
        }
        
        result = await calculator.get_vacancies(filters)
        
        # All vacancies should be open
        for vacancy in result:
            assert vacancy["state"] == "open"
    
    @pytest.mark.asyncio
    async def test_backwards_compatibility(self, calculator):
        """Test that methods work without filters (backwards compatibility)"""
        # RED: This will fail if we break existing functionality
        
        # These should work exactly as before
        applicants = await calculator.get_applicants()
        hires = await calculator.get_hires()
        vacancies = await calculator.get_vacancies()
        
        assert isinstance(applicants, list)
        assert isinstance(hires, list)
        assert isinstance(vacancies, list)
    
    @pytest.mark.asyncio
    async def test_complex_multi_entity_filtering(self, calculator):
        """Test complex filtering across multiple entities"""
        # RED: This will fail
        
        # Get sample data first
        all_applicants = await calculator.get_applicants()
        if len(all_applicants) < 5:
            pytest.skip("Not enough applicants for complex filtering test")
        
        # Use real IDs from the data
        sample_recruiter = all_applicants[0]["recruiter_id"]
        sample_vacancy = all_applicants[0]["vacancy_id"]
        
        filters = {
            "recruiters": sample_recruiter,
            "vacancies": sample_vacancy,
            "period": "3 month"
        }
        
        result = await calculator.get_applicants(filters)
        
        # Should have applicants matching all criteria
        for applicant in result:
            assert applicant["recruiter_id"] == sample_recruiter
            assert applicant["vacancy_id"] == sample_vacancy
```

**Commentary**: These tests use real data to ensure the filtering works with actual production data patterns. They test both simple and complex filtering scenarios while maintaining backwards compatibility.

**Step 2: Implement Enhanced MetricsCalculator (GREEN)**

```python
# enhanced_metrics_calculator.py
from typing import Dict, Any, List, Optional
from metrics_calculator import MetricsCalculator
from universal_filter_engine import UniversalFilterEngine
from universal_filter import EntityType

class EnhancedMetricsCalculator(MetricsCalculator):
    """Enhanced MetricsCalculator with universal filtering support"""
    
    def __init__(self, client, log_analyzer):
        super().__init__(client, log_analyzer)
        self.filter_engine = UniversalFilterEngine(client, log_analyzer)
    
    async def get_applicants(self, filters: Optional[Dict[str, Any]] = None) -> List:
        """Get applicants with universal filtering support"""
        
        # Get base data using parent method
        base_data = await super().get_applicants()
        
        # Apply filters if provided
        if filters:
            filter_set = self.filter_engine.parse_prompt_filters(filters)
            return await self.filter_engine.apply_filters(
                EntityType.APPLICANTS, 
                filter_set, 
                base_data
            )
        
        return base_data
    
    async def get_hires(self, filters: Optional[Dict[str, Any]] = None) -> List:
        """Get hires with universal filtering support"""
        
        base_data = await super().get_hires()
        
        if filters:
            filter_set = self.filter_engine.parse_prompt_filters(filters)
            return await self.filter_engine.apply_filters(
                EntityType.HIRES,
                filter_set,
                base_data
            )
        
        return base_data
    
    async def get_vacancies(self, filters: Optional[Dict[str, Any]] = None) -> List:
        """Get vacancies with universal filtering support"""
        
        base_data = await super().get_vacancies()
        
        if filters:
            filter_set = self.filter_engine.parse_prompt_filters(filters)
            return await self.filter_engine.apply_filters(
                EntityType.VACANCIES,
                filter_set,
                base_data
            )
        
        return base_data
    
    # Apply the same pattern to ALL methods
    async def get_recruiters(self, filters: Optional[Dict[str, Any]] = None) -> List:
        """Get recruiters with universal filtering support"""
        
        base_data = await super().get_recruiters()
        
        if filters:
            filter_set = self.filter_engine.parse_prompt_filters(filters)
            return await self.filter_engine.apply_filters(
                EntityType.RECRUITERS,
                filter_set,
                base_data
            )
        
        return base_data
    
    # ... Continue for all other methods
```

**Commentary**: This approach maintains full backwards compatibility while adding universal filtering. The pattern is consistent across all methods, making it easy to understand and maintain.

### Phase 5: Real Data Validation (Days 12-14)

**Objective**: Ensure the system works with actual production data

#### TDD Cycle 4: Real Data Testing

```python
# tests/integration/test_real_data_filtering.py
import pytest
from huntflow_local_client import HuntflowLocalClient
from enhanced_metrics_calculator import EnhancedMetricsCalculator
from unittest.mock import Mock

class TestRealDataFiltering:
    """Test filtering with actual cached production data"""
    
    @pytest.fixture
    async def real_calculator(self):
        """Calculator with real database connection"""
        client = HuntflowLocalClient()
        return EnhancedMetricsCalculator(client, Mock())
    
    @pytest.mark.asyncio
    async def test_period_filtering_accuracy(self, real_calculator):
        """Test that period filters return accurate date ranges"""
        
        # Get applicants from different time periods
        recent_applicants = await real_calculator.get_applicants({"period": "1 month"})
        older_applicants = await real_calculator.get_applicants({"period": "6 month"})
        
        # Recent should be subset of older
        assert len(recent_applicants) <= len(older_applicants)
        
        # Check actual dates if available
        from datetime import datetime, timedelta
        one_month_ago = datetime.now() - timedelta(days=30)
        
        for applicant in recent_applicants:
            if "created" in applicant:
                assert applicant["created"] >= one_month_ago
    
    @pytest.mark.asyncio
    async def test_cross_entity_filtering_consistency(self, real_calculator):
        """Test that cross-entity filters maintain data consistency"""
        
        # Get all applicants
        all_applicants = await real_calculator.get_applicants()
        if not all_applicants:
            pytest.skip("No applicants in test data")
        
        # Pick a recruiter that has applicants
        recruiter_counts = {}
        for applicant in all_applicants:
            rid = applicant["recruiter_id"]
            recruiter_counts[rid] = recruiter_counts.get(rid, 0) + 1
        
        # Use recruiter with most applicants
        top_recruiter = max(recruiter_counts.keys(), key=lambda x: recruiter_counts[x])
        expected_count = recruiter_counts[top_recruiter]
        
        # Filter by that recruiter
        filtered_applicants = await real_calculator.get_applicants({
            "recruiters": top_recruiter
        })
        
        # Should get exact count
        assert len(filtered_applicants) == expected_count
        
        # All should have correct recruiter_id
        for applicant in filtered_applicants:
            assert applicant["recruiter_id"] == top_recruiter
    
    @pytest.mark.asyncio
    async def test_performance_with_large_datasets(self, real_calculator):
        """Test performance with realistic data volumes"""
        import time
        
        # Test filtering performance
        start_time = time.time()
        
        result = await real_calculator.get_applicants({
            "period": "3 month",
            "recruiters": "any_valid_id"  # Will be replaced with real ID
        })
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete within reasonable time (adjust based on data size)
        assert processing_time < 5.0  # 5 seconds max
        
        # Log performance for monitoring
        print(f"Filtered {len(result)} applicants in {processing_time:.2f} seconds")
    
    @pytest.mark.asyncio
    async def test_data_integrity_after_filtering(self, real_calculator):
        """Test that filtering doesn't corrupt data"""
        
        # Get unfiltered data
        original_applicants = await real_calculator.get_applicants()
        
        # Apply various filters
        period_filtered = await real_calculator.get_applicants({"period": "3 month"})
        
        # Check data integrity
        for applicant in period_filtered:
            # Should have all required fields
            assert "id" in applicant
            assert "recruiter_id" in applicant
            
            # Should be subset of original data
            original_ids = [a["id"] for a in original_applicants]
            assert applicant["id"] in original_ids
```

**Commentary**: These tests ensure that the filtering system works correctly with real production data, maintains performance, and preserves data integrity.

## TDD Benefits and Outcomes

### Design Benefits

1. **Clear Interfaces**: Tests force us to define clean, usable APIs
2. **Separation of Concerns**: Each component has a single responsibility
3. **Extensibility**: New entity types and filters can be added easily
4. **Error Handling**: Edge cases are tested and handled properly

### Quality Assurance

1. **Regression Prevention**: Comprehensive test suite prevents breaking changes
2. **Documentation**: Tests serve as living documentation of system behavior
3. **Confidence**: Every feature is validated against real data
4. **Maintainability**: Well-tested code is easier to refactor and improve

### Integration Benefits

1. **AI Compatibility**: Filters integrate seamlessly with prompt.py
2. **Backwards Compatibility**: Existing code continues to work without changes
3. **Performance**: Filtering is optimized for real-world data volumes
4. **Reliability**: Extensive testing ensures consistent behavior

## Execution Timeline

### Week 1: Foundation (Days 1-7)
- **Days 1-2**: Setup testing infrastructure
- **Days 3-5**: Implement core filter classes with TDD
- **Days 6-7**: Build filter engine core

### Week 2: Integration (Days 8-14)
- **Days 8-11**: Integrate with MetricsCalculator
- **Days 12-14**: Real data validation and performance testing

### Week 3: Completion (Days 15-21)
- **Days 15-17**: Complete all entity method updates
- **Days 18-19**: Add complex filtering features
- **Days 20-21**: Final testing and optimization

## Success Metrics

1. **Test Coverage**: 95%+ code coverage for filtering components
2. **Performance**: Filtering operations complete in <2 seconds
3. **Compatibility**: All existing tests continue to pass
4. **Functionality**: Every entity can be filtered by every other entity
5. **Usability**: AI can generate complex filtering queries naturally

## Conclusion

This TDD approach ensures we build a robust, maintainable, and thoroughly tested universal filtering system. By writing tests first, we guarantee that the system meets its requirements and integrates properly with the existing AI-powered analytics platform.

The comprehensive test suite provides confidence for future development and ensures that the filtering system will work reliably with real production data.