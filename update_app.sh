#!/bin/bash

#############################################
# J.A. Uniforms - Application Update Script
# Safely update the application
#############################################

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🔄 J.A. Uniforms - Application Update${NC}"
echo "================================================"

# Check if running as sudo
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Please run with sudo${NC}"
    exit 1
fi

ACTUAL_USER=${SUDO_USER:-$USER}

# Step 1: Create backup
echo ""
echo -e "${YELLOW}📦 Step 1: Creating backup...${NC}"
cd /workspace
sudo -u $ACTUAL_USER ./backup_database.sh

# Step 2: Stop application
echo ""
echo -e "${YELLOW}🛑 Step 2: Stopping application...${NC}"
systemctl stop ja_uniforms
echo -e "${GREEN}✅ Application stopped${NC}"

# Step 3: Update code (if using git)
echo ""
echo -e "${YELLOW}📥 Step 3: Updating code...${NC}"
read -p "Update from git? (yes/no): " update_git
if [ "$update_git" = "yes" ]; then
    sudo -u $ACTUAL_USER git pull origin main
    echo -e "${GREEN}✅ Code updated${NC}"
else
    echo -e "${YELLOW}⊘ Skipping git update${NC}"
fi

# Step 4: Update dependencies
echo ""
echo -e "${YELLOW}📚 Step 4: Updating Python dependencies...${NC}"
sudo -u $ACTUAL_USER .venv/bin/pip install -r requirements.txt --upgrade
echo -e "${GREEN}✅ Dependencies updated${NC}"

# Step 5: Run migrations
echo ""
echo -e "${YELLOW}🗄️  Step 5: Running database migrations...${NC}"
read -p "Run migrations? (yes/no): " run_migrations
if [ "$run_migrations" = "yes" ]; then
    sudo -u $ACTUAL_USER .venv/bin/flask db upgrade
    echo -e "${GREEN}✅ Migrations complete${NC}"
else
    echo -e "${YELLOW}⊘ Skipping migrations${NC}"
fi

# Step 6: Restart application
echo ""
echo -e "${YELLOW}🚀 Step 6: Restarting application...${NC}"
systemctl start ja_uniforms
systemctl restart nginx

# Wait for application to start
sleep 3

# Step 7: Check status
echo ""
echo -e "${YELLOW}🔍 Step 7: Checking status...${NC}"
if systemctl is-active --quiet ja_uniforms; then
    echo -e "${GREEN}✅ Application is running${NC}"
    
    # Test health endpoint
    HEALTH=$(curl -s http://localhost:5000/health | grep -o '"status":"healthy"')
    if [ ! -z "$HEALTH" ]; then
        echo -e "${GREEN}✅ Health check passed${NC}"
    else
        echo -e "${RED}⚠️  Health check failed${NC}"
    fi
else
    echo -e "${RED}❌ Application failed to start${NC}"
    echo "Check logs: sudo journalctl -u ja_uniforms -n 50"
    exit 1
fi

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}✅ Update complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Access the application at: http://$(hostname -I | awk '{print $1}')"
