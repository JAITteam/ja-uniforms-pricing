#!/bin/bash
# ============================================
# J.A. Uniforms - Production Server Startup
# For Internal Company Network (Linux/Mac)
# ============================================

echo ""
echo "========================================"
echo "  J.A. Uniforms Pricing Tool"
echo "  Starting Production Server..."
echo "========================================"
echo ""

# Activate virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "[OK] Virtual environment activated"
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "[OK] Virtual environment activated"
else
    echo "[WARNING] No virtual environment found, using system Python"
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "[ERROR] .env file not found!"
    echo "[INFO] Please copy .env.example to .env and configure it"
    exit 1
fi

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Check required variables
if [ -z "$SECRET_KEY" ]; then
    echo "[ERROR] SECRET_KEY not set in .env file!"
    exit 1
fi

if [ -z "$DATABASE_URL" ]; then
    echo "[WARNING] DATABASE_URL not set, using SQLite"
fi

# Run database migrations
echo ""
echo "[INFO] Running database migrations..."
python -m flask db upgrade 2>/dev/null || echo "[WARNING] Migration failed or no migrations to run"

# Get local IP address
LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "your-server-ip")

echo ""
echo "========================================"
echo "  Server Starting..."
echo "========================================"
echo ""
echo "  Access the application at:"
echo "  - Local:   http://localhost:5000"
echo "  - Network: http://${LOCAL_IP}:5000"
echo ""
echo "  Share the Network URL with your team!"
echo ""
echo "  Press Ctrl+C to stop the server"
echo "========================================"
echo ""

# Number of workers (2 x CPU cores + 1)
WORKERS=${GUNICORN_WORKERS:-4}

# Start with Gunicorn
echo "[INFO] Starting with Gunicorn (${WORKERS} workers)..."
gunicorn wsgi:app \
    --bind 0.0.0.0:5000 \
    --workers $WORKERS \
    --timeout 120 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --capture-output \
    --log-level info
