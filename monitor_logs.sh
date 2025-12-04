#!/bin/bash

#############################################
# J.A. Uniforms - Log Monitoring Script
# Real-time log monitoring with filtering
#############################################

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}📊 J.A. Uniforms - Log Monitor${NC}"
echo "================================================"
echo ""
echo "Select log to monitor:"
echo "1. Application logs (systemd journal)"
echo "2. Gunicorn error logs"
echo "3. Nginx access logs"
echo "4. Nginx error logs"
echo "5. Application file logs"
echo "6. All errors (filtered)"
echo ""
read -p "Enter choice (1-6): " choice

case $choice in
    1)
        echo -e "${GREEN}Monitoring application logs...${NC}"
        echo "Press Ctrl+C to exit"
        echo ""
        sudo journalctl -u ja_uniforms -f
        ;;
    2)
        echo -e "${GREEN}Monitoring Gunicorn errors...${NC}"
        echo "Press Ctrl+C to exit"
        echo ""
        tail -f /var/log/ja_uniforms/gunicorn_error.log
        ;;
    3)
        echo -e "${GREEN}Monitoring Nginx access...${NC}"
        echo "Press Ctrl+C to exit"
        echo ""
        tail -f /var/log/nginx/ja_uniforms_access.log
        ;;
    4)
        echo -e "${GREEN}Monitoring Nginx errors...${NC}"
        echo "Press Ctrl+C to exit"
        echo ""
        tail -f /var/log/nginx/ja_uniforms_error.log
        ;;
    5)
        echo -e "${GREEN}Monitoring application file logs...${NC}"
        echo "Press Ctrl+C to exit"
        echo ""
        tail -f /workspace/logs/ja_uniforms.log
        ;;
    6)
        echo -e "${RED}Monitoring all errors...${NC}"
        echo "Press Ctrl+C to exit"
        echo ""
        echo "Recent errors:"
        sudo journalctl -u ja_uniforms --since today | grep -i error | tail -20
        echo ""
        echo "Watching for new errors..."
        sudo journalctl -u ja_uniforms -f | grep -i error
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac
