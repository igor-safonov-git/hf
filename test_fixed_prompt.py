"""
Test the fixed prompt against the main failure cases
"""

import asyncio
import json
import aiohttp
from context_data_injector import get_dynamic_context
from hr_analytics_prompt_fixed import get_fixed_prompt

async def test_fixed_prompt():
    """Test the fixed prompt against the most problematic questions"""
    
    # Get real context data
    context = await get_dynamic_context()
    
    # Generate fixed prompt
    fixed_prompt = get_fixed_prompt(huntflow_context=context, use_local_cache=True)
    
    # Test questions that had the most issues
    test_questions = [
        "Сколько у нас сейчас кандидатов в воронке?",  # Score 0.21 - missing secondary metrics
        "Как распределены кандидаты по этапам найма?",  # Score 0.00 - missing chart
        "Сколько открытых вакансий у нас есть?",        # Score 0.11 - structure issues
        "Как работают наши рекрутеры?",                 # Score 0.40 - best performing, let's see if we can improve
    ]
    
    print("🧪 Testing Fixed Prompt Against Main Failure Cases")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        for i, question in enumerate(test_questions, 1):
            print(f"\n📋 Test {i}/4: {question}")
            print("-" * 40)
            
            # Test with bot (note: would need to update bot to use fixed prompt)
            payload = {
                "message": question,
                "use_local_cache": True
            }
            
            try:
                async with session.post("http://localhost:8001/chat", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        if "response" in result and isinstance(result["response"], str):
                            try:
                                parsed_response = json.loads(result["response"])
                                
                                # Check for main issues
                                has_main_metric = "main_metric" in parsed_response
                                has_secondary_metrics = "secondary_metrics" in parsed_response
                                secondary_count = len(parsed_response.get("secondary_metrics", []))
                                has_chart = "chart" in parsed_response
                                
                                print(f"✅ Main metric: {has_main_metric}")
                                print(f"✅ Secondary metrics: {has_secondary_metrics} (count: {secondary_count})")
                                print(f"✅ Chart present: {has_chart}")
                                
                                # Check if it meets our requirements
                                meets_requirements = (
                                    has_main_metric and 
                                    has_secondary_metrics and 
                                    secondary_count == 2 and 
                                    has_chart
                                )
                                
                                if meets_requirements:
                                    print("🎉 PASSES all structure requirements!")
                                else:
                                    print("❌ Still has structural issues")
                                    if secondary_count != 2:
                                        print(f"   - Need exactly 2 secondary metrics, got {secondary_count}")
                                    if not has_chart:
                                        print("   - Missing chart section")
                                
                            except json.JSONDecodeError:
                                print("❌ Invalid JSON response")
                        else:
                            print("❌ Unexpected response format")
                            
                    else:
                        print(f"❌ HTTP Error: {response.status}")
                        
            except Exception as e:
                print(f"❌ Request failed: {e}")
    
    print(f"\n📝 Fixed Prompt Length: {len(fixed_prompt)} characters")
    print("\n🔧 Key improvements in fixed prompt:")
    print("  - MANDATORY secondary metrics with failure warnings")
    print("  - Simplified entity naming (8 core entities vs 20+)")
    print("  - Clear operation mapping (count/avg/sum)")
    print("  - Concrete examples for each question type")
    print("  - Validation checklist before response")
    print("  - Explicit JSON structure requirements")

if __name__ == "__main__":
    asyncio.run(test_fixed_prompt())