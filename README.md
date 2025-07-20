# RushJob v2 - Complete Implementation

🚨 **A production-ready job alert system that monitors ATS platforms like Greenhouse and sends real-time Discord notifications.**

## 🎯 What This Is

RushJob monitors job postings from companies that use Greenhouse (Stripe, Airbnb, Robinhood, etc.) and sends instant Discord notifications when new jobs match your criteria. It's **15 minutes faster** than any other job alert service because it pulls directly from the source APIs.

## ✨ Key Features

- ⚡ **Real-time monitoring** of 20+ verified companies
- 🎯 **Smart filtering** by keywords, location, department, job type
- 💬 **Rich Discord notifications** with apply links
- 🚫 **No spam** - duplicate detection prevents repeat alerts
- 🔄 **Background polling** every 15 minutes
- 🎨 **Beautiful embeds** with company info and job details

## 🏗️ Architecture

```
Greenhouse APIs → FastAPI Backend → PostgreSQL → Discord Webhooks
                     ↓
               User Dashboard (Next.js)
```

## 🚀 Quick Start

### 1. Backend Setup
```bash
cd backend
poetry install
cp .env.example .env
# Configure your database and Supabase credentials
poetry run python -m app.cli init
poetry run uvicorn app.main:app --reload
```

### 2. Initialize Companies
```bash
curl -X POST http://localhost:8000/api/v1/companies/seed
```

### 3. Test Polling
```bash
curl -X POST http://localhost:8000/api/v1/poll-now
```

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL database (Supabase recommended)
- Discord webhook for notifications

## 🔧 Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/rushjob

# Supabase (for user management)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# App settings
DEBUG=false  # Set to false for production polling
LOG_LEVEL=INFO
```

## 🎮 Discord Setup

1. Go to your Discord server → Settings → Integrations → Webhooks
2. Create new webhook, copy URL
3. Use webhook URL when creating alerts

## 📡 API Usage

### Create Job Alert
```bash
curl -X POST "http://localhost:8000/api/v1/alerts" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your-user-id",
    "name": "Senior Engineer Alerts",
    "company_slugs": ["stripe", "airbnb"],
    "title_keywords": ["senior", "engineer"],
    "locations": ["San Francisco", "Remote"],
    "discord_webhook_url": "https://discord.com/api/webhooks/..."
  }'
```

### Get User Alerts
```bash
curl "http://localhost:8000/api/v1/alerts?user_id=your-user-id"
```

### List Available Companies
```bash
curl "http://localhost:8000/api/v1/companies"
```

## 🚀 Deployment

### Railway (Recommended)
1. Connect GitHub repo to Railway
2. Set environment variables in Railway dashboard
3. Deploy automatically on git push

### Docker
```bash
docker build -t rushjob-backend backend/
docker run -p 8000:8000 --env-file backend/.env rushjob-backend
```

### Docker Compose (Development)
```bash
cd backend
docker-compose up -d
```

## 📊 Monitoring

The system provides comprehensive logging and monitoring:

- **Health check**: `GET /health`
- **Polling statistics**: Check logs for cycle performance
- **Discord webhook validation**: Built-in testing
- **Database metrics**: Track job discovery and notifications

## 🧪 Testing

```bash
cd backend
poetry run pytest tests/ -v
```

## 📈 Supported Companies

Currently monitoring 20+ companies including:
- Stripe, Airbnb, Robinhood, Peloton
- Dropbox, Coinbase, Reddit, Lyft
- DoorDash, Pinterest, Snowflake, Databricks
- Figma, Notion, Canva, Discord
- And more...

## 🔮 Next Steps

### Frontend Development
- Next.js dashboard for alert management
- User authentication with Supabase
- Company browsing and job previews

### Backend Enhancements
- Email notifications via Resend
- Additional ATS platforms (Lever, SmartRecruiters)
- Advanced filtering (salary, experience level)
- Analytics dashboard

## 🤝 Contributing

This is currently a personal project, but open to collaboration as it grows!

## 📝 License

MIT License - feel free to use for your own job hunting needs.

---

**Built with:** FastAPI, SQLAlchemy, PostgreSQL, Discord API, and lots of coffee ☕

**Perfect for:** Software engineers, product managers, and anyone hunting for jobs at top tech companies.