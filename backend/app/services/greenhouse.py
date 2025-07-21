"""
Greenhouse API client for fetching job postings.
"""
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any
import httpx
from loguru import logger
from app.core.config import settings
from app.services.location_matcher import LocationMatcher


class GreenhouseJob:
    """Represents a job from Greenhouse API."""
    
    def __init__(self, data: Dict[str, Any]):
        self.raw_data = data
        self.id = str(data.get("id", ""))
        self.title = data.get("title", "")
        self.location = self._parse_location(data.get("location", {}))
        self.department = self._parse_department(data.get("departments", []))
        self.absolute_url = data.get("absolute_url", "")
        self.job_type = self._parse_job_type(data.get("metadata", []))
        
        # Initialize location matcher for enhanced detection
        self._location_matcher = None
        
    def _parse_location(self, location_data: Dict[str, Any]) -> str:
        """Parse location from Greenhouse format with enhanced normalization."""
        if not location_data:
            return ""
        
        name = location_data.get("name", "")
        if not name:
            return ""
        
        # Basic remote detection without LocationMatcher during init
        if "remote" in name.lower():
            return "Remote"
        
        # Clean up common location format issues
        # Handle patterns like "US-NYC", "CA-Toronto", etc.
        if "-" in name and len(name.split("-")) == 2:
            prefix, location = name.split("-", 1)
            if prefix.upper() in ["US", "CA", "UK", "DE", "FR", "AU"]:
                return location.strip()
        
        return name.strip()
    
    def _parse_department(self, departments: List[Dict[str, Any]]) -> str:
        """Extract primary department name."""
        if not departments:
            return ""
        return departments[0].get("name", "")
    
    def _parse_job_type(self, metadata: List[Dict[str, Any]]) -> str:
        """Extract job type from metadata."""
        for item in metadata:
            if item.get("name", "").lower() in ["employment_type", "job_type"]:
                return item.get("value", "")
        
        # Fallback: guess from title
        title_lower = self.title.lower()
        if "intern" in title_lower:
            return "Intern"
        elif "contract" in title_lower:
            return "Contract"
        elif "part-time" in title_lower or "part time" in title_lower:
            return "Part-time"
        else:
            return "Full-time"
    
    def content_hash(self) -> str:
        """Generate hash for change detection."""
        content = f"{self.title}|{self.location}|{self.department}|{self.job_type}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def is_remote(self) -> bool:
        """Check if job is remote using enhanced detection."""
        if self._location_matcher is None:
            from app.services.location_matcher import LocationMatcher
            self._location_matcher = LocationMatcher()
        return self._location_matcher.is_remote_location(self.location)


class GreenhouseClient:
    """Client for interacting with Greenhouse job board API."""
    
    def __init__(self):
        self.base_url = "https://boards-api.greenhouse.io/v1/boards"
        # Add headers that some companies might require
        headers = {
            "User-Agent": "RushJob/1.0",
            "Accept": "application/json",
        }
        self.client = httpx.AsyncClient(
            timeout=settings.request_timeout_seconds,
            limits=httpx.Limits(max_connections=settings.max_concurrent_polls),
            headers=headers
        )
    
    async def fetch_jobs(self, company_slug: str) -> List[GreenhouseJob]:
        """
        Fetch all jobs for a company from Greenhouse API.
        
        Args:
            company_slug: Company identifier (e.g., 'stripe', 'airbnb')
            
        Returns:
            List of GreenhouseJob objects
            
        Raises:
            httpx.HTTPStatusError: If API request fails
            httpx.TimeoutException: If request times out
        """
        url = f"{self.base_url}/{company_slug}/jobs"
        
        try:
            logger.info(f"Fetching jobs for {company_slug} from {url}")
            response = await self.client.get(url)
            response.raise_for_status()
            
            data = response.json()
            jobs_data = data.get("jobs", [])
            
            # Debug logging for problematic companies
            if company_slug in ["stripe", "figma", "notion", "twitch"]:
                logger.info(f"API response for {company_slug}: status={response.status_code}, data_keys={list(data.keys()) if isinstance(data, dict) else 'not_dict'}")
                logger.info(f"Jobs data type: {type(jobs_data)}, length: {len(jobs_data) if jobs_data else 'None'}")
            
            if not jobs_data:
                logger.warning(f"No jobs found for {company_slug}. Response data: {data}")
                return []
            
            jobs = [GreenhouseJob(job_data) for job_data in jobs_data]
            logger.info(f"Found {len(jobs)} jobs for {company_slug}")
            
            return jobs
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching jobs for {company_slug}: {e}")
            if e.response.status_code == 404:
                logger.warning(f"Company {company_slug} not found on Greenhouse")
            raise
        except httpx.TimeoutException as e:
            logger.error(f"Timeout fetching jobs for {company_slug}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching jobs for {company_slug}: {e}")
            raise
    
    async def test_company_endpoint(self, company_slug: str) -> bool:
        """
        Test if a company has a valid Greenhouse endpoint.
        
        Args:
            company_slug: Company identifier to test
            
        Returns:
            True if endpoint is valid and accessible, False otherwise
        """
        try:
            jobs = await self.fetch_jobs(company_slug)
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return False
            # Other HTTP errors might be temporary, so we return True
            return True
        except Exception:
            return False
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()


# Predefined list of companies with verified Greenhouse endpoints
VERIFIED_GREENHOUSE_COMPANIES = [
    {"name": "Stripe", "slug": "stripe"},
    {"name": "Airbnb", "slug": "airbnb"},
    {"name": "Robinhood", "slug": "robinhood"},
    {"name": "Peloton", "slug": "peloton"},
    {"name": "Dropbox", "slug": "dropbox"},
    {"name": "Coinbase", "slug": "coinbase"},
    {"name": "Reddit", "slug": "reddit"},
    {"name": "Lyft", "slug": "lyft"},
    {"name": "DoorDash", "slug": "doordashusa"},  # Fixed slug
    {"name": "Pinterest", "slug": "pinterest"},
    # {"name": "Snowflake", "slug": "snowflake"},  # Uses AshbyHQ
    {"name": "Databricks", "slug": "databricks"},
    {"name": "Figma", "slug": "figma"},
    {"name": "Notion", "slug": "notion"},
    # {"name": "Canva", "slug": "canva"},  # Uses SmartRecruiters
    {"name": "Discord", "slug": "discord"},
    {"name": "Twitch", "slug": "twitch"},
    {"name": "Roblox", "slug": "roblox"},
    {"name": "Epic Games", "slug": "epicgames"},
    # {"name": "Shopify", "slug": "shopify"},  # Different ATS
]