"""
FastAPI main application.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from app.core.config import settings
from app.core.database import init_db, close_db
from app.api.routes import router as api_router
from app.services.poller import PollingScheduler


# Global polling scheduler
polling_scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting RushJob backend...")
    
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.warning("App will start without database - some features may not work")
    
    # Start background polling if not in debug mode
    global polling_scheduler
    if not settings.debug:
        polling_scheduler = PollingScheduler()
        # Note: In production, you'd want to run this in a separate worker process
        # For MVP, we'll start it as a background task
        import asyncio
        asyncio.create_task(polling_scheduler.start_polling(settings.default_poll_interval_minutes))
        logger.info("Background polling started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down RushJob backend...")
    
    if polling_scheduler:
        await polling_scheduler.stop_polling()
    
    await close_db()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Job alert system for ATS platforms like Greenhouse",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to RushJob API",
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/debug/env")
async def debug_env():
    """Debug endpoint to check environment variables (remove in production)."""
    import os
    return {
        "has_database_url": bool(os.getenv("DATABASE_URL") or os.getenv("database_url")),
        "has_supabase_url": bool(os.getenv("SUPABASE_URL") or os.getenv("supabase_url")),
        "database_url_prefix": (os.getenv("DATABASE_URL") or os.getenv("database_url", ""))[:30] + "...",
        "port": os.getenv("PORT"),
        "debug_mode": settings.debug
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version
    }