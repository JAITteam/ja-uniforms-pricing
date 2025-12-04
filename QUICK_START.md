# 🚀 J.A. Uniforms - Quick Start Guide

**Get your application running in production in 15 minutes!**

---

## Prerequisites

- Ubuntu 22.04 LTS or Debian 12 server
- Sudo access
- Server connected to your network
- 8GB RAM recommended

---

## Installation (3 Commands!)

### 1️⃣ Run Automated Setup

```bash
cd /workspace
sudo ./setup_production.sh
```

**This does everything!**
- Installs PostgreSQL, Nginx, Python
- Creates database
- Configures services
- Sets up backups
- Configures firewall

**Time**: ~10 minutes

---

### 2️⃣ Migrate Your Data (if you have SQLite data)

```bash
# Export from SQLite
python3 export_sqlite_data.py

# Import to PostgreSQL
python3 import_to_postgresql.py
```

**Time**: ~2 minutes

---

### 3️⃣ Access Your Application

```bash
# Find your server IP
hostname -I | awk '{print $1}'

# Open browser on any network computer:
# http://<that-ip-address>
```

**Time**: ~1 minute

---

## ✅ That's It!

Your application is now running in production on your local network!

---

## 🔍 Quick Checks

### Is it running?

```bash
./check_health.sh
```

Should show all ✅ green checkmarks.

### Can I access it?

On any computer on your network, open browser:
```
http://<your-server-ip>
```

You should see the login page.

### Where are the logs?

```bash
./monitor_logs.sh
```

Choose option 1 for application logs.

---

## 🛠️ Common Commands

```bash
# Check status
sudo systemctl status ja_uniforms

# Restart application
sudo systemctl restart ja_uniforms

# View logs
sudo journalctl -u ja_uniforms -f

# Create backup
./backup_database.sh

# Update application
sudo ./update_app.sh
```

---

## 🔐 Security Notes

1. **Change default passwords** in `.env` file
2. **Setup HTTPS** for secure connections (optional for internal network)
3. **Enable firewall** (done automatically by setup script)

---

## 📞 Need Help?

1. Check logs: `./monitor_logs.sh`
2. Run health check: `./check_health.sh`
3. Read full guide: `DEPLOYMENT_GUIDE.md`
4. Contact: it@jauniforms.com

---

## 🎉 Success!

You now have a production-ready application running on your own hardware for **$0/month**!

**Access**: `http://<server-ip>` from any computer on your network  
**Backups**: Automatic daily at 2 AM  
**Updates**: Simple with `./update_app.sh`  
**Monitoring**: `./check_health.sh` or `./monitor_logs.sh`

---

**Enjoy your production deployment! 🎊**
