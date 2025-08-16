from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/webhook")
async def clerk_webhook(request: dict, db: Session = Depends(get_db)):
    """Handle Clerk webhook for user creation"""
    if request["type"] == "user.created":
        user_data = request["data"]
        db_user = User(
            id=user_data["id"],
            email=user_data["email_addresses"][0]["email_address"]
        )
        db.add(db_user)
        db.commit()
    return {"status": "ok"}

@router.get("/me")
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user information"""
    return current_user 