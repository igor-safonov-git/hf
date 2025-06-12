#!/usr/bin/env python3
"""
Mock API Response Tests for Huntflow Schema Validation

Tests schema behavior with realistic API responses
"""

import json
from typing import Dict, Any


class HuntflowAPIMocks:
    """Realistic mock responses for Huntflow API endpoints"""
    
    @staticmethod
    def get_vacancies_statuses_response() -> Dict[str, Any]:
        """Mock response for /vacancies/statuses endpoint"""
        return {
            "items": [
                {"id": 1, "name": "Новые", "type": "application", "order": 1},
                {"id": 2, "name": "Скрининг (Телефонное интервью)", "type": "screening", "order": 2},
                {"id": 3, "name": "Собеседование", "type": "interview", "order": 3},
                {"id": 4, "name": "Тестовое задание", "type": "test", "order": 4},
                {"id": 5, "name": "Оффер принят", "type": "hired", "order": 5},
                {"id": 6, "name": "Отказ", "type": "rejected", "order": 6}
            ]
        }
    
    @staticmethod
    def get_applicants_search_response() -> Dict[str, Any]:
        """Mock response for /applicants/search endpoint (NO status field per CLAUDE.md)"""
        return {
            "items": [
                {
                    "id": 12345,
                    "first_name": "Иван",
                    "last_name": "Петров",
                    "vacancy": 1001,       # API field name
                    "source": 201,         # API field name  
                    "recruiter": 301,      # API field name
                    "created": "2024-01-15T10:30:00Z",
                    "updated": "2024-01-20T14:45:00Z",
                    "email": "ivan.petrov@example.com",
                    "phone": "+7 (123) 456-78-90"
                },
                {
                    "id": 12346,
                    "first_name": "Maria",
                    "last_name": "Rodriguez",
                    "vacancy": 1002,
                    "source": 202,
                    "recruiter": 302,
                    "created": "2024-01-16T09:15:00Z",
                    "updated": "2024-01-18T16:20:00Z",
                    "email": "maria.rodriguez@example.com"
                },
                {
                    "id": 12347,
                    "first_name": "Ahmed",
                    "last_name": "Hassan",
                    "vacancy": 1001,
                    "source": 201,
                    "recruiter": 301,
                    "created": "2024-01-17T11:00:00Z",
                    "updated": "2024-01-19T13:30:00Z",
                    "email": "ahmed.hassan@example.com"
                }
            ],
            "total": 150,
            "page": 1,
            "count": 3,
            "has_more": True
        }
    
    @staticmethod
    def get_applicant_logs_response(applicant_id: int) -> Dict[str, Any]:
        """Mock response for /applicants/{id}/logs endpoint"""
        
        # Different logs for different applicants
        logs_data = {
            12345: [
                {
                    "id": 1001,
                    "type": "status_change",
                    "status": 2,  # Скрининг
                    "created": "2024-01-20T14:45:00Z",
                    "message": "Статус изменен на: Скрининг (Телефонное интервью)",
                    "author": {"id": 301, "name": "Jane Smith"}
                },
                {
                    "id": 1000,
                    "type": "status_change", 
                    "status": 1,  # Новые
                    "created": "2024-01-15T10:30:00Z",
                    "message": "Кандидат добавлен",
                    "author": {"id": 301, "name": "Jane Smith"}
                }
            ],
            12346: [
                {
                    "id": 1002,
                    "type": "status_change",
                    "status": 5,  # Оффер принят
                    "created": "2024-01-18T16:20:00Z",
                    "message": "Статус изменен на: Оффер принят",
                    "author": {"id": 302, "name": "John Doe"}
                }
            ],
            12347: [
                {
                    "id": 1003,
                    "type": "status_change",
                    "status": 6,  # Отказ
                    "created": "2024-01-19T13:30:00Z",
                    "message": "Статус изменен на: Отказ",
                    "author": {"id": 301, "name": "Jane Smith"}
                }
            ]
        }
        
        return {
            "items": logs_data.get(applicant_id, [])
        }
    
    @staticmethod
    def get_coworkers_response() -> Dict[str, Any]:
        """Mock response for /coworkers endpoint"""
        return {
            "items": [
                {
                    "id": 301,
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "email": "jane.smith@company.com",
                    "type": "recruiter",
                    "department": "HR",
                    "position": "Senior Recruiter"
                },
                {
                    "id": 302,
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@company.com",
                    "type": "hiring_manager",
                    "department": "Engineering",
                    "position": "Tech Lead"
                },
                {
                    "id": 303,
                    "first_name": "Anna",
                    "last_name": "Wilson",
                    "email": "anna.wilson@company.com",
                    "type": "recruiter",
                    "department": "HR",
                    "position": "Junior Recruiter"
                }
            ]
        }
    
    @staticmethod
    def get_applicants_sources_response() -> Dict[str, Any]:
        """Mock response for /applicants/sources endpoint"""
        return {
            "items": [
                {
                    "id": 201,
                    "name": "LinkedIn",
                    "type": "social_network"
                },
                {
                    "id": 202,
                    "name": "HeadHunter",
                    "type": "job_board"
                },
                {
                    "id": 203,
                    "name": "Referral",
                    "type": "referral"
                },
                {
                    "id": 204,
                    "name": "Company Website",
                    "type": "direct"
                },
                {
                    "id": 205,
                    "name": "Telegram",
                    "type": "social_network"
                }
            ]
        }
    
    @staticmethod
    def get_vacancies_response() -> Dict[str, Any]:
        """Mock response for /vacancies endpoint"""
        return {
            "items": [
                {
                    "id": 1001,
                    "position": "Senior Python Developer",
                    "company": "Tech Corp",
                    "department": "Engineering",
                    "state": "OPEN",
                    "quota": 2,
                    "created": "2024-01-10T09:00:00Z",
                    "updated": "2024-01-15T12:00:00Z"
                },
                {
                    "id": 1002,
                    "position": "Frontend Developer",
                    "company": "Tech Corp",
                    "department": "Engineering", 
                    "state": "OPEN",
                    "quota": 1,
                    "created": "2024-01-12T10:30:00Z",
                    "updated": "2024-01-16T14:20:00Z"
                }
            ]
        }
    
    @staticmethod
    def get_divisions_response() -> Dict[str, Any]:
        """Mock response for /divisions endpoint"""
        return {
            "items": [
                {
                    "id": 1,
                    "name": "Engineering",
                    "active": True
                },
                {
                    "id": 2,
                    "name": "Sales",
                    "active": True
                },
                {
                    "id": 3,
                    "name": "Marketing",
                    "active": True
                },
                {
                    "id": 4,
                    "name": "HR",
                    "active": True
                }
            ]
        }
    
    @classmethod
    def get_mock_router(cls):
        """Returns a function that routes mock requests to appropriate responses"""
        
        async def mock_request_router(method: str, url: str, params: Dict[str, Any] = None, **kwargs):
            """Route mock requests based on URL patterns"""
            
            if 'vacancies/statuses' in url:
                return cls.get_vacancies_statuses_response()
            
            elif 'applicants/search' in url:
                return cls.get_applicants_search_response()
            
            elif 'applicants/' in url and '/logs' in url:
                # Extract applicant ID from URL
                applicant_id = int(url.split('applicants/')[1].split('/')[0])
                return cls.get_applicant_logs_response(applicant_id)
            
            elif 'applicants/sources' in url:
                return cls.get_applicants_sources_response()
            
            elif 'coworkers' in url:
                return cls.get_coworkers_response()
            
            elif 'vacancies' in url and 'statuses' not in url:
                return cls.get_vacancies_response()
            
            elif 'divisions' in url:
                return cls.get_divisions_response()
            
            else:
                # Unknown endpoint
                return {"items": [], "error": f"Mock not found for: {url}"}
        
        return mock_request_router


