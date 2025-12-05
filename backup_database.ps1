# PostgreSQL + Images Backup Script for J.A. Uniforms

$env:PGPASSWORD = "Support1!"
$date = Get-Date -Format "yyyy-MM-dd_HHmm"
$backupDir = "C:\Users\it2\ja_uniforms_pricing\backups"
$dbBackupFile = "$backupDir\ja_uniforms_$date.backup"
$imgBackupFile = "$backupDir\images_$date.zip"

# Backup database
& "C:\Program Files\PostgreSQL\16\bin\pg_dump.exe" -U postgres -d ja_uniforms -F c -f $dbBackupFile

# Backup images folder
Compress-Archive -Path "C:\Users\it2\ja_uniforms_pricing\static\img\*" -DestinationPath $imgBackupFile -Force

# Delete backups older than 14 days
Get-ChildItem $backupDir -Filter "*.backup" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-14) } | Remove-Item
Get-ChildItem $backupDir -Filter "*.zip" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-14) } | Remove-Item

# Log result
$logFile = "$backupDir\backup_log.txt"
Add-Content $logFile "$(Get-Date): DB backup - $dbBackupFile"
Add-Content $logFile "$(Get-Date): Images backup - $imgBackupFile"

Write-Host "Backup complete!"
Write-Host "  Database: $dbBackupFile"
Write-Host "  Images: $imgBackupFile"