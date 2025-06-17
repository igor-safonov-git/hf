#!/usr/bin/env python3
"""
Integration test for all virtual entities
Tests each virtual entity to ensure proper functionality
"""
import asyncio
import json
from app import HuntflowClient
from virtual_engine import HuntflowVirtualEngine
from sqlalchemy_executor import SQLAlchemyHuntflowExecutor

async def test_virtual_entities():
    """Test all virtual entities with real data"""
    
    print("🧪 Testing All Virtual Entities")
    print("=" * 50)
    
    # Initialize components
    hf_client = HuntflowClient()
    
    # Validate client has required credentials
    if not hf_client.token or not hf_client.acc_id:
        print("❌ Missing HF_TOKEN or ACC_ID environment variables")
        return
    
    # Debug the client setup
    print(f"Client type: {type(hf_client)}")
    print(f"Client has _req: {hasattr(hf_client, '_req')}")
    
    engine = HuntflowVirtualEngine(hf_client)
    print(f"Engine hf_client type: {type(engine.hf_client)}")
    print(f"Engine hf_client has _req: {hasattr(engine.hf_client, '_req')}")
    
    executor = SQLAlchemyHuntflowExecutor(engine)
    
    # Define all virtual entities to test
    virtual_entities = [
        "active_candidates",
        "open_vacancies", 
        "closed_vacancies",
        "recruiters",
        "active_statuses",
        "applicant_links"  # Base entity used virtually
    ]
    
    results = {}
    
    for entity in virtual_entities:
        print(f"\n🔍 Testing entity: {entity}")
        print("-" * 30)
        
        try:
            # Test 1: Count operation
            print(f"  📊 Testing count operation...")
            count_query = {
                "operation": "count",
                "entity": entity
            }
            count_result = await executor.execute_expression(count_query)
            print(f"     Count result: {count_result}")
            
            # Test 2: Field operation (if supported)
            field_result = None
            if entity in ["recruiters", "active_statuses"]:
                print(f"  📋 Testing field operation...")
                field_query = {
                    "operation": "field", 
                    "entity": entity
                }
                field_result = await executor.execute_expression(field_query)
                if isinstance(field_result, list):
                    print(f"     Field result: {len(field_result)} items")
                else:
                    print(f"     Field result: {type(field_result)}")
            
            # Test 3: Grouped query (if applicable)
            grouped_result = None
            grouping_tests = {
                "active_candidates": "status_id",
                "open_vacancies": "state", 
                "closed_vacancies": "state",
                "applicant_links": "status_id",
                "recruiters": "hirings"
            }
            
            if entity in grouping_tests:
                group_field = grouping_tests[entity]
                print(f"  📈 Testing grouped query by {group_field}...")
                grouped_query = {
                    "operation": "count",
                    "entity": entity,
                    "group_by": {"field": group_field}
                }
                grouped_result = await executor.execute_grouped_query(grouped_query)
                if isinstance(grouped_result, dict):
                    labels_count = len(grouped_result.get("labels", []))
                    values_count = len(grouped_result.get("values", []))
                    print(f"     Grouped result: {labels_count} labels, {values_count} values")
                else:
                    print(f"     Grouped result: {type(grouped_result)}")
            
            # Store results
            results[entity] = {
                "count": count_result,
                "field": field_result,
                "grouped": grouped_result,
                "status": "✅ PASS"
            }
            
        except Exception as e:
            print(f"     ❌ ERROR: {e}")
            results[entity] = {
                "error": str(e),
                "status": "❌ FAIL"
            }
    
    # Summary report
    print(f"\n📋 SUMMARY REPORT")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for entity, result in results.items():
        status = result.get("status", "❌ FAIL")
        print(f"{entity:20} {status}")
        
        if "✅" in status:
            passed += 1
        else:
            failed += 1
            if "error" in result:
                print(f"                     Error: {result['error']}")
    
    print(f"\n📊 Test Results: {passed} passed, {failed} failed")
    
    # Detailed results for successful entities
    print(f"\n📈 DETAILED RESULTS")
    print("=" * 50)
    
    for entity, result in results.items():
        if result.get("status") == "✅ PASS":
            print(f"\n{entity}:")
            if result.get("count") is not None:
                print(f"  Count: {result['count']}")
            if result.get("field") is not None:
                field_info = result["field"]
                if isinstance(field_info, list):
                    print(f"  Field data: {len(field_info)} items")
                    if field_info and hasattr(field_info[0], '__dict__'):
                        print(f"  Sample fields: {list(field_info[0].__dict__.keys())}")
                else:
                    print(f"  Field data: {type(field_info)}")
            if result.get("grouped") is not None:
                grouped_info = result["grouped"]
                if isinstance(grouped_info, dict):
                    labels = grouped_info.get("labels", [])
                    values = grouped_info.get("values", [])
                    print(f"  Grouped: {len(labels)} categories")
                    if labels and values:
                        # Show top 3 categories
                        for i in range(min(3, len(labels), len(values))):
                            print(f"    {labels[i]}: {values[i]}")

if __name__ == "__main__":
    asyncio.run(test_virtual_entities())