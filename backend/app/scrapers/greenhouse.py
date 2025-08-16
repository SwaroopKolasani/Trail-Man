from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from .base import BaseScraper, JobData, ScrapingError

logger = logging.getLogger(__name__)

class GreenhouseScraper(BaseScraper):
    """Scraper for Greenhouse ATS system using their public API"""
    
    def __init__(self, company_name: str, config: Dict[str, Any]):
        super().__init__(company_name, config)
        self.company_token = config.get('company_token')
        if not self.company_token:
            raise ValueError("Greenhouse scraper requires 'company_token' in config")
        
        self.base_url = f"https://boards-api.greenhouse.io/v1/boards/{self.company_token}"
        self.source_name = "greenhouse"
    
    def get_job_listings(self) -> List[JobData]:
        """Fetch all job listings from Greenhouse API"""
        jobs = []
        url = f"{self.base_url}/jobs"
        
        try:
            logger.info(f"Fetching jobs from Greenhouse for {self.company_name}")
            data = self.fetch_json(url)
            
            if not data:
                logger.error(f"No data received from Greenhouse API for {self.company_name}")
                return jobs
            
            job_listings = data.get('jobs', [])
            logger.info(f"Found {len(job_listings)} jobs from Greenhouse for {self.company_name}")
            
            for job in job_listings:
                job_data = self._parse_job_from_api(job)
                if job_data and self.validate_job_data(job_data):
                    jobs.append(job_data)
                    
        except Exception as e:
            logger.error(f"Error fetching Greenhouse jobs for {self.company_name}: {e}")
            raise ScrapingError(f"Failed to scrape Greenhouse jobs: {e}")
        
        logger.info(f"Successfully parsed {len(jobs)} valid jobs from Greenhouse for {self.company_name}")
        return jobs
    
    def _parse_job_from_api(self, job: Dict[str, Any]) -> Optional[JobData]:
        """Parse job data from Greenhouse API response"""
        try:
            # Basic job information
            title = job.get('title')
            if not title:
                logger.warning("Job missing title, skipping")
                return None
            
            # Location information
            location_data = job.get('location', {})
            location = location_data.get('name', '') if location_data else ''
            
            # Job description and content
            description = job.get('content', '')
            
            # External URL
            external_url = job.get('absolute_url')
            
            # Posted date
            posted_date = None
            created_at = job.get('created_at')
            if created_at:
                try:
                    # Parse ISO format: 2023-10-15T10:30:00.000Z
                    posted_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Failed to parse date {created_at}: {e}")
            
            # Extract job type from title and metadata
            job_type = self._determine_job_type(title, description)
            
            # Extract remote type from location and description
            remote_type = self._determine_remote_type(location, description)
            
            # Extract salary if available
            salary_range = self.extract_salary(description)
            
            # Source job ID
            source_job_id = str(job.get('id'))
            
            # Get departments and other metadata
            departments = job.get('departments', [])
            department_names = [dept.get('name', '') for dept in departments if dept]
            
            # Enhance description with department info
            if department_names:
                description = f"Department: {', '.join(department_names)}\n\n{description}"
            
            return JobData(
                title=self.clean_text(title),
                company=self.company_name,
                location=self.clean_text(location),
                description=self.clean_text(description),
                salary_range=salary_range,
                job_type=job_type,
                remote_type=remote_type,
                external_url=external_url,
                posted_date=posted_date,
                source_job_id=source_job_id,
                source_url=external_url
            )
            
        except Exception as e:
            logger.error(f"Error parsing Greenhouse job: {e}")
            logger.debug(f"Job data: {job}")
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
    
    def get_job_details(self, job_id: str) -> Optional[JobData]:
        """Get detailed job information (Greenhouse API provides full data in listings)"""
        # Greenhouse API typically provides all job details in the main listings
        # This method could be used to get additional metadata if needed
        url = f"{self.base_url}/jobs/{job_id}"
        
        try:
            data = self.fetch_json(url)
            if data:
                return self._parse_job_from_api(data)
        except Exception as e:
            logger.error(f"Error fetching Greenhouse job details for {job_id}: {e}")
        
        return None
    
    def get_departments(self) -> List[Dict[str, Any]]:
        """Get list of departments from Greenhouse"""
        url = f"{self.base_url}/departments"
        
        try:
            data = self.fetch_json(url)
            return data.get('departments', []) if data else []
        except Exception as e:
            logger.error(f"Error fetching Greenhouse departments: {e}")
            return []
    
    def get_offices(self) -> List[Dict[str, Any]]:
        """Get list of offices from Greenhouse"""
        url = f"{self.base_url}/offices"
        
        try:
            data = self.fetch_json(url)
            return data.get('offices', []) if data else []
        except Exception as e:
            logger.error(f"Error fetching Greenhouse offices: {e}")
            return []

# Helper function to validate Greenhouse company token
def validate_greenhouse_token(company_token: str) -> bool:
    """Validate that a Greenhouse company token is accessible"""
    try:
        scraper = GreenhouseScraper("test", {"company_token": company_token})
        url = f"{scraper.base_url}/jobs"
        response = scraper.fetch_json(url)
        return response is not None
    except Exception:
        return False 