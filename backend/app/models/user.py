from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer, Enum, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(255), primary_key=True)  # Clerk user ID
    clerk_user_id = Column(String(255), unique=True, nullable=False)  # Also store Clerk ID separately for clarity
    email = Column(String(255), unique=True, nullable=False)
    first_name = Column(String(255))
    last_name = Column(String(255))
    full_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    profile = relationship("Profile", back_populates="user", uselist=False)
    resumes = relationship("Resume", back_populates="user")
    applications = relationship("Application", back_populates="user")

class Profile(Base):
    __tablename__ = "profiles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey("users.id"), unique=True, nullable=False)
    full_name = Column(String(255))
    phone = Column(String(20))
    location = Column(String(255))
    experience = Column(Text)
    education = Column(Text)
    skills = Column(Text)
    linkedin_url = Column(String(255))
    github_url = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="profile")

class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint('source', 'source_job_id', name='unique_source_job'),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    location = Column(String(255))
    description = Column(Text)
    requirements = Column(Text)
    salary_range = Column(String(100))
    job_type = Column(Enum('full-time', 'part-time', 'contract', 'internship'))
    remote_type = Column(Enum('onsite', 'remote', 'hybrid'))
    external_url = Column(String(500))
    posted_date = Column(DateTime)
    # Source tracking fields for job aggregation
    source = Column(String(100), default='manual', index=True)
    source_url = Column(String(500))
    source_job_id = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    applications = relationship("Application", back_populates="job")

class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    latex_content = Column(Text)
    pdf_url = Column(String(500))
    template_name = Column(String(100))
    last_compiled_at = Column(DateTime)
    compilation_error = Column(Text)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="resumes")
    applications = relationship("Application", back_populates="resume")

class Application(Base):
    __tablename__ = "applications"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey("users.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.id"))
    status = Column(Enum('applied', 'screening', 'interview', 'rejected', 'accepted'), default='applied')
    applied_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    resume = relationship("Resume", back_populates="applications")

class CompanyScraper(Base):
    __tablename__ = "company_scrapers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String(255), nullable=False, index=True)
    scraper_type = Column(Enum('greenhouse', 'lever', 'workday', 'icims', 'jobvite', 'custom'), nullable=False, index=True)
    config = Column(JSON)
    is_active = Column(Boolean, default=True, index=True)
    last_scraped_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ScrapingLog(Base):
    __tablename__ = "scraping_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(100), nullable=False, index=True)
    company_name = Column(String(255))
    status = Column(Enum('started', 'completed', 'failed'), default='started', index=True)
    jobs_found = Column(Integer, default=0)
    jobs_added = Column(Integer, default=0)
    jobs_updated = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime) 