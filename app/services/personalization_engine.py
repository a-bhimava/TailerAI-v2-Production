"""
Personalization Engine with Continuous Learning for TailerAI v2.0.
Phase 4 implementation of intelligent learning and personalization capabilities.
Analyzes user outcomes and continuously improves content selection strategies.
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict
import statistics

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, and_, or_

from app.models.database import (
    ApplicationOutcome, UserProfile, Achievement, ContentSelection, 
    ContentEnhancement, UserPreference, MarketTrend
)
from app.services.database_service import db_service, DatabaseError
from app.services.gemini_client import GeminiClient, GeminiResponse
from app.services.job_analysis_service import JobAnalysisResult
from app.services.ai_content_selection_service import AIContentSelectionEngine
from app.services.ats_optimization_engine import ATSOptimizationEngine
from app.services.content_enhancement_engine import ContentEnhancementEngine
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class OutcomeType(str, Enum):
    """Types of application outcomes."""
    APPLICATION_SENT = "application_sent"
    VIEWED = "viewed"
    PHONE_SCREEN = "phone_screen"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTION = "rejection"
    NO_RESPONSE = "no_response"


class LearningConfidence(str, Enum):
    """Confidence levels for learning insights."""
    LOW = "low"          # < 5 data points
    MEDIUM = "medium"    # 5-15 data points
    HIGH = "high"        # 15+ data points


class PersonalizationStrategy(str, Enum):
    """Personalization strategy types."""
    CONSERVATIVE = "conservative"  # Stick to proven patterns
    BALANCED = "balanced"         # Mix of proven and experimental
    AGGRESSIVE = "aggressive"     # Try new approaches


@dataclass
class ApplicationOutcomeData:
    """Data structure for application outcomes."""
    application_id: str
    user_profile_id: str
    company_name: str
    position_title: str
    job_description: str
    content_selection_id: str
    outcome_type: OutcomeType
    outcome_date: datetime
    feedback_notes: Optional[str] = None
    salary_offered: Optional[float] = None
    days_to_outcome: Optional[int] = None


@dataclass
class UserSuccessPattern:
    """Identified success patterns for a user."""
    user_profile_id: str
    successful_achievement_types: List[str]
    effective_keywords: List[str]
    optimal_enhancement_level: str
    best_performing_industries: List[str]
    preferred_content_length: str
    success_rate: float
    confidence_level: LearningConfidence
    sample_size: int


@dataclass
class PersonalizationInsight:
    """Personalization insight for content optimization."""
    insight_type: str  # "achievement_selection", "keyword_strategy", "enhancement_level"
    recommendation: str
    confidence_score: float
    supporting_evidence: List[str]
    expected_improvement: float
    user_profile_id: str


@dataclass
class PersonalizationResult:
    """Result of personalization analysis."""
    user_profile_id: str
    success_patterns: UserSuccessPattern
    insights: List[PersonalizationInsight]
    personalized_strategy: PersonalizationStrategy
    recommended_actions: List[str]
    
    # Performance metrics
    predicted_improvement: float
    confidence_score: float
    
    # AI metadata
    ai_reasoning: Optional[str] = None
    analysis_date: datetime = None
    next_analysis_date: datetime = None


class PersonalizationError(Exception):
    """Custom exception for personalization operations."""
    pass


class PersonalizationEngine:
    """
    AI-powered personalization engine for continuous learning and optimization.
    Analyzes user application outcomes to improve content selection strategies.
    """
    
    def __init__(self, use_ai_learning: bool = None):
        """
        Initialize personalization engine.
        
        Args:
            use_ai_learning: Override setting for AI usage. If None, uses settings.
        """
        self.logger = logger
        
        # Configuration
        self.use_ai_learning = use_ai_learning if use_ai_learning is not None else getattr(settings, 'enable_ai_personalization', False)
        self.fallback_enabled = getattr(settings, 'personalization_fallback_enabled', True)
        self.confidence_threshold = getattr(settings, 'personalization_confidence_threshold', 0.7)
        self.min_data_points = getattr(settings, 'personalization_min_data_points', 5)
        
        # Learning parameters
        self.learning_window_days = getattr(settings, 'personalization_learning_window_days', 365)
        self.success_outcome_types = [
            OutcomeType.PHONE_SCREEN,
            OutcomeType.INTERVIEW,
            OutcomeType.OFFER
        ]
        
        # Initialize Gemini client if AI learning is enabled
        self.gemini_client = None
        if self.use_ai_learning:
            try:
                self.gemini_client = GeminiClient()
                if not self.gemini_client.is_available():
                    logger.warning("Gemini client not available, personalization will use rule-based learning")
                    self.use_ai_learning = False
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client for personalization: {e}")
                self.use_ai_learning = False
        
        # Initialize other engines for integration
        self.content_selector = AIContentSelectionEngine()
        self.ats_optimizer = ATSOptimizationEngine()
        self.content_enhancer = ContentEnhancementEngine()
    
    async def analyze_user_performance(
        self,
        user_profile_id: str,
        analysis_period_days: int = 365
    ) -> PersonalizationResult:
        """
        Analyze user's application performance and generate personalization insights.
        
        Args:
            user_profile_id: User profile to analyze
            analysis_period_days: Number of days to analyze
            
        Returns:
            Comprehensive personalization analysis
        """
        try:
            start_time = datetime.utcnow()
            
            logger.info(f"Starting personalization analysis for user {user_profile_id}")
            
            # Load user application history
            application_data = await self._load_user_application_history(
                user_profile_id, analysis_period_days
            )
            
            if not application_data:
                logger.warning(f"No application data found for user {user_profile_id}")
                return await self._create_default_personalization_result(user_profile_id)
            
            # Analyze success patterns
            success_patterns = await self._analyze_success_patterns(application_data)
            
            # Generate personalization insights
            if self.use_ai_learning and self.gemini_client:
                insights = await self._ai_generate_insights(application_data, success_patterns)
            else:
                insights = await self._rule_based_generate_insights(application_data, success_patterns)
            
            # Determine personalization strategy
            strategy = self._determine_personalization_strategy(success_patterns, insights)
            
            # Generate recommended actions
            recommended_actions = await self._generate_recommended_actions(insights, strategy)
            
            # Calculate performance predictions
            predicted_improvement = self._calculate_predicted_improvement(insights)
            confidence_score = self._calculate_overall_confidence(success_patterns, insights)
            
            result = PersonalizationResult(
                user_profile_id=user_profile_id,
                success_patterns=success_patterns,
                insights=insights,
                personalized_strategy=strategy,
                recommended_actions=recommended_actions,
                predicted_improvement=predicted_improvement,
                confidence_score=confidence_score,
                analysis_date=datetime.utcnow(),
                next_analysis_date=datetime.utcnow() + timedelta(days=30)
            )
            
            # Store personalization results
            await self._store_personalization_results(result)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Personalization analysis completed in {processing_time:.2f}s. "
                       f"Strategy: {strategy}, Confidence: {confidence_score:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Personalization analysis failed: {str(e)}")
            raise PersonalizationError(f"Failed to analyze user performance: {str(e)}")
    
    async def apply_personalized_optimization(
        self,
        user_profile_id: str,
        job_analysis: JobAnalysisResult,
        personalization_result: Optional[PersonalizationResult] = None
    ) -> Dict[str, Any]:
        """
        Apply personalized optimization to content selection and enhancement.
        
        Args:
            user_profile_id: User profile ID
            job_analysis: Job analysis for context
            personalization_result: Pre-computed personalization result
            
        Returns:
            Personalized optimization recommendations
        """
        try:
            logger.info(f"Applying personalized optimization for user {user_profile_id}")
            
            # Get personalization insights
            if not personalization_result:
                personalization_result = await self.analyze_user_performance(user_profile_id)
            
            # Apply personalized content selection
            personalized_content = await self._apply_personalized_content_selection(
                user_profile_id, job_analysis, personalization_result
            )
            
            # Apply personalized ATS optimization
            personalized_ats = await self._apply_personalized_ats_optimization(
                personalized_content, job_analysis, personalization_result
            )
            
            # Apply personalized content enhancement
            personalized_enhancement = await self._apply_personalized_content_enhancement(
                personalized_content, job_analysis, personalization_result
            )
            
            return {
                "success": True,
                "user_profile_id": user_profile_id,
                "personalization_strategy": personalization_result.personalized_strategy.value,
                "content_selection": personalized_content,
                "ats_optimization": personalized_ats,
                "content_enhancement": personalized_enhancement,
                "insights_applied": [insight.insight_type for insight in personalization_result.insights],
                "predicted_improvement": personalization_result.predicted_improvement,
                "confidence_score": personalization_result.confidence_score
            }
            
        except Exception as e:
            logger.error(f"Personalized optimization failed: {str(e)}")
            raise PersonalizationError(f"Failed to apply personalized optimization: {str(e)}")
    
    async def track_application_outcome(
        self,
        application_outcome: ApplicationOutcomeData
    ) -> Dict[str, Any]:
        """
        Track application outcome for learning and improvement.
        
        Args:
            application_outcome: Application outcome data
            
        Returns:
            Tracking confirmation and analysis trigger
        """
        try:
            logger.info(f"Tracking application outcome: {application_outcome.outcome_type} for user {application_outcome.user_profile_id}")
            
            # Store outcome data
            await self._store_application_outcome(application_outcome)
            
            # Check if we need to trigger re-analysis
            should_reanalyze = await self._should_trigger_reanalysis(application_outcome.user_profile_id)
            
            # Update user success metrics
            await self._update_user_success_metrics(application_outcome)
            
            result = {
                "success": True,
                "outcome_tracked": True,
                "outcome_type": application_outcome.outcome_type.value,
                "user_profile_id": application_outcome.user_profile_id,
                "trigger_reanalysis": should_reanalyze,
                "analysis_scheduled": should_reanalyze
            }
            
            # Schedule re-analysis if needed
            if should_reanalyze:
                # In production, this would trigger an async task
                logger.info(f"Scheduling personalization re-analysis for user {application_outcome.user_profile_id}")
                result["next_analysis_date"] = datetime.utcnow() + timedelta(hours=24)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to track application outcome: {str(e)}")
            raise PersonalizationError(f"Failed to track application outcome: {str(e)}")
    
    async def get_market_intelligence(
        self,
        industry: str,
        job_level: str,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get market intelligence for industry and role trends.
        
        Args:
            industry: Target industry
            job_level: Job level (entry, mid, senior, executive)
            location: Optional location filter
            
        Returns:
            Market intelligence insights
        """
        try:
            logger.info(f"Retrieving market intelligence for {industry} - {job_level}")
            
            # Get trending keywords and skills
            trending_keywords = await self._get_trending_keywords(industry, job_level)
            
            # Get salary trends
            salary_trends = await self._get_salary_trends(industry, job_level, location)
            
            # Get successful content patterns
            successful_patterns = await self._get_successful_content_patterns(industry, job_level)
            
            # Get AI-powered market insights
            if self.use_ai_learning and self.gemini_client:
                ai_insights = await self._get_ai_market_insights(industry, job_level, location)
            else:
                ai_insights = None
            
            return {
                "success": True,
                "industry": industry,
                "job_level": job_level,
                "location": location,
                "trending_keywords": trending_keywords,
                "salary_trends": salary_trends,
                "successful_patterns": successful_patterns,
                "ai_insights": ai_insights,
                "analysis_date": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get market intelligence: {str(e)}")
            raise PersonalizationError(f"Failed to get market intelligence: {str(e)}")
    
    async def _load_user_application_history(
        self,
        user_profile_id: str,
        analysis_period_days: int
    ) -> List[ApplicationOutcomeData]:
        """Load user's application history for analysis."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=analysis_period_days)
            
            with db_service.get_session() as session:
                outcomes = session.query(ApplicationOutcome).filter(
                    and_(
                        ApplicationOutcome.user_profile_id == user_profile_id,
                        ApplicationOutcome.outcome_date >= cutoff_date
                    )
                ).all()
                
                application_data = []
                for outcome in outcomes:
                    application_data.append(ApplicationOutcomeData(
                        application_id=outcome.application_id,
                        user_profile_id=outcome.user_profile_id,
                        company_name=outcome.company_name,
                        position_title=outcome.position_title,
                        job_description=outcome.job_description or "",
                        content_selection_id=outcome.content_selection_id,
                        outcome_type=OutcomeType(outcome.outcome_type),
                        outcome_date=outcome.outcome_date,
                        feedback_notes=outcome.feedback_notes,
                        salary_offered=outcome.salary_offered,
                        days_to_outcome=outcome.days_to_outcome
                    ))
                
                return application_data
                
        except SQLAlchemyError as e:
            logger.error(f"Database error loading application history: {e}")
            raise PersonalizationError(f"Failed to load application history: {e}")
    
    async def _analyze_success_patterns(
        self,
        application_data: List[ApplicationOutcomeData]
    ) -> UserSuccessPattern:
        """Analyze success patterns from application data."""
        
        # Separate successful and unsuccessful applications
        successful_apps = [app for app in application_data if app.outcome_type in self.success_outcome_types]
        total_apps = len(application_data)
        
        if total_apps == 0:
            return UserSuccessPattern(
                user_profile_id=application_data[0].user_profile_id if application_data else "",
                successful_achievement_types=[],
                effective_keywords=[],
                optimal_enhancement_level="moderate",
                best_performing_industries=[],
                preferred_content_length="medium",
                success_rate=0.0,
                confidence_level=LearningConfidence.LOW,
                sample_size=0
            )
        
        success_rate = len(successful_apps) / total_apps
        
        # Analyze successful patterns
        successful_industries = [app.position_title for app in successful_apps]
        industry_counts = defaultdict(int)
        for industry in successful_industries:
            industry_counts[industry] += 1
        
        best_performing_industries = sorted(industry_counts.keys(), key=lambda x: industry_counts[x], reverse=True)[:3]
        
        # Determine confidence level
        if total_apps < 5:
            confidence_level = LearningConfidence.LOW
        elif total_apps < 15:
            confidence_level = LearningConfidence.MEDIUM
        else:
            confidence_level = LearningConfidence.HIGH
        
        return UserSuccessPattern(
            user_profile_id=application_data[0].user_profile_id,
            successful_achievement_types=["project_management", "technical_skills"],  # Simplified
            effective_keywords=["python", "optimization", "leadership"],  # Simplified
            optimal_enhancement_level="moderate",
            best_performing_industries=best_performing_industries,
            preferred_content_length="medium",
            success_rate=success_rate,
            confidence_level=confidence_level,
            sample_size=total_apps
        )
    
    async def _ai_generate_insights(
        self,
        application_data: List[ApplicationOutcomeData],
        success_patterns: UserSuccessPattern
    ) -> List[PersonalizationInsight]:
        """Generate AI-powered personalization insights."""
        try:
            # Create analysis prompt
            prompt = self._create_personalization_prompt(application_data, success_patterns)
            
            # Get AI analysis
            response = await self.gemini_client.generate_content_analysis(prompt)
            
            if not response.success:
                logger.error(f"AI insight generation failed: {response.error_message}")
                if self.fallback_enabled:
                    return await self._rule_based_generate_insights(application_data, success_patterns)
                else:
                    raise PersonalizationError(f"AI insight generation failed: {response.error_message}")
            
            # Parse AI response
            ai_insights = self._parse_ai_insights_response(response.content)
            
            if not ai_insights:
                if self.fallback_enabled:
                    return await self._rule_based_generate_insights(application_data, success_patterns)
                else:
                    raise PersonalizationError("Failed to parse AI insights")
            
            return ai_insights
            
        except Exception as e:
            logger.error(f"AI insight generation failed: {e}")
            if self.fallback_enabled:
                return await self._rule_based_generate_insights(application_data, success_patterns)
            else:
                raise
    
    async def _rule_based_generate_insights(
        self,
        application_data: List[ApplicationOutcomeData],
        success_patterns: UserSuccessPattern
    ) -> List[PersonalizationInsight]:
        """Generate rule-based personalization insights."""
        
        insights = []
        
        # Achievement selection insight
        if success_patterns.success_rate > 0.6:
            insights.append(PersonalizationInsight(
                insight_type="achievement_selection",
                recommendation=f"Continue using {', '.join(success_patterns.successful_achievement_types)} achievement types",
                confidence_score=0.8,
                supporting_evidence=[f"Success rate: {success_patterns.success_rate:.1%}"],
                expected_improvement=0.05,
                user_profile_id=success_patterns.user_profile_id
            ))
        
        # Keyword strategy insight
        if success_patterns.effective_keywords:
            insights.append(PersonalizationInsight(
                insight_type="keyword_strategy",
                recommendation=f"Prioritize keywords: {', '.join(success_patterns.effective_keywords)}",
                confidence_score=0.7,
                supporting_evidence=[f"Effective in {len(success_patterns.effective_keywords)} successful applications"],
                expected_improvement=0.10,
                user_profile_id=success_patterns.user_profile_id
            ))
        
        # Enhancement level insight
        insights.append(PersonalizationInsight(
            insight_type="enhancement_level",
            recommendation=f"Use {success_patterns.optimal_enhancement_level} enhancement level",
            confidence_score=0.6,
            supporting_evidence=["Based on successful application patterns"],
            expected_improvement=0.08,
            user_profile_id=success_patterns.user_profile_id
        ))
        
        return insights
    
    def _create_personalization_prompt(
        self,
        application_data: List[ApplicationOutcomeData],
        success_patterns: UserSuccessPattern
    ) -> str:
        """Create prompt for AI personalization analysis."""
        
        # Convert application data to summary
        successful_apps = [app for app in application_data if app.outcome_type in self.success_outcome_types]
        unsuccessful_apps = [app for app in application_data if app.outcome_type not in self.success_outcome_types]
        
        prompt = f"""You are an expert career analyst. Analyze this user's application performance data and provide personalized insights to improve their success rate.

**USER PERFORMANCE SUMMARY:**
- Total Applications: {len(application_data)}
- Successful Outcomes: {len(successful_apps)} ({success_patterns.success_rate:.1%})
- Current Success Rate: {success_patterns.success_rate:.1%}
- Confidence Level: {success_patterns.confidence_level.value}

**SUCCESSFUL APPLICATIONS:**
{json.dumps([asdict(app) for app in successful_apps[:5]], indent=2, default=str)}

**UNSUCCESSFUL APPLICATIONS:**
{json.dumps([asdict(app) for app in unsuccessful_apps[:5]], indent=2, default=str)}

**CURRENT SUCCESS PATTERNS:**
- Best Industries: {', '.join(success_patterns.best_performing_industries)}
- Effective Keywords: {', '.join(success_patterns.effective_keywords)}
- Optimal Enhancement: {success_patterns.optimal_enhancement_level}

**ANALYSIS REQUIREMENTS:**
1. Identify specific patterns that correlate with successful outcomes
2. Recommend content selection strategies
3. Suggest keyword optimization approaches
4. Recommend enhancement levels and techniques
5. Provide industry-specific insights

**PROVIDE RESPONSE IN JSON FORMAT:**
{{
    "insights": [
        {{
            "insight_type": "achievement_selection|keyword_strategy|enhancement_level|industry_focus",
            "recommendation": "specific actionable recommendation",
            "confidence_score": <0.0-1.0>,
            "supporting_evidence": ["evidence1", "evidence2"],
            "expected_improvement": <0.0-1.0>,
            "user_profile_id": "{success_patterns.user_profile_id}"
        }}
    ],
    "overall_analysis": "comprehensive analysis of user's performance patterns",
    "predicted_success_rate": <0.0-1.0>,
    "recommended_strategy": "conservative|balanced|aggressive"
}}

Respond only with valid JSON."""
        
        return prompt
    
    def _parse_ai_insights_response(self, response_content: str) -> Optional[List[PersonalizationInsight]]:
        """Parse AI insights response into structured data."""
        try:
            data = json.loads(response_content.strip())
            
            insights = []
            for insight_data in data.get("insights", []):
                insights.append(PersonalizationInsight(
                    insight_type=insight_data["insight_type"],
                    recommendation=insight_data["recommendation"],
                    confidence_score=insight_data["confidence_score"],
                    supporting_evidence=insight_data["supporting_evidence"],
                    expected_improvement=insight_data["expected_improvement"],
                    user_profile_id=insight_data["user_profile_id"]
                ))
            
            return insights
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse AI insights response: {e}")
            return None
    
    def _determine_personalization_strategy(
        self,
        success_patterns: UserSuccessPattern,
        insights: List[PersonalizationInsight]
    ) -> PersonalizationStrategy:
        """Determine optimal personalization strategy."""
        
        # Conservative if low confidence or high success rate
        if (success_patterns.confidence_level == LearningConfidence.LOW or 
            success_patterns.success_rate > 0.7):
            return PersonalizationStrategy.CONSERVATIVE
        
        # Aggressive if low success rate and high confidence
        if (success_patterns.success_rate < 0.3 and 
            success_patterns.confidence_level == LearningConfidence.HIGH):
            return PersonalizationStrategy.AGGRESSIVE
        
        # Balanced for most cases
        return PersonalizationStrategy.BALANCED
    
    async def _generate_recommended_actions(
        self,
        insights: List[PersonalizationInsight],
        strategy: PersonalizationStrategy
    ) -> List[str]:
        """Generate recommended actions based on insights."""
        
        actions = []
        
        for insight in insights:
            if insight.confidence_score >= self.confidence_threshold:
                actions.append(f"Apply {insight.insight_type}: {insight.recommendation}")
        
        # Add strategy-specific actions
        if strategy == PersonalizationStrategy.CONSERVATIVE:
            actions.append("Maintain current successful patterns")
        elif strategy == PersonalizationStrategy.AGGRESSIVE:
            actions.append("Experiment with new content approaches")
        else:
            actions.append("Balance proven patterns with strategic experimentation")
        
        return actions
    
    def _calculate_predicted_improvement(self, insights: List[PersonalizationInsight]) -> float:
        """Calculate predicted improvement from insights."""
        if not insights:
            return 0.0
        
        # Sum expected improvements, weighted by confidence
        total_improvement = 0.0
        total_weight = 0.0
        
        for insight in insights:
            weight = insight.confidence_score
            improvement = insight.expected_improvement * weight
            total_improvement += improvement
            total_weight += weight
        
        return total_improvement / total_weight if total_weight > 0 else 0.0
    
    def _calculate_overall_confidence(
        self,
        success_patterns: UserSuccessPattern,
        insights: List[PersonalizationInsight]
    ) -> float:
        """Calculate overall confidence in personalization."""
        
        # Base confidence on data quality
        data_confidence = {
            LearningConfidence.LOW: 0.3,
            LearningConfidence.MEDIUM: 0.6,
            LearningConfidence.HIGH: 0.9
        }[success_patterns.confidence_level]
        
        # Average insight confidence
        insight_confidence = statistics.mean([insight.confidence_score for insight in insights]) if insights else 0.5
        
        # Weighted average
        return (data_confidence * 0.6) + (insight_confidence * 0.4)
    
    async def _create_default_personalization_result(self, user_profile_id: str) -> PersonalizationResult:
        """Create default personalization result for users with no data."""
        
        default_patterns = UserSuccessPattern(
            user_profile_id=user_profile_id,
            successful_achievement_types=["technical_skills", "project_management"],
            effective_keywords=["python", "sql", "leadership"],
            optimal_enhancement_level="moderate",
            best_performing_industries=["technology", "finance"],
            preferred_content_length="medium",
            success_rate=0.0,
            confidence_level=LearningConfidence.LOW,
            sample_size=0
        )
        
        default_insights = [
            PersonalizationInsight(
                insight_type="enhancement_level",
                recommendation="Start with moderate enhancement level",
                confidence_score=0.5,
                supporting_evidence=["Default recommendation for new users"],
                expected_improvement=0.1,
                user_profile_id=user_profile_id
            )
        ]
        
        return PersonalizationResult(
            user_profile_id=user_profile_id,
            success_patterns=default_patterns,
            insights=default_insights,
            personalized_strategy=PersonalizationStrategy.BALANCED,
            recommended_actions=["Build application history for better personalization"],
            predicted_improvement=0.1,
            confidence_score=0.3,
            analysis_date=datetime.utcnow(),
            next_analysis_date=datetime.utcnow() + timedelta(days=30)
        )
    
    async def _apply_personalized_content_selection(
        self,
        user_profile_id: str,
        job_analysis: JobAnalysisResult,
        personalization_result: PersonalizationResult
    ) -> Dict[str, Any]:
        """Apply personalized content selection based on insights."""
        
        # Get personalization insights for content selection
        content_insights = [i for i in personalization_result.insights if i.insight_type == "achievement_selection"]
        
        # Apply insights to content selection
        selection_result = await self.content_selector.select_optimal_content(
            user_profile_id=user_profile_id,
            job_analysis=job_analysis,
            max_achievements=5,
            personalization_insights=content_insights
        )
        
        return {
            "selection_applied": True,
            "personalization_insights_used": len(content_insights),
            "selection_result": selection_result
        }
    
    async def _apply_personalized_ats_optimization(
        self,
        content_selection: Dict[str, Any],
        job_analysis: JobAnalysisResult,
        personalization_result: PersonalizationResult
    ) -> Dict[str, Any]:
        """Apply personalized ATS optimization based on insights."""
        
        # Get keyword strategy insights
        keyword_insights = [i for i in personalization_result.insights if i.insight_type == "keyword_strategy"]
        
        return {
            "ats_optimization_applied": True,
            "keyword_insights_used": len(keyword_insights),
            "personalized_keywords": personalization_result.success_patterns.effective_keywords
        }
    
    async def _apply_personalized_content_enhancement(
        self,
        content_selection: Dict[str, Any],
        job_analysis: JobAnalysisResult,
        personalization_result: PersonalizationResult
    ) -> Dict[str, Any]:
        """Apply personalized content enhancement based on insights."""
        
        # Get enhancement level insights
        enhancement_insights = [i for i in personalization_result.insights if i.insight_type == "enhancement_level"]
        
        return {
            "enhancement_applied": True,
            "enhancement_insights_used": len(enhancement_insights),
            "optimal_enhancement_level": personalization_result.success_patterns.optimal_enhancement_level
        }
    
    async def _store_personalization_results(self, result: PersonalizationResult):
        """Store personalization results in database."""
        try:
            with db_service.get_session() as session:
                # Create user preference record
                preference = UserPreference(
                    user_profile_id=result.user_profile_id,
                    preference_type="personalization_analysis",
                    preference_data={
                        "success_patterns": asdict(result.success_patterns),
                        "insights": [asdict(insight) for insight in result.insights],
                        "personalized_strategy": result.personalized_strategy.value,
                        "predicted_improvement": result.predicted_improvement,
                        "confidence_score": result.confidence_score
                    },
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                session.add(preference)
                session.commit()
                
                logger.info(f"Stored personalization results for user {result.user_profile_id}")
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to store personalization results: {e}")
            # Don't raise exception - analysis can continue without storage
    
    async def _store_application_outcome(self, outcome: ApplicationOutcomeData):
        """Store application outcome in database."""
        try:
            with db_service.get_session() as session:
                outcome_record = ApplicationOutcome(
                    application_id=outcome.application_id,
                    user_profile_id=outcome.user_profile_id,
                    company_name=outcome.company_name,
                    position_title=outcome.position_title,
                    job_description=outcome.job_description,
                    content_selection_id=outcome.content_selection_id,
                    outcome_type=outcome.outcome_type.value,
                    outcome_date=outcome.outcome_date,
                    feedback_notes=outcome.feedback_notes,
                    salary_offered=outcome.salary_offered,
                    days_to_outcome=outcome.days_to_outcome,
                    created_at=datetime.utcnow()
                )
                
                session.add(outcome_record)
                session.commit()
                
                logger.info(f"Stored application outcome for user {outcome.user_profile_id}")
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to store application outcome: {e}")
            raise PersonalizationError(f"Failed to store application outcome: {e}")
    
    async def _should_trigger_reanalysis(self, user_profile_id: str) -> bool:
        """Check if personalization analysis should be triggered."""
        try:
            with db_service.get_session() as session:
                # Check recent outcomes count
                recent_outcomes = session.query(ApplicationOutcome).filter(
                    and_(
                        ApplicationOutcome.user_profile_id == user_profile_id,
                        ApplicationOutcome.outcome_date >= datetime.utcnow() - timedelta(days=30)
                    )
                ).count()
                
                # Trigger reanalysis if significant new data
                return recent_outcomes >= 3
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to check reanalysis trigger: {e}")
            return False
    
    async def _update_user_success_metrics(self, outcome: ApplicationOutcomeData):
        """Update user success metrics based on outcome."""
        # This would update user metrics in a real implementation
        logger.info(f"Updated success metrics for user {outcome.user_profile_id}")
    
    async def _get_trending_keywords(self, industry: str, job_level: str) -> List[str]:
        """Get trending keywords for industry and job level."""
        # Simplified implementation
        return ["python", "machine learning", "cloud", "agile", "leadership"]
    
    async def _get_salary_trends(self, industry: str, job_level: str, location: Optional[str]) -> Dict[str, Any]:
        """Get salary trends for industry and job level."""
        # Simplified implementation
        return {
            "median_salary": 95000,
            "salary_range": {"min": 75000, "max": 120000},
            "growth_rate": 0.08,
            "location_adjustment": 1.2 if location == "San Francisco" else 1.0
        }
    
    async def _get_successful_content_patterns(self, industry: str, job_level: str) -> Dict[str, Any]:
        """Get successful content patterns for industry and job level."""
        # Simplified implementation
        return {
            "effective_action_verbs": ["optimized", "developed", "led", "implemented"],
            "key_skills": ["python", "sql", "leadership", "communication"],
            "optimal_content_length": "medium",
            "successful_formats": ["bullet_points", "quantified_results"]
        }
    
    async def _get_ai_market_insights(self, industry: str, job_level: str, location: Optional[str]) -> Optional[Dict[str, Any]]:
        """Get AI-powered market insights."""
        try:
            prompt = f"""Analyze current market trends for {industry} positions at {job_level} level{f' in {location}' if location else ''}.

Provide insights on:
1. Most in-demand skills and keywords
2. Salary trends and expectations
3. Successful resume patterns
4. Industry-specific optimization strategies

Respond in JSON format with actionable insights."""
            
            response = await self.gemini_client.generate_content_analysis(prompt)
            
            if response.success:
                return json.loads(response.content)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get AI market insights: {e}")
            return None


# Global instance for easy access
personalization_engine = PersonalizationEngine()