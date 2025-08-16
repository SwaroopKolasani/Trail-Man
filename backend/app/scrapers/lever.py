from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from .base import BaseScraper, JobData, ScrapingError

logger = logging.getLogger(__name__)

class LeverScraper(BaseScraper):
    """Scraper for Lever ATS system using their public API"""
    
    def __init__(self, company_name: str, config: Dict[str, Any]):
        super().__init__(company_name, config)
        self.company_handle = config.get('company_handle')
        if not self.company_handle:
            raise ValueError("Lever scraper requires 'company_handle' in config")
        
        self.base_url = f"https://api.lever.co/v0/postings/{self.company_handle}"
        self.source_name = "lever"
    
    def get_job_listings(self) -> List[JobData]:
        """Fetch all job listings from Lever API"""
        jobs = []
        
        try:
            logger.info(f"Fetching jobs from Lever for {self.company_name}")
            
            # Lever API parameters
            params = {
                'mode': 'json',
                'limit': 100,  # Max jobs per request
                'skip': 0
            }
            
            # Lever API might require pagination
            has_more = True
            total_fetched = 0
            
            while has_more:
                data = self.fetch_json(self.base_url, params=params)
                
                if not data:
                    logger.error(f"No data received from Lever API for {self.company_name}")
                    break
                
                # Lever returns an array of job postings directly
                if isinstance(data, list):
                    job_listings = data
                else:
                    # Some Lever endpoints might return wrapped data
                    job_listings = data.get('postings', data.get('jobs', []))
                
                if not job_listings:
                    logger.info(f"No more jobs found, stopping pagination")
                    break
                
                logger.info(f"Found {len(job_listings)} jobs in this batch from Lever for {self.company_name}")
                
                for job in job_listings:
                    job_data = self._parse_job_from_api(job)
                    if job_data and self.validate_job_data(job_data):
                        jobs.append(job_data)
                
                total_fetched += len(job_listings)
                
                # Check if we need to paginate
                if len(job_listings) < params['limit']:
                    has_more = False
                else:
                    params['skip'] += params['limit']
                
                # Safety check to avoid infinite loops
                if total_fetched > 1000:
                    logger.warning(f"Reached maximum job limit (1000) for {self.company_name}")
                    break
                    
        except Exception as e:
            logger.error(f"Error fetching Lever jobs for {self.company_name}: {e}")
            raise ScrapingError(f"Failed to scrape Lever jobs: {e}")
        
        logger.info(f"Successfully parsed {len(jobs)} valid jobs from Lever for {self.company_name}")
        return jobs
    
    def _parse_job_from_api(self, job: Dict[str, Any]) -> Optional[JobData]:
        """Parse job data from Lever API response"""
        try:
            # Basic job information
            title = job.get('text')
            if not title:
                logger.warning("Job missing title, skipping")
                return None
            
            # Categories contain location, commitment, team, etc.
            categories = job.get('categories', {})
            
            # Location information
            location = categories.get('location', '')
            
            # Job description and content
            content = job.get('content', {})
            description = content.get('description', '')
            
            # Additional content sections
            requirements = []
            if content.get('lists'):
                for section in content.get('lists', []):
                    if section.get('text'):
                        requirements.append(section.get('text', ''))
                    if section.get('content'):
                        requirements.append(section.get('content', ''))
            
            requirements_text = '\n\n'.join(requirements) if requirements else ''
            
            # External URL
            external_url = job.get('hostedUrl') or job.get('applyUrl')
            
            # Posted date
            posted_date = None
            created_at = job.get('createdAt')
            if created_at:
                try:
                    # Lever uses Unix timestamp in milliseconds
                    posted_date = datetime.fromtimestamp(created_at / 1000)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse date {created_at}: {e}")
            
            # Extract job type from commitment
            commitment = categories.get('commitment', '')
            job_type = self._determine_job_type(title, description, commitment)
            
            # Extract remote type from location and description
            remote_type = self._determine_remote_type(location, description)
            
            # Extract salary if available
            salary_range = self.extract_salary(description + ' ' + requirements_text)
            
            # Source job ID
            source_job_id = job.get('id')
            
            # Get team/department information
            team = categories.get('team', '')
            if team:
                description = f"Team: {team}\n\n{description}"
            
            return JobData(
                title=self.clean_text(title),
                company=self.company_name,
                location=self.clean_text(location),
                description=self.clean_text(description),
                requirements=self.clean_text(requirements_text),
                salary_range=salary_range,
                job_type=job_type,
                remote_type=remote_type,
                external_url=external_url,
                posted_date=posted_date,
                source_job_id=source_job_id,
                source_url=external_url
            )
            
        except Exception as e:
            logger.error(f"Error parsing Lever job: {e}")
            logger.debug(f"Job data: {job}")
            return None
    
    def _determine_job_type(self, title: str, description: str, commitment: str) -> str:
        """Determine job type from title, description, and commitment"""
        text = (title + ' ' + description + ' ' + commitment).lower()
        
        if any(keyword in text for keyword in ['intern', 'internship']):
            return 'internship'
        elif any(keyword in text for keyword in ['contract', 'contractor', 'freelance', 'temporary', 'consulting']):
            return 'contract'
        elif any(keyword in text for keyword in ['part-time', 'part time', 'parttime']):
            return 'part-time'
        else:
            return 'full-time'
    
    def _determine_remote_type(self, location: str, description: str) -> str:
        """Determine remote work type from location and description"""
        text = (location + ' ' + description).lower()
        
        if any(keyword in text for keyword in ['remote', 'work from home', 'wfh', 'distributed', 'anywhere']):
            return 'remote'
        elif any(keyword in text for keyword in ['hybrid', 'flexible', 'remote optional', 'remote friendly']):
            return 'hybrid'
        else:
            return 'onsite'
    
    def get_job_details(self, job_id: str) -> Optional[JobData]:
        """Get detailed job information (Lever API provides full data in listings)"""
        # Lever API typically provides all job details in the main listings
        # But we can also fetch individual job details if needed
        url = f"https://api.lever.co/v0/postings/{self.company_handle}/{job_id}"
        
        try:
            data = self.fetch_json(url)
            if data:
                return self._parse_job_from_api(data)
        except Exception as e:
            logger.error(f"Error fetching Lever job details for {job_id}: {e}")
        
        return None
    
    def get_company_info(self) -> Optional[Dict[str, Any]]:
        """Get company information from Lever"""
        url = f"https://api.lever.co/v0/postings/{self.company_handle}"
        
        try:
            # First request to get company info from response headers or metadata
            response = self.session.head(url)
            if response.status_code == 200:
                return {"status": "active", "company_handle": self.company_handle}
        except Exception as e:
            logger.error(f"Error fetching Lever company info: {e}")
        
        return None

# Helper function to validate Lever company handle
def validate_lever_handle(company_handle: str) -> bool:
    """Validate that a Lever company handle is accessible"""
    try:
        scraper = LeverScraper("test", {"company_handle": company_handle})
        response = scraper.fetch_json(scraper.base_url + "?limit=1")
        return response is not None
    except Exception:
        return False

# Helper function to discover Lever company handle from URL
def discover_lever_handle(careers_url: str) -> Optional[str]:
    """Try to discover Lever company handle from careers URL"""
    import re
    
    # Common Lever URL patterns
    patterns = [
        r'jobs\.lever\.co/([^/]+)',
        r'lever\.co/([^/]+)',
        r'([^.]+)\.lever\.co'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, careers_url)
        if match:
            return match.group(1)
    
    return None 