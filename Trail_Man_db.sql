CREATE DATABASE IF NOT EXISTS trail_man_db;
USE trail_man_db;

-- Users table (managed by Clerk, but we keep reference)
CREATE TABLE users (
    id VARCHAR(255) PRIMARY KEY,  -- Clerk user ID
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Profiles table
CREATE TABLE profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    phone VARCHAR(20),
    location VARCHAR(255),
    experience TEXT,
    education TEXT,
    skills TEXT,
    linkedin_url VARCHAR(255),
    github_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Jobs table with source tracking for automated job aggregation
CREATE TABLE jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    description TEXT,
    requirements TEXT,
    salary_range VARCHAR(100),
    job_type ENUM('full-time', 'part-time', 'contract', 'internship'),
    remote_type ENUM('onsite', 'remote', 'hybrid'),
    external_url VARCHAR(500),
    posted_date DATETIME,
    source VARCHAR(100) DEFAULT 'manual' COMMENT 'Source of the job listing (greenhouse, lever, workday, etc.)',
    source_url VARCHAR(500) COMMENT 'Original URL of the job posting',
    source_job_id VARCHAR(255) COMMENT 'Unique ID from the source system',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_title (title),
    INDEX idx_company (company),
    INDEX idx_source (source),
    INDEX idx_posted_date (posted_date),
    UNIQUE KEY unique_source_job (source, source_job_id)
);

-- Resumes table with LaTeX support
CREATE TABLE resumes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    latex_content TEXT,
    pdf_url VARCHAR(500),
    template_name VARCHAR(100),
    last_compiled_at TIMESTAMP NULL,
    compilation_error TEXT,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_template (user_id, template_name),
    INDEX idx_compiled (last_compiled_at)
);

-- Applications table
CREATE TABLE applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    job_id INT NOT NULL,
    resume_id INT,
    status ENUM('applied', 'screening', 'interview', 'rejected', 'accepted') DEFAULT 'applied',
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE SET NULL,
    UNIQUE KEY unique_application (user_id, job_id)
);

-- Company scrapers configurations table to manage ATS scraper settings
CREATE TABLE company_scrapers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    scraper_type ENUM('greenhouse', 'lever', 'workday', 'icims', 'jobvite', 'custom') NOT NULL,
    config JSON COMMENT 'JSON configuration for the scraper (tokens, URLs, etc.)',
    is_active BOOLEAN DEFAULT TRUE,
    last_scraped_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_company_scraper (company_name, scraper_type),
    INDEX idx_company_scrapers_active (is_active),
    INDEX idx_company (company_name),
    INDEX idx_type (scraper_type)
);

-- Scraping logs table to track scraping performance and issues
CREATE TABLE scraping_logs (
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

-- Insert some example company configurations
INSERT INTO company_scrapers (company_name, scraper_type, config) VALUES
('Stripe', 'greenhouse', '{"company_token": "stripe"}'),
('Netflix', 'lever', '{"company_handle": "netflix"}'),
('Spotify', 'greenhouse', '{"company_token": "spotify"}'),
('Airbnb', 'greenhouse', '{"company_token": "airbnb"}'),
('Uber', 'lever', '{"company_handle": "uber"}'),
('Apple', 'workday', '{"careers_url": "https://jobs.apple.com/en-us/search"}'),
('Microsoft', 'workday', '{"careers_url": "https://careers.microsoft.com/us/en/search-results"}'),
('Google', 'lever', '{"company_handle": "google"}'),
('Meta', 'lever', '{"company_handle": "meta"}'),
('GitHub', 'lever', '{"company_handle": "github"}')
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
