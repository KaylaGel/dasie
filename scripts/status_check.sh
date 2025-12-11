#!/bin/bash

# System Status Check Script for VoiceAlert System
# This script generates a comprehensive system status report

set -euo pipefail

# Configuration
LOG_FILE="/tmp/voicealert_status_$(date +%Y%m%d_%H%M%S).log"
REPORT_FILE="/tmp/system_status_report_$(date +%Y%m%d_%H%M%S).txt"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Report function
report() {
    echo "$*" >> "$REPORT_FILE"
    log "$*"
}

# Main status check function
main() {
    log "Starting system status check for CVE: ${CVE_ID:-Unknown}"
    
    # Initialize report
    {
        echo "========================================="
        echo "VoiceAlert System Status Report"
        echo "Generated: $(date)"
        echo "CVE Context: ${CVE_ID:-Unknown}"
        echo "========================================="
        echo ""
    } > "$REPORT_FILE"
    
    # System Information
    report "=== SYSTEM INFORMATION ==="
    report "Hostname: $(hostname)"
    report "Uptime: $(uptime)"
    report "Load Average: $(cat /proc/loadavg 2>/dev/null || echo 'N/A')"
    report "Kernel: $(uname -r)"
    report ""
    
    # Memory Usage
    report "=== MEMORY USAGE ==="
    if command -v free &> /dev/null; then
        free -h >> "$REPORT_FILE" 2>/dev/null
    else
        report "Memory information not available"
    fi
    report ""
    
    # Disk Usage
    report "=== DISK USAGE ==="
    if command -v df &> /dev/null; then
        df -h >> "$REPORT_FILE" 2>/dev/null
    else
        report "Disk information not available"
    fi
    report ""
    
    # Service Status
    report "=== CRITICAL SERVICES STATUS ==="
    critical_services=("ssh" "sshd" "apache2" "nginx" "mysql" "postgresql" "redis" "docker")
    
    for service in "${critical_services[@]}"; do
        if systemctl list-units --full -all | grep -Fq "$service.service"; then
            status=$(systemctl is-active "$service" 2>/dev/null || echo "inactive")
            enabled=$(systemctl is-enabled "$service" 2>/dev/null || echo "disabled")
            report "$service: $status ($enabled)"
        fi
    done
    report ""
    
    # Network Status
    report "=== NETWORK STATUS ==="
    report "Network Interfaces:"
    if command -v ip &> /dev/null; then
        ip addr show | grep -E '^[0-9]+:|inet ' >> "$REPORT_FILE" 2>/dev/null || true
    else
        ifconfig 2>/dev/null | grep -E '^[a-z]|inet ' >> "$REPORT_FILE" || report "Network info not available"
    fi
    report ""
    
    # Active Connections
    report "=== ACTIVE NETWORK CONNECTIONS ==="
    if command -v netstat &> /dev/null; then
        netstat -tuln | head -20 >> "$REPORT_FILE" 2>/dev/null || true
    elif command -v ss &> /dev/null; then
        ss -tuln | head -20 >> "$REPORT_FILE" 2>/dev/null || true
    else
        report "Network connection info not available"
    fi
    report ""
    
    # Process Information
    report "=== TOP PROCESSES (CPU) ==="
    if command -v ps &> /dev/null; then
        ps aux --sort=-%cpu | head -10 >> "$REPORT_FILE" 2>/dev/null || true
    else
        report "Process information not available"
    fi
    report ""
    
    # Security Status
    report "=== SECURITY STATUS ==="
    
    # Check for failed login attempts
    if [ -f /var/log/auth.log ]; then
        failed_logins=$(grep "Failed password" /var/log/auth.log | tail -5 | wc -l)
        report "Recent failed login attempts: $failed_logins"
    fi
    
    # Check firewall status
    if command -v ufw &> /dev/null; then
        ufw_status=$(sudo ufw status 2>/dev/null || echo "unknown")
        report "UFW Firewall Status: $ufw_status"
    elif command -v iptables &> /dev/null; then
        iptables_rules=$(sudo iptables -L | wc -l)
        report "Iptables rules count: $iptables_rules"
    fi
    
    # Check for suspicious processes
    suspicious_found=false
    suspicious_processes=("nc" "netcat" "nmap" "masscan")
    for proc in "${suspicious_processes[@]}"; do
        if pgrep "$proc" > /dev/null 2>&1; then
            report "WARNING: Suspicious process found: $proc"
            suspicious_found=true
        fi
    done
    
    if [ "$suspicious_found" = false ]; then
        report "No suspicious processes detected"
    fi
    report ""
    
    # System Updates
    report "=== SYSTEM UPDATES ==="
    if command -v apt &> /dev/null; then
        updates=$(apt list --upgradable 2>/dev/null | wc -l)
        report "Available updates (apt): $((updates - 1))"
    elif command -v yum &> /dev/null; then
        updates=$(yum check-update -q 2>/dev/null | wc -l || echo "0")
        report "Available updates (yum): $updates"
    else
        report "Update information not available"
    fi
    report ""
    
    # VoiceAlert System Status
    report "=== VOICEALERT SYSTEM STATUS ==="
    if [ -f "/tmp/voicealert_patch_status" ]; then
        patch_status=$(cat /tmp/voicealert_patch_status)
        report "Last patch status: $patch_status"
    fi
    
    if [ -f "/tmp/voicealert_isolation_status" ]; then
        isolation_status=$(cat /tmp/voicealert_isolation_status)
        report "Isolation status: $isolation_status"
    fi
    report ""
    
    # Recommendations
    report "=== RECOMMENDATIONS ==="
    
    # Check system load
    load_avg=$(cat /proc/loadavg | cut -d' ' -f1)
    if (( $(echo "$load_avg > 2.0" | bc -l) )); then
        report "HIGH: System load is high ($load_avg)"
    fi
    
    # Check disk usage
    high_disk=$(df -h | awk 'NR>1 {print $5 " " $6}' | grep -E '9[0-9]%|100%' || true)
    if [ -n "$high_disk" ]; then
        report "HIGH: Disk usage is critical: $high_disk"
    fi
    
    # Check memory usage
    mem_usage=$(free | grep Mem | awk '{printf("%.1f", $3/$2 * 100.0)}')
    if (( $(echo "$mem_usage > 90" | bc -l) )); then
        report "HIGH: Memory usage is high (${mem_usage}%)"
    fi
    
    report "Status check completed successfully"
    
    # Display report location
    log "Status report generated: $REPORT_FILE"
    log "Log file: $LOG_FILE"
}

# Run main function
main "$@"