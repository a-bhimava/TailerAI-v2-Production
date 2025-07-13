"""
ATS Optimization Engine with Gemini AI Integration for TailerAI v2.0.
Phase 2 implementation of comprehensive ATS compatibility optimization.
Maintains authenticity while maximizing ATS parsing success rates.
"""

import logging
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.database import ATSOptimization, UserProfile, ContentSelection
from app.services.database_service import db_service, DatabaseError
from app.services.gemini_client import GeminiClient, GeminiResponse
from app.services.job_analysis_service import JobAnalysisResult
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ATSSystem(str, Enum):
    """Supported ATS systems for optimization."""
    TALEO = "taleo"
    WORKDAY = "workday"
    ADP = "adp"
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    BAMBOO_HR = "bamboo_hr"
    SMARTRECRUITERS = "smartrecruiters"
    CORNERSTONE = "cornerstone"
    ICIMS = "icims"
    GENERIC = "generic"  # Fallback for unknown systems


class CompatibilityLevel(str, Enum):
    """ATS compatibility levels."""
    EXCELLENT = "excellent"    # 90-100% compatibility
    GOOD = "good"             # 75-89% compatibility  
    FAIR = "fair"             # 60-74% compatibility
    POOR = "poor"             # 40-59% compatibility
    INCOMPATIBLE = "incompatible"  # <40% compatibility


@dataclass
class KeywordOptimization:
    """Keyword optimization recommendation."""
    keyword: str
    current_density: float
    target_density: float
    integration_strategy: str
    priority: str  # "high", "medium", "low"
    suggested_contexts: List[str]
    authenticity_score: float  # How natural the integration would be


@dataclass
class ATSCompatibilityIssue:
    """Specific ATS compatibility issue."""
    issue_type: str
    severity: str  # "critical", "high", "medium", "low"
    description: str
    affected_sections: List[str]
    fix_strategy: str
    estimated_impact: str


@dataclass
class ATSOptimizationResult:
    """Comprehensive ATS optimization result."""
    content_selection_id: str
    user_profile_id: str
    target_ats_systems: List[ATSSystem]
    
    # Overall compatibility
    overall_compatibility_score: float
    compatibility_level: CompatibilityLevel
    
    # System-specific scores
    system_compatibility_scores: Dict[ATSSystem, float]
    
    # Keyword optimization
    keyword_optimizations: List[KeywordOptimization]
    current_keyword_density: float
    target_keyword_density: float
    keyword_distribution_score: float
    
    # Issues and fixes
    compatibility_issues: List[ATSCompatibilityIssue]
    priority_fixes: List[str]
    
    # Optimization strategy
    optimization_strategy: Dict[str, Any]
    estimated_improvement: float
    
    # AI reasoning
    ai_reasoning: Optional[str] = None
    ai_confidence_score: Optional[float] = None
    
    # Metadata
    optimization_algorithm: str = "gemini_ats_v1"
    processing_time: Optional[float] = None
    fallback_applied: bool = False


class ATSOptimizationError(Exception):
    """Custom exception for ATS optimization operations."""
    pass


