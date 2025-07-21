#!/usr/bin/env python3
"""
Test script to verify which companies actually have working Greenhouse endpoints.
This will help us clean up the VERIFIED_GREENHOUSE_COMPANIES list.
"""
import asyncio
import httpx
from typing import List, Dict, Any
import json

# Current list from greenhouse.py
COMPANIES_TO_TEST = [
    {"name": "Stripe", "slug": "stripe"},
    {"name": "Airbnb", "slug": "airbnb"},
    {"name": "Robinhood", "slug": "robinhood"},
    {"name": "Peloton", "slug": "peloton"},
    {"name": "Dropbox", "slug": "dropbox"},
    {"name": "Coinbase", "slug": "coinbase"},
    {"name": "Reddit", "slug": "reddit"},
    {"name": "Lyft", "slug": "lyft"},
    {"name": "DoorDash", "slug": "doordashusa"},
    {"name": "Pinterest", "slug": "pinterest"},
    {"name": "Databricks", "slug": "databricks"},
    {"name": "Figma", "slug": "figma"},
    {"name": "Notion", "slug": "notion"},
    {"name": "Discord", "slug": "discord"},
    {"name": "Twitch", "slug": "twitch"},
    {"name": "Roblox", "slug": "roblox"},
    {"name": "Epic Games", "slug": "epicgames"},
]

async def test_company_endpoint(slug: str) -> Dict[str, Any]:
    """Test a single company's Greenhouse endpoint."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    
    headers = {
        "User-Agent": "RushJob/1.0",
        "Accept": "application/json",
    }
    
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        try:
            print(f"Testing {slug}...")
            response = await client.get(url)
            
            result = {
                "slug": slug,
                "status_code": response.status_code,
                "success": False,
                "jobs_count": 0,
                "error": None,
                "response_sample": None
            }
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    jobs = data.get("jobs", [])
                    result["success"] = True
                    result["jobs_count"] = len(jobs)
                    
                    # Sample first job for verification
                    if jobs:
                        sample_job = jobs[0]
                        result["response_sample"] = {
                            "id": sample_job.get("id"),
                            "title": sample_job.get("title"),
                            "location": sample_job.get("location", {}).get("name", "N/A")
                        }
                except json.JSONDecodeError:
                    result["error"] = "Invalid JSON response"
                    result["response_sample"] = response.text[:200] + "..." if len(response.text) > 200 else response.text
            
            elif response.status_code == 404:
                result["error"] = "Company not found on Greenhouse (404)"
            else:
                result["error"] = f"HTTP {response.status_code}: {response.text[:100]}"
                
            return result
            
        except httpx.TimeoutException:
            return {
                "slug": slug,
                "status_code": None,
                "success": False,
                "jobs_count": 0,
                "error": "Request timeout",
                "response_sample": None
            }
        except Exception as e:
            return {
                "slug": slug,
                "status_code": None,
                "success": False,
                "jobs_count": 0,
                "error": f"Unexpected error: {str(e)}",
                "response_sample": None
            }

async def test_all_companies():
    """Test all companies and generate a report."""
    print("🧪 Testing all Greenhouse company endpoints...")
    print("=" * 60)
    
    results = []
    successful_companies = []
    failed_companies = []
    
    # Test companies one by one to avoid rate limiting
    for company in COMPANIES_TO_TEST:
        result = await test_company_endpoint(company["slug"])
        result["name"] = company["name"]
        results.append(result)
        
        if result["success"]:
            successful_companies.append(company)
            print(f"✅ {company['name']} ({company['slug']}) - {result['jobs_count']} jobs")
        else:
            failed_companies.append(company)
            print(f"❌ {company['name']} ({company['slug']}) - {result['error']}")
        
        # Small delay to be respectful to the API
        await asyncio.sleep(1)
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"Total companies tested: {len(COMPANIES_TO_TEST)}")
    print(f"Successful: {len(successful_companies)}")
    print(f"Failed: {len(failed_companies)}")
    
    if failed_companies:
        print(f"\n❌ FAILED COMPANIES (should be removed):")
        for company in failed_companies:
            result = next(r for r in results if r["slug"] == company["slug"])
            print(f"  - {company['name']} ({company['slug']}): {result['error']}")
    
    print(f"\n✅ WORKING COMPANIES:")
    for company in successful_companies:
        result = next(r for r in results if r["slug"] == company["slug"])
        print(f"  - {company['name']} ({company['slug']}): {result['jobs_count']} jobs")
    
    # Generate updated company list
    print(f"\n🔧 UPDATED VERIFIED_GREENHOUSE_COMPANIES LIST:")
    print("=" * 60)
    print("VERIFIED_GREENHOUSE_COMPANIES = [")
    for company in successful_companies:
        print(f'    {{"name": "{company["name"]}", "slug": "{company["slug"]}"}},')
    print("]")
    
    # Generate list of companies to comment out
    if failed_companies:
        print(f"\n📝 COMPANIES TO COMMENT OUT:")
        print("=" * 60)
        for company in failed_companies:
            result = next(r for r in results if r["slug"] == company["slug"])
            reason = "404 - Not on Greenhouse" if "404" in result["error"] else "API Error"
            print(f'    # {{"name": "{company["name"]}", "slug": "{company["slug"]}"}},  # {reason}')

if __name__ == "__main__":
    asyncio.run(test_all_companies())
