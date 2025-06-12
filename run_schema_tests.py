#!/usr/bin/env python3
"""
Comprehensive Schema Test Runner

Runs all schema validation tests automatically
"""

import sys
import subprocess
import os
from typing import Dict, Any


def run_command(command: str, description: str) -> tuple[bool, str]:
    """Run a command and return success status and output"""
    try:
        print(f"🔄 {description}...")
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True, result.stdout
        else:
            print(f"❌ {description} - FAILED")
            print(f"   Error: {result.stderr}")
            return False, result.stderr
            
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False, str(e)


def main():
    """Run all schema tests"""
    
    print("🚀 Huntflow Schema Test Suite")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('huntflow_schema.py'):
        print("❌ Error: huntflow_schema.py not found. Please run from project directory.")
        return False
    
    test_results = {}
    
    # 1. Schema Validation Tests
    success, output = run_command(
        "python test_schema.py",
        "Schema Structure Validation"
    )
    test_results['schema_validation'] = success
    if success:
        print("   Schema compliance score available in output")
    
    # 2. Mock API Tests
    success, output = run_command(
        "python test_api_mocks.py",
        "Mock API Response Validation"
    )
    test_results['mock_validation'] = success
    
    # 3. Integration Tests
    success, output = run_command(
        "python test_integration.py",
        "Schema Integration Tests"
    )
    test_results['integration_tests'] = success
    
    # 4. Try running pytest if available
    if check_pytest_available():
        success, output = run_command(
            "python -m pytest test_schema.py -v",
            "Detailed Unit Tests (pytest)"
        )
        test_results['pytest_tests'] = success
    else:
        print("⚠️  pytest not available - install with: pip install pytest pytest-asyncio")
        test_results['pytest_tests'] = None
    
    # 5. Check for hardcoded demo data
    success, output = run_command(
        "grep -r 'Анна Смирнова' *.py || echo 'No hardcoded data found'",
        "Hardcoded Demo Data Check"
    )
    hardcoded_data_found = "Анна Смирнова" in output
    test_results['no_hardcoded_data'] = not hardcoded_data_found
    
    if hardcoded_data_found:
        print("❌ Found hardcoded 'Анна Смирнова' in code")
        print(f"   Details: {output.strip()}")
    else:
        print("✅ No hardcoded demo data found in schema files")
    
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = 0
    
    for test_name, result in test_results.items():
        if result is None:
            status = "⚠️  SKIPPED"
        elif result:
            status = "✅ PASSED"
            passed += 1
        else:
            status = "❌ FAILED"
        
        if result is not None:
            total += 1
        
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    success_rate = (passed / total * 100) if total > 0 else 0
    print(f"\n🎯 Overall Success Rate: {success_rate:.1f}% ({passed}/{total})")
    
    if success_rate >= 90:
        print("🎉 Schema is highly reliable and compliant!")
        return True
    elif success_rate >= 70:
        print("⚠️  Schema has some issues that should be addressed.")
        return False
    else:
        print("❌ Schema has significant issues requiring immediate attention.")
        return False


def check_pytest_available() -> bool:
    """Check if pytest is available"""
    try:
        import pytest
        return True
    except ImportError:
        return False


def install_test_dependencies():
    """Install test dependencies if missing"""
    
    print("🔧 Checking test dependencies...")
    
    dependencies = ['pytest', 'pytest-asyncio']
    missing = []
    
    for dep in dependencies:
        try:
            __import__(dep.replace('-', '_'))
        except ImportError:
            missing.append(dep)
    
    if missing:
        print(f"⚠️  Missing dependencies: {', '.join(missing)}")
        print("📦 Install with: pip install " + " ".join(missing))
        return False
    else:
        print("✅ All test dependencies available")
        return True


if __name__ == "__main__":
    # Check dependencies first
    deps_ok = install_test_dependencies()
    
    # Run tests
    success = main()
    
    if success:
        print("\n🏆 All schema tests completed successfully!")
        print("🚀 Schema is ready for production use!")
        sys.exit(0)
    else:
        print("\n💥 Some schema tests failed!")
        print("🔧 Please review and fix the issues above.")
        sys.exit(1)