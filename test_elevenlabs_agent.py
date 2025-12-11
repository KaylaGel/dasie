#!/usr/bin/env python3

"""
Test script for ElevenLabs agent conversation
"""

from voice_interface import VoiceInterface
from loguru import logger

def test_command_handler(command: str) -> str:
    """Handle voice commands for security alerts"""
    command = command.lower()
    
    if "patch" in command:
        return "Patching process initiated successfully."
    elif "quarantine" in command or "isolate" in command:
        return "Systems have been quarantined successfully."
    elif "acknowledge" in command or "ack" in command:
        return "Incident acknowledged and logged."
    elif "status" in command:
        return "System status check completed. All systems operational."
    elif "shutdown" in command:
        return "Emergency shutdown sequence initiated."
    else:
        return f"Unknown command '{command}'. Available commands: patch, quarantine, acknowledge, status, shutdown."

def main():
    """Main test function"""
    print("🚨 Testing ElevenLabs Agent Conversation 🚨")
    print("=" * 50)
    
    try:
        # Create ElevenLabs voice interface
        interface = VoiceInterface()
        
        # Check if agent is configured
        if not interface.agent_id:
            print("❌ No ElevenLabs agent ID configured!")
            print("Please set ELEVENLABS_AGENT_ID in your .env file")
            return
        
        print(f"✅ ElevenLabs agent configured: {interface.agent_id}")
        print(f"✅ API key configured: {'Yes' if interface.api_key else 'No'}")
        
        # Security alert message
        alert_message = """
        CRITICAL SECURITY ALERT!
        
        CVE-2025-55182 detected - Remote code execution vulnerability in web framework.
        This affects your production systems and requires immediate action.
        
        You are a security engineer responding to this alert. 
        Available response options:
        - Say 'start patching' to begin automatic security updates
        - Say 'quarantine servers' to isolate affected systems  
        - Say 'acknowledge incident' to log your acknowledgment
        - Say 'status report' to get current system status
        
        How would you like to respond to this security incident?
        """
        
        print("\n🎯 Starting ElevenLabs agent conversation...")
        
        # Start conversation with agent
        result = interface.simulate_conversation_with_agent(alert_message, test_command_handler)
        
        print(f"\n✅ Conversation completed: {result}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main()