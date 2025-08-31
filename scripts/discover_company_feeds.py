#!/usr/bin/env python3
"""
Tool to discover RSS feeds and job APIs for companies
Usage: python scripts/discover_company_feeds.py
"""

import asyncio
import aiohttp
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompanyFeedDiscovery:
    def __init__(self):
        self.common_patterns = [
            # RSS patterns
            "/rss",
            "/jobs/rss", 
            "/careers/rss",
            "/feed",
            "/jobs.rss",
            "/careers.rss",
            # API patterns
            "/api/jobs",
            "/api/careers",
            "/api/openings",
            "/jobs.json",
            "/careers.json",
            # Workday patterns
            ".wd1.myworkdayjobs.com/{company}/rss",
            ".wd5.myworkdayjobs.com/{company}/rss",
            # Lever patterns
            "jobs.lever.co/{company}",
            # SmartRecruiters patterns
            "careers.smartrecruiters.com/{company}"
        ]
    
    async def discover_feeds(self, companies: List[str]) -> Dict[str, List[str]]:
        """Discover job feeds for a list of companies"""
        results = {}
        
        async with aiohttp.ClientSession() as session:
            for company in companies:
                logger.info(f"🔍 Discovering feeds for {company}")
                feeds = await self._check_company_feeds(session, company)
                if feeds:
                    results[company] = feeds
                    logger.info(f"✅ Found {len(feeds)} feeds for {company}")
                else:
                    logger.info(f"❌ No feeds found for {company}")
        
        return results
    
    async def _check_company_feeds(self, session: aiohttp.ClientSession, company: str) -> List[str]:
        """Check various feed patterns for a company"""
        found_feeds = []
        company_domains = await self._get_company_domains(company)
        
        for domain in company_domains:
            for pattern in self.common_patterns:
                url = self._build_url(domain, pattern, company)
                if await self._test_url(session, url):
                    found_feeds.append(url)
        
        return found_feeds
    
    async def _get_company_domains(self, company: str) -> List[str]:
        """Get possible domain variations for a company"""
        company_lower = company.lower().replace(' ', '')
        return [
            f"https://{company_lower}.com",
            f"https://www.{company_lower}.com",
            f"https://careers.{company_lower}.com",
            f"https://jobs.{company_lower}.com"
        ]
    
    def _build_url(self, domain: str, pattern: str, company: str) -> str:
        """Build URL from domain and pattern"""
        company_slug = company.lower().replace(' ', '').replace('.', '')
        
        if '{company}' in pattern:
            pattern = pattern.replace('{company}', company_slug)
            return pattern if pattern.startswith('http') else f"https://{pattern}"
        else:
            return f"{domain}{pattern}"
    
    async def _test_url(self, session: aiohttp.ClientSession, url: str) -> bool:
        """Test if URL returns valid content"""
        try:
            async with session.head(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                return response.status == 200
        except:
            return False

async def main():
    """Discover feeds for Indian and global companies"""
    companies = [
        # Indian companies
        "Razorpay", "CRED", "Swiggy", "Zomato", "Flipkart", "PhonePe",
        "Freshworks", "Zoho", "Postman", "BrowserStack", "Chargebee",
        
        # Global tech companies
        "Spotify", "Shopify", "Atlassian", "Canva", "Notion", "Figma",
        "ServiceNow", "Salesforce", "Adobe", "Booking.com"
    ]
    
    discovery = CompanyFeedDiscovery()
    results = await discovery.discover_feeds(companies)
    
    print("\n🎯 DISCOVERED JOB FEEDS:")
    print("=" * 50)
    
    for company, feeds in results.items():
        print(f"\n🏢 {company}:")
        for feed in feeds:
            feed_type = "RSS" if any(x in feed for x in ['/rss', '.rss', '/feed']) else "API"
            print(f"   📡 [{feed_type}] {feed}")
    
    # Generate YAML config
    print("\n📝 Generated sources.yaml config:")
    print("=" * 50)
    
    for company, feeds in results.items():
        company_slug = company.lower().replace(' ', '').replace('.', '')
        for feed in feeds:
            if 'lever.co' in feed:
                print(f'  - slug: "{company_slug}"')
                print(f'    name: "{company}"')
            elif 'workday' in feed:
                print(f'  - slug: "{company_slug}"')
                print(f'    name: "{company}"')
                print(f'    rss_url: "{feed}"')
            elif 'smartrecruiters' in feed:
                print(f'  - slug: "{company_slug}"')
                print(f'    name: "{company}"')
                print(f'    api_url: "{feed}"')

if __name__ == "__main__":
    asyncio.run(main())