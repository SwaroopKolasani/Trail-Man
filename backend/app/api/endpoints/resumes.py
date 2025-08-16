from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.db.session import get_db
from app.models.user import Resume
from app.schemas.resume import (
    ResumeCreate, ResumeResponse, ResumeUpdate,
    CompileRequest, CompileResponse, TemplateListResponse, ResumeTemplate
)
from app.core.auth import get_current_user
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
        description="Contemporary design with clean typography and modern layout",
        content="""\\documentclass[11pt,a4paper,sans]{moderncv}
\\moderncvstyle{banking}
\\moderncvcolor{blue}

\\usepackage[scale=0.8]{geometry}
\\name{Your}{Name}
\\title{Software Developer}
\\email{your.email@example.com}
\\phone[mobile]{+1~(555)~123~4567}
\\social[linkedin]{yourprofile}
\\social[github]{yourusername}

\\begin{document}
\\makecvtitle

\\section{Experience}
\\cventry{2020--Present}{Software Engineer}{Company Name}{Location}{}{
\\begin{itemize}
\\item Developed full-stack applications using modern web technologies
\\item Led a team of 3 developers on key projects
\\item Implemented CI/CD pipelines reducing deployment time by 60\\%
\\end{itemize}}

\\section{Education}
\\cventry{2016--2020}{B.S. Computer Science}{University Name}{Location}{GPA: 3.8/4.0}{}

\\section{Technical Skills}
\\cvitem{Programming}{JavaScript, Python, Java, C++}
\\cvitem{Web}{React, Node.js, Express, MongoDB, PostgreSQL}
\\cvitem{Tools}{Docker, Kubernetes, AWS, Git, Jenkins}

\\section{Projects}
\\cventry{2023}{Open Source Contributor}{Project Name}{}{}{
Contributed to popular open-source project with 10k+ stars on GitHub}

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

@router.get("/", response_model=List[ResumeResponse])
async def get_my_resumes(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resumes = db.query(Resume).filter(Resume.user_id == current_user["user_id"]).all()
    return resumes

@router.get("/{resume_id}/", response_model=ResumeResponse)
async def get_resume(
    resume_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user["user_id"]
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    return resume

@router.post("/", response_model=ResumeResponse)
async def create_resume(
    resume_data: ResumeCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resume = Resume(
        user_id=current_user["user_id"],
        **resume_data.dict()
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume

@router.put("/{resume_id}/", response_model=ResumeResponse)
async def update_resume(
    resume_id: int,
    resume_data: ResumeUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user["user_id"]
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    for field, value in resume_data.dict(exclude_unset=True).items():
        setattr(resume, field, value)
    
    resume.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(resume)
    
    return resume

@router.post("/compile/", response_model=CompileResponse)
async def compile_latex(
    request: CompileRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Compile LaTeX content to PDF"""
    try:
        # Compile LaTeX
        success, pdf_url, errors = latex_compiler.compile_latex(
            request.latex_content,
            current_user["user_id"],
            request.resume_id
        )
        
        # Update resume record if resume_id provided and compilation succeeded
        if request.resume_id:
            resume = db.query(Resume).filter(
                Resume.id == request.resume_id,
                Resume.user_id == current_user["user_id"]
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

@router.get("/templates/", response_model=TemplateListResponse)
async def get_resume_templates():
    """Get available LaTeX resume templates"""
    return TemplateListResponse(templates=list(RESUME_TEMPLATES.values()))

@router.get("/templates/{template_name}/")
async def get_template_content(template_name: str):
    """Get LaTeX content for a specific template"""
    if template_name not in RESUME_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template = RESUME_TEMPLATES[template_name]
    return {
        "name": template.name,
        "display_name": template.display_name,
        "description": template.description,
        "content": template.content
    }

@router.post("/upload/", response_model=ResumeResponse)
async def upload_resume(
    file: UploadFile = File(...),
    name: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # For now, we'll just store the filename
    # In production, you'd upload to S3 or similar storage
    resume_name = name or file.filename.replace('.pdf', '')
    
    resume = Resume(
        user_id=current_user["user_id"],
        name=resume_name,
        pdf_url=f"/uploads/{file.filename}",  # Placeholder URL
        is_primary=False
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume

@router.put("/{resume_id}/set-primary/", response_model=ResumeResponse)
async def set_primary_resume(
    resume_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # First, unset all other resumes as primary
    db.query(Resume).filter(Resume.user_id == current_user["user_id"]).update(
        {"is_primary": False}
    )
    
    # Set the selected resume as primary
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user["user_id"]
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    resume.is_primary = True
    db.commit()
    db.refresh(resume)
    return resume

@router.delete("/{resume_id}/")
async def delete_resume(
    resume_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user["user_id"]
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    db.delete(resume)
    db.commit()
    return {"message": "Resume deleted successfully"} 