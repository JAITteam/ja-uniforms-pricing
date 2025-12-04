#!/bin/bash

#############################################
# J.A. Uniforms - Database Backup Script
# Backs up PostgreSQL database with rotation
#############################################

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Configuration
BACKUP_DIR="/var/backups/ja_uniforms"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/ja_uniforms_backup_$DATE.sql"
KEEP_DAYS=7  # Keep backups for 7 days

# Database connection from .env
DB_NAME="ja_uniforms_prod"
DB_USER="ja_admin"
DB_HOST="localhost"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🗄️  J.A. Uniforms - Database Backup${NC}"
echo "================================================"
echo "Date: $(date)"
echo "Backup Location: $BACKUP_FILE"
echo ""

# Create backup directory if it doesn't exist
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${YELLOW}📁 Creating backup directory...${NC}"
    mkdir -p "$BACKUP_DIR"
    chmod 700 "$BACKUP_DIR"
fi

# Create backup
echo -e "${GREEN}📦 Creating database backup...${NC}"
if pg_dump -U $DB_USER -h $DB_HOST $DB_NAME > "$BACKUP_FILE"; then
    # Compress backup
    echo -e "${GREEN}🗜️  Compressing backup...${NC}"
    gzip "$BACKUP_FILE"
    BACKUP_FILE="${BACKUP_FILE}.gz"
    
    # Get file size
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✅ Backup successful!${NC}"
    echo "   File: $BACKUP_FILE"
    echo "   Size: $SIZE"
else
    echo -e "${RED}❌ Backup failed!${NC}"
    exit 1
fi

# Also backup uploaded files (images)
echo ""
echo -e "${GREEN}📸 Backing up uploaded files...${NC}"
FILES_BACKUP="$BACKUP_DIR/ja_uniforms_files_$DATE.tar.gz"
if [ -d "static/img" ]; then
    tar -czf "$FILES_BACKUP" static/img/
    FILES_SIZE=$(du -h "$FILES_BACKUP" | cut -f1)
    echo -e "${GREEN}✅ Files backup successful!${NC}"
    echo "   File: $FILES_BACKUP"
    echo "   Size: $FILES_SIZE"
fi

# Backup .env file (encrypted)
echo ""
echo -e "${GREEN}🔐 Backing up configuration...${NC}"
if [ -f ".env" ]; then
    ENV_BACKUP="$BACKUP_DIR/ja_uniforms_env_$DATE.tar.gz"
    tar -czf "$ENV_BACKUP" .env
    echo -e "${GREEN}✅ Configuration backup successful!${NC}"
fi

# Clean up old backups (older than KEEP_DAYS)
echo ""
echo -e "${YELLOW}🧹 Cleaning up old backups (older than $KEEP_DAYS days)...${NC}"
find "$BACKUP_DIR" -name "ja_uniforms_backup_*.sql.gz" -mtime +$KEEP_DAYS -delete
find "$BACKUP_DIR" -name "ja_uniforms_files_*.tar.gz" -mtime +$KEEP_DAYS -delete
find "$BACKUP_DIR" -name "ja_uniforms_env_*.tar.gz" -mtime +$KEEP_DAYS -delete

# List recent backups
echo ""
echo -e "${GREEN}📋 Recent backups:${NC}"
ls -lh "$BACKUP_DIR" | grep "ja_uniforms" | tail -5

echo ""
echo -e "${GREEN}✅ Backup process complete!${NC}"
echo "================================================"

# Optional: Send notification (requires mail command)
# echo "Backup completed: $DATE" | mail -s "J.A. Uniforms Backup Success" admin@jauniforms.com

exit 0
