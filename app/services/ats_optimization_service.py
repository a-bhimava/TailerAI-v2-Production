"""
ATS Optimization Engine for TailerAI v2.0.
Implements PRD-006: ATS compatibility, keyword optimization, and format validation.
Following project blueprint best practices for comprehensive ATS optimization.
"""

import logging
import re
import math
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.database import UserProfile, WorkExperience, Achievement, Skill, EducationEntry, Project
from app.services.database_service import db_service, DatabaseError
from app.services.job_analysis_service import JobAnalysisResult
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ATSCompatibilityLevel(str, Enum):
    """ATS compatibility levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    INCOMPATIBLE = "incompatible"


class KeywordIntegrationMethod(str, Enum):
    """Methods for integrating keywords."""
    NATURAL_INTEGRATION = "natural_integration"
    SYNONYM_REPLACEMENT = "synonym_replacement"
    SECTION_BALANCING = "section_balancing"
    CONTEXT_ENHANCEMENT = "context_enhancement"


@dataclass
class KeywordMetrics:
    """Metrics for keyword usage analysis."""
    keyword: str
    exact_matches: int = 0
    partial_matches: int = 0
    context_matches: int = 0
    section_distribution: Dict[str, int] = field(default_factory=dict)
    density: float = 0.0
    prominence_score: float = 0.0
    natural_usage_score: float = 0.0


@dataclass
class KeywordAnalysis:
    """Complete keyword analysis results."""
    total_word_count: int
    keyword_metrics: Dict[str, KeywordMetrics]
    overall_density: float
    distribution_score: float
    natural_language_score: float
    keyword_stuffing_risk: float = 0.0


@dataclass
class KeywordStrategy:
    """Strategy for optimizing a specific keyword."""
    keyword: str
    action: str  # "increase", "reduce", "redistribute", "maintain"
    target_density: float
    current_density: float
    target_additions: Optional[int] = None
    target_reductions: Optional[int] = None
    suggested_locations: List[str] = field(default_factory=list)
    integration_method: KeywordIntegrationMethod = KeywordIntegrationMethod.NATURAL_INTEGRATION
    priority: int = 1  # 1=high, 2=medium, 3=low


@dataclass
class OptimizationStrategy:
    """Overall optimization strategy."""
    keyword_strategies: List[KeywordStrategy]
    overall_approach: str
    priority_order: List[str]
    estimated_impact: float
    word_budget: int = 0


@dataclass
class KeywordOptimizationResult:
    """Results of keyword optimization."""
    original_analysis: KeywordAnalysis
    optimization_strategy: OptimizationStrategy
    optimized_content: Dict[str, Any]
    final_analysis: KeywordAnalysis
    improvement_metrics: Dict[str, float]
    optimization_score: float


@dataclass
class ATSParsingResult:
    """Result of ATS parsing simulation."""
    ats_system: str
    parsing_success: bool
    extracted_data: Dict[str, Any] = field(default_factory=dict)
    parsing_errors: List[str] = field(default_factory=list)
    compatibility_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ATSCompatibilityReport:
    """Comprehensive ATS compatibility report."""
    overall_score: float
    compatibility_level: ATSCompatibilityLevel
    system_results: Dict[str, ATSParsingResult]
    common_issues: List[str]
    priority_fixes: List[str]
    detailed_recommendations: List[str]


@dataclass
class ATSOptimizationResult:
    """Complete ATS optimization results."""
    original_content: Dict[str, Any]
    optimized_content: Dict[str, Any]
    keyword_optimization: KeywordOptimizationResult
    compatibility_report: ATSCompatibilityReport
    optimization_summary: Dict[str, Any]
    recommendations: List[str]
    final_score: float


class KeywordOptimizer:
    """Advanced keyword optimization for ATS compatibility."""
    
    def __init__(self):
        self.target_density_range = (0.02, 0.04)  # 2-4% recommended
        self.keyword_stuffing_threshold = 0.06  # 6% is risky
        self.section_weights = {
            'professional_summary': 0.3,
            'work_experience': 0.4,
            'skills': 0.2,
            'education': 0.05,
            'projects': 0.05
        }
    
    async def optimize_keywords(
        self, 
        content: Dict[str, Any],
        target_keywords: List[str],
        target_density: float = 0.03
    ) -> KeywordOptimizationResult:
        """Optimize keyword placement and density."""
        try:
            logger.info(f"Starting keyword optimization for {len(target_keywords)} keywords")
            
            # Analyze current keyword usage
            current_analysis = await self._analyze_current_keywords(content, target_keywords)
            
            # Generate optimization strategy
            optimization_strategy = await self._generate_optimization_strategy(
                current_analysis,
                target_keywords,
                target_density
            )
            
            # Apply optimizations
            optimized_content = await self._apply_keyword_optimizations(
                content,
                optimization_strategy
            )
            
            # Validate results
            final_analysis = await self._analyze_current_keywords(optimized_content, target_keywords)
            
            # Calculate improvement metrics
            improvement_metrics = self._calculate_improvement_metrics(
                current_analysis, 
                final_analysis
            )
            
            optimization_score = self._calculate_optimization_score(final_analysis)
            
            logger.info(f"Keyword optimization completed with score: {optimization_score:.2f}")
            
            return KeywordOptimizationResult(
                original_analysis=current_analysis,
                optimization_strategy=optimization_strategy,
                optimized_content=optimized_content,
                final_analysis=final_analysis,
                improvement_metrics=improvement_metrics,
                optimization_score=optimization_score
            )
            
        except Exception as e:
            logger.error(f"Keyword optimization failed: {str(e)}")
            raise
    
    async def _analyze_current_keywords(
        self, 
        content: Dict[str, Any],
        target_keywords: List[str]
    ) -> KeywordAnalysis:
        """Analyze current keyword usage in resume content."""
        try:
            # Extract all text content
            full_text = self._extract_full_text(content)
            total_words = len(full_text.split())
            
            keyword_metrics = {}
            for keyword in target_keywords:
                metrics = KeywordMetrics(
                    keyword=keyword,
                    exact_matches=self._count_exact_matches(full_text, keyword),
                    partial_matches=self._count_partial_matches(full_text, keyword),
                    context_matches=self._count_context_matches(full_text, keyword),
                    section_distribution=self._analyze_section_distribution(content, keyword),
                    density=self._calculate_keyword_density(full_text, keyword),
                    prominence_score=self._calculate_prominence_score(content, keyword),
                    natural_usage_score=self._assess_natural_usage(content, keyword)
                )
                keyword_metrics[keyword] = metrics
            
            overall_density = self._calculate_overall_density(keyword_metrics)
            distribution_score = self._calculate_distribution_score(keyword_metrics)
            natural_language_score = self._calculate_natural_language_score(keyword_metrics)
            keyword_stuffing_risk = self._assess_keyword_stuffing_risk(keyword_metrics)
            
            return KeywordAnalysis(
                total_word_count=total_words,
                keyword_metrics=keyword_metrics,
                overall_density=overall_density,
                distribution_score=distribution_score,
                natural_language_score=natural_language_score,
                keyword_stuffing_risk=keyword_stuffing_risk
            )
            
        except Exception as e:
            logger.error(f"Keyword analysis failed: {str(e)}")
            raise
    
    def _extract_full_text(self, content: Dict[str, Any]) -> str:
        """Extract all text content from resume data."""
        text_parts = []
        
        # Professional summary
        if 'professional_summary' in content:
            text_parts.append(content['professional_summary'])
        
        # Work experiences
        if 'work_experiences' in content:
            for exp in content['work_experiences']:
                text_parts.append(exp.get('position_title', ''))
                text_parts.append(exp.get('company_name', ''))
                text_parts.append(exp.get('job_description', ''))
                if 'achievements' in exp:
                    for achievement in exp['achievements']:
                        text_parts.append(achievement.get('achievement_text', ''))
        
        # Skills
        if 'skills' in content:
            for skill in content['skills']:
                text_parts.append(skill.get('skill_name', ''))
                text_parts.append(skill.get('skill_description', ''))
        
        # Education
        if 'education' in content:
            for edu in content['education']:
                text_parts.append(edu.get('degree_type', ''))
                text_parts.append(edu.get('institution_name', ''))
                text_parts.append(edu.get('field_of_study', ''))
        
        # Projects
        if 'projects' in content:
            for project in content['projects']:
                text_parts.append(project.get('project_name', ''))
                text_parts.append(project.get('project_description', ''))
        
        return ' '.join(filter(None, text_parts))
    
    def _count_exact_matches(self, text: str, keyword: str) -> int:
        """Count exact keyword matches."""
        pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
        return len(re.findall(pattern, text.lower()))
    
    def _count_partial_matches(self, text: str, keyword: str) -> int:
        """Count partial keyword matches."""
        # Look for keyword variations and partial matches
        keyword_lower = keyword.lower()
        words = text.lower().split()
        partial_count = 0
        
        for word in words:
            if keyword_lower in word or word in keyword_lower:
                if word != keyword_lower:  # Don't double count exact matches
                    partial_count += 1
        
        return partial_count
    
    def _count_context_matches(self, text: str, keyword: str) -> int:
        """Count contextual keyword matches (synonyms, related terms)."""
        # This would ideally use NLP for semantic similarity
        # For now, simple word proximity analysis
        keyword_lower = keyword.lower().split()
        sentences = re.split(r'[.!?]+', text.lower())
        context_count = 0
        
        for sentence in sentences:
            words_in_sentence = set(sentence.split())
            keyword_words_found = sum(1 for kw in keyword_lower if kw in words_in_sentence)
            if keyword_words_found >= len(keyword_lower) * 0.5:  # At least 50% of keyword words
                context_count += 1
        
        return context_count
    
    def _analyze_section_distribution(self, content: Dict[str, Any], keyword: str) -> Dict[str, int]:
        """Analyze keyword distribution across resume sections."""
        distribution = {}
        
        sections = {
            'professional_summary': content.get('professional_summary', ''),
            'work_experience': self._extract_work_experience_text(content),
            'skills': self._extract_skills_text(content),
            'education': self._extract_education_text(content),
            'projects': self._extract_projects_text(content)
        }
        
        for section_name, section_text in sections.items():
            if section_text:
                distribution[section_name] = self._count_exact_matches(section_text, keyword)
        
        return distribution
    
    def _extract_work_experience_text(self, content: Dict[str, Any]) -> str:
        """Extract work experience text."""
        text_parts = []
        if 'work_experiences' in content:
            for exp in content['work_experiences']:
                text_parts.append(exp.get('position_title', ''))
                text_parts.append(exp.get('company_name', ''))
                text_parts.append(exp.get('job_description', ''))
                if 'achievements' in exp:
                    for achievement in exp['achievements']:
                        text_parts.append(achievement.get('achievement_text', ''))
        return ' '.join(filter(None, text_parts))
    
    def _extract_skills_text(self, content: Dict[str, Any]) -> str:
        """Extract skills text."""
        text_parts = []
        if 'skills' in content:
            for skill in content['skills']:
                text_parts.append(skill.get('skill_name', ''))
                text_parts.append(skill.get('skill_description', ''))
        return ' '.join(filter(None, text_parts))
    
    def _extract_education_text(self, content: Dict[str, Any]) -> str:
        """Extract education text."""
        text_parts = []
        if 'education' in content:
            for edu in content['education']:
                text_parts.append(edu.get('degree_type', ''))
                text_parts.append(edu.get('institution_name', ''))
                text_parts.append(edu.get('field_of_study', ''))
        return ' '.join(filter(None, text_parts))
    
    def _extract_projects_text(self, content: Dict[str, Any]) -> str:
        """Extract projects text."""
        text_parts = []
        if 'projects' in content:
            for project in content['projects']:
                text_parts.append(project.get('project_name', ''))
                text_parts.append(project.get('project_description', ''))
        return ' '.join(filter(None, text_parts))
    
    def _calculate_keyword_density(self, text: str, keyword: str) -> float:
        """Calculate keyword density percentage."""
        total_words = len(text.split())
        if total_words == 0:
            return 0.0
        
        keyword_count = self._count_exact_matches(text, keyword)
        return (keyword_count / total_words) * 100
    
    def _calculate_prominence_score(self, content: Dict[str, Any], keyword: str) -> float:
        """Calculate keyword prominence score based on placement."""
        score = 0.0
        
        # Check professional summary (high weight)
        if 'professional_summary' in content:
            summary_text = content['professional_summary']
            if self._count_exact_matches(summary_text, keyword) > 0:
                score += 0.4
        
        # Check work experience titles (high weight)
        if 'work_experiences' in content:
            for exp in content['work_experiences']:
                position = exp.get('position_title', '')
                if self._count_exact_matches(position, keyword) > 0:
                    score += 0.3
        
        # Check skills section (medium weight)
        if 'skills' in content:
            skills_text = self._extract_skills_text(content)
            if self._count_exact_matches(skills_text, keyword) > 0:
                score += 0.2
        
        # Check other sections (lower weight)
        other_sections = [
            self._extract_education_text(content),
            self._extract_projects_text(content)
        ]
        for section_text in other_sections:
            if self._count_exact_matches(section_text, keyword) > 0:
                score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _assess_natural_usage(self, content: Dict[str, Any], keyword: str) -> float:
        """Assess how naturally the keyword is used."""
        # Simple heuristic - check if keyword appears in complete sentences
        full_text = self._extract_full_text(content)
        sentences = re.split(r'[.!?]+', full_text)
        
        keyword_sentences = [s for s in sentences if keyword.lower() in s.lower()]
        if not keyword_sentences:
            return 0.0
        
        # Check for natural usage patterns
        natural_indicators = [
            r'\b(responsible for|managed|developed|implemented|created|designed)\b.*' + re.escape(keyword.lower()),
            r'\b' + re.escape(keyword.lower()) + r'.*\b(experience|skills|expertise|knowledge)\b',
            r'\b(using|with|in)\b.*' + re.escape(keyword.lower())
        ]
        
        natural_count = 0
        for sentence in keyword_sentences:
            for pattern in natural_indicators:
                if re.search(pattern, sentence.lower()):
                    natural_count += 1
                    break
        
        return natural_count / len(keyword_sentences) if keyword_sentences else 0.0
    
    def _calculate_overall_density(self, keyword_metrics: Dict[str, KeywordMetrics]) -> float:
        """Calculate overall keyword density."""
        if not keyword_metrics:
            return 0.0
        
        total_density = sum(metrics.density for metrics in keyword_metrics.values())
        return total_density / len(keyword_metrics)
    
    def _calculate_distribution_score(self, keyword_metrics: Dict[str, KeywordMetrics]) -> float:
        """Calculate keyword distribution score."""
        if not keyword_metrics:
            return 0.0
        
        total_score = 0.0
        for metrics in keyword_metrics.values():
            section_count = len([count for count in metrics.section_distribution.values() if count > 0])
            total_sections = len(self.section_weights)
            distribution_score = section_count / total_sections
            total_score += distribution_score
        
        return total_score / len(keyword_metrics)
    
    def _calculate_natural_language_score(self, keyword_metrics: Dict[str, KeywordMetrics]) -> float:
        """Calculate overall natural language usage score."""
        if not keyword_metrics:
            return 0.0
        
        total_score = sum(metrics.natural_usage_score for metrics in keyword_metrics.values())
        return total_score / len(keyword_metrics)
    
    def _assess_keyword_stuffing_risk(self, keyword_metrics: Dict[str, KeywordMetrics]) -> float:
        """Assess risk of keyword stuffing."""
        high_density_count = sum(
            1 for metrics in keyword_metrics.values() 
            if metrics.density > self.keyword_stuffing_threshold
        )
        
        if not keyword_metrics:
            return 0.0
        
        stuffing_risk = high_density_count / len(keyword_metrics)
        
        # Also check for unnatural usage patterns
        low_natural_usage = sum(
            1 for metrics in keyword_metrics.values() 
            if metrics.natural_usage_score < 0.3
        )
        
        unnatural_risk = low_natural_usage / len(keyword_metrics)
        
        return max(stuffing_risk, unnatural_risk)
    
    async def _generate_optimization_strategy(
        self, 
        current_analysis: KeywordAnalysis,
        target_keywords: List[str],
        target_density: float
    ) -> OptimizationStrategy:
        """Generate intelligent keyword optimization strategy."""
        try:
            strategies = []
            
            for keyword in target_keywords:
                metrics = current_analysis.keyword_metrics.get(keyword)
                if not metrics:
                    continue
                
                strategy = self._create_keyword_strategy(metrics, target_density)
                strategies.append(strategy)
            
            # Determine overall approach
            overall_approach = self._determine_overall_approach(strategies)
            
            # Prioritize optimizations
            priority_order = self._prioritize_optimizations(strategies)
            
            # Estimate impact
            estimated_impact = self._estimate_optimization_impact(strategies, current_analysis)
            
            # Calculate word budget
            word_budget = self._calculate_word_budget(current_analysis, strategies)
            
            return OptimizationStrategy(
                keyword_strategies=strategies,
                overall_approach=overall_approach,
                priority_order=priority_order,
                estimated_impact=estimated_impact,
                word_budget=word_budget
            )
            
        except Exception as e:
            logger.error(f"Strategy generation failed: {str(e)}")
            raise
    
    def _create_keyword_strategy(self, metrics: KeywordMetrics, target_density: float) -> KeywordStrategy:
        """Create optimization strategy for a specific keyword."""
        current_density = metrics.density / 100  # Convert percentage to decimal
        
        if current_density < target_density * 0.7:
            # Need significant increase
            action = "increase"
            target_additions = max(1, int((target_density - current_density) * 350))  # Assume 350 word resume
            integration_method = KeywordIntegrationMethod.NATURAL_INTEGRATION
            priority = 1
        elif current_density > target_density * 1.5:
            # Need reduction to avoid stuffing
            action = "reduce"
            target_reductions = int((current_density - target_density) * 350)
            integration_method = KeywordIntegrationMethod.SYNONYM_REPLACEMENT
            priority = 1
        elif metrics.natural_usage_score < 0.4:
            # Need better integration
            action = "redistribute"
            integration_method = KeywordIntegrationMethod.CONTEXT_ENHANCEMENT
            priority = 2
        else:
            # Maintain current usage
            action = "maintain"
            integration_method = KeywordIntegrationMethod.NATURAL_INTEGRATION
            priority = 3
        
        # Suggest locations based on section distribution
        suggested_locations = self._suggest_optimization_locations(metrics, action)
        
        return KeywordStrategy(
            keyword=metrics.keyword,
            action=action,
            target_density=target_density,
            current_density=current_density,
            target_additions=target_additions if action == "increase" else None,
            target_reductions=target_reductions if action == "reduce" else None,
            suggested_locations=suggested_locations,
            integration_method=integration_method,
            priority=priority
        )
    
    def _suggest_optimization_locations(self, metrics: KeywordMetrics, action: str) -> List[str]:
        """Suggest locations for keyword optimization."""
        suggestions = []
        
        section_distribution = metrics.section_distribution
        
        if action == "increase":
            # Suggest sections with low keyword presence
            for section, weight in self.section_weights.items():
                current_count = section_distribution.get(section, 0)
                if current_count == 0 and weight > 0.1:
                    suggestions.append(section)
        
        elif action == "reduce":
            # Suggest sections with high keyword concentration
            max_count = max(section_distribution.values()) if section_distribution else 0
            for section, count in section_distribution.items():
                if count >= max_count * 0.7:
                    suggestions.append(section)
        
        elif action == "redistribute":
            # Suggest better distribution across sections
            total_mentions = sum(section_distribution.values())
            if total_mentions > 0:
                for section, weight in self.section_weights.items():
                    expected_mentions = total_mentions * weight
                    actual_mentions = section_distribution.get(section, 0)
                    if actual_mentions < expected_mentions * 0.5:
                        suggestions.append(section)
        
        return suggestions[:3]  # Limit to top 3 suggestions
    
    def _determine_overall_approach(self, strategies: List[KeywordStrategy]) -> str:
        """Determine overall optimization approach."""
        actions = [s.action for s in strategies]
        
        if actions.count("increase") > len(actions) * 0.5:
            return "keyword_enhancement"
        elif actions.count("reduce") > len(actions) * 0.3:
            return "keyword_balancing"
        elif actions.count("redistribute") > len(actions) * 0.4:
            return "distribution_optimization"
        else:
            return "fine_tuning"
    
    def _prioritize_optimizations(self, strategies: List[KeywordStrategy]) -> List[str]:
        """Prioritize keyword optimizations."""
        # Sort by priority, then by potential impact
        sorted_strategies = sorted(strategies, key=lambda s: (s.priority, -s.current_density))
        return [s.keyword for s in sorted_strategies]
    
    def _estimate_optimization_impact(self, strategies: List[KeywordStrategy], analysis: KeywordAnalysis) -> float:
        """Estimate the impact of optimizations."""
        total_impact = 0.0
        
        for strategy in strategies:
            if strategy.action == "increase":
                # Impact based on density improvement
                density_improvement = strategy.target_density - strategy.current_density
                total_impact += density_improvement * 2  # Weight increase actions higher
            elif strategy.action == "reduce":
                # Impact based on avoiding keyword stuffing
                stuffing_reduction = max(0, strategy.current_density - self.keyword_stuffing_threshold)
                total_impact += stuffing_reduction * 1.5
            elif strategy.action == "redistribute":
                # Impact based on distribution improvement
                total_impact += 0.1  # Fixed small improvement
        
        # Normalize to 0-1 scale
        return min(total_impact, 1.0)
    
    def _calculate_word_budget(self, analysis: KeywordAnalysis, strategies: List[KeywordStrategy]) -> int:
        """Calculate word budget for optimizations."""
        total_additions = sum(
            s.target_additions or 0 for s in strategies 
            if s.action == "increase"
        )
        
        # Consider current word count and one-page constraint
        current_words = analysis.total_word_count
        max_words = 350  # One-page constraint
        available_budget = max(0, max_words - current_words)
        
        return min(total_additions, available_budget)
    
    async def _apply_keyword_optimizations(
        self, 
        content: Dict[str, Any],
        strategy: OptimizationStrategy
    ) -> Dict[str, Any]:
        """Apply keyword optimizations to content."""
        try:
            optimized_content = content.copy()
            
            for keyword_strategy in strategy.keyword_strategies:
                if keyword_strategy.action == "increase":
                    optimized_content = await self._increase_keyword_usage(
                        optimized_content, keyword_strategy
                    )
                elif keyword_strategy.action == "reduce":
                    optimized_content = await self._reduce_keyword_usage(
                        optimized_content, keyword_strategy
                    )
                elif keyword_strategy.action == "redistribute":
                    optimized_content = await self._redistribute_keyword_usage(
                        optimized_content, keyword_strategy
                    )
            
            return optimized_content
            
        except Exception as e:
            logger.error(f"Keyword optimization application failed: {str(e)}")
            raise
    
    async def _increase_keyword_usage(
        self, 
        content: Dict[str, Any], 
        strategy: KeywordStrategy
    ) -> Dict[str, Any]:
        """Increase keyword usage in specified locations."""
        # This is a simplified implementation
        # In production, this would use more sophisticated NLP techniques
        
        for location in strategy.suggested_locations:
            if location == "professional_summary" and "professional_summary" in content:
                # Add keyword to professional summary if not present
                summary = content["professional_summary"]
                if strategy.keyword.lower() not in summary.lower():
                    content["professional_summary"] = f"{summary.rstrip('.')}. Experienced with {strategy.keyword}."
            
            elif location == "skills" and "skills" in content:
                # Add as a skill if not present
                existing_skills = [skill.get("skill_name", "").lower() for skill in content["skills"]]
                if strategy.keyword.lower() not in existing_skills:
                    content["skills"].append({
                        "skill_name": strategy.keyword,
                        "skill_category": "Technical",
                        "proficiency_level": "Intermediate",
                        "skill_description": f"Proficient in {strategy.keyword}"
                    })
        
        return content
    
    async def _reduce_keyword_usage(
        self, 
        content: Dict[str, Any], 
        strategy: KeywordStrategy
    ) -> Dict[str, Any]:
        """Reduce keyword usage to avoid stuffing."""
        # Replace some instances with synonyms or remove redundant mentions
        # This is a simplified implementation
        
        full_text = self._extract_full_text(content)
        if strategy.keyword.lower() in full_text.lower():
            # Simple replacement strategy
            # In production, this would be more sophisticated
            pass
        
        return content
    
    async def _redistribute_keyword_usage(
        self, 
        content: Dict[str, Any], 
        strategy: KeywordStrategy
    ) -> Dict[str, Any]:
        """Redistribute keyword usage for better balance."""
        # Move keywords from over-represented sections to under-represented ones
        # This is a simplified implementation
        
        return content
    
    def _calculate_improvement_metrics(
        self, 
        original: KeywordAnalysis, 
        final: KeywordAnalysis
    ) -> Dict[str, float]:
        """Calculate improvement metrics."""
        return {
            "density_improvement": final.overall_density - original.overall_density,
            "distribution_improvement": final.distribution_score - original.distribution_score,
            "natural_language_improvement": final.natural_language_score - original.natural_language_score,
            "keyword_stuffing_risk_reduction": original.keyword_stuffing_risk - final.keyword_stuffing_risk
        }
    
    def _calculate_optimization_score(self, analysis: KeywordAnalysis) -> float:
        """Calculate overall optimization score."""
        # Weighted score based on multiple factors
        density_score = min(analysis.overall_density / 3.0, 1.0)  # Target ~3% density
        distribution_score = analysis.distribution_score
        natural_language_score = analysis.natural_language_score
        stuffing_penalty = max(0, analysis.keyword_stuffing_risk)
        
        # Weighted combination
        score = (
            density_score * 0.3 +
            distribution_score * 0.3 +
            natural_language_score * 0.3 -
            stuffing_penalty * 0.1
        )
        
        return max(0.0, min(1.0, score))


class ATSCompatibilityChecker:
    """Test resume compatibility with various ATS systems."""
    
    def __init__(self):
        # ATS systems we simulate
        self.ats_systems = [
            "workday", "successfactors", "greenhouse", "lever", "taleo",
            "jobvite", "smartrecruiters", "icims", "cornerstone", "bamboohr"
        ]
        
        # ATS compatibility rules
        self.compatibility_rules = {
            "font_requirements": ["Arial", "Calibri", "Times New Roman", "Helvetica"],
            "forbidden_elements": ["images", "tables", "text_boxes", "graphics"],
            "required_sections": ["contact", "experience", "education"],
            "max_file_size_mb": 2,
            "preferred_formats": [".docx", ".pdf", ".txt"]
        }
    
    async def test_compatibility(self, content: Dict[str, Any]) -> ATSCompatibilityReport:
        """Test resume against multiple ATS systems."""
        try:
            logger.info("Starting ATS compatibility testing")
            
            system_results = {}
            for ats_system in self.ats_systems:
                result = await self._simulate_ats_parsing(ats_system, content)
                system_results[ats_system] = result
            
            # Calculate overall compatibility
            overall_score = self._calculate_overall_compatibility_score(system_results)
            compatibility_level = self._determine_compatibility_level(overall_score)
            
            # Identify common issues
            common_issues = self._identify_common_issues(system_results)
            priority_fixes = self._identify_priority_fixes(common_issues, system_results)
            detailed_recommendations = self._generate_detailed_recommendations(system_results)
            
            logger.info(f"ATS compatibility testing completed: {compatibility_level} ({overall_score:.2f})")
            
            return ATSCompatibilityReport(
                overall_score=overall_score,
                compatibility_level=compatibility_level,
                system_results=system_results,
                common_issues=common_issues,
                priority_fixes=priority_fixes,
                detailed_recommendations=detailed_recommendations
            )
            
        except Exception as e:
            logger.error(f"ATS compatibility testing failed: {str(e)}")
            raise
    
    async def _simulate_ats_parsing(self, ats_system: str, content: Dict[str, Any]) -> ATSParsingResult:
        """Simulate ATS parsing for a specific system."""
        try:
            parsing_errors = []
            extracted_data = {}
            recommendations = []
            
            # Simulate basic parsing logic
            compatibility_score = 1.0
            
            # Check contact information
            if not self._has_contact_info(content):
                parsing_errors.append("Missing contact information")
                compatibility_score -= 0.2
                recommendations.append("Add complete contact information (name, email, phone)")
            else:
                extracted_data["contact"] = self._extract_contact_info(content)
            
            # Check work experience
            if not self._has_work_experience(content):
                parsing_errors.append("Missing work experience section")
                compatibility_score -= 0.3
                recommendations.append("Add work experience section with job titles and descriptions")
            else:
                extracted_data["work_experience"] = self._extract_work_experience(content)
            
            # Check education
            if not self._has_education(content):
                parsing_errors.append("Missing education section")
                compatibility_score -= 0.2
                recommendations.append("Add education section with degree and institution")
            else:
                extracted_data["education"] = self._extract_education(content)
            
            # Check skills
            if self._has_skills(content):
                extracted_data["skills"] = self._extract_skills(content)
            
            # System-specific checks
            if ats_system in ["workday", "successfactors"]:
                # Enterprise systems prefer structured data
                if not self._has_structured_format(content):
                    compatibility_score -= 0.1
                    recommendations.append("Use consistent formatting and clear section headers")
            
            elif ats_system in ["greenhouse", "lever"]:
                # Tech-focused systems handle more complex parsing
                if self._has_technical_skills(content):
                    compatibility_score += 0.1
            
            # Final score adjustment
            compatibility_score = max(0.0, min(1.0, compatibility_score))
            
            return ATSParsingResult(
                ats_system=ats_system,
                parsing_success=len(parsing_errors) == 0,
                extracted_data=extracted_data,
                parsing_errors=parsing_errors,
                compatibility_score=compatibility_score,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"ATS parsing simulation failed for {ats_system}: {str(e)}")
            return ATSParsingResult(
                ats_system=ats_system,
                parsing_success=False,
                parsing_errors=[f"Simulation error: {str(e)}"],
                compatibility_score=0.0
            )
    
    def _has_contact_info(self, content: Dict[str, Any]) -> bool:
        """Check if resume has contact information."""
        return bool(
            content.get("contact_info") or 
            content.get("email") or 
            content.get("phone")
        )
    
    def _extract_contact_info(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Extract contact information."""
        return {
            "name": content.get("full_name", ""),
            "email": content.get("email", ""),
            "phone": content.get("phone", ""),
            "location": content.get("location", "")
        }
    
    def _has_work_experience(self, content: Dict[str, Any]) -> bool:
        """Check if resume has work experience."""
        return bool(content.get("work_experiences"))
    
    def _extract_work_experience(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract work experience."""
        experiences = []
        for exp in content.get("work_experiences", []):
            experiences.append({
                "position": exp.get("position_title", ""),
                "company": exp.get("company_name", ""),
                "start_date": exp.get("start_date", ""),
                "end_date": exp.get("end_date", ""),
                "description": exp.get("job_description", "")
            })
        return experiences
    
    def _has_education(self, content: Dict[str, Any]) -> bool:
        """Check if resume has education."""
        return bool(content.get("education"))
    
    def _extract_education(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract education."""
        education = []
        for edu in content.get("education", []):
            education.append({
                "degree": edu.get("degree_type", ""),
                "institution": edu.get("institution_name", ""),
                "field": edu.get("field_of_study", ""),
                "graduation_date": edu.get("graduation_date", "")
            })
        return education
    
    def _has_skills(self, content: Dict[str, Any]) -> bool:
        """Check if resume has skills."""
        return bool(content.get("skills"))
    
    def _extract_skills(self, content: Dict[str, Any]) -> List[str]:
        """Extract skills."""
        skills = []
        for skill in content.get("skills", []):
            skills.append(skill.get("skill_name", ""))
        return skills
    
    def _has_structured_format(self, content: Dict[str, Any]) -> bool:
        """Check if resume has structured format."""
        # Simple heuristic - check for required sections
        required_sections = ["work_experiences", "education"]
        return all(content.get(section) for section in required_sections)
    
    def _has_technical_skills(self, content: Dict[str, Any]) -> bool:
        """Check if resume has technical skills."""
        tech_keywords = ["python", "javascript", "sql", "aws", "docker", "kubernetes", "react", "node.js"]
        skills_text = self._extract_skills_text(content).lower()
        return any(keyword in skills_text for keyword in tech_keywords)
    
    def _extract_skills_text(self, content: Dict[str, Any]) -> str:
        """Extract skills as text."""
        skills = content.get("skills", [])
        skill_names = [skill.get("skill_name", "") for skill in skills]
        return " ".join(skill_names)
    
    def _calculate_overall_compatibility_score(self, system_results: Dict[str, ATSParsingResult]) -> float:
        """Calculate overall compatibility score."""
        if not system_results:
            return 0.0
        
        total_score = sum(result.compatibility_score for result in system_results.values())
        return total_score / len(system_results)
    
    def _determine_compatibility_level(self, score: float) -> ATSCompatibilityLevel:
        """Determine compatibility level from score."""
        if score >= 0.9:
            return ATSCompatibilityLevel.EXCELLENT
        elif score >= 0.8:
            return ATSCompatibilityLevel.GOOD
        elif score >= 0.6:
            return ATSCompatibilityLevel.FAIR
        elif score >= 0.4:
            return ATSCompatibilityLevel.POOR
        else:
            return ATSCompatibilityLevel.INCOMPATIBLE
    
    def _identify_common_issues(self, system_results: Dict[str, ATSParsingResult]) -> List[str]:
        """Identify common issues across ATS systems."""
        issue_counts = {}
        
        for result in system_results.values():
            for error in result.parsing_errors:
                issue_counts[error] = issue_counts.get(error, 0) + 1
        
        # Return issues that appear in more than 50% of systems
        threshold = len(system_results) * 0.5
        common_issues = [
            issue for issue, count in issue_counts.items() 
            if count >= threshold
        ]
        
        return common_issues
    
    def _identify_priority_fixes(
        self, 
        common_issues: List[str], 
        system_results: Dict[str, ATSParsingResult]
    ) -> List[str]:
        """Identify priority fixes based on impact."""
        priority_fixes = []
        
        # High priority: Issues affecting parsing success
        for issue in common_issues:
            if "missing" in issue.lower():
                priority_fixes.append(f"HIGH: {issue}")
        
        # Medium priority: Issues affecting scoring
        low_score_systems = [
            name for name, result in system_results.items() 
            if result.compatibility_score < 0.7
        ]
        
        if len(low_score_systems) > len(system_results) * 0.3:
            priority_fixes.append("MEDIUM: Improve overall formatting and structure")
        
        return priority_fixes
    
    def _generate_detailed_recommendations(self, system_results: Dict[str, ATSParsingResult]) -> List[str]:
        """Generate detailed recommendations."""
        recommendations = set()
        
        for result in system_results.values():
            recommendations.update(result.recommendations)
        
        # Add general recommendations
        recommendations.add("Use standard section headers (Experience, Education, Skills)")
        recommendations.add("Maintain consistent date formatting (MM/YYYY)")
        recommendations.add("Include quantified achievements where possible")
        recommendations.add("Use bullet points for easy scanning")
        
        return list(recommendations)


class ATSOptimizationEngine:
    """Comprehensive ATS optimization and validation engine."""
    
    def __init__(self):
        self.keyword_optimizer = KeywordOptimizer()
        self.compatibility_checker = ATSCompatibilityChecker()
    
    async def optimize_for_ats(
        self, 
        resume_content: Dict[str, Any],
        job_keywords: List[str],
        target_density: float = 0.03
    ) -> ATSOptimizationResult:
        """
        Complete ATS optimization pipeline.
        Returns optimized content with validation results.
        """
        try:
            logger.info(f"Starting ATS optimization for {len(job_keywords)} keywords")
            
            # Step 1: Keyword optimization
            keyword_optimization = await self.keyword_optimizer.optimize_keywords(
                resume_content,
                job_keywords,
                target_density
            )
            
            # Step 2: ATS compatibility testing
            compatibility_report = await self.compatibility_checker.test_compatibility(
                keyword_optimization.optimized_content
            )
            
            # Step 3: Generate optimization summary
            optimization_summary = self._generate_optimization_summary(
                keyword_optimization,
                compatibility_report
            )
            
            # Step 4: Generate final recommendations
            recommendations = self._generate_final_recommendations(
                keyword_optimization,
                compatibility_report
            )
            
            # Step 5: Calculate final score
            final_score = self._calculate_final_score(
                keyword_optimization.optimization_score,
                compatibility_report.overall_score
            )
            
            logger.info(f"ATS optimization completed with final score: {final_score:.2f}")
            
            return ATSOptimizationResult(
                original_content=resume_content,
                optimized_content=keyword_optimization.optimized_content,
                keyword_optimization=keyword_optimization,
                compatibility_report=compatibility_report,
                optimization_summary=optimization_summary,
                recommendations=recommendations,
                final_score=final_score
            )
            
        except Exception as e:
            logger.error(f"ATS optimization failed: {str(e)}")
            raise
    
    def _generate_optimization_summary(
        self, 
        keyword_opt: KeywordOptimizationResult,
        compatibility: ATSCompatibilityReport
    ) -> Dict[str, Any]:
        """Generate optimization summary."""
        return {
            "keyword_optimization": {
                "original_density": keyword_opt.original_analysis.overall_density,
                "final_density": keyword_opt.final_analysis.overall_density,
                "density_improvement": keyword_opt.improvement_metrics["density_improvement"],
                "distribution_score": keyword_opt.final_analysis.distribution_score,
                "natural_language_score": keyword_opt.final_analysis.natural_language_score,
                "keyword_stuffing_risk": keyword_opt.final_analysis.keyword_stuffing_risk
            },
            "ats_compatibility": {
                "overall_score": compatibility.overall_score,
                "compatibility_level": compatibility.compatibility_level.value,
                "systems_passed": len([r for r in compatibility.system_results.values() if r.parsing_success]),
                "total_systems": len(compatibility.system_results),
                "common_issues_count": len(compatibility.common_issues),
                "priority_fixes_count": len(compatibility.priority_fixes)
            },
            "optimization_stats": {
                "keywords_optimized": len(keyword_opt.optimization_strategy.keyword_strategies),
                "sections_modified": len(set(
                    loc for strategy in keyword_opt.optimization_strategy.keyword_strategies 
                    for loc in strategy.suggested_locations
                )),
                "word_budget_used": keyword_opt.optimization_strategy.word_budget
            }
        }
    
    def _generate_final_recommendations(
        self, 
        keyword_opt: KeywordOptimizationResult,
        compatibility: ATSCompatibilityReport
    ) -> List[str]:
        """Generate final recommendations."""
        recommendations = []
        
        # Keyword optimization recommendations
        if keyword_opt.final_analysis.keyword_stuffing_risk > 0.3:
            recommendations.append("⚠️ HIGH: Reduce keyword density to avoid keyword stuffing penalties")
        
        if keyword_opt.final_analysis.distribution_score < 0.5:
            recommendations.append("📊 MEDIUM: Improve keyword distribution across resume sections")
        
        if keyword_opt.final_analysis.natural_language_score < 0.6:
            recommendations.append("✍️ MEDIUM: Integrate keywords more naturally into existing content")
        
        # ATS compatibility recommendations
        if compatibility.overall_score < 0.8:
            recommendations.append("🔧 HIGH: Address ATS compatibility issues for better parsing")
        
        # Add priority fixes from compatibility report
        recommendations.extend(compatibility.priority_fixes)
        
        # Add specific improvement suggestions
        if keyword_opt.optimization_strategy.word_budget > 50:
            recommendations.append("📝 LOW: Consider expanding content to better utilize keyword opportunities")
        
        return recommendations[:10]  # Limit to top 10 recommendations
    
    def _calculate_final_score(self, keyword_score: float, compatibility_score: float) -> float:
        """Calculate final optimization score."""
        # Weighted combination of keyword optimization and ATS compatibility
        final_score = (keyword_score * 0.6) + (compatibility_score * 0.4)
        return round(final_score, 2)


# Create global instance
ats_optimizer = ATSOptimizationEngine()