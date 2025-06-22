#!/usr/bin/env python3
"""Test script for table chart functionality"""

import asyncio
import aiohttp
import json
import time

# Test queries designed to trigger table chart type
TABLE_TEST_QUERIES = [
    "Покажи всех рекрутеров",
    "Список рекрутеров с их показателями",
    "Какие вакансии открыты?",
    "Покажи источники кандидатов",
    "Кто из рекрутеров нанял больше всех?",
    "Список всех источников",
    "Какие у нас есть рекрутеры?"
]

async def test_chat_endpoint(session, query):
    """Test the chat endpoint with a query"""
    url = "http://localhost:8000/chat"
    
    try:
        start_time = time.time()
        async with session.post(url, json={"message": query}) as response:
            elapsed = time.time() - start_time
            
            if response.status == 200:
                data = await response.json()
                
                # Check if response contains table chart
                chart_type = data.get('report_json', {}).get('chart', {}).get('type', 'unknown')
                has_table_data = bool(data.get('report_json', {}).get('chart', {}).get('real_data', {}).get('columns'))
                
                print(f"\n{'='*80}")
                print(f"Query: {query}")
                print(f"Response time: {elapsed:.2f}s")
                print(f"Chart type: {chart_type}")
                print(f"Has table data: {has_table_data}")
                
                if chart_type == 'table' and has_table_data:
                    table_data = data['report_json']['chart']['real_data']
                    print(f"Columns: {[col['label'] for col in table_data.get('columns', [])]}")
                    print(f"Row count: {len(table_data.get('rows', []))}")
                    
                    # Show first 3 rows
                    rows = table_data.get('rows', [])
                    if rows:
                        print("\nFirst 3 rows:")
                        for i, row in enumerate(rows[:3]):
                            print(f"  {i+1}. {row.get('name', 'N/A')} - Count: {row.get('count', 0)}, "
                                  f"Percentage: {row.get('percentage', 0):.1f}%")
                
                return {
                    'query': query,
                    'success': True,
                    'chart_type': chart_type,
                    'is_table': chart_type == 'table',
                    'has_table_data': has_table_data,
                    'response_time': elapsed
                }
            else:
                print(f"\nError for '{query}': Status {response.status}")
                error_text = await response.text()
                print(f"Error details: {error_text[:200]}")
                return {
                    'query': query,
                    'success': False,
                    'error': f"Status {response.status}",
                    'response_time': elapsed
                }
                
    except Exception as e:
        print(f"\nException for '{query}': {str(e)}")
        return {
            'query': query,
            'success': False,
            'error': str(e),
            'response_time': 0
        }

async def run_tests():
    """Run all test queries"""
    print("Testing Table Chart Implementation")
    print("="*80)
    
    # Wait for server to be ready
    print("Waiting for server to be ready...")
    await asyncio.sleep(2)
    
    async with aiohttp.ClientSession() as session:
        # Run tests sequentially to avoid overwhelming the server
        results = []
        for query in TABLE_TEST_QUERIES:
            result = await test_chat_endpoint(session, query)
            results.append(result)
            await asyncio.sleep(1)  # Small delay between requests
        
        # Summary
        print(f"\n{'='*80}")
        print("SUMMARY")
        print(f"{'='*80}")
        
        successful = [r for r in results if r.get('success', False)]
        table_charts = [r for r in successful if r.get('is_table', False)]
        
        print(f"Total queries: {len(results)}")
        print(f"Successful: {len(successful)}")
        print(f"Table charts generated: {len(table_charts)}")
        print(f"Success rate: {len(successful)/len(results)*100:.1f}%")
        print(f"Table chart rate: {len(table_charts)/len(successful)*100:.1f}% of successful")
        
        print("\nTable chart queries:")
        for r in table_charts:
            print(f"  ✓ {r['query']}")
        
        print("\nNon-table responses:")
        for r in successful:
            if not r.get('is_table'):
                print(f"  • {r['query']} -> {r['chart_type']}")

if __name__ == "__main__":
    asyncio.run(run_tests())