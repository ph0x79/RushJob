# RushJob Backend

A FastAPI-based backend for monitoring job postings from ATS platforms like Greenhouse.

## Features

- **Real-time job monitoring** from Greenhouse APIs
- **Smart filtering** by company, keywords, location, department, and job type
- **Discord notifications** with rich embeds
- **User alerts** with customizable criteria
- **Duplicate detection** to avoid spam
- **Background polling** every 15 minutes

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL database (or Supabase)
- Poetry for dependency management

### Installation

1. **Clone and setup**:
```bash
cd backend
poetry install
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your database and Supabase credentials
```

3. **Initialize database**:
```bash
poetry run python -c "
import asyncio
from app.core.database import init_db
asyncio.run(init_db())
"
```

4. **Seed companies**:
```bash
poetry run python -c "
import asyncio
import httpx
asyncio.run(httpx.post('http://localhost:8000/api/v1/companies/seed'))
"
```

5. **Run the server**:
```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit:
- **Interactive API docs**: http://localhost:8000/docs
- **ReDoc documentation**: http://localhost:8000/redoc

## Key Endpoints

- `GET /api/v1/companies` - List available companies
- `POST /api/v1/alerts` - Create job alert
- `GET /api/v1/alerts?user_id=...` - Get user's alerts
- `GET /api/v1/jobs` - List recent jobs
- `POST /api/v1/poll-now` - Trigger manual poll (dev/testing)

## Background Polling

The system automatically polls companies every 15 minutes when running in production mode (`DEBUG=false`). 

For development, use the `/poll-now` endpoint to trigger polling manually.

## Discord Setup

Users need to create Discord webhooks:

1. Go to Discord server settings → Integrations → Webhooks
2. Create new webhook, copy URL
3. Use webhook URL when creating alerts in RushJob

## Deployment

### Railway (Recommended)
1. Connect GitHub repo to Railway
2. Set environment variables in Railway dashboard
3. Deploy automatically on git push

### Manual Docker
```bash
docker build -t rushjob-backend .
docker run -p 8000:8000 --env-file .env rushjob-backend
```

## Architecture

```
Greenhouse API → FastAPI Backend → PostgreSQL → Discord Webhooks
                      ↓
                User Dashboard (Next.js)
```

## Development

### Running tests:
```bash
poetry run pytest
```

### Code formatting:
```bash
poetry run black .
poetry run isort .
```

### Type checking:
```bash
poetry run mypy .
```

## Environment Variables

See `.env.example` for all required configuration options.

Key variables:
- `DATABASE_URL` - PostgreSQL connection string
- `SUPABASE_URL` & `SUPABASE_ANON_KEY` - Supabase project credentials
- `DEBUG` - Set to `false` for production (enables background polling)

## Monitoring

The system logs detailed information about:
- Polling cycles and performance
- Job discovery and notifications
- API errors and webhooks
- Database operations

## Support

For issues or questions, check the GitHub repository or create an issue.