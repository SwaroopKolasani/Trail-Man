from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.db.session import get_db
from app.models.user import Resume, User
from app.schemas.resume import (
    ResumeCreate, ResumeUpdate, ResumeResponse,
    CompileRequest, CompileResponse, TemplateListResponse, ResumeTemplate
)
from app.core.auth import get_current_user_clerk_id
from app.services.latex_compiler import latex_compiler

router = APIRouter()

# LaTeX Resume Templates
RESUME_TEMPLATES = {
    "professional": ResumeTemplate(
        name="professional",
        display_name="Professional",
        description="Clean, traditional format perfect for corporate environments",
        content="""\\documentclass[11pt,a4paper]{article}
\\usepackage[margin=1in]{geometry}
\\usepackage{hyperref}
\\usepackage{enumitem}

\\begin{document}

\\begin{center}
    {\\LARGE \\textbf{Your Name}} \\\\[5pt]
    \\href{mailto:your.email@example.com}{your.email@example.com} | 
    (555) 123-4567 | 
    \\href{https://linkedin.com/in/yourprofile}{LinkedIn} | 
    \\href{https://github.com/yourusername}{GitHub}
\\end{center}

\\section*{Professional Summary}
Experienced software developer with X years of experience in full-stack development...

\\section*{Experience}
\\textbf{Software Engineer} \\hfill Company Name \\\\
\\textit{June 2020 - Present} \\hfill \\textit{Location}
\\begin{itemize}[leftmargin=*,labelsep=5pt,itemsep=0pt]
    \\item Developed and maintained web applications using React and Node.js
    \\item Collaborated with cross-functional teams to deliver features
    \\item Improved application performance by 40\\%
\\end{itemize}

\\section*{Education}
\\textbf{Bachelor of Science in Computer Science} \\hfill University Name \\\\
\\textit{September 2016 - May 2020} \\hfill \\textit{Location}

\\section*{Skills}
\\textbf{Languages:} JavaScript, Python, Java, SQL \\\\
\\textbf{Technologies:} React, Node.js, Express, PostgreSQL, Docker \\\\
\\textbf{Tools:} Git, AWS, Jenkins, Kubernetes

\\end{document}"""
    ),
    "modern": ResumeTemplate(
        name="modern",
        display_name="Modern",
        description="Contemporary design with clean lines and modern typography",
        content="""\\documentclass[11pt,a4paper]{article}
\\usepackage[margin=0.75in]{geometry}
\\usepackage{hyperref}
\\usepackage{enumitem}
\\usepackage{xcolor}
\\usepackage{titlesec}

\\definecolor{accent}{RGB}{51, 102, 204}

\\titleformat{\\section}{\\color{accent}\\large\\bfseries}{}{0em}{}[\\color{accent}\\titlerule]

\\begin{document}

\\begin{center}
    {\\Huge\\color{accent}\\textbf{Your Name}} \\\\[8pt]
    \\href{mailto:your.email@example.com}{your.email@example.com} \\textbf{|} 
    (555) 123-4567 \\textbf{|} 
    \\href{https://linkedin.com/in/yourprofile}{LinkedIn} \\textbf{|} 
    \\href{https://github.com/yourusername}{GitHub}
\\end{center}

\\section{Professional Summary}
Dynamic software engineer with expertise in modern web technologies and a passion for creating scalable solutions...

\\section{Experience}
\\textbf{Senior Software Engineer} \\hfill \\textbf{Company Name} \\\\
\\textit{June 2020 - Present} \\hfill \\textit{Location}
\\begin{itemize}[leftmargin=*,labelsep=5pt,itemsep=2pt]
    \\item Led development of microservices architecture serving 1M+ users
    \\item Mentored junior developers and conducted code reviews
    \\item Implemented CI/CD pipelines reducing deployment time by 60\\%
\\end{itemize}

\\section{Education}
\\textbf{Bachelor of Science in Computer Science} \\hfill \\textbf{University Name} \\\\
\\textit{September 2016 - May 2020} \\hfill \\textit{Location}

\\section{Technical Skills}
\\textbf{Languages:} JavaScript, TypeScript, Python, Java, Go \\\\
\\textbf{Frontend:} React, Vue.js, Angular, HTML5, CSS3, Sass \\\\
\\textbf{Backend:} Node.js, Express, Django, Spring Boot \\\\
\\textbf{Databases:} PostgreSQL, MongoDB, Redis, MySQL \\\\
\\textbf{Cloud:} AWS, GCP, Docker, Kubernetes, Terraform

\\end{document}"""
    ),
    "minimal": ResumeTemplate(
        name="minimal",
        display_name="Minimal",
        description="Simple, clean design focusing on content over decoration",
        content="""\\documentclass[10pt]{article}
\\usepackage[margin=0.75in]{geometry}
\\usepackage{enumitem}
\\setlist{nosep}
\\pagestyle{empty}

\\begin{document}

\\begin{center}
{\\Large\\bfseries Your Name}\\\\
your.email@example.com | (555) 123-4567
\\end{center}

\\subsection*{Experience}
\\textbf{Software Engineer, Company Name} \\hfill 2020 - Present
\\begin{itemize}
\\item Built scalable web applications serving 100k+ users
\\item Reduced API response time by 50\\% through optimization
\\end{itemize}

\\subsection*{Education}
\\textbf{B.S. Computer Science, University Name} \\hfill 2016 - 2020

\\subsection*{Skills}
JavaScript, Python, React, Node.js, PostgreSQL, AWS, Docker

\\end{document}"""
    )
}

