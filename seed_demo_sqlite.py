"""
Seed demo data for Huntflow schema using SQLite
Creates an in-memory SQLite database with realistic recruitment data
"""

from datetime import datetime, timedelta
import random
import json
from faker import Faker
import sqlalchemy as sa
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, Boolean, Date, Numeric, ForeignKey

fake = Faker()
random.seed(42)
Faker.seed(42)

# Create in-memory SQLite database
engine = create_engine("sqlite:///demo.db", echo=False)
metadata = MetaData()

# Create SQLite-compatible schema (JSON instead of JSONB)
def create_sqlite_tables(metadata: MetaData):
    """Create Huntflow tables with SQLite-compatible types"""
    
    applicants = Table('applicants', metadata,
        Column('id', Integer, primary_key=True),
        Column('first_name', String),
        Column('last_name', String),
        Column('middle_name', String),
        Column('birthday', Date),
        Column('phone', String),
        Column('skype', String),
        Column('email', String),
        Column('money', Numeric(12, 2)),
        Column('position', String),
        Column('company', String),
        Column('photo', Integer),
        Column('photo_url', String),
        Column('created', DateTime),
        Column('account', Integer),
        Column('tags', sa.JSON),
        Column('external', sa.JSON),
        Column('agreement', sa.JSON),
        Column('doubles', sa.JSON),
        Column('social', sa.JSON),
        Column('source_id', Integer, ForeignKey('sources.id')),
        Column('recruiter_id', Integer, ForeignKey('recruiters.id')),
        Column('recruiter_name', String),
        Column('source_name', String),
    )
    
    vacancies = Table('vacancies', metadata,
        Column('id', Integer, primary_key=True),
        Column('position', String, nullable=False),
        Column('company', String),
        Column('account_division', Integer, ForeignKey('divisions.id')),
        Column('account_region', Integer, ForeignKey('regions.id')),
        Column('money', Numeric(12, 2)),
        Column('priority', Integer),
        Column('hidden', Boolean, default=False),
        Column('state', String),
        Column('created', DateTime, nullable=False),
        Column('multiple', Boolean),
        Column('parent', Integer),
        Column('account_vacancy_status_group', Integer),
        Column('additional_fields_list', sa.JSON),
        Column('updated', DateTime),
        Column('body', String),
        Column('requirements', String),
        Column('conditions', String),
        Column('files', sa.JSON),
        Column('coworkers', sa.JSON),
        Column('source', Integer),
        Column('blocks', sa.JSON),
        Column('vacancy_request', Integer)
    )
    
    status_mapping = Table('status_mapping', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String, nullable=False),
        Column('type', String, nullable=False),
        Column('removed', Boolean),
        Column('order', Integer, nullable=False),
        Column('stay_duration', Integer)
    )
    
    recruiters = Table('recruiters', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String),
        Column('email', String),
        Column('member', Integer),
        Column('type', String),
        Column('head', Integer),
        Column('meta', sa.JSON),
        Column('permissions', sa.JSON),
        Column('full_name', String)
    )
    
    sources = Table('sources', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String, nullable=False),
        Column('type', String, nullable=False),
        Column('foreign', String)
    )
    
    divisions = Table('divisions', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String, nullable=False),
        Column('order', Integer, nullable=False),
        Column('active', Boolean, nullable=False),
        Column('deep', Integer, nullable=False),
        Column('parent', Integer),
        Column('foreign', String),
        Column('meta', sa.JSON)
    )
    
    applicant_tags = Table('applicant_tags', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String, nullable=False),
        Column('color', String(7))
    )
    
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
        Column('status', Integer, ForeignKey('status_mapping.id'), nullable=False),
        Column('updated', DateTime),
        Column('changed', DateTime),
        Column('vacancy', Integer, ForeignKey('vacancies.id'), nullable=False)
    )
    
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
    
    status_groups = Table('status_groups', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String),
        Column('order', Integer),
        Column('statuses', sa.JSON)
    )
    
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
        'status_groups': status_groups,
    }

# Create tables
tables = create_sqlite_tables(metadata)
metadata.create_all(engine)

# Helper data
RECRUITERS = [
    {"id": 101, "name": "Anna Petrova", "email": "anna@company.com", "type": "owner"},
    {"id": 102, "name": "Ivan Sidorov", "email": "ivan@company.com", "type": "manager"},
    {"id": 103, "name": "Maria Kozlova", "email": "maria@company.com", "type": "manager"},
]

HIRING_MANAGERS = [
    {"id": 201, "name": "Alexey Volkov", "email": "alexey@company.com", "type": "manager"},
    {"id": 202, "name": "Elena Novak", "email": "elena@company.com", "type": "manager"},
]

DIVISIONS = [
    {"id": 1, "name": "Engineering", "order": 1, "active": True, "deep": 0},
    {"id": 2, "name": "Sales", "order": 2, "active": True, "deep": 0},
    {"id": 3, "name": "Marketing", "order": 3, "active": True, "deep": 0},
    {"id": 4, "name": "HR", "order": 4, "active": True, "deep": 0},
]