def test_mock_responses():
    """Test that mock responses match expected API structure"""
    
    mocks = HuntflowAPIMocks()
    
    print("🧪 Testing Mock API Responses...")
    print("=" * 40)
    
    # Test applicants response structure
    applicants = mocks.get_applicants_search_response()
    print(f"✅ Applicants mock: {len(applicants['items'])} items")
    
    # Verify no status field (critical per CLAUDE.md)
    for applicant in applicants['items']:
        assert 'status' not in applicant, f"Applicant {applicant['id']} should not have 'status' field!"
        assert 'vacancy' in applicant, f"Applicant {applicant['id']} missing 'vacancy' field"
        assert 'source' in applicant, f"Applicant {applicant['id']} missing 'source' field"
        assert 'recruiter' in applicant, f"Applicant {applicant['id']} missing 'recruiter' field"
    
    print("✅ Applicants mock validation passed")
    
    # Test logs response structure
    logs = mocks.get_applicant_logs_response(12345)
    print(f"✅ Logs mock: {len(logs['items'])} items")
    
    # Verify status field exists in logs
    for log in logs['items']:
        if log.get('type') == 'status_change':
            assert 'status' in log, f"Status change log missing 'status' field"
    
    print("✅ Logs mock validation passed")
    
    # Test other endpoints
    statuses = mocks.get_vacancies_statuses_response()
    coworkers = mocks.get_coworkers_response()
    sources = mocks.get_applicants_sources_response()
    
    print(f"✅ Statuses mock: {len(statuses['items'])} items")
    print(f"✅ Coworkers mock: {len(coworkers['items'])} items")
    print(f"✅ Sources mock: {len(sources['items'])} items")
    
    print("\n🎉 All mock responses validated successfully!")


if __name__ == "__main__":
    test_mock_responses()