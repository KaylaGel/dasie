#!/usr/bin/env python3

"""
Test script focused on security incident response with ElevenLabs agent
"""

from voice_interface import VoiceInterface
from loguru import logger

def test_command_handler(command: str) -> str:
    """Handle security voice commands"""
    command = command.lower()
    
    if "patch" in command:
        return "Security patches are being applied to all affected systems. ETA: 15 minutes."
    elif "quarantine" in command or "isolate" in command:
        return "Affected servers are being quarantined. Network isolation in progress."
    elif "acknowledge" in command or "ack" in command:
        return "Security incident CVE-2025-55182 acknowledged by security team."
    elif "status" in command:
        return "System status: 15 servers affected, patching in progress, no breach detected."
    elif "emergency" in command or "shutdown" in command:
        return "Emergency shutdown initiated for all affected systems."
    else:
        return f"Security command received: '{command}'. Processing incident response."

def main():
    """Test security-focused agent conversation"""
    print("🚨 Security Incident Response Agent Test 🚨")
    print("=" * 50)
    
    try:
        interface = VoiceInterface()
        
        if not interface.agent_id:
            print("❌ ElevenLabs agent not configured")
            return
        
        print(f"✅ Testing agent: {interface.agent_id}")
        
        # More focused security alert
        security_alert = """
        IMMEDIATE ACTION REQUIRED - SECURITY BREACH ALERT
        
        This is an emergency security incident notification.
        
        VULNERABILITY: CVE-2025-55182 - Critical Remote Code Execution
        THREAT LEVEL: CRITICAL - Active exploitation detected
        AFFECTED SYSTEMS: Web servers in production environment
        
        You are the on-call security engineer responding to this incident.
        
        REQUIRED IMMEDIATE ACTIONS:
        1. Acknowledge this security incident
        2. Choose response: emergency patch deployment OR quarantine affected systems
        3. Confirm action completion
        
        This is a live security incident. Please respond immediately with your chosen action.
        What is your immediate response to this critical security threat?
        """
        
        print("🎯 Initiating security incident response...")
        result = interface.simulate_conversation_with_agent(security_alert, test_command_handler)
        
        print(f"\n🔒 Security Response Summary:")
        print("=" * 50)
        print(result)
        
    except Exception as e:
        logger.error(f"Security test failed: {e}")
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main()