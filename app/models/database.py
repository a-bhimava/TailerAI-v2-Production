"""
SQLAlchemy database models for TailerAI v2.0 Master Dataset Architecture.
Following project blueprint best practices for modular, secure database design.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Column, String, DateTime, Integer, Text, Boolean, Float, JSON, 
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from sqlalchemy.types import TypeDecorator, CHAR, String as SQLString
from sqlalchemy.dialects import postgresql, sqlite


# Custom UUID type that works with both PostgreSQL and SQLite
class GUID(TypeDecorator):
    """
    Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            return value


# Custom JSON type for SQLite compatibility
class JSONType(TypeDecorator):
    """
    JSON type that works with both PostgreSQL and SQLite.
    """
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSON())
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        else:
            import json
            return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        else:
            import json
            return json.loads(value)


# Custom ARRAY type for SQLite compatibility
class ArrayType(TypeDecorator):
    """
    ARRAY type that works with both PostgreSQL and SQLite.
    """
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(ARRAY(Text))
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        else:
            import json
            return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        else:
            import json
            return json.loads(value) if value else []

# Create the declarative base
Base = declarative_base()


class User(Base):
    """
    User authentication model.
    Handles authentication, authorization, and account management.
    """
    __tablename__ = "users"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Account status
    is_active = Column(Boolean, default=False)  # Requires email verification
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    
    # Account security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    last_login = Column(DateTime(timezone=True))
    
    # Email verification
    email_verification_token = Column(String(255))
    email_verification_expires = Column(DateTime(timezone=True))
    email_verified_at = Column(DateTime(timezone=True))
    
    # Password reset
    password_reset_token = Column(String(255))
    password_reset_expires = Column(DateTime(timezone=True))
    password_changed_at = Column(DateTime(timezone=True))
    
    # OAuth integration
    google_id = Column(String(255), nullable=True, index=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    @property
    def is_locked(self) -> bool:
        """Check if account is locked due to failed login attempts."""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    @property
    def can_login(self) -> bool:
        """Check if user can login (active, verified, not locked)."""
        return self.is_active and self.is_verified and not self.is_locked
    
    @validates('email')
    def validate_email(self, key, email):
        """Email validation."""
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValueError("Invalid email format")
        return email.lower()
    
    @validates('username')
    def validate_username(self, key, username):
        """Username validation."""
        import re
        if not re.match(r'^[a-zA-Z0-9_-]{3,30}$', username):
            raise ValueError("Username must be 3-30 characters, alphanumeric, underscore, or hyphen only")
        return username.lower()


class UserProfile(Base):
    """
    Main user profile containing master dataset.
    Follows PRD-002: Master Dataset Database Architecture.
    """
    __tablename__ = "user_profiles"
    
    # Primary identification
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), unique=True, nullable=False, index=True)
    
    # Basic profile information
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50))
    linkedin_url = Column(String(500))
    location = Column(String(255))
    
    # Career preferences and targeting
    target_industries = Column(ArrayType)  # ["Technology", "Finance"]
    career_level = Column(String(50))  # "senior", "mid", "entry"
    job_search_status = Column(String(50), default="active")  # "active", "passive", "not_searching"
    
    # Account metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    
    # Privacy and preferences
    privacy_settings = Column(JSONType, default=dict)
    notification_preferences = Column(JSONType, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="profile")
    work_experiences = relationship("WorkExperience", back_populates="profile", cascade="all, delete-orphan")
    achievements = relationship("Achievement", back_populates="profile", cascade="all, delete-orphan")
    education_entries = relationship("EducationEntry", back_populates="profile", cascade="all, delete-orphan")
    skills = relationship("Skill", back_populates="profile", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="profile", cascade="all, delete-orphan")
    ats_optimizations = relationship("ATSOptimization", back_populates="profile", cascade="all, delete-orphan")
    content_enhancements = relationship("ContentEnhancement", back_populates="profile", cascade="all, delete-orphan")
    quality_assessments = relationship("QualityAssessment", back_populates="profile", cascade="all, delete-orphan")
    
    # PRD-011: Export & Application Management relationships
    job_applications = relationship("JobApplication", back_populates="profile", cascade="all, delete-orphan")
    export_history = relationship("ExportHistory", back_populates="profile", cascade="all, delete-orphan")
    export_templates = relationship("ExportTemplate", back_populates="profile", cascade="all, delete-orphan")
    
    @validates('email')
    def validate_email(self, key, email):
        """Basic email validation following security best practices."""
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValueError("Invalid email format")
        return email.lower()
    
    @validates('career_level')
    def validate_career_level(self, key, career_level):
        """Validate career level options."""
        valid_levels = ["entry", "mid", "senior", "executive"]
        if career_level and career_level not in valid_levels:
            raise ValueError(f"Career level must be one of: {valid_levels}")
        return career_level


class WorkExperience(Base):
    """
    Individual work experience entries.
    Contains company and role information without specific achievements.
    """
    __tablename__ = "work_experiences"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    profile_id = Column(GUID(), ForeignKey("user_profiles.id"), nullable=False)
    
    # Company and role details
    company_name = Column(String(255), nullable=False)
    position_title = Column(String(255), nullable=False)
    employment_type = Column(String(50))  # "full-time", "internship", "contract", "freelance"
    
    # Duration and location
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)  # NULL for current position
    location = Column(String(255))
    
    # Company context
    company_size = Column(String(50))  # "startup", "small", "medium", "large", "enterprise"
    industry = Column(String(100))
    company_description = Column(Text)
    
    # Role context
    role_summary = Column(Text)  # Brief description of role
    job_description = Column(Text)  # Detailed job description and responsibilities
    team_size = Column(Integer)
    reporting_structure = Column(String(255))
    department = Column(String(255))  # Department/division within company
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile", back_populates="work_experiences")
    achievements = relationship("Achievement", back_populates="experience", cascade="all, delete-orphan")
    
    @property
    def duration_months(self) -> Optional[int]:
        """Calculate duration in months."""
        if not self.start_date:
            return None
        end = self.end_date or datetime.utcnow()
        delta = end - self.start_date
        return int(delta.days / 30)
    
    @property
    def is_current(self) -> bool:
        """Check if this is current employment."""
        return self.end_date is None


