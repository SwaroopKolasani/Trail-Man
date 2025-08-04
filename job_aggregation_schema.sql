-- job_aggregation_schema.sql
-- SQL Schema Updates for Trail-Man Job Aggregation System

-- Update jobs table to support source tracking
ALTER TABLE jobs 
ADD COLUMN source VARCHAR(100) DEFAULT 'manual' COMMENT 'Source of the job listing (greenhouse, lever, workday, etc.)';

ALTER TABLE jobs 
ADD COLUMN source_url VARCHAR(500) COMMENT 'Original URL of the job posting';

ALTER TABLE jobs 
ADD COLUMN source_job_id VARCHAR(255) COMMENT 'Unique ID from the source system';

-- Add unique constraint to prevent duplicate jobs from same source
ALTER TABLE jobs 
ADD CONSTRAINT unique_source_job UNIQUE (source, source_job_id);

-- Add index for better query performance
CREATE INDEX idx_jobs_source ON jobs(source);
CREATE INDEX idx_jobs_posted_date ON jobs(posted_date);

-- Update resumes table for LaTeX support
ALTER TABLE resumes 
ADD COLUMN latex_content TEXT COMMENT 'LaTeX source code for the resume';

ALTER TABLE resumes 
ADD COLUMN template_name VARCHAR(100) COMMENT 'Name of the template used';

ALTER TABLE resumes 
ADD COLUMN last_compiled_at TIMESTAMP NULL COMMENT 'Last successful compilation timestamp';

ALTER TABLE resumes 
ADD COLUMN compilation_error TEXT COMMENT 'Last compilation error message';

-- Create table for tracking scraping jobs (optional but recommended)
CREATE TABLE IF NOT EXISTS scraping_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source VARCHAR(100) NOT NULL,
    company_name VARCHAR(255),
    status ENUM('started', 'completed', 'failed') DEFAULT 'started',
    jobs_found INT DEFAULT 0,
    jobs_added INT DEFAULT 0,
    jobs_updated INT DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    INDEX idx_scraping_logs_source (source),
    INDEX idx_scraping_logs_status (status),
    INDEX idx_scraping_logs_started (started_at)
);

-- Create table for company configurations (for managing scraper settings)
CREATE TABLE IF NOT EXISTS company_scrapers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    scraper_type ENUM('greenhouse', 'lever', 'workday', 'icims', 'jobvite', 'custom') NOT NULL,
    config JSON COMMENT 'JSON configuration for the scraper (tokens, URLs, etc.)',
    is_active BOOLEAN DEFAULT TRUE,
    last_scraped_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_company_scraper (company_name, scraper_type),
    INDEX idx_company_scrapers_active (is_active)
);

-- Insert some example company configurations
INSERT INTO company_scrapers (company_name, scraper_type, config) VALUES
('Stripe', 'greenhouse', '{"company_token": "stripe"}'),
('Aquatic Capital Management', 'greenhouse', '{"company_token": "aquaticcapitalmanagement"}'),
('Netflix', 'lever', '{"company_handle": "netflix"}'),
('Spotify', 'greenhouse', '{"company_token": "spotify"}'),
('Airbnb', 'greenhouse', '{"company_token": "airbnb"}'),
('Uber', 'lever', '{"company_handle": "uber"}'),
('Apple', 'workday', '{"careers_url": "https://jobs.apple.com/en-us/search"}'),
('Microsoft', 'workday', '{"careers_url": "https://careers.microsoft.com/professionals/us/en/search-results"}'),
('Figma', 'lever', '{"company_handle": "figma"}'),
('Coinbase', 'greenhouse', '{"company_token": "coinbase"}'),
('DoorDash', 'greenhouse', '{"company_token": "doordash"}'),
('GitHub', 'lever', '{"company_handle": "github"}'),
('Google', 'workday', '{"careers_url": "https://careers.google.com/jobs/results"}'),
('Meta', 'greenhouse', '{"company_token": "meta"}'),
('Salesforce', 'lever', '{"company_handle": "salesforce"}'),
('Slack', 'greenhouse', '{"company_token": "slack"}'),
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- Create view for job statistics
CREATE OR REPLACE VIEW job_statistics AS
SELECT 
    source,
    COUNT(*) as total_jobs,
    COUNT(DISTINCT company) as unique_companies,
    DATE(MIN(created_at)) as first_job_date,
    DATE(MAX(created_at)) as last_job_date,
    COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 END) as jobs_last_7_days,
    COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 1 END) as jobs_last_30_days
FROM jobs
GROUP BY source;

-- Create view for application statistics
CREATE OR REPLACE VIEW application_statistics AS
SELECT 
    u.email,
    COUNT(DISTINCT a.id) as total_applications,
    COUNT(DISTINCT a.job_id) as unique_jobs_applied,
    COUNT(CASE WHEN a.status = 'applied' THEN 1 END) as status_applied,
    COUNT(CASE WHEN a.status = 'screening' THEN 1 END) as status_screening,
    COUNT(CASE WHEN a.status = 'interview' THEN 1 END) as status_interview,
    COUNT(CASE WHEN a.status = 'rejected' THEN 1 END) as status_rejected,
    COUNT(CASE WHEN a.status = 'accepted' THEN 1 END) as status_accepted,
    DATE(MIN(a.applied_at)) as first_application_date,
    DATE(MAX(a.applied_at)) as last_application_date
FROM applications a
JOIN users u ON a.user_id = u.id
GROUP BY u.id, u.email; 