def ensure_user_exists(clerk_user_id: str, db: Session) -> str:
    """Ensure user exists in database, create if not"""
    user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
    if not user:
        # Create user if doesn't exist
        user = User(
            id=clerk_user_id,
            clerk_user_id=clerk_user_id,
            email=f"{clerk_user_id}@placeholder.com",  # Placeholder email
            first_name="User",
            last_name="Name",
            full_name="User Name"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user.id

@router.get("/", response_model=List[ResumeResponse])
async def get_resumes(
    clerk_user_id: str = Depends(get_current_user_clerk_id),
    db: Session = Depends(get_db)
):
    """Get all resumes for the current user"""
    user_id = ensure_user_exists(clerk_user_id, db)
    resumes = db.query(Resume).filter(Resume.user_id == user_id).all()
    return resumes

@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: int,
    clerk_user_id: str = Depends(get_current_user_clerk_id),
    db: Session = Depends(get_db)
):
    """Get a specific resume by ID"""
    user_id = ensure_user_exists(clerk_user_id, db)
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume

@router.post("/", response_model=ResumeResponse)
async def create_resume(
    resume_data: ResumeCreate,
    clerk_user_id: str = Depends(get_current_user_clerk_id),
    db: Session = Depends(get_db)
):
    """Create a new resume"""
    user_id = ensure_user_exists(clerk_user_id, db)
    resume = Resume(**resume_data.dict(), user_id=user_id)
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume

@router.post("/upload", response_model=ResumeResponse)
async def upload_resume(
    file: UploadFile = File(...),
    name: str = None,
    clerk_user_id: str = Depends(get_current_user_clerk_id),
    db: Session = Depends(get_db)
):
    """Upload a PDF resume file"""
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    user_id = ensure_user_exists(clerk_user_id, db)
    
    # In a real application, you would upload to S3 or similar storage
    # For now, we'll create a mock URL
    pdf_url = f"/uploads/{file.filename}"
    
    resume = Resume(
        user_id=user_id,
        name=name or file.filename.replace('.pdf', ''),
        pdf_url=pdf_url
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume

@router.put("/{resume_id}", response_model=ResumeResponse)
async def update_resume(
    resume_id: int,
    resume_data: ResumeUpdate,
    clerk_user_id: str = Depends(get_current_user_clerk_id),
    db: Session = Depends(get_db)
):
    """Update a resume"""
    user_id = ensure_user_exists(clerk_user_id, db)
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    for field, value in resume_data.dict(exclude_unset=True).items():
        setattr(resume, field, value)
    
    resume.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(resume)
    return resume

@router.post("/compile", response_model=CompileResponse)
async def compile_latex(
    request: CompileRequest,
    clerk_user_id: str = Depends(get_current_user_clerk_id),
    db: Session = Depends(get_db)
):
    """Compile LaTeX content to PDF"""
    user_id = ensure_user_exists(clerk_user_id, db)
    
    try:
        # Compile LaTeX
        success, pdf_url, errors = latex_compiler.compile_latex(
            request.latex_content,
            user_id,
            request.resume_id
        )
        
        # Update resume record if resume_id provided and compilation succeeded
        if request.resume_id:
            resume = db.query(Resume).filter(
                Resume.id == request.resume_id,
                Resume.user_id == user_id
            ).first()
            
            if resume:
                if success:
                    resume.pdf_url = pdf_url
                    resume.last_compiled_at = datetime.utcnow()
                    resume.compilation_error = None
                else:
                    resume.compilation_error = "; ".join([err["message"] for err in errors[:3]])
                
                db.commit()
        
        # Separate errors and warnings
        error_list = [err for err in errors if err.get("type") == "error"]
        warning_list = [err for err in errors if err.get("type") == "warning"]
        
        return CompileResponse(
            success=success,
            pdf_url=pdf_url if success else None,
            errors=error_list,
            warnings=warning_list
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compilation failed: {str(e)}")

@router.get("/templates", response_model=TemplateListResponse)
async def get_resume_templates():
    """Get available LaTeX resume templates"""
    return TemplateListResponse(templates=list(RESUME_TEMPLATES.values()))

@router.get("/templates/{template_name}")
async def get_resume_template(template_name: str):
    """Get a specific LaTeX resume template"""
    if template_name not in RESUME_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")
    return RESUME_TEMPLATES[template_name]

@router.put("/{resume_id}/set-primary", response_model=ResumeResponse)
async def set_primary_resume(
    resume_id: int,
    clerk_user_id: str = Depends(get_current_user_clerk_id),
    db: Session = Depends(get_db)
):
    """Set a resume as the primary resume"""
    user_id = ensure_user_exists(clerk_user_id, db)
    
    # First, unset all primary resumes for this user
    db.query(Resume).filter(Resume.user_id == user_id).update(
        {"is_primary": False}
    )
    
    # Set the specified resume as primary
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    resume.is_primary = True
    db.commit()
    db.refresh(resume)
    return resume

@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: int,
    clerk_user_id: str = Depends(get_current_user_clerk_id),
    db: Session = Depends(get_db)
):
    """Delete a resume"""
    user_id = ensure_user_exists(clerk_user_id, db)
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    db.delete(resume)
    db.commit()
    return {"message": "Resume deleted"} 