"""
Huntflow Analytics Views
Auto-generated view definitions for analytical queries
"""

from typing import Dict, Any, List, Optional
from sqlalchemy import select, func, between, distinct
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class HuntflowViews:
    """SQL view definitions for Huntflow analytics
    
    Provides analytical queries for Huntflow recruitment data with proper
    error handling and validation.
    """
    
    def __init__(self, engine: AsyncEngine, tables: Dict[str, Any]):
        self.engine = engine
        self.tables = tables
        self._validate_tables()
    
    def _validate_tables(self) -> None:
        """Validate required tables exist"""
        required_tables = ['vacancies', 'applicants', 'applicant_links', 'offers', 
                          'sources', 'recruiters', 'status_mapping']
        missing = [t for t in required_tables if t not in self.tables]
        if missing:
            raise ValueError(f"Missing required tables: {missing}")
    
    # Vacancy Views
    async def vacancies_by_state(self, state: str) -> List[Dict]:
        """Get vacancies filtered by state (OPEN, CLOSED, HOLD)
        
        Args:
            state: Vacancy state to filter by
            
        Returns:
            List of vacancy dictionaries
            
        Raises:
            ValueError: If state is invalid
            SQLAlchemyError: On database errors
        """
        valid_states = ['OPEN', 'CLOSED', 'HOLD']
        if state not in valid_states:
            raise ValueError(f"Invalid state '{state}'. Must be one of: {valid_states}")
            
        try:
            query = select(self.tables['vacancies']).where(
                self.tables['vacancies'].c.state == state
            )
            async with self.engine.begin() as conn:
                result = await conn.execute(query)
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as e:
            logger.error(f"Database error in vacancies_by_state: {e}")
            raise
    
    async def vacancies_by_recruiter(self, recruiter_id: int) -> List[Dict]:
        """Get vacancies assigned to specific recruiter (via coworkers JSON)
        
        Args:
            recruiter_id: ID of the recruiter
            
        Returns:
            List of vacancy dictionaries
            
        Raises:
            ValueError: If recruiter_id is invalid
            SQLAlchemyError: On database errors
        """
        if not isinstance(recruiter_id, int) or recruiter_id <= 0:
            raise ValueError(f"Invalid recruiter_id: {recruiter_id}")
            
        try:
            # Using PostgreSQL JSONB operators for efficient search
            query = select(self.tables['vacancies']).where(
                self.tables['vacancies'].c.coworkers.op('@>')([{'id': recruiter_id}])
            )
            async with self.engine.begin() as conn:
                result = await conn.execute(query)
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as e:
            logger.error(f"Database error in vacancies_by_recruiter: {e}")
            raise
    
    async def vacancies_by_division(self, division_id: int) -> List[Dict]:
        """Get vacancies by account division
        
        Args:
            division_id: ID of the division
            
        Returns:
            List of vacancy dictionaries
            
        Raises:
            ValueError: If division_id is invalid
            SQLAlchemyError: On database errors
        """
        if not isinstance(division_id, int) or division_id <= 0:
            raise ValueError(f"Invalid division_id: {division_id}")
            
        try:
            query = select(self.tables['vacancies']).where(
                self.tables['vacancies'].c.account_division == division_id
            )
            async with self.engine.begin() as conn:
                result = await conn.execute(query)
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as e:
            logger.error(f"Database error in vacancies_by_division: {e}")
            raise
    
    async def vacancies_by_date_range(self, start_date: datetime, end_date: datetime, date_field: str = 'created') -> List[Dict]:
        """Get vacancies within date range (created, updated, or custom field)
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            date_field: Field to filter on (default: 'created')
            
        Returns:
            List of vacancy dictionaries
            
        Raises:
            ValueError: If dates or field are invalid
            AttributeError: If date_field doesn't exist
            SQLAlchemyError: On database errors
        """
        if start_date > end_date:
            raise ValueError(f"start_date ({start_date}) must be before end_date ({end_date})")
            
        valid_date_fields = ['created', 'updated']
        if date_field not in valid_date_fields:
            raise ValueError(f"Invalid date_field '{date_field}'. Must be one of: {valid_date_fields}")
            
        try:
            column = getattr(self.tables['vacancies'].c, date_field)
            query = select(self.tables['vacancies']).where(
                between(column, start_date, end_date)
            )
            async with self.engine.begin() as conn:
                result = await conn.execute(query)
                return [dict(row._mapping) for row in result]
        except AttributeError:
            raise ValueError(f"Field '{date_field}' does not exist in vacancies table")
        except SQLAlchemyError as e:
            logger.error(f"Database error in vacancies_by_date_range: {e}")
            raise
    
    # Applicant Views
    async def applicants_by_source(self, source_id: int) -> List[Dict]:
        """Get applicants from specific source
        
        Args:
            source_id: ID of the source
            
        Returns:
            List of applicant dictionaries
            
        Raises:
            ValueError: If source_id is invalid
            SQLAlchemyError: On database errors
        """
        if not isinstance(source_id, int) or source_id <= 0:
            raise ValueError(f"Invalid source_id: {source_id}")
            
        try:
            query = select(self.tables['applicants']).where(
                self.tables['applicants'].c.source_id == source_id
            )
            async with self.engine.begin() as conn:
                result = await conn.execute(query)
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as e:
            logger.error(f"Database error in applicants_by_source: {e}")
            raise
    
    async def applicants_by_vacancy(self, vacancy_id: int) -> List[Dict]:
        """Get applicants linked to specific vacancy
        
        Args:
            vacancy_id: ID of the vacancy
            
        Returns:
            List of applicant dictionaries
            
        Raises:
            ValueError: If vacancy_id is invalid
            SQLAlchemyError: On database errors
        """
        if not isinstance(vacancy_id, int) or vacancy_id <= 0:
            raise ValueError(f"Invalid vacancy_id: {vacancy_id}")
            
        try:
            query = select(self.tables['applicants']).join(
                self.tables['applicant_links'],
                self.tables['applicants'].c.id == self.tables['applicant_links'].c.applicant_id
            ).where(
                self.tables['applicant_links'].c.vacancy == vacancy_id
            )
            async with self.engine.begin() as conn:
                result = await conn.execute(query)
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as e:
            logger.error(f"Database error in applicants_by_vacancy: {e}")
            raise
    
    async def applicants_by_recruiter(self, recruiter_id: int) -> List[Dict]:
        """Get applicants assigned to specific recruiter
        
        Args:
            recruiter_id: ID of the recruiter
            
        Returns:
            List of applicant dictionaries
            
        Raises:
            ValueError: If recruiter_id is invalid
            SQLAlchemyError: On database errors
        """
        if not isinstance(recruiter_id, int) or recruiter_id <= 0:
            raise ValueError(f"Invalid recruiter_id: {recruiter_id}")
            
        try:
            query = select(self.tables['applicants']).where(
                self.tables['applicants'].c.recruiter_id == recruiter_id
            )
            async with self.engine.begin() as conn:
                result = await conn.execute(query)
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as e:
            logger.error(f"Database error in applicants_by_recruiter: {e}")
            raise
    
    async def applicants_by_status(self, status_id: int) -> List[Dict]:
        """Get applicants in specific recruitment stage
        
        Args:
            status_id: ID of the status/stage
            
        Returns:
            List of applicant dictionaries
            
        Raises:
            ValueError: If status_id is invalid
            SQLAlchemyError: On database errors
        """
        if not isinstance(status_id, int) or status_id <= 0:
            raise ValueError(f"Invalid status_id: {status_id}")
            
        try:
            query = select(self.tables['applicants']).join(
                self.tables['applicant_links'],
                self.tables['applicants'].c.id == self.tables['applicant_links'].c.applicant_id
            ).where(
                self.tables['applicant_links'].c.status == status_id
            )
            async with self.engine.begin() as conn:
                result = await conn.execute(query)
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as e:
            logger.error(f"Database error in applicants_by_status: {e}")
            raise
    
    # Offer Views
    async def offers_by_status(self, status: str) -> List[Dict]:
        """Get offers filtered by status
        
        Args:
            status: Offer status to filter by
            
        Returns:
            List of offer dictionaries
            
        Raises:
            ValueError: If status is empty
            SQLAlchemyError: On database errors
        """
        if not status or not isinstance(status, str):
            raise ValueError("Status must be a non-empty string")
            
        try:
            query = select(self.tables['offers']).where(
                self.tables['offers'].c.status == status
            )
            async with self.engine.begin() as conn:
                result = await conn.execute(query)
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as e:
            logger.error(f"Database error in offers_by_status: {e}")
            raise
    
    async def offers_by_vacancy(self, vacancy_id: int) -> List[Dict]:
        """Get offers for specific vacancy
        
        Args:
            vacancy_id: ID of the vacancy
            
        Returns:
            List of offer dictionaries
            
        Raises:
            ValueError: If vacancy_id is invalid
            SQLAlchemyError: On database errors
        """
        if not isinstance(vacancy_id, int) or vacancy_id <= 0:
            raise ValueError(f"Invalid vacancy_id: {vacancy_id}")
            
        try:
            query = select(self.tables['offers']).where(
                self.tables['offers'].c.vacancy_id == vacancy_id
            )
            async with self.engine.begin() as conn:
                result = await conn.execute(query)
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as e:
            logger.error(f"Database error in offers_by_vacancy: {e}")
            raise
    
    async def offers_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get offers created within date range
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            List of offer dictionaries
            
        Raises:
            ValueError: If dates are invalid
            SQLAlchemyError: On database errors
        """
        if start_date > end_date:
            raise ValueError(f"start_date ({start_date}) must be before end_date ({end_date})")
            
        try:
            query = select(self.tables['offers']).where(
                between(self.tables['offers'].c.created, start_date, end_date)
            )
            async with self.engine.begin() as conn:
                result = await conn.execute(query)
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as e:
            logger.error(f"Database error in offers_by_date_range: {e}")
            raise
    
    # Source Analytics
    async def sources_by_type(self, source_type: str) -> List[Dict]:
        """Get sources filtered by type
        
        Args:
            source_type: Type of source to filter by
            
        Returns:
            List of source dictionaries
            
        Raises:
            ValueError: If source_type is empty
            SQLAlchemyError: On database errors
        """
        if not source_type or not isinstance(source_type, str):
            raise ValueError("Source type must be a non-empty string")
            
        try:
            query = select(self.tables['sources']).where(
                self.tables['sources'].c.type == source_type
            )
            async with self.engine.begin() as conn:
                result = await conn.execute(query)
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as e:
            logger.error(f"Database error in sources_by_type: {e}")
            raise
    
    # Rejection Analytics
    async def rejections_by_reason(self, reason_id: int) -> List[Dict]:
        """Get rejections by specific reason (from applicant logs)"""
        raise NotImplementedError("Rejection tracking requires log parsing implementation")
    
    async def rejections_by_stage(self, stage_id: int) -> List[Dict]:
        """Get rejections at specific stage (from applicant logs)"""
        raise NotImplementedError("Rejection tracking requires log parsing implementation")
    
    # Aggregated Views
    async def vacancy_funnel(self, vacancy_id: int) -> Dict[str, int]:
        """Get candidate counts by stage for a vacancy
        
        Args:
            vacancy_id: ID of the vacancy
            
        Returns:
            Dictionary mapping status IDs to candidate counts
            
        Raises:
            ValueError: If vacancy_id is invalid
            SQLAlchemyError: On database errors
        """
        if not isinstance(vacancy_id, int) or vacancy_id <= 0:
            raise ValueError(f"Invalid vacancy_id: {vacancy_id}")
            
        try:
            query = select(
                self.tables['applicant_links'].c.status,
                func.count(distinct(self.tables['applicant_links'].c.applicant_id)).label('count')
            ).where(
                self.tables['applicant_links'].c.vacancy == vacancy_id
            ).group_by(
                self.tables['applicant_links'].c.status
            )
            
            async with self.engine.begin() as conn:
                result = await conn.execute(query)
                return {str(row.status): row._mapping['count'] for row in result}
        except SQLAlchemyError as e:
            logger.error(f"Database error in vacancy_funnel: {e}")
            raise
    
    async def recruiter_performance(self, start_date: Optional[datetime] = None) -> List[Dict]:
        """Get recruiter performance metrics
        
        Args:
            start_date: Optional date to filter from
            
        Returns:
            List of recruiter performance dictionaries
            
        Raises:
            ValueError: If start_date is in the future
            SQLAlchemyError: On database errors
        """
        if start_date and start_date > datetime.now():
            raise ValueError("start_date cannot be in the future")
            
        try:
            base_query = select(
                self.tables['applicants'].c.recruiter_id,
                self.tables['recruiters'].c.name,
                func.count(distinct(self.tables['applicants'].c.id)).label('total_applicants')
            ).join(
                self.tables['recruiters'],
                self.tables['applicants'].c.recruiter_id == self.tables['recruiters'].c.id
            )
            
            if start_date:
                base_query = base_query.where(
                    self.tables['applicants'].c.created >= start_date
                )
            
            query = base_query.group_by(
                self.tables['applicants'].c.recruiter_id,
                self.tables['recruiters'].c.name
            ).order_by(
                func.count(distinct(self.tables['applicants'].c.id)).desc()
            )
            
            async with self.engine.begin() as conn:
                result = await conn.execute(query)
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as e:
            logger.error(f"Database error in recruiter_performance: {e}")
            raise
    
    async def source_effectiveness(self) -> List[Dict]:
        """Get source effectiveness metrics
        
        Returns:
            List of source dictionaries with applicant counts
            
        Raises:
            SQLAlchemyError: On database errors
        """
        try:
            query = select(
                self.tables['sources'].c.id,
                self.tables['sources'].c.name,
                self.tables['sources'].c.type,
                func.count(distinct(self.tables['applicants'].c.id)).label('total_applicants')
            ).join(
                self.tables['applicants'],
                self.tables['sources'].c.id == self.tables['applicants'].c.source_id
            ).group_by(
                self.tables['sources'].c.id,
                self.tables['sources'].c.name,
                self.tables['sources'].c.type
            ).order_by(
                func.count(distinct(self.tables['applicants'].c.id)).desc()
            )
            
            async with self.engine.begin() as conn:
                result = await conn.execute(query)
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as e:
            logger.error(f"Database error in source_effectiveness: {e}")
            raise