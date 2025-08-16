from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Trail-Man"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    MYSQL_SERVER: str = os.environ.get("MYSQL_SERVER", "localhost")
    MYSQL_USER: str = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.environ.get("MYSQL_PASSWORD", "0428@nani")
    MYSQL_DB: str = os.environ.get("MYSQL_DB", "trail_man_db")
    
    CLERK_SECRET_KEY: str = os.environ.get("CLERK_SECRET_KEY", "")
    CLERK_PUBLIC_KEY: str = os.environ.get("CLERK_PUBLIC_KEY", "")
    
    AWS_ACCESS_KEY_ID: Optional[str] = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.environ.get("AWS_SECRET_ACCESS_KEY")
    AWS_S3_BUCKET: Optional[str] = os.environ.get("AWS_S3_BUCKET")
    
    # Selenium and Chrome configuration
    SELENIUM_ENABLED: bool = os.environ.get("SELENIUM_ENABLED", "true").lower() == "true"
    CHROME_BIN: Optional[str] = os.environ.get("CHROME_BIN")
    CHROME_DRIVER_PATH: Optional[str] = os.environ.get("CHROME_DRIVER_PATH")
    HEADLESS_BROWSER: bool = os.environ.get("HEADLESS_BROWSER", "true").lower() == "true"
    BROWSER_TIMEOUT: int = int(os.environ.get("BROWSER_TIMEOUT", "30"))
    
    # Redis configuration for Celery
    REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    
    class Config:
        env_file = "/app/.env"
        env_file_encoding = 'utf-8'

settings = Settings() 