# run_production.py
import socket
from waitress import serve
from app import app

def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "Unable to detect"

if __name__ == '__main__':
    local_ip = get_local_ip()
    
    print("")
    print("=" * 70)
    print("  J.A. Uniforms Production Server")
    print("=" * 70)
    print("")
    print("  🚀 Server Configuration:")
    print("     • Threads: 8 concurrent requests")
    print("     • Max Connections: 1000")
    print("     • Timeout: 120 seconds")
    print("     • Max Upload: 50 MB")
    print("")
    print("  📡 Access URLs:")
    print(f"     • Local:   http://127.0.0.1:5000")
    print(f"     • Network: http://{local_ip}:5000")
    print("")
    print("  Press Ctrl+C to stop the server")
    print("=" * 70)
    print("")
    
    serve(
        app,
        host='0.0.0.0',
        port=5000,
        threads=8,                      # Handle 8 simultaneous requests
        connection_limit=1000,          # Max 1000 simultaneous connections
        channel_timeout=120,            # Close idle connections after 2 minutes
        max_request_body_size=52428800, # 50 MB max upload size
        recv_bytes=65536,               # 64 KB receive buffer for faster uploads
        send_bytes=65536,               # 64 KB send buffer for faster downloads
        expose_tracebacks=False,        # Hide error details from users (security)
        backlog=2048,                   # Queue for pending connections
        cleanup_interval=30,            # Clean stale connections every 30 seconds
    )