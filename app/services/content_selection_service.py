"""
Content Selection Engine for TailerAI v2.0.
Implements PRD-005: Intelligent content selection with multi-dimensional scoring.
Following project blueprint best practices for AI-driven optimization.
"""

import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.database import UserProfile, WorkExperience, Achievement, Skill, EducationEntry, Project, ContentSelection, JobAnalysis
from app.services.database_service import db_service, DatabaseError
from app.services.job_analysis_service import JobAnalysisResult, job_analyzer
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ContentType(str, Enum):
    """Types of content that can be selected."""
    ACHIEVEMENT = "achievement"
    WORK_EXPERIENCE = "work_experience"
    SKILL = "skill"
    PROJECT = "project"
    EDUCATION = "education"


@dataclass
class ScoredContent:
    """Content item with multi-dimensional scoring."""
    content_id: str
    content_type: ContentType
    content_data: Dict[str, Any]
    
    # Multi-dimensional scores (0.0 - 1.0)
    keyword_relevance_score: float
    impact_level_score: float
    recency_score: float
    skill_demonstration_score: float
    quantified_results_score: float
    
    # Combined scores
    total_score: float
    priority_tier: int  # 1 (highest) to 5 (lowest)
    
    # Selection metadata
    estimated_word_count: int
    keywords_matched: List[str]
    reasoning: str


@dataclass
class ContentSelectionResult:
    """Result of content selection optimization."""
    job_analysis_id: str
    user_profile_id: str
    
    # Selected content
    selected_achievements: List[ScoredContent]
    selected_work_experiences: List[ScoredContent]
    selected_skills: List[ScoredContent]
    selected_projects: List[ScoredContent]
    selected_education: List[ScoredContent]
    
    # Optimization metrics
    total_score: float
    estimated_word_count: int
    one_page_compliant: bool
    content_diversity_score: float
    keyword_coverage_percentage: float
    
    # Selection metadata
    selection_algorithm: str
    selection_criteria: Dict[str, Any]
    optimization_notes: List[str]


class ContentSelectionError(Exception):
    """Custom exception for content selection operations."""
    pass


