"""
Huntflow Analytics Templates and Reports
Pre-built analytics queries using SQLAlchemy expressions for common reporting needs
"""
from typing import Dict, Any
import asyncio
import logging

logger = logging.getLogger(__name__)

# Predefined Query Templates for Common Analytics
class HuntflowAnalyticsTemplates:
    """Pre-built analytics queries using SQLAlchemy expressions"""
    
    def __init__(self, executor):
        self.executor = executor
        self.builder = executor.builder
    
    async def recruiter_performance_report(self) -> Dict[str, Any]:
        """Generate complete recruiter performance report"""
        
        # Get recruiter hire counts from applicants with hired status
        # Status information now comes from applicant_links table
        applicants_data = await self.executor.engine._get_applicants_data()
        
        # Use robust hired status detection (replaces fragile string matching)
        hired_status_ids = await self.executor.get_hired_status_ids()
        
        # Use thread pool for CPU-intensive recruiter stats calculation on large datasets
        if len(applicants_data) > 1000:
            logger.debug(f"Processing recruiter stats for {len(applicants_data)} applicants in thread pool")
            # Import here to avoid circular imports
            from sqlalchemy_executor import SQLAlchemyHuntflowExecutor
            return await asyncio.to_thread(
                SQLAlchemyHuntflowExecutor._calculate_recruiter_stats_cpu,
                applicants_data, hired_status_ids
            )
        else:
            # Import here to avoid circular imports  
            from sqlalchemy_executor import SQLAlchemyHuntflowExecutor
            return SQLAlchemyHuntflowExecutor._calculate_recruiter_stats_cpu(applicants_data, hired_status_ids)