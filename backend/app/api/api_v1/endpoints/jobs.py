from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from app.db.session import get_db
from app.models.user import Job
from app.schemas.job import JobCreate, JobUpdate, JobResponse
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/", response_model=List[JobResponse])
async def get_jobs(
    search: Optional[str] = Query(None, description="Search in title and company"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    remote_type: Optional[str] = Query(None, description="Filter by remote type"),
    skip: int = Query(0, ge=0, description="Number of jobs to skip"),
    limit: int = Query(50, le=100, description="Number of jobs to return"),
    db: Session = Depends(get_db)
):
    """Get all jobs with optional filters"""
    query = db.query(Job)
    
    if search:
        query = query.filter(
            or_(
                Job.title.contains(search),
                Job.company.contains(search),
                Job.description.contains(search)
            )
        )
    
    if job_type:
        query = query.filter(Job.job_type == job_type)
    
    if remote_type:
        query = query.filter(Job.remote_type == remote_type)
    
    jobs = query.offset(skip).limit(limit).all()
    return jobs

@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific job by ID"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.post("/", response_model=JobResponse)
async def create_job(
    job_data: JobCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new job listing (admin only)"""
    job = Job(**job_data.dict())
    db.add(job)
    db.commit()
    db.refresh(job)
    return job 