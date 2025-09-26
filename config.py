import os

class Config:
    # Secret key for forms and sessions
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ja-uniforms-secret-key-2024'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///uniforms.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload folder for Excel files
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size