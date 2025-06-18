"""
Test the specific source question that was failing
"""

import asyncio
import json
import aiohttp

async def test_source_question():
    """Test the source question that was failing"""
    
    question = "Откуда приходят наши кандидаты?"
    
    print("🔍 Testing Fixed Source Question")
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
                        
                        print("📊 Response Analysis:")
                        
                        # Main metric
                        main_value = parsed.get('main_metric', {}).get('real_value')
                        print(f"Main metric real_value: {main_value}")
                        
                        # Chart data
                        chart = parsed.get('chart', {})
                        real_data = chart.get('real_data', {})
                        if isinstance(real_data, dict):
                            labels = real_data.get('labels', [])
                            values = real_data.get('values', [])
                            print(f"Chart labels: {labels}")
                            print(f"Chart values: {values}")
                            print(f"Chart data points: {len(values) if values else 0}")
                        
                        # Entity check
                        entity = parsed.get('main_metric', {}).get('value', {}).get('entity', '')
                        operation = parsed.get('main_metric', {}).get('value', {}).get('operation', '')
                        print(f"Entity: {entity}")
                        print(f"Operation: {operation}")
                        
                        # Overall assessment
                        main_ok = main_value is not None and main_value != 0
                        chart_ok = isinstance(real_data, dict) and len(real_data.get('values', [])) > 0
                        
                        print(f"\n✅ Assessment:")
                        print(f"Main metric has content: {'✅' if main_ok else '❌'}")
                        print(f"Chart has content: {'✅' if chart_ok else '❌'}")
                        print(f"Entity correct: {'✅' if entity == 'applicants_by_source' else '❌'}")
                        
                        if main_ok and chart_ok and entity == 'applicants_by_source':
                            print("🎉 SOURCE QUESTION FIXED!")
                        else:
                            print("⚠️ Still needs work")
                        
                else:
                    print(f"❌ HTTP Error: {response.status}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_source_question())