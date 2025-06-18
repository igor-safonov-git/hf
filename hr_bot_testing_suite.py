"""
HR Analytics Bot Testing Suite
Comprehensive testing framework that feeds Russian questions to the HR bot,
compares responses with expected examples, and documents mismatches.
"""

import asyncio
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import aiohttp
import difflib
from pathlib import Path

# Import our example data
from hr_analytics_reports_50 import HR_ANALYTICS_REPORTS
from hr_analytics_examples_200 import HR_ANALYTICS_EXAMPLES

@dataclass
class TestResult:
    """Structure for storing individual test results."""
    question: str
    expected_report: Dict[str, Any]
    actual_response: Dict[str, Any]
    match_score: float
    structural_match: bool
    metric_match: bool
    chart_match: bool
    issues: List[str]
    execution_time: float
    timestamp: datetime

@dataclass
class TestSummary:
    """Overall testing session summary."""
    total_tests: int
    passed_tests: int
    failed_tests: int
    average_score: float
    average_execution_time: float
    start_time: datetime
    end_time: datetime
    issues_summary: Dict[str, int]

class HRBotTester:
    """Main testing class for HR Analytics Bot."""
    
    def __init__(self, bot_url: str = "http://localhost:8001", timeout: int = 30):
        self.bot_url = bot_url
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self.test_results: List[TestResult] = []
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'hr_bot_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def send_question_to_bot(self, question: str) -> Dict[str, Any]:
        """Send a question to the HR bot and get the response."""
        try:
            # Prepare the request payload
            payload = {
                "message": question,
                "use_local_cache": True  # Use local cache for consistent testing
            }
            
            start_time = time.time()
            
            async with self.session.post(f"{self.bot_url}/chat", json=payload) as response:
                execution_time = time.time() - start_time
                
                if response.status == 200:
                    result = await response.json()
                    result["execution_time"] = execution_time
                    return result
                else:
                    error_text = await response.text()
                    return {
                        "error": f"HTTP {response.status}: {error_text}",
                        "execution_time": execution_time
                    }
        
        except asyncio.TimeoutError:
            return {"error": "Request timeout", "execution_time": self.timeout}
        except Exception as e:
            return {"error": str(e), "execution_time": 0}
    
    def compare_metrics(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Compare main and secondary metrics between expected and actual responses."""
        issues = []
        metric_match = True
        
        # Check main metric
        expected_main = expected.get("main_metric", {})
        actual_main = actual.get("main_metric", {})
        
        if not actual_main:
            issues.append("Missing main_metric in actual response")
            metric_match = False
        else:
            # Compare metric structure
            expected_value = expected_main.get("value", {})
            actual_value = actual_main.get("value", {})
            
            if expected_value.get("entity") != actual_value.get("entity"):
                issues.append(f"Entity mismatch: expected {expected_value.get('entity')}, got {actual_value.get('entity')}")
                metric_match = False
            
            if expected_value.get("operation") != actual_value.get("operation"):
                issues.append(f"Operation mismatch: expected {expected_value.get('operation')}, got {actual_value.get('operation')}")
                metric_match = False
        
        # Check secondary metrics
        expected_secondary = expected.get("secondary_metrics", [])
        actual_secondary = actual.get("secondary_metrics", [])
        
        if len(expected_secondary) != len(actual_secondary):
            issues.append(f"Secondary metrics count mismatch: expected {len(expected_secondary)}, got {len(actual_secondary)}")
            metric_match = False
        
        return metric_match, issues
    
    def compare_chart_structure(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Compare chart structure between expected and actual responses."""
        issues = []
        chart_match = True
        
        expected_chart = expected.get("chart", {})
        actual_chart = actual.get("chart", {})
        
        if not actual_chart:
            issues.append("Missing chart in actual response")
            return False, issues
        
        # Check required chart fields
        required_fields = ["chart_type", "x_axis_name", "y_axis_name", "graph_description"]
        for field in required_fields:
            if field not in actual_chart:
                issues.append(f"Missing chart field: {field}")
                chart_match = False
            elif expected_chart.get(field) != actual_chart.get(field):
                issues.append(f"Chart {field} mismatch: expected '{expected_chart.get(field)}', got '{actual_chart.get(field)}'")
        
        # Check chart axes structure
        expected_y_axis = expected_chart.get("y_axis", {})
        actual_y_axis = actual_chart.get("y_axis", {})
        
        if expected_y_axis.get("entity") != actual_y_axis.get("entity"):
            issues.append(f"Chart entity mismatch: expected {expected_y_axis.get('entity')}, got {actual_y_axis.get('entity')}")
            chart_match = False
        
        return chart_match, issues
    
    def calculate_json_similarity(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> float:
        """Calculate similarity score between two JSON structures."""
        try:
            expected_str = json.dumps(expected, sort_keys=True, ensure_ascii=False)
            actual_str = json.dumps(actual, sort_keys=True, ensure_ascii=False)
            
            # Use difflib to calculate similarity
            similarity = difflib.SequenceMatcher(None, expected_str, actual_str).ratio()
            return similarity
        except Exception:
            return 0.0
    
    def analyze_response_structure(self, response: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Analyze if the response has proper structure."""
        issues = []
        structural_match = True
        
        # Check for impossible_query format
        if response.get("impossible_query"):
            # This is a valid response format
            if not response.get("reason"):
                issues.append("Impossible query response missing reason")
                structural_match = False
            return structural_match, issues
        
        # Check for required report fields
        required_fields = ["report_title", "main_metric"]
        for field in required_fields:
            if field not in response:
                issues.append(f"Missing required field: {field}")
                structural_match = False
        
        # Check main_metric structure
        main_metric = response.get("main_metric", {})
        if main_metric:
            if "label" not in main_metric:
                issues.append("Missing label in main_metric")
                structural_match = False
            
            value = main_metric.get("value", {})
            if not value:
                issues.append("Missing value in main_metric")
                structural_match = False
            else:
                required_value_fields = ["operation", "entity"]
                for field in required_value_fields:
                    if field not in value:
                        issues.append(f"Missing {field} in main_metric.value")
                        structural_match = False
        
        return structural_match, issues
    
    async def test_single_question(self, question: str, expected_report: Dict[str, Any]) -> TestResult:
        """Test a single question against expected report."""
        self.logger.info(f"Testing question: {question}")
        
        start_time = time.time()
        response = await self.send_question_to_bot(question)
        execution_time = time.time() - start_time
        
        # Handle bot errors
        if "error" in response:
            return TestResult(
                question=question,
                expected_report=expected_report,
                actual_response=response,
                match_score=0.0,
                structural_match=False,
                metric_match=False,
                chart_match=False,
                issues=[f"Bot error: {response['error']}"],
                execution_time=execution_time,
                timestamp=datetime.now()
            )
        
        # Extract the actual report from bot response
        if "response" in response and isinstance(response["response"], str):
            # Parse JSON string response
            try:
                actual_report = json.loads(response["response"])
            except json.JSONDecodeError:
                actual_report = {"error": "Invalid JSON in response"}
        else:
            actual_report = response.get("report", response)  # Handle different response formats
        
        # Analyze structure
        structural_match, structural_issues = self.analyze_response_structure(actual_report)
        
        # Compare metrics
        metric_match, metric_issues = self.compare_metrics(expected_report, actual_report)
        
        # Compare chart structure
        chart_match, chart_issues = self.compare_chart_structure(expected_report, actual_report)
        
        # Calculate overall similarity
        match_score = self.calculate_json_similarity(expected_report, actual_report)
        
        # Combine all issues
        all_issues = structural_issues + metric_issues + chart_issues
        
        result = TestResult(
            question=question,
            expected_report=expected_report,
            actual_response=actual_report,
            match_score=match_score,
            structural_match=structural_match,
            metric_match=metric_match,
            chart_match=chart_match,
            issues=all_issues,
            execution_time=execution_time,
            timestamp=datetime.now()
        )
        
        self.logger.info(f"Test completed - Score: {match_score:.2f}, Issues: {len(all_issues)}")
        return result
    
    async def run_comprehensive_test(self, max_tests: Optional[int] = None) -> TestSummary:
        """Run comprehensive testing on all available questions."""
        self.logger.info("Starting comprehensive HR bot testing")
        start_time = datetime.now()
        
        # Collect all questions and expected reports
        test_cases = []
        
        # Add questions from the 50 complete reports
        for report_data in HR_ANALYTICS_REPORTS:
            expected_report = report_data["report"]
            for question in report_data["questions"]:
                test_cases.append((question, expected_report))
        
        # Optionally limit number of tests
        if max_tests:
            test_cases = test_cases[:max_tests]
        
        self.logger.info(f"Running {len(test_cases)} test cases")
        
        # Run tests
        for i, (question, expected_report) in enumerate(test_cases, 1):
            self.logger.info(f"Progress: {i}/{len(test_cases)}")
            
            try:
                result = await self.test_single_question(question, expected_report)
                self.test_results.append(result)
                
                # Add small delay to avoid overwhelming the bot
                await asyncio.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Test failed for question '{question}': {e}")
                # Create a failed test result
                failed_result = TestResult(
                    question=question,
                    expected_report=expected_report,
                    actual_response={"error": str(e)},
                    match_score=0.0,
                    structural_match=False,
                    metric_match=False,
                    chart_match=False,
                    issues=[f"Test execution error: {e}"],
                    execution_time=0.0,
                    timestamp=datetime.now()
                )
                self.test_results.append(failed_result)
        
        end_time = datetime.now()
        
        # Generate summary
        summary = self.generate_test_summary(start_time, end_time)
        self.logger.info(f"Testing completed. Passed: {summary.passed_tests}/{summary.total_tests}")
        
        return summary
    
    def generate_test_summary(self, start_time: datetime, end_time: datetime) -> TestSummary:
        """Generate comprehensive test summary."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.match_score > 0.8 and len(r.issues) == 0)
        failed_tests = total_tests - passed_tests
        
        average_score = sum(r.match_score for r in self.test_results) / total_tests if total_tests > 0 else 0
        average_execution_time = sum(r.execution_time for r in self.test_results) / total_tests if total_tests > 0 else 0
        
        # Aggregate issues
        issues_summary = {}
        for result in self.test_results:
            for issue in result.issues:
                # Categorize issues
                if "missing" in issue.lower():
                    category = "Missing Fields"
                elif "mismatch" in issue.lower():
                    category = "Field Mismatches"
                elif "error" in issue.lower():
                    category = "Bot Errors"
                else:
                    category = "Other Issues"
                
                issues_summary[category] = issues_summary.get(category, 0) + 1
        
        return TestSummary(
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            average_score=average_score,
            average_execution_time=average_execution_time,
            start_time=start_time,
            end_time=end_time,
            issues_summary=issues_summary
        )
    
    def save_detailed_report(self, filename: Optional[str] = None) -> str:
        """Save detailed test report to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"hr_bot_test_report_{timestamp}.json"
        
        # Prepare data for JSON serialization
        summary = self.generate_test_summary(
            self.test_results[0].timestamp if self.test_results else datetime.now(),
            self.test_results[-1].timestamp if self.test_results else datetime.now()
        )
        summary_dict = asdict(summary)
        # Convert datetime objects to strings
        summary_dict["start_time"] = summary.start_time.isoformat()
        summary_dict["end_time"] = summary.end_time.isoformat()
        
        report_data = {
            "test_summary": summary_dict,
            "test_results": []
        }
        
        for result in self.test_results:
            result_dict = asdict(result)
            # Convert datetime to string
            result_dict["timestamp"] = result.timestamp.isoformat()
            # Handle any other datetime objects in the summary
            if isinstance(result_dict.get("test_summary"), dict):
                summary = result_dict["test_summary"]
                if "start_time" in summary:
                    summary["start_time"] = summary["start_time"].isoformat() if hasattr(summary["start_time"], "isoformat") else str(summary["start_time"])
                if "end_time" in summary:
                    summary["end_time"] = summary["end_time"].isoformat() if hasattr(summary["end_time"], "isoformat") else str(summary["end_time"])
            report_data["test_results"].append(result_dict)
        
        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Detailed report saved to {filename}")
        return filename
    
    def generate_mismatch_analysis(self) -> Dict[str, Any]:
        """Generate detailed analysis of mismatches."""
        analysis = {
            "frequent_issues": {},
            "problematic_entities": {},
            "problematic_operations": {},
            "chart_issues": {},
            "low_scoring_questions": []
        }
        
        for result in self.test_results:
            # Track frequent issues
            for issue in result.issues:
                analysis["frequent_issues"][issue] = analysis["frequent_issues"].get(issue, 0) + 1
            
            # Track problematic entities
            expected_entity = result.expected_report.get("main_metric", {}).get("value", {}).get("entity")
            if expected_entity and result.match_score < 0.7:
                analysis["problematic_entities"][expected_entity] = analysis["problematic_entities"].get(expected_entity, 0) + 1
            
            # Track problematic operations
            expected_operation = result.expected_report.get("main_metric", {}).get("value", {}).get("operation")
            if expected_operation and result.match_score < 0.7:
                analysis["problematic_operations"][expected_operation] = analysis["problematic_operations"].get(expected_operation, 0) + 1
            
            # Track chart issues
            if not result.chart_match:
                chart_type = result.expected_report.get("chart", {}).get("chart_type", "unknown")
                analysis["chart_issues"][chart_type] = analysis["chart_issues"].get(chart_type, 0) + 1
            
            # Track low scoring questions
            if result.match_score < 0.5:
                analysis["low_scoring_questions"].append({
                    "question": result.question,
                    "score": result.match_score,
                    "issues": result.issues
                })
        
        return analysis
    
    def print_summary_report(self):
        """Print a human-readable summary report."""
        if not self.test_results:
            print("No test results available.")
            return
        
        summary = self.generate_test_summary(
            self.test_results[0].timestamp,
            self.test_results[-1].timestamp
        )
        
        print("\n" + "="*60)
        print("HR BOT TESTING SUMMARY REPORT")
        print("="*60)
        print(f"Total Tests: {summary.total_tests}")
        print(f"Passed Tests: {summary.passed_tests} ({summary.passed_tests/summary.total_tests*100:.1f}%)")
        print(f"Failed Tests: {summary.failed_tests} ({summary.failed_tests/summary.total_tests*100:.1f}%)")
        print(f"Average Match Score: {summary.average_score:.3f}")
        print(f"Average Execution Time: {summary.average_execution_time:.2f}s")
        print(f"Testing Duration: {summary.end_time - summary.start_time}")
        
        print("\nISSUES BREAKDOWN:")
        for category, count in summary.issues_summary.items():
            print(f"  {category}: {count}")
        
        # Detailed mismatch analysis
        analysis = self.generate_mismatch_analysis()
        
        print("\nMOST FREQUENT ISSUES:")
        for issue, count in sorted(analysis["frequent_issues"].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {issue}: {count} occurrences")
        
        print("\nPROBLEMATIC ENTITIES:")
        for entity, count in sorted(analysis["problematic_entities"].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {entity}: {count} failed tests")
        
        print("\nLOW SCORING QUESTIONS:")
        for item in analysis["low_scoring_questions"][:5]:
            print(f"  Score {item['score']:.2f}: {item['question'][:80]}...")

async def run_quick_test():
    """Run a quick test with a few questions."""
    print("Running quick HR bot test...")
    
    async with HRBotTester() as tester:
        # Test first 5 questions
        summary = await tester.run_comprehensive_test(max_tests=5)
        
        tester.print_summary_report()
        filename = tester.save_detailed_report()
        
        print(f"\nDetailed results saved to: {filename}")

async def run_full_test():
    """Run complete test suite."""
    print("Running comprehensive HR bot test...")
    
    async with HRBotTester() as tester:
        summary = await tester.run_comprehensive_test()
        
        tester.print_summary_report()
        filename = tester.save_detailed_report()
        
        print(f"\nDetailed results saved to: {filename}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="HR Analytics Bot Testing Suite")
    parser.add_argument("--quick", action="store_true", help="Run quick test with 5 questions")
    parser.add_argument("--full", action="store_true", help="Run full test suite")
    parser.add_argument("--url", default="http://localhost:8000", help="Bot URL")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds")
    
    args = parser.parse_args()
    
    if args.quick:
        asyncio.run(run_quick_test())
    elif args.full:
        asyncio.run(run_full_test())
    else:
        print("Please specify --quick or --full")
        print("Usage examples:")
        print("  python hr_bot_testing_suite.py --quick")
        print("  python hr_bot_testing_suite.py --full")
        print("  python hr_bot_testing_suite.py --full --url http://localhost:8000")