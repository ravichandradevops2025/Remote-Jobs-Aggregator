#!/usr/bin/env python3
import asyncio
import os
import sys
import yaml
import logging
from typing import List, Dict, Any

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.scrapers.greenhouse import GreenHouseScraper
from backend.scrapers.lever import LeverScraper
from backend.scrapers.generic import GenericScraper
from backend.services.job_classifier import JobClassifier
from backend.services.deduplicator import JobDeduplicator
from backend.services.enhanced_remote_detector import EnhancedRemoteDetector

# Import new ATS scrapers with fallbacks
try:
    from backend.scrapers.workday import WorkdayScraper
    WORKDAY_AVAILABLE = True
except ImportError:
    WORKDAY_AVAILABLE = False

try:
    from backend.scrapers.smartrecruiters import SmartRecruiterscraper
    SMARTRECRUITERS_AVAILABLE = True
except ImportError:
    SMARTRECRUITERS_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def load_sources_config() -> Dict[str, Any]:
    config_path = os.path.join(os.path.dirname(__file__), '..', 'sources.yaml')
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error("sources.yaml not found")
        return {}

async def scrape_all_sources() -> List[Dict[str, Any]]:
    config = await load_sources_config()
    all_jobs = []
    rate_limit = config.get('rate_limits', {}).get('default_delay', 2.5)
    remote_detector = EnhancedRemoteDetector()
    
    # 1. 📡 RSS Job Feeds (High Success Rate)
    logger.info("📡 Scraping RSS Job Feeds (High Success Rate)")
    rss_feeds = config.get('rss_job_feeds', [])
    for feed in rss_feeds:
        if feed.get('working', False):
            try:
                async with GenericScraper(
                    feed['url'], 
                    feed['name'], 
                    feed['type'],
                    rate_limit=rate_limit
                ) as scraper:
                    jobs = await scraper.scrape_jobs()
                    all_jobs.extend(jobs)
                    logger.info(f"✅ {feed['name']}: {len(jobs)} jobs")
            except Exception as e:
                logger.error(f"❌ {feed['name']} failed: {e}")
    
    # 2. 🌍 JSON API Sources
    logger.info("🌍 Scraping JSON API Sources")
    json_sources = config.get('json_api_sources', [])
    for source in json_sources:
        if source.get('working', False):
            try:
                async with GenericScraper(
                    source['url'], 
                    source['name'], 
                    source['type'],
                    rate_limit=rate_limit
                ) as scraper:
                    jobs = await scraper.scrape_jobs()
                    all_jobs.extend(jobs)
                    logger.info(f"✅ {source['name']}: {len(jobs)} jobs")
            except Exception as e:
                logger.error(f"❌ {source['name']} failed: {e}")
    
    # 3. 🏢 Workday Companies (RSS feeds)
    if WORKDAY_AVAILABLE:
        logger.info("🏢 Scraping Workday Companies via RSS")
        workday_companies = config.get('workday_companies', [])
        for company in workday_companies[:3]:  # Limit to avoid rate limits
            try:
                async with WorkdayScraper(
                    company['slug'],
                    company['name'],
                    rate_limit=rate_limit * 1.5  # Slower for Workday
                ) as scraper:
                    all_company_jobs = await scraper.scrape_jobs()
                    
                    # Filter for remote jobs
                    remote_jobs = []
                    for job in all_company_jobs:
                        if remote_detector.is_remote_job(job):
                            job['remote'] = True
                            remote_jobs.append(job)
                    
                    all_jobs.extend(remote_jobs)
                    logger.info(f"✅ {company['name']} (Workday): {len(remote_jobs)}/{len(all_company_jobs)} remote jobs")
                    
            except Exception as e:
                logger.error(f"❌ {company['name']} (Workday) failed: {e}")
    
    # 4. 🔧 Enhanced Lever Companies
    logger.info("🔧 Scraping Lever Companies")
    lever_companies = config.get('lever_companies', [])
    for company in lever_companies[:5]:  # Limit to avoid issues
        try:
            async with LeverScraper(
                company['slug'],
                company['name'],
                rate_limit=rate_limit
            ) as scraper:
                all_company_jobs = await scraper.scrape_jobs()
                
                remote_jobs = []
                for job in all_company_jobs:
                    if remote_detector.is_remote_job(job):
                        job['remote'] = True
                        remote_jobs.append(job)
                
                all_jobs.extend(remote_jobs)
                logger.info(f"✅ {company['name']} (Lever): {len(remote_jobs)}/{len(all_company_jobs)} remote jobs")
                
        except Exception as e:
            logger.error(f"❌ {company['name']} (Lever) failed: {e}")
    
    # 5. 💼 SmartRecruiters Companies
    if SMARTRECRUITERS_AVAILABLE:
        logger.info("💼 Scraping SmartRecruiters Companies")
        sr_companies = config.get('smartrecruiters_companies', [])
        for company in sr_companies:
            try:
                async with SmartRecruiterscraper(
                    company['slug'],
                    company['name'],
                    rate_limit=rate_limit
                ) as scraper:
                    all_company_jobs = await scraper.scrape_jobs()
                    
                    remote_jobs = []
                    for job in all_company_jobs:
                        if remote_detector.is_remote_job(job):
                            job['remote'] = True
                            remote_jobs.append(job)
                    
                    all_jobs.extend(remote_jobs)
                    logger.info(f"✅ {company['name']} (SmartRecruiters): {len(remote_jobs)}/{len(all_company_jobs)} remote jobs")
                    
            except Exception as e:
                logger.error(f"❌ {company['name']} (SmartRecruiters) failed: {e}")
    
    # 6. 🏠 Greenhouse Companies (Existing)
    logger.info("🏠 Scraping Greenhouse Companies")
    greenhouse_companies = config.get('greenhouse_companies', [])
    for company in greenhouse_companies:
        try:
            async with GreenHouseScraper(
                company['slug'],
                company['name'],
                rate_limit=rate_limit
            ) as scraper:
                all_company_jobs = await scraper.scrape_jobs()
                
                remote_jobs = []
                for job in all_company_jobs:
                    if remote_detector.is_remote_job(job):
                        job['remote'] = True
                        remote_jobs.append(job)
                
                all_jobs.extend(remote_jobs)
                logger.info(f"✅ {company['name']} (Greenhouse): {len(remote_jobs)}/{len(all_company_jobs)} remote jobs")
                
        except Exception as e:
            logger.error(f"❌ {company['name']} (Greenhouse) failed: {e}")
    
    return all_jobs

