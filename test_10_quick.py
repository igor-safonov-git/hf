"""
Quick test with 10 questions to verify improvements
"""

import asyncio
import json
import aiohttp
from hr_analytics_reports_50_implemented import get_hr_analytics_reports_50_implemented

async def test_10_questions():
    reports = get_hr_analytics_reports_50_implemented()
    base_url = "http://localhost:8001"
    
    print("🚀 Testing 10 Questions with Fixed Entities")
    print("="*60)
    
    results = []
    perfect_count = 0
    total_score = 0.0
    
    for i in range(10):
        report = reports[i]
        question = report["questions"][0]
        expected_entity = report["json"]["main_metric"]["value"]["entity"]
        expected_operation = report["json"]["main_metric"]["value"]["operation"]
        
        print(f"\n📊 Test {i+1}/10: {question[:60]}...")
        print(f"Expected: {expected_entity}.{expected_operation}")
        
        async with aiohttp.ClientSession() as session:
            payload = {"message": question, "use_local_cache": True}
            
            try:
                async with session.post(f"{base_url}/chat", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        if "response" in result:
                            parsed = json.loads(result["response"])
                            
                            main_metric = parsed.get('main_metric', {})
                            value_info = main_metric.get('value', {})
                            actual_entity = value_info.get('entity', '')
                            actual_operation = value_info.get('operation', '')
                            
                            entity_match = actual_entity == expected_entity
                            operation_match = actual_operation == expected_operation
                            score = (int(entity_match) + int(operation_match)) / 2.0
                            
                            total_score += score
                            if score == 1.0:
                                perfect_count += 1
                            
                            print(f"Actual:   {actual_entity}.{actual_operation}")
                            print(f"Entity: {'✅' if entity_match else '❌'} | Operation: {'✅' if operation_match else '❌'}")
                            print(f"Score: {score:.2f}")
                            
                            if score == 1.0:
                                print("🎉 PERFECT!")
                            elif score >= 0.5:
                                print("⚠️ Partial")
                            else:
                                print("❌ Poor")
                                
                            results.append({
                                "question": question,
                                "expected": f"{expected_entity}.{expected_operation}",
                                "actual": f"{actual_entity}.{actual_operation}",
                                "score": score
                            })
                    
            except Exception as e:
                print(f"Error: {e}")
                results.append({"question": question, "error": str(e), "score": 0.0})
        
        await asyncio.sleep(0.5)  # Brief delay
    
    avg_score = total_score / 10
    
    print(f"\n📈 10-QUESTION TEST RESULTS")
    print("="*50)
    print(f"Average Score: {avg_score:.3f} ({avg_score:.1%})")
    print(f"Perfect Matches: {perfect_count}/10")
    print(f"Improvement from 31.2%: {'+' if avg_score > 0.312 else ''}{(avg_score - 0.312):.1%}")
    
    if avg_score >= 0.9:
        print("🎯 OUTSTANDING! Near-perfect accuracy!")
    elif avg_score >= 0.8:
        print("🎉 EXCELLENT! Major improvement achieved!")
    elif avg_score >= 0.6:
        print("✅ GOOD! Significant improvement!")
    elif avg_score > 0.312:
        print("📈 Better than before!")
    else:
        print("❌ Still needs work")
        
    return avg_score

if __name__ == "__main__":
    asyncio.run(test_10_questions())