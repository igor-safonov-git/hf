"""
Test script to show the full prompt with injected data
"""

import asyncio
from context_data_injector import get_dynamic_context
from hr_analytics_prompt_improved import get_improved_prompt

async def show_injected_prompt():
    """Generate and display the full prompt with real data injected"""
    
    print("🔄 Fetching dynamic context for prompt injection...")
    context = await get_dynamic_context()
    
    print("📝 Generating improved prompt with real data...")
    prompt = get_improved_prompt(huntflow_context=context, use_local_cache=True)
    
    print("=" * 80)
    print("FULL PROMPT WITH INJECTED REAL DATA")
    print("=" * 80)
    print(prompt)
    print("=" * 80)
    print(f"Total prompt length: {len(prompt)} characters")
    print(f"Number of entities included:")
    print(f"  - Statuses: {len(context['all_statuses_with_counts'])}")
    print(f"  - Recruiters: {len(context['all_recruiters_with_counts'])}")
    print(f"  - Divisions: {len(context['divisions'])}")
    print(f"  - Rejection Reasons: {len(context['rejection_reasons'])}")
    print(f"  - Sources: {len(context['sources'])}")
    print(f"  - Regions: {len(context['regions'])}")

if __name__ == "__main__":
    asyncio.run(show_injected_prompt())