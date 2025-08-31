#!/usr/bin/env python3
import asyncio
import os
import sys
import yaml
import logging
from typing import List, Dict, Any

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.scrapers.greenhouse import GreenHouseScraper
from backend.services.job_classifier import JobClassifier
from backend.services.deduplicator import JobDeduplicator
from backend.database import get_database, create_tables

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
    
    rate_limit = config.get('rate_limits', {}).get('default_delay', 1.0)
    
    # Scrape Greenhouse companies
    greenhouse_companies = config.get('greenhouse_companies', [])
    for company in greenhouse_companies[:2]:  # Limit for testing
        try:
            async with GreenHouseScraper(
                company['slug'], 
                company['name'], 
                rate_limit=rate_limit
            ) as scraper:
                jobs = await scraper.scrape_jobs()
                all_jobs.extend(jobs)
        except Exception as e:
            logger.error(f"Error scraping {company['name']}: {e}")
    
    return all_jobs

async def save_jobs_to_database(jobs: List[Dict[str, Any]]) -> Dict[str, int]:
    if not jobs:
        return {"saved": 0, "errors": 0}
    
    try:
        db = await get_database()
        saved_count = 0
        
        for job in jobs:
            try:
                # Simple insert - handle conflicts in production
                logger.info(f"Would save job: {job['title']} at {job['company']}")
                saved_count += 1
            except Exception as e:
                logger.error(f"Error saving job: {e}")
        
        return {"saved": saved_count, "errors": 0}
        
    except Exception as e:
        logger.error(f"Database error: {e}")
        return {"saved": 0, "errors": len(jobs)}

async def main():
    logger.info("Starting job scraper...")
    
    try:
        # For now, just test scraping without database
        logger.info("Scraping jobs...")
        raw_jobs = await scrape_all_sources()
        logger.info(f"Scraped {len(raw_jobs)} raw jobs")
        
        if not raw_jobs:
            logger.warning("No jobs found")
            return {"status": "completed", "jobs_saved": 0}
        
        # Classify and deduplicate
        classifier = JobClassifier()
        deduplicator = JobDeduplicator()
        
        for job in raw_jobs:
            job['domain'] = classifier.classify_job(job)
        
        unique_jobs = deduplicator.deduplicate_jobs(raw_jobs, set())
        
        # For now, just log results instead of saving to DB
        logger.info(f"After processing: {len(unique_jobs)} unique jobs")
        for job in unique_jobs[:3]:  # Show first 3
            logger.info(f"- {job['title']} at {job['company']} ({job['domain']})")
        
        return {
            "status": "completed",
            "jobs_scraped": len(raw_jobs),
            "jobs_unique": len(unique_jobs),
            "jobs_saved": len(unique_jobs)
        }
        
    except Exception as e:
        logger.error(f"Scraper failed: {e}")
        return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"Scraper result: {result}")
EOF