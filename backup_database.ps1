# PostgreSQL + Images Backup Script for J.A. Uniforms
# With backup verification

$env:PGPASSWORD = "Support1!"
$date = Get-Date -Format "yyyy-MM-dd_HHmm"
$backupDir = "C:\Users\it2\ja_uniforms_pricing\backups"
$dbBackupFile = "$backupDir\ja_uniforms_$date.backup"
$imgBackupFile = "$backupDir\images_$date.zip"
$logFile = "$backupDir\backup_log.txt"

# Ensure backup directory exists
if (!(Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir | Out-Null
}

Write-Host "Starting backup process..." -ForegroundColor Cyan

# ===== DATABASE BACKUP =====
Write-Host "Backing up database..." -ForegroundColor Yellow
$dbStartTime = Get-Date
& "C:\Program Files\PostgreSQL\16\bin\pg_dump.exe" -U postgres -d ja_uniforms -F c -f $dbBackupFile 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Database backup failed!" -ForegroundColor Red
    Add-Content $logFile "$(Get-Date): FAILED - Database backup error"
    exit 1
}

# Verify database backup file exists and has content
if (!(Test-Path $dbBackupFile)) {
    Write-Host "ERROR: Database backup file not created!" -ForegroundColor Red
    Add-Content $logFile "$(Get-Date): FAILED - Backup file not found"
    exit 1
}

$dbFileSize = (Get-Item $dbBackupFile).Length
if ($dbFileSize -lt 1000) {
    Write-Host "ERROR: Database backup file too small ($dbFileSize bytes) - likely corrupted!" -ForegroundColor Red
    Add-Content $logFile "$(Get-Date): FAILED - Backup file too small: $dbFileSize bytes"
    exit 1
}

# Verify backup is restorable by listing its contents
Write-Host "Verifying database backup integrity..." -ForegroundColor Yellow
$verifyOutput = & "C:\Program Files\PostgreSQL\16\bin\pg_restore.exe" -U postgres -l $dbBackupFile 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Database backup verification failed - file may be corrupted!" -ForegroundColor Red
    Add-Content $logFile "$(Get-Date): FAILED - Backup verification failed"
    exit 1
}

# Count tables in backup
$tableCount = ($verifyOutput | Select-String -Pattern "TABLE").Count
Write-Host "  Database backup verified: $tableCount tables, $([math]::Round($dbFileSize/1KB, 2)) KB" -ForegroundColor Green

# ===== IMAGES BACKUP =====
Write-Host "Backing up images..." -ForegroundColor Yellow
$imgSourcePath = "C:\Users\it2\ja_uniforms_pricing\static\img"

if (Test-Path $imgSourcePath) {
    $imageFiles = Get-ChildItem $imgSourcePath -Recurse -File
    if ($imageFiles.Count -gt 0) {
        Compress-Archive -Path "$imgSourcePath\*" -DestinationPath $imgBackupFile -Force
        
        # Verify zip file
        if (Test-Path $imgBackupFile) {
            $imgFileSize = (Get-Item $imgBackupFile).Length
            
            # Test zip integrity by listing contents
            try {
                $zipTest = [System.IO.Compression.ZipFile]::OpenRead($imgBackupFile)
                $zipEntryCount = $zipTest.Entries.Count
                $zipTest.Dispose()
                Write-Host "  Images backup verified: $zipEntryCount files, $([math]::Round($imgFileSize/1KB, 2)) KB" -ForegroundColor Green
            } catch {
                Write-Host "WARNING: Images backup may be corrupted!" -ForegroundColor Red
                Add-Content $logFile "$(Get-Date): WARNING - Images zip verification failed"
            }
        }
    } else {
        Write-Host "  No images to backup" -ForegroundColor Gray
    }
} else {
    Write-Host "  Images folder not found - skipping" -ForegroundColor Gray
}

# ===== CLEANUP OLD BACKUPS =====
Write-Host "Cleaning up old backups..." -ForegroundColor Yellow
$deletedDb = Get-ChildItem $backupDir -Filter "*.backup" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-14) }
$deletedImg = Get-ChildItem $backupDir -Filter "*.zip" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-14) }

$deletedDb | Remove-Item -ErrorAction SilentlyContinue
$deletedImg | Remove-Item -ErrorAction SilentlyContinue

if ($deletedDb.Count -gt 0 -or $deletedImg.Count -gt 0) {
    Write-Host "  Removed $($deletedDb.Count) old database backups, $($deletedImg.Count) old image backups" -ForegroundColor Gray
}

# ===== LOG SUCCESS =====
$duration = (Get-Date) - $dbStartTime
Add-Content $logFile "$(Get-Date): SUCCESS - DB: $dbBackupFile ($([math]::Round($dbFileSize/1KB, 2)) KB, $tableCount tables) - Duration: $([math]::Round($duration.TotalSeconds, 1))s"

if (Test-Path $imgBackupFile) {
    Add-Content $logFile "$(Get-Date): SUCCESS - Images: $imgBackupFile ($([math]::Round($imgFileSize/1KB, 2)) KB)"
}

# ===== SUMMARY =====
Write-Host ""
Write-Host "===== BACKUP COMPLETE =====" -ForegroundColor Green
Write-Host "  Database: $dbBackupFile" -ForegroundColor White
Write-Host "  Size: $([math]::Round($dbFileSize/1KB, 2)) KB ($tableCount tables verified)" -ForegroundColor White
if (Test-Path $imgBackupFile) {
    Write-Host "  Images: $imgBackupFile" -ForegroundColor White
}
Write-Host "  Duration: $([math]::Round($duration.TotalSeconds, 1)) seconds" -ForegroundColor White
Write-Host "===========================" -ForegroundColor Green