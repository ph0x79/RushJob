"""
Service for matching jobs against user alerts.
"""
from typing import List, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.models import Job, UserAlert, Company
from app.services.greenhouse import GreenhouseJob


class JobMatcher:
    """Matches jobs against user-defined alert criteria."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
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
        # Check company filter
        if alert.company_slugs and job.company.slug not in alert.company_slugs:
            return False
        
        # Check title keywords (must include at least one)
        if alert.title_keywords:
            title_lower = job.title.lower()
            if not any(keyword.lower() in title_lower for keyword in alert.title_keywords):
                return False
        
        # Check title exclude keywords (must not include any)
        if alert.title_exclude_keywords:
            title_lower = job.title.lower()
            if any(keyword.lower() in title_lower for keyword in alert.title_exclude_keywords):
                return False
        
        # Check department filter
        if alert.departments and job.department:
            if job.department not in alert.departments:
                return False
        
        # Check location filter
        if alert.locations and job.location:
            location_matches = False
            job_location_lower = job.location.lower()
            
            for location in alert.locations:
                if location.lower() in job_location_lower:
                    location_matches = True
                    break
            
            # If remote is included and job is remote, that's also a match
            if not location_matches and alert.include_remote and "remote" in job_location_lower:
                location_matches = True
            
            if not location_matches:
                return False
        
        # Check job type filter
        if alert.job_types and job.job_type:
            if job.job_type not in alert.job_types:
                return False
        
        # Check remote preference
        if not alert.include_remote and job.location and "remote" in job.location.lower():
            return False
        
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
        locations = set()
        job_types = set()
        
        for job in jobs:
            if job.department:
                departments.add(job.department)
            if job.location:
                locations.add(job.location)
            if job.job_type:
                job_types.add(job.job_type)
        
        return {
            "departments": sorted(list(departments)),
            "locations": sorted(list(locations)),
            "job_types": sorted(list(job_types))
        }