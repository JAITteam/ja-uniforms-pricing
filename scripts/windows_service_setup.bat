@echo off
REM ============================================
REM J.A. Uniforms - Windows Service Setup
REM ============================================
REM 
REM This script sets up the J.A. Uniforms application
REM as a Windows service using NSSM (Non-Sucking Service Manager)
REM 
REM Prerequisites:
REM 1. Download NSSM from https://nssm.cc/
REM 2. Extract nssm.exe to C:\nssm or add to PATH
REM 3. Run this script as Administrator
REM 
REM ============================================

echo ============================================
echo J.A. Uniforms - Windows Service Setup
echo ============================================
echo.

REM Configuration - MODIFY THESE PATHS
set APP_DIR=C:\ja_uniforms_pricing
set VENV_DIR=%APP_DIR%\.venv
set NSSM_PATH=C:\nssm\nssm.exe
set SERVICE_NAME=JA_Uniforms

REM Check if running as Administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator!
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

REM Check if NSSM exists
if not exist "%NSSM_PATH%" (
    echo ERROR: NSSM not found at %NSSM_PATH%
    echo Download from https://nssm.cc/
    pause
    exit /b 1
)

REM Check if app directory exists
if not exist "%APP_DIR%\app.py" (
    echo ERROR: Application not found at %APP_DIR%
    echo Please update APP_DIR in this script
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo ERROR: Virtual environment not found at %VENV_DIR%
    echo Please create it with: python -m venv .venv
    pause
    exit /b 1
)

echo.
echo Installing service: %SERVICE_NAME%
echo Application: %APP_DIR%
echo Virtual Environment: %VENV_DIR%
echo.

REM Stop existing service if running
echo Stopping existing service (if any)...
%NSSM_PATH% stop %SERVICE_NAME% >nul 2>&1

REM Remove existing service
echo Removing existing service (if any)...
%NSSM_PATH% remove %SERVICE_NAME% confirm >nul 2>&1

REM Install new service
echo Installing new service...
%NSSM_PATH% install %SERVICE_NAME% "%VENV_DIR%\Scripts\python.exe"

REM Configure service parameters
echo Configuring service...

REM Application directory
%NSSM_PATH% set %SERVICE_NAME% AppDirectory "%APP_DIR%"

REM Command line arguments (use gunicorn)
%NSSM_PATH% set %SERVICE_NAME% AppParameters "-m gunicorn -c gunicorn.conf.py app:app"

REM Environment variables
%NSSM_PATH% set %SERVICE_NAME% AppEnvironmentExtra "FLASK_ENV=production" "FLASK_DEBUG=False"

REM Output logs
%NSSM_PATH% set %SERVICE_NAME% AppStdout "%APP_DIR%\logs\service_stdout.log"
%NSSM_PATH% set %SERVICE_NAME% AppStderr "%APP_DIR%\logs\service_stderr.log"

REM Auto-restart on failure
%NSSM_PATH% set %SERVICE_NAME% AppRestartDelay 5000
%NSSM_PATH% set %SERVICE_NAME% AppThrottle 5000

REM Service description
%NSSM_PATH% set %SERVICE_NAME% Description "J.A. Uniforms Pricing Tool - Web Application"
%NSSM_PATH% set %SERVICE_NAME% DisplayName "J.A. Uniforms Pricing Tool"

REM Start type (Automatic)
%NSSM_PATH% set %SERVICE_NAME% Start SERVICE_AUTO_START

REM Create logs directory if needed
if not exist "%APP_DIR%\logs" mkdir "%APP_DIR%\logs"

echo.
echo Service installed successfully!
echo.

REM Start the service
echo Starting service...
%NSSM_PATH% start %SERVICE_NAME%

REM Check status
echo.
echo Service Status:
%NSSM_PATH% status %SERVICE_NAME%

echo.
echo ============================================
echo Setup Complete!
echo ============================================
echo.
echo Service Name: %SERVICE_NAME%
echo Access URL: http://localhost:5000
echo.
echo To manage the service:
echo   Start:   nssm start %SERVICE_NAME%
echo   Stop:    nssm stop %SERVICE_NAME%
echo   Restart: nssm restart %SERVICE_NAME%
echo   Status:  nssm status %SERVICE_NAME%
echo   Remove:  nssm remove %SERVICE_NAME%
echo.
echo Logs are saved to: %APP_DIR%\logs\
echo.

pause
