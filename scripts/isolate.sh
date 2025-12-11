#!/bin/bash

# Server Isolation Script for VoiceAlert System
# This script quarantines potentially compromised systems

set -euo pipefail

# Configuration
LOG_FILE="/tmp/voicealert_isolation_$(date +%Y%m%d_%H%M%S).log"
ISOLATION_STATUS_FILE="/tmp/voicealert_isolation_status"
IPTABLES_BACKUP="/tmp/iptables_backup_$(date +%Y%m%d_%H%M%S)"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    echo "FAILED" > "$ISOLATION_STATUS_FILE"
    exit 1
}

# Cleanup function
cleanup() {
    log "Isolation script cleanup completed"
}
trap cleanup EXIT

# Main isolation function
main() {
    log "Starting server isolation process for CVE: ${CVE_ID:-Unknown}"
    
    # Set initial status
    echo "IN_PROGRESS" > "$ISOLATION_STATUS_FILE"
    
    # Step 1: Backup current iptables rules
    log "Backing up current iptables rules..."
    if command -v iptables &> /dev/null; then
        sudo iptables-save > "$IPTABLES_BACKUP" || error_exit "Failed to backup iptables rules"
        log "Iptables backup saved to: $IPTABLES_BACKUP"
    fi
    
    # Step 2: Block all incoming connections except SSH and management
    log "Implementing network isolation rules..."
    if command -v iptables &> /dev/null; then
        # Allow loopback
        sudo iptables -A INPUT -i lo -j ACCEPT || true
        
        # Allow established connections
        sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT || true
        
        # Allow SSH (port 22) for management access
        sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT || true
        
        # Allow management IPs (customize as needed)
        # sudo iptables -A INPUT -s 10.0.0.0/8 -j ACCEPT || true
        
        # Block all other incoming traffic
        sudo iptables -A INPUT -j DROP || error_exit "Failed to apply isolation rules"
        
        log "Network isolation rules applied"
    else
        log "WARNING: iptables not available, skipping network isolation"
    fi
    
    # Step 3: Stop non-essential services
    log "Stopping non-essential services..."
    non_essential_services=("apache2" "nginx" "mysql" "postgresql" "redis" "memcached")
    
    for service in "${non_essential_services[@]}"; do
        if systemctl is-active --quiet "$service" 2>/dev/null; then
            log "Stopping service: $service"
            sudo systemctl stop "$service" || log "WARNING: Failed to stop $service"
        fi
    done
    
    # Step 4: Disable non-essential services
    log "Disabling non-essential services..."
    for service in "${non_essential_services[@]}"; do
        if systemctl is-enabled --quiet "$service" 2>/dev/null; then
            log "Disabling service: $service"
            sudo systemctl disable "$service" || log "WARNING: Failed to disable $service"
        fi
    done
    
    # Step 5: Kill suspicious processes
    log "Checking for suspicious processes..."
    # This is a basic example - customize based on specific threats
    suspicious_processes=("nc" "netcat" "wget" "curl")
    
    for proc in "${suspicious_processes[@]}"; do
        if pgrep "$proc" > /dev/null; then
            log "WARNING: Found suspicious process: $proc"
            # Uncomment to kill processes:
            # sudo pkill "$proc" && log "Killed process: $proc"
        fi
    done
    
    # Step 6: Monitor active connections
    log "Logging active network connections..."
    if command -v netstat &> /dev/null; then
        netstat -tuln > "/tmp/active_connections_$(date +%Y%m%d_%H%M%S).log" || true
    fi
    
    # Step 7: Create isolation report
    log "Generating isolation report..."
    {
        echo "Isolation Report - $(date)"
        echo "CVE: ${CVE_ID:-Unknown}"
        echo "Status: ISOLATED"
        echo "Log file: $LOG_FILE"
        echo "Iptables backup: $IPTABLES_BACKUP"
        echo "Restore command: sudo iptables-restore < $IPTABLES_BACKUP"
        echo ""
        echo "Services stopped:"
        for service in "${non_essential_services[@]}"; do
            if ! systemctl is-active --quiet "$service" 2>/dev/null; then
                echo "  - $service"
            fi
        done
    } > "/tmp/isolation_report_$(date +%Y%m%d_%H%M%S).txt"
    
    # Step 8: Set completion status
    echo "COMPLETED" > "$ISOLATION_STATUS_FILE"
    log "Server isolation completed successfully"
    
    # Display restoration instructions
    log "To restore normal operations:"
    log "1. sudo iptables-restore < $IPTABLES_BACKUP"
    log "2. sudo systemctl start <service_name> for each stopped service"
    log "3. sudo systemctl enable <service_name> for each disabled service"
}

# Run main function
main "$@"