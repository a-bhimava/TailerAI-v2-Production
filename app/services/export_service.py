#!/usr/bin/env python3
"""
Export Service for TailerAI v2.0 - PRD-011: Export & Personal Application Management

Multi-format export system supporting PDF, DOCX, HTML, and JSON formats.
Provides optimized document generation with customizable templates and formatting.
"""

import os
import json
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path

from app.services.database_service import DatabaseService
from app.services.content_selection_service import ContentSelectionEngine
from app.services.ats_optimization_service import ATSOptimizationEngine
from app.services.quality_control_service import PersonalQualityControlService
from app.models.database import (
    UserProfile, ExportHistory, ExportTemplate, 
    ContentSelection, ATSOptimization, QualityAssessment
)

logger = logging.getLogger(__name__)


class ExportConfiguration:
    """Configuration settings for document export."""
    
    def __init__(self):
        self.format = "pdf"  # pdf, docx, html, json
        self.template_id = None
        self.include_contact_info = True
        self.include_summary = True
        self.max_pages = 1
        self.font_family = "Arial"
        self.font_size = 11
        self.margins = {"top": 0.5, "bottom": 0.5, "left": 0.5, "right": 0.5}
        self.color_scheme = "professional"  # professional, modern, creative
        self.optimization_level = "high"  # low, medium, high
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "format": self.format,
            "template_id": self.template_id,
            "include_contact_info": self.include_contact_info,
            "include_summary": self.include_summary,
            "max_pages": self.max_pages,
            "font_family": self.font_family,
            "font_size": self.font_size,
            "margins": self.margins,
            "color_scheme": self.color_scheme,
            "optimization_level": self.optimization_level
        }


class ExportResult:
    """Result of document export operation."""
    
    def __init__(self):
        self.success = False
        self.file_path = None
        self.file_size_bytes = 0
        self.generation_time_ms = 0
        self.format = None
        self.quality_metrics = {}
        self.error_message = None
        self.warnings = []
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "success": self.success,
            "file_path": self.file_path,
            "file_size_bytes": self.file_size_bytes,
            "generation_time_ms": self.generation_time_ms,
            "format": self.format,
            "quality_metrics": self.quality_metrics,
            "error_message": self.error_message,
            "warnings": self.warnings
        }


