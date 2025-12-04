#!/bin/bash

###############################################
# J.A. Uniforms - Production Setup Script
# Automates the setup process for deployment
###############################################

set -e  # Exit on any error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
     ██╗   █████╗     ██╗   ██╗███╗   ██╗██╗███████╗ ██████╗ ██████╗ ███╗   ███╗███████╗
     ██║  ██╔══██╗    ██║   ██║████╗  ██║██║██╔════╝██╔═══██╗██╔══██╗████╗ ████║██╔════╝
     ██║  ███████║    ██║   ██║██╔██╗ ██║██║█████╗  ██║   ██║██████╔╝██╔████╔██║███████╗
██   ██║  ██╔══██║    ██║   ██║██║╚██╗██║██║██╔══╝  ██║   ██║██╔══██╗██║╚██╔╝██║╚════██║
╚█████╔╝  ██║  ██║    ╚██████╔╝██║ ╚████║██║██║     ╚██████╔╝██║  ██║██║ ╚═╝ ██║███████║
 ╚════╝   ╚═╝  ╚═╝     ╚═════╝ ╚═╝  ╚═══╝╚═╝╚═╝      ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝
                                                                                           
                      PRODUCTION SETUP SCRIPT                                             
EOF
echo -e "${NC}"

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Starting Production Setup...${NC}"
echo -e "${GREEN}================================================${NC}\n"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Please run with sudo${NC}"
    exit 1
fi

# Get the actual user (not root)
ACTUAL_USER=${SUDO_USER:-$USER}
echo -e "${YELLOW}👤 Running as user: $ACTUAL_USER${NC}\n"

# Step 1: Update system
echo -e "${GREEN}📦 Step 1: Updating system packages...${NC}"
apt update
apt upgrade -y

# Step 2: Install PostgreSQL
echo -e "\n${GREEN}🗄️  Step 2: Installing PostgreSQL...${NC}"
if ! command -v psql &> /dev/null; then
    apt install -y postgresql postgresql-contrib
    systemctl enable postgresql
    systemctl start postgresql
    echo -e "${GREEN}✅ PostgreSQL installed${NC}"
else
    echo -e "${YELLOW}⊘ PostgreSQL already installed${NC}"
fi

# Step 3: Install Nginx
echo -e "\n${GREEN}🌐 Step 3: Installing Nginx...${NC}"
if ! command -v nginx &> /dev/null; then
    apt install -y nginx
    systemctl enable nginx
    echo -e "${GREEN}✅ Nginx installed${NC}"
else
    echo -e "${YELLOW}⊘ Nginx already installed${NC}"
fi

# Step 4: Install Python and pip
echo -e "\n${GREEN}🐍 Step 4: Installing Python...${NC}"
apt install -y python3 python3-pip python3-venv python3-dev build-essential libpq-dev

# Step 5: Create directories
echo -e "\n${GREEN}📁 Step 5: Creating required directories...${NC}"
mkdir -p /var/log/ja_uniforms
mkdir -p /var/run/ja_uniforms
mkdir -p /var/backups/ja_uniforms
chown -R $ACTUAL_USER:www-data /var/log/ja_uniforms
chown -R $ACTUAL_USER:www-data /var/run/ja_uniforms
chown -R $ACTUAL_USER:www-data /var/backups/ja_uniforms
chmod 770 /var/log/ja_uniforms
chmod 770 /var/run/ja_uniforms
chmod 700 /var/backups/ja_uniforms

# Step 6: Setup PostgreSQL database
echo -e "\n${GREEN}🗄️  Step 6: Setting up PostgreSQL database...${NC}"
read -p "Create PostgreSQL database? (yes/no): " create_db

if [ "$create_db" = "yes" ]; then
    read -p "Enter database name [ja_uniforms_prod]: " DB_NAME
    DB_NAME=${DB_NAME:-ja_uniforms_prod}
    
    read -p "Enter database user [ja_admin]: " DB_USER
    DB_USER=${DB_USER:-ja_admin}
    
    read -sp "Enter database password: " DB_PASS
    echo ""
    
    sudo -u postgres psql << EOF
CREATE DATABASE $DB_NAME;
CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
\q
EOF
    
    echo -e "${GREEN}✅ Database created${NC}"
    echo -e "${YELLOW}📝 Add this to your .env file:${NC}"
    echo "DATABASE_URL=postgresql://$DB_USER:$DB_PASS@localhost/$DB_NAME"
fi

# Step 7: Setup virtual environment
echo -e "\n${GREEN}🔧 Step 7: Setting up Python virtual environment...${NC}"
cd /workspace
if [ ! -d ".venv" ]; then
    sudo -u $ACTUAL_USER python3 -m venv .venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Step 8: Install Python dependencies
