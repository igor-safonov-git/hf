#!/usr/bin/env python3
"""Simplified final performance analysis"""

import asyncio
import time
import statistics
from enhanced_metrics_calculator import EnhancedMetricsCalculator
from huntflow_local_client import HuntflowLocalClient
from unittest.mock import Mock

async def main():
    """Performance analysis for universal filtering system"""
    
    print("=== Universal Filtering System - Performance Analysis ===\n")
    
    # Initialize calculator
    client = HuntflowLocalClient()
    calculator = EnhancedMetricsCalculator(client, Mock())
    
    benchmarks = []
    
    print("1. Core Performance Tests")
    print("-" * 40)
    
    # Test 1: Baseline
    start_time = time.time()
    all_applicants = await calculator.get_applicants()
    baseline_time = time.time() - start_time
    print(f"  Baseline: {len(all_applicants)} applicants in {baseline_time:.4f}s")
    benchmarks.append(baseline_time)
    
    # Test 2: Period filter
    start_time = time.time()
    period_result = await calculator.get_applicants({"period": "3 month"})
    period_time = time.time() - start_time
    print(f"  Period filter: {len(period_result)} applicants in {period_time:.4f}s")
    benchmarks.append(period_time)
    
    # Test 3: Advanced operators
    start_time = time.time()
    advanced_result = await calculator.get_applicants({
        "sources": {"operator": "in", "value": ["linkedin", "hh"]}
    })
    advanced_time = time.time() - start_time
    print(f"  Advanced operators: {len(advanced_result)} applicants in {advanced_time:.4f}s")
    benchmarks.append(advanced_time)
    
    # Test 4: Logical AND
    start_time = time.time()
    and_result = await calculator.get_applicants({
        "and": [
            {"period": "6 month"},
            {"recruiters": "12345"}
        ]
    })
    and_time = time.time() - start_time
    print(f"  AND logic: {len(and_result)} applicants in {and_time:.4f}s")
    benchmarks.append(and_time)
    
    # Test 5: Nested logic
    start_time = time.time()
    nested_result = await calculator.get_applicants({
        "and": [
            {"period": "6 month"},
            {"or": [{"recruiters": "12345"}, {"sources": "linkedin"}]}
        ]
    })
    nested_time = time.time() - start_time
    print(f"  Nested logic: {len(nested_result)} applicants in {nested_time:.4f}s")
    benchmarks.append(nested_time)
    
    print("\\n2. Multi-Entity Performance")
    print("-" * 40)
    
    # Test different entities
    entities = [
        ("Vacancies", lambda: calculator.get_vacancies({"period": "3 month"})),
        ("Hires", lambda: calculator.get_hires({"period": "3 month"})),
        ("Recruiters", lambda: calculator.get_recruiters())
    ]
    
    for name, func in entities:
        start_time = time.time()
        result = await func()
        entity_time = time.time() - start_time
        print(f"  {name}: {len(result)} items in {entity_time:.4f}s")
        benchmarks.append(entity_time)
    
    print("\\n3. Performance Summary")
    print("=" * 50)
    
    avg_time = statistics.mean(benchmarks)
    max_time = max(benchmarks)
    min_time = min(benchmarks)
    
    print(f"  Tests performed: {len(benchmarks)}")
    print(f"  Average time: {avg_time:.4f}s")
    print(f"  Fastest: {min_time:.4f}s")
    print(f"  Slowest: {max_time:.4f}s")
    print(f"  Processing rate: {len(all_applicants) / avg_time:.0f} items/second")
    
    # Success criteria
    target_time = 2.0
    all_under_target = max_time < target_time
    
    print("\\n4. Success Criteria Assessment")
    print("-" * 40)
    print(f"  Target: <{target_time}s per operation")
    print(f"  Performance: {'✅ PASS' if all_under_target else '❌ FAIL'}")
    print(f"  All operations: {max_time:.4f}s (under target: {all_under_target})")
    
    if all_under_target:
        print("\\n🎉 PERFORMANCE VALIDATION SUCCESSFUL")
        print("   Universal filtering system meets all performance requirements")
    else:
        print("\\n⚠️  Performance issues detected")
    
    return all_under_target

if __name__ == "__main__":
    asyncio.run(main())