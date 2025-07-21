#!/usr/bin/env python3
"""
Simple test to verify environment and test a few known companies.
"""

def test_environment():
    """Test that our environment is set up correctly."""
    print("🔧 TESTING ENVIRONMENT")
    print("=" * 40)
    
    # Test Python version
    import sys
    print(f"Python version: {sys.version}")
    
    # Test httpx import
    try:
        import httpx
        print(f"✅ httpx available: {httpx.__version__}")
    except ImportError:
        print("❌ httpx not available")
        print("   Run: pip install httpx")
        print("   Or: cd backend && poetry install")
        return False
    
    # Test asyncio
    try:
        import asyncio
        print(f"✅ asyncio available")
    except ImportError:
        print("❌ asyncio not available")
        return False
    
    print("✅ Environment looks good!")
    return True

async def test_stripe():
    """Test just Stripe to verify our approach works."""
    import httpx
    import json
    
    print("\n🧪 TESTING STRIPE ENDPOINT")
    print("=" * 40)
    
    url = "https://boards-api.greenhouse.io/v1/boards/stripe/jobs"
    headers = {
        "User-Agent": "RushJob/1.0",
        "Accept": "application/json",
    }
    
    try:
        async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
            print(f"Making request to: {url}")
            response = await client.get(url)
            
            print(f"Status code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    jobs = data.get("jobs", [])
                    print(f"✅ SUCCESS: Found {len(jobs)} jobs")
                    
                    if jobs:
                        sample_job = jobs[0]
                        print(f"Sample job: {sample_job.get('title', 'No title')}")
                        print(f"Location: {sample_job.get('location', {}).get('name', 'No location')}")
                    
                    return True
                    
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {e}")
                    print(f"Response text: {response.text[:200]}...")
                    return False
            else:
                print(f"❌ HTTP {response.status_code}")
                print(f"Response text: {response.text[:200]}...")
                return False
                
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

async def main():
    """Main test function."""
    if not test_environment():
        return
    
    success = await test_stripe()
    
    if success:
        print("\n🎉 READY TO RUN FULL TEST!")
        print("=" * 40)
        print("Your environment is working correctly.")
        print("You can now run: python quick_greenhouse_test.py")
    else:
        print("\n❌ ENVIRONMENT ISSUES")
        print("=" * 40)
        print("Please check your network connection and Python environment.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
