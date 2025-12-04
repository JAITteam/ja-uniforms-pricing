#!/usr/bin/env python3
"""
File Backup Script for J.A. Uniforms
====================================

Backs up uploaded images and static files with compression.

Usage:
    python scripts/backup_files.py
    
Schedule with cron (Linux) - weekly:
    0 3 * * 0 /path/to/.venv/bin/python /path/to/scripts/backup_files.py
    
Author: J.A. IT Team
"""

import os
import sys
import shutil
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# ============================================
# CONFIGURATION
# ============================================

# Application directory
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Backup directory
BACKUP_DIR = os.environ.get("FILE_BACKUP_DIR", "/var/backups/ja_uniforms/files")

# Folders to backup (relative to APP_DIR)
FOLDERS_TO_BACKUP = [
    "static/img",
    "uploads",
    "logs"
]

# Files to backup
FILES_TO_BACKUP = [
    ".env",
    ".env.production"
]

# Retention settings
KEEP_BACKUPS = int(os.environ.get("FILE_BACKUP_KEEP", 10))  # Keep 10 most recent

# Log file
LOG_FILE = os.environ.get("BACKUP_LOG", "logs/backup.log")

# ============================================
# HELPER FUNCTIONS
# ============================================

def log_message(message, level="INFO"):
    """Log message to file and console."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] [FILES] {message}"
    print(log_entry)
    
    try:
        log_dir = os.path.dirname(LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
    except Exception as e:
        print(f"Warning: Could not write to log file: {e}")


def get_folder_size(folder_path):
    """Get total size of folder in MB."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size / (1024 * 1024)


def create_backup():
    """Create file backup."""
    # Ensure backup directory exists
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"ja_uniforms_files_{timestamp}"
    zip_path = os.path.join(BACKUP_DIR, f"{backup_name}.zip")
    
    log_message(f"Starting file backup: {backup_name}.zip")
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            files_added = 0
            
            # Backup folders
            for folder in FOLDERS_TO_BACKUP:
                folder_path = os.path.join(APP_DIR, folder)
                
                if not os.path.exists(folder_path):
                    log_message(f"  Skipping (not found): {folder}")
                    continue
                
                folder_size = get_folder_size(folder_path)
                file_count = sum([len(files) for _, _, files in os.walk(folder_path)])
                
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, APP_DIR)
                        
                        try:
                            zipf.write(file_path, arcname)
                            files_added += 1
                        except Exception as e:
                            log_message(f"  Error adding {file}: {e}", "WARNING")
                
                log_message(f"  Backed up: {folder} ({file_count} files, {folder_size:.2f} MB)")
            
            # Backup individual files
            for file in FILES_TO_BACKUP:
                file_path = os.path.join(APP_DIR, file)
                
                if os.path.exists(file_path):
                    zipf.write(file_path, file)
                    files_added += 1
                    log_message(f"  Backed up: {file}")
        
        # Get final zip size
        zip_size = os.path.getsize(zip_path) / (1024 * 1024)
        log_message(f"Backup created: {zip_path} ({zip_size:.2f} MB, {files_added} files)")
        
        return zip_path
        
    except Exception as e:
        log_message(f"Backup error: {str(e)}", "ERROR")
        if os.path.exists(zip_path):
            os.remove(zip_path)
        return None


def cleanup_old_backups():
    """Remove old backups keeping only the most recent."""
    log_message("Cleaning up old file backups...")
    
    if not os.path.exists(BACKUP_DIR):
        return
    
    # Get all backup files
    backups = []
    for filename in os.listdir(BACKUP_DIR):
        if filename.startswith('ja_uniforms_files_') and filename.endswith('.zip'):
            filepath = os.path.join(BACKUP_DIR, filename)
            backups.append((filepath, os.path.getmtime(filepath)))
    
    # Sort by modification time (newest first)
    backups.sort(key=lambda x: x[1], reverse=True)
    
    # Remove old backups
    removed_count = 0
    for filepath, _ in backups[KEEP_BACKUPS:]:
        try:
            os.remove(filepath)
            log_message(f"Removed old backup: {os.path.basename(filepath)}")
            removed_count += 1
        except Exception as e:
            log_message(f"Error removing {filepath}: {e}", "ERROR")
    
    log_message(f"Cleanup complete: {removed_count} removed, {min(len(backups), KEEP_BACKUPS)} kept")


def main():
    """Main backup function."""
    log_message("="*60)
    log_message("J.A. UNIFORMS - FILE BACKUP")
    log_message("="*60)
    
    # Create backup
    backup_path = create_backup()
    
    if backup_path:
        # Cleanup old backups
        cleanup_old_backups()
        
        log_message("File backup completed successfully!")
        return 0
    else:
        log_message("File backup failed!", "ERROR")
        return 1


if __name__ == "__main__":
    exit(main())