class Achievement(Base):
    """
    Individual achievements within work experiences.
    Core of the master dataset - stores specific accomplishments with rich metadata.
    """
    __tablename__ = "achievements"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    profile_id = Column(GUID(), ForeignKey("user_profiles.id"), nullable=False)
    experience_id = Column(GUID(), ForeignKey("work_experiences.id"), nullable=False)
    
    # Core achievement data
    achievement_text = Column(Text, nullable=False)  # Original description
    achievement_category = Column(String(100))  # "leadership", "technical", "financial", "operational"
    impact_level = Column(Integer)  # 1-10 scale
    business_function = Column(String(100))  # "sales", "marketing", "engineering", "operations"
    
    # Quantified metrics (stored as JSON for flexibility)
    quantified_metrics = Column(JSONType, default=dict)  # {"revenue": 650000000, "percentage": 25, "count": 45}
    
    # Keywords and optimization
    keywords = Column(ArrayType)  # General keywords extracted from text
    ats_keywords = Column(ArrayType)  # Specific ATS-optimized keywords
    skills_demonstrated = Column(ArrayType)  # Skills shown in this achievement
    
    # Context and verification
    time_period = Column(String(100))  # "Q1 2024", "6 months", "annual"
    context_tags = Column(ArrayType)  # ["remote", "international", "startup", "team_lead"]
    verification_status = Column(String(50), default="user_provided")  # "user_provided", "verified", "disputed"
    
    # Performance tracking for content selection
    selection_count = Column(Integer, default=0)  # How often selected for resumes
    success_correlation = Column(Float, default=0.0)  # Performance in applications (0-1)
    last_selected = Column(DateTime(timezone=True))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile", back_populates="achievements")
    experience = relationship("WorkExperience", back_populates="achievements")
    enhancements = relationship("ContentEnhancement", back_populates="achievement", cascade="all, delete-orphan")
    
    @validates('impact_level')
    def validate_impact_level(self, key, impact_level):
        """Validate impact level is between 1-10."""
        if impact_level is not None and (impact_level < 1 or impact_level > 10):
            raise ValueError("Impact level must be between 1 and 10")
        return impact_level
    
    @validates('achievement_category')
    def validate_category(self, key, category):
        """Validate achievement category."""
        valid_categories = [
            "leadership", "technical", "financial", "operational", 
            "strategic", "customer", "process", "innovation"
        ]
        if category and category not in valid_categories:
            raise ValueError(f"Category must be one of: {valid_categories}")
        return category


class EducationEntry(Base):
    """
    Education and academic information.
    """
    __tablename__ = "education_entries"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    profile_id = Column(GUID(), ForeignKey("user_profiles.id"), nullable=False)
    
    # Institution details
    institution_name = Column(String(255), nullable=False)
    degree_type = Column(String(100))  # "Bachelor's", "Master's", "PhD", "Certificate"
    field_of_study = Column(String(255))
    
    # Duration and achievements
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    gpa = Column(Float)
    gpa_scale = Column(Float, default=4.0)
    
    # Additional details
    honors = Column(ArrayType)  # ["Summa Cum Laude", "Dean's List"]
    relevant_coursework = Column(ArrayType)
    thesis_title = Column(Text)
    academic_achievements = Column(ArrayType)
    
    # Location and context
    location = Column(String(255))
    institution_type = Column(String(50))  # "university", "college", "bootcamp", "online"
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile", back_populates="education_entries")


class Skill(Base):
    """
    Skills and competencies with proficiency levels.
    """
    __tablename__ = "skills"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    profile_id = Column(GUID(), ForeignKey("user_profiles.id"), nullable=False)
    
    # Skill details
    skill_name = Column(String(255), nullable=False)
    skill_category = Column(String(100))  # "technical", "soft", "language", "tool"
    proficiency_level = Column(String(50))  # "beginner", "intermediate", "advanced", "expert"
    years_experience = Column(Float)
    
    # Context and validation
    last_used = Column(DateTime)
    certification_name = Column(String(255))
    certification_date = Column(DateTime)
    
    # Keywords for matching
    related_keywords = Column(ArrayType)
    industry_relevance = Column(ArrayType)  # Industries where this skill is relevant
    
    # Performance tracking
    keyword_match_count = Column(Integer, default=0)  # How often matched in job descriptions
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile", back_populates="skills")
    
    @validates('proficiency_level')
    def validate_proficiency(self, key, proficiency):
        """Validate proficiency level."""
        valid_levels = ["beginner", "intermediate", "advanced", "expert"]
        if proficiency and proficiency not in valid_levels:
            raise ValueError(f"Proficiency must be one of: {valid_levels}")
        return proficiency


class Project(Base):
    """
    Projects and notable work outside of regular employment.
    """
    __tablename__ = "projects"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    profile_id = Column(GUID(), ForeignKey("user_profiles.id"), nullable=False)
    
    # Project details
    project_name = Column(String(500), nullable=False)
    project_description = Column(Text)
    role = Column(String(255))  # Role in the project
    
    # Duration and context
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    project_type = Column(String(100))  # "personal", "open_source", "freelance", "academic"
    
    # Technical details
    technologies_used = Column(ArrayType)
    project_url = Column(String(500))
    repository_url = Column(String(500))
    
    # Outcomes and impact
    key_achievements = Column(ArrayType)
    metrics = Column(JSONType, default=dict)  # Quantified results
    team_size = Column(Integer)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile", back_populates="projects")


class JobAnalysis(Base):
    """
    Stored job description analysis results for caching and reuse.
    """
    __tablename__ = "job_analyses"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # Job identification
    job_description_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA256 hash
    company_name = Column(String(255))
    position_title = Column(String(255))
    
    # Analysis results
    required_skills = Column(ArrayType)
    preferred_skills = Column(ArrayType)
    key_requirements = Column(ArrayType)
    
    # Classification
    industry = Column(String(100))
    seniority_level = Column(String(50))
    employment_type = Column(String(50))
    
    # Keywords and optimization
    important_keywords = Column(ArrayType)
    keyword_frequency = Column(JSONType, default=dict)
    ats_keywords = Column(ArrayType)
    
    # Metadata
    confidence_score = Column(Float)  # AI confidence in analysis
    analysis_model = Column(String(100))  # AI model used
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Performance tracking
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime(timezone=True))


class ContentSelection(Base):
    """
    Stores content selection results for resume generation.
    Tracks which achievements were selected for specific job applications.
    """
    __tablename__ = "content_selections"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    profile_id = Column(GUID(), ForeignKey("user_profiles.id"), nullable=False)
    job_analysis_id = Column(GUID(), ForeignKey("job_analyses.id"))
    
    # Selection metadata
    selection_algorithm = Column(String(100))  # Algorithm version used
    selection_criteria = Column(JSONType, default=dict)
    total_score = Column(Float)
    
    # Selected content
    selected_achievements = Column(ArrayType)  # Achievement IDs as JSON array
    achievement_scores = Column(JSONType, default=dict)  # Achievement ID -> score mapping
    
    # Optimization results
    one_page_compliant = Column(Boolean, default=False)
    estimated_word_count = Column(Integer)
    content_density_score = Column(Float)
    
    # AI-Enhanced Selection Fields (Phase 1 Gemini Integration)
    ai_reasoning = Column(JSONType, default=dict)  # Structured AI reasoning data
    ai_confidence_score = Column(Float)  # AI confidence in selection (0.0-1.0)
    selection_method = Column(String(50), default="algorithmic")  # "algorithmic", "ai_enhanced", "ai_primary"
    fallback_applied = Column(Boolean, default=False)  # Whether fallback was used
    gemini_processing_time = Column(Float)  # Time spent on AI processing
    
    # Performance tracking
    application_outcome = Column(String(50))  # "applied", "interview", "offer", "rejected"
    outcome_date = Column(DateTime)
    feedback_notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ATSOptimization(Base):
    """
    Stores ATS optimization results for resume content.
    Tracks keyword optimization and ATS compatibility analysis.
    """
    __tablename__ = "ats_optimizations"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    profile_id = Column(GUID(), ForeignKey("user_profiles.id"), nullable=False)
    job_analysis_id = Column(GUID(), ForeignKey("job_analyses.id"))
    content_selection_id = Column(GUID(), ForeignKey("content_selections.id"))
    
    # Optimization metadata
    optimization_algorithm = Column(String(100))  # Algorithm version used
    target_keywords = Column(ArrayType)
    target_density = Column(Float, default=0.03)  # Target keyword density (3%)
    
    # Keyword optimization results
    original_keyword_density = Column(Float)
    final_keyword_density = Column(Float)
    keyword_distribution_score = Column(Float)
    natural_language_score = Column(Float)
    keyword_stuffing_risk = Column(Float)
    
    # Detailed keyword metrics
    keyword_metrics = Column(JSONType, default=dict)  # Per-keyword analysis
    optimization_strategy = Column(JSONType, default=dict)  # Strategy used
    improvement_metrics = Column(JSONType, default=dict)  # Before/after comparison
    
    # ATS compatibility results
    ats_compatibility_score = Column(Float)
    ats_compatibility_level = Column(String(50))  # excellent, good, fair, poor, incompatible
    
    # ATS system results
    ats_system_results = Column(JSONType, default=dict)  # Per-system compatibility
    parsing_success_rate = Column(Float)  # Percentage of systems that parsed successfully
    
    # Issues and recommendations
    common_issues = Column(ArrayType)
    priority_fixes = Column(ArrayType)
    detailed_recommendations = Column(ArrayType)
    
    # Overall optimization results
    final_optimization_score = Column(Float)
    word_budget_used = Column(Integer)
    sections_modified = Column(ArrayType)
    
    # Performance tracking
    optimization_applied = Column(Boolean, default=False)
    application_outcome = Column(String(50))  # Track if optimization improved results
    user_rating = Column(Integer)  # User satisfaction (1-5)
    user_feedback = Column(Text)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile", back_populates="ats_optimizations")
    job_analysis = relationship("JobAnalysis")
    content_selection = relationship("ContentSelection")
    
    @validates('ats_compatibility_level')
    def validate_compatibility_level(self, key, level):
        """Validate ATS compatibility level."""
        valid_levels = ["excellent", "good", "fair", "poor", "incompatible"]
        if level and level not in valid_levels:
            raise ValueError(f"Compatibility level must be one of: {valid_levels}")
        return level
    
    @validates('user_rating')
    def validate_user_rating(self, key, rating):
        """Validate user rating."""
        if rating is not None and (rating < 1 or rating > 5):
            raise ValueError("User rating must be between 1 and 5")
        return rating


class ContentEnhancement(Base):
    """
    Stores content enhancement results for achievements and other text.
    Phase 3 implementation for AI-powered content improvement.
    """
    __tablename__ = "content_enhancements"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    achievement_id = Column(GUID(), ForeignKey("achievements.id"))
    profile_id = Column(GUID(), ForeignKey("user_profiles.id"))
    
    # Enhancement metadata
    enhancement_algorithm = Column(String(100))  # Algorithm version used
    enhancement_type = Column(String(50))  # "achievement_text", "summary_statement", etc.
    enhancement_level = Column(String(20))  # "minimal", "moderate", "aggressive"
    
    # Content data
    original_content = Column(Text, nullable=False)
    enhanced_content = Column(Text, nullable=False)
    
    # Enhancement analysis
    changes_made = Column(JSONType, default=list)  # List of changes with details
    overall_improvement_score = Column(Float)  # 0.0-1.0
    authenticity_level = Column(String(20))  # "verified", "likely", "questionable", "flagged"
    
    # Keywords and optimization
    keywords_integrated = Column(ArrayType, default=list)
    action_verbs_improved = Column(ArrayType, default=list)
    quantification_enhanced = Column(Boolean, default=False)
    
    # AI metadata (Phase 3 Gemini Integration)
    ai_reasoning = Column(Text)  # AI explanation of enhancements
    ai_confidence_score = Column(Float)  # AI confidence in enhancement (0.0-1.0)
    processing_time = Column(Float)  # Time spent on enhancement
    fallback_applied = Column(Boolean, default=False)  # Whether fallback was used
    
    # User interaction
    user_approved = Column(Boolean, default=False)  # User approval for enhancement
    user_feedback = Column(Text)  # User comments on enhancement
    user_rating = Column(Integer)  # User satisfaction (1-5)
    applied_to_resume = Column(Boolean, default=False)  # Whether enhancement was used
    
    # Performance tracking
    application_outcome = Column(String(50))  # Track if enhancement improved results
    outcome_date = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    achievement = relationship("Achievement", back_populates="enhancements")
    profile = relationship("UserProfile", back_populates="content_enhancements")
    
    @validates('enhancement_level')
    def validate_enhancement_level(self, key, level):
        """Validate enhancement level."""
        valid_levels = ["minimal", "moderate", "aggressive"]
        if level and level not in valid_levels:
            raise ValueError(f"Enhancement level must be one of: {valid_levels}")
        return level
    
    @validates('authenticity_level')
    def validate_authenticity_level(self, key, level):
        """Validate authenticity level."""
        valid_levels = ["verified", "likely", "questionable", "flagged"]
        if level and level not in valid_levels:
            raise ValueError(f"Authenticity level must be one of: {valid_levels}")
        return level
    
    @validates('user_rating')
    def validate_user_rating(self, key, rating):
        """Validate user rating."""
        if rating is not None and (rating < 1 or rating > 5):
            raise ValueError("User rating must be between 1 and 5")
        return rating


