"""
100 Sample HR Analytics Reports with Questions for AI Testing
Each report includes:
- Realistic JSON structure based on our actual entities
- 3 different questions (conversational + formal Russian)
- Product-meaningful analytics scenarios
"""

import json
from typing import List, Dict, Any

# Real entity data from our system
ENTITIES = {
    "recruiters": [
        {"id": "2", "name": "Михаил Танский"},
        {"id": "14824", "name": "Анастасия Богач"},
        {"id": "84798", "name": "Антон Озорин"},
        {"id": "79161", "name": "Киселев Вячеслав"},
        {"id": "66559", "name": "Ярослав Матвеев"},
        {"id": "64691", "name": "Екатерина Савченко"},
        {"id": "44638", "name": "Саша"},
        {"id": "37102", "name": "Савченко Екатерина"},
        {"id": "4431", "name": "Анастасия"},
        {"id": "86362", "name": "Никита Котов 1"}
    ],
    "hiring_managers": [
        {"id": "103538", "name": "Вася Щерица"},
        {"id": "117791", "name": "Test Test Test"},
        {"id": "122815", "name": "Анастасия Фролова"},
        {"id": "122816", "name": "Соня"},
        {"id": "147708", "name": "Стас Гельман"}
    ],
    "vacancies": [
        {"id": "2536465", "name": "Юрист"},
        {"id": "2536466", "name": "Программист Python"},
        {"id": "2568581", "name": "Team Lead Python Dev"},
        {"id": "2664081", "name": "Менеджер клиентского сервиса Team Lead"},
        {"id": "2700221", "name": "Senior Java / Kotlin Backend Developer"},
        {"id": "2700278", "name": "Менеджер корпоративных продаж"},
        {"id": "2700279", "name": "Менеджер по ключевым клиентам"},
        {"id": "2700280", "name": "Менеджер по продажам"},
        {"id": "2700281", "name": "Инженер QA Стажер"},
        {"id": "2700285", "name": "QA-инженер"}
    ],
    "sources": [
        {"id": "274883", "name": "HeadHunter"},
        {"id": "274884", "name": "Отклик с HeadHunter"},
        {"id": "274885", "name": "SuperJob"},
        {"id": "274886", "name": "LinkedIn"},
        {"id": "274887", "name": "Хабр карьера"}
    ],
    "stages": [
        {"id": "103674", "name": "Новые"},
        {"id": "103676", "name": "Отправлено письмо"},
        {"id": "107602", "name": "Звонок кандидату"},
        {"id": "117967", "name": "Видеоинтервью"},
        {"id": "117968", "name": "Видеоинтервью пройдено"},
        {"id": "103675", "name": "Резюме у заказчика"},
        {"id": "103677", "name": "Интервью"},
        {"id": "103678", "name": "Интервью с заказчиком"}
    ],
    "divisions": [
        {"id": "25516", "name": "Департамент клиентского сервиса"},
        {"id": "25518", "name": "Отдел операционной деятельности"},
        {"id": "25519", "name": "Отдел продаж"},
        {"id": "25520", "name": "Отдел разработки"},
        {"id": "47968", "name": "Департамент маркетинга"}
    ]
}

# Time periods for realistic filtering
PERIODS = ["1 month", "3 month", "6 month", "1 year"]

