from typing import List, Dict, Any
from .base import BaseScraper
import uuid
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class IndianCompanyScraper(BaseScraper):
    """Scraper for Indian company career pages"""
    
    def __init__(self, company_name: str, careers_url: str, **kwargs):
        super().__init__(**kwargs)
        self.company_name = company_name
        self.careers_url = careers_url
        
        # Enhanced headers for Indian sites
        self.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    async def scrape_jobs(self) -> List[Dict[str, Any]]:
        logger.info(f"Scraping {self.company_name} careers page...")
        
        # Try API endpoints first
        api_jobs = await self._try_api_endpoints()
        if api_jobs:
            return api_jobs
        
        # Fall back to HTML scraping
        return await self._scrape_html_careers_page()
    
    async def _try_api_endpoints(self) -> List[Dict[str, Any]]:
        """Try common API endpoints for Indian companies"""
        api_urls = [
            f"{self.careers_url.rstrip('/')}/api/jobs",
            f"{self.careers_url.rstrip('/')}/api/openings",
            f"{self.careers_url.rstrip('/')}/jobs.json",
            f"{self.careers_url.rstrip('/')}/openings.json"
        ]
        
        for api_url in api_urls:
            try:
                response = await self.fetch_url(api_url)
                if response and isinstance(response, dict):
                    jobs_data = response.get('jobs', response.get('data', response.get('openings', [])))
                    if jobs_data:
                        return self._parse_api_jobs(jobs_data)
            except Exception as e:
                logger.debug(f"API endpoint {api_url} failed: {e}")
                continue
        
        return []
    
    async def _scrape_html_careers_page(self) -> List[Dict[str, Any]]:
        """Scrape HTML careers page"""
        logger.info(f"Trying HTML scraping for {self.company_name}")
        
        response = await self.fetch_url(self.careers_url)
        if not response or 'text' not in response:
            logger.warning(f"No HTML content from {self.company_name}")
            return []
        
        try:
            soup = BeautifulSoup(response['text'], 'html.parser')
            jobs = self._extract_jobs_from_html(soup)
            logger.info(f"Found {len(jobs)} jobs from {self.company_name} HTML")
            return jobs
            
        except Exception as e:
            logger.error(f"Error parsing HTML for {self.company_name}: {e}")
            return []
    
    def _parse_api_jobs(self, jobs_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse jobs from API response"""
        jobs = []
        
        for job_data in jobs_data:
            try:
                job = self._create_job_from_data(job_data)
                if job:
                    jobs.append(job)
            except Exception as e:
                logger.error(f"Error parsing API job for {self.company_name}: {e}")
        
        return jobs
    
    def _extract_jobs_from_html(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract jobs from HTML - basic implementation"""
        jobs = []
        
        # Common job listing selectors for Indian company websites
        job_selectors = [
            '.job-listing', '.job-item', '.career-item', '.position',
            '.job-card', '.opening', '[class*="job"]', '[class*="career"]',
            '.vacancy', '.role'
        ]
        
        job_elements = []
        for selector in job_selectors:
            elements = soup.select(selector)
            if elements:
                job_elements = elements
                break
        
        if not job_elements:
            # Try to find job-related links
            job_links = soup.find_all('a', href=True)
            job_elements = [link for link in job_links if any(keyword in str(link).lower() 
                          for keyword in ['job', 'career', 'position', 'opening', 'role', 'vacancy'])]
        
        for element in job_elements[:20]:  # Limit to first 20 jobs
            try:
                job = self._extract_job_from_element(element)
                if job:
                    jobs.append(job)
            except Exception as e:
                logger.debug(f"Error extracting job from element: {e}")
        
        return jobs
    
    def _extract_job_from_element(self, element) -> Dict[str, Any]:
        """Extract job data from HTML element"""
        
        # Try to get job title
        title_element = element.find(['h1', 'h2', 'h3', 'h4', 'h5', '.title', '.job-title'])
        title = title_element.get_text(strip=True) if title_element else element.get_text(strip=True)[:100]
        
        if not title or len(title.strip()) < 5:
            return None
        
        # Try to get apply link
        apply_url = element.get('href') if element.name == 'a' else None
        if not apply_url:
            link_element = element.find('a', href=True)
            apply_url = link_element.get('href') if link_element else None
        
        # Make URL absolute
        if apply_url and not apply_url.startswith('http'):
            base_url = self.careers_url.split('/')[0] + '//' + self.careers_url.split('/')[2]
            apply_url = base_url + apply_url if apply_url.startswith('/') else base_url + '/' + apply_url
        
        if not apply_url:
            apply_url = self.careers_url  # Fallback to careers page
        
        # Try to get description
        description = element.get_text(strip=True)
        
        return self._create_job_from_data({
            'title': title,
            'description': description,
            'apply_url': apply_url
        })
    
    def _create_job_from_data(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create standardized job object"""
        title = job_data.get('title', '').strip()
        if not title or len(title) < 3:
            return None
        
        description = job_data.get('description', job_data.get('summary', ''))
        apply_url = job_data.get('apply_url', job_data.get('url', self.careers_url))
        location = job_data.get('location', 'India')
        
        # Enhanced remote detection for Indian companies
        is_remote = self.is_remote_job({
            'title': title,
            'description': description,
            'location': location
        })
        
        return {
            'id': str(uuid.uuid4()),
            'title': title,
            'company': self.company_name,
            'description': description[:2000],
            'apply_url': apply_url,
            'location': location,
            'remote': is_remote,
            'salary_min': job_data.get('salary_min'),
            'salary_max': job_data.get('salary_max'),
            'domain': 'Other',  # Will be classified later
            'source': f'{self.company_name} Careers',
            'source_job_id': job_data.get('id', str(uuid.uuid4())[:8])
        }