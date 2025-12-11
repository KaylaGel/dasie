#!/usr/bin/env python3

"""
Demo script for VoiceAlert System
Shows the voice conversation flow without requiring CVE monitoring
"""

import os
from simple_voice_interface import create_simple_voice_interface
from command_engine import CommandEngine

def demo_command_handler(command: str) -> str:
    """Demo command handler that shows what each command does"""
    engine = CommandEngine()
    return engine.process_voice_command(command, "CVE-2025-55182")

def main():
    print("\n" + "="*60)
    print("🚨 VOICEALERT SYSTEM DEMO 🚨")
    print("="*60)
    print("This demo shows how the voice conversation works")
    print("You'll receive a security alert and can respond with commands")
    print("="*60 + "\n")
    
    # Create voice interface
    interface = create_simple_voice_interface()
    
    # Demo security alert
    alert_message = """
    CRITICAL SECURITY ALERT!
    
    CVE-2025-55182 has been detected in your web framework.
    This vulnerability allows remote code execution without authentication.
    
    Your production systems are affected and require immediate action.
    
    Available voice commands:
    - Say "start patching" to begin automatic security updates
    - Say "quarantine servers" to isolate affected systems
    - Say "acknowledge incident" to log the incident
    - Say "status report" to check system status
    - Say "emergency shutdown" for emergency procedures
    
    What is your response?
    """
    
    # Start conversation
    result = interface.start_conversation(alert_message, demo_command_handler)
    
    print(f"\n🎯 Demo completed: {result}")
    print("\n" + "="*60)
    print("💡 In a real deployment:")
    print("- System monitors CVE feeds automatically")
    print("- Alerts trigger when vulnerabilities affect your systems") 
    print("- Voice commands execute actual defensive scripts")
    print("- Full audit trail is maintained")
    print("="*60)

if __name__ == "__main__":
    main()