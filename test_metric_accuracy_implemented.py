"""
Test metric accuracy using only implemented entities from metrics_calculator.py
This should have much higher accuracy since all entities actually exist.
"""

import asyncio
import json
import aiohttp
from typing import Dict, Any, List, Tuple
from hr_analytics_reports_50_implemented import get_hr_analytics_reports_50_implemented

class ImplementedEntityTester:
    def __init__(self):
        self.base_url = "http://localhost:8001"
        
    async def test_single_question(self, question: str, expected_entity: str, expected_operation: str) -> Tuple[float, Dict[str, Any]]:
        """Test a single question and return accuracy score and details"""
        async with aiohttp.ClientSession() as session:
            payload = {"message": question, "use_local_cache": True}
            
            try:
                async with session.post(f"{self.base_url}/chat", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        if "response" in result:
                            parsed = json.loads(result["response"])
                            
                            # Extract actual entity and operation
                            main_metric = parsed.get('main_metric', {})
                            value_info = main_metric.get('value', {})
                            actual_entity = value_info.get('entity', '')
                            actual_operation = value_info.get('operation', '')
                            
                            # Calculate accuracy
                            entity_match = 1.0 if actual_entity == expected_entity else 0.0
                            operation_match = 1.0 if actual_operation == expected_operation else 0.0
                            overall_score = (entity_match + operation_match) / 2.0
                            
                            return overall_score, {
                                "expected_entity": expected_entity,
                                "actual_entity": actual_entity,
                                "expected_operation": expected_operation,
                                "actual_operation": actual_operation,
                                "entity_match": entity_match,
                                "operation_match": operation_match,
                                "parsed_response": parsed
                            }
                    
                    return 0.0, {"error": f"HTTP {response.status}"}
                    
            except Exception as e:
                return 0.0, {"error": str(e)}
    
    async def test_implemented_entities(self, max_tests: int = 25) -> Dict[str, Any]:
        """Test questions using only implemented entities"""
        
        print("🧪 Testing Implemented Entities Only")
        print("="*60)
        
        reports = get_hr_analytics_reports_50_implemented()
        
        total_score = 0.0
        entity_matches = 0
        operation_matches = 0
        results = []
        
        # Test first max_tests reports
        for i, report in enumerate(reports[:max_tests]):
            question = report["questions"][0]  # Use first question
            expected_json = report["json"]
            
            expected_entity = expected_json["main_metric"]["value"]["entity"]
            expected_operation = expected_json["main_metric"]["value"]["operation"]
            
            print(f"\n📊 Test {i+1}/{max_tests}: {question[:50]}...")
            print("-" * 50)
            
            score, details = await self.test_single_question(question, expected_entity, expected_operation)
            
            total_score += score
            if details.get("entity_match", 0) == 1.0:
                entity_matches += 1
            if details.get("operation_match", 0) == 1.0:
                operation_matches += 1
            
            # Display result
            if score == 1.0:
                print("🎉 PERFECT!")
            elif score >= 0.5:
                print("⚠️ Partial match")
            else:
                print("❌ Poor match")
                
            print(f"Expected: {expected_entity}.{expected_operation}")
            print(f"Actual:   {details.get('actual_entity', 'N/A')}.{details.get('actual_operation', 'N/A')}")
            print(f"Score: {score:.2f}")
            
            results.append({
                "question": question,
                "score": score,
                "details": details
            })
            
            # Small delay to avoid overwhelming the server
            await asyncio.sleep(0.5)
        
        # Calculate final statistics
        avg_score = total_score / max_tests if max_tests > 0 else 0.0
        entity_accuracy = entity_matches / max_tests if max_tests > 0 else 0.0
        operation_accuracy = operation_matches / max_tests if max_tests > 0 else 0.0
        
        summary = {
            "total_tests": max_tests,
            "average_score": avg_score,
            "entity_accuracy": entity_accuracy,
            "operation_accuracy": operation_accuracy,
            "entity_matches": entity_matches,
            "operation_matches": operation_matches,
            "results": results
        }
        
        print(f"\n📈 IMPLEMENTED ENTITIES TEST SUMMARY")
        print("="*60)
        print(f"Overall Accuracy Score: {avg_score:.3f}")
        print(f"Entity Name Accuracy: {entity_accuracy:.1%}")
        print(f"Operation Accuracy: {operation_accuracy:.1%}")
        print(f"Perfect Matches: {sum(1 for r in results if r['score'] == 1.0)}/{max_tests}")
        print(f"Partial Matches: {sum(1 for r in results if 0.5 <= r['score'] < 1.0)}/{max_tests}")
        print(f"Poor Matches: {sum(1 for r in results if r['score'] < 0.5)}/{max_tests}")
        
        return summary

async def main():
    tester = ImplementedEntityTester()
    
    print("🔬 Testing Comprehensive Prompt with ONLY IMPLEMENTED ENTITIES")
    print("This should show much higher accuracy than the previous 31.2% score")
    print("="*80)
    
    # Test with 25 questions first
    summary = await tester.test_implemented_entities(max_tests=25)
    
    # Save results
    with open("implemented_entities_test_results.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Results saved to implemented_entities_test_results.json")
    
    if summary["average_score"] > 0.8:
        print("🎯 EXCELLENT! High accuracy achieved with implemented entities only.")
    elif summary["average_score"] > 0.6:
        print("✅ GOOD! Significant improvement over previous results.")
    else:
        print("⚠️ Still needs work, but should be better than before.")

if __name__ == "__main__":
    asyncio.run(main())