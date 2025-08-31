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
from backend.scrapers.indian_companies import IndianCompanyScraper
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
    rate_limit = config.get('rate_limits', {}).get('default_delay', 3.0)
    remote_detector = EnhancedRemoteDetector()
    
    # 1. 🌍 Global Remote Job Boards
    logger.info("🌍 Scraping Global Remote Job Boards")
    global_boards = config.get('global_remote_boards', [])
    for board in global_boards:
        if board.get('working', False):
            try:
                async with GenericScraper(
                    board['url'], 
                    board['name'], 
                    board['type'],
                    rate_limit=rate_limit
                ) as scraper:
                    jobs = await scraper.scrape_jobs()
                    all_jobs.extend(jobs)
                    logger.info(f"✅ {board['name']}: {len(jobs)} jobs")
            except Exception as e:
                logger.error(f"❌ {board['name']} failed: {e}")
    
    # 2. 🇮🇳 Indian Product Companies (High Priority)
    logger.info("🇮🇳 Scraping Indian Product Companies")
    indian_companies = config.get('indian_companies', [])
    
    # Focus on top fintech & e-commerce companies first
    priority_companies = [
        {'name': 'Razorpay', 'careers_url': 'https://razorpay.com/careers/'},
        {'name': 'PhonePe', 'careers_url': 'https://www.phonepe.com/careers/'},
        {'name': 'CRED', 'careers_url': 'https://careers.cred.club/'},
        {'name': 'Swiggy', 'careers_url': 'https://careers.swiggy.com/'},
        {'name': 'Flipkart', 'careers_url': 'https://www.flipkartcareers.com/'},
        {'name': 'Freshworks', 'careers_url': 'https://www.freshworks.com/company/careers/'},
        {'name': 'Postman', 'careers_url': 'https://www.postman.com/company/careers/'}
    ]
    
    for company in priority_companies:
        try:
            async with IndianCompanyScraper(
                company['name'],
                company['careers_url'],
                rate_limit=rate_limit * 2  # Be extra respectful
            ) as scraper:
                jobs = await scraper.scrape_jobs()
                
                # Enhanced remote filtering for Indian companies
                remote_jobs = []
                for job in jobs:
                    if remote_detector.is_remote_job(job):
                        job['remote'] = True
                        remote_jobs.append(job)
                    elif 'remote' in job.get('title', '').lower():
                        job['remote'] = True
                        remote_jobs.append(job)
                
                all_jobs.extend(remote_jobs)
                logger.info(f"✅ {company['name']}: {len(remote_jobs)}/{len(jobs)} remote jobs")
                
        except Exception as e:
            logger.error(f"❌ {company['name']} failed: {e}")
    
    # 3. 🏢 Enhanced Greenhouse Companies  
    logger.info("🏢 Scraping Greenhouse Companies")
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
                logger.info(f"✅ {company['name']}: {len(remote_jobs)}/{len(all_company_jobs)} remote jobs")
                
        except Exception as e:
            logger.error(f"❌ {company['name']} failed: {e}")
    
    # 4. 💼 Tech-Specific Job Portals
    logger.info("💼 Scraping Tech-Specific Job Portals")
    
    # GitJobs (DevOps focus)
    try:
        async with GenericScraper(
            "https://gitjobs.dev/api/jobs",
            "GitJobs Dev",
            "json",
            rate_limit=rate_limit
        ) as scraper:
            jobs = await scraper.scrape_jobs()
            all_jobs.extend(jobs)
            logger.info(f"✅ GitJobs: {len(jobs)} DevOps/Cloud jobs")
    except Exception as e:
        logger.error(f"❌ GitJobs failed: {e}")
    
    # 5. 🔧 Lever Companies
    logger.info("🔧 Scraping Lever Companies")
    lever_companies = config.get('lever_companies', [])
    for company in lever_companies:
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
                logger.info(f"✅ {company['name']}: {len(remote_jobs)}/{len(all_company_jobs)} remote jobs")
                
        except Exception as e:
            logger.error(f"❌ {company['name']} failed: {e}")
    
    return all_jobs

async def main():
    logger.info("🚀 Starting COMPREHENSIVE Remote Jobs Scraper v3.0")
    logger.info("🎯 Indian Companies + Global Remote + Tech-Specific Sources")
    
    try:
        raw_jobs = await scrape_all_sources()
        logger.info(f"📊 Total jobs scraped: {len(raw_jobs)}")
        
        if not raw_jobs:
            logger.warning("❌ No jobs found from any source")
            return {"status": "completed", "jobs_saved": 0}
        
        # Enhanced processing
        classifier = JobClassifier()
        deduplicator = JobDeduplicator()
        
        # Classify all jobs with enhanced domains
        for job in raw_jobs:
            job['domain'] = classifier.classify_job(job)
        
        # Deduplicate
        unique_jobs = deduplicator.deduplicate_jobs(raw_jobs, set())
        logger.info(f"✨ Unique remote jobs: {len(unique_jobs)}")
        
        # Enhanced analytics
        sources = {}
        domains = {}
        companies = {}
        
        for job in unique_jobs:
            source = job.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
            
            domain = job.get('domain', 'Other')
            domains[domain] = domains.get(domain, 0) + 1
            
            company = job.get('company', 'Unknown')
            companies[company] = companies.get(company, 0) + 1
        
        logger.info("📈 Jobs by source:")
        for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"   {source}: {count} jobs")
        
        logger.info("🏷️ Jobs by domain:")
        for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"   {domain}: {count} jobs")
        
        logger.info("🏢 Top companies:")
        for company, count in list(sorted(companies.items(), key=lambda x: x[1], reverse=True))[:10]:
            logger.info(f"   {company}: {count} jobs")
        
        logger.info("💼 Sample remote jobs:")
        for job in unique_jobs[:7]:
            logger.info(f"   🌐 {job['title']} at {job['company']} ({job['domain']}) - {job['source']}")
        
        return {
            "status": "completed",
            "jobs_scraped": len(raw_jobs),
            "jobs_unique": len(unique_jobs),
            "jobs_saved": len(unique_jobs),
            "top_sources": dict(list(sources.items())[:5]),
            "top_domains": dict(list(domains.items())[:5]),
            "top_companies": dict(list(companies.items())[:5])
        }
        
    except Exception as e:
        logger.error(f"💥 Comprehensive scraper failed: {e}")
        return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"🎯 Comprehensive Remote Jobs Scraper Result: {result}")