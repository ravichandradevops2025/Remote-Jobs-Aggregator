from typing import List, Dict, Any
from .base import BaseScraper
import uuid
import logging

logger = logging.getLogger(__name__)

class HimalayasScraper(BaseScraper):
    """Scraper for Himalayas remote jobs API"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_url = "https://himalayas.app/jobs/api"
        self.headers.update({
            'User-Agent': 'Remote Jobs Aggregator Bot/1.0 (Educational Purpose)',
            'Accept': 'application/json'
        })
    
    async def scrape_jobs(self) -> List[Dict[str, Any]]:
        logger.info("Scraping Himalayas remote jobs...")
        
        url = f"{self.base_url}?limit=100"
        response = await self.fetch_url(url)
        
        if not response or not isinstance(response, dict):
            logger.warning("No valid response from Himalayas API")
            return []
        
        jobs_data = response.get('data', [])
        if not jobs_data:
            logger.warning("No jobs data in Himalayas response")
            return []
        
        jobs = []
        for job_data in jobs_data:
            try:
                job = self._parse_himalayas_job(job_data)
                if job:
                    jobs.append(job)
            except Exception as e:
                logger.error(f"Error parsing Himalayas job: {e}")
        
        logger.info(f"Found {len(jobs)} jobs from Himalayas")
        return jobs
    
    def _parse_himalayas_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a single Himalayas job"""
        
        title = job_data.get('title', '')
        company_data = job_data.get('company', {})
        company = company_data.get('name', 'Unknown') if isinstance(company_data, dict) else str(company_data)
        
        if not title or not company:
            return None
        
        # Get job URL
        job_id = job_data.get('id', '')
        apply_url = job_data.get('url', '')
        if not apply_url and job_id:
            apply_url = f"https://himalayas.app/jobs/{job_id}"
        elif not apply_url:
            apply_url = "https://himalayas.app"
        
        # Description
        description = job_data.get('description', '')
        
        # Salary info
        salary_min = job_data.get('minSalary')
        salary_max = job_data.get('maxSalary')
        
        return {
            'id': str(uuid.uuid4()),
            'title': title,
            'company': company,
            'description': description[:2000] if description else '',
            'apply_url': apply_url,
            'location': 'Remote Worldwide',
            'remote': True,  # All Himalayas jobs are remote
            'salary_min': salary_min,
            'salary_max': salary_max,
            'domain': 'Other',
            'source': 'Himalayas',
            'source_job_id': str(job_id)
        }