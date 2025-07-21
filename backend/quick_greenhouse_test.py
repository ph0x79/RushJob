#!/usr/bin/env python3
"""
Quick test of current companies plus a few additional ones to validate the approach.
Fixed version with proper error handling and fallback options.
"""
import asyncio
import json
import sys

# Try to import httpx, provide helpful error if not available
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    print("❌ httpx not found. Install with: pip install httpx")
    print("   Or run: cd backend && poetry install")

# Test current companies plus some additional ones you mentioned
TEST_COMPANIES = [
    # Current companies from your list
    "stripe", "airbnb", "robinhood", "peloton", "dropbox", "coinbase", 
    "reddit", "lyft", "doordashusa", "pinterest", "databricks", "figma", 
    "notion", "discord", "twitch", "roblox", "epicgames",
    
    # Additional companies you mentioned or that are likely to use Greenhouse
    "asana", "plaid", "brex", "gusto", "instacart", "checkr", "airtable",
    "flexport", "mixpanel", "amplitude", "segment", "nextdoor", "thumbtack",
    
    # Companies we know DON'T use Greenhouse (for validation)
    "google", "apple", "microsoft", "shopify", "spotify"
]

async def test_with_httpx():
    """Test using httpx (preferred method)."""
    print("🚀 QUICK GREENHOUSE ENDPOINT TEST (using httpx)")
    print("=" * 60)
    
    headers = {
        "User-Agent": "RushJob/1.0",
        "Accept": "application/json",
    }
    
    working_companies = []
    non_working_companies = []
    
    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        for slug in TEST_COMPANIES:
            url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
            
            try:
                print(f"Testing {slug:15}...", end=" ")
                response = await client.get(url)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        jobs = data.get("jobs", [])
                        job_count = len(jobs)
                        
                        if job_count > 0:
                            working_companies.append({"slug": slug, "jobs": job_count})
                            print(f"✅ {job_count:4d} jobs")
                        else:
                            non_working_companies.append({"slug": slug, "error": "No jobs found"})
                            print(f"⚠️  0 jobs")
                            
                    except json.JSONDecodeError:
                        non_working_companies.append({"slug": slug, "error": "JSON error"})
                        print(f"❌ JSON error")
                        
                elif response.status_code == 404:
                    non_working_companies.append({"slug": slug, "error": "404 Not Found"})
                    print(f"❌ 404")
                else:
                    non_working_companies.append({"slug": slug, "error": f"HTTP {response.status_code}"})
                    print(f"❌ {response.status_code}")
                    
            except Exception as e:
                non_working_companies.append({"slug": slug, "error": str(e)})
                print(f"❌ {str(e)[:20]}...")
            
            # Small delay to be respectful
            await asyncio.sleep(0.5)
    
    return working_companies, non_working_companies

def test_with_urllib():
    """Fallback test using standard library urllib (synchronous)."""
    import urllib.request
    import urllib.error
    
    print("🚀 QUICK GREENHOUSE ENDPOINT TEST (using urllib)")
    print("=" * 60)
    print("Note: Using synchronous fallback method")
    
    working_companies = []
    non_working_companies = []
    
    for slug in TEST_COMPANIES:
        url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
        
        try:
            print(f"Testing {slug:15}...", end=" ")
            
            req = urllib.request.Request(
                url, 
                headers={
                    "User-Agent": "RushJob/1.0",
                    "Accept": "application/json",
                }
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status == 200:
                    try:
                        data = json.loads(response.read().decode())
                        jobs = data.get("jobs", [])
                        job_count = len(jobs)
                        
                        if job_count > 0:
                            working_companies.append({"slug": slug, "jobs": job_count})
                            print(f"✅ {job_count:4d} jobs")
                        else:
                            non_working_companies.append({"slug": slug, "error": "No jobs found"})
                            print(f"⚠️  0 jobs")
                            
                    except json.JSONDecodeError:
                        non_working_companies.append({"slug": slug, "error": "JSON error"})
                        print(f"❌ JSON error")
                else:
                    non_working_companies.append({"slug": slug, "error": f"HTTP {response.status}"})
                    print(f"❌ {response.status}")
                    
        except urllib.error.HTTPError as e:
            if e.code == 404:
                non_working_companies.append({"slug": slug, "error": "404 Not Found"})
                print(f"❌ 404")
            else:
                non_working_companies.append({"slug": slug, "error": f"HTTP {e.code}"})
                print(f"❌ {e.code}")
        except Exception as e:
            non_working_companies.append({"slug": slug, "error": str(e)})
            print(f"❌ {str(e)[:20]}...")
        
        # Small delay to be respectful
        import time
        time.sleep(0.5)
    
    return working_companies, non_working_companies

def print_results(working_companies, non_working_companies):
    """Print formatted results."""
    print(f"\n📊 RESULTS:")
    print("=" * 60)
    print(f"Working companies: {len(working_companies)}")
    print(f"Non-working companies: {len(non_working_companies)}")
    
    print(f"\n✅ WORKING COMPANIES:")
    working_companies.sort(key=lambda x: x["jobs"], reverse=True)
    for company in working_companies:
        print(f"  {company['slug']:20} - {company['jobs']:4d} jobs")
    
    print(f"\n❌ NON-WORKING COMPANIES:")
    for company in non_working_companies:
        print(f"  {company['slug']:20} - {company['error']}")
    
    # Identify companies to remove from current list
    current_companies = [
        "stripe", "airbnb", "robinhood", "peloton", "dropbox", "coinbase", 
        "reddit", "lyft", "doordashusa", "pinterest", "databricks", "figma", 
        "notion", "discord", "twitch", "roblox", "epicgames"
    ]
    
    current_working = [c for c in working_companies if c["slug"] in current_companies]
    current_broken = [c for c in non_working_companies if c["slug"] in current_companies]
    
    if current_broken:
        print(f"\n⚠️  CURRENT COMPANIES TO REMOVE ({len(current_broken)} companies):")
        print("=" * 60)
        for company in current_broken:
            print(f"  {company['slug']:20} - {company['error']}")
    
    print(f"\n🔧 RECOMMENDED GREENHOUSE COMPANIES LIST:")
    print("=" * 60)
    print("# Remove the companies listed above and use this clean list:")
    print("VERIFIED_GREENHOUSE_COMPANIES = [")
    for company in current_working:
        name = company["slug"].replace("-", " ").replace("doordashusa", "DoorDash").title()
        print(f'    {{"name": "{name}", "slug": "{company["slug"]}"}},  # {company["jobs"]} jobs')
    print("]")
    
    # Show additional companies found
    additional_companies = [c for c in working_companies if c["slug"] not in current_companies]
    if additional_companies:
        print(f"\n🆕 ADDITIONAL COMPANIES YOU COULD ADD ({len(additional_companies)} companies):")
        print("=" * 60)
        for company in additional_companies:
            name = company["slug"].replace("-", " ").title()
            print(f'    {{"name": "{name}", "slug": "{company["slug"]}"}},  # {company["jobs"]} jobs')

async def main():
    """Main function to run the test."""
    if HTTPX_AVAILABLE:
        working, non_working = await test_with_httpx()
    else:
        print("Falling back to urllib (synchronous mode)...")
        working, non_working = test_with_urllib()
    
    print_results(working, non_working)

if __name__ == "__main__":
    if HTTPX_AVAILABLE:
        asyncio.run(main())
    else:
        # Run synchronous version
        working, non_working = test_with_urllib()
        print_results(working, non_working)
