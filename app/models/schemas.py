"""
Pydantic schemas for API request/response validation.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from datetime import datetime
from app.models.entities import ProcessingStatus, AIModel


class ResumeUploadRequest(BaseModel):
    """Request schema for resume upload."""
    job_description: str = Field(..., min_length=50, max_length=10000)
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ProcessingStatusResponse(BaseModel):
    """Response schema for processing status."""
    session_id: str
    status: ProcessingStatus
    progress_percentage: int = Field(ge=0, le=100)
    current_step: str
    estimated_time_remaining: Optional[int] = None  # seconds
    created_at: datetime
    updated_at: datetime


class PersonalInfoResponse(BaseModel):
    """Response schema for personal information."""
    name: str
    email: str
    phone: str
    location: str
    linkedin: str
    github: str


class ExperienceBulletResponse(BaseModel):
    """Response schema for experience bullet."""
    text: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    keywords: List[str]
    enhanced_text: Optional[str] = None
    selected: bool = False


class WorkExperienceResponse(BaseModel):
    """Response schema for work experience."""
    company: str
    position: str
    duration: str
    bullets: List[ExperienceBulletResponse]


class ResumeAnalysisResponse(BaseModel):
    """Response schema for resume analysis."""
    session_id: str
    match_score: float = Field(ge=0.0, le=100.0)
    processing_time_seconds: float
    ai_model_used: AIModel
    
    # Resume content
    personal_info: PersonalInfoResponse
    work_experience: List[WorkExperienceResponse]
    skills: List[str]
    
    # Analysis results
    selected_bullets_count: int
    keyword_matches: List[str]
    missing_keywords: List[str]
    skill_gaps: List[str]
    strengths: List[str]
    recommendations: List[str]


class AIRecommendationResponse(BaseModel):
    """Response schema for AI recommendation."""
    type: str
    original_text: str
    suggested_text: str
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)
    priority: str


class OptimizationResultResponse(BaseModel):
    """Response schema for optimization results."""
    session_id: str
    match_score: float = Field(ge=0.0, le=100.0)
    selected_bullets: List[ExperienceBulletResponse]
    enhanced_bullets: List[ExperienceBulletResponse]
    added_keywords: List[str]
    recommendations: List[AIRecommendationResponse]
    
    # Metadata
    processing_time_seconds: float
    ai_model_used: AIModel
    created_at: datetime


class DocumentGenerationRequest(BaseModel):
    """Request schema for document generation."""
    session_id: str
    template_preference: str = Field(default="modern", pattern="^(modern|executive|technical)$")
    version: str = Field(default="enhanced", pattern="^(conservative|enhanced)$")


class GeneratedDocumentResponse(BaseModel):
    """Response schema for generated document."""
    file_id: str
    download_url: str
    template_used: str
    version: str
    created_at: datetime
    expires_at: datetime


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    error: str
    error_code: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None


class UsageStatsResponse(BaseModel):
    """Response schema for usage statistics."""
    api_calls_today: int
    api_calls_remaining: int
    rate_limit_reset: datetime
    processing_time_avg: float
    success_rate: float = Field(ge=0.0, le=1.0)
    
    services_status: Dict[str, bool]
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class HealthCheckResponse(BaseModel):
    """Response schema for health check."""
    status: str
    app_name: str
    app_version: str
    gemini_available: bool
    debug_mode: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class APIStatusResponse(BaseModel):
    """Response schema for API status."""
    api_version: str
    services: Dict[str, bool]
    limits: Dict[str, int]
    models: Dict[str, str]


# Validation helpers
class JobDescriptionValidator(BaseModel):
    """Validator for job description content with security checks."""
    content: str = Field(..., min_length=50, max_length=50000)
    
    @validator('content')
    def validate_job_description(cls, v):
        if not v.strip():
            raise ValueError('Job description cannot be empty')
        
        # Security checks - prevent potential injection attacks
        suspicious_patterns = [
            '<script', 'javascript:', 'data:', 'vbscript:', 'onload=', 'onerror=',
            'eval(', 'exec(', 'import os', 'import sys', '__import__',
            'subprocess', 'os.system', 'shell=True'
        ]
        
        content_lower = v.lower()
        for pattern in suspicious_patterns:
            if pattern in content_lower:
                raise ValueError(f'Content contains potentially unsafe pattern: {pattern}')
        
        # Check for excessive repetition (potential spam/injection)
        words = v.split()
        if len(words) < 20:
            raise ValueError('Job description is too short (minimum 20 words)')
        
        # Check for word repetition (simple spam detection)
        word_counts = {}
        for word in words:
            word_counts[word.lower()] = word_counts.get(word.lower(), 0) + 1
        
        max_repetition = max(word_counts.values()) if word_counts else 0
        if max_repetition > len(words) * 0.3:  # More than 30% same word
            raise ValueError('Content appears to contain excessive repetition')
        
        # Check for common job description keywords
        required_keywords = ['responsibilities', 'requirements', 'experience', 'skills', 'qualifications']
        
        if not any(keyword in content_lower for keyword in required_keywords):
            raise ValueError('Job description appears to be invalid (missing key sections)')
        
        # Remove any potentially harmful characters and normalize
        cleaned_content = ''.join(char if char.isprintable() or char.isspace() else ' ' for char in v)
        return cleaned_content.strip()


class SessionValidator(BaseModel):
    """Validator for session IDs with enhanced security checks."""
    session_id: str = Field(..., min_length=10, max_length=50)
    
    @validator('session_id')
    def validate_session_id(cls, v):
        # Allow alphanumeric and common UUID characters (hyphens)
        import re
        if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
            raise ValueError('Session ID contains invalid characters')
        
        # Check for potential path traversal attempts
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError('Session ID cannot contain path separators')
        
        return v


class ContentSanitizer:
    """General content sanitizer for security."""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal and injection."""
        import re
        
        if not filename:
            raise ValueError("Filename cannot be empty")
        
        # Remove path components
        filename = filename.split('/')[-1].split('\\')[-1]
        
        # Remove or replace dangerous characters
        filename = re.sub(r'[<>:"|?*\x00-\x1f]', '_', filename)
        
        # Prevent reserved names on Windows
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                         'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
                         'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
        
        name_without_ext = filename.rsplit('.', 1)[0].upper()
        if name_without_ext in reserved_names:
            filename = f"safe_{filename}"
        
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:250] + ('.' + ext if ext else '')
        
        return filename
    
    @staticmethod
    def sanitize_text_input(text: str, max_length: int = 10000) -> str:
        """Sanitize general text input."""
        if not text:
            return ""
        
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length]
        
        # Remove control characters except newlines and tabs
        sanitized = ''.join(char if char.isprintable() or char in '\n\t' else ' ' for char in text)
        
        # Normalize whitespace
        import re
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        return sanitized


