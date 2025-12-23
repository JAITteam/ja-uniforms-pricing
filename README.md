# J.A. Uniforms Pricing Tool

<p align="center">
  <img src="static/img/logo.svg" alt="J.A. Uniforms Logo" width="200">
</p>

<p align="center">
  <strong>Internal web application for uniform pricing and cost management</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/python-3.11+-green.svg" alt="Python">
  <img src="https://img.shields.io/badge/flask-3.0.0-red.svg" alt="Flask">
  <img src="https://img.shields.io/badge/database-PostgreSQL%2016-blue.svg" alt="PostgreSQL">
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

### User Management
- **Role-Based Access Control** - Admin and User roles with different permissions
- **Secure Authentication** - Login system with password hashing
- **Admin Panel** - Manage users, reset passwords, control access

### Data Management
- **Audit Logs** - Track all changes to fabrics, notions, and vendors
- **Automated Backups** - Scheduled database backups twice daily
- **Excel Import** - Bulk import styles from Excel files

### Additional Features
- **Favorites** - Mark frequently used styles
- **Search & Filter** - Find styles by vendor, name, gender, margin
- **Responsive Design** - Works on desktop and tablet devices

---

## 🛠 Tech Stack

| Category | Technology |
|----------|------------|
| **Backend** | Python 3.11+, Flask 3.0 |
| **Database** | PostgreSQL 16 |
| **ORM** | SQLAlchemy |
| **Frontend** | HTML5, CSS3, JavaScript |
| **Server** | Waitress (Production) |
| **Authentication** | Flask-Login |
| **Forms** | Flask-WTF (CSRF Protection) |
| **Email** | Flask-Mail |

---

## 📦 Requirements

### Software
- Python 3.11 or higher
- PostgreSQL 16
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

### 4. Create Database
```bash
psql -U postgres
CREATE DATABASE ja_uniforms;
\q
```

### 5. Configure Environment
Create a `.env` file in the project root:
```dotenv
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://postgres:password@localhost:5432/ja_uniforms
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

### 6. Initialize Database
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### 7. Run Application

**Development:**
```bash
python app.py
```

**Production:**
```bash
python run_production.py
```

### 8. Access Application

- **On this computer:** `http://127.0.0.1:5000`
- **On other computers (same network):** `http://[YOUR_IP]:5000`

Find your IP: Run `ipconfig` and look for IPv4 Address.

---

## 📁 Project Structure

```
ja-uniforms-pricing/
├── app.py                    # Main application file
├── models.py                 # Database models
├── run_production.py         # Production server (Waitress)
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (not in git)
├── .env.example              # Example environment file
│
├── static/
│   ├── css/                  # Stylesheets
│   ├── js/                   # JavaScript files
│   └── img/                  # Images and logos
│
├── templates/
│   ├── base.html             # Base template
│   ├── dashboard.html        # Cost calculator
│   ├── view_all_styles.html  # Styles listing
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
| Dashboard | `/` | Cost calculator |
| All Styles | `/view-all-styles` | View and manage styles |
| Master Costs | `/master-costs` | Manage fabrics, notions, vendors |
| Users | `/users` | User management (Admin only) |
| Audit Logs | `/audit-logs` | View change history (Admin only) |

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

# Discard local changes
git checkout -- .
```

---

## 👥 Team

| Role | Name | Contact |
|------|------|---------|
| Developer | JAY | it@jauniforms.com |
| Organization | JAIT Team | - |

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
  Pricing Management System v1.0.0<br>
  © 2025 J.A. Uniforms. All rights reserved.
</p>