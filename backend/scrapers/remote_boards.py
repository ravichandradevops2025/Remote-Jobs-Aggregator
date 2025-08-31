from typing import List, Dict, Any
from .base import BaseScraper
from .generic import GenericScraper
import uuid
import logging
import aiohttp

logger = logging.getLogger(__name__)

class RemoteOKScraper(BaseScraper):
    """Specialized scraper for RemoteOK API"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_url = "https://remoteok.io/api"
        # RemoteOK requires specific headers
        self.headers.update({
            'User-Agent': 'Remote Jobs Aggregator (https://github.com/ravichandradevops2025/Remote-Jobs-Aggregator)',
            'Accept': 'application/json'
        })
    
    async def scrape_jobs(self) -> List[Dict[str, Any]]:
        logger.info("Scraping RemoteOK jobs...")
        
        response = await self.fetch_url(self.base_url)
        if not response or not isinstance(response, list):
            logger.warning("No jobs found from RemoteOK")
            return []
        
        jobs = []
        # RemoteOK returns array, first item is metadata
        for job_data in response[1:]:  # Skip first item
            try:
                if isinstance(job_data, dict):
                    job = self._parse_remoteok_job(job_data)
                    if job:
                        jobs.append(job)
            except Exception as e:
                logger.error(f"Error parsing RemoteOK job: {e}")
        
        logger.info(f"Found {len(jobs)} jobs from RemoteOK")
        return jobs
    
    def _parse_remoteok_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        # RemoteOK has specific field structure
        title = job_data.get('position', '')
        company = job_data.get('company', '')
        
        if not title or not company:
            return None
        
        # Build description from tags and description
        description = job_data.get('description', '')
        tags = job_data.get('tags', [])
        if tags:
            description += f" Skills: {', '.join(tags)}"
        
        # RemoteOK jobs are all remote
        apply_url = job_data.get('url', '')
        if not apply_url:
            apply_url = f"https://remoteok.io/remote-jobs/{job_data.get('id', '')}"
        
        # Extract salary if available
        salary_min = job_data.get('salary_min')
        salary_max = job_data.get('salary_max')
        
        return {
            'id': str(uuid.uuid4()),
            'title': title,
            'company': company,
            'description': description[:2000],
            'apply_url': apply_url,
            'location': 'Remote Worldwide',
            'remote': True,  # All RemoteOK jobs are remote
            'salary_min': salary_min,
            'salary_max': salary_max,
            'domain': 'Other',  # Will be classified later
            'source': 'RemoteOK',
            'source_job_id': str(job_data.get('id', ''))
        }

class WeWorkRemotelyScraper(BaseScraper):
    """Scraper for We Work Remotely RSS feed"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.feed_url = "https://weworkremotely.com/remote-jobs.rss"
    
    async def scrape_jobs(self) -> List[Dict[str, Any]]:
        logger.info("Scraping We Work Remotely jobs...")
        
        try:
            import feedparser
            
            response = await self.fetch_url(self.feed_url)
            if not response or 'text' not in response:
                logger.warning("No data from We Work Remotely")
                return []
            
            feed = feedparser.parse(response['text'])
            jobs = []
            
            for entry in feed.entries[:50]:  # Limit to recent jobs
                try:
                    job = self._parse_wwr_job(entry)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    logger.error(f"Error parsing WWR job: {e}")
            
            logger.info(f"Found {len(jobs)} jobs from We Work Remotely")
            return jobs
            
        except Exception as e:
            logger.error(f"Error scraping We Work Remotely: {e}")
            return []
    
    def _parse_wwr_job(self, entry) -> Dict[str, Any]:
        title = getattr(entry, 'title', '')
        link = getattr(entry, 'link', '')
        description = getattr(entry, 'description', '')
        
        if not title or not link:
            return None
        
        # Extract company from title (format: "Job Title at Company Name")
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
            'source': 'We Work Remotely',
            'source_job_id': link.split('/')[-1] if '/' in link else ''
        }

class RemoteCoScraper(BaseScraper):
    """Scraper for Remote.co jobs"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_url = "https://remote.co/api/remote-jobs"
    
    async def scrape_jobs(self) -> List[Dict[str, Any]]:
        logger.info("Scraping Remote.co jobs...")
        
        # Note: Remote.co might not have a public API
        # This is a placeholder - in reality, we might need to scrape their HTML
        # For now, we'll create a generic scraper approach
        
        try:
            response = await self.fetch_url(self.base_url)
            if not response:
                logger.info("Remote.co API not available, skipping...")
                return []
            
            # Handle the response based on actual API structure
            jobs = []
            # Implementation would depend on actual API structure
            
            logger.info(f"Found {len(jobs)} jobs from Remote.co")
            return jobs
            
        except Exception as e:
            logger.info(f"Remote.co not accessible: {e}")
            return []

# Create a factory function to get the right scraper
def create_remote_scraper(source_name: str, **kwargs):
    """Factory function to create appropriate remote job scraper"""
    scrapers = {
        'remoteok': RemoteOKScraper,
        'remote ok': RemoteOKScraper,
        'weworkremotely': WeWorkRemotelyScraper,
        'we work remotely': WeWorkRemotelyScraper,
        'remoteco': RemoteCoScraper,
        'remote.co': RemoteCoScraper,
    }
    
    scraper_class = scrapers.get(source_name.lower().replace(' ', '').replace('.', ''), GenericScraper)
    return scraper_class(**kwargs)