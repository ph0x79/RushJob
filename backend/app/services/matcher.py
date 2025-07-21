"""
Service for matching jobs against user alerts.
"""
from typing import List, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.models import Job, UserAlert, Company
from app.services.greenhouse import GreenhouseJob
from app.services.location_matcher import LocationMatcher


class JobMatcher:
    """Matches jobs against user-defined alert criteria."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.location_matcher = LocationMatcher()
    
    async def find_matching_alerts(self, job: Job) -> List[UserAlert]:
        """
        Find all user alerts that match a given job.
        
        Args:
            job: Job instance to match against
            
        Returns:
            List of UserAlert instances that match the job
        """
        # Fetch all active alerts
        result = await self.db.execute(
            select(UserAlert).where(UserAlert.is_active == True)
        )
        alerts = result.scalars().all()
        
        matching_alerts = []
        
        for alert in alerts:
            if await self._job_matches_alert(job, alert):
                matching_alerts.append(alert)
        
        logger.info(f"Job '{job.title}' at {job.company.name} matches {len(matching_alerts)} alerts")
        return matching_alerts
    
    async def _job_matches_alert(self, job: Job, alert: UserAlert) -> bool:
        """
        Check if a job matches an alert's criteria.
        
        Args:
            job: Job to check
            alert: Alert with criteria to match against
            
        Returns:
            True if job matches alert criteria, False otherwise
        """
        # Check company filter - if alert has no companies specified, include all
        if alert.company_slugs:
            # Load company relationship if we need to check it
            company_result = await self.db.execute(
                select(Company).where(Company.id == job.company_id)
            )
            company = company_result.scalar_one_or_none()
            if not company or company.slug not in alert.company_slugs:
                logger.debug(f"Job '{job.title}' rejected: company filter mismatch")
                return False
        
        # Check title keywords (must include at least one)
        if alert.title_keywords:
            title_lower = job.title.lower()
            matched_keywords = [kw for kw in alert.title_keywords if kw.lower() in title_lower]
            if not matched_keywords:
                logger.debug(f"Job '{job.title}' rejected: no matching keywords from {alert.title_keywords}")
                return False
            else:
                logger.debug(f"Job '{job.title}' matched keywords: {matched_keywords}")
        
        # Check title exclude keywords (must not include any)
        if alert.title_exclude_keywords:
            title_lower = job.title.lower()
            excluded_keywords = [kw for kw in alert.title_exclude_keywords if kw.lower() in title_lower]
            if excluded_keywords:
                logger.debug(f"Job '{job.title}' rejected: contains excluded keywords {excluded_keywords}")
                return False
        
        # Check department filter
        if alert.departments and job.department:
            if job.department not in alert.departments:
                logger.debug(f"Job '{job.title}' rejected: department '{job.department}' not in {alert.departments}")
                return False
            else:
                logger.debug(f"Job '{job.title}' matched department: {job.department}")
        
        # Enhanced location matching
        if alert.locations and job.location:
            location_matches = False
            
            for alert_location in alert.locations:
                if self.location_matcher.match_location(job.location, alert_location):
                    logger.debug(f"Job '{job.title}' location '{job.location}' matches alert location '{alert_location}'")
                    location_matches = True
                    break
            
            # Special handling for remote preference
            if not location_matches and alert.include_remote:
                if self.location_matcher.is_remote_location(job.location):
                    logger.debug(f"Job '{job.title}' matched via remote inclusion: '{job.location}'")
                    location_matches = True
            
            if not location_matches:
                logger.debug(f"Job '{job.title}' rejected: location '{job.location}' doesn't match any of {alert.locations}")
                return False
        
        # Check job type filter
        if alert.job_types and job.job_type:
            if job.job_type not in alert.job_types:
                logger.debug(f"Job '{job.title}' rejected: job type '{job.job_type}' not in {alert.job_types}")
                return False
            else:
                logger.debug(f"Job '{job.title}' matched job type: {job.job_type}")
        
        # Check remote preference (exclude remote jobs if not wanted)
        if not alert.include_remote and job.location:
            if self.location_matcher.is_remote_location(job.location):
                logger.debug(f"Job '{job.title}' rejected: remote job but remote not included")
                return False
        
        logger.debug(f"Job '{job.title}' ACCEPTED by alert '{alert.name}'")
        return True
    
    def get_unique_values_from_jobs(self, jobs: List[Job]) -> dict:
        """
        Extract unique values for departments, locations, and job types from a list of jobs.
        Useful for building filter options in the UI.
        
        Args:
            jobs: List of Job instances
            
        Returns:
            Dictionary with sets of unique values for each field
        """
        departments = set()
        raw_locations = []
        job_types = set()
        
        for job in jobs:
            if job.department:
                departments.add(job.department)
            if job.location:
                raw_locations.append(job.location)
            if job.job_type:
                job_types.add(job.job_type)
        
        # Use enhanced location processing
        unique_locations = self.location_matcher.extract_unique_locations(raw_locations)
        
        return {
            "departments": sorted(list(departments)),
            "locations": unique_locations,  # Already sorted by the location matcher
            "job_types": sorted(list(job_types))
        }
    
    def suggest_similar_locations(self, target_location: str, available_jobs: List[Job]) -> List[str]:
        """
        Suggest similar locations based on available jobs.
        
        Args:
            target_location: Location user is searching for
            available_jobs: List of available jobs to extract locations from
            
        Returns:
            List of suggested similar locations
        """
        available_locations = [job.location for job in available_jobs if job.location]
        return self.location_matcher.suggest_similar_locations(target_location, available_locations)
    
    def debug_location_matching(self, job_location: str, alert_locations: List[str]) -> dict:
        """
        Debug location matching for troubleshooting.
        
        Args:
            job_location: Job location to test
            alert_locations: List of alert locations to test against
            
        Returns:
            Dictionary with detailed matching information
        """
        results = {
            "job_location": job_location,
            "job_location_normalized": self.location_matcher.normalize_location(job_location),
            "job_location_is_remote": self.location_matcher.is_remote_location(job_location),
            "alert_locations": [],
            "any_match": False
        }
        
        for alert_location in alert_locations:
            match_result = {
                "alert_location": alert_location,
                "normalized": self.location_matcher.normalize_location(alert_location),
                "matches": self.location_matcher.match_location(job_location, alert_location)
            }
            results["alert_locations"].append(match_result)
            
            if match_result["matches"]:
                results["any_match"] = True
        
        return results
