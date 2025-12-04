#!/bin/bash

#############################################
# J.A. Uniforms - Database Restore Script
# Restores PostgreSQL database from backup
#############################################

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Configuration
BACKUP_DIR="/var/backups/ja_uniforms"
DB_NAME="ja_uniforms_prod"
DB_USER="ja_admin"
DB_HOST="localhost"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${RED}⚠️  J.A. Uniforms - Database Restore${NC}"
echo "================================================"
echo "⚠️  WARNING: This will replace your current database!"
echo ""

# List available backups
echo -e "${GREEN}📋 Available backups:${NC}"
ls -lh "$BACKUP_DIR"/*.sql.gz 2>/dev/null | nl

if [ ! "$(ls -A $BACKUP_DIR/*.sql.gz 2>/dev/null)" ]; then
    echo -e "${RED}❌ No backups found in $BACKUP_DIR${NC}"
    exit 1
fi

# Ask for backup file
echo ""
read -p "Enter backup file number or full path: " choice

# Get backup file
if [[ "$choice" =~ ^[0-9]+$ ]]; then
    # User entered a number from the list
    BACKUP_FILE=$(ls "$BACKUP_DIR"/*.sql.gz | sed -n "${choice}p")
else
    # User entered full path
    BACKUP_FILE="$choice"
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}❌ Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Selected backup:${NC} $BACKUP_FILE"
echo ""
read -p "Are you sure you want to restore? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${YELLOW}Restore cancelled${NC}"
    exit 0
fi

# Create a backup of current database before restoring
echo ""
echo -e "${GREEN}📦 Creating backup of current database...${NC}"
SAFETY_BACKUP="$BACKUP_DIR/pre_restore_backup_$(date +%Y%m%d_%H%M%S).sql.gz"
pg_dump -U $DB_USER -h $DB_HOST $DB_NAME | gzip > "$SAFETY_BACKUP"
echo -e "${GREEN}✅ Safety backup created: $SAFETY_BACKUP${NC}"

# Drop existing database
echo ""
echo -e "${YELLOW}🗑️  Dropping existing database...${NC}"
dropdb -U $DB_USER -h $DB_HOST $DB_NAME --if-exists

# Create fresh database
echo -e "${GREEN}🆕 Creating fresh database...${NC}"
createdb -U $DB_USER -h $DB_HOST $DB_NAME

# Restore from backup
echo -e "${GREEN}📥 Restoring from backup...${NC}"
if gunzip -c "$BACKUP_FILE" | psql -U $DB_USER -h $DB_HOST $DB_NAME > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Database restored successfully!${NC}"
else
    echo -e "${RED}❌ Restore failed!${NC}"
    echo -e "${YELLOW}⚠️  Restoring from safety backup...${NC}"
    gunzip -c "$SAFETY_BACKUP" | psql -U $DB_USER -h $DB_HOST $DB_NAME
    exit 1
fi

# Restore files if backup exists
FILES_BACKUP="${BACKUP_FILE%.sql.gz}"
FILES_BACKUP="${FILES_BACKUP/backup/files}.tar.gz"

if [ -f "$FILES_BACKUP" ]; then
    echo ""
    read -p "Restore uploaded files too? (yes/no): " restore_files
    if [ "$restore_files" = "yes" ]; then
        echo -e "${GREEN}📸 Restoring uploaded files...${NC}"
        tar -xzf "$FILES_BACKUP"
        echo -e "${GREEN}✅ Files restored${NC}"
    fi
fi

echo ""
echo -e "${GREEN}✅ Restore complete!${NC}"
echo "================================================"

exit 0
