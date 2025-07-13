"""
API routes for Content Enhancement Engine.
Phase 3 implementation of AI-powered content improvement.
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.models.database import User
from app.api.dependencies import auth_deps
from app.services.content_enhancement_engine import (
    ContentEnhancementEngine,
    content_enhancer,
    EnhancementType,
    EnhancementLevel,
    AuthenticityLevel,
    ContentEnhancementResult
)
from app.services.job_analysis_service import job_analyzer
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/v2/content", tags=["Content Enhancement"])


class AchievementEnhancementRequest(BaseModel):
    """Request model for achievement enhancement."""
    achievement_id: str = Field(..., description="ID of achievement to enhance")
    enhancement_level: str = Field(
        default="moderate",
        description="Enhancement intensity: minimal, moderate, aggressive"
    )
    job_description: Optional[str] = Field(
        default=None,
        min_length=50,
        max_length=10000,
        description="Job description for context-aware enhancement"
    )
    company_name: Optional[str] = Field(None, max_length=255)
    position_title: Optional[str] = Field(None, max_length=255)
    target_keywords: Optional[List[str]] = Field(
        default=None,
        description="Specific keywords to integrate naturally"
    )
    style_preferences: Optional[Dict[str, Any]] = Field(
        default=None,
        description="User style preferences (tone, formality, industry focus, etc.)"
    )


class BatchEnhancementRequest(BaseModel):
    """Request model for batch achievement enhancement."""
    achievement_ids: List[str] = Field(..., min_items=1, max_items=10)
    enhancement_level: str = Field(default="moderate")
    job_description: Optional[str] = Field(default=None)
    company_name: Optional[str] = Field(None, max_length=255)
    position_title: Optional[str] = Field(None, max_length=255)


class SummaryEnhancementRequest(BaseModel):
    """Request model for professional summary enhancement."""
    summary_text: str = Field(..., min_length=20, max_length=2000)
    job_description: Optional[str] = Field(default=None)
    company_name: Optional[str] = Field(None, max_length=255)
    position_title: Optional[str] = Field(None, max_length=255)


class EnhancementChangeResponse(BaseModel):
    """Response model for individual enhancement changes."""
    change_type: str
    original_text: str
    enhanced_text: str
    reasoning: str
    impact_score: float
    authenticity_verified: bool


class ContentEnhancementResponse(BaseModel):
    """Response model for content enhancement results."""
    success: bool
    enhancement_id: str
    original_content: str
    enhanced_content: str
    enhancement_type: str
    enhancement_level: str
    
    # Enhancement analysis
    changes_made: List[EnhancementChangeResponse]
    overall_improvement_score: float
    authenticity_level: str
    
    # Keywords and optimization
    keywords_integrated: List[str]
    action_verbs_improved: List[str]
    quantification_enhanced: bool
    
    # Processing metadata
    processing_time: Optional[float] = None
    
    # AI metadata
    ai_reasoning: Optional[str] = None
    ai_confidence_score: Optional[float] = None
    fallback_applied: bool = False


class EnhancementApprovalRequest(BaseModel):
    """Request model for enhancement approval."""
    approved: bool = Field(..., description="Whether user approves the enhancement")
    feedback: Optional[str] = Field(None, max_length=1000, description="User feedback")
    apply_to_resume: bool = Field(default=False, description="Apply enhancement to resume")


@router.post("/enhance/achievement", response_model=ContentEnhancementResponse)
async def enhance_achievement(
    request: AchievementEnhancementRequest,
    current_user: User = Depends(auth_deps.get_current_user)
) -> ContentEnhancementResponse:
    """
    Enhance a single achievement text for maximum impact while maintaining authenticity.
    
    This endpoint analyzes achievement text and provides AI-powered enhancements
    including improved action verbs, natural keyword integration, and better
    quantification presentation.
    
    **Features:**
    - AI-powered text improvement with Gemini
    - Natural keyword integration based on job context
    - Action verb strengthening
    - Quantification enhancement
    - 100% authenticity preservation
    
    **Enhancement Levels:**
    - minimal: Light improvements only
    - moderate: Balanced enhancement (recommended)
    - aggressive: Maximum impact improvements
    """
    try:
        logger.info(f"Starting achievement enhancement for {request.achievement_id}")
        
        # Validate enhancement level
        try:
            enhancement_level = EnhancementLevel(request.enhancement_level)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid enhancement level. Must be one of: {[level.value for level in EnhancementLevel]}"
            )
        
        # Analyze job description if provided
        job_analysis = None
        if request.job_description:
            logger.info("Analyzing job description for enhancement context")
            job_analysis = await job_analyzer.analyze_job_description(
                job_description=request.job_description,
                company_name=request.company_name or "Unknown",
                position_title=request.position_title or "Unknown Position"
            )
        
        # Perform content enhancement
        result = await content_enhancer.enhance_achievement_text(
            achievement_id=request.achievement_id,
            job_analysis=job_analysis,
            enhancement_level=enhancement_level,
            target_keywords=request.target_keywords,
            style_preferences=request.style_preferences
        )
        
        # Convert to response format
        response = ContentEnhancementResponse(
            success=True,
            enhancement_id=f"enh_{request.achievement_id}",
            original_content=result.original_content,
            enhanced_content=result.enhanced_content,
            enhancement_type=result.enhancement_type.value,
            enhancement_level=result.enhancement_level.value,
            changes_made=[
                EnhancementChangeResponse(
                    change_type=change.change_type,
                    original_text=change.original_text,
                    enhanced_text=change.enhanced_text,
                    reasoning=change.reasoning,
                    impact_score=change.impact_score,
                    authenticity_verified=change.authenticity_verified
                ) for change in result.changes_made
            ],
            overall_improvement_score=result.overall_improvement_score,
            authenticity_level=result.authenticity_level.value,
            keywords_integrated=result.keywords_integrated,
            action_verbs_improved=result.action_verbs_improved,
            quantification_enhanced=result.quantification_enhanced,
            processing_time=result.processing_time,
            ai_reasoning=result.ai_reasoning,
            ai_confidence_score=result.ai_confidence_score,
            fallback_applied=result.fallback_applied
        )
        
        logger.info(f"Achievement enhancement completed. Improvement score: {response.overall_improvement_score:.2f}, "
                   f"Authenticity: {response.authenticity_level}, "
                   f"Changes: {len(response.changes_made)}")
        
        return response
        
    except Exception as e:
        logger.error(f"Achievement enhancement failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Achievement enhancement failed: {str(e)}"
        )


@router.post("/enhance/batch", response_model=List[ContentEnhancementResponse])
async def enhance_multiple_achievements(
    request: BatchEnhancementRequest,
    current_user: User = Depends(auth_deps.get_current_user)
) -> List[ContentEnhancementResponse]:
    """
    Enhance multiple achievements with consistent styling and keyword integration.
    
    This endpoint processes multiple achievements together to ensure consistent
    enhancement approach and avoid keyword stuffing across achievements.
    """
    try:
        logger.info(f"Starting batch enhancement for {len(request.achievement_ids)} achievements")
        
        # Validate enhancement level
        try:
            enhancement_level = EnhancementLevel(request.enhancement_level)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid enhancement level. Must be one of: {[level.value for level in EnhancementLevel]}"
            )
        
        # Analyze job description if provided
        job_analysis = None
        if request.job_description:
            job_analysis = await job_analyzer.analyze_job_description(
                job_description=request.job_description,
                company_name=request.company_name or "Unknown",
                position_title=request.position_title or "Unknown Position"
            )
        
        # Perform batch enhancement
        results = await content_enhancer.enhance_multiple_achievements(
            achievement_ids=request.achievement_ids,
            job_analysis=job_analysis,
            enhancement_level=enhancement_level
        )
        
        # Convert to response format
        responses = []
        for i, result in enumerate(results):
            response = ContentEnhancementResponse(
                success=True,
                enhancement_id=f"batch_enh_{request.achievement_ids[i]}",
                original_content=result.original_content,
                enhanced_content=result.enhanced_content,
                enhancement_type=result.enhancement_type.value,
                enhancement_level=result.enhancement_level.value,
                changes_made=[
                    EnhancementChangeResponse(
                        change_type=change.change_type,
                        original_text=change.original_text,
                        enhanced_text=change.enhanced_text,
                        reasoning=change.reasoning,
                        impact_score=change.impact_score,
                        authenticity_verified=change.authenticity_verified
                    ) for change in result.changes_made
                ],
                overall_improvement_score=result.overall_improvement_score,
                authenticity_level=result.authenticity_level.value,
                keywords_integrated=result.keywords_integrated,
                action_verbs_improved=result.action_verbs_improved,
                quantification_enhanced=result.quantification_enhanced,
                processing_time=result.processing_time,
                ai_reasoning=result.ai_reasoning,
                ai_confidence_score=result.ai_confidence_score,
                fallback_applied=result.fallback_applied
            )
            responses.append(response)
        
        return responses
        
    except Exception as e:
        logger.error(f"Batch enhancement failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch enhancement failed: {str(e)}"
        )


@router.post("/enhance/summary", response_model=ContentEnhancementResponse)
async def enhance_professional_summary(
    request: SummaryEnhancementRequest,
    current_user: User = Depends(auth_deps.get_current_user)
) -> ContentEnhancementResponse:
    """
    Enhance professional summary for better impact and keyword integration.
    
    This endpoint improves professional summary text while maintaining the
    user's authentic voice and professional tone.
    """
    try:
        logger.info("Starting professional summary enhancement")
        
        # Analyze job description if provided
        job_analysis = None
        if request.job_description:
            job_analysis = await job_analyzer.analyze_job_description(
                job_description=request.job_description,
                company_name=request.company_name or "Unknown",
                position_title=request.position_title or "Unknown Position"
            )
        
        # Perform summary enhancement
        result = await content_enhancer.enhance_professional_summary(
            summary_text=request.summary_text,
            job_analysis=job_analysis,
            user_profile_id=str(current_user.profile.id)
        )
        
        # Convert to response format
        response = ContentEnhancementResponse(
            success=True,
            enhancement_id=f"summary_enh_{current_user.profile.id}",
            original_content=result.original_content,
            enhanced_content=result.enhanced_content,
            enhancement_type=result.enhancement_type.value,
            enhancement_level=result.enhancement_level.value,
            changes_made=[
                EnhancementChangeResponse(
                    change_type=change.change_type,
                    original_text=change.original_text,
                    enhanced_text=change.enhanced_text,
                    reasoning=change.reasoning,
                    impact_score=change.impact_score,
                    authenticity_verified=change.authenticity_verified
                ) for change in result.changes_made
            ],
            overall_improvement_score=result.overall_improvement_score,
            authenticity_level=result.authenticity_level.value,
            keywords_integrated=result.keywords_integrated,
            action_verbs_improved=result.action_verbs_improved,
            quantification_enhanced=result.quantification_enhanced,
            processing_time=result.processing_time,
            ai_reasoning=result.ai_reasoning,
            ai_confidence_score=result.ai_confidence_score,
            fallback_applied=result.fallback_applied
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Summary enhancement failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Summary enhancement failed: {str(e)}"
        )


@router.post("/enhancement/{enhancement_id}/approve")
async def approve_enhancement(
    enhancement_id: str,
    request: EnhancementApprovalRequest,
    current_user: User = Depends(auth_deps.get_current_user)
) -> Dict[str, Any]:
    """
    Approve or reject a content enhancement.
    
    This endpoint allows users to provide feedback on enhancements and
    decide whether to apply them to their resume.
    """
    try:
        # In a full implementation, this would update the database
        # For now, return a success response
        
        logger.info(f"Enhancement {enhancement_id} {'approved' if request.approved else 'rejected'} by user")
        
        return {
            "success": True,
            "enhancement_id": enhancement_id,
            "status": "approved" if request.approved else "rejected",
            "applied_to_resume": request.apply_to_resume,
            "user_feedback": request.feedback,
            "message": f"Enhancement {enhancement_id} {'approved' if request.approved else 'rejected'} successfully"
        }
        
    except Exception as e:
        logger.error(f"Enhancement approval failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Enhancement approval failed: {str(e)}"
        )


@router.get("/enhancement/history")
async def get_enhancement_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    enhancement_type: Optional[str] = Query(None),
    current_user: User = Depends(auth_deps.get_current_user)
) -> Dict[str, Any]:
    """
    Get user's content enhancement history.
    
    Returns a list of previous enhancements with their approval status
    and performance outcomes.
    """
    try:
        # In a full implementation, this would query the database
        # For now, return a sample response
        
        return {
            "success": True,
            "enhancements": [],
            "total_count": 0,
            "limit": limit,
            "offset": offset,
            "enhancement_type": enhancement_type
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve enhancement history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve enhancement history: {str(e)}"
        )


@router.get("/enhancement/status")
async def get_enhancement_service_status(
    current_user: User = Depends(auth_deps.get_current_user)
) -> Dict[str, Any]:
    """
    Get current status of content enhancement services.
    
    Returns information about service availability, configuration,
    and current performance metrics.
    """
    try:
        status = {
            "content_enhancement_enabled": settings.enable_ai_content_enhancement,
            "fallback_enabled": settings.content_enhancement_fallback_enabled,
            "confidence_threshold": settings.content_enhancement_confidence_threshold,
            "default_enhancement_level": settings.content_enhancement_default_level,
            "ai_enhancement_available": content_enhancer.use_ai_enhancement
        }
        
        if content_enhancer.gemini_client:
            gemini_status = content_enhancer.gemini_client.get_usage_stats()
            status["gemini"] = {
                "available": content_enhancer.gemini_client.is_available(),
                "usage_stats": gemini_status
            }
        else:
            status["gemini"] = {
                "available": False,
                "reason": "Gemini client not initialized or disabled"
            }
        
        # Service capabilities
        status["capabilities"] = {
            "enhancement_types": [t.value for t in EnhancementType],
            "enhancement_levels": [l.value for l in EnhancementLevel],
            "authenticity_levels": [a.value for a in AuthenticityLevel],
            "features": [
                "action_verb_improvement",
                "keyword_integration",
                "quantification_enhancement",
                "natural_language_preservation",
                "authenticity_verification"
            ]
        }
        
        return {
            "success": True,
            "status": status
        }
        
    except Exception as e:
        logger.error(f"Failed to get enhancement service status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get enhancement service status: {str(e)}"
        )