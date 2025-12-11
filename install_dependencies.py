#!/usr/bin/env python3

"""
Installation helper for VoiceAlert System dependencies
Handles platform-specific package installation issues
"""

import subprocess
import sys
import platform
import os

def run_command(cmd, description):
    """Run a shell command with error handling"""
    print(f"Installing {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} installed successfully")
            return True
        else:
            print(f"❌ Failed to install {description}: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error installing {description}: {e}")
        return False

def install_pyaudio_macos():
    """Install PyAudio on macOS using homebrew if available"""
    print("Installing PyAudio on macOS...")
    
    # Try homebrew first
    if run_command("brew install portaudio", "PortAudio via Homebrew"):
        if run_command("pip install PyAudio", "PyAudio"):
            return True
    
    # Fallback to pip with system libraries
    print("Trying pip installation with system flags...")
    return run_command("pip install --global-option='build_ext' --global-option='-I/usr/local/include' --global-option='-L/usr/local/lib' PyAudio", "PyAudio with system libs")

def install_dependencies():
    """Install all dependencies with platform-specific handling"""
    system = platform.system()
    print(f"Detected system: {system}")
    
    # Core dependencies that should work everywhere
    core_deps = [
        ("openai>=1.0.0", "OpenAI"),
        ("elevenlabs>=1.0.0", "ElevenLabs"),
        ("requests>=2.25.0", "Requests"),
        ("python-dotenv>=1.0.0", "Python-dotenv"),
        ("pydantic>=2.0.0", "Pydantic"),
        ("loguru>=0.7.0", "Loguru"),
        ("SpeechRecognition>=3.10.0", "SpeechRecognition"),
        ("pygame>=2.5.0", "Pygame"),
        ("pydub>=0.25.1", "Pydub")
    ]
    
    print("Installing core dependencies...")
    failed = []
    
    for package, name in core_deps:
        if not run_command(f"pip install '{package}'", name):
            failed.append(name)
    
    # Handle PyAudio separately due to platform issues
    pyaudio_success = False
    
    if system == "Darwin":  # macOS
        pyaudio_success = install_pyaudio_macos()
    elif system == "Linux":
        # Try installing system dependencies first
        print("Installing Linux audio dependencies...")
        run_command("sudo apt-get update && sudo apt-get install -y portaudio19-dev python3-pyaudio", "Linux audio libs")
        pyaudio_success = run_command("pip install PyAudio", "PyAudio")
    elif system == "Windows":
        pyaudio_success = run_command("pip install PyAudio", "PyAudio")
    
    if not pyaudio_success:
        failed.append("PyAudio")
        print("\n⚠️  PyAudio installation failed!")
        print("You can still use the system in mock mode by setting USE_MOCK_VOICE=true")
    
    # Summary
    print("\n" + "="*50)
    print("INSTALLATION SUMMARY")
    print("="*50)
    
    if failed:
        print(f"❌ Failed to install: {', '.join(failed)}")
        print("\nWorkarounds:")
        if "PyAudio" in failed:
            print("- For audio issues: Set USE_MOCK_VOICE=true in your .env file")
            print("- On macOS: Install Homebrew, then run: brew install portaudio")
            print("- On Ubuntu: sudo apt-get install portaudio19-dev")
        print(f"\nYou can manually install failed packages with: pip install <package_name>")
    else:
        print("✅ All dependencies installed successfully!")
    
    print(f"\nNext steps:")
    print("1. Copy .env.example to .env")
    print("2. Add your API keys to .env")
    print("3. Run: python voicealert_system.py --test")

if __name__ == "__main__":
    print("VoiceAlert System Dependency Installer")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ required")
        sys.exit(1)
    
    install_dependencies()