#!/usr/bin/env python3

import os
import time
import signal
import threading
from typing import Optional, Dict
from dotenv import load_dotenv
from loguru import logger

from cve_scanner import CVEScanner
from llm_summarizer import LLMSummarizer
from voice_caller import VoiceCaller, create_voice_caller
from voice_interface import VoiceInterface, create_voice_interface
from command_engine import CommandEngine

class VoiceAlertSystem:
    """Main orchestration system for Zero-Day VoiceAlert"""
    
    def __init__(self, config_file: str = ".env"):
        # Load environment configuration
        load_dotenv(config_file)
        
        self.running = False
        self.poll_interval = int(os.getenv("POLL_INTERVAL_MINUTES", 5)) * 60
        self.engineer_phone = os.getenv("ENGINEER_PHONE_NUMBER")
        self.use_mock_voice = os.getenv("USE_MOCK_VOICE", "false").lower() == "true"
        self.use_microphone = os.getenv("USE_MICROPHONE", "true").lower() == "true"
        
        # Initialize components
        self.scanner = CVEScanner(poll_interval_minutes=self.poll_interval // 60)
        self.summarizer = LLMSummarizer()
        self.command_engine = CommandEngine()
        
        # Initialize voice interface (microphone or phone)
        if self.use_microphone:
            self.voice_interface = create_voice_interface(use_mock=self.use_mock_voice)
            logger.info("Using microphone-based voice interface")
        else:
            self.voice_caller = create_voice_caller(use_mock=self.use_mock_voice)
            logger.info("Using phone-based voice caller")
        
        # Setup logging
        log_level = os.getenv("LOG_LEVEL", "INFO")
        logger.remove()
        logger.add("logs/voicealert_{time:YYYY-MM-DD}.log", level=log_level, rotation="1 day")
        logger.add(lambda msg: print(msg, end=""), level=log_level)
        
        # Validate configuration
        self._validate_config()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("VoiceAlert System initialized")
    
    def _validate_config(self):
        """Validate system configuration"""
        if not self.use_microphone and not self.engineer_phone:
            logger.warning("ENGINEER_PHONE_NUMBER not configured and not using microphone")
        
        if not os.getenv("OPENAI_API_KEY"):
            logger.warning("OPENAI_API_KEY not found, LLM features may not work")
        
        if not os.getenv("ELEVENLABS_API_KEY") and not self.use_mock_voice:
            logger.warning("ELEVENLABS_API_KEY not found, using mock voice interface")
    
    def start(self):
        """Start the main monitoring loop"""
        logger.info("Starting VoiceAlert System")
        logger.info(f"Poll interval: {self.poll_interval} seconds")
        if self.use_microphone:
            logger.info("Voice mode: Microphone interface")
        else:
            logger.info(f"Voice mode: Phone calls to {self.engineer_phone}")
        
        self.running = True
        
        try:
            self._main_loop()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the monitoring system"""
        logger.info("Stopping VoiceAlert System")
        self.running = False
    
    def _main_loop(self):
        """Main monitoring and alert loop"""
        while self.running:
            try:
                logger.info("Scanning for new vulnerabilities...")
                
                # Scan for new CVEs
                new_cves = self.scanner.fetch_new_cves()
                
                if not new_cves:
                    logger.info("No new CVEs found")
                    time.sleep(self.poll_interval)
                    continue
                
                # Process each CVE
                for cve_raw in new_cves:
                    if not self.running:
                        break
                        
                    self._process_vulnerability(cve_raw)
                
                # Wait before next scan
                if self.running:
                    logger.info(f"Waiting {self.poll_interval} seconds until next scan...")
                    time.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def _process_vulnerability(self, cve_raw: Dict):
        """Process a single vulnerability detection
        
        Args:
            cve_raw: Raw CVE data from scanner
        """
        try:
            # Extract and normalize CVE information
            cve_info = self.scanner.extract_cve_info(cve_raw)
            cve_id = cve_info["cve_id"]
            
            logger.info(f"Processing vulnerability: {cve_id}")
            
            # Check if system is affected (always True per requirements)
            if not self.scanner.is_affected_system(cve_info):
                logger.info(f"System not affected by {cve_id}, skipping")
                return
            
            logger.warning(f"CRITICAL: System affected by {cve_id}")
            
            # Generate vulnerability summary
            summary = self.summarizer.generate_summary(cve_info)
            
            # Create voice script
            voice_script = self.summarizer.generate_voice_script(summary, cve_id)
            
            # Setup command handler for this CVE
            command_callback = lambda cmd: self.command_engine.process_voice_command(cmd, cve_id)
            
            # Send alert via appropriate interface
            if self.use_microphone:
                # Use microphone interface
                logger.info(f"Starting voice conversation for {cve_id}")
                result = self.voice_interface.start_conversation(voice_script, command_callback)
                logger.info(f"Voice conversation completed for {cve_id}: {result}")
            else:
                # Use phone caller (legacy)
                call_id = self.voice_caller.place_call(
                    phone_number=self.engineer_phone,
                    script=voice_script,
                    command_callback=command_callback
                )
                
                if call_id:
                    logger.info(f"Alert call placed for {cve_id}, call ID: {call_id}")
                    self._monitor_call(call_id, cve_id)
                else:
                    logger.error(f"Failed to place alert call for {cve_id}")
            
        except Exception as e:
            logger.error(f"Error processing vulnerability: {e}")
    
    def _monitor_call(self, call_id: str, cve_id: str, timeout: int = 300):
        """Monitor an active call for responses
        
        Args:
            call_id: Active call identifier  
            cve_id: Associated CVE ID
            timeout: Maximum time to monitor call
        """
        start_time = time.time()
        
        logger.info(f"Monitoring call {call_id} for {cve_id}")
        
        # In a real implementation, this would monitor webhooks or poll call status
        # For now, we'll simulate monitoring
        while time.time() - start_time < timeout:
            if not self.running:
                break
                
            call_status = self.voice_caller.get_call_status(call_id)
            
            if call_status and call_status.get("status") == "ended":
                logger.info(f"Call {call_id} ended")
                break
            
            time.sleep(10)  # Check every 10 seconds
        
        # Cleanup
        if hasattr(self, 'voice_caller'):
            self.voice_caller.end_call(call_id)
    
    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
    
    def process_single_cve(self, cve_id: str = "CVE-2025-55182"):
        """Process a single CVE for testing purposes
        
        Args:
            cve_id: CVE identifier to process
        """
        logger.info(f"Processing single CVE: {cve_id}")
        
        # Create mock CVE data for testing
        mock_cve = {
            "cve_id": cve_id,
            "description": "Remote code execution vulnerability in web framework allowing unauthenticated attackers to execute arbitrary commands via crafted HTTP requests",
            "severity": "Critical",
            "cvss_score": 9.8,
            "published_date": "2025-01-15T10:00:00Z",
            "affected_products": ["WebFramework 2.0", "WebFramework 1.9"],
            "references": ["https://example.com/advisory"]
        }
        
        self._process_vulnerability(mock_cve)
    
    def get_system_status(self) -> Dict:
        """Get current system status
        
        Returns:
            System status information
        """
        return {
            "running": self.running,
            "poll_interval": self.poll_interval,
            "engineer_phone": self.engineer_phone,
            "components": {
                "scanner": "operational",
                "summarizer": "operational", 
                "voice_caller": "operational" if not self.use_mock_voice else "mock",
                "command_engine": "operational"
            },
            "command_history": self.command_engine.get_command_history()
        }

def main():
    """Main entry point"""
    try:
        system = VoiceAlertSystem()
        
        # Check if we should run in test mode
        if len(os.sys.argv) > 1 and os.sys.argv[1] == "--test":
            logger.info("Running in test mode")
            system.process_single_cve()
        else:
            logger.info("Starting continuous monitoring")
            system.start()
            
    except Exception as e:
        logger.error(f"Failed to start VoiceAlert System: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())