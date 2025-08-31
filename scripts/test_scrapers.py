#!/usr/bin/env python3
"""
Test script for scrapers - useful for development and debugging
"""

import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.scrapers.greenhouse import GreenHouseScraper
from backend.scrapers.lever import LeverScraper
from backend.scrapers.generic import GenericScraper

async def test_greenhouse():
    print("Testing Greenhouse scraper...")
    async with GreenHouseScraper("airbnb", "Airbnb") as scraper:
        jobs = await scraper.scrape_jobs()
        print(f"Found {len(jobs)} Airbnb jobs")
        if jobs:
            print(f"Sample job: {jobs[0]['title']} at {jobs[0]['company']}")

async def test_lever():
    print("Testing Lever scraper...")
    async with LeverScraper("netflix", "Netflix") as scraper:
        jobs = await scraper.scrape_jobs()
        print(f"Found {len(jobs)} Netflix jobs")
        if jobs:
            print(f"Sample job: {jobs[0]['title']} at {jobs[0]['company']}")

async def test_generic():
    print("Testing Generic scraper...")
    async with GenericScraper("https://remoteok.io/api", "Remote OK", "json") as scraper:
        jobs = await scraper.scrape_jobs()
        print(f"Found {len(jobs)} Remote OK jobs")
        if jobs:
            print(f"Sample job: {jobs[0]['title']} at {jobs[0]['company']}")

async def main():
    await test_greenhouse()
    await test_lever()
    await test_generic()

if __name__ == "__main__":
    asyncio.run(main())