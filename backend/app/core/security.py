import requests
from fastapi import HTTPException, status
from app.core.config import settings

async def verify_clerk_token(token: str) -> dict:
    """Verify Clerk JWT token and return user data"""
    try:
        # Call Clerk's API to verify the token
        headers = {
            "Authorization": f"Bearer {settings.CLERK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        
        # For now, we'll implement a basic token verification
        # In production, you should use Clerk's JWT verification
        response = requests.get(
            f"https://api.clerk.dev/v1/sessions/{token}",
            headers=headers
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        
        return response.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        ) 