"""
Test metric accuracy - focus only on calculation logic
Tests entity names, operations, and filters used vs expected
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
    filters_match: bool
    score: float

class MetricAccuracyTester:
    """Test specifically metric calculation accuracy"""
    
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
        """Extract entity, operation, and filters from main metric"""
        main_metric = report.get("main_metric", {}).get("value", {})
        
        return {
            "entity": main_metric.get("entity", ""),
            "operation": main_metric.get("operation", ""),
            "filter": main_metric.get("filter", {}),
        }
    
    def calculate_metric_similarity(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> float:
        """Calculate similarity score focused only on metric calculation logic"""
        
        # Entity match (most important)
        entity_score = 1.0 if expected["entity"] == actual["entity"] else 0.0
        
        # Operation match (important)
        operation_score = 1.0 if expected["operation"] == actual["operation"] else 0.0
        
        # Filter match (if present)
        filter_score = 1.0  # Default to full score if no filters expected
        expected_filter = expected.get("filter", {})
        actual_filter = actual.get("filter", {})
        
        if expected_filter:
            if actual_filter:
                # Check key filter components
                field_match = expected_filter.get("field") == actual_filter.get("field")
                op_match = expected_filter.get("op") == actual_filter.get("op")
                value_match = expected_filter.get("value") == actual_filter.get("value")
                
                filter_score = sum([field_match, op_match, value_match]) / 3.0
            else:
                filter_score = 0.0
        
        # Weighted average: entity (50%), operation (30%), filter (20%)
        total_score = (entity_score * 0.5) + (operation_score * 0.3) + (filter_score * 0.2)
        
        return total_score
    
    async def test_metric_accuracy(self):
        """Test metric accuracy using the same 50 questions from our test suite"""
        
        # Import the 50 reports to get expected metrics
        from hr_analytics_reports_50 import HR_ANALYTICS_REPORTS
        
        test_cases = []
        
        # Extract first question from each report with expected metric (first 10 for quick test)
        for report_data in HR_ANALYTICS_REPORTS[:10]:  # Test first 10 reports
            # Take first question from each report
            question = report_data["questions"][0]
            expected_report = report_data["report"]
            
            # Extract expected metric info
            main_metric = expected_report["main_metric"]["value"]
            expected = {
                "entity": main_metric["entity"],
                "operation": main_metric["operation"],
                "filter": main_metric.get("filter", {})
            }
            
            test_cases.append({
                "question": question,
                "expected": expected
            })
        
        print("🎯 Testing Metric Calculation Accuracy")
        print(f"Testing {len(test_cases)} questions from our test suite")
        print("=" * 60)
        
        for i, test_case in enumerate(test_cases, 1):
            question = test_case["question"]
            expected = test_case["expected"]
            
            print(f"\n📊 Test {i}/{len(test_cases)}: {question}")
            print("-" * 40)
            
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
                print(f"Entity Match: {'✅' if entity_match else '❌'}")
                print(f"Operation Match: {'✅' if operation_match else '❌'}")
                print(f"Accuracy Score: {score:.2f}")
                
                # Store result
                comparison = MetricComparison(
                    question=question,
                    expected_entity=expected["entity"],
                    actual_entity=actual["entity"],
                    expected_operation=expected["operation"], 
                    actual_operation=actual["operation"],
                    entity_match=entity_match,
                    operation_match=operation_match,
                    filters_match=True,  # Simplified for now
                    score=score
                )
                self.results.append(comparison)
                
            else:
                print("❌ Failed to get valid response")
        
        # Summary
        if self.results:
            avg_score = sum(r.score for r in self.results) / len(self.results)
            entity_accuracy = sum(1 for r in self.results if r.entity_match) / len(self.results)
            operation_accuracy = sum(1 for r in self.results if r.operation_match) / len(self.results)
            
            print(f"\n📈 METRIC ACCURACY SUMMARY")
            print("=" * 40)
            print(f"Overall Accuracy Score: {avg_score:.2f}")
            print(f"Entity Name Accuracy: {entity_accuracy:.1%}")
            print(f"Operation Accuracy: {operation_accuracy:.1%}")
            print(f"Perfect Matches: {sum(1 for r in self.results if r.score == 1.0)}/{len(self.results)}")
            
            # Show worst performers
            worst = sorted(self.results, key=lambda x: x.score)[:5]
            print(f"\n🔍 Top 5 Areas for Improvement:")
            for result in worst:
                if result.score < 1.0:
                    print(f"  Score {result.score:.2f}: {result.question[:60]}...")
                    if not result.entity_match:
                        print(f"    Expected entity: {result.expected_entity}")
                        print(f"    Got entity: {result.actual_entity}")
                    if not result.operation_match:
                        print(f"    Expected operation: {result.expected_operation}")
                        print(f"    Got operation: {result.actual_operation}")
            
            # Show entity mapping issues
            entity_mismatches = [r for r in self.results if not r.entity_match]
            if entity_mismatches:
                print(f"\n🏷️ Entity Mapping Issues ({len(entity_mismatches)} cases):")
                entity_patterns = {}
                for result in entity_mismatches:
                    pattern = f"{result.expected_entity} → {result.actual_entity}"
                    entity_patterns[pattern] = entity_patterns.get(pattern, 0) + 1
                
                for pattern, count in sorted(entity_patterns.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {pattern}: {count} occurrences")
            
            # Show operation mapping issues  
            operation_mismatches = [r for r in self.results if not r.operation_match]
            if operation_mismatches:
                print(f"\n⚙️ Operation Mapping Issues ({len(operation_mismatches)} cases):")
                op_patterns = {}
                for result in operation_mismatches:
                    pattern = f"{result.expected_operation} → {result.actual_operation}"
                    op_patterns[pattern] = op_patterns.get(pattern, 0) + 1
                
                for pattern, count in sorted(op_patterns.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {pattern}: {count} occurrences")

async def main():
    tester = MetricAccuracyTester()
    await tester.test_metric_accuracy()

if __name__ == "__main__":
    asyncio.run(main())