"""
Master Dataset API routes for TailerAI v2.0.
Handles all master dataset CRUD operations and management.
Following project blueprint best practices for API design and error handling.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from app.services.master_dataset_service import master_dataset_service, MasterDatasetError
from app.api.dependencies.auth_deps import get_current_active_user
from app.models.database import User, UserProfile
from app.services.database_service import db_service

logger = logging.getLogger(__name__)

router = APIRouter()


# Helper function to get user profile
async def get_user_profile_for_user(current_user: User) -> UserProfile:
    """Get user profile for current user, creating it if it doesn't exist."""
    try:
        with db_service.get_session() as session:
            user_profile = session.query(UserProfile).filter_by(
                user_id=current_user.id
            ).first()
            
            if not user_profile:
                # Auto-create profile for users who don't have one (common with OAuth)
                logger.info(f"Creating missing profile for user: {current_user.email}")
                user_profile = UserProfile(
                    user_id=current_user.id,
                    full_name=current_user.email.split('@')[0],
                    email=current_user.email,
                    is_active=True
                )
                session.add(user_profile)
                session.commit()
                session.refresh(user_profile)
                logger.info(f"Auto-created profile for user: {current_user.email}")
            
            return user_profile
    except Exception as e:
        logger.error(f"Error retrieving/creating user profile: {str(e)}")
        # For new users, retry once more with fresh session
        try:
            with db_service.get_session() as session:
                user_profile = session.query(UserProfile).filter_by(
                    user_id=current_user.id
                ).first()
                
                if not user_profile:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User profile not found. Please contact support."
                    )
                
                return user_profile
        except Exception as retry_error:
            logger.error(f"Retry failed for user profile: {str(retry_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving user profile"
            )


# Request/Response Models

class UserProfileCreate(BaseModel):
    """Request model for creating user profile."""
    user_id: str = Field(..., min_length=1, max_length=255)
    full_name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    phone: Optional[str] = Field(None, max_length=50)
    linkedin_url: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=255)
    target_industries: List[str] = Field(default_factory=list)
    career_level: Optional[str] = Field(None, pattern=r'^(entry|mid|senior|executive)$')
    
    @validator('target_industries')
    def validate_industries(cls, v):
        valid_industries = [
            "Technology", "Finance", "Healthcare", "Consulting", "Marketing",
            "Education", "Government", "Non-profit", "Manufacturing", "Retail"
        ]
        for industry in v:
            if industry not in valid_industries:
                raise ValueError(f"Invalid industry: {industry}")
        return v


class UserProfileUpdate(BaseModel):
    """Request model for updating user profile."""
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    phone: Optional[str] = Field(None, max_length=50)
    linkedin_url: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=255)
    target_industries: Optional[List[str]] = None
    career_level: Optional[str] = Field(None, pattern=r'^(entry|mid|senior|executive)$')


class WorkExperienceCreate(BaseModel):
    """Request model for creating work experience."""
    company_name: str = Field(..., min_length=1, max_length=255)
    position_title: str = Field(..., min_length=1, max_length=255)
    employment_type: str = Field(default="full-time", pattern=r'^(full-time|part-time|internship|contract|freelance)$')
    start_date: datetime
    end_date: Optional[datetime] = None
    location: Optional[str] = Field(None, max_length=255)
    company_size: Optional[str] = Field(None, pattern=r'^(startup|small|medium|large|enterprise)$')
    industry: Optional[str] = Field(None, max_length=100)
    company_description: Optional[str] = Field(None, max_length=1000)
    role_summary: Optional[str] = Field(None, max_length=1000)
    team_size: Optional[int] = Field(None, ge=1, le=10000)
    reporting_structure: Optional[str] = Field(None, max_length=255)


class WorkExperienceUpdate(BaseModel):
    """Request model for updating work experience."""
    company_name: Optional[str] = Field(None, max_length=255)
    position_title: Optional[str] = Field(None, max_length=255)
    employment_type: Optional[str] = Field(None, pattern=r'^(full-time|part-time|internship|contract|freelance)$')
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    location: Optional[str] = Field(None, max_length=255)
    company_size: Optional[str] = Field(None, pattern=r'^(startup|small|medium|large|enterprise)$')
    industry: Optional[str] = Field(None, max_length=100)
    company_description: Optional[str] = Field(None, max_length=1000)
    role_summary: Optional[str] = Field(None, max_length=1000)
    team_size: Optional[int] = Field(None, ge=1, le=10000)
    reporting_structure: Optional[str] = Field(None, max_length=255)
    job_description: Optional[str] = Field(None, max_length=2000)
    department: Optional[str] = Field(None, max_length=255)
    is_current: Optional[bool] = None
    
    @validator('company_name', 'position_title', 'location', 'industry', 'company_description', 'role_summary', 'reporting_structure', 'job_description', 'department', pre=True)
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v
    
    @validator('team_size', pre=True)
    def empty_int_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v
    
    @validator('start_date', 'end_date', pre=True)
    def empty_datetime_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v


