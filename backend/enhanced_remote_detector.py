# Create the enhanced remote detector file
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class EnhancedRemoteDetector:
    def __init__(self):
        """Initialize enhanced remote detector with fallback keywords"""
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
        """Enhanced remote job detection - SAFE from None values"""
        
        # Safely get company name
        company = str(job_data.get('company') or '').lower()
        
        # 1. Check company-specific flags first
        for company_key, flag in self.company_flags.items():
            if company_key in company and flag == 'always_remote':
                return True
        
        # 2. Get searchable text safely
        text_to_check = self._get_searchable_text_safe(job_data)
        
        # 3. Check for strict remote keywords
        for keyword in self.remote_keywords.get('strict', []):
            if keyword.lower() in text_to_check:
                return True
        
        # 4. Check flexible keywords (need multiple matches)
        flexible_matches = 0
        for keyword in self.remote_keywords.get('flexible', []):
            if keyword.lower() in text_to_check:
                flexible_matches += 1
        
        if flexible_matches >= 2:
            return True
        
        # 5. Location-based detection
        location = str(job_data.get('location') or '').lower()
        if location:
            remote_locations = ['remote', 'anywhere', 'worldwide', 'global', 'distributed']
            if any(loc in location for loc in remote_locations):
                return True
        
        # 6. Title-based detection
        title = str(job_data.get('title') or '').lower()
        if 'remote' in title:
            return True
        
        return False
    
    def _get_searchable_text_safe(self, job_data: Dict[str, Any]) -> str:
        """Get searchable text safely handling None values"""
        text_parts = []
        
        for field in ['title', 'description', 'location']:
            value = job_data.get(field)
            if value is not None:
                text_parts.append(str(value))
        
        return ' '.join(text_parts).lower()