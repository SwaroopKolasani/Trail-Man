# Selenium Successfully Enabled for Trail-Man 🎉

Selenium is now fully enabled and configured for the Trail-Man job aggregation system. This enables automated web scraping of job postings from various ATS (Applicant Tracking Systems) including Workday.

## ✅ What's Working

### 1. Chrome Browser Integration
- **Chrome Installation**: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- **Status**: ✅ Detected and configured
- **Platform**: macOS (Darwin) with automatic path detection

### 2. ChromeDriver Management
- **Driver Manager**: webdriver-manager (automatic installation)
- **Path**: `/Users/swaroopkolasani/.wdm/drivers/chromedriver/mac64/138.0.7204.94/chromedriver-mac-arm64/chromedriver`
- **Status**: ✅ Installed and permissions fixed
- **Auto-Fix**: Handles path and permission issues automatically

### 3. Selenium Configuration
- **Mode**: Headless (configurable)
- **Timeout**: 30 seconds (configurable)
- **Status**: ✅ Fully functional
- **Options**: Anti-detection measures enabled

### 4. Integration with Trail-Man
- **WorkdayScraper**: ✅ Ready for Workday ATS scraping
- **Configuration**: Environment variables set
- **Error Handling**: Comprehensive error messages and fallbacks

## 🔧 Configuration

The following environment variables are configured in `backend/.env`:

```bash
# Selenium Configuration
SELENIUM_ENABLED=true
HEADLESS_BROWSER=true
BROWSER_TIMEOUT=30
CHROME_BIN=/Applications/Google Chrome.app/Contents/MacOS/Google Chrome

# Redis for Celery (job queue)
REDIS_URL=redis://localhost:6379/0
```

## 🧪 Testing Results

All tests passed successfully:

```
✅ Environment Variables: PASS
✅ Chrome Installation: PASS  
✅ ChromeDriver: PASS
✅ Selenium Basic: PASS
✅ Workday Scraper: PASS

Result: 5/5 tests passed
🎉 All tests passed! Selenium is ready for use.
```

## 🚀 Usage

### 1. Direct Scraper Usage

```python
from app.scrapers.workday import WorkdayScraper

# Configure for a Workday-based company
config = {
    'careers_url': 'https://company.workday.com/careers',
    'wait_timeout': 10,
    'selectors': {
        'job_item': '[data-automation-id="jobItem"]',
        'job_title': '[data-automation-id="jobTitle"]',
        'job_location': '[data-automation-id="jobLocation"]'
    }
}

scraper = WorkdayScraper('CompanyName', config)
jobs = scraper.get_job_listings()
```

### 2. Via Celery Tasks

```python
from app.tasks.scraping import scrape_single_company

# Queue a scraping task
result = scrape_single_company.delay('CompanyName', 'workday', config)
```

### 3. Via Admin API

```bash
curl -X POST http://localhost:8000/api/v1/admin/scraping/test-scraper \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "TestCompany",
    "scraper_type": "workday", 
    "config": {"careers_url": "https://company.workday.com/careers"}
  }'
```

## 🔍 Supported ATS Systems

### 1. Workday (Selenium-based)
- **Technology**: Dynamic JavaScript rendering
- **Scraper**: WorkdayScraper
- **Companies**: Apple, Microsoft, IBM, many Fortune 500s
- **Status**: ✅ Enabled with Selenium

### 2. Greenhouse (API-based)
- **Technology**: REST API
- **Scraper**: GreenhouseScraper  
- **Companies**: Stripe, Airbnb, Robinhood
- **Status**: ✅ Already working (no Selenium needed)

### 3. Lever (API-based)
- **Technology**: REST API
- **Scraper**: LeverScraper
- **Companies**: Netflix, GitHub, Coursera
- **Status**: ✅ Already working (no Selenium needed)

## 🐳 Docker Support

### Production Docker (with Chrome)
```bash
# Uses backend/Dockerfile with Chrome installation
docker-compose up --build
```

### Development Docker (LaTeX only)
```bash
# Uses backend/Dockerfile.dev (faster build, no Selenium)
docker-compose -f docker-compose.dev.yml up --build
```

## 🛠 Troubleshooting

### Common Issues & Solutions

1. **Chrome Not Found**
   ```bash
   # Install Chrome on macOS
   brew install --cask google-chrome
   ```

2. **Permission Denied**
   - Automatically fixed by the scraper
   - Manual fix: `chmod +x /path/to/chromedriver`

3. **ChromeDriver Version Mismatch**
   - Uses webdriver-manager for automatic updates
   - Manual: Delete `~/.wdm/drivers/` folder

4. **Memory Issues in Docker**
   ```yaml
   # Add to docker-compose.yml
   services:
     backend:
       deploy:
         resources:
           limits:
             memory: 2G
   ```

### Testing Commands

```bash
# Test Selenium setup
cd backend
python selenium_test.py

# Test scraping functionality  
python test_scraping.py

# Test specific scraper configuration
python -c "
from app.tasks.scraping import test_single_scraper
result = test_single_scraper('TestCompany', 'workday', {
    'careers_url': 'https://example.com/careers'
})
print(result)
"
```

## 📊 Performance & Monitoring

### Celery Queues
- **scraping**: Main job scraping tasks
- **scraping_priority**: High-priority single company scrapes
- **maintenance**: Cleanup and maintenance tasks

### Monitoring
```bash
# Monitor Celery workers
celery -A app.core.celery_app inspect active

# Monitor with Flower
celery -A app.core.celery_app flower --port=5555
# Visit http://localhost:5555
```

### Scheduled Jobs
- **Daily scraping**: 2 AM, 2 PM, 8 PM UTC
- **Weekly cleanup**: Monday 1 AM UTC
- **Daily reports**: 8 AM UTC

## 🔐 Security & Best Practices

### Rate Limiting
- Default 1-3 second delays between requests
- Configurable per scraper
- Respects robots.txt and terms of service

### Anti-Detection
- Realistic browser user agents
- Random delays and timeouts
- Headless browsing (appears as regular traffic)
- Chrome automation flags disabled

### Error Handling
- Graceful degradation on failures
- Comprehensive logging
- Automatic retries with exponential backoff
- Fallback to alternative selectors

## 📈 Next Steps

1. **Configure Company Scrapers**
   - Add companies to the database via admin panel
   - Configure specific selectors for each company's Workday instance

2. **Monitor Performance**
   - Set up Flower for Celery monitoring
   - Review scraping logs regularly
   - Adjust timeouts and delays as needed

3. **Scale Up**
   - Add more Redis instances for high-volume scraping
   - Configure multiple Celery workers
   - Implement proxy rotation for large-scale operations

---

**Status**: ✅ **SELENIUM FULLY ENABLED AND OPERATIONAL**

Trail-Man now supports comprehensive job scraping from all major ATS systems including dynamic JavaScript-rendered content via Workday and similar platforms. 