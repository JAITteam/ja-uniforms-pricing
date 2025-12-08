@echo off
REM ============================================
REM J.A. Uniforms - Production Server Startup
REM For Internal Company Network
REM ============================================

echo.
echo ========================================
echo   J.A. Uniforms Pricing Tool
echo   Starting Production Server...
echo ========================================
echo.

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo [OK] Virtual environment activated
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo [OK] Virtual environment activated
) else (
    echo [WARNING] No virtual environment found, using system Python
)

REM Check if .env exists
if not exist ".env" (
    echo [ERROR] .env file not found!
    echo [INFO] Please copy .env.example to .env and configure it
    echo.
    pause
    exit /b 1
)

REM Load environment variables from .env
for /f "tokens=*" %%a in ('type .env ^| findstr /v "^#" ^| findstr /v "^$"') do set %%a

REM Check required variables
if "%SECRET_KEY%"=="" (
    echo [ERROR] SECRET_KEY not set in .env file!
    pause
    exit /b 1
)

if "%DATABASE_URL%"=="" (
    echo [WARNING] DATABASE_URL not set, using SQLite
)

REM Run database migrations
echo.
echo [INFO] Running database migrations...
python -m flask db upgrade
if errorlevel 1 (
    echo [WARNING] Migration failed or no migrations to run
)

REM Get local IP address for display
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set LOCAL_IP=%%a
    goto :found_ip
)
:found_ip
set LOCAL_IP=%LOCAL_IP: =%

echo.
echo ========================================
echo   Server Starting...
echo ========================================
echo.
echo   Access the application at:
echo   - Local:   http://localhost:5000
echo   - Network: http://%LOCAL_IP%:5000
echo.
echo   Share the Network URL with your team!
echo.
echo   Press Ctrl+C to stop the server
echo ========================================
echo.

REM Start with Waitress (Windows-compatible production server)
REM If you have waitress installed: pip install waitress
where waitress-serve >nul 2>&1
if %errorlevel%==0 (
    echo [INFO] Starting with Waitress (production mode)...
    waitress-serve --host=0.0.0.0 --port=5000 wsgi:app
) else (
    echo [INFO] Waitress not found, using Flask development server
    echo [TIP] For better performance, install Waitress: pip install waitress
    echo.
    set FLASK_DEBUG=False
    python app.py
)

pause
