from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class JobType(str, Enum):
    full_time = "full-time"
    part_time = "part-time"
    contract = "contract"
    internship = "internship"

class RemoteType(str, Enum):
    onsite = "onsite"
    remote = "remote"
    hybrid = "hybrid"

class JobBase(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    salary_range: Optional[str] = None
    job_type: Optional[JobType] = None
    remote_type: Optional[RemoteType] = None
    external_url: Optional[str] = None
    posted_date: Optional[datetime] = None

class JobCreate(JobBase):
    pass

class JobUpdate(JobBase):
    title: Optional[str] = None
    company: Optional[str] = None

class JobResponse(JobBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True 