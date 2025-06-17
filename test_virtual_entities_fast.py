#!/usr/bin/env python3
"""
Fast integration test for all virtual entities
Tests basic functionality without excessive API calls
"""
import asyncio
import json
from app import HuntflowClient
from virtual_engine import HuntflowVirtualEngine
from sqlalchemy_executor import SQLAlchemyHuntflowExecutor

async def test_virtual_entities_fast():
    """Test all virtual entities with minimal API calls"""
    
    print("🧪 Fast Testing All Virtual Entities")
    print("=" * 50)
    
    # Initialize components
    hf_client = HuntflowClient()
    
    # Validate client has required credentials
    if not hf_client.token or not hf_client.acc_id:
        print("❌ Missing HF_TOKEN or ACC_ID environment variables")
        return
    
    engine = HuntflowVirtualEngine(hf_client)
    executor = SQLAlchemyHuntflowExecutor(engine)
    
    # Define tests for each virtual entity
    test_cases = [
        {
            "entity": "active_candidates",
            "tests": [
                {"operation": "count", "expected_type": int},
            ]
        },
        {
            "entity": "open_vacancies",
            "tests": [
                {"operation": "count", "expected_type": int},
            ]
        },
        {
            "entity": "closed_vacancies", 
            "tests": [
                {"operation": "count", "expected_type": int},
            ]
        },
        {
            "entity": "recruiters",
            "tests": [
                {"operation": "count", "expected_type": int},
                {"operation": "field", "expected_type": list},
            ]
        },
        {
            "entity": "active_statuses",
            "tests": [
                {"operation": "count", "expected_type": int},
                {"operation": "field", "expected_type": list},
            ]
        },
        {
            "entity": "applicant_links",
            "tests": [
                {"operation": "count", "expected_type": int},
            ]
        }
    ]
    
    results = {}
    
    for test_case in test_cases:
        entity = test_case["entity"]
        print(f"\n🔍 Testing entity: {entity}")
        print("-" * 30)
        
        entity_results = {"tests": [], "status": "✅ PASS"}
        
        for test in test_case["tests"]:
            operation = test["operation"]
            expected_type = test["expected_type"]
            
            try:
                print(f"  📊 Testing {operation} operation...")
                query = {
                    "operation": operation,
                    "entity": entity
                }
                result = await executor.execute_expression(query)
                
                # Type check
                if isinstance(result, expected_type):
                    print(f"     ✅ Result type correct: {type(result).__name__}")
                    if expected_type == int:
                        print(f"     Value: {result}")
                    elif expected_type == list:
                        print(f"     Count: {len(result)} items")
                        if result and hasattr(result[0], '__dict__'):
                            print(f"     Fields: {list(result[0].__dict__.keys())}")
                else:
                    print(f"     ❌ Wrong type: expected {expected_type.__name__}, got {type(result).__name__}")
                    entity_results["status"] = "❌ FAIL"
                
                entity_results["tests"].append({
                    "operation": operation,
                    "success": True,
                    "result": result if expected_type == int else f"{len(result)} items"
                })
                
            except Exception as e:
                print(f"     ❌ ERROR: {e}")
                entity_results["status"] = "❌ FAIL"
                entity_results["tests"].append({
                    "operation": operation,
                    "success": False,
                    "error": str(e)
                })
        
        results[entity] = entity_results
    
    # Test one grouped query example
    print(f"\n🔍 Testing grouped query example")
    print("-" * 30)
    try:
        print("  📈 Testing active_candidates grouped by status_id...")
        grouped_query = {
            "operation": "count",
            "entity": "active_candidates",
            "group_by": {"field": "status_id"}
        }
        grouped_result = await executor.execute_grouped_query(grouped_query)
        
        if isinstance(grouped_result, dict):
            labels = grouped_result.get("labels", [])
            values = grouped_result.get("values", []) 
            print(f"     ✅ Success: {len(labels)} statuses")
            if labels and values:
                # Show top 3
                for i in range(min(3, len(labels), len(values))):
                    print(f"        {labels[i]}: {values[i]}")
        else:
            print(f"     ❌ Unexpected result type: {type(grouped_result)}")
            
    except Exception as e:
        print(f"     ❌ ERROR: {e}")
    
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
    
    print(f"\n📊 Test Results: {passed} passed, {failed} failed")
    
    # Show counts for all entities
    print(f"\n📈 ENTITY COUNTS")
    print("=" * 50)
    for entity, result in results.items():
        for test in result["tests"]:
            if test["operation"] == "count" and test["success"]:
                print(f"{entity:20} {test['result']:>10}")

if __name__ == "__main__":
    asyncio.run(test_virtual_entities_fast())