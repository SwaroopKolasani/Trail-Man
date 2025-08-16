from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup
import logging
import time
import random

logger = logging.getLogger(__name__)

@dataclass
class JobData:
    """Data class for job information from scrapers"""
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    salary_range: Optional[str] = None
    job_type: Optional[str] = None  # full-time, part-time, contract, internship
    remote_type: Optional[str] = None  # onsite, remote, hybrid
    external_url: Optional[str] = None
    posted_date: Optional[datetime] = None
    source_job_id: Optional[str] = None
    source_url: Optional[str] = None

    def __post_init__(self):
        """Validate and normalize data after initialization"""
        # Normalize job_type
        if self.job_type:
            job_type_lower = self.job_type.lower()
            if 'intern' in job_type_lower:
                self.job_type = 'internship'
            elif 'contract' in job_type_lower or 'freelance' in job_type_lower:
                self.job_type = 'contract'
            elif 'part' in job_type_lower and 'time' in job_type_lower:
                self.job_type = 'part-time'
            else:
                self.job_type = 'full-time'
        else:
            self.job_type = 'full-time'
        
        # Normalize remote_type
        if self.remote_type:
            remote_type_lower = self.remote_type.lower()
            if 'remote' in remote_type_lower:
                self.remote_type = 'remote'
            elif 'hybrid' in remote_type_lower:
                self.remote_type = 'hybrid'
            else:
                self.remote_type = 'onsite'
        else:
            # Try to determine from location and description
            location_text = (self.location or '').lower()
            description_text = (self.description or '').lower()
            combined_text = location_text + ' ' + description_text
            
            if 'remote' in combined_text:
                self.remote_type = 'remote'
            elif 'hybrid' in combined_text:
                self.remote_type = 'hybrid'
            else:
                self.remote_type = 'onsite'

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database insertion"""
        return {
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'description': self.description,
            'requirements': self.requirements,
            'salary_range': self.salary_range,
            'job_type': self.job_type,
            'remote_type': self.remote_type,
            'external_url': self.external_url,
            'posted_date': self.posted_date,
            'source_job_id': self.source_job_id,
            'source_url': self.source_url
        }

class BaseScraper(ABC):
    """Base class for all job scrapers"""
    
    def __init__(self, company_name: str, config: Dict[str, Any] = None):
        self.company_name = company_name
        self.config = config or {}
        self.session = self._create_session()
        self.source_name = self.__class__.__name__.lower().replace('scraper', '')
        
        # Rate limiting settings
        self.min_delay = self.config.get('min_delay', 1)
        self.max_delay = self.config.get('max_delay', 3)
        self.max_retries = self.config.get('max_retries', 3)
        
    def _create_session(self) -> requests.Session:
        """Create a requests session with proper headers"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        return session
    
    def _rate_limit(self):
        """Implement rate limiting between requests"""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)
    
    def fetch_page(self, url: str, **kwargs) -> Optional[BeautifulSoup]:
        """Fetch and parse a webpage with retries"""
        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    self._rate_limit()
                
                response = self.session.get(url, timeout=30, **kwargs)
                response.raise_for_status()
                
                return BeautifulSoup(response.content, 'html.parser')
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to fetch {url} after {self.max_retries} attempts")
                    return None
                
        return None
    
    def fetch_json(self, url: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Fetch JSON data with retries"""
        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    self._rate_limit()
                
                response = self.session.get(url, timeout=30, **kwargs)
                response.raise_for_status()
                
                return response.json()
                
            except (requests.exceptions.RequestException, ValueError) as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to fetch JSON from {url} after {self.max_retries} attempts")
                    return None
                
        return None
    
    @abstractmethod
    def get_job_listings(self) -> List[JobData]:
        """Fetch all job listings from the source"""
        pass
    
    def parse_job_details(self, job_url: str) -> Optional[JobData]:
        """Parse individual job details (optional for scrapers that get all data in listings)"""
        return None
    
    def validate_job_data(self, job_data: JobData) -> bool:
        """Validate that job data has required fields"""
        if not job_data.title:
            logger.warning(f"Job missing title: {job_data}")
            return False
        
        if not job_data.company:
            logger.warning(f"Job missing company: {job_data}")
            return False
        
        if not job_data.source_job_id:
            logger.warning(f"Job missing source_job_id: {job_data}")
            return False
            
        return True
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = ' '.join(text.split())
        
        # Remove common HTML entities
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&nbsp;': ' '
        }
        
        for entity, replacement in html_entities.items():
            text = text.replace(entity, replacement)
        
        return text.strip()
    
    def extract_salary(self, text: str) -> Optional[str]:
        """Extract salary information from text"""
        if not text:
            return None
        
        import re
        
        # Common salary patterns
        patterns = [
            r'\$[\d,]+\s*[-–]\s*\$[\d,]+',  # $50,000 - $70,000
            r'\$[\d,]+\s*-\s*[\d,]+k',      # $50,000 - 70k
            r'[\d,]+k\s*[-–]\s*[\d,]+k',    # 50k - 70k
            r'\$[\d,]+k\s*[-–]\s*\$[\d,]+k', # $50k - $70k
            r'\$[\d,]+',                     # $50,000
            r'[\d,]+k',                      # 50k
        ]
        
        text_lower = text.lower()
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(0)
        
        return None

class ScrapingError(Exception):
    """Custom exception for scraping errors"""
    pass

class RateLimitError(ScrapingError):
    """Exception for rate limiting issues"""
    pass

class ParsingError(ScrapingError):
    """Exception for data parsing issues"""
    pass 