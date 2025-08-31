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
from backend.scrapers.remote_boards import RemoteOKScraper, WeWorkRemotelyScraper
from backend.services.job_classifier import JobClassifier
from backend.services.deduplicator import JobDeduplicator
from backend.database import get_database

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
    
    # 1. Scrape Remote Job Boards First (highest remote job ratio)
    logger.info("🌐 Scraping dedicated remote job boards...")
    
    # RemoteOK
    try:
        async with RemoteOKScraper(rate_limit=rate_limit) as scraper:
            jobs = await scraper.scrape_jobs()
            all_jobs.extend(jobs)
            logger.info(f"✅ RemoteOK: {len(jobs)} jobs")
    except Exception as e:
        logger.error(f"❌ RemoteOK failed: {e}")
    
    # We Work Remotely
    try:
        async with WeWorkRemotelyScraper(rate_limit=rate_limit) as scraper:
            jobs = await scraper.scrape_jobs()
            all_jobs.extend(jobs)
            logger.info(f"✅ We Work Remotely: {len(jobs)} jobs")
    except Exception as e:
        logger.error(f"❌ We Work Remotely failed: {e}")
    
    # 2. Scrape Greenhouse Companies (filter for remote)
    logger.info("🏢 Scraping Greenhouse companies...")
    greenhouse_companies = config.get('greenhouse_companies', [])
    for company in greenhouse_companies:
        try:
            async with GreenHouseScraper(
                company['slug'], 
                company['name'], 
                rate_limit=rate_limit
            ) as scraper:
                jobs = await scraper.scrape_jobs()
                # Filter for remote jobs only
                remote_jobs = [job for job in jobs if job.get('remote', False)]
                all_jobs.extend(remote_jobs)
                logger.info(f"✅ {company['name']}: {len(remote_jobs)}/{len(jobs)} remote jobs")
        except Exception as e:
            logger.error(f"❌ {company['name']} failed: {e}")
    
    # 3. Scrape Lever Companies (filter for remote)
    logger.info("🔧 Scraping Lever companies...")
    lever_companies = config.get('lever_companies', [])
    for company in lever_companies:
        try:
            async with LeverScraper(
                company['slug'], 
                company['name'], 
                rate_limit=rate_limit
            ) as scraper:
                jobs = await scraper.scrape_jobs()
                # Filter for remote jobs only
                remote_jobs = [job for job in jobs if job.get('remote', False)]
                all_jobs.extend(remote_jobs)
                logger.info(f"✅ {company['name']}: {len(remote_jobs)}/{len(jobs)} remote jobs")
        except Exception as e:
            logger.error(f"❌ {company['name']} failed: {e}")
    
    # 4. Scrape Generic Feeds (remote job aggregators)
    logger.info("📡 Scraping generic remote job feeds...")
    generic_feeds = config.get('generic_feeds', [])
    for feed in generic_feeds:
        if feed.get('enabled', True):  # Skip disabled feeds
            try:
                async with GenericScraper(
                    feed['url'], 
                    feed['name'], 
                    feed.get('type', 'json'),
                    rate_limit=rate_limit
                ) as scraper:
                    jobs = await scraper.scrape_jobs()
                    # These are already remote job sources
                    all_jobs.extend(jobs)
                    logger.info(f"✅ {feed['name']}: {len(jobs)} jobs")
            except Exception as e:
                logger.error(f"❌ {feed['name']} failed: {e}")
    
    return all_jobs

async def main():
    logger.info("🚀 Starting REMOTE JOBS scraper...")
    logger.info("🎯 Only collecting REMOTE opportunities from multiple sources")
    
    try:
        # Scrape all sources
        raw_jobs = await scrape_all_sources()
        logger.info(f"📊 Scraped {len(raw_jobs)} total jobs from all sources")
        
        if not raw_jobs:
            logger.warning("❌ No jobs found from any source")
            return {"status": "completed", "jobs_saved": 0}
        
        # Double-check remote filtering
        remote_jobs = [job for job in raw_jobs if job.get('remote', True)]
        logger.info(f"🌐 Remote jobs after filtering: {len(remote_jobs)}/{len(raw_jobs)}")
        
        # Process jobs
        classifier = JobClassifier()
        deduplicator = JobDeduplicator()
        
        for job in remote_jobs:
            job['domain'] = classifier.classify_job(job)
        
        # Deduplicate
        unique_jobs = deduplicator.deduplicate_jobs(remote_jobs, set())
        logger.info(f"✨ Unique remote jobs: {len(unique_jobs)}")
        
        # Show sample jobs by source
        sources = {}
        for job in unique_jobs:
            source = job.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
        
        logger.info("📈 Jobs by source:")
        for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"   {source}: {count} jobs")
        
        # Show domain breakdown
        domains = {}
        for job in unique_jobs:
            domain = job.get('domain', 'Other')
            domains[domain] = domains.get(domain, 0) + 1
        
        logger.info("🏷️ Jobs by domain:")
        for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"   {domain}: {count} jobs")
        
        # Show sample jobs
        logger.info("💼 Sample remote jobs found:")
        for job in unique_jobs[:5]:
            logger.info(f"   🌐 {job['title']} at {job['company']} ({job['domain']}) - {job['source']}")
        
        return {
            "status": "completed",
            "jobs_scraped": len(raw_jobs),
            "jobs_remote": len(remote_jobs),
            "jobs_unique": len(unique_jobs),
            "jobs_saved": len(unique_jobs)
        }
        
    except Exception as e:
        logger.error(f"💥 Scraper failed: {e}")
        return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"🎯 Remote Jobs Scraper Result: {result}")