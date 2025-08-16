from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import json
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from app.db.session import get_db
from app.models.user import Job, CompanyScraper, ScrapingLog
from .base import JobData, ScrapingError
from .greenhouse import GreenhouseScraper, validate_greenhouse_token
from .lever import LeverScraper, validate_lever_handle
from .workday import WorkdayScraper, validate_workday_url

logger = logging.getLogger(__name__)

class ScrapingStats:
    """Statistics for scraping operations"""
    def __init__(self):
        self.total_sources = 0
        self.successful_sources = 0
        self.failed_sources = 0
        self.total_jobs_found = 0
        self.total_jobs_saved = 0
        self.total_jobs_updated = 0
        self.errors = []
        self.start_time = datetime.utcnow()
        self.end_time = None
    
    def add_source_result(self, company: str, source_type: str, 
                         jobs_found: int, jobs_saved: int, jobs_updated: int, 
                         error: Optional[str] = None):
        """Add results from a single source"""
        self.total_sources += 1
        if error:
            self.failed_sources += 1
            self.errors.append(f"{company} ({source_type}): {error}")
        else:
            self.successful_sources += 1
        
        self.total_jobs_found += jobs_found
        self.total_jobs_saved += jobs_saved
        self.total_jobs_updated += jobs_updated
    
    def finish(self):
        """Mark scraping as finished"""
        self.end_time = datetime.utcnow()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        duration = None
        if self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
        
        return {
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration_seconds': duration,
            'total_sources': self.total_sources,
            'successful_sources': self.successful_sources,
            'failed_sources': self.failed_sources,
            'total_jobs_found': self.total_jobs_found,
            'total_jobs_saved': self.total_jobs_saved,
            'total_jobs_updated': self.total_jobs_updated,
            'success_rate': self.successful_sources / self.total_sources if self.total_sources > 0 else 0,
            'errors': self.errors
        }

