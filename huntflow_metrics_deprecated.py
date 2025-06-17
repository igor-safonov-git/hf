"""
Huntflow Ready-to-Use Metrics
Pre-computed metrics that SQLAlchemy can understand and compute under the hood
"""
from sqlalchemy import func, and_, or_, select, case
from sqlalchemy.sql import Select
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
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
        """Active candidates — candidates that have at least one link to vacancies with state OPEN"""
        # Get all open vacancy IDs first
        open_vacancies = await self.engine._execute_vacancies_query(None)
        open_vacancy_ids = {v['id'] for v in open_vacancies if v.get('state') == 'OPEN'}
        
        # Get applicants with their links info
        applicants_data = await self.engine._get_applicants_data()
        
        # Count unique applicants with at least one link to open vacancies
        active_candidate_ids = set()
        for applicant in applicants_data:
            applicant_id = applicant.get('id')
            if not applicant_id:
                continue
                
            # Check if applicant has any links to open vacancies
            links = applicant.get('links', [])
            for link in links:
                link_vacancy_id = link.get('vacancy')  # API uses 'vacancy' not 'vacancy_id'
                if link_vacancy_id in open_vacancy_ids:
                    active_candidate_ids.add(applicant_id)
                    break  # Found at least one active link, count this candidate
        
        return len(active_candidate_ids)
    
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
        
        # Find hired status IDs using robust type field detection
        hired_status_ids = set()
        for status_id, status_info in status_mapping.items():
            if isinstance(status_info, dict):
                status_type = status_info.get('type', '').lower()
                if status_type == 'hired':
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
        
        count = 0
        for applicant in applicants_data:
            # Extract source_id from external array (actual data structure)
            external_array = applicant.get('external', [])
            if external_array and isinstance(external_array, list):
                for external in external_array:
                    if external.get('account_source') == source_id:
                        count += 1
                        break
        
        return count
    
    # ==================== CHART DATA GENERATORS ====================
    
    async def active_candidates_by_status_chart(self) -> Dict[str, Any]:
        """Chart data for active candidates grouped by status - uses links array for accurate counts"""
        # Get open vacancy IDs
        open_vacancies = await self.engine._execute_vacancies_query(None)
        open_vacancy_ids = {v['id'] for v in open_vacancies if v.get('state') == 'OPEN'}
        
        # Get applicants with their links info
        applicants_data = await self.engine._get_applicants_data()
        status_mapping = await self.engine._get_status_mapping()
        
        # Count active links by status ID (preserves distinct statuses)
        status_id_counts = {}
        for applicant in applicants_data:
            # Process all links, not just primary vacancy
            links = applicant.get('links', [])
            for link in links:
                link_vacancy_id = link.get('vacancy')  # API uses 'vacancy' not 'vacancy_id'
                link_status_id = link.get('status')    # API uses 'status' not 'status_id'
                
                # Only count links to open vacancies, group by status ID
                if link_vacancy_id in open_vacancy_ids and link_status_id:
                    status_id_counts[link_status_id] = status_id_counts.get(link_status_id, 0) + 1
        
        # Use chart helper to convert status IDs to names and sort
        from chart_helpers import build_status_chart_data_cpu
        chart_data = build_status_chart_data_cpu(status_id_counts, status_mapping)
        
        return {
            "labels": chart_data["labels"],
            "values": chart_data["values"],
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
            # Extract source_id from external array (actual data structure)
            source_id = None
            external_array = applicant.get('external', [])
            if external_array and isinstance(external_array, list):
                for external in external_array:
                    if external.get('account_source'):
                        source_id = external.get('account_source')
                        break
            
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
    
    # ==================== ADVANCED CALCULATED METRICS ====================
    
    async def time_to_fill(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> float:
        """
        Time to Fill - Average days from vacancy start to close
        NOTE: Huntflow API doesn't track close dates for vacancies (updated=None for all closed)
        As workaround, estimate based on most recent hire in that vacancy
        """
        vacancies_data = await self.engine._execute_vacancies_query(None)
        applicants_data = await self.engine._get_applicants_data()
        status_mapping = await self.engine._get_status_mapping()
        
        # Find hired status IDs
        hired_status_ids = set()
        for status_id, status_info in status_mapping.items():
            if isinstance(status_info, dict):
                status_type = status_info.get('type', '').lower()
                if status_type == 'hired':
                    hired_status_ids.add(status_id)
        
        total_days = 0
        filled_count = 0
        
        # For each closed vacancy, find the most recent hire
        closed_vacancies = [v for v in vacancies_data if v.get('state') == 'CLOSED']
        
        for vacancy in closed_vacancies:
            vacancy_id = vacancy.get('id')
            created_str = vacancy.get('created')
            
            if not created_str:
                continue
            
            try:
                created_date = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                
                # Find most recent hire in this vacancy
                latest_hire_date = None
                
                for applicant in applicants_data:
                    links = applicant.get('links', [])
                    for link in links:
                        if (link.get('vacancy') == vacancy_id and 
                            link.get('status') in hired_status_ids):
                            
                            hire_date_str = link.get('updated') or link.get('changed')
                            if hire_date_str:
                                hire_date = datetime.fromisoformat(hire_date_str.replace('Z', '+00:00'))
                                if not latest_hire_date or hire_date > latest_hire_date:
                                    latest_hire_date = hire_date
                
                # If we found a hire, calculate time to fill
                if latest_hire_date:
                    days_diff = (latest_hire_date - created_date).days
                    if days_diff >= 0:
                        total_days += days_diff
                        filled_count += 1
                        
            except (ValueError, TypeError):
                continue
        
        return total_days / filled_count if filled_count > 0 else 0.0
    
    async def time_to_hire(self, days_back: int = 90) -> float:
        """
        Time to Hire - Using applicant_logs(applicant_id, status, ts), calculate mean days 
        between first status='created' and first status='hired' for applicants hired in last N days
        """
        # Get cutoff date
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Get applicants data with status info
        applicants_data = await self.engine._get_applicants_data()
        status_mapping = await self.engine._get_status_mapping()
        
        # Find hired status IDs using robust type field detection
        hired_status_ids = set()
        for status_id, status_info in status_mapping.items():
            if isinstance(status_info, dict):
                status_type = status_info.get('type', '').lower()
                if status_type == 'hired':
                    hired_status_ids.add(status_id)
        
        hire_times = []
        
        for applicant in applicants_data:
            # Check if applicant is in hired status
            current_status = applicant.get('status_id')
            if current_status not in hired_status_ids:
                continue
            
            # Get created date
            created_str = applicant.get('created')
            if not created_str:
                continue
            
            try:
                created_date = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                
                # For now, use the most recent link update as "hire date"
                # In real implementation, would need applicant_logs endpoint
                links = applicant.get('links', [])
                hire_date = None
                
                for link in links:
                    if link.get('status') in hired_status_ids:
                        link_updated = link.get('updated') or link.get('changed')
                        if link_updated:
                            link_date = datetime.fromisoformat(link_updated.replace('Z', '+00:00'))
                            if link_date >= cutoff_date:
                                if not hire_date or link_date > hire_date:
                                    hire_date = link_date
                
                if hire_date:
                    days_to_hire = (hire_date - created_date).days
                    if days_to_hire >= 0:
                        hire_times.append(days_to_hire)
                        
            except (ValueError, TypeError):
                continue
        
        return sum(hire_times) / len(hire_times) if hire_times else 0.0
    
    async def source_effectiveness(self) -> List[Dict[str, Any]]:
        """
        Source/Channel Effectiveness - Given applicants(id, source_id) + applicant_logs(status), 
        output hires per source_id and conversion rate (hires ÷ applicants), ordered desc by conversion
        """
        applicants_data = await self.engine._get_applicants_data()
        status_mapping = await self.engine._get_status_mapping()
        sources_mapping = await self.engine._get_sources_mapping()
        
        # Find hired status IDs using robust type field detection
        hired_status_ids = set()
        for status_id, status_info in status_mapping.items():
            if isinstance(status_info, dict):
                status_type = status_info.get('type', '').lower()
                if status_type == 'hired':
                    hired_status_ids.add(status_id)
        
        # Count applicants and hires by source
        source_stats = {}
        
        for applicant in applicants_data:
            # Extract source_id from external array (actual data structure)
            source_id = None
            external_array = applicant.get('external', [])
            if external_array and isinstance(external_array, list):
                for external in external_array:
                    if external.get('account_source'):
                        source_id = external.get('account_source')
                        break
            
            # Get current status from links
            status_id = None
            links = applicant.get('links', [])
            if links:
                # Use the first link's status as current status
                status_id = links[0].get('status')
            
            if not source_id or source_id not in sources_mapping:
                continue
            
            source_name = sources_mapping[source_id]
            
            if source_name not in source_stats:
                source_stats[source_name] = {'total_applicants': 0, 'hires': 0, 'source_id': source_id}
            
            source_stats[source_name]['total_applicants'] += 1
            
            if status_id in hired_status_ids:
                source_stats[source_name]['hires'] += 1
        
        # Calculate conversion rates
        effectiveness_data = []
        for source_name, stats in source_stats.items():
            if stats['total_applicants'] > 0:
                conversion_rate = stats['hires'] / stats['total_applicants']
                effectiveness_data.append({
                    'source_name': source_name,
                    'source_id': stats['source_id'],
                    'total_applicants': stats['total_applicants'],
                    'hires': stats['hires'],
                    'conversion_rate': round(conversion_rate * 100, 2)  # Percentage
                })
        
        # Sort by conversion rate descending
        effectiveness_data.sort(key=lambda x: x['conversion_rate'], reverse=True)
        
        return effectiveness_data
    
    async def applicants_per_opening(self) -> List[Dict[str, Any]]:
        """
        Applicants per Opening - Return table of vacancy_id, COUNT(applicant_id) 
        from applicants grouped by vacancy, limited to currently open vacancies
        """
        # Get open vacancies
        vacancies_data = await self.engine._execute_vacancies_query(None)
        open_vacancies = [v for v in vacancies_data if v.get('state') == 'OPEN']
        open_vacancy_ids = {v['id'] for v in open_vacancies}
        
        # Get applicants with their links
        applicants_data = await self.engine._get_applicants_data()
        
        # Count applicants per open vacancy
        vacancy_applicant_counts = {}
        
        for applicant in applicants_data:
            links = applicant.get('links', [])
            for link in links:
                vacancy_id = link.get('vacancy')
                if vacancy_id in open_vacancy_ids:
                    if vacancy_id not in vacancy_applicant_counts:
                        vacancy_applicant_counts[vacancy_id] = 0
                    vacancy_applicant_counts[vacancy_id] += 1
        
        # Build result with vacancy details
        result = []
        vacancy_lookup = {v['id']: v for v in open_vacancies}
        
        for vacancy_id, applicant_count in vacancy_applicant_counts.items():
            vacancy_info = vacancy_lookup.get(vacancy_id, {})
            result.append({
                'vacancy_id': vacancy_id,
                'position': vacancy_info.get('position', 'Unknown Position'),
                'applicant_count': applicant_count
            })
        
        # Sort by applicant count descending
        result.sort(key=lambda x: x['applicant_count'], reverse=True)
        
        return result
    
    async def application_to_interview_ratio(self) -> List[Dict[str, Any]]:
        """
        Application-to-Interview Ratio - From applicant_logs, count for each vacancy: 
        (a) total applicants and (b) applicants with at least one status='interview' log; 
        output (b ÷ a) as the ratio
        """
        # Get all vacancies
        vacancies_data = await self.engine._execute_vacancies_query(None)
        applicants_data = await self.engine._get_applicants_data()
        status_mapping = await self.engine._get_status_mapping()
        
        # Find interview status IDs
        interview_status_ids = set()
        for status_id, status_info in status_mapping.items():
            status_name = status_info.get('name', '').lower()
            if any(word in status_name for word in ['интервью', 'interview', 'собеседование']):
                interview_status_ids.add(status_id)
        
        # Count applicants per vacancy
        vacancy_stats = {}
        
        for applicant in applicants_data:
            links = applicant.get('links', [])
            current_status = applicant.get('status_id', 0)
            
            for link in links:
                vacancy_id = link.get('vacancy')
                if not vacancy_id:
                    continue
                
                if vacancy_id not in vacancy_stats:
                    vacancy_stats[vacancy_id] = {'total_applicants': 0, 'interviewed': 0}
                
                vacancy_stats[vacancy_id]['total_applicants'] += 1
                
                # Check if this applicant has interview status
                if current_status in interview_status_ids or link.get('status') in interview_status_ids:
                    vacancy_stats[vacancy_id]['interviewed'] += 1
        
        # Calculate ratios
        result = []
        vacancy_lookup = {v['id']: v for v in vacancies_data}
        
        for vacancy_id, stats in vacancy_stats.items():
            if stats['total_applicants'] > 0:
                ratio = stats['interviewed'] / stats['total_applicants']
                vacancy_info = vacancy_lookup.get(vacancy_id, {})
                
                result.append({
                    'vacancy_id': vacancy_id,
                    'position': vacancy_info.get('position', 'Unknown Position'),
                    'total_applicants': stats['total_applicants'],
                    'interviewed': stats['interviewed'],
                    'interview_ratio': round(ratio * 100, 2)  # Percentage
                })
        
        # Sort by interview ratio descending
        result.sort(key=lambda x: x['interview_ratio'], reverse=True)
        
        return result
    
    async def interview_to_offer_ratio(self) -> List[Dict[str, Any]]:
        """
        Interview-to-Offer Ratio - For each vacancy, count applicants with status='interview' 
        and those who reach status='offer'; return (offers ÷ interviews)
        """
        vacancies_data = await self.engine._execute_vacancies_query(None)
        applicants_data = await self.engine._get_applicants_data()
        status_mapping = await self.engine._get_status_mapping()
        
        # Find interview and offer status IDs
        interview_status_ids = set()
        offer_status_ids = set()
        
        for status_id, status_info in status_mapping.items():
            status_name = status_info.get('name', '').lower()
            if any(word in status_name for word in ['интервью', 'interview', 'собеседование']):
                interview_status_ids.add(status_id)
            elif any(word in status_name for word in ['оффер', 'offer', 'предложение']):
                offer_status_ids.add(status_id)
        
        # Count interviews and offers per vacancy
        vacancy_stats = {}
        
        for applicant in applicants_data:
            links = applicant.get('links', [])
            current_status = applicant.get('status_id', 0)
            
            for link in links:
                vacancy_id = link.get('vacancy')
                if not vacancy_id:
                    continue
                
                if vacancy_id not in vacancy_stats:
                    vacancy_stats[vacancy_id] = {'interviews': 0, 'offers': 0}
                
                # Check statuses
                link_status = link.get('status', 0)
                
                if current_status in interview_status_ids or link_status in interview_status_ids:
                    vacancy_stats[vacancy_id]['interviews'] += 1
                
                if current_status in offer_status_ids or link_status in offer_status_ids:
                    vacancy_stats[vacancy_id]['offers'] += 1
        
        # Calculate ratios
        result = []
        vacancy_lookup = {v['id']: v for v in vacancies_data}
        
        for vacancy_id, stats in vacancy_stats.items():
            if stats['interviews'] > 0:
                ratio = stats['offers'] / stats['interviews']
                vacancy_info = vacancy_lookup.get(vacancy_id, {})
                
                result.append({
                    'vacancy_id': vacancy_id,
                    'position': vacancy_info.get('position', 'Unknown Position'),
                    'interviews': stats['interviews'],
                    'offers': stats['offers'],
                    'offer_ratio': round(ratio * 100, 2)  # Percentage
                })
        
        # Sort by offer ratio descending
        result.sort(key=lambda x: x['offer_ratio'], reverse=True)
        
        return result
    
    async def offer_acceptance_rate(self, months_back: int = 12) -> List[Dict[str, Any]]:
        """
        Offer Acceptance Rate - Compute offers_sent vs offers_accepted where offers_accepted 
        equals logs containing status='hired'; output acceptance % per month for the last year
        """
        # Get cutoff date
        cutoff_date = datetime.now() - timedelta(days=months_back * 30)
        
        applicants_data = await self.engine._get_applicants_data()
        status_mapping = await self.engine._get_status_mapping()
        
        # Find offer and hired status IDs
        offer_status_ids = set()
        hired_status_ids = set()
        
        for status_id, status_info in status_mapping.items():
            if isinstance(status_info, dict):
                status_name = status_info.get('name', '').lower()
                status_type = status_info.get('type', '').lower()
                
                # Use robust type detection for hired statuses
                if status_type == 'hired':
                    hired_status_ids.add(status_id)
                # Keep pattern matching for offer statuses (user-defined)
                elif any(word in status_name for word in ['оффер', 'offer', 'предложение']):
                    offer_status_ids.add(status_id)
        
        # Count offers and acceptances by month
        monthly_stats = {}
        
        for applicant in applicants_data:
            links = applicant.get('links', [])
            current_status = applicant.get('status_id', 0)
            
            for link in links:
                link_updated = link.get('updated') or link.get('changed')
                if not link_updated:
                    continue
                
                try:
                    update_date = datetime.fromisoformat(link_updated.replace('Z', '+00:00'))
                    if update_date < cutoff_date:
                        continue
                    
                    month_key = update_date.strftime('%Y-%m')
                    
                    if month_key not in monthly_stats:
                        monthly_stats[month_key] = {'offers_sent': 0, 'offers_accepted': 0}
                    
                    link_status = link.get('status', 0)
                    
                    if link_status in offer_status_ids:
                        monthly_stats[month_key]['offers_sent'] += 1
                    
                    if current_status in hired_status_ids or link_status in hired_status_ids:
                        monthly_stats[month_key]['offers_accepted'] += 1
                        
                except (ValueError, TypeError):
                    continue
        
        # Calculate acceptance rates
        result = []
        for month, stats in sorted(monthly_stats.items()):
            if stats['offers_sent'] > 0:
                acceptance_rate = stats['offers_accepted'] / stats['offers_sent']
                result.append({
                    'month': month,
                    'offers_sent': stats['offers_sent'],
                    'offers_accepted': stats['offers_accepted'],
                    'acceptance_rate': round(acceptance_rate * 100, 2)  # Percentage
                })
        
        return result
    
    async def selection_ratio(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> float:
        """
        Selection Ratio (Applicant-to-Hire) - Give overall hires ÷ applicants for a date range 
        using applicants and applicant_logs with status='hired'
        """
        applicants_data = await self.engine._get_applicants_data()
        status_mapping = await self.engine._get_status_mapping()
        
        # Find hired status IDs using robust type field detection
        hired_status_ids = set()
        for status_id, status_info in status_mapping.items():
            if isinstance(status_info, dict):
                status_type = status_info.get('type', '').lower()
                if status_type == 'hired':
                    hired_status_ids.add(status_id)
        
        total_applicants = 0
        total_hires = 0
        
        for applicant in applicants_data:
            created_str = applicant.get('created')
            if not created_str:
                continue
            
            try:
                created_date = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                
                # Apply date filters if provided
                if start_date:
                    filter_start = datetime.fromisoformat(start_date)
                    if created_date < filter_start:
                        continue
                        
                if end_date:
                    filter_end = datetime.fromisoformat(end_date)
                    if created_date > filter_end:
                        continue
                
                total_applicants += 1
                
                # Check if hired
                current_status = applicant.get('status_id', 0)
                if current_status in hired_status_ids:
                    total_hires += 1
                    
            except (ValueError, TypeError):
                continue
        
        return total_hires / total_applicants if total_applicants > 0 else 0.0
    
    async def vacancy_rate(self) -> float:
        """
        Vacancy Rate (Open Reqs) - From vacancies(state), calculate COUNT(state='open') ÷ COUNT(*) 
        as vacancy_rate at the current timestamp
        """
        vacancies_data = await self.engine._execute_vacancies_query(None)
        
        if not vacancies_data:
            return 0.0
        
        total_vacancies = len(vacancies_data)
        open_vacancies = len([v for v in vacancies_data if v.get('state') == 'OPEN'])
        
        return open_vacancies / total_vacancies if total_vacancies > 0 else 0.0

    # ==================== COMPREHENSIVE METRICS ====================
    
    async def get_all_key_metrics(self) -> Dict[str, Any]:
        """Get all key metrics in one call for dashboard"""
        return {
            "active_candidates": await self.active_candidates(),
            "open_vacancies": await self.open_vacancies(),
            "closed_vacancies": await self.closed_vacancies(),
            "total_vacancies": await self.open_vacancies() + await self.closed_vacancies(),
            "active_statuses_count": len(await self.active_statuses()),
            "recruiters_count": len(await self.get_recruiters()),
            # Advanced metrics
            "time_to_fill_days": await self.time_to_fill(),
            "time_to_hire_days": await self.time_to_hire(),
            "selection_ratio": await self.selection_ratio(),
            "vacancy_rate": await self.vacancy_rate()
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
    
    async def get_advanced_metric(self, metric_name: str, **kwargs) -> Any:
        """Get advanced calculated metric by name with optional parameters"""
        advanced_metrics = {
            "time_to_fill": self.metrics.time_to_fill,
            "time_to_hire": self.metrics.time_to_hire,
            "source_effectiveness": self.metrics.source_effectiveness,
            "applicants_per_opening": self.metrics.applicants_per_opening,
            "application_to_interview_ratio": self.metrics.application_to_interview_ratio,
            "interview_to_offer_ratio": self.metrics.interview_to_offer_ratio,
            "offer_acceptance_rate": self.metrics.offer_acceptance_rate,
            "selection_ratio": self.metrics.selection_ratio,
            "vacancy_rate": self.metrics.vacancy_rate
        }
        
        if metric_name in advanced_metrics:
            return await advanced_metrics[metric_name](**kwargs)
        else:
            raise ValueError(f"Unknown advanced metric: {metric_name}")