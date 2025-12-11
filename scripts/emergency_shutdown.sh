#!/bin/bash

# Emergency Shutdown Script for VoiceAlert System
# This script performs emergency shutdown of critical systems

set -euo pipefail

# Configuration
LOG_FILE="/tmp/voicealert_emergency_$(date +%Y%m%d_%H%M%S).log"
SHUTDOWN_DELAY=60  # 60 seconds delay for graceful shutdown

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Main emergency shutdown function
main() {
    log "EMERGENCY SHUTDOWN INITIATED for CVE: ${CVE_ID:-Unknown}"
    log "This is a CRITICAL security response action"
    
    # Step 1: Notify all logged-in users
    log "Notifying all users of emergency shutdown..."
    wall "EMERGENCY SECURITY SHUTDOWN - System will halt in $SHUTDOWN_DELAY seconds due to critical security vulnerability ${CVE_ID:-Unknown}" || true
    
    # Step 2: Gracefully stop critical services
    log "Gracefully stopping critical services..."
    critical_services=("apache2" "nginx" "mysql" "postgresql" "redis" "docker")
    
    for service in "${critical_services[@]}"; do
        if systemctl is-active --quiet "$service" 2>/dev/null; then
            log "Stopping service: $service"
            sudo systemctl stop "$service" || log "WARNING: Failed to stop $service"
        fi
    done
    
    # Step 3: Sync filesystem
    log "Syncing filesystems..."
    sync
    
    # Step 4: Create emergency log
    {
        echo "Emergency Shutdown Report - $(date)"
        echo "CVE: ${CVE_ID:-Unknown}"
        echo "Reason: Critical security vulnerability"
        echo "Initiated by: VoiceAlert System"
        echo "Log file: $LOG_FILE"
    } > "/tmp/emergency_shutdown_$(date +%Y%m%d_%H%M%S).log"
    
    # Step 5: Countdown and shutdown
    log "System will shutdown in $SHUTDOWN_DELAY seconds..."
    log "Press Ctrl+C within $SHUTDOWN_DELAY seconds to abort"
    
    # Countdown
    for ((i=SHUTDOWN_DELAY; i>0; i--)); do
        if ((i % 10 == 0)) || ((i <= 10)); then
            log "Shutdown in $i seconds..."
        fi
        sleep 1
    done
    
    log "Initiating emergency shutdown NOW"
    sudo shutdown -h now "Emergency shutdown due to security vulnerability ${CVE_ID:-Unknown}"
}

# Run main function
main "$@"