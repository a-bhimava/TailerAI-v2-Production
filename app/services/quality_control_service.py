"""
Personal Quality Control Service for TailerAI v2.0
Provides automated quality assessment and self-improvement tools for individual users.
Following best practices from PROJECT_BLUEPRINT.md for personal optimization focus.
"""

import asyncio
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from app.services.gemini_client import GeminiClient
from app.models.database import QualityAssessment
from app.services.database_service import db_service

logger = logging.getLogger(__name__)


class QualitySeverity(str, Enum):
    """Quality issue severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class QualityCategory(str, Enum):
    """Quality assessment categories"""
    CONTENT = "content"
    GRAMMAR = "grammar"
    ATS_COMPATIBILITY = "ats_compatibility"
    FORMATTING = "formatting"
    KEYWORDS = "keywords"
    PROFESSIONAL_STANDARDS = "professional_standards"
    READABILITY = "readability"
    COMPLETENESS = "completeness"


@dataclass
class QualityIssue:
    """Individual quality issue identified during assessment"""
    category: QualityCategory
    severity: QualitySeverity
    message: str
    suggestion: str
    location: Optional[str] = None
    score_impact: float = 0.0
    auto_fixable: bool = False


@dataclass
class QualityMetrics:
    """Detailed quality metrics for specific aspects"""
    category: QualityCategory
    score: float  # 0-100
    max_score: float = 100.0
    issues: List[QualityIssue] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)


@dataclass
class PersonalQualityAssessment:
    """Comprehensive personal quality assessment result"""
    overall_score: float
    content_quality: QualityMetrics
    grammar_quality: QualityMetrics
    ats_compatibility: QualityMetrics
    formatting_quality: QualityMetrics
    keyword_optimization: QualityMetrics
    professional_standards: QualityMetrics
    readability_metrics: QualityMetrics
    completeness_score: QualityMetrics
    
    total_issues: int = 0
    critical_issues: int = 0
    improvement_priority: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    estimated_improvement_time: str = "Unknown"
    assessed_at: datetime = field(default_factory=datetime.utcnow)


class PersonalQualityControlService:
    """
    Personal Quality Control Service for individual resume optimization.
    Focuses on self-improvement tools and automated quality assessment.
    """

    def __init__(self):
        self.ai_client = GeminiClient()
        self.min_word_count = 150
        self.max_word_count = 500
        self.target_keywords_ratio = 0.02  # 2% keyword density
        
        # Quality scoring weights
        self.scoring_weights = {
            QualityCategory.CONTENT: 0.25,
            QualityCategory.GRAMMAR: 0.15,
            QualityCategory.ATS_COMPATIBILITY: 0.20,
            QualityCategory.FORMATTING: 0.10,
            QualityCategory.KEYWORDS: 0.15,
            QualityCategory.PROFESSIONAL_STANDARDS: 0.10,
            QualityCategory.READABILITY: 0.05
        }

    async def assess_personal_quality(
        self,
        user_id: str,
        resume_content: Dict[str, Any],
        target_role: Optional[str] = None,
        industry: Optional[str] = None
    ) -> PersonalQualityAssessment:
        """
        Perform comprehensive personal quality assessment for individual user.
        Returns detailed analysis with self-improvement recommendations.
        """
        try:
            logger.info(f"Starting personal quality assessment for user {user_id}")
            
            # Extract text content from resume data
            extracted_text = self._extract_text_content(resume_content)
            
            # Perform parallel quality assessments
            assessment_tasks = [
                self._assess_content_quality(extracted_text, target_role, industry),
                self._assess_grammar_quality(extracted_text),
                self._assess_ats_compatibility(extracted_text, target_role),
                self._assess_formatting_quality(resume_content),
                self._assess_keyword_optimization(extracted_text, target_role),
                self._assess_professional_standards(extracted_text, industry),
                self._assess_readability(extracted_text),
                self._assess_completeness(resume_content)
            ]
            
            results = await asyncio.gather(*assessment_tasks, return_exceptions=True)
            
            # Handle any exceptions in parallel execution
            quality_metrics = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Quality assessment task {i} failed: {result}")
                    # Create default metric for failed task
                    category = list(QualityCategory)[i]
                    quality_metrics.append(QualityMetrics(
                        category=category,
                        score=50.0,  # Default score for failed assessment
                        issues=[QualityIssue(
                            category=category,
                            severity=QualitySeverity.INFO,
                            message="Assessment temporarily unavailable",
                            suggestion="Please try again later"
                        )]
                    ))
                else:
                    quality_metrics.append(result)
            
            # Calculate overall assessment
            assessment = self._create_comprehensive_assessment(quality_metrics)
            
            # Store assessment in database
            await self._store_quality_assessment(user_id, assessment)
            
            logger.info(f"Personal quality assessment completed for user {user_id}. Overall score: {assessment.overall_score}")
            
            return assessment
            
        except Exception as e:
            logger.error(f"Personal quality assessment failed for user {user_id}: {str(e)}")
            raise

    async def _assess_content_quality(
        self, 
        text_content: str, 
        target_role: Optional[str] = None, 
        industry: Optional[str] = None
    ) -> QualityMetrics:
        """Assess content quality using AI analysis and NLP techniques"""
        
        issues = []
        suggestions = []
        strengths = []
        base_score = 80.0  # Start with good baseline
        
        # Basic content validation
        word_count = len(text_content.split())
        if word_count < self.min_word_count:
            issues.append(QualityIssue(
                category=QualityCategory.CONTENT,
                severity=QualitySeverity.HIGH,
                message=f"Content too brief ({word_count} words). Minimum recommended: {self.min_word_count}",
                suggestion="Add more detailed achievements and experiences to strengthen your resume",
                score_impact=-15.0
            ))
            base_score -= 15.0
        elif word_count > self.max_word_count:
            issues.append(QualityIssue(
                category=QualityCategory.CONTENT,
                severity=QualitySeverity.MEDIUM,
                message=f"Content may be too lengthy ({word_count} words). Maximum recommended: {self.max_word_count}",
                suggestion="Consider condensing content to focus on most impactful achievements",
                score_impact=-5.0
            ))
            base_score -= 5.0
        else:
            strengths.append("Content length is appropriate for resume format")
        
        # Check for action verbs
        action_verbs = self._count_action_verbs(text_content)
        if action_verbs < 10:
            issues.append(QualityIssue(
                category=QualityCategory.CONTENT,
                severity=QualitySeverity.MEDIUM,
                message="Limited use of strong action verbs",
                suggestion="Use more powerful action verbs like 'achieved', 'implemented', 'optimized', 'delivered'",
                score_impact=-10.0
            ))
            base_score -= 10.0
        else:
            strengths.append(f"Good use of action verbs ({action_verbs} found)")
        
        # Check for quantified achievements
        quantified_results = self._count_quantified_achievements(text_content)
        if quantified_results < 3:
            issues.append(QualityIssue(
                category=QualityCategory.CONTENT,
                severity=QualitySeverity.HIGH,
                message="Few quantified achievements found",
                suggestion="Add specific numbers, percentages, and metrics to demonstrate impact",
                score_impact=-20.0
            ))
            base_score -= 20.0
        else:
            strengths.append(f"Good quantification of results ({quantified_results} metrics found)")
        
        # AI-powered content analysis (if available)
        try:
            ai_analysis = await self._ai_content_analysis(text_content, target_role, industry)
            if ai_analysis:
                issues.extend(ai_analysis.get('issues', []))
                suggestions.extend(ai_analysis.get('suggestions', []))
                strengths.extend(ai_analysis.get('strengths', []))
                ai_score_adjustment = ai_analysis.get('score_adjustment', 0)
                base_score += ai_score_adjustment
        except Exception as e:
            logger.warning(f"AI content analysis failed: {e}")
            suggestions.append("AI analysis temporarily unavailable - review content manually")
        
        # General content improvement suggestions
        suggestions.extend([
            "Focus on achievements rather than job responsibilities",
            "Use specific examples with quantifiable results",
            "Tailor content to match target role requirements",
            "Ensure each point demonstrates clear value and impact"
        ])
        
        final_score = max(0.0, min(100.0, base_score))
        
        return QualityMetrics(
            category=QualityCategory.CONTENT,
            score=final_score,
            issues=issues,
            suggestions=suggestions,
            strengths=strengths
        )

    async def _assess_grammar_quality(self, text_content: str) -> QualityMetrics:
        """Assess grammar and language quality"""
        
        issues = []
        suggestions = []
        strengths = []
        base_score = 90.0  # Start with high baseline for grammar
        
        # Basic grammar checks
        grammar_issues = self._basic_grammar_check(text_content)
        
        for issue in grammar_issues:
            issues.append(QualityIssue(
                category=QualityCategory.GRAMMAR,
                severity=QualitySeverity.MEDIUM,
                message=issue['message'],
                suggestion=issue['suggestion'],
                location=issue.get('location'),
                score_impact=-3.0,
                auto_fixable=issue.get('auto_fixable', False)
            ))
            base_score -= 3.0
        
        # Check for common resume language issues
        language_issues = self._check_resume_language_quality(text_content)
        issues.extend(language_issues)
        
        if len(grammar_issues) == 0:
            strengths.append("No obvious grammar errors detected")
        
        if len(grammar_issues) <= 2:
            strengths.append("Generally good grammar and language usage")
        
        # Grammar improvement suggestions
        suggestions.extend([
            "Use active voice instead of passive voice where possible",
            "Ensure consistent verb tense (typically past tense for previous roles)",
            "Remove personal pronouns (I, me, my, we, us, our)",
            "Use parallel structure in bullet points",
            "Proofread carefully for typos and spelling errors"
        ])
        
        final_score = max(0.0, min(100.0, base_score))
        
        return QualityMetrics(
            category=QualityCategory.GRAMMAR,
            score=final_score,
            issues=issues,
            suggestions=suggestions,
            strengths=strengths
        )

    async def _assess_ats_compatibility(self, text_content: str, target_role: Optional[str] = None) -> QualityMetrics:
        """Assess ATS (Applicant Tracking System) compatibility"""
        
        issues = []
        suggestions = []
        strengths = []
        base_score = 85.0
        
        # Check for ATS-friendly formatting indicators
        if not self._has_clear_sections(text_content):
            issues.append(QualityIssue(
                category=QualityCategory.ATS_COMPATIBILITY,
                severity=QualitySeverity.HIGH,
                message="Sections not clearly defined",
                suggestion="Use clear section headers like 'Work Experience', 'Education', 'Skills'",
                score_impact=-15.0
            ))
            base_score -= 15.0
        else:
            strengths.append("Clear section structure detected")
        
        # Check for appropriate keyword usage
        if target_role:
            keyword_density = self._calculate_keyword_density(text_content, target_role)
            if keyword_density < 0.01:  # Less than 1%
                issues.append(QualityIssue(
                    category=QualityCategory.ATS_COMPATIBILITY,
                    severity=QualitySeverity.MEDIUM,
                    message="Low keyword density for target role",
                    suggestion=f"Include more keywords relevant to {target_role}",
                    score_impact=-10.0
                ))
                base_score -= 10.0
            elif keyword_density > 0.05:  # More than 5%
                issues.append(QualityIssue(
                    category=QualityCategory.ATS_COMPATIBILITY,
                    severity=QualitySeverity.MEDIUM,
                    message="Keyword density may be too high (possible keyword stuffing)",
                    suggestion="Ensure natural integration of keywords in context",
                    score_impact=-5.0
                ))
                base_score -= 5.0
            else:
                strengths.append("Good keyword density for ATS optimization")
        
        # Check for ATS-problematic elements
        ats_issues = self._check_ats_problematic_elements(text_content)
        issues.extend(ats_issues)
        base_score -= len(ats_issues) * 5.0
        
        # ATS optimization suggestions
        suggestions.extend([
            "Use standard section headers (Experience, Education, Skills)",
            "Include relevant keywords naturally throughout content",
            "Avoid complex formatting that may confuse ATS parsers",
            "Use standard job titles and industry terminology",
            "Include both full forms and acronyms for technical terms"
        ])
        
        final_score = max(0.0, min(100.0, base_score))
        
        return QualityMetrics(
            category=QualityCategory.ATS_COMPATIBILITY,
            score=final_score,
            issues=issues,
            suggestions=suggestions,
            strengths=strengths
        )

    async def _assess_formatting_quality(self, resume_content: Dict[str, Any]) -> QualityMetrics:
        """Assess formatting and structure quality"""
        
        issues = []
        suggestions = []
        strengths = []
        base_score = 85.0
        
        # Check for required sections
        required_sections = ['work_experiences', 'education', 'skills']
        missing_sections = []
        
        for section in required_sections:
            if not resume_content.get(section) or len(resume_content[section]) == 0:
                missing_sections.append(section.replace('_', ' ').title())
        
        if missing_sections:
            issues.append(QualityIssue(
                category=QualityCategory.FORMATTING,
                severity=QualitySeverity.HIGH,
                message=f"Missing essential sections: {', '.join(missing_sections)}",
                suggestion="Add all essential resume sections for completeness",
                score_impact=-20.0
            ))
            base_score -= 20.0
        else:
            strengths.append("All essential sections present")
        
        # Check work experience formatting
        work_experiences = resume_content.get('work_experiences', [])
        if work_experiences:
            formatting_issues = self._check_work_experience_formatting(work_experiences)
            issues.extend(formatting_issues)
            base_score -= len(formatting_issues) * 3.0
            
            if len(formatting_issues) == 0:
                strengths.append("Work experience well-formatted with clear structure")
        
        # Check date consistency
        date_issues = self._check_date_consistency(resume_content)
        issues.extend(date_issues)
        base_score -= len(date_issues) * 5.0
        
        # Formatting improvement suggestions
        suggestions.extend([
            "Maintain consistent formatting across all sections",
            "Use clear date formats (MM/YYYY or Month YYYY)",
            "Ensure proper hierarchy with job titles and company names",
            "Use bullet points consistently for achievements",
            "Keep formatting simple and ATS-friendly"
        ])
        
        final_score = max(0.0, min(100.0, base_score))
        
        return QualityMetrics(
            category=QualityCategory.FORMATTING,
            score=final_score,
            issues=issues,
            suggestions=suggestions,
            strengths=strengths
        )

    async def _assess_keyword_optimization(self, text_content: str, target_role: Optional[str] = None) -> QualityMetrics:
        """Assess keyword optimization for job targeting"""
        
        issues = []
        suggestions = []
        strengths = []
        base_score = 75.0
        
        # General keyword analysis
        total_words = len(text_content.split())
        
        if target_role:
            # Role-specific keyword analysis
            relevant_keywords = self._extract_role_keywords(target_role)
            found_keywords = self._find_keywords_in_text(text_content, relevant_keywords)
            
            keyword_coverage = len(found_keywords) / len(relevant_keywords) if relevant_keywords else 0
            
            if keyword_coverage < 0.3:  # Less than 30% coverage
                issues.append(QualityIssue(
                    category=QualityCategory.KEYWORDS,
                    severity=QualitySeverity.HIGH,
                    message=f"Low keyword coverage for {target_role} role ({keyword_coverage:.1%})",
                    suggestion=f"Include more {target_role}-relevant keywords and skills",
                    score_impact=-20.0
                ))
                base_score -= 20.0
            elif keyword_coverage > 0.7:
                strengths.append(f"Excellent keyword coverage for {target_role} ({keyword_coverage:.1%})")
                base_score += 5.0
            else:
                strengths.append(f"Good keyword coverage for {target_role} ({keyword_coverage:.1%})")
        
        # Check for industry-standard terms
        technical_terms = self._count_technical_terms(text_content)
        if technical_terms < 5:
            issues.append(QualityIssue(
                category=QualityCategory.KEYWORDS,
                severity=QualitySeverity.MEDIUM,
                message="Limited use of industry-specific terminology",
                suggestion="Include more technical terms and industry jargon relevant to your field",
                score_impact=-10.0
            ))
            base_score -= 10.0
        else:
            strengths.append(f"Good use of technical terminology ({technical_terms} terms)")
        
        # Keyword optimization suggestions
        suggestions.extend([
            "Research job descriptions for target roles to identify key terms",
            "Include both technical skills and soft skills keywords",
            "Use industry-specific terminology and acronyms",
            "Incorporate keywords naturally in context, not as lists",
            "Balance keyword optimization with readability"
        ])
        
        final_score = max(0.0, min(100.0, base_score))
        
        return QualityMetrics(
            category=QualityCategory.KEYWORDS,
            score=final_score,
            issues=issues,
            suggestions=suggestions,
            strengths=strengths
        )

    async def _assess_professional_standards(self, text_content: str, industry: Optional[str] = None) -> QualityMetrics:
        """Assess adherence to professional resume standards"""
        
        issues = []
        suggestions = []
        strengths = []
        base_score = 80.0
        
        # Check for unprofessional content
        unprofessional_indicators = self._detect_unprofessional_content(text_content)
        issues.extend(unprofessional_indicators)
        base_score -= len(unprofessional_indicators) * 10.0
        
        # Check for appropriate tone
        tone_issues = self._assess_professional_tone(text_content)
        issues.extend(tone_issues)
        base_score -= len(tone_issues) * 5.0
        
        # Check for complete contact information (implied from structure)
        contact_completeness = self._assess_contact_information_completeness(text_content)
        if not contact_completeness:
            issues.append(QualityIssue(
                category=QualityCategory.PROFESSIONAL_STANDARDS,
                severity=QualitySeverity.HIGH,
                message="Contact information appears incomplete",
                suggestion="Ensure phone, email, and location are clearly stated",
                score_impact=-15.0
            ))
            base_score -= 15.0
        else:
            strengths.append("Contact information appears complete")
        
        if len(issues) == 0:
            strengths.append("Maintains professional standards throughout")
        
        # Professional standards suggestions
        suggestions.extend([
            "Maintain formal, professional tone throughout",
            "Avoid personal information (age, marital status, photo)",
            "Use professional email address",
            "Ensure all information is relevant to job applications",
            "Follow industry-specific conventions where applicable"
        ])
        
        final_score = max(0.0, min(100.0, base_score))
        
        return QualityMetrics(
            category=QualityCategory.PROFESSIONAL_STANDARDS,
            score=final_score,
            issues=issues,
            suggestions=suggestions,
            strengths=strengths
        )

    async def _assess_readability(self, text_content: str) -> QualityMetrics:
        """Assess readability and clarity of content"""
        
        issues = []
        suggestions = []
        strengths = []
        base_score = 85.0
        
        # Calculate basic readability metrics
        avg_sentence_length = self._calculate_average_sentence_length(text_content)
        if avg_sentence_length > 20:  # Too long
            issues.append(QualityIssue(
                category=QualityCategory.READABILITY,
                severity=QualitySeverity.MEDIUM,
                message=f"Average sentence length too long ({avg_sentence_length:.1f} words)",
                suggestion="Break down long sentences for better readability",
                score_impact=-10.0
            ))
            base_score -= 10.0
        elif avg_sentence_length < 8:  # Too short
            issues.append(QualityIssue(
                category=QualityCategory.READABILITY,
                severity=QualitySeverity.LOW,
                message=f"Sentences may be too brief ({avg_sentence_length:.1f} words average)",
                suggestion="Consider combining some short sentences for better flow",
                score_impact=-5.0
            ))
            base_score -= 5.0
        else:
            strengths.append("Good sentence length for readability")
        
        # Check for readability issues
        readability_issues = self._check_readability_issues(text_content)
        issues.extend(readability_issues)
        base_score -= len(readability_issues) * 3.0
        
        # Readability improvement suggestions
        suggestions.extend([
            "Use clear, concise language",
            "Avoid jargon unless industry-appropriate",
            "Structure information logically",
            "Use parallel structure in lists",
            "Ensure smooth flow between sections"
        ])
        
        final_score = max(0.0, min(100.0, base_score))
        
        return QualityMetrics(
            category=QualityCategory.READABILITY,
            score=final_score,
            issues=issues,
            suggestions=suggestions,
            strengths=strengths
        )

    async def _assess_completeness(self, resume_content: Dict[str, Any]) -> QualityMetrics:
        """Assess completeness of resume content"""
        
        issues = []
        suggestions = []
        strengths = []
        base_score = 70.0
        
        # Check essential sections
        completeness_score = 0
        total_sections = 8
        
        sections_to_check = [
            ('work_experiences', 'Work Experience', 20),
            ('education', 'Education', 15),
            ('skills', 'Skills', 15),
            ('achievements', 'Achievements', 10),
            ('projects', 'Projects', 10),
            ('contact_info', 'Contact Information', 15),
            ('summary', 'Professional Summary', 10),
            ('certifications', 'Certifications', 5)
        ]
        
        for section_key, section_name, weight in sections_to_check:
            if resume_content.get(section_key) and len(resume_content[section_key]) > 0:
                completeness_score += weight
                strengths.append(f"{section_name} section present")
            else:
                issues.append(QualityIssue(
                    category=QualityCategory.COMPLETENESS,
                    severity=QualitySeverity.MEDIUM if weight > 10 else QualitySeverity.LOW,
                    message=f"Missing {section_name} section",
                    suggestion=f"Add {section_name} to improve resume completeness",
                    score_impact=-weight
                ))
        
        # Detailed completeness checks
        if resume_content.get('work_experiences'):
            exp_completeness = self._check_work_experience_completeness(resume_content['work_experiences'])
            issues.extend(exp_completeness)
        
        if resume_content.get('education'):
            edu_completeness = self._check_education_completeness(resume_content['education'])
            issues.extend(edu_completeness)
        
        final_score = max(0.0, min(100.0, completeness_score))
        
        # Completeness improvement suggestions
        suggestions.extend([
            "Include all relevant work experiences with clear descriptions",
            "Add educational background and relevant coursework",
            "List technical and soft skills relevant to target roles",
            "Include measurable achievements and accomplishments",
            "Add professional projects that demonstrate capabilities"
        ])
        
        return QualityMetrics(
            category=QualityCategory.COMPLETENESS,
            score=final_score,
            issues=issues,
            suggestions=suggestions,
            strengths=strengths
        )

    # =============================================================================
    # HELPER METHODS
    # =============================================================================

    def _extract_text_content(self, resume_content: Dict[str, Any]) -> str:
        """Extract all text content from resume data structure"""
        text_parts = []
        
        # Extract from work experiences
        if resume_content.get('work_experiences'):
            for exp in resume_content['work_experiences']:
                if isinstance(exp, dict):
                    text_parts.append(exp.get('position_title', ''))
                    text_parts.append(exp.get('company_name', ''))
                    text_parts.append(exp.get('company_description', ''))
                    
                    # Extract achievements
                    if exp.get('achievements'):
                        for achievement in exp['achievements']:
                            if isinstance(achievement, dict):
                                text_parts.append(achievement.get('achievement_text', ''))
                            elif isinstance(achievement, str):
                                text_parts.append(achievement)
        
        # Extract from education
        if resume_content.get('education'):
            for edu in resume_content['education']:
                if isinstance(edu, dict):
                    text_parts.append(edu.get('degree_type', ''))
                    text_parts.append(edu.get('field_of_study', ''))
                    text_parts.append(edu.get('institution_name', ''))
                    text_parts.append(edu.get('relevant_coursework', ''))
        
        # Extract from skills
        if resume_content.get('skills'):
            for skill in resume_content['skills']:
                if isinstance(skill, dict):
                    text_parts.append(skill.get('skill_name', ''))
                elif isinstance(skill, str):
                    text_parts.append(skill)
        
        # Extract from projects
        if resume_content.get('projects'):
            for project in resume_content['projects']:
                if isinstance(project, dict):
                    text_parts.append(project.get('project_name', ''))
                    text_parts.append(project.get('description', ''))
                    text_parts.append(project.get('technologies_used', ''))
        
        return ' '.join(filter(None, text_parts))

    def _count_action_verbs(self, text: str) -> int:
        """Count action verbs in text content"""
        action_verbs = {
            'achieved', 'managed', 'led', 'developed', 'implemented', 'optimized',
            'designed', 'created', 'built', 'delivered', 'improved', 'increased',
            'reduced', 'streamlined', 'coordinated', 'executed', 'established',
            'initiated', 'launched', 'modernized', 'negotiated', 'organized',
            'planned', 'promoted', 'resolved', 'supervised', 'transformed'
        }
        
        words = set(word.lower().strip('.,!?;:') for word in text.split())
        return len(words.intersection(action_verbs))

    def _count_quantified_achievements(self, text: str) -> int:
        """Count quantified achievements (numbers, percentages, metrics)"""
        # Patterns for quantified results
        patterns = [
            r'\d+%',  # Percentages
            r'\$\d+',  # Dollar amounts
            r'\d+\+',  # Numbers with plus
            r'\d+[kKmMbB]',  # Numbers with multipliers
            r'\d+:\d+',  # Ratios
            r'\d+\s*(million|thousand|billion)',  # Written numbers
            r'(increased|decreased|improved|reduced|grew|grew by)\s+\d+',  # Performance metrics
        ]
        
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, text, re.IGNORECASE))
        
        return count

    def _basic_grammar_check(self, text: str) -> List[Dict[str, Any]]:
        """Perform basic grammar and language checks"""
        issues = []
        
        # Check for common grammar issues
        if re.search(r'\bi\s+', text, re.IGNORECASE):
            issues.append({
                'message': 'First person pronouns detected (I, me, my)',
                'suggestion': 'Remove personal pronouns for professional tone',
                'auto_fixable': True
            })
        
        # Check for passive voice indicators
        passive_indicators = r'\b(was|were|been|being)\s+\w+ed\b'
        if re.search(passive_indicators, text, re.IGNORECASE):
            issues.append({
                'message': 'Passive voice detected',
                'suggestion': 'Use active voice for stronger impact',
                'auto_fixable': False
            })
        
        # Check for spelling issues (basic)
        common_misspellings = {
            'recieve': 'receive',
            'seperate': 'separate',
            'occured': 'occurred',
            'managment': 'management',
            'responsibilties': 'responsibilities'
        }
        
        for wrong, correct in common_misspellings.items():
            if re.search(rf'\b{wrong}\b', text, re.IGNORECASE):
                issues.append({
                    'message': f'Possible spelling error: "{wrong}"',
                    'suggestion': f'Consider: "{correct}"',
                    'auto_fixable': True
                })
        
        return issues

    def _check_resume_language_quality(self, text: str) -> List[QualityIssue]:
        """Check for resume-specific language quality issues"""
        issues = []
        
        # Check for weak language
        weak_phrases = [
            'responsible for', 'worked on', 'helped with', 'assisted in',
            'participated in', 'involved in', 'duties included'
        ]
        
        for phrase in weak_phrases:
            if phrase.lower() in text.lower():
                issues.append(QualityIssue(
                    category=QualityCategory.GRAMMAR,
                    severity=QualitySeverity.LOW,
                    message=f'Weak phrase detected: "{phrase}"',
                    suggestion='Use stronger action verbs to show direct impact',
                    score_impact=-2.0
                ))
        
        return issues

    async def _ai_content_analysis(
        self, 
        text_content: str, 
        target_role: Optional[str] = None, 
        industry: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Perform AI-powered content quality analysis"""
        try:
            role_context = f" for a {target_role} role" if target_role else ""
            industry_context = f" in the {industry} industry" if industry else ""
            
            prompt = f"""
            Analyze this resume content{role_context}{industry_context} and provide feedback:
            
            CONTENT:
            {text_content[:2000]}  # Limit content length
            
            Evaluate:
            1. Content clarity and impact
            2. Achievement quantification
            3. Professional language usage
            4. Relevance to target role
            5. Overall content strength
            
            Provide response in this format:
            SCORE_ADJUSTMENT: [number between -20 and +20]
            ISSUES: [list of content issues]
            SUGGESTIONS: [list of improvement suggestions]
            STRENGTHS: [list of content strengths]
            """
            
            response = await self.ai_client.generate_content(prompt)
            
            # Parse AI response (basic parsing)
            if response and response.text:
                # This is a simplified parser - in production you'd want more robust parsing
                lines = response.text.split('\n')
                result = {
                    'score_adjustment': 0,
                    'issues': [],
                    'suggestions': [],
                    'strengths': []
                }
                
                current_section = None
                for line in lines:
                    line = line.strip()
                    if line.startswith('SCORE_ADJUSTMENT:'):
                        try:
                            score = float(line.split(':')[1].strip())
                            result['score_adjustment'] = max(-20, min(20, score))
                        except:
                            pass
                    elif line.startswith('ISSUES:'):
                        current_section = 'issues'
                    elif line.startswith('SUGGESTIONS:'):
                        current_section = 'suggestions'
                    elif line.startswith('STRENGTHS:'):
                        current_section = 'strengths'
                    elif line.startswith('-') and current_section:
                        result[current_section].append(line[1:].strip())
                
                return result
            
        except Exception as e:
            logger.warning(f"AI content analysis failed: {e}")
            return None

    def _has_clear_sections(self, text: str) -> bool:
        """Check if text has clear section structure"""
        section_headers = [
            'experience', 'education', 'skills', 'work', 'employment',
            'background', 'qualifications', 'achievements', 'projects'
        ]
        
        for header in section_headers:
            if header.lower() in text.lower():
                return True
        
        return False

    def _calculate_keyword_density(self, text: str, target_role: str) -> float:
        """Calculate keyword density for target role"""
        role_keywords = self._extract_role_keywords(target_role)
        if not role_keywords:
            return 0.0
        
        text_words = text.lower().split()
        keyword_count = sum(1 for word in text_words if word in [kw.lower() for kw in role_keywords])
        
        return keyword_count / len(text_words) if text_words else 0.0

    def _extract_role_keywords(self, target_role: str) -> List[str]:
        """Extract relevant keywords for target role"""
        # This is a simplified implementation - in production you'd have a comprehensive keyword database
        role_keywords_map = {
            'software engineer': ['python', 'javascript', 'api', 'database', 'agile', 'git', 'testing'],
            'data scientist': ['python', 'machine learning', 'sql', 'statistics', 'pandas', 'visualization'],
            'product manager': ['roadmap', 'stakeholder', 'requirements', 'analytics', 'strategy', 'agile'],
            'marketing manager': ['campaign', 'analytics', 'brand', 'digital', 'strategy', 'roi'],
            'sales representative': ['revenue', 'prospecting', 'crm', 'pipeline', 'quota', 'relationship']
        }
        
        return role_keywords_map.get(target_role.lower(), [])

    def _find_keywords_in_text(self, text: str, keywords: List[str]) -> List[str]:
        """Find which keywords are present in text"""
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords

    def _check_ats_problematic_elements(self, text: str) -> List[QualityIssue]:
        """Check for elements that may cause ATS parsing issues"""
        issues = []
        
        # Check for special characters that might confuse ATS
        problematic_chars = ['@', '#', '&', '*', '~', '|']
        for char in problematic_chars:
            if char in text and char != '@':  # @ is okay in email
                issues.append(QualityIssue(
                    category=QualityCategory.ATS_COMPATIBILITY,
                    severity=QualitySeverity.LOW,
                    message=f'Special character "{char}" may confuse ATS systems',
                    suggestion='Consider removing special characters from content',
                    score_impact=-2.0
                ))
        
        return issues

    def _check_work_experience_formatting(self, work_experiences: List[Dict]) -> List[QualityIssue]:
        """Check work experience formatting consistency"""
        issues = []
        
        for i, exp in enumerate(work_experiences):
            if not exp.get('position_title'):
                issues.append(QualityIssue(
                    category=QualityCategory.FORMATTING,
                    severity=QualitySeverity.HIGH,
                    message=f'Work experience {i+1} missing job title',
                    suggestion='Add clear job titles for all positions',
                    score_impact=-5.0
                ))
            
            if not exp.get('company_name'):
                issues.append(QualityIssue(
                    category=QualityCategory.FORMATTING,
                    severity=QualitySeverity.HIGH,
                    message=f'Work experience {i+1} missing company name',
                    suggestion='Add company names for all positions',
                    score_impact=-5.0
                ))
        
        return issues

    def _check_date_consistency(self, resume_content: Dict[str, Any]) -> List[QualityIssue]:
        """Check for date formatting consistency"""
        issues = []
        
        # This is a simplified check - in production you'd have more sophisticated date validation
        date_formats_found = set()
        
        # Check work experience dates
        if resume_content.get('work_experiences'):
            for exp in resume_content['work_experiences']:
                if exp.get('start_date'):
                    # Simple date format detection
                    date_str = str(exp['start_date'])
                    if '/' in date_str:
                        date_formats_found.add('slash')
                    elif '-' in date_str:
                        date_formats_found.add('dash')
        
        if len(date_formats_found) > 1:
            issues.append(QualityIssue(
                category=QualityCategory.FORMATTING,
                severity=QualitySeverity.MEDIUM,
                message='Inconsistent date formats detected',
                suggestion='Use consistent date format throughout resume (e.g., MM/YYYY)',
                score_impact=-5.0
            ))
        
        return issues

    def _count_technical_terms(self, text: str) -> int:
        """Count technical terms and industry-specific language"""
        # This is a simplified implementation
        technical_indicators = [
            'api', 'database', 'framework', 'platform', 'system', 'software',
            'analysis', 'strategy', 'optimization', 'implementation', 'development',
            'management', 'leadership', 'collaboration', 'communication'
        ]
        
        text_lower = text.lower()
        count = 0
        for term in technical_indicators:
            count += text_lower.count(term)
        
        return count

    def _detect_unprofessional_content(self, text: str) -> List[QualityIssue]:
        """Detect potentially unprofessional content"""
        issues = []
        
        # Check for inappropriate personal information
        personal_indicators = [
            'married', 'single', 'divorced', 'age', 'weight', 'height',
            'religion', 'political', 'social security', 'ssn'
        ]
        
        for indicator in personal_indicators:
            if indicator.lower() in text.lower():
                issues.append(QualityIssue(
                    category=QualityCategory.PROFESSIONAL_STANDARDS,
                    severity=QualitySeverity.HIGH,
                    message=f'Inappropriate personal information detected: {indicator}',
                    suggestion='Remove personal information not relevant to job qualifications',
                    score_impact=-10.0
                ))
        
        return issues

    def _assess_professional_tone(self, text: str) -> List[QualityIssue]:
        """Assess professional tone of content"""
        issues = []
        
        # Check for informal language
        informal_words = [
            'awesome', 'cool', 'stuff', 'things', 'guys', 'ok', 'okay'
        ]
        
        for word in informal_words:
            if re.search(rf'\b{word}\b', text, re.IGNORECASE):
                issues.append(QualityIssue(
                    category=QualityCategory.PROFESSIONAL_STANDARDS,
                    severity=QualitySeverity.MEDIUM,
                    message=f'Informal language detected: "{word}"',
                    suggestion='Use more formal, professional language',
                    score_impact=-3.0
                ))
        
        return issues

    def _assess_contact_information_completeness(self, text: str) -> bool:
        """Assess if contact information appears complete"""
        # Basic check for contact information indicators
        has_email = '@' in text and '.' in text
        has_phone = re.search(r'\d{3}[-.]?\d{3}[-.]?\d{4}', text)
        
        return has_email and has_phone

    def _calculate_average_sentence_length(self, text: str) -> float:
        """Calculate average sentence length"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.0
        
        total_words = sum(len(sentence.split()) for sentence in sentences)
        return total_words / len(sentences)

    def _check_readability_issues(self, text: str) -> List[QualityIssue]:
        """Check for specific readability issues"""
        issues = []
        
        # Check for overly complex words
        complex_words = [
            'utilize', 'facilitate', 'optimize', 'leverage', 'synergize',
            'strategize', 'operationalize'
        ]
        
        for word in complex_words:
            if word.lower() in text.lower():
                simpler_alternatives = {
                    'utilize': 'use',
                    'facilitate': 'help',
                    'leverage': 'use'
                }
                
                alternative = simpler_alternatives.get(word.lower(), 'simpler alternative')
                issues.append(QualityIssue(
                    category=QualityCategory.READABILITY,
                    severity=QualitySeverity.LOW,
                    message=f'Complex word detected: "{word}"',
                    suggestion=f'Consider simpler alternative: "{alternative}"',
                    score_impact=-1.0
                ))
        
        return issues

    def _check_work_experience_completeness(self, work_experiences: List[Dict]) -> List[QualityIssue]:
        """Check completeness of work experience entries"""
        issues = []
        
        for i, exp in enumerate(work_experiences):
            if not exp.get('achievements') or len(exp['achievements']) == 0:
                issues.append(QualityIssue(
                    category=QualityCategory.COMPLETENESS,
                    severity=QualitySeverity.MEDIUM,
                    message=f'Work experience {i+1} has no achievements listed',
                    suggestion='Add specific achievements and accomplishments for each role',
                    score_impact=-5.0
                ))
        
        return issues

    def _check_education_completeness(self, education: List[Dict]) -> List[QualityIssue]:
        """Check completeness of education entries"""
        issues = []
        
        for i, edu in enumerate(education):
            if not edu.get('degree_type') or not edu.get('field_of_study'):
                issues.append(QualityIssue(
                    category=QualityCategory.COMPLETENESS,
                    severity=QualitySeverity.MEDIUM,
                    message=f'Education entry {i+1} missing degree or field information',
                    suggestion='Include complete degree information (type, field, institution)',
                    score_impact=-3.0
                ))
        
        return issues

    def _create_comprehensive_assessment(self, quality_metrics: List[QualityMetrics]) -> PersonalQualityAssessment:
        """Create comprehensive assessment from individual metrics"""
        
        # Calculate weighted overall score
        overall_score = 0.0
        total_weight = 0.0
        
        metrics_dict = {}
        all_issues = []
        
        for metric in quality_metrics:
            metrics_dict[metric.category] = metric
            weight = self.scoring_weights.get(metric.category, 0.1)
            overall_score += metric.score * weight
            total_weight += weight
            all_issues.extend(metric.issues)
        
        if total_weight > 0:
            overall_score = overall_score / total_weight
        
        # Count issues by severity
        critical_issues = len([issue for issue in all_issues if issue.severity == QualitySeverity.CRITICAL])
        total_issues = len(all_issues)
        
        # Generate improvement priorities
        improvement_priority = []
        if critical_issues > 0:
            improvement_priority.append("Address critical issues immediately")
        
        low_scoring_categories = [m for m in quality_metrics if m.score < 70]
        if low_scoring_categories:
            for metric in sorted(low_scoring_categories, key=lambda x: x.score)[:3]:
                improvement_priority.append(f"Improve {metric.category.value.replace('_', ' ')}")
        
        # Generate next steps
        next_steps = []
        if any(m.category == QualityCategory.CONTENT for m in low_scoring_categories):
            next_steps.append("Review and strengthen achievement descriptions")
        if any(m.category == QualityCategory.GRAMMAR for m in low_scoring_categories):
            next_steps.append("Proofread content for grammar and language issues")
        if any(m.category == QualityCategory.ATS_COMPATIBILITY for m in low_scoring_categories):
            next_steps.append("Optimize content for ATS compatibility")
        
        if not next_steps:
            next_steps.append("Continue refining content based on specific feedback")
        
        # Estimate improvement time
        estimated_time = "1-2 hours"
        if total_issues > 10:
            estimated_time = "3-4 hours"
        elif total_issues > 20:
            estimated_time = "1-2 days"
        
        return PersonalQualityAssessment(
            overall_score=round(overall_score, 1),
            content_quality=metrics_dict.get(QualityCategory.CONTENT, QualityMetrics(QualityCategory.CONTENT, 0)),
            grammar_quality=metrics_dict.get(QualityCategory.GRAMMAR, QualityMetrics(QualityCategory.GRAMMAR, 0)),
            ats_compatibility=metrics_dict.get(QualityCategory.ATS_COMPATIBILITY, QualityMetrics(QualityCategory.ATS_COMPATIBILITY, 0)),
            formatting_quality=metrics_dict.get(QualityCategory.FORMATTING, QualityMetrics(QualityCategory.FORMATTING, 0)),
            keyword_optimization=metrics_dict.get(QualityCategory.KEYWORDS, QualityMetrics(QualityCategory.KEYWORDS, 0)),
            professional_standards=metrics_dict.get(QualityCategory.PROFESSIONAL_STANDARDS, QualityMetrics(QualityCategory.PROFESSIONAL_STANDARDS, 0)),
            readability_metrics=metrics_dict.get(QualityCategory.READABILITY, QualityMetrics(QualityCategory.READABILITY, 0)),
            completeness_score=metrics_dict.get(QualityCategory.COMPLETENESS, QualityMetrics(QualityCategory.COMPLETENESS, 0)),
            total_issues=total_issues,
            critical_issues=critical_issues,
            improvement_priority=improvement_priority,
            next_steps=next_steps,
            estimated_improvement_time=estimated_time
        )

    async def _store_quality_assessment(self, user_id: str, assessment: PersonalQualityAssessment) -> None:
        """Store quality assessment in database for tracking progress"""
        try:
            # Convert assessment to storable format
            assessment_data = {
                'user_id': user_id,
                'overall_score': assessment.overall_score,
                'content_score': assessment.content_quality.score,
                'grammar_score': assessment.grammar_quality.score,
                'ats_score': assessment.ats_compatibility.score,
                'formatting_score': assessment.formatting_quality.score,
                'keyword_score': assessment.keyword_optimization.score,
                'professional_score': assessment.professional_standards.score,
                'readability_score': assessment.readability_metrics.score,
                'completeness_score': assessment.completeness_score.score,
                'total_issues': assessment.total_issues,
                'critical_issues': assessment.critical_issues,
                'improvement_priority': assessment.improvement_priority,
                'next_steps': assessment.next_steps,
                'estimated_improvement_time': assessment.estimated_improvement_time,
                'assessed_at': assessment.assessed_at
            }
            
            # Store in database (this would use the actual database service)
            await db_service.create_quality_assessment(assessment_data)
            
        except Exception as e:
            logger.error(f"Failed to store quality assessment for user {user_id}: {e}")
            # Don't fail the assessment if storage fails


# Create global service instance
quality_control_service = PersonalQualityControlService()