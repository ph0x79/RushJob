"""
Command-line interface for RushJob.
"""
import asyncio
from typing import Optional
import typer
from loguru import logger

from app.core.database import init_db, AsyncSessionLocal
from app.services.poller import JobPollingService
from app.services.greenhouse import GreenhouseClient, VERIFIED_GREENHOUSE_COMPANIES
from app.models import Company

app = typer.Typer(help="RushJob CLI - Job alert system")


@app.command()
def init():
    """Initialize the database with tables and seed data."""
    async def _init():
        logger.info("Initializing database...")
        await init_db()
        logger.info("Database tables created")
        
        # Seed companies
        async with AsyncSessionLocal() as db:
            for company_data in VERIFIED_GREENHOUSE_COMPANIES:
                company = Company(
                    name=company_data["name"],
                    slug=company_data["slug"],
                    ats_type="greenhouse",
                    api_endpoint=f"https://boards-api.greenhouse.io/v1/boards/{company_data['slug']}/jobs"
                )
                db.add(company)
            
            await db.commit()
            logger.info(f"Seeded {len(VERIFIED_GREENHOUSE_COMPANIES)} companies")
    
    asyncio.run(_init())


@app.command()
def poll():
    """Run a single polling cycle."""
    async def _poll():
        polling_service = JobPollingService()
        try:
            logger.info("Starting manual poll...")
            stats = await polling_service.poll_all_companies()
            logger.info(f"Poll completed: {stats}")
        finally:
            await polling_service.close()
    
    asyncio.run(_poll())


@app.command()
def test_company(slug: str):
    """Test if a company has a valid Greenhouse endpoint."""
    async def _test():
        client = GreenhouseClient()
        try:
            logger.info(f"Testing {slug}...")
            is_valid = await client.test_company_endpoint(slug)
            if is_valid:
                logger.info(f"✅ {slug} has a valid Greenhouse endpoint")
            else:
                logger.error(f"❌ {slug} does not have a valid Greenhouse endpoint")
        finally:
            await client.close()
    
    asyncio.run(_test())


@app.command()
def serve(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False
):
    """Start the FastAPI server."""
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload
    )


if __name__ == "__main__":
    app()