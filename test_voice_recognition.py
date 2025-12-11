#!/usr/bin/env python3

"""
Test script for voice recognition functionality
Tests real speech-to-text without complex dependencies
"""

import sys
import platform
from speech_recognition_helper import SpeechRecognizer, create_enhanced_voice_interface
from command_engine import CommandEngine

def test_basic_speech_recognition():
    """Test basic speech recognition functionality"""
    print("Testing Basic Speech Recognition")
    print("=" * 40)
    
    recognizer = SpeechRecognizer()
    
    print(f"System: {platform.system()}")
    print(f"Available methods: {recognizer.recognition_methods}")
    
    # Test recognition
    print("\nTesting voice recognition...")
    print("Say 'hello world' or any test phrase")
    
    result = recognizer.listen(timeout=15, prompt="Speak clearly into your microphone")
    
    if result:
        print(f"✅ Recognition successful: '{result}'")
        return True
    else:
        print("❌ No speech recognized")
        return False

def test_enhanced_voice_interface():
    """Test the enhanced voice interface"""
    print("\n\nTesting Enhanced Voice Interface")
    print("=" * 40)
    
    try:
        interface = create_enhanced_voice_interface()
        
        # Test TTS
        interface.speak("Voice interface test. Can you hear me?")
        
        # Test combined TTS and STT
        interface.speak("Now I will listen for your response.")
        
        response = interface.listen(timeout=10, prompt="Say 'test successful'")
        
        if response:
            interface.speak(f"I heard you say: {response}")
            print(f"✅ Full interface test successful: '{response}'")
            return True
        else:
            print("❌ No speech recognized in interface test")
            return False
            
    except Exception as e:
        print(f"❌ Enhanced interface test failed: {e}")
        return False

def test_security_commands():
    """Test recognition of security commands"""
    print("\n\nTesting Security Command Recognition")
    print("=" * 40)
    
    interface = create_enhanced_voice_interface()
    engine = CommandEngine()
    
    def command_handler(command: str) -> str:
        return engine.process_voice_command(command, "CVE-2025-55182")
    
    test_commands = [
        "start patching",
        "quarantine servers", 
        "acknowledge incident",
        "status report"
    ]
    
    interface.speak("I will test recognition of security commands.")
    
    for i, expected_cmd in enumerate(test_commands, 1):
        print(f"\nTest {i}/4:")
        interface.speak(f"Please say: {expected_cmd}")
        
        result = interface.listen(timeout=15, prompt=f"Say '{expected_cmd}'")
        
        if result:
            print(f"You said: '{result}'")
            
            # Process the command
            response = command_handler(result)
            interface.speak(f"Command processed: {response[:50]}...")
            
            print(f"✅ Command '{expected_cmd}' test completed")
        else:
            print(f"❌ Failed to recognize '{expected_cmd}'")
    
    return True

def interactive_voice_demo():
    """Interactive demo of voice conversation"""
    print("\n\nInteractive Voice Demo")
    print("=" * 40)
    
    interface = create_enhanced_voice_interface()
    engine = CommandEngine()
    
    def command_handler(command: str) -> str:
        return engine.process_voice_command(command, "CVE-2025-55182")
    
    alert_message = """
    Security Alert Test!
    
    This is a test of the voice conversation system.
    You can say commands like:
    start patching, quarantine servers, acknowledge incident, or status report.
    
    What would you like to do?
    """
    
    print("Starting interactive voice conversation...")
    result = interface.start_conversation(alert_message, command_handler)
    
    print(f"Demo completed: {result}")
    return True

def main():
    """Main test runner"""
    print("VoiceAlert Speech Recognition Test Suite")
    print("=" * 50)
    print("This will test real speech-to-text functionality")
    print("Make sure you have a working microphone")
    print("=" * 50)
    
    tests = [
        ("Basic Speech Recognition", test_basic_speech_recognition),
        ("Enhanced Voice Interface", test_enhanced_voice_interface), 
        ("Security Commands", test_security_commands),
        ("Interactive Demo", interactive_voice_demo)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        try:
            print(f"Running: {test_name}")
            result = test_func()
            results[test_name] = result
        except KeyboardInterrupt:
            print(f"\n❌ {test_name} interrupted by user")
            results[test_name] = False
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All speech recognition tests passed!")
        print("Your system supports voice input for VoiceAlert!")
    else:
        print("\n⚠️  Some tests failed.")
        print("The system will fall back to text input mode.")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)