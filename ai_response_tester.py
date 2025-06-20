"""
AI Response Testing Framework
Tests AI model responses against expected JSON structures
Focuses on metrics similarity, not calculated values
"""

import json
import asyncio
import aiohttp
import time
import logging
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from test_reports_with_questions import save_sample_reports

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Test result for a single question"""
    question_id: str
    question: str
    expected_structure: Dict[str, Any]
    ai_response: Dict[str, Any]
    similarity_score: float
    errors: List[str]
    response_time: float

class JSONSimilarityChecker:
    """Checks similarity between expected and actual JSON structures"""
    
    def __init__(self):
        self.weight_main_metric = 0.4
        self.weight_secondary_metrics = 0.4
        self.weight_chart = 0.2
    
    def calculate_similarity(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        Calculate similarity score between expected and actual JSON structures
        Focuses on structure, not values
        Returns: (similarity_score, list_of_errors)
        """
        errors = []
        scores = []
        
        # Check main metric structure
        main_score, main_errors = self._check_main_metric(
            expected.get('main_metric', {}), 
            actual.get('main_metric', {})
        )
        scores.append(main_score * self.weight_main_metric)
        errors.extend([f"Main metric: {e}" for e in main_errors])
        
        # Check secondary metrics structure  
        secondary_score, secondary_errors = self._check_secondary_metrics(
            expected.get('secondary_metrics', []),
            actual.get('secondary_metrics', [])
        )
        scores.append(secondary_score * self.weight_secondary_metrics)
        errors.extend([f"Secondary metrics: {e}" for e in secondary_errors])
        
        # Check chart structure
        chart_score, chart_errors = self._check_chart(
            expected.get('chart', {}),
            actual.get('chart', {})
        )
        scores.append(chart_score * self.weight_chart)
        errors.extend([f"Chart: {e}" for e in chart_errors])
        
        total_score = sum(scores)
        return total_score, errors
    
    def _check_main_metric(self, expected: Dict, actual: Dict) -> Tuple[float, List[str]]:
        """Check main metric structure similarity"""
        errors = []
        score = 0.0
        
        if not actual:
            return 0.0, ["Missing main_metric"]
        
        # Check if value structure exists
        if 'value' not in actual:
            errors.append("Missing 'value' field")
            return 0.0, errors
        
        expected_value = expected.get('value', {})
        actual_value = actual.get('value', {})
        
        # Check critical fields
        critical_fields = ['operation', 'entity', 'filters']
        field_scores = []
        
        for field in critical_fields:
            if field in expected_value and field in actual_value:
                # For entity and operation, check exact match
                if field in ['entity', 'operation']:
                    if expected_value[field] == actual_value[field]:
                        field_scores.append(1.0)
                    else:
                        field_scores.append(0.0)
                        errors.append(f"Entity/operation mismatch: expected {expected_value[field]}, got {actual_value[field]}")
                # For filters, check structure similarity
                elif field == 'filters':
                    filter_score = self._check_filters_similarity(
                        expected_value[field], actual_value[field]
                    )
                    field_scores.append(filter_score)
                    if filter_score < 0.5:
                        errors.append("Filter structure differs significantly")
            else:
                field_scores.append(0.0)
                errors.append(f"Missing field: {field}")
        
        score = sum(field_scores) / len(field_scores) if field_scores else 0.0
        return score, errors
    
    def _check_secondary_metrics(self, expected: List, actual: List) -> Tuple[float, List[str]]:
        """Check secondary metrics structure similarity"""
        errors = []
        
        if not actual:
            return 0.0, ["Missing secondary_metrics"]
        
        if len(actual) != 2:
            errors.append(f"Expected 2 secondary metrics, got {len(actual)}")
            return 0.0, errors
        
        # Check each secondary metric
        scores = []
        for i, (exp_metric, act_metric) in enumerate(zip(expected[:2], actual[:2])):
            metric_score, metric_errors = self._check_main_metric(exp_metric, act_metric)
            scores.append(metric_score)
            errors.extend([f"Metric {i+1}: {e}" for e in metric_errors])
        
        total_score = sum(scores) / len(scores) if scores else 0.0
        return total_score, errors
    
    def _check_chart(self, expected: Dict, actual: Dict) -> Tuple[float, List[str]]:
        """Check chart structure similarity"""
        errors = []
        
        if not actual:
            return 0.0, ["Missing chart"]
        
        # Check chart type
        score = 0.0
        if 'type' in expected and 'type' in actual:
            if expected['type'] == actual['type']:
                score += 0.3
            else:
                errors.append(f"Chart type mismatch: expected {expected['type']}, got {actual['type']}")
        
        # Check x_axis and y_axis structure
        for axis in ['x_axis', 'y_axis']:
            if axis in expected and axis in actual:
                axis_score, axis_errors = self._check_main_metric({'value': expected[axis]}, {'value': actual[axis]})
                score += axis_score * 0.35  # 0.35 for each axis
                errors.extend([f"{axis}: {e}" for e in axis_errors])
            else:
                errors.append(f"Missing {axis}")
        
        return score, errors
    
    def _check_filters_similarity(self, expected: Dict, actual: Dict) -> float:
        """Check if filter structures are similar (not exact values)"""
        if not expected and not actual:
            return 1.0
        
        if not actual:
            return 0.0
        
        # Check if key filter types are present
        expected_keys = set(expected.keys())
        actual_keys = set(actual.keys())
        
        # Period filter is critical
        period_score = 1.0 if 'period' in actual else 0.0
        
        # Entity filters (recruiters, sources, etc.)
        entity_filters = {'recruiters', 'sources', 'vacancies', 'divisions', 'stages', 'hiring_managers'}
        expected_entities = expected_keys & entity_filters
        actual_entities = actual_keys & entity_filters
        
        if expected_entities and actual_entities:
            entity_score = len(expected_entities & actual_entities) / len(expected_entities)
        elif not expected_entities and not actual_entities:
            entity_score = 1.0
        else:
            entity_score = 0.0
        
        # Weighted average
        total_score = (period_score * 0.4) + (entity_score * 0.6)
        return total_score

