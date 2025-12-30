import os
from datetime import timedelta

class Config:
    # Secret key for forms, sessions, and CSRF protection
    # ===== FIXED: Now properly loads from environment =====
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # If SECRET_KEY not set, generate one for development (with warning)
    if not SECRET_KEY:
        import secrets
        SECRET_KEY = secrets.token_hex(32)
        print("\n" + "="*70)
        print("⚠️  WARNING: No SECRET_KEY found in environment!")
        print("⚠️  Using auto-generated key for development only.")
        print("⚠️  For production, set SECRET_KEY in your .env file!")
        print("="*70 + "\n")
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///uniforms.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ===== DATABASE CONNECTION POOLING =====
    # Optimized for production with multiple concurrent users
    SQLALCHEMY_POOL_SIZE = 20              # Keep 20 persistent connections ready
    SQLALCHEMY_MAX_OVERFLOW = 10           # Allow 10 extra connections (total = 30)
    SQLALCHEMY_POOL_TIMEOUT = 30           # Wait 30 seconds for available connection
    SQLALCHEMY_POOL_RECYCLE = 3600         # Recycle connections every 1 hour (prevents stale connections)
    SQLALCHEMY_POOL_PRE_PING = True        # Test connections before use (prevents "server has gone away" errors)
    SQLALCHEMY_ECHO_POOL = False           # Disable connection logging in production (set True for debugging)
    
    # Upload folder for Excel files and images
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # No time limit for CSRF tokens
    WTF_CSRF_SSL_STRICT = False  # Set to True if using HTTPS in production
    
    # Session configuration
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    REMEMBER_COOKIE_DURATION = timedelta(days=30)  # ← ADD THIS LINE (Remember Me lasts 30 days)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'

    # Email Configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@jauniforms.com')
