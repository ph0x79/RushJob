"""
API routes for RushJob.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from loguru import logger

from app.core.database import get_db
from app.models import Company, UserAlert, Job
from app.schemas.alerts import UserAlertCreate, UserAlertResponse, UserAlertUpdate
from app.schemas.companies import CompanyResponse
from app.schemas.jobs import JobResponse, JobResponseSimple
from app.services.greenhouse import VERIFIED_GREENHOUSE_COMPANIES, GreenhouseClient
from app.services.discord import DiscordNotifier
from app.services.poller import JobPollingService


router = APIRouter()


# Companies endpoints
@router.get("/companies", response_model=List[CompanyResponse])
async def get_companies(db: AsyncSession = Depends(get_db)):
    """Get list of available companies to monitor."""
    result = await db.execute(
        select(Company).where(Company.is_active == True).order_by(Company.name)
    )
    companies = result.scalars().all()
    return companies


@router.post("/companies/seed")
async def seed_companies(db: AsyncSession = Depends(get_db)):
    """Seed database with verified Greenhouse companies."""
    try:
        added_companies = []
        
        for company_data in VERIFIED_GREENHOUSE_COMPANIES:
            # Check if company already exists
            result = await db.execute(
                select(Company).where(Company.slug == company_data["slug"])
            )
            existing_company = result.scalar_one_or_none()
            
            if not existing_company:
                company = Company(
                    name=company_data["name"],
                    slug=company_data["slug"],
                    ats_type="greenhouse",
                    api_endpoint=f"https://boards-api.greenhouse.io/v1/boards/{company_data['slug']}/jobs"
                )
                db.add(company)
                added_companies.append(company_data["name"])
        
        await db.commit()
        
        return {
            "message": f"Added {len(added_companies)} companies",
            "companies": added_companies
        }
    except Exception as e:
        logger.error(f"Error seeding companies: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to seed companies: {str(e)}"
        )


@router.get("/debug/db")
async def debug_database():
    """Debug database connection."""
    try:
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            # Try a simple query
            result = await db.execute(text("SELECT 1 as test"))
            test_result = result.scalar()
            return {
                "database_connection": "success",
                "test_query_result": test_result
            }
    except Exception as e:
        return {
            "database_connection": "failed",
            "error": str(e),
            "error_type": type(e).__name__
        }


# User alerts endpoints
@router.post("/alerts", response_model=UserAlertResponse)
async def create_alert(
    alert_data: UserAlertCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Create a new job alert."""
    # Validate Discord webhook if provided
    if alert_data.discord_webhook_url:
        discord_notifier = DiscordNotifier()
        is_valid = await discord_notifier.test_webhook(alert_data.discord_webhook_url)
        await discord_notifier.close()
        
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail="Invalid Discord webhook URL. Please check the URL and try again."
            )
    
    # Create alert
    alert = UserAlert(
        user_id=alert_data.user_id,
        name=alert_data.name,
        company_slugs=alert_data.company_slugs,
        title_keywords=alert_data.title_keywords,
        title_exclude_keywords=alert_data.title_exclude_keywords,
        departments=alert_data.departments,
        locations=alert_data.locations,
        job_types=alert_data.job_types,
        include_remote=alert_data.include_remote,
        discord_webhook_url=alert_data.discord_webhook_url,
        email_address=alert_data.email_address,
        notification_frequency=alert_data.notification_frequency
    )
    
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    
    # Send initial notification in background
    if alert.discord_webhook_url:
        background_tasks.add_task(send_initial_notification, alert.id)
    
    return alert


