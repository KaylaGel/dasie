#!/usr/bin/env python3

import subprocess
import json
import time
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger

class CVEScanner:
    """Handles CVE scanning using CVELib CLI"""
    
    def __init__(self, poll_interval_minutes: int = 5):
        self.poll_interval = poll_interval_minutes * 60
        
    def fetch_new_cves(self, since_minutes: int = None) -> List[Dict]:
        """Fetch new CVEs using CVELib CLI
        
        Args:
            since_minutes: How far back to look for new CVEs
            
        Returns:
            List of CVE dictionaries
        """
        try:
            if since_minutes is None:
                since_minutes = self.poll_interval // 60
                
            cmd = ["cve", "search", "--new", f"--since", f"{since_minutes}m", "--format", "json"]
            logger.info(f"Running CVELib command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                logger.error(f"CVELib command failed: {result.stderr}")
                return []
                
            if not result.stdout.strip():
                logger.info("No new CVEs found")
                return []
                
            # Parse JSON output
            cves = json.loads(result.stdout)
            logger.info(f"Found {len(cves)} new CVEs")
            
            return cves if isinstance(cves, list) else [cves]
            
        except subprocess.TimeoutExpired:
            logger.error("CVELib command timed out")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse CVELib JSON output: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in CVE scanning: {e}")
            return []
    
    def get_target_cve(self, cves: List[Dict], target_id: str = "CVE-2025-55182") -> Optional[Dict]:
        """Find a specific CVE by ID
        
        Args:
            cves: List of CVE dictionaries
            target_id: CVE ID to search for
            
        Returns:
            CVE dictionary if found, None otherwise
        """
        for cve in cves:
            if cve.get("cve_id") == target_id or cve.get("id") == target_id:
                logger.info(f"Found target CVE: {target_id}")
                return cve
        
        logger.warning(f"Target CVE {target_id} not found in results")
        return None
    
    def is_affected_system(self, cve: Dict) -> bool:
        """Determine if the current system is affected by the CVE
        
        For this implementation, always returns True as per requirements.
        In production, this would check SBOM, software inventory, etc.
        
        Args:
            cve: CVE dictionary
            
        Returns:
            True if system is affected
        """
        # Per PRD: "System assumes the engineer is affected by the vulnerability"
        logger.info(f"Assuming system is affected by {cve.get('cve_id', 'unknown CVE')}")
        return True
    
    def extract_cve_info(self, cve: Dict) -> Dict:
        """Extract key information from CVE dictionary
        
        Args:
            cve: Raw CVE dictionary from CVELib
            
        Returns:
            Normalized CVE information
        """
        return {
            "cve_id": cve.get("cve_id") or cve.get("id", "Unknown"),
            "description": cve.get("description", "No description available"),
            "severity": self._extract_severity(cve),
            "published_date": cve.get("published_date") or cve.get("publishedDate"),
            "cvss_score": self._extract_cvss_score(cve),
            "references": cve.get("references", []),
            "affected_products": cve.get("affected_products", []),
            "raw_data": cve
        }
    
    def _extract_severity(self, cve: Dict) -> str:
        """Extract severity from various possible fields"""
        severity_fields = ["severity", "impact", "cvss_severity"]
        for field in severity_fields:
            if field in cve:
                value = cve[field]
                if isinstance(value, dict):
                    return value.get("baseScore", "Unknown")
                return str(value)
        return "Unknown"
    
    def _extract_cvss_score(self, cve: Dict) -> float:
        """Extract CVSS score from various possible fields"""
        cvss_fields = ["cvss_score", "cvss", "impact"]
        for field in cvss_fields:
            if field in cve:
                value = cve[field]
                if isinstance(value, (int, float)):
                    return float(value)
                if isinstance(value, dict):
                    score = value.get("baseScore") or value.get("cvss_score")
                    if score:
                        return float(score)
        return 0.0

if __name__ == "__main__":
    # Test the scanner
    scanner = CVEScanner()
    cves = scanner.fetch_new_cves(since_minutes=60)
    
    if cves:
        print(f"Found {len(cves)} CVEs")
        for cve in cves[:3]:  # Show first 3
            info = scanner.extract_cve_info(cve)
            print(f"- {info['cve_id']}: {info['description'][:100]}...")
    else:
        print("No CVEs found")