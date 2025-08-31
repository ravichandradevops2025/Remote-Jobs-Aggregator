from typing import List, Dict, Any
from .base import BaseScraper
import uuid
import logging

logger = logging.getLogger(__name__)

class GreenHouseScraper(BaseScraper):
    def __init__(self, company_slug: str, company_name: str, **kwargs):
        super().__init__(**kwargs)
        self.company_slug = company_slug
        self.company_name = company_name
        self.base_url = f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs"
    
    async def scrape_jobs(self) -> List[Dict[str, Any]]:
        """Scrape jobs from Greenhouse API"""
        logger.info(f"Scraping Greenhouse jobs for {self.company_name}")
        
        response = await self.fetch_url(self.base_url)
        if not response or 'jobs' not in response:
            logger.warning(f"No jobs found for {self.company_name} on Greenhouse")
            return []
        
        jobs = []
        for job_data in response['jobs']:
            try:
                job = self._parse_greenhouse_job(job_data)
                if job:
                    jobs.append(job)
            except Exception as e:
                logger.error(f"Error parsing Greenhouse job: {e}")
        
        logger.info(f"Found {len(jobs)} jobs for {self.company_name}")
        return jobs
    
    def _parse_greenhouse_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a single Greenhouse job"""
        job_id = str(job_data.get('id'))
        title = job_data.get('title', '')
        
        # Extract location
        location = None
        if job_data.get('offices'):
            location = ', '.join([office.get('name', '') for office in job_data['offices']])
        
        # Build apply URL
        apply_url = job_data.get('absolute_url', '')
        
        # Get job description
        description = job_data.get('content', '')
        if not description and job_data.get('description'):
            description = job_data['description']
        
        # Check if remote
        remote = self.is_remote_job({
            'title': title,
            'description': description,
            'location': location or ''
        })
        
        # Extract salary if available
        salary_min, salary_max = self.extract_salary(description)
        
        return {
            'id': str(uuid.uuid4()),
            'title': title,
            'company': self.company_name,
            'description': description[:2000],  # Truncate long descriptions
            'apply_url': apply_url,
            'location': location,
            'remote': remote,
            'salary_min': salary_min,
            'salary_max': salary_max,
            'domain': 'Other',  # Will be classified later
            'source': 'Greenhouse',
            'source_job_id': job_id
        }