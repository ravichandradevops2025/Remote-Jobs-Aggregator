-- Initialize database schema for Remote Jobs Aggregator

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

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_jobs_domain ON jobs(domain);
CREATE INDEX IF NOT EXISTS idx_jobs_remote ON jobs(remote);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);

-- Insert some sample data for testing
INSERT INTO jobs (id, title, company, description, apply_url, location, remote, domain, source, source_job_id) 
VALUES 
    ('sample-1', 'Senior Backend Engineer', 'TechCorp', 'We are looking for a senior backend engineer...', 'https://techcorp.com/jobs/backend-1', 'Remote', true, 'Backend', 'Manual', 'tc-001'),
    ('sample-2', 'Frontend Developer - React', 'WebStartup', 'Join our frontend team building amazing UIs...', 'https://webstartup.com/careers/frontend-1', 'San Francisco, CA', false, 'Frontend', 'Manual', 'ws-001'),
    ('sample-3', 'DevOps Engineer', 'CloudCo', 'Looking for DevOps engineer with Kubernetes experience...', 'https://cloudco.com/jobs/devops-1', 'Remote Worldwide', true, 'DevOps', 'Manual', 'cc-001')
ON CONFLICT (apply_url) DO NOTHING;