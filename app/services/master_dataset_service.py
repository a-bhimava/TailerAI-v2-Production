"""
Master Dataset Service for TailerAI v2.0.
Handles all master dataset operations including creation, management, and content selection.
Following project blueprint best practices for modular, secure, and error-resistant design.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_, desc, func

from app.models.database import (
    UserProfile, WorkExperience, Achievement, EducationEntry, 
    Skill, Project, JobAnalysis, ContentSelection
)
from app.services.database_service import db_service, DatabaseError
from app.services.achievement_categorization_service import get_categorization_service

logger = logging.getLogger(__name__)


class MasterDatasetError(Exception):
    """Custom exception for master dataset operations."""
    pass


class MasterDatasetService:
    """
    Service for managing master dataset operations.
    Implements PRD-002 and PRD-003 functionality.
    """
    
    def __init__(self):
        self.logger = logger
    
    # User Profile Management
    
    async def create_user_profile(
        self, 
        user_id: str, 
        profile_data: Dict[str, Any]
    ) -> UserProfile:
        """
        Create a new user profile with validation.
        Following blueprint error handling practices.
        """
        try:
            with db_service.get_session() as session:
                # Check if user already exists
                existing_user = session.query(UserProfile).filter_by(
                    user_id=user_id
                ).first()
                
                if existing_user:
                    raise MasterDatasetError(f"User profile already exists for user_id: {user_id}")
                
                # Create new user profile
                user_profile = UserProfile(
                    user_id=user_id,
                    full_name=profile_data.get('full_name', ''),
                    email=profile_data.get('email', ''),
                    phone=profile_data.get('phone', ''),
                    linkedin_url=profile_data.get('linkedin_url', ''),
                    location=profile_data.get('location', ''),
                    target_industries=profile_data.get('target_industries', []),
                    career_level=profile_data.get('career_level', ''),
                    privacy_settings=profile_data.get('privacy_settings', {}),
                    notification_preferences=profile_data.get('notification_preferences', {})
                )
                
                session.add(user_profile)
                session.commit()
                session.refresh(user_profile)
                
                self.logger.info(f"Created user profile for user_id: {user_id}")
                return user_profile
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error creating user profile: {str(e)}")
            raise MasterDatasetError(f"Failed to create user profile: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error creating user profile: {str(e)}")
            raise MasterDatasetError(f"Unexpected error: {str(e)}")
    
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by user_id."""
        try:
            with db_service.get_session() as session:
                # Convert string to UUID if necessary
                if isinstance(user_id, str):
                    user_uuid = UUID(user_id)
                else:
                    user_uuid = user_id
                    
                user_profile = session.query(UserProfile).filter_by(
                    user_id=user_uuid
                ).first()
                
                return user_profile
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error retrieving user profile: {str(e)}")
            raise MasterDatasetError(f"Failed to retrieve user profile: {str(e)}")
    
    async def update_user_profile(
        self, 
        user_id: str, 
        update_data: Dict[str, Any]
    ) -> UserProfile:
        """Update user profile with new data."""
        try:
            with db_service.get_session() as session:
                # Convert string to UUID if necessary
                if isinstance(user_id, str):
                    user_uuid = UUID(user_id)
                else:
                    user_uuid = user_id
                    
                user_profile = session.query(UserProfile).filter_by(
                    user_id=user_uuid
                ).first()
                
                if not user_profile:
                    raise MasterDatasetError(f"User profile not found: {user_id}")
                
                # Update allowed fields
                allowed_fields = [
                    'full_name', 'email', 'phone', 'linkedin_url', 'location',
                    'target_industries', 'career_level', 'job_search_status',
                    'privacy_settings', 'notification_preferences'
                ]
                
                for field, value in update_data.items():
                    if field in allowed_fields and hasattr(user_profile, field):
                        setattr(user_profile, field, value)
                
                user_profile.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(user_profile)
                
                self.logger.info(f"Updated user profile for user_id: {user_id}")
                return user_profile
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error updating user profile: {str(e)}")
            raise MasterDatasetError(f"Failed to update user profile: {str(e)}")
    
    # Work Experience Management
    
    async def add_work_experience(
        self, 
        user_id: str, 
        experience_data: Dict[str, Any]
    ) -> WorkExperience:
        """Add new work experience to user's master dataset."""
        try:
            with db_service.get_session() as session:
                # Convert string to UUID if necessary
                if isinstance(user_id, str):
                    user_uuid = UUID(user_id)
                else:
                    user_uuid = user_id
                    
                # Get user profile
                user_profile = session.query(UserProfile).filter_by(
                    user_id=user_uuid
                ).first()
                
                if not user_profile:
                    raise MasterDatasetError(f"User profile not found: {user_id}")
                
                # Create work experience
                work_experience = WorkExperience(
                    profile_id=user_profile.id,
                    company_name=experience_data.get('company_name', ''),
                    position_title=experience_data.get('position_title', ''),
                    employment_type=experience_data.get('employment_type', 'full-time'),
                    start_date=experience_data.get('start_date'),
                    end_date=experience_data.get('end_date'),
                    location=experience_data.get('location', ''),
                    company_size=experience_data.get('company_size', ''),
                    industry=experience_data.get('industry', ''),
                    company_description=experience_data.get('company_description', ''),
                    role_summary=experience_data.get('role_summary', ''),
                    team_size=experience_data.get('team_size'),
                    reporting_structure=experience_data.get('reporting_structure', '')
                )
                
                session.add(work_experience)
                session.commit()
                session.refresh(work_experience)
                
                # Force load all attributes before session closes to avoid DetachedInstanceError
                _ = work_experience.id
                _ = work_experience.company_name
                _ = work_experience.position_title
                _ = work_experience.employment_type
                _ = work_experience.start_date
                _ = work_experience.end_date
                _ = work_experience.location
                _ = work_experience.created_at
                _ = work_experience.updated_at
                _ = work_experience.is_current  # Load the is_current property
                
                # Expunge from session to make it independent
                session.expunge(work_experience)
                
                self.logger.info(f"Added work experience for user_id: {user_id}, company: {experience_data.get('company_name')}")
                return work_experience
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error adding work experience: {str(e)}")
            error_str = str(e)
            if "UNIQUE constraint failed" in error_str and "work_experiences" in error_str:
                raise MasterDatasetError("A work experience with the same company, position, and start date already exists")
            raise MasterDatasetError(f"Failed to add work experience: {str(e)}")
    
    async def get_work_experiences(self, user_id: str) -> List[WorkExperience]:
        """Get all work experiences for a user, ordered by start date (most recent first)."""
        try:
            with db_service.get_session() as session:
                # Convert string to UUID if necessary
                if isinstance(user_id, str):
                    user_uuid = UUID(user_id)
                else:
                    user_uuid = user_id
                    
                user_profile = session.query(UserProfile).filter_by(
                    user_id=user_uuid
                ).first()
                
                if not user_profile:
                    return []
                
                work_experiences = session.query(WorkExperience).filter_by(
                    profile_id=user_profile.id
                ).order_by(desc(WorkExperience.start_date)).all()
                
                return work_experiences
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error retrieving work experiences: {str(e)}")
            raise MasterDatasetError(f"Failed to retrieve work experiences: {str(e)}")
    
    async def delete_work_experience(self, user_id: str, experience_id: str) -> bool:
        """Delete work experience and all associated achievements."""
        try:
            with db_service.get_session() as session:
                # Convert string to UUID if necessary
                if isinstance(user_id, str):
                    user_uuid = UUID(user_id)
                else:
                    user_uuid = user_id
                    
                if isinstance(experience_id, str):
                    exp_uuid = UUID(experience_id)
                else:
                    exp_uuid = experience_id
                    
                # Get user profile
                user_profile = session.query(UserProfile).filter_by(
                    user_id=user_uuid
                ).first()
                
                if not user_profile:
                    raise MasterDatasetError(f"User profile not found: {user_id}")
                
                # Get work experience and verify ownership
                work_experience = session.query(WorkExperience).filter_by(
                    id=exp_uuid,
                    profile_id=user_profile.id
                ).first()
                
                if not work_experience:
                    raise MasterDatasetError(f"Work experience not found or access denied: {experience_id}")
                
                # Delete associated achievements first (due to foreign key constraints)
                achievements_deleted = session.query(Achievement).filter_by(
                    experience_id=exp_uuid
                ).delete()
                
                # Delete the work experience
                session.delete(work_experience)
                session.commit()
                
                self.logger.info(f"Deleted work experience {experience_id} for user {user_id}, with {achievements_deleted} associated achievements")
                return True
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error deleting work experience: {str(e)}")
            raise MasterDatasetError(f"Failed to delete work experience: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error deleting work experience: {str(e)}")
            raise MasterDatasetError(f"Unexpected error: {str(e)}")
    
    async def update_work_experience(self, user_id: str, experience_id: str, experience_data: Dict[str, Any]) -> Optional[WorkExperience]:
        """Update work experience for a user."""
        try:
            with db_service.get_session() as session:
                # Convert string to UUID if necessary
                if isinstance(user_id, str):
                    user_uuid = UUID(user_id)
                else:
                    user_uuid = user_id
                    
                if isinstance(experience_id, str):
                    exp_uuid = UUID(experience_id)
                else:
                    exp_uuid = experience_id
                    
                # Get user profile
                user_profile = session.query(UserProfile).filter_by(
                    user_id=user_uuid
                ).first()
                
                if not user_profile:
                    raise MasterDatasetError(f"User profile not found: {user_id}")
                
                # Get work experience and verify ownership
                work_experience = session.query(WorkExperience).filter_by(
                    id=exp_uuid,
                    profile_id=user_profile.id
                ).first()
                
                if not work_experience:
                    raise MasterDatasetError(f"Work experience not found or access denied: {experience_id}")
                
                # Update work experience fields
                if 'company_name' in experience_data:
                    work_experience.company_name = experience_data['company_name']
                if 'position_title' in experience_data:
                    work_experience.position_title = experience_data['position_title']
                if 'department' in experience_data:
                    work_experience.department = experience_data['department']
                if 'employment_type' in experience_data:
                    work_experience.employment_type = experience_data['employment_type']
                if 'start_date' in experience_data:
                    work_experience.start_date = experience_data['start_date']
                if 'end_date' in experience_data:
                    work_experience.end_date = experience_data['end_date']
                if 'location' in experience_data:
                    work_experience.location = experience_data['location']
                if 'job_description' in experience_data:
                    work_experience.job_description = experience_data['job_description']
                if 'is_current' in experience_data:
                    # Handle is_current flag - if True, set end_date to None
                    if experience_data['is_current']:
                        work_experience.end_date = None
                
                session.commit()
                session.refresh(work_experience)
                
                # Force load all attributes before session closes to avoid DetachedInstanceError
                _ = work_experience.id
                _ = work_experience.company_name
                _ = work_experience.position_title
                _ = work_experience.department
                _ = work_experience.employment_type
                _ = work_experience.start_date
                _ = work_experience.end_date
                _ = work_experience.location
                _ = work_experience.job_description
                _ = work_experience.created_at
                _ = work_experience.updated_at
                _ = work_experience.is_current
                
                # Expunge from session to make it independent
                session.expunge(work_experience)
                
                self.logger.info(f"Updated work experience {experience_id} for user {user_id}")
                return work_experience
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error updating work experience: {str(e)}")
            raise MasterDatasetError(f"Failed to update work experience: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error updating work experience: {str(e)}")
            raise MasterDatasetError(f"Unexpected error: {str(e)}")
    
    # Achievement Management
    
    async def add_achievement(
        self, 
        user_id: str, 
        experience_id: UUID, 
        achievement_data: Dict[str, Any]
    ) -> Achievement:
        """Add new achievement to a work experience."""
        try:
            with db_service.get_session() as session:
                # Convert string to UUID if necessary
                if isinstance(user_id, str):
                    user_uuid = UUID(user_id)
                else:
                    user_uuid = user_id
                    
                # Get user profile
                user_profile = session.query(UserProfile).filter_by(
                    user_id=user_uuid
                ).first()
                
                if not user_profile:
                    raise MasterDatasetError(f"User profile not found: {user_id}")
                
                # Verify work experience belongs to user
                work_experience = session.query(WorkExperience).filter_by(
                    id=experience_id,
                    profile_id=user_profile.id
                ).first()
                
                if not work_experience:
                    raise MasterDatasetError(f"Work experience not found: {experience_id}")
                
                # Get achievement text and context for categorization
                achievement_text = achievement_data.get('achievement_text', '')
                work_context = f"{work_experience.position} at {work_experience.company_name}"
                
                # Auto-categorize achievement if not provided
                provided_category = achievement_data.get('achievement_category', '')
                provided_function = achievement_data.get('business_function', '')
                
                if not provided_category or not provided_function:
                    try:
                        categorization_service = get_categorization_service()
                        category, business_function, confidence = await categorization_service.categorize_achievement(
                            achievement_text, work_context
                        )
                        
                        # Use provided values if available, otherwise use AI categorization
                        final_category = provided_category if provided_category else category
                        final_function = provided_function if provided_function else business_function
                        
                        self.logger.info(f"Auto-categorized achievement: {final_category}/{final_function} (confidence: {confidence})")
                        
                    except Exception as e:
                        self.logger.warning(f"Auto-categorization failed, using defaults: {e}")
                        final_category = provided_category if provided_category else 'operational'
                        final_function = provided_function if provided_function else 'general'
                else:
                    final_category = provided_category
                    final_function = provided_function
                
                # Create achievement with categorization
                achievement = Achievement(
                    profile_id=user_profile.id,
                    experience_id=experience_id,
                    achievement_text=achievement_text,
                    achievement_category=final_category,
                    impact_level=achievement_data.get('impact_level', 5),
                    business_function=final_function,
                    quantified_metrics=achievement_data.get('quantified_metrics', {}),
                    keywords=achievement_data.get('keywords', []),
                    ats_keywords=achievement_data.get('ats_keywords', []),
                    skills_demonstrated=achievement_data.get('skills_demonstrated', []),
                    time_period=achievement_data.get('time_period', ''),
                    context_tags=achievement_data.get('context_tags', [])
                )
                
                session.add(achievement)
                session.commit()
                session.refresh(achievement)
                
                # Extract data while session is still active to avoid detached instance errors
                achievement_data_copy = {
                    'id': achievement.id,
                    'achievement_text': achievement.achievement_text,
                    'achievement_category': achievement.achievement_category,
                    'impact_level': achievement.impact_level,
                    'business_function': achievement.business_function,
                    'keywords': achievement.keywords,
                    'skills_demonstrated': achievement.skills_demonstrated,
                    'quantified_metrics': achievement.quantified_metrics,
                    'ats_keywords': achievement.ats_keywords,
                    'time_period': achievement.time_period,
                    'context_tags': achievement.context_tags,
                    'selection_count': achievement.selection_count,
                    'success_correlation': achievement.success_correlation,
                    'experience_id': achievement.experience_id,
                    'profile_id': achievement.profile_id
                }
                
                self.logger.info(f"Added achievement for user_id: {user_id}, experience_id: {experience_id}")
                
                # Create a mock object with the data to return
                class AchievementData:
                    def __init__(self, data):
                        for key, value in data.items():
                            setattr(self, key, value)
                
                return AchievementData(achievement_data_copy)
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error adding achievement: {str(e)}")
            raise MasterDatasetError(f"Failed to add achievement: {str(e)}")
    
    async def get_achievements(
        self, 
        user_id: str, 
        experience_id: Optional[UUID] = None,
        category: Optional[str] = None,
        min_impact_level: Optional[int] = None
    ) -> List[Achievement]:
        """
        Get achievements with optional filtering.
        Used for content selection algorithms.
        """
        try:
            with db_service.get_session() as session:
                # Convert string to UUID if necessary
                if isinstance(user_id, str):
                    user_uuid = UUID(user_id)
                else:
                    user_uuid = user_id
                    
                user_profile = session.query(UserProfile).filter_by(
                    user_id=user_uuid
                ).first()
                
                if not user_profile:
                    return []
                
                # Build query with filters
                query = session.query(Achievement).filter_by(
                    profile_id=user_profile.id
                )
                
                if experience_id:
                    query = query.filter_by(experience_id=experience_id)
                
                if category:
                    query = query.filter_by(achievement_category=category)
                
                if min_impact_level:
                    query = query.filter(Achievement.impact_level >= min_impact_level)
                
                # Order by impact level and selection performance
                achievements = query.order_by(
                    desc(Achievement.impact_level),
                    desc(Achievement.success_correlation),
                    desc(Achievement.selection_count)
                ).all()
                
                return achievements
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error retrieving achievements: {str(e)}")
            raise MasterDatasetError(f"Failed to retrieve achievements: {str(e)}")
    
    async def update_achievement_performance(
        self, 
        achievement_id: UUID, 
        outcome: str
    ) -> None:
        """
        Update achievement performance metrics based on application outcomes.
        Used for continuous learning and optimization.
        """
        try:
            with db_service.get_session() as session:
                achievement = session.query(Achievement).filter_by(
                    id=achievement_id
                ).first()
                
                if not achievement:
                    raise MasterDatasetError(f"Achievement not found: {achievement_id}")
                
                # Update selection count
                achievement.selection_count += 1
                achievement.last_selected = datetime.utcnow()
                
                # Update success correlation based on outcome
                if outcome in ["interview", "offer"]:
                    # Positive outcome - increase success correlation
                    achievement.success_correlation = min(
                        1.0, 
                        achievement.success_correlation + 0.1
                    )
                elif outcome in ["rejected"]:
                    # Negative outcome - slightly decrease success correlation
                    achievement.success_correlation = max(
                        0.0, 
                        achievement.success_correlation - 0.05
                    )
                
                session.commit()
                self.logger.info(f"Updated achievement performance: {achievement_id}, outcome: {outcome}")
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error updating achievement performance: {str(e)}")
            raise MasterDatasetError(f"Failed to update achievement performance: {str(e)}")
    
    # Skills Management
    
    async def add_skill(self, user_id: str, skill_data: Dict[str, Any]) -> Skill:
        """Add new skill to user's master dataset."""
        try:
            with db_service.get_session() as session:
                # Convert string to UUID if necessary
                if isinstance(user_id, str):
                    user_uuid = UUID(user_id)
                else:
                    user_uuid = user_id
                    
                user_profile = session.query(UserProfile).filter_by(
                    user_id=user_uuid
                ).first()
                
                if not user_profile:
                    raise MasterDatasetError(f"User profile not found: {user_id}")
                
                # Check if skill already exists
                existing_skill = session.query(Skill).filter_by(
                    profile_id=user_profile.id,
                    skill_name=skill_data.get('skill_name', '')
                ).first()
                
                if existing_skill:
                    raise MasterDatasetError(f"Skill already exists: {skill_data.get('skill_name')}")
                
                skill = Skill(
                    profile_id=user_profile.id,
                    skill_name=skill_data.get('skill_name', ''),
                    skill_category=skill_data.get('skill_category', ''),
                    proficiency_level=skill_data.get('proficiency_level', 'intermediate'),
                    years_experience=skill_data.get('years_experience'),
                    last_used=skill_data.get('last_used'),
                    certification_name=skill_data.get('certification_name', ''),
                    certification_date=skill_data.get('certification_date'),
                    related_keywords=skill_data.get('related_keywords', []),
                    industry_relevance=skill_data.get('industry_relevance', [])
                )
                
                session.add(skill)
                session.commit()
                session.refresh(skill)
                
                self.logger.info(f"Added skill for user_id: {user_id}, skill: {skill_data.get('skill_name')}")
                return skill
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error adding skill: {str(e)}")
            error_str = str(e)
            if "UNIQUE constraint failed" in error_str and "skills" in error_str:
                raise MasterDatasetError(f"The skill '{skill_data.get('skill_name', 'unknown')}' already exists in your profile")
            raise MasterDatasetError(f"Failed to add skill: {str(e)}")
    
    async def get_skills(
        self, 
        user_id: str, 
        category: Optional[str] = None
    ) -> List[Skill]:
        """Get all skills for a user, optionally filtered by category."""
        try:
            with db_service.get_session() as session:
                # Convert string to UUID if necessary
                if isinstance(user_id, str):
                    user_uuid = UUID(user_id)
                else:
                    user_uuid = user_id
                    
                user_profile = session.query(UserProfile).filter_by(
                    user_id=user_uuid
                ).first()
                
                if not user_profile:
                    return []
                
                query = session.query(Skill).filter_by(
                    profile_id=user_profile.id
                )
                
                if category:
                    query = query.filter_by(skill_category=category)
                
                skills = query.order_by(
                    desc(Skill.years_experience),
                    desc(Skill.keyword_match_count),
                    Skill.skill_name
                ).all()
                
                return skills
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error retrieving skills: {str(e)}")
            raise MasterDatasetError(f"Failed to retrieve skills: {str(e)}")
    
    # Education Management
    
    async def add_education_entry(self, user_id: str, education_data: Dict[str, Any]) -> EducationEntry:
        """Add new education entry to user's master dataset."""
        try:
            with db_service.get_session() as session:
                # Convert string to UUID if necessary
                if isinstance(user_id, str):
                    user_uuid = UUID(user_id)
                else:
                    user_uuid = user_id
                    
                user_profile = session.query(UserProfile).filter_by(
                    user_id=user_uuid
                ).first()
                
                if not user_profile:
                    raise MasterDatasetError(f"User profile not found: {user_id}")
                
                education_entry = EducationEntry(
                    profile_id=user_profile.id,
                    institution_name=education_data.get('institution_name', ''),
                    degree_type=education_data.get('degree_type', ''),
                    field_of_study=education_data.get('field_of_study', ''),
                    start_date=education_data.get('start_date'),
                    end_date=education_data.get('graduation_date') or education_data.get('end_date'),
                    gpa=education_data.get('gpa'),
                    gpa_scale=education_data.get('gpa_scale', 4.0),
                    location=education_data.get('location', ''),
                    relevant_coursework=education_data.get('relevant_coursework', []) if isinstance(education_data.get('relevant_coursework'), list) else [education_data.get('relevant_coursework')] if education_data.get('relevant_coursework') else [],
                    academic_achievements=education_data.get('academic_achievements', []) if isinstance(education_data.get('academic_achievements'), list) else [education_data.get('academic_achievements')] if education_data.get('academic_achievements') else [],
                    honors=education_data.get('honors_awards', []) if isinstance(education_data.get('honors_awards'), list) else [education_data.get('honors_awards')] if education_data.get('honors_awards') else []
                )
                
                session.add(education_entry)
                session.commit()
                session.refresh(education_entry)
                
                # Force load all attributes before session closes to avoid DetachedInstanceError
                _ = education_entry.id
                _ = education_entry.institution_name
                _ = education_entry.degree_type
                _ = education_entry.field_of_study
                _ = education_entry.start_date
                _ = education_entry.end_date
                _ = education_entry.gpa
                _ = education_entry.gpa_scale
                _ = education_entry.location
                _ = education_entry.relevant_coursework
                _ = education_entry.academic_achievements
                _ = education_entry.honors
                _ = education_entry.created_at
                _ = education_entry.updated_at
                
                # Expunge from session to make it independent
                session.expunge(education_entry)
                
                self.logger.info(f"Added education entry for user_id: {user_id}, institution: {education_data.get('institution_name')}")
                return education_entry
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error adding education entry: {str(e)}")
            raise MasterDatasetError(f"Failed to add education entry: {str(e)}")
    
    async def get_education_entries(self, user_id: str) -> List[EducationEntry]:
        """Get all education entries for a user, ordered by graduation date (most recent first)."""
        try:
            with db_service.get_session() as session:
                # Convert string to UUID if necessary
                if isinstance(user_id, str):
                    user_uuid = UUID(user_id)
                else:
                    user_uuid = user_id
                    
                user_profile = session.query(UserProfile).filter_by(
                    user_id=user_uuid
                ).first()
                
                if not user_profile:
                    return []
                
                education_entries = session.query(EducationEntry).filter_by(
                    profile_id=user_profile.id
                ).order_by(desc(EducationEntry.end_date)).all()
                
                return education_entries
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error retrieving education entries: {str(e)}")
            raise MasterDatasetError(f"Failed to retrieve education entries: {str(e)}")
    
    async def delete_education_entry(self, user_id: str, education_id: str) -> bool:
        """Delete education entry."""
        try:
            with db_service.get_session() as session:
                # Convert string to UUID if necessary
                if isinstance(user_id, str):
                    user_uuid = UUID(user_id)
                else:
                    user_uuid = user_id
                    
                if isinstance(education_id, str):
                    edu_uuid = UUID(education_id)
                else:
                    edu_uuid = education_id
                    
                # Get user profile
                user_profile = session.query(UserProfile).filter_by(
                    user_id=user_uuid
                ).first()
                
                if not user_profile:
                    raise MasterDatasetError(f"User profile not found: {user_id}")
                
                # Get education entry and verify ownership
                education_entry = session.query(EducationEntry).filter_by(
                    id=edu_uuid,
                    profile_id=user_profile.id
                ).first()
                
                if not education_entry:
                    raise MasterDatasetError(f"Education entry not found or access denied: {education_id}")
                
                # Delete the education entry
                session.delete(education_entry)
                session.commit()
                
                self.logger.info(f"Deleted education entry {education_id} for user {user_id}")
                return True
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error deleting education entry: {str(e)}")
            raise MasterDatasetError(f"Failed to delete education entry: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error deleting education entry: {str(e)}")
            raise MasterDatasetError(f"Unexpected error: {str(e)}")
    
    async def update_education_entry(self, user_id: str, education_id: str, education_data: Dict[str, Any]) -> Optional[EducationEntry]:
        """Update education entry for a user."""
        try:
            with db_service.get_session() as session:
                # Convert string to UUID if necessary
                if isinstance(user_id, str):
                    user_uuid = UUID(user_id)
                else:
                    user_uuid = user_id
                    
                if isinstance(education_id, str):
                    edu_uuid = UUID(education_id)
                else:
                    edu_uuid = education_id
                    
                # Get user profile
                user_profile = session.query(UserProfile).filter_by(
                    user_id=user_uuid
                ).first()
                
                if not user_profile:
                    raise MasterDatasetError(f"User profile not found: {user_id}")
                
                # Get education entry and verify ownership
                education_entry = session.query(EducationEntry).filter_by(
                    id=edu_uuid,
                    profile_id=user_profile.id
                ).first()
                
                if not education_entry:
                    raise MasterDatasetError(f"Education entry not found or access denied: {education_id}")
                
                # Update education entry fields
                if 'institution_name' in education_data:
                    education_entry.institution_name = education_data['institution_name']
                if 'degree_type' in education_data:
                    education_entry.degree_type = education_data['degree_type']
                if 'field_of_study' in education_data:
                    education_entry.field_of_study = education_data['field_of_study']
                if 'start_date' in education_data:
                    education_entry.start_date = education_data['start_date']
                if 'end_date' in education_data or 'graduation_date' in education_data:
                    # Handle both field names for compatibility
                    education_entry.end_date = education_data.get('end_date') or education_data.get('graduation_date')
                if 'gpa' in education_data:
                    education_entry.gpa = education_data['gpa']
                if 'gpa_scale' in education_data:
                    education_entry.gpa_scale = education_data['gpa_scale']
                if 'location' in education_data:
                    education_entry.location = education_data['location']
                if 'relevant_coursework' in education_data:
                    coursework = education_data['relevant_coursework']
                    education_entry.relevant_coursework = coursework if isinstance(coursework, list) else [coursework] if coursework else []
                if 'academic_achievements' in education_data:
                    achievements = education_data['academic_achievements']
                    education_entry.academic_achievements = achievements if isinstance(achievements, list) else [achievements] if achievements else []
                if 'honors_awards' in education_data:
                    honors = education_data['honors_awards']
                    education_entry.honors = honors if isinstance(honors, list) else [honors] if honors else []
                
                session.commit()
                session.refresh(education_entry)
                
                # Force load all attributes before session closes to avoid DetachedInstanceError
                _ = education_entry.id
                _ = education_entry.institution_name
                _ = education_entry.degree_type
                _ = education_entry.field_of_study
                _ = education_entry.start_date
                _ = education_entry.end_date
                _ = education_entry.gpa
                _ = education_entry.gpa_scale
                _ = education_entry.location
                _ = education_entry.relevant_coursework
                _ = education_entry.academic_achievements
                _ = education_entry.honors
                _ = education_entry.created_at
                _ = education_entry.updated_at
                
                # Expunge from session to make it independent
                session.expunge(education_entry)
                
                self.logger.info(f"Updated education entry {education_id} for user {user_id}")
                return education_entry
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error updating education entry: {str(e)}")
            raise MasterDatasetError(f"Failed to update education entry: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error updating education entry: {str(e)}")
            raise MasterDatasetError(f"Unexpected error: {str(e)}")
    
    # Project Management
    
    async def add_project(self, user_id: str, project_data: Dict[str, Any]) -> Project:
        """Add new project to user's master dataset."""
        try:
            with db_service.get_session() as session:
                # Convert string to UUID if necessary
                if isinstance(user_id, str):
                    user_uuid = UUID(user_id)
                else:
                    user_uuid = user_id
                    
                user_profile = session.query(UserProfile).filter_by(
                    user_id=user_uuid
                ).first()
                
                if not user_profile:
                    raise MasterDatasetError(f"User profile not found: {user_id}")
                
                project = Project(
                    profile_id=user_profile.id,
                    project_name=project_data.get('project_name', ''),
                    project_type=project_data.get('project_type', ''),
                    project_description=project_data.get('project_description', ''),
                    start_date=project_data.get('start_date'),
                    end_date=project_data.get('end_date'),
                    technologies_used=project_data.get('technologies_used', ''),
                    project_url=project_data.get('project_url', ''),
                    repository_url=project_data.get('repository_url', ''),
                    role=project_data.get('role', ''),
                    team_size=project_data.get('team_size'),
                    key_achievements=project_data.get('key_achievements', ''),
                    metrics=project_data.get('metrics', '')
                )
                
                session.add(project)
                session.commit()
                session.refresh(project)
                
                # Force load all attributes before session closes to avoid DetachedInstanceError
                _ = project.id
                _ = project.project_name
                _ = project.project_type
                _ = project.project_description
                _ = project.start_date
                _ = project.end_date
                _ = project.technologies_used
                _ = project.project_url
                _ = project.repository_url
                _ = project.role
                _ = project.team_size
                _ = project.key_achievements
                _ = project.metrics
                _ = project.created_at
                _ = project.updated_at
                
                # Expunge from session to make it independent
                session.expunge(project)
                
                self.logger.info(f"Added project for user_id: {user_id}, project: {project_data.get('project_name')}")
                return project
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error adding project: {str(e)}")
            raise MasterDatasetError(f"Failed to add project: {str(e)}")
    
    async def get_projects(self, user_id: str) -> List[Project]:
        """Get all projects for a user, ordered by start date (most recent first)."""
        try:
            with db_service.get_session() as session:
                # Convert string to UUID if necessary
                if isinstance(user_id, str):
                    user_uuid = UUID(user_id)
                else:
                    user_uuid = user_id
                    
                user_profile = session.query(UserProfile).filter_by(
                    user_id=user_uuid
                ).first()
                
                if not user_profile:
                    return []
                
                projects = session.query(Project).filter_by(
                    profile_id=user_profile.id
                ).order_by(desc(Project.start_date)).all()
                
                return projects
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error retrieving projects: {str(e)}")
            raise MasterDatasetError(f"Failed to retrieve projects: {str(e)}")
    
    async def delete_project(self, user_id: str, project_id: str) -> bool:
        """Delete project."""
        try:
            with db_service.get_session() as session:
                # Convert string to UUID if necessary
                if isinstance(user_id, str):
                    user_uuid = UUID(user_id)
                else:
                    user_uuid = user_id
                    
                if isinstance(project_id, str):
                    proj_uuid = UUID(project_id)
                else:
                    proj_uuid = project_id
                    
                # Get user profile
                user_profile = session.query(UserProfile).filter_by(
                    user_id=user_uuid
                ).first()
                
                if not user_profile:
                    raise MasterDatasetError(f"User profile not found: {user_id}")
                
                # Get project and verify ownership
                project = session.query(Project).filter_by(
                    id=proj_uuid,
                    profile_id=user_profile.id
                ).first()
                
                if not project:
                    raise MasterDatasetError(f"Project not found or access denied: {project_id}")
                
                # Delete the project
                session.delete(project)
                session.commit()
                
                self.logger.info(f"Deleted project {project_id} for user {user_id}")
                return True
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error deleting project: {str(e)}")
            raise MasterDatasetError(f"Failed to delete project: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error deleting project: {str(e)}")
            raise MasterDatasetError(f"Unexpected error: {str(e)}")
    
    async def update_project(self, user_id: str, project_id: str, project_data: Dict[str, Any]) -> Optional[Project]:
        """Update project for a user."""
        try:
            with db_service.get_session() as session:
                # Convert string to UUID if necessary
                if isinstance(user_id, str):
                    user_uuid = UUID(user_id)
                else:
                    user_uuid = user_id
                    
                if isinstance(project_id, str):
                    proj_uuid = UUID(project_id)
                else:
                    proj_uuid = project_id
                    
                # Get user profile
                user_profile = session.query(UserProfile).filter_by(
                    user_id=user_uuid
                ).first()
                
                if not user_profile:
                    raise MasterDatasetError(f"User profile not found: {user_id}")
                
                # Get project and verify ownership
                project = session.query(Project).filter_by(
                    id=proj_uuid,
                    profile_id=user_profile.id
                ).first()
                
                if not project:
                    raise MasterDatasetError(f"Project not found or access denied: {project_id}")
                
                # Update project fields
                if 'project_name' in project_data:
                    project.project_name = project_data['project_name']
                if 'project_type' in project_data:
                    project.project_type = project_data['project_type']
                if 'project_description' in project_data:
                    project.project_description = project_data['project_description']
                if 'start_date' in project_data:
                    project.start_date = project_data['start_date']
                if 'end_date' in project_data:
                    project.end_date = project_data['end_date']
                if 'technologies_used' in project_data:
                    project.technologies_used = project_data['technologies_used']
                if 'project_url' in project_data:
                    project.project_url = project_data['project_url']
                if 'repository_url' in project_data:
                    project.repository_url = project_data['repository_url']
                if 'role' in project_data:
                    project.role = project_data['role']
                if 'team_size' in project_data:
                    project.team_size = project_data['team_size']
                if 'key_achievements' in project_data:
                    project.key_achievements = project_data['key_achievements']
                if 'metrics' in project_data:
                    project.metrics = project_data['metrics']
                
                session.commit()
                session.refresh(project)
                
                # Force load all attributes before session closes to avoid DetachedInstanceError
                _ = project.id
                _ = project.project_name
                _ = project.project_type
                _ = project.project_description
                _ = project.start_date
                _ = project.end_date
                _ = project.technologies_used
                _ = project.project_url
                _ = project.repository_url
                _ = project.role
                _ = project.team_size
                _ = project.key_achievements
                _ = project.metrics
                _ = project.created_at
                _ = project.updated_at
                
                # Expunge from session to make it independent
                session.expunge(project)
                
                self.logger.info(f"Updated project {project_id} for user {user_id}")
                return project
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error updating project: {str(e)}")
            raise MasterDatasetError(f"Failed to update project: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error updating project: {str(e)}")
            raise MasterDatasetError(f"Unexpected error: {str(e)}")
    
    # Master Dataset Statistics and Summary
    
    async def get_dataset_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive summary of user's master dataset.
        Used for dashboard and analytics.
        """
        try:
            with db_service.get_session() as session:
                # Convert string to UUID if necessary
                if isinstance(user_id, str):
                    user_uuid = UUID(user_id)
                else:
                    user_uuid = user_id
                    
                user_profile = session.query(UserProfile).filter_by(
                    user_id=user_uuid
                ).first()
                
                if not user_profile:
                    raise MasterDatasetError(f"User profile not found: {user_id}")
                
                # Count statistics
                work_experience_count = session.query(WorkExperience).filter_by(
                    profile_id=user_profile.id
                ).count()
                
                achievement_count = session.query(Achievement).filter_by(
                    profile_id=user_profile.id
                ).count()
                
                skill_count = session.query(Skill).filter_by(
                    profile_id=user_profile.id
                ).count()
                
                education_count = session.query(EducationEntry).filter_by(
                    profile_id=user_profile.id
                ).count()
                
                project_count = session.query(Project).filter_by(
                    profile_id=user_profile.id
                ).count()
                
                # Achievement category breakdown
                achievement_categories = session.query(
                    Achievement.achievement_category,
                    func.count(Achievement.id).label('count')
                ).filter_by(
                    profile_id=user_profile.id
                ).group_by(Achievement.achievement_category).all()
                
                # Top performing achievements
                top_achievements = session.query(Achievement).filter_by(
                    profile_id=user_profile.id
                ).order_by(
                    desc(Achievement.success_correlation),
                    desc(Achievement.impact_level)
                ).limit(5).all()
                
                summary = {
                    "user_profile": {
                        "user_id": user_id,
                        "full_name": user_profile.full_name,
                        "created_at": user_profile.created_at.isoformat(),
                        "updated_at": user_profile.updated_at.isoformat(),
                        "career_level": user_profile.career_level,
                        "target_industries": user_profile.target_industries
                    },
                    "dataset_statistics": {
                        "work_experiences": work_experience_count,
                        "achievements": achievement_count,
                        "skills": skill_count,
                        "education_entries": education_count,
                        "projects": project_count
                    },
                    "achievement_breakdown": {
                        category.achievement_category or "uncategorized": category.count 
                        for category in achievement_categories
                    },
                    "top_performing_achievements": [
                        {
                            "id": str(achievement.id),
                            "text": achievement.achievement_text[:100] + "..." if len(achievement.achievement_text) > 100 else achievement.achievement_text,
                            "impact_level": achievement.impact_level,
                            "success_correlation": achievement.success_correlation,
                            "selection_count": achievement.selection_count
                        }
                        for achievement in top_achievements
                    ],
                    "completion_status": {
                        "has_work_experience": work_experience_count > 0,
                        "has_achievements": achievement_count > 0,
                        "has_skills": skill_count > 0,
                        "has_education": education_count > 0,
                        "completion_percentage": min(100, (
                            (work_experience_count > 0) * 40 +
                            (achievement_count >= 3) * 30 +
                            (skill_count >= 5) * 20 +
                            (education_count > 0) * 10
                        ))
                    }
                }
                
                return summary
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error getting dataset summary: {str(e)}")
            raise MasterDatasetError(f"Failed to get dataset summary: {str(e)}")
    
    # Master Dataset Validation
    
    async def validate_dataset_completeness(self, user_id: str) -> Dict[str, Any]:
        """
        Validate master dataset completeness and quality.
        Used for quality control and user guidance.
        """
        try:
            summary = await self.get_dataset_summary(user_id)
            stats = summary["dataset_statistics"]
            
            validation_results = {
                "is_complete": True,
                "completeness_score": 0,
                "missing_elements": [],
                "recommendations": [],
                "quality_issues": []
            }
            
            # Check required elements
            if stats["work_experiences"] == 0:
                validation_results["is_complete"] = False
                validation_results["missing_elements"].append("work_experience")
                validation_results["recommendations"].append(
                    "Add at least one work experience to get started"
                )
            elif stats["work_experiences"] < 2:
                validation_results["recommendations"].append(
                    "Consider adding more work experiences for better content variety"
                )
            
            if stats["achievements"] < 3:
                validation_results["is_complete"] = False
                validation_results["missing_elements"].append("achievements")
                validation_results["recommendations"].append(
                    "Add at least 3 achievements to enable effective content selection"
                )
            elif stats["achievements"] < 8:
                validation_results["recommendations"].append(
                    "Add more achievements (target: 8+) for optimal resume customization"
                )
            
            if stats["skills"] < 5:
                validation_results["missing_elements"].append("skills")
                validation_results["recommendations"].append(
                    "Add at least 5 key skills to improve ATS matching"
                )
            
            if stats["education_entries"] == 0:
                validation_results["recommendations"].append(
                    "Consider adding education information if relevant to your target roles"
                )
            
            # Calculate completeness score
            validation_results["completeness_score"] = summary["completion_status"]["completion_percentage"]
            
            # Quality checks
            if validation_results["completeness_score"] >= 80:
                validation_results["is_complete"] = True
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Error validating dataset completeness: {str(e)}")
            raise MasterDatasetError(f"Failed to validate dataset: {str(e)}")


# Global service instance
master_dataset_service = MasterDatasetService()