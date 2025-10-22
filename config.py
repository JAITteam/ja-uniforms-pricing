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