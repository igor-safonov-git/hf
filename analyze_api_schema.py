#!/usr/bin/env python3
"""
Analyze actual Huntflow API responses to compare with schema definitions
"""
import os
import json
import asyncio
from typing import Dict, Any, List
from dotenv import load_dotenv
import httpx

# Load environment variables
load_dotenv()

class HuntflowAPIAnalyzer:
    """Analyze actual Huntflow API responses to understand schema structure"""
    
    def __init__(self):
        self.hf_token = os.getenv("HF_TOKEN")
        self.acc_id = os.getenv("ACC_ID")
        self.base_url = "https://api.huntflow.ru/v2"
        
        if not self.hf_token or not self.acc_id:
            raise ValueError("Missing HF_TOKEN or ACC_ID environment variables")
    
    async def _req(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated API request"""
        headers = {
            "Authorization": f"Bearer {self.hf_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=f"{self.base_url}{path}",
                    headers=headers,
                    timeout=30.0,
                    **kwargs
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"API request failed: {e}")
                return {}
    
    def analyze_field_structure(self, data: Any, path: str = "") -> Dict[str, str]:
        """Recursively analyze data structure to extract field types"""
        field_info = {}
        
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                if isinstance(value, dict):
                    field_info.update(self.analyze_field_structure(value, current_path))
                elif isinstance(value, list) and value:
                    # Analyze first item in list
                    field_info[current_path] = f"array of {type(value[0]).__name__}"
                    if isinstance(value[0], dict):
                        field_info.update(self.analyze_field_structure(value[0], f"{current_path}[0]"))
                else:
                    field_info[current_path] = type(value).__name__
        elif isinstance(data, list) and data:
            # Analyze first item in root list
            field_info.update(self.analyze_field_structure(data[0], f"{path}[0]"))
        
        return field_info
    
    async def analyze_endpoint(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze a specific endpoint and return field structure"""
        print(f"\n📍 Analyzing endpoint: {endpoint}")
        
        response = await self._req("GET", endpoint, params=params)
        if not response:
            return {"error": "Failed to fetch data"}
        
        # Analyze structure
        field_info = self.analyze_field_structure(response)
        
        # Show sample data
        sample_data = response
        if isinstance(response, dict) and "items" in response and response["items"]:
            sample_data = response["items"][0]  # Show first item
        
        return {
            "endpoint": endpoint,
            "field_structure": field_info,
            "sample_item": sample_data,
            "total_items": len(response.get("items", [])) if isinstance(response, dict) else None
        }
    
    async def run_analysis(self):
        """Run complete analysis of key endpoints"""
        print("🔍 Starting Huntflow API Schema Analysis...")
        
        endpoints_to_analyze = [
            # Applicants
            {
                "endpoint": f"/accounts/{self.acc_id}/applicants/search",
                "params": {"count": 5, "page": 1},
                "name": "Applicants Search"
            },
            # Sources
            {
                "endpoint": f"/accounts/{self.acc_id}/applicants/sources",
                "params": None,
                "name": "Applicant Sources"
            },
            # Coworkers (Recruiters)
            {
                "endpoint": f"/accounts/{self.acc_id}/coworkers",
                "params": None,
                "name": "Coworkers/Recruiters"
            },
            # Vacancies
            {
                "endpoint": f"/accounts/{self.acc_id}/vacancies",
                "params": {"count": 5, "page": 1},
                "name": "Vacancies"
            },
            # Vacancy Statuses (try both endpoints)
            {
                "endpoint": f"/accounts/{self.acc_id}/vacancies/statuses",
                "params": None,
                "name": "Vacancy Statuses (endpoint 1)"
            },
            {
                "endpoint": f"/accounts/{self.acc_id}/vacancy_statuses",
                "params": None,
                "name": "Vacancy Statuses (endpoint 2)"
            }
        ]
        
        analysis_results = {}
        
        for endpoint_info in endpoints_to_analyze:
            try:
                result = await self.analyze_endpoint(
                    endpoint_info["endpoint"], 
                    endpoint_info.get("params")
                )
                analysis_results[endpoint_info["name"]] = result
            except Exception as e:
                print(f"❌ Failed to analyze {endpoint_info['name']}: {e}")
                analysis_results[endpoint_info["name"]] = {"error": str(e)}
        
        # Get specific applicant and logs for detailed analysis
        try:
            # Get first applicant
            applicants_response = await self._req("GET", f"/accounts/{self.acc_id}/applicants/search", params={"count": 1})
            if applicants_response.get("items"):
                applicant_id = applicants_response["items"][0]["id"]
                
                # Get specific applicant details
                applicant_detail = await self.analyze_endpoint(f"/accounts/{self.acc_id}/applicants/{applicant_id}")
                analysis_results["Applicant Detail"] = applicant_detail
                
                # Get applicant logs
                logs_detail = await self.analyze_endpoint(f"/accounts/{self.acc_id}/applicants/{applicant_id}/logs")
                analysis_results["Applicant Logs"] = logs_detail
        except Exception as e:
            print(f"❌ Failed to analyze applicant details: {e}")
        
        return analysis_results

async def main():
    analyzer = HuntflowAPIAnalyzer()
    results = await analyzer.run_analysis()
    
    # Print detailed analysis
    print("\n" + "="*80)
    print("📊 HUNTFLOW API SCHEMA ANALYSIS RESULTS")
    print("="*80)
    
    for endpoint_name, data in results.items():
        print(f"\n🔸 {endpoint_name}")
        print("-" * 50)
        
        if "error" in data:
            print(f"❌ Error: {data['error']}")
            continue
        
        # Show field structure
        if "field_structure" in data:
            print("📋 Field Structure:")
            for field, field_type in sorted(data["field_structure"].items()):
                print(f"  {field}: {field_type}")
        
        # Show total items count
        if data.get("total_items") is not None:
            print(f"\n📊 Total items: {data['total_items']}")
    
    # Save results to file for comparison
    with open("huntflow_api_analysis.md", "w") as f:
        f.write("# Huntflow API Schema Analysis\n\n")
        f.write("This file contains the actual field structures from the Huntflow API endpoints.\n\n")
        
        for endpoint_name, data in results.items():
            f.write(f"## {endpoint_name}\n\n")
            
            if "error" in data:
                f.write(f"**Error:** {data['error']}\n\n")
                continue
            
            f.write(f"**Endpoint:** `{data.get('endpoint', 'Unknown')}`\n\n")
            
            if data.get("total_items") is not None:
                f.write(f"**Total items:** {data['total_items']}\n\n")
            
            if "field_structure" in data:
                f.write("### Field Structure\n\n")
                f.write("| Field | Type |\n")
                f.write("|-------|------|\n")
                for field, field_type in sorted(data["field_structure"].items()):
                    f.write(f"| `{field}` | {field_type} |\n")
                f.write("\n")
            
            if "sample_item" in data and data["sample_item"]:
                f.write("### Sample Data\n\n")
                f.write("```json\n")
                f.write(json.dumps(data["sample_item"], indent=2, ensure_ascii=False))
                f.write("\n```\n\n")
    
    print(f"\n✅ Analysis complete! Results saved to 'huntflow_api_analysis.md'")

if __name__ == "__main__":
    asyncio.run(main())