import asyncio
import aiohttp
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    def __init__(self, rate_limit: float = 1.0, max_retries: int = 3, timeout: int = 30):
        self.rate_limit = rate_limit
        self.max_retries = max_retries
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Polite User-Agent header
        self.headers = {
            'User-Agent': 'Remote Jobs Aggregator Bot 1.0 (Respectful Crawler)'
        }
    
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=10)
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def fetch_url(self, url: str) -> Optional[Dict[Any, Any]]:
        """Fetch URL with retries and rate limiting"""
        if not self.session:
            raise RuntimeError("Scraper not properly initialized. Use 'async with' context.")
        
        try:
            await asyncio.sleep(self.rate_limit)  # Rate limiting
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' in content_type:
                        return await response.json()
                    else:
                        text = await response.text()
                        return {'text': text, 'url': url}
                else:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    @abstractmethod
    async def scrape_jobs(self) -> List[Dict[str, Any]]:
        """Scrape jobs from the source. Must be implemented by subclasses."""
        pass
    
    def is_remote_job(self, job_data: Dict[str, Any]) -> bool:
        """Detect if a job is remote based on title, description, or location"""
        remote_keywords = [
            'remote', 'work from home', 'wfh', 'distributed', 'anywhere',
            'home office', 'telecommute', 'virtual', 'flexible location'
        ]
        
        text_to_check = ' '.join([
            job_data.get('title', ''),
            job_data.get('description', ''),
            job_data.get('location', '')
        ]).lower()
        
        return any(keyword in text_to_check for keyword in remote_keywords)
    
    def extract_salary(self, text: str) -> tuple[Optional[int], Optional[int]]:
        """Extract salary range from text"""
        import re
        
        # Simple regex to find salary ranges
        salary_patterns = [
            r'\$(\d+)k?\s*-\s*\$?(\d+)k?',
            r'(\d+)k\s*-\s*(\d+)k',
            r'\$(\d+),?(\d{3})\s*-\s*\$?(\d+),?(\d{3})'
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    min_sal = int(groups[0]) * 1000 if 'k' in text.lower() else int(groups[0])
                    max_sal = int(groups[1]) * 1000 if 'k' in text.lower() else int(groups[1])
                    return min_sal, max_sal
        
        return None, None