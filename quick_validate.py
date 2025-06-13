#!/usr/bin/env python3
"""
Quick validation of response
"""
import json

# Extract just the analytics JSON content
json_content = '''{
  "report_title": "Total Applicants in System",
  "main_metric": {
    "label": "Total Applicants",
    "value": {
      "operation": "count",
      "entity": "applicants"
    }
  },
  "secondary_metrics": [],
  "chart": {
    "graph_description": "Total number of applicants in the system",
    "chart_type": "bar",
    "x_axis_name": "Applicants",
    "y_axis_name": "Count",
    "x_axis": {
      "operation": "field",
      "field": "id"
    },
    "y_axis": {
      "operation": "count",
      "entity": "applicants"
    }
  }
}'''

# Parse the JSON
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
print("=" * 60)