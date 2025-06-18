"""
Test Real Data Pipeline - Ensure all JSON responses have 'real_data' populated
Tests the complete pipeline from question → AI response → data enrichment
"""

import asyncio
import json
import aiohttp
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class RealDataCheck:
    question: str
    has_real_data: bool
    main_metric_real_value: Any
    secondary_metrics_real_values: List[Any]
    chart_real_data: bool
    missing_fields: List[str]
    score: float

class RealDataTester:
    """Test that all responses from the full pipeline contain real data"""
    
    def __init__(self, bot_url: str = "http://localhost:8001"):
        self.bot_url = bot_url
        self.results: List[RealDataCheck] = []
    
    async def get_bot_response(self, question: str) -> Dict[str, Any]:
        """Get bot response through full pipeline"""
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
    
    def check_real_data_presence(self, response: Dict[str, Any]) -> RealDataCheck:
        """Check if response contains real data in all expected fields"""
        missing_fields = []
        
        # Check main metric real_value
        main_metric_real_value = None
        main_metric = response.get("main_metric", {})
        if "real_value" in main_metric:
            main_metric_real_value = main_metric["real_value"]
        else:
            missing_fields.append("main_metric.real_value")
        
        # Check secondary metrics real_values
        secondary_metrics_real_values = []
        secondary_metrics = response.get("secondary_metrics", [])
        
        for i, metric in enumerate(secondary_metrics):
            if "real_value" in metric:
                secondary_metrics_real_values.append(metric["real_value"])
            else:
                missing_fields.append(f"secondary_metrics[{i}].real_value")
        
        # Check chart real_data
        chart_real_data = False
        chart = response.get("chart", {})
        if "real_data" in chart:
            chart_real_data = True
        else:
            if chart:  # Only add to missing if chart exists
                missing_fields.append("chart.real_data")
        
        # Calculate score
        total_expected = 1 + len(secondary_metrics) + (1 if chart else 0)  # main + secondary + chart
        found_count = (1 if main_metric_real_value is not None else 0) + \
                     len(secondary_metrics_real_values) + \
                     (1 if chart_real_data else 0)
        
        score = found_count / total_expected if total_expected > 0 else 0.0
        
        return RealDataCheck(
            question="",  # Will be set by caller
            has_real_data=len(missing_fields) == 0,
            main_metric_real_value=main_metric_real_value,
            secondary_metrics_real_values=secondary_metrics_real_values,
            chart_real_data=chart_real_data,
            missing_fields=missing_fields,
            score=score
        )
    
    async def test_real_data_pipeline(self):
        """Test real data pipeline using same questions from metric accuracy test"""
        
        # Import the 50 reports to get same questions
        from hr_analytics_reports_50 import HR_ANALYTICS_REPORTS
        
        test_questions = []
        
        # Extract first question from each report (first 10 for manageable test)
        for report_data in HR_ANALYTICS_REPORTS[:10]:
            question = report_data["questions"][0]
            test_questions.append(question)
        
        print("🔍 Testing Real Data Pipeline")
        print(f"Testing {len(test_questions)} questions for real data presence")
        print("=" * 60)
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n📊 Test {i}/{len(test_questions)}: {question}")
            print("-" * 40)
            
            # Get bot response through full pipeline
            response = await self.get_bot_response(question)
            
            if response:
                # Check real data presence
                check = self.check_real_data_presence(response)
                check.question = question
                
                # Display results
                print(f"Main Metric Real Value: {'✅' if check.main_metric_real_value is not None else '❌'} ({check.main_metric_real_value})")
                print(f"Secondary Metrics Real Values: {'✅' if check.secondary_metrics_real_values else '❌'} ({len(check.secondary_metrics_real_values)} found)")
                if check.secondary_metrics_real_values:
                    print(f"  Values: {check.secondary_metrics_real_values}")
                print(f"Chart Real Data: {'✅' if check.chart_real_data else '❌'}")
                
                if check.missing_fields:
                    print(f"❌ Missing Fields: {', '.join(check.missing_fields)}")
                
                print(f"Real Data Score: {check.score:.2f}")
                
                if check.has_real_data:
                    print("🎉 COMPLETE REAL DATA!")
                else:
                    print("⚠️ Missing real data fields")
                
                self.results.append(check)
                
            else:
                print("❌ Failed to get valid response")
        
        # Summary
        if self.results:
            avg_score = sum(r.score for r in self.results) / len(self.results)
            complete_real_data = sum(1 for r in self.results if r.has_real_data) / len(self.results)
            
            print(f"\n📈 REAL DATA PIPELINE SUMMARY")
            print("=" * 40)
            print(f"Average Real Data Score: {avg_score:.2f}")
            print(f"Complete Real Data: {complete_real_data:.1%}")
            print(f"Perfect Real Data: {sum(1 for r in self.results if r.score == 1.0)}/{len(self.results)}")
            
            # Show issues
            issues = [r for r in self.results if not r.has_real_data]
            if issues:
                print(f"\n🔍 Real Data Issues ({len(issues)} cases):")
                for result in issues:
                    print(f"  {result.question[:60]}...")
                    for field in result.missing_fields:
                        print(f"    Missing: {field}")
            
            # Show field coverage
            all_missing = []
            for result in self.results:
                all_missing.extend(result.missing_fields)
            
            if all_missing:
                from collections import Counter
                field_counts = Counter(all_missing)
                print(f"\n📋 Missing Field Frequency:")
                for field, count in sorted(field_counts.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {field}: {count} occurrences")
            
            # Check specific data types/values
            print(f"\n📊 Real Data Value Analysis:")
            
            # Main metric values
            main_values = [r.main_metric_real_value for r in self.results if r.main_metric_real_value is not None]
            if main_values:
                print(f"Main Metric Values: {main_values}")
                print(f"  Range: {min(main_values)} - {max(main_values)}")
                print(f"  Average: {sum(main_values) / len(main_values):.1f}")
            
            # Secondary metrics
            all_secondary = []
            for result in self.results:
                all_secondary.extend(result.secondary_metrics_real_values)
            
            if all_secondary:
                print(f"Secondary Metric Values: {len(all_secondary)} total")
                print(f"  Sample: {all_secondary[:5]}...")
                if all(isinstance(x, (int, float)) for x in all_secondary):
                    print(f"  Range: {min(all_secondary)} - {max(all_secondary)}")
                    print(f"  Average: {sum(all_secondary) / len(all_secondary):.1f}")

async def main():
    tester = RealDataTester()
    await tester.test_real_data_pipeline()

if __name__ == "__main__":
    asyncio.run(main())