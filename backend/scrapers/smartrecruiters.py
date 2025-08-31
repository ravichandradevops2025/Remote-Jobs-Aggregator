from typing import List, Dict, Any
from .base import BaseScraper
import uuid
import logging

logger = logging.getLogger(__name__)

class SmartRecruiterscraper(BaseScraper):
    """Scraper for SmartRecruiters API"""
    
    def __init__(self, company_slug: str, company_name: str, **kwargs):
        super().__init__(**kwargs)
        self.company_slug = company_slug
        self.company_name = company_name
        self.base_url = f"https://api.smartrecruiters.com/v1/companies/{company_slug}/postings"
    
    async def scrape_jobs(self) -> List[Dict[str, Any]]:
        logger.info(f"Scraping SmartRecruiters for {self.company_name}")
        
        # Add query parameters for remote jobs
        url = f"{self.base_url}?limit=100&offset=0"
        response = await self.fetch_url(url)
        
        if not response:
            logger.warning(f"No response from SmartRecruiters for {self.company_name}")
            return []
        
        # Handle SmartRecruiters API response structure
        jobs_data = []
        if isinstance(response, dict):
            jobs_data = response.get('content', response.get('postings', response.get('data', [])))
        elif isinstance(response, list):
            jobs_data = response
        
        if not jobs_data:
            logger.warning(f"No jobs found for {self.company_name} on SmartRecruiters")
            return []
        
        jobs = []
        for job_data in jobs_data:
            try:
                job = self._parse_smartrecruiters_job(job_data)
                if job:
                    jobs.append(job)
            except Exception as e:
                logger.error(f"Error parsing SmartRecruiters job: {e}")
        
        logger.info(f"Found {len(jobs)} jobs from {self.company_name} via SmartRecruiters")
        return jobs
    
    def _parse_smartrecruiters_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        job_id = job_data.get('id', job_data.get('uuid', ''))
        title = job_data.get('name', job_data.get('title', ''))
        
        if not title:
            return None
        
        # Extract location
        location = None
        if job_data.get('location'):
            loc_data = job_data['location']
            if isinstance(loc_data, dict):
                location = loc_data.get('city', loc_data.get('name', ''))
                if loc_data.get('country'):
                    location = f"{location}, {loc_data['country']}" if location else loc_data['country']
            else:
                location = str(loc_data)
        
        # Get description
        description = job_data.get('jobAd', {}).get('sections', {}).get('jobDescription', {}).get('text', '')
        if not description:
            description = job_data.get('description', '')
        
        # Build apply URL
        apply_url = job_data.get('ref', '')
        if not apply_url and job_id:
            apply_url = f"https://jobs.smartrecruiters.com/{self.company_slug}/{job_id}"
        
        # Check remote status
        remote = self.is_remote_job({
            'title': title,
            'description': description,
            'location': location or ''
        })
        
        return {
            'id': str(uuid.uuid4()),
            'title': title,
            'company': self.company_name,
            'description': str(description)[:2000],
            'apply_url': apply_url,
            'location': location,
            'remote': remote,
            'salary_min': None,
            'salary_max': None,
            'domain': 'Other',
            'source': 'SmartRecruiters',
            'source_job_id': job_id
        }