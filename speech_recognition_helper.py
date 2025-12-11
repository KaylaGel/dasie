#!/usr/bin/env python3

"""
Cross-platform speech recognition helper
Provides multiple methods for speech-to-text without PyAudio dependency
"""

import os
import sys
import subprocess
import tempfile
import json
import platform
from typing import Optional, Dict, Any
import requests
from loguru import logger

class SpeechRecognizer:
    """Cross-platform speech recognition without PyAudio"""
    
    def __init__(self):
        self.system = platform.system()
        self.recognition_methods = []
        
        # Check available recognition methods
        self._detect_available_methods()
        logger.info(f"Available recognition methods: {self.recognition_methods}")
    
    def _detect_available_methods(self):
        """Detect which speech recognition methods are available"""
        
        # Python speech_recognition library (best option if available)
        try:
            import speech_recognition as sr
            self.recognition_methods.append("python_speech_recognition")
        except ImportError:
            pass
        
        # macOS - built-in dictation
        if self.system == "Darwin":
            if self._check_command_exists("osascript"):
                self.recognition_methods.append("macos_dictation")
        
        # Windows - built-in speech recognition  
        elif self.system == "Windows":
            self.recognition_methods.append("windows_sapi")
        
        # Linux - try various options
        elif self.system == "Linux":
            if self._check_command_exists("arecord") and self._check_command_exists("sox"):
                self.recognition_methods.append("linux_recording")
        
        # Web-based recognition (cross-platform)
        self.recognition_methods.append("web_speech_api")
        
        # Fallback - text input
        self.recognition_methods.append("text_fallback")
    
    def _check_command_exists(self, command: str) -> bool:
        """Check if a system command exists"""
        try:
            subprocess.run([command, "--help"], 
                         capture_output=True, 
                         check=False, 
                         timeout=2)
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def listen(self, timeout: int = 10, prompt: str = "Speak now...") -> Optional[str]:
        """Listen for speech input using best available method
        
        Args:
            timeout: Maximum time to wait for speech
            prompt: Message to display to user
            
        Returns:
            Recognized text or None
        """
        logger.info(f"Listening for speech: {prompt}")
        
        for method in self.recognition_methods:
            try:
                result = self._try_recognition_method(method, timeout, prompt)
                if result:
                    logger.info(f"Speech recognized via {method}: '{result}'")
                    return result.strip().lower()
            except Exception as e:
                logger.warning(f"Recognition method {method} failed: {e}")
                continue
        
        logger.error("All speech recognition methods failed")
        return None
    
    def _try_recognition_method(self, method: str, timeout: int, prompt: str) -> Optional[str]:
        """Try a specific recognition method"""
        
        if method == "python_speech_recognition":
            return self._python_speech_recognition(timeout, prompt)
        elif method == "macos_dictation":
            return self._macos_dictation(timeout, prompt)
        elif method == "windows_sapi":
            return self._windows_sapi(timeout, prompt)
        elif method == "linux_recording":
            return self._linux_recording(timeout, prompt)
        elif method == "web_speech_api":
            return self._web_speech_api(timeout, prompt)
        elif method == "text_fallback":
            return self._text_fallback(prompt)
        else:
            return None
    
    def _python_speech_recognition(self, timeout: int, prompt: str) -> Optional[str]:
        """Use Python speech_recognition library"""
        try:
            import speech_recognition as sr
            
            print(f"\n🎤 {prompt}")
            print("Initializing microphone...")
            
            # Initialize recognizer and microphone
            recognizer = sr.Recognizer()
            microphone = sr.Microphone()
            
            # Adjust for ambient noise
            print("Calibrating for ambient noise...")
            with microphone as source:
                recognizer.adjust_for_ambient_noise(source, duration=1)
            
            print(f"🎤 Speak now for up to {timeout} seconds...")
            
            # Listen for audio
            with microphone as source:
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=timeout)
            
            print("🔄 Processing speech...")
            
            # Recognize speech using Google's free service
            text = recognizer.recognize_google(audio)
            
            print(f"✅ Recognized: '{text}'")
            return text.lower().strip()
            
        except sr.WaitTimeoutError:
            print("⚠️  Listening timeout - no speech detected")
            return None
        except sr.UnknownValueError:
            print("⚠️  Could not understand speech")
            return None
        except sr.RequestError as e:
            print(f"⚠️  Speech recognition service error: {e}")
            return None
        except ImportError:
            print("⚠️  speech_recognition library not available")
            return None
        except Exception as e:
            logger.warning(f"Python speech recognition failed: {e}")
            return None
    
    def _macos_dictation(self, timeout: int, prompt: str) -> Optional[str]:
        """Use macOS built-in dictation via AppleScript"""
        print(f"\n🎤 {prompt}")
        print("Starting speech recognition...")
        
        # Create a temporary text file to capture dictation
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # AppleScript to open TextEdit, dictate, and save
            applescript = f'''
            tell application "TextEdit"
                activate
                delay 0.5
                make new document
                delay 0.5
                
                -- Try to start dictation using the standard keyboard shortcut
                tell application "System Events"
                    -- Most common dictation shortcuts: Fn+Fn or Cmd+Space twice
                    key code 63  -- Fn key
                    delay 0.1
                    key code 63  -- Fn key again
                    delay 2
                    
                    -- If that doesn't work, try Cmd+Space twice
                    if false then
                        keystroke " " using command down
                        delay 0.1
                        keystroke " " using command down
                        delay 2
                    end if
                end tell
                
                delay {timeout}
                
                -- Get the text content
                set docText to text of front document
                
                -- Save to temporary file
                tell application "System Events"
                    set textFile to open for access POSIX file "{temp_path}" with write permission
                    write docText to textFile
                    close access textFile
                end tell
                
                -- Close the document without saving
                close front document saving no
            end tell
            '''
            
            print(f"🎤 Speak now for up to {timeout} seconds...")
            print("💡 You may need to manually start dictation if it doesn't auto-start")
            print("   Try pressing Fn+Fn or the configured dictation shortcut")
            
            result = subprocess.run(
                ["osascript", "-e", applescript],
                capture_output=True,
                text=True,
                timeout=timeout + 10
            )
            
            # Read the result from the temp file
            try:
                with open(temp_path, 'r') as f:
                    dictated_text = f.read().strip()
                
                if dictated_text and dictated_text != "":
                    print(f"✅ Captured: '{dictated_text}'")
                    return dictated_text
                else:
                    print("⚠️  No dictation captured")
                    
            except FileNotFoundError:
                print("⚠️  Dictation file not found")
            
        except subprocess.TimeoutExpired:
            print("⚠️  Dictation timed out")
        except Exception as e:
            logger.warning(f"macOS dictation failed: {e}")
            
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass
        
        # Fallback to text input
        print("🔄 Falling back to text input...")
        return input("Please type your command: ").strip()
    
    def _windows_sapi(self, timeout: int, prompt: str) -> Optional[str]:
        """Use Windows Speech API"""
        print(f"\n🎤 {prompt}")
        
        # PowerShell script for speech recognition
        ps_script = f'''
        Add-Type -AssemblyName System.Speech
        $recognizer = New-Object System.Speech.Recognition.SpeechRecognitionEngine
        $recognizer.SetInputToDefaultAudioDevice()
        
        $grammar = New-Object System.Speech.Recognition.DictationGrammar
        $recognizer.LoadGrammar($grammar)
        
        $recognizer.RecognizeTimeout = New-TimeSpan -Seconds {timeout}
        
        try {{
            $result = $recognizer.Recognize()
            if ($result) {{
                Write-Output $result.Text
            }} else {{
                Write-Output ""
            }}
        }} catch {{
            Write-Output ""
        }}
        
        $recognizer.Dispose()
        '''
        
        try:
            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=timeout + 5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            logger.warning("Windows speech recognition timed out")
        
        return None
    
    def _linux_recording(self, timeout: int, prompt: str) -> Optional[str]:
        """Record audio on Linux and use online STT service"""
        print(f"\n🎤 {prompt}")
        print(f"Recording for {timeout} seconds...")
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            audio_file = temp_file.name
        
        try:
            # Record audio using arecord
            subprocess.run([
                "arecord", 
                "-f", "cd",  # CD quality
                "-t", "wav",
                "-d", str(timeout),
                audio_file
            ], check=True, timeout=timeout + 5)
            
            # Convert to format suitable for web APIs using sox if available
            if self._check_command_exists("sox"):
                converted_file = audio_file + "_converted.wav"
                subprocess.run([
                    "sox", audio_file, "-r", "16000", "-c", "1", converted_file
                ], check=True)
                audio_file = converted_file
            
            # Use the audio file with web speech API
            return self._transcribe_audio_file(audio_file)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Audio recording failed: {e}")
            return None
        finally:
            # Clean up temp files
            try:
                os.unlink(audio_file)
                if os.path.exists(audio_file + "_converted.wav"):
                    os.unlink(audio_file + "_converted.wav")
            except:
                pass
    
    def _transcribe_audio_file(self, audio_file: str) -> Optional[str]:
        """Transcribe audio file using a web service"""
        # This would use a service like Google Cloud Speech-to-Text
        # For demo purposes, we'll simulate it
        logger.info(f"Would transcribe audio file: {audio_file}")
        print("⚠️  Audio transcription would require cloud STT service setup")
        print("Please type what you said:")
        return input("Your command: ").strip()
    
    def _web_speech_api(self, timeout: int, prompt: str) -> Optional[str]:
        """Use web-based speech recognition via JavaScript"""
        print(f"\n🎤 {prompt}")
        print("This would open a web page for speech recognition...")
        
        # Create a simple HTML page with Web Speech API
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>VoiceAlert Speech Input</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    text-align: center; 
                    padding: 50px;
                    background: #1a1a1a;
                    color: #fff;
                }}
                button {{
                    padding: 20px 40px;
                    font-size: 18px;
                    background: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    margin: 20px;
                }}
                button:hover {{ background: #45a049; }}
                #result {{
                    font-size: 24px;
                    margin: 30px;
                    padding: 20px;
                    background: #333;
                    border-radius: 5px;
                }}
                .recording {{ background: #f44336 !important; }}
            </style>
        </head>
        <body>
            <h1>🚨 VoiceAlert Voice Command</h1>
            <p>Click the button and speak your command</p>
            <button id="startBtn" onclick="startRecording()">🎤 Start Recording</button>
            <button onclick="submitResult()">✅ Submit Command</button>
            <div id="result">Ready to record...</div>
            
            <script>
                let recognition;
                let finalTranscript = '';
                
                if ('webkitSpeechRecognition' in window) {{
                    recognition = new webkitSpeechRecognition();
                }} else if ('SpeechRecognition' in window) {{
                    recognition = new SpeechRecognition();
                }} else {{
                    document.getElementById('result').textContent = 'Speech recognition not supported';
                }}
                
                if (recognition) {{
                    recognition.continuous = true;
                    recognition.interimResults = true;
                    
                    recognition.onstart = function() {{
                        document.getElementById('startBtn').textContent = '🛑 Stop Recording';
                        document.getElementById('startBtn').className = 'recording';
                        document.getElementById('result').textContent = 'Listening...';
                    }};
                    
                    recognition.onresult = function(event) {{
                        let interimTranscript = '';
                        
                        for (let i = event.resultIndex; i < event.results.length; i++) {{
                            if (event.results[i].isFinal) {{
                                finalTranscript += event.results[i][0].transcript;
                            }} else {{
                                interimTranscript += event.results[i][0].transcript;
                            }}
                        }}
                        
                        document.getElementById('result').textContent = 
                            finalTranscript + ' ' + interimTranscript;
                    }};
                    
                    recognition.onend = function() {{
                        document.getElementById('startBtn').textContent = '🎤 Start Recording';
                        document.getElementById('startBtn').className = '';
                    }};
                }}
                
                function startRecording() {{
                    if (recognition) {{
                        if (document.getElementById('startBtn').textContent.includes('Stop')) {{
                            recognition.stop();
                        }} else {{
                            finalTranscript = '';
                            recognition.start();
                        }}
                    }}
                }}
                
                function submitResult() {{
                    const result = document.getElementById('result').textContent;
                    if (result && result !== 'Ready to record...' && result !== 'Listening...') {{
                        alert('Command: ' + result);
                        // In real implementation, would send to Python backend
                        console.log('Voice command:', result);
                    }} else {{
                        alert('Please record a voice command first');
                    }}
                }}
            </script>
        </body>
        </html>
        '''
        
        # For now, fall back to text input
        print("💡 Web Speech API would be implemented with browser interface")
        return self._text_fallback(prompt)
    
    def _text_fallback(self, prompt: str) -> Optional[str]:
        """Fallback to text input"""
        print(f"\n💬 {prompt}")
        print("Using text input as fallback...")
        try:
            response = input("🎤 Enter your voice command: ").strip()
            return response if response else None
        except (KeyboardInterrupt, EOFError):
            return None

class EnhancedVoiceInterface:
    """Enhanced voice interface with real speech recognition"""
    
    def __init__(self):
        self.speech_recognizer = SpeechRecognizer()
        self.system = platform.system()
        logger.info("Enhanced voice interface initialized")
    
    def speak(self, text: str) -> bool:
        """Use system text-to-speech"""
        try:
            if self.system == "Darwin":  # macOS
                subprocess.run(["say", text], check=True)
            elif self.system == "Linux":
                if subprocess.run(["which", "espeak"], capture_output=True).returncode == 0:
                    subprocess.run(["espeak", text], check=True)
                elif subprocess.run(["which", "festival"], capture_output=True).returncode == 0:
                    subprocess.run(["echo", text, "|", "festival", "--tts"], shell=True, check=True)
                else:
                    print(f"🔊 SYSTEM: {text}")
            elif self.system == "Windows":
                ps_command = f'Add-Type -AssemblyName System.speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("{text}")'
                subprocess.run(["powershell", "-Command", ps_command], check=True)
            else:
                print(f"🔊 SYSTEM: {text}")
            
            return True
        except Exception as e:
            logger.warning(f"TTS failed: {e}")
            print(f"🔊 SYSTEM: {text}")
            return True
    
    def listen(self, timeout: int = 10, prompt: str = "Speak your command...") -> Optional[str]:
        """Listen for speech input"""
        return self.speech_recognizer.listen(timeout, prompt)
    
    def start_conversation(self, initial_message: str, command_callback) -> str:
        """Start voice conversation with real speech recognition"""
        print("\n" + "="*60)
        print("🚨 VOICE CONVERSATION WITH SPEECH RECOGNITION 🚨")
        print("="*60)
        
        # Speak initial message
        self.speak(initial_message)
        print(f"\nAlert Message:\n{initial_message}\n")
        
        attempts = 0
        max_attempts = 3
        
        while attempts < max_attempts:
            self.speak("What would you like to do?")
            
            # Listen for voice input
            response = self.listen(timeout=15, prompt="Waiting for your voice command...")
            
            if not response:
                attempts += 1
                if attempts < max_attempts:
                    self.speak("I didn't hear you clearly. Please try again.")
                    print("💡 Available commands: start patching, quarantine servers, acknowledge incident")
                else:
                    self.speak("No response received. Ending conversation.")
                    break
                continue
            
            # Process command
            logger.info(f"Processing voice command: {response}")
            result = command_callback(response)
            
            # Speak result
            self.speak(result)
            print(f"\n✅ Response: {result}\n")
            
            # Check if conversation should end
            if any(word in result.lower() for word in ["completed", "acknowledged", "successful"]):
                self.speak("Security response completed. Thank you.")
                break
            
            attempts = 0  # Reset on successful interaction
        
        print("="*60)
        print("🔒 VOICE CONVERSATION ENDED")
        print("="*60)
        
        return "Voice conversation completed"

def create_enhanced_voice_interface():
    """Create enhanced voice interface with speech recognition"""
    return EnhancedVoiceInterface()

if __name__ == "__main__":
    # Test speech recognition
    recognizer = SpeechRecognizer()
    
    print("Testing speech recognition...")
    result = recognizer.listen(timeout=10, prompt="Say 'hello world'")
    
    if result:
        print(f"You said: {result}")
    else:
        print("No speech detected")