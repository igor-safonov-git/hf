"""
Test metric accuracy on ALL 50 questions from our test suite
Comprehensive test to see how well the comprehensive prompt performs across all scenarios
"""

import asyncio
import json
import aiohttp
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass

@dataclass
class MetricComparison:
    question: str
    expected_entity: str
    actual_entity: str
    expected_operation: str
    actual_operation: str
    entity_match: bool
    operation_match: bool
    score: float

class FullMetricAccuracyTester:
    """Test metric accuracy on all 50 questions"""
    
    def __init__(self, bot_url: str = "http://localhost:8001"):
        self.bot_url = bot_url
        self.results: List[MetricComparison] = []
    
    async def get_bot_response(self, question: str) -> Dict[str, Any]:
        """Get bot response and parse JSON"""
        async with aiohttp.ClientSession() as session:
            payload = {"message": question, "use_local_cache": True}
            
            try:
                async with session.post(f"{self.bot_url}/chat", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        if "response" in result:
                            return json.loads(result["response"])
            except Exception as e:
                print(f"Error: {e}")
            
            return {}
    
    def extract_metric_info(self, report: Dict[str, Any]) -> Dict[str, str]:
        """Extract entity, operation from main metric"""
        main_metric = report.get("main_metric", {}).get("value", {})
        
        return {
            "entity": main_metric.get("entity", ""),
            "operation": main_metric.get("operation", ""),
        }
    
    def calculate_metric_similarity(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> float:
        """Calculate similarity score focused on metric calculation logic"""
        
        # Entity match (60% weight)
        entity_score = 1.0 if expected["entity"] == actual["entity"] else 0.0
        
        # Operation match (40% weight)  
        operation_score = 1.0 if expected["operation"] == actual["operation"] else 0.0
        
        # Weighted average
        total_score = (entity_score * 0.6) + (operation_score * 0.4)
        
        return total_score
    
    async def test_all_50_questions(self):
        """Test metric accuracy using ALL 50 questions from our test suite"""
        
        # Import the 50 reports to get expected metrics
        from hr_analytics_reports_50 import HR_ANALYTICS_REPORTS
        
        test_cases = []
        
        # Extract first question from ALL 50 reports
        for i, report_data in enumerate(HR_ANALYTICS_REPORTS):
            # Take first question from each report
            question = report_data["questions"][0]
            expected_report = report_data["report"]
            
            # Extract expected metric info
            main_metric = expected_report["main_metric"]["value"]
            expected = {
                "entity": main_metric["entity"],
                "operation": main_metric["operation"]
            }
            
            test_cases.append({
                "report_id": i + 1,
                "question": question,
                "expected": expected
            })
        
        print("🎯 Testing Metric Calculation Accuracy - ALL 50 QUESTIONS")
        print(f"Testing {len(test_cases)} questions from complete test suite")
        print("=" * 70)
        
        categories = {
            "perfect": [],      # 1.0 score
            "good": [],         # 0.8-0.99 score  
            "partial": [],      # 0.4-0.79 score
            "poor": []          # 0.0-0.39 score
        }
        
        for i, test_case in enumerate(test_cases, 1):
            question = test_case["question"]
            expected = test_case["expected"]
            report_id = test_case["report_id"]
            
            print(f"\n📊 Test {i}/50 (Report #{report_id}): {question[:60]}...")
            print("-" * 50)
            
            # Get bot response
            response = await self.get_bot_response(question)
            
            if response:
                actual = self.extract_metric_info(response)
                
                # Compare metrics
                entity_match = expected["entity"] == actual["entity"]
                operation_match = expected["operation"] == actual["operation"]
                
                # Calculate similarity score
                score = self.calculate_metric_similarity(expected, actual)
                
                # Display results
                print(f"Expected: {expected['entity']}.{expected['operation']}")
                print(f"Actual:   {actual['entity']}.{actual['operation']}")
                print(f"Entity: {'✅' if entity_match else '❌'} | Operation: {'✅' if operation_match else '❌'}")
                print(f"Score: {score:.2f}")
                
                # Categorize result
                if score == 1.0:
                    categories["perfect"].append(i)
                    print("🎉 PERFECT!")
                elif score >= 0.8:
                    categories["good"].append(i)
                    print("✅ Good")
                elif score >= 0.4:
                    categories["partial"].append(i)
                    print("⚠️ Partial")
                else:
                    categories["poor"].append(i)
                    print("❌ Poor")
                
                # Store result
                comparison = MetricComparison(
                    question=question,
                    expected_entity=expected["entity"],
                    actual_entity=actual["entity"],
                    expected_operation=expected["operation"], 
                    actual_operation=actual["operation"],
                    entity_match=entity_match,
                    operation_match=operation_match,
                    score=score
                )
                self.results.append(comparison)
                
            else:
                print("❌ Failed to get valid response")
                categories["poor"].append(i)
        
        # Comprehensive Summary
        if self.results:
            avg_score = sum(r.score for r in self.results) / len(self.results)
            entity_accuracy = sum(1 for r in self.results if r.entity_match) / len(self.results)
            operation_accuracy = sum(1 for r in self.results if r.operation_match) / len(self.results)
            
            print(f"\n📈 COMPREHENSIVE METRIC ACCURACY SUMMARY (50 Questions)")
            print("=" * 60)
            print(f"Overall Accuracy Score: {avg_score:.3f}")
            print(f"Entity Name Accuracy: {entity_accuracy:.1%}")
            print(f"Operation Accuracy: {operation_accuracy:.1%}")
            
            print(f"\n📊 Performance Categories:")
            print(f"🎉 Perfect (1.0): {len(categories['perfect'])}/50 ({len(categories['perfect'])/50:.1%})")
            print(f"✅ Good (0.8-0.99): {len(categories['good'])}/50 ({len(categories['good'])/50:.1%})")
            print(f"⚠️ Partial (0.4-0.79): {len(categories['partial'])}/50 ({len(categories['partial'])/50:.1%})")
            print(f"❌ Poor (0.0-0.39): {len(categories['poor'])}/50 ({len(categories['poor'])/50:.1%})")
            
            # Entity mapping analysis
            entity_mismatches = [r for r in self.results if not r.entity_match]
            if entity_mismatches:
                print(f"\n🏷️ Entity Mapping Issues ({len(entity_mismatches)} cases):")
                entity_patterns = {}
                for result in entity_mismatches:
                    pattern = f"{result.expected_entity} → {result.actual_entity}"
                    entity_patterns[pattern] = entity_patterns.get(pattern, 0) + 1
                
                for pattern, count in sorted(entity_patterns.items(), key=lambda x: x[1], reverse=True)[:10]:
                    print(f"  {pattern}: {count} occurrences")
            
            # Operation mapping analysis
            operation_mismatches = [r for r in self.results if not r.operation_match]
            if operation_mismatches:
                print(f"\n⚙️ Operation Mapping Issues ({len(operation_mismatches)} cases):")
                op_patterns = {}
                for result in operation_mismatches:
                    pattern = f"{result.expected_operation} → {result.actual_operation}"
                    op_patterns[pattern] = op_patterns.get(pattern, 0) + 1
                
                for pattern, count in sorted(op_patterns.items(), key=lambda x: x[1], reverse=True)[:5]:
                    print(f"  {pattern}: {count} occurrences")
            
            # Show worst performing questions
            worst = sorted(self.results, key=lambda x: x.score)[:5]
            print(f"\n🔍 Top 5 Areas for Improvement:")
            for result in worst:
                if result.score < 1.0:
                    print(f"  Score {result.score:.2f}: {result.question[:50]}...")
                    if not result.entity_match:
                        print(f"    Expected entity: {result.expected_entity}")
                        print(f"    Got entity: {result.actual_entity}")
                    if not result.operation_match:
                        print(f"    Expected operation: {result.expected_operation}")
                        print(f"    Got operation: {result.actual_operation}")

async def main():
    tester = FullMetricAccuracyTester()
    await tester.test_all_50_questions()

if __name__ == "__main__":
    asyncio.run(main())