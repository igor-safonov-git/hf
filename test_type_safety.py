#!/usr/bin/env python3
"""
Test Type Safety with Literal Unions
This will help mypy catch unknown operations and entities
"""
from sqlalchemy_executor import (
    SQLAlchemyHuntflowExecutor, 
    OperationType, 
    EntityType, 
    FilterOperation
)

def test_valid_operations():
    """Test that valid operations work"""
    # Valid operation types
    valid_op: OperationType = "count"
    valid_entity: EntityType = "applicants" 
    valid_filter_op: FilterOperation = "eq"
    
    print("✅ Valid types accepted")

def test_invalid_operations():
    """Test that invalid operations are caught by mypy (uncomment to test)"""
    # These should cause mypy errors when uncommented:
    
    # invalid_op: OperationType = "invalid_operation"  # mypy error
    # invalid_entity: EntityType = "unknown_entity"    # mypy error  
    # invalid_filter: FilterOperation = "unknown_op"   # mypy error
    
    print("✅ Type safety test setup complete")

def create_valid_expression():
    """Create a properly typed expression"""
    expression = {
        "operation": "count",  # Valid OperationType
        "entity": "applicants",  # Valid EntityType
        "filter": {
            "field": "status_id",
            "op": "eq",  # Valid FilterOperation
            "value": 123
        }
    }
    return expression

def create_invalid_expression():
    """Example of expressions that would fail mypy if typed strictly"""
    # This would pass runtime but fail mypy with strict typing:
    expression = {
        "operation": "invalid_op",  # Would be caught by mypy
        "entity": "unknown_table",  # Would be caught by mypy
        "filter": {
            "field": "status_id",
            "op": "unknown_op",  # Would be caught by mypy
            "value": 123
        }
    }
    return expression

if __name__ == "__main__":
    test_valid_operations()
    test_invalid_operations()
    
    valid_expr = create_valid_expression()
    print(f"Valid expression: {valid_expr}")
    
    # Note: invalid expression would cause mypy errors if strictly typed
    invalid_expr = create_invalid_expression()
    print(f"Invalid expression (would fail mypy): {invalid_expr}")
    
    print("\n🎯 Type Safety Benefits:")
    print("• OperationType catches typos in 'count', 'avg', 'field'")
    print("• EntityType catches typos in table names")  
    print("• FilterOperation catches typos in filter operators")
    print("• mypy --strict will catch these at development time")
    print("• Better IDE autocompletion and error detection")