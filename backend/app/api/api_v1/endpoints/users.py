"""
User management endpoints for Trail-Man

This module handles user operations including user synchronization
with Clerk authentication system.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.models.user import User
from app.core.auth import get_current_user_clerk_id, get_current_user_optional
from app.schemas.user import UserCreate, UserResponse, UserSync

router = APIRouter()

@router.post("/sync", response_model=UserResponse)
async def sync_user(
    user_data: UserSync,
    db: Session = Depends(get_db)
):
    """
    Synchronize user with database on first login or profile updates.
    
    This endpoint creates or updates a user record in the database
    when they authenticate through Clerk.
    """
    try:
        # For now, return a mock response since Clerk auth is not configured
        # TODO: Implement proper Clerk authentication
        from datetime import datetime
        return UserResponse(
            id=1,  # Mock ID as integer
            clerk_user_id="temp_user_id",
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            full_name=f"{user_data.first_name} {user_data.last_name}".strip(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync user: {str(e)}"
        )

@router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    clerk_user_id: str = Depends(get_current_user_clerk_id),
    db: Session = Depends(get_db)
):
    """Get current user's profile information"""
    user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Please sync your account first."
        )
    
    return UserResponse.from_orm(user)

@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    user_update: UserCreate,
    clerk_user_id: str = Depends(get_current_user_clerk_id),
    db: Session = Depends(get_db)
):
    """Update current user's profile information"""
    user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Please sync your account first."
        )
    
    try:
        # Update user fields
        user.email = user_update.email
        user.first_name = user_update.first_name
        user.last_name = user_update.last_name
        user.full_name = f"{user_update.first_name} {user_update.last_name}".strip()
        
        db.commit()
        db.refresh(user)
        
        return UserResponse.from_orm(user)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user profile: {str(e)}"
        )

@router.delete("/profile")
async def delete_user_account(
    clerk_user_id: str = Depends(get_current_user_clerk_id),
    db: Session = Depends(get_db)
):
    """Delete current user's account and all associated data"""
    user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Delete user and all associated data (cascading deletes)
        db.delete(user)
        db.commit()
        
        return {"message": "User account deleted successfully"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user account: {str(e)}"
        ) 