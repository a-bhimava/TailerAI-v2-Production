"""
API routes for ATS Optimization Engine.
Phase 2 implementation of comprehensive ATS compatibility optimization.
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.models.database import User
from app.api.dependencies import auth_deps
from app.services.ats_optimization_engine import (
    ATSOptimizationEngine,
    ATSSystem,
    CompatibilityLevel,
    ATSOptimizationResult
)
from app.services.ai_content_selection_service import ai_content_selector
from app.services.job_analysis_service import job_analyzer
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/v2/ats", tags=["ATS Optimization"])

# Initialize ATS optimization engine
ats_optimizer = ATSOptimizationEngine()


class ATSOptimizationRequest(BaseModel):
    """Request model for ATS optimization."""
    content_selection_id: str = Field(..., description="ID of content selection to optimize")
    target_ats_systems: Optional[List[str]] = Field(
        default=None,
        description="Target ATS systems (taleo, workday, adp, greenhouse, etc.)"
    )
    job_description: Optional[str] = Field(
        default=None,
        min_length=50,
        max_length=10000,
        description="Job description for context (optional)"
    )
    company_name: Optional[str] = Field(None, max_length=255)
    position_title: Optional[str] = Field(None, max_length=255)


class QuickATSAnalysisRequest(BaseModel):
    """Request model for quick ATS analysis without content selection."""
    job_description: str = Field(..., min_length=50, max_length=10000)
    company_name: Optional[str] = Field(None, max_length=255)
    position_title: Optional[str] = Field(None, max_length=255)
    target_ats_systems: Optional[List[str]] = Field(default=None)


class KeywordOptimizationResponse(BaseModel):
    """Response model for keyword optimization recommendations."""
    keyword: str
    current_density: float
    target_density: float
    integration_strategy: str
    priority: str
    suggested_contexts: List[str]
    authenticity_score: float


class ATSIssueResponse(BaseModel):
    """Response model for ATS compatibility issues."""
    issue_type: str
    severity: str
    description: str
    affected_sections: List[str]
    fix_strategy: str
    estimated_impact: str


class ATSOptimizationResponse(BaseModel):
    """Response model for ATS optimization results."""
    success: bool
    optimization_id: str
    content_selection_id: str
    
    # Overall compatibility
    overall_compatibility_score: float
    compatibility_level: str
    
    # System-specific scores
    system_compatibility_scores: Dict[str, float]
    
    # Keyword optimization
    keyword_optimizations: List[KeywordOptimizationResponse]
    current_keyword_density: float
    target_keyword_density: float
    keyword_distribution_score: float
    
    # Issues and recommendations
    compatibility_issues: List[ATSIssueResponse]
    priority_fixes: List[str]
    
    # Optimization metadata
    optimization_strategy: Dict[str, Any]
    estimated_improvement: float
    processing_time: Optional[float] = None
    
    # AI metadata
    ai_reasoning: Optional[str] = None
    ai_confidence_score: Optional[float] = None
    fallback_applied: bool = False


class ATSSystemInfoResponse(BaseModel):
    """Response model for ATS system information."""
    system_name: str
    configuration: Dict[str, Any]
    optimization_tips: List[str]
    common_issues: List[str]


@router.post("/optimize", response_model=ATSOptimizationResponse)
async def optimize_content_for_ats(
    request: ATSOptimizationRequest,
    current_user: User = Depends(auth_deps.get_current_user)
) -> ATSOptimizationResponse:
    """
    Optimize selected content for ATS compatibility.
    
    This endpoint analyzes content selection results and provides comprehensive
    optimization recommendations for multiple ATS systems.
    
    **Features:**
    - Multi-ATS system compatibility analysis
    - AI-powered keyword optimization strategies
    - Format and structure recommendations
    - Priority-based fix suggestions
    - Authenticity-preserving optimizations
    
    **Supported ATS Systems:**
    - Taleo, Workday, ADP, Greenhouse, Lever
    - BambooHR, SmartRecruiters, Cornerstone, iCIMS
    - Generic (fallback for unknown systems)
    """
    try:
        logger.info(f"Starting ATS optimization for content {request.content_selection_id}")
        
        # Parse target ATS systems
        target_systems = []
        if request.target_ats_systems:
            for sys_name in request.target_ats_systems:
                try:
                    ats_system = ATSSystem(sys_name.lower())
                    target_systems.append(ats_system)
                except ValueError:
                    logger.warning(f"Unknown ATS system: {sys_name}, using generic")
                    target_systems.append(ATSSystem.GENERIC)
        else:
            # Use default systems from configuration
            default_systems = settings.ats_default_target_systems.split(",")
            target_systems = [ATSSystem(sys.strip()) for sys in default_systems]
        
        # Analyze job description if provided
        job_analysis = None
        if request.job_description:
            logger.info("Analyzing job description for ATS optimization context")
            job_analysis = await job_analyzer.analyze_job_description(
                job_description=request.job_description,
                company_name=request.company_name or "Unknown",
                position_title=request.position_title or "Unknown Position"
            )
        
        # Perform ATS optimization
        result = await ats_optimizer.optimize_content_for_ats(
            content_selection_id=request.content_selection_id,
            target_ats_systems=target_systems,
            job_analysis=job_analysis
        )
        
        # Convert to response format
        response = ATSOptimizationResponse(
            success=True,
            optimization_id=f"ats_opt_{result.content_selection_id}",
            content_selection_id=result.content_selection_id,
            overall_compatibility_score=result.overall_compatibility_score,
            compatibility_level=result.compatibility_level.value,
            system_compatibility_scores={
                k.value: v for k, v in result.system_compatibility_scores.items()
            },
            keyword_optimizations=[
                KeywordOptimizationResponse(
                    keyword=opt.keyword,
                    current_density=opt.current_density,
                    target_density=opt.target_density,
                    integration_strategy=opt.integration_strategy,
                    priority=opt.priority,
                    suggested_contexts=opt.suggested_contexts,
                    authenticity_score=opt.authenticity_score
                ) for opt in result.keyword_optimizations
            ],
            current_keyword_density=result.current_keyword_density,
            target_keyword_density=result.target_keyword_density,
            keyword_distribution_score=result.keyword_distribution_score,
            compatibility_issues=[
                ATSIssueResponse(
                    issue_type=issue.issue_type,
                    severity=issue.severity,
                    description=issue.description,
                    affected_sections=issue.affected_sections,
                    fix_strategy=issue.fix_strategy,
                    estimated_impact=issue.estimated_impact
                ) for issue in result.compatibility_issues
            ],
            priority_fixes=result.priority_fixes,
            optimization_strategy=result.optimization_strategy,
            estimated_improvement=result.estimated_improvement,
            processing_time=result.processing_time,
            ai_reasoning=result.ai_reasoning,
            ai_confidence_score=result.ai_confidence_score,
            fallback_applied=result.fallback_applied
        )
        
        logger.info(f"ATS optimization completed. Overall score: {response.overall_compatibility_score:.2f}, "
                   f"Level: {response.compatibility_level}, "
                   f"Issues: {len(response.compatibility_issues)}")
        
        return response
        
    except Exception as e:
        logger.error(f"ATS optimization failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"ATS optimization failed: {str(e)}"
        )


@router.post("/analyze", response_model=ATSOptimizationResponse)
async def quick_ats_analysis(
    request: QuickATSAnalysisRequest,
    current_user: User = Depends(auth_deps.get_current_user)
) -> ATSOptimizationResponse:
    """
    Perform quick ATS analysis without content selection.
    
    This endpoint provides a fast ATS compatibility assessment based on
    job description requirements without requiring existing content selection.
    Useful for initial job posting analysis and ATS requirements discovery.
    """
    try:
        logger.info("Performing quick ATS analysis")
        
        # First, perform content selection to get baseline content
        job_analysis = await job_analyzer.analyze_job_description(
            job_description=request.job_description,
            company_name=request.company_name or "Unknown",
            position_title=request.position_title or "Unknown Position"
        )
        
        if not job_analysis:
            raise HTTPException(
                status_code=400,
                detail="Failed to analyze job description"
            )
        
        # Perform content selection to get something to optimize
        content_selection = await ai_content_selector.select_optimal_content(
            user_profile_id=str(current_user.profile.id),
            job_analysis=job_analysis
        )
        
        # Parse target ATS systems
        target_systems = []
        if request.target_ats_systems:
            for sys_name in request.target_ats_systems:
                try:
                    ats_system = ATSSystem(sys_name.lower())
                    target_systems.append(ats_system)
                except ValueError:
                    target_systems.append(ATSSystem.GENERIC)
        else:
            target_systems = [ATSSystem.TALEO, ATSSystem.WORKDAY, ATSSystem.GENERIC]
        
        # Perform ATS optimization on selected content
        result = await ats_optimizer.optimize_content_for_ats(
            content_selection_id=content_selection.job_analysis_id,
            target_ats_systems=target_systems,
            job_analysis=job_analysis
        )
        
        # Convert to response format (same as optimize endpoint)
        response = ATSOptimizationResponse(
            success=True,
            optimization_id=f"quick_ats_{result.content_selection_id}",
            content_selection_id=result.content_selection_id,
            overall_compatibility_score=result.overall_compatibility_score,
            compatibility_level=result.compatibility_level.value,
            system_compatibility_scores={
                k.value: v for k, v in result.system_compatibility_scores.items()
            },
            keyword_optimizations=[
                KeywordOptimizationResponse(
                    keyword=opt.keyword,
                    current_density=opt.current_density,
                    target_density=opt.target_density,
                    integration_strategy=opt.integration_strategy,
                    priority=opt.priority,
                    suggested_contexts=opt.suggested_contexts,
                    authenticity_score=opt.authenticity_score
                ) for opt in result.keyword_optimizations
            ],
            current_keyword_density=result.current_keyword_density,
            target_keyword_density=result.target_keyword_density,
            keyword_distribution_score=result.keyword_distribution_score,
            compatibility_issues=[
                ATSIssueResponse(
                    issue_type=issue.issue_type,
                    severity=issue.severity,
                    description=issue.description,
                    affected_sections=issue.affected_sections,
                    fix_strategy=issue.fix_strategy,
                    estimated_impact=issue.estimated_impact
                ) for issue in result.compatibility_issues
            ],
            priority_fixes=result.priority_fixes,
            optimization_strategy=result.optimization_strategy,
            estimated_improvement=result.estimated_improvement,
            processing_time=result.processing_time,
            ai_reasoning=result.ai_reasoning,
            ai_confidence_score=result.ai_confidence_score,
            fallback_applied=result.fallback_applied
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quick ATS analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Quick ATS analysis failed: {str(e)}"
        )


@router.get("/systems")
async def get_supported_ats_systems(
    current_user: User = Depends(auth_deps.get_current_user)
) -> Dict[str, Any]:
    """
    Get information about supported ATS systems.
    
    Returns comprehensive information about each supported ATS system,
    including optimization strategies, requirements, and common issues.
    """
    try:
        systems_info = {}
        
        for ats_system in ATSSystem:
            system_info = await ats_optimizer.get_ats_system_capabilities(ats_system)
            systems_info[ats_system.value] = system_info
        
        return {
            "success": True,
            "supported_systems": list(ATSSystem),
            "default_systems": settings.ats_default_target_systems.split(","),
            "systems_info": systems_info,
            "optimization_features": [
                "Keyword density optimization",
                "Format compatibility analysis",
                "Section structure optimization",
                "Natural language preservation",
                "Multi-system compatibility"
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get ATS systems info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get ATS systems info: {str(e)}"
        )


@router.get("/systems/{ats_system}")
async def get_ats_system_info(
    ats_system: str,
    current_user: User = Depends(auth_deps.get_current_user)
) -> ATSSystemInfoResponse:
    """
    Get detailed information about a specific ATS system.
    
    Returns configuration, optimization tips, and common issues
    for the specified ATS system.
    """
    try:
        # Validate ATS system
        try:
            system_enum = ATSSystem(ats_system.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported ATS system: {ats_system}. Supported systems: {[s.value for s in ATSSystem]}"
            )
        
        system_info = await ats_optimizer.get_ats_system_capabilities(system_enum)
        
        return ATSSystemInfoResponse(
            system_name=system_info["system_name"],
            configuration=system_info["configuration"],
            optimization_tips=system_info["optimization_tips"],
            common_issues=system_info["common_issues"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get ATS system info for {ats_system}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get ATS system info: {str(e)}"
        )


@router.get("/status")
async def get_ats_optimization_status(
    current_user: User = Depends(auth_deps.get_current_user)
) -> Dict[str, Any]:
    """
    Get current status of ATS optimization services.
    
    Returns information about service availability, configuration,
    and current performance metrics.
    """
    try:
        status = {
            "ats_optimization_enabled": settings.enable_ai_ats_optimization,
            "fallback_enabled": settings.ats_optimization_fallback_enabled,
            "confidence_threshold": settings.ats_optimization_confidence_threshold,
            "default_target_systems": settings.ats_default_target_systems.split(","),
            "ai_optimization_available": ats_optimizer.use_ai_optimization
        }
        
        if ats_optimizer.gemini_client:
            gemini_status = ats_optimizer.gemini_client.get_usage_stats()
            status["gemini"] = {
                "available": ats_optimizer.gemini_client.is_available(),
                "usage_stats": gemini_status
            }
        else:
            status["gemini"] = {
                "available": False,
                "reason": "Gemini client not initialized or disabled"
            }
        
        # Service capabilities
        status["capabilities"] = {
            "supported_systems": [s.value for s in ATSSystem],
            "optimization_types": [
                "keyword_density",
                "format_compatibility", 
                "section_structure",
                "natural_language_preservation"
            ],
            "analysis_features": [
                "multi_system_scoring",
                "priority_issue_identification",
                "improvement_estimation",
                "authenticity_preservation"
            ]
        }
        
        return {
            "success": True,
            "status": status
        }
        
    except Exception as e:
        logger.error(f"Failed to get ATS optimization status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get ATS optimization status: {str(e)}"
        )