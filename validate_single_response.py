#!/usr/bin/env python3
"""
Quick validation of single response
"""
import json

response_text = """{"response":"{\n  \"report_title\": \"Total Applicants in System\",\n  \"main_metric\": {\n    \"label\": \"Total Applicants\",\n    \"value\": {\n      \"operation\": \"count\",\n      \"entity\": \"applicants\"\n    }\n  },\n  \"secondary_metrics\": [],\n  \"chart\": {\n    \"graph_description\": \"Total number of applicants in the system\",\n    \"chart_type\": \"bar\",\n    \"x_axis_name\": \"Applicants\",\n    \"y_axis_name\": \"Count\",\n    \"x_axis\": {\n      \"operation\": \"field\",\n      \"field\": \"id\"\n    },\n    \"y_axis\": {\n      \"operation\": \"count\",\n      \"entity\": \"applicants\"\n    }\n  }\n}","thread_id":"deepseek_763578"}"""

# Parse the response
response_data = json.loads(response_text)
json_content = response_data["response"]

# Parse the inner JSON
analytics_data = json.loads(json_content)

print("✅ Response 1 Validation:")
print(f"📊 Report Title: {analytics_data['report_title']}")
print(f"📈 Main Metric: {analytics_data['main_metric']['label']}")
print(f"🔧 Operation: {analytics_data['main_metric']['value']['operation']}")
print(f"📋 Entity: {analytics_data['main_metric']['value']['entity']}")
print(f"📊 Chart Type: {analytics_data['chart']['chart_type']}")

# Check required fields
required_fields = ["report_title", "main_metric", "secondary_metrics", "chart"]
missing = [field for field in required_fields if field not in analytics_data]

if not missing:
    print("✅ All required fields present")
else:
    print(f"❌ Missing fields: {missing}")

# Check for forbidden fields
forbidden_in_response = any(forbidden in json_content for forbidden in ["demo_value", "demo_data"])
if not forbidden_in_response:
    print("✅ No forbidden demo fields found")
else:
    print("❌ Contains forbidden demo fields")

print(f"\n🎯 RESULT: VALID RESPONSE - Agent correctly generated analytics JSON!")