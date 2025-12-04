#!/bin/bash

#############################################
# J.A. Uniforms - Health Check Script
# Quick health check for the application
#############################################

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🏥 J.A. Uniforms Health Check${NC}"
echo "========================================"

# Check if application is running
if systemctl is-active --quiet ja_uniforms; then
    echo -e "${GREEN}✅ Application Service: Running${NC}"
else
    echo -e "${RED}❌ Application Service: Not Running${NC}"
    echo "   Run: sudo systemctl start ja_uniforms"
fi

# Check if Nginx is running
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ Nginx Service: Running${NC}"
else
    echo -e "${RED}❌ Nginx Service: Not Running${NC}"
fi

# Check if PostgreSQL is running
if systemctl is-active --quiet postgresql; then
    echo -e "${GREEN}✅ PostgreSQL Service: Running${NC}"
else
    echo -e "${RED}❌ PostgreSQL Service: Not Running${NC}"
fi

# Check health endpoint
echo ""
echo "Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:5000/health)

if [ $? -eq 0 ]; then
    STATUS=$(echo $HEALTH_RESPONSE | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    if [ "$STATUS" = "healthy" ]; then
        echo -e "${GREEN}✅ Application Health: Healthy${NC}"
    else
        echo -e "${RED}❌ Application Health: Unhealthy${NC}"
        echo "   Response: $HEALTH_RESPONSE"
    fi
else
    echo -e "${RED}❌ Cannot reach health endpoint${NC}"
fi

# Check disk space
echo ""
echo "Disk Space:"
df -h / | tail -n 1 | awk '{print "   Used: "$3" / "$2" ("$5")"}'

DISK_USAGE=$(df / | tail -n 1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    echo -e "${RED}⚠️  Warning: Disk usage above 90%${NC}"
elif [ $DISK_USAGE -gt 80 ]; then
    echo -e "${YELLOW}⚠️  Warning: Disk usage above 80%${NC}"
fi

# Check memory
echo ""
echo "Memory Usage:"
free -h | grep Mem | awk '{print "   Used: "$3" / "$2}'

echo ""
echo "========================================"
echo -e "${GREEN}Health check complete!${NC}"
