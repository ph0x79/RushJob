"""
API endpoint to run comprehensive Greenhouse company testing.
This allows running the discovery script remotely via Railway.
"""
import asyncio
import time
from typing import Dict, List, Any
from fastapi import APIRouter, BackgroundTasks
from loguru import logger
import httpx

# Import the comprehensive company list from our test script
COMPREHENSIVE_COMPANY_LIST = [
    # Current working companies
    "stripe", "airbnb", "robinhood", "peloton", "dropbox", "coinbase", 
    "reddit", "lyft", "doordashusa", "pinterest", "databricks", "figma", 
    "discord", "twitch", "brex", "instacart", "asana", "flexport", 
    "gusto", "checkr", "amplitude", "airtable", "mixpanel", "nextdoor", "thumbtack",
    
    # Additional tech companies to test
    "plaid", "ramp", "mercury", "chime", "noom", "calm", "headspace",
    "strava", "grubhub", "postmates", "ubereats", "caviar", "vrbo", 
    "booking", "expedia", "kayak", "tripadvisor", "lime", "bird", "spin", 
    "getaround", "turo", "zipcar", "wework", "industrious", "regus",
    "sketch", "invision", "abstract", "zeplin", "obsidian", "roam", 
    "logseq", "craft", "linear", "monday", "trello", "jira", "confluence",
    "gitlab", "bitbucket", "sourcetree", "gitkraken", "vercel", "netlify", 
    "heroku", "digitalocean", "linode", "vultr", "cloudflare", "fastly",
    
    # Financial services
    "etrade", "schwab", "fidelity", "vanguard", "blackrock", "binance", 
    "kraken", "gemini", "blockfi", "celsius",
    
    # Healthcare & biotech
    "23andme", "ancestry", "color", "tempus", "grail", "guardant",
    "teladoc", "amwell", "doxy", "mdlive",
    
    # E-commerce & retail
    "bigcommerce", "magento", "woocommerce", "etsy", "mercari", 
    "poshmark", "depop", "vinted", "wayfair", "overstock",
    
    # Gaming companies
    "riot", "blizzard", "activision", "ea", "ubisoft", "take-two", 
    "valve", "steam", "youtube-gaming",
    
    # Startups and scale-ups
    "segment", "datadog", "newrelic", "pagerduty", "splunk", "okta",
    "auth0", "twilio", "sendgrid", "mailchimp", "hubspot", "zendesk", 
    "intercom", "elastic", "mongodb", "coursera", "udemy", "classdojo",
    "verkada", "anduril", "lattice", "rippling", "deel", "remote",
    "superhuman", "notion", "coda", "retool", "zapier", "make",
    "algolia", "segment", "customer-io", "sendbird", "pusher", "stream",
    
    # Alternative slug patterns
    "doordash", "door-dash", "epic-games", "epic", "epicgames",
    "riotgames", "riot-games", "activision-blizzard", "blizzard-entertainment",
    "electronic-arts", "ea-games", "twenty-three-and-me", "23-and-me"
]

router = APIRouter()

async def test_single_company(slug: str, session: httpx.AsyncClient) -> Dict[str, Any]:
    """Test a single company's Greenhouse endpoint."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    
    try:
        response = await session.get(url)
        
        result = {
            "slug": slug,
            "status_code": response.status_code,
            "success": False,
            "jobs_count": 0,
            "error": None,
            "sample_job": None
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
                
            except Exception as e:
                result["error"] = f"JSON decode error: {str(e)}"
                
        elif response.status_code == 404:
            result["error"] = "Company not found (404)"
        elif response.status_code == 403:
            result["error"] = "Access forbidden (403)"
        elif response.status_code == 429:
            result["error"] = "Rate limited (429)"
        else:
            result["error"] = f"HTTP {response.status_code}"
            
        return result
        
    except Exception as e:
        return {
            "slug": slug,
            "status_code": None,
            "success": False,
            "jobs_count": 0,
            "error": f"Request error: {str(e)}",
            "sample_job": None
        }

@router.post("/discover-greenhouse-companies")
async def discover_greenhouse_companies(
    limit: int = 50,  # Limit companies to test to avoid timeouts
    background_tasks: BackgroundTasks = None
):
    """
    Discover which companies use Greenhouse by testing their endpoints.
    This runs the comprehensive company testing remotely.
    """
    logger.info(f"Starting comprehensive Greenhouse company discovery (testing {limit} companies)")
    
    # Limit the list to avoid timeouts
    companies_to_test = COMPREHENSIVE_COMPANY_LIST[:limit]
    
    headers = {
        "User-Agent": "RushJob/1.0 (Company Discovery)",
        "Accept": "application/json",
    }
    
    timeout = httpx.Timeout(15.0, connect=5.0)  # Shorter timeouts for web endpoint
    
    start_time = time.time()
    results = []
    successful_companies = []
    failed_companies = []
    
    async with httpx.AsyncClient(headers=headers, timeout=timeout) as session:
        # Test companies in smaller batches for web endpoint
        batch_size = 5
        total_batches = (len(companies_to_test) + batch_size - 1) // batch_size
        
        for i in range(0, len(companies_to_test), batch_size):
            batch = companies_to_test[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            logger.info(f"Testing batch {batch_num}/{total_batches}: {batch}")
            
            # Test companies in batch
            batch_tasks = [test_single_company(slug, session) for slug in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Exception testing company: {result}")
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
            
            # Small delay between batches
            await asyncio.sleep(1)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Sort successful companies by job count
    successful_companies.sort(key=lambda x: x["jobs_count"], reverse=True)
    
    # Generate response
    response = {
        "summary": {
            "total_tested": len(results),
            "successful": len(successful_companies),
            "failed": len(failed_companies),
            "success_rate": round(len(successful_companies)/len(results)*100, 1) if results else 0,
            "duration_seconds": round(duration, 1),
            "companies_tested": companies_to_test
        },
        "successful_companies": successful_companies,
        "failed_companies": [{"slug": c["slug"], "error": c["error"]} for c in failed_companies],
        "recommendations": {
            "new_companies_to_add": [
                c for c in successful_companies 
                if c["slug"] not in [
                    "stripe", "airbnb", "robinhood", "peloton", "dropbox", "coinbase", 
                    "reddit", "lyft", "doordashusa", "pinterest", "databricks", "figma", 
                    "discord", "twitch", "brex", "instacart", "asana", "flexport", 
                    "gusto", "checkr", "amplitude", "airtable", "mixpanel", "nextdoor", "thumbtack"
                ]
            ][:20],  # Top 20 new companies
            "companies_to_remove": [
                "canva", "shopify", "snowflake"  # Already identified as non-Greenhouse
            ]
        }
    }
    
    logger.info(f"Company discovery completed: {len(successful_companies)} successful, {len(failed_companies)} failed")
    
    return response

@router.get("/test-company/{slug}")
async def test_single_company_endpoint(slug: str):
    """Test a single company's Greenhouse endpoint quickly."""
    
    headers = {
        "User-Agent": "RushJob/1.0",
        "Accept": "application/json",
    }
    
    async with httpx.AsyncClient(headers=headers, timeout=10.0) as session:
        result = await test_single_company(slug, session)
        
        return {
            "company": slug,
            "result": result,
            "recommendation": "add" if result["success"] and result["jobs_count"] > 0 else "skip"
        }
