"""
Gunicorn Configuration for J.A. Uniforms Pricing Tool
=====================================================

Production WSGI server configuration.

Usage:
    gunicorn -c gunicorn.conf.py app:app

Or with systemd service for auto-start on boot.
"""

import multiprocessing
import os

# ============================================
# SERVER SOCKET
# ============================================

# Bind to all interfaces so other computers can connect
bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:5000")

# Number of pending connections (backlog)
backlog = 2048

# ============================================
# WORKER PROCESSES
# ============================================

# Number of worker processes
# Formula: (2 x CPU cores) + 1
workers = int(os.environ.get("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))

# Worker class (sync is fine for most use cases)
worker_class = "sync"

# Maximum number of simultaneous clients
worker_connections = 1000

# Worker timeout (seconds) - increase for long-running requests
timeout = 120

# Keep-alive connections timeout
keepalive = 5

# Maximum requests per worker before respawn (prevents memory leaks)
max_requests = 1000
max_requests_jitter = 50

# ============================================
# PROCESS NAMING
# ============================================

# Process name for monitoring
proc_name = "ja_uniforms"

# ============================================
# LOGGING
# ============================================

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Access log
accesslog = "logs/gunicorn_access.log"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Error log
errorlog = "logs/gunicorn_error.log"

# Log level: debug, info, warning, error, critical
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")

# Capture output from application
capture_output = True

# Enable access logging to stdout for Docker
accesslog = "-" if os.environ.get("DOCKER") else "logs/gunicorn_access.log"

# ============================================
# SECURITY
# ============================================

# Limit request line size (URL length)
limit_request_line = 4094

# Limit number of HTTP headers
limit_request_fields = 100

# Limit size of HTTP header
limit_request_field_size = 8190

# ============================================
# SERVER HOOKS
# ============================================

def on_starting(server):
    """Called when Gunicorn starts."""
    print("="*60)
    print("J.A. UNIFORMS - Starting Production Server")
    print("="*60)
    print(f"Workers: {workers}")
    print(f"Binding: {bind}")
    print("="*60)


def on_reload(server):
    """Called when Gunicorn reloads."""
    print("Reloading J.A. Uniforms application...")


def worker_exit(server, worker):
    """Called when a worker exits."""
    pass  # Can add cleanup logic here


def on_exit(server):
    """Called when Gunicorn shuts down."""
    print("J.A. Uniforms application stopped.")


# ============================================
# ENVIRONMENT-SPECIFIC SETTINGS
# ============================================

# Production mode
if os.environ.get("FLASK_ENV") == "production":
    # Stricter settings for production
    timeout = 60
    loglevel = "warning"
    
# Development mode
elif os.environ.get("FLASK_ENV") == "development":
    # More permissive settings for development
    reload = True
    reload_engine = "auto"
    loglevel = "debug"
    workers = 1