class KeywordAnalysisCache(Base):
    """
    Caches keyword analysis results for resume content.
    Optimizes performance by avoiding re-analysis of similar content.
    """
    __tablename__ = "keyword_analysis_cache"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # Cache key (hash of content + keywords)
    content_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA256 hash
    keywords_hash = Column(String(64), nullable=False, index=True)  # SHA256 of sorted keywords
    
    # Cached analysis results
    total_word_count = Column(Integer)
    overall_keyword_density = Column(Float)
    distribution_score = Column(Float)
    natural_language_score = Column(Float)
    keyword_stuffing_risk = Column(Float)
    
    # Detailed keyword metrics
    keyword_metrics = Column(JSONType, default=dict)  # Full KeywordMetrics for each keyword
    
    # Cache metadata
    analysis_version = Column(String(50))  # Algorithm version for invalidation
    hit_count = Column(Integer, default=0)  # Usage tracking
    
    # Expiration and cleanup
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))  # For TTL-based expiration
    
    def update_usage(self):
        """Update usage statistics."""
        self.hit_count += 1
        self.last_used = datetime.utcnow()


# Database indexes for performance optimization
# Following blueprint best practices for query optimization

# User authentication lookups
Index('idx_users_email', User.email)
Index('idx_users_username', User.username)
Index('idx_users_verification_token', User.email_verification_token)
Index('idx_users_reset_token', User.password_reset_token)

# User profile lookups
Index('idx_user_profiles_user_id', UserProfile.user_id)
Index('idx_user_profiles_email', UserProfile.email)

# Achievement queries (most frequent)
Index('idx_achievements_profile_id', Achievement.profile_id)
Index('idx_achievements_category', Achievement.achievement_category)
Index('idx_achievements_impact_level', Achievement.impact_level)
Index('idx_achievements_selection_performance', Achievement.selection_count, Achievement.success_correlation)

# Work experience lookups
Index('idx_work_exp_profile_dates', WorkExperience.profile_id, WorkExperience.start_date, WorkExperience.end_date)

# Compound indexes for common query patterns
Index('idx_achievements_profile_experience', Achievement.profile_id, Achievement.experience_id)
Index('idx_skills_profile_category', Skill.profile_id, Skill.skill_category)

# Job analysis caching
Index('idx_job_analysis_hash', JobAnalysis.job_description_hash)
Index('idx_job_analysis_usage', JobAnalysis.usage_count, JobAnalysis.last_used)

# Content selection tracking
Index('idx_content_selection_profile', ContentSelection.profile_id, ContentSelection.created_at)

# ATS optimization indexes
Index('idx_ats_optimization_profile', ATSOptimization.profile_id, ATSOptimization.created_at)
Index('idx_ats_optimization_job_analysis', ATSOptimization.job_analysis_id)
Index('idx_ats_optimization_content_selection', ATSOptimization.content_selection_id)
Index('idx_ats_optimization_score', ATSOptimization.final_optimization_score, ATSOptimization.ats_compatibility_score)
Index('idx_ats_optimization_performance', ATSOptimization.optimization_applied, ATSOptimization.application_outcome)

# Content enhancement indexes
Index('idx_content_enhancement_profile', ContentEnhancement.profile_id, ContentEnhancement.created_at)
Index('idx_content_enhancement_achievement', ContentEnhancement.achievement_id)
Index('idx_content_enhancement_type', ContentEnhancement.enhancement_type, ContentEnhancement.enhancement_level)
Index('idx_content_enhancement_approval', ContentEnhancement.user_approved, ContentEnhancement.applied_to_resume)
Index('idx_content_enhancement_performance', ContentEnhancement.overall_improvement_score, ContentEnhancement.authenticity_level)

# Keyword analysis cache indexes
Index('idx_keyword_cache_content_hash', KeywordAnalysisCache.content_hash)
Index('idx_keyword_cache_keywords_hash', KeywordAnalysisCache.keywords_hash)
Index('idx_keyword_cache_usage', KeywordAnalysisCache.hit_count, KeywordAnalysisCache.last_used)
Index('idx_keyword_cache_expiration', KeywordAnalysisCache.expires_at)


# Additional constraints for data integrity
# Unique constraint to prevent duplicate work experiences
UniqueConstraint(
    WorkExperience.profile_id, 
    WorkExperience.company_name, 
    WorkExperience.position_title, 
    WorkExperience.start_date,
    name='unique_work_experience'
)

# Unique constraint for skills per profile
UniqueConstraint(
    Skill.profile_id, 
    Skill.skill_name,
    name='unique_skill_per_profile'
)


class QualityAssessment(Base):
    """
    Personal quality assessments for resume content.
    Tracks quality scores and improvement progress over time.
    """
    __tablename__ = "quality_assessments"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    profile_id = Column(GUID(), ForeignKey("user_profiles.id"), nullable=False)
    
    # Overall quality metrics
    overall_score = Column(Float, nullable=False)  # 0-100
    
    # Category-specific scores
    content_score = Column(Float, default=0.0)  # Content quality score
    grammar_score = Column(Float, default=0.0)  # Grammar and language score
    ats_score = Column(Float, default=0.0)  # ATS compatibility score
    formatting_score = Column(Float, default=0.0)  # Formatting consistency score
    keyword_score = Column(Float, default=0.0)  # Keyword optimization score
    professional_score = Column(Float, default=0.0)  # Professional standards score
    readability_score = Column(Float, default=0.0)  # Readability score
    completeness_score = Column(Float, default=0.0)  # Content completeness score
    
    # Issue tracking
    total_issues = Column(Integer, default=0)
    critical_issues = Column(Integer, default=0)
    
    # Improvement guidance
    improvement_priority = Column(ArrayType)  # List of priority areas
    next_steps = Column(ArrayType)  # List of recommended next steps
    estimated_improvement_time = Column(String(50))  # "1-2 hours", "1-2 days", etc.
    
    # Assessment context
    target_role = Column(String(255))  # Role being optimized for
    target_industry = Column(String(255))  # Industry context
    assessment_type = Column(String(50), default="comprehensive")  # Type of assessment
    
    # Progress tracking
    previous_assessment_id = Column(GUID(), ForeignKey("quality_assessments.id"))
    improvement_since_last = Column(Float)  # Score improvement since last assessment
    
    # Metadata
    assessed_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile", back_populates="quality_assessments")
    previous_assessment = relationship("QualityAssessment", remote_side=[id])


class APIUsage(Base):
    """
    Tracks API usage for monitoring and rate limiting.
    """
    __tablename__ = "api_usage"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # API call details
    service = Column(String(100), nullable=False)  # "gemini", "openai", etc.
    endpoint = Column(String(255), nullable=False)
    response_time_ms = Column(Integer)
    success = Column(Boolean, nullable=False)
    error_message = Column(Text)
    
    # Metadata
    request_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_api_usage_service_timestamp', 'service', 'request_timestamp'),
        Index('idx_api_usage_success', 'success'),
    )


# PRD-011: Export & Personal Application Management Models

