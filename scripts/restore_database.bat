@echo off
setlocal

:: ========================================
:: J.A. UNIFORMS - DATABASE RESTORE SCRIPT
:: ========================================

set BACKUP_DIR=C:\ja-uniforms\backup
set PG_PATH=C:\Program Files\PostgreSQL\16\bin
set DB_NAME=ja_uniforms
set DB_USER=postgres

echo ========================================
echo   J.A. UNIFORMS - DATABASE RESTORE
echo ========================================
echo.
echo Available backups:
echo.
dir /b "%BACKUP_DIR%\*.backup" 2>nul
echo.

set /p BACKUP_FILE="Enter backup filename (e.g., ja_uniforms_2024-12-05_17-30.backup): "

if not exist "%BACKUP_DIR%\%BACKUP_FILE%" (
    echo.
    echo [ERROR] Backup file not found!
    pause
    exit /b 1
)

echo.
echo WARNING: This will OVERWRITE the current database!
set /p CONFIRM="Are you sure? (yes/no): "

if /i not "%CONFIRM%"=="yes" (
    echo Restore cancelled.
    pause
    exit /b 0
)

echo.
echo [1/3] Dropping existing database...
"%PG_PATH%\psql.exe" -U %DB_USER% -c "DROP DATABASE IF EXISTS %DB_NAME%;"

echo [2/3] Creating fresh database...
"%PG_PATH%\psql.exe" -U %DB_USER% -c "CREATE DATABASE %DB_NAME%;"

echo [3/3] Restoring from backup...
"%PG_PATH%\pg_restore.exe" -U %DB_USER% -d %DB_NAME% "%BACKUP_DIR%\%BACKUP_FILE%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Database restored successfully!
) else (
    echo.
    echo [WARNING] Restore completed with some warnings (usually OK).
)

echo.
pause
