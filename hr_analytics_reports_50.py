"""
50 Complete HR Analytics JSON Reports for Huntflow Integration
Each report includes full JSON structure with main metric, secondary metrics, and charts,
plus 2-3 conversational Russian questions that can be answered by this report.
"""

# Real data context
REAL_RECRUITERS = ["Анастасия Богач", "Михаил Танский", "Виталий Глибин", "Алина Петрова", "София Данилова"]
REAL_STATUSES = ["Новые", "Интервью", "Резюме у заказчика", "Отправлено письмо", "Оффер принят", "Отказ"]
REAL_POSITIONS = ["Python Developer", "Java Developer", "QA Engineer", "Designer", "Sales Manager", "HR Manager"]

# 50 Complete HR Analytics Reports
HR_ANALYTICS_REPORTS = [

# ==========================================
# CATEGORY 1: BASIC PIPELINE OVERVIEW (1-10)
# ==========================================

{
    "questions": [
        "Сколько у нас сейчас кандидатов в воронке?",
        "Какое общее количество активных кандидатов?",
        "Как распределены кандидаты по этапам найма?"
    ],
    "report": {
        "report_title": "Active Pipeline Overview",
        "main_metric": {
            "label": "Total Active Candidates",
            "value": {
                "operation": "count",
                "entity": "applicants_by_status"
            },
            "real_value": 142
        },
        "secondary_metrics": [
            {
                "label": "New This Week",
                "value": {
                    "operation": "count",
                    "entity": "applicants_all",
                    "filter": {"field": "created", "op": "gte", "value": "2025-06-11T00:00:00"}
                },
                "real_value": 23
            },
            {
                "label": "Interview Ready",
                "value": {
                    "operation": "count",
                    "entity": "applicants_by_status",
                    "filter": {"field": "status_name", "op": "eq", "value": "Интервью"}
                },
                "real_value": 34
            }
        ],
        "chart": {
            "graph_description": "Candidate distribution across pipeline stages",
            "chart_type": "bar",
            "x_axis_name": "Pipeline Stage",
            "y_axis_name": "Number of Candidates",
            "x_axis": {"operation": "field", "field": "status_name"},
            "y_axis": {
                "operation": "count",
                "entity": "applicants_by_status",
                "group_by": {"field": "status_name"}
            },
            "real_data": {
                "labels": ["Новые", "Интервью", "Резюме у заказчика", "Отправлено письмо", "Оффер принят"],
                "values": [45, 34, 28, 21, 14],
                "title": "Pipeline Distribution"
            }
        }
    }
},

{
    "questions": [
        "Сколько открытых вакансий у нас есть?",
        "Какие вакансии сейчас активны?",
        "Как распределены вакансии по приоритетам?"
    ],
    "report": {
        "report_title": "Open Vacancies Dashboard",
        "main_metric": {
            "label": "Open Vacancies",
            "value": {
                "operation": "count",
                "entity": "vacancies_open"
            },
            "real_value": 42
        },
        "secondary_metrics": [
            {
                "label": "High Priority",
                "value": {
                    "operation": "count",
                    "entity": "vacancies_all",
                    "filter": [
                        {"field": "state", "op": "eq", "value": "OPEN"},
                        {"field": "priority", "op": "eq", "value": "high"}
                    ]
                },
                "real_value": 12
            },
            {
                "label": "Created This Month",
                "value": {
                    "operation": "count",
                    "entity": "vacancies_all",
                    "filter": [
                        {"field": "state", "op": "eq", "value": "OPEN"},
                        {"field": "created", "op": "gte", "value": "2025-06-01T00:00:00"}
                    ]
                },
                "real_value": 8
            }
        ],
        "chart": {
            "graph_description": "Vacancy distribution by priority level",
            "chart_type": "pie",
            "x_axis_name": "Priority",
            "y_axis_name": "Count",
            "x_axis": {"operation": "field", "field": "priority"},
            "y_axis": {
                "operation": "count",
                "entity": "vacancies_by_priority",
                "group_by": {"field": "priority"}
            },
            "real_data": {
                "labels": ["high", "normal", "low"],
                "values": [12, 25, 5],
                "title": "Vacancy Priority Distribution"
            }
        }
    }
},

{
    "questions": [
        "Как работают наши рекрутеры?",
        "Кто из рекрутеров самый активный?",
        "Сколько действий выполняют рекрутеры?"
    ],
    "report": {
        "report_title": "Recruiter Activity Overview",
        "main_metric": {
            "label": "Total Recruiter Actions",
            "value": {
                "operation": "sum",
                "entity": "actions_by_recruiter"
            },
            "real_value": 1247
        },
        "secondary_metrics": [
            {
                "label": "Active Recruiters",
                "value": {
                    "operation": "count",
                    "entity": "recruiters_all"
                },
                "real_value": 5
            },
            {
                "label": "Avg Actions per Recruiter",
                "value": {
                    "operation": "avg",
                    "entity": "actions_by_recruiter"
                },
                "real_value": 249
            }
        ],
        "chart": {
            "graph_description": "Activity level by recruiter",
            "chart_type": "bar",
            "x_axis_name": "Recruiter",
            "y_axis_name": "Number of Actions",
            "x_axis": {"operation": "field", "field": "recruiter_name"},
            "y_axis": {
                "operation": "sum",
                "entity": "actions_by_recruiter",
                "group_by": {"field": "recruiter_name"}
            },
            "real_data": {
                "labels": ["Анастасия Богач", "Михаил Танский", "Виталий Глибин", "Алина Петрова", "София Данилова"],
                "values": [342, 298, 267, 201, 139],
                "title": "Recruiter Activity Levels"
            }
        }
    }
},

{
    "questions": [
        "Откуда приходят наши кандидаты?",
        "Какие источники найма самые эффективные?",
        "Сколько кандидатов из каждого источника?"
    ],
    "report": {
        "report_title": "Candidate Sources Analysis",
        "main_metric": {
            "label": "Total Sources Active",
            "value": {
                "operation": "count",
                "entity": "applicants_by_source"
            },
            "real_value": 8
        },
        "secondary_metrics": [
            {
                "label": "LinkedIn Candidates",
                "value": {
                    "operation": "count",
                    "entity": "applicants_by_source",
                    "filter": {"field": "source_name", "op": "eq", "value": "LinkedIn"}
                },
                "real_value": 47
            },
            {
                "label": "Referral Candidates",
                "value": {
                    "operation": "count",
                    "entity": "applicants_by_source",
                    "filter": {"field": "source_name", "op": "eq", "value": "Referral"}
                },
                "real_value": 23
            }
        ],
        "chart": {
            "graph_description": "Candidate volume by recruitment source",
            "chart_type": "pie",
            "x_axis_name": "Source",
            "y_axis_name": "Candidates",
            "x_axis": {"operation": "field", "field": "source_name"},
            "y_axis": {
                "operation": "count",
                "entity": "applicants_by_source",
                "group_by": {"field": "source_name"}
            },
            "real_data": {
                "labels": ["LinkedIn", "HeadHunter", "Referral", "Direct", "Agency", "Indeed", "Telegram", "Other"],
                "values": [47, 32, 23, 18, 12, 6, 3, 1],
                "title": "Source Distribution"
            }
        }
    }
},

{
    "questions": [
        "Какая конверсия вакансий в найм?",
        "Какие вакансии лучше всего конвертируют?",
        "Насколько эффективен наш процесс найма?"
    ],
    "report": {
        "report_title": "Hiring Conversion Analysis",
        "main_metric": {
            "label": "Overall Conversion Rate (%)",
            "value": {
                "operation": "avg",
                "entity": "vacancy_conversion_summary"
            },
            "real_value": 6.3
        },
        "secondary_metrics": [
            {
                "label": "Total Hires",
                "value": {
                    "operation": "count",
                    "entity": "applicants_hired"
                },
                "real_value": 9
            },
            {
                "label": "Best Converting Vacancy (%)",
                "value": {
                    "operation": "max",
                    "entity": "vacancy_conversion_rates"
                },
                "real_value": 25.0
            }
        ],
        "chart": {
            "graph_description": "Conversion rates by vacancy position",
            "chart_type": "bar",
            "x_axis_name": "Position",
            "y_axis_name": "Conversion Rate (%)",
            "x_axis": {"operation": "field", "field": "position_name"},
            "y_axis": {
                "operation": "avg",
                "entity": "vacancy_conversion_rates",
                "group_by": {"field": "position_name"}
            },
            "real_data": {
                "labels": ["Python Developer", "QA Engineer", "Designer", "Sales Manager", "Java Developer"],
                "values": [12.5, 8.7, 6.2, 4.1, 3.8],
                "title": "Position Conversion Rates"
            }
        }
    }
},

{
    "questions": [
        "Сколько времени кандидаты проводят в каждом статусе?",
        "Где у нас узкие места в воронке?",
        "На каком этапе кандидаты застревают?"
    ],
    "report": {
        "report_title": "Pipeline Bottleneck Analysis",
        "main_metric": {
            "label": "Average Days in Pipeline",
            "value": {
                "operation": "avg",
                "entity": "time_in_status"
            },
            "real_value": 14.2
        },
        "secondary_metrics": [
            {
                "label": "Longest Stage (days)",
                "value": {
                    "operation": "max",
                    "entity": "time_in_status"
                },
                "real_value": 28.5
            },
            {
                "label": "Bottleneck Score",
                "value": {
                    "operation": "max",
                    "entity": "pipeline_bottlenecks"
                },
                "real_value": 85
            }
        ],
        "chart": {
            "graph_description": "Average time spent in each pipeline stage",
            "chart_type": "bar",
            "x_axis_name": "Pipeline Stage",
            "y_axis_name": "Days",
            "x_axis": {"operation": "field", "field": "status_name"},
            "y_axis": {
                "operation": "avg",
                "entity": "time_in_status",
                "group_by": {"field": "status_name"}
            },
            "real_data": {
                "labels": ["Новые", "Интервью", "Резюме у заказчика", "Отправлено письмо", "Оффер принят"],
                "values": [3.2, 7.1, 28.5, 12.4, 5.8],
                "title": "Time in Each Stage"
            }
        }
    }
},

{
    "questions": [
        "Как изменилась активность за последние месяцы?",
        "Есть ли сезонные тренды в найме?",
        "Когда у нас пик активности?"
    ],
    "report": {
        "report_title": "Hiring Trends Analysis",
        "main_metric": {
            "label": "This Year Applicants",
            "value": {
                "operation": "count",
                "entity": "applicants_all",
                "filter": {"field": "created", "op": "gte", "value": "2024-06-18T00:00:00"}
            },
            "real_value": 186
        },
        "secondary_metrics": [
            {
                "label": "Monthly Growth (%)",
                "value": {
                    "operation": "avg",
                    "entity": "monthly_growth"
                },
                "real_value": 12.4
            },
            {
                "label": "Peak Month Applications",
                "value": {
                    "operation": "max",
                    "entity": "monthly_applications"
                },
                "real_value": 34
            }
        ],
        "chart": {
            "graph_description": "Application volume trends over time",
            "chart_type": "line",
            "x_axis_name": "Month",
            "y_axis_name": "Applications",
            "x_axis": {"operation": "date_trunc", "field": "created"},
            "y_axis": {
                "operation": "count",
                "entity": "applicants_all",
                "group_by": {"field": "month"}
            },
            "real_data": {
                "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                "values": [18, 22, 34, 28, 31, 23],
                "title": "Monthly Application Trends"
            }
        }
    }
},

{
    "questions": [
        "Какие причины отказов самые частые?",
        "Почему мы отклоняем кандидатов?",
        "На каких этапах больше всего отказов?"
    ],
    "report": {
        "report_title": "Rejection Analysis",
        "main_metric": {
            "label": "Total Rejections",
            "value": {
                "operation": "sum",
                "entity": "rejections_by_stage"
            },
            "real_value": 89
        },
        "secondary_metrics": [
            {
                "label": "Top Rejection Stage",
                "value": {
                    "operation": "max",
                    "entity": "rejections_by_stage"
                },
                "real_value": 34
            },
            {
                "label": "Rejection Rate (%)",
                "value": {
                    "operation": "avg",
                    "entity": "rejection_rates"
                },
                "real_value": 62.7
            }
        ],
        "chart": {
            "graph_description": "Rejection distribution by pipeline stage",
            "chart_type": "bar",
            "x_axis_name": "Stage",
            "y_axis_name": "Rejections",
            "x_axis": {"operation": "field", "field": "stage_name"},
            "y_axis": {
                "operation": "count",
                "entity": "rejections_by_stage",
                "group_by": {"field": "stage_name"}
            },
            "real_data": {
                "labels": ["После скрининга", "После интервью", "После технического задания", "После оффера", "Другое"],
                "values": [34, 28, 15, 8, 4],
                "title": "Rejection Points"
            }
        }
    }
},

{
    "questions": [
        "Сколько вакансий мы закрыли успешно?",
        "Какой процент вакансий заполняется?",
        "Как быстро мы закрываем позиции?"
    ],
    "report": {
        "report_title": "Vacancy Closure Success",
        "main_metric": {
            "label": "Successful Closures",
            "value": {
                "operation": "count",
                "entity": "successful_closures"
            },
            "real_value": 23
        },
        "secondary_metrics": [
            {
                "label": "Success Rate (%)",
                "value": {
                    "operation": "avg",
                    "entity": "closure_success_rate"
                },
                "real_value": 78.3
            },
            {
                "label": "Avg Days to Close",
                "value": {
                    "operation": "avg",
                    "entity": "days_to_close"
                },
                "real_value": 45.2
            }
        ],
        "chart": {
            "graph_description": "Closure time distribution",
            "chart_type": "bar",
            "x_axis_name": "Time Range",
            "y_axis_name": "Vacancies Closed",
            "x_axis": {"operation": "field", "field": "time_range"},
            "y_axis": {
                "operation": "count",
                "entity": "closure_times",
                "group_by": {"field": "time_range"}
            },
            "real_data": {
                "labels": ["< 30 days", "30-60 days", "60-90 days", "90+ days"],
                "values": [5, 12, 4, 2],
                "title": "Time to Close Distribution"
            }
        }
    }
},

{
    "questions": [
        "Какая загрузка у каждого рекрутера?",
        "Кто из рекрутеров перегружен?",
        "Как равномерно распределена работа?"
    ],
    "report": {
        "report_title": "Recruiter Workload Balance",
        "main_metric": {
            "label": "Average Workload",
            "value": {
                "operation": "avg",
                "entity": "applicants_by_recruiter"
            },
            "real_value": 28.4
        },
        "secondary_metrics": [
            {
                "label": "Most Loaded Recruiter",
                "value": {
                    "operation": "max",
                    "entity": "applicants_by_recruiter"
                },
                "real_value": 47
            },
            {
                "label": "Workload Balance Score",
                "value": {
                    "operation": "avg",
                    "entity": "workload_balance"
                },
                "real_value": 0.73
            }
        ],
        "chart": {
            "graph_description": "Active candidates per recruiter",
            "chart_type": "bar",
            "x_axis_name": "Recruiter",
            "y_axis_name": "Active Candidates",
            "x_axis": {"operation": "field", "field": "recruiter_name"},
            "y_axis": {
                "operation": "count",
                "entity": "applicants_by_recruiter",
                "group_by": {"field": "recruiter_name"}
            },
            "real_data": {
                "labels": ["Анастасия Богач", "Михаил Танский", "Виталий Глибин", "Алина Петрова", "София Данилова"],
                "values": [47, 32, 28, 23, 12],
                "title": "Recruiter Workload"
            }
        }
    }
},

# ==========================================
# CATEGORY 2: PERFORMANCE ANALYSIS (11-20)
# ==========================================

{
    "questions": [
        "Кто из рекрутеров лучше всего нанимает?",
        "Сколько закрытий у каждого рекрутера?",
        "Какая эффективность найма по рекрутерам?"
    ],
    "report": {
        "report_title": "Recruiter Hiring Performance",
        "main_metric": {
            "label": "Total Hires by Team",
            "value": {
                "operation": "sum",
                "entity": "recruiters_by_hirings"
            },
            "real_value": 23
        },
        "secondary_metrics": [
            {
                "label": "Top Performer Hires",
                "value": {
                    "operation": "max",
                    "entity": "recruiters_by_hirings"
                },
                "real_value": 8
            },
            {
                "label": "Average Hires per Recruiter",
                "value": {
                    "operation": "avg",
                    "entity": "recruiters_by_hirings"
                },
                "real_value": 4.6
            }
        ],
        "chart": {
            "graph_description": "Successful hires by recruiter",
            "chart_type": "bar",
            "x_axis_name": "Recruiter",
            "y_axis_name": "Number of Hires",
            "x_axis": {"operation": "field", "field": "recruiter_name"},
            "y_axis": {
                "operation": "count",
                "entity": "recruiters_by_hirings",
                "group_by": {"field": "recruiter_name"}
            },
            "real_data": {
                "labels": ["Анастасия Богач", "Михаил Танский", "Виталий Глибин", "Алина Петрова", "София Данилова"],
                "values": [8, 6, 4, 3, 2],
                "title": "Hiring Success by Recruiter"
            }
        }
    }
},

{
    "questions": [
        "Как быстро рекрутеры отвечают кандидатам?",
        "Кто быстрее всех обрабатывает заявки?",
        "Есть ли проблемы со скоростью ответа?"
    ],
    "report": {
        "report_title": "Response Time Analysis",
        "main_metric": {
            "label": "Average Response Time (hours)",
            "value": {
                "operation": "avg",
                "entity": "response_times_by_recruiter"
            },
            "real_value": 18.7
        },
        "secondary_metrics": [
            {
                "label": "Fastest Responder (hours)",
                "value": {
                    "operation": "min",
                    "entity": "response_times_by_recruiter"
                },
                "real_value": 4.2
            },
            {
                "label": "SLA Compliance (%)",
                "value": {
                    "operation": "avg",
                    "entity": "sla_compliance"
                },
                "real_value": 87.3
            }
        ],
        "chart": {
            "graph_description": "Average response time by recruiter",
            "chart_type": "bar",
            "x_axis_name": "Recruiter",
            "y_axis_name": "Hours",
            "x_axis": {"operation": "field", "field": "recruiter_name"},
            "y_axis": {
                "operation": "avg",
                "entity": "response_times_by_recruiter",
                "group_by": {"field": "recruiter_name"}
            },
            "real_data": {
                "labels": ["София Данилова", "Анастасия Богач", "Алина Петрова", "Виталий Глибин", "Михаил Танский"],
                "values": [4.2, 12.1, 18.7, 25.3, 33.4],
                "title": "Response Time Performance"
            }
        }
    }
},

{
    "questions": [
        "Какая конверсия у каждого источника?",
        "Какие источники дают лучших кандидатов?",
        "ROI по каналам привлечения?"
    ],
    "report": {
        "report_title": "Source Quality & ROI Analysis",
        "main_metric": {
            "label": "Best Source Conversion (%)",
            "value": {
                "operation": "max",
                "entity": "source_conversion_rates"
            },
            "real_value": 15.6
        },
        "secondary_metrics": [
            {
                "label": "Average Source ROI",
                "value": {
                    "operation": "avg",
                    "entity": "source_roi"
                },
                "real_value": 240
            },
            {
                "label": "Cost per Hire ($)",
                "value": {
                    "operation": "avg",
                    "entity": "cost_per_hire"
                },
                "real_value": 1250
            }
        ],
        "chart": {
            "graph_description": "Conversion rate vs cost per candidate by source",
            "chart_type": "scatter",
            "x_axis_name": "Cost per Candidate ($)",
            "y_axis_name": "Conversion Rate (%)",
            "x_axis": {"operation": "field", "field": "cost_per_candidate"},
            "y_axis": {
                "operation": "avg",
                "entity": "source_conversion_rates",
                "group_by": {"field": "source_name"}
            },
            "real_data": {
                "labels": ["Referral", "LinkedIn", "HeadHunter", "Direct", "Agency", "Indeed"],
                "values": [15.6, 8.2, 6.1, 4.7, 3.2, 2.1],
                "title": "Source Performance Matrix"
            }
        }
    }
},

{
    "questions": [
        "Какая динамика найма за год?",
        "Улучшаются ли наши показатели?",
        "Есть ли рост эффективности?"
    ],
    "report": {
        "report_title": "Annual Performance Trends",
        "main_metric": {
            "label": "YoY Growth (%)",
            "value": {
                "operation": "avg",
                "entity": "yearly_growth"
            },
            "real_value": 23.5
        },
        "secondary_metrics": [
            {
                "label": "Conversion Improvement (%)",
                "value": {
                    "operation": "avg",
                    "entity": "conversion_improvement"
                },
                "real_value": 12.3
            },
            {
                "label": "Time to Hire Reduction (days)",
                "value": {
                    "operation": "avg",
                    "entity": "time_to_hire_reduction"
                },
                "real_value": 8.2
            }
        ],
        "chart": {
            "graph_description": "Key metrics progression over 12 months",
            "chart_type": "line",
            "x_axis_name": "Month",
            "y_axis_name": "Performance Index",
            "x_axis": {"operation": "date_trunc", "field": "created"},
            "y_axis": {
                "operation": "avg",
                "entity": "performance_index",
                "group_by": {"field": "month"}
            },
            "real_data": {
                "labels": ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                "values": [100, 105, 98, 112, 118, 103, 125, 134, 128, 141, 156, 162],
                "title": "Performance Growth Trend"
            }
        }
    }
},

{
    "questions": [
        "Сколько движений по воронке делают рекрутеры?",
        "Кто активнее работает с кандидатами?",
        "Какая активность в процессах?"
    ],
    "report": {
        "report_title": "Pipeline Activity Analysis",
        "main_metric": {
            "label": "Total Pipeline Moves",
            "value": {
                "operation": "sum",
                "entity": "moves_by_recruiter"
            },
            "real_value": 847
        },
        "secondary_metrics": [
            {
                "label": "Moves per Day",
                "value": {
                    "operation": "avg",
                    "entity": "daily_moves"
                },
                "real_value": 28.2
            },
            {
                "label": "Most Active Recruiter Moves",
                "value": {
                    "operation": "max",
                    "entity": "moves_by_recruiter"
                },
                "real_value": 234
            }
        ],
        "chart": {
            "graph_description": "Pipeline moves by recruiter",
            "chart_type": "bar",
            "x_axis_name": "Recruiter",
            "y_axis_name": "Pipeline Moves",
            "x_axis": {"operation": "field", "field": "recruiter_name"},
            "y_axis": {
                "operation": "sum",
                "entity": "moves_by_recruiter",
                "group_by": {"field": "recruiter_name"}
            },
            "real_data": {
                "labels": ["Анастасия Богач", "Михаил Танский", "Виталий Глибин", "Алина Петрова", "София Данилова"],
                "values": [234, 198, 176, 134, 105],
                "title": "Pipeline Activity Levels"
            }
        }
    }
},

{
    "questions": [
        "Какие позиции самые сложные для закрытия?",
        "Где у нас проблемы с наймом?",
        "Какие роли требуют больше времени?"
    ],
    "report": {
        "report_title": "Position Difficulty Analysis",
        "main_metric": {
            "label": "Average Time to Fill (days)",
            "value": {
                "operation": "avg",
                "entity": "time_to_fill_by_position"
            },
            "real_value": 52.3
        },
        "secondary_metrics": [
            {
                "label": "Most Difficult Position (days)",
                "value": {
                    "operation": "max",
                    "entity": "time_to_fill_by_position"
                },
                "real_value": 89.5
            },
            {
                "label": "Success Rate (%)",
                "value": {
                    "operation": "avg",
                    "entity": "position_success_rate"
                },
                "real_value": 68.4
            }
        ],
        "chart": {
            "graph_description": "Time to fill by position type",
            "chart_type": "bar",
            "x_axis_name": "Position",
            "y_axis_name": "Days to Fill",
            "x_axis": {"operation": "field", "field": "position_name"},
            "y_axis": {
                "operation": "avg",
                "entity": "time_to_fill_by_position",
                "group_by": {"field": "position_name"}
            },
            "real_data": {
                "labels": ["Senior Python Developer", "Java Developer", "QA Engineer", "Designer", "Sales Manager"],
                "values": [89.5, 67.2, 45.1, 38.7, 21.3],
                "title": "Position Complexity"
            }
        }
    }
},

{
    "questions": [
        "Какой процент кандидатов доходит до оффера?",
        "Где теряется больше всего кандидатов?",
        "Эффективность воронки найма?"
    ],
    "report": {
        "report_title": "Funnel Conversion Analysis",
        "main_metric": {
            "label": "Overall Funnel Efficiency (%)",
            "value": {
                "operation": "avg",
                "entity": "funnel_efficiency"
            },
            "real_value": 31.7
        },
        "secondary_metrics": [
            {
                "label": "Application to Interview (%)",
                "value": {
                    "operation": "avg",
                    "entity": "app_to_interview_rate"
                },
                "real_value": 68.3
            },
            {
                "label": "Interview to Offer (%)",
                "value": {
                    "operation": "avg",
                    "entity": "interview_to_offer_rate"
                },
                "real_value": 46.4
            }
        ],
        "chart": {
            "graph_description": "Conversion rates between funnel stages",
            "chart_type": "line",
            "x_axis_name": "Funnel Stage",
            "y_axis_name": "Conversion Rate (%)",
            "x_axis": {"operation": "field", "field": "stage_name"},
            "y_axis": {
                "operation": "avg",
                "entity": "stage_conversion_rates",
                "group_by": {"field": "stage_name"}
            },
            "real_data": {
                "labels": ["Applied", "Screened", "Interview", "Technical", "Final", "Offer", "Hired"],
                "values": [100, 68.3, 45.2, 31.7, 22.4, 15.8, 12.6],
                "title": "Funnel Drop-off Analysis"
            }
        }
    }
},

{
    "questions": [
        "Когда у нас пики активности в течение недели?",
        "В какие дни лучше связываться с кандидатами?",
        "Есть ли паттерны в поведении кандидатов?"
    ],
    "report": {
        "report_title": "Weekly Activity Patterns",
        "main_metric": {
            "label": "Peak Day Activity",
            "value": {
                "operation": "max",
                "entity": "daily_activity"
            },
            "real_value": 47
        },
        "secondary_metrics": [
            {
                "label": "Weekend Activity (%)",
                "value": {
                    "operation": "avg",
                    "entity": "weekend_activity_ratio"
                },
                "real_value": 12.3
            },
            {
                "label": "Best Response Day",
                "value": {
                    "operation": "max",
                    "entity": "response_rate_by_day"
                },
                "real_value": 89.2
            }
        ],
        "chart": {
            "graph_description": "Activity distribution by day of week",
            "chart_type": "bar",
            "x_axis_name": "Day of Week",
            "y_axis_name": "Activity Level",
            "x_axis": {"operation": "field", "field": "day_name"},
            "y_axis": {
                "operation": "sum",
                "entity": "daily_activity",
                "group_by": {"field": "day_of_week"}
            },
            "real_data": {
                "labels": ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"],
                "values": [42, 47, 45, 44, 38, 8, 6],
                "title": "Weekly Activity Pattern"
            }
        }
    }
},

{
    "questions": [
        "Насколько качественные кандидаты из разных источников?",
        "Какие источники дают лучшее качество?",
        "Стоит ли инвестировать больше в определенные каналы?"
    ],
    "report": {
        "report_title": "Source Quality Matrix",
        "main_metric": {
            "label": "Average Source Quality Score",
            "value": {
                "operation": "avg",
                "entity": "source_quality_score"
            },
            "real_value": 7.4
        },
        "secondary_metrics": [
            {
                "label": "Premium Source Quality",
                "value": {
                    "operation": "max",
                    "entity": "source_quality_score"
                },
                "real_value": 9.2
            },
            {
                "label": "Quality Consistency",
                "value": {
                    "operation": "avg",
                    "entity": "quality_consistency"
                },
                "real_value": 0.78
            }
        ],
        "chart": {
            "graph_description": "Quality score vs volume by source",
            "chart_type": "scatter",
            "x_axis_name": "Candidate Volume",
            "y_axis_name": "Quality Score",
            "x_axis": {"operation": "count", "field": "candidate_count"},
            "y_axis": {
                "operation": "avg",
                "entity": "source_quality_score",
                "group_by": {"field": "source_name"}
            },
            "real_data": {
                "labels": ["Referral", "LinkedIn", "Direct", "HeadHunter", "Agency", "Indeed"],
                "values": [9.2, 8.1, 7.8, 6.9, 6.2, 5.4],
                "title": "Source Quality vs Volume"
            }
        }
    }
},

{
    "questions": [
        "Какая конверсия по регионам?",
        "В каких городах проще найти кандидатов?",
        "Географические различия в найме?"
    ],
    "report": {
        "report_title": "Geographic Performance Analysis",
        "main_metric": {
            "label": "Best Regional Conversion (%)",
            "value": {
                "operation": "max",
                "entity": "regional_conversion"
            },
            "real_value": 18.7
        },
        "secondary_metrics": [
            {
                "label": "Active Regions",
                "value": {
                    "operation": "count",
                    "entity": "active_regions"
                },
                "real_value": 12
            },
            {
                "label": "Regional Coverage (%)",
                "value": {
                    "operation": "avg",
                    "entity": "regional_coverage"
                },
                "real_value": 67.3
            }
        ],
        "chart": {
            "graph_description": "Performance metrics by region",
            "chart_type": "bar",
            "x_axis_name": "Region",
            "y_axis_name": "Conversion Rate (%)",
            "x_axis": {"operation": "field", "field": "region_name"},
            "y_axis": {
                "operation": "avg",
                "entity": "regional_conversion",
                "group_by": {"field": "region_name"}
            },
            "real_data": {
                "labels": ["Москва", "СПб", "Екатеринбург", "Новосибирск", "Казань", "Нижний Новгород"],
                "values": [18.7, 14.2, 12.8, 9.3, 8.1, 6.9],
                "title": "Regional Performance"
            }
        }
    }
},

# ==========================================
# CATEGORY 3: OPERATIONAL INSIGHTS (21-30)
# ==========================================

{
    "questions": [
        "Сколько кандидатов добавили рекрутеры за месяц?",
        "Кто активнее всех пополняет воронку?",
        "Какая скорость набора кандидатов?"
    ],
    "report": {
        "report_title": "Candidate Acquisition Rate",
        "main_metric": {
            "label": "Total Added This Month",
            "value": {
                "operation": "sum",
                "entity": "applicants_added_by_recruiter",
                "filter": {"field": "created", "op": "gte", "value": "2025-06-01T00:00:00"}
            },
            "real_value": 67
        },
        "secondary_metrics": [
            {
                "label": "Daily Addition Rate",
                "value": {
                    "operation": "avg",
                    "entity": "daily_additions"
                },
                "real_value": 3.7
            },
            {
                "label": "Top Contributor",
                "value": {
                    "operation": "max",
                    "entity": "applicants_added_by_recruiter"
                },
                "real_value": 23
            }
        ],
        "chart": {
            "graph_description": "Candidates added by each recruiter this month",
            "chart_type": "bar",
            "x_axis_name": "Recruiter",
            "y_axis_name": "Candidates Added",
            "x_axis": {"operation": "field", "field": "recruiter_name"},
            "y_axis": {
                "operation": "count",
                "entity": "applicants_added_by_recruiter",
                "filter": {"field": "created", "op": "gte", "value": "2025-06-01T00:00:00"},
                "group_by": {"field": "recruiter_name"}
            },
            "real_data": {
                "labels": ["Анастасия Богач", "Михаил Танский", "Виталий Глибин", "Алина Петрова", "София Данилова"],
                "values": [23, 18, 12, 9, 5],
                "title": "Monthly Acquisition Activity"
            }
        }
    }
},

{
    "questions": [
        "Какие вакансии остались без кандидатов?",
        "Где нужно усилить поиск?",
        "Какие позиции требуют внимания?"
    ],
    "report": {
        "report_title": "Empty Vacancies Alert",
        "main_metric": {
            "label": "Vacancies Without Candidates",
            "value": {
                "operation": "count",
                "entity": "empty_vacancies"
            },
            "real_value": 8
        },
        "secondary_metrics": [
            {
                "label": "Critical Empty (High Priority)",
                "value": {
                    "operation": "count",
                    "entity": "critical_empty_vacancies"
                },
                "real_value": 3
            },
            {
                "label": "Days Without Activity",
                "value": {
                    "operation": "avg",
                    "entity": "days_without_activity"
                },
                "real_value": 12.4
            }
        ],
        "chart": {
            "graph_description": "Empty vacancies by department",
            "chart_type": "pie",
            "x_axis_name": "Department",
            "y_axis_name": "Empty Vacancies",
            "x_axis": {"operation": "field", "field": "department_name"},
            "y_axis": {
                "operation": "count",
                "entity": "empty_vacancies",
                "group_by": {"field": "department_name"}
            },
            "real_data": {
                "labels": ["IT", "Sales", "Marketing", "HR"],
                "values": [4, 2, 1, 1],
                "title": "Empty Positions by Department"
            }
        }
    }
},

{
    "questions": [
        "Сколько времени уходит на каждый этап найма?",
        "Где процесс можно ускорить?",
        "Какие этапы самые медленные?"
    ],
    "report": {
        "report_title": "Process Efficiency Analysis",
        "main_metric": {
            "label": "Average Process Duration (days)",
            "value": {
                "operation": "avg",
                "entity": "total_process_time"
            },
            "real_value": 34.6
        },
        "secondary_metrics": [
            {
                "label": "Fastest Process (days)",
                "value": {
                    "operation": "min",
                    "entity": "total_process_time"
                },
                "real_value": 12.3
            },
            {
                "label": "Process Efficiency (%)",
                "value": {
                    "operation": "avg",
                    "entity": "process_efficiency"
                },
                "real_value": 73.2
            }
        ],
        "chart": {
            "graph_description": "Time breakdown by process stage",
            "chart_type": "bar",
            "x_axis_name": "Process Stage",
            "y_axis_name": "Average Days",
            "x_axis": {"operation": "field", "field": "process_stage"},
            "y_axis": {
                "operation": "avg",
                "entity": "stage_duration",
                "group_by": {"field": "process_stage"}
            },
            "real_data": {
                "labels": ["Sourcing", "Screening", "Interview Scheduling", "Interview Process", "Decision Making", "Offer Process"],
                "values": [5.2, 3.1, 2.8, 8.4, 7.3, 4.8],
                "title": "Process Stage Duration"
            }
        }
    }
},

{
    "questions": [
        "Какая загрузка вакансий кандидатами?",
        "Где слишком много кандидатов?",
        "Нужно ли перераспределение?"
    ],
    "report": {
        "report_title": "Vacancy Load Distribution",
        "main_metric": {
            "label": "Average Candidates per Vacancy",
            "value": {
                "operation": "avg",
                "entity": "candidates_per_vacancy"
            },
            "real_value": 3.4
        },
        "secondary_metrics": [
            {
                "label": "Overloaded Vacancies",
                "value": {
                    "operation": "count",
                    "entity": "overloaded_vacancies"
                },
                "real_value": 6
            },
            {
                "label": "Max Load per Vacancy",
                "value": {
                    "operation": "max",
                    "entity": "candidates_per_vacancy"
                },
                "real_value": 12
            }
        ],
        "chart": {
            "graph_description": "Candidate load distribution across vacancies",
            "chart_type": "bar",
            "x_axis_name": "Load Range",
            "y_axis_name": "Number of Vacancies",
            "x_axis": {"operation": "field", "field": "load_range"},
            "y_axis": {
                "operation": "count",
                "entity": "vacancy_load_distribution",
                "group_by": {"field": "load_range"}
            },
            "real_data": {
                "labels": ["0 кандидатов", "1-2 кандидата", "3-5 кандидатов", "6-10 кандидатов", "10+ кандидатов"],
                "values": [8, 15, 12, 5, 2],
                "title": "Vacancy Load Distribution"
            }
        }
    }
},

{
    "questions": [
        "Сколько интервью назначено на ближайшую неделю?",
        "Какая нагрузка на интервьюеров?",
        "Успеваем ли мы с интервью?"
    ],
    "report": {
        "report_title": "Interview Pipeline Load",
        "main_metric": {
            "label": "Scheduled Interviews (Next 7 Days)",
            "value": {
                "operation": "count",
                "entity": "scheduled_interviews"
            },
            "real_value": 28
        },
        "secondary_metrics": [
            {
                "label": "Daily Interview Average",
                "value": {
                    "operation": "avg",
                    "entity": "daily_interviews"
                },
                "real_value": 4.0
            },
            {
                "label": "Peak Day Load",
                "value": {
                    "operation": "max",
                    "entity": "daily_interviews"
                },
                "real_value": 8
            }
        ],
        "chart": {
            "graph_description": "Interview distribution by day of week",
            "chart_type": "line",
            "x_axis_name": "Day",
            "y_axis_name": "Scheduled Interviews",
            "x_axis": {"operation": "field", "field": "day_name"},
            "y_axis": {
                "operation": "count",
                "entity": "daily_interviews",
                "group_by": {"field": "day_of_week"}
            },
            "real_data": {
                "labels": ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"],
                "values": [6, 8, 5, 4, 3, 1, 1],
                "title": "Interview Schedule Load"
            }
        }
    }
},

{
    "questions": [
        "Какая конверсия из резюме в интервью?",
        "Сколько резюме нужно для одного интервью?",
        "Эффективность скрининга?"
    ],
    "report": {
        "report_title": "Resume to Interview Conversion",
        "main_metric": {
            "label": "Resume-to-Interview Rate (%)",
            "value": {
                "operation": "avg",
                "entity": "resume_to_interview_rate"
            },
            "real_value": 23.8
        },
        "secondary_metrics": [
            {
                "label": "Resumes per Interview",
                "value": {
                    "operation": "avg",
                    "entity": "resumes_per_interview"
                },
                "real_value": 4.2
            },
            {
                "label": "Screening Efficiency (%)",
                "value": {
                    "operation": "avg",
                    "entity": "screening_efficiency"
                },
                "real_value": 78.4
            }
        ],
        "chart": {
            "graph_description": "Conversion rates by position type",
            "chart_type": "bar",
            "x_axis_name": "Position Type",
            "y_axis_name": "Conversion Rate (%)",
            "x_axis": {"operation": "field", "field": "position_type"},
            "y_axis": {
                "operation": "avg",
                "entity": "resume_to_interview_rate",
                "group_by": {"field": "position_type"}
            },
            "real_data": {
                "labels": ["Sales", "Marketing", "HR", "QA", "Design", "Development"],
                "values": [34.2, 28.7, 26.1, 23.8, 19.4, 15.6],
                "title": "Screening Success by Role"
            }
        }
    }
},

{
    "questions": [
        "Сколько офферов было отклонено?",
        "Почему кандидаты отказываются?",
        "Какая успешность офферов?"
    ],
    "report": {
        "report_title": "Offer Acceptance Analysis",
        "main_metric": {
            "label": "Offer Acceptance Rate (%)",
            "value": {
                "operation": "avg",
                "entity": "offer_acceptance_rate"
            },
            "real_value": 78.9
        },
        "secondary_metrics": [
            {
                "label": "Rejected Offers",
                "value": {
                    "operation": "count",
                    "entity": "rejected_offers"
                },
                "real_value": 4
            },
            {
                "label": "Counter-offers Received",
                "value": {
                    "operation": "count",
                    "entity": "counter_offers"
                },
                "real_value": 2
            }
        ],
        "chart": {
            "graph_description": "Offer outcomes distribution",
            "chart_type": "pie",
            "x_axis_name": "Outcome",
            "y_axis_name": "Count",
            "x_axis": {"operation": "field", "field": "offer_outcome"},
            "y_axis": {
                "operation": "count",
                "entity": "offer_outcomes",
                "group_by": {"field": "offer_outcome"}
            },
            "real_data": {
                "labels": ["Accepted", "Rejected - Salary", "Rejected - Culture", "Rejected - Other", "Counter-offer"],
                "values": [15, 2, 1, 1, 2],
                "title": "Offer Resolution"
            }
        }
    }
},

{
    "questions": [
        "Какие навыки самые востребованные?",
        "Что чаще всего ищут в кандидатах?",
        "Тренды в требованиях?"
    ],
    "report": {
        "report_title": "Skills Demand Analysis",
        "main_metric": {
            "label": "Most Requested Skills",
            "value": {
                "operation": "count",
                "entity": "skills_demand"
            },
            "real_value": 23
        },
        "secondary_metrics": [
            {
                "label": "Unique Skills Required",
                "value": {
                    "operation": "count",
                    "entity": "unique_skills"
                },
                "real_value": 67
            },
            {
                "label": "Skills Gap Index",
                "value": {
                    "operation": "avg",
                    "entity": "skills_gap"
                },
                "real_value": 0.34
            }
        ],
        "chart": {
            "graph_description": "Top skills in demand",
            "chart_type": "bar",
            "x_axis_name": "Skill",
            "y_axis_name": "Mentions in Vacancies",
            "x_axis": {"operation": "field", "field": "skill_name"},
            "y_axis": {
                "operation": "count",
                "entity": "skills_demand",
                "group_by": {"field": "skill_name"}
            },
            "real_data": {
                "labels": ["Python", "JavaScript", "SQL", "Communication", "Leadership", "Project Management", "English", "Teamwork"],
                "values": [23, 18, 15, 34, 12, 19, 28, 25],
                "title": "Skills Demand Ranking"
            }
        }
    }
},

{
    "questions": [
        "Сколько кандидатов возвращается после отказа?",
        "Есть ли повторные заявки?",
        "Работаем ли мы с talent pool?"
    ],
    "report": {
        "report_title": "Candidate Return Analysis",
        "main_metric": {
            "label": "Return Rate (%)",
            "value": {
                "operation": "avg",
                "entity": "candidate_return_rate"
            },
            "real_value": 12.7
        },
        "secondary_metrics": [
            {
                "label": "Returned Candidates",
                "value": {
                    "operation": "count",
                    "entity": "returned_candidates"
                },
                "real_value": 18
            },
            {
                "label": "Success Rate of Returns (%)",
                "value": {
                    "operation": "avg",
                    "entity": "return_success_rate"
                },
                "real_value": 33.3
            }
        ],
        "chart": {
            "graph_description": "Time between applications for returning candidates",
            "chart_type": "bar",
            "x_axis_name": "Time Gap",
            "y_axis_name": "Number of Candidates",
            "x_axis": {"operation": "field", "field": "time_gap_range"},
            "y_axis": {
                "operation": "count",
                "entity": "return_time_distribution",
                "group_by": {"field": "time_gap_range"}
            },
            "real_data": {
                "labels": ["1-3 месяца", "3-6 месяцев", "6-12 месяцев", "12+ месяцев"],
                "values": [2, 6, 7, 3],
                "title": "Return Timeline Distribution"
            }
        }
    }
},

{
    "questions": [
        "Какая нагрузка на систему по дням?",
        "Когда больше всего активности?",
        "Нужно ли масштабирование?"
    ],
    "report": {
        "report_title": "System Load Analysis",
        "main_metric": {
            "label": "Peak Daily Load",
            "value": {
                "operation": "max",
                "entity": "daily_system_load"
            },
            "real_value": 156
        },
        "secondary_metrics": [
            {
                "label": "Average Daily Load",
                "value": {
                    "operation": "avg",
                    "entity": "daily_system_load"
                },
                "real_value": 94.2
            },
            {
                "label": "Load Growth (%)",
                "value": {
                    "operation": "avg",
                    "entity": "load_growth_rate"
                },
                "real_value": 15.3
            }
        ],
        "chart": {
            "graph_description": "System load over the last 30 days",
            "chart_type": "line",
            "x_axis_name": "Date",
            "y_axis_name": "Daily Operations",
            "x_axis": {"operation": "date_trunc", "field": "created"},
            "y_axis": {
                "operation": "sum",
                "entity": "daily_system_load",
                "group_by": {"field": "date"}
            },
            "real_data": {
                "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
                "values": [78, 94, 123, 156],
                "title": "System Load Trend"
            }
        }
    }
},

# ==========================================
# CATEGORY 4: STRATEGIC INSIGHTS (31-40)
# ==========================================

{
    "questions": [
        "Какой ROI от инвестиций в рекрутинг?",
        "Окупаются ли вложения в HR?",
        "Стоимость найма vs ценность кандидата?"
    ],
    "report": {
        "report_title": "Recruitment ROI Analysis",
        "main_metric": {
            "label": "Overall ROI (%)",
            "value": {
                "operation": "avg",
                "entity": "recruitment_roi"
            },
            "real_value": 340
        },
        "secondary_metrics": [
            {
                "label": "Cost per Hire ($)",
                "value": {
                    "operation": "avg",
                    "entity": "cost_per_hire"
                },
                "real_value": 2850
            },
            {
                "label": "Value per Hire ($)",
                "value": {
                    "operation": "avg",
                    "entity": "value_per_hire"
                },
                "real_value": 9690
            }
        ],
        "chart": {
            "graph_description": "ROI breakdown by investment category",
            "chart_type": "bar",
            "x_axis_name": "Investment Category",
            "y_axis_name": "ROI (%)",
            "x_axis": {"operation": "field", "field": "investment_category"},
            "y_axis": {
                "operation": "avg",
                "entity": "category_roi",
                "group_by": {"field": "investment_category"}
            },
            "real_data": {
                "labels": ["LinkedIn Premium", "Referral Program", "Job Boards", "Recruiter Salaries", "Agency Fees", "Tools & Software"],
                "values": [480, 650, 290, 340, 180, 420],
                "title": "Investment ROI by Category"
            }
        }
    }
},

{
    "questions": [
        "Какие тренды в рынке труда мы видим?",
        "Изменилось ли поведение кандидатов?",
        "Что происходит с конкуренцией?"
    ],
    "report": {
        "report_title": "Market Trends Analysis",
        "main_metric": {
            "label": "Market Competition Index",
            "value": {
                "operation": "avg",
                "entity": "market_competition"
            },
            "real_value": 7.8
        },
        "secondary_metrics": [
            {
                "label": "Salary Inflation (%)",
                "value": {
                    "operation": "avg",
                    "entity": "salary_inflation"
                },
                "real_value": 12.4
            },
            {
                "label": "Remote Work Demand (%)",
                "value": {
                    "operation": "avg",
                    "entity": "remote_work_demand"
                },
                "real_value": 67.8
            }
        ],
        "chart": {
            "graph_description": "Market trends over the last 12 months",
            "chart_type": "line",
            "x_axis_name": "Month",
            "y_axis_name": "Index Value",
            "x_axis": {"operation": "date_trunc", "field": "created"},
            "y_axis": {
                "operation": "avg",
                "entity": "market_trends",
                "group_by": {"field": "month"}
            },
            "real_data": {
                "labels": ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                "values": [6.2, 6.8, 7.1, 7.5, 7.9, 8.2, 8.0, 7.8, 7.6, 7.9, 8.1, 7.8],
                "title": "Market Competition Trend"
            }
        }
    }
},

{
    "questions": [
        "Какие навыки будут нужны в будущем?",
        "К чему готовиться в найме?",
        "Что изменится в требованиях?"
    ],
    "report": {
        "report_title": "Future Skills Forecast",
        "main_metric": {
            "label": "Emerging Skills Growth (%)",
            "value": {
                "operation": "avg",
                "entity": "emerging_skills_growth"
            },
            "real_value": 45.6
        },
        "secondary_metrics": [
            {
                "label": "Traditional Skills Decline (%)",
                "value": {
                    "operation": "avg",
                    "entity": "traditional_skills_decline"
                },
                "real_value": -8.3
            },
            {
                "label": "Skills Adaptation Rate (%)",
                "value": {
                    "operation": "avg",
                    "entity": "skills_adaptation_rate"
                },
                "real_value": 72.1
            }
        ],
        "chart": {
            "graph_description": "Skills demand forecast for next 12 months",
            "chart_type": "bar",
            "x_axis_name": "Skill Category",
            "y_axis_name": "Projected Growth (%)",
            "x_axis": {"operation": "field", "field": "skill_category"},
            "y_axis": {
                "operation": "avg",
                "entity": "skills_forecast",
                "group_by": {"field": "skill_category"}
            },
            "real_data": {
                "labels": ["AI/ML", "Data Science", "Cloud Technologies", "Cybersecurity", "Soft Skills", "Traditional IT"],
                "values": [78.2, 56.4, 43.7, 39.1, 28.6, -8.3],
                "title": "Skills Demand Forecast"
            }
        }
    }
},

{
    "questions": [
        "Какой talent pool у нас накопился?",
        "Сколько кандидатов в резерве?",
        "Можем ли быстро закрыть срочные позиции?"
    ],
    "report": {
        "report_title": "Talent Pool Analysis",
        "main_metric": {
            "label": "Total Talent Pool",
            "value": {
                "operation": "count",
                "entity": "talent_pool_candidates"
            },
            "real_value": 234
        },
        "secondary_metrics": [
            {
                "label": "Active Pool (%)",
                "value": {
                    "operation": "avg",
                "entity": "active_pool_ratio"
                },
                "real_value": 67.5
            },
            {
                "label": "Pool Conversion Rate (%)",
                "value": {
                    "operation": "avg",
                    "entity": "pool_conversion_rate"
                },
                "real_value": 23.8
            }
        ],
        "chart": {
            "graph_description": "Talent pool distribution by specialization",
            "chart_type": "pie",
            "x_axis_name": "Specialization",
            "y_axis_name": "Candidates",
            "x_axis": {"operation": "field", "field": "specialization"},
            "y_axis": {
                "operation": "count",
                "entity": "talent_pool_candidates",
                "group_by": {"field": "specialization"}
            },
            "real_data": {
                "labels": ["Development", "QA", "Design", "Marketing", "Sales", "Management", "Other"],
                "values": [78, 45, 32, 28, 24, 18, 9],
                "title": "Talent Pool Composition"
            }
        }
    }
},

{
    "questions": [
        "Какие риски в текущих процессах найма?",
        "Где можем потерять кандидатов?",
        "Что угрожает нашей эффективности?"
    ],
    "report": {
        "report_title": "Recruitment Risk Assessment",
        "main_metric": {
            "label": "Overall Risk Score",
            "value": {
                "operation": "avg",
                "entity": "recruitment_risk_score"
            },
            "real_value": 6.2
        },
        "secondary_metrics": [
            {
                "label": "High Risk Areas",
                "value": {
                    "operation": "count",
                    "entity": "high_risk_areas"
                },
                "real_value": 3
            },
            {
                "label": "Risk Mitigation (%)",
                "value": {
                    "operation": "avg",
                    "entity": "risk_mitigation"
                },
                "real_value": 78.4
            }
        ],
        "chart": {
            "graph_description": "Risk level by process area",
            "chart_type": "bar",
            "x_axis_name": "Process Area",
            "y_axis_name": "Risk Score (1-10)",
            "x_axis": {"operation": "field", "field": "process_area"},
            "y_axis": {
                "operation": "avg",
                "entity": "area_risk_score",
                "group_by": {"field": "process_area"}
            },
            "real_data": {
                "labels": ["Candidate Experience", "Interview Process", "Offer Process", "Sourcing", "Screening", "Onboarding"],
                "values": [8.2, 7.1, 6.8, 5.9, 4.7, 3.8],
                "title": "Risk Assessment by Area"
            }
        }
    }
},

{
    "questions": [
        "Как изменилось качество кандидатов?",
        "Лучше или хуже кандидаты чем раньше?",
        "Динамика качества найма?"
    ],
    "report": {
        "report_title": "Candidate Quality Trends",
        "main_metric": {
            "label": "Average Quality Score",
            "value": {
                "operation": "avg",
                "entity": "candidate_quality_score"
            },
            "real_value": 7.6
        },
        "secondary_metrics": [
            {
                "label": "Quality Improvement (%)",
                "value": {
                    "operation": "avg",
                    "entity": "quality_improvement"
                },
                "real_value": 8.7
            },
            {
                "label": "Premium Candidates (%)",
                "value": {
                    "operation": "avg",
                    "entity": "premium_candidates_ratio"
                },
                "real_value": 23.4
            }
        ],
        "chart": {
            "graph_description": "Quality score trends over time",
            "chart_type": "line",
            "x_axis_name": "Month",
            "y_axis_name": "Quality Score",
            "x_axis": {"operation": "date_trunc", "field": "created"},
            "y_axis": {
                "operation": "avg",
                "entity": "monthly_quality_score",
                "group_by": {"field": "month"}
            },
            "real_data": {
                "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                "values": [7.1, 7.3, 7.2, 7.5, 7.8, 7.6],
                "title": "Quality Score Evolution"
            }
        }
    }
},

{
    "questions": [
        "Сколько стоит удержать хорошего сотрудника vs найти нового?",
        "Экономика текучести кадров?",
        "ROI программ удержания?"
    ],
    "report": {
        "report_title": "Retention vs Acquisition Cost",
        "main_metric": {
            "label": "Retention Cost Savings ($)",
            "value": {
                "operation": "avg",
                "entity": "retention_savings"
            },
            "real_value": 8450
        },
        "secondary_metrics": [
            {
                "label": "Replacement Cost ($)",
                "value": {
                    "operation": "avg",
                    "entity": "replacement_cost"
                },
                "real_value": 12300
            },
            {
                "label": "Retention ROI (%)",
                "value": {
                    "operation": "avg",
                    "entity": "retention_roi"
                },
                "real_value": 280
            }
        ],
        "chart": {
            "graph_description": "Cost comparison: retention vs replacement",
            "chart_type": "bar",
            "x_axis_name": "Position Level",
            "y_axis_name": "Cost ($)",
            "x_axis": {"operation": "field", "field": "position_level"},
            "y_axis": {
                "operation": "avg",
                "entity": "position_costs",
                "group_by": {"field": "position_level"}
            },
            "real_data": {
                "labels": ["Junior", "Middle", "Senior", "Lead", "Manager"],
                "values": [5200, 8900, 12300, 18700, 24500],
                "title": "Replacement Cost by Level"
            }
        }
    }
},

{
    "questions": [
        "Насколько конкурентоспособны наши предложения?",
        "Выигрываем ли мы битву за таланты?",
        "Где проигрываем конкурентам?"
    ],
    "report": {
        "report_title": "Competitive Position Analysis",
        "main_metric": {
            "label": "Win Rate vs Competitors (%)",
            "value": {
                "operation": "avg",
                "entity": "competitive_win_rate"
            },
            "real_value": 68.3
        },
        "secondary_metrics": [
            {
                "label": "Offer Competitiveness Score",
                "value": {
                    "operation": "avg",
                    "entity": "offer_competitiveness"
                },
                "real_value": 7.4
            },
            {
                "label": "Brand Attraction Index",
                "value": {
                    "operation": "avg",
                    "entity": "brand_attraction"
                },
                "real_value": 8.1
            }
        ],
        "chart": {
            "graph_description": "Competitive performance by offer component",
            "chart_type": "radar",
            "x_axis_name": "Offer Component",
            "y_axis_name": "Competitiveness Score",
            "x_axis": {"operation": "field", "field": "offer_component"},
            "y_axis": {
                "operation": "avg",
                "entity": "component_score",
                "group_by": {"field": "offer_component"}
            },
            "real_data": {
                "labels": ["Salary", "Benefits", "Culture", "Growth", "Flexibility", "Technology"],
                "values": [7.8, 8.2, 8.9, 7.1, 8.6, 6.4],
                "title": "Competitive Strength Profile"
            }
        }
    }
},

{
    "questions": [
        "Какую ценность создает HR команда?",
        "Влияние найма на бизнес результаты?",
        "Измеримый вклад рекрутинга?"
    ],
    "report": {
        "report_title": "HR Business Impact Analysis",
        "main_metric": {
            "label": "Business Impact Score",
            "value": {
                "operation": "avg",
                "entity": "hr_business_impact"
            },
            "real_value": 8.7
        },
        "secondary_metrics": [
            {
                "label": "Revenue per Hire ($)",
                "value": {
                    "operation": "avg",
                    "entity": "revenue_per_hire"
                },
                "real_value": 145000
            },
            {
                "label": "Time to Productivity (days)",
                "value": {
                    "operation": "avg",
                    "entity": "time_to_productivity"
                },
                "real_value": 67
            }
        ],
        "chart": {
            "graph_description": "Business impact by hire category",
            "chart_type": "bar",
            "x_axis_name": "Hire Category",
            "y_axis_name": "Impact Score",
            "x_axis": {"operation": "field", "field": "hire_category"},
            "y_axis": {
                "operation": "avg",
                "entity": "category_impact",
                "group_by": {"field": "hire_category"}
            },
            "real_data": {
                "labels": ["Key Positions", "Revenue Generators", "Strategic Roles", "Support Functions", "Replacement Hires"],
                "values": [9.6, 9.2, 8.8, 7.1, 6.4],
                "title": "Impact by Hire Type"
            }
        }
    }
},

{
    "questions": [
        "Какой прогноз потребности в найме?",
        "Сколько нужно нанять в следующем квартале?",
        "Планирование ресурсов на рекрутинг?"
    ],
    "report": {
        "report_title": "Hiring Forecast & Planning",
        "main_metric": {
            "label": "Projected Q3 Hires",
            "value": {
                "operation": "sum",
                "entity": "projected_hires"
            },
            "real_value": 34
        },
        "secondary_metrics": [
            {
                "label": "Resource Requirement (%)",
                "value": {
                    "operation": "avg",
                    "entity": "resource_requirement"
                },
                "real_value": 127
            },
            {
                "label": "Budget Projection ($)",
                "value": {
                    "operation": "sum",
                    "entity": "budget_projection"
                },
                "real_value": 97000
            }
        ],
        "chart": {
            "graph_description": "Hiring forecast by department",
            "chart_type": "bar",
            "x_axis_name": "Department",
            "y_axis_name": "Projected Hires",
            "x_axis": {"operation": "field", "field": "department_name"},
            "y_axis": {
                "operation": "sum",
                "entity": "department_forecast",
                "group_by": {"field": "department_name"}
            },
            "real_data": {
                "labels": ["Engineering", "Sales", "Marketing", "Product", "Operations", "Support"],
                "values": [15, 8, 4, 3, 2, 2],
                "title": "Q3 Hiring Plan by Department"
            }
        }
    }
},

# ==========================================
# CATEGORY 5: ADVANCED ANALYTICS (41-50)
# ==========================================

{
    "questions": [
        "Какие паттерны успешного найма?",
        "Что объединяет лучшие закрытия?",
        "Модель идеального процесса?"
    ],
    "report": {
        "report_title": "Success Pattern Analysis",
        "main_metric": {
            "label": "Pattern Recognition Score",
            "value": {
                "operation": "avg",
                "entity": "pattern_recognition_score"
            },
            "real_value": 0.87
        },
        "secondary_metrics": [
            {
                "label": "Success Predictors Count",
                "value": {
                    "operation": "count",
                    "entity": "success_predictors"
                },
                "real_value": 12
            },
            {
                "label": "Pattern Reliability (%)",
                "value": {
                    "operation": "avg",
                    "entity": "pattern_reliability"
                },
                "real_value": 89.4
            }
        ],
        "chart": {
            "graph_description": "Success factors importance ranking",
            "chart_type": "bar",
            "x_axis_name": "Success Factor",
            "y_axis_name": "Importance Score",
            "x_axis": {"operation": "field", "field": "success_factor"},
            "y_axis": {
                "operation": "avg",
                "entity": "factor_importance",
                "group_by": {"field": "success_factor"}
            },
            "real_data": {
                "labels": ["Source Quality", "Response Time", "Interview Experience", "Offer Timing", "Cultural Fit", "Skill Match"],
                "values": [0.94, 0.87, 0.82, 0.78, 0.76, 0.72],
                "title": "Success Factor Rankings"
            }
        }
    }
},

{
    "questions": [
        "Можем ли предсказать успех кандидата?",
        "Какие признаки указывают на good hire?",
        "Модель прогнозирования качества?"
    ],
    "report": {
        "report_title": "Predictive Hiring Model",
        "main_metric": {
            "label": "Model Accuracy (%)",
            "value": {
                "operation": "avg",
                "entity": "prediction_accuracy"
            },
            "real_value": 84.7
        },
        "secondary_metrics": [
            {
                "label": "High Confidence Predictions (%)",
                "value": {
                    "operation": "avg",
                    "entity": "high_confidence_ratio"
                },
                "real_value": 67.3
            },
            {
                "label": "Model Improvement Rate (%)",
                "value": {
                    "operation": "avg",
                    "entity": "model_improvement"
                },
                "real_value": 12.8
            }
        ],
        "chart": {
            "graph_description": "Prediction accuracy by candidate segment",
            "chart_type": "bar",
            "x_axis_name": "Candidate Segment",
            "y_axis_name": "Accuracy (%)",
            "x_axis": {"operation": "field", "field": "candidate_segment"},
            "y_axis": {
                "operation": "avg",
                "entity": "segment_accuracy",
                "group_by": {"field": "candidate_segment"}
            },
            "real_data": {
                "labels": ["Senior Tech", "Mid-level Tech", "Junior Tech", "Sales", "Marketing", "Management"],
                "values": [91.2, 87.4, 82.1, 89.6, 78.3, 85.7],
                "title": "Model Performance by Segment"
            }
        }
    }
},

{
    "questions": [
        "Какие когорты кандидатов самые успешные?",
        "Есть ли различия по периодам найма?",
        "Анализ когорт по времени?"
    ],
    "report": {
        "report_title": "Cohort Performance Analysis",
        "main_metric": {
            "label": "Best Cohort Performance (%)",
            "value": {
                "operation": "max",
                "entity": "cohort_performance"
            },
            "real_value": 94.3
        },
        "secondary_metrics": [
            {
                "label": "Cohort Consistency Score",
                "value": {
                    "operation": "avg",
                    "entity": "cohort_consistency"
                },
                "real_value": 0.78
            },
            {
                "label": "Performance Variance (%)",
                "value": {
                    "operation": "avg",
                    "entity": "performance_variance"
                },
                "real_value": 18.2
            }
        ],
        "chart": {
            "graph_description": "Cohort performance by hiring quarter",
            "chart_type": "line",
            "x_axis_name": "Hiring Quarter",
            "y_axis_name": "Performance Score",
            "x_axis": {"operation": "field", "field": "hiring_quarter"},
            "y_axis": {
                "operation": "avg",
                "entity": "quarterly_cohort_performance",
                "group_by": {"field": "hiring_quarter"}
            },
            "real_data": {
                "labels": ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024", "Q1 2025", "Q2 2025"],
                "values": [78.4, 82.1, 87.6, 91.2, 94.3, 89.7],
                "title": "Quarterly Cohort Performance"
            }
        }
    }
},

{
    "questions": [
        "Какая оптимальная последовательность действий в найме?",
        "Как автоматизировать процесс?",
        "Модель оптимального workflow?"
    ],
    "report": {
        "report_title": "Process Optimization Model",
        "main_metric": {
            "label": "Optimization Potential (%)",
            "value": {
                "operation": "avg",
                "entity": "optimization_potential"
            },
            "real_value": 34.7
        },
        "secondary_metrics": [
            {
                "label": "Automation Opportunities",
                "value": {
                    "operation": "count",
                    "entity": "automation_opportunities"
                },
                "real_value": 8
            },
            {
                "label": "Efficiency Gain Projection (%)",
                "value": {
                    "operation": "avg",
                    "entity": "efficiency_gain"
                },
                "real_value": 28.5
            }
        ],
        "chart": {
            "graph_description": "Optimization impact by process step",
            "chart_type": "bar",
            "x_axis_name": "Process Step",
            "y_axis_name": "Optimization Impact (%)",
            "x_axis": {"operation": "field", "field": "process_step"},
            "y_axis": {
                "operation": "avg",
                "entity": "step_optimization_impact",
                "group_by": {"field": "process_step"}
            },
            "real_data": {
                "labels": ["Initial Screening", "Interview Scheduling", "Decision Making", "Offer Process", "Reference Checks", "Onboarding"],
                "values": [45.2, 38.7, 34.1, 29.8, 22.3, 18.6],
                "title": "Optimization Opportunities"
            }
        }
    }
},

{
    "questions": [
        "Какое влияние внешних факторов на найм?",
        "Как экономика влияет на рекрутинг?",
        "Корреляции с внешними событиями?"
    ],
    "report": {
        "report_title": "External Factors Impact",
        "main_metric": {
            "label": "External Impact Index",
            "value": {
                "operation": "avg",
                "entity": "external_impact_index"
            },
            "real_value": 6.8
        },
        "secondary_metrics": [
            {
                "label": "Economic Sensitivity (%)",
                "value": {
                    "operation": "avg",
                    "entity": "economic_sensitivity"
                },
                "real_value": 23.4
            },
            {
                "label": "Seasonal Variation (%)",
                "value": {
                    "operation": "avg",
                    "entity": "seasonal_variation"
                },
                "real_value": 31.7
            }
        ],
        "chart": {
            "graph_description": "Impact of external factors on hiring metrics",
            "chart_type": "line",
            "x_axis_name": "Time Period",
            "y_axis_name": "Impact Score",
            "x_axis": {"operation": "date_trunc", "field": "created"},
            "y_axis": {
                "operation": "avg",
                "entity": "monthly_external_impact",
                "group_by": {"field": "month"}
            },
            "real_data": {
                "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                "values": [7.2, 6.8, 5.9, 6.4, 7.1, 6.8],
                "title": "External Impact Timeline"
            }
        }
    }
},

{
    "questions": [
        "Какие метрики лучше всего предсказывают успех?",
        "KPI корреляции с результатами?",
        "Система раннего предупреждения?"
    ],
    "report": {
        "report_title": "Leading Indicators Analysis",
        "main_metric": {
            "label": "Strongest Predictor Correlation",
            "value": {
                "operation": "max",
                "entity": "predictor_correlation"
            },
            "real_value": 0.89
        },
        "secondary_metrics": [
            {
                "label": "Reliable Indicators Count",
                "value": {
                    "operation": "count",
                    "entity": "reliable_indicators"
                },
                "real_value": 7
            },
            {
                "label": "Early Warning Accuracy (%)",
                "value": {
                    "operation": "avg",
                    "entity": "early_warning_accuracy"
                },
                "real_value": 76.3
            }
        ],
        "chart": {
            "graph_description": "Correlation strength of leading indicators",
            "chart_type": "bar",
            "x_axis_name": "Leading Indicator",
            "y_axis_name": "Correlation Strength",
            "x_axis": {"operation": "field", "field": "indicator_name"},
            "y_axis": {
                "operation": "avg",
                "entity": "indicator_correlation",
                "group_by": {"field": "indicator_name"}
            },
            "real_data": {
                "labels": ["Response Time", "Source Quality", "Pipeline Velocity", "Interview NPS", "Offer Accept Rate", "Time to Fill"],
                "values": [0.89, 0.84, 0.78, 0.72, 0.69, 0.65],
                "title": "Predictive Power of Indicators"
            }
        }
    }
},

{
    "questions": [
        "Какая сегментация кандидатов наиболее эффективна?",
        "Как персонализировать подход к разным группам?",
        "Стратегия по сегментам?"
    ],
    "report": {
        "report_title": "Advanced Candidate Segmentation",
        "main_metric": {
            "label": "Segmentation Effectiveness Score",
            "value": {
                "operation": "avg",
                "entity": "segmentation_effectiveness"
            },
            "real_value": 8.4
        },
        "secondary_metrics": [
            {
                "label": "Optimal Segments Count",
                "value": {
                    "operation": "count",
                    "entity": "optimal_segments"
                },
                "real_value": 6
            },
            {
                "label": "Personalization Impact (%)",
                "value": {
                    "operation": "avg",
                    "entity": "personalization_impact"
                },
                "real_value": 42.3
            }
        ],
        "chart": {
            "graph_description": "Segment performance matrix",
            "chart_type": "scatter",
            "x_axis_name": "Segment Size",
            "y_axis_name": "Conversion Rate (%)",
            "x_axis": {"operation": "count", "field": "segment_size"},
            "y_axis": {
                "operation": "avg",
                "entity": "segment_conversion",
                "group_by": {"field": "segment_name"}
            },
            "real_data": {
                "labels": ["Premium Tech", "Experienced Sales", "Rising Stars", "Career Changers", "Remote Workers", "Local Talent"],
                "values": [18.7, 15.2, 22.4, 8.9, 14.6, 12.1],
                "title": "Segment Performance Profile"
            }
        }
    }
},

{
    "questions": [
        "Какая многофакторная модель эффективности?",
        "Комплексный анализ всех переменных?",
        "Интегральная оценка процессов?"
    ],
    "report": {
        "report_title": "Multidimensional Efficiency Model",
        "main_metric": {
            "label": "Composite Efficiency Score",
            "value": {
                "operation": "avg",
                "entity": "composite_efficiency"
            },
            "real_value": 7.8
        },
        "secondary_metrics": [
            {
                "label": "Model Complexity Index",
                "value": {
                    "operation": "avg",
                    "entity": "model_complexity"
                },
                "real_value": 0.73
            },
            {
                "label": "Explanatory Power (%)",
                "value": {
                    "operation": "avg",
                    "entity": "explanatory_power"
                },
                "real_value": 91.6
            }
        ],
        "chart": {
            "graph_description": "Multi-dimensional efficiency radar",
            "chart_type": "radar",
            "x_axis_name": "Efficiency Dimension",
            "y_axis_name": "Score (1-10)",
            "x_axis": {"operation": "field", "field": "efficiency_dimension"},
            "y_axis": {
                "operation": "avg",
                "entity": "dimension_score",
                "group_by": {"field": "efficiency_dimension"}
            },
            "real_data": {
                "labels": ["Speed", "Quality", "Cost", "Experience", "Scalability", "Innovation"],
                "values": [8.2, 7.9, 7.1, 8.6, 6.8, 7.4],
                "title": "Efficiency Profile"
            }
        }
    }
},

{
    "questions": [
        "Какие сценарии развития возможны?",
        "Моделирование будущих изменений?",
        "Планирование по сценариям?"
    ],
    "report": {
        "report_title": "Scenario Planning & Simulation",
        "main_metric": {
            "label": "Most Likely Scenario Probability (%)",
            "value": {
                "operation": "max",
                "entity": "scenario_probability"
            },
            "real_value": 67.8
        },
        "secondary_metrics": [
            {
                "label": "Scenario Preparedness (%)",
                "value": {
                    "operation": "avg",
                    "entity": "scenario_preparedness"
                },
                "real_value": 78.4
            },
            {
                "label": "Risk Mitigation Coverage (%)",
                "value": {
                    "operation": "avg",
                    "entity": "risk_coverage"
                },
                "real_value": 85.2
            }
        ],
        "chart": {
            "graph_description": "Scenario impact vs probability matrix",
            "chart_type": "scatter",
            "x_axis_name": "Probability (%)",
            "y_axis_name": "Impact Score",
            "x_axis": {"operation": "field", "field": "scenario_probability"},
            "y_axis": {
                "operation": "avg",
                "entity": "scenario_impact",
                "group_by": {"field": "scenario_name"}
            },
            "real_data": {
                "labels": ["Growth Acceleration", "Market Stabilization", "Economic Downturn", "Tech Shortage", "Remote Transition", "AI Disruption"],
                "values": [67.8, 45.2, 23.1, 34.7, 56.3, 28.9],
                "title": "Scenario Planning Matrix"
            }
        }
    }
},

{
    "questions": [
        "Какой комплексный дашборд эффективности?",
        "Все ключевые метрики в одном месте?",
        "Интегральная картина состояния?"
    ],
    "report": {
        "report_title": "Executive Dashboard Overview",
        "main_metric": {
            "label": "Overall Health Score",
            "value": {
                "operation": "avg",
                "entity": "overall_health_score"
            },
            "real_value": 8.2
        },
        "secondary_metrics": [
            {
                "label": "Process Excellence (%)",
                "value": {
                    "operation": "avg",
                    "entity": "process_excellence"
                },
                "real_value": 87.3
            },
            {
                "label": "Strategic Alignment (%)",
                "value": {
                    "operation": "avg",
                    "entity": "strategic_alignment"
                },
                "real_value": 91.7
            },
            {
                "label": "Innovation Index",
                "value": {
                    "operation": "avg",
                    "entity": "innovation_index"
                },
                "real_value": 7.6
            }
        ],
        "chart": {
            "graph_description": "Comprehensive performance dashboard",
            "chart_type": "table",
            "x_axis_name": "Metric Category",
            "y_axis_name": "Performance Value",
            "x_axis": {"operation": "field", "field": "metric_category"},
            "y_axis": {
                "operation": "avg",
                "entity": "category_performance",
                "group_by": {"field": "metric_category"}
            },
            "real_data": {
                "labels": ["Efficiency", "Quality", "Speed", "Experience", "Innovation", "ROI"],
                "values": [8.2, 8.7, 7.4, 8.9, 7.6, 8.1],
                "title": "Executive Performance Overview"
            }
        }
    }
}

]