class ContentSelectionEngine:
    """
    Intelligent content selection engine with multi-dimensional scoring.
    Optimizes content selection for job requirements and one-page constraint.
    """
    
    def __init__(self):
        self.logger = logger
        
        # Configuration parameters
        self.max_word_count = 350  # Target for one-page resume
        self.max_achievements = 8  # Maximum achievements to select
        self.max_projects = 2  # Maximum projects to select
        self.max_skills = 15  # Maximum skills to show
        
        # Scoring weights for multi-dimensional analysis
        self.scoring_weights = {
            "keyword_relevance": 0.35,  # Most important for ATS
            "impact_level": 0.25,       # High-impact achievements
            "recency": 0.15,            # Recent experience preferred
            "skill_demonstration": 0.15, # Shows relevant skills
            "quantified_results": 0.10  # Measurable outcomes
        }
    
    async def select_optimal_content(
        self, 
        user_profile_id: str, 
        job_analysis: JobAnalysisResult
    ) -> ContentSelectionResult:
        """
        Select optimal content from user's master dataset for the given job.
        Uses multi-dimensional scoring and one-page optimization.
        """
        try:
            self.logger.info(f"Starting content selection for user {user_profile_id} and job {job_analysis.position_title}")
            
            # Load user's master dataset
            user_data = await self._load_user_master_dataset(user_profile_id)
            
            # Score all content items
            scored_content = await self._score_all_content(user_data, job_analysis)
            
            # Optimize selection for one-page constraint
            selection_result = await self._optimize_content_selection(
                scored_content, job_analysis, user_profile_id
            )
            
            # Store selection results
            await self._store_selection_results(selection_result)
            
            self.logger.info(f"Content selection completed: {len(selection_result.selected_achievements)} achievements, {selection_result.estimated_word_count} words")
            return selection_result
            
        except Exception as e:
            self.logger.error(f"Content selection failed: {str(e)}")
            raise ContentSelectionError(f"Failed to select optimal content: {str(e)}")
    
    async def _load_user_master_dataset(self, user_profile_id: str) -> Dict[str, Any]:
        """Load complete user master dataset from database."""
        try:
            with db_service.get_session() as session:
                # Load user profile
                profile = session.query(UserProfile).filter_by(id=user_profile_id).first()
                if not profile:
                    raise ContentSelectionError(f"User profile not found: {user_profile_id}")
                
                # Load all related data
                work_experiences = session.query(WorkExperience).filter_by(profile_id=user_profile_id).all()
                achievements = session.query(Achievement).filter_by(profile_id=user_profile_id).all()
                skills = session.query(Skill).filter_by(profile_id=user_profile_id).all()
                education = session.query(EducationEntry).filter_by(profile_id=user_profile_id).all()
                projects = session.query(Project).filter_by(profile_id=user_profile_id).all()
                
                return {
                    "profile": profile,
                    "work_experiences": work_experiences,
                    "achievements": achievements,
                    "skills": skills,
                    "education": education,
                    "projects": projects
                }
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error loading user data: {e}")
            raise ContentSelectionError(f"Failed to load user data: {e}")
    
    async def _score_all_content(
        self, 
        user_data: Dict[str, Any], 
        job_analysis: JobAnalysisResult
    ) -> Dict[ContentType, List[ScoredContent]]:
        """Score all content items using multi-dimensional analysis."""
        scored_content = {
            ContentType.ACHIEVEMENT: [],
            ContentType.WORK_EXPERIENCE: [],
            ContentType.SKILL: [],
            ContentType.PROJECT: [],
            ContentType.EDUCATION: []
        }
        
        # Prepare job keywords for matching
        all_job_keywords = (
            job_analysis.required_skills + 
            job_analysis.preferred_skills + 
            job_analysis.important_keywords + 
            job_analysis.ats_keywords
        )
        job_keywords_lower = [k.lower() for k in all_job_keywords]
        
        # Score achievements
        for achievement in user_data["achievements"]:
            scored = await self._score_achievement(achievement, job_keywords_lower, job_analysis)
            scored_content[ContentType.ACHIEVEMENT].append(scored)
        
        # Score work experiences
        for work_exp in user_data["work_experiences"]:
            scored = await self._score_work_experience(work_exp, job_keywords_lower, job_analysis)
            scored_content[ContentType.WORK_EXPERIENCE].append(scored)
        
        # Score skills
        for skill in user_data["skills"]:
            scored = await self._score_skill(skill, job_keywords_lower, job_analysis)
            scored_content[ContentType.SKILL].append(scored)
        
        # Score projects
        for project in user_data["projects"]:
            scored = await self._score_project(project, job_keywords_lower, job_analysis)
            scored_content[ContentType.PROJECT].append(scored)
        
        # Score education
        for edu in user_data["education"]:
            scored = await self._score_education(edu, job_keywords_lower, job_analysis)
            scored_content[ContentType.EDUCATION].append(scored)
        
        # Sort each category by total score
        for content_type in scored_content:
            scored_content[content_type].sort(key=lambda x: x.total_score, reverse=True)
        
        return scored_content
    
    async def _score_achievement(
        self, 
        achievement: Achievement, 
        job_keywords: List[str], 
        job_analysis: JobAnalysisResult
    ) -> ScoredContent:
        """Score individual achievement with multi-dimensional analysis."""
        
        # Extract text for analysis
        achievement_text = f"{achievement.achievement_text} {' '.join(achievement.skills_demonstrated or [])}".lower()
        
        # 1. Keyword Relevance Score
        keyword_matches = []
        for keyword in job_keywords:
            if keyword in achievement_text:
                keyword_matches.append(keyword)
        keyword_relevance = len(keyword_matches) / max(len(job_keywords), 1)
        
        # 2. Impact Level Score (based on quantified results and impact level)
        impact_score = 0.0
        if achievement.quantified_metrics:
            impact_score += 0.4  # Has quantified results
        if achievement.impact_level:
            impact_score += min(0.6, achievement.impact_level / 10)  # Scale 1-10 to 0.1-0.6
        
        # 3. Recency Score (more recent = higher score)
        recency_score = 0.0
        if achievement.created_at:
            days_ago = (datetime.utcnow() - achievement.created_at).days
            # Score decreases over 3 years
            recency_score = max(0.0, 1.0 - (days_ago / (3 * 365)))
        else:
            recency_score = 0.5  # Default for unknown dates
        
        # 4. Skill Demonstration Score
        skill_demo_score = 0.0
        required_skills_lower = [s.lower() for s in job_analysis.required_skills]
        for skill in (achievement.skills_demonstrated or []):
            if skill.lower() in required_skills_lower:
                skill_demo_score += 0.2
        skill_demo_score = min(1.0, skill_demo_score)
        
        # 5. Quantified Results Score
        quantified_score = 1.0 if achievement.quantified_metrics else 0.0
        
        # Calculate total score
        total_score = (
            keyword_relevance * self.scoring_weights["keyword_relevance"] +
            impact_score * self.scoring_weights["impact_level"] +
            recency_score * self.scoring_weights["recency"] +
            skill_demo_score * self.scoring_weights["skill_demonstration"] +
            quantified_score * self.scoring_weights["quantified_results"]
        )
        
        # Determine priority tier
        priority_tier = self._calculate_priority_tier(total_score)
        
        # Estimate word count
        word_count = len(achievement.achievement_text.split()) + len(achievement.skills_demonstrated or []) * 2
        
        return ScoredContent(
            content_id=str(achievement.id),
            content_type=ContentType.ACHIEVEMENT,
            content_data={
                "description": achievement.achievement_text,
                "skills": achievement.skills_demonstrated,
                "metrics": achievement.quantified_metrics,
                "category": achievement.achievement_category,
                "impact_level": achievement.impact_level
            },
            keyword_relevance_score=keyword_relevance,
            impact_level_score=impact_score,
            recency_score=recency_score,
            skill_demonstration_score=skill_demo_score,
            quantified_results_score=quantified_score,
            total_score=total_score,
            priority_tier=priority_tier,
            estimated_word_count=word_count,
            keywords_matched=keyword_matches,
            reasoning=f"Matches {len(keyword_matches)} keywords, impact: {impact_score:.2f}, recency: {recency_score:.2f}"
        )
    
    async def _score_work_experience(
        self, 
        work_exp: WorkExperience, 
        job_keywords: List[str], 
        job_analysis: JobAnalysisResult
    ) -> ScoredContent:
        """Score work experience entry."""
        
        # Extract text for analysis
        work_text = f"{work_exp.position_title} {work_exp.company_name} {work_exp.role_summary or ''}".lower()
        
        # 1. Keyword Relevance Score
        keyword_matches = []
        for keyword in job_keywords:
            if keyword in work_text:
                keyword_matches.append(keyword)
        keyword_relevance = len(keyword_matches) / max(len(job_keywords), 1)
        
        # 2. Impact Level Score (based on seniority and scope)
        impact_score = 0.0
        if any(word in work_exp.position_title.lower() for word in ["senior", "lead", "principal", "manager", "director"]):
            impact_score += 0.5
        if work_exp.company_name:
            impact_score += 0.3  # Company experience valued
        if work_exp.team_size and work_exp.team_size > 1:
            impact_score += 0.2  # Team leadership experience
        
        # 3. Recency Score
        recency_score = 0.0
        if work_exp.end_date:
            days_ago = (datetime.utcnow() - work_exp.end_date).days
            recency_score = max(0.0, 1.0 - (days_ago / (5 * 365)))
        elif not work_exp.end_date:  # Current job
            recency_score = 1.0
        
        # 4. Skill Demonstration Score (based on industry and role)
        skill_demo_score = 0.0
        required_skills_lower = [s.lower() for s in job_analysis.required_skills]
        # Check if industry matches
        if work_exp.industry and any(skill in work_exp.industry.lower() for skill in required_skills_lower):
            skill_demo_score += 0.5
        skill_demo_score = min(1.0, skill_demo_score)
        
        # 5. Quantified Results Score
        quantified_score = 0.5  # Work experience inherently has some quantification
        
        # Calculate total score
        total_score = (
            keyword_relevance * self.scoring_weights["keyword_relevance"] +
            impact_score * self.scoring_weights["impact_level"] +
            recency_score * self.scoring_weights["recency"] +
            skill_demo_score * self.scoring_weights["skill_demonstration"] +
            quantified_score * self.scoring_weights["quantified_results"]
        )
        
        priority_tier = self._calculate_priority_tier(total_score)
        word_count = len(f"{work_exp.position_title} {work_exp.company_name}".split()) + 5  # Base count
        
        return ScoredContent(
            content_id=str(work_exp.id),
            content_type=ContentType.WORK_EXPERIENCE,
            content_data={
                "position": work_exp.position_title,
                "company": work_exp.company_name,
                "duration": f"{work_exp.start_date.strftime('%Y-%m') if work_exp.start_date else 'Unknown'} - {work_exp.end_date.strftime('%Y-%m') if work_exp.end_date else 'Present'}",
                "industry": work_exp.industry,
                "team_size": work_exp.team_size
            },
            keyword_relevance_score=keyword_relevance,
            impact_level_score=impact_score,
            recency_score=recency_score,
            skill_demonstration_score=skill_demo_score,
            quantified_results_score=quantified_score,
            total_score=total_score,
            priority_tier=priority_tier,
            estimated_word_count=word_count,
            keywords_matched=keyword_matches,
            reasoning=f"Recent work experience with {len(keyword_matches)} keyword matches"
        )
    
    async def _score_skill(
        self, 
        skill: Skill, 
        job_keywords: List[str], 
        job_analysis: JobAnalysisResult
    ) -> ScoredContent:
        """Score individual skill."""
        
        skill_name_lower = skill.skill_name.lower()
        
        # 1. Keyword Relevance Score (primary factor for skills)
        keyword_relevance = 0.0
        matched_keywords = []
        
        # Direct match with required skills (highest priority)
        for req_skill in job_analysis.required_skills:
            if req_skill.lower() == skill_name_lower or req_skill.lower() in skill_name_lower:
                keyword_relevance = 1.0
                matched_keywords.append(req_skill)
                break
        
        # Match with preferred skills
        if keyword_relevance == 0.0:
            for pref_skill in job_analysis.preferred_skills:
                if pref_skill.lower() == skill_name_lower or pref_skill.lower() in skill_name_lower:
                    keyword_relevance = 0.8
                    matched_keywords.append(pref_skill)
                    break
        
        # Match with other keywords
        if keyword_relevance == 0.0:
            for keyword in job_keywords:
                if keyword == skill_name_lower or keyword in skill_name_lower:
                    keyword_relevance = 0.6
                    matched_keywords.append(keyword)
                    break
        
        # 2. Impact Level Score (based on proficiency and category)
        impact_score = 0.0
        if skill.proficiency_level:
            proficiency_map = {"expert": 1.0, "advanced": 0.8, "intermediate": 0.6, "beginner": 0.3}
            impact_score = proficiency_map.get(skill.proficiency_level.lower(), 0.5)
        else:
            impact_score = 0.5
        
        # 3. Recency Score (skills don't age as much as achievements)
        recency_score = 0.8  # Default high value for skills
        
        # 4. Skill Demonstration Score (always 1.0 for skills)
        skill_demo_score = 1.0
        
        # 5. Quantified Results Score (not applicable to skills directly)
        quantified_score = 0.0
        
        # Calculate total score
        total_score = (
            keyword_relevance * self.scoring_weights["keyword_relevance"] +
            impact_score * self.scoring_weights["impact_level"] +
            recency_score * self.scoring_weights["recency"] +
            skill_demo_score * self.scoring_weights["skill_demonstration"] +
            quantified_score * self.scoring_weights["quantified_results"]
        )
        
        priority_tier = self._calculate_priority_tier(total_score)
        word_count = len(skill.skill_name.split())
        
        return ScoredContent(
            content_id=str(skill.id),
            content_type=ContentType.SKILL,
            content_data={
                "name": skill.skill_name,
                "proficiency": skill.proficiency_level,
                "category": skill.skill_category,
                "years_experience": skill.years_experience
            },
            keyword_relevance_score=keyword_relevance,
            impact_level_score=impact_score,
            recency_score=recency_score,
            skill_demonstration_score=skill_demo_score,
            quantified_results_score=quantified_score,
            total_score=total_score,
            priority_tier=priority_tier,
            estimated_word_count=word_count,
            keywords_matched=matched_keywords,
            reasoning=f"{'Required' if keyword_relevance >= 0.8 else 'Relevant'} skill with {skill.proficiency_level or 'unknown'} proficiency"
        )
    
    async def _score_project(
        self, 
        project: Project, 
        job_keywords: List[str], 
        job_analysis: JobAnalysisResult
    ) -> ScoredContent:
        """Score project entry."""
        
        project_text = f"{project.project_name} {project.project_description or ''} {' '.join(project.technologies_used or [])}".lower()
        
        # Similar scoring logic to achievements but with project-specific adjustments
        keyword_matches = []
        for keyword in job_keywords:
            if keyword in project_text:
                keyword_matches.append(keyword)
        keyword_relevance = len(keyword_matches) / max(len(job_keywords), 1)
        
        # Impact based on project scope and metrics
        impact_score = 0.0
        if project.metrics:
            impact_score += 0.4
        if project.project_url or project.repository_url:
            impact_score += 0.3  # Demonstrates actual work
        if project.team_size and project.team_size > 1:
            impact_score += 0.3  # Collaboration experience
        
        # Recency for projects
        recency_score = 0.0
        if project.end_date:
            days_ago = (datetime.utcnow() - project.end_date).days
            recency_score = max(0.0, 1.0 - (days_ago / (2 * 365)))
        else:
            recency_score = 0.7  # Ongoing projects
        
        # Skill demonstration through technologies
        skill_demo_score = 0.0
        required_skills_lower = [s.lower() for s in job_analysis.required_skills]
        for tech in (project.technologies_used or []):
            if tech.lower() in required_skills_lower:
                skill_demo_score += 0.25
        skill_demo_score = min(1.0, skill_demo_score)
        
        quantified_score = 1.0 if project.metrics else 0.0
        
        total_score = (
            keyword_relevance * self.scoring_weights["keyword_relevance"] +
            impact_score * self.scoring_weights["impact_level"] +
            recency_score * self.scoring_weights["recency"] +
            skill_demo_score * self.scoring_weights["skill_demonstration"] +
            quantified_score * self.scoring_weights["quantified_results"]
        )
        
        priority_tier = self._calculate_priority_tier(total_score)
        word_count = len(f"{project.project_name} {project.role}".split()) + 8
        
        return ScoredContent(
            content_id=str(project.id),
            content_type=ContentType.PROJECT,
            content_data={
                "name": project.project_name,
                "role": project.role,
                "description": project.project_description,
                "technologies": project.technologies_used,
                "url": project.project_url
            },
            keyword_relevance_score=keyword_relevance,
            impact_level_score=impact_score,
            recency_score=recency_score,
            skill_demonstration_score=skill_demo_score,
            quantified_results_score=quantified_score,
            total_score=total_score,
            priority_tier=priority_tier,
            estimated_word_count=word_count,
            keywords_matched=keyword_matches,
            reasoning=f"Project demonstrating {len(keyword_matches)} relevant technologies"
        )
    
    async def _score_education(
        self, 
        education: EducationEntry, 
        job_keywords: List[str], 
        job_analysis: JobAnalysisResult
    ) -> ScoredContent:
        """Score education entry."""
        
        edu_text = f"{education.degree_type} {education.field_of_study} {education.institution_name}".lower()
        
        # Education scoring is more straightforward
        keyword_matches = []
        for keyword in job_keywords:
            if keyword in edu_text:
                keyword_matches.append(keyword)
        keyword_relevance = len(keyword_matches) / max(len(job_keywords), 1)
        
        # Impact based on degree level and GPA
        impact_score = 0.0
        if education.degree_type:
            degree_lower = education.degree_type.lower()
            if "phd" in degree_lower or "doctorate" in degree_lower:
                impact_score = 1.0
            elif "master" in degree_lower or "mba" in degree_lower:
                impact_score = 0.8
            elif "bachelor" in degree_lower:
                impact_score = 0.6
            else:
                impact_score = 0.4
        
        if education.gpa and education.gpa >= 3.5:
            impact_score += 0.2
        
        # Recency matters less for education but still relevant
        recency_score = 0.0
        if education.end_date:
            years_ago = (datetime.utcnow() - education.end_date).days / 365
            recency_score = max(0.2, 1.0 - (years_ago / 10))  # Degrades over 10 years
        else:
            recency_score = 0.5
        
        skill_demo_score = 0.5  # Education demonstrates foundational skills
        quantified_score = 1.0 if education.gpa else 0.0
        
        total_score = (
            keyword_relevance * self.scoring_weights["keyword_relevance"] +
            impact_score * self.scoring_weights["impact_level"] +
            recency_score * self.scoring_weights["recency"] +
            skill_demo_score * self.scoring_weights["skill_demonstration"] +
            quantified_score * self.scoring_weights["quantified_results"]
        )
        
        priority_tier = self._calculate_priority_tier(total_score)
        word_count = len(f"{education.degree_type} {education.field_of_study} {education.institution_name}".split())
        
        return ScoredContent(
            content_id=str(education.id),
            content_type=ContentType.EDUCATION,
            content_data={
                "degree": education.degree_type,
                "field": education.field_of_study,
                "institution": education.institution_name,
                "graduation": education.end_date,
                "gpa": education.gpa
            },
            keyword_relevance_score=keyword_relevance,
            impact_level_score=impact_score,
            recency_score=recency_score,
            skill_demonstration_score=skill_demo_score,
            quantified_results_score=quantified_score,
            total_score=total_score,
            priority_tier=priority_tier,
            estimated_word_count=word_count,
            keywords_matched=keyword_matches,
            reasoning=f"Education with {education.degree_type} in relevant field"
        )
    
    def _calculate_priority_tier(self, total_score: float) -> int:
        """Calculate priority tier based on total score."""
        if total_score >= 0.8:
            return 1  # Highest priority
        elif total_score >= 0.6:
            return 2  # High priority
        elif total_score >= 0.4:
            return 3  # Medium priority
        elif total_score >= 0.2:
            return 4  # Low priority
        else:
            return 5  # Lowest priority
    
    async def _optimize_content_selection(
        self, 
        scored_content: Dict[ContentType, List[ScoredContent]], 
        job_analysis: JobAnalysisResult,
        user_profile_id: str
    ) -> ContentSelectionResult:
        """Optimize content selection for one-page constraint and maximum impact."""
        
        optimization_notes = []
        
        # Start with highest-priority content
        selected_achievements = []
        selected_work_experiences = []
        selected_skills = []
        selected_projects = []
        selected_education = []
        
        current_word_count = 0
        
        # 1. Always include top work experiences (essential for context)
        for work_exp in scored_content[ContentType.WORK_EXPERIENCE][:3]:  # Top 3 most recent/relevant
            if current_word_count + work_exp.estimated_word_count <= self.max_word_count:
                selected_work_experiences.append(work_exp)
                current_word_count += work_exp.estimated_word_count
            else:
                break
        
        # 2. Select achievements greedily by score, respecting word limit
        for achievement in scored_content[ContentType.ACHIEVEMENT]:
            if (len(selected_achievements) < self.max_achievements and 
                current_word_count + achievement.estimated_word_count <= self.max_word_count):
                selected_achievements.append(achievement)
                current_word_count += achievement.estimated_word_count
            elif current_word_count >= self.max_word_count:
                break
        
        # 3. Select skills (compact, high value)
        skills_word_budget = 30  # Reserve words for skills section
        skills_used = 0
        for skill in scored_content[ContentType.SKILL]:
            if (len(selected_skills) < self.max_skills and 
                skills_used + skill.estimated_word_count <= skills_word_budget):
                selected_skills.append(skill)
                skills_used += skill.estimated_word_count
        current_word_count += skills_used
        
        # 4. Select projects if space allows
        for project in scored_content[ContentType.PROJECT]:
            if (len(selected_projects) < self.max_projects and 
                current_word_count + project.estimated_word_count <= self.max_word_count):
                selected_projects.append(project)
                current_word_count += project.estimated_word_count
        
        # 5. Include education (usually compact)
        for education in scored_content[ContentType.EDUCATION][:2]:  # Max 2 education entries
            if current_word_count + education.estimated_word_count <= self.max_word_count:
                selected_education.append(education)
                current_word_count += education.estimated_word_count
        
        # Calculate optimization metrics
        total_score = self._calculate_total_selection_score(
            selected_achievements + selected_work_experiences + selected_skills + selected_projects + selected_education
        )
        
        one_page_compliant = current_word_count <= self.max_word_count
        
        # Calculate content diversity (different categories represented)
        diversity_score = self._calculate_diversity_score([
            selected_achievements, selected_work_experiences, selected_skills, selected_projects, selected_education
        ])
        
        # Calculate keyword coverage
        all_selected_keywords = []
        for content_list in [selected_achievements, selected_work_experiences, selected_skills, selected_projects, selected_education]:
            for content in content_list:
                all_selected_keywords.extend(content.keywords_matched)
        
        unique_keywords = set(all_selected_keywords)
        total_job_keywords = set(job_analysis.required_skills + job_analysis.preferred_skills + job_analysis.important_keywords)
        keyword_coverage = len(unique_keywords.intersection(total_job_keywords)) / max(len(total_job_keywords), 1)
        
        # Add optimization notes
        optimization_notes.append(f"Selected {len(selected_achievements)} achievements from {len(scored_content[ContentType.ACHIEVEMENT])} available")
        optimization_notes.append(f"Word count: {current_word_count}/{self.max_word_count} ({'✓' if one_page_compliant else '⚠️ over limit'})")
        optimization_notes.append(f"Keyword coverage: {keyword_coverage:.1%}")
        
        return ContentSelectionResult(
            job_analysis_id=job_analysis.analysis_id or job_analysis.job_description_hash,
            user_profile_id=user_profile_id,
            selected_achievements=selected_achievements,
            selected_work_experiences=selected_work_experiences,
            selected_skills=selected_skills,
            selected_projects=selected_projects,
            selected_education=selected_education,
            total_score=total_score,
            estimated_word_count=current_word_count,
            one_page_compliant=one_page_compliant,
            content_diversity_score=diversity_score,
            keyword_coverage_percentage=keyword_coverage * 100,
            selection_algorithm="multi_dimensional_greedy_v1",
            selection_criteria={
                "max_word_count": self.max_word_count,
                "max_achievements": self.max_achievements,
                "scoring_weights": self.scoring_weights,
                "job_analysis_confidence": job_analysis.confidence_score
            },
            optimization_notes=optimization_notes
        )
    
    def _calculate_total_selection_score(self, selected_content: List[ScoredContent]) -> float:
        """Calculate total score for selected content."""
        if not selected_content:
            return 0.0
        
        # Weighted average of all selected content scores
        total_weighted_score = sum(content.total_score for content in selected_content)
        return total_weighted_score / len(selected_content)
    
    def _calculate_diversity_score(self, content_lists: List[List[ScoredContent]]) -> float:
        """Calculate diversity score based on representation across categories."""
        categories_with_content = sum(1 for content_list in content_lists if len(content_list) > 0)
        max_categories = len(content_lists)
        return categories_with_content / max_categories
    
    async def _store_selection_results(self, selection_result: ContentSelectionResult):
        """Store content selection results to database."""
        try:
            with db_service.get_session() as session:
                # Prepare selected content IDs
                selected_achievement_ids = [c.content_id for c in selection_result.selected_achievements]
                
                # Find the JobAnalysis ID by hash if needed
                job_analysis_id = selection_result.job_analysis_id
                if len(job_analysis_id) == 64:  # It's a hash, need to find the actual ID
                    job_analysis = session.query(JobAnalysis).filter_by(
                        job_description_hash=job_analysis_id
                    ).first()
                    if job_analysis:
                        job_analysis_id = str(job_analysis.id)
                    else:
                        job_analysis_id = None  # Skip storing if analysis not found
                
                # Create content selection record
                content_selection = ContentSelection(
                    profile_id=selection_result.user_profile_id,
                    job_analysis_id=job_analysis_id,
                    selection_algorithm=selection_result.selection_algorithm,
                    selection_criteria=selection_result.selection_criteria,
                    total_score=selection_result.total_score,
                    selected_achievements=selected_achievement_ids,
                    achievement_scores={
                        c.content_id: c.total_score for c in selection_result.selected_achievements
                    },
                    one_page_compliant=selection_result.one_page_compliant,
                    estimated_word_count=selection_result.estimated_word_count,
                    content_density_score=selection_result.content_diversity_score
                )
                
                session.add(content_selection)
                session.commit()
                session.refresh(content_selection)
                
                self.logger.info(f"Stored content selection results: {content_selection.id}")
                
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to store selection results: {e}")
            # Don't raise exception - this is for tracking only
    
    async def get_selected_content_for_job(
        self, 
        user_id: str, 
        job_analysis_id: str, 
        manual_overrides: Optional[Dict[str, List[str]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get previously selected content for a job analysis ID.
        If not found, perform new content selection.
        """
        try:
            with db_service.get_session() as session:
                # Get user profile
                user_profile = session.query(UserProfile).filter_by(user_id=UUID(user_id)).first()
                if not user_profile:
                    self.logger.error(f"User profile not found: {user_id}")
                    return None
                
                # Try to find existing content selection
                content_selection = session.query(ContentSelection).filter_by(
                    profile_id=user_profile.id,
                    job_analysis_id=UUID(job_analysis_id)
                ).first()
                
                if content_selection and not manual_overrides:
                    # Return existing selection
                    self.logger.info(f"Found existing content selection for job {job_analysis_id}")
                    return await self._convert_selection_to_content_dict(content_selection, session)
                
                # Need to perform new selection
                # Get job analysis
                job_analysis = session.query(JobAnalysis).filter_by(id=UUID(job_analysis_id)).first()
                if not job_analysis:
                    self.logger.error(f"Job analysis not found: {job_analysis_id}")
                    return None
                
                # Convert to JobAnalysisResult format
                job_analysis_result = JobAnalysisResult(
                    job_description_hash=job_analysis.job_description_hash,
                    company_name=job_analysis.company_name,
                    position_title=job_analysis.position_title,
                    industry=job_analysis.industry,
                    employment_type=job_analysis.employment_type,
                    seniority_level=job_analysis.seniority_level,
                    required_skills=job_analysis.required_skills or [],
                    preferred_skills=job_analysis.preferred_skills or [],
                    important_keywords=job_analysis.important_keywords or [],
                    ats_keywords=job_analysis.ats_keywords or [],
                    salary_range_estimate=job_analysis.salary_range_estimate,
                    confidence_score=job_analysis.confidence_score,
                    difficulty_level=job_analysis.difficulty_level,
                    competition_level=job_analysis.competition_level
                )
                
                # Perform content selection
                selection_result = await self.select_optimal_content(
                    user_profile_id=str(user_profile.id),
                    job_analysis=job_analysis_result,
                    manual_overrides=manual_overrides
                )
                
                if selection_result:
                    # Convert to format expected by LaTeX service
                    return await self._convert_result_to_content_dict(selection_result, session)
                else:
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error getting selected content for job: {e}")
            return None
    
    async def _convert_selection_to_content_dict(
        self, 
        content_selection: ContentSelection, 
        session: Session
    ) -> Dict[str, Any]:
        """Convert ContentSelection DB record to content dictionary."""
        try:
            # Get selected achievements
            achievement_ids = content_selection.selected_achievements or []
            achievements = session.query(Achievement).filter(
                Achievement.id.in_([UUID(aid) for aid in achievement_ids])
            ).all()
            
            # Group achievements by work experience
            work_experiences = {}
            for achievement in achievements:
                exp_id = str(achievement.work_experience_id)
                if exp_id not in work_experiences:
                    work_experience = session.query(WorkExperience).filter_by(
                        id=achievement.work_experience_id
                    ).first()
                    work_experiences[exp_id] = {
                        'experience': work_experience,
                        'achievements': []
                    }
                work_experiences[exp_id]['achievements'].append(achievement)
            
            # Get user's education, skills, etc.
            user_profile = session.query(UserProfile).filter_by(
                id=content_selection.profile_id
            ).first()
            
            education = session.query(EducationEntry).filter_by(
                profile_id=user_profile.id
            ).all()
            
            skills = session.query(Skill).filter_by(
                profile_id=user_profile.id
            ).all()
            
            return {
                'work_experiences': list(work_experiences.values()),
                'education': education,
                'skills': skills,
                'projects': [],  # Add project support later
                'certifications': []  # Add certification support later
            }
            
        except Exception as e:
            self.logger.error(f"Error converting selection to content dict: {e}")
            return {}
    
    async def _convert_result_to_content_dict(
        self, 
        selection_result: ContentSelectionResult, 
        session: Session
    ) -> Dict[str, Any]:
        """Convert ContentSelectionResult to content dictionary."""
        try:
            # Get selected achievements by ID
            achievement_ids = [UUID(c.content_id) for c in selection_result.selected_achievements]
            achievements = session.query(Achievement).filter(
                Achievement.id.in_(achievement_ids)
            ).all()
            
            # Group by work experience
            work_experiences = {}
            for achievement in achievements:
                exp_id = str(achievement.work_experience_id)
                if exp_id not in work_experiences:
                    work_experience = session.query(WorkExperience).filter_by(
                        id=achievement.work_experience_id
                    ).first()
                    work_experiences[exp_id] = {
                        'experience': work_experience,
                        'achievements': []
                    }
                work_experiences[exp_id]['achievements'].append(achievement)
            
            # Get other content
            user_profile = session.query(UserProfile).filter_by(
                id=UUID(selection_result.user_profile_id)
            ).first()
            
            education = session.query(EducationEntry).filter_by(
                profile_id=user_profile.id
            ).all()
            
            skills = session.query(Skill).filter_by(
                profile_id=user_profile.id
            ).all()
            
            return {
                'work_experiences': list(work_experiences.values()),
                'education': education,
                'skills': skills,
                'projects': [],
                'certifications': []
            }
            
        except Exception as e:
            self.logger.error(f"Error converting result to content dict: {e}")
            return {}
    
    def get_selection_stats(self) -> Dict[str, Any]:
        """Get statistics about content selection usage."""
        try:
            with db_service.get_session() as session:
                total_selections = session.query(ContentSelection).count()
                
                # Recent selections (last 7 days)
                week_ago = datetime.utcnow() - timedelta(days=7)
                recent_selections = session.query(ContentSelection).filter(
                    ContentSelection.created_at >= week_ago
                ).count()
                
                # Average scores and metrics
                from sqlalchemy import func
                avg_stats = session.query(
                    func.avg(ContentSelection.total_score).label('avg_score'),
                    func.avg(ContentSelection.estimated_word_count).label('avg_words'),
                    func.avg(ContentSelection.content_density_score).label('avg_diversity')
                ).first()
                
                return {
                    "total_selections": total_selections,
                    "selections_this_week": recent_selections,
                    "average_score": float(avg_stats.avg_score) if avg_stats.avg_score else 0.0,
                    "average_word_count": int(avg_stats.avg_words) if avg_stats.avg_words else 0,
                    "average_diversity": float(avg_stats.avg_diversity) if avg_stats.avg_diversity else 0.0,
                    "one_page_compliance_rate": self._calculate_compliance_rate(session)
                }
                
        except Exception as e:
            self.logger.error(f"Error getting selection stats: {e}")
            return {"error": str(e)}
    
    def _calculate_compliance_rate(self, session: Session) -> float:
        """Calculate one-page compliance rate."""
        try:
            total = session.query(ContentSelection).count()
            compliant = session.query(ContentSelection).filter_by(one_page_compliant=True).count()
            return (compliant / total) if total > 0 else 0.0
        except:
            return 0.0


# Global service instance
content_selector = ContentSelectionEngine()