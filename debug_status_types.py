#!/usr/bin/env python3
"""
Debug what status types are actually available in the production database
"""
import asyncio
import logging
from collections import Counter
from virtual_engine import HuntflowVirtualEngine
from app import hf_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_status_types():
    """Check what status types are actually in the production data"""
    print("🔍 Debugging Status Types in Production Data")
    print("=" * 60)
    
    try:
        # Setup
        engine = HuntflowVirtualEngine(hf_client)
        
        # Get status mapping
        print("\n📊 Getting status mapping...")
        status_mapping = await engine._get_status_mapping()
        print(f"✅ Found {len(status_mapping)} statuses")
        
        # Analyze status types
        print("\n📊 Analyzing status types...")
        type_counts = Counter()
        status_examples = {}
        
        for status_id, status_info in status_mapping.items():
            if isinstance(status_info, dict):
                status_type = status_info.get('type', 'NO_TYPE')
                status_name = status_info.get('name', 'NO_NAME')
                
                type_counts[status_type] += 1
                
                if status_type not in status_examples:
                    status_examples[status_type] = []
                if len(status_examples[status_type]) < 3:  # Keep up to 3 examples
                    status_examples[status_type].append(status_name)
        
        print(f"\n📈 STATUS TYPE DISTRIBUTION:")
        for status_type, count in type_counts.most_common():
            print(f"   {status_type}: {count} statuses")
            if status_type in status_examples:
                examples = ", ".join(status_examples[status_type][:3])
                print(f"      Examples: {examples}")
        
        # Check if we have key types we need
        key_types = ['hired', 'interview', 'offer', 'new', 'progress', 'declined']
        print(f"\n🔍 CHECKING FOR KEY TYPES:")
        for key_type in key_types:
            count = type_counts.get(key_type, 0)
            status = "✅" if count > 0 else "❌"
            print(f"   {status} {key_type}: {count} statuses")
        
        # Get applicants data to see what status IDs are actually in use
        print(f"\n📊 Checking status usage in applicants...")
        applicants_data = await engine._get_applicants_data()
        print(f"✅ Found {len(applicants_data)} applicants")
        
        # Count status usage
        status_usage = Counter()
        for applicant in applicants_data:
            status_id = applicant.get('status_id')
            if status_id:
                status_usage[status_id] += 1
        
        print(f"\n📈 TOP 10 MOST USED STATUSES:")
        for status_id, count in status_usage.most_common(10):
            status_info = status_mapping.get(status_id, {})
            status_name = status_info.get('name', 'Unknown')
            status_type = status_info.get('type', 'Unknown')
            print(f"   ID {status_id}: {count} applicants - '{status_name}' (type: {status_type})")
        
        # Check for hired applicants specifically
        hired_count = 0
        for status_id, count in status_usage.items():
            status_info = status_mapping.get(status_id, {})
            if status_info.get('type') == 'hired':
                hired_count += count
        
        print(f"\n🎯 HIRED APPLICANTS: {hired_count} total")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(debug_status_types())
    exit(0 if success else 1)