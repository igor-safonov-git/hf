#!/usr/bin/env python3
"""
Test script to send 10 different HR analytics requests and validate responses
"""
import asyncio
import json
import httpx
from typing import Dict, Any, List
from datetime import datetime

# Test queries covering different aspects of HR analytics
TEST_QUERIES = [
    {
        "id": 1,
        "query": "Покажи общее количество кандидатов в системе",
        "description": "Simple count of all applicants",
        "expected_entity": "applicants",
        "expected_operation": "count"
    },
    {
        "id": 2, 
        "query": "Сколько у нас принятых кандидатов (оффер принят)?",
        "description": "Count hired applicants with status filter",
        "expected_entity": "applicants",
        "expected_operation": "count"
    },
    {
        "id": 3,
        "query": "Анализ производительности рекрутеров - кто больше всех нанял?",
        "description": "Recruiter performance analysis",
        "expected_entity": "applicants", 
        "expected_operation": "count"
    },
    {
        "id": 4,
        "query": "Покажи распределение кандидатов по статусам",
        "description": "Status distribution chart",
        "expected_entity": "applicants",
        "expected_operation": "count"
    },
    {
        "id": 5,
        "query": "Сколько у нас активных вакансий?",
        "description": "Count of active vacancies",
        "expected_entity": "vacancies",
        "expected_operation": "count"
    },
    {
        "id": 6,
        "query": "Эффективность источников кандидатов - откуда приходят лучшие?",
        "description": "Source effectiveness analysis",
        "expected_entity": "applicants",
        "expected_operation": "count"
    },
    {
        "id": 7,
        "query": "Покажи статистику по отделам (divisions)",
        "description": "Department/division statistics",
        "expected_entity": "divisions",
        "expected_operation": "count"
    },
    {
        "id": 8,
        "query": "Анализ вакансий по компаниям",
        "description": "Vacancy analysis by company",
        "expected_entity": "vacancies",
        "expected_operation": "count"
    },
    {
        "id": 9,
        "query": "Топ рекрутеров по количеству кандидатов",
        "description": "Top recruiters by candidate count",
        "expected_entity": "applicants",
        "expected_operation": "count"
    },
    {
        "id": 10,
        "query": "Общая статистика: кандидаты, вакансии, рекрутеры",
        "description": "Overall dashboard statistics",
        "expected_entity": "applicants",
        "expected_operation": "count"
    }
]

def validate_json_structure(response_text: str) -> Dict[str, Any]:
    """Validate that response contains valid JSON with required structure"""
    result = {
        "valid_json": False,
        "has_required_fields": False,
        "json_data": None,
        "errors": []
    }
    
    try:
        # Extract JSON from markdown if present
        json_content = response_text
        json_start = response_text.find('```json')
        if json_start != -1:
            json_end = response_text.find('```', json_start + 7)
            if json_end != -1:
                json_content = response_text[json_start + 7:json_end].strip()
        
        # Parse JSON
        json_data = json.loads(json_content)
        result["valid_json"] = True
        result["json_data"] = json_data
        
        # Check required fields
        required_fields = ["report_title", "main_metric", "secondary_metrics", "chart"]
        has_all_required = all(field in json_data for field in required_fields)
        result["has_required_fields"] = has_all_required
        
        if not has_all_required:
            missing = [field for field in required_fields if field not in json_data]
            result["errors"].append(f"Missing required fields: {missing}")
        
        # Check main_metric structure
        if "main_metric" in json_data:
            main_metric = json_data["main_metric"]
            if not isinstance(main_metric, dict):
                result["errors"].append("main_metric is not a dict")
            elif "value" not in main_metric:
                result["errors"].append("main_metric missing 'value' field")
            elif not isinstance(main_metric["value"], dict):
                result["errors"].append("main_metric.value is not a dict")
            else:
                value = main_metric["value"]
                required_value_fields = ["operation", "entity"]
                missing_value_fields = [f for f in required_value_fields if f not in value]
                if missing_value_fields:
                    result["errors"].append(f"main_metric.value missing: {missing_value_fields}")
        
        # Check chart structure
        if "chart" in json_data:
            chart = json_data["chart"]
            if not isinstance(chart, dict):
                result["errors"].append("chart is not a dict")
            else:
                required_chart_fields = ["x_axis", "y_axis", "chart_type"]
                missing_chart_fields = [f for f in required_chart_fields if f not in chart]
                if missing_chart_fields:
                    result["errors"].append(f"chart missing: {missing_chart_fields}")
        
        # Check for forbidden demo fields
        forbidden_fields = ["demo_value", "demo_data"]
        for field in forbidden_fields:
            if field in json.dumps(json_data):
                result["errors"].append(f"Contains forbidden field: {field}")
        
    except json.JSONDecodeError as e:
        result["errors"].append(f"JSON parsing error: {str(e)}")
    except Exception as e:
        result["errors"].append(f"Validation error: {str(e)}")
    
    return result

