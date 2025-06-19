import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timedelta
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
        base_time = datetime(2025, 6, 15, 12, 0, 0)  # Fixed timestamp
        return [
            {
                "id": "1",
                "recruiter_id": "12345",
                "vacancy_id": "v1",
                "source_id": "linkedin",
                "created": base_time
            },
            {
                "id": "2", 
                "recruiter_id": "67890",
                "vacancy_id": "v2",
                "source_id": "hh",
                "created": base_time - timedelta(days=100)
            },
            {
                "id": "3",
                "recruiter_id": "12345",
                "vacancy_id": "v3", 
                "source_id": "linkedin",
                "created": base_time - timedelta(days=25)  # Within 30 days for sure
            }
        ]
    
    @pytest.mark.asyncio
    async def test_apply_simple_recruiter_filter(self, filter_engine, sample_applicants):
        """Test filtering applicants by specific recruiter"""
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
        assert len(result) == 2
        linkedin_ids = {r["id"] for r in result}
        assert linkedin_ids == {"1", "3"}
        for applicant in result:
            assert applicant["source_id"] == "linkedin"
    
    @pytest.mark.asyncio
    async def test_apply_list_filter(self, filter_engine, sample_applicants):
        """Test filtering with list of values"""
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