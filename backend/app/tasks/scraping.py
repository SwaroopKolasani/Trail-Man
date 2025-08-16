from celery import current_task
from app.core.celery_app import celery_app
from app.scrapers.orchestrator import ScrapingOrchestrator, run_scraping_job
from app.db.session import get_db
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name='app.tasks.scraping.scrape_all_jobs')
def scrape_all_jobs(self):
    """Celery task to run all job scrapers"""
    try:
        logger.info("Starting automated job scraping task")
        
        # Update task state
        self.update_state(state='PROGRESS', meta={'status': 'Starting scrapers...'})
        
        # Run scraping
        summary = run_scraping_job('database')
        
        # Update task state with results
        self.update_state(
            state='SUCCESS',
            meta={
                'status': 'Completed successfully',
                'summary': summary
            }
        )
        
        logger.info(f"Scraping task completed: {summary['successful_sources']}/{summary['total_sources']} sources successful")
        return summary
        
    except Exception as e:
        logger.error(f"Scraping task failed: {e}")
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'Failed',
                'error': str(e)
            }
        )
        raise

@celery_app.task(bind=True, name='app.tasks.scraping.scrape_single_company')
def scrape_single_company(self, company_name: str):
    """Celery task to scrape jobs for a specific company"""
    try:
        logger.info(f"Starting scraping task for company: {company_name}")
        
        self.update_state(state='PROGRESS', meta={'status': f'Scraping {company_name}...'})
        
        # Create orchestrator and scrape specific company
        orchestrator = ScrapingOrchestrator()
        orchestrator.load_scraper_configs('database')
        summary = orchestrator.scrape_company(company_name)
        
        self.update_state(
            state='SUCCESS',
            meta={
                'status': f'Completed scraping {company_name}',
                'summary': summary
            }
        )
        
        logger.info(f"Company scraping completed for {company_name}: {summary}")
        return summary
        
    except Exception as e:
        logger.error(f"Company scraping task failed for {company_name}: {e}")
        self.update_state(
            state='FAILURE',
            meta={
                'status': f'Failed to scrape {company_name}',
                'error': str(e)
            }
        )
        raise

@celery_app.task(bind=True, name='app.tasks.scraping.validate_all_scrapers')
def validate_all_scrapers(self):
    """Celery task to validate all scraper configurations"""
    try:
        logger.info("Starting scraper validation task")
        
        self.update_state(state='PROGRESS', meta={'status': 'Validating scrapers...'})
        
        orchestrator = ScrapingOrchestrator()
        orchestrator.load_scraper_configs('database')
        status_list = orchestrator.get_scraper_status()
        
        # Count valid vs invalid scrapers
        valid_count = sum(1 for status in status_list if status['is_valid'])
        total_count = len(status_list)
        
        result = {
            'total_scrapers': total_count,
            'valid_scrapers': valid_count,
            'invalid_scrapers': total_count - valid_count,
            'scraper_status': status_list
        }
        
        self.update_state(
            state='SUCCESS',
            meta={
                'status': 'Validation completed',
                'result': result
            }
        )
        
        logger.info(f"Scraper validation completed: {valid_count}/{total_count} scrapers valid")
        return result
        
    except Exception as e:
        logger.error(f"Scraper validation task failed: {e}")
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'Validation failed',
                'error': str(e)
            }
        )
        raise

