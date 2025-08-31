from typing import List, Dict, Any
from .base import BaseScraper
import uuid
import logging

logger = logging.getLogger(__name__)

class WorkdayScraper(BaseScraper):
    """Scraper for Workday RSS feeds"""
    
    def __init__(self, company_slug: str, company_name: str, **kwargs):
        super().__init__(**kwargs)
        self.company_slug = company_slug
        self.company_name = company_name
        # Workday RSS feed format
        self.rss_url = f"https://{company_slug}.wd1.myworkdayjobs.com/{company_slug}/rss"
    
    async def scrape_jobs(self) -> List[Dict[str, Any]]:
        logger.info(f"Scraping Workday RSS for {self.company_name}")
        
        response = await self.fetch_url(self.rss_url)
        if not response or 'text' not in response:
            logger.warning(f"No RSS data from Workday for {self.company_name}")
            return []
        
        try:
            import feedparser
            feed = feedparser.parse(response['text'])
            
            if not feed.entries:
                logger.warning(f"No job entries in Workday RSS for {self.company_name}")
                return []
            
            jobs = []
            for entry in feed.entries:
                try:
                    job = self._parse_workday_entry(entry)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    logger.debug(f"Error parsing Workday entry: {e}")
            
            logger.info(f"Found {len(jobs)} jobs from {self.company_name} via Workday")
            return jobs
            
        except Exception as e:
            logger.error(f"Error parsing Workday RSS for {self.company_name}: {e}")
            return []
    
    def _parse_workday_entry(self, entry) -> Dict[str, Any]:
        title = getattr(entry, 'title', '')
        link = getattr(entry, 'link', '')
        description = getattr(entry, 'description', getattr(entry, 'summary', ''))
        
        if not title or not link:
            return None
        
        # Extract location from title (Workday often includes location in title)
        location = None
        if ' - ' in title:
            parts = title.split(' - ')
            if len(parts) >= 2:
                # Last part is often location
                potential_location = parts[-1].strip()
                if any(keyword in potential_location.lower() for keyword in 
                      ['remote', 'office', 'city', 'state', 'country', 'worldwide']):
                    location = potential_location
        
        # Check for remote indicators
        remote = self.is_remote_job({
            'title': title,
            'description': description,
            'location': location or ''
        })
        
        return {
            'id': str(uuid.uuid4()),
            'title': title,
            'company': self.company_name,
            'description': description[:2000],
            'apply_url': link,
            'location': location,
            'remote': remote,
            'salary_min': None,
            'salary_max': None,
            'domain': 'Other',
            'source': 'Workday',
            'source_job_id': link.split('/')[-1] if '/' in link else ''
        }