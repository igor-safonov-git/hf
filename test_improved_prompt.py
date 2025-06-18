"""
Test script to compare original vs improved prompt performance
"""

import asyncio
import json
import aiohttp
from typing import Dict, Any
from hr_analytics_prompt_improved import get_improved_prompt

async def test_question_with_improved_prompt(question: str) -> Dict[str, Any]:
    """Test a single question with the improved prompt"""
    
    # Get improved prompt
    improved_prompt = get_improved_prompt(use_local_cache=True)
    
    payload = {
        "message": question,
        "use_local_cache": True,
        "custom_prompt": improved_prompt  # If the bot supports custom prompts
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post("http://localhost:8001/chat", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error_text = await response.text()
                    return {"error": f"HTTP {response.status}: {error_text}"}
        except Exception as e:
            return {"error": str(e)}

async def compare_prompts():
    """Compare original vs improved prompt on key test questions"""
    
    test_questions = [
        "Сколько у нас сейчас кандидатов в воронке?",
        "Сколько открытых вакансий у нас есть?", 
        "Как работают наши рекрутеры?"
    ]
    
    print("🧪 Testing Improved Prompt")
    print("=" * 50)
    
    for question in test_questions:
        print(f"\n📋 Question: {question}")
        print("-" * 30)
        
        # Test with current system (assuming it uses original prompt)
        result = await test_question_with_improved_prompt(question)
        
        if "response" in result and isinstance(result["response"], str):
            try:
                parsed_response = json.loads(result["response"])
                
                # Check key structure elements
                has_main_metric = "main_metric" in parsed_response
                has_secondary_metrics = "secondary_metrics" in parsed_response
                secondary_count = len(parsed_response.get("secondary_metrics", []))
                entity_name = parsed_response.get("main_metric", {}).get("value", {}).get("entity", "unknown")
                
                print(f"✅ Main metric: {has_main_metric}")
                print(f"✅ Secondary metrics: {has_secondary_metrics} (count: {secondary_count})")
                print(f"✅ Entity used: {entity_name}")
                
                # Check if using systematic naming
                systematic_entities = [
                    "applicants_by_status", "applicants_all", "vacancies_open", 
                    "vacancies_all", "actions_by_recruiter", "moves_by_recruiter"
                ]
                uses_systematic_naming = entity_name in systematic_entities
                print(f"✅ Systematic naming: {uses_systematic_naming}")
                
                if not uses_systematic_naming:
                    print(f"⚠️  Should use systematic naming instead of: {entity_name}")
                
            except json.JSONDecodeError:
                print("❌ Invalid JSON response")
        elif "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print("❌ Unexpected response format")

if __name__ == "__main__":
    asyncio.run(compare_prompts())