class ExportService:
    """
    Multi-format export service for TailerAI documents.
    Supports PDF, DOCX, HTML, and JSON export formats with optimization.
    """
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.content_selection_service = ContentSelectionEngine()
        self.ats_optimization_service = ATSOptimizationEngine()
        self.quality_control_service = PersonalQualityControlService()
        
        # Export directories
        self.export_base_dir = Path("exports")
        self.template_dir = Path("templates/export")
        
        # Ensure directories exist
        self.export_base_dir.mkdir(exist_ok=True)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # Supported formats and their handlers
        self.format_handlers = {
            "pdf": self._export_pdf,
            "docx": self._export_docx,
            "html": self._export_html,
            "json": self._export_json
        }
        
    async def export_document(
        self,
        profile_id: str,
        export_type: str = "resume",
        target_role: str = None,
        target_company: str = None,
        config: ExportConfiguration = None
    ) -> ExportResult:
        """
        Export document in specified format with optimization.
        
        Args:
            profile_id: User profile ID
            export_type: Type of document ("resume", "cover_letter", "portfolio")
            target_role: Target job role for optimization
            target_company: Target company for customization
            config: Export configuration settings
            
        Returns:
            ExportResult with export details and file information
        """
        start_time = datetime.now()
        result = ExportResult()
        
        try:
            if config is None:
                config = ExportConfiguration()
                
            result.format = config.format
            
            # Validate format support
            if config.format not in self.format_handlers:
                raise ValueError(f"Unsupported export format: {config.format}")
            
            # Get user profile
            profile = await self._get_user_profile(profile_id)
            if not profile:
                raise ValueError(f"Profile not found: {profile_id}")
            
            # Select and optimize content
            content_data = await self._prepare_content(
                profile, export_type, target_role, target_company, config
            )
            
            # Generate document using format handler
            handler = self.format_handlers[config.format]
            file_path = await handler(profile, content_data, config)
            
            # Calculate file size
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            
            # Calculate generation time
            generation_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Run quality assessment
            quality_metrics = await self._assess_export_quality(
                profile, content_data, file_path, config
            )
            
            # Record export in history
            await self._record_export_history(
                profile_id, export_type, target_role, target_company, 
                config, file_path, file_size, generation_time, quality_metrics
            )
            
            # Set success result
            result.success = True
            result.file_path = str(file_path)
            result.file_size_bytes = file_size
            result.generation_time_ms = generation_time
            result.quality_metrics = quality_metrics
            
            logger.info(f"Successfully exported {export_type} for profile {profile_id} in {config.format} format")
            
        except Exception as e:
            result.success = False
            result.error_message = str(e)
            result.generation_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error(f"Export failed for profile {profile_id}: {str(e)}")
            
        return result
    
    async def _get_user_profile(self, profile_id: str) -> Optional[UserProfile]:
        """Get user profile with all related data."""
        try:
            with self.db_service.get_session() as session:
                profile = session.query(UserProfile).filter(
                    UserProfile.id == profile_id
                ).first()
                
                if profile:
                    # Ensure all relationships are loaded
                    _ = profile.work_experiences
                    _ = profile.achievements
                    _ = profile.education_entries
                    _ = profile.skills
                    _ = profile.projects
                    
                return profile
        except Exception as e:
            logger.error(f"Error fetching profile {profile_id}: {str(e)}")
            return None
    
    async def _prepare_content(
        self,
        profile: UserProfile,
        export_type: str,
        target_role: str,
        target_company: str,
        config: ExportConfiguration
    ) -> Dict[str, Any]:
        """Prepare and optimize content for export."""
        content_data = {
            "profile": profile,
            "export_type": export_type,
            "target_role": target_role,
            "target_company": target_company,
            "selected_achievements": [],
            "optimized_content": {},
            "quality_assessment": {}
        }
        
        try:
            # Run content selection if targeting specific role
            if target_role and export_type == "resume":
                job_description = f"Position: {target_role}"
                if target_company:
                    job_description += f" at {target_company}"
                
                selection_result = await self.content_selection_service.select_optimal_content(
                    user_profile_id=str(profile.id),
                    job_description=job_description,
                    target_word_count=350 if config.max_pages == 1 else 500
                )
                
                if selection_result.get("success"):
                    content_data["selected_achievements"] = selection_result.get("selected_achievements", [])
                    content_data["selection_metadata"] = selection_result.get("metadata", {})
            
            # Run ATS optimization if high optimization level
            if config.optimization_level == "high" and target_role:
                ats_result = await self.ats_optimization_service.optimize_keywords(
                    profile_id=str(profile.id),
                    target_keywords=[target_role.lower(), "professional", "experienced"],
                    content_selection_data=content_data.get("selected_achievements", [])
                )
                
                if ats_result.get("success"):
                    content_data["optimized_content"] = ats_result.get("optimization_results", {})
            
            # Run quality assessment
            quality_result = await self.quality_control_service.assess_personal_quality(
                profile_id=str(profile.id),
                target_role=target_role,
                assessment_type="export_preparation"
            )
            
            if quality_result.get("success"):
                content_data["quality_assessment"] = quality_result.get("assessment", {})
                
        except Exception as e:
            logger.warning(f"Content preparation partially failed: {str(e)}")
            # Continue with basic content
            
        return content_data
    
    async def _export_pdf(
        self,
        profile: UserProfile,
        content_data: Dict[str, Any],
        config: ExportConfiguration
    ) -> Path:
        """Export document as PDF using existing LaTeX pipeline."""
        try:
            # Import LaTeX service
            from app.services.latex_generation_service import LaTeXGenerationService
            
            latex_service = LaTeXGenerationService(self.db_service)
            
            # Generate PDF using existing LaTeX pipeline
            result = await latex_service.generate_resume(
                profile_id=str(profile.id),
                selected_achievements=content_data.get("selected_achievements", []),
                template_name="mspm_template",
                output_format="pdf"
            )
            
            if result.get("success") and result.get("output_path"):
                # Move to export directory with better naming
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{profile.full_name.replace(' ', '_')}_{content_data['export_type']}_{timestamp}.pdf"
                export_path = self.export_base_dir / filename
                
                # Copy file to export directory
                import shutil
                shutil.copy2(result["output_path"], export_path)
                
                return export_path
            else:
                raise Exception(f"LaTeX generation failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"PDF export failed: {str(e)}")
            raise
    
    async def _export_docx(
        self,
        profile: UserProfile,
        content_data: Dict[str, Any],
        config: ExportConfiguration
    ) -> Path:
        """Export document as DOCX using python-docx."""
        try:
            from docx import Document
            from docx.shared import Inches, Pt
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            from docx.enum.style import WD_STYLE_TYPE
            
            # Create new document
            doc = Document()
            
            # Set margins
            sections = doc.sections
            for section in sections:
                section.top_margin = Inches(config.margins["top"])
                section.bottom_margin = Inches(config.margins["bottom"])
                section.left_margin = Inches(config.margins["left"])
                section.right_margin = Inches(config.margins["right"])
            
            # Add header with contact information
            if config.include_contact_info:
                header = doc.add_heading(profile.full_name, 0)
                header.alignment = WD_ALIGN_PARAGRAPH.CENTER
                
                contact_info = []
                if profile.email:
                    contact_info.append(profile.email)
                if profile.phone:
                    contact_info.append(profile.phone)
                if profile.location:
                    contact_info.append(profile.location)
                
                if contact_info:
                    contact_para = doc.add_paragraph(" | ".join(contact_info))
                    contact_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                
                doc.add_paragraph()  # Spacing
            
            # Add professional summary if included
            if config.include_summary and hasattr(profile, 'professional_summary'):
                doc.add_heading('Professional Summary', level=1)
                doc.add_paragraph(getattr(profile, 'professional_summary', ''))
                doc.add_paragraph()
            
            # Add work experience
            if profile.work_experiences:
                doc.add_heading('Professional Experience', level=1)
                
                for exp in sorted(profile.work_experiences, key=lambda x: x.start_date, reverse=True):
                    # Company and position
                    exp_header = f"{exp.position_title} at {exp.company_name}"
                    doc.add_heading(exp_header, level=2)
                    
                    # Dates and location
                    date_str = exp.start_date.strftime("%Y-%m") if exp.start_date else ""
                    if exp.end_date:
                        date_str += f" - {exp.end_date.strftime('%Y-%m')}"
                    else:
                        date_str += " - Present"
                    
                    if exp.location:
                        date_str += f" | {exp.location}"
                    
                    date_para = doc.add_paragraph(date_str)
                    date_para.style = 'Intense Quote'
                    
                    # Role summary
                    if exp.role_summary:
                        doc.add_paragraph(exp.role_summary)
                    
                    # Selected achievements for this experience
                    selected_achievements = content_data.get("selected_achievements", [])
                    exp_achievements = [ach for ach in profile.achievements 
                                     if ach.experience_id == exp.id and str(ach.id) in selected_achievements]
                    
                    if exp_achievements:
                        for achievement in exp_achievements:
                            bullet_para = doc.add_paragraph(f"• {achievement.achievement_text}")
                            bullet_para.style = 'List Bullet'
                    
                    doc.add_paragraph()  # Spacing between experiences
            
            # Add education
            if profile.education_entries:
                doc.add_heading('Education', level=1)
                
                for edu in sorted(profile.education_entries, key=lambda x: x.end_date or datetime.now(), reverse=True):
                    edu_text = f"{edu.degree_type} in {edu.field_of_study}" if edu.degree_type and edu.field_of_study else "Education"
                    edu_text += f" - {edu.institution_name}"
                    
                    if edu.end_date:
                        edu_text += f" ({edu.end_date.strftime('%Y')})"
                    
                    doc.add_paragraph(edu_text, style='List Bullet')
            
            # Add skills
            if profile.skills:
                doc.add_heading('Skills', level=1)
                
                # Group skills by category
                skill_categories = {}
                for skill in profile.skills:
                    category = skill.skill_category or "General"
                    if category not in skill_categories:
                        skill_categories[category] = []
                    skill_categories[category].append(skill.skill_name)
                
                for category, skills in skill_categories.items():
                    skills_text = f"{category}: {', '.join(skills)}"
                    doc.add_paragraph(skills_text, style='List Bullet')
            
            # Save document
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{profile.full_name.replace(' ', '_')}_{content_data['export_type']}_{timestamp}.docx"
            export_path = self.export_base_dir / filename
            
            doc.save(str(export_path))
            
            return export_path
            
        except ImportError:
            raise Exception("python-docx library not installed. Install with: pip install python-docx")
        except Exception as e:
            logger.error(f"DOCX export failed: {str(e)}")
            raise
    
    async def _export_html(
        self,
        profile: UserProfile,
        content_data: Dict[str, Any],
        config: ExportConfiguration
    ) -> Path:
        """Export document as HTML with CSS styling."""
        try:
            # Generate HTML content
            html_content = self._generate_html_content(profile, content_data, config)
            
            # Save HTML file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{profile.full_name.replace(' ', '_')}_{content_data['export_type']}_{timestamp}.html"
            export_path = self.export_base_dir / filename
            
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return export_path
            
        except Exception as e:
            logger.error(f"HTML export failed: {str(e)}")
            raise
    
    def _generate_html_content(
        self,
        profile: UserProfile,
        content_data: Dict[str, Any],
        config: ExportConfiguration
    ) -> str:
        """Generate HTML content with embedded CSS."""
        
        # CSS styles based on color scheme
        css_styles = self._get_html_styles(config)
        
        # Build HTML content
        html_parts = [
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head>",
            "<meta charset='UTF-8'>",
            "<meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            f"<title>{profile.full_name} - {content_data['export_type'].title()}</title>",
            "<style>",
            css_styles,
            "</style>",
            "</head>",
            "<body>",
            "<div class='container'>"
        ]
        
        # Header section
        if config.include_contact_info:
            html_parts.extend([
                "<header class='header'>",
                f"<h1 class='name'>{profile.full_name}</h1>",
                "<div class='contact-info'>"
            ])
            
            contact_items = []
            if profile.email:
                contact_items.append(f"<span class='contact-item'>{profile.email}</span>")
            if profile.phone:
                contact_items.append(f"<span class='contact-item'>{profile.phone}</span>")
            if profile.location:
                contact_items.append(f"<span class='contact-item'>{profile.location}</span>")
            
            html_parts.append(" | ".join(contact_items))
            html_parts.extend([
                "</div>",
                "</header>"
            ])
        
        # Professional summary
        if config.include_summary and hasattr(profile, 'professional_summary'):
            summary = getattr(profile, 'professional_summary', '')
            if summary:
                html_parts.extend([
                    "<section class='section'>",
                    "<h2 class='section-title'>Professional Summary</h2>",
                    f"<p class='summary'>{summary}</p>",
                    "</section>"
                ])
        
        # Work experience
        if profile.work_experiences:
            html_parts.extend([
                "<section class='section'>",
                "<h2 class='section-title'>Professional Experience</h2>"
            ])
            
            selected_achievements = content_data.get("selected_achievements", [])
            
            for exp in sorted(profile.work_experiences, key=lambda x: x.start_date, reverse=True):
                date_str = exp.start_date.strftime("%b %Y") if exp.start_date else ""
                if exp.end_date:
                    date_str += f" - {exp.end_date.strftime('%b %Y')}"
                else:
                    date_str += " - Present"
                
                html_parts.extend([
                    "<div class='experience'>",
                    f"<h3 class='position'>{exp.position_title}</h3>",
                    f"<div class='company'>{exp.company_name}</div>",
                    f"<div class='dates'>{date_str}" + (f" | {exp.location}" if exp.location else "") + "</div>"
                ])
                
                if exp.role_summary:
                    html_parts.append(f"<p class='role-summary'>{exp.role_summary}</p>")
                
                # Achievements
                exp_achievements = [ach for ach in profile.achievements 
                                 if ach.experience_id == exp.id and str(ach.id) in selected_achievements]
                
                if exp_achievements:
                    html_parts.append("<ul class='achievements'>")
                    for achievement in exp_achievements:
                        html_parts.append(f"<li class='achievement'>{achievement.achievement_text}</li>")
                    html_parts.append("</ul>")
                
                html_parts.append("</div>")
            
            html_parts.append("</section>")
        
        # Education
        if profile.education_entries:
            html_parts.extend([
                "<section class='section'>",
                "<h2 class='section-title'>Education</h2>",
                "<ul class='education-list'>"
            ])
            
            for edu in sorted(profile.education_entries, key=lambda x: x.end_date or datetime.now(), reverse=True):
                edu_text = f"{edu.degree_type} in {edu.field_of_study}" if edu.degree_type and edu.field_of_study else "Education"
                edu_text += f" - {edu.institution_name}"
                
                if edu.end_date:
                    edu_text += f" ({edu.end_date.strftime('%Y')})"
                
                html_parts.append(f"<li class='education-item'>{edu_text}</li>")
            
            html_parts.extend([
                "</ul>",
                "</section>"
            ])
        
        # Skills
        if profile.skills:
            html_parts.extend([
                "<section class='section'>",
                "<h2 class='section-title'>Skills</h2>"
            ])
            
            # Group skills by category
            skill_categories = {}
            for skill in profile.skills:
                category = skill.skill_category or "General"
                if category not in skill_categories:
                    skill_categories[category] = []
                skill_categories[category].append(skill.skill_name)
            
            for category, skills in skill_categories.items():
                html_parts.extend([
                    f"<div class='skill-category'>",
                    f"<strong>{category}:</strong> {', '.join(skills)}",
                    "</div>"
                ])
            
            html_parts.append("</section>")
        
        # Close HTML
        html_parts.extend([
            "</div>",
            "</body>",
            "</html>"
        ])
        
        return "\n".join(html_parts)
    
    def _get_html_styles(self, config: ExportConfiguration) -> str:
        """Get CSS styles based on configuration."""
        
        color_schemes = {
            "professional": {
                "primary": "#2c3e50",
                "secondary": "#34495e",
                "accent": "#3498db",
                "text": "#2c3e50",
                "light": "#ecf0f1"
            },
            "modern": {
                "primary": "#1a1a1a",
                "secondary": "#333333",
                "accent": "#ff6b6b",
                "text": "#1a1a1a",
                "light": "#f8f9fa"
            },
            "creative": {
                "primary": "#6c5ce7",
                "secondary": "#a29bfe",
                "accent": "#fd79a8",
                "text": "#2d3436",
                "light": "#f1f2f6"
            }
        }
        
        colors = color_schemes.get(config.color_scheme, color_schemes["professional"])
        
        return f"""
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: '{config.font_family}', Arial, sans-serif;
            font-size: {config.font_size}pt;
            line-height: 1.6;
            color: {colors['text']};
            background-color: white;
        }}
        
        .container {{
            max-width: 8.5in;
            margin: 0 auto;
            padding: {config.margins['top']}in {config.margins['right']}in {config.margins['bottom']}in {config.margins['left']}in;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 1.5em;
            padding-bottom: 1em;
            border-bottom: 2px solid {colors['accent']};
        }}
        
        .name {{
            font-size: 1.8em;
            font-weight: bold;
            color: {colors['primary']};
            margin-bottom: 0.5em;
        }}
        
        .contact-info {{
            font-size: 0.95em;
            color: {colors['secondary']};
        }}
        
        .contact-item {{
            margin: 0 0.5em;
        }}
        
        .section {{
            margin-bottom: 1.5em;
        }}
        
        .section-title {{
            font-size: 1.2em;
            font-weight: bold;
            color: {colors['primary']};
            margin-bottom: 0.75em;
            padding-bottom: 0.25em;
            border-bottom: 1px solid {colors['light']};
        }}
        
        .experience {{
            margin-bottom: 1.25em;
        }}
        
        .position {{
            font-size: 1.05em;
            font-weight: bold;
            color: {colors['primary']};
            margin-bottom: 0.25em;
        }}
        
        .company {{
            font-weight: 600;
            color: {colors['secondary']};
            margin-bottom: 0.25em;
        }}
        
        .dates {{
            font-size: 0.9em;
            color: {colors['secondary']};
            font-style: italic;
            margin-bottom: 0.5em;
        }}
        
        .role-summary {{
            margin-bottom: 0.5em;
            font-style: italic;
        }}
        
        .achievements {{
            margin-left: 1.5em;
            margin-bottom: 0.5em;
        }}
        
        .achievement {{
            margin-bottom: 0.25em;
        }}
        
        .education-list {{
            margin-left: 1.5em;
        }}
        
        .education-item {{
            margin-bottom: 0.5em;
        }}
        
        .skill-category {{
            margin-bottom: 0.5em;
        }}
        
        .summary {{
            font-size: 1em;
            line-height: 1.5;
        }}
        
        @media print {{
            body {{
                print-color-adjust: exact;
            }}
            
            .container {{
                max-width: none;
                margin: 0;
                padding: 0.5in;
            }}
        }}
        """
    
    async def _export_json(
        self,
        profile: UserProfile,
        content_data: Dict[str, Any],
        config: ExportConfiguration
    ) -> Path:
        """Export document as JSON for data portability."""
        try:
            # Build comprehensive JSON structure
            json_data = {
                "export_metadata": {
                    "export_type": content_data["export_type"],
                    "export_date": datetime.now().isoformat(),
                    "target_role": content_data.get("target_role"),
                    "target_company": content_data.get("target_company"),
                    "configuration": config.to_dict()
                },
                "profile": {
                    "basic_info": {
                        "full_name": profile.full_name,
                        "email": profile.email,
                        "phone": profile.phone,
                        "location": profile.location,
                        "linkedin_url": profile.linkedin_url
                    },
                    "preferences": {
                        "target_industries": profile.target_industries,
                        "career_level": profile.career_level,
                        "job_search_status": profile.job_search_status
                    }
                },
                "work_experiences": [],
                "achievements": [],
                "education": [],
                "skills": [],
                "projects": []
            }
            
            # Add work experiences
            for exp in profile.work_experiences:
                exp_data = {
                    "id": str(exp.id),
                    "company_name": exp.company_name,
                    "position_title": exp.position_title,
                    "employment_type": exp.employment_type,
                    "start_date": exp.start_date.isoformat() if exp.start_date else None,
                    "end_date": exp.end_date.isoformat() if exp.end_date else None,
                    "location": exp.location,
                    "company_size": exp.company_size,
                    "industry": exp.industry,
                    "role_summary": exp.role_summary,
                    "duration_months": exp.duration_months,
                    "is_current": exp.is_current
                }
                json_data["work_experiences"].append(exp_data)
            
            # Add achievements (filtered by selection if available)
            selected_achievements = content_data.get("selected_achievements", [])
            for ach in profile.achievements:
                if not selected_achievements or str(ach.id) in selected_achievements:
                    ach_data = {
                        "id": str(ach.id),
                        "experience_id": str(ach.experience_id),
                        "achievement_text": ach.achievement_text,
                        "achievement_category": ach.achievement_category,
                        "impact_level": ach.impact_level,
                        "business_function": ach.business_function,
                        "quantified_metrics": ach.quantified_metrics,
                        "keywords": ach.keywords,
                        "skills_demonstrated": ach.skills_demonstrated,
                        "time_period": ach.time_period,
                        "context_tags": ach.context_tags,
                        "selection_count": ach.selection_count,
                        "success_correlation": ach.success_correlation
                    }
                    json_data["achievements"].append(ach_data)
            
            # Add education
            for edu in profile.education_entries:
                edu_data = {
                    "id": str(edu.id),
                    "institution_name": edu.institution_name,
                    "degree_type": edu.degree_type,
                    "field_of_study": edu.field_of_study,
                    "start_date": edu.start_date.isoformat() if edu.start_date else None,
                    "end_date": edu.end_date.isoformat() if edu.end_date else None,
                    "gpa": edu.gpa,
                    "honors": edu.honors,
                    "relevant_coursework": edu.relevant_coursework,
                    "location": edu.location
                }
                json_data["education"].append(edu_data)
            
            # Add skills
            for skill in profile.skills:
                skill_data = {
                    "id": str(skill.id),
                    "skill_name": skill.skill_name,
                    "skill_category": skill.skill_category,
                    "proficiency_level": skill.proficiency_level,
                    "years_experience": skill.years_experience,
                    "last_used": skill.last_used.isoformat() if skill.last_used else None,
                    "certification_name": skill.certification_name
                }
                json_data["skills"].append(skill_data)
            
            # Add projects
            for project in profile.projects:
                project_data = {
                    "id": str(project.id),
                    "project_name": project.project_name,
                    "project_description": project.project_description,
                    "role": project.role,
                    "start_date": project.start_date.isoformat() if project.start_date else None,
                    "end_date": project.end_date.isoformat() if project.end_date else None,
                    "project_type": project.project_type,
                    "technologies_used": project.technologies_used,
                    "key_achievements": project.key_achievements
                }
                json_data["projects"].append(project_data)
            
            # Add optimization data if available
            if content_data.get("optimized_content"):
                json_data["optimization"] = content_data["optimized_content"]
            
            if content_data.get("quality_assessment"):
                json_data["quality_assessment"] = content_data["quality_assessment"]
            
            # Save JSON file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{profile.full_name.replace(' ', '_')}_{content_data['export_type']}_{timestamp}.json"
            export_path = self.export_base_dir / filename
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            return export_path
            
        except Exception as e:
            logger.error(f"JSON export failed: {str(e)}")
            raise
    
    async def _assess_export_quality(
        self,
        profile: UserProfile,
        content_data: Dict[str, Any],
        file_path: Path,
        config: ExportConfiguration
    ) -> Dict[str, Any]:
        """Assess quality of exported document."""
        quality_metrics = {
            "format_compliance": 1.0,
            "content_completeness": 0.0,
            "optimization_score": 0.0,
            "file_integrity": 1.0 if os.path.exists(file_path) else 0.0
        }
        
        try:
            # Calculate content completeness
            sections_present = 0
            total_sections = 4  # contact, experience, education, skills
            
            if profile.email or profile.phone:
                sections_present += 1
            if profile.work_experiences:
                sections_present += 1
            if profile.education_entries:
                sections_present += 1
            if profile.skills:
                sections_present += 1
            
            quality_metrics["content_completeness"] = sections_present / total_sections
            
            # Use existing quality assessment if available
            if content_data.get("quality_assessment"):
                quality_data = content_data["quality_assessment"]
                quality_metrics["optimization_score"] = quality_data.get("overall_score", 0.0) / 100.0
            
            # Calculate overall quality score
            weights = {
                "format_compliance": 0.2,
                "content_completeness": 0.4,
                "optimization_score": 0.3,
                "file_integrity": 0.1
            }
            
            overall_score = sum(quality_metrics[key] * weights[key] for key in weights)
            quality_metrics["overall_score"] = overall_score
            
        except Exception as e:
            logger.warning(f"Quality assessment failed: {str(e)}")
            quality_metrics["overall_score"] = 0.5  # Default moderate score
        
        return quality_metrics
    
    async def _record_export_history(
        self,
        profile_id: str,
        export_type: str,
        target_role: str,
        target_company: str,
        config: ExportConfiguration,
        file_path: Path,
        file_size: int,
        generation_time: int,
        quality_metrics: Dict[str, Any]
    ):
        """Record export in history for tracking and analytics."""
        try:
            export_data = {
                "profile_id": profile_id,
                "export_type": export_type,
                "export_format": config.format,
                "export_purpose": "job_application" if target_role else "general",
                "target_role": target_role,
                "target_company": target_company,
                "export_success": True,
                "file_size_bytes": file_size,
                "generation_time_ms": generation_time
            }
            
            with self.db_service.get_session() as session:
                from app.models.database import ExportHistory
                
                export_history = ExportHistory(**export_data)
                session.add(export_history)
                session.commit()
                
                logger.info(f"Export history recorded for profile {profile_id}")
                
        except Exception as e:
            logger.error(f"Failed to record export history: {str(e)}")
            # Don't fail the export for history recording issues
    
    async def get_export_history(
        self,
        profile_id: str,
        limit: int = 50,
        export_format: str = None
    ) -> List[Dict[str, Any]]:
        """Get export history for a user profile."""
        try:
            with self.db_service.get_session() as session:
                from app.models.database import ExportHistory
                
                query = session.query(ExportHistory).filter(
                    ExportHistory.profile_id == profile_id
                )
                
                if export_format:
                    query = query.filter(ExportHistory.export_format == export_format)
                
                exports = query.order_by(ExportHistory.created_at.desc()).limit(limit).all()
                
                return [
                    {
                        "id": str(export.id),
                        "export_type": export.export_type,
                        "export_format": export.export_format,
                        "target_role": export.target_role,
                        "target_company": export.target_company,
                        "file_size_bytes": export.file_size_bytes,
                        "generation_time_ms": export.generation_time_ms,
                        "created_at": export.created_at.isoformat()
                    }
                    for export in exports
                ]
                
        except Exception as e:
            logger.error(f"Failed to get export history: {str(e)}")
            return []


# Create global export service instance
export_service = None

def get_export_service() -> ExportService:
    """Get the global export service instance."""
    global export_service
    if export_service is None:
        from app.services.database_service import database_service
        export_service = ExportService(database_service)
    return export_service