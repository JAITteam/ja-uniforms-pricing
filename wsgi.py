"""
WSGI entry point for production deployment
Used by Gunicorn to run the application
"""
from app import app

if __name__ == "__main__":
    app.run()
