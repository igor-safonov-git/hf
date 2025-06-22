#!/usr/bin/env python3
"""
Performance test for restructured metrics_filter system
Ensures processing maintains <0.5s response time
"""

import asyncio
import time
import statistics
from chart_data_processor import process_chart_data, validate_report_json
from huntflow_local_client import HuntflowLocalClient

# Performance test scenarios
performance_scenarios = [
    {
        "name": "Simple Period Query",
        "report": {
            "report_title": "Simple Performance Test",
            "metrics_filter": {"period": "3 month"},
            "main_metric": {"label": "Hires", "value": {"operation": "count", "entity": "hires"}},
            "secondary_metrics": [
                {"label": "Applicants", "value": {"operation": "count", "entity": "applicants"}},
                {"label": "Vacancies", "value": {"operation": "count", "entity": "vacancies"}}
            ],
            "chart": {
                "label": "Pipeline", "type": "bar", "x_label": "Stages", "y_label": "Count",
                "x_axis": {"operation": "count", "entity": "applicants", "group_by": {"field": "stages"}},
                "y_axis": {"operation": "count", "entity": "applicants", "group_by": {"field": "stages"}}
            }
        }
    },
    {
        "name": "Specific Recruiter Query",
        "report": {
            "report_title": "Recruiter Performance Test",
            "metrics_filter": {"period": "6 month", "recruiters": "55498"},
            "main_metric": {"label": "Hires", "value": {"operation": "count", "entity": "hires"}},
            "secondary_metrics": [
                {"label": "Applicants", "value": {"operation": "count", "entity": "applicants"}},
                {"label": "Time to Hire", "value": {"operation": "avg", "entity": "hires", "value_field": "time_to_hire"}}
            ],
            "chart": {
                "label": "Monthly Trend", "type": "line", "x_label": "Month", "y_label": "Hires",
                "x_axis": {"operation": "count", "entity": "hires", "group_by": {"field": "month"}},
                "y_axis": {"operation": "count", "entity": "hires", "group_by": {"field": "month"}}
            }
        }
    },
    {
        "name": "Complex Division Query",
        "report": {
            "report_title": "Division Performance Test",
            "metrics_filter": {"period": "1 month", "divisions": "101"},
            "main_metric": {"label": "Division Hires", "value": {"operation": "count", "entity": "hires"}},
            "secondary_metrics": [
                {"label": "Division Applicants", "value": {"operation": "count", "entity": "applicants"}},
                {"label": "Open Vacancies", "value": {"operation": "count", "entity": "vacancies"}}
            ],
            "chart": {
                "label": "Source Analysis", "type": "bar", "x_label": "Sources", "y_label": "Applicants", 
                "x_axis": {"operation": "count", "entity": "applicants", "group_by": {"field": "sources"}},
                "y_axis": {"operation": "count", "entity": "applicants", "group_by": {"field": "sources"}}
            }
        }
    }
]

async def run_performance_test():
    """Run performance test for restructured metrics system"""
    print("🚀 PERFORMANCE TEST - Restructured Metrics Filter System\n")
    print("=" * 60)
    
    client = HuntflowLocalClient()
    all_times = []
    
    for round_num in range(1, 4):  # 3 rounds for statistical accuracy
        print(f"\n📊 Performance Round {round_num}/3")
        round_times = []
        
        for i, scenario in enumerate(performance_scenarios, 1):
            print(f"   🔄 Test {i}/3: {scenario['name']}")
            
            # Multiple runs per scenario for accuracy
            scenario_times = []
            for run in range(3):
                start_time = time.time()
                
                try:
                    # Schema validation
                    validate_report_json(scenario['report'])
                    
                    # Processing
                    await process_chart_data(scenario['report'].copy(), client)
                    
                    end_time = time.time()
                    processing_time = end_time - start_time
                    scenario_times.append(processing_time)
                    
                except Exception as e:
                    print(f"      ❌ Run {run+1} failed: {e}")
                    scenario_times.append(999)  # Mark as failure
            
            # Calculate scenario average
            avg_time = statistics.mean(scenario_times)
            round_times.append(avg_time)
            
            status = "✅" if avg_time < 0.5 else "⚠️"
            print(f"      {status} Average: {avg_time:.3f}s")
        
        # Calculate round average
        round_avg = statistics.mean(round_times)
        all_times.extend(round_times)
        
        print(f"   📈 Round {round_num} average: {round_avg:.3f}s")
    
    # Final analysis
    print("\n" + "=" * 60)
    print("📊 PERFORMANCE TEST RESULTS")
    print("=" * 60)
    
    overall_avg = statistics.mean(all_times)
    max_time = max(all_times)
    min_time = min(all_times)
    
    print(f"⏱️  Overall average: {overall_avg:.3f}s")
    print(f"🔺 Maximum time: {max_time:.3f}s") 
    print(f"🔻 Minimum time: {min_time:.3f}s")
    
    # Performance assessment
    target_time = 0.5
    fast_queries = len([t for t in all_times if t < target_time])
    total_queries = len(all_times)
    
    print(f"🎯 Target compliance: {fast_queries}/{total_queries} queries under {target_time}s")
    print(f"📈 Success rate: {(fast_queries/total_queries)*100:.1f}%")
    
    if overall_avg < target_time:
        print(f"\n🎉 PERFORMANCE TEST PASSED!")
        print(f"✅ Average {overall_avg:.3f}s meets <{target_time}s requirement")
        return True
    else:
        print(f"\n⚠️  PERFORMANCE WARNING!")
        print(f"❌ Average {overall_avg:.3f}s exceeds {target_time}s target")
        return False

if __name__ == "__main__":
    async def main():
        success = await run_performance_test()
        
        if success:
            print("\n✅ PERFORMANCE TEST PASSED!")
            exit(0)
        else:
            print("\n❌ PERFORMANCE TEST FAILED!")
            exit(1)
    
    asyncio.run(main())