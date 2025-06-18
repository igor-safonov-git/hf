"""
Quick metric accuracy test - just a few key questions
"""

import asyncio
import json
import aiohttp

async def test_key_metrics():
    """Test 3 key questions to see metric accuracy"""
    
    test_cases = [
        {
            "question": "Сколько у нас сейчас кандидатов в воронке?",
            "expected_entity": "applicants_by_status",
            "expected_operation": "count"
        },
        {
            "question": "Сколько открытых вакансий у нас есть?", 
            "expected_entity": "vacancies_open",
            "expected_operation": "count"
        },
        {
            "question": "Как работают наши рекрутеры?",
            "expected_entity": "actions_by_recruiter", 
            "expected_operation": "sum"
        }
    ]
    
    print("🎯 Quick Metric Accuracy Test")
    print("=" * 40)
    
    async with aiohttp.ClientSession() as session:
        for i, test in enumerate(test_cases, 1):
            print(f"\n📊 Test {i}: {test['question']}")
            print("-" * 30)
            
            payload = {"message": test["question"], "use_local_cache": True}
            
            try:
                async with session.post("http://localhost:8001/chat", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        if "response" in result:
                            parsed = json.loads(result["response"])
                            
                            # Extract actual metric
                            actual_entity = parsed.get("main_metric", {}).get("value", {}).get("entity", "")
                            actual_operation = parsed.get("main_metric", {}).get("value", {}).get("operation", "")
                            
                            # Compare
                            entity_match = test["expected_entity"] == actual_entity
                            operation_match = test["expected_operation"] == actual_operation
                            
                            print(f"Expected: {test['expected_entity']}.{test['expected_operation']}")
                            print(f"Actual:   {actual_entity}.{actual_operation}")
                            print(f"Entity: {'✅' if entity_match else '❌'}")
                            print(f"Operation: {'✅' if operation_match else '❌'}")
                            
                            if entity_match and operation_match:
                                print("🎉 PERFECT MATCH!")
                            else:
                                print("⚠️ Needs improvement")
                        
                    else:
                        print(f"❌ HTTP Error: {response.status}")
                        
            except Exception as e:
                print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_key_metrics())