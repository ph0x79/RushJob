"""
Greenhouse API client for fetching job postings.
"""
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any
import httpx
from loguru import logger
from app.core.config import settings


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
        if not metadata:
            # Fallback: guess from title if no metadata
            title_lower = self.title.lower()
            if "intern" in title_lower:
                return "Intern"
            elif "contract" in title_lower:
                return "Contract"
            elif "part-time" in title_lower or "part time" in title_lower:
                return "Part-time"
            else:
                return "Full-time"
        
        for item in metadata:
            if item and item.get("name", "").lower() in ["employment_type", "job_type"]:
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
        """Check if job is remote using basic detection."""
        return "remote" in self.location.lower()


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
# Updated based on comprehensive testing - January 2025
VERIFIED_GREENHOUSE_COMPANIES = [
    # Original verified companies (high job counts)
    {"name": "Stripe", "slug": "stripe"},              # Confirmed working
    {"name": "Airbnb", "slug": "airbnb"},              # Confirmed working
    {"name": "Robinhood", "slug": "robinhood"},        # Confirmed working
    {"name": "Peloton", "slug": "peloton"},            # Confirmed working
    {"name": "Dropbox", "slug": "dropbox"},            # Confirmed working
    {"name": "Coinbase", "slug": "coinbase"},          # Confirmed working
    {"name": "Reddit", "slug": "reddit"},              # Confirmed working
    {"name": "Lyft", "slug": "lyft"},                  # Confirmed working
    {"name": "DoorDash", "slug": "doordashusa"},       # Confirmed working (fixed slug)
    {"name": "Pinterest", "slug": "pinterest"},        # Confirmed working
    {"name": "Databricks", "slug": "databricks"},      # Confirmed working
    {"name": "Figma", "slug": "figma"},                # Confirmed working
    {"name": "Discord", "slug": "discord"},            # Confirmed working
    {"name": "Twitch", "slug": "twitch"},              # Confirmed working
    
    # High-value additional companies (discovered via testing)
    {"name": "Brex", "slug": "brex"},                  # 146 jobs
    {"name": "Instacart", "slug": "instacart"},        # 121 jobs
    {"name": "Asana", "slug": "asana"},                # 95 jobs
    {"name": "Flexport", "slug": "flexport"},          # 75 jobs
    {"name": "Gusto", "slug": "gusto"},                # 69 jobs
    {"name": "Checkr", "slug": "checkr"},              # 63 jobs
    {"name": "Amplitude", "slug": "amplitude"},        # 48 jobs
    {"name": "Airtable", "slug": "airtable"},          # 47 jobs
    {"name": "Mixpanel", "slug": "mixpanel"},          # 45 jobs
    {"name": "Nextdoor", "slug": "nextdoor"},          # 36 jobs
    {"name": "Thumbtack", "slug": "thumbtack"},        # 27 jobs
    
    # Newly discovered high-value companies (January 2025)
    {"name": "TripAdvisor", "slug": "tripadvisor"},    # 148 jobs
    {"name": "Bird", "slug": "bird"},                  # 101 jobs
    {"name": "Chime", "slug": "chime"},                # 53 jobs
    {"name": "Kayak", "slug": "kayak"},                # 52 jobs
    {"name": "Mercury", "slug": "mercury"},            # 45 jobs
    {"name": "Industrious", "slug": "industrious"},    # 42 jobs
    {"name": "Strava", "slug": "strava"},              # 26 jobs
    
    # Companies that may need verification or have been problematic
    # {"name": "Notion", "slug": "notion"},            # May have moved to AshbyHQ
    # {"name": "Roblox", "slug": "roblox"},            # May use enterprise ATS
    # {"name": "Epic Games", "slug": "epicgames"},     # May use custom ATS
    
    # Companies confirmed NOT to use Greenhouse (remove these)
    # {"name": "Canva", "slug": "canva"},              # Uses SmartRecruiters
    # {"name": "Shopify", "slug": "shopify"},          # Uses custom ATS
    # {"name": "Snowflake", "slug": "snowflake"},      # Uses AshbyHQ
]