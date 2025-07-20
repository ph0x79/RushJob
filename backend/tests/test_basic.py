"""
Basic tests to verify the RushJob backend setup.
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.services.greenhouse import GreenhouseClient, GreenhouseJob


client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns expected response."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "status" in data


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_greenhouse_job_parsing():
    """Test Greenhouse job data parsing."""
    sample_job_data = {
        "id": 123456,
        "title": "Senior Software Engineer",
        "location": {"name": "San Francisco, CA"},
        "departments": [{"name": "Engineering"}],
        "absolute_url": "https://boards.greenhouse.io/stripe/jobs/123456",
        "metadata": [
            {"name": "employment_type", "value": "Full-time"}
        ]
    }
    
    job = GreenhouseJob(sample_job_data)
    
    assert job.id == "123456"
    assert job.title == "Senior Software Engineer"
    assert job.location == "San Francisco, CA"
    assert job.department == "Engineering"
    assert job.job_type == "Full-time"
    assert len(job.content_hash()) == 64  # SHA256 hash length


@pytest.mark.asyncio
async def test_greenhouse_client_initialization():
    """Test that Greenhouse client can be initialized."""
    client = GreenhouseClient()
    assert client.base_url == "https://boards-api.greenhouse.io/v1/boards"
    await client.close()


def test_api_companies_endpoint():
    """Test companies endpoint structure."""
    response = client.get("/api/v1/companies")
    # Should return 200 even if no companies are seeded yet
    assert response.status_code == 200
    assert isinstance(response.json(), list)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])