class AIResponseTester:
    """Main testing framework for AI responses"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.similarity_checker = JSONSimilarityChecker()
        self.results: List[TestResult] = []
    
    async def run_test_suite(self, max_questions: int = 50) -> List[TestResult]:
        """Run the complete test suite"""
        logger.info(f"Starting AI response test suite (max {max_questions} questions)")
        
        # Load sample reports
        reports = save_sample_reports()
        logger.info(f"Loaded {len(reports)} sample reports")
        
        # Collect all questions with their expected structures
        test_cases = []
        for report in reports[:max_questions//3]:  # Limit reports to stay within question limit
            expected_structure = report['report_json']
            for i, question in enumerate(report['questions']):
                test_cases.append({
                    'question_id': f"{report['id']}-{i+1}",
                    'question': question,
                    'expected_structure': expected_structure,
                    'category': report['category']
                })
        
        # Limit to max_questions
        test_cases = test_cases[:max_questions]
        logger.info(f"Running {len(test_cases)} test cases")
        
        # Run tests with controlled concurrency
        semaphore = asyncio.Semaphore(3)  # Max 3 concurrent requests
        tasks = [self._test_single_question(semaphore, case) for case in test_cases]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and collect valid results
        valid_results = [r for r in results if isinstance(r, TestResult)]
        self.results = valid_results
        
        logger.info(f"Test suite completed. {len(valid_results)} valid results.")
        return valid_results
    
    async def _test_single_question(self, semaphore: asyncio.Semaphore, test_case: Dict) -> TestResult:
        """Test a single question against the AI"""
        async with semaphore:
            start_time = time.time()
            
            try:
                # Send question to AI
                async with aiohttp.ClientSession() as session:
                    payload = {"message": test_case['question']}
                    
                    async with session.post(
                        f"{self.base_url}/chat",
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status != 200:
                            raise Exception(f"HTTP {response.status}: {await response.text()}")
                        
                        response_data = await response.json()
                        ai_response = json.loads(response_data['response'])
                
                response_time = time.time() - start_time
                
                # Calculate similarity
                similarity_score, errors = self.similarity_checker.calculate_similarity(
                    test_case['expected_structure'], 
                    ai_response
                )
                
                return TestResult(
                    question_id=test_case['question_id'],
                    question=test_case['question'],
                    expected_structure=test_case['expected_structure'],
                    ai_response=ai_response,
                    similarity_score=similarity_score,
                    errors=errors,
                    response_time=response_time
                )
                
            except Exception as e:
                logger.error(f"Error testing question {test_case['question_id']}: {e}")
                return TestResult(
                    question_id=test_case['question_id'],
                    question=test_case['question'],
                    expected_structure=test_case['expected_structure'],
                    ai_response={},
                    similarity_score=0.0,
                    errors=[str(e)],
                    response_time=time.time() - start_time
                )
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate test report with statistics"""
        if not self.results:
            return {"error": "No test results available"}
        
        # Calculate statistics
        scores = [r.similarity_score for r in self.results]
        response_times = [r.response_time for r in self.results]
        
        # Success criteria
        high_quality = [r for r in self.results if r.similarity_score >= 0.8]
        medium_quality = [r for r in self.results if 0.5 <= r.similarity_score < 0.8]
        low_quality = [r for r in self.results if r.similarity_score < 0.5]
        
        # Common errors
        all_errors = []
        for result in self.results:
            all_errors.extend(result.errors)
        
        error_counts = {}
        for error in all_errors:
            error_counts[error] = error_counts.get(error, 0) + 1
        
        top_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        report = {
            "summary": {
                "total_tests": len(self.results),
                "avg_similarity_score": sum(scores) / len(scores),
                "avg_response_time": sum(response_times) / len(response_times),
                "high_quality_count": len(high_quality),
                "medium_quality_count": len(medium_quality),
                "low_quality_count": len(low_quality),
                "success_rate": len(high_quality) / len(self.results) * 100
            },
            "quality_distribution": {
                "high_quality": [r.question_id for r in high_quality],
                "medium_quality": [r.question_id for r in medium_quality],
                "low_quality": [r.question_id for r in low_quality]
            },
            "top_errors": top_errors,
            "detailed_results": [
                {
                    "question_id": r.question_id,
                    "question": r.question[:100] + "..." if len(r.question) > 100 else r.question,
                    "similarity_score": r.similarity_score,
                    "response_time": r.response_time,
                    "error_count": len(r.errors)
                }
                for r in sorted(self.results, key=lambda x: x.similarity_score, reverse=True)
            ]
        }
        
        return report