def get_report_by_category(category: str):
    """Get reports filtered by category."""
    if category == "pipeline":
        return HR_ANALYTICS_REPORTS[0:10]
    elif category == "performance":
        return HR_ANALYTICS_REPORTS[10:20]
    elif category == "operational":
        return HR_ANALYTICS_REPORTS[20:30]
    elif category == "strategic":
        return HR_ANALYTICS_REPORTS[30:40]
    elif category == "advanced":
        return HR_ANALYTICS_REPORTS[40:50]
    else:
        return HR_ANALYTICS_REPORTS

def get_reports_by_metric(metric_entity: str):
    """Get reports that use a specific metric entity."""
    matching_reports = []
    for report_data in HR_ANALYTICS_REPORTS:
        report = report_data.get("report", {})
        main_metric = report.get("main_metric", {})
        entity = main_metric.get("value", {}).get("entity", "")
        if metric_entity in entity:
            matching_reports.append(report_data)
    return matching_reports

def get_random_reports(count: int = 5):
    """Get random selection of reports."""
    import random
    return random.sample(HR_ANALYTICS_REPORTS, min(count, len(HR_ANALYTICS_REPORTS)))

def validate_reports():
    """Validate that all reports have complete structure."""
    issues = []
    for i, report_data in enumerate(HR_ANALYTICS_REPORTS):
        # Check questions
        if not report_data.get("questions") or len(report_data["questions"]) < 2:
            issues.append(f"Report {i+1}: Missing or insufficient questions")
        
        # Check report structure
        report = report_data.get("report", {})
        if not all(key in report for key in ["report_title", "main_metric", "secondary_metrics", "chart"]):
            issues.append(f"Report {i+1}: Missing required report components")
        
        # Check chart structure
        chart = report.get("chart", {})
        if not all(key in chart for key in ["graph_description", "chart_type", "real_data"]):
            issues.append(f"Report {i+1}: Incomplete chart structure")
    
    return issues

