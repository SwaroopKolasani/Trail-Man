from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.celery_app import celery_app
from app.tasks.scraping import (
    trigger_all_scrapers_task,
    trigger_company_scraper_task,
    validate_scraper_config_task,
    get_scraping_statistics_task,
    cleanup_old_jobs_task
)
from app.scrapers.orchestrator import ScrapingOrchestrator
from app.models.user import Job
from sqlalchemy import func, desc

router = APIRouter(prefix="/admin", tags=["Admin"])

def is_admin(current_user: dict = Depends(get_current_user)) -> bool:
    """Check if current user is admin (placeholder implementation)"""
    # TODO: Implement proper admin role checking
    # For now, this is a placeholder that allows all authenticated users
    # In production, you should check user roles/permissions
    return True

@router.post("/scraping/trigger-all")
async def trigger_all_scraping(
    current_user: dict = Depends(get_current_user),
    admin_check: bool = Depends(is_admin)
):
    """Manually trigger scraping for all configured sources"""
    try:
        # Start async Celery task
        task = trigger_all_scrapers_task.delay()
        
        return {
            "message": "Scraping task started successfully",
            "task_id": task.id,
            "status": "PENDING"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scraping task: {str(e)}")

@router.post("/scraping/trigger-company/{company_name}")
async def trigger_company_scraping(
    company_name: str,
    current_user: dict = Depends(get_current_user),
    admin_check: bool = Depends(is_admin)
):
    """Manually trigger scraping for a specific company"""
    try:
        # Start async Celery task
        task = trigger_company_scraper_task.delay(company_name)
        
        return {
            "message": f"Scraping task started for {company_name}",
            "task_id": task.id,
            "company_name": company_name,
            "status": "PENDING"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start company scraping task: {str(e)}")

@router.get("/scraping/task-status/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: dict = Depends(get_current_user),
    admin_check: bool = Depends(is_admin)
):
    """Get status of a scraping task"""
    try:
        task_result = celery_app.AsyncResult(task_id)
        
        response = {
            "task_id": task_id,
            "status": task_result.status,
            "ready": task_result.ready(),
        }
        
        if task_result.ready():
            if task_result.successful():
                response["result"] = task_result.result
            else:
                response["error"] = str(task_result.result)
        else:
            # Get task meta information if available
            if hasattr(task_result, 'info') and task_result.info:
                response["meta"] = task_result.info
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")

@router.post("/scraping/validate-scrapers")
async def validate_scrapers(
    current_user: dict = Depends(get_current_user),
    admin_check: bool = Depends(is_admin)
):
    """Validate all scraper configurations"""
    try:
        task = validate_scraper_config_task.delay()
        
        return {
            "message": "Scraper validation started",
            "task_id": task.id,
            "status": "PENDING"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start validation: {str(e)}")

@router.post("/scraping/test-scraper")
async def test_scraper_config(
    company_name: str,
    scraper_type: str,
    config: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    admin_check: bool = Depends(is_admin)
):
    """Test a scraper configuration without saving results"""
    try:
        # Validate scraper type
        valid_types = ['greenhouse', 'lever', 'workday']
        if scraper_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid scraper type. Must be one of: {valid_types}")
        
        # This task is not directly available in the current tasks.py,
        # so this endpoint will need to be implemented or removed if not used.
        # For now, we'll return a placeholder response.
        return {
            "message": f"Test scraper functionality is not directly available via this endpoint. Please use the scraping/trigger-company/{company_name} endpoint for testing.",
            "company_name": company_name,
            "scraper_type": scraper_type,
            "config": config
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scraper test: {str(e)}")

@router.get("/scraping/stats")
async def get_scraping_statistics(
    days: int = Query(default=7, ge=1, le=365, description="Number of days to include in statistics"),
    current_user: dict = Depends(get_current_user),
    admin_check: bool = Depends(is_admin)
):
    """Get scraping statistics for the specified number of days"""
    try:
        task = get_scraping_statistics_task.delay(days)
        
        return {
            "message": f"Generating scraping statistics for last {days} days",
            "task_id": task.id,
            "days": days,
            "status": "PENDING"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate statistics: {str(e)}")

@router.get("/scraping/status")
async def get_scraper_status(
    current_user: dict = Depends(get_current_user),
    admin_check: bool = Depends(is_admin)
):
    """Get current status of all configured scrapers"""
    try:
        orchestrator = ScrapingOrchestrator()
        orchestrator.load_scraper_configs('database')
        status_list = orchestrator.get_scraper_status()
        
        return {
            "scrapers": status_list,
            "total_scrapers": len(status_list),
            "valid_scrapers": sum(1 for s in status_list if s['is_valid']),
            "invalid_scrapers": sum(1 for s in status_list if not s['is_valid']),
            "last_updated": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scraper status: {str(e)}")

@router.get("/jobs/summary")
async def get_jobs_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    admin_check: bool = Depends(is_admin)
):
    """Get summary of jobs in the database"""
    try:
        # Basic counts
        total_jobs = db.query(Job).count()
        
        # Jobs by source
        jobs_by_source = db.query(
            Job.source, func.count(Job.id).label('count')
        ).group_by(Job.source).all()
        
        # Jobs by company (top 10)
        jobs_by_company = db.query(
            Job.company, func.count(Job.id).label('count')
        ).group_by(Job.company).order_by(desc(func.count(Job.id))).limit(10).all()
        
        # Jobs by type
        jobs_by_type = db.query(
            Job.job_type, func.count(Job.id).label('count')
        ).group_by(Job.job_type).all()
        
        # Jobs by remote type
        jobs_by_remote = db.query(
            Job.remote_type, func.count(Job.id).label('count')
        ).group_by(Job.remote_type).all()
        
        # Recent jobs (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_jobs = db.query(Job).filter(Job.created_at >= week_ago).count()
        
        return {
            "total_jobs": total_jobs,
            "recent_jobs_7_days": recent_jobs,
            "jobs_by_source": [{"source": source, "count": count} for source, count in jobs_by_source],
            "top_companies": [{"company": company, "count": count} for company, count in jobs_by_company],
            "jobs_by_type": [{"type": job_type, "count": count} for job_type, count in jobs_by_type],
            "jobs_by_remote_type": [{"remote_type": remote_type, "count": count} for remote_type, count in jobs_by_remote],
            "generated_at": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate jobs summary: {str(e)}")

@router.delete("/jobs/cleanup")
async def cleanup_old_jobs(
    days_old: int = Query(default=90, ge=30, le=365, description="Delete jobs older than this many days"),
    dry_run: bool = Query(default=True, description="If true, only count jobs that would be deleted"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    admin_check: bool = Depends(is_admin)
):
    """Clean up old job postings"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        # Find jobs to delete
        old_jobs_query = db.query(Job).filter(Job.created_at < cutoff_date)
        job_count = old_jobs_query.count()
        
        if dry_run:
            return {
                "message": f"Dry run: Would delete {job_count} jobs older than {days_old} days",
                "jobs_to_delete": job_count,
                "cutoff_date": cutoff_date,
                "dry_run": True
            }
        else:
            # Actually delete the jobs
            deleted_count = old_jobs_query.delete()
            db.commit()
            
            return {
                "message": f"Deleted {deleted_count} jobs older than {days_old} days",
                "jobs_deleted": deleted_count,
                "cutoff_date": cutoff_date,
                "dry_run": False
            }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to cleanup jobs: {str(e)}")

@router.get("/celery/active-tasks")
async def get_active_tasks(
    current_user: dict = Depends(get_current_user),
    admin_check: bool = Depends(is_admin)
):
    """Get list of active Celery tasks"""
    try:
        # Get active tasks from Celery
        inspect = celery_app.control.inspect()
        
        active_tasks = inspect.active()
        scheduled_tasks = inspect.scheduled()
        reserved_tasks = inspect.reserved()
        
        return {
            "active_tasks": active_tasks,
            "scheduled_tasks": scheduled_tasks,
            "reserved_tasks": reserved_tasks,
            "retrieved_at": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get Celery tasks: {str(e)}")

@router.post("/celery/revoke-task/{task_id}")
async def revoke_task(
    task_id: str,
    terminate: bool = Query(default=False, description="Whether to terminate the task if it's running"),
    current_user: dict = Depends(get_current_user),
    admin_check: bool = Depends(is_admin)
):
    """Revoke a Celery task"""
    try:
        celery_app.control.revoke(task_id, terminate=terminate)
        
        return {
            "message": f"Task {task_id} revoked",
            "task_id": task_id,
            "terminated": terminate
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to revoke task: {str(e)}")

# Health check endpoint for the scraping system
@router.get("/health/scraping")
async def scraping_health_check(
    current_user: dict = Depends(get_current_user),
    admin_check: bool = Depends(is_admin)
):
    """Health check for the scraping system"""
    try:
        health_status = {
            "status": "healthy",
            "components": {},
            "timestamp": datetime.utcnow()
        }
        
        # Check Celery connection
        try:
            inspect = celery_app.control.inspect()
            stats = inspect.stats()
            health_status["components"]["celery"] = {
                "status": "healthy" if stats else "unhealthy",
                "workers": len(stats) if stats else 0
            }
        except Exception as e:
            health_status["components"]["celery"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Check database connection
        try:
            db = next(get_db())
            db.execute("SELECT 1")
            db.close()
            health_status["components"]["database"] = {"status": "healthy"}
        except Exception as e:
            health_status["components"]["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Check scraper configurations
        try:
            orchestrator = ScrapingOrchestrator()
            orchestrator.load_scraper_configs('database')
            scraper_count = len(orchestrator.scrapers)
            health_status["components"]["scrapers"] = {
                "status": "healthy" if scraper_count > 0 else "warning",
                "configured_scrapers": scraper_count
            }
        except Exception as e:
            health_status["components"]["scrapers"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Overall status
        component_statuses = [comp["status"] for comp in health_status["components"].values()]
        if "unhealthy" in component_statuses:
            health_status["status"] = "unhealthy"
        elif "warning" in component_statuses:
            health_status["status"] = "warning"
        
        return health_status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow()
        } 