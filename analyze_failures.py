#!/usr/bin/env python3
"""
Analyze failure patterns to improve the prompt
"""
import asyncio
import httpx
import json

# Queries specifically designed to trigger different types of failures
FAILURE_ANALYSIS_QUERIES = [
    # Field mapping issues
    "Покажи среднее stay_duration для вакансий по отделам",
    "Какие вакансии имеют department поле?",
    "Анализ по отделам для status_mapping",
    "Группировка status_mapping по divisions",
    
    # Cross-entity relationship confusion
    "Соедини данные из applicants и vacancies по отделам",
    "Покажи applicants сгруппированные по divisions из vacancies", 
    "Анализ источников с группировкой по отделам вакансий",
    
    # Conceptual impossibilities
    "Среднее время в статусе для каждой вакансии",
    "stay_duration вакансий по рекрутерам",
    "Какие отделы имеют самое долгое stay_duration?",
    
    # Complex business logic that often fails
    "ROI каждого источника с учетом зарплаты и времени найма по отделам",
    "Конверсия воронки с детализацией по этапам и отделам",
    "Эффективность рекрутеров по отделам с учетом stay_duration",
]


async def analyze_failure_patterns():
    """Analyze specific failure patterns to improve prompts"""
    print("🔍 ANALYZING FAILURE PATTERNS")
    print("=" * 60)
    
    failures = []
    
    async with httpx.AsyncClient() as client:
        for i, query in enumerate(FAILURE_ANALYSIS_QUERIES):
            print(f"\n[{i+1:2d}/14] Testing: {query}")
            
            try:
                response = await client.post(
                    "http://localhost:8001/chat-retry",
                    json={
                        "message": query,
                        "model": "deepseek",
                        "show_debug": True,
                        "max_retries": 2,
                        "temperature": 0.1
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    success = result.get('validation_success', False)
                    attempts = result.get('attempts', 1)
                    conversation_log = result.get('conversation_log', [])
                    
                    if not success:
                        # Analyze the failure pattern
                        error_patterns = []
                        for log in conversation_log:
                            if "❌ Validation Failed:" in log:
                                error = log.split("❌ Validation Failed:")[-1].strip()
                                error_patterns.append(error)
                        
                        failure_info = {
                            'query': query,
                            'attempts': attempts,
                            'error_patterns': error_patterns,
                            'conversation_log': conversation_log
                        }
                        failures.append(failure_info)
                        print(f"  ❌ FAILED after {attempts} attempts")
                        print(f"  📝 Error: {error_patterns[-1][:100]}..." if error_patterns else "Unknown error")
                    else:
                        print(f"  ✅ SUCCESS after {attempts} attempts")
                        if attempts > 1:
                            # Still interesting - what was the retry reason?
                            for log in conversation_log:
                                if "❌ Validation Failed:" in log:
                                    error = log.split("❌ Validation Failed:")[-1].strip()
                                    print(f"  🔧 Had to fix: {error[:80]}...")
                                    break
                else:
                    print(f"  💥 HTTP Error: {response.status_code}")
                    
            except Exception as e:
                print(f"  💥 Exception: {str(e)}")
    
    # Analyze failure patterns
    print("\n" + "=" * 60)
    print("📊 FAILURE PATTERN ANALYSIS")
    print("=" * 60)
    
    if failures:
        print(f"\n🔴 Found {len(failures)} persistent failures:")
        
        # Categorize error patterns
        error_categories = {
            'Field not valid for entity': [],
            'Entity relationship issues': [],
            'Conceptual impossibilities': [],
            'Cross-entity grouping': [],
            'Other': []
        }
        
        for failure in failures:
            query = failure['query']
            patterns = failure['error_patterns']
            
            print(f"\n❌ {query}")
            for pattern in patterns:
                print(f"   └─ {pattern[:150]}...")
                
                # Categorize
                if 'not valid for entity' in pattern:
                    error_categories['Field not valid for entity'].append((query, pattern))
                elif 'department' in pattern and 'status_mapping' in pattern:
                    error_categories['Cross-entity grouping'].append((query, pattern))
                elif 'stay_duration' in query and 'вакансий' in query:
                    error_categories['Conceptual impossibilities'].append((query, pattern))
                else:
                    error_categories['Other'].append((query, pattern))
        
        # Report categories
        print(f"\n📋 Error Categories:")
        for category, errors in error_categories.items():
            if errors:
                print(f"\n🏷️  {category}: {len(errors)} cases")
                for query, pattern in errors[:3]:  # Show first 3 examples
                    print(f"   • {query[:50]}... → {pattern[:80]}...")
    
    # Generate prompt improvements
    print(f"\n💡 PROMPT IMPROVEMENT RECOMMENDATIONS")
    print("=" * 60)
    
    recommendations = []
    
    # Analyze specific patterns
    field_entity_errors = [f for f in failures if any('department' in p and 'status_mapping' in p for p in f['error_patterns'])]
    if field_entity_errors:
        recommendations.append({
            'issue': 'Cross-entity field confusion',
            'pattern': 'AI tries to group status_mapping by department field',
            'solution': 'Add explicit field mapping guidance between entities',
            'examples': [f['query'] for f in field_entity_errors[:2]]
        })
    
    stay_duration_errors = [f for f in failures if 'stay_duration' in f['query'] and 'вакансий' in f['query']]
    if stay_duration_errors:
        recommendations.append({
            'issue': 'Conceptual impossibility',
            'pattern': 'User asks for stay_duration of vacancies (impossible)',
            'solution': 'Add guidance to explain impossible concepts and suggest alternatives',
            'examples': [f['query'] for f in stay_duration_errors[:2]]
        })
    
    # Print recommendations
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['issue']}")
        print(f"   Pattern: {rec['pattern']}")
        print(f"   Solution: {rec['solution']}")
        print(f"   Examples: {rec['examples']}")
    
    # Save detailed analysis
    with open('failure_analysis.json', 'w', encoding='utf-8') as f:
        json.dump({
            'total_tested': len(FAILURE_ANALYSIS_QUERIES),
            'failures': failures,
            'recommendations': recommendations
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Detailed failure analysis saved to failure_analysis.json")
    
    return recommendations


if __name__ == "__main__":
    asyncio.run(analyze_failure_patterns())