def get_questions_for_metric(metric_entity: str):
    """Get all questions that can be answered by reports using specific metric."""
    questions = []
    for report_data in HR_ANALYTICS_REPORTS:
        report = report_data.get("report", {})
        main_metric = report.get("main_metric", {})
        entity = main_metric.get("value", {}).get("entity", "")
        if metric_entity in entity:
            questions.extend(report_data.get("questions", []))
    return questions

# Example usage and statistics
if __name__ == "__main__":
    print(f"Total reports: {len(HR_ANALYTICS_REPORTS)}")
    print(f"Categories: pipeline (1-10), performance (11-20), operational (21-30), strategic (31-40), advanced (41-50)")
    
    # Show first report
    first_report = HR_ANALYTICS_REPORTS[0]
    print(f"\nSample questions: {first_report['questions']}")
    print(f"Report title: {first_report['report']['report_title']}")
    print(f"Main metric: {first_report['report']['main_metric']['label']}")
    
    # Validate reports
    validation_issues = validate_reports()
    if validation_issues:
        print(f"\nValidation issues found: {len(validation_issues)}")
        for issue in validation_issues[:3]:  # Show first 3
            print(f"  - {issue}")
    else:
        print("\nAll reports validated successfully!")
    
    # Show statistics
    total_questions = sum(len(r["questions"]) for r in HR_ANALYTICS_REPORTS)
    print(f"\nTotal questions: {total_questions}")
    print(f"Average questions per report: {total_questions / len(HR_ANALYTICS_REPORTS):.1f}")
    
    # Show category breakdown
    categories = {
        "Basic Pipeline": len(get_report_by_category("pipeline")),
        "Performance Analysis": len(get_report_by_category("performance")),
        "Operational Insights": len(get_report_by_category("operational")),
        "Strategic Insights": len(get_report_by_category("strategic")),
        "Advanced Analytics": len(get_report_by_category("advanced"))
    }
    
    print(f"\nCategory breakdown:")
    for category, count in categories.items():
        print(f"  {category}: {count} reports")