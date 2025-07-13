"""
API routes for Personalization Engine.
Phase 4 implementation of continuous learning and personalization capabilities.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from app.models.database import User
from app.api.dependencies import auth_deps
from app.services.personalization_engine import (
    PersonalizationEngine,
    personalization_engine,
    OutcomeType,
    LearningConfidence,
    PersonalizationStrategy,
    ApplicationOutcomeData,
    UserSuccessPattern,
    PersonalizationInsight,
    PersonalizationResult
)
from app.services.job_analysis_service import job_analyzer
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/v2/personalization", tags=["Personalization & Learning"])


class ApplicationOutcomeRequest(BaseModel):
    """Request model for tracking application outcomes."""
    application_id: str = Field(..., description="Unique application identifier")
    company_name: str = Field(..., max_length=255)
    position_title: str = Field(..., max_length=255)
    job_description: Optional[str] = Field(None, max_length=10000)
    industry: Optional[str] = Field(None, max_length=100)
    
    # Application context
    content_selection_id: Optional[str] = Field(None, description="Content selection used")
    ats_optimization_id: Optional[str] = Field(None, description="ATS optimization applied")
    content_enhancement_ids: Optional[List[str]] = Field(None, description="Content enhancements used")
    
    # Outcome details
    outcome_type: str = Field(..., description="Type of outcome")
    outcome_date: datetime = Field(..., description="When the outcome occurred")
    days_to_outcome: Optional[int] = Field(None, ge=0, le=365)
    
    # Additional outcome data
    feedback_notes: Optional[str] = Field(None, max_length=2000)
    salary_offered: Optional[float] = Field(None, ge=0)
    rejection_reason: Optional[str] = Field(None, max_length=255)
    interview_rounds: Optional[int] = Field(None, ge=0, le=10)
    
    # Learning metadata
    ai_content_selection_used: bool = Field(default=False)
    ats_optimization_applied: bool = Field(default=False)
    content_enhancement_applied: bool = Field(default=False)
    personalization_applied: bool = Field(default=False)


class PersonalizationAnalysisRequest(BaseModel):
    """Request model for personalization analysis."""
    analysis_period_days: int = Field(default=365, ge=30, le=1095, description="Analysis period in days")
    force_reanalysis: bool = Field(default=False, description="Force fresh analysis")
    include_market_intelligence: bool = Field(default=True, description="Include market trends")


class PersonalizedOptimizationRequest(BaseModel):
    """Request model for personalized optimization."""
    job_description: str = Field(..., min_length=50, max_length=10000)
    company_name: Optional[str] = Field(None, max_length=255)
    position_title: Optional[str] = Field(None, max_length=255)
    use_cached_analysis: bool = Field(default=True, description="Use cached personalization analysis")


class MarketIntelligenceRequest(BaseModel):
    """Request model for market intelligence."""
    industry: str = Field(..., max_length=100)
    job_level: str = Field(..., description="Job level: entry, mid, senior, executive")
    location: Optional[str] = Field(None, max_length=255)
    include_ai_insights: bool = Field(default=True)


class UserSuccessPatternResponse(BaseModel):
    """Response model for user success patterns."""
    user_profile_id: str
    successful_achievement_types: List[str]
    effective_keywords: List[str]
    optimal_enhancement_level: str
    best_performing_industries: List[str]
    preferred_content_length: str
    success_rate: float
    confidence_level: str
    sample_size: int


class PersonalizationInsightResponse(BaseModel):
    """Response model for personalization insights."""
    insight_type: str
    recommendation: str
    confidence_score: float
    supporting_evidence: List[str]
    expected_improvement: float
    user_profile_id: str


class PersonalizationAnalysisResponse(BaseModel):
    """Response model for personalization analysis."""
    success: bool
    user_profile_id: str
    analysis_date: datetime
    next_analysis_date: datetime
    
    # Analysis results
    success_patterns: UserSuccessPatternResponse
    insights: List[PersonalizationInsightResponse]
    personalized_strategy: str
    recommended_actions: List[str]
    
    # Performance predictions
    predicted_improvement: float
    confidence_score: float
    
    # AI metadata
    ai_reasoning: Optional[str] = None
    processing_time: Optional[float] = None


class ApplicationOutcomeResponse(BaseModel):
    """Response model for application outcome tracking."""
    success: bool
    outcome_tracked: bool
    outcome_type: str
    user_profile_id: str
    trigger_reanalysis: bool
    analysis_scheduled: bool
    next_analysis_date: Optional[datetime] = None


class PersonalizedOptimizationResponse(BaseModel):
    """Response model for personalized optimization."""
    success: bool
    user_profile_id: str
    personalization_strategy: str
    content_selection: Dict[str, Any]
    ats_optimization: Dict[str, Any]
    content_enhancement: Dict[str, Any]
    insights_applied: List[str]
    predicted_improvement: float
    confidence_score: float


class MarketIntelligenceResponse(BaseModel):
    """Response model for market intelligence."""
    success: bool
    industry: str
    job_level: str
    location: Optional[str]
    trending_keywords: List[str]
    salary_trends: Dict[str, Any]
    successful_patterns: Dict[str, Any]
    ai_insights: Optional[Dict[str, Any]]
    analysis_date: str


@router.post("/track-outcome", response_model=ApplicationOutcomeResponse)
async def track_application_outcome(
    request: ApplicationOutcomeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(auth_deps.get_current_user)
) -> ApplicationOutcomeResponse:
    """
    Track application outcome for learning and personalization improvement.
    
    This endpoint records job application outcomes to enable the system to learn
    which content selection, ATS optimization, and enhancement strategies work best
    for each user. The data is used to improve future recommendations.
    
    **Features:**
    - Tracks detailed application outcomes
    - Links outcomes to specific optimization strategies used
    - Triggers personalization re-analysis when sufficient new data
    - Enables continuous learning and improvement
    
    **Outcome Types:**
    - application_sent: Application was submitted
    - viewed: Application was viewed by recruiter
    - phone_screen: Phone screening scheduled/completed
    - interview: Interview scheduled/completed
    - offer: Job offer received
    - rejection: Application rejected
    - no_response: No response after reasonable time
    """
    try:
        logger.info(f"Tracking application outcome: {request.outcome_type} for user {current_user.profile.id}")
        
        # Validate outcome type
        try:
            outcome_type = OutcomeType(request.outcome_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid outcome type. Must be one of: {[ot.value for ot in OutcomeType]}"
            )
        
        # Create application outcome data
        outcome_data = ApplicationOutcomeData(
            application_id=request.application_id,
            user_profile_id=str(current_user.profile.id),
            company_name=request.company_name,
            position_title=request.position_title,
            job_description=request.job_description or "",
            content_selection_id=request.content_selection_id,
            outcome_type=outcome_type,
            outcome_date=request.outcome_date,
            feedback_notes=request.feedback_notes,
            salary_offered=request.salary_offered,
            days_to_outcome=request.days_to_outcome
        )
        
        # Track the outcome
        result = await personalization_engine.track_application_outcome(outcome_data)
        
        # Schedule background re-analysis if needed
        if result["trigger_reanalysis"]:
            background_tasks.add_task(
                _background_reanalysis,
                str(current_user.profile.id)
            )
        
        response = ApplicationOutcomeResponse(
            success=result["success"],
            outcome_tracked=result["outcome_tracked"],
            outcome_type=result["outcome_type"],
            user_profile_id=result["user_profile_id"],
            trigger_reanalysis=result["trigger_reanalysis"],
            analysis_scheduled=result["analysis_scheduled"],
            next_analysis_date=result.get("next_analysis_date")
        )
        
        logger.info(f"Application outcome tracked successfully. Reanalysis triggered: {response.trigger_reanalysis}")
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to track application outcome: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to track application outcome: {str(e)}"
        )


@router.post("/analyze-performance", response_model=PersonalizationAnalysisResponse)
async def analyze_user_performance(
    request: PersonalizationAnalysisRequest,
    current_user: User = Depends(auth_deps.get_current_user)
) -> PersonalizationAnalysisResponse:
    """
    Analyze user's application performance and generate personalization insights.
    
    This endpoint performs comprehensive analysis of the user's application history
    to identify successful patterns and generate personalized recommendations for
    improving future application outcomes.
    
    **Analysis Includes:**
    - Success pattern identification
    - Content selection optimization
    - Enhancement level recommendations
    - Industry-specific insights
    - Keyword strategy optimization
    
    **Learning Confidence Levels:**
    - Low: < 5 data points (basic recommendations)
    - Medium: 5-15 data points (reliable patterns)
    - High: 15+ data points (strong statistical confidence)
    """
    try:
        logger.info(f"Starting personalization analysis for user {current_user.profile.id}")
        
        # Perform personalization analysis
        start_time = datetime.utcnow()
        result = await personalization_engine.analyze_user_performance(
            user_profile_id=str(current_user.profile.id),
            analysis_period_days=request.analysis_period_days
        )
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Convert to response format
        success_patterns = UserSuccessPatternResponse(
            user_profile_id=result.success_patterns.user_profile_id,
            successful_achievement_types=result.success_patterns.successful_achievement_types,
            effective_keywords=result.success_patterns.effective_keywords,
            optimal_enhancement_level=result.success_patterns.optimal_enhancement_level,
            best_performing_industries=result.success_patterns.best_performing_industries,
            preferred_content_length=result.success_patterns.preferred_content_length,
            success_rate=result.success_patterns.success_rate,
            confidence_level=result.success_patterns.confidence_level.value,
            sample_size=result.success_patterns.sample_size
        )
        
        insights = [
            PersonalizationInsightResponse(
                insight_type=insight.insight_type,
                recommendation=insight.recommendation,
                confidence_score=insight.confidence_score,
                supporting_evidence=insight.supporting_evidence,
                expected_improvement=insight.expected_improvement,
                user_profile_id=insight.user_profile_id
            ) for insight in result.insights
        ]
        
        response = PersonalizationAnalysisResponse(
            success=True,
            user_profile_id=result.user_profile_id,
            analysis_date=result.analysis_date,
            next_analysis_date=result.next_analysis_date,
            success_patterns=success_patterns,
            insights=insights,
            personalized_strategy=result.personalized_strategy.value,
            recommended_actions=result.recommended_actions,
            predicted_improvement=result.predicted_improvement,
            confidence_score=result.confidence_score,
            ai_reasoning=result.ai_reasoning,
            processing_time=processing_time
        )
        
        logger.info(f"Personalization analysis completed. Strategy: {response.personalized_strategy}, "
                   f"Confidence: {response.confidence_score:.2f}, "
                   f"Predicted improvement: {response.predicted_improvement:.2f}")
        
        return response
        
    except Exception as e:
        logger.error(f"Personalization analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Personalization analysis failed: {str(e)}"
        )


@router.post("/optimize", response_model=PersonalizedOptimizationResponse)
async def apply_personalized_optimization(
    request: PersonalizedOptimizationRequest,
    current_user: User = Depends(auth_deps.get_current_user)
) -> PersonalizedOptimizationResponse:
    """
    Apply personalized optimization to content selection and enhancement.
    
    This endpoint uses the user's personalization insights to optimize resume
    content selection, ATS compatibility, and content enhancement specifically
    for their success patterns and the target job requirements.
    
    **Personalization Features:**
    - Tailored content selection based on user's successful patterns
    - Customized keyword strategies from user's effective keywords
    - Optimized enhancement levels based on user's preferences
    - Industry-specific recommendations from user's performance history
    """
    try:
        logger.info(f"Applying personalized optimization for user {current_user.profile.id}")
        
        # Analyze job description
        job_analysis = await job_analyzer.analyze_job_description(
            job_description=request.job_description,
            company_name=request.company_name or "Unknown",
            position_title=request.position_title or "Unknown Position"
        )
        
        # Apply personalized optimization
        result = await personalization_engine.apply_personalized_optimization(
            user_profile_id=str(current_user.profile.id),
            job_analysis=job_analysis,
            personalization_result=None  # Will analyze if needed
        )
        
        response = PersonalizedOptimizationResponse(
            success=result["success"],
            user_profile_id=result["user_profile_id"],
            personalization_strategy=result["personalization_strategy"],
            content_selection=result["content_selection"],
            ats_optimization=result["ats_optimization"],
            content_enhancement=result["content_enhancement"],
            insights_applied=result["insights_applied"],
            predicted_improvement=result["predicted_improvement"],
            confidence_score=result["confidence_score"]
        )
        
        logger.info(f"Personalized optimization applied. Strategy: {response.personalization_strategy}, "
                   f"Insights applied: {len(response.insights_applied)}")
        
        return response
        
    except Exception as e:
        logger.error(f"Personalized optimization failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Personalized optimization failed: {str(e)}"
        )


@router.get("/market-intelligence", response_model=MarketIntelligenceResponse)
async def get_market_intelligence(
    request: MarketIntelligenceRequest = Depends(),
    current_user: User = Depends(auth_deps.get_current_user)
) -> MarketIntelligenceResponse:
    """
    Get market intelligence for industry and role trends.
    
    This endpoint provides real-time market insights including trending keywords,
    salary information, successful content patterns, and AI-powered market analysis
    for specific industries and job levels.
    
    **Intelligence Sources:**
    - User application outcome data
    - Successful resume patterns
    - AI-powered trend analysis
    - Industry-specific optimization strategies
    
    **Job Levels:**
    - entry: Entry-level positions
    - mid: Mid-level positions  
    - senior: Senior-level positions
    - executive: Executive-level positions
    """
    try:
        logger.info(f"Retrieving market intelligence for {request.industry} - {request.job_level}")
        
        # Validate job level
        valid_levels = ["entry", "mid", "senior", "executive"]
        if request.job_level not in valid_levels:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid job level. Must be one of: {valid_levels}"
            )
        
        # Get market intelligence
        result = await personalization_engine.get_market_intelligence(
            industry=request.industry,
            job_level=request.job_level,
            location=request.location
        )
        
        response = MarketIntelligenceResponse(
            success=result["success"],
            industry=result["industry"],
            job_level=result["job_level"],
            location=result["location"],
            trending_keywords=result["trending_keywords"],
            salary_trends=result["salary_trends"],
            successful_patterns=result["successful_patterns"],
            ai_insights=result["ai_insights"],
            analysis_date=result["analysis_date"]
        )
        
        logger.info(f"Market intelligence retrieved. Keywords: {len(response.trending_keywords)}, "
                   f"AI insights: {'Yes' if response.ai_insights else 'No'}")
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to get market intelligence: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get market intelligence: {str(e)}"
        )


@router.get("/insights")
async def get_user_insights(
    limit: int = Query(10, ge=1, le=50),
    insight_type: Optional[str] = Query(None),
    status: str = Query("active"),
    current_user: User = Depends(auth_deps.get_current_user)
) -> Dict[str, Any]:
    """
    Get user's personalization insights and recommendations.
    
    Returns the user's current personalization insights, including achievement
    selection strategies, keyword optimization recommendations, and enhancement
    level suggestions based on their application history and success patterns.
    """
    try:
        # In a full implementation, this would query the database
        # For now, return a sample response
        
        return {
            "success": True,
            "user_profile_id": str(current_user.profile.id),
            "insights": [],
            "total_count": 0,
            "limit": limit,
            "insight_type": insight_type,
            "status": status
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve user insights: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve user insights: {str(e)}"
        )


@router.get("/performance-metrics")
async def get_performance_metrics(
    period_days: int = Query(90, ge=30, le=365),
    current_user: User = Depends(auth_deps.get_current_user)
) -> Dict[str, Any]:
    """
    Get user's performance metrics and trends.
    
    Returns comprehensive performance analytics including application success rates,
    response times, most effective strategies, and improvement trends over time.
    """
    try:
        # In a full implementation, this would query the database and calculate metrics
        # For now, return a sample response
        
        return {
            "success": True,
            "user_profile_id": str(current_user.profile.id),
            "period_days": period_days,
            "metrics": {
                "total_applications": 0,
                "success_rate": 0.0,
                "average_response_time_days": 0,
                "interview_rate": 0.0,
                "offer_rate": 0.0,
                "most_effective_strategies": [],
                "improvement_trend": "stable"
            },
            "analysis_date": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve performance metrics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve performance metrics: {str(e)}"
        )


@router.get("/status")
async def get_personalization_service_status(
    current_user: User = Depends(auth_deps.get_current_user)
) -> Dict[str, Any]:
    """
    Get current status of personalization and learning services.
    
    Returns information about service availability, configuration, learning
    progress, and current performance metrics for the personalization system.
    """
    try:
        status = {
            "personalization_enabled": settings.enable_ai_personalization,
            "fallback_enabled": settings.personalization_fallback_enabled,
            "confidence_threshold": settings.personalization_confidence_threshold,
            "min_data_points": settings.personalization_min_data_points,
            "learning_window_days": settings.personalization_learning_window_days,
            "ai_learning_available": personalization_engine.use_ai_learning
        }
        
        if personalization_engine.gemini_client:
            gemini_status = personalization_engine.gemini_client.get_usage_stats()
            status["gemini"] = {
                "available": personalization_engine.gemini_client.is_available(),
                "usage_stats": gemini_status
            }
        else:
            status["gemini"] = {
                "available": False,
                "reason": "Gemini client not initialized or disabled"
            }
        
        # Service capabilities
        status["capabilities"] = {
            "learning_confidence_levels": [l.value for l in LearningConfidence],
            "personalization_strategies": [s.value for s in PersonalizationStrategy],
            "outcome_types": [ot.value for ot in OutcomeType],
            "features": [
                "application_outcome_tracking",
                "success_pattern_analysis",
                "personalized_optimization",
                "market_intelligence",
                "continuous_learning",
                "ab_testing_framework"
            ]
        }
        
        # A/B testing status
        status["ab_testing"] = {
            "enabled": settings.enable_ab_testing,
            "default_duration_days": settings.ab_test_default_duration_days,
            "min_sample_size": settings.ab_test_min_sample_size,
            "confidence_level": settings.ab_test_confidence_level
        }
        
        # Market intelligence status
        status["market_intelligence"] = {
            "enabled": settings.enable_market_intelligence,
            "refresh_hours": settings.market_intelligence_refresh_hours,
            "data_sources": settings.market_intelligence_data_sources
        }
        
        return {
            "success": True,
            "status": status
        }
        
    except Exception as e:
        logger.error(f"Failed to get personalization service status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get personalization service status: {str(e)}"
        )


async def _background_reanalysis(user_profile_id: str):
    """Background task for user personalization re-analysis."""
    try:
        logger.info(f"Starting background personalization re-analysis for user {user_profile_id}")
        
        result = await personalization_engine.analyze_user_performance(user_profile_id)
        
        logger.info(f"Background re-analysis completed for user {user_profile_id}. "
                   f"Strategy: {result.personalized_strategy}, "
                   f"Confidence: {result.confidence_score:.2f}")
        
    except Exception as e:
        logger.error(f"Background re-analysis failed for user {user_profile_id}: {e}")