"""
Huntflow Virtual Table Schema Definitions
Clean, isolated table structures mapping Huntflow API endpoints to SQL tables
"""
from sqlalchemy import MetaData, Table, Column, Integer, String, DateTime, Boolean, Date, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from typing import Dict


def create_huntflow_tables(metadata: MetaData) -> Dict[str, Table]:
    """
    Create all Huntflow virtual table definitions
    
    Args:
        metadata: SQLAlchemy MetaData instance
        
    Returns:
        Dictionary mapping table names to Table objects
    """
    
    # Core recruitment entities
    applicants = Table('applicants', metadata,
        Column('id', Integer, primary_key=True),
        Column('first_name', String),
        Column('last_name', String),
        Column('middle_name', String),  # Available in search response
        Column('birthday', Date),       # Available in search response
        Column('phone', String),        # Available in search response
        Column('skype', String),        # Available in search response
        Column('email', String),        # Available in search response
        Column('money', Numeric(12, 2)), # Salary expectation in search response
        Column('position', String),     # Available in search response
        Column('company', String),      # Available in search response
        Column('photo', Integer),       # Photo ID in search response
        Column('photo_url', String),    # Available in search response
        Column('created', DateTime),
        # Required ApplicantItem fields from individual /applicants/{id} calls
        Column('account', Integer),           # Organization ID
        Column('tags', JSONB),               # List of tags
        Column('external', JSONB),           # Resume data
        Column('agreement', JSONB),          # Agreement state
        Column('doubles', JSONB),            # List of duplicates
        Column('social', JSONB),             # Social accounts
        # Computed fields from logs or individual calls
        Column('source_id', Integer, ForeignKey('sources.id')),      # From logs or individual call
        Column('recruiter_id', Integer, ForeignKey('recruiters.id')), # From logs or individual call
        Column('recruiter_name', String),  # Computed from coworkers mapping
        Column('source_name', String),     # Computed from sources mapping
    )
    
    vacancies = Table('vacancies', metadata,
        Column('id', Integer, primary_key=True),     # Required field per OpenAPI
        Column('position', String, nullable=False),  # Required field per OpenAPI spec
        Column('company', String),                   # Optional field per OpenAPI
        Column('account_division', Integer, ForeignKey('divisions.id')), # Optional field per OpenAPI
        Column('account_region', Integer, ForeignKey('regions.id')),    # Optional field per OpenAPI  
        Column('money', Numeric(12, 2)),            # Optional field per OpenAPI
        Column('priority', Integer),                 # Optional field: 0-1 range per OpenAPI
        Column('hidden', Boolean, default=False),    # Optional field: default false per OpenAPI
        Column('state', String),                     # Optional field per OpenAPI
        Column('created', DateTime, nullable=False), # Required field per OpenAPI
        Column('multiple', Boolean),                 # Optional field per OpenAPI
        Column('parent', Integer),                   # Optional field per OpenAPI
        Column('account_vacancy_status_group', Integer),  # Optional field per OpenAPI
        Column('additional_fields_list', JSONB),    # Optional field per OpenAPI spec
        # Additional fields from VacancyItem that were missing
        Column('updated', DateTime),                 # Optional field per OpenAPI
        Column('body', String),                      # Optional field: responsibilities in HTML
        Column('requirements', String),              # Optional field: requirements in HTML
        Column('conditions', String),                # Optional field: conditions in HTML
        Column('files', JSONB),                      # Optional field: list
        Column('coworkers', JSONB),                  # Optional field: list
        Column('source', Integer),                   # Optional field: vacancy source ID
        Column('blocks', JSONB),                     # Optional field: affiliate vacancies
        Column('vacancy_request', Integer)           # Optional field: vacancy request ID
    )
    
    # Reference data tables
    status_mapping = Table('status_mapping', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String, nullable=False),
        Column('type', String, nullable=False),      # Required per OpenAPI VacancyStatus
        Column('removed', Boolean),                  # Optional per OpenAPI VacancyStatus
        Column('order', Integer, nullable=False),    # Required per OpenAPI VacancyStatus  
        Column('stay_duration', Integer)             # Optional per OpenAPI VacancyStatus (null=unlimited)
    )
    
    recruiters = Table('recruiters', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String),           # Correct field name per OpenAPI CoworkerResponse
        Column('email', String),          # Correct field name per OpenAPI
        Column('member', Integer),        # User ID per OpenAPI CoworkerResponse
        Column('type', String),           # Correct field name (not 'role') per OpenAPI
        Column('head', Integer),          # Head user ID per OpenAPI
        Column('meta', JSONB),            # Additional meta information
        Column('permissions', JSONB),     # Coworker permissions
        Column('full_name', String)       # Computed field
    )
    
    sources = Table('sources', metadata,
        Column('id', Integer, primary_key=True),     # Required per OpenAPI
        Column('name', String, nullable=False),      # Required per OpenAPI
        Column('type', String, nullable=False),      # Required per OpenAPI
        Column('foreign', String)                    # Missing field from OpenAPI spec
    )
    
    divisions = Table('divisions', metadata,
        Column('id', Integer, primary_key=True),     # Required per OpenAPI
        Column('name', String, nullable=False),      # Required per OpenAPI
        Column('order', Integer, nullable=False),    # Required per OpenAPI
        Column('active', Boolean, nullable=False),   # Required per OpenAPI
        Column('deep', Integer, nullable=False),     # Required per OpenAPI
        Column('parent', Integer),                   # Optional per OpenAPI
        Column('foreign', String),                   # Optional per OpenAPI
        Column('meta', JSONB)                        # Optional per OpenAPI
    )
    
    applicant_tags = Table('applicant_tags', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String, nullable=False),
        Column('color', String(7))  # Hex color code
    )
    
    # Relationship and tracking tables
    offers = Table('offers', metadata,
        Column('id', Integer, primary_key=True),
        Column('applicant_id', Integer, ForeignKey('applicants.id'), nullable=False),
        Column('vacancy_id', Integer, ForeignKey('vacancies.id'), nullable=False),
        Column('status', String),
        Column('created', DateTime),
        Column('updated', DateTime)
    )
    
    applicant_links = Table('applicant_links', metadata,
        Column('id', Integer, primary_key=True),
        Column('applicant_id', Integer, ForeignKey('applicants.id'), nullable=False),
        Column('status', Integer, ForeignKey('status_mapping.id'), nullable=False), # Required per OpenAPI
        Column('updated', DateTime),          # Required per OpenAPI  
        Column('changed', DateTime),          # Required per OpenAPI
        Column('vacancy', Integer, ForeignKey('vacancies.id'), nullable=False) # Required per OpenAPI
    )
    
    # Geographic and organizational data
    regions = Table('regions', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String),
        Column('order', Integer),
        Column('foreign', String)
    )
    
    rejection_reasons = Table('rejection_reasons', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String),
        Column('order', Integer)
    )
    
    dictionaries = Table('dictionaries', metadata,
        Column('code', String, primary_key=True),
        Column('name', String),
        Column('items', JSONB)   # Dictionary items
    )
    
    # Activity and response tracking
    applicant_responses = Table('applicant_responses', metadata,
        Column('id', Integer, primary_key=True),
        Column('applicant_id', Integer, ForeignKey('applicants.id')),
        Column('vacancy_id', Integer, ForeignKey('vacancies.id')),
        Column('source', String),
        Column('created', DateTime),
        Column('response_data', JSONB)
    )
    
    vacancy_logs = Table('vacancy_logs', metadata,
        Column('id', Integer, primary_key=True),
        Column('vacancy_id', Integer, ForeignKey('vacancies.id')),
        Column('type', String),
        Column('created', DateTime),
        Column('account_info', JSONB),
        Column('data', JSONB)           # Log data
    )
    
    status_groups = Table('status_groups', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String),
        Column('order', Integer),
        Column('statuses', JSONB)   # Array of status IDs
    )
    
    # Vacancy detail and analytics tables
    vacancy_periods = Table('vacancy_periods', metadata,
        Column('id', Integer, primary_key=True),
        Column('vacancy_id', Integer, ForeignKey('vacancies.id')),
        Column('period_type', String),  # work, hold, closed
        Column('start_date', DateTime),
        Column('end_date', DateTime),
        Column('duration_days', Integer)
    )
    
    vacancy_frames = Table('vacancy_frames', metadata,
        Column('id', Integer, primary_key=True),
        Column('vacancy_id', Integer, ForeignKey('vacancies.id')),
        Column('created', DateTime),
        Column('is_current', Boolean),
        Column('data', JSONB)    # Frame data
    )
    
    vacancy_quotas = Table('vacancy_quotas', metadata,
        Column('id', Integer, primary_key=True),
        Column('vacancy_id', Integer, ForeignKey('vacancies.id')),
        Column('frame_id', Integer, ForeignKey('vacancy_frames.id')),
        Column('quota_value', Integer),
        Column('filled', Integer),
        Column('created', DateTime)
    )
    
    # Audit and system logs
    action_logs = Table('action_logs', metadata,
        Column('id', Integer, primary_key=True),
        Column('type', String),
        Column('created', DateTime),
        Column('account_info', JSONB),
        Column('data', JSONB)           # Log data
    )
    
    # Return all tables as a dictionary for easy access
    return {
        'applicants': applicants,
        'vacancies': vacancies,
        'status_mapping': status_mapping,
        'recruiters': recruiters,
        'sources': sources,
        'divisions': divisions,
        'applicant_tags': applicant_tags,
        'offers': offers,
        'applicant_links': applicant_links,
        'regions': regions,
        'rejection_reasons': rejection_reasons,
        'dictionaries': dictionaries,
        'applicant_responses': applicant_responses,
        'vacancy_logs': vacancy_logs,
        'status_groups': status_groups,
        'vacancy_periods': vacancy_periods,
        'vacancy_frames': vacancy_frames,
        'vacancy_quotas': vacancy_quotas,
        'action_logs': action_logs,
    }