#!/bin/bash
set -eo pipefail

LOG_FILE="/app/logs/backup.log"
BACKUP_DIR="/app/backups/$(date +\%Y-\%m-\%d)"
SOURCE_DB="/app/manager/data/db.sqlite3"
LOCK_FILE="/app/backups/backup.lock"

{
    echo "Starting backup at $(date)"
    mkdir -p "$BACKUP_DIR"
    
    # Use file locking and SQLite backup command
    (
        flock -x -w 300 200 || exit 1
        echo "Lock acquired, starting database backup..."
        sqlite3 "$SOURCE_DB" "PRAGMA wal_checkpoint;"
        sqlite3 "$SOURCE_DB" ".backup '$BACKUP_DIR/db.sqlite3_$(date +\%H-\%M-\%S)'"
        chmod 644 "$BACKUP_DIR"/*
        echo "Backup completed successfully at $(date)"
        
        # Cleanup old backups (older than 10 days)
        find /app/backups/* -type d -ctime +10 -exec rm -rf {} \; || echo "No old backups to remove"
        
    ) 200>"$LOCK_FILE"
    
} >> "$LOG_FILE" 2>&1