echo -e "\n${GREEN}📚 Step 8: Installing Python dependencies...${NC}"
sudo -u $ACTUAL_USER .venv/bin/pip install --upgrade pip
sudo -u $ACTUAL_USER .venv/bin/pip install -r requirements.txt
sudo -u $ACTUAL_USER .venv/bin/pip install psycopg2-binary gunicorn

# Step 9: Setup environment file
echo -e "\n${GREEN}🔐 Step 9: Setting up .env file...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    # Generate secure SECRET_KEY
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    sed -i "s/your-secret-key-here-change-in-production/$SECRET_KEY/" .env
    sed -i "s/FLASK_ENV=development/FLASK_ENV=production/" .env
    echo "FLASK_DEBUG=False" >> .env
    chown $ACTUAL_USER:www-data .env
    chmod 640 .env
    echo -e "${GREEN}✅ .env file created${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env and update database credentials${NC}"
else
    echo -e "${YELLOW}⊘ .env already exists${NC}"
fi

# Step 10: Run database migrations
echo -e "\n${GREEN}🗄️  Step 10: Running database migrations...${NC}"
read -p "Run migrations now? (yes/no): " run_migrations
if [ "$run_migrations" = "yes" ]; then
    sudo -u $ACTUAL_USER .venv/bin/flask db upgrade
    echo -e "${GREEN}✅ Migrations complete${NC}"
fi

# Step 11: Setup systemd service
echo -e "\n${GREEN}⚙️  Step 11: Setting up systemd service...${NC}"
cp ja_uniforms.service /etc/systemd/system/
sed -i "s|User=ubuntu|User=$ACTUAL_USER|" /etc/systemd/system/ja_uniforms.service
systemctl daemon-reload
systemctl enable ja_uniforms
echo -e "${GREEN}✅ Systemd service configured${NC}"

# Step 12: Setup Nginx
echo -e "\n${GREEN}🌐 Step 12: Setting up Nginx...${NC}"
cp nginx_ja_uniforms.conf /etc/nginx/sites-available/ja_uniforms
ln -sf /etc/nginx/sites-available/ja_uniforms /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default  # Remove default site
nginx -t  # Test configuration

# Step 13: Setup cron for backups
echo -e "\n${GREEN}⏰ Step 13: Setting up automated backups...${NC}"
chmod +x backup_database.sh
chmod +x restore_database.sh
# Add cron job (daily at 2 AM)
CRON_JOB="0 2 * * * cd /workspace && ./backup_database.sh >> /var/log/ja_uniforms/backup.log 2>&1"
(crontab -u $ACTUAL_USER -l 2>/dev/null | grep -v backup_database.sh; echo "$CRON_JOB") | crontab -u $ACTUAL_USER -
echo -e "${GREEN}✅ Backup cron job added (runs daily at 2 AM)${NC}"

# Step 14: Setup firewall
echo -e "\n${GREEN}🔥 Step 14: Configuring firewall...${NC}"
read -p "Configure UFW firewall? (yes/no): " setup_firewall
if [ "$setup_firewall" = "yes" ]; then
    ufw allow ssh
    ufw allow 'Nginx Full'
    ufw --force enable
    echo -e "${GREEN}✅ Firewall configured${NC}"
fi

# Step 15: Start services
echo -e "\n${GREEN}🚀 Step 15: Starting services...${NC}"
systemctl restart ja_uniforms
systemctl restart nginx

# Final status check
echo -e "\n${GREEN}================================================${NC}"
echo -e "${GREEN}📊 Service Status:${NC}"
echo -e "${GREEN}================================================${NC}"
systemctl status ja_uniforms --no-pager | head -n 10
systemctl status nginx --no-pager | head -n 5

echo -e "\n${GREEN}================================================${NC}"
echo -e "${GREEN}✅ SETUP COMPLETE!${NC}"
echo -e "${GREEN}================================================${NC}"

echo -e "\n${YELLOW}📋 Next Steps:${NC}"
echo "1. Edit .env file with your settings"
echo "2. Import your data: python3 import_to_postgresql.py"
echo "3. Access the application at: http://$(hostname -I | awk '{print $1}')"
echo "4. Check logs: sudo journalctl -u ja_uniforms -f"
echo ""
echo -e "${YELLOW}🔐 Security Reminders:${NC}"
echo "• Setup SSL/TLS certificates for HTTPS"
echo "• Change default passwords"
echo "• Review firewall rules"
echo "• Setup fail2ban for additional security"
echo ""
echo -e "${GREEN}🎉 J.A. Uniforms is ready for production!${NC}"