class AchievementCreate(BaseModel):
    """Request model for creating achievement."""
    achievement_text: str = Field(..., min_length=10, max_length=1000)
    achievement_category: str = Field(
        ..., 
        pattern=r'^(leadership|technical|financial|operational|strategic|customer|process|innovation)$'
    )
    impact_level: int = Field(..., ge=1, le=10)
    business_function: Optional[str] = Field(None, max_length=100)
    quantified_metrics: Dict[str, Any] = Field(default_factory=dict)
    keywords: List[str] = Field(default_factory=list)
    ats_keywords: List[str] = Field(default_factory=list)
    skills_demonstrated: List[str] = Field(default_factory=list)
    time_period: Optional[str] = Field(None, max_length=100)
    context_tags: List[str] = Field(default_factory=list)
    
    @validator('achievement_text')
    def sanitize_achievement_text(cls, v):
        # Basic text sanitization
        import re
        # Remove excessive whitespace
        v = re.sub(r'\s+', ' ', v.strip())
        # Remove potentially harmful characters
        v = re.sub(r'[<>\"\'&]', '', v)
        return v


class SkillCreate(BaseModel):
    """Request model for creating skill."""
    skill_name: str = Field(..., min_length=1, max_length=255)
    skill_category: str = Field(
        ..., 
        pattern=r'^(technical|soft|language|tool|certification)$'
    )
    proficiency_level: str = Field(
        default="intermediate",
        pattern=r'^(beginner|intermediate|advanced|expert)$'
    )
    years_experience: Optional[float] = Field(None, ge=0, le=50)
    certification_name: Optional[str] = Field(None, max_length=255)
    certification_date: Optional[datetime] = None
    related_keywords: List[str] = Field(default_factory=list)
    industry_relevance: List[str] = Field(default_factory=list)


class EducationCreate(BaseModel):
    """Request model for creating education entry."""
    institution_name: str = Field(..., min_length=1, max_length=255)
    degree_type: str = Field(..., min_length=1, max_length=100)
    field_of_study: str = Field(..., min_length=1, max_length=255)
    graduation_date: Optional[datetime] = None
    gpa: Optional[float] = Field(None, ge=0, le=10)
    gpa_scale: Optional[float] = Field(4.0, ge=1, le=10)
    location: Optional[str] = Field(None, max_length=255)
    relevant_coursework: Optional[str] = Field(None, max_length=1000)
    academic_achievements: Optional[str] = Field(None, max_length=1000)
    honors_awards: Optional[str] = Field(None, max_length=500)


class EducationEntryUpdate(BaseModel):
    """Request model for updating education entry."""
    institution_name: Optional[str] = Field(None, max_length=255)
    degree_type: Optional[str] = Field(None, max_length=100)
    field_of_study: Optional[str] = Field(None, max_length=255)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None  # For compatibility with graduation_date
    graduation_date: Optional[datetime] = None  # Alias for end_date
    gpa: Optional[float] = Field(None, ge=0, le=10)
    gpa_scale: Optional[float] = Field(None, ge=1, le=10)
    location: Optional[str] = Field(None, max_length=255)
    relevant_coursework: Optional[str] = Field(None, max_length=1000)
    academic_achievements: Optional[str] = Field(None, max_length=1000)
    honors_awards: Optional[str] = Field(None, max_length=500)
    
    @validator('institution_name', 'degree_type', 'field_of_study', 'location', 'relevant_coursework', 'academic_achievements', 'honors_awards', pre=True)
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v
    
    @validator('gpa', 'gpa_scale', pre=True)
    def empty_float_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v
    
    @validator('start_date', 'end_date', 'graduation_date', pre=True)
    def empty_datetime_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v


class ProjectCreate(BaseModel):
    """Request model for creating project."""
    project_name: str = Field(..., min_length=1, max_length=500)
    project_type: Optional[str] = Field(None, max_length=100)
    project_description: Optional[str] = Field(None, max_length=1000)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    technologies_used: Optional[str] = Field(None, max_length=500)
    project_url: Optional[str] = Field(None, max_length=500)
    repository_url: Optional[str] = Field(None, max_length=500)
    role: Optional[str] = Field(None, max_length=255)
    team_size: Optional[int] = Field(None, ge=1, le=100)
    key_achievements: Optional[str] = Field(None, max_length=1000)
    metrics: Optional[str] = Field(None, max_length=500)


