#!/bin/bash

# Automated Patching Script for VoiceAlert System
# This script handles emergency patching for critical vulnerabilities

set -euo pipefail

# Configuration
LOG_FILE="/tmp/voicealert_patching_$(date +%Y%m%d_%H%M%S).log"
BACKUP_DIR="/tmp/voicealert_backups"
PATCH_STATUS_FILE="/tmp/voicealert_patch_status"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    echo "FAILED" > "$PATCH_STATUS_FILE"
    exit 1
}

# Cleanup function
cleanup() {
    log "Cleanup completed"
}
trap cleanup EXIT

# Main patching function
main() {
    log "Starting emergency patching process for CVE: ${CVE_ID:-Unknown}"
    
    # Create necessary directories
    mkdir -p "$BACKUP_DIR"
    
    # Set initial status
    echo "IN_PROGRESS" > "$PATCH_STATUS_FILE"
    
    # Step 1: System assessment
    log "Performing system assessment..."
    if ! command -v apt-get &> /dev/null && ! command -v yum &> /dev/null && ! command -v pacman &> /dev/null; then
        error_exit "No supported package manager found"
    fi
    
    # Step 2: Create system backup
    log "Creating system backup..."
    if command -v dpkg &> /dev/null; then
        dpkg --get-selections > "$BACKUP_DIR/package_list_$(date +%Y%m%d_%H%M%S).txt" || true
    fi
    
    # Step 3: Update package lists
    log "Updating package lists..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update -qq || log "WARNING: Failed to update apt package list"
    elif command -v yum &> /dev/null; then
        sudo yum check-update -q || log "WARNING: Failed to update yum package list"
    fi
    
    # Step 4: Apply security updates
    log "Applying security updates..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get upgrade -y -qq || error_exit "Failed to apply apt security updates"
    elif command -v yum &> /dev/null; then
        sudo yum update -y -q || error_exit "Failed to apply yum security updates"
    fi
    
    # Step 5: Restart critical services
    log "Restarting critical services..."
    services=("ssh" "apache2" "nginx" "mysql" "postgresql")
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service" 2>/dev/null; then
            log "Restarting $service..."
            sudo systemctl restart "$service" || log "WARNING: Failed to restart $service"
        fi
    done
    
    # Step 6: Verify system status
    log "Verifying system status..."
    if ! ping -c 1 8.8.8.8 &> /dev/null; then
        log "WARNING: Network connectivity check failed"
    fi
    
    # Step 7: Generate patch report
    log "Generating patch report..."
    {
        echo "Patch Report - $(date)"
        echo "CVE: ${CVE_ID:-Unknown}"
        echo "Status: SUCCESS"
        echo "Log file: $LOG_FILE"
        echo "Backup location: $BACKUP_DIR"
    } > "$BACKUP_DIR/patch_report_$(date +%Y%m%d_%H%M%S).txt"
    
    # Set success status
    echo "COMPLETED" > "$PATCH_STATUS_FILE"
    log "Emergency patching completed successfully"
}

# Run main function
main "$@"