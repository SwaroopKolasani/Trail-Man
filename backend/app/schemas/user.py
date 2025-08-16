"""
User schemas for Trail-Man

Pydantic schemas for user-related API operations including
user synchronization and profile management.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    first_name: str
    last_name: str

class UserCreate(UserBase):
    """Schema for creating a new user"""
    pass

class UserSync(UserBase):
    """Schema for synchronizing user data from Clerk"""
    pass

class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserResponse(UserBase):
    """Schema for user response data"""
    id: int
    clerk_user_id: str
    full_name: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True  # For Pydantic v2 compatibility

class UserProfile(UserResponse):
    """Extended user profile with additional information"""
    total_applications: int = 0
    total_resumes: int = 0
    last_login: Optional[datetime] = None 