# Additional schemas for API routes
class FileUploadResponse(BaseModel):
    """Response schema for file upload."""
    success: bool
    file_id: str
    filename: str
    size: int
    message: str
    session_id: Optional[str] = None


class AnalysisRequest(BaseModel):
    """Request schema for analysis."""
    session_id: str
    analysis_type: str = "comprehensive"


class AnalysisResponse(BaseModel):
    """Response schema for analysis."""
    success: bool
    overall_score: float
    keyword_matches: List[str]
    missing_keywords: List[str]
    recommendations: List[str]
    session_id: str
    processing_time: float


class OptimizationRequest(BaseModel):
    """Request schema for optimization."""
    session_id: str
    optimization_type: str = "content"


class OptimizationResponse(BaseModel):
    """Response schema for optimization."""
    success: bool
    optimizations: List[Dict[str, Any]]
    applied_count: int
    session_id: str
    # New fields for master resume targeting
    targeting_data: Optional[List[Dict[str, Any]]] = None
    one_page_validation: Optional[Dict[str, Any]] = None
    targeting_config: Optional[Dict[str, Any]] = None


class GenerationRequest(BaseModel):
    """Request schema for document generation."""
    session_id: str
    template_id: str = "traditional"
    apply_optimizations: bool = True


class GenerationResponse(BaseModel):
    """Response schema for document generation."""
    success: bool
    session_id: str
    file_info: Dict[str, Any]  # Contains filename, template_used, file_size_bytes, format
    generation_metadata: Dict[str, Any]
    download_url: str
    preview_available: bool


class TemplateListResponse(BaseModel):
    """Response schema for template list."""
    success: bool
    templates: List[Dict[str, Any]]
    total_templates: int
    categories: List[Dict[str, str]]
    default_template: str


class TemplateDetailsResponse(BaseModel):
    """Response schema for template details."""
    success: bool
    template: Dict[str, Any]
    usage_stats: Dict[str, Any]
    similar_templates: List[str]


class SessionResponse(BaseModel):
    """Response schema for session operations."""
    success: bool
    session_id: str
    status: str
    updated_at: str
    message: str


