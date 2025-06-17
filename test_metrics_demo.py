"""
Test metrics.py with the demo SQLite database
"""

import asyncio
from sqlalchemy import MetaData, Table, Column, Integer, String, DateTime, Boolean, Date, Numeric, ForeignKey
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine
from metrics import HuntflowViews


def create_sqlite_tables(metadata):
    """Create minimal table definitions for testing"""
    return {
        'applicants': Table('applicants', metadata, autoload=True),
        'vacancies': Table('vacancies', metadata, autoload=True),
        'status_mapping': Table('status_mapping', metadata, autoload=True),
        'recruiters': Table('recruiters', metadata, autoload=True),
        'sources': Table('sources', metadata, autoload=True),
        'divisions': Table('divisions', metadata, autoload=True),
        'applicant_tags': Table('applicant_tags', metadata, autoload=True),
        'offers': Table('offers', metadata, autoload=True),
        'applicant_links': Table('applicant_links', metadata, autoload=True),
        'regions': Table('regions', metadata, autoload=True),
        'rejection_reasons': Table('rejection_reasons', metadata, autoload=True),
        'status_groups': Table('status_groups', metadata, autoload=True),
    }


async def test_metrics_with_demo():
    """Test all metrics functions with demo data"""
    # Create async engine for the demo database
    engine = create_async_engine("sqlite+aiosqlite:///demo.db", echo=False)
    metadata = MetaData()
    
    # Reflect tables from existing database
    async with engine.begin() as conn:
        await conn.run_sync(metadata.reflect)
    
    # Get table references
    tables = {table.name: table for table in metadata.tables.values()}
    
    # Create views instance
    views = HuntflowViews(engine, tables)
    
    print("🧪 Testing metrics.py with demo database...\n")
    
    # Test 1: Vacancies by state
    print("1. Testing vacancies_by_state:")
    for state in ['OPEN', 'CLOSED', 'HOLD']:
        vacancies = await views.vacancies_by_state(state)
        print(f"   - {state}: {len(vacancies)} vacancies")
        if vacancies:
            print(f"     Example: {vacancies[0]['position']} at {vacancies[0]['company']}")
    
    # Test 2: Vacancies by division
    print("\n2. Testing vacancies_by_division:")
    for div_id in range(1, 5):
        vacancies = await views.vacancies_by_division(div_id)
        print(f"   - Division {div_id}: {len(vacancies)} vacancies")
    
    # Test 3: Applicants by source
    print("\n3. Testing applicants_by_source:")
    for source_id in range(1, 6):
        applicants = await views.applicants_by_source(source_id)
        print(f"   - Source {source_id}: {len(applicants)} applicants")
    
    # Test 4: Vacancy funnel
    print("\n4. Testing vacancy_funnel for first 3 open vacancies:")
    open_vacancies = await views.vacancies_by_state('OPEN')
    for vacancy in open_vacancies[:3]:
        funnel = await views.vacancy_funnel(vacancy['id'])
        print(f"   - Vacancy '{vacancy['position']}':")
        for status_id, count in sorted(funnel.items()):
            print(f"     Stage {status_id}: {count} candidates")
    
    # Test 5: Recruiter performance
    print("\n5. Testing recruiter_performance:")
    performance = await views.recruiter_performance()
    print(f"   Found {len(performance)} recruiters with applicants")
    for recruiter in performance[:3]:
        print(f"   - {recruiter['name']}: {recruiter['total_applicants']} applicants")
    
    # Test 6: Source effectiveness
    print("\n6. Testing source_effectiveness:")
    sources = await views.source_effectiveness()
    print(f"   Found {len(sources)} sources with applicants")
    for source in sources:
        print(f"   - {source['name']} ({source['type']}): {source['total_applicants']} applicants")
    
    # Test 7: Offers by status
    print("\n7. Testing offers_by_status:")
    for status in ['pending', 'accepted', 'rejected', 'sent']:
        offers = await views.offers_by_status(status)
        print(f"   - {status}: {len(offers)} offers")
    
    # Test 8: Error handling
    print("\n8. Testing error handling:")
    try:
        await views.vacancies_by_state('INVALID')
    except ValueError:
        print("   ✅ ValueError raised for invalid state")
    
    try:
        await views.applicants_by_source(-1)
    except ValueError:
        print("   ✅ ValueError raised for negative source ID")
    
    try:
        await views.rejections_by_reason(1)
    except NotImplementedError:
        print("   ✅ NotImplementedError raised for rejections")
    
    print("\n✅ All tests completed successfully!")
    
    # Cleanup
    await engine.dispose()


if __name__ == "__main__":
    # Install aiosqlite if needed
    import subprocess
    import sys
    try:
        import aiosqlite
    except ImportError:
        print("Installing aiosqlite...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "aiosqlite"])
    
    asyncio.run(test_metrics_with_demo())