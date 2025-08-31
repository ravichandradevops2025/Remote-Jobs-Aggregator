from typing import Dict, Any
import yaml
import os
import logging

logger = logging.getLogger(__name__)

class EnhancedRemoteDetector:
    def __init__(self):
        self.load_remote_config()
    
    def load_remote_config(self):
        """Load remote detection configuration"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'sources.yaml')
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                self.remote_keywords = config.get('remote_keywords', {})
                self.company_flags = config.get('company_remote_flags', {})
        except Exception as e:
            logger.warning(f"Could not load sources.yaml: {e}")
            # Fallback keywords
            self.remote_keywords = {
                'strict': ['remote', '100% remote', 'fully remote', 'distributed', 'work from anywhere'],
                'flexible': ['work from home', 'wfh', 'remote friendly', 'telecommute', 'virtual']
            }
            self.company_flags = {
                'gitlab': 'always_remote',
                'automattic': 'always_remote',
                'zapier': 'always_remote',
                'buffer': 'always_remote'
            }
    
    def is_remote_job(self, job_data: Dict[str, Any]) -> bool:
        """Enhanced remote job detection with company-specific rules - FIXED"""
        
        company = str(job_data.get('company', '')).lower()
        
        # 1. Check company-specific flags first
        for company_key, flag in self.company_flags.items():
            if company_key in company and flag == 'always_remote':
                return True
        
        # 2. Get searchable text - FIX: Handle None values
        text_to_check = self._get_searchable_text_safe(job_data)
        
        # 3. Check for strict remote keywords (high confidence)
        for keyword in self.remote_keywords.get('strict', []):
            if keyword.lower() in text_to_check:
                return True
        
        # 4. Check flexible keywords (need multiple matches)
        flexible_matches = 0
        for keyword in self.remote_keywords.get('flexible', []):
            if keyword.lower() in text_to_check:
                flexible_matches += 1
        
        # If multiple flexible matches, likely remote
        if flexible_matches >= 2:
            return True
        
        # 5. Location-based detection
        location = str(job_data.get('location', '')).lower()
        if location:
            remote_locations = [
                'remote', 'anywhere', 'worldwide', 'global', 
                'distributed', 'work from home', 'virtual'
            ]
            if any(loc in location for loc in remote_locations):
                return True
        
        # 6. Title-based detection (high weight)
        title = str(job_data.get('title', '')).lower()
        if 'remote' in title:
            return True
        
        return False
    
    def _get_searchable_text_safe(self, job_data: Dict[str, Any]) -> str:
        """Get all searchable text from job data - SAFE from None values"""
        text_fields = []
        
        # Safely convert all fields to strings
        for field in ['title', 'description', 'location']:
            value = job_data.get(field)
            if value is not None:
                text_fields.append(str(value))
            else:
                text_fields.append('')
        
        return ' '.join(text_fields).lower()
    
    def get_remote_confidence(self, job_data: Dict[str, Any]) -> float:
        """Return confidence score (0-1) that job is remote"""
        text = self._get_searchable_text_safe(job_data)
        company = str(job_data.get('company', '')).lower()
        
        confidence = 0.0
        
        # Company flags
        for company_key, flag in self.company_flags.items():
            if company_key in company and flag == 'always_remote':
                confidence += 0.9
        
        # Strict keywords  
        for keyword in self.remote_keywords.get('strict', []):
            if keyword.lower() in text:
                confidence += 0.8
                
        # Flexible keywords
        for keyword in self.remote_keywords.get('flexible', []):
            if keyword.lower() in text:
                confidence += 0.3
        
        # Location indicators
        location = str(job_data.get('location', '')).lower()
        if 'remote' in location or 'anywhere' in location:
            confidence += 0.7
            
        return min(confidence, 1.0)