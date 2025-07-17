"""
LaTeX Generation Service for TailerAI v2.0.
Converts selected achievements from master dataset into professional PDF resumes.
Following project blueprint best practices for modular design and error handling.
"""

import logging
import os
import subprocess
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID, uuid4

from app.config.settings import get_settings
from app.models.database import UserProfile, WorkExperience, Achievement, Skill, EducationEntry
from app.services.database_service import db_service

logger = logging.getLogger(__name__)
settings = get_settings()


class LaTeXGenerationError(Exception):
    """Custom exception for LaTeX generation operations."""
    pass


class LaTeXGenerationService:
    """
    Service for generating professional PDF resumes using LaTeX.
    Converts selected content from master dataset into formatted PDF documents.
    """
    
    def __init__(self):
        self.logger = logger
        self.template_dir = Path(__file__).parent.parent.parent / "templates" / "latex"
        self.temp_dir = Path(tempfile.gettempdir()) / "tailer_latex"
        self.temp_dir.mkdir(exist_ok=True)
    
    # Content Preparation
    
    def _escape_latex_characters(self, text: str) -> str:
        """
        Escape special LaTeX characters in text content.
        Essential for preventing compilation errors from user input.
        """
        if not text:
            return ""
        
        # Remove Unicode control characters (U+0000 to U+001F)
        import re
        # Remove control characters that cause LaTeX compilation errors
        cleaned_text = re.sub(r'[\x00-\x1f]', '', text)
        
        # Handle newlines properly - replace with spaces for single-line output
        # This prevents LaTeX formatting issues in bullet points
        cleaned_text = re.sub(r'\s*\n\s*', ' ', cleaned_text)
        
        # Remove extra whitespace
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        # Normalize Unicode text
        import unicodedata
        normalized_text = unicodedata.normalize('NFKD', cleaned_text)
        
        # LaTeX special characters that need escaping (order matters!)
        latex_special_chars = [
            ('\\', r'\textbackslash{}'),  # Must be first to avoid double escaping
            ('&', r'\&'),
            ('%', r'\%'),
            ('$', r'\$'),
            ('#', r'\#'),
            ('^', r'\^{}'),
            ('_', r'\_'),
            ('{', r'\{'),
            ('}', r'\}'),
            ('~', r'\textasciitilde{}'),
            ('|', r'\textbar{}'),  # Add pipe character escaping
        ]
        
        # Replace each special character in order
        escaped_text = normalized_text
        for char, replacement in latex_special_chars:
            escaped_text = escaped_text.replace(char, replacement)
        
        # Additional safety: remove any remaining problematic characters
        # Remove any character that might cause math mode issues
        escaped_text = re.sub(r'[^\w\s\.\,\:\;\!\?\-\(\)\[\]\/\\\&\%\$\#\^\_\{\}\~\|]', '', escaped_text)
        
        return escaped_text
    
    def _format_achievement_bullets(self, achievements) -> str:
        """
        Format achievements as LaTeX bullet points.
        Ensures proper spacing and escaping.
        """
        if not achievements:
            return ""
        
        bullets = []
        for achievement in achievements:
            # Handle database objects, dictionaries, and plain strings
            if hasattr(achievement, 'achievement_text'):
                achievement_text = achievement.achievement_text
            elif isinstance(achievement, dict):
                achievement_text = achievement.get('achievement_text', '')
            else:
                # Plain string
                achievement_text = str(achievement)
            
            # Escape the achievement text
            escaped_text = self._escape_latex_characters(achievement_text)
            bullets.append(f"  \\item {escaped_text}")
        
        return "\n".join(bullets)
    
    def _format_work_experience_entry(self, experience, selected_achievements) -> str:
        """
        Format a work experience entry with selected achievements.
        Uses modular LaTeX commands for consistency.
        """
        # Handle both database objects and dictionaries
        if hasattr(experience, 'company_name'):
            # Database object
            company_name = self._escape_latex_characters(experience.company_name)
            position_title = self._escape_latex_characters(experience.position_title)
            location = self._escape_latex_characters(experience.location or "")
            start_date = experience.start_date.strftime("%m/%y") if experience.start_date else ""
            end_date = experience.end_date.strftime("%m/%y") if experience.end_date else "Present"
            company_description = experience.company_description
            job_description = experience.job_description or experience.role_summary
        else:
            # Dictionary
            company_name = self._escape_latex_characters(experience.get('company_name', ''))
            position_title = self._escape_latex_characters(experience.get('position_title', ''))
            location = self._escape_latex_characters(experience.get('location', '') or "")
            start_date_obj = experience.get('start_date')
            end_date_obj = experience.get('end_date')
            
            # Handle string dates (ISO format) and datetime objects
            if start_date_obj:
                if isinstance(start_date_obj, str):
                    try:
                        from datetime import datetime
                        parsed_date = datetime.fromisoformat(start_date_obj.replace('T', ' ').replace('Z', ''))
                        start_date = parsed_date.strftime("%m/%y")
                    except:
                        start_date = ""
                elif hasattr(start_date_obj, 'strftime'):
                    start_date = start_date_obj.strftime("%m/%y")
                else:
                    start_date = ""
            else:
                start_date = ""
                
            if end_date_obj:
                if isinstance(end_date_obj, str):
                    try:
                        from datetime import datetime
                        parsed_date = datetime.fromisoformat(end_date_obj.replace('T', ' ').replace('Z', ''))
                        end_date = parsed_date.strftime("%m/%y")
                    except:
                        end_date = "Present"
                elif hasattr(end_date_obj, 'strftime'):
                    end_date = end_date_obj.strftime("%m/%y")
                else:
                    end_date = "Present"
            else:
                end_date = "Present"
            company_description = experience.get('company_description')
            job_description = experience.get('job_description') or experience.get('role_summary')
        
        date_range = f"{start_date} -- {end_date}" if start_date else end_date
        
        # Format achievements
        achievement_bullets = self._format_achievement_bullets(selected_achievements)
        
        # Company description for context
        company_desc = ""
        if company_description:
            company_desc = f" ({self._escape_latex_characters(company_description[:50])})"
        
        entry = f"""
\\noindent\\textbf{{{company_name.upper()}{company_desc}}} \\hfill {location}\\\\
\\textit{{{position_title}}} \\hfill {date_range}"""
        
        # Add job description if available
        if job_description:
            job_desc_escaped = self._escape_latex_characters(job_description)
            entry += f"""\\\\
{job_desc_escaped}"""
        
        # Only add itemize block if there are achievements
        if achievement_bullets.strip():
            entry += f"""
\\begin{{itemize}}
{achievement_bullets}
\\end{{itemize}}
"""
        
        entry += "\n"
        return entry
    
    def _format_education_entry(self, education) -> str:
        """Format education entry for LaTeX template."""
        # Handle both database objects and dictionaries
        if hasattr(education, 'institution_name'):
            # Database object
            institution = self._escape_latex_characters(education.institution_name)
            degree = self._escape_latex_characters(education.degree_type)
            field = self._escape_latex_characters(education.field_of_study or "")
            location = self._escape_latex_characters(education.location or "")
            grad_date = education.graduation_date.strftime("%m/%y") if education.graduation_date else ""
            gpa = education.gpa
            gpa_scale = education.gpa_scale
            coursework = education.relevant_coursework
            achievements = education.academic_achievements
        else:
            # Dictionary
            institution = self._escape_latex_characters(education.get('institution_name', ''))
            degree = self._escape_latex_characters(education.get('degree_type', ''))
            field = self._escape_latex_characters(education.get('field_of_study', '') or "")
            location = self._escape_latex_characters(education.get('location', '') or "")
            grad_date_obj = education.get('graduation_date')
            if grad_date_obj:
                if isinstance(grad_date_obj, str):
                    try:
                        from datetime import datetime
                        parsed_date = datetime.fromisoformat(grad_date_obj.replace('T', ' ').replace('Z', ''))
                        grad_date = parsed_date.strftime("%m/%y")
                    except:
                        grad_date = ""
                elif hasattr(grad_date_obj, 'strftime'):
                    grad_date = grad_date_obj.strftime("%m/%y")
                else:
                    grad_date = ""
            else:
                grad_date = ""
            gpa = education.get('gpa')
            gpa_scale = education.get('gpa_scale')
            coursework = education.get('relevant_coursework')
            achievements = education.get('academic_achievements')
        
        # Format GPA if available
        gpa_text = ""
        if gpa:
            gpa_text = f", GPA: {gpa}"
            if gpa_scale:
                gpa_text += f"/{gpa_scale}"
        
        degree_line = f"{degree}"
        if field:
            degree_line += f", {field}"
        degree_line += f" -- {gpa_text}" if gpa_text else ""
        
        entry = f"""
\\noindent\\textbf{{{institution.upper()}}} \\hfill {location}\\\\
\\textit{{{degree_line}}} \\hfill {grad_date}
"""
        
        # Add coursework, awards, or other details if available
        details = []
        if coursework:
            coursework_escaped = self._escape_latex_characters(coursework)
            details.append(f"Selected Coursework: {coursework_escaped}")
        
        if achievements:
            achievements_escaped = self._escape_latex_characters(achievements)
            details.append(f"Awards: {achievements_escaped}")
        
        if details:
            entry += "\\begin{itemize}\n"
            for detail in details:
                entry += f"  \\item {detail}\n"
            entry += "\\end{itemize}\n"
        
        return entry
    
    def _format_skills_section(self, skills) -> str:
        """Format skills section grouped by category."""
        if not skills:
            return ""
        
        # Group skills by category
        skill_groups = {}
        for skill in skills:
            # Handle both database objects and dictionaries
            if hasattr(skill, 'skill_category'):
                category = skill.skill_category or "Other"
                skill_name = skill.skill_name
            else:
                category = skill.get('skill_category') or "Other"
                skill_name = skill.get('skill_name', '')
            
            if category not in skill_groups:
                skill_groups[category] = []
            skill_groups[category].append(skill_name)
        
        # Format each group
        formatted_groups = []
        for category, skill_names in skill_groups.items():
            escaped_skills = [self._escape_latex_characters(name) for name in skill_names]
            skills_text = ", ".join(escaped_skills)
            formatted_groups.append(f"{category.title()}: {skills_text}")
        
        return "; ".join(formatted_groups)
    
    # Template Generation
    
    def _create_dynamic_template(self, user_profile: UserProfile, selected_content: Dict[str, Any]) -> str:
        """
        Create dynamic LaTeX template with injected content.
        Converts static template to dynamic by replacing placeholders.
        """
        try:
            # Read the base template
            template_path = self.template_dir / "mspm_template.tex"
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Prepare user information
            full_name = self._escape_latex_characters(user_profile.full_name or "Your Name")
            email = self._escape_latex_characters(user_profile.email)
            phone = self._escape_latex_characters(user_profile.phone or "")
            linkedin_url = self._escape_latex_characters(user_profile.linkedin_url or "")
            location = self._escape_latex_characters(user_profile.location or "")
            
            # Build header
            header_parts = []
            if phone:
                header_parts.append(phone)
            if email:
                header_parts.append(email)
            if linkedin_url:
                # Extract just the username part from LinkedIn URL
                linkedin_display = linkedin_url.replace("https://", "").replace("http://", "")
                header_parts.append(linkedin_display)
            if location:
                header_parts.append(location)
            
            header_line = " $|$ ".join(header_parts)
            
            # Build education section
            education_content = ""
            if selected_content.get('education'):
                for edu in selected_content['education']:
                    education_content += self._format_education_entry(edu)
            
            # Add fallback if no education content
            if not education_content.strip():
                education_content = "\\noindent\\textbf{EDUCATION INFORMATION PENDING}\\\\\\textit{Please add education details}"
            
            # Build work experience section
            work_experience_content = ""
            if selected_content.get('work_experiences'):
                for exp_data in selected_content['work_experiences']:
                    # Handle both formats: direct experience data and nested format
                    if 'experience' in exp_data:
                        # Nested format from content selection service (optimized endpoint)
                        experience = exp_data['experience']
                        achievements = exp_data.get('achievements', [])
                    else:
                        # Direct format from generate endpoint
                        experience = exp_data
                        achievements = exp_data.get('achievements', [])
                    
                    work_experience_content += self._format_work_experience_entry(experience, achievements)
            
            # Add fallback if no work experience content
            if not work_experience_content.strip():
                work_experience_content = "\\noindent\\textbf{WORK EXPERIENCE INFORMATION PENDING}\\\\\\textit{Please add work experience details}"
            
            # Build skills section
            skills_content = ""
            if selected_content.get('skills'):
                skills_content = self._format_skills_section(selected_content['skills'])
            
            # Build additional sections
            additional_content = ""
            if selected_content.get('certifications'):
                cert_list = [self._escape_latex_characters(cert) for cert in selected_content['certifications']]
                additional_content += f"\\item Certifications: {', '.join(cert_list)}\n"
            
            if selected_content.get('projects'):
                self.logger.info(f"Processing {len(selected_content['projects'])} projects")
                for project in selected_content['projects']:
                    project_name = self._escape_latex_characters(project.get('name', ''))
                    project_desc = self._escape_latex_characters(project.get('description', ''))
                    self.logger.info(f"Project: {project_name} | Desc: {project_desc[:50]}...")
                    
                    # Handle empty description
                    if not project_desc.strip():
                        project_desc = "Project description pending"
                    
                    # Only add project if name exists
                    if project_name.strip():
                        additional_content += f"\\item {project_name} -- {project_desc}\n"
            
            # Replace static content with dynamic content
            # This is a simplified replacement - in production, we'd use a proper template engine
            
            # Replace header
            template_content = template_content.replace(
                "ADITYA TEJA BHIMAVARAPU",
                full_name.upper()
            )
            template_content = template_content.replace(
                "412.287.1018 $|$ abhimava@andrew.cmu.edu $|$ linkedin.com/in/aditya-teja $|$ Pittsburgh, PA",
                header_line
            )
            
            # For this MVP, we'll inject the content sections manually
            # In a full implementation, we'd create proper template placeholders
            
            # Build skills section if available
            skills_section = ""
            if skills_content:
                skills_section = f"""
\\section*{{TECHNICAL SKILLS}}
\\sectionline
{skills_content}
"""
            
            # Build additional information section if available
            additional_section = ""
            if additional_content:
                additional_section = f"""
\\section*{{ADDITIONAL INFORMATION}}
\\sectionline
\\begin{{itemize}}
{additional_content}
\\end{{itemize}}
"""
            
            # Create the complete dynamic template
            dynamic_template = f"""% Ultra-compact, high-density resume with section lines
\\documentclass[10pt,letterpaper]{{article}}
\\usepackage[left=0.5in, right=0.5in, top=0.5in, bottom=0.3in]{{geometry}}
\\usepackage{{helvet}}
\\renewcommand{{\\familydefault}}{{\\sfdefault}}
\\usepackage{{tabularx}}
\\usepackage{{enumitem}}
\\usepackage{{titlesec}}
\\usepackage{{tikz}}

% Remove page numbers
\\pagestyle{{empty}}

% Section formatting (tighter)
\\titleformat{{\\section}}{{\\bfseries\\uppercase}}{{\\thesection}}{{1em}}{{}}
\\titlespacing*{{\\section}}{{0pt}}{{0.5ex}}{{0.2ex}}

% Custom entry command
\\newcommand{{\\resumeEntry}}[4]{{%
  \\begin{{tabularx}}{{\\textwidth}}{{@{{}}Xr@{{}}}}
    \\textbf{{#1}} #2 & #3 \\\\
    \\textit{{#4}} & \\\\
  \\end{{tabularx}}
}}

% Bullet formatting (flush left)
\\setlist[itemize]{{left=0em, itemsep=0.1em, topsep=0.1em, parsep=0em, partopsep=0em}}

% Reduce line spacing globally
\\linespread{{0.97}}
\\setlength{{\\parskip}}{{0em}}

% Horizontal rule command (force paragraph break)
\\newcommand{{\\sectionline}}{{\\par\\vspace{{-0.5em}}\\noindent\\rule{{\\textwidth}}{{0.6pt}}\\vspace{{0.3em}}\\par}}

\\begin{{document}}

% Header
\\begin{{center}}
  {{\\LARGE \\textbf{{{full_name.upper()}}}}}\\\\
  {header_line}
\\end{{center}}
\\sectionline

% Education
\\section*{{EDUCATION}}
\\sectionline
{education_content}

% Work Experience  
\\section*{{WORK EXPERIENCE}}
\\sectionline
{work_experience_content}
{skills_section}
{additional_section}
\\end{{document}}
"""
            
            return dynamic_template
            
        except Exception as e:
            self.logger.error(f"Error creating dynamic template: {str(e)}")
            raise LaTeXGenerationError(f"Template generation failed: {str(e)}")
    
    # PDF Compilation
    
    def _compile_latex_to_pdf(self, latex_content: str, output_filename: str) -> Tuple[bool, str, str]:
        """
        Compile LaTeX content to PDF using Tectonic.
        Returns (success, pdf_path, error_message).
        """
        try:
            # Create unique working directory
            work_dir = self.temp_dir / str(uuid4())
            work_dir.mkdir(exist_ok=True)
            
            # Write LaTeX content to file
            tex_file = work_dir / f"{output_filename}.tex"
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
            # Compile LaTeX to PDF using configured LaTeX engine
            latex_engine = settings.latex_engine_path or settings.latex_engine
            
            if settings.latex_engine == 'pdflatex':
                # Use pdflatex with standard LaTeX compilation
                cmd = [latex_engine, '-interaction=nonstopmode', f'{output_filename}.tex']
            else:
                # Use tectonic or other engines
                cmd = [latex_engine, f'{output_filename}.tex']
            
            self.logger.info(f"========== LATEX COMPILATION WITH {settings.latex_engine.upper()} ==========")
            self.logger.info(f"Command: {' '.join(cmd)}")
            self.logger.info(f"Working directory: {work_dir}")
            self.logger.info(f"LaTeX file: {tex_file}")
            
            result = subprocess.run(
                cmd,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout for Tectonic
            )
            
            if result.returncode != 0:
                self.logger.error(f"========== LATEX COMPILATION FAILED ==========")
                self.logger.error(f"Return code: {result.returncode}")
                self.logger.error(f"FULL STDERR: {result.stderr}")
                self.logger.error(f"FULL STDOUT: {result.stdout}")
                
                # Log the .tex file content for debugging
                try:
                    with open(tex_file, 'r') as f:
                        tex_content = f.read()
                    self.logger.error(f"LaTeX file content: {tex_content}")
                except Exception as e:
                    self.logger.error(f"Could not read .tex file: {e}")
                
                # Return the FULL error instead of parsed version for debugging
                full_error_msg = f"Tectonic compilation failed. STDERR: {result.stderr}. STDOUT: {result.stdout}"
                
                # Clean up
                shutil.rmtree(work_dir, ignore_errors=True)
                return False, "", full_error_msg
            
            # Check if PDF was created
            pdf_file = work_dir / f"{output_filename}.pdf"
            if not pdf_file.exists():
                error_msg = "PDF file was not created after compilation"
                self.logger.error(error_msg)
                shutil.rmtree(work_dir, ignore_errors=True)
                return False, "", error_msg
            
            # Move PDF to final location
            final_pdf_path = self.temp_dir / f"{output_filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            shutil.copy2(pdf_file, final_pdf_path)
            
            # Clean up working directory
            shutil.rmtree(work_dir, ignore_errors=True)
            
            self.logger.info(f"Successfully compiled PDF: {final_pdf_path}")
            return True, str(final_pdf_path), ""
            
        except subprocess.TimeoutExpired:
            error_msg = "LaTeX compilation timed out"
            self.logger.error(error_msg)
            return False, "", error_msg
        except Exception as e:
            error_msg = f"Unexpected error during PDF compilation: {str(e)}"
            self.logger.error(error_msg)
            return False, "", error_msg
    
    # Main Generation Methods
    
    async def generate_resume_pdf(
        self, 
        user_id: str, 
        selected_content: Dict[str, Any],
        filename_prefix: str = "resume"
    ) -> Tuple[bool, Optional[str], str]:
        """
        Generate a PDF resume from selected content.
        
        Args:
            user_id: User ID for profile lookup
            selected_content: Dictionary containing selected achievements, experiences, etc.
            filename_prefix: Prefix for output filename
            
        Returns:
            Tuple of (success, pdf_path, message)
        """
        try:
            # Get user profile
            with db_service.get_session() as session:
                from app.models.database import User, UserProfile
                
                user = session.query(User).filter_by(id=UUID(user_id)).first()
                if not user:
                    # Create a mock user profile for testing
                    class MockUserProfile:
                        def __init__(self):
                            self.full_name = "Test User"
                            self.email = "test@example.com"
                            self.phone = "123-456-7890"
                            self.linkedin_url = "https://linkedin.com/in/testuser"
                            self.location = "Test City, State"
                    
                    user_profile = MockUserProfile()
                else:
                    user_profile = session.query(UserProfile).filter_by(user_id=user.id).first()
                    if not user_profile:
                        return False, None, "User profile not found"
                
                # Create dynamic LaTeX template
                self.logger.info(f"Generating resume for user: {user_id}")
                self.logger.info(f"Selected content: {selected_content}")
                latex_content = self._create_dynamic_template(user_profile, selected_content)
                self.logger.info(f"Generated LaTeX content length: {len(latex_content)} characters")
                
                # Debug: log the generated LaTeX content
                self.logger.info("Generated LaTeX content (first 500 chars):")
                self.logger.info(latex_content[:500])
                
                # Generate unique filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"{filename_prefix}_{user_id}_{timestamp}"
                
                # Compile to PDF
                success, pdf_path, error_message = self._compile_latex_to_pdf(latex_content, output_filename)
                
                if success:
                    return True, pdf_path, "Resume generated successfully"
                else:
                    return False, None, f"PDF generation failed: {error_message}"
        
        except Exception as e:
            error_msg = f"Resume generation failed: {str(e)}"
            self.logger.error(error_msg)
            return False, None, error_msg
    
    async def validate_latex_installation(self) -> Tuple[bool, str]:
        """
        Validate that configured LaTeX engine is properly installed and available.
        Returns (is_available, version_info).
        """
        latex_engine = settings.latex_engine_path or settings.latex_engine
        engine_name = settings.latex_engine
        
        try:
            if engine_name == 'pdflatex':
                # Check pdflatex version
                result = subprocess.run(
                    [latex_engine, '--version'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            else:
                # Check tectonic or other engines
                result = subprocess.run(
                    [latex_engine, '--version'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            
            if result.returncode == 0:
                version_info = result.stdout.split('\n')[0]
                self.logger.info(f"{engine_name} available: {version_info}")
                return True, version_info
            else:
                return False, f"{engine_name} command failed"
                
        except subprocess.TimeoutExpired:
            return False, f"{engine_name} command timed out"
        except FileNotFoundError:
            return False, f"{engine_name} not found - LaTeX engine not installed"
        except Exception as e:
            return False, f"Error checking {engine_name}: {str(e)}"
    
    def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up temporary PDF files older than max_age_hours.
        Returns number of files cleaned up.
        """
        try:
            cleaned_count = 0
            current_time = datetime.now()
            
            for file_path in self.temp_dir.glob("*.pdf"):
                file_age = current_time - datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_age.total_seconds() > (max_age_hours * 3600):
                    file_path.unlink()
                    cleaned_count += 1
            
            self.logger.info(f"Cleaned up {cleaned_count} temporary PDF files")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up temp files: {str(e)}")
            return 0


# Global service instance
latex_generation_service = LaTeXGenerationService()