@celery_app.task(name='app.tasks.scraping.test_single_scraper')
def test_single_scraper(company_name: str, scraper_type: str, config: dict):
    """Test a single scraper configuration without saving to database"""
    try:
        logger.info(f"Testing {scraper_type} scraper for {company_name}")
        
        # Import scraper class
        from app.scrapers.greenhouse import GreenhouseScraper
        from app.scrapers.lever import LeverScraper  
        from app.scrapers.workday import WorkdayScraper
        
        scraper_classes = {
            'greenhouse': GreenhouseScraper,
            'lever': LeverScraper,
            'workday': WorkdayScraper
        }
        
        if scraper_type not in scraper_classes:
            raise ValueError(f"Unknown scraper type: {scraper_type}")
        
        # Create and test scraper
        scraper_class = scraper_classes[scraper_type]
        scraper = scraper_class(company_name, config)
        
        # Fetch a limited number of jobs for testing
        jobs = scraper.get_job_listings()
        
        # Limit results for testing
        test_jobs = jobs[:5] if len(jobs) > 5 else jobs
        
        result = {
            'success': True,
            'total_jobs_found': len(jobs),
            'sample_jobs': [
                {
                    'title': job.title,
                    'company': job.company,
                    'location': job.location,
                    'job_type': job.job_type,
                    'remote_type': job.remote_type,
                    'source_job_id': job.source_job_id
                }
                for job in test_jobs
            ],
            'scraper_type': scraper_type,
            'company_name': company_name
        }
        
        logger.info(f"Scraper test completed for {company_name}: {len(jobs)} jobs found")
        return result
        
    except Exception as e:
        logger.error(f"Scraper test failed for {company_name}: {e}")
        return {
            'success': False,
            'error': str(e),
            'scraper_type': scraper_type,
            'company_name': company_name
        }

# Helper task for monitoring and notifications
@celery_app.task(name='app.tasks.scraping.get_scraping_stats')
def get_scraping_stats(days: int = 7):
    """Get scraping statistics for the last N days"""
    try:
        from datetime import datetime, timedelta
        from app.models.user import Job
        from sqlalchemy import func
        
        db = next(get_db())
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query statistics
        stats = {
            'total_jobs': db.query(Job).count(),
            'jobs_added_period': db.query(Job).filter(
                Job.created_at >= start_date
            ).count(),
            'jobs_by_source': db.query(
                Job.source, func.count(Job.id)
            ).group_by(Job.source).all(),
            'jobs_by_company': db.query(
                Job.company, func.count(Job.id)
            ).group_by(Job.company).order_by(
                func.count(Job.id).desc()
            ).limit(10).all(),
            'period_days': days,
            'start_date': start_date,
            'end_date': end_date
        }
        
        db.close()
        
        # Convert to serializable format
        stats['jobs_by_source'] = [{'source': source, 'count': count} for source, count in stats['jobs_by_source']]
        stats['jobs_by_company'] = [{'company': company, 'count': count} for company, count in stats['jobs_by_company']]
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get scraping stats: {e}")
        raise 

# Updated task names for the admin API
@celery_app.task(bind=True, name='app.tasks.scraping.trigger_all_scrapers_task')
def trigger_all_scrapers_task(self):
    """Celery task to scrape jobs from all configured sources"""
    return scrape_all_jobs(self)

@celery_app.task(bind=True, name='app.tasks.scraping.trigger_company_scraper_task')
def trigger_company_scraper_task(self, company_name: str):
    """Celery task to scrape jobs for a specific company"""
    return scrape_single_company(self, company_name)

@celery_app.task(bind=True, name='app.tasks.scraping.validate_scraper_config_task')
def validate_scraper_config_task(self):
    """Celery task to validate all scraper configurations"""
    return validate_all_scrapers(self)

@celery_app.task(name='app.tasks.scraping.get_scraping_statistics_task')
def get_scraping_statistics_task(days: int = 7):
    """Get scraping statistics for the last N days"""
    return get_scraping_stats(days)

@celery_app.task(name='app.tasks.scraping.cleanup_old_jobs_task')
def cleanup_old_jobs_task(days: int = 90):
    """Clean up old job listings"""
    try:
        from datetime import datetime, timedelta
        from app.models.user import Job
        
        db = next(get_db())
        
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Delete old jobs
        deleted_count = db.query(Job).filter(
            Job.created_at < cutoff_date
        ).delete()
        
        db.commit()
        db.close()
        
        logger.info(f"Cleaned up {deleted_count} old job listings older than {days} days")
        return {
            'success': True,
            'deleted_count': deleted_count,
            'cutoff_date': cutoff_date
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup old jobs: {e}")
        return {
            'success': False,
            'error': str(e)
        } 