"""
Main job polling orchestrator service.
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from loguru import logger

from app.core.database import AsyncSessionLocal
from app.models import Company, Job, UserAlert, Notification, PollLog
from app.services.greenhouse import GreenhouseClient, GreenhouseJob
from app.services.matcher import JobMatcher
from app.services.discord import DiscordNotifier


class JobPollingService:
    """Orchestrates the job polling process for all companies."""
    
    def __init__(self):
        self.greenhouse_client = GreenhouseClient()
        self.discord_notifier = DiscordNotifier()
    
    async def poll_all_companies(self) -> Dict[str, any]:
        """
        Poll all active companies for new jobs and send notifications.
        
        Returns:
            Summary statistics of the polling operation
        """
        stats = {
            "companies_polled": 0,
            "companies_successful": 0,
            "companies_failed": 0,
            "total_jobs_found": 0,
            "new_jobs": 0,
            "updated_jobs": 0,
            "notifications_sent": 0,
            "notifications_failed": 0,
            "started_at": datetime.utcnow(),
            "completed_at": None
        }
        
        async with AsyncSessionLocal() as db:
            try:
                # Get companies that should be polled
                companies = await self._get_companies_to_poll(db)
                stats["companies_polled"] = len(companies)
                
                logger.info(f"Starting poll cycle for {len(companies)} companies")
                
                # Poll each company
                for company in companies:
                    company_stats = await self._poll_company(db, company)
                    
                    if company_stats["success"]:
                        stats["companies_successful"] += 1
                    else:
                        stats["companies_failed"] += 1
                    
                    stats["total_jobs_found"] += company_stats["jobs_found"]
                    stats["new_jobs"] += company_stats["new_jobs"]
                    stats["updated_jobs"] += company_stats["updated_jobs"]
                    stats["notifications_sent"] += company_stats["notifications_sent"]
                    stats["notifications_failed"] += company_stats["notifications_failed"]
                
                stats["completed_at"] = datetime.utcnow()
                duration = (stats["completed_at"] - stats["started_at"]).total_seconds()
                
                logger.info(f"Poll cycle completed in {duration:.2f}s: "
                          f"{stats['companies_successful']}/{stats['companies_polled']} companies successful, "
                          f"{stats['new_jobs']} new jobs, {stats['notifications_sent']} notifications sent")
                
                return stats
                
            except Exception as e:
                logger.error(f"Error during poll cycle: {e}")
                stats["completed_at"] = datetime.utcnow()
                raise
    
    async def _get_companies_to_poll(self, db: AsyncSession) -> List[Company]:
        """
        Get list of companies that should be polled based on their schedule.
        
        Args:
            db: Database session
            
        Returns:
            List of Company instances ready to be polled
        """
        now = datetime.utcnow()
        
        # Select companies that:
        # 1. Are active
        # 2. Haven't been polled recently (based on their poll interval)
        # 3. Are Greenhouse companies (for MVP)
        result = await db.execute(
            select(Company).where(
                Company.is_active == True,
                Company.ats_type == "greenhouse",
                (Company.last_polled_at.is_(None) | 
                 (Company.last_polled_at < now - timedelta(minutes=Company.poll_interval_minutes)))
            )
        )
        
        return list(result.scalars().all())
    
    async def _poll_company(self, db: AsyncSession, company: Company) -> Dict[str, any]:
        """
        Poll a single company for jobs and process results.
        
        Args:
            db: Database session
            company: Company to poll
            
        Returns:
            Statistics about the polling operation
        """
        stats = {
            "success": False,
            "jobs_found": 0,
            "new_jobs": 0,
            "updated_jobs": 0,
            "notifications_sent": 0,
            "notifications_failed": 0
        }
        
        # Create poll log entry
        poll_log = PollLog(
            company_id=company.id,
            status="running"
        )
        db.add(poll_log)
        await db.commit()
        
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Polling {company.name} ({company.slug})")
            
            # Fetch jobs from Greenhouse
            greenhouse_jobs = await self.greenhouse_client.fetch_jobs(company.slug)
            stats["jobs_found"] = len(greenhouse_jobs)
            
            # Process each job
            for gh_job in greenhouse_jobs:
                job_result = await self._process_job(db, company, gh_job)
                
                if job_result["is_new"]:
                    stats["new_jobs"] += 1
                elif job_result["is_updated"]:
                    stats["updated_jobs"] += 1
                
                stats["notifications_sent"] += job_result["notifications_sent"]
                stats["notifications_failed"] += job_result["notifications_failed"]
            
            # Update company last polled time
            await db.execute(
                update(Company)
                .where(Company.id == company.id)
                .values(last_polled_at=datetime.utcnow())
            )
            
            # Update poll log
            end_time = datetime.utcnow()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            poll_log.completed_at = end_time
            poll_log.status = "success"
            poll_log.jobs_found = stats["jobs_found"]
            poll_log.new_jobs = stats["new_jobs"]
            poll_log.updated_jobs = stats["updated_jobs"]
            poll_log.response_time_ms = response_time_ms
            
            await db.commit()
            stats["success"] = True
            
            logger.info(f"Successfully polled {company.name}: "
                       f"{stats['jobs_found']} jobs, {stats['new_jobs']} new, {stats['updated_jobs']} updated")
            
        except Exception as e:
            # Update poll log with error
            poll_log.completed_at = datetime.utcnow()
            poll_log.status = "error"
            poll_log.error_message = str(e)
            await db.commit()
            
            logger.error(f"Error polling {company.name}: {e}")
        
        return stats
    
    async def _process_job(self, db: AsyncSession, company: Company, gh_job: GreenhouseJob) -> Dict[str, any]:
        """
        Process a single job: create/update in database and send notifications.
        
        Args:
            db: Database session
            company: Company the job belongs to
            gh_job: Greenhouse job data
            
        Returns:
            Processing statistics
        """
        result = {
            "is_new": False,
            "is_updated": False,
            "notifications_sent": 0,
            "notifications_failed": 0
        }
        
        # Check if job already exists
        existing_job_result = await db.execute(
            select(Job).where(
                Job.company_id == company.id,
                Job.external_id == gh_job.id
            )
        )
        existing_job = existing_job_result.scalar_one_or_none()
        
        content_hash = gh_job.content_hash()
        
        if existing_job is None:
            # New job - create it
            job = Job(
                company_id=company.id,
                external_id=gh_job.id,
                title=gh_job.title,
                department=gh_job.department,
                location=gh_job.location,
                job_type=gh_job.job_type,
                external_url=gh_job.absolute_url,
                content_hash=content_hash,
                raw_data=gh_job.raw_data
            )
            db.add(job)
            await db.flush()  # Get the job ID
            result["is_new"] = True
            
            # Send notifications for new job
            notification_stats = await self._send_job_notifications(db, job, is_new=True)
            result["notifications_sent"] = notification_stats["sent"]
            result["notifications_failed"] = notification_stats["failed"]
            
        elif existing_job.content_hash != content_hash:
            # Job was updated - update it
            existing_job.title = gh_job.title
            existing_job.department = gh_job.department
            existing_job.location = gh_job.location
            existing_job.job_type = gh_job.job_type
            existing_job.external_url = gh_job.absolute_url
            existing_job.content_hash = content_hash
            existing_job.raw_data = gh_job.raw_data
            existing_job.last_seen_at = datetime.utcnow()
            result["is_updated"] = True
            
            # Send notifications for updated job
            notification_stats = await self._send_job_notifications(db, existing_job, is_new=False)
            result["notifications_sent"] = notification_stats["sent"]
            result["notifications_failed"] = notification_stats["failed"]
            
        else:
            # Job unchanged - just update last_seen_at
            existing_job.last_seen_at = datetime.utcnow()
        
        return result
    
    async def _send_job_notifications(self, db: AsyncSession, job: Job, is_new: bool) -> Dict[str, int]:
        """
        Send notifications for a job to all matching alerts.
        
        Args:
            db: Database session
            job: Job to send notifications for
            is_new: Whether this is a new job or an update
            
        Returns:
            Dictionary with counts of sent and failed notifications
        """
        stats = {"sent": 0, "failed": 0}
        
        # Find matching alerts
        matcher = JobMatcher(db)
        matching_alerts = await matcher.find_matching_alerts(job)
        
        for alert in matching_alerts:
            # Check if we've already notified this alert about this job
            existing_notification = await db.execute(
                select(Notification).where(
                    Notification.alert_id == alert.id,
                    Notification.job_id == job.id
                )
            )
            
            if existing_notification.scalar_one_or_none():
                continue  # Already notified about this job
            
            # Send Discord notification if configured
            if alert.discord_webhook_url:
                success = await self.discord_notifier.send_job_notification(
                    webhook_url=alert.discord_webhook_url,
                    jobs=[job],
                    alert=alert,
                    is_initial=False
                )
                
                # Record notification attempt
                notification = Notification(
                    alert_id=alert.id,
                    job_id=job.id,
                    notification_type="discord",
                    status="sent" if success else "failed"
                )
                db.add(notification)
                
                if success:
                    stats["sent"] += 1
                    # Update alert last notified time
                    alert.last_notified_at = datetime.utcnow()
                else:
                    stats["failed"] += 1
        
        return stats
    
    async def send_initial_alert_notification(self, db: AsyncSession, alert: UserAlert) -> bool:
        """
        Send initial notification when a user creates a new alert.
        Shows all existing jobs that match their criteria.
        
        Args:
            db: Database session
            alert: Newly created UserAlert
            
        Returns:
            True if notification was sent successfully
        """
        try:
            # Find all existing jobs that match the alert
            matcher = JobMatcher(db)
            
            # Get all active jobs for companies in the alert
            if alert.company_slugs:
                companies_result = await db.execute(
                    select(Company).where(Company.slug.in_(alert.company_slugs))
                )
                companies = companies_result.scalars().all()
                company_ids = [c.id for c in companies]
                
                jobs_result = await db.execute(
                    select(Job).where(
                        Job.company_id.in_(company_ids),
                        Job.is_active == True
                    )
                )
                jobs = jobs_result.scalars().all()
                
                # Filter jobs that match alert criteria
                matching_jobs = []
                for job in jobs:
                    if await matcher._job_matches_alert(job, alert):
                        matching_jobs.append(job)
                
                if matching_jobs and alert.discord_webhook_url:
                    # Send initial notification
                    success = await self.discord_notifier.send_job_notification(
                        webhook_url=alert.discord_webhook_url,
                        jobs=matching_jobs,
                        alert=alert,
                        is_initial=True
                    )
                    
                    if success:
                        # Record notifications for all jobs
                        for job in matching_jobs:
                            notification = Notification(
                                alert_id=alert.id,
                                job_id=job.id,
                                notification_type="discord",
                                status="sent"
                            )
                            db.add(notification)
                        
                        alert.last_notified_at = datetime.utcnow()
                        await db.commit()
                    
                    return success
                
            return True  # No matching jobs or no Discord webhook is still "successful"
            
        except Exception as e:
            logger.error(f"Error sending initial alert notification: {e}")
            return False
    
    async def poll_once(self) -> Dict[str, any]:
        """
        Run a single poll cycle manually.
        
        Returns:
            Polling statistics
        """
        return await self.poll_all_companies()

    async def close(self) -> None:
        """Close all client connections."""
        await self.greenhouse_client.close()
        await self.discord_notifier.close()


class PollingScheduler:
    """Manages the background polling schedule."""
    
    def __init__(self):
        self.polling_service = JobPollingService()
        self.is_running = False
    
    async def start_polling(self, interval_minutes: int = 15) -> None:
        """
        Start the background polling loop.
        
        Args:
            interval_minutes: How often to poll in minutes
        """
        self.is_running = True
        logger.info(f"Starting job polling scheduler with {interval_minutes} minute intervals")
        
        while self.is_running:
            try:
                await self.polling_service.poll_all_companies()
                
                # Wait for next poll cycle
                await asyncio.sleep(interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"Error in polling cycle: {e}")
                # Wait a bit before retrying
                await asyncio.sleep(60)
    
    async def stop_polling(self) -> None:
        """Stop the background polling loop."""
        self.is_running = False
        await self.polling_service.close()
        logger.info("Job polling scheduler stopped")
    
    async def poll_once(self) -> Dict[str, any]:
        """
        Run a single poll cycle manually.
        
        Returns:
            Polling statistics
        """
        return await self.polling_service.poll_all_companies()