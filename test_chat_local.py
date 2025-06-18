"""Test the chat endpoint with local data processing"""

import requests
import json

# Test queries
test_queries = [
    "Покажи топ рекрутеров по количеству наймов",
    "Сколько у нас открытых вакансий?",
    "Покажи распределение вакансий по статусам",
    "Сколько всего кандидатов в базе?"
]

for query in test_queries:
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print('='*60)
    
    response = requests.post(
        "http://localhost:8002/chat",
        json={"message": query}
    )
    
    if response.status_code == 200:
        data = response.json()
        report = data.get("response", "")
        
        try:
            # Try to parse as JSON
            report_json = json.loads(report)
            
            print(f"Title: {report_json.get('report_title', 'N/A')}")
            print(f"Main metric: {report_json.get('main_metric', {}).get('label', 'N/A')}")
            
            if 'real_value' in report_json.get('main_metric', {}):
                print(f"Real value: {report_json['main_metric']['real_value']}")
            
            if 'real_data' in report_json.get('chart', {}):
                real_data = report_json['chart']['real_data']
                print(f"\nChart data:")
                print(f"  Labels: {real_data.get('labels', [])[:5]}...")
                print(f"  Values: {real_data.get('values', [])[:5]}...")
                print(f"  Total items: {len(real_data.get('labels', []))}")
            
        except json.JSONDecodeError:
            print("Response (text):", report[:200] + "..." if len(report) > 200 else report)
    else:
        print(f"Error: {response.status_code}")
        print(response.text)