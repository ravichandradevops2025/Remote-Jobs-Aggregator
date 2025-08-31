from typing import List, Dict, Any
from .base import BaseScraper
import uuid
import logging

logger = logging.getLogger(__name__)

class LeverScraper(BaseScraper):
    def __init__(self, company_slug: str, company_name: str, **kwargs):
        super().__init__(**kwargs)
        self.company_slug = company_slug
        self.company_name = company_name
        self.base_url = f"https://api.lever.co/v0/postings/{company_slug}"
    
    async def scrape_jobs(self) -> List[Dict[str, Any]]:
        logger.info(f"Scraping Lever jobs for {self.company_name}")
        
        response = await self.fetch_url(self.base_url)
        if not response or not isinstance(response, list):
            logger.warning(f"No jobs found for {self.company_name} on Lever")
            return []
        
        jobs = []
        for job_data in response:
            try:
                job = self._parse_lever_job(job_data)
                if job:
                    jobs.append(job)
            except Exception as e:
                logger.error(f"Error parsing Lever job: {e}")
        
        return jobs
    
    def _parse_lever_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        job_id = job_data.get('id', '')
        title = job_data.get('text', '')
        
        # Extract location
        location = None
        if job_data.get('categories') and job_data['categories'].get('location'):
            location = job_data['categories']['location']
        
        # Build apply URL
        apply_url = job_data.get('applyUrl', '')
        if not apply_url:
            apply_url = job_data.get('hostedUrl', '')
        
        # Get job description
        description = ''
        if job_data.get('description'):
            description = job_data['description']
        elif job_data.get('descriptionPlain'):
            description = job_data['descriptionPlain']
        
        # Enhanced remote detection
        remote = self.is_remote_job({
            'title': title,
            'description': description,
            'location': location or ''
        })
        
        # Also check Lever's specific location indicators
        if location:
            location_lower = location.lower()
            if any(keyword in location_lower for keyword in ['remote', 'anywhere', 'distributed']):
                remote = True
        
        return {
            'id': str(uuid.uuid4()),
            'title': title,
            'company': self.company_name,
            'description': description[:2000],
            'apply_url': apply_url,
            'location': location,
            'remote': remote,
            'salary_min': None,
            'salary_max': None,
            'domain': 'Other',
            'source': 'Lever',
            'source_job_id': job_id
        }