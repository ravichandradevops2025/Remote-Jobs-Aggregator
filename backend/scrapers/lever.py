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
        if not response:
            logger.warning(f"No response from Lever for {self.company_name}")
            return []
        
        # Handle different response structures
        jobs_data = []
        if isinstance(response, list):
            jobs_data = response
        elif isinstance(response, dict):
            jobs_data = response.get('data', response.get('postings', []))
        
        if not jobs_data:
            logger.warning(f"No jobs found for {self.company_name} on Lever")
            return []
        
        jobs = []
        for job_data in jobs_data:
            try:
                job = self._parse_lever_job(job_data)
                if job:
                    jobs.append(job)
            except Exception as e:
                logger.error(f"Error parsing Lever job: {e}")
        
        logger.info(f"Found {len(jobs)} jobs from {self.company_name} via Lever")
        return jobs
    
    def _parse_lever_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        job_id = job_data.get('id', '')
        title = job_data.get('text', job_data.get('title', ''))
        
        if not title:
            return None
        
        # Extract location with multiple fallbacks
        location = None
        if job_data.get('categories'):
            categories = job_data['categories']
            if isinstance(categories, dict):
                location = categories.get('location', categories.get('office'))
            elif isinstance(categories, list) and categories:
                # Sometimes categories is a list
                for cat in categories:
                    if isinstance(cat, dict) and cat.get('location'):
                        location = cat['location']
                        break
        
        if not location and job_data.get('workplaceType'):
            location = job_data['workplaceType']
        
        # Get apply URL with multiple strategies
        apply_url = job_data.get('applyUrl', job_data.get('hostedUrl'))
        if not apply_url and job_id:
            # Construct URL from job ID
            apply_url = f"https://jobs.lever.co/{self.company_slug}/{job_id}"
        
        # Get description
        description = job_data.get('description', job_data.get('descriptionPlain', ''))
        if isinstance(description, dict):
            description = description.get('content', str(description))
        
        # Enhanced remote detection
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
            'apply_url': apply_url or f"https://jobs.lever.co/{self.company_slug}",
            'location': location,
            'remote': remote,
            'salary_min': None,
            'salary_max': None,
            'domain': 'Other',
            'source': 'Lever',
            'source_job_id': job_id
        }