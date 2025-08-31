from typing import List, Dict, Any
from .base import BaseScraper
import uuid
import logging
import feedparser
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class GenericScraper(BaseScraper):
    def __init__(self, feed_url: str, feed_name: str, feed_type: str = 'json', **kwargs):
        super().__init__(**kwargs)
        self.feed_url = feed_url
        self.feed_name = feed_name
        self.feed_type = feed_type.lower()
    
    async def scrape_jobs(self) -> List[Dict[str, Any]]:
        """Scrape jobs from generic JSON or RSS feeds"""
        logger.info(f"Scraping {self.feed_type} jobs from {self.feed_name}")
        
        if self.feed_type == 'rss':
            return await self._scrape_rss_feed()
        else:
            return await self._scrape_json_feed()
    
    async def _scrape_json_feed(self) -> List[Dict[str, Any]]:
        """Scrape JSON feed"""
        response = await self.fetch_url(self.feed_url)
        if not response:
            return []
        
        jobs = []
        
        # Handle different JSON structures
        job_list = response
        if isinstance(response, dict):
            # Try common keys for job arrays
            for key in ['jobs', 'data', 'results', 'items']:
                if key in response and isinstance(response[key], list):
                    job_list = response[key]
                    break
        
        if not isinstance(job_list, list):
            logger.warning(f"Unexpected JSON structure in {self.feed_name}")
            return []
        
        for job_data in job_list:
            try:
                job = self._parse_generic_job(job_data)
                if job:
                    jobs.append(job)
            except Exception as e:
                logger.error(f"Error parsing generic job: {e}")
        
        logger.info(f"Found {len(jobs)} jobs from {self.feed_name}")
        return jobs
    
    async def _scrape_rss_feed(self) -> List[Dict[str, Any]]:
        """Scrape RSS feed"""
        response = await self.fetch_url(self.feed_url)
        if not response or 'text' not in response:
            return []
        
        try:
            feed = feedparser.parse(response['text'])
            jobs = []
            
            for entry in feed.entries:
                job_data = {
                    'title': getattr(entry, 'title', ''),
                    'description': getattr(entry, 'description', ''),
                    'link': getattr(entry, 'link', ''),
                    'company': getattr(entry, 'author', 'Unknown'),
                    'published': getattr(entry, 'published', '')
                }
                
                job = self._parse_generic_job(job_data)
                if job:
                    jobs.append(job)
            
            logger.info(f"Found {len(jobs)} jobs from RSS feed {self.feed_name}")
            return jobs
            
        except Exception as e:
            logger.error(f"Error parsing RSS feed {self.feed_name}: {e}")
            return []
    
    def _parse_generic_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a single generic job from JSON or RSS"""
        # Try different possible field names
        title = job_data.get('title') or job_data.get('position') or job_data.get('job_title', '')
        company = job_data.get('company') or job_data.get('company_name') or job_data.get('author', 'Unknown')
        description = job_data.get('description') or job_data.get('summary') or job_data.get('job_description', '')
        
        # Apply URL
        # Apply URL
        apply_url = (job_data.get('apply_url') or 
                    job_data.get('url') or 
                    job_data.get('link') or
                    job_data.get('job_url', ''))
        
        if not apply_url:
            logger.warning(f"No apply URL found for job: {title}")
            return None
        
        # Location
        location = job_data.get('location') or job_data.get('job_location')
        
        # Clean up HTML in description if present
        if description and '<' in description:
            soup = BeautifulSoup(description, 'html.parser')
            description = soup.get_text(strip=True)
        
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
            'company': company,
            'description': description[:2000],  # Truncate long descriptions
            'apply_url': apply_url,
            'location': location,
            'remote': remote,
            'salary_min': salary_min,
            'salary_max': salary_max,
            'domain': 'Other',  # Will be classified later
            'source': self.feed_name,
            'source_job_id': job_data.get('id', str(uuid.uuid4())[:8])
        }