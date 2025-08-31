#!/usr/bin/env python3
"""
Main scraper script that runs all job scrapers
Can be run manually or via GitHub Actions
"""

import asyncio
import os
import sys
import yaml
import logging
from typing import List, Dict, Any

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.scrapers.greenhouse import GreenHouseScraper
from backend.scrapers.lever import LeverScraper
from backend.scrapers.generic import GenericScraper
from backend.services.job_classifier import JobClassifier
from backend.services.deduplicator import JobDeduplicator
from backend.database import get_database, create_tables

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def load_sources_config() -> Dict[str, Any]:
    """Load sources configuration from YAML file"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'sources.yaml')
    
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error("sources.yaml not found")
        return {}
    except yaml.YAMLError as e:
        logger.error(f"Error parsing sources.yaml: {e}")
        return {}

async def scrape_all_sources() -> List[Dict[str, Any]]:
    """Scrape jobs from all configured sources"""
    config = await load_sources_config()
    all_jobs = []
    
    rate_limit = config.get('rate_limits', {}).get('default_delay', 1.0)
    
    # Scrape Greenhouse companies
    greenhouse_companies = config.get('greenhouse_companies', [])
    for company in greenhouse_companies:
        try:
            async with GreenHouseScraper(
                company['slug'], 
                company['name'], 
                rate_limit=rate_limit
            ) as scraper:
                jobs = await scraper.scrape_jobs()
                all_jobs.extend(jobs)
        except Exception as e:
            logger.error(f"Error scraping Greenhouse {company['name']}: {e}")
    
    # Scrape Lever companies  
    lever_companies = config.get('lever_companies', [])
    for company in lever_companies:
        try:
            async with LeverScraper(
                company['slug'], 
                company['name'], 
                rate_limit=rate_limit
            ) as scraper:
                jobs = await scraper.scrape_jobs()
                all_jobs.extend(jobs)
        except Exception as e:
            logger.error(f"Error scraping Lever {company['name']}: {e}")
    
    # Scrape generic feeds
    generic_feeds = config.get('generic_feeds', [])
    for feed in generic_feeds:
        try:
            async with GenericScraper(
                feed['url'], 
                feed['name'], 
                feed.get('type', 'json'),
                rate_limit=rate_limit
            ) as scraper:
                jobs = await scraper.scrape_jobs()
                all_jobs.extend(jobs)
        except Exception as e:
            logger.error(f"Error scraping generic feed {feed['name']}: {e}")
    
    return all_jobs

async def get_existing_job_urls() -> set:
    """Get existing job URLs from database to avoid duplicates"""
    try:
        db = await get_database()
        result = await db.fetch_all("SELECT apply_url FROM jobs")
        return {row[0] for row in result} if result else set()
    except Exception as e:
        logger.error(f"Error fetching existing URLs: {e}")
        return set()

async def save_jobs_to_database(jobs: List[Dict[str, Any]]) -> Dict[str, int]:
    """Save jobs to database"""
    if not jobs:
        return {"saved": 0, "errors": 0}
    
    try:
        db = await get_database()
        saved_count = 0
        error_count = 0
        
        for job in jobs:
            try:
                # Insert job
                insert_query = """
                INSERT INTO jobs (id, title, company, description, apply_url, location, 
                                remote, salary_min, salary_max, domain, source, source_job_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT (apply_url) DO NOTHING
                """
                
                await db.execute(insert_query, [
                    job['id'], job['title'], job['company'], job['description'],
                    job['apply_url'], job['location'], job['remote'],
                    job['salary_min'], job['salary_max'], job['domain'],
                    job['source'], job['source_job_id']
                ])
                
                saved_count += 1
                
            except Exception as e:
                logger.error(f"Error saving job {job.get('title', 'Unknown')}: {e}")
                error_count += 1
        
        return {"saved": saved_count, "errors": error_count}
        
    except Exception as e:
        logger.error(f"Database error: {e}")
        return {"saved": 0, "errors": len(jobs)}

async def main():
    """Main scraper function"""
    logger.info("Starting job scraper...")
    
    try:
        # Initialize database
        await create_tables()
        
        # Scrape all sources
        logger.info("Scraping all sources...")
        raw_jobs = await scrape_all_sources()
        logger.info(f"Scraped {len(raw_jobs)} raw jobs")
        
        if not raw_jobs:
            logger.warning("No jobs found from any source")
            return {"status": "completed", "jobs_saved": 0}
        
        # Get existing URLs to avoid duplicates
        existing_urls = await get_existing_job_urls()
        logger.info(f"Found {len(existing_urls)} existing jobs in database")
        
        # Deduplicate jobs
        deduplicator = JobDeduplicator()
        unique_jobs = deduplicator.deduplicate_jobs(raw_jobs, existing_urls)
        logger.info(f"After deduplication: {len(unique_jobs)} unique jobs")
        
        # Classify jobs by domain
        classifier = JobClassifier()
        for job in unique_jobs:
            job['domain'] = classifier.classify_job(job)
        
        # Save to database
        result = await save_jobs_to_database(unique_jobs)
        logger.info(f"Saved {result['saved']} jobs, {result['errors']} errors")
        
        return {
            "status": "completed",
            "jobs_scraped": len(raw_jobs),
            "jobs_unique": len(unique_jobs),
            "jobs_saved": result['saved'],
            "errors": result['errors']
        }
        
    except Exception as e:
        logger.error(f"Scraper failed: {e}")
        return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"Scraper result: {result}")