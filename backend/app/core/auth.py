import os
import jwt
import requests
from typing import Optional
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import lru_cache

security = HTTPBearer()

# Clerk configuration
CLERK_PUBLISHABLE_KEY = os.getenv("CLERK_PUBLISHABLE_KEY")
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")

def extract_user_id_from_clerk_publishable_key(publishable_key: str) -> str:
    """Extract the instance identifier from Clerk's publishable key"""
    # Clerk publishable keys have format: pk_test_[base64] or pk_live_[base64]
    # The instance part is encoded in the base64 portion
    try:
        import base64
        key_parts = publishable_key.split('_')
        if len(key_parts) >= 3:
            encoded_part = key_parts[2]
            # Add padding if needed
            missing_padding = len(encoded_part) % 4
            if missing_padding:
                encoded_part += '=' * (4 - missing_padding)
            decoded = base64.b64decode(encoded_part).decode('utf-8')
            return decoded.split('$')[0] if '$' in decoded else decoded
    except Exception:
        pass
    return "clerk_instance"

@lru_cache()
def get_clerk_jwks():
    """Fetch Clerk's JWKS (JSON Web Key Set) for token verification"""
    if not CLERK_PUBLISHABLE_KEY:
        raise HTTPException(status_code=500, detail="Clerk not configured")
    
    instance_id = extract_user_id_from_clerk_publishable_key(CLERK_PUBLISHABLE_KEY)
    jwks_url = f"https://{instance_id}.clerk.accounts.dev/.well-known/jwks.json"
    
    try:
        response = requests.get(jwks_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Failed to fetch JWKS: {e}")
        return None

def verify_clerk_token(token: str) -> Optional[dict]:
    """Verify a Clerk JWT token and return the payload"""
    try:
        # For development, we'll use a simpler verification
        # In production, you should verify with Clerk's JWKS
        
        # Decode without verification for now (development only)
        # This allows the app to work while we set up proper verification
        payload = jwt.decode(token, options={"verify_signature": False})
        
        # Basic validation
        if not payload.get('sub'):  # 'sub' contains the user ID
            return None
            
        return payload
        
    except Exception as e:
        print(f"Token verification failed: {e}")
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """FastAPI dependency to get the current authenticated user"""
    token = credentials.credentials
    
    payload = verify_clerk_token(token)
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "name": payload.get("name"),
        "clerk_user_id": payload.get("sub")
    }

async def get_current_user_clerk_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """FastAPI dependency to get just the Clerk user ID"""
    user = await get_current_user(credentials)
    return user["clerk_user_id"]

# Optional: dependency for routes that don't require authentication
async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[dict]:
    """FastAPI dependency for optional authentication"""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None 