"""
Analysis endpoint for TailerAI v2.0
Analyze resume and job description for optimization with AI-powered insights
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel

from app.config.settings import get_settings
from app.services.job_analysis_service import job_analyzer, JobDescriptionAnalysisError
from app.services.ai_content_selection_service import AIContentSelectionEngine, ContentSelectionError
from app.api.dependencies.auth_deps import get_current_active_user
from app.models.database import User

router = APIRouter()
settings = get_settings()

# Initialize AI-enhanced content selector
ai_content_selector = AIContentSelectionEngine(use_ai_selection=True)


class JobAnalysisRequest(BaseModel):
    """Request model for job description analysis."""
    job_text: str
    job_url: Optional[str] = None


class JobAnalysisResponse(BaseModel):
    """Response model for job description analysis."""
    success: bool
    analysis_id: Optional[str] = None
    company_name: str
    position_title: str
    industry: str
    seniority_level: str
    employment_type: str
    required_skills: list
    preferred_skills: list
    key_requirements: list
    important_keywords: list
    ats_keywords: list
    keyword_frequency: dict
    confidence_score: float
    difficulty_level: str
    competition_level: str
    salary_range_estimate: Optional[str] = None
    from_cache: bool = False
    processing_time_ms: Optional[float] = None

@router.post("/job-analysis")
async def analyze_job_description(
    request: JobAnalysisRequest,
    current_user: User = Depends(get_current_active_user)
) -> JobAnalysisResponse:
    """
    Analyze job description with AI-powered insights.
    Returns comprehensive analysis including keywords, requirements, and ATS optimization.
    """
    try:
        import time
        start_time = time.time()
        
        # Perform job analysis
        analysis_result = await job_analyzer.analyze_job_description(
            job_text=request.job_text,
            job_url=request.job_url
        )
        
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Check if result came from cache
        from_cache = hasattr(analysis_result, '_from_cache') and analysis_result._from_cache
        
        return JobAnalysisResponse(
            success=True,
            analysis_id=analysis_result.job_description_hash,
            company_name=analysis_result.company_name,
            position_title=analysis_result.position_title,
            industry=analysis_result.industry,
            seniority_level=analysis_result.seniority_level,
            employment_type=analysis_result.employment_type,
            required_skills=analysis_result.required_skills,
            preferred_skills=analysis_result.preferred_skills,
            key_requirements=analysis_result.key_requirements,
            important_keywords=analysis_result.important_keywords,
            ats_keywords=analysis_result.ats_keywords,
            keyword_frequency=analysis_result.keyword_frequency,
            confidence_score=analysis_result.confidence_score,
            difficulty_level=analysis_result.difficulty_level,
            competition_level=analysis_result.competition_level,
            salary_range_estimate=analysis_result.salary_range_estimate,
            from_cache=from_cache,
            processing_time_ms=processing_time
        )
        
    except JobDescriptionAnalysisError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyze/{session_id}")
async def analyze_resume(session_id: str) -> Dict[str, Any]:
    """Legacy endpoint for uploaded resume and job description analysis"""
    
    session_dir = Path(settings.upload_dir) / session_id
    
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Find uploaded files
    resume_files = list(session_dir.glob("resume.*"))
    job_desc_files = list(session_dir.glob("job_description.*"))
    
    if not resume_files:
        raise HTTPException(status_code=400, detail="No resume file found")
    
    try:
        # TODO: Integrate with master dataset and job analysis service
        # For now, return enhanced placeholder response
        
        job_analysis = None
        if job_desc_files:
            # Read job description file and analyze
            job_file = job_desc_files[0]
            with open(job_file, 'r', encoding='utf-8') as f:
                job_text = f.read()
            
            try:
                analysis_result = await job_analyzer.analyze_job_description(job_text)
                job_analysis = {
                    "company": analysis_result.company_name,
                    "position": analysis_result.position_title,
                    "industry": analysis_result.industry,
                    "seniority_level": analysis_result.seniority_level,
                    "required_skills": analysis_result.required_skills,
                    "preferred_skills": analysis_result.preferred_skills,
                    "important_keywords": analysis_result.important_keywords,
                    "ats_keywords": analysis_result.ats_keywords,
                    "confidence_score": analysis_result.confidence_score
                }
            except Exception as e:
                print(f"Job analysis failed: {e}")
                job_analysis = {
                    "error": "Failed to analyze job description",
                    "fallback_keywords": ["python", "fastapi", "ai", "product management"]
                }
        
        analysis_result = {
            "session_id": session_id,
            "analysis_status": "completed",
            "resume_analysis": {
                "sections_found": ["education", "experience", "skills"],
                "word_count": 250,
                "format_score": 85
            },
            "job_description_analysis": job_analysis,
            "optimization_suggestions": [
                "Add more quantifiable achievements",
                "Include relevant keywords from job description",
                "Optimize for one-page format"
            ]
        }
        
        return analysis_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/job-analysis/{analysis_id}")
async def get_job_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_active_user)
) -> JobAnalysisResponse:
    """
    Retrieve a previously performed job analysis by ID.
    Useful for referencing past analyses without re-processing.
    """
    try:
        # Get cached analysis by hash
        cached_analysis = job_analyzer._get_cached_analysis(analysis_id)
        
        if not cached_analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return JobAnalysisResponse(
            success=True,
            analysis_id=cached_analysis.job_description_hash,
            company_name=cached_analysis.company_name,
            position_title=cached_analysis.position_title,
            industry=cached_analysis.industry,
            seniority_level=cached_analysis.seniority_level,
            employment_type=cached_analysis.employment_type,
            required_skills=cached_analysis.required_skills,
            preferred_skills=cached_analysis.preferred_skills,
            key_requirements=cached_analysis.key_requirements,
            important_keywords=cached_analysis.important_keywords,
            ats_keywords=cached_analysis.ats_keywords,
            keyword_frequency=cached_analysis.keyword_frequency,
            confidence_score=cached_analysis.confidence_score,
            difficulty_level=cached_analysis.difficulty_level,
            competition_level=cached_analysis.competition_level,
            salary_range_estimate=cached_analysis.salary_range_estimate,
            from_cache=True,
            processing_time_ms=0.0
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analysis: {str(e)}")


@router.get("/history")
async def get_job_analysis_history(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get job analysis history for the current user.
    Returns list of previously analyzed jobs.
    """
    try:
        # For now, return empty history - this would normally query the database
        return {
            "success": True,
            "history": [],
            "total": 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")

@router.get("/job-analysis/stats")
async def get_analysis_statistics(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get statistics about job analysis usage and performance.
    Useful for monitoring and optimization.
    """
    try:
        stats = job_analyzer.get_analysis_stats()
        return {
            "success": True,
            "statistics": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get("/analyze/{session_id}/status")
async def get_analysis_status(session_id: str) -> Dict[str, Any]:
    """Get analysis status for a session"""
    
    # TODO: Implement actual status tracking
    return {
        "session_id": session_id,
        "status": "ready_for_analysis",
        "message": "Analysis endpoint ready - Job Analysis & Content Selection Engines implemented"
    }


# Content Selection Engine Endpoints

class ContentSelectionRequest(BaseModel):
    """Request model for content selection."""
    job_analysis_id: str  # Hash ID from job analysis


class ScoredContentResponse(BaseModel):
    """Response model for scored content items."""
    content_id: str
    content_type: str
    content_data: dict
    total_score: float
    priority_tier: int
    estimated_word_count: int
    keywords_matched: list
    reasoning: str


class ContentSelectionResponse(BaseModel):
    """Response model for content selection results."""
    success: bool
    user_profile_id: str
    job_analysis_id: str
    
    # Selected content by category
    selected_achievements: list
    selected_work_experiences: list
    selected_skills: list
    selected_projects: list
    selected_education: list
    
    # Optimization metrics
    total_score: float
    estimated_word_count: int
    one_page_compliant: bool
    content_diversity_score: float
    keyword_coverage_percentage: float
    
    # Selection metadata
    selection_algorithm: str
    optimization_notes: list
    processing_time_ms: Optional[float] = None


@router.post("/content-selection")
async def select_optimal_content(
    request: ContentSelectionRequest,
    current_user: User = Depends(get_current_active_user)
) -> ContentSelectionResponse:
    """
    Select optimal content from user's master dataset for a specific job.
    Uses multi-dimensional scoring and one-page optimization.
    """
    try:
        import time
        start_time = time.time()
        
        # Get the job analysis first
        job_analysis = job_analyzer._get_cached_analysis(request.job_analysis_id)
        if not job_analysis:
            raise HTTPException(status_code=404, detail="Job analysis not found")
        
        # Get user profile ID
        user_profile_id = str(current_user.id)
        
        # Perform AI-enhanced content selection
        selection_result = await ai_content_selector.select_optimal_content(
            user_profile_id=user_profile_id,
            job_analysis=job_analysis
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        # Convert scored content to response format
        def convert_scored_content(scored_items):
            return [
                {
                    "content_id": item.content_id,
                    "content_type": item.content_type,
                    "content_data": item.content_data,
                    "total_score": item.total_score,
                    "priority_tier": item.priority_tier,
                    "estimated_word_count": item.estimated_word_count,
                    "keywords_matched": item.keywords_matched,
                    "reasoning": item.reasoning
                }
                for item in scored_items
            ]
        
        return ContentSelectionResponse(
            success=True,
            user_profile_id=selection_result.user_profile_id,
            job_analysis_id=selection_result.job_analysis_id,
            selected_achievements=convert_scored_content(selection_result.selected_achievements),
            selected_work_experiences=convert_scored_content(selection_result.selected_work_experiences),
            selected_skills=convert_scored_content(selection_result.selected_skills),
            selected_projects=convert_scored_content(selection_result.selected_projects),
            selected_education=convert_scored_content(selection_result.selected_education),
            total_score=selection_result.total_score,
            estimated_word_count=selection_result.estimated_word_count,
            one_page_compliant=selection_result.one_page_compliant,
            content_diversity_score=selection_result.content_diversity_score,
            keyword_coverage_percentage=selection_result.keyword_coverage_percentage,
            selection_algorithm=selection_result.selection_algorithm,
            optimization_notes=selection_result.optimization_notes,
            processing_time_ms=processing_time
        )
        
    except ContentSelectionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content selection failed: {str(e)}")


@router.get("/content-selection/stats")
async def get_content_selection_statistics(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get statistics about content selection usage and performance.
    """
    try:
        stats = ai_content_selector.get_selection_stats()
        return {
            "success": True,
            "statistics": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.post("/full-analysis")
async def perform_full_analysis(
    request: JobAnalysisRequest,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Perform complete job analysis and content selection in one request.
    Returns both job analysis and optimized content selection.
    """
    try:
        import time
        start_time = time.time()
        
        # Step 1: Analyze job description
        job_analysis_result = await job_analyzer.analyze_job_description(
            job_text=request.job_text,
            job_url=request.job_url
        )
        
        # Step 2: Select optimal content using AI-enhanced selector
        user_profile_id = str(current_user.id)
        selection_result = await ai_content_selector.select_optimal_content(
            user_profile_id=user_profile_id,
            job_analysis=job_analysis_result
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return {
            "success": True,
            "processing_time_ms": processing_time,
            "job_analysis": {
                "analysis_id": job_analysis_result.job_description_hash,
                "company_name": job_analysis_result.company_name,
                "position_title": job_analysis_result.position_title,
                "industry": job_analysis_result.industry,
                "required_skills": job_analysis_result.required_skills,
                "important_keywords": job_analysis_result.important_keywords,
                "confidence_score": job_analysis_result.confidence_score
            },
            "content_selection": {
                "total_score": selection_result.total_score,
                "estimated_word_count": selection_result.estimated_word_count,
                "one_page_compliant": selection_result.one_page_compliant,
                "keyword_coverage_percentage": selection_result.keyword_coverage_percentage,
                "selected_achievements_count": len(selection_result.selected_achievements),
                "selected_skills_count": len(selection_result.selected_skills),
                "optimization_notes": selection_result.optimization_notes
            }
        }
        
    except (JobDescriptionAnalysisError, ContentSelectionError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Full analysis failed: {str(e)}")