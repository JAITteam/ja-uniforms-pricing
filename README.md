# J.A Uniforms Pricing Tool

Internal web application for uniform pricing and cost management.

## 📋 Quick Links

- **🚀 [Quick Start Guide](QUICK_START_GUIDE.md)** - Get running in 15 minutes
- **📊 [Readiness Report](APPLICATION_READINESS_REPORT.md)** - Full analysis of the application
- **✅ [Deployment Checklist](DEPLOYMENT_CHECKLIST.md)** - Production deployment guide

## ⚠️ Important: Before You Start

**Your application is 90% ready but needs these critical fixes:**

1. **🔴 SECURITY:** Remove hardcoded password from `backup_database.ps1`
2. **🔴 REQUIRED:** Create `.env` file with your configuration
3. **🔴 REQUIRED:** Install Python dependencies

👉 **See [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) for detailed instructions**

## Features

- ✅ User authentication with role-based access (Admin/User)
- ✅ Style management with images
- ✅ Fabric and notion cost tracking
- ✅ Labor cost calculations
- ✅ Automatic pricing based on margins
- ✅ Excel import/export
- ✅ Audit logging
- ✅ Email verification
- ✅ Modern responsive UI

## Tech Stack

- **Backend:** Flask 3.0 (Python)
- **Database:** PostgreSQL (or SQLite for development)
- **Frontend:** Bootstrap 5, Vanilla JS
- **Auth:** Flask-Login
- **ORM:** SQLAlchemy
- **Email:** Flask-Mail

## Quick Setup (5 minutes)

```bash
# 1. Copy environment file
cp .env.example .env
# Edit .env with your settings

# 2. Install dependencies
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# 3. Run application
python3 app.py
```

Open http://localhost:5000

## Team

- Developer: JAITTEAM

## Status

🟡 **90% Complete** - See [APPLICATION_READINESS_REPORT.md](APPLICATION_READINESS_REPORT.md) for details

## Support

For issues or questions, check:
1. [Quick Start Guide](QUICK_START_GUIDE.md)
2. [Application Readiness Report](APPLICATION_READINESS_REPORT.md)
3. Error logs in `logs/ja_uniforms_errors.log`