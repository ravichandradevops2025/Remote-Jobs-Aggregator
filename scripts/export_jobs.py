#!/usr/bin/env python3
import asyncio
import json
import os
import sys
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from scripts.run_scraper import scrape_all_sources
from backend.services.job_classifier import JobClassifier
from backend.services.date_filter import JobDateFilter

async def export_jobs():
    print("🚀 Starting job scraper with 15-day filtering...")
    
    # Get all jobs
    print("📡 Scraping jobs from all sources...")
    jobs = await scrape_all_sources()
    print(f"📊 Raw jobs scraped: {len(jobs)}")
    
    if not jobs:
        print("❌ No jobs found!")
        return
    
    # Apply 15-day filter
    print("📅 Filtering jobs from last 15 days...")
    date_filter = JobDateFilter(days_back=15)
    recent_jobs = date_filter.filter_recent_jobs(jobs)
    print(f"🗓️ Recent jobs (last 15 days): {len(recent_jobs)}")
    
    # Classify jobs
    print("🏷️ Classifying jobs by domain...")
    classifier = JobClassifier()
    for job in recent_jobs:
        job['domain'] = classifier.classify_job(job)
    
    # Add export metadata
    export_data = {
        "export_timestamp": datetime.utcnow().isoformat() + "Z",
        "filter_applied": "last_15_days",
        "total_jobs_scraped": len(jobs),
        "recent_jobs_count": len(recent_jobs),
        "jobs": recent_jobs
    }
    
    # Save to JSON
    output_file = 'scraped_jobs.json'
    print(f"💾 Saving {len(recent_jobs)} recent jobs to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, default=str)
    
    # Create HTML browser
    print("🌐 Creating HTML job browser...")
    await create_html_browser(recent_jobs)
    
    # Generate summary
    print("📊 Generating summary statistics...")
    create_summary_stats(recent_jobs, len(jobs))
    
    print(f"✅ Export completed successfully!")
    print(f"📄 Files created: scraped_jobs.json, job_browser.html, jobs_summary.txt")

async def create_html_browser(jobs):
    """Create HTML browser for recent jobs"""
    
    domains = {}
    sources = {}
    for job in jobs:
        domain = job.get('domain', 'Other')
        domains[domain] = domains.get(domain, 0) + 1
        source = job.get('source', 'Unknown')
        sources[source] = sources.get(source, 0) + 1
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Recent Remote Jobs - Last 15 Days ({len(jobs)} jobs)</title>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: system-ui, sans-serif; margin: 20px; background: #f5f7fa; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 20px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #667eea; }}
        .job-card {{ background: white; margin: 15px 0; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .job-title {{ font-size: 1.3em; font-weight: bold; color: #2d3748; margin-bottom: 8px; }}
        .job-company {{ font-size: 1.1em; color: #667eea; margin-bottom: 10px; }}
        .apply-btn {{ background: #667eea; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 10px; }}
        .badge {{ background: #e2e8f0; color: #2d3748; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; margin-right: 5px; }}
        .remote-badge {{ background: #48bb78; color: white; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📅 Recent Remote Jobs</h1>
        <p>Last 15 Days • {len(jobs)} Fresh Opportunities</p>
        <p><small>Updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</small></p>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <div class="stat-number">{len(jobs)}</div>
            <div>Recent Jobs</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{sum(1 for j in jobs if j.get('remote'))}</div>
            <div>Remote Jobs</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{len(set(j['company'] for j in jobs))}</div>
            <div>Companies</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">15</div>
            <div>Days Back</div>
        </div>
    </div>
"""
    
    for job in jobs[:100]:  # Limit to first 100 for HTML
        remote_badge = '<span class="badge remote-badge">🌐 Remote</span>' if job.get('remote') else ''
        domain_badge = f'<span class="badge">{job.get("domain", "Other")}</span>'
        
        html += f"""
    <div class="job-card">
        <div class="job-title">{job['title']}</div>
        <div class="job-company">🏢 {job['company']}</div>
        <div style="margin: 10px 0;">
            {remote_badge}
            {domain_badge}
            <span class="badge">📅 Recent</span>
            <span class="badge">📊 {job['source']}</span>
        </div>
        <a href="{job['apply_url']}" target="_blank" class="apply-btn">Apply Now →</a>
    </div>
        """
    
    html += """
</body>
</html>"""
    
    with open('job_browser.html', 'w', encoding='utf-8') as f:
        f.write(html)

def create_summary_stats(recent_jobs, total_scraped):
    """Create summary with 15-day focus"""
    
    sources = {}
    domains = {}
    companies = {}
    
    for job in recent_jobs:
        source = job.get('source', 'Unknown')
        sources[source] = sources.get(source, 0) + 1
        
        domain = job.get('domain', 'Other')
        domains[domain] = domains.get(domain, 0) + 1
        
        company = job.get('company', 'Unknown')
        companies[company] = companies.get(company, 0) + 1
    
    summary = f"""📅 RECENT REMOTE JOBS REPORT (LAST 15 DAYS)
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
Email: ravichandra.devops2025@gmail.com

🎯 FILTERING RESULTS
Total Jobs Scraped: {total_scraped}
Recent Jobs (15 days): {len(recent_jobs)}
Filter Efficiency: {len(recent_jobs)/total_scraped*100:.1f}% jobs are recent

🌐 REMOTE JOBS BREAKDOWN
Remote Jobs: {sum(1 for j in recent_jobs if j.get('remote'))}
On-site Jobs: {len(recent_jobs) - sum(1 for j in recent_jobs if j.get('remote'))}

📊 TOP SOURCES (LAST 15 DAYS)
{chr(10).join(f"{source}: {count} jobs" for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True)[:10])}

🏷️ JOBS BY DOMAIN
{chr(10).join(f"{domain}: {count} jobs" for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True))}

🏢 TOP HIRING COMPANIES
{chr(10).join(f"{company}: {count} jobs" for company, count in sorted(companies.items(), key=lambda x: x[1], reverse=True)[:10])}

📁 FILES IN ZIP PACKAGE
- scraped_jobs.json - {len(recent_jobs)} recent jobs with full data
- job_browser.html - Interactive browser (first 100 jobs)
- jobs_summary.txt - This detailed summary

⏰ NEXT UPDATE
Tomorrow at 1:00 AM IST (automated)
"""
    
    with open('jobs_summary.txt', 'w', encoding='utf-8') as f:
        f.write(summary)

if __name__ == "__main__":
    asyncio.run(export_jobs())
