"""
Job scraping endpoints for Trail-Man

This module provides endpoints to trigger job scraping,
monitor scraping status, and manage scraping configurations.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List, Optional

from app.db.session import get_db
from app.core.auth import get_current_user_clerk_id
from app.tasks.scraping import scrape_all_jobs, scrape_single_company, test_single_scraper
from app.models.user import Job, CompanyScraper, ScrapingLog
from app.schemas.scraping import (
    ScrapingTriggerResponse, 
    ScrapingStatusResponse,
    CompanyScraperCreate,
    CompanyScraperResponse,
    ScrapingLogResponse
)

router = APIRouter()

@router.post("/trigger", response_model=ScrapingTriggerResponse)
async def trigger_job_scraping(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger job scraping for all configured companies.
    
    This endpoint starts the job scraping process in the background
    using Celery tasks.
    """
    try:
        # Trigger the Celery task for scraping all jobs
        task = scrape_all_jobs.delay()
        
        return ScrapingTriggerResponse(
            success=True,
            task_id=task.id,
            message="Job scraping started successfully",
            status="queued"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger job scraping: {str(e)}"
        )

@router.post("/trigger/{company_name}", response_model=ScrapingTriggerResponse)
async def trigger_single_company_scraping(
    company_name: str,
    db: Session = Depends(get_db)
):
    """
    Trigger job scraping for a specific company.
    """
    try:
        # Find the company scraper configuration
        scraper_config = db.query(CompanyScraper).filter(
            CompanyScraper.company_name == company_name,
            CompanyScraper.is_active == True
        ).first()
        
        if not scraper_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active scraper configuration found for {company_name}"
            )
        
        # Trigger the Celery task for single company
        task = scrape_single_company.delay(
            company_name=scraper_config.company_name,
            scraper_type=scraper_config.scraper_type,
            config=scraper_config.config_data
        )
        
        return ScrapingTriggerResponse(
            success=True,
            task_id=task.id,
            message=f"Job scraping started for {company_name}",
            status="queued",
            company_name=company_name
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger scraping for {company_name}: {str(e)}"
        )

@router.get("/status/{task_id}", response_model=ScrapingStatusResponse)
async def get_scraping_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Get the status of a scraping task"""
    try:
        from celery.result import AsyncResult
        from app.core.celery_app import celery_app
        
        result = AsyncResult(task_id, app=celery_app)
        
        return ScrapingStatusResponse(
            task_id=task_id,
            status=result.status,
            result=result.result if result.ready() else None,
            progress=getattr(result, 'info', {}) if hasattr(result, 'info') else {}
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )

@router.get("/logs", response_model=List[ScrapingLogResponse])
async def get_scraping_logs(
    limit: int = 50,
    skip: int = 0,
    company_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get recent scraping logs"""
    try:
        query = db.query(ScrapingLog)
        
        if company_name:
            query = query.filter(ScrapingLog.company_name == company_name)
        
        logs = query.order_by(ScrapingLog.started_at.desc()).offset(skip).limit(limit).all()
        
        return [ScrapingLogResponse.from_orm(log) for log in logs]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scraping logs: {str(e)}"
        )

@router.get("/companies", response_model=List[CompanyScraperResponse])
async def get_scraper_configurations(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get all scraper configurations"""
    try:
        query = db.query(CompanyScraper)
        
        if active_only:
            query = query.filter(CompanyScraper.is_active == True)
        
        scrapers = query.all()
        
        return [CompanyScraperResponse.from_orm(scraper) for scraper in scrapers]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scraper configurations: {str(e)}"
        )

@router.post("/companies", response_model=CompanyScraperResponse)
async def create_scraper_configuration(
    scraper_config: CompanyScraperCreate,
    clerk_user_id: str = Depends(get_current_user_clerk_id),
    db: Session = Depends(get_db)
):
    """Create a new scraper configuration"""
    try:
        # Check if scraper already exists for this company
        existing_scraper = db.query(CompanyScraper).filter(
            CompanyScraper.company_name == scraper_config.company_name
        ).first()
        
        if existing_scraper:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Scraper configuration already exists for {scraper_config.company_name}"
            )
        
        # Create new scraper configuration
        new_scraper = CompanyScraper(
            company_name=scraper_config.company_name,
            scraper_type=scraper_config.scraper_type,
            config_data=scraper_config.config_data,
            is_active=scraper_config.is_active
        )
        
        db.add(new_scraper)
        db.commit()
        db.refresh(new_scraper)
        
        return CompanyScraperResponse.from_orm(new_scraper)
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create scraper configuration: {str(e)}"
        )

@router.post("/test", response_model=Dict[str, Any])
async def test_scraper_configuration(
    company_name: str,
    scraper_type: str,
    config_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Test a scraper configuration without saving to database"""
    try:
        # Trigger the test scraper task
        task = test_single_scraper.delay(
            company_name=company_name,
            scraper_type=scraper_type,
            config=config_data
        )
        
        return {
            "success": True,
            "task_id": task.id,
            "message": f"Test scraper started for {company_name}",
            "status": "queued"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test scraper configuration: {str(e)}"
        )

@router.get("/stats", response_model=Dict[str, Any])
async def get_scraping_statistics(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get scraping statistics for the last N days"""
    try:
        from datetime import datetime, timedelta
        
        start_date = datetime.now() - timedelta(days=days)
        
        # Get basic statistics
        total_jobs = db.query(Job).filter(Job.created_at >= start_date).count()
        total_logs = db.query(ScrapingLog).filter(ScrapingLog.started_at >= start_date).count()
        active_scrapers = db.query(CompanyScraper).filter(CompanyScraper.is_active == True).count()
        
        # Get jobs by company
        jobs_by_company = db.query(Job.company, func.count(Job.id)).filter(
            Job.created_at >= start_date
        ).group_by(Job.company).all()
        
        return {
            "period_days": days,
            "total_jobs_scraped": total_jobs,
            "total_scraping_runs": total_logs,
            "active_scrapers": active_scrapers,
            "jobs_by_company": [{"company": company, "count": count} for company, count in jobs_by_company],
            "start_date": start_date.isoformat(),
            "end_date": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scraping statistics: {str(e)}"
        ) 