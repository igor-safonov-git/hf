"""
Quick test with just 5 questions using implemented entities
"""

import asyncio
import json
import aiohttp
from hr_analytics_reports_50_implemented import get_hr_analytics_reports_50_implemented

async def quick_test():
    reports = get_hr_analytics_reports_50_implemented()
    base_url = "http://localhost:8001"
    
    print("🚀 Quick Test: 5 Questions with Implemented Entities")
    print("="*60)
    
    results = []
    total_score = 0.0
    
    for i in range(5):
        report = reports[i]
        question = report["questions"][0]
        expected_entity = report["json"]["main_metric"]["value"]["entity"]
        expected_operation = report["json"]["main_metric"]["value"]["operation"]
        
        print(f"\n📊 Test {i+1}/5: {question[:50]}...")
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
    
    avg_score = total_score / 5
    perfect_count = sum(1 for r in results if r.get("score", 0) == 1.0)
    
    print(f"\n📈 QUICK TEST RESULTS")
    print("="*40)
    print(f"Average Score: {avg_score:.3f} ({avg_score:.1%})")
    print(f"Perfect Matches: {perfect_count}/5")
    print(f"Improvement from 31.2%: {'+' if avg_score > 0.312 else ''}{(avg_score - 0.312):.1%}")
    
    if avg_score > 0.8:
        print("🎯 EXCELLENT! Major improvement achieved!")
    elif avg_score > 0.6:
        print("✅ GOOD! Significant improvement!")
    elif avg_score > 0.312:
        print("📈 Better than before, heading in right direction!")
    else:
        print("❌ Still needs work")
        
    return results

if __name__ == "__main__":
    asyncio.run(quick_test())