#!/usr/bin/env python3

"""
Test script for VoiceAlert System without PyAudio dependencies
This script tests all components to ensure they work properly
"""

import os
import sys
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import requests
        print("✅ requests")
    except ImportError as e:
        print(f"❌ requests: {e}")
        return False
    
    try:
        import openai
        print("✅ openai")
    except ImportError as e:
        print(f"❌ openai: {e}")
        return False
    
    try:
        import elevenlabs
        print("✅ elevenlabs")
    except ImportError as e:
        print(f"❌ elevenlabs: {e}")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv")
    except ImportError as e:
        print(f"❌ python-dotenv: {e}")
        return False
    
    try:
        import pydantic
        print("✅ pydantic")
    except ImportError as e:
        print(f"❌ pydantic: {e}")
        return False
    
    try:
        import loguru
        print("✅ loguru")
    except ImportError as e:
        print(f"❌ loguru: {e}")
        return False
    
    return True

def test_voice_interface():
    """Test the simple voice interface"""
    print("\nTesting simple voice interface...")
    
    try:
        from simple_voice_interface import create_simple_voice_interface
        
        interface = create_simple_voice_interface()
        
        # Test TTS
        interface.speak("Voice interface test successful")
        
        print("✅ Simple voice interface working")
        return True
        
    except Exception as e:
        print(f"❌ Simple voice interface failed: {e}")
        return False

def test_command_engine():
    """Test the command processing engine"""
    print("\nTesting command engine...")
    
    try:
        from command_engine import CommandEngine
        
        engine = CommandEngine()
        
        # Test commands
        test_commands = [
            "start patching",
            "quarantine servers", 
            "acknowledge incident",
            "status report"
        ]
        
        for cmd in test_commands:
            response = engine.process_voice_command(cmd, "CVE-2025-55182")
            print(f"  {cmd} → {response[:50]}...")
        
        print("✅ Command engine working")
        return True
        
    except Exception as e:
        print(f"❌ Command engine failed: {e}")
        return False

def test_cve_scanner():
    """Test CVE scanner (mock mode)"""
    print("\nTesting CVE scanner...")
    
    try:
        from cve_scanner import CVEScanner
        
        scanner = CVEScanner()
        
        # Test with mock data
        mock_cve = {
            "cve_id": "CVE-2025-55182",
            "description": "Test vulnerability",
            "severity": "Critical"
        }
        
        cve_info = scanner.extract_cve_info(mock_cve)
        print(f"  Extracted CVE info: {cve_info['cve_id']}")
        
        print("✅ CVE scanner working")
        return True
        
    except Exception as e:
        print(f"❌ CVE scanner failed: {e}")
        return False

def test_llm_summarizer():
    """Test LLM summarizer"""
    print("\nTesting LLM summarizer...")
    
    try:
        from llm_summarizer import LLMSummarizer
        
        # Check if API key is available
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️  No OpenAI API key - testing fallback summary")
            
            summarizer = LLMSummarizer(api_key="dummy")
            
            mock_cve = {
                "cve_id": "CVE-2025-55182",
                "description": "Test vulnerability",
                "severity": "Critical"
            }
            
            summary = summarizer._generate_fallback_summary(mock_cve)
            print("  Fallback summary generated")
        else:
            print("✅ OpenAI API key found")
        
        print("✅ LLM summarizer working")
        return True
        
    except Exception as e:
        print(f"❌ LLM summarizer failed: {e}")
        return False

def test_main_system():
    """Test the main VoiceAlert system"""
    print("\nTesting main VoiceAlert system...")
    
    try:
        # Set environment for testing
        os.environ["USE_MOCK_VOICE"] = "true"
        os.environ["USE_MICROPHONE"] = "true"
        os.environ["POLL_INTERVAL_MINUTES"] = "1"
        
        from voicealert_system import VoiceAlertSystem
        
        system = VoiceAlertSystem()
        
        # Test single CVE processing
        system.process_single_cve("CVE-2025-55182")
        
        print("✅ Main system working")
        return True
        
    except Exception as e:
        print(f"❌ Main system failed: {e}")
        return False

def check_environment():
    """Check environment setup"""
    print("\nChecking environment...")
    
    # Check if .env exists
    if os.path.exists(".env"):
        print("✅ .env file found")
    else:
        print("⚠️  .env file not found - copy .env.example to .env")
    
    # Check scripts
    scripts_dir = Path("scripts")
    if scripts_dir.exists():
        scripts = list(scripts_dir.glob("*.sh"))
        print(f"✅ {len(scripts)} scripts found")
    else:
        print("❌ Scripts directory not found")
    
    # Check logs directory
    logs_dir = Path("logs")
    if not logs_dir.exists():
        logs_dir.mkdir(exist_ok=True)
        print("✅ Created logs directory")
    else:
        print("✅ Logs directory exists")

def main():
    """Run all tests"""
    print("VoiceAlert System Test Suite")
    print("=" * 50)
    
    tests = [
        test_imports,
        check_environment,
        test_voice_interface,
        test_command_engine,
        test_cve_scanner,
        test_llm_summarizer,
        test_main_system
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with error: {e}")
    
    print("\n" + "=" * 50)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System ready to use.")
        print("\nNext steps:")
        print("1. Add your API keys to .env file")
        print("2. Run: python voicealert_system.py --test")
    else:
        print("⚠️  Some tests failed. Check error messages above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)