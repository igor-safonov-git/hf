"""
Test the specific failed cases from previous metric accuracy test
Focus on the 7 cases that failed to see if comprehensive prompt fixes them
"""

import asyncio
import json
import aiohttp

async def test_failed_cases():
    """Test the specific cases that failed in previous test"""
    
    failed_cases = [
        {
            "question": "Откуда приходят наши кандидаты?",
            "expected_entity": "applicants_by_source",
            "expected_operation": "count"
        },
        {
            "question": "Какая конверсия вакансий в найм?",
            "expected_entity": "vacancy_conversion_summary", 
            "expected_operation": "avg"
        },
        {
            "question": "Сколько времени кандидаты проводят в каждом статусе?",
            "expected_entity": "time_in_status",
            "expected_operation": "avg"
        },
        {
            "question": "Как изменилась активность за последние месяцы?",
            "expected_entity": "applicant_activity_trends",
            "expected_operation": "count"
        },
        {
            "question": "Какие причины отказов самые частые?",
            "expected_entity": "rejections_by_stage",
            "expected_operation": "sum"
        },
        {
            "question": "Сколько вакансий мы закрыли успешно?",
            "expected_entity": "successful_closures",
            "expected_operation": "count"
        },
        {
            "question": "Какая загрузка у каждого рекрутера?",
            "expected_entity": "applicants_by_recruiter",
            "expected_operation": "avg"
        }
    ]
    
    print("🎯 Testing Previously Failed Cases with Comprehensive Prompt")
    print("=" * 60)
    
    improvements = 0
    total_tests = len(failed_cases)
    
    async with aiohttp.ClientSession() as session:
        for i, test in enumerate(failed_cases, 1):
            print(f"\n📊 Test {i}/{total_tests}: {test['question']}")
            print("-" * 40)
            
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
                                print("🎉 FIXED! Perfect match!")
                                improvements += 1
                            elif entity_match:
                                print("⚡ Entity FIXED! Operation still needs work")
                            elif operation_match:
                                print("⚡ Operation FIXED! Entity still needs work")
                            else:
                                print("❌ Still failing")
                        
                    else:
                        print(f"❌ HTTP Error: {response.status}")
                        
            except Exception as e:
                print(f"❌ Error: {e}")
    
    print(f"\n📈 IMPROVEMENT SUMMARY")
    print("=" * 30)
    print(f"Previously failed cases: {total_tests}")
    print(f"Now working perfectly: {improvements}")
    print(f"Improvement rate: {improvements/total_tests:.1%}")
    
    if improvements > 0:
        print(f"🎉 Comprehensive prompt fixed {improvements} cases!")
    else:
        print("😕 No improvements detected - prompt needs more work")

if __name__ == "__main__":
    asyncio.run(test_failed_cases())