from typing import Optional, Dict, Any
from .greenhouse import GreenHouseScraper
from .lever import LeverScraper

try:
    from .workday import WorkdayScraper
    WORKDAY_AVAILABLE = True
except ImportError:
    WORKDAY_AVAILABLE = False

try:
    from .smartrecruiters import SmartRecruiterscraper
    SMARTRECRUITERS_AVAILABLE = True
except ImportError:
    SMARTRECRUITERS_AVAILABLE = False

class ATSScraperFactory:
    """Factory to create appropriate ATS scrapers"""
    
    @staticmethod
    def create_scraper(ats_type: str, company_slug: str, company_name: str, **kwargs):
        """Create scraper based on ATS type"""
        
        ats_type = ats_type.lower()
        
        if ats_type == 'greenhouse':
            return GreenHouseScraper(company_slug, company_name, **kwargs)
        
        elif ats_type == 'lever':
            return LeverScraper(company_slug, company_name, **kwargs)
        
        elif ats_type == 'workday' and WORKDAY_AVAILABLE:
            return WorkdayScraper(company_slug, company_name, **kwargs)
        
        elif ats_type == 'smartrecruiters' and SMARTRECRUITERS_AVAILABLE:
            return SmartRecruiterscraper(company_slug, company_name, **kwargs)
        
        else:
            raise ValueError(f"Unsupported ATS type: {ats_type}")
    
    @staticmethod
    def get_supported_platforms() -> Dict[str, bool]:
        """Get list of supported ATS platforms"""
        return {
            'greenhouse': True,
            'lever': True,
            'workday': WORKDAY_AVAILABLE,
            'smartrecruiters': SMARTRECRUITERS_AVAILABLE,
        }
    
    @staticmethod
    def detect_ats_from_url(url: str) -> Optional[str]:
        """Try to detect ATS platform from URL"""
        url_lower = url.lower()
        
        if 'greenhouse.io' in url_lower:
            return 'greenhouse'
        elif 'lever.co' in url_lower:
            return 'lever'
        elif 'myworkdayjobs.com' in url_lower:
            return 'workday'
        elif 'smartrecruiters.com' in url_lower:
            return 'smartrecruiters'
        else:
            return None