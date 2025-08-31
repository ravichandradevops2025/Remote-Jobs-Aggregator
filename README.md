# Remote Jobs Aggregator

A complete, production-ready MVP that collects remote job listings from company career pages and public ATS APIs (Greenhouse, Lever, generic feeds), deduplicates and categorizes them, and serves them through a modern web interface.

## 🎯 Features

- **Automated Scraping**: Nightly collection at 01:00 AM IST via GitHub Actions
- **Multiple Sources**: Greenhouse, Lever APIs, and generic JSON/RSS feeds
- **Smart Classification**: Jobs tagged by domain (DevOps, Cloud/AWS, Java, Backend, Frontend, Data/ML, QA, PM)
- **Deduplication**: Prevents duplicate listings based on apply URL and similarity
- **Modern Frontend**: Next.js interface with filtering, search, and pagination
- **Production Ready**: Deployable to Vercel + Supabase with Docker support for local development

## 🚀 Quick Start (Non-Technical)

### Prerequisites
- GitHub account
- Supabase account (free)
- Vercel account (free)

### Step 1: Set Up Supabase Database
1. Go to [supabase.com](https://supabase.com) and create a free account
2. Click "New Project" and fill in:
   - Project Name: `remote-jobs-db`
   - Database Password: Choose a strong password
   - Region: Choose closest to you
3. Wait for project to be created (2-3 minutes)
4. Go to Settings > API and copy these values:
   - `Project URL` (starts with https://...)
   - `service_role` key (long string starting with eyJ...)
   - `anon public` key (another long string)
5. Go to SQL Editor and run this setup script:

```sql
-- Copy the contents from backend/migrations/init.sql here
CREATE TABLE IF NOT EXISTS jobs (
    id VARCHAR(255) PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    company VARCHAR(255) NOT NULL,
    description TEXT,
    apply_url VARCHAR(1000) NOT NULL UNIQUE,
    location VARCHAR(255),
    remote BOOLEAN DEFAULT false,
    salary_min INTEGER,
    salary_max INTEGER,
    domain VARCHAR(50) DEFAULT 'Other',
    source VARCHAR(100) NOT NULL,
    source_job_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_jobs_domain ON jobs(domain);
CREATE INDEX IF NOT EXISTS idx_jobs_remote ON jobs(remote);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);