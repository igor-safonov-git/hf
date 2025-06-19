#!/usr/bin/env python3
"""
Debug script to print the full prompt with injected context data
"""

import asyncio
from prompt import get_comprehensive_prompt
from context_data_injector import get_dynamic_context
from huntflow_local_client import HuntflowLocalClient

async def main():
    print("=" * 80)
    print("FETCHING CONTEXT DATA...")
    print("=" * 80)
    
    client = HuntflowLocalClient()
    context = await get_dynamic_context(client)
    
    print("\nCONTEXT DATA:")
    print("-" * 40)
    
    # Print recruiters specifically to see their IDs
    print("RECRUITERS:")
    if 'recruiters' in context:
        for i, recruiter in enumerate(context['recruiters'][:10]):  # Show first 10
            print(f"  {i+1}. {recruiter}")
    
    print("\nSOURCES:")
    if 'sources' in context:
        for i, source in enumerate(context['sources'][:5]):  # Show first 5
            print(f"  {i+1}. {source}")
    
    print("\nSTATUSES:")
    if 'stages' in context:
        for i, status in enumerate(context['stages'][:5]):  # Show first 5
            print(f"  {i+1}. {status}")
    
    print("\n" + "=" * 80)
    print("FULL PROMPT WITH INJECTED DATA:")
    print("=" * 80)
    
    full_prompt = get_comprehensive_prompt(context)
    print(full_prompt)
    
    print("\n" + "=" * 80)
    print("END OF PROMPT")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())