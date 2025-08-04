# Job Aggregation System Setup Guide

This guide explains how to set up and use the automated job aggregation system for Trail-Man.

## Overview

The job aggregation system automatically scrapes job postings from major ATS (Applicant Tracking Systems) including:
- **Greenhouse**: API-based scraping
- **Lever**: API-based scraping  
- **Workday**: Selenium-based web scraping

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Frontend     │    │    Backend      │    │     Database    │
│                 │    │                 │    │                 │
│ Admin Dashboard │◄──►│  FastAPI        │◄──►│     MySQL       │
│                 │    │  Admin APIs     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │     Celery      │    │     Redis       │
                       │                 │    │                 │
                       │ • Workers       │◄──►│   Message       │
                       │ • Beat Scheduler│    │   Broker        │
                       │ • Flower UI     │    │                 │
                       └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │    Scrapers     │
                       │                 │
                       │ • Greenhouse    │
                       │ • Lever         │
                       │ • Workday       │
                       └─────────────────┘
```

## Quick Start

### 1. Database Setup

The database schema has been updated with source tracking fields:

```sql
-- New fields added to jobs table
ALTER TABLE jobs ADD COLUMN source VARCHAR(100) DEFAULT 'manual';
ALTER TABLE jobs ADD COLUMN source_url VARCHAR(500);
ALTER TABLE jobs ADD COLUMN source_job_id VARCHAR(255);
ALTER TABLE jobs ADD UNIQUE KEY unique_source_job (source, source_job_id);
```

### 2. Docker Setup

Start all services including Redis and Celery:

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f celery-worker
docker-compose logs -f celery-beat
```

### 3. Manual Setup (Development)

If you prefer to run services manually:

```bash
# 1. Install dependencies
cd backend
pip install -r requirements.txt

# 2. Start Redis
docker run -d -p 6379:6379 redis:alpine

# 3. Start Celery Worker
celery -A app.core.celery_app worker --loglevel=info

# 4. Start Celery Beat (scheduler)
celery -A app.core.celery_app beat --loglevel=info

# 5. Start Flower (monitoring UI)
celery -A app.core.celery_app flower --port=5555
```

## Configuration

### Environment Variables

Add these to your backend `.env` file:

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Database Configuration (if not already set)
DATABASE_URL=mysql+pymysql://root:password123@localhost:3307/trail_man_db
```

### Scraper Configuration

Scrapers can be configured in two ways:

#### Option 1: Database Configuration (Recommended)

Create scraper configurations in the database:

```sql
INSERT INTO scraper_configs (company_name, scraper_type, config_data, is_active) VALUES
('Stripe', 'greenhouse', '{"company_token": "stripe"}', 1),
('Netflix', 'lever', '{"company_handle": "netflix"}', 1),
('Apple', 'workday', '{"careers_url": "https://jobs.apple.com/en-us/search"}', 1);
```

#### Option 2: Hardcoded Configuration

The system falls back to hardcoded configurations in `app/scrapers/orchestrator.py`.

## Available Scrapers

### 1. Greenhouse Scraper

**API-based scraper for Greenhouse ATS**

Configuration:
```json
{
  "company_token": "stripe"
}
```

Example companies using Greenhouse:
- Stripe (`stripe`)
- Airbnb (`airbnb`)
- Robinhood (`robinhood`)

### 2. Lever Scraper

**API-based scraper for Lever ATS**

Configuration:
```json
{
  "company_handle": "netflix"
}
```

Example companies using Lever:
- Netflix (`netflix`)
- GitHub (`github`)
- Coursera (`coursera`)

### 3. Workday Scraper

**Selenium-based scraper for Workday ATS**

Configuration:
```json
{
  "careers_url": "https://jobs.apple.com/en-us/search",
  "wait_timeout": 10,
  "selectors": {
    "job_item": "[data-automation-id=\"jobItem\"]",
    "job_title": "[data-automation-id=\"jobTitle\"]"
  }
}
```

Example companies using Workday:
- Apple
- Microsoft 
- IBM

## Automated Scheduling

Jobs are automatically scraped on the following schedule:

- **2 AM UTC**: Daily scraping (all sources)
- **2 PM UTC**: Daily scraping (all sources)  
- **8 PM UTC**: Daily scraping (all sources)
- **1 AM UTC Monday**: Weekly cleanup of old jobs
- **8 AM UTC**: Daily scraping reports

## Admin API Endpoints

### Manual Triggers

```bash
# Trigger all scrapers
POST /admin/scraping/trigger-all

# Trigger specific company
POST /admin/scraping/trigger-company/stripe

