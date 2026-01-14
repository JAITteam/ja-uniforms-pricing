# J.A. Uniforms Pricing Tool

<p align="center">
  <img src="static/img/logo.svg" alt="J.A. Uniforms Logo" width="200">
</p>

<p align="center">
  <strong>Internal web application for uniform pricing and cost management</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.1.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/python-3.11+-green.svg" alt="Python">
  <img src="https://img.shields.io/badge/flask-3.0.0-red.svg" alt="Flask">
  <img src="https://img.shields.io/badge/database-PostgreSQL%2016-blue.svg" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/redis-enabled-red.svg" alt="Redis">
  <img src="https://img.shields.io/badge/status-Production%20Ready-brightgreen.svg" alt="Status">
</p>

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Requirements](#-requirements)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Analytics Dashboard](#-analytics-dashboard)
- [Security Features](#-security-features)
- [Deployment](#-deployment)
- [Backup System](#-backup-system)
- [Team](#-team)
- [License](#-license)

---

## ✨ Features

### Core Features
- **Cost Calculator Dashboard** - Calculate uniform costs with real-time pricing
- **Style Management** - Create, edit, duplicate, and manage uniform styles
- **Master Cost Lists** - Centralized management of fabrics, notions, vendors, and labor costs
- **SAP Export** - Export pricing data in SAP-compatible CSV format
- **Style Wizard** - Step-by-step style creation with validation

### Analytics Dashboard (NEW)
- **Cost Distribution Chart** - Visual breakdown of styles by price range
- **Top Fabrics Chart** - Most frequently used fabrics across styles
- **Compare Styles** - Side-by-side cost comparison of any 2 styles
- **Cost Breakdown** - Doughnut chart showing Fabric/Labor/Notions/Labels split
- **Activity Trend** - Line chart of style creation over time
- **Quick Insights** - Real-time stats including margins, trends, and totals

### User Management
- **Role-Based Access Control** - Admin and User roles with different permissions
- **Secure Authentication** - Login system with password hashing
- **Email Verification** - New user registration with email verification codes
- **Admin Panel** - Manage users, reset passwords, control access

### Security Features (NEW)
- **Rate Limiting** - Redis-backed request throttling to prevent abuse
- **Login Protection** - 10 attempts per minute limit
- **API Throttling** - Configurable limits on all endpoints
- **CSRF Protection** - Cross-site request forgery prevention
- **XSS Prevention** - Input sanitization and output encoding

### Data Management
- **Audit Logs** - Track all changes with before/after comparisons
- **Automated Cleanup** - Scheduled cleanup of old logs and expired codes
- **Automated Backups** - Scheduled database backups twice daily
- **Excel Import** - Bulk import styles from Excel files

### Additional Features
- **Favorites** - Mark frequently used styles
- **Search & Filter** - Find styles by vendor, name, gender, margin
- **Style Images** - Upload and manage style images
- **Responsive Design** - Works on desktop and tablet devices

---

## 🛠 Tech Stack

| Category | Technology |
|----------|------------|
| **Backend** | Python 3.11+, Flask 3.0 |
| **Database** | PostgreSQL 16 |
| **Cache/Rate Limit** | Redis |
| **ORM** | SQLAlchemy |
| **Task Scheduler** | APScheduler |
| **Frontend** | HTML5, CSS3, JavaScript, Chart.js |
| **Server** | Waitress (Production) |
| **Authentication** | Flask-Login |
| **Forms** | Flask-WTF (CSRF Protection) |
| **Email** | Flask-Mail |
| **Rate Limiting** | Flask-Limiter |

---

## 📦 Requirements

### Software
- Python 3.11 or higher
- PostgreSQL 16
- Redis (for rate limiting)
- Git

### Python Packages
```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-WTF==1.2.1
Flask-Login==0.6.3
Flask-Mail==0.9.1
Flask-Migrate==4.0.5
Flask-Limiter==3.5.0
pandas==2.1.4
openpyxl==3.1.2
python-dotenv==1.0.0
Werkzeug==3.0.0
pytz==2023.3
psycopg2-binary==2.9.9
waitress==2.1.2
redis==5.0.1
APScheduler==3.10.4
Pillow==10.1.0
```

---

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/JAITteam/ja-uniforms-pricing.git
cd ja-uniforms-pricing
```

### 2. Create Virtual Environment
```bash
python -m venv .venv

# Windows
.venv\Scripts\Activate

# Linux/Mac
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install & Start Redis
```bash
# Windows (using chocolatey)
choco install redis-64
redis-server

# Or download from https://github.com/microsoftarchive/redis/releases
```

### 5. Create Database
```bash
psql -U postgres
CREATE DATABASE ja_uniforms;
\q
```

### 6. Configure Environment
Create a `.env` file in the project root:
```dotenv
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://postgres:password@localhost:5432/ja_uniforms
REDIS_URL=redis://127.0.0.1:6379
FLASK_ENV=production
FLASK_DEBUG=False
ADMIN_EMAILS=admin@yourcompany.com
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@company.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@company.com
```

Generate a secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 7. Initialize Database
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### 8. Run Application

**Development:**
```bash
python app.py
```

**Production:**
```bash
python run_production.py
```

### 9. Access Application

- **On this computer:** `http://127.0.0.1:5000`
- **On other computers (same network):** `http://[YOUR_IP]:5000`

Find your IP: Run `ipconfig` and look for IPv4 Address.

---

## 📁 Project Structure

```
ja-uniforms-pricing/
├── app.py                    # Main application file
├── models.py                 # Database models
├── config.py                 # Configuration settings
├── database.py               # Database initialization
├── run_production.py         # Production server (Waitress)
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (not in git)
├── .env.example              # Example environment file
│
├── static/
│   ├── css/
│   │   ├── dashboard_modern.css    # Dashboard styles
│   │   └── ...
│   ├── js/
│   │   ├── dashboard_charts.js     # Chart.js analytics
│   │   ├── dashboard_modern.js     # Dashboard functionality
│   │   └── ...
│   └── img/                  # Images and logos
│
├── templates/
│   ├── base.html             # Base template
│   ├── dashboard.html        # Main dashboard with analytics
│   ├── view_all_styles.html  # Styles listing
│   ├── style_wizard.html     # Style creation wizard
│   ├── master_costs.html     # Master costs management
│   ├── audit_logs.html       # Audit log viewer
│   └── includes/             # Reusable components
│
├── uploads/                  # Uploaded files
├── backups/                  # Database backups
├── logs/                     # Application logs
│
└── backup_database.ps1       # Backup script (Windows)
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | `your-random-string` |
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:pass@localhost:5432/db` |
| `REDIS_URL` | Redis connection | `redis://127.0.0.1:6379` |
| `FLASK_ENV` | Environment mode | `production` or `development` |
| `FLASK_DEBUG` | Debug mode | `False` |
| `ADMIN_EMAILS` | Auto-admin emails | `admin@company.com` |
| `MAIL_SERVER` | SMTP server | `smtp.gmail.com` |
| `MAIL_PORT` | SMTP port | `587` |
| `MAIL_USERNAME` | Email username | `email@company.com` |
| `MAIL_PASSWORD` | Email app password | `your-app-password` |

---

## 📖 Usage

### User Roles

| Role | Permissions |
|------|-------------|
| **Admin** | Full access - manage users, edit all data, view audit logs |
| **User** | View styles, use calculator, export data |

### Key Pages

| Page | URL | Description |
|------|-----|-------------|
| Dashboard | `/` | Cost calculator with analytics |
| All Styles | `/view-all-styles` | View and manage styles |
| Style Wizard | `/style/new` | Create new styles |
| Master Costs | `/master-costs` | Manage fabrics, notions, vendors |
| Users | `/users` | User management (Admin only) |
| Audit Logs | `/audit-logs` | View change history (Admin only) |
| Database Stats | `/admin/database-stats` | View cleanup statistics (Admin only) |

---

## 📊 Analytics Dashboard

The dashboard includes 6 interactive Chart.js visualizations:

| Chart | Type | Description |
|-------|------|-------------|
| **Cost Distribution** | Bar | Styles grouped by price range ($0-20, $20-40, etc.) |
| **Top Fabrics** | Horizontal Bar | Most frequently used fabrics |
| **Compare Styles** | Grouped Bar | Side-by-side comparison of 2 selected styles |
| **Cost Breakdown** | Doughnut | Fabric/Labor/Notions/Labels percentage split |
| **Activity Trend** | Line | Style creation over the last 6 months |
| **Quick Insights** | Text | Real-time stats and trends |

### API Endpoints for Charts

| Endpoint | Description |
|----------|-------------|
| `/api/dashboard-charts` | All chart data |
| `/api/style-cost-breakdown` | Individual style breakdown |
| `/api/compare-styles` | Compare multiple styles |
| `/api/styles-list-simple` | Style list for dropdowns |

---

## 🔒 Security Features

### Rate Limiting

| Route | Limit |
|-------|-------|
| Login | 10 per minute |
| Register | 10 per minute |
| Send Verification Code | 3/min, 10/hour |
| Verify Code | 5 per minute |
| Style Save | 60 per minute |
| Style Delete | 10 per minute |
| Bulk Delete | 3 per minute |
| Default (all routes) | 500/hour, 2000/day |

### Check Rate Limits (Redis)
```bash
redis-cli keys "*LIMITER*"
redis-cli get "LIMITS:LIMITER/[IP]/login/10/1/minute"
```

### Scheduled Cleanup Tasks

| Task | Schedule | Description |
|------|----------|-------------|
| Audit Log Cleanup | Daily at 2 AM | Removes logs older than 90 days |
| Verification Code Cleanup | Every 6 hours | Removes expired codes |

---

## 🚀 Deployment

### Production Server

Use Waitress for production deployment:

```bash
python run_production.py
```

Access the application:
- **On server computer:** `http://127.0.0.1:5000`
- **On other computers (same network):** `http://[SERVER_IP]:5000`

Example: `http://192.168.1.151:5000`

### Required Services

Ensure these are running before starting the app:
```bash
# Start Redis
redis-server

# Start PostgreSQL (usually auto-starts)
pg_ctl start
```

### Windows Firewall

Allow network access:
```powershell
New-NetFirewallRule -DisplayName "JA Uniforms App" -Direction Inbound -Port 5000 -Protocol TCP -Action Allow
```

### Startup Script

Create `Start JA Uniforms.bat`:
```batch
@echo off
cd C:\Users\%USERNAME%\ja-uniforms-pricing
call .venv\Scripts\activate
python run_production.py
```

---

## 💾 Backup System

### Automated Backups

Backups run automatically at:
- 12:00 AM daily
- 4:40 PM daily

### Manual Backup
```powershell
Start-ScheduledTask -TaskName "JA_Uniforms_Backup"
```

### Backup Location
```
backups/
├── ja_uniforms_YYYY-MM-DD_HHMM.backup  # Database
└── images_YYYY-MM-DD_HHMM.zip          # Uploaded files
```

### Network Backup
Backups are also copied to: `\\192.168.1.11\Users\Public\Backups\JA_Uniforms\`

### Restore Database
```bash
pg_restore -U postgres -d ja_uniforms -c backups/ja_uniforms_YYYY-MM-DD_HHMM.backup
```

---

## 🔄 Development Workflow

### Making Changes

1. **Make changes** on development machine
2. **Test locally** at `http://127.0.0.1:5000`
3. **Commit and push**:
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin main
   ```
4. **On production server**:
   ```bash
   git pull origin main
   # Restart server
   ```

### Git Commands

```bash
# Check status
git status

# Pull latest changes
git pull origin main

# View commit history
git log --oneline

# Push to both remotes 
git push origin main 
```

---

## 👥 Team

| Role | Name | Contact |
|------|------|---------|
| Developer | JAY | it@jauniforms.com |

---

## 📄 License

This is proprietary software for internal use by J.A. Uniforms only.

---

## 📞 Support

For issues or questions, contact the IT department:
- Email: it@jauniforms.com

---

<p align="center">
  <strong>J.A. Uniforms</strong><br>
  Pricing Management System v2.1.0<br>
  © 2026 J.A. Uniforms. All rights reserved.
</p>