REGIONS = [
    {"id": 1, "name": "Moscow", "order": 1},
    {"id": 2, "name": "St. Petersburg", "order": 2},
    {"id": 3, "name": "Remote", "order": 3},
]

SOURCES = [
    {"id": 1, "name": "HeadHunter", "type": "job_site"},
    {"id": 2, "name": "LinkedIn", "type": "social_network"},
    {"id": 3, "name": "Referral", "type": "referral"},
    {"id": 4, "name": "Agency Partner", "type": "agency"},
    {"id": 5, "name": "Company Website", "type": "website"},
]

STATUSES = [
    {"id": 1, "name": "New", "type": "New", "order": 1, "removed": False, "stay_duration": None},
    {"id": 2, "name": "Resume Review", "type": "In Progress", "order": 2, "removed": False, "stay_duration": 2},
    {"id": 3, "name": "Phone Screen", "type": "In Progress", "order": 3, "removed": False, "stay_duration": 3},
    {"id": 4, "name": "Technical Interview", "type": "In Progress", "order": 4, "removed": False, "stay_duration": 5},
    {"id": 5, "name": "Final Interview", "type": "In Progress", "order": 5, "removed": False, "stay_duration": 7},
    {"id": 6, "name": "Offer Preparation", "type": "Offer", "order": 6, "removed": False, "stay_duration": 2},
    {"id": 7, "name": "Offer Sent", "type": "Offer", "order": 7, "removed": False, "stay_duration": 5},
    {"id": 8, "name": "Hired", "type": "Hired", "order": 8, "removed": False, "stay_duration": None},
    {"id": 9, "name": "Rejected - Skills Mismatch", "type": "Rejected", "order": 9, "removed": False, "stay_duration": None},
    {"id": 10, "name": "Rejected - Salary Expectations", "type": "Rejected", "order": 10, "removed": False, "stay_duration": None},
]

REJECTION_REASONS = [
    {"id": 1, "name": "Skills mismatch", "order": 1},
    {"id": 2, "name": "Salary expectations too high", "order": 2},
    {"id": 3, "name": "No show for interview", "order": 3},
    {"id": 4, "name": "Cultural fit", "order": 4},
    {"id": 5, "name": "Accepted another offer", "order": 5},
]

TAGS = [
    {"id": 1, "name": "Senior", "color": "#FF5733"},
    {"id": 2, "name": "Remote", "color": "#33FF57"},
    {"id": 3, "name": "Urgent", "color": "#3357FF"},
    {"id": 4, "name": "Referral", "color": "#FF33F5"},
]

# Seed functions
def create_vacancy(v_id):
    """Create a realistic vacancy"""
    state = random.choice(["OPEN", "OPEN", "OPEN", "CLOSED", "HOLD"])
    created = fake.date_time_between(start_date="-90d", end_date="-30d")
    
    recruiter = random.choice(RECRUITERS)
    manager = random.choice(HIRING_MANAGERS)
    division = random.choice(DIVISIONS)
    region = random.choice(REGIONS)
    
    position = fake.job()
    salary_min = random.randint(50000, 150000)
    salary_max = salary_min + random.randint(20000, 50000)
    
    return {
        "id": v_id,
        "position": position,
        "company": fake.company(),
        "account_division": division["id"],
        "account_region": region["id"],
        "money": (salary_min + salary_max) / 2,
        "priority": random.randint(0, 1),
        "hidden": False,
        "state": state,
        "created": created,
        "updated": created + timedelta(days=random.randint(1, 30)),
        "multiple": random.choice([True, False, False]),
        "body": f"<p>We are looking for a {position} to join our {division['name']} team.</p>",
        "requirements": f"<ul><li>5+ years experience</li><li>Strong technical skills</li></ul>",
        "conditions": f"<ul><li>Competitive salary: ${salary_min}-${salary_max}</li><li>Remote work available</li></ul>",
        "coworkers": json.dumps([
            {"id": recruiter["id"], "type": "owner"},
            {"id": manager["id"], "type": "manager"}
        ])
    }

def create_applicant(a_id):
    """Create a realistic applicant"""
    source = random.choice(SOURCES)
    created = fake.date_time_between(start_date="-30d", end_date="now")
    
    return {
        "id": a_id,
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "middle_name": fake.first_name() if random.random() > 0.5 else None,
        "birthday": fake.date_of_birth(minimum_age=22, maximum_age=55),
        "phone": fake.phone_number(),
        "email": fake.email(),
        "position": fake.job(),
        "company": fake.company(),
        "created": created,
        "source_id": source["id"],
        "source_name": source["name"],
        "money": random.randint(60000, 200000),
        "tags": json.dumps(random.sample([1, 2, 3, 4], k=random.randint(0, 2))),
        "external": json.dumps({
            "resume_text": fake.text(max_nb_chars=500),
            "skills": [fake.word() for _ in range(random.randint(3, 8))]
        }),
        "agreement": json.dumps({"state": "accepted", "accepted_at": created.isoformat()}),
        "social": json.dumps({
            "linkedin": f"https://linkedin.com/in/{fake.user_name()}" if random.random() > 0.5 else None
        })
    }