# Test scraper configuration
POST /admin/scraping/test-scraper
{
  "company_name": "Stripe",
  "scraper_type": "greenhouse",
  "config": {"company_token": "stripe"}
}
```

### Monitoring

```bash
# Get task status
GET /admin/scraping/task-status/{task_id}

# Get scraper status
GET /admin/scraping/status

# Get scraping statistics
GET /admin/scraping/stats?days=7

# Health check
GET /admin/health/scraping
```

### Celery Management

```bash
# View active tasks
GET /admin/celery/active-tasks

# Revoke task
POST /admin/celery/revoke-task/{task_id}
```

## Monitoring Interfaces

### 1. Flower UI
Monitor Celery tasks at: http://localhost:5555

### 2. API Endpoints
Use the admin endpoints to monitor scraping status and statistics.

### 3. Database Logs
Check the `scraping_logs` table for detailed scraping history.

## Development Workflow

### Adding a New Scraper

1. **Create scraper class** in `app/scrapers/new_scraper.py`:
```python
from .base import BaseScraper, JobData

class NewScraper(BaseScraper):
    def get_job_listings(self) -> List[JobData]:
        # Implementation
        pass
```

2. **Register scraper** in `app/scrapers/orchestrator.py`:
```python
self.scraper_classes = {
    'greenhouse': GreenhouseScraper,
    'lever': LeverScraper,
    'workday': WorkdayScraper,
    'new_scraper': NewScraper  # Add here
}
```

3. **Add validation** function if needed.

### Testing Scrapers

```bash
# Test individual scraper
POST /admin/scraping/test-scraper
{
  "company_name": "Test Company",
  "scraper_type": "greenhouse", 
  "config": {"company_token": "test"}
}

# Validate all scrapers
POST /admin/scraping/validate-scrapers
```

## Common Issues & Troubleshooting

### 1. Chrome/Selenium Issues

If Workday scraper fails:
```bash
# Check Chrome installation
google-chrome --version

# Check ChromeDriver
chromedriver --version

# Install Chrome (Ubuntu/Debian)
sudo apt-get install google-chrome-stable
```

### 2. Redis Connection Issues

```bash
# Check Redis connection
redis-cli ping

# Check Redis logs
docker logs trail-man-redis
```

### 3. Celery Issues

```bash
# Check Celery worker status
celery -A app.core.celery_app inspect active

# Purge tasks
celery -A app.core.celery_app purge

# Check Celery logs
docker logs trail-man-celery-worker
```

### 4. Rate Limiting

If getting rate limited:
- Increase delays in scraper config
- Reduce scraping frequency
- Use different IP/proxy

## Performance Optimization

### 1. Concurrent Scraping

Adjust `max_concurrent` in orchestrator:
```python
orchestrator.scrape_all(max_concurrent=2)  # Reduce for rate limiting
```

### 2. Database Optimization

- Add indexes for frequent queries
- Regular cleanup of old jobs
- Monitor database performance

### 3. Redis Optimization

- Increase Redis memory if needed
- Monitor Redis memory usage
- Configure Redis persistence

## Security Considerations

1. **Rate Limiting**: Respect target sites' rate limits
2. **User Agents**: Use realistic browser user agents  
3. **IP Rotation**: Consider proxy rotation for large scale
4. **Data Privacy**: Handle scraped data according to privacy laws
5. **Access Control**: Restrict admin endpoints to authorized users

## Maintenance

### Weekly Tasks

1. Review scraping logs for errors
2. Check scraper configurations for broken ones
3. Update scraper selectors if sites change
4. Clean up old job postings
5. Monitor Redis/database storage usage

### Monthly Tasks

1. Update dependencies
2. Review and optimize scraping schedules
3. Add new target companies
4. Performance analysis and optimization

## Support

For issues with the job aggregation system:

1. Check logs in Flower UI (http://localhost:5555)
2. Review scraping_logs table in database
3. Test individual scrapers using admin APIs
4. Verify scraper configurations and credentials

## API Reference

### Data Models

#### JobData
```python
@dataclass
class JobData:
    title: str
    company: str  
    location: str
    description: str
    requirements: str
    salary_range: str
    job_type: str  # full-time, part-time, contract, internship
    remote_type: str  # onsite, remote, hybrid
    external_url: str
    posted_date: datetime
    source_job_id: str
    source_url: str
```

#### Database Schema
```sql
-- Updated jobs table
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
    source VARCHAR(100) DEFAULT 'manual',
    source_url VARCHAR(500),
    source_job_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_source_job (source, source_job_id)
);
``` 