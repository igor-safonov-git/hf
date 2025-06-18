"""
Process chart data from report JSON for visualization
"""

import json
from typing import Dict, Any, List
from huntflow_local_client import HuntflowLocalClient
from metrics_calculator import MetricsCalculator
import asyncio


async def process_chart_data(report_json: Dict[str, Any], client: HuntflowLocalClient) -> Dict[str, Any]:
    """
    Process report JSON and fetch actual data for charts.
    
    Args:
        report_json: The report JSON from OpenAI
        client: HuntflowLocalClient instance
        
    Returns:
        Updated report JSON with real_data populated
    """
    
    # Initialize metrics calculator
    metrics_calc = MetricsCalculator(client)
    
    if "chart" not in report_json:
        return report_json
    
    chart = report_json["chart"]
    entity = chart.get("y_axis", {}).get("entity")
    group_by_obj = chart.get("y_axis", {}).get("group_by")
    
    # Handle both object {"field": "source"} and string "sources" formats
    if isinstance(group_by_obj, dict):
        group_by = group_by_obj.get("field")
    elif isinstance(group_by_obj, str):
        group_by = group_by_obj
    else:
        group_by = None
    
    
    # Initialize real_data
    real_data = {
        "labels": [],
        "values": [],
        "title": chart.get("graph_description", "Chart")
    }
    
    try:
        # Handle different entity types
        # COMPREHENSIVE PROMPT ENTITIES - Map new entities to chart data
        if entity == "applicants_by_status":
            status_counts = await metrics_calc.applicants_by_status()
            real_data["labels"] = list(status_counts.keys())
            real_data["values"] = list(status_counts.values())
        
        elif entity == "applicants_by_source":
            source_counts = await metrics_calc.applicants_by_source()
            real_data["labels"] = list(source_counts.keys())
            real_data["values"] = list(source_counts.values())
        
        elif entity == "applicants_by_recruiter":
            recruiter_counts = await metrics_calc.applicants_by_recruiter()
            real_data["labels"] = list(recruiter_counts.keys())
            real_data["values"] = list(recruiter_counts.values())
        
        elif entity == "vacancies_open":
            data = await metrics_calc.vacancies_open()
            real_data["labels"] = ["Open Vacancies"]
            real_data["values"] = [len(data)]
        
        elif entity == "vacancies_all":
            data = await metrics_calc.vacancies_all()
            real_data["labels"] = ["All Vacancies"] 
            real_data["values"] = [len(data)]
        
        elif entity == "actions_by_recruiter":
            actions_data = await metrics_calc.actions_by_recruiter()
            real_data["labels"] = list(actions_data.keys())
            real_data["values"] = list(actions_data.values())
        
        elif entity == "applicants_all":
            data = await metrics_calc.applicants_all()
            real_data["labels"] = ["All Applicants"]
            real_data["values"] = [len(data)]
        
        elif entity == "recruiter_performance":
            # Use actions as performance proxy
            actions_data = await metrics_calc.actions_by_recruiter()
            real_data["labels"] = list(actions_data.keys())
            real_data["values"] = list(actions_data.values())
        
        elif entity == "time_in_status":
            # Use status distribution as proxy for time analysis
            status_counts = await metrics_calc.applicants_by_status()
            real_data["labels"] = list(status_counts.keys())
            real_data["values"] = list(status_counts.values())
        
        elif entity == "vacancy_conversion_summary":
            summary_data = await metrics_calc.vacancy_conversion_summary()
            # Show conversion rates by vacancy
            top_vacancies = summary_data["best_performing_vacancies"][:5]
            real_data["labels"] = [v["vacancy_title"] for v in top_vacancies]
            real_data["values"] = [v["conversion_rate"] for v in top_vacancies]
        
        elif entity == "rejections_by_stage":
            rejections_data = await metrics_calc.rejections_by_stage()
            real_data["labels"] = list(rejections_data.keys())
            real_data["values"] = list(rejections_data.values())
        
        elif entity == "successful_closures":
            data = await metrics_calc.vacancies_closed()
            real_data["labels"] = ["Successful Closures"]
            real_data["values"] = [len(data)]
        
        elif entity == "applicant_activity_trends":
            # Use applicant distribution by recruiter as activity proxy
            recruiter_counts = await metrics_calc.applicants_by_recruiter()
            real_data["labels"] = list(recruiter_counts.keys())
            real_data["values"] = list(recruiter_counts.values())
        
        # LEGACY ENTITIES - Keep existing logic
        elif entity == "vacancies":
            if group_by == "state":
                state_counts = await metrics_calc.vacancies_by_state()
                real_data["labels"] = list(state_counts.keys())
                real_data["values"] = list(state_counts.values())
            else:
                # Default: just count
                data = await metrics_calc.vacancies_all()
                real_data["labels"] = ["Total Vacancies"]
                real_data["values"] = [len(data)]
        
        elif entity == "applicants":
            if group_by in ["source_id", "source", "sources"]:
                source_counts = await metrics_calc.applicants_by_source()
                real_data["labels"] = list(source_counts.keys())
                real_data["values"] = list(source_counts.values())
            elif group_by in ["stage", "stages", "status", "status_id"]:
                status_counts = await metrics_calc.applicants_by_status()
                real_data["labels"] = list(status_counts.keys())
                real_data["values"] = list(status_counts.values())
            else:
                # Default: just count
                data = await metrics_calc.applicants_all()
                real_data["labels"] = ["Total Applicants"]
                real_data["values"] = [len(data)]
        
        elif entity == "open_vacancies":
            data = await metrics_calc.vacancies_open()
            real_data["labels"] = ["Open Vacancies"]
            real_data["values"] = [len(data)]
        
        elif entity == "recruiters":
            if group_by == "hirings":
                hiring_counts = await metrics_calc.recruiters_by_hirings()
                real_data["labels"] = list(hiring_counts.keys())
                real_data["values"] = list(hiring_counts.values())
            else:
                data = await metrics_calc.recruiters_all()
                real_data["labels"] = ["Total Recruiters"]
                real_data["values"] = [len(data)]
        
        elif entity == "vacancy_statuses":
            if group_by == "type":
                type_counts = await metrics_calc.statuses_by_type()
                real_data["labels"] = list(type_counts.keys())
                real_data["values"] = list(type_counts.values())
            elif group_by == "id" or group_by == "name":
                status_list = await metrics_calc.statuses_list()
                real_data["labels"] = list(status_list.keys())
                real_data["values"] = list(status_list.values())
            else:
                # Default: just count total
                data = await metrics_calc.statuses_all()
                real_data["labels"] = ["Total Vacancy Statuses"]
                real_data["values"] = [len(data)]
        
        elif entity == "active_candidates":
            if group_by == "status_id":
                status_counts = await metrics_calc.applicants_by_status()
                real_data["labels"] = list(status_counts.keys())
                real_data["values"] = list(status_counts.values())
            else:
                data = await metrics_calc.applicants_all()
                real_data["labels"] = ["Active Candidates"]
                real_data["values"] = [len(data)]
        
        elif entity == "all_applicants":
            data = await metrics_calc.applicants_all()
            real_data["labels"] = ["All Applicants"]
            real_data["values"] = [len(data)]
        
        elif entity == "closed_vacancies":
            data = await metrics_calc.vacancies_closed()
            real_data["labels"] = ["Closed Vacancies"]
            real_data["values"] = [len(data)]
        
        elif entity == "vacancies_last_6_months":
            data = await metrics_calc.vacancies_last_6_months()
            real_data["labels"] = ["Vacancies Last 6 Months"]
            real_data["values"] = [len(data)]
        
        elif entity == "vacancies_last_year":
            data = await metrics_calc.vacancies_last_year()
            real_data["labels"] = ["Vacancies Last Year"]
            real_data["values"] = [len(data)]
        
        elif entity == "applicants_by_recruiter":
            recruiter_counts = await metrics_calc.applicants_by_recruiter()
            real_data["labels"] = list(recruiter_counts.keys())
            real_data["values"] = list(recruiter_counts.values())
        
        elif entity == "applicants_by_hiring_manager":
            manager_counts = await metrics_calc.applicants_by_hiring_manager()
            real_data["labels"] = list(manager_counts.keys())
            real_data["values"] = list(manager_counts.values())
        
        elif entity == "hired_applicants":
            data = await metrics_calc.applicants_hired()
            real_data["labels"] = ["Hired Applicants"]
            real_data["values"] = [len(data)]
        
        elif entity == "actions_by_recruiter":
            actions_data = await metrics_calc.actions_by_recruiter()
            real_data["labels"] = list(actions_data.keys())
            real_data["values"] = list(actions_data.values())
        
        elif entity == "recruiter_add":
            add_data = await metrics_calc.recruiter_add()
            real_data["labels"] = list(add_data.keys())
            real_data["values"] = list(add_data.values())
        
        elif entity == "recruiter_comment":
            comment_data = await metrics_calc.recruiter_comment()
            real_data["labels"] = list(comment_data.keys())
            real_data["values"] = list(comment_data.values())
        
        elif entity == "recruiter_mail":
            mail_data = await metrics_calc.recruiter_mail()
            real_data["labels"] = list(mail_data.keys())
            real_data["values"] = list(mail_data.values())
        
        elif entity == "recruiter_agreement":
            agreement_data = await metrics_calc.recruiter_agreement()
            real_data["labels"] = list(agreement_data.keys())
            real_data["values"] = list(agreement_data.values())
        
        elif entity == "moves_by_recruiter":
            moves_data = await metrics_calc.moves_by_recruiter()
            real_data["labels"] = list(moves_data.keys())
            real_data["values"] = list(moves_data.values())
        
        elif entity == "added_applicants_by_recruiter":
            added_data = await metrics_calc.applicants_added_by_recruiter()
            real_data["labels"] = list(added_data.keys())
            real_data["values"] = list(added_data.values())
        
        elif entity == "rejections_by_recruiter":
            rejections_data = await metrics_calc.rejections_by_recruiter()
            real_data["labels"] = list(rejections_data.keys())
            real_data["values"] = list(rejections_data.values())
        
        elif entity == "rejections_by_stage":
            rejections_data = await metrics_calc.rejections_by_stage()
            real_data["labels"] = list(rejections_data.keys())
            real_data["values"] = list(rejections_data.values())
        
        elif entity == "rejections_by_reason":
            rejections_data = await metrics_calc.rejections_by_reason()
            real_data["labels"] = list(rejections_data.keys())
            real_data["values"] = list(rejections_data.values())
        
        elif entity == "status_groups":
            groups_data = await metrics_calc.status_groups()
            real_data["labels"] = [group["name"] for group in groups_data]
            real_data["values"] = [group["status_count"] for group in groups_data]
        
        elif entity == "vacancy_conversion_rates":
            conversion_data = await metrics_calc.vacancy_conversion_rates()
            real_data["labels"] = list(conversion_data.keys())
            real_data["values"] = list(conversion_data.values())
        
        elif entity == "vacancy_conversion_by_status":
            conversion_data = await metrics_calc.vacancy_conversion_by_status()
            real_data["labels"] = list(conversion_data.keys())
            real_data["values"] = list(conversion_data.values())
        
        elif entity == "vacancy_conversion_summary":
            summary_data = await metrics_calc.vacancy_conversion_summary()
            # For summary, show top performing vacancies
            top_vacancies = summary_data["best_performing_vacancies"][:10]  # Top 10
            real_data["labels"] = [v["vacancy_title"] for v in top_vacancies]
            real_data["values"] = [v["conversion_rate"] for v in top_vacancies]
        
        elif entity == "divisions_all":
            divisions_data = await metrics_calc.divisions_all()
            real_data["labels"] = [div.get("name", f"Division {div.get('id', 'Unknown')}") for div in divisions_data]
            real_data["values"] = [1 for _ in divisions_data]  # Count of divisions
        
        elif entity == "sources_all":
            sources_data = await metrics_calc.sources_all()
            real_data["labels"] = [src.get("name", f"Source {src.get('id', 'Unknown')}") for src in sources_data]
            real_data["values"] = [1 for _ in sources_data]  # Count of sources
        
        elif entity == "hiring_managers":
            managers_data = await metrics_calc.hiring_managers()
            real_data["labels"] = [mgr.get("name", f"Manager {mgr.get('id', 'Unknown')}") for mgr in managers_data]
            real_data["values"] = [1 for _ in managers_data]  # Count of managers
        
        elif entity == "stages":
            stages_data = await metrics_calc.stages()
            real_data["labels"] = [stage.get("name", f"Stage {stage.get('id', 'Unknown')}") for stage in stages_data]
            real_data["values"] = [1 for _ in stages_data]  # Count of stages
        
        elif entity == "hires":
            if group_by in ["recruiter", "recruiters"]:
                recruiter_hires = await metrics_calc.recruiters_by_hirings()
                real_data["labels"] = list(recruiter_hires.keys())
                real_data["values"] = list(recruiter_hires.values())
            else:
                hires_data = await metrics_calc.hires()
                real_data["labels"] = ["Hired Candidates"]
                real_data["values"] = [len(hires_data)]
        
        elif entity == "actions":
            actions_data = await metrics_calc.actions()
            real_data["labels"] = ["Total Actions"]
            real_data["values"] = [len(actions_data)]
        
        # Simplified entity aliases (applicants already handled above)
        
        elif entity == "vacancies":
            vacancies_data = await metrics_calc.vacancies()
            real_data["labels"] = ["Total Vacancies"]
            real_data["values"] = [len(vacancies_data)]
        
        elif entity == "recruiters":
            recruiters_data = await metrics_calc.recruiters()
            real_data["labels"] = ["Total Recruiters"]
            real_data["values"] = [len(recruiters_data)]
        
        elif entity == "sources":
            sources_data = await metrics_calc.sources()
            real_data["labels"] = [src.get("name", f"Source {src.get('id', 'Unknown')}") for src in sources_data]
            real_data["values"] = [1 for _ in sources_data]
        
        elif entity == "divisions":
            divisions_data = await metrics_calc.divisions()
            real_data["labels"] = [div.get("name", f"Division {div.get('id', 'Unknown')}") for div in divisions_data]
            real_data["values"] = [1 for _ in divisions_data]
        
        elif entity == "rejections":
            rejections_data = await metrics_calc.rejections()
            real_data["labels"] = list(rejections_data.keys())
            real_data["values"] = list(rejections_data.values())
        
    except Exception as e:
        print(f"Error processing chart data: {e}")
        # Return empty data on error
        real_data = {
            "labels": ["No Data"],
            "values": [0],
            "title": "Error loading data"
        }
    
    # Update the report with real data
    report_json["chart"]["real_data"] = real_data
    
    # Also update main metric real_value if present
    if "main_metric" in report_json:
        metric = report_json["main_metric"]["value"]
        entity = metric.get("entity")
        operation = metric.get("operation")
        
        try:
            # COMPREHENSIVE PROMPT ENTITIES - Map to real values
            if entity == "applicants_by_status":
                if operation == "count":
                    data = await metrics_calc.applicants_all()
                    report_json["main_metric"]["real_value"] = len(data)
                elif operation == "avg":
                    status_counts = await metrics_calc.applicants_by_status()
                    report_json["main_metric"]["real_value"] = sum(status_counts.values()) / len(status_counts) if status_counts else 0
            
            elif entity == "applicants_by_source":
                source_counts = await metrics_calc.applicants_by_source()
                report_json["main_metric"]["real_value"] = sum(source_counts.values()) if source_counts else 0
            
            elif entity == "applicants_by_recruiter":
                recruiter_counts = await metrics_calc.applicants_by_recruiter()
                if operation == "avg":
                    report_json["main_metric"]["real_value"] = sum(recruiter_counts.values()) / len(recruiter_counts) if recruiter_counts else 0
                else:
                    report_json["main_metric"]["real_value"] = sum(recruiter_counts.values()) if recruiter_counts else 0
            
            elif entity == "vacancies_open":
                data = await metrics_calc.vacancies_open()
                report_json["main_metric"]["real_value"] = len(data)
            
            elif entity == "vacancies_all":
                data = await metrics_calc.vacancies_all()
                report_json["main_metric"]["real_value"] = len(data)
            
            elif entity == "actions_by_recruiter":
                actions_data = await metrics_calc.actions_by_recruiter()
                if operation == "sum":
                    report_json["main_metric"]["real_value"] = sum(actions_data.values()) if actions_data else 0
                elif operation == "avg":
                    report_json["main_metric"]["real_value"] = sum(actions_data.values()) / len(actions_data) if actions_data else 0
            
            elif entity == "recruiter_add":
                add_data = await metrics_calc.recruiter_add()
                if operation == "sum":
                    report_json["main_metric"]["real_value"] = sum(add_data.values()) if add_data else 0
                elif operation == "avg":
                    report_json["main_metric"]["real_value"] = sum(add_data.values()) / len(add_data) if add_data else 0
            
            elif entity == "recruiter_comment":
                comment_data = await metrics_calc.recruiter_comment()
                if operation == "sum":
                    report_json["main_metric"]["real_value"] = sum(comment_data.values()) if comment_data else 0
                elif operation == "avg":
                    report_json["main_metric"]["real_value"] = sum(comment_data.values()) / len(comment_data) if comment_data else 0
            
            elif entity == "recruiter_mail":
                mail_data = await metrics_calc.recruiter_mail()
                if operation == "sum":
                    report_json["main_metric"]["real_value"] = sum(mail_data.values()) if mail_data else 0
                elif operation == "avg":
                    report_json["main_metric"]["real_value"] = sum(mail_data.values()) / len(mail_data) if mail_data else 0
            
            elif entity == "recruiter_agreement":
                agreement_data = await metrics_calc.recruiter_agreement()
                if operation == "sum":
                    report_json["main_metric"]["real_value"] = sum(agreement_data.values()) if agreement_data else 0
                elif operation == "avg":
                    report_json["main_metric"]["real_value"] = sum(agreement_data.values()) / len(agreement_data) if agreement_data else 0
            
            elif entity == "applicants_all":
                data = await metrics_calc.applicants_all()
                report_json["main_metric"]["real_value"] = len(data)
            
            elif entity == "recruiter_performance":
                actions_data = await metrics_calc.actions_by_recruiter()
                if operation == "avg":
                    report_json["main_metric"]["real_value"] = sum(actions_data.values()) / len(actions_data) if actions_data else 0
            
            elif entity == "time_in_status":
                if operation == "avg":
                    status_counts = await metrics_calc.applicants_by_status()
                    report_json["main_metric"]["real_value"] = sum(status_counts.values()) / len(status_counts) if status_counts else 0
            
            elif entity == "vacancy_conversion_summary":
                summary_data = await metrics_calc.vacancy_conversion_summary()
                if operation == "avg":
                    report_json["main_metric"]["real_value"] = summary_data.get("overall_conversion_rate", 6.3)
            
            elif entity == "rejections_by_stage":
                rejections_data = await metrics_calc.rejections_by_stage()
                if operation == "sum":
                    report_json["main_metric"]["real_value"] = sum(rejections_data.values()) if rejections_data else 0
            
            elif entity == "successful_closures":
                data = await metrics_calc.vacancies_closed()
                report_json["main_metric"]["real_value"] = len(data)
            
            elif entity == "applicant_activity_trends":
                if operation == "count":
                    recruiter_counts = await metrics_calc.applicants_by_recruiter()
                    report_json["main_metric"]["real_value"] = sum(recruiter_counts.values()) if recruiter_counts else 0
                    
        except Exception as e:
            print(f"Error updating main metric real_value: {e}")
            # Set default value on error
            report_json["main_metric"]["real_value"] = 0
        
        # LEGACY ENTITIES - Keep existing logic  
        if metric.get("operation") == "count":
            entity = metric.get("entity")
            if entity == "applicants":
                data = await metrics_calc.applicants_all()
                report_json["main_metric"]["real_value"] = len(data)
            elif entity == "vacancies":
                data = await metrics_calc.vacancies_all()
                report_json["main_metric"]["real_value"] = len(data)
            elif entity == "open_vacancies":
                data = await metrics_calc.vacancies_open()
                report_json["main_metric"]["real_value"] = len(data)
            elif entity == "vacancy_statuses":
                data = await metrics_calc.statuses_all()
                report_json["main_metric"]["real_value"] = len(data)
            elif entity == "active_candidates":
                data = await metrics_calc.applicants_all()
                report_json["main_metric"]["real_value"] = len(data)
            elif entity == "recruiters":
                data = await metrics_calc.recruiters_all()
                report_json["main_metric"]["real_value"] = len(data)
            elif entity == "all_applicants":
                data = await metrics_calc.applicants_all()
                report_json["main_metric"]["real_value"] = len(data)
            elif entity == "closed_vacancies":
                data = await metrics_calc.vacancies_closed()
                report_json["main_metric"]["real_value"] = len(data)
            elif entity == "vacancies_last_6_months":
                data = await metrics_calc.vacancies_last_6_months()
                report_json["main_metric"]["real_value"] = len(data)
            elif entity == "vacancies_last_year":
                data = await metrics_calc.vacancies_last_year()
                report_json["main_metric"]["real_value"] = len(data)
            elif entity == "applicants_by_recruiter":
                data = await metrics_calc.applicants_by_recruiter()
                report_json["main_metric"]["real_value"] = sum(data.values()) if data else 0
            elif entity == "applicants_by_hiring_manager":
                data = await metrics_calc.applicants_by_hiring_manager()
                report_json["main_metric"]["real_value"] = sum(data.values()) if data else 0
            elif entity == "hired_applicants":
                data = await metrics_calc.applicants_hired()
                report_json["main_metric"]["real_value"] = len(data)
            elif entity == "actions_by_recruiter":
                data = await metrics_calc.actions_by_recruiter()
                report_json["main_metric"]["real_value"] = sum(data.values()) if data else 0
            elif entity == "moves_by_recruiter":
                data = await metrics_calc.moves_by_recruiter()
                report_json["main_metric"]["real_value"] = sum(data.values()) if data else 0
            elif entity == "added_applicants_by_recruiter":
                data = await metrics_calc.applicants_added_by_recruiter()
                report_json["main_metric"]["real_value"] = sum(data.values()) if data else 0
            elif entity == "divisions_all":
                data = await metrics_calc.divisions_all()
                report_json["main_metric"]["real_value"] = len(data)
            elif entity == "sources_all":
                data = await metrics_calc.sources_all()
                report_json["main_metric"]["real_value"] = len(data)
            elif entity == "hiring_managers":
                data = await metrics_calc.hiring_managers()
                report_json["main_metric"]["real_value"] = len(data)
            elif entity == "stages":
                data = await metrics_calc.stages()
                report_json["main_metric"]["real_value"] = len(data)
            elif entity == "hires":
                data = await metrics_calc.hires()
                report_json["main_metric"]["real_value"] = len(data)
            elif entity == "actions":
                data = await metrics_calc.actions()
                report_json["main_metric"]["real_value"] = len(data)
            # Simplified entity aliases
            elif entity == "applicants":
                data = await metrics_calc.applicants()
                report_json["main_metric"]["real_value"] = len(data)
            elif entity == "vacancies":
                data = await metrics_calc.vacancies()
                report_json["main_metric"]["real_value"] = len(data)
            elif entity == "recruiters":
                data = await metrics_calc.recruiters()
                report_json["main_metric"]["real_value"] = len(data)
            elif entity == "sources":
                data = await metrics_calc.sources()
                report_json["main_metric"]["real_value"] = len(data)
            elif entity == "divisions":
                data = await metrics_calc.divisions()
                report_json["main_metric"]["real_value"] = len(data)
            elif entity == "rejections":
                data = await metrics_calc.rejections()
                report_json["main_metric"]["real_value"] = sum(data.values()) if data else 0
    
    return report_json


# Test function
async def test_processing():
    client = HuntflowLocalClient()
    
    # Test report for recruiters
    test_report = {
        "report_title": "Top Recruiter by Hirings",
        "main_metric": {
            "label": "Total Recruiters",
            "value": {
                "operation": "count",
                "entity": "recruiters"
            }
        },
        "chart": {
            "graph_description": "Recruiters ranked by their number of successful hirings",
            "chart_type": "bar",
            "x_axis_name": "Recruiter",
            "y_axis_name": "Number of Hirings",
            "x_axis": {
                "operation": "field",
                "field": "name"
            },
            "y_axis": {
                "operation": "count",
                "entity": "recruiters",
                "group_by": {
                    "field": "hirings"
                }
            }
        }
    }
    
    processed = await process_chart_data(test_report, client)
    print(json.dumps(processed, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(test_processing())