class ProjectUpdate(BaseModel):
    """Request model for updating project."""
    project_name: Optional[str] = Field(None, max_length=500)
    project_type: Optional[str] = Field(None, max_length=100)
    project_description: Optional[str] = Field(None, max_length=1000)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    technologies_used: Optional[str] = Field(None, max_length=500)
    project_url: Optional[str] = Field(None, max_length=500)
    repository_url: Optional[str] = Field(None, max_length=500)
    role: Optional[str] = Field(None, max_length=255)
    team_size: Optional[int] = Field(None, ge=1, le=100)
    key_achievements: Optional[str] = Field(None, max_length=1000)
    metrics: Optional[str] = Field(None, max_length=500)
    
    @validator('project_name', 'project_type', 'project_description', 'technologies_used', 'project_url', 'repository_url', 'role', 'key_achievements', 'metrics', pre=True)
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v
    
    @validator('team_size', pre=True)
    def empty_int_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v
    
    @validator('start_date', 'end_date', pre=True)
    def empty_datetime_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v


class StandardResponse(BaseModel):
    """Standard API response model."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None


# API Routes

@router.get("/", response_model=StandardResponse)
async def get_master_dataset_summary(current_user: User = Depends(get_current_active_user)):
    """
    Get summary of master dataset for current user.
    Returns profile completeness and data overview.
    """
    try:
        current_user_profile = await get_user_profile_for_user(current_user)
        
        # Get dataset completeness summary
        with db_service.get_session() as session:
            from app.models.database import WorkExperience, Achievement, Skill, EducationEntry
            
            work_exp_count = session.query(WorkExperience).filter_by(profile_id=current_user_profile.id).count()
            achievements_count = session.query(Achievement).filter_by(profile_id=current_user_profile.id).count()
            skills_count = session.query(Skill).filter_by(profile_id=current_user_profile.id).count()
            education_count = session.query(EducationEntry).filter_by(profile_id=current_user_profile.id).count()
            
            return StandardResponse(
                success=True,
                message="Master dataset summary retrieved successfully",
                data={
                    "profile": {
                        "full_name": current_user_profile.full_name,
                        "email": current_user_profile.email,
                        "career_level": current_user_profile.career_level,
                        "target_industries": current_user_profile.target_industries or []
                    },
                    "counts": {
                        "work_experiences": work_exp_count,
                        "achievements": achievements_count,
                        "skills": skills_count,
                        "education": education_count
                    },
                    "completion_percentage": min(100, (work_exp_count + achievements_count + skills_count + education_count) * 10)
                }
            )
            
    except Exception as e:
        logger.error(f"Error getting master dataset summary: {str(e)}")
        return StandardResponse(
            success=False,
            message="Error retrieving master dataset summary",
            errors=[str(e)]
        )

@router.get("/complete", response_model=StandardResponse)
async def get_complete_master_dataset(current_user: User = Depends(get_current_active_user)):
    """
    Get complete master dataset for current user.
    Returns all work experiences, achievements, skills, education, and projects.
    """
    try:
        # Get all data from database in a single session
        with db_service.get_session() as session:
            from app.models.database import WorkExperience, Achievement, Skill, EducationEntry, Project
            
            # Get user profile first
            user_profile = session.query(UserProfile).filter_by(
                user_id=current_user.id
            ).first()
            
            if not user_profile:
                # Auto-create profile for users who don't have one (common with OAuth)
                logger.info(f"Creating missing profile for user: {current_user.email}")
                user_profile = UserProfile(
                    user_id=current_user.id,
                    full_name=current_user.email.split('@')[0],
                    email=current_user.email,
                    is_active=True
                )
                session.add(user_profile)
                session.commit()
                session.refresh(user_profile)
                logger.info(f"Auto-created profile for user: {current_user.email}")
            
            profile_id = user_profile.id
            
            # Get work experiences
            work_experiences = session.query(WorkExperience).filter_by(profile_id=profile_id).all()
            work_exp_data = []
            for exp in work_experiences:
                work_exp_data.append({
                    "id": str(exp.id),
                    "company_name": exp.company_name,
                    "position_title": exp.position_title,
                    "employment_type": exp.employment_type,
                    "start_date": exp.start_date.isoformat(),
                    "end_date": exp.end_date.isoformat() if exp.end_date else None,
                    "location": exp.location,
                    "company_size": exp.company_size,
                    "industry": exp.industry,
                    "company_description": exp.company_description,
                    "role_summary": exp.role_summary,
                    "job_description": exp.job_description,
                    "team_size": exp.team_size,
                    "reporting_structure": exp.reporting_structure,
                    "department": exp.department,
                    "duration_months": exp.duration_months,
                    "is_current": exp.is_current
                })
            
            # Get achievements
            achievements = session.query(Achievement).filter_by(profile_id=profile_id).all()
            achievement_data = []
            for achievement in achievements:
                achievement_data.append({
                    "id": str(achievement.id),
                    "work_experience_id": str(achievement.experience_id) if achievement.experience_id else None,
                    "achievement_text": achievement.achievement_text,
                    "achievement_category": achievement.achievement_category,
                    "impact_level": achievement.impact_level,
                    "business_function": achievement.business_function,
                    "quantified_metrics": achievement.quantified_metrics,
                    "keywords": achievement.keywords,
                    "ats_keywords": achievement.ats_keywords,
                    "skills_demonstrated": achievement.skills_demonstrated,
                    "time_period": achievement.time_period,
                    "context_tags": achievement.context_tags,
                    "selection_count": achievement.selection_count,
                    "success_correlation": achievement.success_correlation
                })
            
            # Get skills
            skills = session.query(Skill).filter_by(profile_id=profile_id).all()
            skill_data = []
            for skill in skills:
                skill_data.append({
                    "id": str(skill.id),
                    "skill_name": skill.skill_name,
                    "skill_category": skill.skill_category,
                    "proficiency_level": skill.proficiency_level,
                    "years_experience": skill.years_experience,
                    "certification_name": skill.certification_name,
                    "certification_date": skill.certification_date.isoformat() if skill.certification_date else None,
                    "related_keywords": skill.related_keywords,
                    "industry_relevance": skill.industry_relevance,
                    "keyword_match_count": skill.keyword_match_count
                })
            
            # Get education entries
            education = session.query(EducationEntry).filter_by(profile_id=profile_id).all()
            education_data = []
            for edu in education:
                education_data.append({
                    "id": str(edu.id),
                    "institution_name": edu.institution_name,
                    "degree_type": edu.degree_type,
                    "field_of_study": edu.field_of_study,
                    "graduation_date": edu.end_date.isoformat() if edu.end_date else None,
                    "gpa": edu.gpa,
                    "gpa_scale": edu.gpa_scale,
                    "location": edu.location,
                    "relevant_coursework": edu.relevant_coursework or [],
                    "academic_achievements": edu.academic_achievements or [],
                    "honors_awards": edu.honors or []
                })
            
            # Get projects
            projects = session.query(Project).filter_by(profile_id=profile_id).all()
            project_data = []
            for project in projects:
                project_data.append({
                    "id": str(project.id),
                    "project_name": project.project_name,
                    "project_type": project.project_type,
                    "project_description": project.project_description,
                    "start_date": project.start_date.isoformat() if project.start_date else None,
                    "end_date": project.end_date.isoformat() if project.end_date else None,
                    "technologies_used": project.technologies_used,
                    "project_url": project.project_url,
                    "repository_url": project.repository_url,
                    "role": project.role,
                    "team_size": project.team_size,
                    "key_achievements": project.key_achievements,
                    "technical_challenges": project.metrics
                })
            
            return StandardResponse(
                success=True,
                message="Complete master dataset retrieved successfully",
                data={
                    "profile": {
                        "id": str(user_profile.id),
                        "full_name": user_profile.full_name,
                        "email": user_profile.email,
                        "phone": user_profile.phone,
                        "linkedin_url": user_profile.linkedin_url,
                        "location": user_profile.location,
                        "career_level": user_profile.career_level,
                        "target_industries": user_profile.target_industries or []
                    },
                    "work_experiences": work_exp_data,
                    "achievements": achievement_data,
                    "skills": skill_data,
                    "education": education_data,
                    "projects": project_data,
                    "counts": {
                        "work_experiences": len(work_exp_data),
                        "achievements": len(achievement_data),
                        "skills": len(skill_data),
                        "education": len(education_data),
                        "projects": len(project_data)
                    }
                }
            )
            
    except Exception as e:
        logger.error(f"Error getting complete master dataset: {str(e)}")
        return StandardResponse(
            success=False,
            message="Error retrieving complete master dataset",
            errors=[str(e)]
        )

@router.get("/profile", response_model=StandardResponse)
async def get_user_profile(current_user: User = Depends(get_current_active_user)):
    """
    Get current user's profile.
    Profile is automatically created during user registration.
    """
    try:
        current_user_profile = await get_user_profile_for_user(current_user)
        
        return StandardResponse(
            success=True,
            message="User profile retrieved successfully",
            data={
                "profile_id": str(current_user_profile.id),
                "user_id": str(current_user_profile.user_id),
                "full_name": current_user_profile.full_name,
                "email": current_user_profile.email,
                "phone": current_user_profile.phone,
                "linkedin_url": current_user_profile.linkedin_url,
                "location": current_user_profile.location,
                "target_industries": current_user_profile.target_industries,
                "career_level": current_user_profile.career_level,
                "created_at": current_user_profile.created_at.isoformat(),
                "updated_at": current_user_profile.updated_at.isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/profile", response_model=StandardResponse)
async def update_user_profile(
    update_data: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update current user's profile with new information."""
    try:
        # Filter out None values
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        
        user_profile = await master_dataset_service.update_user_profile(
            user_id=str(current_user.id),
            update_data=update_dict
        )
        
        logger.info(f"Updated user profile: {current_user.id}")
        
        return StandardResponse(
            success=True,
            message="User profile updated successfully",
            data={
                "profile_id": str(user_profile.id),
                "user_id": str(user_profile.user_id),
                "updated_at": user_profile.updated_at.isoformat()
            }
        )
        
    except MasterDatasetError as e:
        logger.error(f"Failed to update user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Profile update failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error updating user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/experience", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def add_work_experience(
    experience_data: WorkExperienceCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Add new work experience to current user's master dataset."""
    try:
        work_experience = await master_dataset_service.add_work_experience(
            user_id=str(current_user.id),
            experience_data=experience_data.dict()
        )
        
        logger.info(f"Added work experience for user {current_user.id}: {experience_data.company_name}")
        
        return StandardResponse(
            success=True,
            message="Work experience added successfully",
            data={
                "experience_id": str(work_experience.id),
                "company_name": work_experience.company_name,
                "position_title": work_experience.position_title,
                "start_date": work_experience.start_date.isoformat(),
                "end_date": work_experience.end_date.isoformat() if work_experience.end_date else None,
                "is_current": work_experience.is_current
            }
        )
        
    except MasterDatasetError as e:
        logger.error(f"Failed to add work experience: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Work experience creation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error adding work experience: {str(e)}")
        
        # Check for unique constraint violation
        error_message = str(e)
        if "UNIQUE constraint failed" in error_message and "work_experiences" in error_message:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A work experience with the same company, position, and start date already exists. Please check your existing entries or modify the details."
            )
        elif "Data integrity violation" in error_message:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This work experience already exists in your profile. Please check your existing entries."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add work experience. Please try again."
            )