def create_sample_reports() -> List[Dict[str, Any]]:
    """Generate 100 sample reports with questions"""
    reports = []
    
    # Category 1: General Pipeline Analysis (10 reports)
    reports.extend([
        {
            "id": 1,
            "category": "general_pipeline",
            "report_json": {
                "report_title": "Общая воронка найма",
                "main_metric": {
                    "label": "Всего кандидатов в работе",
                    "value": {
                        "operation": "count",
                        "entity": "applicants",
                        "value_field": None,
                        "group_by": None,
                        "filters": {"period": "3 month"}
                    }
                },
                "secondary_metrics": [
                    {
                        "label": "Среднее время найма (дни)",
                        "value": {
                            "operation": "avg",
                            "entity": "hires", 
                            "value_field": "time_to_hire",
                            "group_by": None,
                            "filters": {"period": "3 month"}
                        }
                    },
                    {
                        "label": "Всего нанято",
                        "value": {
                            "operation": "count",
                            "entity": "hires",
                            "value_field": None,
                            "group_by": None,
                            "filters": {"period": "3 month"}
                        }
                    }
                ],
                "chart": {
                    "label": "Распределение кандидатов по этапам",
                    "type": "bar",
                    "x_label": "Этап",
                    "y_label": "Количество кандидатов",
                    "x_axis": {
                        "operation": "count",
                        "entity": "stages",
                        "value_field": None,
                        "group_by": {"field": "stages"},
                        "filters": {"period": "3 month"}
                    },
                    "y_axis": {
                        "operation": "count",
                        "entity": "applicants",
                        "value_field": None,
                        "group_by": {"field": "stages"},
                        "filters": {"period": "3 month"}
                    }
                }
            },
            "questions": [
                "Покажи общую ситуацию с наймом за последние 3 месяца",
                "Какая воронка рекрутмента сейчас?",
                "Проанализируйте распределение кандидатов по этапам найма за квартал"
            ]
        },
        {
            "id": 2,
            "category": "general_pipeline",
            "report_json": {
                "report_title": "Конверсия по этапам найма",
                "main_metric": {
                    "label": "Общая конверсия в найм (%)",
                    "value": {
                        "operation": "avg",
                        "entity": "vacancies",
                        "value_field": "conversion",
                        "group_by": None,
                        "filters": {"period": "6 month"}
                    }
                },
                "secondary_metrics": [
                    {
                        "label": "Кандидатов на этапе интервью",
                        "value": {
                            "operation": "count",
                            "entity": "applicants",
                            "value_field": None,
                            "group_by": None,
                            "filters": {"period": "6 month", "stages": "103677"}
                        }
                    },
                    {
                        "label": "Кандидатов у заказчика",
                        "value": {
                            "operation": "count",
                            "entity": "applicants",
                            "value_field": None,
                            "group_by": None,
                            "filters": {"period": "6 month", "stages": "103675"}
                        }
                    }
                ],
                "chart": {
                    "label": "Конверсия кандидатов по этапам",
                    "type": "line",
                    "x_label": "Этап воронки",
                    "y_label": "Процент конверсии",
                    "x_axis": {
                        "operation": "count",
                        "entity": "stages",
                        "value_field": None,
                        "group_by": {"field": "stages"},
                        "filters": {"period": "6 month"}
                    },
                    "y_axis": {
                        "operation": "avg",
                        "entity": "applicants",
                        "value_field": "conversion",
                        "group_by": {"field": "stages"},
                        "filters": {"period": "6 month"}
                    }
                }
            },
            "questions": [
                "Какая конверсия у нас в воронке найма?",
                "Покажи эффективность этапов отбора",
                "Проанализируйте показатели конверсии по этапам рекрутмента за полгода"
            ]
        },
        {
            "id": 3,
            "category": "general_pipeline", 
            "report_json": {
                "report_title": "Динамика найма по месяцам",
                "main_metric": {
                    "label": "Нанято в этом месяце",
                    "value": {
                        "operation": "count",
                        "entity": "hires",
                        "value_field": None,
                        "group_by": None,
                        "filters": {"period": "1 month"}
                    }
                },
                "secondary_metrics": [
                    {
                        "label": "Нанято за предыдущий месяц",
                        "value": {
                            "operation": "count",
                            "entity": "hires",
                            "value_field": None,
                            "group_by": None,
                            "filters": {"period": "2 month"}
                        }
                    },
                    {
                        "label": "Всего нанято за полгода",
                        "value": {
                            "operation": "count", 
                            "entity": "hires",
                            "value_field": None,
                            "group_by": None,
                            "filters": {"period": "6 month"}
                        }
                    }
                ],
                "chart": {
                    "label": "Динамика найма за полгода",
                    "type": "line",
                    "x_label": "Месяц",
                    "y_label": "Количество нанятых",
                    "x_axis": {
                        "operation": "date_trunc",
                        "entity": "hires",
                        "value_field": None,
                        "group_by": {"field": "month"},
                        "date_trunc": "month",
                        "filters": {"period": "6 month"}
                    },
                    "y_axis": {
                        "operation": "count",
                        "entity": "hires",
                        "value_field": None,
                        "group_by": {"field": "month"},
                        "filters": {"period": "6 month"}
                    }
                }
            },
            "questions": [
                "Как нанимали за последние месяцы?",
                "Покажи динамику найма по времени",
                "Предоставьте анализ тенденций найма за последние полгода"
            ]
        }
    ])
    
    # Category 2: Recruiter Performance Analysis (15 reports)
    recruiter_reports = []
    for i, recruiter in enumerate(ENTITIES["recruiters"][:5]):  # Top 5 recruiters
        recruiter_reports.extend([
            {
                "id": 10 + i*3 + 1,
                "category": "recruiter_performance",
                "report_json": {
                    "report_title": f"Эффективность рекрутера {recruiter['name']}",
                    "main_metric": {
                        "label": f"Нанято {recruiter['name']}",
                        "value": {
                            "operation": "count",
                            "entity": "hires",
                            "value_field": None,
                            "group_by": None,
                            "filters": {"period": "6 month", "recruiters": recruiter["id"]}
                        }
                    },
                    "secondary_metrics": [
                        {
                            "label": f"Кандидатов добавил {recruiter['name']}",
                            "value": {
                                "operation": "count",
                                "entity": "applicants",
                                "value_field": None,
                                "group_by": None,
                                "filters": {"period": "6 month", "recruiters": recruiter["id"]}
                            }
                        },
                        {
                            "label": f"Среднее время найма {recruiter['name']} (дни)",
                            "value": {
                                "operation": "avg",
                                "entity": "hires",
                                "value_field": "time_to_hire",
                                "group_by": None,
                                "filters": {"period": "6 month", "recruiters": recruiter["id"]}
                            }
                        }
                    ],
                    "chart": {
                        "label": f"Активность {recruiter['name']} по месяцам",
                        "type": "line",
                        "x_label": "Месяц",
                        "y_label": "Количество нанятых",
                        "x_axis": {
                            "operation": "date_trunc",
                            "entity": "hires",
                            "value_field": None,
                            "group_by": {"field": "month"},
                            "date_trunc": "month",
                            "filters": {"period": "6 month", "recruiters": recruiter["id"]}
                        },
                        "y_axis": {
                            "operation": "count",
                            "entity": "hires",
                            "value_field": None,
                            "group_by": {"field": "month"},
                            "filters": {"period": "6 month", "recruiters": recruiter["id"]}
                        }
                    }
                },
                "questions": [
                    f"Сколько нанял {recruiter['name']}?",
                    f"Как работает {recruiter['name']}?",
                    f"Проанализируйте результативность рекрутера {recruiter['name']} за полгода"
                ]
            },
            {
                "id": 10 + i*3 + 2,
                "category": "recruiter_performance",
                "report_json": {
                    "report_title": f"Воронка найма {recruiter['name']}",
                    "main_metric": {
                        "label": f"Конверсия {recruiter['name']} (%)",
                        "value": {
                            "operation": "avg",
                            "entity": "vacancies",
                            "value_field": "conversion",
                            "group_by": None,
                            "filters": {"period": "3 month", "recruiters": recruiter["id"]}
                        }
                    },
                    "secondary_metrics": [
                        {
                            "label": f"Вакансий ведёт {recruiter['name']}",
                            "value": {
                                "operation": "count",
                                "entity": "vacancies",
                                "value_field": None,
                                "group_by": None,
                                "filters": {"period": "3 month", "recruiters": recruiter["id"]}
                            }
                        },
                        {
                            "label": f"Закрытых вакансий {recruiter['name']}",
                            "value": {
                                "operation": "count",
                                "entity": "vacancies",
                                "value_field": None,
                                "group_by": None,
                                "filters": {"period": "3 month", "recruiters": recruiter["id"], "vacancies": "closed"}
                            }
                        }
                    ],
                    "chart": {
                        "label": f"Кандидаты {recruiter['name']} по этапам",
                        "type": "bar",
                        "x_label": "Этап",
                        "y_label": "Количество кандидатов",
                        "x_axis": {
                            "operation": "count",
                            "entity": "stages",
                            "value_field": None,
                            "group_by": {"field": "stages"},
                            "filters": {"period": "3 month", "recruiters": recruiter["id"]}
                        },
                        "y_axis": {
                            "operation": "count",
                            "entity": "applicants",
                            "value_field": None,
                            "group_by": {"field": "stages"},
                            "filters": {"period": "3 month", "recruiters": recruiter["id"]}
                        }
                    }
                },
                "questions": [
                    f"Какая воронка у {recruiter['name']}?",
                    f"Покажи этапы найма {recruiter['name']}",
                    f"Предоставьте анализ воронки рекрутмента для {recruiter['name']}"
                ]
            },
            {
                "id": 10 + i*3 + 3,
                "category": "recruiter_performance",  
                "report_json": {
                    "report_title": f"Источники кандидатов {recruiter['name']}",
                    "main_metric": {
                        "label": f"Основной источник {recruiter['name']}",
                        "value": {
                            "operation": "count",
                            "entity": "applicants",
                            "value_field": None,
                            "group_by": None,
                            "filters": {"period": "6 month", "recruiters": recruiter["id"], "sources": "274883"}
                        }
                    },
                    "secondary_metrics": [
                        {
                            "label": f"Из LinkedIn {recruiter['name']}",
                            "value": {
                                "operation": "count",
                                "entity": "applicants",
                                "value_field": None,
                                "group_by": None,
                                "filters": {"period": "6 month", "recruiters": recruiter["id"], "sources": "274886"}
                            }
                        },
                        {
                            "label": f"Всего источников {recruiter['name']}",
                            "value": {
                                "operation": "count",
                                "entity": "sources",
                                "value_field": None,
                                "group_by": None,
                                "filters": {"period": "6 month", "recruiters": recruiter["id"]}
                            }
                        }
                    ],
                    "chart": {
                        "label": f"Источники кандидатов {recruiter['name']}",
                        "type": "bar",
                        "x_label": "Источник",
                        "y_label": "Количество кандидатов",
                        "x_axis": {
                            "operation": "count",
                            "entity": "sources",
                            "value_field": None,
                            "group_by": {"field": "sources"},
                            "filters": {"period": "6 month", "recruiters": recruiter["id"]}
                        },
                        "y_axis": {
                            "operation": "count",
                            "entity": "applicants",
                            "value_field": None,
                            "group_by": {"field": "sources"},
                            "filters": {"period": "6 month", "recruiters": recruiter["id"]}
                        }
                    }
                },
                "questions": [
                    f"Откуда {recruiter['name']} берёт кандидатов?",
                    f"Какие источники использует {recruiter['name']}?",
                    f"Проанализируйте источники поиска кандидатов для рекрутера {recruiter['name']}"
                ]
            }
        ])
    
    reports.extend(recruiter_reports)
    
    # Category 3: Source Effectiveness Analysis (10 reports)
    source_reports = []
    for i, source in enumerate(ENTITIES["sources"]):
        source_reports.append({
            "id": 40 + i + 1,
            "category": "source_effectiveness",
            "report_json": {
                "report_title": f"Эффективность источника {source['name']}",
                "main_metric": {
                    "label": f"Нанято через {source['name']}",
                    "value": {
                        "operation": "count",
                        "entity": "hires",
                        "value_field": None,
                        "group_by": None,
                        "filters": {"period": "6 month", "sources": source["id"]}
                    }
                },
                "secondary_metrics": [
                    {
                        "label": f"Кандидатов из {source['name']}",
                        "value": {
                            "operation": "count",
                            "entity": "applicants",
                            "value_field": None,
                            "group_by": None,
                            "filters": {"period": "6 month", "sources": source["id"]}
                        }
                    },
                    {
                        "label": f"Время найма через {source['name']} (дни)",
                        "value": {
                            "operation": "avg",
                            "entity": "hires",
                            "value_field": "time_to_hire",
                            "group_by": None,
                            "filters": {"period": "6 month", "sources": source["id"]}
                        }
                    }
                ],
                "chart": {
                    "label": f"Динамика найма через {source['name']}",
                    "type": "line",
                    "x_label": "Месяц",
                    "y_label": "Количество нанятых",
                    "x_axis": {
                        "operation": "date_trunc",
                        "entity": "hires",
                        "value_field": None,
                        "group_by": {"field": "month"},
                        "date_trunc": "month",
                        "filters": {"period": "6 month", "sources": source["id"]}
                    },
                    "y_axis": {
                        "operation": "count",
                        "entity": "hires",
                        "value_field": None,
                        "group_by": {"field": "month"},
                        "filters": {"period": "6 month", "sources": source["id"]}
                    }
                }
            },
            "questions": [
                f"Как работает {source['name']}?",
                f"Сколько нанимаем через {source['name']}?",
                f"Проанализируйте эффективность источника {source['name']} за полгода"
            ]
        })
        
    # Add comparison report for sources
    source_reports.append({
        "id": 50,
        "category": "source_effectiveness",
        "report_json": {
            "report_title": "Сравнение эффективности источников",
            "main_metric": {
                "label": "Лучший источник по найму",
                "value": {
                    "operation": "count",
                    "entity": "hires",
                    "value_field": None,
                    "group_by": None,
                    "filters": {"period": "6 month"}
                }
            },
            "secondary_metrics": [
                {
                    "label": "Всего кандидатов из источников",
                    "value": {
                        "operation": "count",
                        "entity": "applicants",
                        "value_field": None,
                        "group_by": None,
                        "filters": {"period": "6 month"}
                    }
                },
                {
                    "label": "Среднее время найма по источникам",
                    "value": {
                        "operation": "avg",
                        "entity": "hires",
                        "value_field": "time_to_hire",
                        "group_by": None,
                        "filters": {"period": "6 month"}
                    }
                }
            ],
            "chart": {
                "label": "Сравнение источников по количеству найма",
                "type": "bar",
                "x_label": "Источник",
                "y_label": "Количество нанятых",
                "x_axis": {
                    "operation": "count",
                    "entity": "sources",
                    "value_field": None,
                    "group_by": {"field": "sources"},
                    "filters": {"period": "6 month"}
                },
                "y_axis": {
                    "operation": "count",
                    "entity": "hires",
                    "value_field": None,
                    "group_by": {"field": "sources"},
                    "filters": {"period": "6 month"}
                }
            }
        },
        "questions": [
            "Какой источник самый эффективный?",
            "Сравни источники найма",
            "Предоставьте сравнительный анализ эффективности источников рекрутмента"
        ]
    })
    
    reports.extend(source_reports)
    
    # Category 4: Vacancy Analysis (15 reports)
    vacancy_reports = []
    for i, vacancy in enumerate(ENTITIES["vacancies"][:5]):  # Top 5 vacancies
        vacancy_reports.extend([
            {
                "id": 60 + i*3 + 1,
                "category": "vacancy_analysis",
                "report_json": {
                    "report_title": f"Статус вакансии {vacancy['name']}",
                    "main_metric": {
                        "label": f"Кандидатов на позицию {vacancy['name']}",
                        "value": {
                            "operation": "count",
                            "entity": "applicants",
                            "value_field": None,
                            "group_by": None,
                            "filters": {"period": "3 month", "vacancies": vacancy["id"]}
                        }
                    },
                    "secondary_metrics": [
                        {
                            "label": f"Дней открыта {vacancy['name']}",
                            "value": {
                                "operation": "avg",
                                "entity": "vacancies",
                                "value_field": "days_active",
                                "group_by": None,
                                "filters": {"vacancies": vacancy["id"]}
                            }
                        },
                        {
                            "label": f"Нанято на {vacancy['name']}",
                            "value": {
                                "operation": "count",
                                "entity": "hires",
                                "value_field": None,
                                "group_by": None,
                                "filters": {"period": "3 month", "vacancies": vacancy["id"]}
                            }
                        }
                    ],
                    "chart": {
                        "label": f"Воронка вакансии {vacancy['name']}",
                        "type": "bar",
                        "x_label": "Этап",
                        "y_label": "Количество кандидатов",
                        "x_axis": {
                            "operation": "count",
                            "entity": "stages",
                            "value_field": None,
                            "group_by": {"field": "stages"},
                            "filters": {"period": "3 month", "vacancies": vacancy["id"]}
                        },
                        "y_axis": {
                            "operation": "count",
                            "entity": "applicants",
                            "value_field": None,
                            "group_by": {"field": "stages"},
                            "filters": {"period": "3 month", "vacancies": vacancy["id"]}
                        }
                    }
                },
                "questions": [
                    f"А что с вакансией {vacancy['name']}?",
                    f"Как дела с позицией {vacancy['name']}?",
                    f"Предоставьте анализ статуса вакансии {vacancy['name']}"
                ]
            },
            {
                "id": 60 + i*3 + 2,
                "category": "vacancy_analysis",
                "report_json": {
                    "report_title": f"Источники для {vacancy['name']}",
                    "main_metric": {
                        "label": f"Основной источник для {vacancy['name']}",
                        "value": {
                            "operation": "count",
                            "entity": "applicants",
                            "value_field": None,
                            "group_by": None,
                            "filters": {"period": "3 month", "vacancies": vacancy["id"], "sources": "274883"}
                        }
                    },
                    "secondary_metrics": [
                        {
                            "label": f"Из LinkedIn на {vacancy['name']}",
                            "value": {
                                "operation": "count",
                                "entity": "applicants",
                                "value_field": None,
                                "group_by": None,
                                "filters": {"period": "3 month", "vacancies": vacancy["id"], "sources": "274886"}
                            }
                        },
                        {
                            "label": f"Всего источников {vacancy['name']}",
                            "value": {
                                "operation": "count",
                                "entity": "sources",
                                "value_field": None,
                                "group_by": None,
                                "filters": {"period": "3 month", "vacancies": vacancy["id"]}
                            }
                        }
                    ],
                    "chart": {
                        "label": f"Источники кандидатов для {vacancy['name']}",
                        "type": "bar",
                        "x_label": "Источник",
                        "y_label": "Количество кандидатов",
                        "x_axis": {
                            "operation": "count",
                            "entity": "sources",
                            "value_field": None,
                            "group_by": {"field": "sources"},
                            "filters": {"period": "3 month", "vacancies": vacancy["id"]}
                        },
                        "y_axis": {
                            "operation": "count",
                            "entity": "applicants",
                            "value_field": None,
                            "group_by": {"field": "sources"},
                            "filters": {"period": "3 month", "vacancies": vacancy["id"]}
                        }
                    }
                },
                "questions": [
                    f"Откуда кандидаты на {vacancy['name']}?",
                    f"Какие источники работают для {vacancy['name']}?",
                    f"Проанализируйте источники поиска для вакансии {vacancy['name']}"
                ]
            },
            {
                "id": 60 + i*3 + 3,
                "category": "vacancy_analysis",
                "report_json": {
                    "report_title": f"Скорость закрытия {vacancy['name']}",
                    "main_metric": {
                        "label": f"Время закрытия {vacancy['name']} (дни)",
                        "value": {
                            "operation": "avg",
                            "entity": "hires",
                            "value_field": "time_to_hire",
                            "group_by": None,
                            "filters": {"period": "6 month", "vacancies": vacancy["id"]}
                        }
                    },
                    "secondary_metrics": [
                        {
                            "label": f"Дней с момента создания {vacancy['name']}",
                            "value": {
                                "operation": "avg",
                                "entity": "vacancies",
                                "value_field": "days_active",
                                "group_by": None,
                                "filters": {"vacancies": vacancy["id"]}
                            }
                        },
                        {
                            "label": f"Статус {vacancy['name']}",
                            "value": {
                                "operation": "count",
                                "entity": "vacancies",
                                "value_field": None,
                                "group_by": None,
                                "filters": {"vacancies": vacancy["id"], "vacancies": "open"}
                            }
                        }
                    ],
                    "chart": {
                        "label": f"Динамика найма для {vacancy['name']}",
                        "type": "line",
                        "x_label": "Месяц",
                        "y_label": "Количество нанятых",
                        "x_axis": {
                            "operation": "date_trunc",
                            "entity": "hires",
                            "value_field": None,
                            "group_by": {"field": "month"},
                            "date_trunc": "month",
                            "filters": {"period": "6 month", "vacancies": vacancy["id"]}
                        },
                        "y_axis": {
                            "operation": "count",
                            "entity": "hires",
                            "value_field": None,
                            "group_by": {"field": "month"},
                            "filters": {"period": "6 month", "vacancies": vacancy["id"]}
                        }
                    }
                },
                "questions": [
                    f"Как быстро закрываем {vacancy['name']}?",
                    f"Сколько времени займёт найм на {vacancy['name']}?",
                    f"Проанализируйте скорость закрытия вакансии {vacancy['name']}"
                ]
            }
        ])
    
    reports.extend(vacancy_reports)
    
    # Category 5: Division Analysis (10 reports)
    division_reports = []
    for i, division in enumerate(ENTITIES["divisions"]):
        division_reports.extend([
            {
                "id": 80 + i*2 + 1,
                "category": "division_analysis",
                "report_json": {
                    "report_title": f"Найм в {division['name']}",
                    "main_metric": {
                        "label": f"Нанято в {division['name']}",
                        "value": {
                            "operation": "count",
                            "entity": "hires",
                            "value_field": None,
                            "group_by": None,
                            "filters": {"period": "6 month", "divisions": division["id"]}
                        }
                    },
                    "secondary_metrics": [
                        {
                            "label": f"Кандидатов в {division['name']}",
                            "value": {
                                "operation": "count",
                                "entity": "applicants",
                                "value_field": None,
                                "group_by": None,
                                "filters": {"period": "6 month", "divisions": division["id"]}
                            }
                        },
                        {
                            "label": f"Открытых вакансий в {division['name']}",
                            "value": {
                                "operation": "count",
                                "entity": "vacancies",
                                "value_field": None,
                                "group_by": None,
                                "filters": {"divisions": division["id"], "vacancies": "open"}
                            }
                        }
                    ],
                    "chart": {
                        "label": f"Динамика найма в {division['name']}",
                        "type": "line",
                        "x_label": "Месяц",
                        "y_label": "Количество нанятых",
                        "x_axis": {
                            "operation": "date_trunc",
                            "entity": "hires",
                            "value_field": None,
                            "group_by": {"field": "month"},
                            "date_trunc": "month",
                            "filters": {"period": "6 month", "divisions": division["id"]}
                        },
                        "y_axis": {
                            "operation": "count",
                            "entity": "hires",
                            "value_field": None,
                            "group_by": {"field": "month"},
                            "filters": {"period": "6 month", "divisions": division["id"]}
                        }
                    }
                },
                "questions": [
                    f"Как дела с наймом в {division['name']}?",
                    f"Сколько нанято в отдел {division['name']}?",
                    f"Проанализируйте найм в {division['name']} за полгода"
                ]
            },
            {
                "id": 80 + i*2 + 2,
                "category": "division_analysis",
                "report_json": {
                    "report_title": f"Источники для {division['name']}",
                    "main_metric": {
                        "label": f"Основной источник для {division['name']}",
                        "value": {
                            "operation": "count",
                            "entity": "applicants",
                            "value_field": None,
                            "group_by": None,
                            "filters": {"period": "6 month", "divisions": division["id"], "sources": "274883"}
                        }
                    },
                    "secondary_metrics": [
                        {
                            "label": f"Из LinkedIn в {division['name']}",
                            "value": {
                                "operation": "count",
                                "entity": "applicants",
                                "value_field": None,
                                "group_by": None,
                                "filters": {"period": "6 month", "divisions": division["id"], "sources": "274886"}
                            }
                        },
                        {
                            "label": f"Среднее время найма {division['name']}",
                            "value": {
                                "operation": "avg",
                                "entity": "hires",
                                "value_field": "time_to_hire",
                                "group_by": None,
                                "filters": {"period": "6 month", "divisions": division["id"]}
                            }
                        }
                    ],
                    "chart": {
                        "label": f"Источники для {division['name']}",
                        "type": "bar",
                        "x_label": "Источник",
                        "y_label": "Количество кандидатов",
                        "x_axis": {
                            "operation": "count",
                            "entity": "sources",
                            "value_field": None,
                            "group_by": {"field": "sources"},
                            "filters": {"period": "6 month", "divisions": division["id"]}
                        },
                        "y_axis": {
                            "operation": "count",
                            "entity": "applicants",
                            "value_field": None,
                            "group_by": {"field": "sources"},
                            "filters": {"period": "6 month", "divisions": division["id"]}
                        }
                    }
                },
                "questions": [
                    f"Откуда кандидаты в {division['name']}?",
                    f"Какие источники работают для {division['name']}?",
                    f"Проанализируйте источники найма для {division['name']}"
                ]
            }
        ])
    
    reports.extend(division_reports)
    
    # Category 6: Time-based Analysis (5 additional reports)
    time_reports = [
        {
            "id": 91,
            "category": "time_analysis",
            "report_json": {
                "report_title": "Сравнение найма по месяцам",
                "main_metric": {
                    "label": "Нанято в этом месяце",
                    "value": {
                        "operation": "count",
                        "entity": "hires",
                        "value_field": None,
                        "group_by": None,
                        "filters": {"period": "1 month"}
                    }
                },
                "secondary_metrics": [
                    {
                        "label": "Нанято в прошлом месяце",
                        "value": {
                            "operation": "count",
                            "entity": "hires",
                            "value_field": None,
                            "group_by": None,
                            "filters": {"period": "2 month"}
                        }
                    },
                    {
                        "label": "Среднее найма за полгода",
                        "value": {
                            "operation": "avg",
                            "entity": "hires",
                            "value_field": "count",
                            "group_by": None,
                            "filters": {"period": "6 month"}
                        }
                    }
                ],
                "chart": {
                    "label": "Динамика найма по месяцам",
                    "type": "line",
                    "x_label": "Месяц",
                    "y_label": "Количество нанятых",
                    "x_axis": {
                        "operation": "date_trunc",
                        "entity": "hires",
                        "value_field": None,
                        "group_by": {"field": "month"},
                        "date_trunc": "month",
                        "filters": {"period": "1 year"}
                    },
                    "y_axis": {
                        "operation": "count",
                        "entity": "hires",
                        "value_field": None,
                        "group_by": {"field": "month"},
                        "filters": {"period": "1 year"}
                    }
                }
            },
            "questions": [
                "Как изменился найм за последние месяцы?",
                "Покажи тренды найма по времени",
                "Проанализируйте динамику найма за год"
            ]
        },
        {
            "id": 92,
            "category": "time_analysis",
            "report_json": {
                "report_title": "Сезонность найма",
                "main_metric": {
                    "label": "Нанято за текущий квартал",
                    "value": {
                        "operation": "count",
                        "entity": "hires",
                        "value_field": None,
                        "group_by": None,
                        "filters": {"period": "3 month"}
                    }
                },
                "secondary_metrics": [
                    {
                        "label": "Кандидатов добавили за квартал",
                        "value": {
                            "operation": "count",
                            "entity": "applicants",
                            "value_field": None,
                            "group_by": None,
                            "filters": {"period": "3 month"}
                        }
                    },
                    {
                        "label": "Средняя конверсия за квартал",
                        "value": {
                            "operation": "avg",
                            "entity": "vacancies",
                            "value_field": "conversion",
                            "group_by": None,
                            "filters": {"period": "3 month"}
                        }
                    }
                ],
                "chart": {
                    "label": "Сезонная активность найма",
                    "type": "bar",
                    "x_label": "Квартал",
                    "y_label": "Количество нанятых",
                    "x_axis": {
                        "operation": "date_trunc",
                        "entity": "hires",
                        "value_field": None,
                        "group_by": {"field": "month"},
                        "date_trunc": "month",
                        "filters": {"period": "1 year"}
                    },
                    "y_axis": {
                        "operation": "count",
                        "entity": "hires",
                        "value_field": None,
                        "group_by": {"field": "month"},
                        "filters": {"period": "1 year"}
                    }
                }
            },
            "questions": [
                "Есть ли сезонность в найме?",
                "В какие месяцы нанимаем больше?",
                "Проанализируйте сезонные тренды найма"
            ]
        }
    ]
    
    reports.extend(time_reports)
    
    # Category 7: Hiring Manager Performance (3 reports)
    hm_reports = []
    for i, hm in enumerate(ENTITIES["hiring_managers"][:3]):
        hm_reports.append({
            "id": 94 + i,
            "category": "hiring_manager_performance",
            "report_json": {
                "report_title": f"Скорость найма с {hm['name']}",
                "main_metric": {
                    "label": f"Среднее время ответа {hm['name']} (дни)",
                    "value": {
                        "operation": "avg",
                        "entity": "actions",
                        "value_field": "count",
                        "group_by": None,
                        "filters": {"period": "3 month", "hiring_managers": hm["id"]}
                    }
                },
                "secondary_metrics": [
                    {
                        "label": f"Интервью с {hm['name']}",
                        "value": {
                            "operation": "count",
                            "entity": "actions",
                            "value_field": None,
                            "group_by": None,
                            "filters": {"period": "3 month", "hiring_managers": hm["id"], "actions": "interview"}
                        }
                    },
                    {
                        "label": f"Нанято через {hm['name']}",
                        "value": {
                            "operation": "count",
                            "entity": "hires",
                            "value_field": None,
                            "group_by": None,
                            "filters": {"period": "3 month", "hiring_managers": hm["id"]}
                        }
                    }
                ],
                "chart": {
                    "label": f"Активность {hm['name']} по месяцам",
                    "type": "line",
                    "x_label": "Месяц",
                    "y_label": "Количество интервью",
                    "x_axis": {
                        "operation": "date_trunc",
                        "entity": "actions",
                        "value_field": None,
                        "group_by": {"field": "month"},
                        "date_trunc": "month",
                        "filters": {"period": "6 month", "hiring_managers": hm["id"], "actions": "interview"}
                    },
                    "y_axis": {
                        "operation": "count",
                        "entity": "actions",
                        "value_field": None,
                        "group_by": {"field": "month"},
                        "filters": {"period": "6 month", "hiring_managers": hm["id"], "actions": "interview"}
                    }
                }
            },
            "questions": [
                f"Как быстро отвечает {hm['name']}?",
                f"Сколько интервью проводит {hm['name']}?",
                f"Проанализируйте скорость работы менеджера {hm['name']}"
            ]
        })
    
    reports.extend(hm_reports)
    
    # Category 8: Comparison and Mixed Analysis (3 reports)
    comparison_reports = [
        {
            "id": 97,
            "category": "comparison_analysis",
            "report_json": {
                "report_title": "Сравнение рекрутеров по эффективности",
                "main_metric": {
                    "label": "Лучший рекрутер по найму",
                    "value": {
                        "operation": "count",
                        "entity": "hires",
                        "value_field": None,
                        "group_by": None,
                        "filters": {"period": "6 month"}
                    }
                },
                "secondary_metrics": [
                    {
                        "label": "Среднее время найма по команде",
                        "value": {
                            "operation": "avg",
                            "entity": "hires",
                            "value_field": "time_to_hire",
                            "group_by": None,
                            "filters": {"period": "6 month"}
                        }
                    },
                    {
                        "label": "Всего рекрутеров активных",
                        "value": {
                            "operation": "count",
                            "entity": "recruiters",
                            "value_field": None,
                            "group_by": None,
                            "filters": {"period": "6 month", "recruiters": "with_vacancies"}
                        }
                    }
                ],
                "chart": {
                    "label": "Рейтинг рекрутеров по количеству найма",
                    "type": "scatter",
                    "x_label": "Количество кандидатов",
                    "y_label": "Количество нанятых",
                    "x_axis": {
                        "operation": "count",
                        "entity": "applicants",
                        "value_field": None,
                        "group_by": {"field": "recruiters"},
                        "filters": {"period": "6 month"}
                    },
                    "y_axis": {
                        "operation": "count",
                        "entity": "hires",
                        "value_field": None,
                        "group_by": {"field": "recruiters"},
                        "filters": {"period": "6 month"}
                    }
                }
            },
            "questions": [
                "Кто из рекрутеров работает лучше?",
                "Сравни эффективность команды",
                "Предоставьте рейтинг рекрутеров по результативности"
            ]
        },
        {
            "id": 98,
            "category": "comparison_analysis",
            "report_json": {
                "report_title": "Анализ воронки отказов",
                "main_metric": {
                    "label": "Всего отказов",
                    "value": {
                        "operation": "count",
                        "entity": "rejections",
                        "value_field": None,
                        "group_by": None,
                        "filters": {"period": "3 month"}
                    }
                },
                "secondary_metrics": [
                    {
                        "label": "Отказов на этапе интервью",
                        "value": {
                            "operation": "count",
                            "entity": "rejections",
                            "value_field": None,
                            "group_by": None,
                            "filters": {"period": "3 month", "stages": "103677"}
                        }
                    },
                    {
                        "label": "Конверсия в финал (%)",
                        "value": {
                            "operation": "avg",
                            "entity": "stages",
                            "value_field": "conversion",
                            "group_by": None,
                            "filters": {"period": "3 month", "stages": "hire"}
                        }
                    }
                ],
                "chart": {
                    "label": "Причины отказов по этапам",
                    "type": "bar",
                    "x_label": "Этап",
                    "y_label": "Количество отказов",
                    "x_axis": {
                        "operation": "count",
                        "entity": "stages",
                        "value_field": None,
                        "group_by": {"field": "stages"},
                        "filters": {"period": "3 month", "stages": "rejection"}
                    },
                    "y_axis": {
                        "operation": "count",
                        "entity": "rejections",
                        "value_field": None,
                        "group_by": {"field": "stages"},
                        "filters": {"period": "3 month"}
                    }
                }
            },
            "questions": [
                "Почему кандидаты отваливаются?",
                "На каких этапах больше отказов?",
                "Проанализируйте причины отказов в воронке"
            ]
        },
        {
            "id": 99,
            "category": "comparison_analysis",
            "report_json": {
                "report_title": "Общая эффективность системы найма",
                "main_metric": {
                    "label": "Общая конверсия найма (%)",
                    "value": {
                        "operation": "avg",
                        "entity": "vacancies",
                        "value_field": "conversion",
                        "group_by": None,
                        "filters": {"period": "1 year"}
                    }
                },
                "secondary_metrics": [
                    {
                        "label": "Среднее время найма (дни)",
                        "value": {
                            "operation": "avg",
                            "entity": "hires",
                            "value_field": "time_to_hire",
                            "group_by": None,
                            "filters": {"period": "1 year"}
                        }
                    },
                    {
                        "label": "Закрытых вакансий (%)",
                        "value": {
                            "operation": "count",
                            "entity": "vacancies",
                            "value_field": None,
                            "group_by": None,
                            "filters": {"period": "1 year", "vacancies": "closed"}
                        }
                    }
                ],
                "chart": {
                    "label": "Общие показатели найма за год",
                    "type": "line",
                    "x_label": "Месяц",
                    "y_label": "Конверсия (%)",
                    "x_axis": {
                        "operation": "date_trunc",
                        "entity": "vacancies",
                        "value_field": None,
                        "group_by": {"field": "month"},
                        "date_trunc": "month",
                        "filters": {"period": "1 year"}
                    },
                    "y_axis": {
                        "operation": "avg",
                        "entity": "vacancies",
                        "value_field": "conversion",
                        "group_by": {"field": "month"},
                        "filters": {"period": "1 year"}
                    }
                }
            },
            "questions": [
                "Как у нас дела с наймом в целом?",
                "Какая общая эффективность системы?",
                "Предоставьте общий анализ эффективности найма за год"
            ]
        },
        {
            "id": 100,
            "category": "general_pipeline",
            "report_json": {
                "report_title": "Итоговая сводка по найму",
                "main_metric": {
                    "label": "Всего нанято за год",
                    "value": {
                        "operation": "count",
                        "entity": "hires",
                        "value_field": None,
                        "group_by": None,
                        "filters": {"period": "1 year"}
                    }
                },
                "secondary_metrics": [
                    {
                        "label": "Всего кандидатов обработано",
                        "value": {
                            "operation": "count",
                            "entity": "applicants",
                            "value_field": None,
                            "group_by": None,
                            "filters": {"period": "1 year"}
                        }
                    },
                    {
                        "label": "Активных вакансий сейчас",
                        "value": {
                            "operation": "count",
                            "entity": "vacancies",
                            "value_field": None,
                            "group_by": None,
                            "filters": {"vacancies": "open"}
                        }
                    }
                ],
                "chart": {
                    "label": "Сводка результатов по месяцам",
                    "type": "bar",
                    "x_label": "Месяц",
                    "y_label": "Количество нанятых",
                    "x_axis": {
                        "operation": "date_trunc",
                        "entity": "hires",
                        "value_field": None,
                        "group_by": {"field": "month"},
                        "date_trunc": "month",
                        "filters": {"period": "1 year"}
                    },
                    "y_axis": {
                        "operation": "count",
                        "entity": "hires",
                        "value_field": None,
                        "group_by": {"field": "month"},
                        "filters": {"period": "1 year"}
                    }
                }
            },
            "questions": [
                "Покажи итоговую сводку по найму",
                "Какие общие результаты за год?",
                "Предоставьте сводный отчет по всем результатам найма"
            ]
        }
    ]
    
    reports.extend(comparison_reports)
    
    # Category 9: Advanced Mixed Scenarios (30 additional reports)
    advanced_reports = []
    
    # Complex filtering scenarios
    for i in range(5):
        recruiter = ENTITIES["recruiters"][i % len(ENTITIES["recruiters"])]
        source = ENTITIES["sources"][i % len(ENTITIES["sources"])]
        division = ENTITIES["divisions"][i % len(ENTITIES["divisions"])]
        
        advanced_reports.extend([
            {
                "id": 101 + i*6 + 1,
                "category": "advanced_mixed",
                "report_json": {
                    "report_title": f"Кросс-анализ {recruiter['name']} и {source['name']}",
                    "main_metric": {
                        "label": f"Нанято {recruiter['name']} через {source['name']}",
                        "value": {
                            "operation": "count",
                            "entity": "hires",
                            "value_field": None,
                            "group_by": None,
                            "filters": {
                                "period": "6 month",
                                "and": [
                                    {"recruiters": recruiter["id"]},
                                    {"sources": source["id"]}
                                ]
                            }
                        }
                    },
                    "secondary_metrics": [
                        {
                            "label": f"Кандидатов {recruiter['name']} из {source['name']}",
                            "value": {
                                "operation": "count",
                                "entity": "applicants",
                                "value_field": None,
                                "group_by": None,
                                "filters": {
                                    "period": "6 month",
                                    "and": [
                                        {"recruiters": recruiter["id"]},
                                        {"sources": source["id"]}
                                    ]
                                }
                            }
                        },
                        {
                            "label": f"Конверсия {recruiter['name']} с {source['name']}",
                            "value": {
                                "operation": "avg",
                                "entity": "vacancies",
                                "value_field": "conversion",
                                "group_by": None,
                                "filters": {
                                    "period": "6 month",
                                    "and": [
                                        {"recruiters": recruiter["id"]},
                                        {"sources": source["id"]}
                                    ]
                                }
                            }
                        }
                    ],
                    "chart": {
                        "label": f"Результаты {recruiter['name']} из {source['name']} по месяцам",
                        "type": "line",
                        "x_label": "Месяц",
                        "y_label": "Количество нанятых",
                        "x_axis": {
                            "operation": "date_trunc",
                            "entity": "hires",
                            "value_field": None,
                            "group_by": {"field": "month"},
                            "date_trunc": "month",
                            "filters": {
                                "period": "6 month",
                                "and": [
                                    {"recruiters": recruiter["id"]},
                                    {"sources": source["id"]}
                                ]
                            }
                        },
                        "y_axis": {
                            "operation": "count",
                            "entity": "hires",
                            "value_field": None,
                            "group_by": {"field": "month"},
                            "filters": {
                                "period": "6 month",
                                "and": [
                                    {"recruiters": recruiter["id"]},
                                    {"sources": source["id"]}
                                ]
                            }
                        }
                    }
                },
                "questions": [
                    f"Сколько нанял {recruiter['name']} через {source['name']}?",
                    f"Как работает связка {recruiter['name']} + {source['name']}?",
                    f"Проанализируйте эффективность рекрутера {recruiter['name']} при работе с источником {source['name']}"
                ]
            },
            {
                "id": 101 + i*6 + 2,
                "category": "advanced_mixed",
                "report_json": {
                    "report_title": f"OR-фильтр: {source['name']} или {ENTITIES['sources'][(i+1) % len(ENTITIES['sources'])]['name']}",
                    "main_metric": {
                        "label": f"Нанято из топ источников",
                        "value": {
                            "operation": "count",
                            "entity": "hires",
                            "value_field": None,
                            "group_by": None,
                            "filters": {
                                "period": "3 month",
                                "or": [
                                    {"sources": source["id"]},
                                    {"sources": ENTITIES['sources'][(i+1) % len(ENTITIES['sources'])]["id"]}
                                ]
                            }
                        }
                    },
                    "secondary_metrics": [
                        {
                            "label": f"Из {source['name']} отдельно",
                            "value": {
                                "operation": "count",
                                "entity": "hires",
                                "value_field": None,
                                "group_by": None,
                                "filters": {"period": "3 month", "sources": source["id"]}
                            }
                        },
                        {
                            "label": f"Из {ENTITIES['sources'][(i+1) % len(ENTITIES['sources'])]['name']} отдельно",
                            "value": {
                                "operation": "count",
                                "entity": "hires",
                                "value_field": None,
                                "group_by": None,
                                "filters": {"period": "3 month", "sources": ENTITIES['sources'][(i+1) % len(ENTITIES['sources'])]["id"]}
                            }
                        }
                    ],
                    "chart": {
                        "label": "Сравнение топ источников",
                        "type": "bar",
                        "x_label": "Источник",
                        "y_label": "Количество нанятых",
                        "x_axis": {
                            "operation": "count",
                            "entity": "sources",
                            "value_field": None,
                            "group_by": {"field": "sources"},
                            "filters": {
                                "period": "3 month",
                                "sources": {"operator": "in", "value": [source["id"], ENTITIES['sources'][(i+1) % len(ENTITIES['sources'])]["id"]]}
                            }
                        },
                        "y_axis": {
                            "operation": "count",
                            "entity": "hires",
                            "value_field": None,
                            "group_by": {"field": "sources"},
                            "filters": {
                                "period": "3 month",
                                "sources": {"operator": "in", "value": [source["id"], ENTITIES['sources'][(i+1) % len(ENTITIES['sources'])]["id"]]}
                            }
                        }
                    }
                },
                "questions": [
                    f"Сравни {source['name']} и {ENTITIES['sources'][(i+1) % len(ENTITIES['sources'])]['name']}",
                    f"Что лучше: {source['name']} или {ENTITIES['sources'][(i+1) % len(ENTITIES['sources'])]['name']}?",
                    f"Предоставьте сравнительный анализ источников {source['name']} и {ENTITIES['sources'][(i+1) % len(ENTITIES['sources'])]['name']}"
                ]
            },
            {
                "id": 101 + i*6 + 3,
                "category": "advanced_mixed",
                "report_json": {
                    "report_title": f"Численные операторы: вакансии старше 30 дней в {division['name']}",
                    "main_metric": {
                        "label": f"Старых вакансий в {division['name']}",
                        "value": {
                            "operation": "count",
                            "entity": "vacancies",
                            "value_field": None,
                            "group_by": None,
                            "filters": {
                                "and": [
                                    {"divisions": division["id"]},
                                    {"vacancies": "open"},
                                    {"days_active": {"operator": "gt", "value": 30}}
                                ]
                            }
                        }
                    },
                    "secondary_metrics": [
                        {
                            "label": f"Всего открытых в {division['name']}",
                            "value": {
                                "operation": "count",
                                "entity": "vacancies",
                                "value_field": None,
                                "group_by": None,
                                "filters": {
                                    "divisions": division["id"],
                                    "vacancies": "open"
                                }
                            }
                        },
                        {
                            "label": f"Среднее время открытия в {division['name']}",
                            "value": {
                                "operation": "avg",
                                "entity": "vacancies",
                                "value_field": "days_active",
                                "group_by": None,
                                "filters": {
                                    "divisions": division["id"],
                                    "vacancies": "open"
                                }
                            }
                        }
                    ],
                    "chart": {
                        "label": f"Распределение вакансий по времени открытия в {division['name']}",
                        "type": "bar",
                        "x_label": "Возраст вакансии (дни)",
                        "y_label": "Количество вакансий",
                        "x_axis": {
                            "operation": "count",
                            "entity": "vacancies",
                            "value_field": "days_active",
                            "group_by": {"field": "days_active"},
                            "filters": {
                                "divisions": division["id"],
                                "vacancies": "open"
                            }
                        },
                        "y_axis": {
                            "operation": "count",
                            "entity": "vacancies",
                            "value_field": None,
                            "group_by": {"field": "days_active"},
                            "filters": {
                                "divisions": division["id"],
                                "vacancies": "open"
                            }
                        }
                    }
                },
                "questions": [
                    f"Сколько старых вакансий в {division['name']}?",
                    f"Какие вакансии долго висят в {division['name']}?",
                    f"Проанализируйте вакансии старше месяца в {division['name']}"
                ]
            },
            {
                "id": 101 + i*6 + 4,
                "category": "advanced_mixed",
                "report_json": {
                    "report_title": f"Nested фильтры: {recruiter['name']} в {division['name']} за последние 2 недели",
                    "main_metric": {
                        "label": f"Активность {recruiter['name']} в {division['name']}",
                        "value": {
                            "operation": "count",
                            "entity": "actions",
                            "value_field": None,
                            "group_by": None,
                            "filters": {
                                "period": "2 weeks",
                                "and": [
                                    {"recruiters": recruiter["id"]},
                                    {"divisions": division["id"]},
                                    {
                                        "or": [
                                            {"actions": "add"},
                                            {"actions": "interview"}
                                        ]
                                    }
                                ]
                            }
                        }
                    },
                    "secondary_metrics": [
                        {
                            "label": f"Добавлений кандидатов {recruiter['name']}",
                            "value": {
                                "operation": "count",
                                "entity": "actions",
                                "value_field": None,
                                "group_by": None,
                                "filters": {
                                    "period": "2 weeks",
                                    "and": [
                                        {"recruiters": recruiter["id"]},
                                        {"divisions": division["id"]},
                                        {"actions": "add"}
                                    ]
                                }
                            }
                        },
                        {
                            "label": f"Интервью {recruiter['name']}",
                            "value": {
                                "operation": "count",
                                "entity": "actions",
                                "value_field": None,
                                "group_by": None,
                                "filters": {
                                    "period": "2 weeks",
                                    "and": [
                                        {"recruiters": recruiter["id"]},
                                        {"divisions": division["id"]},
                                        {"actions": "interview"}
                                    ]
                                }
                            }
                        }
                    ],
                    "chart": {
                        "label": f"Активность {recruiter['name']} в {division['name']} по дням",
                        "type": "line",
                        "x_label": "День",
                        "y_label": "Количество действий",
                        "x_axis": {
                            "operation": "date_trunc",
                            "entity": "actions",
                            "value_field": None,
                            "group_by": {"field": "day"},
                            "date_trunc": "day",
                            "filters": {
                                "period": "2 weeks",
                                "and": [
                                    {"recruiters": recruiter["id"]},
                                    {"divisions": division["id"]}
                                ]
                            }
                        },
                        "y_axis": {
                            "operation": "count",
                            "entity": "actions",
                            "value_field": None,
                            "group_by": {"field": "day"},
                            "filters": {
                                "period": "2 weeks",
                                "and": [
                                    {"recruiters": recruiter["id"]},
                                    {"divisions": division["id"]}
                                ]
                            }
                        }
                    }
                },
                "questions": [
                    f"Что делал {recruiter['name']} в {division['name']} на этой неделе?",
                    f"Какая активность у {recruiter['name']} в отделе {division['name']}?",
                    f"Проанализируйте последнюю активность рекрутера {recruiter['name']} в {division['name']}"
                ]
            },
            {
                "id": 101 + i*6 + 5,
                "category": "advanced_mixed",
                "report_json": {
                    "report_title": f"Between операторы: время найма 10-50 дней",
                    "main_metric": {
                        "label": "Нанятых за оптимальное время",
                        "value": {
                            "operation": "count",
                            "entity": "hires",
                            "value_field": None,
                            "group_by": None,
                            "filters": {
                                "period": "6 month",
                                "time_to_hire": {"operator": "between", "value": [10, 50]}
                            }
                        }
                    },
                    "secondary_metrics": [
                        {
                            "label": "Быстрых найма (<10 дней)",
                            "value": {
                                "operation": "count",
                                "entity": "hires",
                                "value_field": None,
                                "group_by": None,
                                "filters": {
                                    "period": "6 month",
                                    "time_to_hire": {"operator": "lt", "value": 10}
                                }
                            }
                        },
                        {
                            "label": "Медленных найма (>50 дней)",
                            "value": {
                                "operation": "count",
                                "entity": "hires",
                                "value_field": None,
                                "group_by": None,
                                "filters": {
                                    "period": "6 month",
                                    "time_to_hire": {"operator": "gt", "value": 50}
                                }
                            }
                        }
                    ],
                    "chart": {
                        "label": "Распределение найма по скорости",
                        "type": "bar",
                        "x_label": "Диапазон времени (дни)",
                        "y_label": "Количество найма",
                        "x_axis": {
                            "operation": "count",
                            "entity": "hires",
                            "value_field": "time_to_hire",
                            "group_by": {"field": "time_to_hire"},
                            "filters": {"period": "6 month"}
                        },
                        "y_axis": {
                            "operation": "count",
                            "entity": "hires",
                            "value_field": None,
                            "group_by": {"field": "time_to_hire"},
                            "filters": {"period": "6 month"}
                        }
                    }
                },
                "questions": [
                    "Сколько нанимаем за оптимальное время?",
                    "Как распределяется скорость найма?",
                    "Проанализируйте найм по скорости закрытия вакансий"
                ]
            },
            {
                "id": 101 + i*6 + 6,
                "category": "advanced_mixed",
                "report_json": {
                    "report_title": f"Contains операторы: вакансии с 'разработ' в названии",
                    "main_metric": {
                        "label": "IT-вакансий",
                        "value": {
                            "operation": "count",
                            "entity": "vacancies",
                            "value_field": None,
                            "group_by": None,
                            "filters": {
                                "period": "3 month",
                                "position": {"operator": "contains", "value": "разработ"}
                            }
                        }
                    },
                    "secondary_metrics": [
                        {
                            "label": "Кандидатов на IT-позиции",
                            "value": {
                                "operation": "count",
                                "entity": "applicants",
                                "value_field": None,
                                "group_by": None,
                                "filters": {
                                    "period": "3 month",
                                    "vacancy_position": {"operator": "contains", "value": "разработ"}
                                }
                            }
                        },
                        {
                            "label": "Нанятых разработчиков",
                            "value": {
                                "operation": "count",
                                "entity": "hires",
                                "value_field": None,
                                "group_by": None,
                                "filters": {
                                    "period": "3 month",
                                    "vacancy_position": {"operator": "contains", "value": "разработ"}
                                }
                            }
                        }
                    ],
                    "chart": {
                        "label": "IT-вакансии по этапам",
                        "type": "bar",
                        "x_label": "Этап",
                        "y_label": "Количество кандидатов",
                        "x_axis": {
                            "operation": "count",
                            "entity": "stages",
                            "value_field": None,
                            "group_by": {"field": "stages"},
                            "filters": {
                                "period": "3 month",
                                "vacancy_position": {"operator": "contains", "value": "разработ"}
                            }
                        },
                        "y_axis": {
                            "operation": "count",
                            "entity": "applicants",
                            "value_field": None,
                            "group_by": {"field": "stages"},
                            "filters": {
                                "period": "3 month",
                                "vacancy_position": {"operator": "contains", "value": "разработ"}
                            }
                        }
                    }
                },
                "questions": [
                    "Сколько вакансий для разработчиков?",
                    "Как дела с наймом разработчиков?",
                    "Проанализируйте найм IT-специалистов"
                ]
            }
        ])
    
    reports.extend(advanced_reports)
    
    # Category 10: Complex Operators & Multi-Parameter Filtering (30 reports)
    complex_operator_reports = []
    
    # Complex numerical operators tests
    for i in range(10):
        recruiter = ENTITIES["recruiters"][i % len(ENTITIES["recruiters"])]
        source = ENTITIES["sources"][i % len(ENTITIES["sources"])]
        
        complex_operator_reports.extend([
            {
                "id": 131 + i*3 + 1,
                "category": "complex_operators",
                "report_json": {
                    "report_title": f"Быстрые найма через {source['name']} (менее 20 дней)",
                    "main_metric": {
                        "label": f"Быстрых найма через {source['name']}",
                        "value": {
                            "operation": "count",
                            "entity": "hires",
                            "value_field": None,
                            "group_by": None,
                            "filters": {
                                "and": [
                                    {"sources": source["id"]},
                                    {"time_to_hire": {"operator": "lt", "value": 20}},
                                    {"period": "6 month"}
                                ]
                            }
                        }
                    },
                    "secondary_metrics": [
                        {
                            "label": f"Медленных найма через {source['name']} (>50 дней)",
                            "value": {
                                "operation": "count",
                                "entity": "hires",
                                "value_field": None,
                                "group_by": None,
                                "filters": {
                                    "and": [
                                        {"sources": source["id"]},
                                        {"time_to_hire": {"operator": "gt", "value": 50}},
                                        {"period": "6 month"}
                                    ]
                                }
                            }
                        },
                        {
                            "label": f"Оптимальных найма через {source['name']} (20-50 дней)",
                            "value": {
                                "operation": "count",
                                "entity": "hires",
                                "value_field": None,
                                "group_by": None,
                                "filters": {
                                    "and": [
                                        {"sources": source["id"]},
                                        {"time_to_hire": {"operator": "between", "value": [20, 50]}},
                                        {"period": "6 month"}
                                    ]
                                }
                            }
                        }
                    ],
                    "chart": {
                        "label": f"Распределение найма по скорости через {source['name']}",
                        "type": "bar",
                        "x_label": "Диапазон времени найма",
                        "y_label": "Количество найма",
                        "x_axis": {
                            "operation": "count",
                            "entity": "hires",
                            "value_field": "time_to_hire",
                            "group_by": {"field": "time_to_hire"},
                            "filters": {
                                "sources": source["id"],
                                "period": "6 month"
                            }
                        },
                        "y_axis": {
                            "operation": "count",
                            "entity": "hires",
                            "value_field": None,
                            "group_by": {"field": "time_to_hire"},
                            "filters": {
                                "sources": source["id"],
                                "period": "6 month"
                            }
                        }
                    }
                },
                "questions": [
                    f"Сколько быстро нанимаем через {source['name']}?",
                    f"Какая скорость найма у {source['name']}?",
                    f"Покажи быстрые найма через {source['name']} менее 20 дней"
                ]
            },
            {
                "id": 131 + i*3 + 2,
                "category": "complex_operators",
                "report_json": {
                    "report_title": f"Многоуровневая фильтрация: {recruiter['name']} + {source['name']} + IT",
                    "main_metric": {
                        "label": f"IT-найма {recruiter['name']} из {source['name']}",
                        "value": {
                            "operation": "count",
                            "entity": "hires",
                            "value_field": None,
                            "group_by": None,
                            "filters": {
                                "and": [
                                    {"recruiters": recruiter["id"]},
                                    {"sources": source["id"]},
                                    {
                                        "or": [
                                            {"vacancy_position": {"operator": "contains", "value": "разработ"}},
                                            {"vacancy_position": {"operator": "contains", "value": "программ"}},
                                            {"vacancy_position": {"operator": "contains", "value": "developer"}}
                                        ]
                                    },
                                    {"period": "1 year"}
                                ]
                            }
                        }
                    },
                    "secondary_metrics": [
                        {
                            "label": f"Всего IT-кандидатов {recruiter['name']} из {source['name']}",
                            "value": {
                                "operation": "count",
                                "entity": "applicants",
                                "value_field": None,
                                "group_by": None,
                                "filters": {
                                    "and": [
                                        {"recruiters": recruiter["id"]},
                                        {"sources": source["id"]},
                                        {
                                            "or": [
                                                {"vacancy_position": {"operator": "contains", "value": "разработ"}},
                                                {"vacancy_position": {"operator": "contains", "value": "программ"}},
                                                {"vacancy_position": {"operator": "contains", "value": "developer"}}
                                            ]
                                        },
                                        {"period": "1 year"}
                                    ]
                                }
                            }
                        },
                        {
                            "label": f"Средняя IT-конверсия {recruiter['name']}",
                            "value": {
                                "operation": "avg",
                                "entity": "vacancies",
                                "value_field": "conversion",
                                "group_by": None,
                                "filters": {
                                    "and": [
                                        {"recruiters": recruiter["id"]},
                                        {"sources": source["id"]},
                                        {"position": {"operator": "contains", "value": "разработ"}},
                                        {"period": "1 year"}
                                    ]
                                }
                            }
                        }
                    ],
                    "chart": {
                        "label": f"IT-найм {recruiter['name']} по месяцам",
                        "type": "line",
                        "x_label": "Месяц",
                        "y_label": "Количество IT-найма",
                        "x_axis": {
                            "operation": "date_trunc",
                            "entity": "hires",
                            "value_field": None,
                            "group_by": {"field": "month"},
                            "date_trunc": "month",
                            "filters": {
                                "and": [
                                    {"recruiters": recruiter["id"]},
                                    {"sources": source["id"]},
                                    {"vacancy_position": {"operator": "contains", "value": "разработ"}},
                                    {"period": "1 year"}
                                ]
                            }
                        },
                        "y_axis": {
                            "operation": "count",
                            "entity": "hires",
                            "value_field": None,
                            "group_by": {"field": "month"},
                            "filters": {
                                "and": [
                                    {"recruiters": recruiter["id"]},
                                    {"sources": source["id"]},
                                    {"vacancy_position": {"operator": "contains", "value": "разработ"}},
                                    {"period": "1 year"}
                                ]
                            }
                        }
                    }
                },
                "questions": [
                    f"Сколько IT-шников нанял {recruiter['name']} через {source['name']}?",
                    f"Как {recruiter['name']} работает с {source['name']} по разработчикам?",
                    f"Покажи IT-найм {recruiter['name']} из источника {source['name']}"
                ]
            },
            {
                "id": 131 + i*3 + 3,
                "category": "complex_operators",
                "report_json": {
                    "report_title": f"Исключающие фильтры: НЕ {source['name']} И НЕ старше 60 дней",
                    "main_metric": {
                        "label": f"Найма НЕ из {source['name']} за разумное время",
                        "value": {
                            "operation": "count",
                            "entity": "hires",
                            "value_field": None,
                            "group_by": None,
                            "filters": {
                                "and": [
                                    {"sources": {"operator": "not_in", "value": [source["id"]]}},
                                    {"time_to_hire": {"operator": "lte", "value": 60}},
                                    {"period": "6 month"}
                                ]
                            }
                        }
                    },
                    "secondary_metrics": [
                        {
                            "label": f"Всего найма НЕ из {source['name']}",
                            "value": {
                                "operation": "count",
                                "entity": "hires",
                                "value_field": None,
                                "group_by": None,
                                "filters": {
                                    "and": [
                                        {"sources": {"operator": "not_in", "value": [source["id"]]}},
                                        {"period": "6 month"}
                                    ]
                                }
                            }
                        },
                        {
                            "label": f"Альтернативных источников (кроме {source['name']})",
                            "value": {
                                "operation": "count",
                                "entity": "sources",
                                "value_field": None,
                                "group_by": None,
                                "filters": {
                                    "and": [
                                        {"sources": {"operator": "not_in", "value": [source["id"]]}},
                                        {"period": "6 month"}
                                    ]
                                }
                            }
                        }
                    ],
                    "chart": {
                        "label": f"Альтернативные источники (исключая {source['name']})",
                        "type": "bar",
                        "x_label": "Источник",
                        "y_label": "Количество найма",
                        "x_axis": {
                            "operation": "count",
                            "entity": "sources",
                            "value_field": None,
                            "group_by": {"field": "sources"},
                            "filters": {
                                "and": [
                                    {"sources": {"operator": "not_in", "value": [source["id"]]}},
                                    {"period": "6 month"}
                                ]
                            }
                        },
                        "y_axis": {
                            "operation": "count",
                            "entity": "hires",
                            "value_field": None,
                            "group_by": {"field": "sources"},
                            "filters": {
                                "and": [
                                    {"sources": {"operator": "not_in", "value": [source["id"]]}},
                                    {"period": "6 month"}
                                ]
                            }
                        }
                    }
                },
                "questions": [
                    f"Сколько нанимаем НЕ через {source['name']}?",
                    f"Какие альтернативы {source['name']}?",
                    f"Покажи найм исключая {source['name']} за разумное время"
                ]
            }
        ])
    
    reports.extend(complex_operator_reports)
    
    # Category 11: Abstract & Vague Questions (15 reports)
    abstract_questions_reports = [
        {
            "id": 161,
            "category": "abstract_questions",
            "report_json": {
                "report_title": "Состояние воронки найма",
                "main_metric": {
                    "label": "Кандидатов в воронке",
                    "value": {
                        "operation": "count",
                        "entity": "applicants",
                        "value_field": None,
                        "group_by": None,
                        "filters": {"period": "1 month"}
                    }
                },
                "secondary_metrics": [
                    {
                        "label": "Прогресс по этапам",
                        "value": {
                            "operation": "count",
                            "entity": "actions",
                            "value_field": None,
                            "group_by": None,
                            "filters": {"period": "1 month", "actions": "move"}
                        }
                    },
                    {
                        "label": "Общая конверсия",
                        "value": {
                            "operation": "avg",
                            "entity": "vacancies",
                            "value_field": "conversion",
                            "group_by": None,
                            "filters": {"period": "1 month"}
                        }
                    }
                ],
                "chart": {
                    "label": "Распределение кандидатов по воронке",
                    "type": "bar",
                    "x_label": "Этап воронки",
                    "y_label": "Количество кандидатов",
                    "x_axis": {
                        "operation": "count",
                        "entity": "stages",
                        "value_field": None,
                        "group_by": {"field": "stages"},
                        "filters": {"period": "1 month"}
                    },
                    "y_axis": {
                        "operation": "count",
                        "entity": "applicants",
                        "value_field": None,
                        "group_by": {"field": "stages"},
                        "filters": {"period": "1 month"}
                    }
                }
            },
            "questions": [
                "Что с воронкой?",
                "Как дела с воронкой найма?",
                "Покажи состояние воронки"
            ]
        },
        {
            "id": 162,
            "category": "abstract_questions",
            "report_json": {
                "report_title": "Общая ситуация с наймом",
                "main_metric": {
                    "label": "Нанято за месяц",
                    "value": {
                        "operation": "count",
                        "entity": "hires",
                        "value_field": None,
                        "group_by": None,
                        "filters": {"period": "1 month"}
                    }
                },
                "secondary_metrics": [
                    {
                        "label": "Новых кандидатов",
                        "value": {
                            "operation": "count",
                            "entity": "applicants",
                            "value_field": None,
                            "group_by": None,
                            "filters": {"period": "1 month"}
                        }
                    },
                    {
                        "label": "Среднее время найма",
                        "value": {
                            "operation": "avg",
                            "entity": "hires",
                            "value_field": "time_to_hire",
                            "group_by": None,
                            "filters": {"period": "1 month"}
                        }
                    }
                ],
                "chart": {
                    "label": "Активность найма за месяц",
                    "type": "line",
                    "x_label": "День",
                    "y_label": "Активность",
                    "x_axis": {
                        "operation": "date_trunc",
                        "entity": "actions",
                        "value_field": None,
                        "group_by": {"field": "day"},
                        "date_trunc": "day",
                        "filters": {"period": "1 month"}
                    },
                    "y_axis": {
                        "operation": "count",
                        "entity": "actions",
                        "value_field": None,
                        "group_by": {"field": "day"},
                        "filters": {"period": "1 month"}
                    }
                }
            },
            "questions": [
                "Как дела с наймом?",
                "Что происходит с наймом?",
                "Какая ситуация с рекрутментом?"
            ]
        },
        {
            "id": 163,
            "category": "abstract_questions",
            "report_json": {
                "report_title": "Активность команды",
                "main_metric": {
                    "label": "Активных рекрутеров",
                    "value": {
                        "operation": "count",
                        "entity": "recruiters",
                        "value_field": None,
                        "group_by": None,
                        "filters": {"period": "2 weeks", "recruiters": "with_vacancies"}
                    }
                },
                "secondary_metrics": [
                    {
                        "label": "Общих действий команды",
                        "value": {
                            "operation": "count",
                            "entity": "actions",
                            "value_field": None,
                            "group_by": None,
                            "filters": {"period": "2 weeks"}
                        }
                    },
                    {
                        "label": "Средняя активность на человека",
                        "value": {
                            "operation": "avg",
                            "entity": "actions",
                            "value_field": "count",
                            "group_by": None,
                            "filters": {"period": "2 weeks"}
                        }
                    }
                ],
                "chart": {
                    "label": "Активность рекрутеров",
                    "type": "bar",
                    "x_label": "Рекрутер",
                    "y_label": "Количество действий",
                    "x_axis": {
                        "operation": "count",
                        "entity": "recruiters",
                        "value_field": None,
                        "group_by": {"field": "recruiters"},
                        "filters": {"period": "2 weeks"}
                    },
                    "y_axis": {
                        "operation": "count",
                        "entity": "actions",
                        "value_field": None,
                        "group_by": {"field": "recruiters"},
                        "filters": {"period": "2 weeks"}
                    }
                }
            },
            "questions": [
                "Как работает команда?",
                "Что делает команда?",
                "Покажи активность команды"
            ]
        }
    ]
    
    # Add more abstract questions to reach 15 total
    for i in range(12):
        if i < 5:
            # General abstract questions
            abstract_questions_reports.append({
                "id": 164 + i,
                "category": "abstract_questions",
                "report_json": {
                    "report_title": ["Проблемы в процессе", "Эффективность источников", "Качество работы", "Общая производительность", "Узкие места"][i],
                    "main_metric": {
                        "label": ["Отказов за месяц", "Лучший источник", "Показатель качества найма", "Производительность команды", "Проблемных вакансий"][i],
                        "value": {
                            "operation": ["count", "count", "avg", "avg", "count"][i],
                            "entity": ["rejections", "hires", "hires", "recruiters", "vacancies"][i],
                            "value_field": [None, None, "quality_score", "performance", None][i],
                            "group_by": None,
                            "filters": {"period": "1 month"} if i != 4 else {"and": [{"vacancies": "open"}, {"days_active": {"operator": "gt", "value": 45}}]}
                        }
                    },
                    "secondary_metrics": [
                        {
                            "label": f"Secondary metric {i+1}",
                            "value": {
                                "operation": "count",
                                "entity": "applicants",
                                "value_field": None,
                                "group_by": None,
                                "filters": {"period": "1 month"}
                            }
                        }
                    ],
                    "chart": {
                        "label": f"Chart for abstract question {i+1}",
                        "type": ["bar", "bar", "line", "scatter", "bar"][i],
                        "x_label": "Category",
                        "y_label": "Value",
                        "x_axis": {
                            "operation": "count",
                            "entity": "stages",
                            "value_field": None,
                            "group_by": {"field": "stages"},
                            "filters": {"period": "1 month"}
                        },
                        "y_axis": {
                            "operation": "count",
                            "entity": "applicants",
                            "value_field": None,
                            "group_by": {"field": "stages"},
                            "filters": {"period": "1 month"}
                        }
                    }
                },
                "questions": [
                    ["Что идёт не так?", "Откуда лучше кандидаты?", "Как качество найма?", "Как производительность?", "Какие узкие места?"][i],
                    ["Какие проблемы в найме?", "Какие источники работают?", "Хорошо ли мы работаем?", "Эффективно ли мы работаем?", "Что тормозит процесс?"][i],
                    ["Покажи что тормозит процесс", "Что с источниками найма?", "Покажи качество процесса найма", "Покажи общую эффективность команды", "Где проблемы в процессе?"][i]
                ]
            })
        else:
            # Division-specific abstract questions
            division = ENTITIES["divisions"][(i-5) % len(ENTITIES["divisions"])]
            abstract_questions_reports.append({
                "id": 169 + i - 5,
                "category": "abstract_questions",
                "report_json": {
                    "report_title": f"Ситуация в {division['name']}",
                    "main_metric": {
                        "label": f"Активность в {division['name']}",
                        "value": {
                            "operation": "count",
                            "entity": "applicants",
                            "value_field": None,
                            "group_by": None,
                            "filters": {"period": "1 month", "divisions": division["id"]}
                        }
                    },
                    "secondary_metrics": [
                        {
                            "label": f"Нанято в {division['name']}",
                            "value": {
                                "operation": "count",
                                "entity": "hires",
                                "value_field": None,
                                "group_by": None,
                                "filters": {"period": "1 month", "divisions": division["id"]}
                            }
                        },
                        {
                            "label": f"Вакансий открыто в {division['name']}",
                            "value": {
                                "operation": "count",
                                "entity": "vacancies",
                                "value_field": None,
                                "group_by": None,
                                "filters": {"divisions": division["id"], "vacancies": "open"}
                            }
                        }
                    ],
                    "chart": {
                        "label": f"Динамика найма в {division['name']}",
                        "type": "line",
                        "x_label": "Неделя",
                        "y_label": "Активность",
                        "x_axis": {
                            "operation": "date_trunc",
                            "entity": "applicants",
                            "value_field": None,
                            "group_by": {"field": "week"},
                            "date_trunc": "week",
                            "filters": {"period": "1 month", "divisions": division["id"]}
                        },
                        "y_axis": {
                            "operation": "count",
                            "entity": "applicants",
                            "value_field": None,
                            "group_by": {"field": "week"},
                            "filters": {"period": "1 month", "divisions": division["id"]}
                        }
                    }
                },
                "questions": [
                    f"Что творится в {division['name']}?",
                    f"Как дела в отделе {division['name']}?",
                    f"Покажи ситуацию с {division['name']}"
                ]
            })
    
    reports.extend(abstract_questions_reports)
    
    return reports

def save_sample_reports():
    """Save all sample reports to JSON file"""
    reports = create_sample_reports()
    
    with open('/home/igor/hf/sample_reports_100.json', 'w', encoding='utf-8') as f:
        json.dump(reports, f, indent=2, ensure_ascii=False)
    
    print(f"Generated {len(reports)} sample reports")
    return reports

if __name__ == "__main__":
    reports = save_sample_reports()
    print("Sample reports created successfully!")