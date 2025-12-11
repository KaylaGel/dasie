# Zero-Day VoiceAlert System

An automated defensive security system that monitors for new CVE vulnerabilities and places voice calls to on-call engineers with summaries and interactive voice commands.

## Overview

The VoiceAlert System continuously monitors CVE feeds, generates AI-powered vulnerability summaries, and uses voice calls to alert engineers about critical vulnerabilities affecting their systems.

### Key Features

- **Automated CVE Monitoring**: Uses CVELib CLI to scan for new vulnerabilities
- **AI-Powered Summarization**: Leverages OpenAI GPT to generate human-readable vulnerability summaries
- **Voice Notifications**: Uses ElevenLabs TTS with microphone interface for local testing, or phone calls for production
- **Interactive Commands**: Accepts voice commands via microphone with speech recognition
- **Defensive Actions**: Automated patching, system isolation, and emergency shutdown capabilities

## Architecture

```
CVELib Scanner → CVE Parser → LLM Summarizer → Voice Caller → Command Engine
     ↓              ↓            ↓              ↓           ↓
 New CVEs    →  Normalized  →  Summary    →   Phone    →  Actions
                   Data                        Call
```

## Installation

### Option 1: Automatic Installation (Recommended)
```bash
python install_dependencies.py
```

### Option 2: Manual Installation

**For full audio support:**
```bash
# macOS users: Install PortAudio first
brew install portaudio

# Install all dependencies
pip install -r requirements.txt
```

**For minimal installation (text-based testing):**
```bash
pip install -r requirements_minimal.txt
```

### Additional Setup

1. **Install CVELib**:
```bash
# Follow CVELib installation instructions from their documentation
```

2. **Configure Environment**:
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

3. **Set Up Scripts**:
```bash
chmod +x scripts/*.sh
# Review and customize scripts for your environment
```

### Troubleshooting Installation

**PyAudio Issues:**
- **macOS**: `brew install portaudio` then `pip install PyAudio`
- **Ubuntu**: `sudo apt-get install portaudio19-dev` then `pip install PyAudio`
- **Windows**: Try `pip install PyAudio` or download wheel from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/)
- **Fallback**: Use `USE_MOCK_VOICE=true` or the simple voice interface

**Audio Dependencies Not Working:**
- Use minimal requirements: `pip install -r requirements_minimal.txt`
- Set `USE_MOCK_VOICE=true` in your `.env` file
- System will automatically fall back to text-based interaction

## Configuration

### Required Environment Variables

```bash
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Contact Information  
ENGINEER_PHONE_NUMBER=+1234567890
VOICE_ID=your_elevenlabs_voice_id

# System Settings
POLL_INTERVAL_MINUTES=5
LOG_LEVEL=INFO
```

### Optional Configuration

```bash
# LLM Settings
LLM_MODEL=gpt-4
LLM_MAX_TOKENS=500
LLM_TEMPERATURE=0.3

# Security Settings
MAX_CALL_DURATION=300
COMMAND_TIMEOUT=300
ENABLE_EMERGENCY_SHUTDOWN=false

# Testing
USE_MOCK_VOICE=true
TARGET_CVE=CVE-2025-55182
```

## Usage

### Production Mode
```bash
python voicealert_system.py
```

### Test Mode
```bash
python voicealert_system.py --test
```

### Component Testing
```bash
# Test CVE scanner
python cve_scanner.py

# Test LLM summarizer
python llm_summarizer.py

# Test voice caller
python voice_caller.py

# Test command engine
python command_engine.py
```

## Voice Commands

The system accepts the following voice commands during alert calls:

- **"start patching"** - Initiates automated patching process
- **"quarantine servers"** - Isolates affected systems  
- **"acknowledge incident"** - Logs incident acknowledgment
- **"emergency shutdown"** - Performs emergency system shutdown
- **"status report"** - Generates comprehensive system status

## System Flow

1. **CVE Monitoring**: System polls CVELib every 5 minutes for new vulnerabilities
2. **Vulnerability Detection**: When CVE-2025-55182 (or other target CVE) is detected:
   - System assumes engineer's systems are affected
   - CVE data is parsed and normalized
3. **Summary Generation**: LLM creates human-readable vulnerability summary
4. **Voice Alert**: System places phone call to engineer with:
   - Vulnerability description
   - Exploit mechanism and impact
   - Immediate remediation recommendations
5. **Interactive Response**: Engineer can respond with voice commands
6. **Action Execution**: System executes whitelisted defensive actions

## Scripts

### Patching Script (`scripts/patch_r2s.sh`)
- Updates package lists
- Applies security updates
- Restarts critical services
- Creates backup and generates report

### Isolation Script (`scripts/isolate.sh`)
- Implements network isolation rules
- Stops non-essential services
- Monitors for suspicious processes
- Provides restoration instructions

### Emergency Shutdown (`scripts/emergency_shutdown.sh`)
- Notifies all users
- Gracefully stops critical services
- Performs controlled system shutdown

### Status Check (`scripts/status_check.sh`)
- Generates comprehensive system status
- Monitors resource usage
- Checks security indicators
- Provides recommendations

## Security Considerations

### Defensive Use Only
This system is designed for **defensive security purposes only**:
- Automated vulnerability response
- System protection and isolation
- Emergency incident response
- Security monitoring and alerting

### Safety Features
- Command whitelisting prevents unauthorized actions
- Confirmation required for destructive operations
- Comprehensive logging and audit trails
- Graceful degradation for missing dependencies

### Best Practices
- Run with least privilege necessary
- Regularly review and test response scripts
- Monitor system logs for unusual activity
- Keep API keys secure and rotate regularly

## Troubleshooting

### Common Issues

1. **CVELib Not Found**
   - Install CVELib CLI tool
   - Ensure it's in system PATH

2. **API Key Errors**
   - Verify OpenAI and ElevenLabs API keys
   - Check API rate limits and quotas

3. **Voice Call Failures**
   - Verify phone number format
   - Check ElevenLabs account status
   - Use mock mode for testing

4. **Script Execution Errors**
   - Ensure scripts have execute permissions
   - Check script dependencies
   - Review system logs

### Debug Mode
```bash
LOG_LEVEL=DEBUG python voicealert_system.py
```

### Mock Mode
```bash
USE_MOCK_VOICE=true python voicealert_system.py --test
```

## Logging

System logs are stored in:
- `logs/voicealert_YYYY-MM-DD.log` - Main system logs
- `logs/acknowledgments.log` - Incident acknowledgments
- `/tmp/voicealert_*` - Script execution logs

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review system logs
3. Test individual components
4. Verify configuration settings

## License

This software is provided for defensive security purposes only.
Unauthorized use for malicious activities is prohibited.