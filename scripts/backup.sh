#!/bin/bash

# Rental Management System Database Backup Script
set -e

# Configuration
DB_HOST="postgres"
DB_PORT="5432"
DB_NAME="rental_management"
DB_USER="rental_user"
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="rental_management_backup_${DATE}.sql"
RETENTION_DAYS=30

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to create database backup
create_backup() {
    log "Starting database backup..."
    
    pg_dump \
        --host="${DB_HOST}" \
        --port="${DB_PORT}" \
        --username="${DB_USER}" \
        --dbname="${DB_NAME}" \
        --verbose \
        --clean \
        --if-exists \
        --create \
        --format=custom \
        --file="${BACKUP_DIR}/${BACKUP_FILE}"
    
    if [ $? -eq 0 ]; then
        log "Database backup completed successfully: ${BACKUP_FILE}"
        
        # Compress the backup
        gzip "${BACKUP_DIR}/${BACKUP_FILE}"
        log "Backup compressed: ${BACKUP_FILE}.gz"
        
        # Create a latest symlink
        ln -sf "${BACKUP_FILE}.gz" "${BACKUP_DIR}/latest.sql.gz"
        log "Latest backup symlink updated"
        
    else
        log "ERROR: Database backup failed!"
        exit 1
    fi
}

# Function to cleanup old backups
cleanup_old_backups() {
    log "Cleaning up backups older than ${RETENTION_DAYS} days..."
    
    find "${BACKUP_DIR}" -name "rental_management_backup_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
    
    if [ $? -eq 0 ]; then
        log "Old backups cleaned up successfully"
    else
        log "WARNING: Failed to cleanup old backups"
    fi
}

# Function to verify backup integrity
verify_backup() {
    local backup_file="${BACKUP_DIR}/${BACKUP_FILE}.gz"
    
    log "Verifying backup integrity..."
    
    # Check if file exists and is not empty
    if [ -s "${backup_file}" ]; then
        # Test gzip integrity
        gzip -t "${backup_file}"
        if [ $? -eq 0 ]; then
            log "Backup integrity verification passed"
            return 0
        else
            log "ERROR: Backup file is corrupted!"
            return 1
        fi
    else
        log "ERROR: Backup file is missing or empty!"
        return 1
    fi
}

# Function to send backup notification
send_notification() {
    local status=$1
    local message=$2
    
    # This could be extended to send emails, Slack notifications, etc.
    log "NOTIFICATION [${status}]: ${message}"
    
    # Example: Send to webhook (uncomment and configure)
    # curl -X POST "https://hooks.slack.com/services/YOUR/WEBHOOK/URL" \
    #      -H "Content-Type: application/json" \
    #      -d "{\"text\":\"Database Backup ${status}: ${message}\"}"
}

# Main execution
main() {
    log "=== Starting Rental Management System Database Backup ==="
    
    # Check if PostgreSQL is available
    until pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}"; do
        log "Waiting for PostgreSQL to be ready..."
        sleep 5
    done
    
    # Create backup
    create_backup
    
    # Verify backup
    if verify_backup; then
        send_notification "SUCCESS" "Database backup completed successfully: ${BACKUP_FILE}.gz"
    else
        send_notification "FAILED" "Database backup verification failed: ${BACKUP_FILE}.gz"
        exit 1
    fi
    
    # Cleanup old backups
    cleanup_old_backups
    
    # Display backup information
    log "=== Backup Information ==="
    log "Backup file: ${BACKUP_FILE}.gz"
    log "Backup size: $(du -h "${BACKUP_DIR}/${BACKUP_FILE}.gz" | cut -f1)"
    log "Total backups: $(ls -1 "${BACKUP_DIR}"/rental_management_backup_*.sql.gz | wc -l)"
    log "Disk usage: $(df -h "${BACKUP_DIR}" | tail -1 | awk '{print $3 "/" $2 " (" $5 ")"}')"
    
    log "=== Database Backup Process Completed ==="
}

# Error handling
trap 'log "ERROR: Backup script failed on line $LINENO"' ERR

# Run main function
main "$@"