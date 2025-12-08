# Quick Start Guide - J.A. Uniforms Pricing Tool

**Get your application running in 15 minutes!** 🚀

---

## Prerequisites

- Python 3.7 or higher
- PostgreSQL 12+ (or you can start with SQLite for testing)
- Git
- Text editor

---

## Step 1: Fix Critical Security Issue (5 minutes)

### ⚠️ IMPORTANT: Secure Your Backup Script

The file `backup_database.ps1` contains a hardcoded password. We need to secure it:

```bash
# 1. Move it outside the repository
mv backup_database.ps1 ../backup_database.ps1

# 2. Add it to .gitignore
echo "backup_database.ps1" >> .gitignore
echo "*.ps1" >> .gitignore

# 3. Edit the moved file to use environment variable
# Change line 3 from:
#   $env:PGPASSWORD = "Support1!"
# To:
#   $env:PGPASSWORD = $env:DB_PASSWORD
```

---

## Step 2: Set Up Environment (5 minutes)

### Create .env file

```bash
# Copy the example
cp .env.example .env
```

### Edit .env file with your settings:

```bash
# For quick testing with SQLite (easier to start):
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here-generate-below
DATABASE_URL=sqlite:///uniforms.db

# For production with PostgreSQL:
# DATABASE_URL=postgresql://username:password@localhost/ja_uniforms

# Email (optional for now, needed for user registration):
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@example.com

# Admin emails (will get admin role automatically):
ADMIN_EMAILS=your-email@example.com
```

### Generate a secure SECRET_KEY:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and paste it into your `.env` file as the `SECRET_KEY` value.

---

## Step 3: Install Dependencies (3 minutes)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# On Linux/Mac:
source venv/bin/activate

# On Windows:
.venv\Scripts\Activate.ps1

# Install packages
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed Flask-3.0.0 Flask-Login-0.6.3 ... (14 packages)
```

---

## Step 4: Set Up Database (2 minutes)

### Option A: SQLite (Quick Start - Recommended for Testing)

```bash
# Create tables
python3 app.py
# Press Ctrl+C after it says "Running on http://0.0.0.0:5000"
```

### Option B: PostgreSQL (Production)

```bash
# Create database
sudo -u postgres createdb ja_uniforms

# Update .env with PostgreSQL URL:
# DATABASE_URL=postgresql://postgres:yourpassword@localhost/ja_uniforms

# Run migrations
flask db upgrade

# Start app
python3 app.py
```

---

## Step 5: Start the Application (1 minute)

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\Activate.ps1  # Windows

# Start the application
python3 app.py
```

**You should see:**
```
[2025-12-08 14:32:00] INFO in app: === J.A. Uniforms Application Started ===
 * Running on http://0.0.0.0:5000
```

---

## Step 6: Access Your Application

Open your browser and go to:
```
http://localhost:5000
```

### First Time Setup:

1. **Register an account:**
   - Click "Register"
   - Enter your details
   - Use the email you set in `ADMIN_EMAILS` to get admin access
   - Check your email for verification code (if email is configured)

2. **Login:**
   - Use your registered credentials
   - You should see the dashboard

3. **Start using the app:**
   - Create fabric vendors
   - Add fabrics
   - Create styles
   - Set up labor costs
   - Calculate pricing

---

## Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'flask'"

**Solution:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

---

### Problem: "No SECRET_KEY found in environment"

**Solution:**
```bash
# Make sure .env file exists
ls -la .env

# Generate a key and add it to .env
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

### Problem: Email verification not working

**Solution:**
```bash
# For Gmail, you need an "App Password":
# 1. Go to Google Account settings
# 2. Security → 2-Step Verification → App Passwords
# 3. Generate password for "Mail"
# 4. Use that password in .env as MAIL_PASSWORD

# Temporary workaround: Skip email verification
# Comment out email verification in app.py (not recommended for production)
```

---

### Problem: Database errors

**Solution:**
```bash
# For SQLite:
rm uniforms.db  # Delete and recreate
python3 app.py

# For PostgreSQL:
flask db upgrade
```

---

### Problem: Port 5000 already in use

**Solution:**
```bash
# Change port in app.py (last line):
# From: app.run(debug=debug_mode, host='0.0.0.0', port=5000)
# To:   app.run(debug=debug_mode, host='0.0.0.0', port=8080)

# Or kill the process using port 5000:
# Linux/Mac:
sudo lsof -i :5000
sudo kill -9 <PID>

# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

---

## What's Next?

### For Development:
1. ✅ You're ready to develop!
2. Check `APPLICATION_READINESS_REPORT.md` for detailed analysis
3. Add features or fix issues as needed
4. Commit your changes to git

### For Production:
1. Read `APPLICATION_READINESS_REPORT.md`
2. Follow the "Pre-Deployment Checklist"
3. Set up production server (gunicorn + nginx)
4. Configure HTTPS
5. Set up automated backups
6. Deploy!

---

## Common Commands

```bash
# Start application
python3 app.py

# Run with production server
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Database migrations
flask db init         # Initialize (first time only)
flask db migrate -m "description"  # Create migration
flask db upgrade      # Apply migrations

# Clear old data
rm uniforms.db        # SQLite only
rm -rf logs/*.log     # Clear logs

# Create admin user manually (Python shell)
python3
>>> from app import app, db
>>> from models import User
>>> with app.app_context():
...     user = User(username='admin', email='admin@example.com', role='admin')
...     user.set_password('SecurePassword123')
...     db.session.add(user)
...     db.session.commit()
```

---

## File Structure Reference

```
/workspace/
├── app.py                  # Main application (4,196 lines)
├── config.py              # Configuration
├── database.py            # Database initialization
├── models.py              # Database models
├── auth.py                # Authentication helpers
├── requirements.txt       # Python dependencies
├── .env                   # Your environment variables (CREATE THIS)
├── .env.example           # Example environment file
├── README.md              # Basic readme
├── migrations/            # Database migrations
│   └── versions/
├── templates/             # HTML templates (12 files)
├── static/                # CSS, JS, images
│   ├── css/
│   ├── js/
│   └── img/
└── logs/                  # Application logs
    ├── ja_uniforms.log
    └── ja_uniforms_errors.log
```

---

## Support & Resources

### Documentation:
- Main report: `APPLICATION_READINESS_REPORT.md`
- Flask docs: https://flask.palletsprojects.com/
- SQLAlchemy docs: https://docs.sqlalchemy.org/

### Getting Help:
1. Check error logs: `logs/ja_uniforms_errors.log`
2. Enable debug mode: `FLASK_DEBUG=True` in `.env`
3. Check application logs: `logs/ja_uniforms.log`

---

## Quick Test Checklist

After setup, test these features:

- [ ] Application starts without errors
- [ ] Can access login page (http://localhost:5000)
- [ ] Can register a new user
- [ ] Can login
- [ ] Can see dashboard
- [ ] Can navigate to different pages
- [ ] Can create a style (if admin)
- [ ] Can view all styles
- [ ] Can logout

If all tests pass, **you're good to go!** ✅

---

**Happy Coding!** 🎉

*Last updated: December 8, 2025*
