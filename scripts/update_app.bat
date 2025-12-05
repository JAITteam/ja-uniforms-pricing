@echo off
echo ========================================
echo   J.A. UNIFORMS - UPDATE APPLICATION
echo ========================================
echo.

cd /d C:\ja-uniforms

echo [1/4] Stopping server...
taskkill /f /im python.exe 2>nul
taskkill /f /im waitress-serve.exe 2>nul
timeout /t 2 >nul

echo.
echo [2/4] Pulling latest code from GitHub...
git pull origin main

echo.
echo [3/4] Activating virtual environment...
call venv\Scripts\activate

echo.
echo [4/4] Installing/updating dependencies...
pip install -r requirements.txt --quiet

echo.
echo ========================================
echo   UPDATE COMPLETE!
echo ========================================
echo.
echo   Next steps:
echo   1. Restart your computer, OR
echo   2. Double-click start_server.bat
echo.
echo ========================================
pause
