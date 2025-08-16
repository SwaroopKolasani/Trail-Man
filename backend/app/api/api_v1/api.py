from fastapi import APIRouter
from app.api.endpoints import auth, profile, jobs, applications
from app.api.api_v1.endpoints import users, scraping, resumes

api_router = APIRouter()
 
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(resumes.router, prefix="/resumes", tags=["resumes"])
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(scraping.router, prefix="/scraping", tags=["scraping"]) 