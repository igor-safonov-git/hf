#!/usr/bin/env python3
"""
Test script to validate Literal type unions catch invalid operations
Run `mypy test_literal_validation.py` to see type errors
"""
from sqlalchemy_executor import OperationType, EntityType, FilterOperation

def test_valid_literals():
    """These should pass mypy validation"""
    valid_op: OperationType = "count" 
    valid_entity: EntityType = "applicants"
    valid_filter: FilterOperation = "eq"
    print(f"✅ Valid types: {valid_op}, {valid_entity}, {valid_filter}")

# Uncomment these to test mypy error detection:
def test_invalid_literals():
    """These should cause mypy errors when uncommented"""
    # invalid_op: OperationType = "sum"  # mypy error: not in Literal union
    # invalid_entity: EntityType = "users"  # mypy error: not in Literal union  
    # invalid_filter: FilterOperation = "contains"  # mypy error: not in Literal union
    pass

def demonstrate_type_safety():
    """Show how the types improve safety"""
    print("🎯 Type Safety Demonstration:")
    print("Available operations:", OperationType.__args__)
    print("Available entities:", EntityType.__args__) 
    print("Available filter ops:", FilterOperation.__args__)
    
    print("\n💡 To test mypy validation:")
    print("1. Uncomment lines in test_invalid_literals()")
    print("2. Run: mypy test_literal_validation.py")
    print("3. See mypy catch invalid literal values at check time")

if __name__ == "__main__":
    test_valid_literals()
    test_invalid_literals() 
    demonstrate_type_safety()