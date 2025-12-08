#!/bin/bash

# J.A. Uniforms Pricing Tool - Quick Setup Script
# This script helps you get started quickly

set -e  # Exit on error

echo "======================================================================"
echo "  J.A. Uniforms Pricing Tool - Quick Setup"
echo "======================================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env exists
echo "📋 Checking configuration..."
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ Created .env file${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  IMPORTANT: Edit .env file and set:${NC}"
    echo "   - SECRET_KEY (generate with: python3 -c \"import secrets; print(secrets.token_hex(32))\")"
    echo "   - DATABASE_URL (or keep SQLite default for testing)"
    echo "   - MAIL_* settings (for email verification)"
    echo ""
    read -p "Press Enter after you've edited .env to continue..."
else
    echo -e "${GREEN}✅ .env file exists${NC}"
fi

# Check if backup_database.ps1 exists (security issue)
if [ -f backup_database.ps1 ]; then
    echo ""
    echo -e "${RED}🔴 SECURITY WARNING!${NC}"
    echo -e "${RED}   backup_database.ps1 contains a hardcoded password!${NC}"
    echo ""
    read -p "Move it outside repository? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        mv backup_database.ps1 ../backup_database.ps1.old
        echo "*.ps1" >> .gitignore
        echo -e "${GREEN}✅ Moved backup_database.ps1 and added *.ps1 to .gitignore${NC}"
    else
        echo -e "${YELLOW}⚠️  Skipped. Please fix this security issue manually!${NC}"
    fi
fi

# Check Python version
echo ""
echo "🐍 Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ $PYTHON_VERSION found${NC}"
else
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.7+${NC}"
    exit 1
fi

# Create virtual environment
echo ""
echo "📦 Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "📚 Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ All dependencies installed successfully${NC}"
else
    echo -e "${RED}❌ Failed to install dependencies${NC}"
    exit 1
fi

# Check database
echo ""
echo "🗄️  Setting up database..."
if grep -q "sqlite" .env 2>/dev/null || ! grep -q "DATABASE_URL" .env 2>/dev/null; then
    echo -e "${GREEN}✅ Using SQLite (good for testing)${NC}"
else
    echo -e "${YELLOW}⚠️  Using PostgreSQL. Make sure database exists!${NC}"
fi

echo ""
echo "======================================================================"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "======================================================================"
echo ""
echo "🚀 To start your application:"
echo ""
echo "   1. Make sure you've edited .env with your settings"
echo "   2. Run: source venv/bin/activate"
echo "   3. Run: python3 app.py"
echo "   4. Open: http://localhost:5000"
echo ""
echo "📚 For detailed instructions, see:"
echo "   - QUICK_START_GUIDE.md"
echo "   - APPLICATION_READINESS_REPORT.md"
echo ""
echo "======================================================================"
