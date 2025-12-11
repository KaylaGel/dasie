#!/usr/bin/env python3

import os
import time
from typing import Dict, Optional, Callable
from elevenlabs import ElevenLabs
from loguru import logger

class VoiceCaller:
    """Handles ElevenLabs voice call functionality"""
    
    def __init__(self, api_key: Optional[str] = None, voice_id: Optional[str] = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = voice_id or os.getenv("VOICE_ID")
        
        if not self.api_key:
            raise ValueError("ElevenLabs API key not provided")
        
        if not self.voice_id:
            logger.warning("No voice ID provided, will use default")
            
        self.client = ElevenLabs(api_key=self.api_key)
        self.active_calls = {}
    
    def place_call(self, phone_number: str, script: str, command_callback: Optional[Callable] = None) -> Optional[str]:
        """Place an outbound voice call
        
        Args:
            phone_number: Target phone number
            script: Text to read via TTS
            command_callback: Function to handle voice commands
            
        Returns:
            Call ID if successful, None otherwise
        """
        try:
            logger.info(f"Placing voice call to {phone_number}")
            
            # Note: ElevenLabs calling API may vary based on their current implementation
            # This is based on the conceptual API described in the PRD
            call = self.client.call.create(
                to=phone_number,
                voice_id=self.voice_id,
                text=script,
                enable_commands=True,
                webhook_url=None  # Would need webhook for production
            )
            
            call_id = getattr(call, 'call_id', getattr(call, 'id', None))
            
            if call_id:
                self.active_calls[call_id] = {
                    "phone_number": phone_number,
                    "start_time": time.time(),
                    "callback": command_callback,
                    "status": "active"
                }
                logger.info(f"Call initiated with ID: {call_id}")
                return call_id
            else:
                logger.error("Failed to get call ID from ElevenLabs response")
                return None
                
        except Exception as e:
            logger.error(f"Failed to place call: {e}")
            return None
    
    def handle_voice_response(self, call_id: str, transcribed_text: str) -> str:
        """Process voice response from call recipient
        
        Args:
            call_id: Active call identifier
            transcribed_text: Speech-to-text result
            
        Returns:
            Response text to send back to caller
        """
        if call_id not in self.active_calls:
            logger.warning(f"Received response for unknown call ID: {call_id}")
            return "Sorry, I don't recognize this call session."
        
        call_info = self.active_calls[call_id]
        callback = call_info.get("callback")
        
        logger.info(f"Processing voice response: '{transcribed_text}'")
        
        if callback:
            try:
                response = callback(transcribed_text.lower().strip())
                logger.info(f"Command processed, response: {response}")
                return response
            except Exception as e:
                logger.error(f"Error processing voice command: {e}")
                return "Sorry, there was an error processing your command."
        else:
            return "Command received but no handler configured."
    
    def end_call(self, call_id: str) -> bool:
        """End an active call
        
        Args:
            call_id: Call to terminate
            
        Returns:
            True if successful
        """
        try:
            if call_id in self.active_calls:
                # Update call status
                self.active_calls[call_id]["status"] = "ended"
                self.active_calls[call_id]["end_time"] = time.time()
                
                # Attempt to end call via API if available
                # Note: Actual API method may differ
                try:
                    self.client.call.end(call_id)
                except AttributeError:
                    logger.warning("ElevenLabs call.end() method not available")
                
                logger.info(f"Call {call_id} ended")
                return True
            else:
                logger.warning(f"Call ID {call_id} not found in active calls")
                return False
                
        except Exception as e:
            logger.error(f"Error ending call: {e}")
            return False
    
    def get_call_status(self, call_id: str) -> Optional[Dict]:
        """Get status of a call
        
        Args:
            call_id: Call identifier
            
        Returns:
            Call status information
        """
        return self.active_calls.get(call_id)
    
    def cleanup_old_calls(self, max_age_seconds: int = 3600):
        """Remove old call records
        
        Args:
            max_age_seconds: Maximum age to keep call records
        """
        current_time = time.time()
        to_remove = []
        
        for call_id, call_info in self.active_calls.items():
            if current_time - call_info["start_time"] > max_age_seconds:
                to_remove.append(call_id)
        
        for call_id in to_remove:
            del self.active_calls[call_id]
            logger.info(f"Cleaned up old call record: {call_id}")

class MockVoiceCaller:
    """Mock implementation for testing without ElevenLabs API"""
    
    def __init__(self):
        logger.info("Using mock voice caller for testing")
        self.call_counter = 0
    
    def place_call(self, phone_number: str, script: str, command_callback: Optional[Callable] = None) -> str:
        self.call_counter += 1
        call_id = f"mock_call_{self.call_counter}"
        
        logger.info(f"[MOCK] Placing call to {phone_number}")
        logger.info(f"[MOCK] Call script: {script[:100]}...")
        
        # Simulate call interaction
        if command_callback:
            logger.info("[MOCK] Simulating voice command: 'start patching'")
            response = command_callback("start patching")
            logger.info(f"[MOCK] Command response: {response}")
        
        return call_id
    
    def handle_voice_response(self, call_id: str, transcribed_text: str) -> str:
        return f"[MOCK] Received: {transcribed_text}"
    
    def end_call(self, call_id: str) -> bool:
        logger.info(f"[MOCK] Ending call {call_id}")
        return True
    
    def get_call_status(self, call_id: str) -> Dict:
        return {"status": "mock", "call_id": call_id}

def create_voice_caller(use_mock: bool = False) -> VoiceCaller:
    """Factory function to create appropriate voice caller
    
    Args:
        use_mock: Whether to use mock implementation
        
    Returns:
        Voice caller instance
    """
    if use_mock or not os.getenv("ELEVENLABS_API_KEY"):
        return MockVoiceCaller()
    else:
        return VoiceCaller()

if __name__ == "__main__":
    # Test the voice caller
    def test_command_handler(command: str) -> str:
        if "patch" in command:
            return "Patching initiated"
        elif "quarantine" in command:
            return "Servers quarantined"
        elif "acknowledge" in command:
            return "Incident acknowledged"
        else:
            return "Unknown command"
    
    caller = create_voice_caller(use_mock=True)
    
    test_script = """
    Security Alert! Critical vulnerability CVE-2025-55182 detected.
    
    Remote code execution vulnerability allowing unauthenticated access.
    Immediate action required.
    
    Say 'start patching' to begin remediation.
    """
    
    call_id = caller.place_call("+1234567890", test_script, test_command_handler)
    print(f"Call placed with ID: {call_id}")