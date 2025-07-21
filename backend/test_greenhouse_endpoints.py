#!/usr/bin/env python3
"""
Comprehensive test of Greenhouse endpoints to identify which companies actually use Greenhouse.
This script tests actual API responses rather than making assumptions.
"""
import asyncio
import httpx
import json
from typing import List, Dict, Any
import time

# Comprehensive list of potential company slugs to test
# Includes current companies plus many other tech companies
POTENTIAL_COMPANIES = [
    # Current list
    "stripe", "airbnb", "robinhood", "peloton", "dropbox", "coinbase", 
    "reddit", "lyft", "doordashusa", "pinterest", "databricks", "figma", 
    "notion", "discord", "twitch", "roblox", "epicgames",
    
    # Additional tech companies (using common slug patterns)
    "asana", "atlassian", "zoom", "slack", "spotify", "uber", "square",
    "shopify", "github", "gitlab", "mongodb", "elastic", "snowflake",
    "salesforce", "hubspot", "zendesk", "intercom", "segment", "mixpanel",
    "amplitude", "datadog", "newrelic", "pagerduty", "splunk", "okta",
    "auth0", "twilio", "sendgrid", "mailchimp", "constant-contact",
    "adobe", "autodesk", "intuit", "paypal", "ebay", "netflix", "hulu",
    "disney", "warner", "paramount", "sony", "nvidia", "amd", "intel",
    "qualcomm", "broadcom", "cisco", "vmware", "citrix", "oracle",
    "microsoft", "google", "amazon", "apple", "meta", "twitter", "x",
    "linkedin", "snapchat", "tiktok", "bytedance", "pinterest", "tumblr",
    "reddit", "discord", "slack", "telegram", "whatsapp", "signal",
    
    # Startups and scale-ups
    "plaid", "brex", "ramp", "mercury", "chime", "noom", "calm", "headspace",
    "peloton", "mirror", "tonal", "whoop", "strava", "garmin", "fitbit",
    "instacart", "doordash", "grubhub", "postmates", "ubereats", "caviar",
    "airbnb", "vrbo", "booking", "expedia", "kayak", "tripadvisor",
    "lime", "bird", "spin", "jump", "getaround", "turo", "zipcar",
    "wework", "industrious", "regus", "spaces", "mindspace",
    "canva", "figma", "sketch", "invision", "abstract", "zeplin",
    "airtable", "notion", "obsidian", "roam", "logseq", "craft",
    "linear", "asana", "monday", "trello", "jira", "confluence",
    "github", "gitlab", "bitbucket", "sourcetree", "gitkraken",
    "vercel", "netlify", "heroku", "digitalocean", "linode", "vultr",
    "aws", "gcp", "azure", "cloudflare", "fastly", "akamai",
    
    # Financial services
    "robinhood", "etrade", "schwab", "fidelity", "vanguard", "blackrock",
    "goldman", "jpmorgan", "bankofamerica", "wells-fargo", "chase",
    "stripe", "square", "paypal", "venmo", "zelle", "cashapp",
    "coinbase", "binance", "kraken", "gemini", "blockfi", "celsius",
    
    # Healthcare & biotech
    "23andme", "ancestry", "color", "tempus", "grail", "guardant",
    "moderna", "pfizer", "jnj", "merck", "roche", "novartis",
    "teladoc", "amwell", "doxy", "mdlive", "doctor-on-demand",
    
    # E-commerce & retail
    "amazon", "shopify", "bigcommerce", "magento", "woocommerce",
    "etsy", "ebay", "mercari", "poshmark", "depop", "vinted",
    "wayfair", "overstock", "bed-bath-beyond", "target", "walmart",
    
    # Gaming companies
    "roblox", "epicgames", "riot", "blizzard", "activision", "ea",
    "ubisoft", "take-two", "nintendo", "sony-interactive", "microsoft-gaming",
    "valve", "steam", "discord", "twitch", "youtube-gaming",
    
    # Alternative slug patterns for known companies
    "doordash", "door-dash", "doordashusa",
    "epic-games", "epic", "epicgames",
    "riotgames", "riot-games", 
    "activision-blizzard", "blizzard-entertainment",
    "electronic-arts", "ea-games",
]

