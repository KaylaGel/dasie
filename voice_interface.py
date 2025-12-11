#!/usr/bin/env python3

import os
import io
import time
import threading
import json
import requests
from typing import Optional, Callable, Dict

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    sr = None
    SPEECH_RECOGNITION_AVAILABLE = False

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    pygame = None
    PYGAME_AVAILABLE = False
from elevenlabs import ElevenLabs, Voice
from loguru import logger

class VoiceInterface:
    """Microphone-based voice interface using ElevenLabs TTS and local STT"""
    
    def __init__(self, api_key: Optional[str] = None, voice_id: Optional[str] = None, agent_id: Optional[str] = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = voice_id or os.getenv("VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Default voice
        self.agent_id = agent_id or os.getenv("ELEVENLABS_AGENT_ID")  # For conversation simulation
        
        if not self.api_key:
            raise ValueError("ElevenLabs API key not provided")
        
        self.client = ElevenLabs(api_key=self.api_key)
        
        # Initialize speech recognition if available
        if SPEECH_RECOGNITION_AVAILABLE:
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
        else:
            self.recognizer = None
            self.microphone = None
        
        # Initialize pygame for audio playback if available
        if PYGAME_AVAILABLE:
            pygame.mixer.init()
        else:
            logger.warning("Pygame not available, audio playback disabled")
        
        # Conversation state
        self.conversation_active = False
        self.listening = False
        self.command_callback = None
        self.conversation_history = []
        
        # Calibrate microphone
        self._calibrate_microphone()
        
        logger.info("Voice interface initialized")
    
    def _calibrate_microphone(self):
        """Calibrate microphone for ambient noise"""
        try:
            logger.info("Calibrating microphone for ambient noise...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            logger.info("Microphone calibrated successfully")
        except Exception as e:
            logger.warning(f"Failed to calibrate microphone: {e}")
    
    def speak(self, text: str) -> bool:
        """Convert text to speech and play it
        
        Args:
            text: Text to speak
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Speaking: {text[:50]}...")
            
            # Generate audio using ElevenLabs
            audio_generator = self.client.generate(
                text=text,
                voice=Voice(voice_id=self.voice_id),
                model="eleven_monolingual_v1"
            )
            
            # Convert generator to bytes
            audio_data = b"".join(audio_generator)
            
            # Play audio using pygame
            audio_io = io.BytesIO(audio_data)
            pygame.mixer.music.load(audio_io)
            pygame.mixer.music.play()
            
            # Wait for audio to finish
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            logger.info("Speech playback completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to speak text: {e}")
            return False
    
    def listen(self, timeout: int = 5, phrase_timeout: int = 2) -> Optional[str]:
        """Listen for speech input from microphone
        
        Args:
            timeout: Maximum time to wait for speech
            phrase_timeout: Time to wait after speech ends
            
        Returns:
            Recognized text or None
        """
        try:
            logger.info("Listening for speech...")
            
            with self.microphone as source:
                # Listen for audio
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_timeout
                )
            
            logger.info("Processing speech...")
            
            # Recognize speech using Google's free service
            text = self.recognizer.recognize_google(audio)
            
            logger.info(f"Recognized: '{text}'")
            return text.lower().strip()
            
        except sr.WaitTimeoutError:
            logger.info("Listening timeout - no speech detected")
            return None
        except sr.UnknownValueError:
            logger.warning("Could not understand speech")
            return None
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during speech recognition: {e}")
            return None
    
    def simulate_conversation_with_agent(self, initial_message: str, command_callback: Callable[[str], str]) -> str:
        """Use ElevenLabs agent for conversation simulation
        
        Args:
            initial_message: Initial security alert message
            command_callback: Function to handle voice commands
            
        Returns:
            Conversation result summary
        """
        if not self.agent_id:
            logger.warning("No agent ID configured, falling back to manual conversation")
            return self.start_conversation(initial_message, command_callback)
        
        try:
            logger.info("Starting ElevenLabs agent conversation simulation")
            
            # Prepare simulation request
            simulation_data = {
                "simulation_specification": {
                    "simulated_user_config": {
                        "first_message": initial_message,
                        "language": "en",
                        "disable_first_message_interruptions": False
                    }
                },
                "new_turns_limit": 10  # Limit conversation length
            }
            
            # Make API request to ElevenLabs
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            url = f"https://api.elevenlabs.io/v1/convai/agents/{self.agent_id}/simulate-conversation"
            
            response = requests.post(url, headers=headers, json=simulation_data)
            
            if response.status_code == 200:
                result = response.json()
                
                # Process the conversation
                conversation_turns = result.get("simulated_conversation", [])
                analysis = result.get("analysis", {})
                
                # Extract voice commands from conversation
                self._process_agent_conversation(conversation_turns, command_callback)
                
                # Return summary
                summary = analysis.get("transcript_summary", "Conversation completed")
                logger.info(f"Agent conversation completed: {summary}")
                
                return summary
            else:
                logger.error(f"Agent simulation failed: {response.status_code} - {response.text}")
                return self.start_conversation(initial_message, command_callback)
                
        except Exception as e:
            logger.error(f"Error in agent conversation simulation: {e}")
            return self.start_conversation(initial_message, command_callback)
    
    def _process_agent_conversation(self, conversation_turns: list, command_callback: Callable[[str], str]):
        """Process conversation turns from agent simulation
        
        Args:
            conversation_turns: List of conversation turns from agent
            command_callback: Function to handle detected commands
        """
        logger.info("Processing agent conversation turns")
        
        for turn in conversation_turns:
            role = turn.get("role", "")
            content = turn.get("content", "")
            
            if role == "user" and content:
                # Check if user message contains commands
                logger.info(f"User said: {content}")
                
                # Look for command keywords in the conversation
                command_keywords = ["patch", "quarantine", "isolate", "acknowledge", "shutdown", "status"]
                
                for keyword in command_keywords:
                    if keyword in content.lower():
                        logger.info(f"Detected command keyword: {keyword}")
                        try:
                            response = command_callback(content.lower())
                            logger.info(f"Command executed: {response}")
                        except Exception as e:
                            logger.error(f"Error executing command: {e}")
                        break
    
    def start_conversation(self, initial_message: str, command_callback: Callable[[str], str]) -> str:
        """Start an interactive voice conversation
        
        Args:
            initial_message: Initial message to speak
            command_callback: Function to handle voice commands
            
        Returns:
            Final conversation result
        """
        # Try agent simulation first if available
        if self.agent_id:
            return self.simulate_conversation_with_agent(initial_message, command_callback)
        
        self.conversation_active = True
        self.command_callback = command_callback
        
        logger.info("Starting voice conversation")
        
        try:
            # Speak initial message
            if not self.speak(initial_message):
                return "Failed to start conversation - audio error"
            
            # Main conversation loop
            attempts = 0
            max_attempts = 3
            
            while self.conversation_active and attempts < max_attempts:
                self.speak("What would you like to do?")
                
                # Listen for response
                response = self.listen(timeout=10, phrase_timeout=3)
                
                if response is None:
                    attempts += 1
                    if attempts < max_attempts:
                        self.speak("I didn't hear you. Please speak clearly.")
                    else:
                        self.speak("No response received. Ending conversation.")
                        break
                    continue
                
                # Process command
                if self.command_callback:
                    result = self.command_callback(response)
                    self.speak(result)
                    
                    # Check if conversation should continue
                    if "completed" in result.lower() or "acknowledged" in result.lower():
                        self.speak("Thank you. Conversation ended.")
                        break
                else:
                    self.speak("Command received but no handler available.")
                    break
                
                attempts = 0  # Reset attempts on successful interaction
            
            return "Conversation completed"
            
        except KeyboardInterrupt:
            logger.info("Conversation interrupted by user")
            self.speak("Conversation interrupted.")
            return "Interrupted"
        except Exception as e:
            logger.error(f"Error during conversation: {e}")
            self.speak("An error occurred. Ending conversation.")
            return f"Error: {e}"
        finally:
            self.conversation_active = False
    
    def quick_alert(self, message: str, wait_for_response: bool = True) -> Optional[str]:
        """Send a quick voice alert and optionally wait for response
        
        Args:
            message: Alert message to speak
            wait_for_response: Whether to wait for voice response
            
        Returns:
            Voice response if wait_for_response is True
        """
        logger.info("Sending voice alert")
        
        try:
            # Speak the alert
            if not self.speak(message):
                return "Failed to deliver alert"
            
            if wait_for_response:
                response = self.listen(timeout=15, phrase_timeout=5)
                return response
            
            return "Alert delivered"
            
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
            return None
    
    def stop_conversation(self):
        """Stop the current conversation"""
        logger.info("Stopping conversation")
        self.conversation_active = False
        
        # Stop any playing audio
        try:
            pygame.mixer.music.stop()
        except:
            pass
    
    def test_audio_system(self) -> bool:
        """Test the audio input/output system
        
        Returns:
            True if system is working
        """
        logger.info("Testing audio system...")
        
        try:
            # Test speech synthesis
            test_message = "Audio test. Can you hear me? Please say yes or no."
            if not self.speak(test_message):
                logger.error("Speech synthesis test failed")
                return False
            
            # Test speech recognition
            logger.info("Testing speech recognition - please say 'test'")
            response = self.listen(timeout=10)
            
            if response and "test" in response:
                self.speak("Audio system test successful!")
                logger.info("Audio system test passed")
                return True
            else:
                self.speak("Speech recognition test failed")
                logger.warning("Speech recognition test failed")
                return False
                
        except Exception as e:
            logger.error(f"Audio system test error: {e}")
            return False

class MockVoiceInterface:
    """Mock voice interface for testing without audio hardware"""
    
    def __init__(self):
        logger.info("Using mock voice interface")
        self.conversation_active = False
    
    def speak(self, text: str) -> bool:
        print(f"\n🔊 SYSTEM SPEAKING: {text}\n")
        return True
    
    def listen(self, timeout: int = 5, phrase_timeout: int = 2) -> Optional[str]:
        print("🎤 Listening for your response...")
        response = input("Enter your voice command: ").strip()
        return response if response else None
    
    def start_conversation(self, initial_message: str, command_callback: Callable[[str], str]) -> str:
        print("\n" + "="*50)
        print("VOICE CONVERSATION STARTED")
        print("="*50)
        
        self.speak(initial_message)
        
        while True:
            response = self.listen()
            
            if not response:
                self.speak("No response received. Ending conversation.")
                break
            
            if response.lower() in ["quit", "exit", "end"]:
                self.speak("Ending conversation.")
                break
            
            result = command_callback(response)
            self.speak(result)
            
            if "completed" in result.lower() or "acknowledged" in result.lower():
                break
        
        print("="*50)
        print("VOICE CONVERSATION ENDED")
        print("="*50 + "\n")
        
        return "Conversation completed"
    
    def quick_alert(self, message: str, wait_for_response: bool = True) -> Optional[str]:
        print("\n" + "🚨" * 20)
        self.speak(f"ALERT: {message}")
        print("🚨" * 20 + "\n")
        
        if wait_for_response:
            return self.listen()
        return "Alert delivered"
    
    def stop_conversation(self):
        self.conversation_active = False
    
    def test_audio_system(self) -> bool:
        self.speak("Mock audio system test - always passes")
        return True

def create_voice_interface(use_mock: bool = False) -> VoiceInterface:
    """Factory function to create appropriate voice interface
    
    Args:
        use_mock: Whether to use mock implementation
        
    Returns:
        Voice interface instance
    """
    if use_mock:
        return MockVoiceInterface()
    
    # Try enhanced interface with speech recognition first
    try:
        from speech_recognition_helper import create_enhanced_voice_interface
        logger.info("Using enhanced voice interface (system TTS + speech recognition)")
        return create_enhanced_voice_interface()
    except Exception as e:
        logger.warning(f"Enhanced interface failed: {e}")
        
        # Fall back to simple interface
        try:
            from simple_voice_interface import create_simple_voice_interface
            logger.info("Using simple voice interface (system TTS + text input)")
            return create_simple_voice_interface()
        except Exception as e2:
            logger.warning(f"Simple interface failed: {e2}")
            logger.info("Falling back to mock interface")
            return MockVoiceInterface()

if __name__ == "__main__":
    # Test the voice interface
    def test_command_handler(command: str) -> str:
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
            return "Unknown command. Available commands: patch, quarantine, acknowledge, status, shutdown."
    
    # Test with ElevenLabs interface 
    interface = create_voice_interface(use_mock=False)
    
    # Test audio system
    interface.test_audio_system()
    
    # Test conversation
    alert_message = """
    Security Alert! Critical vulnerability CVE-2025-55182 detected.
    
    Remote code execution vulnerability in web framework allowing unauthenticated access.
    This affects your production systems and requires immediate action.
    
    Available commands: start patching, quarantine servers, acknowledge incident, status report.
    """
    
    result = interface.start_conversation(alert_message, test_command_handler)
    print(f"Conversation result: {result}")