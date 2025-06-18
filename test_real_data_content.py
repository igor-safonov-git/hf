"""
Test Real Data Content - Ensure real_data contains actual data, not empty structures
Enhanced version that checks content quality, not just field presence
"""

import asyncio
import json
import aiohttp
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class RealDataContentCheck:
    question: str
    main_metric_has_content: bool
    main_metric_value: Any
    secondary_metrics_have_content: bool
    secondary_count: int
    chart_has_real_data: bool
    chart_data_points: int
    empty_fields: List[str]
    score: float

class RealDataContentTester:
    """Test that real_data contains actual meaningful content"""
    
    def __init__(self, bot_url: str = "http://localhost:8001"):
        self.bot_url = bot_url
        self.results: List[RealDataContentCheck] = []
    
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
    
    def check_real_data_content(self, response: Dict[str, Any]) -> RealDataContentCheck:
        """Check if real_data contains meaningful content, not just empty structures"""
        empty_fields = []
        
        # Check main metric real_value content
        main_metric_has_content = False
        main_metric_value = None
        main_metric = response.get("main_metric", {})
        
        if "real_value" in main_metric:
            value = main_metric["real_value"]
            if value is not None and value != "" and value != 0:
                main_metric_has_content = True
                main_metric_value = value
            else:
                empty_fields.append("main_metric.real_value (empty/zero)")
        else:
            empty_fields.append("main_metric.real_value (missing)")
        
        # Check secondary metrics real_values content
        secondary_metrics_have_content = False
        secondary_count = 0
        secondary_metrics = response.get("secondary_metrics", [])
        
        for i, metric in enumerate(secondary_metrics):
            if "real_value" in metric:
                value = metric["real_value"] 
                if value is not None and value != "" and value != 0:
                    secondary_count += 1
                else:
                    empty_fields.append(f"secondary_metrics[{i}].real_value (empty/zero)")
            else:
                empty_fields.append(f"secondary_metrics[{i}].real_value (missing)")
        
        secondary_metrics_have_content = secondary_count > 0
        
        # Check chart real_data content
        chart_has_real_data = False
        chart_data_points = 0
        chart = response.get("chart", {})
        
        if "real_data" in chart:
            real_data = chart["real_data"]
            
            # Handle both list and dict formats
            if isinstance(real_data, list) and len(real_data) > 0:
                # List format: [{'label': 'A', 'value': 10}, ...]
                for point in real_data:
                    if isinstance(point, dict) and len(point) > 0:
                        # Check if values are not empty/zero
                        has_meaningful_values = any(
                            v is not None and v != "" and v != 0 
                            for v in point.values() 
                            if not isinstance(v, str) or v.strip()
                        )
                        if has_meaningful_values:
                            chart_data_points += 1
                
                if chart_data_points > 0:
                    chart_has_real_data = True
                else:
                    empty_fields.append("chart.real_data (no meaningful data points)")
                    
            elif isinstance(real_data, dict):
                # Dict format: {'labels': [...], 'values': [...]}
                labels = real_data.get('labels', [])
                values = real_data.get('values', [])
                
                if len(labels) > 0 and len(values) > 0:
                    # Count non-zero values
                    meaningful_values = [v for v in values if v is not None and v != "" and v != 0]
                    chart_data_points = len(meaningful_values)
                    
                    if chart_data_points > 0:
                        chart_has_real_data = True
                    else:
                        empty_fields.append("chart.real_data (all values are zero/empty)")
                else:
                    empty_fields.append("chart.real_data (empty labels or values)")
            else:
                empty_fields.append("chart.real_data (invalid format)")
        else:
            if chart:  # Only complain if chart exists
                empty_fields.append("chart.real_data (missing)")
        
        # Calculate content quality score
        content_checks = [
            main_metric_has_content,
            secondary_metrics_have_content,
            chart_has_real_data if chart else True  # Don't penalize missing charts
        ]
        
        score = sum(content_checks) / len(content_checks)
        
        return RealDataContentCheck(
            question="",  # Will be set by caller
            main_metric_has_content=main_metric_has_content,
            main_metric_value=main_metric_value,
            secondary_metrics_have_content=secondary_metrics_have_content,
            secondary_count=secondary_count,
            chart_has_real_data=chart_has_real_data,
            chart_data_points=chart_data_points,
            empty_fields=empty_fields,
            score=score
        )
    
    async def test_real_data_content(self):
        """Test real data content quality using same questions"""
        
        # Import the 50 reports to get same questions
        from hr_analytics_reports_50 import HR_ANALYTICS_REPORTS
        
        test_questions = []
        
        # Extract first question from each report (first 10 for focused test)
        for report_data in HR_ANALYTICS_REPORTS[:10]:
            question = report_data["questions"][0]
            test_questions.append(question)
        
        print("🔍 Testing Real Data Content Quality")
        print(f"Testing {len(test_questions)} questions for meaningful real data")
        print("=" * 60)
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n📊 Test {i}/{len(test_questions)}: {question}")
            print("-" * 40)
            
            # Get bot response through full pipeline
            response = await self.get_bot_response(question)
            
            if response:
                # Check real data content quality
                check = self.check_real_data_content(response)
                check.question = question
                
                # Display results
                print(f"Main Metric Content: {'✅' if check.main_metric_has_content else '❌'} (value: {check.main_metric_value})")
                print(f"Secondary Metrics Content: {'✅' if check.secondary_metrics_have_content else '❌'} ({check.secondary_count} with content)")
                print(f"Chart Real Data: {'✅' if check.chart_has_real_data else '❌'} ({check.chart_data_points} data points)")
                
                if check.empty_fields:
                    print(f"❌ Empty/Missing Fields: {len(check.empty_fields)}")
                    for field in check.empty_fields:
                        print(f"  - {field}")
                
                print(f"Content Quality Score: {check.score:.2f}")
                
                if check.score == 1.0:
                    print("🎉 PERFECT CONTENT QUALITY!")
                elif check.score >= 0.8:
                    print("✅ Good content quality")
                elif check.score >= 0.5:
                    print("⚠️ Moderate content quality")
                else:
                    print("❌ Poor content quality")
                
                self.results.append(check)
                
            else:
                print("❌ Failed to get valid response")
        
        # Summary
        if self.results:
            avg_score = sum(r.score for r in self.results) / len(self.results)
            perfect_content = sum(1 for r in self.results if r.score == 1.0) / len(self.results)
            
            print(f"\n📈 REAL DATA CONTENT SUMMARY")
            print("=" * 40)
            print(f"Average Content Quality Score: {avg_score:.2f}")
            print(f"Perfect Content Quality: {perfect_content:.1%}")
            print(f"Perfect Content Cases: {sum(1 for r in self.results if r.score == 1.0)}/{len(self.results)}")
            
            # Content analysis
            main_metric_issues = sum(1 for r in self.results if not r.main_metric_has_content)
            secondary_issues = sum(1 for r in self.results if not r.secondary_metrics_have_content)
            chart_issues = sum(1 for r in self.results if not r.chart_has_real_data)
            
            print(f"\n📊 Content Issues Breakdown:")
            print(f"Main Metric Issues: {main_metric_issues}/{len(self.results)}")
            print(f"Secondary Metrics Issues: {secondary_issues}/{len(self.results)}")
            print(f"Chart Data Issues: {chart_issues}/{len(self.results)}")
            
            # Show value ranges
            main_values = [r.main_metric_value for r in self.results if r.main_metric_value is not None]
            if main_values:
                print(f"\n📊 Real Data Value Analysis:")
                print(f"Main Metric Values: {main_values}")
                if all(isinstance(x, (int, float)) for x in main_values):
                    print(f"  Range: {min(main_values)} - {max(main_values)}")
                    print(f"  Average: {sum(main_values) / len(main_values):.1f}")
                    print(f"  Non-zero values: {sum(1 for x in main_values if x != 0)}/{len(main_values)}")
            
            # Show common empty field patterns
            all_empty = []
            for result in self.results:
                all_empty.extend(result.empty_fields)
            
            if all_empty:
                from collections import Counter
                empty_counts = Counter(all_empty)
                print(f"\n⚠️ Most Common Empty Field Issues:")
                for field, count in sorted(empty_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                    print(f"  {field}: {count} occurrences")

async def main():
    tester = RealDataContentTester()
    await tester.test_real_data_content()

if __name__ == "__main__":
    asyncio.run(main())