#!/usr/bin/env python3

import os
from typing import Dict, Any
from dotenv import load_dotenv

class VoiceAlertConfig:
    """Configuration management for VoiceAlert System"""
    
    def __init__(self, config_file: str = ".env"):
        load_dotenv(config_file)
        self._config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        return {
            # API Keys
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "elevenlabs_api_key": os.getenv("ELEVENLABS_API_KEY"),
            
            # Voice Settings
            "engineer_phone": os.getenv("ENGINEER_PHONE_NUMBER"),
            "voice_id": os.getenv("VOICE_ID"),
            "use_mock_voice": os.getenv("USE_MOCK_VOICE", "false").lower() == "true",
            
            # Scanning Settings
            "poll_interval_minutes": int(os.getenv("POLL_INTERVAL_MINUTES", 5)),
            "target_cve": os.getenv("TARGET_CVE", "CVE-2025-55182"),
            "cve_scan_timeout": int(os.getenv("CVE_SCAN_TIMEOUT", 60)),
            
            # LLM Settings
            "llm_model": os.getenv("LLM_MODEL", "gpt-4"),
            "llm_max_tokens": int(os.getenv("LLM_MAX_TOKENS", 500)),
            "llm_temperature": float(os.getenv("LLM_TEMPERATURE", 0.3)),
            
            # System Settings
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "scripts_dir": os.getenv("SCRIPTS_DIR", "scripts"),
            "logs_dir": os.getenv("LOGS_DIR", "logs"),
            
            # Security Settings
            "max_call_duration": int(os.getenv("MAX_CALL_DURATION", 300)),
            "command_timeout": int(os.getenv("COMMAND_TIMEOUT", 300)),
            "enable_emergency_shutdown": os.getenv("ENABLE_EMERGENCY_SHUTDOWN", "false").lower() == "true",
            
            # Monitoring Settings
            "health_check_interval": int(os.getenv("HEALTH_CHECK_INTERVAL", 30)),
            "webhook_url": os.getenv("WEBHOOK_URL"),
        }
    
    def _validate_config(self):
        """Validate critical configuration values"""
        required_for_production = [
            "engineer_phone",
            "openai_api_key",
        ]
        
        missing = []
        for key in required_for_production:
            if not self._config.get(key):
                missing.append(key.upper())
        
        if missing:
            print(f"WARNING: Missing configuration for production use: {', '.join(missing)}")
            print("System will run in mock/test mode")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self._config.get(key, default)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values (excluding sensitive data)"""
        config_copy = self._config.copy()
        
        # Mask sensitive values
        sensitive_keys = ["openai_api_key", "elevenlabs_api_key"]
        for key in sensitive_keys:
            if config_copy.get(key):
                config_copy[key] = "***MASKED***"
        
        return config_copy
    
    def is_production_ready(self) -> bool:
        """Check if configuration is ready for production use"""
        required = ["engineer_phone", "openai_api_key"]
        return all(self._config.get(key) for key in required)

# Global config instance
config = VoiceAlertConfig()