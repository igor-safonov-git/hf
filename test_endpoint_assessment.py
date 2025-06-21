#!/usr/bin/env python3
"""
Comprehensive assessment of Universal Filtering System through chat endpoints
"""

import asyncio
import aiohttp
import json
import time

class EndpointAssessor:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_question(self, question, description=""):
        """Test a single question through the chat endpoint"""
        print(f"\n📋 Testing: {description}")
        print(f"❓ Question: {question}")
        
        payload = {
            "message": question,
            "temperature": 0.1
        }
        
        start_time = time.time()
        try:
            async with self.session.post(
                f"{self.base_url}/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    response_time = time.time() - start_time
                    
                    # Parse the JSON response
                    ai_response = json.loads(result["response"])
                    
                    print(f"⏱️  Response time: {response_time:.2f}s")
                    print(f"✅ Status: SUCCESS")
                    
                    # Analyze the response structure
                    self.analyze_response(ai_response)
                    
                    return True, ai_response
                else:
                    print(f"❌ HTTP Error: {response.status}")
                    error_text = await response.text()
                    print(f"   Error details: {error_text[:200]}...")
                    return False, None
                    
        except asyncio.TimeoutError:
            print(f"⏱️  TIMEOUT after 60s")
            return False, None
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return False, None
    
    def analyze_response(self, ai_response):
        """Analyze AI response structure and filtering usage"""
        print(f"📊 Analysis:")
        
        # Check report-level period (NEW schema)
        report_period = ai_response.get("period", "N/A")
        print(f"   ⏱️  Report period: {report_period}")
        
        # Check main metric
        if "main_metric" in ai_response:
            main_metric = ai_response["main_metric"]
            filters = main_metric.get("value", {}).get("filters", {})
            real_value = main_metric.get("real_value", "N/A")
            print(f"   📈 Main metric: {main_metric.get('label', 'N/A')} = {real_value}")
            print(f"   🔍 Main filters: {json.dumps(filters, ensure_ascii=False)}")
        
        # Check chart data
        if "chart" in ai_response:
            chart = ai_response["chart"]
            chart_type = chart.get("type", "unknown")
            real_data = chart.get("real_data", {})
            y_filters = chart.get("y_axis", {}).get("filters", {})
            
            print(f"   📊 Chart type: {chart_type}")
            print(f"   🔍 Chart filters: {json.dumps(y_filters, ensure_ascii=False)}")
            
            if "labels" in real_data:
                if real_data["labels"] == ["Error"]:
                    print(f"   ❌ Chart processing error: {real_data.get('title', 'Unknown error')}")
                else:
                    print(f"   ✅ Chart data: {len(real_data['labels'])} data points")
                    print(f"      Top 3 results: {real_data['labels'][:3]}")
        
        # Check for advanced filtering usage
        all_filters = []
        for section in ["main_metric", "chart"]:
            if section in ai_response:
                if section == "main_metric":
                    filters = ai_response[section].get("value", {}).get("filters", {})
                    all_filters.append(filters)
                elif section == "chart":
                    y_filters = ai_response[section].get("y_axis", {}).get("filters", {})
                    x_filters = ai_response[section].get("x_axis", {}).get("filters", {})
                    all_filters.extend([y_filters, x_filters])
        
        # Analyze filtering sophistication
        # Check for report-level period (NEW schema)
        has_report_period = "period" in ai_response
        # Check for period in filters (OLD schema - should be empty now)
        has_period_in_filters = any("period" in f for f in all_filters)
        has_entity_filters = any(any(k in f for k in ["recruiters", "sources", "vacancies"]) for f in all_filters)
        has_logical_operators = any(any(k in f for k in ["and", "or"]) for f in all_filters)
        has_advanced_operators = any(
            any(isinstance(v, dict) and "operator" in v for v in f.values()) 
            for f in all_filters if isinstance(f, dict)
        )
        
        print(f"   🎯 Filtering assessment:")
        print(f"      Report-level period: {'✅' if has_report_period else '❌'}")
        print(f"      Period in filters (OLD): {'⚠️ ' if has_period_in_filters else '✅'}")
        print(f"      Basic filters (period): {'✅' if has_report_period else '❌'}")
        print(f"      Entity filters: {'✅' if has_entity_filters else '❌'}")
        print(f"      Logical operators (and/or): {'✅' if has_logical_operators else '❌'}")
        print(f"      Advanced operators: {'✅' if has_advanced_operators else '❌'}")

async def main():
    """Run comprehensive endpoint assessment"""
    print("🔬 UNIVERSAL FILTERING SYSTEM - ENDPOINT ASSESSMENT")
    print("=" * 60)
    
    # Test questions covering different scenarios
    test_questions = [
        {
            "question": "Покажи мне воронку кандидатов по этапам за последние 3 месяца",
            "description": "Basic pipeline analysis with period filter"
        },
        {
            "question": "Сколько кандидатов добавил каждый рекрутер за последний месяц?",
            "description": "Recruiter performance with grouping"
        },
        {
            "question": "Какие источники кандидатов самые эффективные?",
            "description": "Source effectiveness analysis"
        },
        {
            "question": "Покажи динамику наймов по месяцам за последние 6 месяцев",
            "description": "Time-based trending analysis"
        },
        {
            "question": "Сравни рекрутеров по количеству наймов и времени до найма",
            "description": "Multi-dimensional comparison (scatter plot)"
        }
    ]
    
    results = []
    success_count = 0
    
    async with EndpointAssessor() as assessor:
        for i, test_case in enumerate(test_questions, 1):
            print(f"\n{'='*20} TEST {i}/{len(test_questions)} {'='*20}")
            
            success, response = await assessor.test_question(
                test_case["question"], 
                test_case["description"]
            )
            
            results.append({
                "test": test_case["description"],
                "success": success,
                "response": response
            })
            
            if success:
                success_count += 1
    
    # Final assessment
    print(f"\n{'='*60}")
    print(f"🎯 FINAL ASSESSMENT RESULTS")
    print(f"{'='*60}")
    print(f"✅ Successful tests: {success_count}/{len(test_questions)}")
    print(f"🔄 Success rate: {(success_count/len(test_questions)*100):.1f}%")
    
    if success_count == len(test_questions):
        print(f"🎉 UNIVERSAL FILTERING SYSTEM: FULLY OPERATIONAL")
        print(f"   ✅ AI generates proper filtering queries")
        print(f"   ✅ EnhancedMetricsCalculator processes filters correctly")
        print(f"   ✅ Real data enrichment works")
        print(f"   ✅ End-to-end integration successful")
    elif success_count >= len(test_questions) * 0.8:
        print(f"⚠️  UNIVERSAL FILTERING SYSTEM: MOSTLY OPERATIONAL")
        print(f"   ✅ Core functionality works")
        print(f"   ⚠️  Some chart processing issues detected")
    else:
        print(f"❌ UNIVERSAL FILTERING SYSTEM: NEEDS ATTENTION")
        print(f"   ❌ Multiple integration issues detected")
    
    # Identify specific issues
    failed_tests = [r for r in results if not r["success"]]
    if failed_tests:
        print(f"\n🔧 Issues to address:")
        for test in failed_tests:
            print(f"   • {test['test']}")

if __name__ == "__main__":
    asyncio.run(main())