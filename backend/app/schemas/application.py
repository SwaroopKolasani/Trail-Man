from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class ApplicationStatus(str, Enum):
    applied = "applied"
    screening = "screening"
    interview = "interview"
    rejected = "rejected"
    accepted = "accepted"

class ApplicationBase(BaseModel):
    job_id: int
    resume_id: Optional[int] = None
    status: ApplicationStatus = ApplicationStatus.applied

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationUpdate(BaseModel):
    resume_id: Optional[int] = None
    status: Optional[ApplicationStatus] = None

class ApplicationResponse(ApplicationBase):
    id: int
    user_id: str
    applied_at: datetime
    
    class Config:
        from_attributes = True 