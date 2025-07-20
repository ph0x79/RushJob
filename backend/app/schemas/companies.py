"""
Pydantic schemas for companies.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CompanyBase(BaseModel):
    """Base schema for companies."""
    name: str
    slug: str
    ats_type: str
    is_active: bool = True
    poll_interval_minutes: int = 15


class CompanyResponse(CompanyBase):
    """Schema for company responses."""
    id: int
    api_endpoint: str
    last_polled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True