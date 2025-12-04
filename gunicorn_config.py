"""
Gunicorn configuration file for J.A. Uniforms Production
"""
import multiprocessing
import os

# Server socket
bind = "127.0.0.1:5000"  # Only accessible via Nginx reverse proxy
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1  # Recommended formula
worker_class = 'sync'
worker_connections = 1000
timeout = 120  # 2 minutes for long-running requests
keepalive = 5

# Logging
accesslog = '/var/log/ja_uniforms/gunicorn_access.log'
errorlog = '/var/log/ja_uniforms/gunicorn_error.log'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = 'ja_uniforms'

# Server mechanics
daemon = False  # Don't daemonize (systemd will manage)
pidfile = '/var/run/ja_uniforms/gunicorn.pid'
user = None  # Run as the user that starts it
group = None
tmp_upload_dir = None

# SSL (optional - if not using Nginx)
# keyfile = '/path/to/ssl/key.pem'
# certfile = '/path/to/ssl/cert.pem'

# Server hooks
def on_starting(server):
    """Called just before the master process is initialized"""
    print("🚀 Starting J.A. Uniforms Application Server")

def on_reload(server):
    """Called when a worker is reloaded"""
    print("🔄 Reloading J.A. Uniforms workers")

def when_ready(server):
    """Called just after the server is started"""
    print(f"✅ J.A. Uniforms ready on {bind}")

def on_exit(server):
    """Called just before exiting"""
    print("👋 Shutting down J.A. Uniforms")