class JobApplication(Base):
    """
    Personal job application tracking for individual users.
    Tracks application status, progress, and outcomes for personal use.
    """
    __tablename__ = "job_applications"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    profile_id = Column(GUID(), ForeignKey("user_profiles.id"), nullable=False)
    
    # Job details
    company_name = Column(String(255), nullable=False)
    position_title = Column(String(255), nullable=False)
    job_board_url = Column(String(1000))  # Original job posting URL
    job_board_source = Column(String(100))  # "linkedin", "indeed", "company_website"
    
    # Application details
    application_method = Column(String(100))  # "online", "email", "referral", "in_person"
    cover_letter_used = Column(Boolean, default=False)
    resume_version_used = Column(String(255))  # Reference to specific resume version
    
    # Personal tracking
    application_status = Column(String(50), default="applied")  # "applied", "screening", "interview", "offer", "rejected", "withdrawn"
    application_date = Column(DateTime(timezone=True), nullable=False)
    
    # Contact and follow-up tracking
    recruiter_name = Column(String(255))
    recruiter_email = Column(String(255))
    recruiter_phone = Column(String(50))
    hr_contact = Column(String(255))
    
    # Interview tracking
    interview_rounds = Column(Integer, default=0)
    next_interview_date = Column(DateTime(timezone=True))
    interview_notes = Column(Text)
    
    # Outcome tracking
    outcome = Column(String(50))  # "pending", "hired", "rejected", "withdrawn", "no_response"
    outcome_date = Column(DateTime(timezone=True))
    outcome_reason = Column(Text)  # Feedback or reason for outcome
    
    # Personal insights
    salary_range_min = Column(Integer)  # For personal tracking
    salary_range_max = Column(Integer)
    benefits_notes = Column(Text)
    company_culture_notes = Column(Text)
    personal_interest_level = Column(Integer)  # 1-10 scale
    
    # Performance tracking
    response_time_days = Column(Integer)  # Days to get first response
    total_process_days = Column(Integer)  # Total days from application to outcome
    
    # Follow-up tracking
    last_follow_up_date = Column(DateTime(timezone=True))
    next_follow_up_date = Column(DateTime(timezone=True))
    follow_up_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile", back_populates="job_applications")
    application_documents = relationship("ApplicationDocument", back_populates="application", cascade="all, delete-orphan")
    application_events = relationship("ApplicationEvent", back_populates="application", cascade="all, delete-orphan")
    
    @validates('application_status')
    def validate_status(self, key, status):
        """Validate application status."""
        valid_statuses = [
            "applied", "screening", "phone_screen", "technical_interview", 
            "on_site_interview", "final_interview", "offer", "rejected", 
            "withdrawn", "no_response"
        ]
        if status and status not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return status
    
    @validates('outcome')
    def validate_outcome(self, key, outcome):
        """Validate application outcome."""
        valid_outcomes = ["pending", "hired", "rejected", "withdrawn", "no_response"]
        if outcome and outcome not in valid_outcomes:
            raise ValueError(f"Outcome must be one of: {valid_outcomes}")
        return outcome
    
    @validates('personal_interest_level')
    def validate_interest_level(self, key, level):
        """Validate interest level."""
        if level is not None and (level < 1 or level > 10):
            raise ValueError("Interest level must be between 1 and 10")
        return level


class ApplicationDocument(Base):
    """
    Documents associated with job applications (resumes, cover letters, etc.).
    Tracks which documents were used for specific applications.
    """
    __tablename__ = "application_documents"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    application_id = Column(GUID(), ForeignKey("job_applications.id"), nullable=False)
    
    # Document details
    document_type = Column(String(100), nullable=False)  # "resume", "cover_letter", "portfolio"
    document_format = Column(String(50), nullable=False)  # "pdf", "docx", "html"
    file_path = Column(String(1000))  # Local file path
    file_size_bytes = Column(Integer)
    
    # Export details
    export_settings = Column(JSONType, default=dict)  # Settings used for this export
    content_selection_id = Column(GUID(), ForeignKey("content_selections.id"))  # Which content was selected
    ats_optimization_id = Column(GUID(), ForeignKey("ats_optimizations.id"))  # ATS optimization applied
    
    # Quality metrics
    quality_score = Column(Float)  # Quality score at time of export
    ats_compatibility_score = Column(Float)
    keyword_optimization_score = Column(Float)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    application = relationship("JobApplication", back_populates="application_documents")
    content_selection = relationship("ContentSelection")
    ats_optimization = relationship("ATSOptimization")


class ApplicationEvent(Base):
    """
    Timeline events for job applications (follow-ups, interviews, responses).
    Provides detailed tracking of application progress.
    """
    __tablename__ = "application_events"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    application_id = Column(GUID(), ForeignKey("job_applications.id"), nullable=False)
    
    # Event details
    event_type = Column(String(100), nullable=False)  # "application_sent", "response_received", "interview_scheduled"
    event_date = Column(DateTime(timezone=True), nullable=False)
    event_description = Column(Text)
    
    # Contact information
    contact_person = Column(String(255))
    contact_method = Column(String(100))  # "email", "phone", "linkedin", "in_person"
    
    # Event outcomes
    outcome = Column(String(100))  # "positive", "negative", "neutral", "pending"
    next_steps = Column(Text)
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(DateTime(timezone=True))
    
    # Attachments and references
    attachments = Column(ArrayType)  # File paths to relevant documents
    external_references = Column(ArrayType)  # URLs, email IDs, etc.
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    application = relationship("JobApplication", back_populates="application_events")


class ExportHistory(Base):
    """
    History of document exports for tracking and analytics.
    Helps users understand export patterns and success rates.
    """
    __tablename__ = "export_history"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    profile_id = Column(GUID(), ForeignKey("user_profiles.id"), nullable=False)
    
    # Export details
    export_type = Column(String(100), nullable=False)  # "resume", "cover_letter", "portfolio"
    export_format = Column(String(50), nullable=False)  # "pdf", "docx", "html", "json"
    export_purpose = Column(String(100))  # "job_application", "networking", "portfolio"
    
    # Target job context
    target_role = Column(String(255))
    target_company = Column(String(255))
    target_industry = Column(String(100))
    
    # Content selection details
    content_selection_id = Column(GUID(), ForeignKey("content_selections.id"))
    ats_optimization_id = Column(GUID(), ForeignKey("ats_optimizations.id"))
    quality_assessment_id = Column(GUID(), ForeignKey("quality_assessments.id"))
    
    # Export results
    export_success = Column(Boolean, nullable=False)
    file_size_bytes = Column(Integer)
    generation_time_ms = Column(Integer)
    error_message = Column(Text)
    
    # Usage tracking
    download_count = Column(Integer, default=0)
    last_downloaded = Column(DateTime(timezone=True))
    
    # Performance tracking
    application_outcome = Column(String(50))  # Track if this export led to success
    user_satisfaction = Column(Integer)  # 1-5 rating from user
    user_feedback = Column(Text)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile", back_populates="export_history")
    content_selection = relationship("ContentSelection")
    ats_optimization = relationship("ATSOptimization")
    quality_assessment = relationship("QualityAssessment")


