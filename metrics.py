"""
Huntflow Analytics Views
Auto-generated view definitions for analytical queries
"""

from typing import Dict, Any, List, Optional
from sqlalchemy import select, func, between, distinct
from sqlalchemy.ext.asyncio import AsyncEngine
from datetime import datetime


class HuntflowViews:
    """SQL view definitions for Huntflow analytics"""
    
    def __init__(self, engine: AsyncEngine, tables: Dict[str, Any]):
        self.engine = engine
        self.tables = tables
    
    # Vacancy Views
    async def vacancies_by_state(self, state: str) -> List[Dict]:
        """Get vacancies filtered by state (OPEN, CLOSED, HOLD)"""
        query = select(self.tables['vacancies']).where(
            self.tables['vacancies'].c.state == state
        )
        async with self.engine.begin() as conn:
            result = await conn.execute(query)
            return [dict(row._mapping) for row in result]
    
    async def vacancies_by_recruiter(self, recruiter_id: int) -> List[Dict]:
        """Get vacancies assigned to specific recruiter (via coworkers JSON)"""
        # Using PostgreSQL JSONB operators for efficient search
        query = select(self.tables['vacancies']).where(
            self.tables['vacancies'].c.coworkers.op('@>')([{'id': recruiter_id}])
        )
        async with self.engine.begin() as conn:
            result = await conn.execute(query)
            return [dict(row._mapping) for row in result]
    
    async def vacancies_by_division(self, division_id: int) -> List[Dict]:
        """Get vacancies by account division"""
        query = select(self.tables['vacancies']).where(
            self.tables['vacancies'].c.account_division == division_id
        )
        async with self.engine.begin() as conn:
            result = await conn.execute(query)
            return [dict(row._mapping) for row in result]
    
    async def vacancies_by_date_range(self, start_date: datetime, end_date: datetime, date_field: str = 'created') -> List[Dict]:
        """Get vacancies within date range (created, updated, or custom field)"""
        column = getattr(self.tables['vacancies'].c, date_field)
        query = select(self.tables['vacancies']).where(
            between(column, start_date, end_date)
        )
        async with self.engine.begin() as conn:
            result = await conn.execute(query)
            return [dict(row._mapping) for row in result]
    
    # Applicant Views
    async def applicants_by_source(self, source_id: int) -> List[Dict]:
        """Get applicants from specific source"""
        query = select(self.tables['applicants']).where(
            self.tables['applicants'].c.source_id == source_id
        )
        async with self.engine.begin() as conn:
            result = await conn.execute(query)
            return [dict(row._mapping) for row in result]
    
    async def applicants_by_vacancy(self, vacancy_id: int) -> List[Dict]:
        """Get applicants linked to specific vacancy"""
        query = select(self.tables['applicants']).join(
            self.tables['applicant_links'],
            self.tables['applicants'].c.id == self.tables['applicant_links'].c.applicant_id
        ).where(
            self.tables['applicant_links'].c.vacancy == vacancy_id
        )
        async with self.engine.begin() as conn:
            result = await conn.execute(query)
            return [dict(row._mapping) for row in result]
    
    async def applicants_by_recruiter(self, recruiter_id: int) -> List[Dict]:
        """Get applicants assigned to specific recruiter"""
        query = select(self.tables['applicants']).where(
            self.tables['applicants'].c.recruiter_id == recruiter_id
        )
        async with self.engine.begin() as conn:
            result = await conn.execute(query)
            return [dict(row._mapping) for row in result]
    
    async def applicants_by_status(self, status_id: int) -> List[Dict]:
        """Get applicants in specific recruitment stage"""
        query = select(self.tables['applicants']).join(
            self.tables['applicant_links'],
            self.tables['applicants'].c.id == self.tables['applicant_links'].c.applicant_id
        ).where(
            self.tables['applicant_links'].c.status == status_id
        )
        async with self.engine.begin() as conn:
            result = await conn.execute(query)
            return [dict(row._mapping) for row in result]
    
    # Offer Views
    async def offers_by_status(self, status: str) -> List[Dict]:
        """Get offers filtered by status"""
        query = select(self.tables['offers']).where(
            self.tables['offers'].c.status == status
        )
        async with self.engine.begin() as conn:
            result = await conn.execute(query)
            return [dict(row._mapping) for row in result]
    
    async def offers_by_vacancy(self, vacancy_id: int) -> List[Dict]:
        """Get offers for specific vacancy"""
        query = select(self.tables['offers']).where(
            self.tables['offers'].c.vacancy_id == vacancy_id
        )
        async with self.engine.begin() as conn:
            result = await conn.execute(query)
            return [dict(row._mapping) for row in result]
    
    async def offers_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get offers created within date range"""
        query = select(self.tables['offers']).where(
            between(self.tables['offers'].c.created, start_date, end_date)
        )
        async with self.engine.begin() as conn:
            result = await conn.execute(query)
            return [dict(row._mapping) for row in result]
    
    # Source Analytics
    async def sources_by_type(self, source_type: str) -> List[Dict]:
        """Get sources filtered by type"""
        query = select(self.tables['sources']).where(
            self.tables['sources'].c.type == source_type
        )
        async with self.engine.begin() as conn:
            result = await conn.execute(query)
            return [dict(row._mapping) for row in result]
    
    # Rejection Analytics
    async def rejections_by_reason(self, reason_id: int) -> List[Dict]:
        """Get rejections by specific reason (from applicant logs)"""
        raise NotImplementedError("Rejection tracking requires log parsing implementation")
    
    async def rejections_by_stage(self, stage_id: int) -> List[Dict]:
        """Get rejections at specific stage (from applicant logs)"""
        raise NotImplementedError("Rejection tracking requires log parsing implementation")
    
    # Aggregated Views
    async def vacancy_funnel(self, vacancy_id: int) -> Dict[str, int]:
        """Get candidate counts by stage for a vacancy"""
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
    
    async def recruiter_performance(self, start_date: Optional[datetime] = None) -> List[Dict]:
        """Get recruiter performance metrics"""
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
    
    async def source_effectiveness(self) -> List[Dict]:
        """Get source effectiveness metrics"""
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