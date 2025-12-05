# 📋 SOP: J.A. Uniforms Pricing Tool - Server Setup

## Standard Operating Procedure
**Document Version:** 1.0  
**Created:** December 2024  
**Purpose:** Complete setup guide for production server (Ruben's PC)

---

## 📑 Table of Contents

1. [Overview](#1-overview)
2. [Prerequisites](#2-prerequisites)
3. [Step 1: Set Static IP Address](#step-1-set-static-ip-address)
4. [Step 2: Install PostgreSQL](#step-2-install-postgresql)
5. [Step 3: Install Python](#step-3-install-python)
6. [Step 4: Install Git](#step-4-install-git)
7. [Step 5: Clone the Application](#step-5-clone-the-application)
8. [Step 6: Set Up Python Environment](#step-6-set-up-python-environment)
9. [Step 7: Create Database](#step-7-create-database)
10. [Step 8: Configure Environment Variables](#step-8-configure-environment-variables)
11. [Step 9: Initialize Database](#step-9-initialize-database)
12. [Step 10: Test the Application](#step-10-test-the-application)
13. [Step 11: Set Up Auto-Start](#step-11-set-up-auto-start)
14. [Step 12: Configure Firewall](#step-12-configure-firewall)
15. [Step 13: Set Up Daily Backups](#step-13-set-up-daily-backups)
16. [Daily Operations](#daily-operations)
17. [How to Update Application](#how-to-update-application)
18. [Troubleshooting](#troubleshooting)

---

## 1. Overview

### What This Setup Does:
- Installs all required software on Ruben's PC
- Configures the PC as a server for 20+ employees
- Sets up automatic startup so the app runs when PC boots
- Configures daily database backups

### Network Architecture:
```
Ruben's PC (Server): 192.168.1.140
├── PostgreSQL Database (port 5432)
└── Flask Application (port 5000)

All Employees Access: http://192.168.1.140:5000
```

### Estimated Setup Time: 45-60 minutes

---

## 2. Prerequisites

### Hardware Requirements:
- [x] Windows 10/11 PC (minimum 8GB RAM recommended)
- [x] At least 10GB free disk space
- [x] Connected to office network (192.168.1.x)

### Required Downloads (Download these first):
| Software | Download Link | Version |
|----------|--------------|---------|
| PostgreSQL | https://www.postgresql.org/download/windows/ | 16.x |
| Python | https://www.python.org/downloads/ | 3.11 or 3.12 |
| Git | https://git-scm.com/download/win | Latest |

### Information Needed:
- [ ] GitHub repository URL
- [ ] PostgreSQL password (will set: `Support1!`)
- [ ] Static IP address for this PC (example: `192.168.1.140`)
- [ ] Network gateway (usually: `192.168.1.1`)

---

## Step 1: Set Static IP Address

**Why:** Ensures the server always has the same IP address.

### Instructions:

1. Press `Win + R`, type `ncpa.cpl`, press Enter
2. Right-click on **Ethernet** (or Wi-Fi) → **Properties**
3. Select **Internet Protocol Version 4 (TCP/IPv4)** → Click **Properties**
4. Select **"Use the following IP address"**
5. Enter:
   ```
   IP address:      192.168.1.140
   Subnet mask:     255.255.255.0
   Default gateway: 192.168.1.1
   ```
6. Select **"Use the following DNS server addresses"**
   ```
   Preferred DNS:   8.8.8.8
   Alternate DNS:   8.8.4.4
   ```
7. Click **OK** → **Close**

### Verify:
```powershell
# Open PowerShell and run:
ipconfig
# Should show: IPv4 Address: 192.168.1.140
```

✅ **Checkpoint:** IP address is set to 192.168.1.140

---

## Step 2: Install PostgreSQL

### Instructions:

1. Run the PostgreSQL installer (downloaded earlier)
2. Click **Next** through the welcome screen
3. **Installation Directory:** Keep default (`C:\Program Files\PostgreSQL\16`)
4. **Select Components:** Keep all selected (especially "pgAdmin 4")
5. **Data Directory:** Keep default
6. **Password:** Enter `Support1!` (REMEMBER THIS!)
7. **Port:** Keep default `5432`
8. **Locale:** Keep default
9. Click **Next** → **Install**
10. Wait for installation to complete
11. **Uncheck** "Launch Stack Builder" → Click **Finish**

### Verify PostgreSQL is Running:
```powershell
# Open PowerShell as Administrator and run:
Get-Service -Name "postgresql*"

# Should show:
# Status   Name               DisplayName
# ------   ----               -----------
# Running  postgresql-x64-16  postgresql-x64-16
```

### Verify PostgreSQL Service is Auto-Start:
1. Press `Win + R`, type `services.msc`, press Enter
2. Find **postgresql-x64-16**
3. Verify **Startup Type** is **Automatic**
4. If not, right-click → Properties → Set to **Automatic**

✅ **Checkpoint:** PostgreSQL installed and running

---

## Step 3: Install Python

### Instructions:

1. Run the Python installer (downloaded earlier)
2. ⚠️ **IMPORTANT:** Check ✅ **"Add Python to PATH"** at the bottom!
3. Click **"Install Now"**
4. Wait for installation
5. Click **Close**

### Verify:
```powershell
# Open NEW PowerShell window and run:
python --version
# Should show: Python 3.11.x or 3.12.x

pip --version
# Should show: pip 23.x.x or higher
```

✅ **Checkpoint:** Python installed and in PATH

---

## Step 4: Install Git

### Instructions:

1. Run the Git installer (downloaded earlier)
2. Click **Next** through all screens (keep all defaults)
3. Click **Install**
4. Click **Finish**

### Verify:
```powershell
# Open NEW PowerShell window and run:
git --version
# Should show: git version 2.x.x
```

✅ **Checkpoint:** Git installed

---

## Step 5: Clone the Application

### Instructions:

```powershell
# Open PowerShell and run these commands:

# 1. Navigate to C:\ drive
cd C:\

# 2. Clone the repository (replace with your actual GitHub URL)
git clone https://github.com/JAITteam/ja-uniforms-pricing.git ja-uniforms

# 3. Navigate into the folder
cd C:\ja-uniforms

# 4. Verify files are there
dir
# Should see: app.py, requirements.txt, templates/, static/, etc.
```

✅ **Checkpoint:** Application code downloaded to `C:\ja-uniforms`

---

## Step 6: Set Up Python Environment

### Instructions:

```powershell
# Make sure you're in the app folder
cd C:\ja-uniforms

# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment
.\venv\Scripts\Activate

# Your prompt should now show: (venv) PS C:\ja-uniforms>

# 3. Upgrade pip
python -m pip install --upgrade pip

# 4. Install all required packages
pip install -r requirements.txt

# 5. Install gunicorn for production
pip install gunicorn waitress
```

### Verify:
```powershell
# Still in virtual environment, run:
pip list
# Should show Flask, SQLAlchemy, psycopg2-binary, gunicorn, etc.
```

✅ **Checkpoint:** Python packages installed

---

## Step 7: Create Database

### Instructions:

```powershell
# Open PowerShell and run:

# 1. Open PostgreSQL command line
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres

# Enter password when prompted: Support1!
```

### In PostgreSQL prompt (postgres=#):
```sql
-- Create the database
CREATE DATABASE ja_uniforms;

-- Verify it was created
\l

-- You should see ja_uniforms in the list

-- Exit PostgreSQL
\q
```

✅ **Checkpoint:** Database `ja_uniforms` created

---

## Step 8: Configure Environment Variables

### Instructions:

1. Create the `.env` file in `C:\ja-uniforms\`:

```powershell
# In PowerShell:
cd C:\ja-uniforms
notepad .env
```

2. Paste this content and save:

```env
# ============================================
# J.A. UNIFORMS - PRODUCTION CONFIGURATION
# ============================================

# PostgreSQL Database
DATABASE_URL=postgresql://postgres:Support1!@localhost:5432/ja_uniforms

# Flask Settings
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-super-secret-key-change-this-to-random-string-abc123xyz

# Upload Settings
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216

# Email Configuration (Update with real values)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@jauniforms.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@jauniforms.com

# Admin Emails (comma-separated)
ADMIN_EMAILS=it@jauniforms.com,ruben@jauniforms.com
```

3. **Generate a secure SECRET_KEY:**
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
# Copy the output and replace 'your-super-secret-key...' in .env
```

✅ **Checkpoint:** Environment file created

---

## Step 9: Initialize Database

### Option A: Fresh Database (New Installation)

```powershell
cd C:\ja-uniforms
.\venv\Scripts\Activate

# Initialize database migrations
flask db upgrade

# Verify tables were created
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d ja_uniforms -c "\dt"
# Should show list of tables (users, styles, fabrics, etc.)
```

### Option B: Restore from Backup (Migration from Your PC)

```powershell
# Copy the backup file to Ruben's PC first, then:

& "C:\Program Files\PostgreSQL\16\bin\pg_restore.exe" -U postgres -d ja_uniforms C:\backup\ja_uniforms_backup.dump
```

✅ **Checkpoint:** Database tables created or restored

---

## Step 10: Test the Application

### Start the Application:

```powershell
cd C:\ja-uniforms
.\venv\Scripts\Activate

# For testing, use Flask development server:
flask run --host=0.0.0.0 --port=5000
```

### Verify:

1. **On Ruben's PC:** Open browser → `http://localhost:5000`
2. **From another PC:** Open browser → `http://192.168.1.140:5000`
3. Both should show the login page

### Stop the test server:
Press `Ctrl + C` in PowerShell

✅ **Checkpoint:** Application runs and is accessible from network

---

## Step 11: Set Up Auto-Start

### Create Startup Script:

1. Create `C:\ja-uniforms\start_server.bat`:

```powershell
notepad C:\ja-uniforms\start_server.bat
```

2. Paste this content:

```batch
@echo off
title J.A. Uniforms Pricing Server
cd /d C:\ja-uniforms
call venv\Scripts\activate
echo.
echo ========================================
echo   J.A. UNIFORMS PRICING SERVER
echo   Running on: http://192.168.1.140:5000
echo ========================================
echo.
echo Server starting... (Do not close this window)
echo.
waitress-serve --host=0.0.0.0 --port=5000 app:app
pause
```

3. Save and close

### Create Scheduled Task for Auto-Start:

1. Press `Win + R`, type `taskschd.msc`, press Enter
2. Click **Create Task** (not Basic Task)
3. **General Tab:**
   - Name: `JA Uniforms Server`
   - Check: ✅ Run whether user is logged on or not
   - Check: ✅ Run with highest privileges
4. **Triggers Tab:**
   - Click **New**
   - Begin the task: **At startup**
   - Click **OK**
5. **Actions Tab:**
   - Click **New**
   - Action: Start a program
   - Program: `C:\ja-uniforms\start_server.bat`
   - Click **OK**
6. **Conditions Tab:**
   - Uncheck: Start only if on AC power
7. **Settings Tab:**
   - Check: Allow task to be run on demand
   - Check: If the task fails, restart every: 1 minute
8. Click **OK**
9. Enter Windows password when prompted

### Test Auto-Start:
```powershell
# Restart the computer
Restart-Computer

# After reboot, check if app is running:
# Open browser → http://localhost:5000
```

✅ **Checkpoint:** Application starts automatically on boot

---

## Step 12: Configure Firewall

### Allow the App Through Windows Firewall:

```powershell
# Run PowerShell as Administrator:

# Allow Flask/Waitress on port 5000
New-NetFirewallRule -DisplayName "JA Uniforms App" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow

# Verify the rule was created
Get-NetFirewallRule -DisplayName "JA Uniforms App"
```

### Test from Another Computer:
- Open browser on any other PC in office
- Go to `http://192.168.1.140:5000`
- Should see login page

✅ **Checkpoint:** Firewall configured, app accessible from network

---

## Step 13: Set Up Daily Backups

### Create Backup Script:

1. Create `C:\ja-uniforms\backup\` folder:
```powershell
mkdir C:\ja-uniforms\backup
```

2. Create `C:\ja-uniforms\backup_database.bat`:

```batch
@echo off
setlocal

:: Set backup location
set BACKUP_DIR=C:\ja-uniforms\backup
set DATE=%date:~10,4%-%date:~4,2%-%date:~7,2%
set TIME=%time:~0,2%-%time:~3,2%
set TIME=%TIME: =0%
set FILENAME=ja_uniforms_%DATE%_%TIME%.backup

:: Create backup
echo Creating database backup...
"C:\Program Files\PostgreSQL\16\bin\pg_dump.exe" -U postgres -F c -d ja_uniforms -f "%BACKUP_DIR%\%FILENAME%"

:: Delete backups older than 7 days
echo Cleaning old backups...
forfiles /p "%BACKUP_DIR%" /m *.backup /d -7 /c "cmd /c del @path" 2>nul

echo.
echo Backup complete: %FILENAME%
echo.
```

### Schedule Daily Backup:

1. Open **Task Scheduler**
2. Click **Create Basic Task**
3. Name: `JA Uniforms Daily Backup`
4. Trigger: **Daily** at **5:30 PM** (after work hours)
5. Action: **Start a program**
6. Program: `C:\ja-uniforms\backup_database.bat`
7. Click **Finish**

✅ **Checkpoint:** Daily backups configured

---

## Daily Operations

### For Ruben - Morning Routine:

```
1. Turn on PC
2. Wait 1-2 minutes for Windows to start
3. Application starts automatically!
4. Verify: Open browser → http://localhost:5000
5. Done! ✅
```

### For All Employees:

```
1. Open any web browser (Chrome, Edge, Firefox)
2. Go to: http://192.168.1.140:5000
3. Log in with your credentials
4. Start working!
```

---

## How to Update Application

### When Developer Pushes New Code:

**Option 1: Manual Update (Ruben runs this)**

```powershell
cd C:\ja-uniforms
git pull origin main
pip install -r requirements.txt
```

Then restart the PC or restart the scheduled task.

**Option 2: Use Update Script**

Create `C:\ja-uniforms\update_app.bat`:

```batch
@echo off
echo ========================================
echo   J.A. UNIFORMS - UPDATE APPLICATION
echo ========================================
echo.

cd /d C:\ja-uniforms

echo Stopping server...
taskkill /f /im python.exe 2>nul
taskkill /f /im waitress-serve.exe 2>nul

echo.
echo Pulling latest code from GitHub...
git pull origin main

echo.
echo Installing dependencies...
call venv\Scripts\activate
pip install -r requirements.txt

echo.
echo ========================================
echo   UPDATE COMPLETE!
echo.
echo   Please restart the computer or
echo   run start_server.bat manually.
echo ========================================
pause
```

Ruben just double-clicks `update_app.bat` when you tell him an update is ready!

---

## Troubleshooting

### Problem: Application Won't Start

```powershell
# Check if PostgreSQL is running:
Get-Service postgresql*

# If stopped, start it:
Start-Service postgresql-x64-16

# Check for errors in the app:
cd C:\ja-uniforms
.\venv\Scripts\Activate
python app.py
# Look for error messages
```

### Problem: Can't Connect from Other PCs

1. Check firewall: `Get-NetFirewallRule -DisplayName "JA Uniforms*"`
2. Check IP: `ipconfig` (should be 192.168.1.140)
3. Check if app is running: Open `http://localhost:5000` on Ruben's PC

### Problem: Database Connection Error

```powershell
# Test database connection:
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d ja_uniforms -c "SELECT 1;"
# Should return: 1
```

### Problem: Forgot PostgreSQL Password

1. Open `C:\Program Files\PostgreSQL\16\data\pg_hba.conf`
2. Change `scram-sha-256` to `trust` temporarily
3. Restart PostgreSQL service
4. Reset password:
   ```sql
   psql -U postgres
   ALTER USER postgres PASSWORD 'Support1!';
   ```
5. Change `pg_hba.conf` back to `scram-sha-256`
6. Restart PostgreSQL

---

## 📞 Support Contacts

| Issue | Contact |
|-------|---------|
| Application bugs | Developer (You) |
| PC/Hardware issues | IT Support |
| Network issues | IT Support |
| Password reset | Admin (via app) |

---

## ✅ Setup Completion Checklist

- [ ] Static IP configured (192.168.1.140)
- [ ] PostgreSQL installed and running
- [ ] Python installed with PATH
- [ ] Git installed
- [ ] Application cloned to C:\ja-uniforms
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Database created
- [ ] .env file configured
- [ ] Database initialized/restored
- [ ] Application tested locally
- [ ] Application tested from network
- [ ] Auto-start configured
- [ ] Firewall rule added
- [ ] Daily backup scheduled
- [ ] Ruben trained on daily operations
- [ ] Update script created

---

**Document End**

*Last Updated: December 2024*
