#!/bin/bash
# ============================================
# J.A. Uniforms - Production Start Script (Linux)
# ============================================
#
# Usage: ./scripts/start_production.sh
#
# ============================================

set -e

# Configuration
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$APP_DIR/.venv"
LOG_DIR="$APP_DIR/logs"
PID_FILE="$APP_DIR/gunicorn.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================"
echo "J.A. Uniforms - Production Server"
echo "============================================"
echo ""

# Check virtual environment
if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo -e "${RED}ERROR: Virtual environment not found!${NC}"
    echo "Create it with: python3 -m venv .venv"
    exit 1
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Check if gunicorn is installed
if ! command -v gunicorn &> /dev/null; then
    echo -e "${RED}ERROR: Gunicorn not installed!${NC}"
    echo "Install with: pip install gunicorn"
    exit 1
fi

# Create logs directory
mkdir -p "$LOG_DIR"

# Load environment variables
if [ -f "$APP_DIR/.env.production" ]; then
    echo -e "${GREEN}Loading production environment...${NC}"
    export $(cat "$APP_DIR/.env.production" | grep -v '^#' | xargs)
elif [ -f "$APP_DIR/.env" ]; then
    echo -e "${YELLOW}Warning: Using .env instead of .env.production${NC}"
    export $(cat "$APP_DIR/.env" | grep -v '^#' | xargs)
fi

# Set production mode
export FLASK_ENV=production
export FLASK_DEBUG=False

# Stop existing instance if running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Stopping existing instance (PID: $OLD_PID)..."
        kill "$OLD_PID"
        sleep 2
    fi
    rm -f "$PID_FILE"
fi

# Start Gunicorn
echo ""
echo "Starting Gunicorn..."
echo "  App Directory: $APP_DIR"
echo "  Logs: $LOG_DIR"
echo "  Config: gunicorn.conf.py"
echo ""

cd "$APP_DIR"

gunicorn \
    --config gunicorn.conf.py \
    --pid "$PID_FILE" \
    --daemon \
    app:app

# Wait for server to start
sleep 2

# Check if started successfully
if [ -f "$PID_FILE" ]; then
    NEW_PID=$(cat "$PID_FILE")
    if kill -0 "$NEW_PID" 2>/dev/null; then
        echo -e "${GREEN}Server started successfully!${NC}"
        echo ""
        echo "  PID: $NEW_PID"
        echo "  URL: http://0.0.0.0:5000"
        echo ""
        echo "To stop: kill $NEW_PID"
        echo "To view logs: tail -f $LOG_DIR/gunicorn_access.log"
    else
        echo -e "${RED}ERROR: Server failed to start!${NC}"
        echo "Check logs: cat $LOG_DIR/gunicorn_error.log"
        exit 1
    fi
else
    echo -e "${RED}ERROR: PID file not created!${NC}"
    exit 1
fi
