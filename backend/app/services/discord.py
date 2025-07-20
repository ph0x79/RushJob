"""
Discord webhook notification service.
"""
from typing import List, Optional
import httpx
from loguru import logger
from datetime import datetime

from app.models import Job, UserAlert


class DiscordNotifier:
    """Handles sending job notifications via Discord webhooks."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30)
    
    async def send_job_notification(
        self, 
        webhook_url: str, 
        jobs: List[Job], 
        alert: UserAlert,
        is_initial: bool = False
    ) -> bool:
        """
        Send job notification to Discord webhook.
        
        Args:
            webhook_url: Discord webhook URL
            jobs: List of jobs to notify about
            alert: User alert that triggered the notification
            is_initial: Whether this is the initial notification after creating alert
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        try:
            embed = self._create_embed(jobs, alert, is_initial)
            payload = {
                "embeds": [embed],
                "username": "RushJob",
                "avatar_url": "https://cdn.discordapp.com/attachments/placeholder/rushjob-logo.png"
            }
            
            response = await self.client.post(webhook_url, json=payload)
            response.raise_for_status()
            
            logger.info(f"Successfully sent Discord notification for {len(jobs)} jobs to alert '{alert.name}'")
            return True
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error sending Discord notification: {e}")
            logger.error(f"Response: {e.response.text if e.response else 'No response'}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Discord notification: {e}")
            return False
    
    def _create_embed(self, jobs: List[Job], alert: UserAlert, is_initial: bool) -> dict:
        """
        Create Discord embed for job notification.
        
        Args:
            jobs: List of jobs to include in notification
            alert: User alert configuration
            is_initial: Whether this is initial notification
            
        Returns:
            Discord embed dictionary
        """
        # Determine embed color and title
        if is_initial:
            title = f"🎯 Initial Job Alert: {alert.name}"
            color = 0x5865F2  # Discord brand blue
            description = f"Found **{len(jobs)}** existing jobs matching your criteria!"
        else:
            title = f"🚨 New Job Alert: {alert.name}"
            color = 0x57F287  # Discord green
            if len(jobs) == 1:
                description = "A new job was posted that matches your criteria!"
            else:
                description = f"**{len(jobs)}** new jobs were posted that match your criteria!"
        
        # Create embed structure
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": "RushJob • Job Alert System"
            },
            "fields": []
        }
        
        # Add job fields (limit to 10 jobs to avoid Discord limits)
        jobs_to_show = jobs[:10]
        for job in jobs_to_show:
            job_field = self._create_job_field(job)
            embed["fields"].append(job_field)
        
        # Add "and X more" field if there are more jobs
        if len(jobs) > 10:
            embed["fields"].append({
                "name": "➕ Additional Jobs",
                "value": f"... and {len(jobs) - 10} more jobs! Check your alert dashboard for the complete list.",
                "inline": False
            })
        
        # Add alert summary field
        alert_summary = self._create_alert_summary(alert)
        embed["fields"].append({
            "name": "🔍 Alert Criteria",
            "value": alert_summary,
            "inline": False
        })
        
        return embed
    
    def _create_job_field(self, job: Job) -> dict:
        """
        Create Discord embed field for a single job.
        
        Args:
            job: Job instance
            
        Returns:
            Discord embed field dictionary
        """
        # Create job title with company
        title = f"**{job.title}**"
        
        # Create job details
        details = []
        details.append(f"🏢 {job.company.name}")
        
        if job.department:
            details.append(f"📁 {job.department}")
        
        if job.location:
            location_emoji = "🌍" if "remote" in job.location.lower() else "📍"
            details.append(f"{location_emoji} {job.location}")
        
        if job.job_type:
            details.append(f"💼 {job.job_type}")
        
        # Add apply link
        details.append(f"[**Apply Here**]({job.external_url})")
        
        return {
            "name": title,
            "value": "\n".join(details),
            "inline": True
        }
    
    def _create_alert_summary(self, alert: UserAlert) -> str:
        """
        Create human-readable summary of alert criteria.
        
        Args:
            alert: UserAlert instance
            
        Returns:
            Formatted string describing the alert criteria
        """
        criteria = []
        
        if alert.company_slugs:
            if len(alert.company_slugs) <= 3:
                companies = ", ".join(alert.company_slugs)
                criteria.append(f"**Companies:** {companies}")
            else:
                criteria.append(f"**Companies:** {len(alert.company_slugs)} selected")
        
        if alert.title_keywords:
            keywords = ", ".join(alert.title_keywords[:5])
            if len(alert.title_keywords) > 5:
                keywords += f" (+{len(alert.title_keywords) - 5} more)"
            criteria.append(f"**Keywords:** {keywords}")
        
        if alert.title_exclude_keywords:
            exclude = ", ".join(alert.title_exclude_keywords[:3])
            if len(alert.title_exclude_keywords) > 3:
                exclude += f" (+{len(alert.title_exclude_keywords) - 3} more)"
            criteria.append(f"**Excluding:** {exclude}")
        
        if alert.departments:
            depts = ", ".join(alert.departments[:3])
            if len(alert.departments) > 3:
                depts += f" (+{len(alert.departments) - 3} more)"
            criteria.append(f"**Departments:** {depts}")
        
        if alert.locations:
            locs = ", ".join(alert.locations[:3])
            if len(alert.locations) > 3:
                locs += f" (+{len(alert.locations) - 3} more)"
            criteria.append(f"**Locations:** {locs}")
        
        if alert.job_types:
            types = ", ".join(alert.job_types)
            criteria.append(f"**Types:** {types}")
        
        remote_text = "Yes" if alert.include_remote else "No"
        criteria.append(f"**Remote Jobs:** {remote_text}")
        
        return "\n".join(criteria) if criteria else "No specific criteria"
    
    async def test_webhook(self, webhook_url: str) -> bool:
        """
        Test a Discord webhook URL to ensure it's valid.
        
        Args:
            webhook_url: Discord webhook URL to test
            
        Returns:
            True if webhook is valid and reachable, False otherwise
        """
        try:
            payload = {
                "content": "✅ RushJob webhook test successful! Your job alerts are now configured.",
                "username": "RushJob",
                "embeds": [{
                    "title": "Webhook Test",
                    "description": "This is a test message to verify your Discord webhook is working correctly.",
                    "color": 0x5865F2,
                    "timestamp": datetime.utcnow().isoformat()
                }]
            }
            
            response = await self.client.post(webhook_url, json=payload)
            response.raise_for_status()
            
            logger.info("Discord webhook test successful")
            return True
            
        except Exception as e:
            logger.error(f"Discord webhook test failed: {e}")
            return False
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()