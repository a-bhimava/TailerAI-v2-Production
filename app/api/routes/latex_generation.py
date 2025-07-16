"""
LaTeX Generation API Routes for TailerAI v2.0.
Handles resume PDF generation from selected master dataset content.
Following project blueprint best practices for API design and error handling.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.models.database import User
from app.api.dependencies.auth_deps import get_current_user
from app.services.latex_generation_service import latex_generation_service, LaTeXGenerationError
from app.services.database_service import db_service
from app.services.content_selection_service import content_selector

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/latex", tags=["latex-generation"])


# Request/Response Models

class WorkExperienceData(BaseModel):
    """Work experience data for PDF generation."""
    experience_id: str
    company_name: str
    position_title: str
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    company_description: Optional[str] = None
    achievements: List[str] = Field(default_factory=list)


class EducationData(BaseModel):
    """Education data for PDF generation."""
    institution_name: str
    degree_type: str
    field_of_study: Optional[str] = None
    location: Optional[str] = None
    graduation_date: Optional[str] = None
    gpa: Optional[float] = None
    gpa_scale: Optional[float] = None
    relevant_coursework: Optional[str] = None
    academic_achievements: Optional[str] = None


class SkillData(BaseModel):
    """Skill data for PDF generation."""
    skill_name: str
    skill_category: Optional[str] = None
    proficiency_level: Optional[str] = None


class ProjectData(BaseModel):
    """Project data for PDF generation."""
    name: str
    description: str
    technologies: Optional[List[str]] = None


class GenerateResumeRequest(BaseModel):
    """Request model for resume PDF generation."""
    work_experiences: List[WorkExperienceData] = Field(default_factory=list)
    education: List[EducationData] = Field(default_factory=list)
    skills: List[SkillData] = Field(default_factory=list)
    projects: List[ProjectData] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    additional_sections: Dict[str, Any] = Field(default_factory=dict)
    filename_prefix: Optional[str] = Field(default="resume", max_length=50)


class OptimizedResumeRequest(BaseModel):
    """Request model for optimized resume generation using content selection."""
    job_analysis_id: str = Field(..., description="ID from job analysis service")
    manual_overrides: Optional[Dict[str, List[str]]] = Field(
        default_factory=dict,
        description="Manual overrides for content selection"
    )
    filename_prefix: Optional[str] = Field(default="optimized_resume", max_length=50)


class GenerateResumeResponse(BaseModel):
    """Response model for resume generation."""
    success: bool
    message: str
    pdf_download_url: Optional[str] = None
    generation_id: Optional[str] = None
    processing_time_ms: Optional[float] = None


class LaTeXStatusResponse(BaseModel):
    """Response model for LaTeX system status."""
    latex_available: bool
    version_info: str
    temp_files_count: int
    service_status: str


# Helper Functions

async def get_current_user_for_latex(
    user: User = Depends(get_current_user)
) -> User:
    """Get authenticated user for LaTeX generation routes."""
    return user


def _convert_request_to_content_dict(request: GenerateResumeRequest) -> Dict[str, Any]:
    """Convert request model to content dictionary format."""
    content = {
        'work_experiences': [],
        'education': [edu.dict() for edu in request.education],
        'skills': [skill.dict() for skill in request.skills],
        'projects': [project.dict() for project in request.projects],
        'certifications': request.certifications,
        'additional_sections': request.additional_sections
    }
    
    # Convert work experiences with achievements
    for work_exp in request.work_experiences:
        exp_dict = work_exp.dict()
        # Format as expected by LaTeX service - merge experience data with achievements directly
        exp_dict['achievements'] = work_exp.achievements  # Keep as strings, not objects
        content['work_experiences'].append(exp_dict)
    
    return content


# API Routes

@router.post("/generate", response_model=GenerateResumeResponse)
async def generate_resume_pdf(
    request: GenerateResumeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_for_latex)
):
    """
    Generate a PDF resume from provided content.
    
    This endpoint allows users to generate a PDF resume by providing
    their work experiences, education, skills, and other content directly.
    """
    try:
        start_time = datetime.now()
        
        # Debug: log the received request data
        logger.info(f"========== LATEX DEBUG START ==========")
        logger.info(f"Received LaTeX generation request from user {current_user.id}")
        logger.info(f"Request data: work_experiences={len(request.work_experiences)}, education={len(request.education)}, skills={len(request.skills)}, projects={len(request.projects)}")
        logger.info(f"Full request details: {request.dict()}")
        
        # Log each work experience in detail
        for i, exp in enumerate(request.work_experiences):
            logger.info(f"Work Experience {i}: {exp.dict()}")
        
        # Log each education entry in detail  
        for i, edu in enumerate(request.education):
            logger.info(f"Education {i}: {edu.dict()}")
        
        # Validate request
        if not request.work_experiences and not request.education:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least work experience or education must be provided"
            )
        
        # Convert request to content format
        selected_content = _convert_request_to_content_dict(request)
        logger.info(f"Converted content format: {selected_content}")
        
        # Generate PDF
        success, pdf_path, message = await latex_generation_service.generate_resume_pdf(
            user_id=str(current_user.id),
            selected_content=selected_content,
            filename_prefix=request.filename_prefix or "resume"
        )
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        if success and pdf_path:
            # Create download URL
            filename = Path(pdf_path).name
            download_url = f"/api/v2/latex/download/{filename}"
            
            # Schedule cleanup of old files
            background_tasks.add_task(
                latex_generation_service.cleanup_temp_files,
                max_age_hours=24
            )
            
            logger.info(f"Resume generated successfully for user {current_user.id}")
            
            return GenerateResumeResponse(
                success=True,
                message=message,
                pdf_download_url=download_url,
                generation_id=filename.replace('.pdf', ''),
                processing_time_ms=processing_time
            )
        else:
            logger.error(f"========== LATEX GENERATION FAILED ==========")
            logger.error(f"Resume generation failed for user {current_user.id}: {message}")
            logger.error(f"PDF path: {pdf_path}")
            logger.error(f"Success flag: {success}")
            logger.error(f"Processing time: {processing_time}ms")
            logger.error(f"========== LATEX DEBUG END ==========")
            return GenerateResumeResponse(
                success=False,
                message=f"PDF generation failed: {message}",
                processing_time_ms=processing_time
            )
    
    except HTTPException:
        raise
    except LaTeXGenerationError as e:
        logger.error(f"LaTeX generation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF generation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in resume generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during PDF generation"
        )


@router.post("/generate-optimized", response_model=GenerateResumeResponse)
async def generate_optimized_resume(
    request: OptimizedResumeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_for_latex)
):
    """
    Generate an optimized PDF resume using content selection engine.
    
    This endpoint uses the job analysis and content selection services
    to automatically select the best content from the user's master dataset
    and generate an optimized PDF resume.
    """
    try:
        from datetime import datetime
        start_time = datetime.now()
        
        # Get selected content from content selection service
        selected_content = await content_selector.get_selected_content_for_job(
            user_id=str(current_user.id),
            job_analysis_id=request.job_analysis_id,
            manual_overrides=request.manual_overrides
        )
        
        if not selected_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No content selection found for the provided job analysis ID"
            )
        
        # Generate PDF with optimized content
        success, pdf_path, message = await latex_generation_service.generate_resume_pdf(
            user_id=str(current_user.id),
            selected_content=selected_content,
            filename_prefix=request.filename_prefix or "optimized_resume"
        )
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        if success and pdf_path:
            # Create download URL
            filename = Path(pdf_path).name
            download_url = f"/api/v2/latex/download/{filename}"
            
            # Schedule cleanup
            background_tasks.add_task(
                latex_generation_service.cleanup_temp_files,
                max_age_hours=24
            )
            
            logger.info(f"Optimized resume generated for user {current_user.id}, job analysis {request.job_analysis_id}")
            
            return GenerateResumeResponse(
                success=True,
                message="Optimized resume generated successfully",
                pdf_download_url=download_url,
                generation_id=filename.replace('.pdf', ''),
                processing_time_ms=processing_time
            )
        else:
            logger.error(f"Optimized resume generation failed: {message}")
            return GenerateResumeResponse(
                success=False,
                message=message,
                processing_time_ms=processing_time
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in optimized resume generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimized resume generation failed: {str(e)}"
        )


@router.get("/download/{filename}")
async def download_pdf(
    filename: str,
    current_user: User = Depends(get_current_user_for_latex)
):
    """
    Download a generated PDF resume.
    
    Security: Only authenticated users can download PDFs, and the filename
    must contain their user ID for additional security.
    """
    try:
        # Validate filename format and security
        if not filename.endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file format"
            )
        
        # Check if user ID is in filename for security
        user_id_str = str(current_user.id)
        if user_id_str not in filename:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Construct file path
        file_path = latex_generation_service.temp_dir / filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found or has expired"
            )
        
        logger.info(f"User {current_user.id} downloading PDF: {filename}")
        
        return FileResponse(
            path=str(file_path),
            filename=f"resume_{datetime.now().strftime('%Y%m%d')}.pdf",
            media_type="application/pdf"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading PDF: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Download failed"
        )


@router.get("/status", response_model=LaTeXStatusResponse)
async def get_latex_status():
    """
    Get LaTeX system status and health check.
    
    This endpoint provides information about the LaTeX installation
    and service health for debugging and monitoring purposes.
    """
    try:
        # Check LaTeX availability
        latex_available, version_info = await latex_generation_service.validate_latex_installation()
        
        # Count temporary files
        temp_files_count = len(list(latex_generation_service.temp_dir.glob("*.pdf")))
        
        # Determine service status
        if latex_available:
            service_status = "operational"
        else:
            service_status = "degraded - LaTeX not available"
        
        logger.info(f"LaTeX status check: {service_status}")
        
        return LaTeXStatusResponse(
            latex_available=latex_available,
            version_info=version_info,
            temp_files_count=temp_files_count,
            service_status=service_status
        )
    
    except Exception as e:
        logger.error(f"Error checking LaTeX status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Status check failed"
        )


@router.post("/cleanup")
async def cleanup_temp_files(
    max_age_hours: int = 24,
    current_user: User = Depends(get_current_user_for_latex)
):
    """
    Manually trigger cleanup of temporary PDF files.
    
    Admin endpoint for maintaining the temporary file storage.
    """
    try:
        cleaned_count = latex_generation_service.cleanup_temp_files(max_age_hours)
        
        logger.info(f"Manual cleanup completed by user {current_user.id}: {cleaned_count} files removed")
        
        return {
            "success": True,
            "message": f"Cleaned up {cleaned_count} temporary files",
            "files_removed": cleaned_count
        }
    
    except Exception as e:
        logger.error(f"Error during manual cleanup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cleanup failed"
        )