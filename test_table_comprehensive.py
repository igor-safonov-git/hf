#!/usr/bin/env python3
"""Comprehensive test for table chart implementation - full pipeline test"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Any

class TableChartTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        
    async def test_query(self, session: aiohttp.ClientSession, query: str, expected_type: str = None) -> Dict[str, Any]:
        """Test a single query and validate response"""
        url = f"{self.base_url}/chat"
        
        try:
            start_time = time.time()
            async with session.post(url, json={"message": query}) as response:
                elapsed = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    report = data.get('report_json', {})
                    chart = report.get('chart', {})
                    
                    # Extract key information
                    chart_type = chart.get('type', 'unknown')
                    real_data = chart.get('real_data', {})
                    
                    # Validate table-specific data
                    is_table = chart_type == 'table'
                    has_columns = bool(real_data.get('columns'))
                    has_rows = bool(real_data.get('rows'))
                    row_count = len(real_data.get('rows', []))
                    
                    # Check if table data is properly formatted
                    table_valid = False
                    if is_table and has_columns and has_rows:
                        # Check if rows have the expected keys from columns
                        columns = real_data.get('columns', [])
                        rows = real_data.get('rows', [])
                        if rows and columns:
                            column_keys = {col['key'] for col in columns}
                            row_keys = set(rows[0].keys()) if rows else set()
                            table_valid = bool(column_keys & row_keys)
                    
                    result = {
                        'query': query,
                        'success': True,
                        'chart_type': chart_type,
                        'expected_type': expected_type,
                        'type_match': chart_type == expected_type if expected_type else None,
                        'is_table': is_table,
                        'has_columns': has_columns,
                        'has_rows': has_rows,
                        'row_count': row_count,
                        'table_valid': table_valid,
                        'response_time': elapsed,
                        'report_title': report.get('report_title', ''),
                        'columns': [col['label'] for col in real_data.get('columns', [])] if is_table else None,
                        'sample_data': real_data.get('rows', [])[:2] if is_table else None
                    }
                    
                    return result
                else:
                    error_text = await response.text()
                    return {
                        'query': query,
                        'success': False,
                        'error': f"Status {response.status}: {error_text[:100]}",
                        'response_time': elapsed
                    }
                    
        except Exception as e:
            return {
                'query': query,
                'success': False,
                'error': str(e),
                'response_time': 0
            }
    
    def print_result(self, result: Dict[str, Any]):
        """Print detailed result for a single test"""
        print(f"\n{'='*80}")
        print(f"Query: {result['query']}")
        print(f"Status: {'✓ Success' if result['success'] else '✗ Failed'}")
        
        if result['success']:
            print(f"Chart Type: {result['chart_type']}")
            if result['expected_type']:
                match_icon = '✓' if result['type_match'] else '✗'
                print(f"Expected: {result['expected_type']} {match_icon}")
            
            if result['is_table']:
                print(f"Table Valid: {'✓' if result['table_valid'] else '✗'}")
                print(f"Rows: {result['row_count']}")
                print(f"Columns: {', '.join(result['columns'] or [])}")
                
                if result['sample_data']:
                    print("Sample Data:")
                    for i, row in enumerate(result['sample_data']):
                        print(f"  {i+1}. {row.get('name', 'N/A')}: "
                              f"Count={row.get('count', 0)}, "
                              f"Percentage={row.get('percentage', 0):.1f}%")
            
            print(f"Response Time: {result['response_time']:.2f}s")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
    
    async def run_test_suite(self):
        """Run comprehensive test suite"""
        # Test cases with expected chart types
        test_cases = [
            # Table queries - entity listings
            ("Покажи всех рекрутеров", "table"),
            ("Список рекрутеров", "table"),
            ("Какие вакансии открыты?", "table"),
            ("Покажи все источники кандидатов", "table"),
            ("Кто наши рекрутеры?", "table"),
            ("Перечисли источники", "table"),
            
            # Comparison queries - should use bar/line
            ("Сравни рекрутеров по эффективности", "bar"),
            ("Динамика найма за год", "line"),
            ("Сколько кандидатов из разных источников?", "bar"),
            
            # Edge cases
            ("Топ-5 рекрутеров", "table"),  # Should be table with sorting
            ("Покажи рекрутеров с их показателями", "table"),
            
            # Complex queries
            ("Какие рекрутеры работали в последние 3 месяца?", "table"),
            ("Список открытых вакансий с количеством кандидатов", "table"),
        ]
        
        print("="*80)
        print("COMPREHENSIVE TABLE CHART IMPLEMENTATION TEST")
        print("="*80)
        print(f"Testing {len(test_cases)} queries...")
        
        async with aiohttp.ClientSession() as session:
            # Wait for server
            await asyncio.sleep(2)
            
            # Run tests
            for query, expected in test_cases:
                result = await self.test_query(session, query, expected)
                self.results.append(result)
                self.print_result(result)
                await asyncio.sleep(1)  # Rate limiting
            
            # Print summary
            self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*80}")
        print("TEST SUMMARY")
        print("="*80)
        
        total = len(self.results)
        successful = [r for r in self.results if r['success']]
        failed = [r for r in self.results if not r['success']]
        
        # Type analysis
        tables = [r for r in successful if r['is_table']]
        valid_tables = [r for r in tables if r['table_valid']]
        type_matches = [r for r in successful if r['type_match'] is True]
        type_mismatches = [r for r in successful if r['type_match'] is False]
        
        print(f"\nOverall Results:")
        print(f"  Total Tests: {total}")
        print(f"  Successful: {len(successful)} ({len(successful)/total*100:.1f}%)")
        print(f"  Failed: {len(failed)}")
        
        print(f"\nChart Type Analysis:")
        print(f"  Table Charts: {len(tables)}")
        print(f"  Valid Tables: {len(valid_tables)}")
        print(f"  Type Matches: {len(type_matches)}")
        print(f"  Type Mismatches: {len(type_mismatches)}")
        
        if type_mismatches:
            print(f"\nType Mismatches:")
            for r in type_mismatches:
                print(f"  • '{r['query']}' - Expected: {r['expected_type']}, Got: {r['chart_type']}")
        
        print(f"\nTable Quality:")
        total_rows = sum(r['row_count'] for r in tables)
        avg_rows = total_rows / len(tables) if tables else 0
        print(f"  Average Rows per Table: {avg_rows:.1f}")
        print(f"  Tables with Valid Structure: {len(valid_tables)}/{len(tables)}")
        
        # Performance
        avg_response = sum(r['response_time'] for r in successful) / len(successful) if successful else 0
        print(f"\nPerformance:")
        print(f"  Average Response Time: {avg_response:.2f}s")
        
        # Final verdict
        table_success_rate = len(valid_tables) / len([r for r in self.results if r['expected_type'] == 'table']) * 100
        print(f"\n{'='*80}")
        print(f"TABLE IMPLEMENTATION SUCCESS RATE: {table_success_rate:.1f}%")
        print("="*80)

async def main():
    tester = TableChartTester()
    await tester.run_test_suite()

if __name__ == "__main__":
    asyncio.run(main())