@router.get("/alerts", response_model=List[UserAlertResponse])
async def get_user_alerts(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all alerts for a user."""
    result = await db.execute(
        select(UserAlert)
        .where(UserAlert.user_id == user_id)
        .order_by(UserAlert.created_at.desc())
    )
    alerts = result.scalars().all()
    return alerts


@router.get("/alerts/{alert_id}", response_model=UserAlertResponse)
async def get_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific alert by ID."""
    result = await db.execute(
        select(UserAlert).where(UserAlert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return alert


@router.put("/alerts/{alert_id}", response_model=UserAlertResponse)
async def update_alert(
    alert_id: int,
    alert_data: UserAlertUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing alert."""
    result = await db.execute(
        select(UserAlert).where(UserAlert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Validate Discord webhook if provided
    if alert_data.discord_webhook_url:
        discord_notifier = DiscordNotifier()
        is_valid = await discord_notifier.test_webhook(alert_data.discord_webhook_url)
        await discord_notifier.close()
        
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail="Invalid Discord webhook URL. Please check the URL and try again."
            )
    
    # Update fields
    update_data = alert_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(alert, field, value)
    
    await db.commit()
    await db.refresh(alert)
    
    return alert


@router.delete("/alerts/{alert_id}")
async def delete_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete an alert."""
    result = await db.execute(
        select(UserAlert).where(UserAlert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    await db.delete(alert)
    await db.commit()
    
    return {"message": "Alert deleted successfully"}


@router.get("/debug/jobs-count")
async def debug_jobs_count(db: AsyncSession = Depends(get_db)):
    """Simple endpoint to check job count."""
    try:
        from sqlalchemy import func
        result = await db.execute(
            select(func.count(Job.id)).where(Job.is_active == True)
        )
        count = result.scalar()
        return {"total_jobs": count}
    except Exception as e:
        return {"error": str(e)}


@router.get("/debug/jobs-simple")
async def debug_jobs_simple(limit: int = 5, db: AsyncSession = Depends(get_db)):
    """Simple jobs endpoint without response model."""
    try:
        result = await db.execute(
            select(Job.id, Job.title, Job.company_id)
            .where(Job.is_active == True)
            .order_by(Job.first_seen_at.desc())
            .limit(limit)
        )
        jobs = result.all()
        return {"jobs": [dict(row._mapping) for row in jobs]}
    except Exception as e:
        return {"error": str(e)}


# Jobs endpoints
@router.get("/jobs", response_model=List[JobResponseSimple])
async def get_jobs(
    company_slugs: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get recent jobs, optionally filtered by company."""
    try:
        query = select(Job).where(Job.is_active == True)
        
        if company_slugs:
            slug_list = company_slugs.split(",")
            companies_result = await db.execute(
                select(Company).where(Company.slug.in_(slug_list))
            )
            companies = companies_result.scalars().all()
            company_ids = [c.id for c in companies]
            query = query.where(Job.company_id.in_(company_ids))
        
        query = query.order_by(Job.first_seen_at.desc()).limit(limit)
        
        result = await db.execute(query)
        jobs = result.scalars().all()
        
        return jobs
    except Exception as e:
        logger.error(f"Error fetching jobs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch jobs: {str(e)}"
        )


@router.get("/jobs/{job_id}", response_model=JobResponseSimple)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific job by ID."""
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job


# Utility endpoints
@router.post("/test-webhook")
async def test_discord_webhook(webhook_url: str):
    """Test a Discord webhook URL."""
    discord_notifier = DiscordNotifier()
    is_valid = await discord_notifier.test_webhook(webhook_url)
    await discord_notifier.close()
    
    if is_valid:
        return {"message": "Webhook test successful"}
    else:
        raise HTTPException(
            status_code=400,
            detail="Webhook test failed. Please check the URL and try again."
        )


@router.post("/poll-now")
async def trigger_poll():
    """Manually trigger a polling cycle (for development/testing)."""
    try:
        polling_service = JobPollingService()
        stats = await polling_service.poll_once()
        await polling_service.close()
        
        return {
            "message": "Polling completed successfully",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Manual polling failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Polling failed: {str(e)}"
        )


# Background task functions
async def send_initial_notification(alert_id: int):
    """Send initial notification for a new alert."""
    try:
        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(UserAlert).where(UserAlert.id == alert_id)
            )
            alert = result.scalar_one_or_none()
            
            if alert:
                polling_service = JobPollingService()
                await polling_service.send_initial_alert_notification(db, alert)
                await polling_service.close()
                
    except Exception as e:
        logger.error(f"Error sending initial notification for alert {alert_id}: {e}")