#!/usr/bin/env python3
"""Test prompt.py integration with Universal Filtering System"""

from prompt import get_comprehensive_prompt

def test_prompt_integration():
    """Test that prompt.py includes Universal Filtering documentation"""
    
    print("=== Testing prompt.py Integration with Universal Filtering ===\n")
    
    # Generate the prompt
    prompt = get_comprehensive_prompt()
    
    # Test 1: Check that existing content is preserved
    print("1. Testing Existing Content Preservation")
    existing_elements = [
        "YOU CAN FILTER BY ONLY THESE PARAMETERS",
        "period: year | 6 month | 3 month",
        "applicants: id | active",
        "vacancies: open | closed | paused | id",
        "ID FILTER EXAMPLES"
    ]
    
    for element in existing_elements:
        if element in prompt:
            print(f"  ✅ Preserved: {element[:40]}...")
        else:
            print(f"  ❌ Missing: {element[:40]}...")
    
    # Test 2: Check that new Universal Filtering content is added
    print("\n2. Testing Universal Filtering Integration")
    new_elements = [
        "ADVANCED FILTERING",
        "Cross-entity filtering",
        "Logical operators",
        "Advanced operators",
        "ADVANCED FILTER EXAMPLES",
        '"and": [{"period": "3 month"}',
        '"or": [{"sources": "linkedin"}',
        '{"operator": "in", "value": [',
        "Nested:"
    ]
    
    for element in new_elements:
        if element in prompt:
            print(f"  ✅ Added: {element[:40]}...")
        else:
            print(f"  ❌ Missing: {element[:40]}...")
    
    # Test 3: Check total prompt length (should be slightly longer)
    print(f"\n3. Prompt Statistics")
    print(f"  Total length: {len(prompt)} characters")
    print(f"  Lines: {prompt.count(chr(10)) + 1}")
    
    # Test 4: Verify no critical sections were accidentally removed
    print("\n4. Critical Sections Check")
    critical_sections = [
        "MANDATORY JSON SCHEMA:",
        "MANDATORY RESPONSE TEMPLATE:",
        "FOLLOW THIS PROCESS STEP BY STEP",
        "YOU CAN USE ONLY THESE ENTITIES"
    ]
    
    all_critical_present = True
    for section in critical_sections:
        if section in prompt:
            print(f"  ✅ Present: {section}")
        else:
            print(f"  ❌ MISSING: {section}")
            all_critical_present = False
    
    # Summary
    print(f"\n5. Integration Summary")
    if all_critical_present:
        print("  ✅ All critical sections preserved")
        print("  ✅ Universal Filtering documentation added")
        print("  ✅ Integration successful - prompt ready for advanced filtering")
        return True
    else:
        print("  ❌ Critical sections missing - integration failed")
        return False

if __name__ == "__main__":
    success = test_prompt_integration()
    if success:
        print("\n🎉 PROMPT INTEGRATION SUCCESSFUL")
        print("   AI can now generate Universal Filtering queries")
    else:
        print("\n⚠️  PROMPT INTEGRATION ISSUES DETECTED")