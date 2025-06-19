"""
Legacy entity mappings for backward compatibility
"""

# Legacy entity name mappings
LEGACY_ENTITY_MAPPINGS = {
    "open_vacancies": "vacancies_open",
    "closed_vacancies": "vacancies_closed", 
    "all_applicants": "applicants_all",
    # Add more legacy mappings as needed
}

# Method operation mappings for consolidated metric calculation
METRIC_METHOD_CONFIG = {
    # Count operations - return len(data)
    "count_methods": {
        "applicants_all", "vacancies_all", "vacancies_open", "vacancies_closed",
        "vacancies_last_6_months", "vacancies_last_year", "applicants_hired",
        "divisions_all", "sources_all", "hiring_managers", "stages",
        "recruiters_all", "hires", "actions", "applicants", "vacancies",
        "recruiters", "sources", "divisions"
    },
    
    # Dict operations - return dict with values to sum/average
    "dict_methods": {
        "applicants_by_status", "applicants_by_source", "applicants_by_recruiter",
        "applicants_by_hiring_manager", "actions_by_recruiter", "moves_by_recruiter",
        "applicants_added_by_recruiter", "rejections_by_stage", "recruiter_add",
        "recruiter_comment", "recruiter_mail", "recruiter_agreement", "rejections"
    },
    
    # Special cases with lambda handlers
    "special_cases": {
        "vacancy_conversion_summary": {
            "avg": lambda data: data.get("overall_conversion_rate", 6.3)
        }
    }
}