@router.delete("/experience/{experience_id}", response_model=StandardResponse)
async def delete_work_experience(
    experience_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete work experience and all associated achievements."""
    try:
        # Validate experience_id format
        try:
            UUID(experience_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid experience ID format"
            )
        
        success = await master_dataset_service.delete_work_experience(
            user_id=str(current_user.id),
            experience_id=experience_id
        )
        
        if success:
            logger.info(f"Successfully deleted work experience {experience_id} for user {current_user.id}")
            return StandardResponse(
                success=True,
                message="Work experience deleted successfully",
                data={
                    "experience_id": experience_id,
                    "deleted": True
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete work experience"
            )
        
    except MasterDatasetError as e:
        logger.error(f"Failed to delete work experience: {str(e)}")
        if "not found" in str(e).lower() or "access denied" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Work experience not found or access denied"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Work experience deletion failed: {str(e)}"
            )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting work experience: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete work experience. Please try again."
        )


@router.put("/experience/{experience_id}", response_model=StandardResponse)
async def update_work_experience(
    experience_id: str,
    experience_data: WorkExperienceUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update work experience for current user."""
    try:
        # Debug: log the received data
        logger.info(f"Received work experience update data: {experience_data.dict()}")
        logger.info(f"Experience ID: {experience_id}")
        
        # Validate experience_id format
        try:
            UUID(experience_id)
        except ValueError:
            logger.error(f"Invalid experience ID format: {experience_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid experience ID format"
            )
        
        updated_experience = await master_dataset_service.update_work_experience(
            user_id=str(current_user.id),
            experience_id=experience_id,
            experience_data=experience_data.dict(exclude_unset=True)
        )
        
        if updated_experience:
            logger.info(f"Updated work experience {experience_id} for user {current_user.id}")
            return StandardResponse(
                success=True,
                message="Work experience updated successfully",
                data={
                    "experience_id": str(updated_experience.id),
                    "company_name": updated_experience.company_name,
                    "position_title": updated_experience.position_title,
                    "department": updated_experience.department,
                    "employment_type": updated_experience.employment_type,
                    "start_date": updated_experience.start_date.isoformat() if updated_experience.start_date else None,
                    "end_date": updated_experience.end_date.isoformat() if updated_experience.end_date else None,
                    "location": updated_experience.location,
                    "job_description": updated_experience.job_description,
                    "is_current": updated_experience.is_current
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update work experience"
            )
        
    except MasterDatasetError as e:
        logger.error(f"Failed to update work experience: {str(e)}")
        if "not found" in str(e).lower() or "access denied" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Work experience not found or access denied"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Work experience update failed: {str(e)}"
            )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating work experience: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update work experience. Please try again."
        )


