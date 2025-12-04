#!/usr/bin/env python3
"""
Database Backup Script for J.A. Uniforms
=========================================

Creates automated PostgreSQL database backups with compression
and automatic cleanup of old backups.

Usage:
    python scripts/backup_database.py
    
Schedule with cron (Linux):
    0 2 * * * /path/to/.venv/bin/python /path/to/scripts/backup_database.py

Schedule with Task Scheduler (Windows):
    Create a task that runs daily at 2:00 AM
    
Author: J.A. IT Team
"""

import os
import sys
import subprocess
import shutil
import gzip
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# ============================================
# CONFIGURATION
# ============================================

# Backup directory (change this to your preferred location)
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/var/backups/ja_uniforms/database")

# For Windows, use something like:
# BACKUP_DIR = "C:\\Backups\\ja_uniforms\\database"

# PostgreSQL connection settings
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "ja_uniforms")
DB_USER = os.environ.get("DB_USER", "ja_uniforms_user")

# Retention settings
KEEP_DAYS = int(os.environ.get("BACKUP_KEEP_DAYS", 30))  # Keep backups for 30 days
KEEP_WEEKLY = int(os.environ.get("BACKUP_KEEP_WEEKLY", 12))  # Keep 12 weekly backups
KEEP_MONTHLY = int(os.environ.get("BACKUP_KEEP_MONTHLY", 12))  # Keep 12 monthly backups

# Log file
LOG_FILE = os.environ.get("BACKUP_LOG", "logs/backup.log")

# ============================================
# HELPER FUNCTIONS
# ============================================

def log_message(message, level="INFO"):
    """Log message to file and console."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    print(log_entry)
    
    # Also write to log file
    try:
        log_dir = os.path.dirname(LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
    except Exception as e:
        print(f"Warning: Could not write to log file: {e}")


def get_backup_filename():
    """Generate backup filename with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"ja_uniforms_{timestamp}.sql"


def create_backup():
    """Create PostgreSQL backup."""
    # Ensure backup directory exists
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # Generate filenames
    sql_filename = get_backup_filename()
    sql_path = os.path.join(BACKUP_DIR, sql_filename)
    gz_path = sql_path + ".gz"
    
    log_message(f"Starting backup: {sql_filename}")
    
    # Build pg_dump command
    pg_dump_cmd = [
        "pg_dump",
        "-h", DB_HOST,
        "-p", DB_PORT,
        "-U", DB_USER,
        "-d", DB_NAME,
        "-F", "p",  # Plain text format
        "-f", sql_path,
        "--clean",  # Include DROP statements
        "--if-exists",  # Add IF EXISTS to DROP statements
    ]
    
    try:
        # Run pg_dump
        result = subprocess.run(
            pg_dump_cmd,
            capture_output=True,
            text=True,
            env={**os.environ, "PGPASSWORD": os.environ.get("DB_PASSWORD", "")}
        )
        
        if result.returncode != 0:
            log_message(f"pg_dump error: {result.stderr}", "ERROR")
            return None
        
        # Compress the backup
        log_message("Compressing backup...")
        with open(sql_path, 'rb') as f_in:
            with gzip.open(gz_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove uncompressed file
        os.remove(sql_path)
        
        # Get file size
        file_size = os.path.getsize(gz_path) / (1024 * 1024)  # MB
        
        log_message(f"Backup created: {gz_path} ({file_size:.2f} MB)")
        return gz_path
        
    except FileNotFoundError:
        log_message("pg_dump not found. Is PostgreSQL client installed?", "ERROR")
        return None
    except Exception as e:
        log_message(f"Backup error: {str(e)}", "ERROR")
        return None


def cleanup_old_backups():
    """Remove old backups based on retention policy."""
    log_message("Cleaning up old backups...")
    
    if not os.path.exists(BACKUP_DIR):
        return
    
    now = datetime.now()
    daily_cutoff = now - timedelta(days=KEEP_DAYS)
    
    removed_count = 0
    kept_count = 0
    
    for filename in os.listdir(BACKUP_DIR):
        if not filename.endswith('.sql.gz'):
            continue
        
        filepath = os.path.join(BACKUP_DIR, filename)
        file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
        
        # Keep if within daily retention
        if file_mtime > daily_cutoff:
            kept_count += 1
            continue
        
        # For older backups, check weekly/monthly retention
        # Keep weekly backups (Sunday) for KEEP_WEEKLY weeks
        if file_mtime.weekday() == 6:  # Sunday
            weekly_cutoff = now - timedelta(weeks=KEEP_WEEKLY)
            if file_mtime > weekly_cutoff:
                kept_count += 1
                continue
        
        # Keep monthly backups (1st of month) for KEEP_MONTHLY months
        if file_mtime.day == 1:
            monthly_cutoff = now - timedelta(days=KEEP_MONTHLY * 30)
            if file_mtime > monthly_cutoff:
                kept_count += 1
                continue
        
        # Remove old backup
        try:
            os.remove(filepath)
            log_message(f"Removed old backup: {filename}")
            removed_count += 1
        except Exception as e:
            log_message(f"Error removing {filename}: {e}", "ERROR")
    
    log_message(f"Cleanup complete: {removed_count} removed, {kept_count} kept")


def verify_backup(backup_path):
    """Verify backup file is valid."""
    if not backup_path or not os.path.exists(backup_path):
        return False
    
    # Check file size (should be > 1KB for non-empty database)
    file_size = os.path.getsize(backup_path)
    if file_size < 1024:
        log_message("Warning: Backup file is suspiciously small", "WARNING")
        return False
    
    # Try to read gzip header
    try:
        with gzip.open(backup_path, 'rt') as f:
            header = f.read(100)
            if '--' in header or 'PostgreSQL' in header:
                return True
    except Exception as e:
        log_message(f"Backup verification failed: {e}", "ERROR")
        return False
    
    return True


def main():
    """Main backup function."""
    log_message("="*60)
    log_message("J.A. UNIFORMS - DATABASE BACKUP")
    log_message("="*60)
    
    # Create backup
    backup_path = create_backup()
    
    if backup_path:
        # Verify backup
        if verify_backup(backup_path):
            log_message("Backup verification: PASSED")
        else:
            log_message("Backup verification: FAILED", "WARNING")
        
        # Cleanup old backups
        cleanup_old_backups()
        
        log_message("Backup completed successfully!")
        return 0
    else:
        log_message("Backup failed!", "ERROR")
        return 1


if __name__ == "__main__":
    exit(main())
