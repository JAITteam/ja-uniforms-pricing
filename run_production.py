# run_production.py
from waitress import serve
from app import app

if __name__ == '__main__':
    print("Starting J.A. Uniforms Production Server...")
    print("Running on http://0.0.0.0:5000")
    serve(app, host='0.0.0.0', port=5000, threads=4)