async def test_greenhouse_endpoint(slug: str, session: httpx.AsyncClient) -> Dict[str, Any]:
    """Test a single Greenhouse endpoint and return detailed results."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    
    try:
        print(f"Testing {slug}...", end=" ")
        response = await session.get(url)
        
        result = {
            "slug": slug,
            "url": url,
            "status_code": response.status_code,
            "success": False,
            "jobs_count": 0,
            "error": None,
            "sample_job": None,
            "response_time_ms": None
        }
        
        if response.status_code == 200:
            try:
                data = response.json()
                jobs = data.get("jobs", [])
                result["success"] = True
                result["jobs_count"] = len(jobs)
                
                # Get sample job for verification
                if jobs:
                    sample = jobs[0]
                    result["sample_job"] = {
                        "id": sample.get("id"),
                        "title": sample.get("title", "")[:50] + "..." if len(sample.get("title", "")) > 50 else sample.get("title", ""),
                        "location": sample.get("location", {}).get("name", "N/A")
                    }
                
                print(f"✅ {len(jobs)} jobs")
                
            except json.JSONDecodeError as e:
                result["error"] = f"JSON decode error: {str(e)}"
                print(f"❌ JSON error")
                
        elif response.status_code == 404:
            result["error"] = "Company not found (404)"
            print(f"❌ 404")
        elif response.status_code == 403:
            result["error"] = "Access forbidden (403)"
            print(f"❌ 403")
        elif response.status_code == 429:
            result["error"] = "Rate limited (429)"
            print(f"❌ Rate limited")
        else:
            result["error"] = f"HTTP {response.status_code}"
            print(f"❌ {response.status_code}")
            
        return result
        
    except httpx.TimeoutException:
        print(f"❌ Timeout")
        return {
            "slug": slug,
            "url": url,
            "status_code": None,
            "success": False,
            "jobs_count": 0,
            "error": "Request timeout",
            "sample_job": None,
            "response_time_ms": None
        }
    except Exception as e:
        print(f"❌ Error: {str(e)[:30]}...")
        return {
            "slug": slug,
            "url": url,
            "status_code": None,
            "success": False,
            "jobs_count": 0,
            "error": f"Unexpected error: {str(e)}",
            "sample_job": None,
            "response_time_ms": None
        }

async def test_all_companies():
    """Test all potential companies and generate comprehensive results."""
    print("🔍 COMPREHENSIVE GREENHOUSE ENDPOINT TESTING")
    print("=" * 80)
    print(f"Testing {len(POTENTIAL_COMPANIES)} potential company slugs...")
    print("=" * 80)
    
    # Create HTTP client with appropriate headers and settings
    headers = {
        "User-Agent": "RushJob/1.0 (Greenhouse Endpoint Tester)",
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
    }
    
    timeout = httpx.Timeout(30.0, connect=10.0)
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    
    async with httpx.AsyncClient(
        headers=headers, 
        timeout=timeout, 
        limits=limits,
        follow_redirects=True
    ) as session:
        
        results = []
        successful_companies = []
        failed_companies = []
        
        # Test companies in small batches to avoid overwhelming the API
        batch_size = 10
        total_batches = (len(POTENTIAL_COMPANIES) + batch_size - 1) // batch_size
        
        for i in range(0, len(POTENTIAL_COMPANIES), batch_size):
            batch = POTENTIAL_COMPANIES[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            print(f"\n--- Batch {batch_num}/{total_batches} ---")
            
            # Test companies in batch
            batch_tasks = [test_greenhouse_endpoint(slug, session) for slug in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    print(f"❌ Exception: {result}")
                    # Create a failed result for the exception
                    failed_result = {
                        "slug": "unknown",
                        "success": False,
                        "error": str(result)
                    }
                    failed_companies.append(failed_result)
                    continue
                    
                results.append(result)
                
                if result["success"]:
                    successful_companies.append({
                        "name": result["slug"].title().replace("-", " "),
                        "slug": result["slug"],
                        "jobs_count": result["jobs_count"]
                    })
                else:
                    failed_companies.append(result)
            
            # Small delay between batches to be respectful
            if i + batch_size < len(POTENTIAL_COMPANIES):
                print("  (Waiting 2 seconds between batches...)")
                await asyncio.sleep(2)
    
    # Generate comprehensive report
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE RESULTS")
    print("=" * 80)
    print(f"Total companies tested: {len(results)}")
    print(f"Successful (use Greenhouse): {len(successful_companies)}")
    print(f"Failed (don't use Greenhouse): {len(failed_companies)}")
    print(f"Success rate: {len(successful_companies)/len(results)*100:.1f}%")
    
    # Sort successful companies by job count (descending)
    successful_companies.sort(key=lambda x: x["jobs_count"], reverse=True)
    
    print(f"\n✅ COMPANIES THAT USE GREENHOUSE ({len(successful_companies)} found):")
    print("=" * 80)
    print("# Companies sorted by number of jobs available")
    print("VERIFIED_GREENHOUSE_COMPANIES = [")
    for company in successful_companies:
        jobs_comment = f"  # {company['jobs_count']} jobs"
        print(f'    {{"name": "{company["name"]}", "slug": "{company["slug"]}"}},{jobs_comment}')
    print("]")
    
    # Show top companies by job count
    print(f"\n🏆 TOP COMPANIES BY JOB COUNT:")
    print("=" * 80)
    for i, company in enumerate(successful_companies[:20], 1):
        print(f"{i:2d}. {company['name']:25} ({company['slug']:20}) - {company['jobs_count']:4d} jobs")
    
    # Show some interesting failures
    notable_failures = [r for r in failed_companies if r["slug"] in [
        "google", "apple", "microsoft", "amazon", "meta", "shopify", 
        "spotify", "uber", "netflix", "salesforce"
    ]]
    
    if notable_failures:
        print(f"\n❌ NOTABLE COMPANIES NOT USING GREENHOUSE:")
        print("=" * 80)
        for failure in notable_failures:
            print(f"  - {failure['slug']:15} ({failure['error']})")
    
    # Export results to JSON for further analysis
    output_file = "greenhouse_test_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "summary": {
                "total_tested": len(results),
                "successful": len(successful_companies),
                "failed": len(failed_companies),
                "success_rate": len(successful_companies)/len(results)*100
            },
            "successful_companies": successful_companies,
            "all_results": results
        }, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {output_file}")
    print("\n🎯 NEXT STEPS:")
    print("=" * 80)
    print("1. Review the generated VERIFIED_GREENHOUSE_COMPANIES list above")
    print("2. Update your greenhouse.py file with the working companies")
    print("3. Remove or comment out companies that returned 404 errors")
    print("4. Consider adding high-job-count companies you weren't tracking before")

if __name__ == "__main__":
    print("Starting comprehensive Greenhouse endpoint testing...")
    print("This may take a few minutes due to respectful rate limiting.\n")
    
    start_time = time.time()
    asyncio.run(test_all_companies())
    end_time = time.time()
    
    print(f"\n⏱️  Total testing time: {end_time - start_time:.1f} seconds")
