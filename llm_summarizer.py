#!/usr/bin/env python3

import os
from typing import Dict, Optional
from openai import OpenAI
from loguru import logger

class LLMSummarizer:
    """Handles LLM-based vulnerability summarization"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")
            
        self.client = OpenAI(api_key=self.api_key)
    
    def generate_summary(self, cve_info: Dict) -> str:
        """Generate a vulnerability summary for voice delivery
        
        Args:
            cve_info: Normalized CVE information dictionary
            
        Returns:
            Human-readable vulnerability summary
        """
        try:
            prompt = self._create_summary_prompt(cve_info)
            
            logger.info(f"Generating LLM summary for {cve_info.get('cve_id', 'unknown CVE')}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a cybersecurity expert explaining vulnerabilities to on-call engineers. Be concise, clear, and actionable. Focus on immediate threats and remediation steps."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            summary = response.choices[0].message.content.strip()
            logger.info(f"Generated summary of {len(summary)} characters")
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate LLM summary: {e}")
            return self._generate_fallback_summary(cve_info)
    
    def _create_summary_prompt(self, cve_info: Dict) -> str:
        """Create the LLM prompt for vulnerability summarization"""
        
        cve_id = cve_info.get('cve_id', 'Unknown')
        description = cve_info.get('description', 'No description available')
        severity = cve_info.get('severity', 'Unknown')
        cvss_score = cve_info.get('cvss_score', 0.0)
        affected_products = cve_info.get('affected_products', [])
        
        affected_text = ""
        if affected_products:
            affected_text = f"\nAffected products: {', '.join(affected_products[:5])}"
        
        prompt = f"""
Summarize the following vulnerability for an on-call engineer receiving an urgent phone call:

CVE ID: {cve_id}
Description: {description}
Severity: {severity}
CVSS Score: {cvss_score}{affected_text}

Focus on:
1. What the vulnerability is (in simple terms)
2. How attackers exploit it
3. Why it's dangerous to our systems
4. Evidence of active exploitation (if any)
5. Immediate remediation actions needed

Keep the response under 300 words and suitable for text-to-speech delivery. Be urgent but clear.
"""
        return prompt
    
    def _generate_fallback_summary(self, cve_info: Dict) -> str:
        """Generate a basic summary when LLM fails"""
        
        cve_id = cve_info.get('cve_id', 'Unknown CVE')
        description = cve_info.get('description', 'No description available')[:200]
        severity = cve_info.get('severity', 'Unknown')
        
        return f"""
SECURITY ALERT: {cve_id}

Vulnerability Description: {description}

Severity Level: {severity}

This is an automated alert. A new vulnerability has been detected that may affect your systems. 

Immediate Actions Required:
1. Review the vulnerability details
2. Check if your systems are affected  
3. Apply patches if available
4. Consider isolating affected systems

Please respond with voice commands to take action or escalate to your security team.
"""

    def generate_voice_script(self, summary: str, cve_id: str) -> str:
        """Generate a voice script optimized for phone delivery
        
        Args:
            summary: Vulnerability summary
            cve_id: CVE identifier
            
        Returns:
            Voice-optimized script
        """
        script = f"""
Security Alert! This is an urgent notification about vulnerability {cve_id}.

{summary}

You can respond with the following voice commands:
- Say "start patching" to begin automatic patching
- Say "quarantine servers" to isolate affected systems  
- Say "acknowledge incident" to log acknowledgment

What would you like to do?
"""
        return script.strip()

if __name__ == "__main__":
    # Test the summarizer
    test_cve = {
        "cve_id": "CVE-2025-55182",
        "description": "Remote code execution vulnerability in web framework allowing unauthenticated attackers to execute arbitrary commands",
        "severity": "Critical",
        "cvss_score": 9.8,
        "affected_products": ["WebFramework 2.0", "WebFramework 1.9"]
    }
    
    # Only test if API key is available
    if os.getenv("OPENAI_API_KEY"):
        summarizer = LLMSummarizer()
        summary = summarizer.generate_summary(test_cve)
        print("Generated Summary:")
        print(summary)
        print("\nVoice Script:")
        print(summarizer.generate_voice_script(summary, test_cve["cve_id"]))
    else:
        print("No OpenAI API key found, testing fallback summary:")
        summarizer = LLMSummarizer(api_key="dummy")
        summary = summarizer._generate_fallback_summary(test_cve)
        print(summary)