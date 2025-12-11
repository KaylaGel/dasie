#!/usr/bin/env python3

"""
Simple voice interface that works without PyAudio dependencies
Uses system text-to-speech and text input for testing
"""

import os
import subprocess
import platform
from typing import Optional, Callable
from loguru import logger

class SimpleVoiceInterface:
    """Simple voice interface using system TTS and text input"""
    
    def __init__(self):
        self.system = platform.system()
        logger.info(f"Simple voice interface initialized for {self.system}")
    
    def speak(self, text: str) -> bool:
        """Use system text-to-speech to speak text"""
        try:
            if self.system == "Darwin":  # macOS
                subprocess.run(["say", text], check=True)
            elif self.system == "Linux":
                subprocess.run(["espeak", text], check=True)
            elif self.system == "Windows":
                # Use PowerShell for Windows TTS
                ps_command = f'Add-Type -AssemblyName System.speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("{text}")'
                subprocess.run(["powershell", "-Command", ps_command], check=True)
            else:
                print(f"🔊 SYSTEM SPEAKING: {text}")
                
            return True
        except subprocess.CalledProcessError:
            # Fallback to text output
            print(f"🔊 SYSTEM SPEAKING: {text}")
            return True
        except Exception as e:
            logger.warning(f"TTS failed, using text output: {e}")
            print(f"🔊 SYSTEM SPEAKING: {text}")
            return True
    
    def listen(self, timeout: int = 5, phrase_timeout: int = 2) -> Optional[str]:
        """Listen for voice input with speech recognition"""
        try:
            # Try to use enhanced speech recognition
            from speech_recognition_helper import SpeechRecognizer
            
            recognizer = SpeechRecognizer()
            result = recognizer.listen(timeout=timeout, prompt="🎤 Listening for your voice command...")
            
            if result:
                return result
            else:
                print("No speech detected, falling back to text input...")
                return self._text_fallback()
                
        except ImportError:
            logger.warning("Speech recognition not available, using text input")
            return self._text_fallback()
        except Exception as e:
            logger.warning(f"Speech recognition failed: {e}, using text input")
            return self._text_fallback()
    
    def _text_fallback(self) -> Optional[str]:
        """Fallback to text input"""
        try:
            response = input("💬 Enter your voice command (or press Enter to skip): ").strip()
            return response if response else None
        except (KeyboardInterrupt, EOFError):
            return None
    
    def start_conversation(self, initial_message: str, command_callback: Callable[[str], str]) -> str:
        """Start an interactive conversation"""
        print("\n" + "="*60)
        print("🚨 SECURITY ALERT - VOICE CONVERSATION STARTED 🚨")
        print("="*60)
        
        # Speak the initial alert
        self.speak(initial_message)
        print(f"\nAlert Message:\n{initial_message}\n")
        
        # Interactive conversation loop
        attempts = 0
        max_attempts = 3
        
        while attempts < max_attempts:
            self.speak("What would you like to do?")
            
            response = self.listen()
            
            if not response:
                attempts += 1
                if attempts < max_attempts:
                    self.speak("I didn't hear you. Please try again.")
                    print("💡 Available commands: start patching, quarantine servers, acknowledge incident, status report")
                else:
                    self.speak("No response received. Ending conversation.")
                    break
                continue
            
            # Process the command
            logger.info(f"Processing command: {response}")
            result = command_callback(response)
            
            # Speak the result
            self.speak(result)
            print(f"\n✅ Response: {result}\n")
            
            # Check if conversation should end
            if any(word in result.lower() for word in ["completed", "acknowledged", "successful"]):
                self.speak("Thank you. Security response completed.")
                break
            
            attempts = 0  # Reset on successful interaction
        
        print("="*60)
        print("🔒 SECURITY CONVERSATION ENDED")
        print("="*60)
        
        return "Conversation completed"
    
    def quick_alert(self, message: str, wait_for_response: bool = True) -> Optional[str]:
        """Send a quick alert and optionally wait for response"""
        print("\n" + "🚨" * 25)
        print("CRITICAL SECURITY ALERT")
        print("🚨" * 25)
        
        self.speak(message)
        print(f"\nAlert: {message}\n")
        
        if wait_for_response:
            return self.listen(timeout=15)
        
        return "Alert delivered"
    
    def stop_conversation(self):
        """Stop the conversation"""
        logger.info("Conversation stopped")
    
    def test_audio_system(self) -> bool:
        """Test the audio system"""
        print("\n🔧 Testing audio system...")
        self.speak("Audio system test. Please respond with 'test' to confirm.")
        
        response = self.listen()
        if response and "test" in response.lower():
            self.speak("Audio test successful!")
            print("✅ Audio test passed")
            return True
        else:
            print("⚠️  Audio test completed with text interface")
            return True  # Still functional, just without audio

def create_simple_voice_interface():
    """Create a simple voice interface that works without complex dependencies"""
    return SimpleVoiceInterface()

if __name__ == "__main__":
    # Test the simple interface
    def test_command_handler(command: str) -> str:
        if "patch" in command.lower():
            return "Patching process initiated successfully."
        elif "quarantine" in command.lower() or "isolate" in command.lower():
            return "Systems have been quarantined successfully."
        elif "acknowledge" in command.lower():
            return "Incident acknowledged and logged."
        elif "status" in command.lower():
            return "System status check completed. All systems operational."
        elif "shutdown" in command.lower():
            return "Emergency shutdown sequence initiated."
        else:
            return "Unknown command. Available commands: patch, quarantine, acknowledge, status, shutdown."
    
    # Test the interface
    interface = create_simple_voice_interface()
    
    # Test audio
    interface.test_audio_system()
    
    # Test conversation
    alert_message = """
    Critical Security Alert! 
    
    CVE-2025-55182 detected - Remote code execution vulnerability in web framework.
    This affects your production systems and requires immediate action.
    
    Available voice commands:
    - Say 'start patching' to begin automatic patching
    - Say 'quarantine servers' to isolate affected systems  
    - Say 'acknowledge incident' to log acknowledgment
    - Say 'status report' for system status
    """
    
    result = interface.start_conversation(alert_message, test_command_handler)
    print(f"\nFinal result: {result}")