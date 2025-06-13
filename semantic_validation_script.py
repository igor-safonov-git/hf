#!/usr/bin/env python3
"""
Semantic validation script to analyze response relevance to prompts
"""
import asyncio
import json
import httpx
from typing import Dict, Any, List, Tuple
from datetime import datetime

# Test cases with expected semantic elements
SEMANTIC_TEST_CASES = [
    {
        "id": 1,
        "query": "Покажи общее количество кандидатов в системе",
        "expected_elements": {
            "entity": "applicants",
            "operation": "count", 
            "filters": [],
            "semantic_focus": "total_count",
            "title_keywords": ["total", "applicants", "candidates", "общее", "количество", "кандидатов"]
        }
    },
    {
        "id": 2,
        "query": "Сколько у нас принятых кандидатов (оффер принят)?",
        "expected_elements": {
            "entity": "applicants",
            "operation": "count",
            "filters": ["status_name", "Оффер принят"],
            "semantic_focus": "hired_candidates",
            "title_keywords": ["hired", "accepted", "принятых", "оффер"]
        }
    },
    {
        "id": 3,
        "query": "Анализ производительности рекрутеров - кто больше всех нанял?",
        "expected_elements": {
            "entity": "applicants",
            "operation": "count",
            "filters": ["status_name", "Оффер принят"],
            "group_by": "recruiter_name",
            "semantic_focus": "recruiter_performance",
            "title_keywords": ["recruiter", "performance", "рекрутер", "производительность", "нанял"]
        }
    },
    {
        "id": 4,
        "query": "Распределение кандидатов по статусам",
        "expected_elements": {
            "entity": "applicants",
            "operation": "count",
            "group_by": "status_name",
            "semantic_focus": "status_distribution", 
            "title_keywords": ["status", "distribution", "статус", "распределение"]
        }
    },
    {
        "id": 5,
        "query": "Эффективность источников кандидатов - откуда приходят лучшие?",
        "expected_elements": {
            "entity": "applicants",
            "operation": "count",
            "group_by": "source_name",
            "semantic_focus": "source_effectiveness",
            "title_keywords": ["source", "effectiveness", "источник", "эффективность"]
        }
    },
    {
        "id": 6,
        "query": "Средняя зарплата по всем вакансиям",
        "expected_elements": {
            "entity": "vacancies",
            "operation": "avg",
            "field": "money",
            "semantic_focus": "average_salary",
            "title_keywords": ["average", "salary", "средняя", "зарплата"]
        }
    },
    {
        "id": 7,
        "query": "Топ рекрутеров по количеству кандидатов",
        "expected_elements": {
            "entity": "applicants",
            "operation": "count",
            "group_by": "recruiter_name",
            "semantic_focus": "top_recruiters",
            "title_keywords": ["top", "recruiters", "топ", "рекрутер"]
        }
    },
    {
        "id": 8,
        "query": "Активные вакансии",
        "expected_elements": {
            "entity": "vacancies", 
            "operation": "count",
            "filters": ["state", "active"],
            "semantic_focus": "active_vacancies",
            "title_keywords": ["active", "vacancies", "активные", "вакансии"]
        }
    }
]

