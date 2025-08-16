"""
Scraping schemas for Trail-Man

Pydantic schemas for scraping-related API operations including
job scraping triggers, status monitoring, and configuration management.
"""

from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime

class ScrapingTriggerResponse(BaseModel):
    """Response for scraping trigger endpoints"""
    success: bool
    task_id: str
    message: str
    status: str
    company_name: Optional[str] = None

class ScrapingStatusResponse(BaseModel):
    """Response for scraping status checks"""
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    progress: Optional[Dict[str, Any]] = None

class CompanyScraperBase(BaseModel):
    """Base schema for company scraper configuration"""
    company_name: str
    scraper_type: str
    config: Dict[str, Any]
    is_active: bool = True

class CompanyScraperCreate(CompanyScraperBase):
    """Schema for creating a new company scraper"""
    pass

class CompanyScraperResponse(CompanyScraperBase):
    """Response schema for company scraper configuration"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ScrapingLogResponse(BaseModel):
    """Response schema for scraping logs"""
    id: int
    company_name: str
    scraper_type: str
    jobs_found: int
    jobs_saved: int
    jobs_updated: int
    execution_time_seconds: Optional[float] = None
    success: bool
    error_message: Optional[str] = None
    started_at: datetime
    
    class Config:
        from_attributes = True

class ScrapingStatsResponse(BaseModel):
    """Response schema for scraping statistics"""
    period_days: int
    total_jobs_scraped: int
    total_scraping_runs: int
    active_scrapers: int
    jobs_by_company: List[Dict[str, Any]]
    start_date: str
    end_date: str 