class ExportTemplate(Base):
    """
    Custom export templates for different formats and purposes.
    Allows users to create personalized document templates.
    """
    __tablename__ = "export_templates"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    profile_id = Column(GUID(), ForeignKey("user_profiles.id"), nullable=False)
    
    # Template details
    template_name = Column(String(255), nullable=False)
    template_description = Column(Text)
    template_type = Column(String(100), nullable=False)  # "resume", "cover_letter"
    export_format = Column(String(50), nullable=False)  # "pdf", "docx", "html"
    
    # Template configuration
    template_content = Column(Text, nullable=False)  # Template file content
    styling_options = Column(JSONType, default=dict)  # CSS, fonts, colors, etc.
    layout_options = Column(JSONType, default=dict)  # Margins, spacing, etc.
    
    # Usage settings
    is_default = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)  # Share with other users
    usage_count = Column(Integer, default=0)
    
    # Template metadata
    template_version = Column(String(50), default="1.0")
    compatibility_notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile", back_populates="export_templates")


# PRD-011: Database indexes for application management performance optimization

# Job application indexes
Index('idx_job_applications_profile_id', JobApplication.profile_id)
Index('idx_job_applications_status', JobApplication.application_status)
Index('idx_job_applications_company', JobApplication.company_name)
Index('idx_job_applications_date', JobApplication.application_date)
Index('idx_job_applications_outcome', JobApplication.outcome)
Index('idx_job_applications_profile_status', JobApplication.profile_id, JobApplication.application_status)

# Application document indexes
Index('idx_application_documents_application_id', ApplicationDocument.application_id)
Index('idx_application_documents_type', ApplicationDocument.document_type)
Index('idx_application_documents_format', ApplicationDocument.document_format)

# Application event indexes
Index('idx_application_events_application_id', ApplicationEvent.application_id)
Index('idx_application_events_date', ApplicationEvent.event_date)
Index('idx_application_events_type', ApplicationEvent.event_type)

# Export history indexes
Index('idx_export_history_profile_id', ExportHistory.profile_id)
Index('idx_export_history_format', ExportHistory.export_format)
Index('idx_export_history_created', ExportHistory.created_at)
Index('idx_export_history_profile_format', ExportHistory.profile_id, ExportHistory.export_format)

# Export template indexes
Index('idx_export_templates_profile_id', ExportTemplate.profile_id)
Index('idx_export_templates_type', ExportTemplate.template_type)
Index('idx_export_templates_format', ExportTemplate.export_format)
Index('idx_export_templates_default', ExportTemplate.is_default)

# Additional constraints for PRD-011 data integrity
UniqueConstraint(
    ExportTemplate.profile_id,
    ExportTemplate.template_name,
    name='unique_template_name_per_profile'
)


# Phase 4: Continuous Learning & Personalization Database Models

class ApplicationOutcome(Base):
    """
    Application outcomes for learning and personalization.
    Phase 4 implementation for tracking job application results.
    """
    __tablename__ = "application_outcomes"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    application_id = Column(String(255), nullable=False, index=True)
    user_profile_id = Column(GUID(), ForeignKey("user_profiles.id"), nullable=False)
    
    # Job details
    company_name = Column(String(255), nullable=False)
    position_title = Column(String(255), nullable=False)
    job_description = Column(Text)
    industry = Column(String(100))
    
    # Application context
    content_selection_id = Column(GUID(), ForeignKey("content_selections.id"))
    ats_optimization_id = Column(GUID(), ForeignKey("ats_optimizations.id"))
    content_enhancement_ids = Column(ArrayType)  # List of enhancement IDs used
    
    # Outcome details
    outcome_type = Column(String(50), nullable=False)  # "application_sent", "viewed", "phone_screen", "interview", "offer", "rejection", "no_response"
    outcome_date = Column(DateTime(timezone=True), nullable=False)
    days_to_outcome = Column(Integer)  # Days from application to outcome
    
    # Additional outcome data
    feedback_notes = Column(Text)
    salary_offered = Column(Float)
    rejection_reason = Column(String(255))
    interview_rounds = Column(Integer, default=0)
    
    # Learning metadata
    ai_content_selection_used = Column(Boolean, default=False)
    ats_optimization_applied = Column(Boolean, default=False)
    content_enhancement_applied = Column(Boolean, default=False)
    personalization_applied = Column(Boolean, default=False)
    
    # Tracking metadata
    data_source = Column(String(100), default="user_input")  # "user_input", "automated", "import"
    confidence_level = Column(Float, default=1.0)  # Confidence in outcome data (0.0-1.0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile")
    content_selection = relationship("ContentSelection")
    ats_optimization = relationship("ATSOptimization")
    
    @validates('outcome_type')
    def validate_outcome_type(self, key, outcome_type):
        """Validate outcome type."""
        valid_types = [
            "application_sent", "viewed", "phone_screen", "interview", 
            "offer", "rejection", "no_response", "withdrawn"
        ]
        if outcome_type and outcome_type not in valid_types:
            raise ValueError(f"Outcome type must be one of: {valid_types}")
        return outcome_type


class UserPreference(Base):
    """
    User preferences and personalization data.
    Stores learned preferences and personalization insights.
    """
    __tablename__ = "user_preferences"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_profile_id = Column(GUID(), ForeignKey("user_profiles.id"), nullable=False)
    
    # Preference details
    preference_type = Column(String(100), nullable=False)  # "personalization_analysis", "content_strategy", "enhancement_level"
    preference_category = Column(String(100))  # "content_selection", "enhancement", "ats_optimization"
    
    # Preference data (JSON for flexibility)
    preference_data = Column(JSONType, nullable=False)
    confidence_score = Column(Float, default=0.5)  # Confidence in this preference (0.0-1.0)
    
    # Learning metadata
    data_points_count = Column(Integer, default=1)  # Number of data points supporting this preference
    last_validation_date = Column(DateTime(timezone=True))
    validation_success_rate = Column(Float, default=0.0)  # Success rate when this preference is applied
    
    # Preference lifecycle
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True))  # Optional expiration for temporary preferences
    superseded_by = Column(GUID(), ForeignKey("user_preferences.id"))  # Reference to newer preference
    
    # Usage tracking
    times_applied = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile")
    superseded_preference = relationship("UserPreference", remote_side=[id])


class PersonalizationInsight(Base):
    """
    Personalization insights generated from user data analysis.
    Stores AI-generated insights for improving user outcomes.
    """
    __tablename__ = "personalization_insights"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_profile_id = Column(GUID(), ForeignKey("user_profiles.id"), nullable=False)
    
    # Insight details
    insight_type = Column(String(100), nullable=False)  # "achievement_selection", "keyword_strategy", "enhancement_level"
    insight_category = Column(String(100))  # "content", "optimization", "strategy"
    recommendation = Column(Text, nullable=False)
    
    # Supporting evidence
    supporting_evidence = Column(ArrayType)  # List of evidence supporting this insight
    data_points_analyzed = Column(Integer, default=0)
    analysis_period_days = Column(Integer, default=365)
    
    # Confidence and impact
    confidence_score = Column(Float, nullable=False)  # AI confidence in insight (0.0-1.0)
    expected_improvement = Column(Float, default=0.0)  # Expected improvement percentage
    actual_improvement = Column(Float)  # Measured improvement when applied
    
    # Insight status
    status = Column(String(50), default="active")  # "active", "applied", "superseded", "invalid"
    applied_date = Column(DateTime(timezone=True))
    validation_date = Column(DateTime(timezone=True))
    
    # AI metadata
    ai_model_used = Column(String(100))  # AI model that generated the insight
    ai_reasoning = Column(Text)  # Detailed AI reasoning
    generation_algorithm = Column(String(100), default="gemini_personalization_v1")
    
    # Performance tracking
    times_applied = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    user_satisfaction = Column(Float)  # User rating of insight quality
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile")
    
    @validates('insight_type')
    def validate_insight_type(self, key, insight_type):
        """Validate insight type."""
        valid_types = [
            "achievement_selection", "keyword_strategy", "enhancement_level", 
            "industry_focus", "content_length", "ats_optimization", "timing_strategy"
        ]
        if insight_type and insight_type not in valid_types:
            raise ValueError(f"Insight type must be one of: {valid_types}")
        return insight_type
    
    @validates('status')
    def validate_status(self, key, status):
        """Validate insight status."""
        valid_statuses = ["active", "applied", "superseded", "invalid", "expired"]
        if status and status not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return status


class MarketTrend(Base):
    """
    Market trends and intelligence data for personalization.
    Stores industry and role-specific trends for optimization.
    """
    __tablename__ = "market_trends"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # Trend identification
    trend_type = Column(String(100), nullable=False)  # "keyword_popularity", "skill_demand", "salary_trend"
    industry = Column(String(100))
    job_level = Column(String(50))  # "entry", "mid", "senior", "executive"
    location = Column(String(255))
    
    # Trend data
    trend_name = Column(String(255), nullable=False)  # Name of the trend
    trend_description = Column(Text)
    trend_value = Column(Float)  # Numeric value (frequency, salary, etc.)
    trend_direction = Column(String(20))  # "increasing", "decreasing", "stable"
    trend_strength = Column(Float, default=0.5)  # Strength of trend (0.0-1.0)
    
    # Time period
    analysis_period_start = Column(DateTime(timezone=True))
    analysis_period_end = Column(DateTime(timezone=True))
    data_points_count = Column(Integer, default=0)
    
    # Data source and confidence
    data_source = Column(String(100))  # "job_postings", "salary_data", "user_outcomes"
    confidence_score = Column(Float, default=0.5)  # Confidence in trend data
    
    # Related data
    related_keywords = Column(ArrayType)
    related_skills = Column(ArrayType)
    supporting_data = Column(JSONType, default=dict)
    
    # Trend metadata
    trend_rank = Column(Integer)  # Rank among similar trends
    previous_value = Column(Float)  # Previous period value for comparison
    change_percentage = Column(Float)  # Percentage change from previous period
    
    # Usage tracking
    times_referenced = Column(Integer, default=0)
    last_referenced = Column(DateTime(timezone=True))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    @validates('trend_direction')
    def validate_trend_direction(self, key, direction):
        """Validate trend direction."""
        valid_directions = ["increasing", "decreasing", "stable", "volatile"]
        if direction and direction not in valid_directions:
            raise ValueError(f"Trend direction must be one of: {valid_directions}")
        return direction


class ABTestExperiment(Base):
    """
    A/B testing experiments for algorithm optimization.
    Enables continuous improvement of personalization algorithms.
    """
    __tablename__ = "ab_test_experiments"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # Experiment details
    experiment_name = Column(String(255), nullable=False)
    experiment_description = Column(Text)
    experiment_type = Column(String(100), nullable=False)  # "content_selection", "enhancement_level", "keyword_strategy"
    
    # Experiment configuration
    control_algorithm = Column(String(100), nullable=False)  # Current algorithm
    test_algorithm = Column(String(100), nullable=False)  # New algorithm being tested
    experiment_config = Column(JSONType, default=dict)  # Configuration parameters
    
    # Experiment status
    status = Column(String(50), default="draft")  # "draft", "active", "paused", "completed", "cancelled"
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    planned_duration_days = Column(Integer, default=30)
    
    # Traffic allocation
    traffic_allocation = Column(Float, default=0.5)  # Percentage of users in test group (0.0-1.0)
    min_sample_size = Column(Integer, default=100)  # Minimum users needed for statistical significance
    confidence_level = Column(Float, default=0.95)  # Required confidence level for results
    
    # Success metrics
    primary_metric = Column(String(100), nullable=False)  # "success_rate", "user_satisfaction", "improvement_score"
    secondary_metrics = Column(ArrayType)  # Additional metrics to track
    success_criteria = Column(JSONType, default=dict)  # What constitutes success
    
    # Results tracking
    control_group_size = Column(Integer, default=0)
    test_group_size = Column(Integer, default=0)
    control_group_results = Column(JSONType, default=dict)
    test_group_results = Column(JSONType, default=dict)
    
    # Statistical analysis
    statistical_significance = Column(Float)  # P-value of results
    effect_size = Column(Float)  # Measured effect size
    confidence_interval_lower = Column(Float)
    confidence_interval_upper = Column(Float)
    
    # Conclusion
    winner = Column(String(20))  # "control", "test", "inconclusive"
    conclusion_notes = Column(Text)
    implementation_decision = Column(String(50))  # "implement", "reject", "iterate"
    
    # Metadata
    created_by = Column(String(255))  # User or system that created the experiment
    analyzed_by = Column(String(255))  # Who analyzed the results
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    @validates('status')
    def validate_status(self, key, status):
        """Validate experiment status."""
        valid_statuses = ["draft", "active", "paused", "completed", "cancelled"]
        if status and status not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return status
    
    @validates('winner')
    def validate_winner(self, key, winner):
        """Validate experiment winner."""
        valid_winners = ["control", "test", "inconclusive"]
        if winner and winner not in valid_winners:
            raise ValueError(f"Winner must be one of: {valid_winners}")
        return winner


