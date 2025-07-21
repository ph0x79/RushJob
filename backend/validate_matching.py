"""
Simple validation of the location matching logic without external dependencies.
"""

# Simulate the LocationMatcher logic for testing
class SimpleLocationMatcher:
    def __init__(self):
        self.location_mappings = {
            'chicago': ['chicago', 'chi', 'illinois', 'il'],
            'new york': ['new york', 'nyc', 'ny', 'new york city', 'manhattan'],
            'san francisco': ['san francisco', 'sf', 'ssf', 'south san francisco'],
            'seattle': ['seattle', 'sea', 'washington', 'wa'],
            'berlin': ['berlin', 'germany', 'de-berlin'],
            'dublin': ['dublin', 'ireland'],
            'remote': ['remote', 'us-remote', 'us remote', 'remote us', 'remote in us', 
                      'remote in the us', 'work from home', 'wfh'],
            'bangalore': ['bangalore', 'bengaluru', 'india'],
            'london': ['london', 'uk', 'united kingdom', 'england'],
            'tokyo': ['tokyo', 'japan'],
        }
    
    def normalize_location(self, location):
        if not location:
            return []
        
        cleaned = location.lower().replace('-', ' ').strip()
        parts = []
        for separator in [',', ';', ' and ', ' or ', '/']:
            if separator in cleaned:
                parts.extend([part.strip() for part in cleaned.split(separator)])
                break
        else:
            parts = [cleaned]
        
        return [part for part in parts if part]
    
    def match_location(self, job_location, target_location):
        if not job_location or not target_location:
            return False
        
        job_parts = self.normalize_location(job_location)
        target_parts = self.normalize_location(target_location)
        
        # Direct matches
        for job_part in job_parts:
            for target_part in target_parts:
                if job_part == target_part or job_part in target_part or target_part in job_part:
                    return True
        
        # Alias matching
        for canonical, aliases in self.location_mappings.items():
            job_matches = any(any(alias in job_part or job_part in alias for alias in aliases) for job_part in job_parts)
            target_matches = any(any(alias in target_part or target_part in alias for alias in aliases) for target_part in target_parts)
            
            if job_matches and target_matches:
                return True
        
        return False

# Test the matching logic
def test_stripe_scenarios():
    matcher = SimpleLocationMatcher()
    
    test_cases = [
        ("DE-Berlin", "Berlin", True),
        ("Chicago", "Chicago", True), 
        ("Tokyo, Japan", "Tokyo", True),
        ("London", "UK", True),
        ("Texas,  New York ", "New York", True),
        ("US-Remote", "Remote", True),
        ("Seattle, San Francisco, US-Remote", "San Francisco", True),
        ("Seattle, San Francisco, US-Remote", "Remote", True),
        ("SF, Seattle, New York, Remote in the US", "Remote", True),
        ("US-NYC, US-SEA", "New York", True),
        ("US-NYC, US-SEA", "Seattle", True),
        ("Dublin", "Ireland", True),
        ("Bengaluru", "Bangalore", True),
    ]
    
    print("Testing Enhanced Location Matching with Stripe Data")
    print("=" * 55)
    
    passed = 0
    for job_loc, alert_loc, expected in test_cases:
        result = matcher.match_location(job_loc, alert_loc)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        if result == expected:
            passed += 1
        
        print(f"{status} | '{job_loc}' vs '{alert_loc}' -> {result}")
        
        # Show normalization for debugging
        job_norm = matcher.normalize_location(job_loc)
        alert_norm = matcher.normalize_location(alert_loc)
        print(f"      Job normalized: {job_norm}")
        print(f"      Alert normalized: {alert_norm}")
        print()
    
    print(f"Results: {passed}/{len(test_cases)} tests passed")
    return passed == len(test_cases)

if __name__ == "__main__":
    test_stripe_scenarios()
