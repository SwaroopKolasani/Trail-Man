from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import time
import re
import os
import platform
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from .base import BaseScraper, JobData, ScrapingError
from app.core.config import settings

logger = logging.getLogger(__name__)

class WorkdayScraper(BaseScraper):
    """Scraper for Workday ATS system using Selenium for dynamic content"""
    
    def __init__(self, company_name: str, config: Dict[str, Any]):
        super().__init__(company_name, config)
        self.careers_url = config.get('careers_url')
        if not self.careers_url:
            raise ValueError("Workday scraper requires 'careers_url' in config")
        
        self.source_name = "workday"
        self.driver = None
        self.wait_timeout = config.get('wait_timeout', 10)
        self.page_load_timeout = config.get('page_load_timeout', 30)
        
        # Workday-specific selectors (can be customized per company)
        self.selectors = config.get('selectors', {
            'job_item': '[data-automation-id="jobItem"]',
            'job_title': '[data-automation-id="jobTitle"]',
            'job_location': '[data-automation-id="jobLocation"]',
            'job_description': '[data-automation-id="jobDescription"]',
            'next_page': '[data-automation-id="nextPage"]',
            'load_more': '[data-automation-id="loadMoreJobs"]',
            'search_results': '[data-automation-id="searchResults"]'
        })
    
    def _init_driver(self):
        """Initialize Selenium Chrome driver with appropriate options"""
        if self.driver:
            return
        
        # Check if Selenium is enabled
        if not settings.SELENIUM_ENABLED:
            raise ScrapingError("Selenium is disabled in configuration")
            
        try:
            chrome_options = Options()
            
            # Configure headless mode
            if settings.HEADLESS_BROWSER:
                chrome_options.add_argument('--headless')
            
            # Standard Chrome options for stability
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Add user agent
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            # Check if we should use remote Selenium (Docker environment)
            selenium_remote_url = os.getenv('SELENIUM_REMOTE_URL', 'http://selenium:4444/wd/hub')
            
            # Try to use remote Selenium first (for Docker environment)
            if os.getenv('DOCKER_ENV') == 'true':
                try:
                    from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
                    
                    # Set up desired capabilities for Chrome
                    desired_caps = DesiredCapabilities.CHROME.copy()
                    desired_caps['browserName'] = 'chrome'
                    desired_caps['version'] = ''
                    desired_caps['platform'] = 'ANY'
                    
                    # Merge Chrome options with capabilities
                    desired_caps.update(chrome_options.to_capabilities())
                    
                    self.driver = webdriver.Remote(
                        command_executor=selenium_remote_url,
                        desired_capabilities=desired_caps
                    )
                    
                    logger.info(f"Successfully initialized remote Chrome driver for {self.company_name} at {selenium_remote_url}")
                    
                except Exception as remote_error:
                    logger.warning(f"Failed to connect to remote Selenium: {remote_error}")
                    logger.info("Falling back to local Chrome driver")
                    # Continue to local driver setup below
            
            # If remote driver failed or not in Docker, use local driver
            if not self.driver:
                # Set Chrome/Chromium binary path if specified
                if settings.CHROME_BIN:
                    chrome_options.binary_location = settings.CHROME_BIN
                    logger.info(f"Using browser binary from config: {settings.CHROME_BIN}")
                else:
                    # Auto-detect browser based on platform
                    browser_found = False
                    
                    if platform.system() == "Darwin":  # macOS
                        # Try common macOS Chrome locations
                        possible_paths = [
                            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                            "/Applications/Chrome.app/Contents/MacOS/Chrome",
                            "/Applications/Chromium.app/Contents/MacOS/Chromium"
                        ]
                        for path in possible_paths:
                            if os.path.exists(path):
                                chrome_options.binary_location = path
                                logger.info(f"Found browser at: {path}")
                                browser_found = True
                                break
                    
                    elif platform.system() == "Linux":  # Linux/Docker
                        # Try common Linux Chrome/Chromium locations
                        possible_paths = [
                            "/usr/bin/chromium",           # Debian/Ubuntu Chromium
                            "/usr/bin/chromium-browser",   # Alternative Chromium path
                            "/usr/bin/google-chrome",      # Google Chrome
                            "/usr/bin/google-chrome-stable",
                            "/usr/bin/chrome",
                            "/opt/google/chrome/chrome"
                        ]
                        for path in possible_paths:
                            if os.path.exists(path):
                                chrome_options.binary_location = path
                                logger.info(f"Found browser at: {path}")
                                browser_found = True
                                break
                    
                    if not browser_found:
                        logger.warning("No browser binary found, using system default")
                
                # Initialize ChromeDriver service
                service = None
                if settings.CHROME_DRIVER_PATH and os.path.exists(settings.CHROME_DRIVER_PATH):
                    # Use specified ChromeDriver path
                    service = Service(settings.CHROME_DRIVER_PATH)
                    logger.info(f"Using ChromeDriver from: {settings.CHROME_DRIVER_PATH}")
                else:
                    # Try system ChromeDriver first (for Docker/Linux)
                    system_chromedriver_paths = [
                        "/usr/bin/chromedriver",
                        "/usr/local/bin/chromedriver",
                        "/opt/chromedriver/chromedriver"
                    ]
                    
                    chromedriver_found = False
                    for driver_path in system_chromedriver_paths:
                        if os.path.exists(driver_path):
                            service = Service(driver_path)
                            logger.info(f"Using system ChromeDriver: {driver_path}")
                            chromedriver_found = True
                            break
                    
                    if not chromedriver_found:
                        # Use webdriver-manager as fallback
                        try:
                            driver_path = ChromeDriverManager().install()
                            
                            # Fix webdriver-manager path issue on macOS
                            if platform.system() == "Darwin" and "THIRD_PARTY_NOTICES" in driver_path:
                                # Extract the directory and find the actual chromedriver executable
                                driver_dir = os.path.dirname(driver_path)
                                actual_driver_path = os.path.join(driver_dir, "chromedriver")
                                if os.path.exists(actual_driver_path):
                                    driver_path = actual_driver_path
                                    # Ensure the chromedriver has execute permissions
                                    import stat
                                    current_permissions = os.stat(driver_path).st_mode
                                    os.chmod(driver_path, current_permissions | stat.S_IEXEC)
                                    logger.info(f"Fixed ChromeDriver path and permissions: {driver_path}")
                            
                            service = Service(driver_path)
                            logger.info(f"Using ChromeDriver from webdriver-manager: {driver_path}")
                        except Exception as e:
                            logger.warning(f"webdriver-manager failed: {e}")
                            # Try system ChromeDriver as final fallback
                            logger.info("Attempting to use system ChromeDriver without explicit path")
                
                # Create the Chrome driver
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info(f"Successfully initialized local Chrome driver for {self.company_name}")
            
            # Set page load timeout
            self.driver.set_page_load_timeout(settings.BROWSER_TIMEOUT)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info(f"Successfully initialized Chrome driver for {self.company_name}")
            
        except Exception as e:
            error_msg = f"Failed to initialize Chrome driver: {e}"
            logger.error(error_msg)
            
            # Provide helpful error message based on the error
            if "chrome not reachable" in str(e).lower():
                error_msg += "\nHint: Make sure Chrome/Chromium is installed and accessible or Selenium container is running"
            elif "chromedriver" in str(e).lower():
                error_msg += "\nHint: ChromeDriver may need to be updated or installed manually"
            elif "permission denied" in str(e).lower():
                error_msg += "\nHint: Check file permissions for Chrome/Chromium and ChromeDriver"
            elif "connection refused" in str(e).lower():
                error_msg += "\nHint: Selenium container may not be running or accessible"
                
            raise ScrapingError(error_msg)
    
    def _close_driver(self):
        """Close the Selenium driver"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"Error closing driver: {e}")
            finally:
                self.driver = None
    
    def get_job_listings(self) -> List[JobData]:
        """Fetch all job listings from Workday careers page"""
        jobs = []
        
        try:
            self._init_driver()
            logger.info(f"Fetching jobs from Workday for {self.company_name}")
            
            # Navigate to careers page
            self.driver.get(self.careers_url)
            wait = WebDriverWait(self.driver, self.wait_timeout)
            
            # Wait for job listings to load
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors['job_item'])))
            except TimeoutException:
                logger.warning(f"No job items found for {self.company_name}, trying alternative selectors")
                # Try common alternative selectors
                alternative_selectors = [
                    '[data-automation-id="job"]',
                    '.job-item',
                    '.job-posting',
                    '[class*="job"]'
                ]
                
                job_elements = []
                for selector in alternative_selectors:
                    try:
                        job_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if job_elements:
                            self.selectors['job_item'] = selector
                            break
                    except:
                        continue
                
                if not job_elements:
                    logger.error(f"Could not find job listings on {self.careers_url}")
                    return jobs
            
            # Load all jobs by clicking "Load More" or pagination
            self._load_all_jobs()
            
            # Get all job elements
            job_elements = self.driver.find_elements(By.CSS_SELECTOR, self.selectors['job_item'])
            logger.info(f"Found {len(job_elements)} job elements for {self.company_name}")
            
            # Process each job
            for i, element in enumerate(job_elements):
                try:
                    job_data = self._extract_job_from_element(element, i)
                    if job_data and self.validate_job_data(job_data):
                        jobs.append(job_data)
                        
                except Exception as e:
                    logger.warning(f"Error processing job element {i}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Workday for {self.company_name}: {e}")
            raise ScrapingError(f"Failed to scrape Workday jobs: {e}")
        finally:
            self._close_driver()
        
        logger.info(f"Successfully parsed {len(jobs)} valid jobs from Workday for {self.company_name}")
        return jobs
    
    def _load_all_jobs(self):
        """Load all jobs by handling pagination or 'Load More' buttons"""
        max_attempts = 10
        attempts = 0
        
        while attempts < max_attempts:
            try:
                # Try to find and click "Load More" button
                load_more_buttons = self.driver.find_elements(By.CSS_SELECTOR, self.selectors['load_more'])
                if not load_more_buttons:
                    # Try alternative load more selectors
                    alternative_selectors = [
                        '[data-automation-id="loadMore"]',
                        'button[aria-label*="Load more"]',
                        'button[aria-label*="Show more"]',
                        '.load-more',
                        '[class*="load-more"]'
                    ]
                    
                    for selector in alternative_selectors:
                        load_more_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if load_more_buttons:
                            break
                
                if load_more_buttons and load_more_buttons[0].is_displayed():
                    # Scroll to button and click
                    self.driver.execute_script("arguments[0].scrollIntoView();", load_more_buttons[0])
                    time.sleep(1)
                    load_more_buttons[0].click()
                    
                    # Wait for new jobs to load
                    time.sleep(3)
                    attempts += 1
                    continue
                
                # Try pagination
                next_buttons = self.driver.find_elements(By.CSS_SELECTOR, self.selectors['next_page'])
                if not next_buttons:
                    # Try alternative next page selectors
                    alternative_selectors = [
                        '[data-automation-id="next"]',
                        'button[aria-label*="Next"]',
                        '.pagination-next',
                        '[class*="next"]'
                    ]
                    
                    for selector in alternative_selectors:
                        next_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if next_buttons:
                            break
                
                if next_buttons and next_buttons[0].is_enabled():
                    next_buttons[0].click()
                    time.sleep(3)
                    attempts += 1
                    continue
                
                # No more pagination options
                break
                
            except Exception as e:
                logger.warning(f"Error during pagination attempt {attempts}: {e}")
                break
        
        logger.info(f"Completed pagination after {attempts} attempts")
    
    def _extract_job_from_element(self, element, index: int) -> Optional[JobData]:
        """Extract job data from a job element"""
        try:
            # Extract title
            title = self._extract_text_from_element(element, self.selectors['job_title'])
            if not title:
                # Try alternative title selectors
                alternative_selectors = ['h3', '.job-title', '[class*="title"]', 'a']
                for selector in alternative_selectors:
                    title = self._extract_text_from_element(element, selector)
                    if title:
                        break
            
            if not title:
                logger.warning(f"Could not extract title for job {index}")
                return None
            
            # Extract location
            location = self._extract_text_from_element(element, self.selectors['job_location'])
            if not location:
                alternative_selectors = ['.location', '[class*="location"]', '[data-automation-id="location"]']
                for selector in alternative_selectors:
                    location = self._extract_text_from_element(element, selector)
                    if location:
                        break
            
            # Get job URL by clicking and getting current URL
            job_url = self._get_job_url(element)
            
            # Extract job details by clicking on the job
            description, requirements, posted_date = self._extract_job_details(element, index)
            
            # Generate a source job ID
            source_job_id = f"workday_{self.company_name}_{index}_{hash(title + location or '')}"
            
            # Determine job type and remote type
            job_type = self._determine_job_type(title, description or '')
            remote_type = self._determine_remote_type(location or '', description or '')
            
            # Extract salary if available
            salary_range = self.extract_salary((description or '') + ' ' + (requirements or ''))
            
            return JobData(
                title=self.clean_text(title),
                company=self.company_name,
                location=self.clean_text(location) if location else '',
                description=self.clean_text(description) if description else '',
                requirements=self.clean_text(requirements) if requirements else '',
                salary_range=salary_range,
                job_type=job_type,
                remote_type=remote_type,
                external_url=job_url,
                posted_date=posted_date,
                source_job_id=source_job_id,
                source_url=job_url
            )
            
        except Exception as e:
            logger.error(f"Error extracting job data from element {index}: {e}")
            return None
    
    def _extract_text_from_element(self, parent_element, selector: str) -> Optional[str]:
        """Extract text from an element using CSS selector"""
        try:
            elements = parent_element.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                return elements[0].text.strip()
        except Exception:
            pass
        return None
    
    def _get_job_url(self, element) -> Optional[str]:
        """Get the job URL by finding clickable link"""
        try:
            # Look for clickable links within the element
            links = element.find_elements(By.TAG_NAME, 'a')
            if links:
                href = links[0].get_attribute('href')
                if href:
                    return href
            
            # If no direct link, the URL might be generated by JavaScript
            # We'll use the current page URL as fallback
            return self.driver.current_url
            
        except Exception as e:
            logger.warning(f"Could not extract job URL: {e}")
            return self.driver.current_url
    
    def _extract_job_details(self, element, index: int) -> tuple:
        """Extract detailed job information by clicking on the job"""
        description = ""
        requirements = ""
        posted_date = None
        
        try:
            # Click on the job element to open details
            self.driver.execute_script("arguments[0].click();", element)
            
            # Wait for job details to load
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors['job_description']))
            )
            
            # Extract description
            description_elements = self.driver.find_elements(By.CSS_SELECTOR, self.selectors['job_description'])
            if description_elements:
                description = description_elements[0].text.strip()
            else:
                # Try alternative selectors
                alternative_selectors = [
                    '.job-description',
                    '[class*="description"]',
                    '[data-automation-id="details"]',
                    '.job-details'
                ]
                
                for selector in alternative_selectors:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        description = elements[0].text.strip()
                        break
            
            # Try to extract requirements section
            requirements_selectors = [
                '[data-automation-id="requirements"]',
                '.requirements',
                '[class*="requirements"]',
                '.qualifications',
                '[class*="qualifications"]'
            ]
            
            for selector in requirements_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    requirements = elements[0].text.strip()
                    break
            
            # Try to extract posted date
            date_selectors = [
                '[data-automation-id="postedDate"]',
                '.posted-date',
                '[class*="posted"]',
                '.date'
            ]
            
            for selector in date_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    date_text = elements[0].text.strip()
                    posted_date = self._parse_date(date_text)
                    break
            
        except Exception as e:
            logger.warning(f"Could not extract detailed job info for job {index}: {e}")
        
        return description, requirements, posted_date
    
    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """Parse date from various formats"""
        if not date_text:
            return None
            
        import dateparser
        
        try:
            # Use dateparser for flexible date parsing
            parsed_date = dateparser.parse(date_text)
            return parsed_date
        except Exception:
            # Fallback to regex patterns
            date_patterns = [
                r'(\d{1,2}/\d{1,2}/\d{4})',
                r'(\d{4}-\d{2}-\d{2})',
                r'(\w+ \d{1,2}, \d{4})'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, date_text)
                if match:
                    try:
                        return datetime.strptime(match.group(1), '%m/%d/%Y')
                    except:
                        try:
                            return datetime.strptime(match.group(1), '%Y-%m-%d')
                        except:
                            continue
        
        return None
    
    def _determine_job_type(self, title: str, description: str) -> str:
        """Determine job type from title and description"""
        text = (title + ' ' + description).lower()
        
        if any(keyword in text for keyword in ['intern', 'internship']):
            return 'internship'
        elif any(keyword in text for keyword in ['contract', 'contractor', 'freelance', 'temporary']):
            return 'contract'
        elif any(keyword in text for keyword in ['part-time', 'part time', 'parttime']):
            return 'part-time'
        else:
            return 'full-time'
    
    def _determine_remote_type(self, location: str, description: str) -> str:
        """Determine remote work type from location and description"""
        text = (location + ' ' + description).lower()
        
        if any(keyword in text for keyword in ['remote', 'work from home', 'wfh', 'distributed']):
            return 'remote'
        elif any(keyword in text for keyword in ['hybrid', 'flexible', 'remote optional']):
            return 'hybrid'
        else:
            return 'onsite'

# Helper function to validate Workday careers URL
def validate_workday_url(careers_url: str) -> bool:
    """Validate that a Workday careers URL is accessible"""
    try:
        import requests
        response = requests.head(careers_url, timeout=10)
        return response.status_code == 200
    except Exception:
        return False

# Helper function to detect if a URL is a Workday careers page
def is_workday_url(careers_url: str) -> bool:
    """Detect if a URL is a Workday careers page"""
    workday_indicators = [
        'myworkdayjobs.com',
        'workday.com',
        'wd1.myworkdaysite.com',
        'wd5.myworkdaysite.com'
    ]
    
    return any(indicator in careers_url for indicator in workday_indicators) 