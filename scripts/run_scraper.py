#!/usr/bin/env python3
import asyncio
import os
import sys
import yaml
import logging
from typing import List, Dict, Any

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Only import what we know exists
from backend.scrapers.greenhouse import GreenHouseScraper
from backend.scrapers.lever import LeverScraper
from backend.scrapers.generic import GenericScraper
from backend.services.job_classifier import JobClassifier
from backend.services.deduplicator import JobDeduplicator

# Try to import enhanced modules, fall back to basic if missing
try:
    from backend.scrapers.himalayas_scraper import HimalayasScraper
    HIMALAYAS_AVAILABLE = True
except ImportError:
    logger.info("Himalayas scraper not available")
    HIMALAYAS_AVAILABLE = False

try:
    from backend.scrapers.fixed_remoteok import FixedRemoteOKScraper
    FIXED_REMOTEOK_AVAILABLE = True
except ImportError:
    FIXED_REMOTEOK_AVAILABLE = False

try:
    from backend.services.enhanced_remote_detector import EnhancedRemoteDetector
    ENHANCED_DETECTOR_AVAILABLE = True
except ImportError:
    ENHANCED_DETECTOR_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_remote_job_basic(job_data: Dict[str, Any]) -> bool:
    """Basic remote job detection"""
    remote_keywords = [
        'remote', '100% remote', 'fully remote', 'work from home', 'wfh',
        'distributed', 'work from anywhere', 'location independent', 
        'remote first', 'remote friendly'
    ]
    
    # Check all text fields
    text_to_check = ' '.join([
        job_data.get('title', ''),
        job_data.get('description', ''),
        job_data.get('location', '')
    ]).lower()
    
    # Check for remote keywords
    for keyword in remote_keywords:
        if keyword in text_to_check:
            return True
    
    # Company-specific rules
    company = job_data.get('company', '').lower()
    always_remote_companies = ['gitlab', 'automattic', 'zapier', 'buffer']
    for remote_company in always_remote_companies:
        if remote_company in company:
            return True
    
    return False

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
    rate_limit = config.get('rate_limits', {}).get('default_delay', 2.0)
    
    # 1. Try Himalayas if available
    if HIMALAYAS_AVAILABLE:
        logger.info("🌟 Scraping Himalayas remote jobs")
        try:
            async with HimalayasScraper(rate_limit=rate_limit) as scraper:
                jobs = await scraper.scrape_jobs()
                all_jobs.extend(jobs)
                logger.info(f"✅ Himalayas: {len(jobs)} remote jobs")
        except Exception as e:
            logger.error(f"❌ Himalayas failed: {e}")
    
    # 2. Try Enhanced RemoteOK if available
    if FIXED_REMOTEOK_AVAILABLE:
        logger.info("🔄 Scraping RemoteOK with enhanced approach")
        try:
            async with FixedRemoteOKScraper(rate_limit=rate_limit * 2) as scraper:
                jobs = await scraper.scrape_jobs()
                all_jobs.extend(jobs)
                logger.info(f"✅ RemoteOK Enhanced: {len(jobs)} remote jobs")
        except Exception as e:
            logger.error(f"❌ RemoteOK Enhanced failed: {e}")
    
    # 3. We Work Remotely RSS (This should work)
    logger.info("📡 Scraping We Work Remotely RSS")
    try:
        async with GenericScraper(
            "https://weworkremotely.com/remote-jobs.rss",
            "We Work Remotely",
            "rss",
            rate_limit=rate_limit
        ) as scraper:
            jobs = await scraper.scrape_jobs()
            all_jobs.extend(jobs)
            logger.info(f"✅ We Work Remotely: {len(jobs)} remote jobs")
    except Exception as e:
        logger.error(f"❌ We Work Remotely failed: {e}")
    
    # 4. Greenhouse Companies with enhanced remote detection
    logger.info("🏢 Scraping Greenhouse companies")
    greenhouse_companies = config.get('greenhouse_companies', [])
    
    # Use enhanced detector if available
    if ENHANCED_DETECTOR_AVAILABLE:
        remote_detector = EnhancedRemoteDetector()
    else:
        remote_detector = None
    
    for company in greenhouse_companies[:6]:  # Limit to first 6 to avoid too many requests
        try:
            async with GreenHouseScraper(
                company['slug'],
                company['name'],
                rate_limit=rate_limit
            ) as scraper:
                all_company_jobs = await scraper.scrape_jobs()
                
                # Enhanced remote detection
                remote_jobs = []
                for job in all_company_jobs:
                    if remote_detector:
                        is_remote = remote_detector.is_remote_job(job)
                    else:
                        is_remote = is_remote_job_basic(job)
                    
                    if is_remote:
                        job['remote'] = True
                        remote_jobs.append(job)
                
                all_jobs.extend(remote_jobs)
                logger.info(f"✅ {company['name']}: {len(remote_jobs)}/{len(all_company_jobs)} remote jobs")
                
        except Exception as e:
            logger.error(f"❌ {company['name']} failed: {e}")
    
    # 5. Working Nomads (reliable source)
    logger.info("⚡ Scraping Working Nomads")
    try:
        async with GenericScraper(
            "https://www.workingnomads.co/api/exposed_jobs",
            "Working Nomads",
            "json",
            rate_limit=rate_limit
        ) as scraper:
            jobs = await scraper.scrape_jobs()
            all_jobs.extend(jobs)
            logger.info(f"✅ Working Nomads: {len(jobs)} remote jobs")
    except Exception as e:
        logger.error(f"❌ Working Nomads failed: {e}")
    
    return all_jobs

async def main():
    logger.info("🚀 Starting Enhanced Remote Jobs Scraper")
    logger.info("🎯 Focusing on reliable remote job sources")
    
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
        
        # Show analytics
        sources = {}
        domains = {}
        for job in unique_jobs:
            source = job.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
            domain = job.get('domain', 'Other')
            domains[domain] = domains.get(domain, 0) + 1
        
        logger.info("📈 Jobs by source:")
        for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"   {source}: {count} jobs")
        
        logger.info("🏷️ Jobs by domain:")
        for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"   {domain}: {count} jobs")
        
        logger.info("💼 Sample remote jobs:")
        for job in unique_jobs[:5]:
            logger.info(f"   🌐 {job['title']} at {job['company']} ({job['domain']}) - {job['source']}")
        
        return {
            "status": "completed",
            "jobs_scraped": len(raw_jobs),
            "jobs_unique": len(unique_jobs),
            "jobs_saved": len(unique_jobs),
            "top_sources": dict(list(sources.items())[:5])
        }
        
    except Exception as e:
        logger.error(f"💥 Scraper failed: {e}")
        return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"🎯 Enhanced Remote Jobs Scraper Result: {result}")