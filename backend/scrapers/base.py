import asyncio
import aiohttp
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    def __init__(self, rate_limit: float = 2.0, max_retries: int = 3, timeout: int = 30):
        self.rate_limit = rate_limit
        self.max_retries = max_retries
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Enhanced polite headers
        self.headers = {
            'User-Agent': 'Remote Jobs Aggregator Bot/1.0 (Respectful Crawler; +https://github.com/ravichandradevops2025/Remote-Jobs-Aggregator)',
            'Accept': 'application/json, text/html, application/xml;q=0.9, */*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
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
            # Respectful rate limiting
            await asyncio.sleep(self.rate_limit)
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' in content_type:
                        return await response.json()
                    else:
                        text = await response.text()
                        return {'text': text, 'url': url}
                elif response.status == 429:
                    logger.warning(f"Rate limited by {url}, waiting longer...")
                    await asyncio.sleep(self.rate_limit * 3)
                    return None
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
        """Enhanced remote job detection"""
        remote_keywords = [
            'remote', 'work from home', 'wfh', 'distributed', 'anywhere',
            'home office', 'telecommute', 'virtual', 'flexible location',
            'remote first', 'remote friendly', 'fully remote', '100% remote',
            'remote work', 'remote position', 'remote opportunity',
            'work from anywhere', 'location independent', 'global remote'
        ]
        
        # Check title, description, and location
        text_to_check = ' '.join([
            job_data.get('title', ''),
            job_data.get('description', ''),
            job_data.get('location', '')
        ]).lower()
        
        return any(keyword in text_to_check for keyword in remote_keywords)
    
    def extract_salary(self, text: str) -> tuple[Optional[int], Optional[int]]:
        """Extract salary range from text"""
        import re
        
        # Enhanced salary patterns
        salary_patterns = [
            r'\$(\d+)k?\s*-\s*\$?(\d+)k?',
            r'(\d+)k\s*-\s*(\d+)k',
            r'\$(\d+),?(\d{3})\s*-\s*\$?(\d+),?(\d{3})',
            r'salary:\s*\$?(\d+)k?\s*-\s*\$?(\d+)k?',
            r'compensation:\s*\$?(\d+)k?\s*-\s*\$?(\d+)k?'
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    try:
                        min_sal = int(groups[0])
                        max_sal = int(groups[1])
                        
                        # Convert k to thousands
                        if 'k' in text.lower():
                            min_sal *= 1000
                            max_sal *= 1000
                        
                        return min_sal, max_sal
                    except ValueError:
                        continue
        
        return None, None