@router.get("/experience", response_model=StandardResponse)
async def get_work_experiences(
    current_user: User = Depends(get_current_active_user)
):
    """Get all work experiences for current user."""
    try:
        work_experiences = await master_dataset_service.get_work_experiences(str(current_user.id))
        
        experiences_data = []
        for exp in work_experiences:
            experiences_data.append({
                "experience_id": str(exp.id),
                "company_name": exp.company_name,
                "position_title": exp.position_title,
                "employment_type": exp.employment_type,
                "start_date": exp.start_date.isoformat(),
                "end_date": exp.end_date.isoformat() if exp.end_date else None,
                "location": exp.location,
                "company_size": exp.company_size,
                "industry": exp.industry,
                "role_summary": exp.role_summary,
                "duration_months": exp.duration_months,
                "is_current": exp.is_current
            })
        
        return StandardResponse(
            success=True,
            message=f"Retrieved {len(work_experiences)} work experiences",
            data={
                "work_experiences": experiences_data,
                "total_count": len(work_experiences)
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving work experiences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/experience/{experience_id}/achievement", 
             response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def add_achievement(
    experience_id: str, 
    achievement_data: AchievementCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Add new achievement to a work experience."""
    try:
        # Convert string to UUID
        exp_uuid = UUID(experience_id)
        
        achievement = await master_dataset_service.add_achievement(
            user_id=str(current_user.id),
            experience_id=exp_uuid,
            achievement_data=achievement_data.dict()
        )
        
        logger.info(f"Added achievement for user {current_user.id}, experience {experience_id}")
        
        return StandardResponse(
            success=True,
            message="Achievement added successfully",
            data={
                "achievement_id": str(achievement.id),
                "achievement_text": achievement.achievement_text,
                "achievement_category": achievement.achievement_category,
                "impact_level": achievement.impact_level,
                "business_function": achievement.business_function,
                "keywords": achievement.keywords,
                "skills_demonstrated": achievement.skills_demonstrated
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid experience_id format: {experience_id}"
        )
    except MasterDatasetError as e:
        logger.error(f"Failed to add achievement: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Achievement creation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error adding achievement: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/achievements", response_model=StandardResponse)
async def get_achievements(
    current_user: User = Depends(get_current_active_user),
    experience_id: Optional[str] = Query(None, description="Filter by experience ID"),
    category: Optional[str] = Query(None, description="Filter by achievement category"),
    min_impact_level: Optional[int] = Query(None, ge=1, le=10, description="Minimum impact level")
):
    """Get achievements with optional filtering for current user."""
    try:
        # Convert experience_id to UUID if provided
        exp_uuid = UUID(experience_id) if experience_id else None
        
        achievements = await master_dataset_service.get_achievements(
            user_id=str(current_user.id),
            experience_id=exp_uuid,
            category=category,
            min_impact_level=min_impact_level
        )
        
        achievements_data = []
        for achievement in achievements:
            achievements_data.append({
                "achievement_id": str(achievement.id),
                "experience_id": str(achievement.experience_id),
                "achievement_text": achievement.achievement_text,
                "achievement_category": achievement.achievement_category,
                "impact_level": achievement.impact_level,
                "business_function": achievement.business_function,
                "quantified_metrics": achievement.quantified_metrics,
                "keywords": achievement.keywords,
                "ats_keywords": achievement.ats_keywords,
                "skills_demonstrated": achievement.skills_demonstrated,
                "time_period": achievement.time_period,
                "context_tags": achievement.context_tags,
                "selection_count": achievement.selection_count,
                "success_correlation": achievement.success_correlation
            })
        
        return StandardResponse(
            success=True,
            message=f"Retrieved {len(achievements)} achievements",
            data={
                "achievements": achievements_data,
                "total_count": len(achievements),
                "filters_applied": {
                    "experience_id": experience_id,
                    "category": category,
                    "min_impact_level": min_impact_level
                }
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid experience_id format: {experience_id}"
        )
    except Exception as e:
        logger.error(f"Error retrieving achievements: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/skill", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def add_skill(
    skill_data: SkillCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Add new skill to current user's master dataset."""
    try:
        skill = await master_dataset_service.add_skill(
            user_id=str(current_user.id),
            skill_data=skill_data.dict()
        )
        
        logger.info(f"Added skill for user {current_user.id}: {skill_data.skill_name}")
        
        return StandardResponse(
            success=True,
            message="Skill added successfully",
            data={
                "skill_id": str(skill.id),
                "skill_name": skill.skill_name,
                "skill_category": skill.skill_category,
                "proficiency_level": skill.proficiency_level,
                "years_experience": skill.years_experience
            }
        )
        
    except MasterDatasetError as e:
        logger.error(f"Failed to add skill: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Skill creation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error adding skill: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/skills", response_model=StandardResponse)
async def get_skills(
    current_user: User = Depends(get_current_active_user),
    category: Optional[str] = Query(None, description="Filter by skill category")
):
    """Get all skills for current user, optionally filtered by category."""
    try:
        skills = await master_dataset_service.get_skills(
            user_id=str(current_user.id),
            category=category
        )
        
        skills_data = []
        for skill in skills:
            skills_data.append({
                "skill_id": str(skill.id),
                "skill_name": skill.skill_name,
                "skill_category": skill.skill_category,
                "proficiency_level": skill.proficiency_level,
                "years_experience": skill.years_experience,
                "certification_name": skill.certification_name,
                "certification_date": skill.certification_date.isoformat() if skill.certification_date else None,
                "related_keywords": skill.related_keywords,
                "industry_relevance": skill.industry_relevance,
                "keyword_match_count": skill.keyword_match_count
            })
        
        return StandardResponse(
            success=True,
            message=f"Retrieved {len(skills)} skills",
            data={
                "skills": skills_data,
                "total_count": len(skills),
                "category_filter": category
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving skills: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/summary", response_model=StandardResponse)
async def get_dataset_summary(
    current_user: User = Depends(get_current_active_user)
):
    """Get comprehensive summary of current user's master dataset."""
    try:
        summary = await master_dataset_service.get_dataset_summary(str(current_user.id))
        
        return StandardResponse(
            success=True,
            message="Dataset summary retrieved successfully",
            data=summary
        )
        
    except MasterDatasetError as e:
        logger.error(f"Failed to get dataset summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Summary generation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error retrieving dataset summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Education endpoints

@router.post("/education", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def add_education_entry(
    education_data: EducationCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Add new education entry to current user's master dataset."""
    try:
        education_entry = await master_dataset_service.add_education_entry(
            user_id=str(current_user.id),
            education_data=education_data.dict()
        )
        
        logger.info(f"Added education entry for user {current_user.id}: {education_data.institution_name}")
        
        return StandardResponse(
            success=True,
            message="Education entry added successfully",
            data={
                "education_id": str(education_entry.id),
                "institution_name": education_entry.institution_name,
                "degree_type": education_entry.degree_type,
                "field_of_study": education_entry.field_of_study,
                "graduation_date": education_entry.end_date.isoformat() if education_entry.end_date else None
            }
        )
        
    except MasterDatasetError as e:
        logger.error(f"Failed to add education entry: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Education entry creation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error adding education entry: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add education entry. Please try again."
        )


@router.get("/education", response_model=StandardResponse)
async def get_education_entries(
    current_user: User = Depends(get_current_active_user)
):
    """Get all education entries for current user."""
    try:
        education_entries = await master_dataset_service.get_education_entries(str(current_user.id))
        
        education_data = []
        for edu in education_entries:
            education_data.append({
                "education_id": str(edu.id),
                "institution_name": edu.institution_name,
                "degree_type": edu.degree_type,
                "field_of_study": edu.field_of_study,
                "graduation_date": edu.end_date.isoformat() if edu.end_date else None,
                "gpa": edu.gpa,
                "gpa_scale": edu.gpa_scale,
                "location": edu.location,
                "relevant_coursework": edu.relevant_coursework or [],
                "academic_achievements": edu.academic_achievements or [],
                "honors_awards": edu.honors or []
            })
        
        return StandardResponse(
            success=True,
            message=f"Retrieved {len(education_entries)} education entries",
            data={
                "education_entries": education_data,
                "total_count": len(education_entries)
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving education entries: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete("/education/{education_id}", response_model=StandardResponse)
async def delete_education_entry(
    education_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete education entry for current user."""
    try:
        success = await master_dataset_service.delete_education_entry(
            user_id=str(current_user.id),
            education_id=education_id
        )
        
        if success:
            logger.info(f"Deleted education entry {education_id} for user {current_user.id}")
            return StandardResponse(
                success=True,
                message="Education entry deleted successfully",
                data={"education_id": education_id}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete education entry"
            )
        
    except MasterDatasetError as e:
        logger.error(f"Failed to delete education entry: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Education entry deletion failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting education entry: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete education entry. Please try again."
        )


@router.put("/education/{education_id}", response_model=StandardResponse)
async def update_education_entry(
    education_id: str,
    education_data: EducationEntryUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update education entry for current user."""
    try:
        # Debug: log the received data
        logger.info(f"Received education update data: {education_data.dict()}")
        
        updated_education = await master_dataset_service.update_education_entry(
            user_id=str(current_user.id),
            education_id=education_id,
            education_data=education_data.dict(exclude_unset=True)
        )
        
        if updated_education:
            logger.info(f"Updated education entry {education_id} for user {current_user.id}")
            return StandardResponse(
                success=True,
                message="Education entry updated successfully",
                data={
                    "education_id": str(updated_education.id),
                    "institution_name": updated_education.institution_name,
                    "degree_type": updated_education.degree_type,
                    "field_of_study": updated_education.field_of_study,
                    "start_date": updated_education.start_date.isoformat() if updated_education.start_date else None,
                    "end_date": updated_education.end_date.isoformat() if updated_education.end_date else None,
                    "gpa": updated_education.gpa,
                    "gpa_scale": updated_education.gpa_scale,
                    "location": updated_education.location,
                    "relevant_coursework": updated_education.relevant_coursework or [],
                    "academic_achievements": updated_education.academic_achievements or [],
                    "honors_awards": updated_education.honors or []
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update education entry"
            )
        
    except MasterDatasetError as e:
        logger.error(f"Failed to update education entry: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Education entry update failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error updating education entry: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update education entry. Please try again."
        )


# Project endpoints

@router.post("/project", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def add_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Add new project to current user's master dataset."""
    try:
        project = await master_dataset_service.add_project(
            user_id=str(current_user.id),
            project_data=project_data.dict()
        )
        
        logger.info(f"Added project for user {current_user.id}: {project_data.project_name}")
        
        return StandardResponse(
            success=True,
            message="Project added successfully",
            data={
                "project_id": str(project.id),
                "project_name": project.project_name,
                "project_type": project.project_type,
                "start_date": project.start_date.isoformat() if project.start_date else None,
                "end_date": project.end_date.isoformat() if project.end_date else None
            }
        )
        
    except MasterDatasetError as e:
        logger.error(f"Failed to add project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project creation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error adding project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add project. Please try again."
        )


@router.get("/projects", response_model=StandardResponse)
async def get_projects(
    current_user: User = Depends(get_current_active_user)
):
    """Get all projects for current user."""
    try:
        projects = await master_dataset_service.get_projects(str(current_user.id))
        
        project_data = []
        for project in projects:
            project_data.append({
                "project_id": str(project.id),
                "project_name": project.project_name,
                "project_type": project.project_type,
                "project_description": project.project_description,
                "start_date": project.start_date.isoformat() if project.start_date else None,
                "end_date": project.end_date.isoformat() if project.end_date else None,
                "technologies_used": project.technologies_used,
                "project_url": project.project_url,
                "repository_url": project.repository_url,
                "role": project.role,
                "team_size": project.team_size,
                "key_achievements": project.key_achievements,
                "metrics": project.metrics
            })
        
        return StandardResponse(
            success=True,
            message=f"Retrieved {len(projects)} projects",
            data={
                "projects": project_data,
                "total_count": len(projects)
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving projects: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete("/project/{project_id}", response_model=StandardResponse)
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete project for current user."""
    try:
        success = await master_dataset_service.delete_project(
            user_id=str(current_user.id),
            project_id=project_id
        )
        
        if success:
            logger.info(f"Deleted project {project_id} for user {current_user.id}")
            return StandardResponse(
                success=True,
                message="Project deleted successfully",
                data={"project_id": project_id}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete project"
            )
        
    except MasterDatasetError as e:
        logger.error(f"Failed to delete project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project deletion failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete project. Please try again."
        )


@router.put("/project/{project_id}", response_model=StandardResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update project for current user."""
    try:
        updated_project = await master_dataset_service.update_project(
            user_id=str(current_user.id),
            project_id=project_id,
            project_data=project_data.dict(exclude_unset=True)
        )
        
        if updated_project:
            logger.info(f"Updated project {project_id} for user {current_user.id}")
            return StandardResponse(
                success=True,
                message="Project updated successfully",
                data={
                    "project_id": str(updated_project.id),
                    "project_name": updated_project.project_name,
                    "project_type": updated_project.project_type,
                    "project_description": updated_project.project_description,
                    "start_date": updated_project.start_date.isoformat() if updated_project.start_date else None,
                    "end_date": updated_project.end_date.isoformat() if updated_project.end_date else None,
                    "technologies_used": updated_project.technologies_used,
                    "project_url": updated_project.project_url,
                    "repository_url": updated_project.repository_url,
                    "role": updated_project.role,
                    "team_size": updated_project.team_size,
                    "key_achievements": updated_project.key_achievements,
                    "metrics": updated_project.metrics
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update project"
            )
        
    except MasterDatasetError as e:
        logger.error(f"Failed to update project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project update failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error updating project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project. Please try again."
        )


@router.get("/validation", response_model=StandardResponse)
async def validate_dataset_completeness(
    current_user: User = Depends(get_current_active_user)
):
    """Validate current user's master dataset completeness and provide recommendations."""
    try:
        validation_results = await master_dataset_service.validate_dataset_completeness(str(current_user.id))
        
        return StandardResponse(
            success=True,
            message="Dataset validation completed",
            data=validation_results
        )
        
    except MasterDatasetError as e:
        logger.error(f"Failed to validate dataset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error validating dataset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )