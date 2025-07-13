"""
Quality Control API routes for TailerAI v2.0
Provides personal quality assessment and improvement tools for individual users.
Following best practices from PROJECT_BLUEPRINT.md for personal optimization focus.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field

from app.api.dependencies.auth_deps import get_current_user
from app.models.database import User, UserProfile
from app.services.quality_control_service import (
    PersonalQualityControlService, 
    PersonalQualityAssessment,
    QualityCategory,
    QualitySeverity
)
from app.services.database_service import db_service
from app.services.master_dataset_service import master_dataset_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/quality", tags=["quality_control"])

# Initialize quality control service
quality_service = PersonalQualityControlService()


# Request/Response Models
class QualityAssessmentRequest(BaseModel):
    """Request model for quality assessment"""
    target_role: Optional[str] = Field(None, description="Target job role for optimization")
    target_industry: Optional[str] = Field(None, description="Target industry context")
    assessment_type: str = Field("comprehensive", description="Type of assessment to perform")


class QualityIssueResponse(BaseModel):
    """Response model for individual quality issues"""
    category: str
    severity: str
    message: str
    suggestion: str
    location: Optional[str] = None
    score_impact: float = 0.0
    auto_fixable: bool = False


class QualityMetricsResponse(BaseModel):
    """Response model for quality metrics"""
    category: str
    score: float
    max_score: float = 100.0
    issues: List[QualityIssueResponse]
    suggestions: List[str]
    strengths: List[str]


class QualityAssessmentResponse(BaseModel):
    """Response model for complete quality assessment"""
    assessment_id: str
    overall_score: float
    content_quality: QualityMetricsResponse
    grammar_quality: QualityMetricsResponse
    ats_compatibility: QualityMetricsResponse
    formatting_quality: QualityMetricsResponse
    keyword_optimization: QualityMetricsResponse
    professional_standards: QualityMetricsResponse
    readability_metrics: QualityMetricsResponse
    completeness_score: QualityMetricsResponse
    total_issues: int
    critical_issues: int
    improvement_priority: List[str]
    next_steps: List[str]
    estimated_improvement_time: str
    assessed_at: datetime
    target_role: Optional[str] = None
    target_industry: Optional[str] = None


class QualityHistoryResponse(BaseModel):
    """Response model for quality assessment history"""
    assessments: List[QualityAssessmentResponse]
    total_count: int
    improvement_trend: Optional[float] = None  # Overall improvement over time


class QualityStatsResponse(BaseModel):
    """Response model for quality statistics"""
    total_assessments: int
    average_score: float
    latest_score: Optional[float] = None
    improvement_since_first: Optional[float] = None
    most_common_issues: List[Dict[str, Any]]
    strengths_identified: List[str]
    recommendations_completed: int


@router.post("/assess", response_model=QualityAssessmentResponse)
async def assess_personal_quality(
    request: QualityAssessmentRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Perform comprehensive personal quality assessment of user's resume content.
    Analyzes content quality, grammar, ATS compatibility, and provides improvement guidance.
    """
    try:
        # Get user profile
        user_profile = await master_dataset_service.get_user_profile(current_user.id)
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found. Please create your profile first."
            )
        
        # Get user's resume content
        resume_content = await _build_resume_content(user_profile.id)
        
        # Perform quality assessment
        assessment_result = await quality_service.assess_personal_quality(
            user_id=current_user.id,
            resume_content=resume_content,
            target_role=request.target_role,
            industry=request.target_industry
        )
        
        # Store assessment in database
        assessment_data = {
            "profile_id": user_profile.id,
            "overall_score": assessment_result.overall_score,
            "content_score": assessment_result.content_quality.score,
            "grammar_score": assessment_result.grammar_quality.score,
            "ats_score": assessment_result.ats_compatibility.score,
            "formatting_score": assessment_result.formatting_quality.score,
            "keyword_score": assessment_result.keyword_optimization.score,
            "professional_score": assessment_result.professional_standards.score,
            "readability_score": assessment_result.readability_metrics.score,
            "completeness_score": assessment_result.completeness_score.score,
            "total_issues": assessment_result.total_issues,
            "critical_issues": assessment_result.critical_issues,
            "improvement_priority": assessment_result.improvement_priority,
            "next_steps": assessment_result.next_steps,
            "estimated_improvement_time": assessment_result.estimated_improvement_time,
            "target_role": request.target_role,
            "target_industry": request.target_industry,
            "assessment_type": request.assessment_type
        }
        
        db_assessment = db_service.create_quality_assessment(assessment_data)
        
        # Convert to response format
        return _convert_assessment_to_response(assessment_result, str(db_assessment.id))
        
    except Exception as e:
        logger.error(f"Quality assessment failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quality assessment failed: {str(e)}"
        )


