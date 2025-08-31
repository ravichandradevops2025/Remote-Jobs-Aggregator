from typing import Dict, Any
import yaml
import os

class EnhancedRemoteDetector:
    def __init__(self):
        self.load_remote_config()
    
    def load_remote_config(self):
        """Load remote detection configuration"""
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'sources.yaml')
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                self.remote_keywords = config.get('remote_keywords', {})
                self.company_flags = config.get('company_remote_flags', {})
        except:
            # Fallback keywords
            self.remote_keywords = {
                'strict': ['remote', '100% remote', 'fully remote', 'distributed'],
                'flexible': ['work from home', 'wfh', 'remote friendly']
            }
            self.company_flags = {
                'gitlab': 'always_remote',
                'automattic': 'always_remote',
                'zapier': 'always_remote'
            }
    
    def is_remote_job(self, job_data: Dict[str, Any]) -> bool:
        """Enhanced remote job detection with company-specific rules"""
        
        company = job_data.get('company', '').lower()
        
        # 1. Check company-specific flags first
        if company in self.company_flags:
            if self.company_flags[company] == 'always_remote':
                return True
        
        # 2. Check for strict remote keywords (high confidence)
        text_to_check = self._get_searchable_text(job_data)
        
        # Strict keywords = definitely remote
        for keyword in self.remote_keywords.get('strict', []):
            if keyword.lower() in text_to_check:
                return True
        
        # 3. Check flexible keywords (medium confidence)
        flexible_matches = 0
        for keyword in self.remote_keywords.get('flexible', []):
            if keyword.lower() in text_to_check:
                flexible_matches += 1
        
        # If multiple flexible matches, likely remote
        if flexible_matches >= 2:
            return True
        
        # 4. Location-based detection
        location = job_data.get('location', '').lower()
        if location:
            remote_locations = [
                'remote', 'anywhere', 'worldwide', 'global', 
                'distributed', 'work from home', 'virtual'
            ]
            if any(loc in location for loc in remote_locations):
                return True
        
        # 5. Title-based detection (high weight)
        title = job_data.get('title', '').lower()
        if 'remote' in title:
            return True
        
        return False
    
    def _get_searchable_text(self, job_data: Dict[str, Any]) -> str:
        """Get all searchable text from job data"""
        text_fields = [
            job_data.get('title', ''),
            job_data.get('description', ''),
            job_data.get('location', ''),
            job_data.get('requirements', ''),  # If available
        ]
        return ' '.join(text_fields).lower()
    
    def get_remote_confidence(self, job_data: Dict[str, Any]) -> float:
        """Return confidence score (0-1) that job is remote"""
        text = self._get_searchable_text(job_data)
        company = job_data.get('company', '').lower()
        
        confidence = 0.0
        
        # Company flags
        if company in self.company_flags:
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
        location = job_data.get('location', '').lower()
        if 'remote' in location or 'anywhere' in location:
            confidence += 0.7
            
        return min(confidence, 1.0)