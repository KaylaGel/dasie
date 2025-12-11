#!/usr/bin/env python3

import os
import subprocess
import time
from typing import Dict, List, Callable, Optional
from datetime import datetime
from loguru import logger

class CommandEngine:
    """Handles voice command processing and execution"""
    
    def __init__(self, scripts_dir: str = "scripts"):
        self.scripts_dir = scripts_dir
        self.command_history = []
        
        # Whitelisted commands mapping
        self.command_whitelist = {
            "start patching": {
                "script": "scripts/patch_r2s.sh",
                "description": "Initiate automated patching process",
                "requires_confirmation": False
            },
            "quarantine servers": {
                "script": "scripts/isolate.sh", 
                "description": "Isolate affected systems",
                "requires_confirmation": True
            },
            "acknowledge incident": {
                "script": None,
                "description": "Log incident acknowledgment",
                "requires_confirmation": False
            },
            "emergency shutdown": {
                "script": "scripts/emergency_shutdown.sh",
                "description": "Emergency system shutdown",
                "requires_confirmation": True
            },
            "status report": {
                "script": "scripts/status_check.sh",
                "description": "Generate system status report", 
                "requires_confirmation": False
            }
        }
        
        # Ensure scripts directory exists
        os.makedirs(self.scripts_dir, exist_ok=True)
    
    def process_voice_command(self, command_text: str, cve_id: str = None) -> str:
        """Process a voice command and execute appropriate action
        
        Args:
            command_text: Transcribed voice command
            cve_id: Associated CVE ID for logging
            
        Returns:
            Response message for the caller
        """
        command_text = command_text.lower().strip()
        
        logger.info(f"Processing voice command: '{command_text}'")
        
        # Log the command
        self._log_command(command_text, cve_id)
        
        # Find matching command
        matched_command = self._match_command(command_text)
        
        if not matched_command:
            logger.warning(f"No matching command found for: '{command_text}'")
            return self._get_help_response()
        
        # Execute the command
        return self._execute_command(matched_command, command_text, cve_id)
    
    def _match_command(self, command_text: str) -> Optional[Dict]:
        """Find the best matching whitelisted command
        
        Args:
            command_text: Input command text
            
        Returns:
            Matching command configuration or None
        """
        # Direct match first
        for trigger, config in self.command_whitelist.items():
            if trigger in command_text:
                logger.info(f"Direct match found: '{trigger}'")
                return {"trigger": trigger, **config}
        
        # Fuzzy matching for common variations
        fuzzy_matches = {
            "patch": "start patching",
            "quarantine": "quarantine servers", 
            "isolate": "quarantine servers",
            "acknowledge": "acknowledge incident",
            "ack": "acknowledge incident",
            "shutdown": "emergency shutdown",
            "status": "status report",
            "report": "status report"
        }
        
        for keyword, trigger in fuzzy_matches.items():
            if keyword in command_text:
                config = self.command_whitelist[trigger]
                logger.info(f"Fuzzy match found: '{keyword}' -> '{trigger}'")
                return {"trigger": trigger, **config}
        
        return None
    
    def _execute_command(self, command_config: Dict, original_text: str, cve_id: str = None) -> str:
        """Execute a matched command
        
        Args:
            command_config: Command configuration
            original_text: Original voice command
            cve_id: Associated CVE ID
            
        Returns:
            Execution result message
        """
        trigger = command_config["trigger"]
        script_path = command_config.get("script")
        description = command_config.get("description", "Unknown command")
        
        logger.info(f"Executing command: {trigger}")
        
        try:
            if trigger == "acknowledge incident":
                return self._handle_acknowledgment(cve_id)
            
            elif script_path:
                return self._execute_script(script_path, trigger, cve_id)
            
            else:
                logger.warning(f"No handler defined for command: {trigger}")
                return f"Command '{trigger}' recognized but no action configured."
                
        except Exception as e:
            logger.error(f"Error executing command '{trigger}': {e}")
            return f"Failed to execute {trigger}. Error: {str(e)}"
    
    def _execute_script(self, script_path: str, command_name: str, cve_id: str = None) -> str:
        """Execute a shell script
        
        Args:
            script_path: Path to script file
            command_name: Human-readable command name
            cve_id: Associated CVE ID for context
            
        Returns:
            Execution result message
        """
        if not os.path.exists(script_path):
            logger.error(f"Script not found: {script_path}")
            return f"Script {script_path} not found. Please check configuration."
        
        if not os.access(script_path, os.X_OK):
            logger.error(f"Script not executable: {script_path}")
            return f"Script {script_path} is not executable."
        
        try:
            # Set environment variables for the script
            env = os.environ.copy()
            if cve_id:
                env["CVE_ID"] = cve_id
            env["TIMESTAMP"] = datetime.now().isoformat()
            
            logger.info(f"Executing script: {script_path}")
            
            result = subprocess.run(
                [script_path],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                env=env
            )
            
            if result.returncode == 0:
                logger.info(f"Script {script_path} executed successfully")
                return f"{command_name} completed successfully."
            else:
                logger.error(f"Script {script_path} failed with code {result.returncode}")
                logger.error(f"Error output: {result.stderr}")
                return f"{command_name} failed. Check logs for details."
                
        except subprocess.TimeoutExpired:
            logger.error(f"Script {script_path} timed out")
            return f"{command_name} timed out after 5 minutes."
        
        except Exception as e:
            logger.error(f"Error executing script {script_path}: {e}")
            return f"Error executing {command_name}: {str(e)}"
    
    def _handle_acknowledgment(self, cve_id: str = None) -> str:
        """Handle incident acknowledgment
        
        Args:
            cve_id: CVE ID being acknowledged
            
        Returns:
            Acknowledgment confirmation
        """
        timestamp = datetime.now().isoformat()
        
        # Log acknowledgment
        ack_message = f"Incident acknowledged at {timestamp}"
        if cve_id:
            ack_message += f" for {cve_id}"
        
        logger.info(ack_message)
        
        # Write to acknowledgment log
        ack_file = os.path.join("logs", "acknowledgments.log")
        os.makedirs("logs", exist_ok=True)
        
        try:
            with open(ack_file, "a") as f:
                f.write(f"{timestamp}: {ack_message}\n")
        except Exception as e:
            logger.error(f"Failed to write acknowledgment log: {e}")
        
        return "Incident acknowledged and logged."
    
    def _log_command(self, command_text: str, cve_id: str = None):
        """Log command for audit trail
        
        Args:
            command_text: Voice command text
            cve_id: Associated CVE ID
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command_text,
            "cve_id": cve_id,
            "source": "voice_command"
        }
        
        self.command_history.append(log_entry)
        logger.info(f"Command logged: {log_entry}")
    
    def _get_help_response(self) -> str:
        """Generate help response for unknown commands
        
        Returns:
            Help message listing available commands
        """
        available_commands = list(self.command_whitelist.keys())
        commands_text = "', '".join(available_commands)
        
        return f"Unknown command. Available commands: '{commands_text}'. Please try again."
    
    def get_command_history(self) -> List[Dict]:
        """Get command execution history
        
        Returns:
            List of command log entries
        """
        return self.command_history.copy()
    
    def add_custom_command(self, trigger: str, script_path: str, description: str = "Custom command"):
        """Add a custom command to the whitelist
        
        Args:
            trigger: Voice trigger phrase
            script_path: Path to script to execute
            description: Human-readable description
        """
        self.command_whitelist[trigger.lower()] = {
            "script": script_path,
            "description": description,
            "requires_confirmation": True  # Custom commands require confirmation by default
        }
        
        logger.info(f"Added custom command: '{trigger}' -> {script_path}")

if __name__ == "__main__":
    # Test the command engine
    engine = CommandEngine()
    
    test_commands = [
        "start patching now",
        "quarantine all servers",
        "acknowledge this incident", 
        "show status report",
        "invalid command here"
    ]
    
    for cmd in test_commands:
        print(f"\nCommand: '{cmd}'")
        response = engine.process_voice_command(cmd, "CVE-2025-55182")
        print(f"Response: {response}")
    
    print(f"\nCommand History:")
    for entry in engine.get_command_history():
        print(f"  {entry['timestamp']}: {entry['command']}")