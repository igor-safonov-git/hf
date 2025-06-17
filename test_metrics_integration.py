"""
Integration tests for metrics.py with real database data
Tests all view methods and error handling
"""

import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import create_async_engine
from metrics import HuntflowViews
from schema import create_huntflow_tables
from sqlalchemy_executor import SQLAlchemyHuntflowExecutor

load_dotenv()


async def test_all_metrics():
    """Run integration tests for all metrics functions"""
    # Setup
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not found in environment")
        return
    
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(db_url)
    metadata = MetaData()
    tables = create_huntflow_tables(metadata)
    
    views = HuntflowViews(engine, tables)
    executor = SQLAlchemyHuntflowExecutor(engine, metadata)
    
    print("🔧 Setting up test environment...")
    
    # First, let's check what data we have
    print("\n📊 Checking available data...")
    
    try:
        # Get some basic counts
        vacancies_count = await executor.execute(
            "vacancies", 
            {"operation": "count"}
        )
        print(f"Total vacancies in DB: {vacancies_count}")
        
        applicants_count = await executor.execute(
            "applicants",
            {"operation": "count"}
        )
        print(f"Total applicants in DB: {applicants_count}")
        
        # Get sample data for testing
        sample_vacancies = await executor.execute(
            "vacancies",
            {"operation": "list", "limit": 5}
        )
        
        sample_applicants = await executor.execute(
            "applicants", 
            {"operation": "list", "limit": 5}
        )
        
        # Test Vacancy Views
        print("\n🏢 Testing Vacancy Views...")
        
        # Test vacancies_by_state
        print("\n1. Testing vacancies_by_state...")
        for state in ['OPEN', 'CLOSED', 'HOLD']:
            try:
                result = await views.vacancies_by_state(state)
                print(f"   - {state} vacancies: {len(result)}")
                if result and len(result) > 0:
                    print(f"     Sample: {result[0].get('position', 'N/A')}")
            except Exception as e:
                print(f"   ❌ Error testing state {state}: {e}")
        
        # Test invalid state
        try:
            await views.vacancies_by_state('INVALID')
            print("   ❌ Should have raised ValueError for invalid state")
        except ValueError as e:
            print(f"   ✅ Correctly raised ValueError: {e}")
        
        # Test vacancies_by_division
        print("\n2. Testing vacancies_by_division...")
        if sample_vacancies:
            for vacancy in sample_vacancies[:2]:
                division_id = vacancy.get('account_division')
                if division_id:
                    try:
                        result = await views.vacancies_by_division(division_id)
                        print(f"   - Division {division_id}: {len(result)} vacancies")
                    except Exception as e:
                        print(f"   ❌ Error testing division {division_id}: {e}")
        
        # Test vacancies_by_date_range
        print("\n3. Testing vacancies_by_date_range...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        try:
            result = await views.vacancies_by_date_range(start_date, end_date)
            print(f"   - Last 30 days: {len(result)} vacancies")
        except Exception as e:
            print(f"   ❌ Error testing date range: {e}")
        
        # Test invalid date range
        try:
            await views.vacancies_by_date_range(end_date, start_date)
            print("   ❌ Should have raised ValueError for invalid date range")
        except ValueError as e:
            print(f"   ✅ Correctly raised ValueError: {e}")
        
        # Test vacancies_by_recruiter
        print("\n4. Testing vacancies_by_recruiter...")
        # Get a sample recruiter ID
        recruiters = await executor.execute(
            "recruiters",
            {"operation": "list", "limit": 5}
        )
        if recruiters:
            for recruiter in recruiters[:2]:
                try:
                    result = await views.vacancies_by_recruiter(recruiter['id'])
                    print(f"   - Recruiter {recruiter['name']}: {len(result)} vacancies")
                except Exception as e:
                    print(f"   ❌ Error testing recruiter {recruiter['id']}: {e}")
        
        # Test Applicant Views
        print("\n👥 Testing Applicant Views...")
        
        # Test applicants_by_source
        print("\n5. Testing applicants_by_source...")
        sources = await executor.execute(
            "sources",
            {"operation": "list", "limit": 5}
        )
        if sources:
            for source in sources[:2]:
                try:
                    result = await views.applicants_by_source(source['id'])
                    print(f"   - Source {source['name']}: {len(result)} applicants")
                except Exception as e:
                    print(f"   ❌ Error testing source {source['id']}: {e}")
        
        # Test applicants_by_vacancy
        print("\n6. Testing applicants_by_vacancy...")
        if sample_vacancies:
            for vacancy in sample_vacancies[:2]:
                try:
                    result = await views.applicants_by_vacancy(vacancy['id'])
                    print(f"   - Vacancy '{vacancy.get('position', 'N/A')}': {len(result)} applicants")
                except Exception as e:
                    print(f"   ❌ Error testing vacancy {vacancy['id']}: {e}")
        
        # Test applicants_by_recruiter
        print("\n7. Testing applicants_by_recruiter...")
        if recruiters:
            for recruiter in recruiters[:2]:
                try:
                    result = await views.applicants_by_recruiter(recruiter['id'])
                    print(f"   - Recruiter {recruiter['name']}: {len(result)} applicants")
                except Exception as e:
                    print(f"   ❌ Error testing recruiter {recruiter['id']}: {e}")
        
        # Test applicants_by_status
        print("\n8. Testing applicants_by_status...")
        statuses = await executor.execute(
            "status_mapping",
            {"operation": "list", "limit": 5}
        )
        if statuses:
            for status in statuses[:2]:
                try:
                    result = await views.applicants_by_status(status['id'])
                    print(f"   - Status '{status['name']}': {len(result)} applicants")
                except Exception as e:
                    print(f"   ❌ Error testing status {status['id']}: {e}")
        
        # Test Offer Views
        print("\n💼 Testing Offer Views...")
        
        # Test offers_by_status
        print("\n9. Testing offers_by_status...")
        offer_statuses = ['pending', 'accepted', 'rejected', 'sent']
        for status in offer_statuses:
            try:
                result = await views.offers_by_status(status)
                print(f"   - Status '{status}': {len(result)} offers")
            except Exception as e:
                print(f"   ❌ Error testing offer status {status}: {e}")
        
        # Test offers_by_vacancy
        print("\n10. Testing offers_by_vacancy...")
        if sample_vacancies:
            for vacancy in sample_vacancies[:2]:
                try:
                    result = await views.offers_by_vacancy(vacancy['id'])
                    print(f"   - Vacancy '{vacancy.get('position', 'N/A')}': {len(result)} offers")
                except Exception as e:
                    print(f"   ❌ Error testing vacancy offers {vacancy['id']}: {e}")
        
        # Test offers_by_date_range
        print("\n11. Testing offers_by_date_range...")
        try:
            result = await views.offers_by_date_range(start_date, end_date)
            print(f"   - Last 30 days: {len(result)} offers")
        except Exception as e:
            print(f"   ❌ Error testing offer date range: {e}")
        
        # Test Source Analytics
        print("\n📈 Testing Source Analytics...")
        
        # Test sources_by_type
        print("\n12. Testing sources_by_type...")
        source_types = ['website', 'referral', 'job_board', 'social']
        for source_type in source_types:
            try:
                result = await views.sources_by_type(source_type)
                print(f"   - Type '{source_type}': {len(result)} sources")
            except Exception as e:
                print(f"   ❌ Error testing source type {source_type}: {e}")
        
        # Test Rejection Analytics
        print("\n13. Testing rejection methods (NotImplementedError expected)...")
        try:
            await views.rejections_by_reason(1)
            print("   ❌ Should have raised NotImplementedError")
        except NotImplementedError as e:
            print(f"   ✅ Correctly raised NotImplementedError: {e}")
        
        try:
            await views.rejections_by_stage(1)
            print("   ❌ Should have raised NotImplementedError")
        except NotImplementedError as e:
            print(f"   ✅ Correctly raised NotImplementedError: {e}")
        
        # Test Aggregated Views
        print("\n📊 Testing Aggregated Views...")
        
        # Test vacancy_funnel
        print("\n14. Testing vacancy_funnel...")
        if sample_vacancies:
            for vacancy in sample_vacancies[:2]:
                try:
                    result = await views.vacancy_funnel(vacancy['id'])
                    print(f"   - Vacancy '{vacancy.get('position', 'N/A')}' funnel:")
                    for status_id, count in result.items():
                        print(f"     Stage {status_id}: {count} candidates")
                except Exception as e:
                    print(f"   ❌ Error testing vacancy funnel {vacancy['id']}: {e}")
        
        # Test recruiter_performance
        print("\n15. Testing recruiter_performance...")
        try:
            result = await views.recruiter_performance()
            print(f"   - Total recruiters with applicants: {len(result)}")
            if result:
                top_recruiter = result[0]
                print(f"   - Top recruiter: {top_recruiter.get('name', 'N/A')} ({top_recruiter.get('total_applicants', 0)} applicants)")
        except Exception as e:
            print(f"   ❌ Error testing recruiter performance: {e}")
        
        # Test with date filter
        try:
            last_week = datetime.now() - timedelta(days=7)
            result = await views.recruiter_performance(start_date=last_week)
            print(f"   - Recruiters active in last 7 days: {len(result)}")
        except Exception as e:
            print(f"   ❌ Error testing recruiter performance with date: {e}")
        
        # Test source_effectiveness
        print("\n16. Testing source_effectiveness...")
        try:
            result = await views.source_effectiveness()
            print(f"   - Total sources with applicants: {len(result)}")
            if result:
                top_source = result[0]
                print(f"   - Top source: {top_source.get('name', 'N/A')} ({top_source.get('total_applicants', 0)} applicants)")
        except Exception as e:
            print(f"   ❌ Error testing source effectiveness: {e}")
        
        # Test Error Handling
        print("\n🚨 Testing Error Handling...")
        
        # Test invalid IDs
        print("\n17. Testing invalid ID handling...")
        invalid_tests = [
            ("vacancies_by_division", -1),
            ("vacancies_by_recruiter", 0),
            ("applicants_by_source", -5),
            ("applicants_by_vacancy", 0),
            ("applicants_by_recruiter", -1),
            ("applicants_by_status", 0),
            ("offers_by_vacancy", -1),
            ("vacancy_funnel", 0)
        ]
        
        for method_name, invalid_id in invalid_tests:
            try:
                method = getattr(views, method_name)
                await method(invalid_id)
                print(f"   ❌ {method_name} should have raised ValueError for ID {invalid_id}")
            except ValueError as e:
                print(f"   ✅ {method_name} correctly raised ValueError: {e}")
            except Exception as e:
                print(f"   ❌ {method_name} raised unexpected error: {e}")
        
        # Test empty strings
        print("\n18. Testing empty string handling...")
        string_tests = [
            ("offers_by_status", ""),
            ("sources_by_type", "")
        ]
        
        for method_name, empty_string in string_tests:
            try:
                method = getattr(views, method_name)
                await method(empty_string)
                print(f"   ❌ {method_name} should have raised ValueError for empty string")
            except ValueError as e:
                print(f"   ✅ {method_name} correctly raised ValueError: {e}")
            except Exception as e:
                print(f"   ❌ {method_name} raised unexpected error: {e}")
        
        print("\n✅ Integration tests completed!")
        
    except Exception as e:
        print(f"\n❌ Fatal error during testing: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_all_metrics())