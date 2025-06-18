"""
Integration layer for metrics.py with the existing Huntflow system
Bridges HuntflowViews with the virtual engine and API endpoints
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from metrics import HuntflowViews
from schema import create_huntflow_tables
from sqlalchemy import MetaData
from async_engine_adapter import AsyncEngineAdapter
import logging

logger = logging.getLogger(__name__)


class MetricsIntegration:
    """Integrates HuntflowViews with the existing SQLAlchemy executor and app infrastructure"""
    
    def __init__(self, virtual_engine):
        """Initialize with virtual engine that connects to Huntflow API"""
        self.virtual_engine = virtual_engine
        
        # Create async adapter for the views
        self.async_engine = AsyncEngineAdapter(virtual_engine)
        
        # Create schema tables
        metadata = MetaData()
        self.tables = create_huntflow_tables(metadata)
        
        # Initialize views
        self.views = HuntflowViews(self.async_engine, self.tables)
    
    # Metric methods that can be called from app.py endpoints
    
    async def get_open_vacancies_count(self) -> int:
        """Get count of open vacancies"""
        vacancies = await self.views.vacancies_by_state('OPEN')
        return len(vacancies)
    
    async def get_vacancy_distribution(self) -> Dict[str, int]:
        """Get vacancy distribution by state"""
        states = ['OPEN', 'CLOSED', 'HOLD']
        distribution = {}
        
        for state in states:
            vacancies = await self.views.vacancies_by_state(state)
            distribution[state] = len(vacancies)
        
        return distribution
    
    async def get_applicants_by_source_chart(self) -> Dict[str, Any]:
        """Get chart data for applicants by source"""
        effectiveness = await self.views.source_effectiveness()
        
        # Sort by total_applicants descending
        effectiveness = sorted(effectiveness, key=lambda x: x['total_applicants'], reverse=True)
        
        # Take top 10 sources
        top_sources = effectiveness[:10]
        
        labels = [s['name'] for s in top_sources]
        values = [s['total_applicants'] for s in top_sources]
        
        return {
            "labels": labels,
            "values": values,
            "chart_type": "bar",
            "title": "Top 10 Applicant Sources"
        }
    
    async def get_vacancy_funnel_chart(self, vacancy_id: int) -> Dict[str, Any]:
        """Get funnel chart for a specific vacancy"""
        funnel_data = await self.views.vacancy_funnel(vacancy_id)
        
        # Need to get status names from mapping
        status_mapping = await self.virtual_engine._get_status_mapping()
        
        labels = []
        values = []
        
        for status_id, count in sorted(funnel_data.items()):
            status_info = status_mapping.get(int(status_id), {})
            status_name = status_info.get('name', f'Status {status_id}') if isinstance(status_info, dict) else str(status_info)
            labels.append(status_name)
            values.append(count)
        
        return {
            "labels": labels,
            "values": values,
            "chart_type": "funnel",
            "title": f"Recruitment Funnel for Vacancy {vacancy_id}"
        }
    
    async def get_recruiter_performance_data(self, days_back: int = 30) -> Dict[str, Any]:
        """Get recruiter performance metrics"""
        start_date = datetime.now() - timedelta(days=days_back)
        performance = await self.views.recruiter_performance(start_date=start_date)
        
        # Take top 10 recruiters
        top_recruiters = performance[:10]
        
        labels = [r['name'] for r in top_recruiters]
        values = [r['total_applicants'] for r in top_recruiters]
        
        return {
            "labels": labels,
            "values": values,
            "chart_type": "bar",
            "title": f"Top Recruiters (Last {days_back} Days)"
        }
    
    async def get_offers_summary(self) -> Dict[str, int]:
        """Get summary of offers by status"""
        statuses = ['pending', 'accepted', 'rejected', 'sent']
        summary = {}
        
        for status in statuses:
            try:
                offers = await self.views.offers_by_status(status)
                summary[status] = len(offers)
            except Exception as e:
                logger.warning(f"Error getting offers for status {status}: {e}")
                summary[status] = 0
        
        return summary
    
    async def get_recent_activity_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get metrics for recent activity"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get recent vacancies
        recent_vacancies = await self.views.vacancies_by_date_range(start_date, end_date)
        
        # Get recent offers
        recent_offers = await self.views.offers_by_date_range(start_date, end_date)
        
        return {
            "period_days": days,
            "new_vacancies": len(recent_vacancies),
            "new_offers": len(recent_offers),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
    
    async def search_vacancies_by_division(self, division_id: int) -> List[Dict[str, Any]]:
        """Get all vacancies for a specific division"""
        vacancies = await self.views.vacancies_by_division(division_id)
        
        # Enrich with division name if available
        divisions_map = await self.virtual_engine._get_divisions_mapping()
        division_name = divisions_map.get(division_id, f"Division {division_id}")
        
        for vacancy in vacancies:
            vacancy['division_name'] = division_name
        
        return vacancies
    
    async def get_pipeline_status_distribution(self) -> Dict[str, Any]:
        """Get distribution of candidates across pipeline stages"""
        # This would aggregate across all active vacancies
        open_vacancies = await self.views.vacancies_by_state('OPEN')
        
        total_distribution = {}
        
        for vacancy in open_vacancies[:10]:  # Limit to first 10 to avoid too many API calls
            try:
                funnel = await self.views.vacancy_funnel(vacancy['id'])
                for status_id, count in funnel.items():
                    total_distribution[status_id] = total_distribution.get(status_id, 0) + count
            except Exception as e:
                logger.warning(f"Error getting funnel for vacancy {vacancy['id']}: {e}")
        
        # Convert to chart format
        status_mapping = await self.virtual_engine._get_status_mapping()
        
        labels = []
        values = []
        
        for status_id, count in sorted(total_distribution.items()):
            status_info = status_mapping.get(int(status_id), {})
            status_name = status_info.get('name', f'Status {status_id}') if isinstance(status_info, dict) else str(status_info)
            labels.append(status_name)
            values.append(count)
        
        return {
            "labels": labels,
            "values": values,
            "chart_type": "bar",
            "title": "Candidate Distribution Across Pipeline Stages"
        }


# Extension to SQLAlchemyHuntflowExecutor to use metrics views
class EnhancedSQLAlchemyExecutor:
    """Enhanced executor that combines existing functionality with new metrics views"""
    
    def __init__(self, base_executor, metrics_integration):
        self.base_executor = base_executor
        self.metrics = metrics_integration
        
        # Delegate all base methods
        for attr in dir(base_executor):
            if not attr.startswith('_') and not hasattr(self, attr):
                setattr(self, attr, getattr(base_executor, attr))
    
    async def execute_view_query(self, view_name: str, **params) -> Union[List[Dict], Dict[str, Any]]:
        """Execute a query using the metrics views"""
        if not hasattr(self.metrics.views, view_name):
            raise ValueError(f"Unknown view: {view_name}")
        
        view_method = getattr(self.metrics.views, view_name)
        return await view_method(**params)
    
    async def get_advanced_metric(self, metric_name: str, **params) -> Any:
        """Get advanced metrics using the new views system"""
        metric_methods = {
            "open_vacancies_count": self.metrics.get_open_vacancies_count,
            "vacancy_distribution": self.metrics.get_vacancy_distribution,
            "applicants_by_source": self.metrics.get_applicants_by_source_chart,
            "recruiter_performance": self.metrics.get_recruiter_performance_data,
            "offers_summary": self.metrics.get_offers_summary,
            "recent_activity": self.metrics.get_recent_activity_metrics,
            "pipeline_distribution": self.metrics.get_pipeline_status_distribution
        }
        
        if metric_name not in metric_methods:
            # Fall back to base executor metrics
            return await self.base_executor.get_ready_metric(metric_name, **params)
        
        method = metric_methods[metric_name]
        return await method(**params)
    
    async def get_view_chart(self, chart_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Get chart data using views"""
        chart_type = chart_spec.get("type")
        
        if chart_type == "vacancy_funnel":
            vacancy_id = chart_spec.get("vacancy_id")
            if not vacancy_id:
                raise ValueError("vacancy_id required for funnel chart")
            return await self.metrics.get_vacancy_funnel_chart(vacancy_id)
        
        elif chart_type == "applicants_by_source":
            return await self.metrics.get_applicants_by_source_chart()
        
        elif chart_type == "recruiter_performance":
            days_back = chart_spec.get("days_back", 30)
            return await self.metrics.get_recruiter_performance_data(days_back)
        
        elif chart_type == "pipeline_distribution":
            return await self.metrics.get_pipeline_status_distribution()
        
        else:
            # Fall back to base chart methods
            return await self.base_executor.get_ready_chart(chart_type)