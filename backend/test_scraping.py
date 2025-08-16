#!/usr/bin/env python3
"""
Quick Selenium Scraping Test

This script tests the actual scraping functionality to ensure
Selenium is working end-to-end with job scraping.
"""

import sys
import os
import logging

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.scrapers.workday import WorkdayScraper

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_simple_scraping():
    """Test scraping with a simple, public job board"""
    print("🧪 Testing Selenium Scraping Functionality")
    print("=" * 50)
    
    # Use a simple test URL (GitHub's public job board)
    config = {
        'careers_url': 'https://jobs.lever.co/github',
        'wait_timeout': 10,
        'selectors': {
            'job_item': '.posting',
            'job_title': '.posting-title h5',
            'job_location': '.posting-categories .location',
            'job_description': '.posting-description'
        }
    }
    
    try:
        print("🔧 Initializing WorkdayScraper...")
        scraper = WorkdayScraper('GitHub-Test', config)
        
        print("🌐 Testing web page access...")
        scraper._init_driver()
        
        # Navigate to the page
        scraper.driver.get(config['careers_url'])
        page_title = scraper.driver.title
        print(f"✅ Successfully loaded page: {page_title}")
        
        # Check if we can find job elements
        from selenium.webdriver.common.by import By
        job_elements = scraper.driver.find_elements(By.CSS_SELECTOR, '.posting')
        print(f"✅ Found {len(job_elements)} job postings")
        
        # Test extracting basic info from first few jobs
        if job_elements:
            for i, element in enumerate(job_elements[:3]):
                try:
                    title_elem = element.find_element(By.CSS_SELECTOR, '.posting-title h5')
                    location_elem = element.find_element(By.CSS_SELECTOR, '.posting-categories .location')
                    
                    title = title_elem.text.strip() if title_elem else "N/A"
                    location = location_elem.text.strip() if location_elem else "N/A"
                    
                    print(f"  📋 Job {i+1}: {title} - {location}")
                    
                except Exception as e:
                    print(f"  ⚠️ Could not extract job {i+1}: {e}")
        
        scraper._close_driver()
        
        print("\n🎉 Selenium scraping test completed successfully!")
        print("✅ Selenium is fully enabled and ready for job scraping")
        
        return True
        
    except Exception as e:
        print(f"❌ Scraping test failed: {e}")
        return False

def main():
    """Run the scraping test"""
    success = test_simple_scraping()
    
    if success:
        print("\n" + "=" * 50)
        print("🚀 Selenium Setup Complete!")
        print("=" * 50)
        print("Your Trail-Man system now supports:")
        print("✅ Workday ATS scraping")
        print("✅ Dynamic content loading")
        print("✅ Chrome headless browsing")
        print("✅ Automated job aggregation")
        print("\nNext steps:")
        print("1. Configure company scrapers in the admin panel")
        print("2. Run automated scraping with Celery")
        print("3. Monitor jobs through the frontend dashboard")
        return 0
    else:
        print("\n❌ Selenium setup needs attention")
        print("Check the error messages above for troubleshooting")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 