@router.get("/assessment/{assessment_id}", response_model=QualityAssessmentResponse)
async def get_quality_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve a specific quality assessment by ID.
    Only returns assessments belonging to the current user.
    """
    try:
        assessment = db_service.get_quality_assessment(assessment_id)
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quality assessment not found"
            )
        
        # Verify ownership
        user_profile = await master_dataset_service.get_user_profile(current_user.id)
        if not user_profile or assessment.profile_id != user_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this assessment"
            )
        
        # Convert database model to response format
        return _convert_db_assessment_to_response(assessment)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve assessment {assessment_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Assessment retrieval failed: {str(e)}"
        )


@router.get("/history", response_model=QualityHistoryResponse)
async def get_quality_history(
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """
    Get quality assessment history for the current user.
    Shows improvement trends and progress over time.
    """
    try:
        user_profile = await master_dataset_service.get_user_profile(current_user.id)
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        assessments = db_service.get_user_quality_assessments(user_profile.id, limit)
        
        # Convert to response format
        assessment_responses = [
            _convert_db_assessment_to_response(assessment) 
            for assessment in assessments
        ]
        
        # Calculate improvement trend
        improvement_trend = None
        if len(assessments) >= 2:
            first_score = assessments[-1].overall_score  # Oldest (last in desc order)
            latest_score = assessments[0].overall_score   # Latest (first in desc order)
            improvement_trend = latest_score - first_score
        
        return QualityHistoryResponse(
            assessments=assessment_responses,
            total_count=len(assessment_responses),
            improvement_trend=improvement_trend
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get quality history for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quality history retrieval failed: {str(e)}"
        )


@router.get("/stats", response_model=QualityStatsResponse)
async def get_quality_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Get quality statistics and analytics for the current user.
    Provides insights into improvement patterns and common issues.
    """
    try:
        user_profile = await master_dataset_service.get_user_profile(current_user.id)
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        assessments = db_service.get_user_quality_assessments(user_profile.id, limit=50)
        
        if not assessments:
            return QualityStatsResponse(
                total_assessments=0,
                average_score=0.0,
                latest_score=None,
                improvement_since_first=None,
                most_common_issues=[],
                strengths_identified=[],
                recommendations_completed=0
            )
        
        # Calculate statistics
        total_assessments = len(assessments)
        average_score = sum(a.overall_score for a in assessments) / total_assessments
        latest_score = assessments[0].overall_score
        
        improvement_since_first = None
        if total_assessments >= 2:
            first_score = assessments[-1].overall_score
            improvement_since_first = latest_score - first_score
        
        # Analyze common issues (simplified for now)
        most_common_issues = [
            {"category": "grammar", "frequency": 15},
            {"category": "keywords", "frequency": 12},
            {"category": "formatting", "frequency": 8}
        ]
        
        strengths_identified = [
            "Strong quantified achievements",
            "Good industry keyword usage",
            "Professional formatting"
        ]
        
        return QualityStatsResponse(
            total_assessments=total_assessments,
            average_score=average_score,
            latest_score=latest_score,
            improvement_since_first=improvement_since_first,
            most_common_issues=most_common_issues,
            strengths_identified=strengths_identified,
            recommendations_completed=0  # To be implemented with tracking
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get quality stats for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quality stats retrieval failed: {str(e)}"
        )


