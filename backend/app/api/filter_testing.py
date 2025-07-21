"""
Filter testing endpoints to validate job matching logic.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from app.core.database import get_db
from app.models import Job, Company, UserAlert
from app.services.matcher import JobMatcher
from app.services.location_matcher import LocationMatcher

router = APIRouter()

@router.get("/test-filters/location-matching")
async def test_location_matching(db: AsyncSession = Depends(get_db)):
    """Test location matching with real job data."""
    
    # Get jobs with complex locations (like Stripe)
    result = await db.execute(
        select(Job, Company).join(Company)
        .where(Company.slug == "stripe")
        .limit(10)
    )
    jobs_with_companies = result.all()
    
    location_matcher = LocationMatcher()
    test_cases = []
    
    for job, company in jobs_with_companies:
        if job.location:
            # Test common location patterns
            test_patterns = ["Remote", "San Francisco", "New York", "NYC", "SF", "Seattle"]
            
            matches = {}
            for pattern in test_patterns:
                matches[pattern] = location_matcher.match_location(job.location, pattern)
            
            test_cases.append({
                "job_title": job.title,
                "job_location": job.location,
                "company": company.name,
                "matches": matches,
                "is_remote": location_matcher.is_remote_location(job.location),
                "normalized": location_matcher.normalize_location(job.location)
            })
    
    return {
        "test_type": "location_matching",
        "total_jobs_tested": len(test_cases),
        "test_cases": test_cases
    }

@router.post("/test-filters/create-test-alert")
async def create_test_alert(
    alert_criteria: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Create a test alert and see what jobs it matches."""
    
    # Create a temporary alert object (don't save to DB)
    test_alert = UserAlert(
        user_id="test-user",
        name="Test Alert",
        company_slugs=alert_criteria.get("company_slugs", []),
        title_keywords=alert_criteria.get("title_keywords", []),
        title_exclude_keywords=alert_criteria.get("title_exclude_keywords", []),
        departments=alert_criteria.get("departments", []),
        locations=alert_criteria.get("locations", []),
        job_types=alert_criteria.get("job_types", []),
        include_remote=alert_criteria.get("include_remote", True)
    )
    
    # Get recent jobs to test against
    jobs_result = await db.execute(
        select(Job, Company).join(Company)
        .where(Job.is_active == True)
        .order_by(Job.first_seen_at.desc())
        .limit(100)
    )
    jobs_with_companies = jobs_result.all()
    
    # Test matching
    matcher = JobMatcher(db)
    matching_jobs = []
    non_matching_jobs = []
    
    for job, company in jobs_with_companies:
        job.company = company  # Add company relation for matching
        
        if await matcher._job_matches_alert(job, test_alert):
            matching_jobs.append({
                "id": job.id,
                "title": job.title,
                "company": company.name,
                "location": job.location,
                "department": job.department,
                "job_type": job.job_type
            })
        else:
            non_matching_jobs.append({
                "id": job.id,
                "title": job.title,
                "company": company.name,
                "location": job.location,
                "reason": "failed_criteria_check"
            })
    
    return {
        "test_alert_criteria": alert_criteria,
        "total_jobs_tested": len(jobs_with_companies),
        "matching_jobs_count": len(matching_jobs),
        "non_matching_jobs_count": len(non_matching_jobs),
        "matching_jobs": matching_jobs[:20],  # First 20 matches
        "sample_non_matching": non_matching_jobs[:10]  # First 10 non-matches
    }

@router.get("/test-filters/data-quality")
async def test_data_quality(db: AsyncSession = Depends(get_db)):
    """Test data quality and parsing accuracy."""
    
    # Get stats on data completeness
    total_jobs = await db.execute(select(func.count(Job.id)).where(Job.is_active == True))
    total_count = total_jobs.scalar()
    
    # Jobs with various fields populated
    jobs_with_location = await db.execute(
        select(func.count(Job.id)).where(Job.is_active == True, Job.location.isnot(None), Job.location != "")
    )
    
    jobs_with_department = await db.execute(
        select(func.count(Job.id)).where(Job.is_active == True, Job.department.isnot(None), Job.department != "")
    )
    
    jobs_with_job_type = await db.execute(
        select(func.count(Job.id)).where(Job.is_active == True, Job.job_type.isnot(None), Job.job_type != "")
    )
    
    # Sample of jobs for manual review
    sample_jobs = await db.execute(
        select(Job, Company).join(Company)
        .where(Job.is_active == True)
        .order_by(Job.first_seen_at.desc())
        .limit(20)
    )
    
    sample_data = []
    for job, company in sample_jobs.all():
        sample_data.append({
            "company": company.name,
            "title": job.title,
            "location": job.location,
            "department": job.department,
            "job_type": job.job_type,
            "has_location": bool(job.location and job.location.strip()),
            "has_department": bool(job.department and job.department.strip()),
            "has_job_type": bool(job.job_type and job.job_type.strip())
        })
    
    return {
        "data_quality_stats": {
            "total_jobs": total_count,
            "jobs_with_location": jobs_with_location.scalar(),
            "jobs_with_department": jobs_with_department.scalar(),
            "jobs_with_job_type": jobs_with_job_type.scalar(),
            "location_coverage": round(jobs_with_location.scalar() / total_count * 100, 1),
            "department_coverage": round(jobs_with_department.scalar() / total_count * 100, 1),
            "job_type_coverage": round(jobs_with_job_type.scalar() / total_count * 100, 1)
        },
        "sample_jobs": sample_data
    }

@router.get("/test-filters/location-patterns")
async def test_location_patterns(db: AsyncSession = Depends(get_db)):
    """Test location parsing patterns from real data."""
    
    # Get unique locations to see parsing patterns
    locations_result = await db.execute(
        select(Job.location, func.count(Job.id).label('count'))
        .where(Job.is_active == True, Job.location.isnot(None), Job.location != "")
        .group_by(Job.location)
        .order_by(func.count(Job.id).desc())
        .limit(50)
    )
    
    location_matcher = LocationMatcher()
    location_analysis = []
    
    for location, count in locations_result.all():
        normalized = location_matcher.normalize_location(location)
        is_remote = location_matcher.is_remote_location(location)
        
        # Test matching against common patterns
        test_matches = {}
        test_patterns = ["Remote", "San Francisco", "New York", "London", "Seattle", "Chicago"]
        for pattern in test_patterns:
            test_matches[pattern] = location_matcher.match_location(location, pattern)
        
        location_analysis.append({
            "original_location": location,
            "job_count": count,
            "normalized": normalized,
            "is_remote": is_remote,
            "test_matches": test_matches
        })
    
    return {
        "total_unique_locations": len(location_analysis),
        "location_patterns": location_analysis
    }