def analyze_semantic_relevance(query: str, response_json: Dict[str, Any], expected: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze how well the response matches the semantic intent of the query"""
    
    analysis = {
        "query": query,
        "semantic_score": 0,
        "matches": [],
        "mismatches": [],
        "warnings": [],
        "detailed_analysis": {}
    }
    
    # Extract actual response elements
    main_metric = response_json.get("main_metric", {})
    main_value = main_metric.get("value", {})
    chart = response_json.get("chart", {})
    title = response_json.get("report_title", "")
    
    # 1. Entity Relevance (20 points)
    expected_entity = expected["entity"]
    actual_entity = main_value.get("entity")
    
    if actual_entity == expected_entity:
        analysis["semantic_score"] += 20
        analysis["matches"].append(f"✅ Correct entity: {actual_entity}")
    else:
        analysis["mismatches"].append(f"❌ Entity mismatch: expected {expected_entity}, got {actual_entity}")
    
    # 2. Operation Relevance (20 points)
    expected_operation = expected["operation"]
    actual_operation = main_value.get("operation")
    
    if actual_operation == expected_operation:
        analysis["semantic_score"] += 20
        analysis["matches"].append(f"✅ Correct operation: {actual_operation}")
    else:
        analysis["mismatches"].append(f"❌ Operation mismatch: expected {expected_operation}, got {actual_operation}")
    
    # 3. Filter Relevance (15 points)
    expected_filters = expected.get("filters", [])
    actual_filter = main_value.get("filter", {})
    
    if not expected_filters and not actual_filter:
        analysis["semantic_score"] += 15
        analysis["matches"].append("✅ No filters needed and none applied")
    elif expected_filters:
        if actual_filter:
            filter_field = actual_filter.get("field")
            filter_value = actual_filter.get("value")
            
            if len(expected_filters) >= 2:
                expected_field = expected_filters[0]
                expected_value = expected_filters[1]
                
                if filter_field == expected_field:
                    analysis["semantic_score"] += 10
                    analysis["matches"].append(f"✅ Correct filter field: {filter_field}")
                    
                    if expected_value in str(filter_value):
                        analysis["semantic_score"] += 5
                        analysis["matches"].append(f"✅ Correct filter value: {filter_value}")
                    else:
                        analysis["warnings"].append(f"⚠️ Filter value mismatch: expected {expected_value}, got {filter_value}")
                else:
                    analysis["mismatches"].append(f"❌ Filter field mismatch: expected {expected_field}, got {filter_field}")
        else:
            analysis["mismatches"].append(f"❌ Missing expected filter: {expected_filters}")
    
    # 4. Group By Relevance (15 points)
    expected_group_by = expected.get("group_by")
    actual_group_by = main_value.get("group_by", {}).get("field")
    
    if expected_group_by:
        if actual_group_by == expected_group_by:
            analysis["semantic_score"] += 15
            analysis["matches"].append(f"✅ Correct grouping: {actual_group_by}")
        else:
            analysis["mismatches"].append(f"❌ Grouping mismatch: expected {expected_group_by}, got {actual_group_by}")
    elif not actual_group_by:
        analysis["semantic_score"] += 15
        analysis["matches"].append("✅ No grouping needed and none applied")
    else:
        analysis["warnings"].append(f"⚠️ Unexpected grouping: {actual_group_by}")
    
    # 5. Field Relevance for avg operations (10 points)
    expected_field = expected.get("field")
    actual_field = main_value.get("field")
    
    if expected_operation == "avg":
        if expected_field and actual_field == expected_field:
            analysis["semantic_score"] += 10
            analysis["matches"].append(f"✅ Correct avg field: {actual_field}")
        elif expected_field and actual_field != expected_field:
            analysis["mismatches"].append(f"❌ Avg field mismatch: expected {expected_field}, got {actual_field}")
        elif not expected_field and actual_field:
            analysis["semantic_score"] += 8  # Points for including a field even if not specifically expected
            analysis["matches"].append(f"✅ Included avg field: {actual_field}")
    elif actual_operation == "avg" and not actual_field:
        analysis["mismatches"].append("❌ avg operation missing required field parameter")
    else:
        analysis["semantic_score"] += 10  # Full points for non-avg operations
    
    # 6. Title Relevance (20 points)
    expected_keywords = expected.get("title_keywords", [])
    title_lower = title.lower()
    
    keyword_matches = 0
    for keyword in expected_keywords:
        if keyword.lower() in title_lower:
            keyword_matches += 1
    
    if keyword_matches > 0:
        title_score = min(20, (keyword_matches / len(expected_keywords)) * 20)
        analysis["semantic_score"] += title_score
        analysis["matches"].append(f"✅ Title relevance: {keyword_matches}/{len(expected_keywords)} keywords matched")
    else:
        analysis["mismatches"].append("❌ Title doesn't contain expected keywords")
    
    # Determine semantic quality
    if analysis["semantic_score"] >= 85:
        quality = "EXCELLENT"
        quality_emoji = "🌟"
    elif analysis["semantic_score"] >= 70:
        quality = "GOOD"
        quality_emoji = "✅"
    elif analysis["semantic_score"] >= 50:
        quality = "FAIR"
        quality_emoji = "⚠️"
    else:
        quality = "POOR"
        quality_emoji = "❌"
    
    analysis["quality"] = quality
    analysis["quality_emoji"] = quality_emoji
    
    # Store detailed analysis
    analysis["detailed_analysis"] = {
        "title": title,
        "actual_entity": actual_entity,
        "actual_operation": actual_operation,
        "actual_filter": actual_filter,
        "actual_group_by": actual_group_by,
        "actual_field": actual_field,
        "expected": expected
    }
    
    return analysis

async def send_chat_request(query: str) -> str:
    """Send chat request to get response"""
    url = "http://localhost:8001/chat"
    
    payload = {
        "message": query,
        "model": "deepseek",
        "use_real_data": False,
        "temperature": 0.1
    }
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "No response received")
            
    except Exception as e:
        return f"ERROR: {str(e)}"

async def run_semantic_validation():
    """Run semantic validation on test cases"""
    print("🧠 Starting Semantic Relevance Validation")
    print("=" * 80)
    
    results = []
    total_semantic_score = 0
    valid_responses = 0
    
    for test_case in SEMANTIC_TEST_CASES:
        semantic_focus = test_case['expected_elements']['semantic_focus'].replace('_', ' ').title()
        print(f"\n📋 Test {test_case['id']}: {semantic_focus}")
        print(f"Query: {test_case['query']}")
        print("-" * 60)
        
        # Get response
        response = await send_chat_request(test_case['query'])
        
        if response.startswith("ERROR:"):
            print(f"❌ Request failed: {response}")
            continue
        
        try:
            # Parse JSON response
            if '```json' in response:
                start = response.find('```json') + 7
                end = response.find('```', start)
                if end != -1:
                    json_content = response[start:end].strip()
            else:
                json_content = response
                
            response_json = json.loads(json_content)
            
            # Analyze semantic relevance
            analysis = analyze_semantic_relevance(
                test_case['query'], 
                response_json, 
                test_case['expected_elements']
            )
            
            # Display results
            print(f"{analysis['quality_emoji']} {analysis['quality']} (Semantic Score: {analysis['semantic_score']}/100)")
            print(f"   📊 Title: {analysis['detailed_analysis']['title']}")
            print(f"   🎯 Focus: {test_case['expected_elements']['semantic_focus'].replace('_', ' ').title()}")
            
            # Show matches
            for match in analysis['matches'][:3]:  # Show first 3 matches
                print(f"   {match}")
            
            # Show mismatches
            for mismatch in analysis['mismatches'][:2]:  # Show first 2 mismatches
                print(f"   {mismatch}")
                
            results.append(analysis)
            total_semantic_score += analysis['semantic_score']
            valid_responses += 1
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {str(e)}")
        except Exception as e:
            print(f"❌ Analysis failed: {str(e)}")
        
        await asyncio.sleep(0.5)  # Small delay
    
    # Summary analysis
    print("\n" + "=" * 80)
    print("🧠 SEMANTIC RELEVANCE ANALYSIS")
    print("=" * 80)
    
    if valid_responses > 0:
        avg_semantic_score = total_semantic_score / valid_responses
        
        # Quality distribution
        excellent = sum(1 for r in results if r['quality'] == 'EXCELLENT')
        good = sum(1 for r in results if r['quality'] == 'GOOD') 
        fair = sum(1 for r in results if r['quality'] == 'FAIR')
        poor = sum(1 for r in results if r['quality'] == 'POOR')
        
        print(f"🌟 EXCELLENT: {excellent}/{valid_responses} ({excellent/valid_responses*100:.1f}%)")
        print(f"✅ GOOD: {good}/{valid_responses} ({good/valid_responses*100:.1f}%)")
        print(f"⚠️ FAIR: {fair}/{valid_responses} ({fair/valid_responses*100:.1f}%)")
        print(f"❌ POOR: {poor}/{valid_responses} ({poor/valid_responses*100:.1f}%)")
        
        print(f"\n📊 Average Semantic Relevance Score: {avg_semantic_score:.1f}/100")
        
        # Semantic quality assessment
        if avg_semantic_score >= 85:
            assessment = "🌟 OUTSTANDING - Perfect semantic understanding"
        elif avg_semantic_score >= 75:
            assessment = "🎯 EXCELLENT - Strong semantic accuracy"
        elif avg_semantic_score >= 65:
            assessment = "✅ GOOD - Generally accurate responses"
        elif avg_semantic_score >= 50:
            assessment = "⚠️ FAIR - Some semantic issues"
        else:
            assessment = "❌ POOR - Significant semantic problems"
        
        print(f"\n🎯 Semantic Assessment: {assessment}")
        
        # Common issue analysis
        all_mismatches = []
        for r in results:
            all_mismatches.extend(r['mismatches'])
        
        if all_mismatches:
            print(f"\n⚠️ Most Common Issues:")
            issue_counts = {}
            for issue in all_mismatches:
                # Extract issue type
                if "Entity mismatch" in issue:
                    issue_type = "Entity Selection"
                elif "Operation mismatch" in issue:
                    issue_type = "Operation Selection"  
                elif "Filter" in issue:
                    issue_type = "Filter Logic"
                elif "Grouping" in issue:
                    issue_type = "Grouping Logic"
                else:
                    issue_type = "Other"
                    
                issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
            
            for issue_type, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"   • {issue_type}: {count} instances")
        else:
            print(f"\n🎉 No semantic issues found!")
    
    return results

if __name__ == "__main__":
    print(f"🕐 Semantic validation started at: {datetime.now().isoformat()}")
    results = asyncio.run(run_semantic_validation())
    print(f"🕐 Semantic validation completed at: {datetime.now().isoformat()}")