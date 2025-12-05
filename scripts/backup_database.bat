@echo off
setlocal EnableDelayedExpansion

:: ========================================
:: J.A. UNIFORMS - DATABASE BACKUP SCRIPT
:: ========================================

:: Configuration
set BACKUP_DIR=C:\ja-uniforms\backup
set PG_PATH=C:\Program Files\PostgreSQL\16\bin
set DB_NAME=ja_uniforms
set DB_USER=postgres

:: Create timestamp
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set TIMESTAMP=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%_%datetime:~8,2%-%datetime:~10,2%
set FILENAME=ja_uniforms_%TIMESTAMP%.backup

:: Create backup directory if it doesn't exist
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

:: Create backup
echo ========================================
echo   J.A. UNIFORMS - DATABASE BACKUP
echo ========================================
echo.
echo Creating backup: %FILENAME%
echo.

"%PG_PATH%\pg_dump.exe" -U %DB_USER% -F c -d %DB_NAME% -f "%BACKUP_DIR%\%FILENAME%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Backup created successfully!
    echo Location: %BACKUP_DIR%\%FILENAME%
) else (
    echo.
    echo [ERROR] Backup failed! Check PostgreSQL is running.
)

:: Delete backups older than 7 days
echo.
echo Cleaning old backups (older than 7 days)...
forfiles /p "%BACKUP_DIR%" /m *.backup /d -7 /c "cmd /c del @path" 2>nul

echo.
echo ========================================
echo   BACKUP COMPLETE
echo ========================================

:: If running interactively, pause
if "%1"=="" pause
