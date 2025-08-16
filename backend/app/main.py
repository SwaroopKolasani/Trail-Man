from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.api_v1.api import api_router
from app.db.base import Base, engine
import time
import logging
import os
from sqlalchemy.exc import OperationalError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables_with_retry(max_retries: int = 30, base_delay: float = 1.0):
    """Create database tables with exponential backoff retry logic."""
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to create database tables (attempt {attempt + 1}/{max_retries})")
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully!")
            return
        except OperationalError as e:
            if "Connection refused" in str(e) or "Can't connect to MySQL server" in str(e):
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Database connection failed, retrying in {delay} seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                else:
                    logger.error("Max retries exceeded. Could not connect to database.")
                    raise
            else:
                # Re-raise other database errors immediately
                raise
        except Exception as e:
            logger.error(f"Unexpected error creating tables: {e}")
            raise

# Create tables with retry logic
create_tables_with_retry()

# Create static directories if they don't exist
os.makedirs("./static/resumes", exist_ok=True)
os.makedirs("./uploads", exist_ok=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for serving PDFs and uploads
app.mount("/static", StaticFiles(directory="./static"), name="static")
app.mount("/uploads", StaticFiles(directory="./uploads"), name="uploads")

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {"message": "Welcome to Trail-Man API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/health/latex")
def latex_health_check():
    """Check if LaTeX is properly installed"""
    import subprocess
    try:
        result = subprocess.run(['pdflatex', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return {"status": "healthy", "latex_version": result.stdout.split('\n')[0]}
        else:
            return {"status": "unhealthy", "error": "pdflatex command failed"}
    except FileNotFoundError:
        return {"status": "unhealthy", "error": "pdflatex not found"}
    except subprocess.TimeoutExpired:
        return {"status": "unhealthy", "error": "pdflatex timeout"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)} 