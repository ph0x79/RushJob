"""
SQLAlchemy models for RushJob database.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Boolean, DateTime, String, Text, Integer, 
    ForeignKey, JSON, Index, UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class Company(Base):
    """Companies that we monitor for job postings."""
    __tablename__ = "companies"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    ats_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'greenhouse', 'lever', etc
    api_endpoint: Mapped[str] = mapped_column(String(500), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    poll_interval_minutes: Mapped[int] = mapped_column(Integer, default=15)
    last_polled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    jobs: Mapped[list["Job"]] = relationship("Job", back_populates="company")
    
    def __repr__(self) -> str:
        return f"<Company {self.name} ({self.slug})>"


class Job(Base):
    """Job postings we've discovered."""
    __tablename__ = "jobs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    external_id: Mapped[str] = mapped_column(String(100), nullable=False)  # Greenhouse job ID
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(100))
    location: Mapped[Optional[str]] = mapped_column(String(255))
    job_type: Mapped[Optional[str]] = mapped_column(String(50))  # full-time, part-time, contract, intern
    external_url: Mapped[str] = mapped_column(String(500), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # For change detection
    raw_data: Mapped[dict] = mapped_column(JSON)  # Full API response
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="jobs")
    notifications: Mapped[list["Notification"]] = relationship("Notification", back_populates="job")
    
    # Indexes for efficient querying
    __table_args__ = (
        Index("idx_company_external_id", "company_id", "external_id"),
        Index("idx_job_active_last_seen", "is_active", "last_seen_at"),
        UniqueConstraint("company_id", "external_id", name="uq_company_job"),
    )
    
    def __repr__(self) -> str:
        return f"<Job {self.title} at {self.company.name if self.company else 'Unknown'}>"


class UserAlert(Base):
    """User-configured job alerts."""
    __tablename__ = "user_alerts"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)  # Supabase user ID
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Filter criteria (stored as JSON for flexibility)
    company_slugs: Mapped[list[str]] = mapped_column(JSON, default=list)
    title_keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    title_exclude_keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    departments: Mapped[list[str]] = mapped_column(JSON, default=list)
    locations: Mapped[list[str]] = mapped_column(JSON, default=list)
    job_types: Mapped[list[str]] = mapped_column(JSON, default=list)
    include_remote: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Notification settings
    discord_webhook_url: Mapped[Optional[str]] = mapped_column(String(500))
    email_address: Mapped[Optional[str]] = mapped_column(String(255))
    notification_frequency: Mapped[str] = mapped_column(String(20), default="immediate")  # immediate, daily, weekly
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_notified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    notifications: Mapped[list["Notification"]] = relationship("Notification", back_populates="alert")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_alerts_active", "user_id", "is_active"),
    )
    
    def __repr__(self) -> str:
        return f"<UserAlert {self.name} for user {self.user_id}>"


class Notification(Base):
    """Record of notifications sent to users."""
    __tablename__ = "notifications"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("user_alerts.id"), nullable=False)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    notification_type: Mapped[str] = mapped_column(String(20), nullable=False)  # discord, email
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # sent, failed, pending
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    alert: Mapped["UserAlert"] = relationship("UserAlert", back_populates="notifications")
    job: Mapped["Job"] = relationship("Job", back_populates="notifications")
    
    # Indexes
    __table_args__ = (
        Index("idx_notifications_alert_job", "alert_id", "job_id"),
        Index("idx_notifications_status_sent", "status", "sent_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Notification {self.notification_type} for alert {self.alert_id}>"


class PollLog(Base):
    """Log of polling attempts for monitoring and debugging."""
    __tablename__ = "poll_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # success, error, timeout
    jobs_found: Mapped[int] = mapped_column(Integer, default=0)
    new_jobs: Mapped[int] = mapped_column(Integer, default=0)
    updated_jobs: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Relationships
    company: Mapped["Company"] = relationship("Company")
    
    # Indexes
    __table_args__ = (
        Index("idx_poll_logs_company_started", "company_id", "started_at"),
        Index("idx_poll_logs_status", "status"),
    )
    
    def __repr__(self) -> str:
        return f"<PollLog for {self.company.name if self.company else 'Unknown'} at {self.started_at}>"