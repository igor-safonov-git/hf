"""
Quick test to show what the enhanced real data content test checks
"""

import asyncio
import json
import aiohttp

async def quick_content_test():
    """Test one question to show content validation logic"""
    
    question = "Сколько у нас сейчас кандидатов в воронке?"
    
    print("🔍 Quick Real Data Content Check")
    print(f"Question: {question}")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        payload = {"message": question, "use_local_cache": True}
        
        try:
            async with session.post("http://localhost:8001/chat", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    if "response" in result:
                        parsed = json.loads(result["response"])
                        
                        print("📊 Raw Response Structure:")
                        print(f"  Main metric: {parsed.get('main_metric', {}).get('real_value', 'MISSING')}")
                        
                        secondary = parsed.get('secondary_metrics', [])
                        print(f"  Secondary metrics count: {len(secondary)}")
                        for i, metric in enumerate(secondary):
                            value = metric.get('real_value', 'MISSING')
                            print(f"    [{i}]: {value}")
                        
                        chart = parsed.get('chart', {})
                        real_data = chart.get('real_data', 'MISSING')
                        if isinstance(real_data, list):
                            print(f"  Chart real_data: {len(real_data)} items")
                            if real_data:
                                print(f"    Sample: {real_data[0] if real_data else 'Empty'}")
                        else:
                            print(f"  Chart real_data: {real_data}")
                        
                        # Content Quality Check
                        print("\n✅ Content Quality Analysis:")
                        
                        # Main metric check
                        main_value = parsed.get('main_metric', {}).get('real_value')
                        main_ok = main_value is not None and main_value != "" and main_value != 0
                        print(f"  Main metric has content: {'✅' if main_ok else '❌'} ({main_value})")
                        
                        # Secondary metrics check
                        secondary_count = 0
                        for metric in secondary:
                            value = metric.get('real_value')
                            if value is not None and value != "" and value != 0:
                                secondary_count += 1
                        
                        secondary_ok = secondary_count > 0
                        print(f"  Secondary metrics have content: {'✅' if secondary_ok else '❌'} ({secondary_count}/{len(secondary)})")
                        
                        # Chart data check - handle both formats
                        chart_ok = False
                        data_points = 0
                        
                        if isinstance(real_data, list) and len(real_data) > 0:
                            # List format
                            for point in real_data:
                                if isinstance(point, dict) and len(point) > 0:
                                    has_values = any(
                                        v is not None and v != "" and v != 0 
                                        for v in point.values() 
                                        if not isinstance(v, str) or v.strip()
                                    )
                                    if has_values:
                                        data_points += 1
                            chart_ok = data_points > 0
                            
                        elif isinstance(real_data, dict):
                            # Dict format
                            labels = real_data.get('labels', [])
                            values = real_data.get('values', [])
                            
                            if len(labels) > 0 and len(values) > 0:
                                meaningful_values = [v for v in values if v is not None and v != "" and v != 0]
                                data_points = len(meaningful_values)
                                chart_ok = data_points > 0
                        
                        print(f"  Chart has meaningful data: {'✅' if chart_ok else '❌'} ({data_points} data points)")
                        
                        # Overall score
                        checks = [main_ok, secondary_ok, chart_ok]
                        score = sum(checks) / len(checks)
                        print(f"\n🎯 Content Quality Score: {score:.2f}")
                        
                        if score == 1.0:
                            print("🎉 PERFECT CONTENT QUALITY!")
                        elif score >= 0.8:
                            print("✅ Good content quality")
                        else:
                            print("⚠️ Needs improvement")
                        
                else:
                    print(f"❌ HTTP Error: {response.status}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(quick_content_test())