async def main():
    logger.info("🚀 Starting COMPREHENSIVE ATS Platform Scraper")
    logger.info("🎯 Greenhouse + Lever + Workday + SmartRecruiters + RSS Feeds")
    
    try:
        raw_jobs = await scrape_all_sources()
        logger.info(f"📊 Total jobs scraped: {len(raw_jobs)}")
        
        if not raw_jobs:
            logger.warning("❌ No jobs found from any source")
            return {"status": "completed", "jobs_saved": 0}
        
        # Process jobs
        classifier = JobClassifier()
        deduplicator = JobDeduplicator()
        
        # Classify all jobs
        for job in raw_jobs:
            job['domain'] = classifier.classify_job(job)
        
        # Deduplicate
        unique_jobs = deduplicator.deduplicate_jobs(raw_jobs, set())
        logger.info(f"✨ Unique remote jobs: {len(unique_jobs)}")
        
        # Analytics
        sources = {}
        domains = {}
        ats_platforms = {}
        
        for job in unique_jobs:
            source = job.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
            
            domain = job.get('domain', 'Other')
            domains[domain] = domains.get(domain, 0) + 1
            
            # Track ATS platforms
            if source in ['Greenhouse', 'Lever', 'Workday', 'SmartRecruiters']:
                ats_platforms[source] = ats_platforms.get(source, 0) + 1
        
        logger.info("📈 Jobs by source:")
        for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"   {source}: {count} jobs")
        
        logger.info("🏷️ Jobs by domain:")
        for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"   {domain}: {count} jobs")
        
        logger.info("🏢 Jobs by ATS Platform:")
        for platform, count in sorted(ats_platforms.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"   {platform}: {count} jobs")
        
        logger.info("💼 Sample remote jobs:")
        for job in unique_jobs[:7]:
            logger.info(f"   🌐 {job['title']} at {job['company']} ({job['domain']}) - {job['source']}")
        
        return {
            "status": "completed",
            "jobs_scraped": len(raw_jobs),
            "jobs_unique": len(unique_jobs),
            "jobs_saved": len(unique_jobs),
            "top_sources": dict(list(sources.items())[:5]),
            "ats_breakdown": ats_platforms,
            "features_enabled": {
                "workday_scraper": WORKDAY_AVAILABLE,
                "smartrecruiters_scraper": SMARTRECRUITERS_AVAILABLE,
                "rss_feeds": True,
                "enhanced_remote_detection": True
            }
        }
        
    except Exception as e:
        logger.error(f"💥 ATS Scraper failed: {e}")
        return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"🎯 Comprehensive ATS Scraper Result: {result}")