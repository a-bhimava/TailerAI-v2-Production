"""
Core business entities for Resume AI Tailer.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class ProcessingStatus(str, Enum):
    """Status of resume processing."""
    PENDING = "pending"
    PARSING = "parsing"
    ANALYZING = "analyzing"
    OPTIMIZING = "optimizing"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class AIModel(str, Enum):
    """Available AI models."""
    GEMINI_PRO = "gemini-1.5-pro"
    LLAMA_8B = "llama3.1:8b"
    PHI_MINI = "phi-3-mini"


@dataclass
class PersonalInfo:
    """Personal information extracted from resume."""
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""


@dataclass
class ExperienceBullet:
    """Individual experience bullet point."""
    text: str
    relevance_score: float = 0.0
    keywords: List[str] = field(default_factory=list)
    enhanced_text: Optional[str] = None
    selected: bool = False


@dataclass
class WorkExperience:
    """Work experience section."""
    company: str
    position: str
    duration: str
    location: str = ""
    bullets: List[ExperienceBullet] = field(default_factory=list)


@dataclass
class Education:
    """Education information."""
    institution: str = ""
    degree: str = ""
    year: str = ""
    gpa: Optional[str] = None


@dataclass
class Resume:
    """Complete resume structure."""
    personal_info: PersonalInfo = field(default_factory=PersonalInfo)
    summary: str = ""
    work_experience: List[WorkExperience] = field(default_factory=list)
    education: List[Education] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    
    def get_all_bullets(self) -> List[ExperienceBullet]:
        """Get all experience bullets from all jobs."""
        bullets = []
        for exp in self.work_experience:
            bullets.extend(exp.bullets)
        return bullets


@dataclass
class JobRequirement:
    """Individual job requirement."""
    text: str
    category: str  # technical, soft_skill, experience, education
    importance: str  # required, preferred, nice_to_have
    keywords: List[str] = field(default_factory=list)


@dataclass
class JobDescription:
    """Parsed job description."""
    raw_text: str
    company: str = ""
    position: str = ""
    requirements: List[JobRequirement] = field(default_factory=list)
    skills_needed: List[str] = field(default_factory=list)
    industry: str = ""
    seniority_level: str = ""  # entry, mid, senior, executive
    
    def get_all_keywords(self) -> List[str]:
        """Get all keywords from requirements."""
        keywords = []
        for req in self.requirements:
            keywords.extend(req.keywords)
        return list(set(keywords))


@dataclass
class MatchAnalysis:
    """Analysis of resume-job matching."""
    overall_score: float
    keyword_matches: List[str] = field(default_factory=list)
    missing_keywords: List[str] = field(default_factory=list)
    skill_gaps: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class AIRecommendation:
    """AI-generated recommendation."""
    type: str  # experience, skill, keyword, format
    original_text: str
    suggested_text: str
    reasoning: str
    confidence: float
    priority: str  # high, medium, low


@dataclass
class OptimizedResume:
    """Optimized resume result."""
    original_resume: Resume
    selected_bullets: List[ExperienceBullet]
    enhanced_bullets: List[ExperienceBullet]
    added_keywords: List[str]
    match_analysis: MatchAnalysis
    recommendations: List[AIRecommendation]
    processing_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingSession:
    """Complete processing session."""
    session_id: str
    status: ProcessingStatus = ProcessingStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Input data
    original_filename: str = ""
    resume: Optional[Resume] = None
    job_description: Optional[JobDescription] = None
    
    # Processing results
    optimized_resume: Optional[OptimizedResume] = None
    generated_files: List[str] = field(default_factory=list)
    
    # Metadata
    processing_time_seconds: float = 0.0
    ai_model_used: AIModel = AIModel.GEMINI_PRO
    error_message: Optional[str] = None
    
    def update_status(self, status: ProcessingStatus):
        """Update processing status with timestamp."""
        self.status = status
        self.updated_at = datetime.utcnow()


@dataclass
class GeneratedDocument:
    """Generated resume document."""
    file_path: str
    template_used: str
    version: str  # conservative, enhanced
    created_at: datetime = field(default_factory=datetime.utcnow)
    download_count: int = 0