class ScrapingOrchestrator:
    """Orchestrates all job scraping operations"""
    
    def __init__(self, db_session: Optional[Session] = None):
        self.db = db_session or next(get_db())
        self.scrapers = []
        self.stats = ScrapingStats()
        
        # Scraper factory mapping
        self.scraper_classes = {
            'greenhouse': GreenhouseScraper,
            'lever': LeverScraper,
            'workday': WorkdayScraper
        }
        
        # Validation functions
        self.validators = {
            'greenhouse': validate_greenhouse_token,
            'lever': validate_lever_handle,
            'workday': validate_workday_url
        }
    
    def load_scraper_configs(self, config_source: str = 'database'):
        """Load scraper configurations from database or config file"""
        self.scrapers = []
        
        if config_source == 'database':
            self._load_configs_from_database()
        else:
            self._load_configs_from_file(config_source)
    
    def _load_configs_from_database(self):
        """Load scraper configurations from database"""
        try:
            configs = self.db.query(CompanyScraper).filter(
                CompanyScraper.is_active == True
            ).all()
            
            for config in configs:
                try:
                    scraper = self._create_scraper(
                        config.company_name,
                        config.scraper_type,
                        json.loads(config.config) if isinstance(config.config, str) else config.config
                    )
                    if scraper:
                        self.scrapers.append((scraper, config.scraper_type, config.id))
                        
                except Exception as e:
                    logger.error(f"Failed to create scraper for {config.company_name}: {e}")
            
            logger.info(f"Loaded {len(self.scrapers)} scrapers from database")
            
        except Exception as e:
            logger.error(f"Error loading configs from database: {e}")
            self._load_hardcoded_configs()
    
    def _load_hardcoded_configs(self):
        """Load hardcoded scraper configurations for testing"""
        hardcoded_configs = [
            # Working Greenhouse companies
            {
                'company_name': 'Stripe',
                'scraper_type': 'greenhouse',
                'config': {'company_token': 'stripe'}
            },
            {
                'company_name': 'Airbnb',
                'scraper_type': 'greenhouse',
                'config': {'company_token': 'airbnb'}
            },
            {
                'company_name': 'Coinbase',
                'scraper_type': 'greenhouse',
                'config': {'company_token': 'coinbase'}
            },
            {
                'company_name': 'DoorDash',
                'scraper_type': 'greenhouse',
                'config': {'company_token': 'doordash'}
            },
            # Working Lever companies
            {
                'company_name': 'Netflix',
                'scraper_type': 'lever',
                'config': {'company_handle': 'netflix'}
            },
            {
                'company_name': 'Figma',
                'scraper_type': 'lever',
                'config': {'company_handle': 'figma'}
            },
            # Working Workday companies (using Chromium in Docker)
            {
                'company_name': 'Apple',
                'scraper_type': 'workday',
                'config': {'careers_url': 'https://jobs.apple.com/en-us/search'}
            },
            {
                'company_name': 'Microsoft',
                'scraper_type': 'workday',
                'config': {'careers_url': 'https://careers.microsoft.com/professionals/us/en/search-results'}
            }
        ]
        
        for config in hardcoded_configs:
            try:
                scraper = self._create_scraper(
                    config['company_name'],
                    config['scraper_type'],
                    config['config']
                )
                if scraper:
                    self.scrapers.append((scraper, config['scraper_type'], None))
            except Exception as e:
                logger.error(f"Failed to create hardcoded scraper for {config['company_name']}: {e}")
        
        logger.info(f"Loaded {len(self.scrapers)} hardcoded scrapers")
    
    def _load_configs_from_file(self, file_path: str):
        """Load scraper configurations from JSON file"""
        try:
            with open(file_path, 'r') as f:
                configs = json.load(f)
            
            for config in configs:
                try:
                    scraper = self._create_scraper(
                        config['company_name'],
                        config['scraper_type'],
                        config['config']
                    )
                    if scraper:
                        self.scrapers.append((scraper, config['scraper_type'], None))
                except Exception as e:
                    logger.error(f"Failed to create scraper for {config['company_name']}: {e}")
            
            logger.info(f"Loaded {len(self.scrapers)} scrapers from {file_path}")
            
        except Exception as e:
            logger.error(f"Error loading configs from file {file_path}: {e}")
            self._load_hardcoded_configs()
    
    def _create_scraper(self, company_name: str, scraper_type: str, config: Dict[str, Any]):
        """Factory method to create appropriate scraper"""
        if scraper_type not in self.scraper_classes:
            logger.error(f"Unknown scraper type: {scraper_type}")
            return None
        
        try:
            scraper_class = self.scraper_classes[scraper_type]
            return scraper_class(company_name, config)
        except Exception as e:
            logger.error(f"Failed to create {scraper_type} scraper for {company_name}: {e}")
            return None
    
    def validate_scraper_config(self, scraper_type: str, config: Dict[str, Any]) -> bool:
        """Validate scraper configuration"""
        if scraper_type not in self.validators:
            return False
        
        try:
            validator = self.validators[scraper_type]
            
            if scraper_type == 'greenhouse':
                return validator(config.get('company_token', ''))
            elif scraper_type == 'lever':
                return validator(config.get('company_handle', ''))
            elif scraper_type == 'workday':
                return validator(config.get('careers_url', ''))
                
        except Exception as e:
            logger.error(f"Error validating {scraper_type} config: {e}")
            return False
        
        return False
    
    def scrape_all(self, max_concurrent: int = 3) -> Dict[str, Any]:
        """Run all configured scrapers"""
        logger.info(f"Starting scraping process with {len(self.scrapers)} sources")
        
        if not self.scrapers:
            self.load_scraper_configs()
        
        self.stats = ScrapingStats()
        
        # Process scrapers in batches to avoid overwhelming target sites
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            # Submit all scraping tasks
            future_to_scraper = {}
            for scraper, source_type, config_id in self.scrapers:
                future = executor.submit(self._scrape_single_source, scraper, source_type, config_id)
                future_to_scraper[future] = (scraper.company_name, source_type)
            
            # Process completed tasks
            for future in as_completed(future_to_scraper):
                company_name, source_type = future_to_scraper[future]
                try:
                    jobs_found, jobs_saved, jobs_updated = future.result()
                    self.stats.add_source_result(
                        company_name, source_type, jobs_found, jobs_saved, jobs_updated
                    )
                    logger.info(f"Completed {company_name} ({source_type}): "
                              f"{jobs_found} found, {jobs_saved} saved, {jobs_updated} updated")
                    
                except Exception as e:
                    error_msg = str(e)
                    self.stats.add_source_result(
                        company_name, source_type, 0, 0, 0, error_msg
                    )
                    logger.error(f"Failed to scrape {company_name} ({source_type}): {error_msg}")
        
        self.stats.finish()
        
        # Log final summary
        summary = self.stats.get_summary()
        logger.info(f"Scraping completed: {summary['successful_sources']}/{summary['total_sources']} "
                   f"sources successful, {summary['total_jobs_saved']} jobs saved, "
                   f"{summary['total_jobs_updated']} jobs updated")
        
        # Save scraping log to database
        self._save_scraping_log(summary)
        
        return summary
    
    def _scrape_single_source(self, scraper, source_type: str, config_id: Optional[int]) -> Tuple[int, int, int]:
        """Scrape a single job source"""
        jobs_found = 0
        jobs_saved = 0
        jobs_updated = 0
        
        try:
            # Create a new database session for this thread
            db = next(get_db())
            
            logger.info(f"Scraping {scraper.company_name} using {source_type}")
            
            # Fetch jobs from scraper
            jobs = scraper.get_job_listings()
            jobs_found = len(jobs)
            
            # Save jobs to database
            for job_data in jobs:
                try:
                    saved, updated = self._save_job(db, job_data, source_type)
                    if saved:
                        jobs_saved += 1
                    if updated:
                        jobs_updated += 1
                except Exception as e:
                    logger.warning(f"Failed to save job {job_data.title} from {scraper.company_name}: {e}")
            
            # Commit all changes for this scraper
            try:
                db.commit()
            except IntegrityError as e:
                logger.warning(f"Commit failed for {scraper.company_name} due to integrity error: {e}")
                db.rollback()
            except Exception as e:
                logger.error(f"Commit failed for {scraper.company_name}: {e}")
                db.rollback()
                raise
            
            # Update last_scraped timestamp if config_id provided
            if config_id:
                try:
                    self._update_last_scraped(db, config_id)
                    db.commit()
                except Exception as e:
                    logger.warning(f"Failed to update last_scraped for {scraper.company_name}: {e}")
            
            db.close()
            
        except Exception as e:
            logger.error(f"Error scraping {scraper.company_name}: {e}")
            raise
        
        return jobs_found, jobs_saved, jobs_updated
    
    def _save_job(self, db: Session, job_data: JobData, source: str) -> Tuple[bool, bool]:
        """Save or update job in database"""
        saved = False
        updated = False
        
        try:
            # Check if job already exists
            existing_job = db.query(Job).filter(
                Job.source == source,
                Job.source_job_id == job_data.source_job_id
            ).first()
            
            if existing_job:
                # Update existing job
                job_dict = job_data.to_dict()
                for key, value in job_dict.items():
                    if value is not None and hasattr(existing_job, key):
                        setattr(existing_job, key, value)
                
                existing_job.updated_at = datetime.utcnow()
                updated = True
                
            else:
                # Create new job
                job_dict = job_data.to_dict()
                job_dict['source'] = source
                job_dict['created_at'] = datetime.utcnow()
                job_dict['updated_at'] = datetime.utcnow()
                
                job = Job(**job_dict)
                db.add(job)
                saved = True
                
                # Flush to check for integrity errors before committing
                try:
                    db.flush()
                except IntegrityError:
                    # Job already exists (race condition), try to update instead
                    db.rollback()
                    existing_job = db.query(Job).filter(
                        Job.source == source,
                        Job.source_job_id == job_data.source_job_id
                    ).first()
                    
                    if existing_job:
                        # Update the existing job
                        for key, value in job_dict.items():
                            if value is not None and hasattr(existing_job, key) and key not in ['created_at']:
                                setattr(existing_job, key, value)
                        
                        existing_job.updated_at = datetime.utcnow()
                        updated = True
                        saved = False
                    else:
                        # Still can't find it, log and skip
                        logger.warning(f"Integrity error for job {job_data.title} but couldn't find existing record")
                        return False, False
            
        except Exception as e:
            logger.error(f"Error saving job {job_data.title}: {e}")
            db.rollback()
            return False, False
        
        return saved, updated
    
    def _update_last_scraped(self, db: Session, config_id: int):
        """Update last_scraped timestamp for scraper config"""
        try:
            config = db.query(CompanyScraper).filter(CompanyScraper.id == config_id).first()
            if config:
                config.last_scraped_at = datetime.utcnow()
        except Exception as e:
            logger.warning(f"Failed to update last_scraped for config {config_id}: {e}")
    
    def _save_scraping_log(self, summary: Dict[str, Any]):
        """Save scraping log to database"""
        try:
            log = ScrapingLog(
                source='orchestrator',
                company_name='all',
                jobs_found=summary['total_jobs_found'],
                jobs_added=summary['total_jobs_saved'],
                jobs_updated=summary['total_jobs_updated'],
                status='completed' if summary['failed_sources'] == 0 else ('failed' if summary['successful_sources'] == 0 else 'completed'),
                error_message='; '.join(summary['errors']) if summary['errors'] else None,
                started_at=summary['start_time'],
                completed_at=summary['end_time']
            )
            
            self.db.add(log)
            self.db.commit()
            
        except Exception as e:
            logger.warning(f"Failed to save scraping log: {e}")
    
    def scrape_company(self, company_name: str) -> Dict[str, Any]:
        """Scrape jobs for a specific company"""
        matching_scrapers = [
            (scraper, source_type, config_id) 
            for scraper, source_type, config_id in self.scrapers 
            if scraper.company_name.lower() == company_name.lower()
        ]
        
        if not matching_scrapers:
            raise ValueError(f"No scraper found for company: {company_name}")
        
        self.stats = ScrapingStats()
        
        for scraper, source_type, config_id in matching_scrapers:
            try:
                jobs_found, jobs_saved, jobs_updated = self._scrape_single_source(scraper, source_type, config_id)
                self.stats.add_source_result(
                    scraper.company_name, source_type, jobs_found, jobs_saved, jobs_updated
                )
            except Exception as e:
                self.stats.add_source_result(
                    scraper.company_name, source_type, 0, 0, 0, str(e)
                )
        
        self.stats.finish()
        return self.stats.get_summary()
    
    def get_scraper_status(self) -> List[Dict[str, Any]]:
        """Get status of all configured scrapers"""
        status_list = []
        
        for scraper, source_type, config_id in self.scrapers:
            status = {
                'company_name': scraper.company_name,
                'scraper_type': source_type,
                'config_id': config_id,
                'is_valid': False,
                'last_scraped': None,
                'error': None
            }
            
            try:
                # Validate configuration
                if source_type == 'greenhouse':
                    status['is_valid'] = validate_greenhouse_token(scraper.company_token)
                elif source_type == 'lever':
                    status['is_valid'] = validate_lever_handle(scraper.company_handle)
                elif source_type == 'workday':
                    status['is_valid'] = validate_workday_url(scraper.careers_url)
                
                # Get last scraped time from database
                if config_id:
                    try:
                        config = self.db.query(CompanyScraper).filter(CompanyScraper.id == config_id).first()
                        if config:
                            status['last_scraped'] = config.last_scraped_at
                    except Exception:
                        pass
                
            except Exception as e:
                status['error'] = str(e)
            
            status_list.append(status)
        
        return status_list

# Utility function for standalone scraping
def run_scraping_job(config_source: str = 'database') -> Dict[str, Any]:
    """Standalone function to run scraping job"""
    orchestrator = ScrapingOrchestrator()
    orchestrator.load_scraper_configs(config_source)
    return orchestrator.scrape_all() 