class SessionListResponse(BaseModel):
    """Response schema for session list."""
    success: bool
    sessions: List[Dict[str, Any]]
    total_sessions: int
    page_info: Dict[str, Any]
    summary: Dict[str, Any]


class SessionDetailsResponse(BaseModel):
    """Response schema for session details."""
    success: bool
    session: Dict[str, Any]


class JobDescriptionTextRequest(BaseModel):
    """Request schema for job description text."""
    session_id: str
    job_description: str = Field(..., min_length=50)


class SessionCreateRequest(BaseModel):
    """Request schema for session creation."""
    client_info: Optional[Dict[str, Any]] = None


class SessionCreateResponse(BaseModel):
    """Response schema for session creation."""
    success: bool
    session_id: str
    expires_at: datetime
    message: str


class ResumeUploadResponse(BaseModel):
    """Response schema for resume upload."""
    success: bool
    file_id: str
    filename: str
    parsed_data: Optional[Dict[str, Any]] = None
    session_id: str
    message: str


class JobDescriptionUploadResponse(BaseModel):
    """Response schema for job description upload."""
    success: bool
    file_id: str
    filename: str
    extracted_text: Optional[str] = None
    session_id: str
    message: str


class KeywordMatch(BaseModel):
    """Represents a single matched keyword or requirement."""
    job_requirement: str
    resume_match: str
    similarity: float


class MatchAnalysisResponse(BaseModel):
    """Response schema for match analysis."""
    success: bool
    overall_score: float
    keyword_matches: List[KeywordMatch]
    missing_keywords: List[str]
    semantic_score: float
    recommendations: List[str]
    session_id: str
    processing_time: float
    education_analysis: Optional[Dict[str, Any]] = None
    experience_analysis: Optional[Dict[str, Any]] = None


class JobDescriptionAnalysisResponse(BaseModel):
    """Response schema for job description analysis."""
    success: bool
    key_requirements: List[str]
    required_skills: List[str]
    preferred_skills: List[str]
    industry: str
    seniority_level: str
    session_id: str


class KeywordAnalysisResponse(BaseModel):
    """Response schema for keyword analysis."""
    success: bool
    extracted_keywords: List[str]
    keyword_frequency: Dict[str, int]
    important_keywords: List[str]
    session_id: str


class BulletOptimizationResponse(BaseModel):
    """Response schema for bullet optimization."""
    success: bool
    original_bullet: str
    optimized_bullet: str
    improvements: List[str]
    confidence: float
    impact_score: float


# Enhanced schemas for v2.0 file parsing and upload
class ParsedDocument(BaseModel):
    """
    Structured representation of parsed document
    Contains all extracted information with metadata
    """
    filename: str = Field(..., description="Original filename")
    file_path: str = Field(..., description="Path to saved file")
    file_type: str = Field(..., description="Type of document (resume/job_description)")
    
    # Parsed content
    content: str = Field(..., description="Raw extracted text")
    contact_info: Dict[str, str] = Field(default_factory=dict, description="Extracted contact information")
    sections: Dict[str, List[str]] = Field(default_factory=dict, description="Organized content sections")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata (word count, etc.)")
    parsing_errors: List[str] = Field(default_factory=list, description="Any parsing errors encountered")
    
    class Config:
        schema_extra = {
            "example": {
                "filename": "resume.pdf",
                "file_path": "/uploads/session_123/resume.pdf",
                "file_type": "resume",
                "content": "John Doe\nSoftware Engineer...",
                "contact_info": {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "+1-555-0123"
                },
                "sections": {
                    "education": ["MIT, Computer Science, 2020"],
                    "experience": ["Software Engineer at Google, 2020-2023"]
                },
                "metadata": {
                    "character_count": 1200,
                    "word_count": 180,
                    "line_count": 25
                },
                "parsing_errors": []
            }
        }


class UploadResponse(BaseModel):
    """
    Enhanced response model for file upload endpoint
    Provides comprehensive upload and parsing results
    """
    status: str = Field(..., description="Upload status")
    session_id: str = Field(..., description="Unique session identifier")
    resume: ParsedDocument = Field(..., description="Parsed resume data")
    job_description: Optional[ParsedDocument] = Field(None, description="Parsed job description (if provided)")
    message: str = Field(..., description="Human-readable status message")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "resume": {
                    "filename": "resume.pdf",
                    "file_type": "resume",
                    "content": "John Doe\nSoftware Engineer..."
                },
                "job_description": None,
                "message": "Files uploaded and parsed successfully"
            }
        }