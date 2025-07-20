"""
Pydantic schemas for jobs.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel


class JobBase(BaseModel):
    """Base schema for jobs."""
    external_id: str
    title: str
    department: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    external_url: str


class JobResponse(JobBase):
    """Schema for job responses."""
    id: int
    company_id: int
    content_hash: str
    raw_data: Dict[str, Any]
    first_seen_at: datetime
    last_seen_at: datetime
    is_active: bool
    
    # Related company info
    company: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True