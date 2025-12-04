# J.A. Uniforms - Complete Production Deployment Guide

**Version**: 1.0  
**Date**: December 4, 2025  
**Target**: Local Network Production Deployment

---

## 📋 Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Server Requirements](#server-requirements)
3. [Installation Steps](#installation-steps)
4. [Database Migration](#database-migration)
5. [Configuration](#configuration)
6. [Starting the Application](#starting-the-application)
7. [Testing the Deployment](#testing-the-deployment)
8. [Maintenance & Operations](#maintenance--operations)
9. [Troubleshooting](#troubleshooting)
10. [Security Hardening](#security-hardening)
11. [Backup & Recovery](#backup--recovery)

---

## 🚀 Pre-Deployment Checklist

### Hardware Requirements

**Minimum Configuration:**
- CPU: 2 cores
- RAM: 4GB
- Storage: 50GB
- Network: 100Mbps

**Recommended Configuration:**
- CPU: 4+ cores
- RAM: 8GB+
- Storage: 100GB SSD
- Network: 1Gbps

### Software Requirements

- **Operating System**: Ubuntu 22.04 LTS or Debian 12
- **Python**: 3.10 or higher
- **PostgreSQL**: 14 or higher
- **Nginx**: 1.18 or higher

### Network Requirements

- Static IP address for the server
- Firewall configured to allow HTTP (80) and HTTPS (443)
- DNS or hosts file entries on client machines

---

## 📦 Installation Steps

### Option 1: Automated Setup (Recommended)

The easiest way to set up the application is using the automated setup script:

```bash
# Clone the repository or copy files to /workspace
cd /workspace

# Make setup script executable
chmod +x setup_production.sh

# Run the setup script
sudo ./setup_production.sh
```

The script will:
- ✅ Install all dependencies (PostgreSQL, Nginx, Python)
- ✅ Create required directories
- ✅ Set up database
- ✅ Configure services
- ✅ Set up automated backups
- ✅ Configure firewall

### Option 2: Manual Setup

Follow these steps if you prefer manual installation:

#### Step 1: Update System

```bash
sudo apt update
sudo apt upgrade -y
```

#### Step 2: Install PostgreSQL

```bash
sudo apt install -y postgresql postgresql-contrib
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

#### Step 3: Install Nginx

```bash
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

#### Step 4: Install Python & Dependencies

```bash
sudo apt install -y python3 python3-pip python3-venv python3-dev \
    build-essential libpq-dev
```

#### Step 5: Create Application User (Optional)

```bash
sudo useradd -m -s /bin/bash jauniforms
sudo usermod -aG www-data jauniforms
```

#### Step 6: Create Required Directories

```bash
sudo mkdir -p /var/log/ja_uniforms
sudo mkdir -p /var/run/ja_uniforms
sudo mkdir -p /var/backups/ja_uniforms

sudo chown -R $USER:www-data /var/log/ja_uniforms
sudo chown -R $USER:www-data /var/run/ja_uniforms
sudo chown -R $USER:www-data /var/backups/ja_uniforms

sudo chmod 770 /var/log/ja_uniforms
sudo chmod 770 /var/run/ja_uniforms
sudo chmod 700 /var/backups/ja_uniforms
```

---

## 🗄️ Database Migration

### Step 1: Create PostgreSQL Database

```bash
sudo -u postgres psql
```

In PostgreSQL shell:

```sql
CREATE DATABASE ja_uniforms_prod;
CREATE USER ja_admin WITH PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE ja_uniforms_prod TO ja_admin;
\q
```

### Step 2: Export Data from SQLite

```bash
cd /workspace
python3 export_sqlite_data.py
```

This creates `sqlite_export.json` with all your current data.

### Step 3: Update Database Configuration

Edit `.env` file:

```bash
DATABASE_URL=postgresql://ja_admin:your_secure_password_here@localhost/ja_uniforms_prod
```

### Step 4: Run Migrations

```bash
source .venv/bin/activate
flask db upgrade
```

### Step 5: Import Data to PostgreSQL

```bash
python3 import_to_postgresql.py
```

Verify the import:

```bash
psql -U ja_admin -d ja_uniforms_prod -c "SELECT COUNT(*) FROM users;"
psql -U ja_admin -d ja_uniforms_prod -c "SELECT COUNT(*) FROM styles;"
```

---

## ⚙️ Configuration

### 1. Environment Variables (.env)

Create `.env` file from template:

```bash
cp .env.example .env
```

Edit `.env` with your production settings:

```bash
# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">

# Database
DATABASE_URL=postgresql://ja_admin:password@localhost/ja_uniforms_prod

# Email Configuration (for notifications)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@jauniforms.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@jauniforms.com

# Admin Configuration
ADMIN_EMAILS=it@jauniforms.com,admin@jauniforms.com
```

**Important**: Never commit `.env` to version control!

### 2. Python Virtual Environment

```bash
cd /workspace
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install psycopg2-binary gunicorn
```

### 3. Systemd Service

Copy service file:

```bash
sudo cp ja_uniforms.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ja_uniforms
```

### 4. Nginx Configuration

Copy Nginx config:

```bash
sudo cp nginx_ja_uniforms.conf /etc/nginx/sites-available/ja_uniforms
sudo ln -s /etc/nginx/sites-available/ja_uniforms /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
```

Test Nginx configuration:

```bash
sudo nginx -t
```

### 5. File Permissions

```bash
cd /workspace
sudo chown -R $USER:www-data .
sudo chmod -R 755 .
sudo chmod 640 .env
sudo chmod +x *.sh
```

---

## 🚀 Starting the Application

### Start All Services

```bash
# Start application
sudo systemctl start ja_uniforms

# Start Nginx
sudo systemctl restart nginx

# Check status
sudo systemctl status ja_uniforms
sudo systemctl status nginx
```

### Check Logs

```bash
# Application logs
sudo journalctl -u ja_uniforms -f

# Nginx logs
sudo tail -f /var/log/nginx/ja_uniforms_access.log
sudo tail -f /var/log/nginx/ja_uniforms_error.log

# Application logs
tail -f /var/log/ja_uniforms/gunicorn_error.log
```

---

## ✅ Testing the Deployment

### 1. Local Server Test

On the server itself:

```bash
curl http://localhost
```

Should return HTML content.

### 2. Network Access Test

From another computer on the network:

1. Open browser
2. Navigate to: `http://<server-ip-address>`
3. You should see the login page

### 3. Find Server IP Address

```bash
hostname -I | awk '{print $1}'
# or
ip addr show | grep 'inet ' | grep -v '127.0.0.1'
```

### 4. Test Login

- Try logging in with your credentials
- Check all major features work

### 5. Performance Test

```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test with 100 requests, 10 concurrent
ab -n 100 -c 10 http://localhost/
```

---

## 🔧 Maintenance & Operations

### Daily Tasks

**1. Check Application Status**
```bash
sudo systemctl status ja_uniforms
```

**2. Check Disk Space**
```bash
df -h
```

**3. Check Logs for Errors**
```bash
sudo journalctl -u ja_uniforms --since today | grep ERROR
```

### Weekly Tasks

**1. Review Logs**
```bash
sudo journalctl -u ja_uniforms --since "1 week ago" > weekly_logs.txt
```

**2. Check Database Size**
```bash
psql -U ja_admin -d ja_uniforms_prod -c "SELECT pg_size_pretty(pg_database_size('ja_uniforms_prod'));"
```

**3. Review Backup Status**
```bash
ls -lh /var/backups/ja_uniforms/
```

### Monthly Tasks

**1. Test Backup Restoration**
```bash
# Create test database
sudo -u postgres createdb ja_uniforms_test

# Restore latest backup to test database
gunzip -c /var/backups/ja_uniforms/latest_backup.sql.gz | \
    psql -U ja_admin ja_uniforms_test

# Verify
psql -U ja_admin ja_uniforms_test -c "SELECT COUNT(*) FROM users;"

# Clean up
sudo -u postgres dropdb ja_uniforms_test
```

**2. Update System**
```bash
sudo apt update
sudo apt upgrade -y
sudo systemctl restart ja_uniforms
```

**3. Review User Access**
```bash
psql -U ja_admin -d ja_uniforms_prod -c "SELECT username, role, is_active, last_login FROM users ORDER BY last_login DESC;"
```

### Updating the Application

```bash
# Backup database first!
./backup_database.sh

# Stop application
sudo systemctl stop ja_uniforms

# Update code (via git or manual copy)
# git pull origin main

# Update dependencies
source .venv/bin/activate
pip install -r requirements.txt

# Run migrations (if needed)
flask db upgrade

# Start application
sudo systemctl start ja_uniforms

# Check status
sudo systemctl status ja_uniforms
```

---

## 🔍 Troubleshooting

### Application Won't Start

**Check service status:**
```bash
sudo systemctl status ja_uniforms
```

**Check logs:**
```bash
sudo journalctl -u ja_uniforms -n 50
```

**Common Issues:**
- Database connection failed → Check `.env` DATABASE_URL
- Port already in use → Check if another service is using port 5000
- Permission denied → Check file permissions

### Database Connection Errors

**Test connection manually:**
```bash
psql -U ja_admin -d ja_uniforms_prod -h localhost
```

**If fails:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check authentication settings
sudo nano /etc/postgresql/14/main/pg_hba.conf
# Ensure this line exists:
# local   all             all                                     md5
```

### Nginx 502 Bad Gateway

**Causes:**
1. Gunicorn not running
2. Wrong socket/port configuration

**Fix:**
```bash
# Check Gunicorn is running
sudo systemctl status ja_uniforms

# Check Nginx config
sudo nginx -t

# Check connection
curl http://127.0.0.1:5000
```

### Slow Performance

**Check system resources:**
```bash
# CPU and Memory
htop

# Disk I/O
iostat -x 1

# Network
iftop
```

**Optimize database:**
```bash
psql -U ja_admin -d ja_uniforms_prod
```

```sql
-- Analyze tables
ANALYZE;

-- Vacuum database
VACUUM ANALYZE;

-- Check slow queries
SELECT query, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

### Application Errors

**Check application logs:**
```bash
tail -f /var/log/ja_uniforms/gunicorn_error.log
tail -f logs/ja_uniforms.log
tail -f logs/ja_uniforms_errors.log
```

---

## 🔐 Security Hardening

### 1. Setup Firewall (UFW)

```bash
# Install UFW
sudo apt install ufw

# Allow SSH
sudo ufw allow ssh

# Allow HTTP/HTTPS
sudo ufw allow 'Nginx Full'

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### 2. Setup Fail2Ban

```bash
# Install
sudo apt install fail2ban

# Create configuration
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local

# Edit configuration
sudo nano /etc/fail2ban/jail.local
```

Add this section:

```ini
[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/*error.log

[nginx-noscript]
enabled = true
port = http,https
logpath = /var/log/nginx/*access.log
```

Start Fail2Ban:

```bash
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 3. Setup SSL/TLS (HTTPS)

**Option A: Self-Signed Certificate (for internal network)**

```bash
# Create SSL directory
sudo mkdir -p /etc/ssl/ja_uniforms

# Generate certificate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/ja_uniforms/ja_uniforms.key \
    -out /etc/ssl/ja_uniforms/ja_uniforms.crt

# Update Nginx config (uncomment SSL lines in nginx_ja_uniforms.conf)
sudo nano /etc/nginx/sites-available/ja_uniforms

# Restart Nginx
sudo systemctl restart nginx
```

**Option B: Let's Encrypt (if you have a domain)**

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal is set up automatically
```

### 4. Secure PostgreSQL

```bash
# Edit PostgreSQL config
sudo nano /etc/postgresql/14/main/postgresql.conf
```

Change:

```
listen_addresses = 'localhost'  # Only local connections
```

Restart PostgreSQL:

```bash
sudo systemctl restart postgresql
```

### 5. Regular Security Updates

```bash
# Enable automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

---

## 💾 Backup & Recovery

### Automated Backups

Backups run automatically daily at 2 AM via cron.

**Manual backup:**

```bash
./backup_database.sh
```

This backs up:
- Database (PostgreSQL dump)
- Uploaded files (images)
- Configuration (.env file)

### Backup Location

```
/var/backups/ja_uniforms/
├── ja_uniforms_backup_20251204_020000.sql.gz
├── ja_uniforms_files_20251204_020000.tar.gz
└── ja_uniforms_env_20251204_020000.tar.gz
```

### Retention Policy

- **Daily backups**: Kept for 7 days
- **Weekly backups**: Kept for 4 weeks
- **Monthly backups**: Kept for 12 months

### Restore from Backup

```bash
./restore_database.sh
```

Follow the prompts to select which backup to restore.

### Off-Site Backup

For additional safety, copy backups to another location:

```bash
# Copy to external drive
cp /var/backups/ja_uniforms/*.gz /mnt/external_drive/ja_uniforms_backups/

# Or sync to another server
rsync -avz /var/backups/ja_uniforms/ user@backup-server:/backups/ja_uniforms/
```

---

## 📊 Monitoring (Optional)

### Setup Prometheus & Grafana

For advanced monitoring, you can set up Prometheus and Grafana:

```bash
# Install Prometheus
sudo apt install prometheus

# Install Grafana
sudo apt install grafana

# Configure and start services
sudo systemctl enable prometheus grafana-server
sudo systemctl start prometheus grafana-server
```

Access Grafana at: `http://<server-ip>:3000`

---

## 📞 Support & Contact

For issues or questions:

1. Check logs first (see Troubleshooting section)
2. Review this guide
3. Contact IT team at: it@jauniforms.com

---

## ✅ Post-Deployment Checklist

After deployment, verify:

- [ ] Application accessible from all network computers
- [ ] Login works for all users
- [ ] All features functional (create/edit/delete styles)
- [ ] Database migration successful (data intact)
- [ ] Backups running automatically
- [ ] Logs being generated properly
- [ ] Email notifications working (if configured)
- [ ] SSL/HTTPS enabled (if required)
- [ ] Firewall configured
- [ ] Performance acceptable

---

## 🎉 Congratulations!

Your J.A. Uniforms application is now running in production on your local network!

**Quick Reference:**

- **Access URL**: `http://<server-ip>`
- **Logs**: `/var/log/ja_uniforms/`
- **Backups**: `/var/backups/ja_uniforms/`
- **Service**: `sudo systemctl status ja_uniforms`
- **Restart**: `sudo systemctl restart ja_uniforms`

---

**Document Version**: 1.0  
**Last Updated**: December 4, 2025
