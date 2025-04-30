#!/bin/bash
set -eo pipefail

LOG_FILE="/app/logs/backup.log"
BACKUP_DIR="/app/backups/$(date +\%Y-\%m-\%d)"
SOURCE_DB="/app/manager/data/db.sqlite3"

{
    echo "Starting backup at $(date)"
    mkdir -p "$BACKUP_DIR"
    cp -v "$SOURCE_DB" "$BACKUP_DIR/db.sqlite3_$(date +\%H-\%M-\%S)"
    echo "Backup completed successfully at $(date)"
    
    # Cleanup old backups (older than 10 days)
    find /app/backups/* -type d -ctime +10 -exec rm -rf {} \; || echo "No old backups to remove"
    
} >> "$LOG_FILE" 2>&1
