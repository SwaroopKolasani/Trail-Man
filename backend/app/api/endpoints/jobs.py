from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func, text
from typing import List, Optional
from datetime import datetime, timedelta
from app.db.session import get_db
from app.models.user import Job
from app.schemas.job import JobResponse

router = APIRouter()

@router.get("/", response_model=List[JobResponse])
async def get_jobs(
    search: Optional[str] = Query(None, description="Search in title, company, and description"),
    job_type: Optional[str] = Query(None, description="Filter by job type (full-time, part-time, contract, internship)"),
    remote_type: Optional[str] = Query(None, description="Filter by remote type (onsite, remote, hybrid)"),
    country: Optional[str] = Query(None, description="Filter by country (extracted from location)"),
    experience_level: Optional[str] = Query(None, description="Filter by experience level (entry, mid, senior, executive)"),
    min_salary: Optional[int] = Query(None, description="Minimum salary filter"),
    max_salary: Optional[int] = Query(None, description="Maximum salary filter"),
    company_name: Optional[str] = Query(None, description="Filter by specific company"),
    posted_within_days: Optional[int] = Query(None, description="Filter jobs posted within last N days"),
    sort_by: Optional[str] = Query("relevance", description="Sort by: relevance, date_desc, date_asc, company, title"),
    skip: int = Query(0, ge=0, description="Number of jobs to skip"),
    limit: int = Query(50, le=100, description="Number of jobs to return"),
    db: Session = Depends(get_db)
):
    """Get all jobs with enhanced filtering and sorting options"""
    query = db.query(Job)
    
    # Search filter
    if search:
        search_terms = search.split()
        for term in search_terms:
            query = query.filter(
                (Job.title.contains(term)) | 
                (Job.company.contains(term)) |
                (Job.description.contains(term)) |
                (Job.requirements.contains(term))
            )
    
    # Job type filter
    if job_type:
        query = query.filter(Job.job_type == job_type)
    
    # Remote type filter
    if remote_type:
        query = query.filter(Job.remote_type == remote_type)
    
    # Country filter (extract from location)
    if country:
        query = query.filter(Job.location.contains(country))
    
    # Experience level filter (search in title and description)
    if experience_level:
        experience_keywords = {
            'entry': ['entry', 'junior', 'associate', 'graduate', 'new grad', 'intern'],
            'mid': ['mid', 'intermediate', 'experienced', '2-5 years', '3-7 years'],
            'senior': ['senior', 'lead', 'principal', 'staff', '5+ years', '7+ years'],
            'executive': ['director', 'vp', 'vice president', 'head of', 'chief', 'executive']
        }
        
        if experience_level in experience_keywords:
            keywords = experience_keywords[experience_level]
            experience_conditions = []
            for keyword in keywords:
                experience_conditions.append(Job.title.contains(keyword))
                experience_conditions.append(Job.description.contains(keyword))
            
            # Use OR condition for any of the keywords
            from sqlalchemy import or_
            query = query.filter(or_(*experience_conditions))
    
    # Salary range filter
    if min_salary or max_salary:
        # This is a simplified approach - in a real app you'd want to parse salary ranges properly
        if min_salary:
            query = query.filter(Job.salary_range.contains(str(min_salary)))
        if max_salary:
            query = query.filter(Job.salary_range.contains(str(max_salary)))
    
    # Company filter
    if company_name:
        query = query.filter(Job.company.contains(company_name))
    
    # Posted within days filter
    if posted_within_days:
        cutoff_date = datetime.utcnow() - timedelta(days=posted_within_days)
        query = query.filter(
            (Job.posted_date >= cutoff_date) | 
            (Job.created_at >= cutoff_date)
        )
    
    # Sorting
    if sort_by == "date_desc":
        # Sort by posted_date first, then created_at
        query = query.order_by(
            desc(Job.posted_date.is_(None)),  # Non-null posted_date first
            desc(Job.posted_date),
            desc(Job.created_at)
        )
    elif sort_by == "date_asc":
        query = query.order_by(
            asc(Job.posted_date.is_(None)),  # Non-null posted_date first
            asc(Job.posted_date),
            asc(Job.created_at)
        )
    elif sort_by == "company":
        query = query.order_by(asc(Job.company), desc(Job.created_at))
    elif sort_by == "title":
        query = query.order_by(asc(Job.title), desc(Job.created_at))
    else:  # relevance (default)
        if search:
            # Simple relevance scoring based on search term matches
            # In a real app, you'd use full-text search or Elasticsearch
            query = query.order_by(desc(Job.created_at))
        else:
            # Default to newest first when no search
            query = query.order_by(desc(Job.created_at))
    
    jobs = query.offset(skip).limit(limit).all()
    return jobs

@router.get("/filters/countries", response_model=List[str])
async def get_available_countries(
    db: Session = Depends(get_db)
):
    """Get list of available countries from job locations"""
    # Extract unique countries from locations
    # This is a simplified approach - in production you'd want better location parsing
    locations = db.query(Job.location).distinct().filter(Job.location.isnot(None)).all()
    
    countries = set()
    common_countries = [
        'United States', 'USA', 'US', 'Canada', 'United Kingdom', 'UK', 'Germany', 
        'France', 'Netherlands', 'Australia', 'Singapore', 'India', 'Japan', 'Brazil'
    ]
    
    for location_tuple in locations:
        location = location_tuple[0]
        if location:
            # Simple country extraction - check if common countries are in location
            for country in common_countries:
                if country.lower() in location.lower():
                    countries.add(country)
                    break
    
    return sorted(list(countries))

@router.get("/filters/companies", response_model=List[str])
async def get_available_companies(
    db: Session = Depends(get_db)
):
    """Get list of available companies"""
    companies = db.query(Job.company).distinct().filter(Job.company.isnot(None)).all()
    return sorted([company[0] for company in companies if company[0]])

@router.get("/stats")
async def get_job_stats(
    db: Session = Depends(get_db)
):
    """Get job statistics for filtering UI"""
    total_jobs = db.query(Job).count()
    
    # Jobs by type
    jobs_by_type = db.query(Job.job_type, func.count(Job.id)).group_by(Job.job_type).all()
    
    # Jobs by remote type
    jobs_by_remote = db.query(Job.remote_type, func.count(Job.id)).group_by(Job.remote_type).all()
    
    # Jobs by company (top 10)
    jobs_by_company = db.query(Job.company, func.count(Job.id)).group_by(Job.company).order_by(desc(func.count(Job.id))).limit(10).all()
    
    # Recent jobs (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_jobs = db.query(Job).filter(Job.created_at >= week_ago).count()
    
    return {
        "total_jobs": total_jobs,
        "recent_jobs_7_days": recent_jobs,
        "jobs_by_type": [{"type": job_type, "count": count} for job_type, count in jobs_by_type],
        "jobs_by_remote_type": [{"remote_type": remote_type, "count": count} for remote_type, count in jobs_by_remote],
        "top_companies": [{"company": company, "count": count} for company, count in jobs_by_company],
        "generated_at": datetime.utcnow()
    } 