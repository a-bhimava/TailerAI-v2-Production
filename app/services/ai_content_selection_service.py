"""
Enhanced Content Selection Engine with Gemini AI Integration for TailerAI v2.0.
Extends existing algorithmic content selection with AI-powered reasoning and optimization.
Maintains full backward compatibility with feature flags for safe deployment.
"""

import logging
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from app.services.content_selection_service import (
    ContentSelectionEngine, 
    ContentSelectionResult, 
    ScoredContent, 
    ContentType,
    ContentSelectionError
)
from app.services.gemini_client import GeminiClient, GeminiResponse
from app.services.job_analysis_service import JobAnalysisResult
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class AISelectionReasoning:
    """Structured reasoning from AI for content selection decisions."""
    selection_rationale: str
    content_fit_analysis: str
    keyword_integration_strategy: str
    combination_logic: str
    confidence_score: float
    alternative_considerations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "selection_rationale": self.selection_rationale,
            "content_fit_analysis": self.content_fit_analysis,
            "keyword_integration_strategy": self.keyword_integration_strategy,
            "combination_logic": self.combination_logic,
            "confidence_score": self.confidence_score,
            "alternative_considerations": self.alternative_considerations
        }


@dataclass 
class EnhancedContentSelectionResult(ContentSelectionResult):
    """Extended result with AI reasoning and enhanced metadata."""
    ai_reasoning: Optional[AISelectionReasoning] = None
    ai_confidence_score: Optional[float] = None
    selection_method: str = "algorithmic"  # "algorithmic", "ai_enhanced", "ai_primary"
    fallback_applied: bool = False
    gemini_processing_time: Optional[float] = None


class SelectionMethod(str, Enum):
    """Available content selection methods."""
    ALGORITHMIC = "algorithmic"      # Original algorithm-based selection
    AI_ENHANCED = "ai_enhanced"      # AI reasoning with algorithmic fallback
    AI_PRIMARY = "ai_primary"        # AI-first with algorithmic validation


