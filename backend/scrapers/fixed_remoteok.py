from typing import List, Dict, Any
from .base import BaseScraper
import uuid
import logging
import asyncio

logger = logging.getLogger(__name__)

class FixedRemoteOKScraper(BaseScraper):
    """Fixed RemoteOK scraper with proper headers"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_url = "https://remoteok.io/api"
        # Browser-like headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive'
        }
    
    async def scrape_jobs(self) -> List[Dict[str, Any]]:
        logger.info("Scraping RemoteOK jobs with browser headers...")
        
        # Extra delay for RemoteOK
        await asyncio.sleep(3)
        
        response = await self.fetch_url(self.base_url)
        if not response or not isinstance(response, list):
            logger.warning("RemoteOK API still blocked, trying RSS fallback")
            return await self._try_rss_fallback()
        
        jobs = []
        # Skip first item (metadata)
        for job_data in response[1:]:
            try:
                if isinstance(job_data, dict):
                    job = self._parse_remoteok_job(job_data)
                    if job:
                        jobs.append(job)
            except Exception as e:
                logger.error(f"Error parsing RemoteOK job: {e}")
        
        logger.info(f"Found {len(jobs)} jobs from RemoteOK API")
        return jobs
    
    async def _try_rss_fallback(self) -> List[Dict[str, Any]]:
        """Try RSS feed if API is blocked"""
        logger.info("Trying RemoteOK RSS fallback...")
        
        try:
            # Try RSS approach
            from .generic import GenericScraper
            async with GenericScraper(
                "https://remoteok.io/remote-jobs.rss",
                "RemoteOK RSS",
                "rss",
                rate_limit=self.rate_limit
            ) as scraper:
                jobs = await scraper.scrape_jobs()
                logger.info(f"Found {len(jobs)} jobs from RemoteOK RSS fallback")
                return jobs
                
        except Exception as e:
            logger.error(f"RSS fallback failed: {e}")
            return []
    
    def _parse_remoteok_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse RemoteOK API job"""
        title = job_data.get('position', '')
        company = job_data.get('company', '')
        
        if not title or not company:
            return None
        
        description = job_data.get('description', '')
        tags = job_data.get('tags', [])
        if tags and isinstance(tags, list):
            description += f" | Skills: {', '.join(str(tag) for tag in tags)}"
        
        apply_url = job_data.get('url', '')
        if not apply_url:
            job_id = job_data.get('id', '')
            apply_url = f"https://remoteok.io/remote-jobs/{job_id}" if job_id else "https://remoteok.io"
        
        return {
            'id': str(uuid.uuid4()),
            'title': title,
            'company': company,
            'description': description[:2000],
            'apply_url': apply_url,
            'location': 'Remote Worldwide',
            'remote': True,
            'salary_min': job_data.get('salary_min'),
            'salary_max': job_data.get('salary_max'),
            'domain': 'Other',
            'source': 'RemoteOK',
            'source_job_id': str(job_data.get('id', ''))
        }