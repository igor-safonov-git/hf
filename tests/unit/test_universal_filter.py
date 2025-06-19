import pytest
from datetime import datetime
from universal_filter import UniversalFilter, FilterOperator, EntityType, FilterSet, PeriodFilter

class TestUniversalFilter:
    """Test the core UniversalFilter data class"""
    
    def test_create_simple_equality_filter(self):
        """Test creating a basic equality filter"""
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
        with pytest.raises(ValueError, match="Invalid entity type"):
            UniversalFilter(
                entity_type="invalid_entity",
                field="id",
                operator=FilterOperator.EQUALS,
                value="123"
            )
    
    def test_filter_validation(self):
        """Test filter value validation"""
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
        period_filter = PeriodFilter.from_string("3 month")
        
        assert period_filter.period_type == "3 month"
        assert period_filter.start_date is not None
        assert period_filter.end_date is not None
    
    def test_period_filter_date_calculation(self):
        """Test that period filters calculate correct date ranges"""
        period_filter = PeriodFilter.from_string("1 month")
        
        # Should be approximately 30 days ago
        days_diff = (datetime.now() - period_filter.start_date).days
        assert 28 <= days_diff <= 32  # Allow some variance

class TestFilterSet:
    """Test the FilterSet container"""
    
    def test_create_empty_filter_set(self):
        """Test creating an empty filter set"""
        filter_set = FilterSet()
        
        assert filter_set.period_filter is None
        assert filter_set.entity_filters == []
        assert filter_set.cross_entity_filters == []
    
    def test_filter_set_with_multiple_filters(self):
        """Test filter set with various filter types"""
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