from celery import Celery
from celery.schedules import crontab
from app.core.config import settings
import os

# Create Celery app
celery_app = Celery(
    'trail-man',
    broker=getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0'),
    backend=getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0'),
    include=[
        'app.tasks.scraping',
        'app.tasks.notifications', 
        'app.tasks.maintenance',
        'app.tasks.reports'
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Beat schedule for automated scraping
    beat_schedule={
        'scrape-jobs-daily': {
            'task': 'app.tasks.scraping.scrape_all_jobs',
            'schedule': crontab(hour=2, minute=0),  # 2 AM UTC daily
            'options': {
                'queue': 'scraping',
                'expires': 3600,  # Task expires after 1 hour
                'retry': False    # Don't retry to avoid overlapping
            }
        },
        
        # Clean up old job postings
        'cleanup-old-jobs': {
            'task': 'app.tasks.maintenance.cleanup_old_jobs',
            'schedule': crontab(hour=1, minute=0, day_of_week=1),  # Weekly on Monday at 1 AM
            'options': {'queue': 'maintenance'}
        },
        
        # Generate scraping reports
        'generate-scraping-report': {
            'task': 'app.tasks.reports.generate_daily_scraping_report',
            'schedule': crontab(hour=8, minute=0),  # 8 AM UTC daily
            'options': {'queue': 'reports'}
        }
    },
    
    # Task routing
    task_routes={
        'app.tasks.scraping.*': {'queue': 'scraping'},
        'app.tasks.notifications.*': {'queue': 'notifications'},
        'app.tasks.maintenance.*': {'queue': 'maintenance'},
        'app.tasks.reports.*': {'queue': 'reports'},
    }
)

# Optional: Configure different queues for different priorities
CELERY_TASK_ROUTES = {
    'app.tasks.scraping.scrape_all_jobs': {
        'queue': 'scraping',
        'routing_key': 'scraping.bulk'
    },
    'app.tasks.scraping.scrape_single_company': {
        'queue': 'scraping_priority',
        'routing_key': 'scraping.single'
    }
}

# Update configuration
celery_app.conf.task_routes.update(CELERY_TASK_ROUTES) 