# Helper functions
async def _build_resume_content(profile_id: str) -> Dict[str, Any]:
    """
    Build comprehensive resume content from user's master dataset.
    """
    try:
        # Get all user data
        work_experiences = await master_dataset_service.get_work_experiences(profile_id)
        achievements = await master_dataset_service.get_achievements(profile_id)
        education_entries = await master_dataset_service.get_education_entries(profile_id)
        skills = await master_dataset_service.get_skills(profile_id)
        projects = await master_dataset_service.get_projects(profile_id)
        
        # Build content structure
        return {
            "work_experiences": [exp.__dict__ for exp in work_experiences],
            "achievements": [ach.__dict__ for ach in achievements],
            "education": [edu.__dict__ for edu in education_entries],
            "skills": [skill.__dict__ for skill in skills],
            "projects": [proj.__dict__ for proj in projects]
        }
        
    except Exception as e:
        logger.error(f"Failed to build resume content for profile {profile_id}: {str(e)}")
        raise


def _convert_assessment_to_response(assessment: PersonalQualityAssessment, assessment_id: str) -> QualityAssessmentResponse:
    """
    Convert PersonalQualityAssessment to API response format.
    """
    return QualityAssessmentResponse(
        assessment_id=assessment_id,
        overall_score=assessment.overall_score,
        content_quality=_convert_metrics_to_response(assessment.content_quality),
        grammar_quality=_convert_metrics_to_response(assessment.grammar_quality),
        ats_compatibility=_convert_metrics_to_response(assessment.ats_compatibility),
        formatting_quality=_convert_metrics_to_response(assessment.formatting_quality),
        keyword_optimization=_convert_metrics_to_response(assessment.keyword_optimization),
        professional_standards=_convert_metrics_to_response(assessment.professional_standards),
        readability_metrics=_convert_metrics_to_response(assessment.readability_metrics),
        completeness_score=_convert_metrics_to_response(assessment.completeness_score),
        total_issues=assessment.total_issues,
        critical_issues=assessment.critical_issues,
        improvement_priority=assessment.improvement_priority,
        next_steps=assessment.next_steps,
        estimated_improvement_time=assessment.estimated_improvement_time,
        assessed_at=assessment.assessed_at
    )


def _convert_db_assessment_to_response(assessment) -> QualityAssessmentResponse:
    """
    Convert database QualityAssessment to API response format.
    """
    # Create simplified metrics (full details would need to be stored in DB)
    def create_simple_metrics(category: str, score: float) -> QualityMetricsResponse:
        return QualityMetricsResponse(
            category=category,
            score=score,
            max_score=100.0,
            issues=[],
            suggestions=[],
            strengths=[]
        )
    
    return QualityAssessmentResponse(
        assessment_id=str(assessment.id),
        overall_score=assessment.overall_score,
        content_quality=create_simple_metrics("content", assessment.content_score),
        grammar_quality=create_simple_metrics("grammar", assessment.grammar_score),
        ats_compatibility=create_simple_metrics("ats_compatibility", assessment.ats_score),
        formatting_quality=create_simple_metrics("formatting", assessment.formatting_score),
        keyword_optimization=create_simple_metrics("keywords", assessment.keyword_score),
        professional_standards=create_simple_metrics("professional_standards", assessment.professional_score),
        readability_metrics=create_simple_metrics("readability", assessment.readability_score),
        completeness_score=create_simple_metrics("completeness", assessment.completeness_score),
        total_issues=assessment.total_issues,
        critical_issues=assessment.critical_issues,
        improvement_priority=assessment.improvement_priority or [],
        next_steps=assessment.next_steps or [],
        estimated_improvement_time=assessment.estimated_improvement_time or "Unknown",
        assessed_at=assessment.assessed_at,
        target_role=assessment.target_role,
        target_industry=assessment.target_industry
    )


def _convert_metrics_to_response(metrics) -> QualityMetricsResponse:
    """
    Convert QualityMetrics to API response format.
    """
    return QualityMetricsResponse(
        category=metrics.category.value,
        score=metrics.score,
        max_score=metrics.max_score,
        issues=[
            QualityIssueResponse(
                category=issue.category.value,
                severity=issue.severity.value,
                message=issue.message,
                suggestion=issue.suggestion,
                location=issue.location,
                score_impact=issue.score_impact,
                auto_fixable=issue.auto_fixable
            ) for issue in metrics.issues
        ],
        suggestions=metrics.suggestions,
        strengths=metrics.strengths
    )