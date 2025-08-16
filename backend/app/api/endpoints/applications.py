from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.user import Application, Job, Resume
from app.schemas.application import ApplicationCreate, ApplicationResponse, ApplicationUpdate
from app.core.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=ApplicationResponse)
async def create_application(
    application_data: ApplicationCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if job exists
    job = db.query(Job).filter(Job.id == application_data.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if user already applied to this job
    existing_application = db.query(Application).filter(
        Application.user_id == current_user["user_id"],
        Application.job_id == application_data.job_id
    ).first()
    if existing_application:
        raise HTTPException(status_code=400, detail="Already applied to this job")
    
    application = Application(
        user_id=current_user["user_id"],
        job_id=application_data.job_id,
        resume_id=application_data.resume_id,
        status="applied"
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application

@router.get("/", response_model=List[ApplicationResponse])
async def get_my_applications(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    applications = db.query(Application).filter(
        Application.user_id == current_user["user_id"]
    ).all()
    return applications

@router.put("/{application_id}/", response_model=ApplicationResponse)
async def update_application(
    application_id: int,
    application_data: ApplicationUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user["user_id"]
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    for field, value in application_data.dict(exclude_unset=True).items():
        setattr(application, field, value)
    
    db.commit()
    db.refresh(application)
    return application

@router.delete("/{application_id}/")
async def delete_application(
    application_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user["user_id"]
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    db.delete(application)
    db.commit()
    return {"message": "Application deleted successfully"} 