class ABTestAssignment(Base):
    """
    User assignments to A/B test experiments.
    Tracks which users are in which test groups.
    """
    __tablename__ = "ab_test_assignments"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(GUID(), ForeignKey("ab_test_experiments.id"), nullable=False)
    user_profile_id = Column(GUID(), ForeignKey("user_profiles.id"), nullable=False)
    
    # Assignment details
    test_group = Column(String(20), nullable=False)  # "control", "test"
    assignment_date = Column(DateTime(timezone=True), server_default=func.now())
    assignment_method = Column(String(100), default="random")  # "random", "stratified", "manual"
    
    # User context at assignment
    user_segment = Column(String(100))  # User segment for stratified testing
    user_characteristics = Column(JSONType, default=dict)  # User properties at assignment
    
    # Participation tracking
    is_active = Column(Boolean, default=True)
    opt_out_date = Column(DateTime(timezone=True))
    opt_out_reason = Column(String(255))
    
    # Results tracking
    primary_metric_value = Column(Float)  # User's result for primary metric
    secondary_metric_values = Column(JSONType, default=dict)  # Secondary metric results
    outcome_recorded = Column(Boolean, default=False)
    outcome_date = Column(DateTime(timezone=True))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    experiment = relationship("ABTestExperiment")
    profile = relationship("UserProfile")
    
    @validates('test_group')
    def validate_test_group(self, key, group):
        """Validate test group."""
        valid_groups = ["control", "test"]
        if group and group not in valid_groups:
            raise ValueError(f"Test group must be one of: {valid_groups}")
        return group


class LearningEvent(Base):
    """
    Learning events for tracking algorithm performance.
    Records when algorithms are used and their outcomes.
    """
    __tablename__ = "learning_events"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_profile_id = Column(GUID(), ForeignKey("user_profiles.id"), nullable=False)
    
    # Event details
    event_type = Column(String(100), nullable=False)  # "content_selection", "enhancement_applied", "ats_optimization"
    algorithm_name = Column(String(100), nullable=False)  # Algorithm that was used
    algorithm_version = Column(String(50), default="1.0")
    
    # Context
    context_data = Column(JSONType, default=dict)  # Context when algorithm was applied
    input_parameters = Column(JSONType, default=dict)  # Parameters passed to algorithm
    output_results = Column(JSONType, default=dict)  # Results from algorithm
    
    # Performance metrics
    processing_time_ms = Column(Integer)
    confidence_score = Column(Float)  # Algorithm's confidence in results
    success = Column(Boolean, nullable=False)  # Whether algorithm execution succeeded
    error_message = Column(Text)  # Error message if algorithm failed
    
    # Outcome tracking
    outcome_type = Column(String(100))  # Type of outcome measured
    outcome_value = Column(Float)  # Numeric outcome value
    outcome_measured_date = Column(DateTime(timezone=True))
    
    # Learning metadata
    feedback_received = Column(Boolean, default=False)
    feedback_type = Column(String(100))  # "user_rating", "application_outcome", "manual"
    feedback_value = Column(Float)  # Feedback score or rating
    feedback_notes = Column(Text)
    
    # A/B testing context
    ab_test_id = Column(GUID(), ForeignKey("ab_test_experiments.id"))
    test_group = Column(String(20))  # "control", "test"
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile")
    ab_test = relationship("ABTestExperiment")
    
    @validates('event_type')
    def validate_event_type(self, key, event_type):
        """Validate event type."""
        valid_types = [
            "content_selection", "enhancement_applied", "ats_optimization", 
            "personalization_applied", "job_analysis", "market_intelligence"
        ]
        if event_type and event_type not in valid_types:
            raise ValueError(f"Event type must be one of: {valid_types}")
        return event_type


# Phase 4: Database indexes for performance optimization

# Application outcome indexes
Index('idx_application_outcomes_user', ApplicationOutcome.user_profile_id)
Index('idx_application_outcomes_outcome_type', ApplicationOutcome.outcome_type)
Index('idx_application_outcomes_date', ApplicationOutcome.outcome_date)
Index('idx_application_outcomes_company', ApplicationOutcome.company_name)
Index('idx_application_outcomes_user_outcome', ApplicationOutcome.user_profile_id, ApplicationOutcome.outcome_type)
Index('idx_application_outcomes_learning', ApplicationOutcome.ai_content_selection_used, ApplicationOutcome.ats_optimization_applied, ApplicationOutcome.content_enhancement_applied)

# User preference indexes
Index('idx_user_preferences_user', UserPreference.user_profile_id)
Index('idx_user_preferences_type', UserPreference.preference_type)
Index('idx_user_preferences_category', UserPreference.preference_category)
Index('idx_user_preferences_active', UserPreference.is_active)
Index('idx_user_preferences_user_type', UserPreference.user_profile_id, UserPreference.preference_type)

# Personalization insight indexes
Index('idx_personalization_insights_user', PersonalizationInsight.user_profile_id)
Index('idx_personalization_insights_type', PersonalizationInsight.insight_type)
Index('idx_personalization_insights_status', PersonalizationInsight.status)
Index('idx_personalization_insights_confidence', PersonalizationInsight.confidence_score)
Index('idx_personalization_insights_user_type', PersonalizationInsight.user_profile_id, PersonalizationInsight.insight_type)

# Market trend indexes
Index('idx_market_trends_type', MarketTrend.trend_type)
Index('idx_market_trends_industry', MarketTrend.industry)
Index('idx_market_trends_job_level', MarketTrend.job_level)
Index('idx_market_trends_location', MarketTrend.location)
Index('idx_market_trends_industry_level', MarketTrend.industry, MarketTrend.job_level)
Index('idx_market_trends_rank', MarketTrend.trend_rank)

# A/B test indexes
Index('idx_ab_test_experiments_status', ABTestExperiment.status)
Index('idx_ab_test_experiments_type', ABTestExperiment.experiment_type)
Index('idx_ab_test_experiments_dates', ABTestExperiment.start_date, ABTestExperiment.end_date)

# A/B test assignment indexes
Index('idx_ab_test_assignments_experiment', ABTestAssignment.experiment_id)
Index('idx_ab_test_assignments_user', ABTestAssignment.user_profile_id)
Index('idx_ab_test_assignments_group', ABTestAssignment.test_group)
Index('idx_ab_test_assignments_active', ABTestAssignment.is_active)
Index('idx_ab_test_assignments_outcome', ABTestAssignment.outcome_recorded)

# Learning event indexes
Index('idx_learning_events_user', LearningEvent.user_profile_id)
Index('idx_learning_events_type', LearningEvent.event_type)
Index('idx_learning_events_algorithm', LearningEvent.algorithm_name)
Index('idx_learning_events_success', LearningEvent.success)
Index('idx_learning_events_ab_test', LearningEvent.ab_test_id)
Index('idx_learning_events_user_algorithm', LearningEvent.user_profile_id, LearningEvent.algorithm_name)

# Unique constraints for Phase 4 data integrity
UniqueConstraint(
    ABTestAssignment.experiment_id,
    ABTestAssignment.user_profile_id,
    name='unique_user_per_experiment'
)