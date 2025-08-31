import asyncio
import aiohttp
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    def __init__(self, rate_limit: float = 1.0, max_retries: int = 3, timeout: int = 30):
        self.rate_limit = rate_limit
        self.max_retries = max_retries
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        
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
    
    async def fetch_url(self, url: str) -> Optional[Dict[Any, Any]]:
        """Fetch URL with retries and rate limiting"""
        if not self.session:
            raise RuntimeError("Scraper not properly initialized.")
        
        try:
            await asyncio.sleep(self.rate_limit)
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    @abstractmethod
    async def scrape_jobs(self) -> List[Dict[str, Any]]:
        """Scrape jobs from the source"""
        pass
    
    def is_remote_job(self, job_data: Dict[str, Any]) -> bool:
        """Detect if a job is remote"""
        remote_keywords = [
            'remote', 'work from home', 'wfh', 'distributed', 'anywhere'
        ]
        
        text_to_check = ' '.join([
            job_data.get('title', ''),
            job_data.get('description', ''),
            job_data.get('location', '')
        ]).lower()
        
        return any(keyword in text_to_check for keyword in remote_keywords)
EOF