class ATSOptimizationEngine:
    """
    AI-powered ATS optimization engine using Gemini.
    Analyzes content for ATS compatibility and provides optimization recommendations.
    """
    
    def __init__(self, use_ai_optimization: bool = None):
        """
        Initialize ATS optimization engine.
        
        Args:
            use_ai_optimization: Override setting for AI usage. If None, uses settings.
        """
        self.logger = logger
        
        # Configuration
        self.use_ai_optimization = use_ai_optimization if use_ai_optimization is not None else getattr(settings, 'enable_ai_ats_optimization', False)
        self.fallback_enabled = getattr(settings, 'ats_optimization_fallback_enabled', True)
        self.confidence_threshold = getattr(settings, 'ats_optimization_confidence_threshold', 0.7)
        
        # ATS system configurations
        self.ats_system_configs = self._initialize_ats_configs()
        
        # Target metrics
        self.target_keyword_density = 0.03  # 3% keyword density
        self.max_keyword_density = 0.08     # 8% maximum to avoid keyword stuffing
        
        # Initialize Gemini client if AI optimization is enabled
        self.gemini_client = None
        if self.use_ai_optimization:
            try:
                self.gemini_client = GeminiClient()
                if not self.gemini_client.is_available():
                    logger.warning("Gemini client not available, falling back to rule-based optimization")
                    self.use_ai_optimization = False
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client for ATS optimization: {e}")
                self.use_ai_optimization = False
    
    def _initialize_ats_configs(self) -> Dict[ATSSystem, Dict[str, Any]]:
        """Initialize configuration for different ATS systems."""
        return {
            ATSSystem.TALEO: {
                "keyword_weight": 0.35,
                "format_strictness": "high",
                "section_order_important": True,
                "supports_bullets": True,
                "max_word_count": 600,
                "preferred_date_format": "MM/YYYY",
                "common_issues": ["complex_formatting", "special_characters", "long_bullets"]
            },
            ATSSystem.WORKDAY: {
                "keyword_weight": 0.30,
                "format_strictness": "medium",
                "section_order_important": False,
                "supports_bullets": True,
                "max_word_count": 800,
                "preferred_date_format": "Month YYYY",
                "common_issues": ["header_footer_content", "tables", "columns"]
            },
            ATSSystem.ADP: {
                "keyword_weight": 0.40,
                "format_strictness": "high",
                "section_order_important": True,
                "supports_bullets": True,
                "max_word_count": 500,
                "preferred_date_format": "MM/DD/YYYY",
                "common_issues": ["font_variations", "special_formatting", "graphics"]
            },
            ATSSystem.GREENHOUSE: {
                "keyword_weight": 0.25,
                "format_strictness": "low",
                "section_order_important": False,
                "supports_bullets": True,
                "max_word_count": 1000,
                "preferred_date_format": "YYYY-MM",
                "common_issues": ["minimal_parsing_issues"]
            },
            ATSSystem.GENERIC: {
                "keyword_weight": 0.30,
                "format_strictness": "medium",
                "section_order_important": False,
                "supports_bullets": True,
                "max_word_count": 700,
                "preferred_date_format": "MM/YYYY",
                "common_issues": ["varies_by_system"]
            }
        }
    
    async def optimize_content_for_ats(
        self,
        content_selection_id: str,
        target_ats_systems: List[ATSSystem] = None,
        job_analysis: Optional[JobAnalysisResult] = None
    ) -> ATSOptimizationResult:
        """
        Optimize content for ATS compatibility.
        
        Args:
            content_selection_id: ID of content selection to optimize
            target_ats_systems: List of target ATS systems
            job_analysis: Job analysis for context (optional)
            
        Returns:
            Comprehensive optimization result with recommendations
        """
        try:
            start_time = datetime.utcnow()
            
            # Set default ATS systems if not provided
            if not target_ats_systems:
                target_ats_systems = [ATSSystem.GENERIC, ATSSystem.TALEO, ATSSystem.WORKDAY]
            
            logger.info(f"Starting ATS optimization for content {content_selection_id} targeting {target_ats_systems}")
            
            # Load content selection data
            content_data = await self._load_content_selection(content_selection_id)
            
            if self.use_ai_optimization and self.gemini_client:
                result = await self._ai_powered_optimization(
                    content_data, target_ats_systems, job_analysis
                )
            else:
                result = await self._rule_based_optimization(
                    content_data, target_ats_systems, job_analysis
                )
            
            # Store optimization results
            await self._store_optimization_results(result)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            result.processing_time = processing_time
            
            logger.info(f"ATS optimization completed in {processing_time:.2f}s. "
                       f"Overall score: {result.overall_compatibility_score:.2f}, "
                       f"Level: {result.compatibility_level}")
            
            return result
            
        except Exception as e:
            logger.error(f"ATS optimization failed: {str(e)}")
            raise ATSOptimizationError(f"Failed to optimize content for ATS: {str(e)}")
    
    async def _load_content_selection(self, content_selection_id: str) -> Dict[str, Any]:
        """Load content selection data from database."""
        try:
            with db_service.get_session() as session:
                content_selection = session.query(ContentSelection).filter_by(id=content_selection_id).first()
                
                if not content_selection:
                    raise ATSOptimizationError(f"Content selection not found: {content_selection_id}")
                
                # Load related user profile data
                profile = session.query(UserProfile).filter_by(id=content_selection.profile_id).first()
                
                return {
                    "content_selection": content_selection,
                    "profile": profile,
                    "selected_achievements": content_selection.selected_achievements or [],
                    "achievement_scores": content_selection.achievement_scores or {},
                    "estimated_word_count": content_selection.estimated_word_count or 0,
                    "selection_criteria": content_selection.selection_criteria or {}
                }
                
        except SQLAlchemyError as e:
            logger.error(f"Database error loading content selection: {e}")
            raise ATSOptimizationError(f"Failed to load content selection: {e}")
    
    async def _ai_powered_optimization(
        self,
        content_data: Dict[str, Any],
        target_ats_systems: List[ATSSystem],
        job_analysis: Optional[JobAnalysisResult]
    ) -> ATSOptimizationResult:
        """Perform AI-powered ATS optimization using Gemini."""
        try:
            # Create comprehensive analysis prompt
            prompt = self._create_ats_optimization_prompt(content_data, target_ats_systems, job_analysis)
            
            # Get AI analysis
            response = await self.gemini_client.generate_content_analysis(prompt)
            
            if not response.success:
                logger.error(f"AI ATS optimization failed: {response.error_message}")
                if self.fallback_enabled:
                    logger.info("Falling back to rule-based optimization")
                    return await self._rule_based_optimization(content_data, target_ats_systems, job_analysis, fallback=True)
                else:
                    raise ATSOptimizationError(f"AI optimization failed: {response.error_message}")
            
            # Parse AI response
            ai_result = self._parse_ai_optimization_response(response.content)
            
            if not ai_result or ai_result.get("confidence_score", 0) < self.confidence_threshold:
                logger.warning(f"AI optimization confidence too low: {ai_result.get('confidence_score', 0) if ai_result else 'N/A'}")
                if self.fallback_enabled:
                    return await self._rule_based_optimization(content_data, target_ats_systems, job_analysis, fallback=True)
                else:
                    raise ATSOptimizationError("AI optimization confidence below threshold")
            
            # Convert AI result to structured optimization result
            result = self._convert_ai_result_to_optimization(
                ai_result, content_data, target_ats_systems, job_analysis
            )
            
            result.ai_reasoning = ai_result.get("reasoning", "")
            result.ai_confidence_score = ai_result.get("confidence_score", 0.0)
            
            return result
            
        except Exception as e:
            logger.error(f"AI-powered optimization failed: {e}")
            if self.fallback_enabled:
                return await self._rule_based_optimization(content_data, target_ats_systems, job_analysis, fallback=True)
            else:
                raise
    
    async def _rule_based_optimization(
        self,
        content_data: Dict[str, Any],
        target_ats_systems: List[ATSSystem],
        job_analysis: Optional[JobAnalysisResult],
        fallback: bool = False
    ) -> ATSOptimizationResult:
        """Perform rule-based ATS optimization using algorithmic analysis."""
        
        content_selection = content_data["content_selection"]
        
        # Calculate keyword metrics
        keyword_analysis = self._analyze_keyword_density(content_data, job_analysis)
        
        # Analyze ATS compatibility for each system
        system_scores = {}
        compatibility_issues = []
        
        for ats_system in target_ats_systems:
            score, issues = self._analyze_ats_compatibility(content_data, ats_system)
            system_scores[ats_system] = score
            compatibility_issues.extend(issues)
        
        # Calculate overall compatibility
        overall_score = sum(system_scores.values()) / len(system_scores) if system_scores else 0.0
        compatibility_level = self._calculate_compatibility_level(overall_score)
        
        # Generate keyword optimizations
        keyword_optimizations = self._generate_keyword_optimizations(keyword_analysis, job_analysis)
        
        # Generate priority fixes
        priority_fixes = self._generate_priority_fixes(compatibility_issues)
        
        # Create optimization strategy
        optimization_strategy = {
            "primary_focus": "keyword_optimization" if overall_score > 0.6 else "format_fixes",
            "target_systems": [sys.value for sys in target_ats_systems],
            "keyword_strategy": "natural_integration",
            "format_strategy": "conservative_formatting"
        }
        
        return ATSOptimizationResult(
            content_selection_id=str(content_selection.id),
            user_profile_id=str(content_selection.profile_id),
            target_ats_systems=target_ats_systems,
            overall_compatibility_score=overall_score,
            compatibility_level=compatibility_level,
            system_compatibility_scores=system_scores,
            keyword_optimizations=keyword_optimizations,
            current_keyword_density=keyword_analysis["current_density"],
            target_keyword_density=self.target_keyword_density,
            keyword_distribution_score=keyword_analysis["distribution_score"],
            compatibility_issues=compatibility_issues,
            priority_fixes=priority_fixes,
            optimization_strategy=optimization_strategy,
            estimated_improvement=self._estimate_improvement(overall_score, len(compatibility_issues)),
            optimization_algorithm="rule_based_v1" if not fallback else "rule_based_fallback_v1",
            fallback_applied=fallback
        )
    
    def _create_ats_optimization_prompt(
        self,
        content_data: Dict[str, Any],
        target_ats_systems: List[ATSSystem],
        job_analysis: Optional[JobAnalysisResult]
    ) -> str:
        """Create comprehensive prompt for AI ATS optimization."""
        
        content_selection = content_data["content_selection"]
        achievement_ids = content_selection.selected_achievements or []
        word_count = content_selection.estimated_word_count or 0
        
        # Extract job context if available
        job_context = ""
        if job_analysis:
            job_context = f"""
**JOB CONTEXT:**
Position: {job_analysis.position_title}
Company: {job_analysis.company_name}
Required Skills: {', '.join(job_analysis.required_skills)}
Important Keywords: {', '.join(job_analysis.important_keywords)}
ATS Keywords: {', '.join(job_analysis.ats_keywords)}
"""
        
        # Target ATS systems info
        ats_info = []
        for ats_system in target_ats_systems:
            config = self.ats_system_configs.get(ats_system, {})
            ats_info.append(f"- {ats_system.value}: keyword_weight={config.get('keyword_weight', 0.3)}, strictness={config.get('format_strictness', 'medium')}")
        
        prompt = f"""You are an expert ATS (Applicant Tracking System) optimization specialist. Analyze the provided resume content for compatibility with multiple ATS systems and provide detailed optimization recommendations.

{job_context}

**TARGET ATS SYSTEMS:**
{chr(10).join(ats_info)}

**CURRENT CONTENT:**
Selected Achievements: {len(achievement_ids)} items
Estimated Word Count: {word_count}
Selection Criteria: {content_selection.selection_criteria}

**ANALYSIS REQUIREMENTS:**
1. Keyword density analysis and optimization
2. Format compatibility assessment
3. Section structure evaluation
4. ATS parsing success prediction
5. Specific improvement recommendations

**OPTIMIZATION CONSTRAINTS:**
- Maintain 100% content authenticity (no false information)
- Target keyword density: 2-5% (avoid keyword stuffing)
- Optimize for readability AND ATS parsing
- Preserve professional tone and impact
- Focus on natural keyword integration

**PROVIDE ANALYSIS IN JSON FORMAT:**

{{
    "overall_compatibility_score": <0.0-1.0>,
    "system_specific_scores": {{
        "taleo": <0.0-1.0>,
        "workday": <0.0-1.0>,
        "adp": <0.0-1.0>
    }},
    "keyword_analysis": {{
        "current_density": <0.0-1.0>,
        "target_density": <0.0-1.0>,
        "keyword_gaps": ["missing_keyword1", "missing_keyword2"],
        "optimization_opportunities": [
            {{
                "keyword": "keyword_name",
                "priority": "high|medium|low",
                "integration_strategy": "specific strategy",
                "suggested_context": "where to integrate naturally"
            }}
        ]
    }},
    "compatibility_issues": [
        {{
            "issue_type": "keyword_density|format|structure|parsing",
            "severity": "critical|high|medium|low",
            "description": "detailed issue description",
            "fix_strategy": "specific fix recommendation",
            "estimated_impact": "high|medium|low"
        }}
    ],
    "optimization_recommendations": [
        {{
            "category": "keywords|format|structure|content",
            "recommendation": "specific actionable recommendation",
            "priority": "high|medium|low",
            "estimated_improvement": "percentage improvement expected"
        }}
    ],
    "confidence_score": <0.0-1.0>,
    "reasoning": "comprehensive reasoning for analysis and recommendations"
}}

**GUIDELINES:**
- Prioritize authenticity over keyword density
- Focus on natural language integration
- Consider multiple ATS system requirements
- Provide actionable, specific recommendations
- Explain reasoning for all suggestions

Respond only with valid JSON.
"""
        return prompt
    
    def _parse_ai_optimization_response(self, response_content: str) -> Optional[Dict[str, Any]]:
        """Parse AI optimization response into structured data."""
        try:
            data = json.loads(response_content.strip())
            
            # Validate required fields
            required_fields = [
                "overall_compatibility_score",
                "system_specific_scores", 
                "keyword_analysis",
                "compatibility_issues",
                "optimization_recommendations",
                "confidence_score"
            ]
            
            for field in required_fields:
                if field not in data:
                    logger.error(f"Missing required field in AI response: {field}")
                    return None
            
            return data
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse AI optimization response: {e}")
            logger.debug(f"Response content: {response_content}")
            return None
    
    def _convert_ai_result_to_optimization(
        self,
        ai_result: Dict[str, Any],
        content_data: Dict[str, Any],
        target_ats_systems: List[ATSSystem],
        job_analysis: Optional[JobAnalysisResult]
    ) -> ATSOptimizationResult:
        """Convert AI analysis result to structured optimization result."""
        
        content_selection = content_data["content_selection"]
        
        # Extract system-specific scores
        system_scores = {}
        for ats_system in target_ats_systems:
            score = ai_result["system_specific_scores"].get(ats_system.value, 0.0)
            system_scores[ats_system] = score
        
        # Convert keyword optimizations
        keyword_optimizations = []
        for opt in ai_result["keyword_analysis"].get("optimization_opportunities", []):
            keyword_optimizations.append(KeywordOptimization(
                keyword=opt["keyword"],
                current_density=0.0,  # TODO: Calculate from content
                target_density=ai_result["keyword_analysis"]["target_density"],
                integration_strategy=opt["integration_strategy"],
                priority=opt["priority"],
                suggested_contexts=[opt["suggested_context"]],
                authenticity_score=0.9  # Assume high authenticity for AI suggestions
            ))
        
        # Convert compatibility issues
        compatibility_issues = []
        for issue in ai_result["compatibility_issues"]:
            compatibility_issues.append(ATSCompatibilityIssue(
                issue_type=issue["issue_type"],
                severity=issue["severity"],
                description=issue["description"],
                affected_sections=[],  # TODO: Extract from description
                fix_strategy=issue["fix_strategy"],
                estimated_impact=issue["estimated_impact"]
            ))
        
        # Generate priority fixes from recommendations
        priority_fixes = []
        for rec in ai_result["optimization_recommendations"]:
            if rec["priority"] == "high":
                priority_fixes.append(rec["recommendation"])
        
        # Calculate compatibility level
        overall_score = ai_result["overall_compatibility_score"]
        compatibility_level = self._calculate_compatibility_level(overall_score)
        
        return ATSOptimizationResult(
            content_selection_id=str(content_selection.id),
            user_profile_id=str(content_selection.profile_id),
            target_ats_systems=target_ats_systems,
            overall_compatibility_score=overall_score,
            compatibility_level=compatibility_level,
            system_compatibility_scores=system_scores,
            keyword_optimizations=keyword_optimizations,
            current_keyword_density=ai_result["keyword_analysis"]["current_density"],
            target_keyword_density=ai_result["keyword_analysis"]["target_density"],
            keyword_distribution_score=0.8,  # TODO: Calculate properly
            compatibility_issues=compatibility_issues,
            priority_fixes=priority_fixes,
            optimization_strategy={
                "ai_driven": True,
                "focus_areas": [rec["category"] for rec in ai_result["optimization_recommendations"][:3]]
            },
            estimated_improvement=self._calculate_estimated_improvement_from_ai(ai_result)
        )
    
    def _analyze_keyword_density(
        self,
        content_data: Dict[str, Any],
        job_analysis: Optional[JobAnalysisResult]
    ) -> Dict[str, Any]:
        """Analyze current keyword density and distribution."""
        
        # TODO: Implement comprehensive keyword analysis
        # This is a simplified version for now
        
        word_count = content_data["content_selection"].estimated_word_count or 1
        
        if job_analysis:
            total_keywords = len(job_analysis.required_skills + job_analysis.important_keywords)
            # Simplified density calculation
            current_density = min(0.1, total_keywords / max(word_count, 1))
        else:
            current_density = 0.02  # Default assumption
        
        return {
            "current_density": current_density,
            "target_density": self.target_keyword_density,
            "distribution_score": 0.7,  # Placeholder
            "keyword_gaps": [],
            "overstuffed_keywords": []
        }
    
    def _analyze_ats_compatibility(
        self,
        content_data: Dict[str, Any],
        ats_system: ATSSystem
    ) -> Tuple[float, List[ATSCompatibilityIssue]]:
        """Analyze compatibility with specific ATS system."""
        
        config = self.ats_system_configs.get(ats_system, {})
        issues = []
        
        # Basic compatibility scoring based on word count
        word_count = content_data["content_selection"].estimated_word_count or 0
        max_words = config.get("max_word_count", 700)
        
        score = 0.8  # Base score
        
        # Word count penalty
        if word_count > max_words:
            score -= 0.2
            issues.append(ATSCompatibilityIssue(
                issue_type="word_count",
                severity="medium",
                description=f"Content exceeds {ats_system.value} recommended word limit ({word_count} > {max_words})",
                affected_sections=["overall"],
                fix_strategy="Reduce content length while maintaining impact",
                estimated_impact="medium"
            ))
        
        # Format strictness penalty
        if config.get("format_strictness") == "high":
            score -= 0.1  # Conservative penalty for high-strictness systems
            issues.append(ATSCompatibilityIssue(
                issue_type="format",
                severity="low",
                description=f"{ats_system.value} requires strict formatting compliance",
                affected_sections=["formatting"],
                fix_strategy="Use simple, clean formatting without complex elements",
                estimated_impact="medium"
            ))
        
        return max(0.0, score), issues
    
    def _generate_keyword_optimizations(
        self,
        keyword_analysis: Dict[str, Any],
        job_analysis: Optional[JobAnalysisResult]
    ) -> List[KeywordOptimization]:
        """Generate keyword optimization recommendations."""
        
        optimizations = []
        
        if job_analysis:
            # Focus on required skills first
            for skill in job_analysis.required_skills[:5]:  # Top 5 skills
                optimizations.append(KeywordOptimization(
                    keyword=skill,
                    current_density=0.0,  # TODO: Calculate actual density
                    target_density=0.01,  # 1% target for each important keyword
                    integration_strategy="Natural integration within existing achievements",
                    priority="high",
                    suggested_contexts=[
                        f"Integrate '{skill}' into relevant achievement descriptions",
                        f"Include '{skill}' in skills section if not present"
                    ],
                    authenticity_score=0.9
                ))
        
        return optimizations
    
    def _generate_priority_fixes(self, issues: List[ATSCompatibilityIssue]) -> List[str]:
        """Generate prioritized list of fixes from compatibility issues."""
        
        # Sort issues by severity and generate fix recommendations
        high_severity_issues = [issue for issue in issues if issue.severity in ["critical", "high"]]
        
        fixes = []
        for issue in high_severity_issues[:5]:  # Top 5 priority fixes
            fixes.append(f"{issue.issue_type.title()}: {issue.fix_strategy}")
        
        return fixes
    
    def _calculate_compatibility_level(self, score: float) -> CompatibilityLevel:
        """Calculate compatibility level from score."""
        if score >= 0.9:
            return CompatibilityLevel.EXCELLENT
        elif score >= 0.75:
            return CompatibilityLevel.GOOD
        elif score >= 0.6:
            return CompatibilityLevel.FAIR
        elif score >= 0.4:
            return CompatibilityLevel.POOR
        else:
            return CompatibilityLevel.INCOMPATIBLE
    
    def _estimate_improvement(self, current_score: float, issue_count: int) -> float:
        """Estimate potential improvement from optimization."""
        base_improvement = min(0.3, (1.0 - current_score) * 0.5)  # Up to 30% improvement
        issue_improvement = min(0.2, issue_count * 0.05)  # 5% per issue, max 20%
        return base_improvement + issue_improvement
    
    def _calculate_estimated_improvement_from_ai(self, ai_result: Dict[str, Any]) -> float:
        """Calculate estimated improvement from AI recommendations."""
        # Extract improvement estimates from AI recommendations
        total_improvement = 0.0
        
        for rec in ai_result.get("optimization_recommendations", []):
            if "estimated_improvement" in rec:
                try:
                    # Parse percentage improvement (e.g., "15%" -> 0.15)
                    improvement_str = rec["estimated_improvement"].replace("%", "")
                    improvement = float(improvement_str) / 100
                    total_improvement += improvement
                except (ValueError, KeyError):
                    continue
        
        return min(0.5, total_improvement)  # Cap at 50% improvement
    
    async def _store_optimization_results(self, result: ATSOptimizationResult):
        """Store optimization results in database."""
        try:
            with db_service.get_session() as session:
                optimization = ATSOptimization(
                    profile_id=result.user_profile_id,
                    content_selection_id=result.content_selection_id,
                    optimization_algorithm=result.optimization_algorithm,
                    target_keywords=[opt.keyword for opt in result.keyword_optimizations],
                    target_density=result.target_keyword_density,
                    original_keyword_density=result.current_keyword_density,
                    final_keyword_density=result.target_keyword_density,
                    keyword_distribution_score=result.keyword_distribution_score,
                    natural_language_score=0.8,  # TODO: Calculate properly
                    keyword_stuffing_risk=0.1,   # TODO: Calculate properly
                    keyword_metrics={
                        "optimizations": [opt.__dict__ for opt in result.keyword_optimizations],
                        "system_scores": {k.value: v for k, v in result.system_compatibility_scores.items()}
                    },
                    optimization_strategy=result.optimization_strategy,
                    improvement_metrics={
                        "estimated_improvement": result.estimated_improvement,
                        "compatibility_level": result.compatibility_level.value
                    },
                    ats_compatibility_score=result.overall_compatibility_score,
                    ats_compatibility_level=result.compatibility_level.value,
                    ats_system_results={k.value: v for k, v in result.system_compatibility_scores.items()},
                    parsing_success_rate=result.overall_compatibility_score,
                    common_issues=[issue.description for issue in result.compatibility_issues],
                    priority_fixes=result.priority_fixes,
                    detailed_recommendations=[issue.fix_strategy for issue in result.compatibility_issues],
                    final_optimization_score=result.overall_compatibility_score,
                    word_budget_used=0,  # TODO: Calculate
                    sections_modified=[],  # TODO: Track modifications
                    optimization_applied=False,  # Not applied yet, just analyzed
                    created_at=datetime.utcnow()
                )
                
                session.add(optimization)
                session.commit()
                
                logger.info(f"Stored ATS optimization results for content {result.content_selection_id}")
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to store optimization results: {e}")
            # Don't raise exception - optimization can continue without storage
    
    async def get_ats_system_capabilities(self, ats_system: ATSSystem) -> Dict[str, Any]:
        """Get capabilities and requirements for specific ATS system."""
        config = self.ats_system_configs.get(ats_system, {})
        
        return {
            "system_name": ats_system.value,
            "configuration": config,
            "optimization_tips": [
                f"Target keyword density: {config.get('keyword_weight', 0.3) * 10:.1f}%",
                f"Format strictness: {config.get('format_strictness', 'medium')}",
                f"Max word count: {config.get('max_word_count', 700)}",
                f"Preferred date format: {config.get('preferred_date_format', 'MM/YYYY')}"
            ],
            "common_issues": config.get("common_issues", [])
        }


# Global instance for easy access
ats_optimizer = ATSOptimizationEngine()