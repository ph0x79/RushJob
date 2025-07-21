#!/usr/bin/env python3
"""
Test script for enhanced location matching using Stripe job data.
"""
import sys
import os
import asyncio
import json
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.location_matcher import LocationMatcher
from app.services.greenhouse import GreenhouseJob


def test_location_matching():
    """Test location matching with various scenarios."""
    location_matcher = LocationMatcher()
    
    # Test cases based on the Stripe data patterns
    test_cases = [
        # (job_location, alert_location, expected_match)
        ("DE-Berlin", "Berlin", True),
        ("Chicago", "Chicago", True),
        ("Tokyo, Japan", "Tokyo", True),
        ("London", "UK", True),
        ("Texas,  New York ", "New York", True),
        ("Texas,  New York ", "Texas", True),
        ("US-Remote", "Remote", True),
        ("Seattle, San Francisco, US-Remote", "San Francisco", True),
        ("Seattle, San Francisco, US-Remote", "Remote", True),
        ("Dublin", "Ireland", True),
        ("Bengaluru", "Bangalore", True),
        ("N/A", "Remote", False),
        ("San Francisco", "New York", False),
        ("SF, Seattle, New York, Remote in the US", "Remote", True),
        ("US-NYC, US-SEA", "New York", True),
        ("US-NYC, US-SEA", "Seattle", True),
    ]
    
    print("🧪 Testing Enhanced Location Matching")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for job_location, alert_location, expected in test_cases:
        result = location_matcher.match_location(job_location, alert_location)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} | Job: '{job_location}' vs Alert: '{alert_location}' -> {result} (expected {expected})")
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed} passed, {failed} failed")
    
    return failed == 0


def test_normalization():
    """Test location normalization."""
    location_matcher = LocationMatcher()
    
    print("\n🔧 Testing Location Normalization")
    print("=" * 50)
    
    test_locations = [
        "DE-Berlin",
        "Texas,  New York ",
        "Seattle, San Francisco, US-Remote",
        "US-NYC, US-SEA",
        "SF, Seattle, New York, Remote in the US",
        "Dublin HQ",
        "Bengaluru, India",
    ]
    
    for location in test_locations:
        normalized = location_matcher.normalize_location(location)
        print(f"'{location}' -> {normalized}")


def test_with_stripe_data():
    """Test with actual Stripe job data structure."""
    print("\n🎯 Testing with Stripe Job Data")
    print("=" * 50)
    
    # Sample Stripe job data based on your provided data
    stripe_jobs_data = [
        {
            "location": {"name": "DE-Berlin"},
            "title": "Account Executive, BaaS Product Sales (Global)",
            "id": 6931807
        },
        {
            "location": {"name": "Chicago"},
            "title": "Account Executive, Commercial (New Business)",
            "id": 7015293
        },
        {
            "location": {"name": "Seattle, San Francisco, US-Remote"},
            "title": "Backend Engineer, Core Technology",
            "id": 6042172
        },
        {
            "location": {"name": "SF, Seattle, New York, Remote in the US"},
            "title": "Product Designer, Dashboard",
            "id": 6895159
        },
        {
            "location": {"name": "US-NYC, US-SEA"},
            "title": "Senior Software Engineer, Stripe Assistant",
            "id": 7081317
        },
        {
            "location": {"name": "Dublin"},
            "title": "Backend Engineer Dublin: Stripe Products",
            "id": 6852208
        }
    ]
    
    # Convert to GreenhouseJob objects
    greenhouse_jobs = [GreenhouseJob(job_data) for job_data in stripe_jobs_data]
    
    # Test various alert location scenarios
    alert_scenarios = [
        ("Remote", "Looking for remote jobs"),
        ("San Francisco", "Looking for SF jobs"),
        ("New York", "Looking for NYC jobs"),
        ("Berlin", "Looking for Berlin jobs"),
        ("Dublin", "Looking for Dublin jobs"),
        ("London", "Looking for London jobs (should not match)"),
    ]
    
    location_matcher = LocationMatcher()
    
    for alert_location, description in alert_scenarios:
        print(f"\n🔍 {description} (Alert: '{alert_location}')")
        matching_jobs = []
        
        for job in greenhouse_jobs:
            if location_matcher.match_location(job.location, alert_location):
                matching_jobs.append(job)
        
        if matching_jobs:
            for job in matching_jobs:
                print(f"  ✅ {job.title} | {job.location}")
        else:
            print(f"  ❌ No matching jobs found")


def test_remote_detection():
    """Test remote job detection."""
    print("\n🏠 Testing Remote Job Detection")
    print("=" * 50)
    
    location_matcher = LocationMatcher()
    
    remote_test_cases = [
        ("US-Remote", True),
        ("Remote", True),
        ("Remote in the US", True),
        ("Work from home", True),
        ("WFH", True),
        ("Distributed", True),
        ("Anywhere", True),
        ("San Francisco", False),
        ("New York", False),
        ("Chicago, Remote OK", True),
        ("N/A", False),
    ]
    
    for location, expected in remote_test_cases:
        result = location_matcher.is_remote_location(location)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status} | '{location}' -> Remote: {result} (expected {expected})")


def test_edge_cases():
    """Test edge cases and error scenarios."""
    print("\n🔧 Testing Edge Cases")
    print("=" * 50)
    
    location_matcher = LocationMatcher()
    
    edge_cases = [
        # (job_location, alert_location, description)
        ("", "San Francisco", "Empty job location"),
        ("San Francisco", "", "Empty alert location"),
        ("", "", "Both empty"),
        (None, "San Francisco", "None job location"),
        ("San Francisco", None, "None alert location"),
        ("San Francisco, CA", "SF", "Abbreviation matching"),
        ("NYC", "New York City", "Reverse abbreviation"),
        ("Remote - San Francisco", "Remote", "Remote with city specification"),
    ]
    
    for job_loc, alert_loc, description in edge_cases:
        try:
            result = location_matcher.match_location(job_loc, alert_loc)
            print(f"✅ {description}: '{job_loc}' vs '{alert_loc}' -> {result}")
        except Exception as e:
            print(f"❌ {description}: ERROR - {e}")


def main():
    """Run all tests."""
    print("🚀 Enhanced Location Matching Test Suite")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 5
    
    try:
        if test_location_matching():
            tests_passed += 1
        
        test_normalization()
        tests_passed += 1
        
        test_with_stripe_data()
        tests_passed += 1
        
        test_remote_detection()
        tests_passed += 1
        
        test_edge_cases()
        tests_passed += 1
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"\n🎉 Test Suite Complete: {tests_passed}/{total_tests} test sections completed")
    
    if tests_passed == total_tests:
        print("✅ All tests completed successfully!")
        return True
    else:
        print("❌ Some tests had issues. Check output above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
