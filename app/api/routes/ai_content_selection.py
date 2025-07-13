"""
API routes for AI-enhanced content selection.
Phase 1 implementation of Gemini integration strategy.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.models.database import User
from app.api.dependencies import auth_deps
from app.services.ai_content_selection_service import (
    AIContentSelectionEngine, 
    SelectionMethod, 
    EnhancedContentSelectionResult
)
from app.services.job_analysis_service import JobAnalysisResult, job_analyzer
from app.models.schemas import ErrorResponse
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/v2/content", tags=["AI Content Selection"])

# Initialize AI content selection engine
ai_selector = AIContentSelectionEngine()


class ContentSelectionRequest(BaseModel):
    """Request model for AI-enhanced content selection."""
    job_description: str = Field(..., min_length=50, max_length=10000, description="Job description text")
    company_name: Optional[str] = Field(None, max_length=255, description="Company name")
    position_title: Optional[str] = Field(None, max_length=255, description="Position title")
    selection_method: SelectionMethod = Field(
        default=SelectionMethod.AI_ENHANCED, 
        description="Content selection method to use"
    )
    include_reasoning: bool = Field(
        default=True, 
        description="Whether to include AI reasoning in response"
    )


class SelectionReasoningResponse(BaseModel):
    """Response model for AI selection reasoning."""
    selection_rationale: str
    content_fit_analysis: str
    keyword_integration_strategy: str
    combination_logic: str
    confidence_score: float
    alternative_considerations: list[str]


class ContentSelectionResponse(BaseModel):
    """Response model for content selection results."""
    success: bool
    selection_id: str
    user_profile_id: str
    
    # Selection results
    selected_achievements: list[Dict[str, Any]]
    selected_skills: list[Dict[str, Any]]
    selected_projects: list[Dict[str, Any]]
    selected_education: list[Dict[str, Any]]
    
    # Metrics
    total_score: float
    estimated_word_count: int
    one_page_compliant: bool
    keyword_coverage_percentage: float
    
    # AI metadata
    selection_method: str
    ai_confidence_score: Optional[float] = None
    fallback_applied: bool = False
    gemini_processing_time: Optional[float] = None
    
    # Optional AI reasoning
    ai_reasoning: Optional[SelectionReasoningResponse] = None


@router.post("/select", response_model=ContentSelectionResponse)
async def ai_enhanced_content_selection(
    request: ContentSelectionRequest,
    current_user: User = Depends(auth_deps.get_current_user)
) -> ContentSelectionResponse:
    """
    Perform AI-enhanced content selection for resume optimization.
    
    This endpoint uses Gemini AI to intelligently select and score content
    from the user's master dataset based on job requirements.
    
    **Selection Methods:**
    - `algorithmic`: Traditional scoring-based selection (fallback)
    - `ai_enhanced`: AI reasoning + algorithmic validation (recommended)
    - `ai_primary`: AI-first selection with constraints (experimental)
    
    **Features:**
    - Intelligent content combination optimization
    - One-page compliance enforcement
    - ATS keyword optimization
    - Transparent AI reasoning (optional)
    - Automatic fallback on AI failure
    """
    try:
        logger.info(f"Starting AI content selection for user {current_user.id} using method: {request.selection_method}")
        
        # Check if AI selection is enabled
        if request.selection_method != SelectionMethod.ALGORITHMIC and not settings.enable_ai_content_selection:
            logger.warning(f"AI content selection disabled, falling back to algorithmic method")
            request.selection_method = SelectionMethod.ALGORITHMIC
        
        # Analyze job description first
        logger.info("Analyzing job description with AI")
        job_analysis = await job_analyzer.analyze_job_description(
            job_description=request.job_description,
            company_name=request.company_name or "Unknown",
            position_title=request.position_title or "Unknown Position"
        )
        
        if not job_analysis:
            raise HTTPException(
                status_code=400,
                detail="Failed to analyze job description. Please ensure it contains valid job requirements."
            )
        
        # Perform enhanced content selection
        logger.info(f"Performing content selection using method: {request.selection_method}")
        selection_result = await ai_selector.select_optimal_content(
            user_profile_id=str(current_user.profile.id),
            job_analysis=job_analysis,
            selection_method=request.selection_method
        )
        
        # Prepare response
        response = ContentSelectionResponse(
            success=True,
            selection_id=selection_result.job_analysis_id,
            user_profile_id=selection_result.user_profile_id,
            selected_achievements=[item.content_data for item in selection_result.selected_achievements],
            selected_skills=[item.content_data for item in selection_result.selected_skills],
            selected_projects=[item.content_data for item in selection_result.selected_projects],
            selected_education=[item.content_data for item in selection_result.selected_education],
            total_score=selection_result.total_score,
            estimated_word_count=selection_result.estimated_word_count,
            one_page_compliant=selection_result.one_page_compliant,
            keyword_coverage_percentage=selection_result.keyword_coverage_percentage,
            selection_method=selection_result.selection_method,
            ai_confidence_score=selection_result.ai_confidence_score,
            fallback_applied=selection_result.fallback_applied,
            gemini_processing_time=selection_result.gemini_processing_time
        )
        
        # Include AI reasoning if requested and available
        if request.include_reasoning and selection_result.ai_reasoning:
            response.ai_reasoning = SelectionReasoningResponse(
                selection_rationale=selection_result.ai_reasoning.selection_rationale,
                content_fit_analysis=selection_result.ai_reasoning.content_fit_analysis,
                keyword_integration_strategy=selection_result.ai_reasoning.keyword_integration_strategy,
                combination_logic=selection_result.ai_reasoning.combination_logic,
                confidence_score=selection_result.ai_reasoning.confidence_score,
                alternative_considerations=selection_result.ai_reasoning.alternative_considerations
            )
        
        logger.info(f"Content selection completed successfully. Method: {response.selection_method}, "
                   f"Achievements: {len(response.selected_achievements)}, "
                   f"Words: {response.estimated_word_count}, "
                   f"Fallback: {response.fallback_applied}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content selection failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Content selection failed: {str(e)}"
        )


@router.get("/selection/{selection_id}/reasoning")
async def get_selection_reasoning(
    selection_id: str,
    current_user: User = Depends(auth_deps.get_current_user)
) -> SelectionReasoningResponse:
    """
    Get AI reasoning for a specific content selection.
    
    Retrieves the detailed AI reasoning that was used to make content
    selection decisions for a particular job application.
    """
    try:
        # TODO: Implement retrieval from database
        # For now, return a placeholder response
        raise HTTPException(
            status_code=501,
            detail="Selection reasoning retrieval not yet implemented"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve selection reasoning: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve selection reasoning: {str(e)}"
        )


@router.get("/methods")
async def get_available_selection_methods(
    current_user: User = Depends(auth_deps.get_current_user)
) -> Dict[str, Any]:
    """
    Get available content selection methods and their capabilities.
    
    Returns information about which selection methods are available
    based on current configuration and AI service status.
    """
    try:
        # Check AI availability
        ai_available = settings.enable_ai_content_selection and ai_selector.gemini_client
        if ai_available:
            ai_available = ai_selector.gemini_client.is_available()
        
        # Check rate limits
        rate_limit_ok = True
        if ai_available and ai_selector.gemini_client:
            rate_limit_ok = ai_selector.gemini_client.rate_limiter.can_make_request()
        
        methods = {
            "algorithmic": {
                "available": True,
                "description": "Traditional scoring-based content selection",
                "features": ["Fast processing", "Reliable results", "No API dependencies"],
                "recommended_for": ["Quick selections", "Fallback scenarios"]
            }
        }
        
        if ai_available:
            methods["ai_enhanced"] = {
                "available": rate_limit_ok,
                "description": "AI reasoning with algorithmic validation",
                "features": ["Intelligent reasoning", "Transparent decisions", "Automatic fallback"],
                "recommended_for": ["Most applications", "Balanced AI assistance"]
            }
            
            methods["ai_primary"] = {
                "available": rate_limit_ok,
                "description": "AI-first selection with constraint validation",
                "features": ["Advanced AI reasoning", "Context-aware decisions", "Experimental"],
                "recommended_for": ["Complex roles", "Maximum AI assistance"]
            }
        
        return {
            "success": True,
            "ai_enabled": ai_available,
            "rate_limit_ok": rate_limit_ok,
            "default_method": settings.ai_selection_default_method,
            "fallback_enabled": settings.ai_selection_fallback_enabled,
            "methods": methods
        }
        
    except Exception as e:
        logger.error(f"Failed to get selection methods: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get selection methods: {str(e)}"
        )


@router.get("/status")
async def get_ai_selection_status(
    current_user: User = Depends(auth_deps.get_current_user)
) -> Dict[str, Any]:
    """
    Get current status of AI content selection services.
    
    Returns information about AI service availability, rate limits,
    and current configuration for debugging and monitoring.
    """
    try:
        status = {
            "ai_enabled": settings.enable_ai_content_selection,
            "fallback_enabled": settings.ai_selection_fallback_enabled,
            "confidence_threshold": settings.ai_selection_confidence_threshold,
            "default_method": settings.ai_selection_default_method
        }
        
        if ai_selector.gemini_client:
            gemini_status = ai_selector.gemini_client.get_usage_stats()
            status["gemini"] = {
                "available": ai_selector.gemini_client.is_available(),
                "usage_stats": gemini_status
            }
        else:
            status["gemini"] = {
                "available": False,
                "error": "Gemini client not initialized"
            }
        
        return {
            "success": True,
            "status": status
        }
        
    except Exception as e:
        logger.error(f"Failed to get AI selection status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get AI selection status: {str(e)}"
        )