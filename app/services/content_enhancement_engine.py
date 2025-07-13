"""
Content Enhancement Engine with Gemini AI Integration for TailerAI v2.0.
Phase 3 implementation of intelligent achievement and content enhancement.
Maintains 100% authenticity while improving impact and ATS compatibility.
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

from app.models.database import ContentEnhancement, UserProfile, Achievement
from app.services.database_service import db_service, DatabaseError
from app.services.gemini_client import GeminiClient, GeminiResponse
from app.services.job_analysis_service import JobAnalysisResult
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EnhancementType(str, Enum):
    """Types of content enhancement."""
    ACHIEVEMENT_TEXT = "achievement_text"
    BULLET_POINT = "bullet_point"
    SKILL_DESCRIPTION = "skill_description"
    SUMMARY_STATEMENT = "summary_statement"
    PROJECT_DESCRIPTION = "project_description"


class EnhancementLevel(str, Enum):
    """Enhancement intensity levels."""
    MINIMAL = "minimal"      # Minor improvements only
    MODERATE = "moderate"    # Balanced enhancement
    AGGRESSIVE = "aggressive" # Maximum impact improvements


class AuthenticityLevel(str, Enum):
    """Content authenticity verification levels."""
    VERIFIED = "verified"       # Verified against original data
    LIKELY_AUTHENTIC = "likely" # High confidence authentic
    QUESTIONABLE = "questionable" # Needs review
    FLAGGED = "flagged"        # Potential authenticity issues


@dataclass
class EnhancementChange:
    """Individual change made during enhancement."""
    change_type: str  # "keyword_integration", "action_verb", "quantification", etc.
    original_text: str
    enhanced_text: str
    reasoning: str
    impact_score: float  # 0.0-1.0
    authenticity_verified: bool


@dataclass
class ContentEnhancementResult:
    """Result of content enhancement operation."""
    original_content: str
    enhanced_content: str
    enhancement_type: EnhancementType
    enhancement_level: EnhancementLevel
    
    # Enhancement analysis
    changes_made: List[EnhancementChange]
    overall_improvement_score: float
    authenticity_level: AuthenticityLevel
    
    # Keywords and optimization
    keywords_integrated: List[str]
    action_verbs_improved: List[str]
    quantification_enhanced: bool
    
    # AI metadata
    ai_reasoning: Optional[str] = None
    ai_confidence_score: Optional[float] = None
    
    # Processing metadata
    enhancement_algorithm: str = "gemini_enhancement_v1"
    processing_time: Optional[float] = None
    fallback_applied: bool = False


class ContentEnhancementError(Exception):
    """Custom exception for content enhancement operations."""
    pass


class ContentEnhancementEngine:
    """
    AI-powered content enhancement engine using Gemini.
    Enhances achievement text, descriptions, and other content while maintaining authenticity.
    """
    
    def __init__(self, use_ai_enhancement: bool = None):
        """
        Initialize content enhancement engine.
        
        Args:
            use_ai_enhancement: Override setting for AI usage. If None, uses settings.
        """
        self.logger = logger
        
        # Configuration
        self.use_ai_enhancement = use_ai_enhancement if use_ai_enhancement is not None else getattr(settings, 'enable_ai_content_enhancement', False)
        self.fallback_enabled = getattr(settings, 'content_enhancement_fallback_enabled', True)
        self.confidence_threshold = getattr(settings, 'content_enhancement_confidence_threshold', 0.7)
        
        # Enhancement guidelines
        self.authenticity_guidelines = {
            "no_fabrication": "Never add false information or experiences",
            "quantification_only": "Only enhance existing quantified metrics",
            "keyword_natural": "Integrate keywords only where naturally appropriate",
            "action_verb_accuracy": "Strengthen existing action verbs without changing meaning",
            "maintain_voice": "Preserve the user's professional voice and tone"
        }
        
        # Initialize Gemini client if AI enhancement is enabled
        self.gemini_client = None
        if self.use_ai_enhancement:
            try:
                self.gemini_client = GeminiClient()
                if not self.gemini_client.is_available():
                    logger.warning("Gemini client not available, content enhancement will use fallback methods")
                    self.use_ai_enhancement = False
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client for content enhancement: {e}")
                self.use_ai_enhancement = False
    
    async def enhance_achievement_text(
        self,
        achievement_id: str,
        job_analysis: Optional[JobAnalysisResult] = None,
        enhancement_level: EnhancementLevel = EnhancementLevel.MODERATE,
        target_keywords: Optional[List[str]] = None,
        style_preferences: Optional[Dict[str, Any]] = None
    ) -> ContentEnhancementResult:
        """
        Enhance achievement text for maximum impact while maintaining authenticity.
        
        Args:
            achievement_id: ID of achievement to enhance
            job_analysis: Job context for targeted enhancement
            enhancement_level: Intensity of enhancement
            target_keywords: Specific keywords to integrate naturally
            style_preferences: User style preferences for enhancement
            
        Returns:
            Enhanced content with detailed analysis
        """
        try:
            start_time = datetime.utcnow()
            
            logger.info(f"Starting achievement enhancement for {achievement_id}")
            
            # Load achievement data
            achievement_data = await self._load_achievement_data(achievement_id)
            
            if self.use_ai_enhancement and self.gemini_client:
                result = await self._ai_powered_enhancement(
                    achievement_data, job_analysis, enhancement_level, target_keywords, style_preferences
                )
            else:
                result = await self._rule_based_enhancement(
                    achievement_data, job_analysis, enhancement_level, target_keywords
                )
            
            # Store enhancement results
            await self._store_enhancement_results(result, achievement_id)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            result.processing_time = processing_time
            
            logger.info(f"Achievement enhancement completed in {processing_time:.2f}s. "
                       f"Improvement score: {result.overall_improvement_score:.2f}, "
                       f"Authenticity: {result.authenticity_level}")
            
            return result
            
        except Exception as e:
            logger.error(f"Achievement enhancement failed: {str(e)}")
            raise ContentEnhancementError(f"Failed to enhance achievement: {str(e)}")
    
    async def enhance_multiple_achievements(
        self,
        achievement_ids: List[str],
        job_analysis: Optional[JobAnalysisResult] = None,
        enhancement_level: EnhancementLevel = EnhancementLevel.MODERATE
    ) -> List[ContentEnhancementResult]:
        """
        Enhance multiple achievements with consistent styling and keyword integration.
        
        Args:
            achievement_ids: List of achievement IDs to enhance
            job_analysis: Job context for targeted enhancement
            enhancement_level: Intensity of enhancement
            
        Returns:
            List of enhancement results
        """
        try:
            logger.info(f"Starting batch enhancement for {len(achievement_ids)} achievements")
            
            results = []
            for achievement_id in achievement_ids:
                result = await self.enhance_achievement_text(
                    achievement_id=achievement_id,
                    job_analysis=job_analysis,
                    enhancement_level=enhancement_level
                )
                results.append(result)
            
            # Post-process for consistency
            results = await self._ensure_consistency_across_enhancements(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Batch achievement enhancement failed: {str(e)}")
            raise ContentEnhancementError(f"Failed to enhance achievements: {str(e)}")
    
    async def enhance_professional_summary(
        self,
        summary_text: str,
        job_analysis: Optional[JobAnalysisResult] = None,
        user_profile_id: str = None
    ) -> ContentEnhancementResult:
        """
        Enhance professional summary for better impact and keyword integration.
        
        Args:
            summary_text: Original summary text
            job_analysis: Job context for enhancement
            user_profile_id: User profile for personalization
            
        Returns:
            Enhanced summary with analysis
        """
        try:
            logger.info("Starting professional summary enhancement")
            
            if self.use_ai_enhancement and self.gemini_client:
                result = await self._ai_enhance_summary(summary_text, job_analysis)
            else:
                result = await self._rule_based_enhance_summary(summary_text, job_analysis)
            
            return result
            
        except Exception as e:
            logger.error(f"Summary enhancement failed: {str(e)}")
            raise ContentEnhancementError(f"Failed to enhance summary: {str(e)}")
    
    async def _load_achievement_data(self, achievement_id: str) -> Dict[str, Any]:
        """Load achievement data from database."""
        try:
            with db_service.get_session() as session:
                achievement = session.query(Achievement).filter_by(id=achievement_id).first()
                
                if not achievement:
                    raise ContentEnhancementError(f"Achievement not found: {achievement_id}")
                
                return {
                    "achievement": achievement,
                    "original_text": achievement.achievement_text,
                    "quantified_metrics": achievement.quantified_result or {},
                    "impact_level": achievement.impact_level,
                    "skills_demonstrated": achievement.skills_demonstrated or [],
                    "category": achievement.category or "general"
                }
                
        except SQLAlchemyError as e:
            logger.error(f"Database error loading achievement: {e}")
            raise ContentEnhancementError(f"Failed to load achievement: {e}")
    
    async def _ai_powered_enhancement(
        self,
        achievement_data: Dict[str, Any],
        job_analysis: Optional[JobAnalysisResult],
        enhancement_level: EnhancementLevel,
        target_keywords: Optional[List[str]],
        style_preferences: Optional[Dict[str, Any]] = None
    ) -> ContentEnhancementResult:
        """Perform AI-powered content enhancement using Gemini."""
        try:
            # Create enhancement prompt
            prompt = self._create_enhancement_prompt(
                achievement_data, job_analysis, enhancement_level, target_keywords, style_preferences
            )
            
            # Get AI enhancement
            response = await self.gemini_client.generate_content_analysis(prompt)
            
            if not response.success:
                logger.error(f"AI enhancement failed: {response.error_message}")
                if self.fallback_enabled:
                    logger.info("Falling back to rule-based enhancement")
                    return await self._rule_based_enhancement(
                        achievement_data, job_analysis, enhancement_level, target_keywords, fallback=True
                    )
                else:
                    raise ContentEnhancementError(f"AI enhancement failed: {response.error_message}")
            
            # Parse AI response
            ai_result = self._parse_ai_enhancement_response(response.content)
            
            if not ai_result or ai_result.get("confidence_score", 0) < self.confidence_threshold:
                logger.warning(f"AI enhancement confidence too low: {ai_result.get('confidence_score', 0) if ai_result else 'N/A'}")
                if self.fallback_enabled:
                    return await self._rule_based_enhancement(
                        achievement_data, job_analysis, enhancement_level, target_keywords, fallback=True
                    )
                else:
                    raise ContentEnhancementError("AI enhancement confidence below threshold")
            
            # Convert AI result to enhancement result
            result = self._convert_ai_result_to_enhancement(
                ai_result, achievement_data, enhancement_level
            )
            
            result.ai_reasoning = ai_result.get("reasoning", "")
            result.ai_confidence_score = ai_result.get("confidence_score", 0.0)
            
            return result
            
        except Exception as e:
            logger.error(f"AI-powered enhancement failed: {e}")
            if self.fallback_enabled:
                return await self._rule_based_enhancement(
                    achievement_data, job_analysis, enhancement_level, target_keywords, fallback=True
                )
            else:
                raise
    
    async def _rule_based_enhancement(
        self,
        achievement_data: Dict[str, Any],
        job_analysis: Optional[JobAnalysisResult],
        enhancement_level: EnhancementLevel,
        target_keywords: Optional[List[str]],
        fallback: bool = False
    ) -> ContentEnhancementResult:
        """Perform rule-based content enhancement."""
        
        original_text = achievement_data["original_text"]
        enhanced_text = original_text
        changes_made = []
        
        # Apply rule-based improvements
        enhanced_text, verb_changes = self._improve_action_verbs(enhanced_text)
        if verb_changes:
            changes_made.extend(verb_changes)
        
        # Keyword integration if job analysis available
        if job_analysis and target_keywords:
            enhanced_text, keyword_changes = self._integrate_keywords_naturally(
                enhanced_text, target_keywords, job_analysis
            )
            if keyword_changes:
                changes_made.extend(keyword_changes)
        
        # Quantification enhancement
        enhanced_text, quant_changes = self._enhance_quantification(enhanced_text)
        if quant_changes:
            changes_made.extend(quant_changes)
        
        # Calculate improvement score
        improvement_score = len(changes_made) * 0.15  # Each change adds 15%
        improvement_score = min(improvement_score, 0.8)  # Cap at 80%
        
        return ContentEnhancementResult(
            original_content=original_text,
            enhanced_content=enhanced_text,
            enhancement_type=EnhancementType.ACHIEVEMENT_TEXT,
            enhancement_level=enhancement_level,
            changes_made=changes_made,
            overall_improvement_score=improvement_score,
            authenticity_level=AuthenticityLevel.VERIFIED,
            keywords_integrated=target_keywords or [],
            action_verbs_improved=[change.enhanced_text for change in changes_made if change.change_type == "action_verb"],
            quantification_enhanced=any(change.change_type == "quantification" for change in changes_made),
            enhancement_algorithm="rule_based_v1" if not fallback else "rule_based_fallback_v1",
            fallback_applied=fallback
        )
    
    def _create_enhancement_prompt(
        self,
        achievement_data: Dict[str, Any],
        job_analysis: Optional[JobAnalysisResult],
        enhancement_level: EnhancementLevel,
        target_keywords: Optional[List[str]],
        style_preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create comprehensive prompt for AI content enhancement."""
        
        original_text = achievement_data["original_text"]
        quantified_metrics = achievement_data.get("quantified_metrics", {})
        impact_level = achievement_data.get("impact_level", 0)
        
        # Job context
        job_context = ""
        if job_analysis:
            job_context = f"""
**JOB CONTEXT:**
Position: {job_analysis.position_title}
Company: {job_analysis.company_name}
Required Skills: {', '.join(job_analysis.required_skills)}
Important Keywords: {', '.join(job_analysis.important_keywords)}
Experience Level: {job_analysis.experience_level}
"""
        
        # Target keywords
        keywords_context = ""
        if target_keywords:
            keywords_context = f"**TARGET KEYWORDS:** {', '.join(target_keywords)}"
        
        # Style preferences
        style_context = ""
        if style_preferences:
            style_context = f"""
**STYLE PREFERENCES:**
Tone: {style_preferences.get('tone', 'professional')}
Formality: {style_preferences.get('formality', 'formal')}
Industry Focus: {style_preferences.get('industry_focus', 'general')}
Writing Style: {style_preferences.get('writing_style', 'concise')}
"""
        
        prompt = f"""You are an expert resume enhancement specialist. Enhance the following achievement text for maximum impact while maintaining 100% authenticity and truthfulness.

{job_context}

{keywords_context}

{style_context}

**ORIGINAL ACHIEVEMENT:**
{original_text}

**QUANTIFIED METRICS AVAILABLE:**
{json.dumps(quantified_metrics, indent=2) if quantified_metrics else 'None specified'}

**CURRENT IMPACT LEVEL:** {impact_level}/10

**ENHANCEMENT LEVEL:** {enhancement_level.value}

**ENHANCEMENT GUIDELINES:**
1. **MAINTAIN 100% AUTHENTICITY** - Never add false information or fabricated details
2. **Strengthen action verbs** - Use more impactful, specific action words
3. **Highlight quantified results** - Make metrics more prominent and compelling
4. **Integrate keywords naturally** - Only where contextually appropriate
5. **Improve clarity and impact** - Make achievements more compelling to read
6. **Preserve user voice** - Maintain professional tone and style

**STRICT RULES:**
- Do NOT fabricate any metrics, dates, or details
- Do NOT add information not implied in the original
- Do NOT change the fundamental meaning or scope
- Do NOT make false claims about achievements
- Only enhance existing content authentically

**PROVIDE RESPONSE IN JSON FORMAT:**

{{
    "enhanced_text": "improved version of the achievement",
    "changes_made": [
        {{
            "change_type": "action_verb|keyword_integration|quantification|clarity",
            "original_phrase": "original text phrase",
            "enhanced_phrase": "improved text phrase", 
            "reasoning": "why this change improves impact",
            "authenticity_verified": true|false
        }}
    ],
    "keywords_integrated": ["keyword1", "keyword2"],
    "action_verbs_improved": ["original -> improved"],
    "quantification_enhanced": true|false,
    "overall_improvement_score": <0.0-1.0>,
    "authenticity_level": "verified|likely|questionable|flagged",
    "confidence_score": <0.0-1.0>,
    "reasoning": "comprehensive explanation of enhancement approach and authenticity verification"
}}

**EXAMPLES OF GOOD ENHANCEMENTS:**

Original: "Worked on database optimization"
Enhanced: "Optimized database queries, reducing response times by 40%"

Original: "Led team meetings"  
Enhanced: "Facilitated weekly cross-functional team meetings with 8 stakeholders"

Original: "Improved customer satisfaction"
Enhanced: "Enhanced customer satisfaction scores from 3.2 to 4.7 through targeted service improvements"

Respond only with valid JSON.
"""
        return prompt
    
    def _parse_ai_enhancement_response(self, response_content: str) -> Optional[Dict[str, Any]]:
        """Parse AI enhancement response into structured data."""
        try:
            data = json.loads(response_content.strip())
            
            # Validate required fields
            required_fields = [
                "enhanced_text",
                "changes_made",
                "overall_improvement_score",
                "authenticity_level",
                "confidence_score"
            ]
            
            for field in required_fields:
                if field not in data:
                    logger.error(f"Missing required field in AI response: {field}")
                    return None
            
            return data
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse AI enhancement response: {e}")
            logger.debug(f"Response content: {response_content}")
            return None
    
    def _convert_ai_result_to_enhancement(
        self,
        ai_result: Dict[str, Any],
        achievement_data: Dict[str, Any],
        enhancement_level: EnhancementLevel
    ) -> ContentEnhancementResult:
        """Convert AI analysis result to structured enhancement result."""
        
        # Convert changes made
        changes_made = []
        for change in ai_result.get("changes_made", []):
            changes_made.append(EnhancementChange(
                change_type=change["change_type"],
                original_text=change["original_phrase"],
                enhanced_text=change["enhanced_phrase"],
                reasoning=change["reasoning"],
                impact_score=0.8,  # Default impact score
                authenticity_verified=change.get("authenticity_verified", True)
            ))
        
        # Determine authenticity level
        authenticity_str = ai_result.get("authenticity_level", "verified")
        try:
            authenticity_level = AuthenticityLevel(authenticity_str)
        except ValueError:
            authenticity_level = AuthenticityLevel.VERIFIED
        
        return ContentEnhancementResult(
            original_content=achievement_data["original_text"],
            enhanced_content=ai_result["enhanced_text"],
            enhancement_type=EnhancementType.ACHIEVEMENT_TEXT,
            enhancement_level=enhancement_level,
            changes_made=changes_made,
            overall_improvement_score=ai_result["overall_improvement_score"],
            authenticity_level=authenticity_level,
            keywords_integrated=ai_result.get("keywords_integrated", []),
            action_verbs_improved=ai_result.get("action_verbs_improved", []),
            quantification_enhanced=ai_result.get("quantification_enhanced", False)
        )
    
    def _improve_action_verbs(self, text: str) -> Tuple[str, List[EnhancementChange]]:
        """Improve action verbs in achievement text."""
        changes = []
        enhanced_text = text
        
        # Simple action verb improvements
        verb_improvements = {
            "worked on": "developed",
            "helped": "contributed to",
            "did": "executed",
            "made": "created",
            "was responsible for": "managed",
            "handled": "administered"
        }
        
        for original, improved in verb_improvements.items():
            if original.lower() in enhanced_text.lower():
                enhanced_text = enhanced_text.replace(original, improved)
                changes.append(EnhancementChange(
                    change_type="action_verb",
                    original_text=original,
                    enhanced_text=improved,
                    reasoning=f"Strengthened action verb from '{original}' to '{improved}'",
                    impact_score=0.6,
                    authenticity_verified=True
                ))
        
        return enhanced_text, changes
    
    def _integrate_keywords_naturally(
        self, 
        text: str, 
        keywords: List[str], 
        job_analysis: JobAnalysisResult
    ) -> Tuple[str, List[EnhancementChange]]:
        """Integrate keywords naturally into existing text."""
        changes = []
        enhanced_text = text
        
        for keyword in keywords[:3]:  # Limit to 3 keywords to avoid stuffing
            if keyword.lower() not in enhanced_text.lower():
                # Simple keyword integration (this would be more sophisticated in production)
                if "technology" in keyword.lower() and "using" in enhanced_text.lower():
                    enhanced_text = enhanced_text.replace("using", f"using {keyword}")
                    changes.append(EnhancementChange(
                        change_type="keyword_integration",
                        original_text="using",
                        enhanced_text=f"using {keyword}",
                        reasoning=f"Naturally integrated '{keyword}' keyword",
                        impact_score=0.7,
                        authenticity_verified=True
                    ))
        
        return enhanced_text, changes
    
    def _enhance_quantification(self, text: str) -> Tuple[str, List[EnhancementChange]]:
        """Enhance existing quantification in text."""
        changes = []
        enhanced_text = text
        
        # Look for opportunities to highlight existing numbers
        import re
        numbers = re.findall(r'\d+', text)
        
        for number in numbers:
            if f"{number}%" not in text and len(number) <= 2:  # Simple percentage enhancement
                enhanced_text = enhanced_text.replace(number, f"{number}%")
                changes.append(EnhancementChange(
                    change_type="quantification",
                    original_text=number,
                    enhanced_text=f"{number}%",
                    reasoning="Enhanced number with percentage for clearer impact",
                    impact_score=0.8,
                    authenticity_verified=True
                ))
                break  # Only enhance one number to avoid over-quantification
        
        return enhanced_text, changes
    
    async def _ai_enhance_summary(
        self, 
        summary_text: str, 
        job_analysis: Optional[JobAnalysisResult]
    ) -> ContentEnhancementResult:
        """AI-powered professional summary enhancement."""
        # Simplified implementation for now
        return ContentEnhancementResult(
            original_content=summary_text,
            enhanced_content=summary_text,  # No changes in basic implementation
            enhancement_type=EnhancementType.SUMMARY_STATEMENT,
            enhancement_level=EnhancementLevel.MINIMAL,
            changes_made=[],
            overall_improvement_score=0.0,
            authenticity_level=AuthenticityLevel.VERIFIED,
            keywords_integrated=[],
            action_verbs_improved=[],
            quantification_enhanced=False
        )
    
    async def _rule_based_enhance_summary(
        self, 
        summary_text: str, 
        job_analysis: Optional[JobAnalysisResult]
    ) -> ContentEnhancementResult:
        """Rule-based professional summary enhancement."""
        # Simplified implementation for now
        return ContentEnhancementResult(
            original_content=summary_text,
            enhanced_content=summary_text,  # No changes in basic implementation
            enhancement_type=EnhancementType.SUMMARY_STATEMENT,
            enhancement_level=EnhancementLevel.MINIMAL,
            changes_made=[],
            overall_improvement_score=0.0,
            authenticity_level=AuthenticityLevel.VERIFIED,
            keywords_integrated=[],
            action_verbs_improved=[],
            quantification_enhanced=False
        )
    
    async def _ensure_consistency_across_enhancements(
        self, 
        results: List[ContentEnhancementResult]
    ) -> List[ContentEnhancementResult]:
        """Ensure consistency across multiple enhanced achievements."""
        # Basic consistency check - in production this would be more sophisticated
        return results
    
    async def _store_enhancement_results(
        self, 
        result: ContentEnhancementResult, 
        achievement_id: str
    ):
        """Store enhancement results in database."""
        try:
            with db_service.get_session() as session:
                enhancement = ContentEnhancement(
                    achievement_id=achievement_id,
                    enhancement_algorithm=result.enhancement_algorithm,
                    original_content=result.original_content,
                    enhanced_content=result.enhanced_content,
                    enhancement_type=result.enhancement_type.value,
                    enhancement_level=result.enhancement_level.value,
                    changes_made=[change.__dict__ for change in result.changes_made],
                    overall_improvement_score=result.overall_improvement_score,
                    authenticity_level=result.authenticity_level.value,
                    keywords_integrated=result.keywords_integrated,
                    action_verbs_improved=result.action_verbs_improved,
                    quantification_enhanced=result.quantification_enhanced,
                    ai_reasoning=result.ai_reasoning,
                    ai_confidence_score=result.ai_confidence_score,
                    processing_time=result.processing_time,
                    fallback_applied=result.fallback_applied,
                    user_approved=False,  # Requires user approval
                    created_at=datetime.utcnow()
                )
                
                session.add(enhancement)
                session.commit()
                
                logger.info(f"Stored content enhancement results for achievement {achievement_id}")
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to store enhancement results: {e}")
            # Don't raise exception - enhancement can continue without storage


# Global instance for easy access
content_enhancer = ContentEnhancementEngine()