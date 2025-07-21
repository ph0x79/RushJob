"""
Enhanced location matching service for job filtering.
"""
from typing import List, Dict, Set
import re
from loguru import logger


class LocationMatcher:
    """Enhanced location matching with comprehensive alias support."""
    
    def __init__(self):
        """Initialize location mappings and aliases."""
        self.location_mappings = {
            # US Cities and States
            'chicago': ['chicago', 'chi', 'illinois', 'il'],
            'new york': ['new york', 'nyc', 'ny', 'new york city', 'manhattan'],
            'san francisco': ['san francisco', 'sf', 'ssf', 'south san francisco'],
            'seattle': ['seattle', 'sea', 'washington', 'wa'],
            'atlanta': ['atlanta', 'atl', 'georgia', 'ga'],
            'boston': ['boston', 'massachusetts', 'ma'],
            'texas': ['texas', 'tx', 'dallas', 'austin', 'houston'],
            'california': ['california', 'ca', 'calif'],
            'los angeles': ['los angeles', 'la', 'los angeles county'],
            'denver': ['denver', 'colorado', 'co'],
            'phoenix': ['phoenix', 'arizona', 'az'],
            'portland': ['portland', 'oregon', 'or'],
            'miami': ['miami', 'florida', 'fl'],
            'philadelphia': ['philadelphia', 'philly', 'pennsylvania', 'pa'],
            'detroit': ['detroit', 'michigan', 'mi'],
            'las vegas': ['las vegas', 'vegas', 'nevada', 'nv'],
            'salt lake city': ['salt lake city', 'slc', 'utah', 'ut'],
            'minneapolis': ['minneapolis', 'minnesota', 'mn'],
            'nashville': ['nashville', 'tennessee', 'tn'],
            'raleigh': ['raleigh', 'north carolina', 'nc'],
            'charlotte': ['charlotte', 'north carolina', 'nc'],
            'richmond': ['richmond', 'virginia', 'va'],
            'pittsburgh': ['pittsburgh', 'pennsylvania', 'pa'],
            
            # US Regions/Remote
            'remote': ['remote', 'us-remote', 'us remote', 'remote us', 'remote in us', 
                      'remote in the us', 'work from home', 'wfh', 'telecommute', 
                      'distributed', 'anywhere'],
            'us': ['us', 'usa', 'united states', 'america', 'amer', 'national us'],
            'canada': ['canada', 'ca', 'toronto', 'ca-remote', 'can-remote', 
                      'ca-toronto', 'vancouver', 'montreal', 'ottawa', 'calgary'],
            
            # International - Europe
            'london': ['london', 'uk', 'united kingdom', 'england', 'great britain'],
            'dublin': ['dublin', 'ireland', 'dublin hq'],
            'berlin': ['berlin', 'germany', 'de-berlin', 'deutschland'],
            'paris': ['paris', 'france'],
            'madrid': ['madrid', 'spain'],
            'barcelona': ['barcelona', 'spain'],
            'bucharest': ['bucharest', 'romania'],
            'amsterdam': ['amsterdam', 'netherlands', 'holland'],
            'zurich': ['zurich', 'switzerland'],
            'stockholm': ['stockholm', 'sweden'],
            'oslo': ['oslo', 'norway'],
            'copenhagen': ['copenhagen', 'denmark'],
            'helsinki': ['helsinki', 'finland'],
            'vienna': ['vienna', 'austria'],
            'warsaw': ['warsaw', 'poland'],
            'prague': ['prague', 'czech republic'],
            'budapest': ['budapest', 'hungary'],
            'lisbon': ['lisbon', 'portugal'],
            'rome': ['rome', 'italy'],
            'milan': ['milan', 'italy'],
            
            # International - Asia Pacific
            'tokyo': ['tokyo', 'japan'],
            'singapore': ['singapore'],
            'sydney': ['sydney', 'australia'],
            'melbourne': ['melbourne', 'australia'],
            'bangalore': ['bangalore', 'bengaluru', 'india'],
            'mumbai': ['mumbai', 'bombay', 'india'],
            'delhi': ['delhi', 'new delhi', 'india'],
            'hyderabad': ['hyderabad', 'india'],
            'pune': ['pune', 'india'],
            'chennai': ['chennai', 'madras', 'india'],
            'hong kong': ['hong kong', 'hk'],
            'seoul': ['seoul', 'south korea', 'korea'],
            'beijing': ['beijing', 'china'],
            'shanghai': ['shanghai', 'china'],
            'taipei': ['taipei', 'taiwan'],
            'bangkok': ['bangkok', 'thailand'],
            'manila': ['manila', 'philippines'],
            'jakarta': ['jakarta', 'indonesia'],
            'kuala lumpur': ['kuala lumpur', 'malaysia'],
            
            # Latin America
            'mexico city': ['mexico city', 'mexico', 'mx', 'cdmx'],
            'sao paulo': ['sao paulo', 'brazil'],
            'buenos aires': ['buenos aires', 'argentina'],
            'santiago': ['santiago', 'chile'],
            'bogota': ['bogota', 'colombia'],
            
            # Other patterns
            'tel aviv': ['tel aviv', 'israel'],
            'emea': ['emea', 'europe', 'europe middle east africa'],
            'apac': ['apac', 'asia pacific', 'asia-pacific'],
            'latam': ['latam', 'latin america'],
            'mena': ['mena', 'middle east north africa']
        }
        
        # Cache for normalized locations to improve performance
        self._normalization_cache = {}
    
    def normalize_location(self, location: str) -> List[str]:
        """
        Normalize a location string into searchable parts.
        
        Args:
            location: Raw location string
            
        Returns:
            List of normalized location parts
        """
        if not location:
            return []
        
        # Check cache first
        if location in self._normalization_cache:
            return self._normalization_cache[location]
        
        # Clean up the location string
        cleaned = location.lower()
        
        # Remove common prefixes/suffixes
        cleaned = re.sub(r'^(us-|ca-|uk-)', '', cleaned)
        cleaned = re.sub(r'\s+(hq|headquarters)$', '', cleaned)
        
        # Replace special characters and normalize whitespace
        cleaned = re.sub(r'[^\w\s,;/-]', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Split on common separators
        parts = []
        for separator in [',', ';', ' and ', ' or ', '/']:
            if separator in cleaned:
                parts.extend([part.strip() for part in cleaned.split(separator)])
                break
        else:
            parts = [cleaned]
        
        # Filter out empty parts and common noise words
        noise_words = {'and', 'or', 'the', 'area', 'metro', 'region', 'greater'}
        normalized_parts = []
        
        for part in parts:
            part = part.strip()
            if part and part not in noise_words:
                normalized_parts.append(part)
        
        # Cache the result
        self._normalization_cache[location] = normalized_parts
        
        return normalized_parts
    
    def match_location(self, job_location: str, target_location: str) -> bool:
        """
        Check if a job location matches a target location using enhanced matching logic.
        
        Args:
            job_location: Location from job posting
            target_location: Location from user's alert criteria
            
        Returns:
            True if locations match, False otherwise
        """
        if not job_location or not target_location:
            return False
        
        job_parts = self.normalize_location(job_location)
        target_parts = self.normalize_location(target_location)
        
        if not job_parts or not target_parts:
            return False
        
        logger.debug(f"Matching job location '{job_location}' -> {job_parts} "
                    f"against target '{target_location}' -> {target_parts}")
        
        # Check direct matches first
        for job_part in job_parts:
            for target_part in target_parts:
                if job_part == target_part:
                    logger.debug(f"Direct match: '{job_part}' == '{target_part}'")
                    return True
                
                # Check substring matches (both directions)
                if job_part in target_part or target_part in job_part:
                    logger.debug(f"Substring match: '{job_part}' <-> '{target_part}'")
                    return True
        
        # Check against location mappings
        for canonical, aliases in self.location_mappings.items():
            job_matches = any(
                any(alias in job_part or job_part in alias for alias in aliases)
                for job_part in job_parts
            )
            target_matches = any(
                any(alias in target_part or target_part in alias for alias in aliases)
                for target_part in target_parts
            )
            
            if job_matches and target_matches:
                logger.debug(f"Alias match via '{canonical}': job={job_matches}, target={target_matches}")
                return True
        
        logger.debug(f"No match found between '{job_location}' and '{target_location}'")
        return False
    
    def is_remote_location(self, location: str) -> bool:
        """
        Check if a location indicates remote work.
        
        Args:
            location: Location string to check
            
        Returns:
            True if location indicates remote work
        """
        if not location:
            return False
        
        remote_indicators = [
            'remote', 'work from home', 'wfh', 'telecommute', 'distributed',
            'anywhere', 'virtual', 'home-based', 'home based'
        ]
        
        location_lower = location.lower()
        return any(indicator in location_lower for indicator in remote_indicators)
    
    def extract_unique_locations(self, locations: List[str]) -> List[str]:
        """
        Extract and deduplicate locations, handling aliases.
        
        Args:
            locations: List of raw location strings
            
        Returns:
            Deduplicated list of canonical location names
        """
        canonical_locations = set()
        
        for location in locations:
            if not location:
                continue
                
            # Try to find canonical form
            normalized_parts = self.normalize_location(location)
            found_canonical = False
            
            for part in normalized_parts:
                for canonical, aliases in self.location_mappings.items():
                    if any(alias in part or part in alias for alias in aliases):
                        canonical_locations.add(canonical.title())
                        found_canonical = True
                        break
                
                if found_canonical:
                    break
            
            # If no canonical form found, use the original (cleaned)
            if not found_canonical and normalized_parts:
                canonical_locations.add(' '.join(normalized_parts).title())
        
        return sorted(list(canonical_locations))
    
    def suggest_similar_locations(self, target_location: str, available_locations: List[str]) -> List[str]:
        """
        Suggest similar locations from available options.
        
        Args:
            target_location: Location user is looking for
            available_locations: Available location options
            
        Returns:
            List of similar location suggestions
        """
        if not target_location or not available_locations:
            return []
        
        suggestions = []
        target_parts = self.normalize_location(target_location)
        
        for location in available_locations:
            # Skip exact matches
            if self.match_location(location, target_location):
                continue
            
            location_parts = self.normalize_location(location)
            
            # Check for partial matches
            similarity_score = 0
            for target_part in target_parts:
                for location_part in location_parts:
                    if target_part in location_part or location_part in target_part:
                        similarity_score += 1
            
            if similarity_score > 0:
                suggestions.append((location, similarity_score))
        
        # Sort by similarity score and return top suggestions
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return [location for location, _ in suggestions[:5]]