def create_applicant_link(link_id, applicant_id, vacancy_id, status_id, created):
    """Create applicant-vacancy link with status"""
    return {
        "id": link_id,
        "applicant_id": applicant_id,
        "vacancy": vacancy_id,
        "status": status_id,
        "updated": created + timedelta(days=random.randint(0, 5)),
        "changed": created + timedelta(days=random.randint(0, 3))
    }

def create_offer(offer_id, applicant_id, vacancy_id, created):
    """Create job offer"""
    statuses = ["pending", "accepted", "rejected", "sent"]
    return {
        "id": offer_id,
        "applicant_id": applicant_id,
        "vacancy_id": vacancy_id,
        "status": random.choice(statuses),
        "created": created,
        "updated": created + timedelta(days=random.randint(1, 3))
    }

# Main seeding logic
with engine.connect() as conn:
    # Insert reference data
    conn.execute(tables['sources'].insert(), SOURCES)
    conn.execute(tables['divisions'].insert(), DIVISIONS)
    conn.execute(tables['regions'].insert(), REGIONS)
    conn.execute(tables['status_mapping'].insert(), STATUSES)
    conn.execute(tables['rejection_reasons'].insert(), REJECTION_REASONS)
    conn.execute(tables['applicant_tags'].insert(), TAGS)
    
    # Insert recruiters
    recruiter_data = []
    for r in RECRUITERS + HIRING_MANAGERS:
        recruiter_data.append({
            "id": r["id"],
            "name": r["name"],
            "email": r["email"],
            "type": r["type"],
            "member": r["id"],
            "permissions": json.dumps({"can_edit": True, "can_view": True})
        })
    conn.execute(tables['recruiters'].insert(), recruiter_data)
    
    # Create vacancies
    vacancies = []
    for i in range(1, 31):  # 30 vacancies
        vacancy = create_vacancy(i)
        vacancies.append(vacancy)
    conn.execute(tables['vacancies'].insert(), vacancies)
    
    # Create applicants
    applicants = []
    applicant_links = []
    offers = []
    
    applicant_id = 1
    link_id = 1
    offer_id = 1
    
    for vacancy in vacancies:
        # Each vacancy gets 5-20 applicants
        num_applicants = random.randint(5, 20)
        
        for _ in range(num_applicants):
            # Create applicant
            applicant = create_applicant(applicant_id)
            applicants.append(applicant)
            
            # Assign to random status
            status = random.choice(STATUSES)
            link = create_applicant_link(link_id, applicant_id, vacancy["id"], 
                                        status["id"], applicant["created"])
            applicant_links.append(link)
            
            # Some applicants get offers
            if status["type"] in ["Offer", "Hired"] and random.random() > 0.3:
                offer = create_offer(offer_id, applicant_id, vacancy["id"], 
                                   applicant["created"] + timedelta(days=10))
                offers.append(offer)
                offer_id += 1
            
            applicant_id += 1
            link_id += 1
    
    conn.execute(tables['applicants'].insert(), applicants)
    conn.execute(tables['applicant_links'].insert(), applicant_links)
    if offers:
        conn.execute(tables['offers'].insert(), offers)
    
    # Create status groups
    status_groups = [
        {
            "id": 1,
            "name": "Active Pipeline",
            "order": 1,
            "statuses": json.dumps([1, 2, 3, 4, 5])
        },
        {
            "id": 2,
            "name": "Offer Stage",
            "order": 2,
            "statuses": json.dumps([6, 7])
        },
        {
            "id": 3,
            "name": "Final",
            "order": 3,
            "statuses": json.dumps([8, 9, 10])
        }
    ]
    conn.execute(tables['status_groups'].insert(), status_groups)
    
    conn.commit()

# Print summary
print("✨ Demo database seeded successfully!")
print(f"   - {len(vacancies)} vacancies")
print(f"   - {len(applicants)} applicants")
print(f"   - {len(offers)} offers")
print(f"   - {len(SOURCES)} sources")
print(f"   - {len(STATUSES)} recruitment stages")
print(f"   - {len(RECRUITERS + HIRING_MANAGERS)} users")

# Quick test queries
with engine.connect() as conn:
    result = conn.execute(sa.text("SELECT COUNT(*) FROM vacancies WHERE state = 'OPEN'"))
    open_count = result.scalar()
    print(f"\n📊 Quick stats:")
    print(f"   - {open_count} open vacancies")
    
    result = conn.execute(sa.text("SELECT COUNT(*) FROM applicants"))
    total_applicants = result.scalar()
    print(f"   - {total_applicants} total applicants")
    
    result = conn.execute(sa.text("SELECT COUNT(*) FROM offers WHERE status = 'accepted'"))
    accepted_offers = result.scalar()
    print(f"   - {accepted_offers} accepted offers")

print(f"\n💾 Database saved to: demo.db")