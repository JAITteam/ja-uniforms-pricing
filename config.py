import os
from datetime import timedelta

class Config:
    # Secret key for forms, sessions, and CSRF protection
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
    
    # Database configuration - PostgreSQL for production, SQLite for development
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///uniforms.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Connection pool settings for PostgreSQL (important for multiple users)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # Verify connections before use
        'pool_recycle': 300,    # Recycle connections after 5 minutes
        'pool_size': 10,        # Number of connections to keep open
        'max_overflow': 20,     # Additional connections when pool is full
    }
    
    # Upload folder for Excel files and images
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # No time limit for CSRF tokens
    WTF_CSRF_SSL_STRICT = False  # Set to True if using HTTPS
    
    # Session configuration
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    
    # For HTTPS deployments (uncomment if using SSL)
    # SESSION_COOKIE_SECURE = True
    # REMEMBER_COOKIE_SECURE = True

    # Email Configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@jauniforms.com')
