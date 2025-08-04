# LaTeX Resume Editor Setup Guide

## Overview

The LaTeX Resume Editor provides a seamless, in-app experience for creating and editing professional LaTeX resumes with live preview. It features:

- **Two-panel interface**: LaTeX editor on the left, PDF preview on the right
- **Live preview**: Debounced auto-compilation (1.5s delay after typing stops)
- **Professional templates**: 3 built-in templates (Professional, Modern, Minimal)
- **Error handling**: Detailed compilation error messages with line numbers
- **PDF generation**: Instant download of compiled PDFs
- **Save functionality**: Persistent storage of LaTeX source and compiled PDFs

## Architecture

### Frontend Components
- **Editor Page** (`/resume/editor`): Main editing interface with CodeMirror and react-pdf
- **Resume List** (`/resume`): Updated with LaTeX template buttons and edit functionality
- **CodeMirror**: Syntax highlighting and editing for LaTeX
- **react-pdf**: PDF preview with zoom and pagination controls

### Backend Services
- **LaTeX Compiler**: Python service using subprocess to run pdflatex
- **Error Parser**: Intelligent parsing of LaTeX compilation errors and warnings
- **PDF Storage**: Local file system storage (production ready for S3 integration)
- **Template System**: Built-in professional LaTeX templates

### Database Schema
```sql
-- Added to resumes table:
latex_content TEXT,
template_name VARCHAR(100),
last_compiled_at TIMESTAMP,
compilation_error TEXT
```

## Installation & Setup

### 1. Install Frontend Dependencies
```bash
cd frontend
npm install @uiw/react-codemirror @codemirror/lang-markdown @codemirror/theme-one-dark
npm install react-pdf lodash.debounce @types/lodash.debounce
```

### 2. Install LaTeX (Development)
For local development, install LaTeX distribution:

**macOS:**
```bash
brew install --cask mactex
# or minimal version
brew install --cask basictex
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install texlive-latex-base texlive-fonts-recommended texlive-fonts-extra texlive-latex-extra
```

**Windows:**
```bash
# Install MiKTeX or TeX Live from official websites
```

### 3. Docker Setup (Recommended)
The Docker configuration includes full LaTeX installation:

```bash
# Build and run with Docker Compose
docker-compose up --build

# LaTeX health check
curl http://localhost:8000/health/latex
```

## API Endpoints

### LaTeX Compilation
```typescript
POST /api/v1/resumes/compile/
{
  "latex_content": "\\documentclass{article}...",
  "resume_id": 123  // optional
}

// Response
{
  "success": true,
  "pdf_url": "/static/resumes/user123/resume_456.pdf",
  "errors": [],
  "warnings": [...]
}
```

### Template Management
```typescript
GET /api/v1/resumes/templates/
// Returns list of available templates

GET /api/v1/resumes/templates/professional/
// Returns specific template content
```

### Resume CRUD
```typescript
GET /api/v1/resumes/{id}/
PUT /api/v1/resumes/{id}/
POST /api/v1/resumes/
// Enhanced with LaTeX support
```

## Usage Guide

### Creating a New LaTeX Resume

1. **From Resume List Page:**
   - Click one of the template buttons (Professional, Modern, Minimal)
   - Or click "Create LaTeX Resume" if no resumes exist

2. **In the Editor:**
   - Left panel: Edit LaTeX source code
   - Right panel: Live PDF preview
   - Auto-compilation occurs 1.5s after stopping typing
   - Manual "Compile" button for immediate compilation

3. **Error Handling:**
   - Compilation errors appear in bottom panel with line numbers
   - Warnings are shown but don't prevent PDF generation
   - Hover over errors for detailed information

4. **Saving:**
   - Click "Save" to persist changes
   - Auto-saves LaTeX content and PDF URL
   - Resume name is editable in header

### Editing Existing LaTeX Resumes

1. From resume list, click "✏️ Edit LaTeX" on any LaTeX resume
2. Editor loads with existing content and PDF (if available)
3. Edit and save as normal

### Template System

#### Professional Template
- Clean, traditional format
- Perfect for corporate environments
- Sections: Summary, Experience, Education, Skills

#### Modern Template
- Contemporary design with color accents
- Uses moderncv package
- Professional social media integration

#### Minimal Template
- Simple, clean design
- Focus on content over decoration
- Compact single-page layout

## Error Handling

### Common LaTeX Errors

1. **Undefined Control Sequence**
   - Misspelled commands
   - Missing packages
   - Shows line number and problematic command

2. **Missing Packages**
   - Detected automatically
   - Suggests standard alternatives
   - Lists unsupported packages

3. **Syntax Errors**
   - Missing braces, brackets
   - Unmatched environments
   - Line-specific error reporting

### Error Recovery
- Errors don't crash the application
- Previous successful PDF remains visible
- Detailed error messages help debugging
- Compilation timeout protection (30s)

## Customization

### Adding New Templates

1. **Backend** (in `app/api/endpoints/resumes.py`):
```python
RESUME_TEMPLATES["new_template"] = ResumeTemplate(
    name="new_template",
    display_name="New Template",
    description="Description of the template",
    content="\\documentclass{article}..."
)
```

2. **Frontend** (in `/resume/editor/page.tsx`):
```typescript
const RESUME_TEMPLATES = {
  // Add new template here
  new_template: `\\documentclass{article}...`
}
```

3. **Resume List** (in `/resume/page.tsx`):
```jsx
<button onClick={() => createNewResume('new_template')}>
  New Template
</button>
```

### Styling Customization

The editor uses these CSS classes:
- `.cm-editor`: CodeMirror editor
- `.react-pdf__Document`: PDF viewer
- Error panel: Custom styling in component

## Production Deployment

### Environment Variables
```bash
# Optional: AWS S3 for PDF storage
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_S3_BUCKET=trail-man-resumes
AWS_REGION=us-east-1
```

### Performance Considerations

1. **LaTeX Compilation**
   - 30-second timeout prevents hanging
   - Subprocess isolation for security
   - Error logging for debugging

2. **PDF Storage**
   - Local storage for development
   - S3 integration ready for production
   - Automatic cleanup of temporary files

3. **Frontend Optimization**
   - Debounced compilation prevents excessive requests
   - PDF caching with react-pdf
   - Code splitting for editor components

## Troubleshooting

### LaTeX Not Found
```bash
# Check LaTeX installation
pdflatex --version

# Health check endpoint
curl http://localhost:8000/health/latex
```

### Compilation Timeouts
- Check LaTeX content for infinite loops
- Verify package availability
- Review Docker container resources

### PDF Preview Issues
- Ensure PDF.js worker is loaded
- Check CORS settings for static files
- Verify PDF file permissions

### Database Issues
- Ensure new LaTeX fields are migrated
- Check foreign key constraints
- Verify user permissions

## Security Considerations

1. **LaTeX Compilation**
   - Subprocess timeout protection
   - Temporary file cleanup
   - No external network access from LaTeX

2. **File Storage**
   - User-specific directories
   - No executable content in PDFs
   - Regular cleanup of temporary files

3. **Input Validation**
   - LaTeX content size limits
   - Sanitized error messages
   - User authentication required

## Future Enhancements

1. **Collaborative Editing**
   - Real-time collaboration
   - Version history
   - Comment system

2. **Advanced Templates**
   - Industry-specific templates
   - Custom template builder
   - Template marketplace

3. **Integration Features**
   - Direct export to job applications
   - LinkedIn import
   - ATS compatibility checking

4. **Performance Optimizations**
   - WebAssembly LaTeX compilation
   - Client-side PDF generation
   - Incremental compilation 