@echo off
title J.A. Uniforms Pricing Server
cd /d C:\ja-uniforms
call venv\Scripts\activate

echo.
echo ========================================
echo   J.A. UNIFORMS PRICING SERVER
echo   Running on: http://192.168.1.140:5000
echo ========================================
echo.
echo Server starting... (Do not close this window)
echo Press Ctrl+C to stop the server
echo.

waitress-serve --host=0.0.0.0 --port=5000 app:app

pause
