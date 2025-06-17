"""
Huntflow Ready-to-Use Metrics
Pre-computed metrics that SQLAlchemy can understand and compute under the hood
"""
from sqlalchemy import func, and_, or_, select, case
from sqlalchemy.sql import Select
from typing import Dict, Any, List, Optional
from virtual_engine import HuntflowVirtualEngine

# Public API exports
__all__ = [
    'HuntflowComputedMetrics',
    'HuntflowMetricsHelper'
]

class HuntflowComputedMetrics:
    """Ready-to-use metrics that the AI model can use when generating charts"""
    
    def __init__(self, engine: HuntflowVirtualEngine):
        self.engine = engine
        self.applicants = engine.applicants
        self.vacancies = engine.vacancies
        self.applicant_links = engine.applicant_links
        self.recruiters = engine.recruiters
        self.sources = engine.sources
    
    # ==================== BASIC COUNTS ====================
    
    async def active_candidates(self) -> int:
        """Active candidates — candidates that have a link to vacancies with the state OPEN"""
        # Get all open vacancy IDs first
        open_vacancies = await self.engine._execute_vacancies_query(None)
        open_vacancy_ids = {v['id'] for v in open_vacancies if v.get('state') == 'OPEN'}
        
        # Get applicants with their status info
        applicants_data = await self.engine._get_applicants_data()
        
        # Count applicants linked to open vacancies
        active_count = 0
        for applicant in applicants_data:
            vacancy_id = applicant.get('vacancy_id', 0)
            if vacancy_id in open_vacancy_ids:
                active_count += 1
        
        return active_count
    
    async def open_vacancies(self) -> int:
        """Open vacancies — vacancies that have state OPEN"""
        vacancies_data = await self.engine._execute_vacancies_query(None)
        return len([v for v in vacancies_data if v.get('state') == 'OPEN'])
    
    async def closed_vacancies(self) -> int:
        """Closed vacancies — vacancies that have state CLOSED"""
        vacancies_data = await self.engine._execute_vacancies_query(None)
        return len([v for v in vacancies_data if v.get('state') == 'CLOSED'])
    
    async def active_statuses(self) -> List[Dict[str, Any]]:
        """Active statuses — statuses within status_groups that are used in vacancies with status OPEN"""
        # Get open vacancies
        open_vacancies = await self.engine._execute_vacancies_query(None)
        open_vacancy_ids = {v['id'] for v in open_vacancies if v.get('state') == 'OPEN'}
        
        # Get applicants with their status info
        applicants_data = await self.engine._get_applicants_data()
        status_mapping = await self.engine._get_status_mapping()
        
        # Find statuses used by applicants in open vacancies
        active_status_ids = set()
        for applicant in applicants_data:
            vacancy_id = applicant.get('vacancy_id', 0)
            status_id = applicant.get('status_id', 0)
            if vacancy_id in open_vacancy_ids and status_id:
                active_status_ids.add(status_id)
        
        # Return status info for active statuses
        active_statuses = []
        for status_id in active_status_ids:
            status_info = status_mapping.get(status_id, {'name': f'Status {status_id}'})
            active_statuses.append({
                'id': status_id,
                'name': status_info.get('name', f'Status {status_id}'),
                'type': status_info.get('type', ''),
                'order': status_info.get('order', 0)
            })
        
        return sorted(active_statuses, key=lambda x: x['order'])
    
    async def get_recruiters(self) -> List[Dict[str, Any]]:
        """Recruiters — users with type 'owner' and 'manager'"""
        recruiters_data = await self.engine._execute_recruiters_query(None)
        return [r for r in recruiters_data if r.get('type') in ['owner', 'manager']]
    
    # ==================== RECRUITER-SPECIFIC METRICS ====================
    
    async def vacancies_by_recruiter(self, recruiter_id: int) -> int:
        """Vacancies with %recruiter_id% — all vacancies that contain %recruiter_id% in coworkers field"""
        vacancies_data = await self.engine._execute_vacancies_query(None)
        
        count = 0
        for vacancy in vacancies_data:
            coworkers_str = vacancy.get('coworkers', '[]')
            if str(recruiter_id) in coworkers_str:
                count += 1
        
        return count
    
    async def hirings_by_recruiter(self, recruiter_id: int) -> int:
        """Hirings by %recruiter_id% — number of applicants that moved to hired status in vacancies by %recruiter_id%"""
        # Get vacancies for this recruiter
        vacancies_data = await self.engine._execute_vacancies_query(None)
        recruiter_vacancy_ids = set()
        
        for vacancy in vacancies_data:
            coworkers_str = vacancy.get('coworkers', '[]')
            if str(recruiter_id) in coworkers_str:
                recruiter_vacancy_ids.add(vacancy['id'])
        
        # Get applicants in hired status in these vacancies
        applicants_data = await self.engine._get_applicants_data()
        status_mapping = await self.engine._get_status_mapping()
        
        # Find hired status IDs
        hired_status_ids = set()
        for status_id, status_info in status_mapping.items():
            status_name = status_info.get('name', '').lower()
            if any(word in status_name for word in ['принят', 'hired', 'offer accepted', 'оффер принят']):
                hired_status_ids.add(status_id)
        
        # Count hired applicants in recruiter's vacancies
        hired_count = 0
        for applicant in applicants_data:
            vacancy_id = applicant.get('vacancy_id', 0)
            status_id = applicant.get('status_id', 0)
            if vacancy_id in recruiter_vacancy_ids and status_id in hired_status_ids:
                hired_count += 1
        
        return hired_count
    
    # ==================== SOURCE-SPECIFIC METRICS ====================
    
    async def applicants_by_source(self, source_id: int) -> int:
        """Applicants by %source_id% — applicants with external account_source = %source_id%"""
        applicants_data = await self.engine._get_applicants_data()
        return len([a for a in applicants_data if a.get('source_id') == source_id])
    
    # ==================== CHART DATA GENERATORS ====================
    
    async def active_candidates_by_status_chart(self) -> Dict[str, Any]:
        """Chart data for active candidates grouped by status"""
        # Get open vacancy IDs
        open_vacancies = await self.engine._execute_vacancies_query(None)
        open_vacancy_ids = {v['id'] for v in open_vacancies if v.get('state') == 'OPEN'}
        
        # Get applicants with their status info
        applicants_data = await self.engine._get_applicants_data()
        status_mapping = await self.engine._get_status_mapping()
        
        # Count active candidates by status
        status_counts = {}
        for applicant in applicants_data:
            vacancy_id = applicant.get('vacancy_id', 0)
            status_id = applicant.get('status_id', 0)
            
            if vacancy_id in open_vacancy_ids and status_id:
                status_info = status_mapping.get(status_id, {'name': f'Status {status_id}'})
                status_name = status_info.get('name', f'Status {status_id}')
                status_counts[status_name] = status_counts.get(status_name, 0) + 1
        
        # Sort by count
        sorted_statuses = sorted(status_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "labels": [status for status, count in sorted_statuses],
            "values": [count for status, count in sorted_statuses],
            "title": "Active Candidates by Status"
        }
    
    async def vacancy_states_chart(self) -> Dict[str, Any]:
        """Chart data for vacancy distribution by state"""
        vacancies_data = await self.engine._execute_vacancies_query(None)
        
        state_counts = {}
        for vacancy in vacancies_data:
            state = vacancy.get('state', 'Unknown')
            state_counts[state] = state_counts.get(state, 0) + 1
        
        return {
            "labels": list(state_counts.keys()),
            "values": list(state_counts.values()),
            "title": "Vacancies by State"
        }
    
    async def recruiter_performance_chart(self) -> Dict[str, Any]:
        """Chart data for recruiter performance (hirings)"""
        recruiters_data = await self.get_recruiters()
        
        performance_data = []
        for recruiter in recruiters_data:
            recruiter_id = recruiter['id']
            hirings = await self.hirings_by_recruiter(recruiter_id)
            if hirings > 0:  # Only include recruiters with hirings
                performance_data.append({
                    'name': recruiter['name'],
                    'hirings': hirings
                })
        
        # Sort by hirings
        performance_data.sort(key=lambda x: x['hirings'], reverse=True)
        
        # Take top 10
        top_performers = performance_data[:10]
        
        return {
            "labels": [r['name'] for r in top_performers],
            "values": [r['hirings'] for r in top_performers],
            "title": "Top Recruiters by Hirings"
        }
    
    async def applicants_by_source_chart(self) -> Dict[str, Any]:
        """Chart data for applicants distribution by source"""
        sources_mapping = await self.engine._get_sources_mapping()
        applicants_data = await self.engine._get_applicants_data()
        
        source_counts = {}
        for applicant in applicants_data:
            source_id = applicant.get('source_id', 0)
            if source_id and source_id in sources_mapping:
                source_name = sources_mapping[source_id]
                source_counts[source_name] = source_counts.get(source_name, 0) + 1
        
        # Sort by count and take top 10
        sorted_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "labels": [source for source, count in sorted_sources],
            "values": [count for source, count in sorted_sources],
            "title": "Top Sources of Applicants"
        }
    
    # ==================== COMPREHENSIVE METRICS ====================
    
    async def get_all_key_metrics(self) -> Dict[str, Any]:
        """Get all key metrics in one call for dashboard"""
        return {
            "active_candidates": await self.active_candidates(),
            "open_vacancies": await self.open_vacancies(),
            "closed_vacancies": await self.closed_vacancies(),
            "total_vacancies": await self.open_vacancies() + await self.closed_vacancies(),
            "active_statuses_count": len(await self.active_statuses()),
            "recruiters_count": len(await self.get_recruiters())
        }
    
    async def get_all_chart_data(self) -> Dict[str, Any]:
        """Get all chart data in one call"""
        return {
            "active_candidates_by_status": await self.active_candidates_by_status_chart(),
            "vacancy_states": await self.vacancy_states_chart(),
            "recruiter_performance": await self.recruiter_performance_chart(),
            "applicants_by_source": await self.applicants_by_source_chart()
        }


class HuntflowMetricsHelper:
    """Helper class to integrate metrics with existing executor"""
    
    def __init__(self, executor):
        self.executor = executor
        self.metrics = HuntflowComputedMetrics(executor.engine)
    
    async def execute_metric(self, metric_name: str, **kwargs) -> Any:
        """Execute a specific metric by name"""
        if hasattr(self.metrics, metric_name):
            method = getattr(self.metrics, metric_name)
            return await method(**kwargs)
        else:
            raise ValueError(f"Unknown metric: {metric_name}")
    
    async def get_metric_chart_data(self, chart_type: str) -> Dict[str, Any]:
        """Get chart data for specific metric"""
        chart_methods = {
            "active_candidates_by_status": self.metrics.active_candidates_by_status_chart,
            "vacancy_states": self.metrics.vacancy_states_chart,
            "recruiter_performance": self.metrics.recruiter_performance_chart,
            "applicants_by_source": self.metrics.applicants_by_source_chart
        }
        
        if chart_type in chart_methods:
            return await chart_methods[chart_type]()
        else:
            raise ValueError(f"Unknown chart type: {chart_type}")