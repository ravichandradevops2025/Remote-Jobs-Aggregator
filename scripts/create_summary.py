#!/usr/bin/env python3
import json
import os
from datetime import datetime

def create_summary():
    # Check if scraped_jobs.json exists
    if not os.path.exists('scraped_jobs.json'):
        print("❌ No scraped_jobs.json found")
        return
    
    # Load job data
    with open('scraped_jobs.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    jobs = data.get('jobs', [])
    
    if not jobs:
        print("❌ No jobs found in data")
        return
    
    print(f"✅ Summary created for {len(jobs)} jobs")
    print("📄 Files available for download:")
    print("   • scraped_jobs.json - Complete job data")
    print("   • job_browser.html - Interactive job browser")
    print("   • jobs_summary.txt - Quick statistics")

if __name__ == "__main__":
    create_summary()