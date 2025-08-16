from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.user import Application, Job
from app.schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationResponse
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/", response_model=List[ApplicationResponse])
async def get_applications(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all applications for the current user"""
    applications = db.query(Application).filter(
        Application.user_id == current_user["id"]
    ).all()
    return applications

@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific application by ID"""
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user["id"]
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application

@router.post("/", response_model=ApplicationResponse)
async def create_application(
    application_data: ApplicationCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Apply to a job"""
    # Check if job exists
    job = db.query(Job).filter(Job.id == application_data.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if user already applied to this job
    existing_application = db.query(Application).filter(
        Application.user_id == current_user["id"],
        Application.job_id == application_data.job_id
    ).first()
    if existing_application:
        raise HTTPException(status_code=400, detail="Already applied to this job")
    
    application = Application(
        **application_data.dict(),
        user_id=current_user["id"]
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application

@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: int,
    application_data: ApplicationUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an application"""
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user["id"]
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    for field, value in application_data.dict(exclude_unset=True).items():
        setattr(application, field, value)
    
    db.commit()
    db.refresh(application)
    return application

@router.delete("/{application_id}")
async def delete_application(
    application_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an application"""
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user["id"]
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    db.delete(application)
    db.commit()
    return {"message": "Application deleted"} 