async def main():
    """Run the test suite"""
    tester = AIResponseTester()
    
    # Run tests
    results = await tester.run_test_suite(max_questions=105)  # Further expanded to 105 questions
    
    # Generate and save report
    report = tester.generate_report()
    
    # Save detailed results
    with open('/home/igor/hf/test_results.json', 'w', encoding='utf-8') as f:
        json.dump({
            "report": report,
            "detailed_results": [
                {
                    "question_id": r.question_id,
                    "question": r.question,
                    "similarity_score": r.similarity_score,
                    "response_time": r.response_time,
                    "errors": r.errors,
                    "expected_structure": r.expected_structure,
                    "ai_response": r.ai_response
                }
                for r in results
            ]
        }, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("\n" + "="*60)
    print("AI RESPONSE TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"Average Similarity Score: {report['summary']['avg_similarity_score']:.3f}")
    print(f"Success Rate (≥80%): {report['summary']['success_rate']:.1f}%")
    print(f"Average Response Time: {report['summary']['avg_response_time']:.2f}s")
    print(f"\nQuality Distribution:")
    print(f"  High Quality (≥80%): {report['summary']['high_quality_count']}")
    print(f"  Medium Quality (50-80%): {report['summary']['medium_quality_count']}")
    print(f"  Low Quality (<50%): {report['summary']['low_quality_count']}")
    print(f"\nTop Errors:")
    for error, count in report['top_errors'][:5]:
        print(f"  {error}: {count} times")
    print("\nDetailed results saved to test_results.json")

if __name__ == "__main__":
    asyncio.run(main())