from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class EnhancedRemoteDetector:
    def __init__(self):
        """Enhanced remote detector with company-specific rules"""
        self.remote_keywords = {
            'strict': [
                'remote', '100% remote', 'fully remote', 'distributed', 
                'work from anywhere', 'remote first', 'remote work', 
                'work remotely', 'location independent', 'global remote'
            ],
            'flexible': [
                'work from home', 'wfh', 'remote friendly', 'telecommute', 
                'virtual', 'home office', 'flexible location', 
                'hybrid remote', 'remote position', 'remote opportunity'
            ],
            'location_indicators': [
                'anywhere', 'worldwide', 'global', 'multiple locations',
                'various locations', 'location flexible', 'no location restriction'
            ]
        }
        
        # Companies with known remote policies
        self.company_flags = {
            'gitlab': 'always_remote',
            'automattic': 'always_remote',
            'zapier': 'always_remote',
            'buffer': 'always_remote',
            'toptal': 'always_remote',
            # Companies with significant remote programs
            'stripe': 'remote_friendly',
            'airbnb': 'remote_friendly',
            'spotify': 'remote_friendly',
            'delivery hero': 'remote_friendly',
            'deliveryhero': 'remote_friendly',
            'booking': 'remote_friendly',
            'postman': 'remote_friendly'
        }
    
    def is_remote_job(self, job_data: Dict[str, Any]) -> bool:
        """Enhanced remote job detection with better coverage"""
        
        company = str(job_data.get('company') or '').lower()
        title = str(job_data.get('title') or '').lower()
        description = str(job_data.get('description') or '').lower()
        location = str(job_data.get('location') or '').lower()
        
        # 1. Company-specific flags
        for company_key, flag in self.company_flags.items():
            if company_key in company:
                if flag == 'always_remote':
                    return True
                elif flag == 'remote_friendly':
                    # For remote-friendly companies, be more lenient
                    all_text = f"{title} {description} {location}"
                    if any(keyword in all_text for keyword in 
                           self.remote_keywords['strict'] + self.remote_keywords['flexible']):
                        return True
                    # Check for location flexibility
                    if any(indicator in all_text for indicator in self.remote_keywords['location_indicators']):
                        return True
        
        # 2. Strict remote keywords (definitive)
        all_text = f"{title} {description} {location}"
        for keyword in self.remote_keywords['strict']:
            if keyword in all_text:
                return True
        
        # 3. Multiple flexible keywords
        flexible_matches = sum(1 for keyword in self.remote_keywords['flexible'] 
                              if keyword in all_text)
        if flexible_matches >= 2:
            return True
        
        # 4. Location-based detection (enhanced)
        location_remote_indicators = [
            'remote', 'anywhere', 'worldwide', 'global', 'distributed',
            'work from home', 'virtual', 'multiple cities', 'various locations'
        ]
        if any(indicator in location for indicator in location_remote_indicators):
            return True
        
        # 5. Title contains remote (high confidence)
        if 'remote' in title or 'wfh' in title:
            return True
        
        # 6. Special patterns for job descriptions
        description_patterns = [
            'you can work from anywhere',
            'work from home',
            'distributed team',
            'location is flexible',
            'remote work',
            'work remotely'
        ]
        if any(pattern in description for pattern in description_patterns):
            return True
        
        return False