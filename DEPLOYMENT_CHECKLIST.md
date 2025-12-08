# 🚀 Deployment Checklist - J.A. Uniforms Pricing Tool

Use this checklist to prepare your application for production.

---

## ⚠️ Critical Issues (DO THESE FIRST!)

- [ ] **Remove hardcoded password** from `backup_database.ps1`
  - [ ] Move file outside repository
  - [ ] Update it to use environment variable
  - [ ] Add `*.ps1` to `.gitignore`
  
- [ ] **Create `.env` file** with proper configuration
  - [ ] Generate secure SECRET_KEY
  - [ ] Configure DATABASE_URL
  - [ ] Set up email credentials
  - [ ] Add admin emails
  
- [ ] **Install dependencies**
  - [ ] Create virtual environment
  - [ ] Run `pip install -r requirements.txt`
  - [ ] Verify all packages installed

---

## 🔧 Setup & Configuration

- [ ] **Database Setup**
  - [ ] Choose database (SQLite for dev, PostgreSQL for prod)
  - [ ] Create database
  - [ ] Run migrations (`flask db upgrade`)
  - [ ] Verify tables created
  
- [ ] **Environment Variables**
  - [ ] `SECRET_KEY` - Generated and unique
  - [ ] `FLASK_ENV` - Set to 'production' for production
  - [ ] `FLASK_DEBUG` - Set to False for production
  - [ ] `DATABASE_URL` - Correct connection string
  - [ ] `MAIL_*` variables - Configured for email
  - [ ] `ADMIN_EMAILS` - Set admin users
  
- [ ] **Test Local Startup**
  - [ ] Application starts without errors
  - [ ] Can access http://localhost:5000
  - [ ] Can register a user
  - [ ] Can login
  - [ ] Dashboard loads correctly

---

## 🔒 Security Review

- [ ] **Password Security**
  - [ ] No hardcoded passwords in code
  - [ ] All passwords in environment variables
  - [ ] Strong SECRET_KEY configured
  
- [ ] **HTTPS/SSL**
  - [ ] SSL certificate obtained
  - [ ] HTTPS configured on web server
  - [ ] HTTP redirects to HTTPS
  
- [ ] **Security Headers**
  - [ ] CSRF protection enabled (✅ already configured)
  - [ ] Session cookies secure
  - [ ] Rate limiting enabled (✅ already configured)
  
- [ ] **Database Security**
  - [ ] Database user has minimal permissions
  - [ ] Database not exposed to internet
  - [ ] Connection uses SSL (for remote databases)

---

## 🗄️ Database & Backups

- [ ] **Database**
  - [ ] Production database created
  - [ ] Migrations applied
  - [ ] Test data removed
  - [ ] Admin users created
  
- [ ] **Backup Strategy**
  - [ ] Automated database backups configured
  - [ ] Backup retention policy set
  - [ ] Backup restoration tested
  - [ ] Image uploads backup configured

---

## 🌐 Web Server Configuration

- [ ] **Application Server**
  - [ ] Gunicorn installed (or production WSGI server)
  - [ ] Systemd service created (for Linux)
  - [ ] Auto-restart on failure configured
  - [ ] Log files configured
  
- [ ] **Reverse Proxy**
  - [ ] Nginx (or Apache) installed
  - [ ] Reverse proxy configured
  - [ ] Static files served by nginx
  - [ ] Gzip compression enabled
  
- [ ] **Firewall**
  - [ ] Only ports 80/443 exposed
  - [ ] Port 5000 blocked from internet
  - [ ] Database port not exposed

---

## 📝 Documentation

- [ ] **README Updated**
  - [ ] Installation instructions
  - [ ] Configuration guide
  - [ ] Usage examples
  
- [ ] **Admin Documentation**
  - [ ] How to create users
  - [ ] How to manage styles
  - [ ] How to run backups
  - [ ] Troubleshooting guide

---

## 🧪 Testing

- [ ] **Functional Testing**
  - [ ] User registration works
  - [ ] Email verification works
  - [ ] Login/logout works
  - [ ] Style creation works
  - [ ] Pricing calculations correct
  - [ ] Excel export works
  - [ ] Image upload works
  
- [ ] **Performance Testing**
  - [ ] Page load times acceptable
  - [ ] Database queries optimized
  - [ ] No N+1 query problems
  
- [ ] **Security Testing**
  - [ ] CSRF protection works
  - [ ] SQL injection protected
  - [ ] XSS protection works
  - [ ] Authentication required on protected pages

---

## 📊 Monitoring & Logging

- [ ] **Logging**
  - [ ] Log rotation configured
  - [ ] Error logs monitored
  - [ ] Log retention policy set
  
- [ ] **Monitoring** (Optional but recommended)
  - [ ] Application monitoring (e.g., Sentry)
  - [ ] Server monitoring (e.g., New Relic, DataDog)
  - [ ] Uptime monitoring (e.g., UptimeRobot)
  - [ ] Error alerting configured

---

## 🚀 Deployment

- [ ] **Pre-Deployment**
  - [ ] Code reviewed
  - [ ] All tests passing
  - [ ] Database backed up
  - [ ] Deployment plan documented
  
- [ ] **Deployment**
  - [ ] Code deployed to server
  - [ ] Dependencies installed
  - [ ] Environment variables set
  - [ ] Database migrated
  - [ ] Static files collected
  - [ ] Web server restarted
  
- [ ] **Post-Deployment**
  - [ ] Smoke tests completed
  - [ ] Admin can login
  - [ ] Basic functionality works
  - [ ] Error logs checked
  - [ ] Performance acceptable

---

## 🎯 Production Readiness

### Essential (Must Have)
- [ ] All critical issues fixed
- [ ] Application starts successfully
- [ ] Database configured and accessible
- [ ] HTTPS enabled
- [ ] Backups configured

### Important (Should Have)
- [ ] Monitoring enabled
- [ ] Log rotation configured
- [ ] Documentation complete
- [ ] Automated deployment

### Nice to Have
- [ ] Automated tests
- [ ] CI/CD pipeline
- [ ] Staging environment
- [ ] Performance monitoring

---

## 📞 Emergency Contacts

**Before going live, document:**

- [ ] Server access credentials (stored securely)
- [ ] Database access credentials (stored securely)
- [ ] Email service credentials
- [ ] DNS provider access
- [ ] SSL certificate renewal date
- [ ] Who to contact for issues

---

## ✅ Final Sign-Off

Before marking complete, verify:

- [ ] All critical checklist items completed
- [ ] Application tested in production-like environment
- [ ] Team trained on how to use the application
- [ ] Support plan in place
- [ ] Backup and recovery tested

---

**Deployment Date:** _______________

**Deployed By:** _______________

**Sign-Off:** _______________

---

**Last Updated:** December 8, 2025
