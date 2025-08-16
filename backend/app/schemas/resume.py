from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ResumeBase(BaseModel):
    name: str
    latex_content: Optional[str] = None
    pdf_url: Optional[str] = None
    template_name: Optional[str] = None
    is_primary: bool = False

class ResumeCreate(ResumeBase):
    pass

class ResumeUpdate(BaseModel):
    name: Optional[str] = None
    latex_content: Optional[str] = None
    pdf_url: Optional[str] = None
    template_name: Optional[str] = None
    is_primary: Optional[bool] = None

class ResumeResponse(ResumeBase):
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime
    last_compiled_at: Optional[datetime] = None
    compilation_error: Optional[str] = None
    
    class Config:
        from_attributes = True

class CompileRequest(BaseModel):
    latex_content: str
    resume_id: Optional[int] = None

class CompilationError(BaseModel):
    line: Optional[int] = None
    message: str
    type: str = "error"  # "error" or "warning"

class CompileResponse(BaseModel):
    success: bool
    pdf_url: Optional[str] = None
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []

class ResumeTemplate(BaseModel):
    name: str
    display_name: str
    description: str
    content: str
    preview_image: Optional[str] = None

class TemplateListResponse(BaseModel):
    templates: List[ResumeTemplate] 