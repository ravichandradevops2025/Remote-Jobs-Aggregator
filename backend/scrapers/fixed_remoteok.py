from typing import List, Dict, Any
from .base import BaseScraper
import uuid
import logging
import asyncio

logger = logging.getLogger(__name__)

class FixedRemoteOKScraper(BaseScraper):
    """Fixed RemoteOK scraper with proper headers to avoid 403"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_url = "https://remoteok.io/api"
        # Use browser-like headers to avoid blocking
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }
    
    async def scrape_jobs(self) -> List[Dict[str, Any]]:
        logger.info("Scraping RemoteOK jobs with fixed headers...")
        
        # Add extra delay for RemoteOK
        await asyncio.sleep(3)
        
        response = await self.fetch_url(self.base_url)
        if not response or not isinstance(response, list):
            logger.warning("RemoteOK still blocking - trying RSS fallback")
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
        
        logger.info(f"Found {len(jobs)} jobs from RemoteOK")
        return jobs
    
    async def _try_rss_fallback(self) -> List[Dict[str, Any]]:
        """Try RSS feed if API is blocked"""
        logger.info("Trying RemoteOK RSS fallback...")
        rss_url = "https://remoteok.io/remote-jobs.rss"
        
        try:
            import feedparser
            response = await self.fetch_url(rss_url)
            
            if not response or 'text' not in response:
                return []
            
            feed = feedparser.parse(response['text'])
            jobs = []
            
            for entry in feed.entries[:50]:  # Limit to 50
                job = self._parse_rss_entry(entry)
                if job:
                    jobs.append(job)
            
            logger.info(f"Found {len(jobs)} jobs from RemoteOK RSS")
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
        if tags:
            description += f" | Skills: {', '.join(tags)}"
        
        apply_url = job_data.get('url', '')
        if not apply_url:
            apply_url = f"https://remoteok.io/remote-jobs/{job_data.get('id', '')}"
        
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
    
    def _parse_rss_entry(self, entry) -> Dict[str, Any]:
        """Parse RemoteOK RSS entry"""
        title = getattr(entry, 'title', '')
        link = getattr(entry, 'link', '')
        description = getattr(entry, 'description', '')
        
        if not title or not link:
            return None
        
        # Extract company from title
        company = 'Unknown'
        if ' at ' in title:
            parts = title.split(' at ')
            if len(parts) >= 2:
                company = parts[-1].strip()
                title = ' at '.join(parts[:-1]).strip()
        
        return {
            'id': str(uuid.uuid4()),
            'title': title,
            'company': company,
            'description': description[:2000],
            'apply_url': link,
            'location': 'Remote',
            'remote': True,
            'salary_min': None,
            'salary_max': None,
            'domain': 'Other',
            'source': 'RemoteOK RSS',
            'source_job_id': link.split('/')[-1] if '/' in link else ''
        }