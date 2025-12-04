# J.A. Uniforms Pricing Tool - Production Deployment Guide

## Table of Contents
1. [Bugs & Issues Analysis](#bugs--issues-analysis)
2. [Missing Dependencies](#missing-dependencies)
3. [PostgreSQL Migration](#postgresql-migration)
4. [Local Network Production Deployment](#local-network-production-deployment)
5. [Backup Strategy](#backup-strategy)
6. [Unit Testing Setup](#unit-testing-setup)
7. [Security Hardening](#security-hardening)

---

## Bugs & Issues Analysis

### Critical Issues Found

#### 1. Missing Dependencies in `requirements.txt`
**Status:** CRITICAL  
**Issue:** The following packages are imported but not listed in requirements.txt:
- `Flask-Mail` - Used for email verification
- `Flask-Migrate` - Used for database migrations
- `psycopg2-binary` - Required for PostgreSQL (you want to migrate)

#### 2. Historical Bug (Already Fixed)
**Status:** RESOLVED  
The error log shows a past bug with `style_labors` vs `style_labor`. The code now correctly uses `style_labor`.

```
AttributeError: type object 'Style' has no attribute 'style_labors'
```

### Medium Priority Issues

#### 3. Rate Limiter Storage
**Issue:** Rate limiter uses in-memory storage (`storage_uri="memory://"`), which resets on restart.
**Impact:** Rate limits won't persist across application restarts.
**Fix:** Use Redis or file-based storage for production.

#### 4. Session Security
**Issue:** `SESSION_COOKIE_SECURE = False` is not set for HTTPS.
**Impact:** Session cookies may be transmitted over insecure connections.
**Fix:** Set to `True` when using HTTPS.

#### 5. CSRF SSL Strict Mode
**Issue:** `WTF_CSRF_SSL_STRICT = False` should be `True` for HTTPS.

### Low Priority Issues

#### 6. Debug Mode Safety
**Status:** HANDLED  
The code has good debug mode protection already.

#### 7. Timezone Handling
**Issue:** Using `datetime.now()` without timezone awareness.
**Impact:** Potential issues with users in different timezones.
**Recommendation:** Consider using `datetime.now(timezone.utc)` for consistency.

---

## Missing Dependencies

Update your `requirements.txt` with these additions:

```txt
# Add these to requirements.txt
Flask-Mail==0.9.1
Flask-Migrate==4.0.5
psycopg2-binary==2.9.9
```

---

## PostgreSQL Migration

### Step 1: Install PostgreSQL on Your Server

**For Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

**For Windows:**
Download from https://www.postgresql.org/download/windows/

### Step 2: Create Database and User

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE ja_uniforms;
CREATE USER ja_uniforms_user WITH ENCRYPTED PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE ja_uniforms TO ja_uniforms_user;

# Grant schema permissions (PostgreSQL 15+)
\c ja_uniforms
GRANT ALL ON SCHEMA public TO ja_uniforms_user;
\q
```

### Step 3: Update Environment Variables

Edit your `.env` file:
```env
# Change this line
DATABASE_URL=postgresql://ja_uniforms_user:your_secure_password_here@localhost:5432/ja_uniforms
```

### Step 4: Migrate Data from SQLite to PostgreSQL

Run the migration script (provided below as `migrate_sqlite_to_postgres.py`):
```bash
python migrate_sqlite_to_postgres.py
```

---

## Local Network Production Deployment

### Architecture Overview
```
[Your Computer - Host Server]
     |
     |-- Gunicorn (WSGI Server)
     |-- PostgreSQL Database
     |-- Nginx (Reverse Proxy - Optional but recommended)
     |
[Other Computers on Network] --> Access via http://192.168.x.x:5000
```

### Step 1: Create Production Environment File

Create `.env.production`:
```env
# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-very-long-random-secret-key-here-generate-with-python-secrets

# Database (PostgreSQL)
DATABASE_URL=postgresql://ja_uniforms_user:your_password@localhost:5432/ja_uniforms

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@jauniforms.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@jauniforms.com

# Admin emails (comma-separated)
ADMIN_EMAILS=it@jauniforms.com,admin@jauniforms.com

# Server Configuration
HOST_IP=0.0.0.0
PORT=5000
```

### Step 2: Create Gunicorn Configuration

Create `gunicorn.conf.py`:
```python
# Gunicorn configuration file
import multiprocessing

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

# Process naming
proc_name = "ja_uniforms"

# Logging
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"
capture_output = True

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
```

### Step 3: Create Systemd Service (Linux)

Create `/etc/systemd/system/ja_uniforms.service`:
```ini
[Unit]
Description=J.A. Uniforms Pricing Tool
After=network.target postgresql.service

[Service]
User=your_username
Group=your_group
WorkingDirectory=/path/to/ja_uniforms_pricing
Environment="PATH=/path/to/ja_uniforms_pricing/.venv/bin"
EnvironmentFile=/path/to/ja_uniforms_pricing/.env.production
ExecStart=/path/to/ja_uniforms_pricing/.venv/bin/gunicorn -c gunicorn.conf.py app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ja_uniforms
sudo systemctl start ja_uniforms
sudo systemctl status ja_uniforms
```

### Step 4: Configure Firewall (Allow Network Access)

**For Ubuntu/Debian:**
```bash
sudo ufw allow 5000/tcp
sudo ufw reload
```

**For Windows:**
1. Open Windows Defender Firewall
2. Click "Advanced settings"
3. Inbound Rules > New Rule
4. Port > TCP > 5000
5. Allow the connection
6. Apply to Domain, Private, Public
7. Name it "JA Uniforms Application"

### Step 5: Access from Other Computers

1. Find your host computer's IP address:
   - Windows: `ipconfig` (look for IPv4 Address)
   - Linux: `ip addr` or `hostname -I`

2. Access from other computers: `http://192.168.x.x:5000`

### Windows Service Alternative (NSSM)

For Windows, use NSSM (Non-Sucking Service Manager):

```batch
# Download NSSM from https://nssm.cc/
# Install service
nssm install JA_Uniforms

# Configure in the GUI:
# Path: C:\path\to\.venv\Scripts\python.exe
# Startup directory: C:\path\to\ja_uniforms_pricing
# Arguments: -m gunicorn -c gunicorn.conf.py app:app
```

---

## Backup Strategy

### Automated Daily PostgreSQL Backups

Create `scripts/backup_database.py`:
```python
#!/usr/bin/env python3
"""
Database Backup Script for J.A. Uniforms
Run this daily via cron (Linux) or Task Scheduler (Windows)
"""
import os
import subprocess
from datetime import datetime
import shutil

# Configuration
BACKUP_DIR = "/path/to/backups/database"
DB_NAME = "ja_uniforms"
DB_USER = "ja_uniforms_user"
KEEP_DAYS = 30  # Keep backups for 30 days

def create_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{BACKUP_DIR}/ja_uniforms_{timestamp}.sql"
    
    # Create PostgreSQL backup
    cmd = f"pg_dump -U {DB_USER} -d {DB_NAME} -f {backup_file}"
    subprocess.run(cmd, shell=True, check=True)
    
    # Compress backup
    shutil.make_archive(backup_file, 'gzip', BACKUP_DIR, os.path.basename(backup_file))
    os.remove(backup_file)
    
    print(f"Backup created: {backup_file}.gz")
    
    # Clean old backups
    cleanup_old_backups()

def cleanup_old_backups():
    import time
    cutoff = time.time() - (KEEP_DAYS * 86400)
    
    for f in os.listdir(BACKUP_DIR):
        filepath = os.path.join(BACKUP_DIR, f)
        if os.path.getmtime(filepath) < cutoff:
            os.remove(filepath)
            print(f"Removed old backup: {f}")

if __name__ == "__main__":
    create_backup()
```

### Backup Images and Uploads

Create `scripts/backup_files.py`:
```python
#!/usr/bin/env python3
"""
File Backup Script for J.A. Uniforms
Backs up uploaded images and static files
"""
import os
import shutil
from datetime import datetime

# Configuration
APP_DIR = "/path/to/ja_uniforms_pricing"
BACKUP_DIR = "/path/to/backups/files"
FOLDERS_TO_BACKUP = ["static/img", "uploads"]

def create_file_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"ja_uniforms_files_{timestamp}"
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    
    os.makedirs(backup_path, exist_ok=True)
    
    for folder in FOLDERS_TO_BACKUP:
        src = os.path.join(APP_DIR, folder)
        dst = os.path.join(backup_path, folder)
        if os.path.exists(src):
            shutil.copytree(src, dst)
            print(f"Backed up: {folder}")
    
    # Compress
    shutil.make_archive(backup_path, 'zip', BACKUP_DIR, backup_name)
    shutil.rmtree(backup_path)
    
    print(f"File backup created: {backup_path}.zip")

if __name__ == "__main__":
    create_file_backup()
```

### Schedule Backups

**Linux (Cron):**
```bash
# Edit crontab
crontab -e

# Add these lines (runs daily at 2 AM)
0 2 * * * /path/to/.venv/bin/python /path/to/scripts/backup_database.py >> /path/to/logs/backup.log 2>&1
30 2 * * * /path/to/.venv/bin/python /path/to/scripts/backup_files.py >> /path/to/logs/backup.log 2>&1
```

**Windows (Task Scheduler):**
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 2:00 AM
4. Action: Start a program
5. Program: `C:\path\to\.venv\Scripts\python.exe`
6. Arguments: `C:\path\to\scripts\backup_database.py`

---

## Unit Testing Setup

### Install Testing Dependencies

Add to `requirements.txt`:
```txt
pytest==7.4.3
pytest-flask==1.3.0
pytest-cov==4.1.0
coverage==7.3.2
```

### Create Test Configuration

Create `tests/conftest.py`:
```python
import pytest
from app import app, db
from models import User, Style, Fabric, FabricVendor

@pytest.fixture(scope='session')
def test_app():
    """Create application for testing."""
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'LOGIN_DISABLED': False
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(test_app):
    """Create test client."""
    return test_app.test_client()

@pytest.fixture
def runner(test_app):
    """Create test CLI runner."""
    return test_app.test_cli_runner()

@pytest.fixture
def admin_user(test_app):
    """Create admin user for testing."""
    with test_app.app_context():
        user = User(
            username='admin@jauniforms.com',
            email='admin@jauniforms.com',
            first_name='Admin',
            last_name='User',
            role='admin'
        )
        user.set_password('TestPassword123')
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def regular_user(test_app):
    """Create regular user for testing."""
    with test_app.app_context():
        user = User(
            username='user@jauniforms.com',
            email='user@jauniforms.com',
            first_name='Regular',
            last_name='User',
            role='user'
        )
        user.set_password('TestPassword123')
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def sample_fabric(test_app):
    """Create sample fabric for testing."""
    with test_app.app_context():
        vendor = FabricVendor(name='Test Vendor', vendor_code='TV01')
        db.session.add(vendor)
        db.session.commit()
        
        fabric = Fabric(
            name='Test Fabric',
            fabric_code='TF001',
            cost_per_yard=5.50,
            color='Blue',
            fabric_vendor_id=vendor.id
        )
        db.session.add(fabric)
        db.session.commit()
        return fabric
```

### Create Example Tests

Create `tests/test_auth.py`:
```python
"""Tests for authentication functionality."""
import pytest
from flask_login import current_user

class TestLogin:
    """Tests for login functionality."""
    
    def test_login_page_loads(self, client):
        """Test that login page loads successfully."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Login' in response.data
    
    def test_login_with_valid_credentials(self, client, admin_user, test_app):
        """Test login with valid credentials."""
        with test_app.app_context():
            response = client.post('/login', data={
                'username': 'admin@jauniforms.com',
                'password': 'TestPassword123'
            }, follow_redirects=True)
            assert response.status_code == 200
    
    def test_login_with_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post('/login', data={
            'username': 'wrong@jauniforms.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        assert b'Invalid email or password' in response.data
    
    def test_login_requires_company_email(self, client):
        """Test that only company emails are allowed."""
        response = client.post('/login', data={
            'username': 'user@gmail.com',
            'password': 'somepassword'
        }, follow_redirects=True)
        assert b'Only company emails' in response.data


class TestLogout:
    """Tests for logout functionality."""
    
    def test_logout(self, client, admin_user, test_app):
        """Test logout functionality."""
        with test_app.app_context():
            # Login first
            client.post('/login', data={
                'username': 'admin@jauniforms.com',
                'password': 'TestPassword123'
            })
            
            # Then logout
            response = client.get('/logout', follow_redirects=True)
            assert response.status_code == 200
            assert b'logged out' in response.data.lower()


class TestPasswordValidation:
    """Tests for password validation."""
    
    def test_password_minimum_length(self, test_app):
        """Test password minimum length requirement."""
        from app import validate_password
        
        is_valid, message = validate_password('Short1')
        assert not is_valid
        assert 'at least 8 characters' in message
    
    def test_password_requires_uppercase(self, test_app):
        """Test password requires uppercase letter."""
        from app import validate_password
        
        is_valid, message = validate_password('lowercase123')
        assert not is_valid
        assert 'uppercase' in message
    
    def test_password_requires_number(self, test_app):
        """Test password requires number."""
        from app import validate_password
        
        is_valid, message = validate_password('NoNumbersHere')
        assert not is_valid
        assert 'number' in message
    
    def test_valid_password(self, test_app):
        """Test valid password passes validation."""
        from app import validate_password
        
        is_valid, message = validate_password('ValidPass123')
        assert is_valid
```

Create `tests/test_styles.py`:
```python
"""Tests for style functionality."""
import pytest

class TestStyleOperations:
    """Tests for style CRUD operations."""
    
    def test_view_all_styles_requires_login(self, client):
        """Test that viewing styles requires authentication."""
        response = client.get('/view-all-styles')
        assert response.status_code == 302  # Redirect to login
    
    def test_dashboard_loads(self, client, admin_user, test_app):
        """Test dashboard loads for authenticated user."""
        with test_app.app_context():
            client.post('/login', data={
                'username': 'admin@jauniforms.com',
                'password': 'TestPassword123'
            })
            
            response = client.get('/')
            assert response.status_code == 200


class TestAPIEndpoints:
    """Tests for API endpoints."""
    
    def test_api_colors_requires_auth(self, client):
        """Test that API requires authentication."""
        response = client.get('/api/colors')
        assert response.status_code == 302  # Redirect to login
    
    def test_api_fabrics_requires_auth(self, client):
        """Test that fabrics API requires authentication."""
        response = client.get('/api/fabrics')
        assert response.status_code == 302


class TestAdminOperations:
    """Tests for admin-only operations."""
    
    def test_regular_user_cannot_delete_style(self, client, regular_user, test_app):
        """Test that regular users cannot delete styles."""
        with test_app.app_context():
            client.post('/login', data={
                'username': 'user@jauniforms.com',
                'password': 'TestPassword123'
            })
            
            response = client.delete('/api/style/delete/1')
            # Should be forbidden or redirect
            assert response.status_code in [302, 403]
```

Create `tests/test_models.py`:
```python
"""Tests for database models."""
import pytest
from models import User, Style, Fabric, FabricVendor

class TestUserModel:
    """Tests for User model."""
    
    def test_user_password_hashing(self, test_app):
        """Test that passwords are properly hashed."""
        with test_app.app_context():
            user = User(
                username='test@jauniforms.com',
                email='test@jauniforms.com'
            )
            user.set_password('mypassword')
            
            assert user.password_hash != 'mypassword'
            assert user.check_password('mypassword')
            assert not user.check_password('wrongpassword')
    
    def test_user_is_admin(self, test_app):
        """Test admin role checking."""
        with test_app.app_context():
            admin = User(username='admin@test.com', email='admin@test.com', role='admin')
            regular = User(username='user@test.com', email='user@test.com', role='user')
            
            assert admin.is_admin()
            assert not regular.is_admin()
    
    def test_get_display_name(self, test_app):
        """Test display name generation."""
        with test_app.app_context():
            user = User(
                username='john@jauniforms.com',
                email='john@jauniforms.com',
                first_name='John'
            )
            
            assert user.get_display_name() == 'John'


class TestStyleModel:
    """Tests for Style model."""
    
    def test_style_creation(self, test_app):
        """Test style can be created."""
        with test_app.app_context():
            from database import db
            
            style = Style(
                vendor_style='TEST-001',
                style_name='Test Style',
                gender='UNISEX',
                garment_type='SHIRT'
            )
            db.session.add(style)
            db.session.commit()
            
            assert style.id is not None
            assert style.vendor_style == 'TEST-001'
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v

# Run tests matching a pattern
pytest -k "test_login"
```

---

## Security Hardening

### Production Security Checklist

1. **Secret Key**
   ```bash
   # Generate a secure secret key
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **HTTPS (Recommended)**
   - Use nginx as reverse proxy with SSL certificate
   - Or use Cloudflare tunnel for free HTTPS

3. **Database Credentials**
   - Use strong passwords
   - Never commit credentials to git

4. **File Permissions (Linux)**
   ```bash
   chmod 600 .env.production
   chmod 700 scripts/
   ```

5. **Rate Limiting**
   - Already implemented in the app
   - Consider Redis for persistent storage

---

## Quick Start Commands

```bash
# 1. Update requirements
pip install -r requirements.txt

# 2. Set up PostgreSQL (after installing)
sudo -u postgres psql -c "CREATE DATABASE ja_uniforms;"
sudo -u postgres psql -c "CREATE USER ja_uniforms_user WITH ENCRYPTED PASSWORD 'password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ja_uniforms TO ja_uniforms_user;"

# 3. Run migrations
flask db upgrade

# 4. Start production server
gunicorn -c gunicorn.conf.py app:app

# 5. Or use systemd (Linux)
sudo systemctl start ja_uniforms
```

---

## Troubleshooting

### Common Issues

1. **Cannot connect from other computers**
   - Check firewall settings
   - Verify host IP address
   - Ensure app is bound to `0.0.0.0`

2. **Database connection errors**
   - Check PostgreSQL is running
   - Verify DATABASE_URL in .env
   - Check PostgreSQL logs

3. **Email not sending**
   - Verify SMTP credentials
   - Check firewall allows port 587
   - Use App Password for Gmail

---

## Summary

Your application is well-structured with good security practices in place. The main improvements needed are:

1. Add missing dependencies to requirements.txt
2. Migrate from SQLite to PostgreSQL for production
3. Set up Gunicorn as production WSGI server
4. Configure systemd/Windows service for auto-start
5. Implement automated backup scripts
6. Add unit tests for code quality

Following this guide will give you a production-ready deployment that runs on your local network for free!
