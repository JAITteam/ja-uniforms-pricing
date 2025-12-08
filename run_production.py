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
    print("=" * 50)
    print("  J.A. Uniforms Production Server")
    print("=" * 50)
    print("")
    print("  Server is running!")
    print("")
    print("  Access URLs:")
    print(f"  • Local:   http://127.0.0.1:5000")
    print(f"  • Network: http://{local_ip}:5000")
    print("")
    print("  Press Ctrl+C to stop the server")
    print("=" * 50)
    print("")
    
    serve(app, host='0.0.0.0', port=5000, threads=4)