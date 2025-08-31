#!/usr/bin/env python3
import asyncio
import json
import os
import sys
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from scripts.run_scraper import scrape_all_sources
from backend.services.job_classifier import JobClassifier

async def export_jobs():
    print("🚀 Starting job scraper and export...")
    
    # Get all jobs
    print("📡 Scraping jobs from all sources...")
    jobs = await scrape_all_sources()
    
    if not jobs:
        print("❌ No jobs found!")
        return
    
    # Classify jobs
    print("🏷️ Classifying jobs by domain...")
    classifier = JobClassifier()
    for job in jobs:
        job['domain'] = classifier.classify_job(job)
    
    # Add export timestamp
    export_data = {
        "export_timestamp": datetime.utcnow().isoformat() + "Z",
        "total_jobs": len(jobs),
        "jobs": jobs
    }
    
    # Save to JSON file
    output_file = 'scraped_jobs.json'
    print(f"💾 Saving {len(jobs)} jobs to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, default=str)
    
    # Create HTML browser
    print("🌐 Creating HTML job browser...")
    await create_html_browser(jobs)
    
    # Generate summary stats
    print("📊 Generating summary statistics...")
    create_summary_stats(jobs)
    
    print(f"✅ Export completed successfully!")
    print(f"📄 Files created: scraped_jobs.json, job_browser.html, jobs_summary.txt")

async def create_html_browser(jobs):
    """Create an interactive HTML browser for jobs"""
    
    # Calculate stats
    remote_count = sum(1 for j in jobs if j.get('remote'))
    companies = set(j['company'] for j in jobs)
    domains = {}
    for job in jobs:
        domain = job.get('domain', 'Other')
        domains[domain] = domains.get(domain, 0) + 1
    
    # Create HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Remote Jobs Browser - {len(jobs)} Jobs Found</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; line-height: 1.6; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 20px; border-radius: 15px; margin-bottom: 30px; text-align: center; }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .header p {{ font-size: 1.2em; opacity: 0.9; }}
        
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
        .stat-card {{ background: white; padding: 25px; border-radius: 10px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #667eea; }}
        .stat-label {{ color: #64748b; margin-top: 5px; }}
        
        .filters {{ background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .filter-row {{ display: flex; gap: 15px; align-items: center; flex-wrap: wrap; }}
        .filter-group {{ display: flex; flex-direction: column; }}
        .filter-group label {{ font-weight: 600; margin-bottom: 5px; color: #374151; }}
        .filter-group input, .filter-group select {{ padding: 8px 12px; border: 2px solid #e5e7eb; border-radius: 6px; font-size: 14px; }}
        .filter-group input:focus, .filter-group select:focus {{ outline: none; border-color: #667eea; }}
        
        .job-grid {{ display: grid; gap: 20px; }}
        .job-card {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); border-left: 4px solid #667eea; transition: transform 0.2s; }}
        .job-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 20px rgba(0,0,0,0.15); }}
        
        .job-title {{ font-size: 1.4em; font-weight: 700; color: #1f2937; margin-bottom: 8px; }}
        .job-company {{ font-size: 1.1em; color: #667eea; font-weight: 600; margin-bottom: 15px; }}
        .job-meta {{ display: flex; gap: 10px; margin-bottom: 15px; flex-wrap: wrap; }}
        .badge {{ padding: 4px 12px; border-radius: 20px; font-size: 0.85em; font-weight: 500; }}
        .badge.remote {{ background: #10b981; color: white; }}
        .badge.onsite {{ background: #6b7280; color: white; }}
        .badge.domain {{ background: #3b82f6; color: white; }}
        .badge.location {{ background: #f59e0b; color: white; }}
        
        .job-description {{ color: #4b5563; margin: 15px 0; line-height: 1.6; }}
        .job-actions {{ display: flex; justify-content: space-between; align-items: center; margin-top: 20px; }}
        .apply-btn {{ background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: 600; transition: background 0.2s; }}
        .apply-btn:hover {{ background: #5a67d8; }}
        .job-source {{ font-size: 0.9em; color: #9ca3af; }}
        
        .no-results {{ text-align: center; padding: 60px 20px; color: #6b7280; }}
        .no-results h3 {{ font-size: 1.5em; margin-bottom: 10px; }}
        
        @media (max-width: 768px) {{
            .filter-row {{ flex-direction: column; align-items: stretch; }}
            .filter-group {{ width: 100%; }}
            .job-meta {{ justify-content: center; }}
            .job-actions {{ flex-direction: column; gap: 15px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Remote Jobs Browser</h1>
            <p>Discovered <strong>{len(jobs):,}</strong> opportunities from top companies</p>
            <p><small>Last updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p UTC')}</small></p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{len(jobs):,}</div>
                <div class="stat-label">Total Jobs</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{remote_count:,}</div>
                <div class="stat-label">Remote Jobs</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(companies)}</div>
                <div class="stat-label">Companies</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(domains)}</div>
                <div class="stat-label">Job Domains</div>
            </div>
        </div>
        
        <div class="filters">
            <div class="filter-row">
                <div class="filter-group">
                    <label>Search Jobs</label>
                    <input type="text" id="searchInput" placeholder="Search by title, company, or description...">
                </div>
                <div class="filter-group">
                    <label>Domain</label>
                    <select id="domainFilter">
                        <option value="">All Domains</option>
                        {chr(10).join(f'<option value="{domain}">{domain} ({count})</option>' for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True))}
                    </select>
                </div>
                <div class="filter-group">
                    <label>Work Type</label>
                    <select id="remoteFilter">
                        <option value="">All Jobs</option>
                        <option value="remote">Remote Only ({remote_count})</option>
                        <option value="onsite">On-site Only ({len(jobs) - remote_count})</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label>Company</label>
                    <select id="companyFilter">
                        <option value="">All Companies</option>
                        {chr(10).join(f'<option value="{company}">{company}</option>' for company in sorted(companies))}
                    </select>
                </div>
            </div>
        </div>
        
        <div class="job-grid" id="jobGrid">
"""
    
    # Add jobs
    for job in jobs:
        remote_badge = '<span class="badge remote">🌐 Remote</span>' if job.get('remote') else '<span class="badge onsite">🏢 On-site</span>'
        domain_badge = f'<span class="badge domain">{job["domain"]}</span>'
        location_badge = f'<span class="badge location">📍 {job.get("location", "Not specified")}</span>'
        
        description = job.get('description', '')
        if len(description) > 400:
            description = description[:400] + '...'
        
        html += f"""
            <div class="job-card" data-domain="{job['domain']}" data-remote="{str(job.get('remote', False)).lower()}" data-company="{job['company']}" data-searchtext="{job['title'].lower()} {job['company'].lower()} {description.lower()}">
                <div class="job-title">{job['title']}</div>
                <div class="job-company">{job['company']}</div>
                <div class="job-meta">
                    {remote_badge}
                    {domain_badge}
                    {location_badge}
                </div>
                <div class="job-description">{description}</div>
                <div class="job-actions">
                    <div class="job-source">via {job['source']}</div>
                    <a href="{job['apply_url']}" target="_blank" class="apply-btn" rel="noopener noreferrer">Apply Now →</a>
                </div>
            </div>
        """
    
    html += """
        </div>
        
        <div class="no-results" id="noResults" style="display: none;">
            <h3>🔍 No jobs match your filters</h3>
            <p>Try adjusting your search criteria or clearing some filters</p>
        </div>
    </div>
    
    <script>
        // Filter functionality
        const searchInput = document.getElementById('searchInput');
        const domainFilter = document.getElementById('domainFilter');
        const remoteFilter = document.getElementById('remoteFilter');
        const companyFilter = document.getElementById('companyFilter');
        const jobGrid = document.getElementById('jobGrid');
        const noResults = document.getElementById('noResults');
        
        function filterJobs() {
            const searchTerm = searchInput.value.toLowerCase();
            const selectedDomain = domainFilter.value;
            const selectedRemote = remoteFilter.value;
            const selectedCompany = companyFilter.value;
            
            const jobCards = jobGrid.querySelectorAll('.job-card');
            let visibleCount = 0;
            
            jobCards.forEach(card => {
                const matchesSearch = searchTerm === '' || card.dataset.searchtext.includes(searchTerm);
                const matchesDomain = selectedDomain === '' || card.dataset.domain === selectedDomain;
                const matchesRemote = selectedRemote === '' || 
                    (selectedRemote === 'remote' && card.dataset.remote === 'true') ||
                    (selectedRemote === 'onsite' && card.dataset.remote === 'false');
                const matchesCompany = selectedCompany === '' || card.dataset.company === selectedCompany;
                
                const shouldShow = matchesSearch && matchesDomain && matchesRemote && matchesCompany;
                card.style.display = shouldShow ? 'block' : 'none';
                
                if (shouldShow) visibleCount++;
            });
            
            // Show/hide no results message
            if (visibleCount === 0) {
                jobGrid.style.display = 'none';
                noResults.style.display = 'block';
            } else {
                jobGrid.style.display = 'grid';
                noResults.style.display = 'none';
            }
        }
        
        // Add event listeners
        searchInput.addEventListener('input', filterJobs);
        domainFilter.addEventListener('change', filterJobs);
        remoteFilter.addEventListener('change', filterJobs);
        companyFilter.addEventListener('change', filterJobs);
        
        // Add search shortcut
        document.addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.key === 'f') {
                e.preventDefault();
                searchInput.focus();
            }
        });
        
        console.log('🚀 Job browser loaded with """ + str(len(jobs)) + """ jobs');
    </script>
</body>
</html>"""
    
    with open('job_browser.html', 'w', encoding='utf-8') as f:
        f.write(html)

def create_summary_stats(jobs):
    """Create a text summary of the job statistics"""
    
    remote_count = sum(1 for j in jobs if j.get('remote'))
    companies = {}
    domains = {}
    locations = {}
    
    for job in jobs:
        # Count by company
        company = job['company']
        companies[company] = companies.get(company, 0) + 1
        
        # Count by domain
        domain = job.get('domain', 'Other')
        domains[domain] = domains.get(domain, 0) + 1
        
        # Count by location
        location = job.get('location', 'Not specified')
        locations[location] = locations.get(location, 0) + 1
    
    # Create summary text
    summary = f"""📊 JOB SCRAPING SUMMARY
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

🎯 OVERVIEW
Total Jobs Found: {len(jobs):,}
Remote Jobs: {remote_count:,} ({remote_count/len(jobs)*100:.1f}%)
On-site Jobs: {len(jobs) - remote_count:,} ({(len(jobs) - remote_count)/len(jobs)*100:.1f}%)
Companies: {len(companies)}
Job Domains: {len(domains)}

🏢 TOP COMPANIES
{chr(10).join(f"{company}: {count} jobs" for company, count in sorted(companies.items(), key=lambda x: x[1], reverse=True)[:10])}

🏷️ JOBS BY DOMAIN
{chr(10).join(f"{domain}: {count} jobs" for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True))}

📍 TOP LOCATIONS
{chr(10).join(f"{location}: {count} jobs" for location, count in sorted(locations.items(), key=lambda x: x[1], reverse=True)[:10])}

🔗 SAMPLE REMOTE JOBS
{chr(10).join(f"• {job['title']} at {job['company']} ({job['domain']})" for job in [j for j in jobs if j.get('remote')][:5])}

📁 FILES GENERATED
- scraped_jobs.json - Complete job data in JSON format
- job_browser.html - Interactive web interface for browsing jobs
- jobs_summary.txt - This summary file
"""
    
    with open('jobs_summary.txt', 'w', encoding='utf-8') as f:
        f.write(summary)

if __name__ == "__main__":
    asyncio.run(export_jobs())