async def send_chat_request(query: str, model: str = "deepseek") -> str:
    """Send chat request to local FastAPI server"""
    url = "http://localhost:8001/chat"
    
    payload = {
        "message": query,
        "model": model,
        "use_real_data": False,  # Use schema validation only
        "temperature": 0.1
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "No response received")
            
    except httpx.ConnectError:
        return "ERROR: Cannot connect to FastAPI server at localhost:8001. Make sure the server is running."
    except httpx.TimeoutException:
        return "ERROR: Request timed out after 30 seconds"
    except Exception as e:
        return f"ERROR: {str(e)}"

async def test_all_queries():
    """Test all queries and validate responses"""
    print("🚀 Starting 10 agent request tests...")
    print("=" * 80)
    
    results = []
    
    for test_case in TEST_QUERIES:
        print(f"\n📋 Test {test_case['id']}: {test_case['description']}")
        print(f"Query: {test_case['query']}")
        print("-" * 40)
        
        # Send request
        response = await send_chat_request(test_case['query'])
        
        if response.startswith("ERROR:"):
            print(f"❌ Request failed: {response}")
            results.append({
                "test_id": test_case['id'],
                "status": "FAILED",
                "error": response,
                "validation": None
            })
            continue
        
        # Validate response
        validation = validate_json_structure(response)
        
        # Print results
        if validation["valid_json"] and validation["has_required_fields"] and not validation["errors"]:
            print("✅ PASSED: Valid JSON with correct structure")
            status = "PASSED"
        elif validation["valid_json"] and validation["has_required_fields"]:
            print(f"⚠️  PARTIAL: Valid structure but has issues: {'; '.join(validation['errors'])}")
            status = "PARTIAL"
        else:
            print(f"❌ FAILED: {'; '.join(validation['errors'])}")
            status = "FAILED"
        
        # Show key extracted info
        if validation["json_data"]:
            json_data = validation["json_data"]
            print(f"   Title: {json_data.get('report_title', 'N/A')}")
            if "main_metric" in json_data and "value" in json_data["main_metric"]:
                value = json_data["main_metric"]["value"]
                print(f"   Entity: {value.get('entity', 'N/A')}")
                print(f"   Operation: {value.get('operation', 'N/A')}")
            if "chart" in json_data:
                print(f"   Chart Type: {json_data['chart'].get('chart_type', 'N/A')}")
        
        results.append({
            "test_id": test_case['id'],
            "status": status,
            "query": test_case['query'],
            "validation": validation,
            "response_length": len(response)
        })
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for r in results if r["status"] == "PASSED")
    partial = sum(1 for r in results if r["status"] == "PARTIAL") 
    failed = sum(1 for r in results if r["status"] == "FAILED")
    
    print(f"✅ PASSED: {passed}/10 ({passed*10}%)")
    print(f"⚠️  PARTIAL: {partial}/10 ({partial*10}%)")
    print(f"❌ FAILED: {failed}/10 ({failed*10}%)")
    
    if failed > 0:
        print(f"\n❌ Failed tests:")
        for r in results:
            if r["status"] == "FAILED":
                print(f"   Test {r['test_id']}: {r.get('error', 'Validation failed')}")
    
    if partial > 0:
        print(f"\n⚠️  Partial tests (have issues):")
        for r in results:
            if r["status"] == "PARTIAL":
                errors = r["validation"]["errors"] if r["validation"] else ["Unknown issues"]
                print(f"   Test {r['test_id']}: {'; '.join(errors)}")
    
    # Overall result
    overall_success_rate = (passed + partial) / 10 * 100
    print(f"\n🎯 Overall Success Rate: {overall_success_rate}%")
    
    if overall_success_rate >= 80:
        print("🎉 EXCELLENT: Agent is working well!")
    elif overall_success_rate >= 60:
        print("👍 GOOD: Agent is mostly working, minor issues")
    else:
        print("⚠️  NEEDS WORK: Significant issues detected")
    
    return results

if __name__ == "__main__":
    print(f"🕐 Test started at: {datetime.now().isoformat()}")
    results = asyncio.run(test_all_queries())
    print(f"🕐 Test completed at: {datetime.now().isoformat()}")