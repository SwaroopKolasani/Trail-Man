import os
import tempfile
import subprocess
import shutil
import re
from typing import Tuple, List, Dict, Optional
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CompilationError:
    def __init__(self, line: Optional[int], message: str, error_type: str = "error"):
        self.line = line
        self.message = message
        self.type = error_type
    
    def to_dict(self) -> Dict:
        return {
            "line": self.line,
            "message": self.message,
            "type": self.type
        }

class LaTeXCompiler:
    def __init__(self):
        # For development: use local storage
        # In production: could be extended to use S3
        self.static_dir = "./static/resumes"
        os.makedirs(self.static_dir, exist_ok=True)
    
    def compile_latex(self, latex_content: str, user_id: str, resume_id: Optional[int] = None) -> Tuple[bool, Optional[str], List[Dict]]:
        """
        Compile LaTeX content to PDF
        Returns: (success, pdf_url/path, errors)
        """
        # Create temporary directory for compilation
        with tempfile.TemporaryDirectory() as temp_dir:
            tex_file = os.path.join(temp_dir, 'resume.tex')
            pdf_file = os.path.join(temp_dir, 'resume.pdf')
            log_file = os.path.join(temp_dir, 'resume.log')
            
            try:
                # Write LaTeX content to file
                with open(tex_file, 'w', encoding='utf-8') as f:
                    f.write(latex_content)
                
                # Run pdflatex (twice for references and citations)
                for run_num in range(2):
                    result = subprocess.run(
                        [
                            'pdflatex', 
                            '-interaction=nonstopmode',
                            '-output-directory', temp_dir,
                            '-jobname', 'resume',
                            tex_file
                        ],
                        capture_output=True,
                        text=True,
                        timeout=30,
                        cwd=temp_dir
                    )
                    
                    # If first run fails, don't continue
                    if run_num == 0 and result.returncode != 0:
                        break
                
                # Check if PDF was created successfully
                if os.path.exists(pdf_file) and os.path.getsize(pdf_file) > 0:
                    # Save PDF and get URL
                    pdf_url = self._save_pdf(pdf_file, user_id, resume_id)
                    
                    # Still parse warnings even on success
                    warnings = self._parse_latex_warnings(log_file)
                    return True, pdf_url, [w.to_dict() for w in warnings]
                else:
                    # Parse errors from log file
                    errors = self._parse_latex_errors(log_file, result.stderr)
                    return False, None, [e.to_dict() for e in errors]
                    
            except subprocess.TimeoutExpired:
                logger.warning("LaTeX compilation timeout")
                return False, None, [CompilationError(
                    None, 
                    "Compilation timeout - LaTeX took too long to compile (>30s)",
                    "error"
                ).to_dict()]
            except FileNotFoundError:
                logger.error("pdflatex not found")
                return False, None, [CompilationError(
                    None,
                    "LaTeX compiler not installed - pdflatex command not found",
                    "error"
                ).to_dict()]
            except Exception as e:
                logger.error(f"LaTeX compilation error: {e}")
                return False, None, [CompilationError(
                    None,
                    f"Unexpected compilation error: {str(e)}",
                    "error"
                ).to_dict()]
    
    def _parse_latex_errors(self, log_file: str, stderr_output: str = "") -> List[CompilationError]:
        """Parse LaTeX log file for errors and warnings"""
        errors = []
        
        try:
            # Read log file if it exists
            log_content = ""
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    log_content = f.read()
            
            # Combine log content with stderr
            full_output = log_content + "\n" + stderr_output
            
            # Parse different types of errors
            errors.extend(self._parse_syntax_errors(full_output))
            errors.extend(self._parse_missing_packages(full_output))
            errors.extend(self._parse_undefined_commands(full_output))
            errors.extend(self._parse_general_errors(full_output))
            
            # If no specific errors found but compilation failed
            if not errors:
                if "No pages of output" in full_output:
                    errors.append(CompilationError(
                        None,
                        "No output generated - check your LaTeX syntax and document structure",
                        "error"
                    ))
                elif "Emergency stop" in full_output:
                    errors.append(CompilationError(
                        None,
                        "LaTeX encountered a fatal error and stopped compilation",
                        "error"
                    ))
                else:
                    errors.append(CompilationError(
                        None,
                        "Unknown compilation error - please check your LaTeX syntax",
                        "error"
                    ))
                
        except Exception as e:
            logger.error(f"Error parsing LaTeX errors: {e}")
            errors.append(CompilationError(
                None,
                "Failed to parse compilation errors",
                "error"
            ))
        
        return errors
    
    def _parse_syntax_errors(self, content: str) -> List[CompilationError]:
        """Parse syntax errors with line numbers"""
        errors = []
        
        # Pattern for syntax errors: ! Error message \n l.123 line content
        error_pattern = r'! (.+?)(?:\n|\r\n?)l\.(\d+)(.+?)(?:\n|\r\n?)'
        matches = re.finditer(error_pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            error_message = match.group(1).strip()
            line_number = int(match.group(2))
            line_content = match.group(3).strip()
            
            # Clean up common error messages
            if "Undefined control sequence" in error_message:
                error_message = f"Undefined command in: {line_content}"
            elif "Missing" in error_message and "inserted" in error_message:
                error_message = f"Missing character or bracket: {error_message}"
            
            errors.append(CompilationError(line_number, error_message, "error"))
        
        return errors
    
    def _parse_missing_packages(self, content: str) -> List[CompilationError]:
        """Parse missing package errors"""
        errors = []
        
        package_pattern = r'! LaTeX Error: File `([^\']+)\.sty\' not found'
        matches = re.finditer(package_pattern, content)
        
        for match in matches:
            package_name = match.group(1)
            errors.append(CompilationError(
                None,
                f"Missing LaTeX package: {package_name}. Please use standard packages or remove this dependency.",
                "error"
            ))
        
        return errors
    
    def _parse_undefined_commands(self, content: str) -> List[CompilationError]:
        """Parse undefined command errors"""
        errors = []
        
        # Pattern for undefined control sequences
        undef_pattern = r'! Undefined control sequence\.(?:\n|\r\n?)l\.(\d+).*?\\([a-zA-Z]+)'
        matches = re.finditer(undef_pattern, content, re.MULTILINE)
        
        for match in matches:
            line_number = int(match.group(1))
            command = match.group(2)
            errors.append(CompilationError(
                line_number,
                f"Undefined command: \\{command}",
                "error"
            ))
        
        return errors
    
    def _parse_general_errors(self, content: str) -> List[CompilationError]:
        """Parse general LaTeX errors"""
        errors = []
        
        # General error pattern
        general_pattern = r'! (.+?)(?:\n|\r\n?)(?:l\.(\d+))?'
        matches = re.finditer(general_pattern, content, re.MULTILINE)
        
        seen_errors = set()
        for match in matches:
            error_message = match.group(1).strip()
            line_number = int(match.group(2)) if match.group(2) else None
            
            # Skip if we've already seen this error
            error_key = (line_number, error_message)
            if error_key in seen_errors:
                continue
            seen_errors.add(error_key)
            
            # Filter out non-error messages
            if any(skip in error_message.lower() for skip in [
                'undefined control sequence',  # Handled separately
                'file not found',  # Handled separately
                'package',  # Handled separately
            ]):
                continue
            
            if error_message and len(error_message) > 10:  # Ignore very short messages
                errors.append(CompilationError(line_number, error_message, "error"))
        
        return errors[:5]  # Limit to first 5 general errors
    
    def _parse_latex_warnings(self, log_file: str) -> List[CompilationError]:
        """Parse LaTeX warnings (non-fatal issues)"""
        warnings = []
        
        try:
            if not os.path.exists(log_file):
                return warnings
                
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                log_content = f.read()
            
            # Pattern for LaTeX warnings
            warning_pattern = r'LaTeX Warning: (.+?)(?:\n|\r\n?)'
            matches = re.finditer(warning_pattern, log_content, re.MULTILINE)
            
            seen_warnings = set()
            for match in matches[:3]:  # Limit to 3 warnings
                warning_message = match.group(1).strip()
                
                if warning_message not in seen_warnings:
                    seen_warnings.add(warning_message)
                    warnings.append(CompilationError(
                        None,
                        f"Warning: {warning_message}",
                        "warning"
                    ))
                
        except Exception as e:
            logger.error(f"Error parsing LaTeX warnings: {e}")
        
        return warnings
    
    def _save_pdf(self, pdf_path: str, user_id: str, resume_id: Optional[int] = None) -> str:
        """Save PDF to local storage and return URL"""
        try:
            # Create user directory
            user_dir = os.path.join(self.static_dir, user_id)
            os.makedirs(user_dir, exist_ok=True)
            
            # Generate filename
            if resume_id:
                filename = f"resume_{resume_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            else:
                filename = f"temp_{uuid.uuid4().hex[:8]}.pdf"
            
            local_path = os.path.join(user_dir, filename)
            
            # Copy PDF to destination
            shutil.copy2(pdf_path, local_path)
            
            # Return relative URL for serving
            return f"/static/resumes/{user_id}/{filename}"
            
        except Exception as e:
            logger.error(f"Error saving PDF: {e}")
            raise
    
    def cleanup_temp_files(self, user_id: str, older_than_hours: int = 24):
        """Clean up temporary PDF files older than specified hours"""
        try:
            user_dir = os.path.join(self.static_dir, user_id)
            if not os.path.exists(user_dir):
                return
                
            cutoff_time = datetime.now().timestamp() - (older_than_hours * 3600)
            
            for filename in os.listdir(user_dir):
                if filename.startswith('temp_'):
                    file_path = os.path.join(user_dir, filename)
                    if os.path.getctime(file_path) < cutoff_time:
                        os.remove(file_path)
                        logger.info(f"Cleaned up temp file: {filename}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")

# Global instance
latex_compiler = LaTeXCompiler() 