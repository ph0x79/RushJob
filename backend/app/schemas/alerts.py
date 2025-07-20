"""
Pydantic schemas for user alerts.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl


class UserAlertBase(BaseModel):
    """Base schema for user alerts."""
    name: str = Field(..., min_length=1, max_length=255, description="Alert name")
    is_active: bool = True
    
    # Filter criteria
    company_slugs: List[str] = Field(default=[], description="Company slugs to monitor")
    title_keywords: List[str] = Field(default=[], description="Keywords to include in job titles")
    title_exclude_keywords: List[str] = Field(default=[], description="Keywords to exclude from job titles")
    departments: List[str] = Field(default=[], description="Departments to filter by")
    locations: List[str] = Field(default=[], description="Locations to filter by")
    job_types: List[str] = Field(default=[], description="Job types to filter by")
    include_remote: bool = True
    
    # Notification settings
    discord_webhook_url: Optional[HttpUrl] = None
    email_address: Optional[str] = Field(None, max_length=255)
    notification_frequency: str = Field("immediate", regex="^(immediate|daily|weekly)$")


class UserAlertCreate(UserAlertBase):
    """Schema for creating a new user alert."""
    user_id: str = Field(..., description="Supabase user ID")


class UserAlertUpdate(UserAlertBase):
    """Schema for updating an existing user alert."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None
    company_slugs: Optional[List[str]] = None
    title_keywords: Optional[List[str]] = None
    title_exclude_keywords: Optional[List[str]] = None
    departments: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    job_types: Optional[List[str]] = None
    include_remote: Optional[bool] = None
    discord_webhook_url: Optional[HttpUrl] = None
    email_address: Optional[str] = Field(None, max_length=255)
    notification_frequency: Optional[str] = Field(None, regex="^(immediate|daily|weekly)$")


class UserAlertResponse(UserAlertBase):
    """Schema for user alert responses."""
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime
    last_notified_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True