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
from backend.scrapers.himalayas_scraper import HimalayasScraper
from backend.scrapers.fixed_remoteok import FixedRemoteOKScraper
from backend.scrapers.generic import GenericScraper
from backend.services.job_classifier import JobClassifier
from backend.services.deduplicator import JobDeduplicator
from backend.services.enhanced_remote_detector import EnhancedRemoteDetector

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
    rate_limit = config.get('rate_limits', {}).get('default_delay', 2.0)
    
    # Initialize enhanced remote detector
    remote_detector = EnhancedRemoteDetector()
    
    # 1. 🌟 Himalayas API (Best working source)
    logger.info("🌟 Scraping Himalayas (Premium Remote Jobs)")
    try:
        async with HimalayasScraper(rate_limit=rate_limit) as scraper:
            jobs = await scraper.scrape_jobs()
            all_jobs.extend(jobs)
            logger.info(f"✅ Himalayas: {len(jobs)} remote jobs")
    except Exception as e:
        logger.error(f"❌ Himalayas failed: {e}")
    
    # 2. 🔄 RemoteOK (Fixed approach)
    logger.info("🔄 Scraping RemoteOK with enhanced headers")
    try:
        async with FixedRemoteOKScraper(rate_limit=rate_limit * 2) as scraper:  # Extra delay
            jobs = await scraper.scrape_jobs()
            all_jobs.extend(jobs)
            logger.info(f"✅ RemoteOK: {len(jobs)} remote jobs")
    except Exception as e:
        logger.error(f"❌ RemoteOK failed: {e}")
    
    # 3. 📡 We Work Remotely RSS (Reliable)
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
    
    # 4. 🏢 Enhanced Greenhouse Companies (Better remote detection)
    logger.info("🏢 Scraping Greenhouse companies with enhanced remote detection")
    greenhouse_companies = config.get('greenhouse_companies', [])
    for company in greenhouse_companies:
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
                    if remote_detector.is_remote_job(job):
                        job['remote'] = True
                        remote_jobs.append(job)
                
                all_jobs.extend(remote_jobs)
                logger.info(f"✅ {company['name']}: {len(remote_jobs)}/{len(all_company_jobs)} remote jobs")
                
        except Exception as e:
            logger.error(f"❌ {company['name']} failed: {e}")
    
    # 5. ⚡ Working Nomads (Additional source)
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
    logger.info("🚀 Starting ENHANCED Remote Jobs Scraper v2.0")
    logger.info("🎯 Focus: Remote jobs from Indian & Global companies")
    
    try:
        raw_jobs = await scrape_all_sources()
        logger.info(f"📊 Total jobs scraped: {len(raw_jobs)}")
        
        if not raw_jobs:
            logger.warning("❌ No jobs found from any source")
            return {"status": "completed", "jobs_saved": 0}
        
        # Enhanced processing
        classifier = JobClassifier()
        deduplicator = JobDeduplicator()
        remote_detector = EnhancedRemoteDetector()
        
        # Double-check remote status with enhanced detector
        verified_remote_jobs = []
        for job in raw_jobs:
            if remote_detector.is_remote_job(job):
                job['remote'] = True
                job['domain'] = classifier.classify_job(job)
                verified_remote_jobs.append(job)
        
        logger.info(f"🌐 Verified remote jobs: {len(verified_remote_jobs)}")
        
        # Deduplicate
        unique_jobs = deduplicator.deduplicate_jobs(verified_remote_jobs, set())
        logger.info(f"✨ Unique remote jobs: {len(unique_jobs)}")
        
        # Analytics
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
            "jobs_remote_verified": len(verified_remote_jobs),
            "jobs_unique": len(unique_jobs),
            "jobs_saved": len(unique_jobs),
            "top_sources": dict(list(sources.items())[:5])
        }
        
    except Exception as e:
        logger.error(f"💥 Enhanced scraper failed: {e}")
        return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"🎯 Enhanced Remote Jobs Scraper Result: {result}")