class AIContentSelectionEngine(ContentSelectionEngine):
    """
    Enhanced content selection engine with Gemini AI integration.
    Extends base ContentSelectionEngine while maintaining full backward compatibility.
    """
    
    def __init__(self, use_ai_selection: bool = None):
        """
        Initialize enhanced content selection engine.
        
        Args:
            use_ai_selection: Override setting for AI usage. If None, uses settings.
        """
        super().__init__()
        
        # AI configuration
        self.use_ai_selection = use_ai_selection if use_ai_selection is not None else getattr(settings, 'enable_ai_content_selection', False)
        self.ai_fallback_enabled = getattr(settings, 'ai_selection_fallback_enabled', True)
        self.ai_confidence_threshold = getattr(settings, 'ai_selection_confidence_threshold', 0.7)
        
        # Initialize Gemini client if AI selection is enabled
        self.gemini_client = None
        if self.use_ai_selection:
            try:
                self.gemini_client = GeminiClient()
                if not self.gemini_client.is_available():
                    logger.warning("Gemini client not available, falling back to algorithmic selection")
                    self.use_ai_selection = False
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                self.use_ai_selection = False
    
    async def select_optimal_content(
        self, 
        user_profile_id: str, 
        job_analysis: JobAnalysisResult,
        selection_method: SelectionMethod = SelectionMethod.AI_ENHANCED
    ) -> EnhancedContentSelectionResult:
        """
        Select optimal content with optional AI enhancement.
        
        Args:
            user_profile_id: User's profile identifier
            job_analysis: Analyzed job requirements
            selection_method: Selection method to use
            
        Returns:
            Enhanced selection result with AI reasoning
        """
        try:
            logger.info(f"Starting enhanced content selection for user {user_profile_id} using method: {selection_method}")
            
            # Load user's master dataset
            user_data = await self._load_user_master_dataset(user_profile_id)
            
            # Determine selection strategy based on method and availability
            effective_method = self._determine_effective_method(selection_method)
            
            if effective_method == SelectionMethod.ALGORITHMIC:
                return await self._algorithmic_selection(user_data, job_analysis, user_profile_id)
            
            elif effective_method == SelectionMethod.AI_ENHANCED:
                return await self._ai_enhanced_selection(user_data, job_analysis, user_profile_id)
            
            elif effective_method == SelectionMethod.AI_PRIMARY:
                return await self._ai_primary_selection(user_data, job_analysis, user_profile_id)
            
            else:
                raise ContentSelectionError(f"Unknown selection method: {effective_method}")
                
        except Exception as e:
            logger.error(f"Enhanced content selection failed: {str(e)}")
            # Always fallback to algorithmic selection on error
            if self.ai_fallback_enabled and selection_method != SelectionMethod.ALGORITHMIC:
                logger.info("Falling back to algorithmic selection due to error")
                return await self._algorithmic_selection(user_data, job_analysis, user_profile_id, fallback=True)
            raise ContentSelectionError(f"Failed to select optimal content: {str(e)}")
    
    def _determine_effective_method(self, requested_method: SelectionMethod) -> SelectionMethod:
        """Determine which method to actually use based on configuration and availability."""
        if not self.use_ai_selection or not self.gemini_client:
            return SelectionMethod.ALGORITHMIC
        
        if requested_method == SelectionMethod.ALGORITHMIC:
            return SelectionMethod.ALGORITHMIC
        
        # Check if Gemini client can make requests
        if not self.gemini_client.rate_limiter.can_make_request():
            logger.warning("Gemini rate limit exceeded, falling back to algorithmic selection")
            return SelectionMethod.ALGORITHMIC
        
        return requested_method
    
    async def _algorithmic_selection(
        self, 
        user_data: Dict[str, Any], 
        job_analysis: JobAnalysisResult, 
        user_profile_id: str,
        fallback: bool = False
    ) -> EnhancedContentSelectionResult:
        """Perform traditional algorithmic content selection."""
        
        # Use parent class method for core algorithmic selection
        base_result = await super().select_optimal_content(user_profile_id, job_analysis)
        
        # Convert to enhanced result
        enhanced_result = EnhancedContentSelectionResult(
            job_analysis_id=base_result.job_analysis_id,
            user_profile_id=base_result.user_profile_id,
            selected_achievements=base_result.selected_achievements,
            selected_work_experiences=base_result.selected_work_experiences,
            selected_skills=base_result.selected_skills,
            selected_projects=base_result.selected_projects,
            selected_education=base_result.selected_education,
            total_score=base_result.total_score,
            estimated_word_count=base_result.estimated_word_count,
            one_page_compliant=base_result.one_page_compliant,
            content_diversity_score=base_result.content_diversity_score,
            keyword_coverage_percentage=base_result.keyword_coverage_percentage,
            selection_algorithm=base_result.selection_algorithm,
            selection_criteria=base_result.selection_criteria,
            optimization_notes=base_result.optimization_notes,
            selection_method=SelectionMethod.ALGORITHMIC,
            fallback_applied=fallback
        )
        
        return enhanced_result
    
    async def _ai_enhanced_selection(
        self, 
        user_data: Dict[str, Any], 
        job_analysis: JobAnalysisResult, 
        user_profile_id: str
    ) -> EnhancedContentSelectionResult:
        """
        AI-enhanced selection: Use algorithmic scoring with AI validation and reasoning.
        This provides the safest integration of AI capabilities.
        """
        try:
            # First, perform algorithmic selection
            algorithmic_result = await self._algorithmic_selection(user_data, job_analysis, user_profile_id)
            
            # Get AI reasoning for the algorithmic selection
            ai_start_time = datetime.utcnow()
            ai_reasoning = await self._get_ai_selection_reasoning(
                algorithmic_result, user_data, job_analysis
            )
            ai_processing_time = (datetime.utcnow() - ai_start_time).total_seconds()
            
            # Enhance the result with AI insights
            enhanced_result = EnhancedContentSelectionResult(
                job_analysis_id=algorithmic_result.job_analysis_id,
                user_profile_id=algorithmic_result.user_profile_id,
                selected_achievements=algorithmic_result.selected_achievements,
                selected_work_experiences=algorithmic_result.selected_work_experiences,
                selected_skills=algorithmic_result.selected_skills,
                selected_projects=algorithmic_result.selected_projects,
                selected_education=algorithmic_result.selected_education,
                total_score=algorithmic_result.total_score,
                estimated_word_count=algorithmic_result.estimated_word_count,
                one_page_compliant=algorithmic_result.one_page_compliant,
                content_diversity_score=algorithmic_result.content_diversity_score,
                keyword_coverage_percentage=algorithmic_result.keyword_coverage_percentage,
                selection_algorithm=f"{algorithmic_result.selection_algorithm}_ai_enhanced",
                selection_criteria=algorithmic_result.selection_criteria,
                optimization_notes=algorithmic_result.optimization_notes + (ai_reasoning.alternative_considerations if ai_reasoning else []),
                ai_reasoning=ai_reasoning,
                ai_confidence_score=ai_reasoning.confidence_score if ai_reasoning else None,
                selection_method=SelectionMethod.AI_ENHANCED,
                fallback_applied=False,
                gemini_processing_time=ai_processing_time
            )
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"AI enhancement failed, using algorithmic result: {e}")
            # Return algorithmic result with fallback flag
            algorithmic_result.selection_method = SelectionMethod.AI_ENHANCED
            algorithmic_result.fallback_applied = True
            return algorithmic_result
    
    async def _ai_primary_selection(
        self, 
        user_data: Dict[str, Any], 
        job_analysis: JobAnalysisResult, 
        user_profile_id: str
    ) -> EnhancedContentSelectionResult:
        """
        AI-primary selection: Let AI make the selection decisions with algorithmic validation.
        This is the most advanced but also highest-risk approach.
        """
        try:
            ai_start_time = datetime.utcnow()
            
            # Get AI-driven content selection
            ai_selection = await self._get_ai_content_selection(user_data, job_analysis)
            
            if not ai_selection or ai_selection.confidence_score < self.ai_confidence_threshold:
                logger.warning(f"AI selection confidence too low ({ai_selection.confidence_score if ai_selection else 0}), falling back to enhanced selection")
                return await self._ai_enhanced_selection(user_data, job_analysis, user_profile_id)
            
            # Convert AI selection to structured result
            ai_result = await self._convert_ai_selection_to_result(
                ai_selection, user_data, job_analysis, user_profile_id
            )
            
            ai_processing_time = (datetime.utcnow() - ai_start_time).total_seconds()
            
            # Validate with algorithmic constraints
            validated_result = await self._validate_ai_selection_with_constraints(ai_result)
            
            validated_result.selection_method = SelectionMethod.AI_PRIMARY
            validated_result.gemini_processing_time = ai_processing_time
            
            return validated_result
            
        except Exception as e:
            logger.error(f"AI primary selection failed, falling back to enhanced selection: {e}")
            return await self._ai_enhanced_selection(user_data, job_analysis, user_profile_id)
    
    async def _get_ai_selection_reasoning(
        self, 
        selection_result: EnhancedContentSelectionResult,
        user_data: Dict[str, Any],
        job_analysis: JobAnalysisResult
    ) -> Optional[AISelectionReasoning]:
        """Get AI reasoning for an existing content selection."""
        
        try:
            # Prepare prompt for AI reasoning
            prompt = self._create_selection_reasoning_prompt(selection_result, user_data, job_analysis)
            
            # Get AI response
            response = await self.gemini_client.generate_content_analysis(prompt)
            
            if not response.success:
                logger.error(f"AI reasoning failed: {response.error_message}")
                return None
            
            # Parse AI response
            reasoning_data = self._parse_ai_reasoning_response(response.content)
            return reasoning_data
            
        except Exception as e:
            logger.error(f"Failed to get AI reasoning: {e}")
            return None
    
    async def _get_ai_content_selection(
        self, 
        user_data: Dict[str, Any], 
        job_analysis: JobAnalysisResult
    ) -> Optional[AISelectionReasoning]:
        """Get AI-driven content selection recommendations."""
        
        try:
            # Prepare prompt for AI selection
            prompt = self._create_content_selection_prompt(user_data, job_analysis)
            
            # Get AI response
            response = await self.gemini_client.generate_content_analysis(prompt)
            
            if not response.success:
                logger.error(f"AI content selection failed: {response.error_message}")
                return None
            
            # Parse AI response into selection data
            selection_data = self._parse_ai_selection_response(response.content)
            return selection_data
            
        except Exception as e:
            logger.error(f"Failed to get AI content selection: {e}")
            return None
    
    def _create_selection_reasoning_prompt(
        self, 
        selection_result: EnhancedContentSelectionResult,
        user_data: Dict[str, Any],
        job_analysis: JobAnalysisResult
    ) -> str:
        """Create prompt for AI to provide reasoning about existing selection."""
        
        # Extract selected content summaries
        selected_achievements = [item.content_data for item in selection_result.selected_achievements]
        selected_skills = [item.content_data for item in selection_result.selected_skills]
        
        prompt = f"""You are an expert resume strategist analyzing a content selection for job application optimization.

**JOB REQUIREMENTS:**
Position: {job_analysis.position_title} at {job_analysis.company_name}
Industry: {job_analysis.industry}
Required Skills: {', '.join(job_analysis.required_skills)}
Key Requirements: {', '.join(job_analysis.key_requirements)}
Important Keywords: {', '.join(job_analysis.important_keywords)}

**SELECTED CONTENT:**
Achievements ({len(selected_achievements)} selected):
{json.dumps(selected_achievements, indent=2)}

Skills ({len(selected_skills)} selected):
{json.dumps(selected_skills, indent=2)}

**SELECTION METRICS:**
Total Score: {selection_result.total_score:.2f}
Word Count: {selection_result.estimated_word_count}
Keyword Coverage: {selection_result.keyword_coverage_percentage:.1f}%
One-Page Compliant: {selection_result.one_page_compliant}

**ANALYSIS TASK:**
Provide strategic reasoning for this content selection in JSON format:

{{
    "selection_rationale": "Overall strategic reasoning for content choices",
    "content_fit_analysis": "How well selected content matches job requirements",
    "keyword_integration_strategy": "Analysis of keyword coverage and opportunities",
    "combination_logic": "Why this combination of content works together",
    "confidence_score": <0.0-1.0>,
    "alternative_considerations": [
        "Alternative content that could have been selected",
        "Potential improvements or adjustments"
    ]
}}

**GUIDELINES:**
- Focus on strategic fit and resume effectiveness
- Consider both ATS optimization and human reviewer appeal
- Assess content diversity and story coherence
- Identify keyword gaps and integration opportunities
- Provide actionable insights for improvement

Respond only with valid JSON.
"""
        return prompt
    
    def _create_content_selection_prompt(
        self, 
        user_data: Dict[str, Any], 
        job_analysis: JobAnalysisResult
    ) -> str:
        """Create prompt for AI to make content selection decisions."""
        
        # Prepare user content for analysis
        achievements_data = []
        for achievement in user_data["achievements"]:
            achievements_data.append({
                "id": str(achievement.id),
                "text": achievement.achievement_text,
                "category": achievement.achievement_category,
                "impact_level": achievement.impact_level,
                "skills": achievement.skills_demonstrated or [],
                "metrics": achievement.quantified_metrics or {}
            })
        
        skills_data = []
        for skill in user_data["skills"]:
            skills_data.append({
                "id": str(skill.id),
                "name": skill.skill_name,
                "category": skill.skill_category,
                "proficiency": skill.proficiency_level,
                "years": skill.years_experience
            })
        
        prompt = f"""You are an expert resume strategist tasked with selecting optimal content for a job application.

**TARGET JOB:**
Position: {job_analysis.position_title} at {job_analysis.company_name}
Industry: {job_analysis.industry}
Seniority: {job_analysis.seniority_level}
Required Skills: {', '.join(job_analysis.required_skills)}
Preferred Skills: {', '.join(job_analysis.preferred_skills)}
Key Requirements: {', '.join(job_analysis.key_requirements)}
Important Keywords: {', '.join(job_analysis.important_keywords)}

**AVAILABLE CONTENT:**

Achievements ({len(achievements_data)} available):
{json.dumps(achievements_data, indent=2)}

Skills ({len(skills_data)} available):
{json.dumps(skills_data, indent=2)}

**SELECTION CONSTRAINTS:**
- Target word count: 300-350 words for one-page compliance
- Maximum 8 achievements
- Maximum 15 skills
- Prioritize content with quantified results
- Ensure keyword coverage while maintaining authenticity

**SELECTION TASK:**
Select optimal content combination and provide reasoning in JSON format:

{{
    "selected_achievement_ids": ["id1", "id2", ...],
    "selected_skill_ids": ["id1", "id2", ...],
    "selection_rationale": "Strategic reasoning for selections",
    "content_fit_analysis": "Analysis of how content matches job",
    "keyword_integration_strategy": "Keyword coverage approach",
    "combination_logic": "Why this combination is optimal",
    "confidence_score": <0.0-1.0>,
    "alternative_considerations": [
        "Alternative content considered",
        "Trade-offs and improvements"
    ]
}}

**OPTIMIZATION CRITERIA:**
1. Job relevance and keyword matching
2. Impact level and quantified results
3. Content diversity and skill demonstration
4. ATS compatibility and human appeal
5. One-page constraint compliance

Select content that tells the strongest, most relevant story for this specific role.

Respond only with valid JSON.
"""
        return prompt
    
    def _parse_ai_reasoning_response(self, response_content: str) -> Optional[AISelectionReasoning]:
        """Parse AI reasoning response into structured data."""
        try:
            data = json.loads(response_content.strip())
            
            return AISelectionReasoning(
                selection_rationale=data.get("selection_rationale", ""),
                content_fit_analysis=data.get("content_fit_analysis", ""),
                keyword_integration_strategy=data.get("keyword_integration_strategy", ""),
                combination_logic=data.get("combination_logic", ""),
                confidence_score=float(data.get("confidence_score", 0.0)),
                alternative_considerations=data.get("alternative_considerations", [])
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse AI reasoning response: {e}")
            logger.debug(f"Response content: {response_content}")
            return None
    
    def _parse_ai_selection_response(self, response_content: str) -> Optional[AISelectionReasoning]:
        """Parse AI selection response into structured data."""
        try:
            data = json.loads(response_content.strip())
            
            # Store selection IDs in the reasoning object for processing
            reasoning = AISelectionReasoning(
                selection_rationale=data.get("selection_rationale", ""),
                content_fit_analysis=data.get("content_fit_analysis", ""),
                keyword_integration_strategy=data.get("keyword_integration_strategy", ""),
                combination_logic=data.get("combination_logic", ""),
                confidence_score=float(data.get("confidence_score", 0.0)),
                alternative_considerations=data.get("alternative_considerations", [])
            )
            
            # Add selection data as metadata
            reasoning.selected_achievement_ids = data.get("selected_achievement_ids", [])
            reasoning.selected_skill_ids = data.get("selected_skill_ids", [])
            
            return reasoning
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse AI selection response: {e}")
            logger.debug(f"Response content: {response_content}")
            return None
    
    async def _convert_ai_selection_to_result(
        self,
        ai_selection: AISelectionReasoning,
        user_data: Dict[str, Any],
        job_analysis: JobAnalysisResult,
        user_profile_id: str
    ) -> EnhancedContentSelectionResult:
        """Convert AI selection data to structured result."""
        
        # Filter selected achievements
        selected_achievements = []
        for achievement in user_data["achievements"]:
            if str(achievement.id) in getattr(ai_selection, 'selected_achievement_ids', []):
                # Score the selected achievement for consistency
                scored = await self._score_achievement(achievement, [], job_analysis)
                selected_achievements.append(scored)
        
        # Filter selected skills
        selected_skills = []
        for skill in user_data["skills"]:
            if str(skill.id) in getattr(ai_selection, 'selected_skill_ids', []):
                scored = await self._score_skill(skill, [], job_analysis)
                selected_skills.append(scored)
        
        # Calculate metrics
        total_score = sum(item.total_score for item in selected_achievements + selected_skills)
        estimated_word_count = sum(item.estimated_word_count for item in selected_achievements + selected_skills)
        one_page_compliant = estimated_word_count <= self.max_word_count
        
        # Calculate keyword coverage
        all_keywords = set(job_analysis.required_skills + job_analysis.important_keywords)
        matched_keywords = set()
        for item in selected_achievements + selected_skills:
            matched_keywords.update(item.keywords_matched)
        keyword_coverage = len(matched_keywords) / max(len(all_keywords), 1) * 100
        
        return EnhancedContentSelectionResult(
            job_analysis_id=job_analysis.job_description_hash,
            user_profile_id=user_profile_id,
            selected_achievements=selected_achievements,
            selected_work_experiences=[],  # TODO: Add work experience selection
            selected_skills=selected_skills,
            selected_projects=[],  # TODO: Add project selection
            selected_education=[],  # TODO: Add education selection
            total_score=total_score,
            estimated_word_count=estimated_word_count,
            one_page_compliant=one_page_compliant,
            content_diversity_score=0.8,  # TODO: Calculate properly
            keyword_coverage_percentage=keyword_coverage,
            selection_algorithm="ai_primary_v1",
            selection_criteria={"method": "ai_selection", "confidence_threshold": self.ai_confidence_threshold},
            optimization_notes=[],
            ai_reasoning=ai_selection,
            ai_confidence_score=ai_selection.confidence_score,
            selection_method=SelectionMethod.AI_PRIMARY,
            fallback_applied=False
        )
    
    async def _validate_ai_selection_with_constraints(
        self, 
        ai_result: EnhancedContentSelectionResult
    ) -> EnhancedContentSelectionResult:
        """Validate AI selection against algorithmic constraints."""
        
        # Check word count constraint
        if ai_result.estimated_word_count > self.max_word_count:
            logger.warning(f"AI selection exceeds word limit ({ai_result.estimated_word_count} > {self.max_word_count})")
            # TODO: Implement constraint fixing logic
        
        # Check achievement count constraint
        if len(ai_result.selected_achievements) > self.max_achievements:
            logger.warning(f"AI selection exceeds achievement limit ({len(ai_result.selected_achievements)} > {self.max_achievements})")
            # TODO: Implement constraint fixing logic
        
        return ai_result


# Extend GeminiClient with content analysis capabilities
def extend_gemini_client():
    """Add content analysis methods to GeminiClient."""
    
    async def generate_content_analysis(self, prompt: str) -> GeminiResponse:
        """Generate content analysis using Gemini."""
        import time
        
        try:
            start_time = time.time()
            
            generation_config = {
                "temperature": 0.2,  # Lower temperature for more consistent analysis
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 2000
            }
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=generation_config
            )
            
            processing_time = time.time() - start_time
            
            return GeminiResponse(
                content=response.text,
                usage_metadata={},
                processing_time=processing_time,
                model_used=self.model_name,
                success=True
            )
            
        except Exception as e:
            processing_time = time.time() - start_time if 'start_time' in locals() else 0.0
            return GeminiResponse(
                content="",
                usage_metadata={},
                processing_time=processing_time,
                model_used=self.model_name,
                success=False,
                error_message=str(e)
            )
    
    # Add the method to the class
    GeminiClient.generate_content_analysis = generate_content_analysis


# Initialize the extension
extend_gemini_client()

# Create global instance for easy access
ai_content_selector = AIContentSelectionEngine()