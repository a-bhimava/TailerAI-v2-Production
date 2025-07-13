"""
Google Gemini 1.5 Pro API client for resume analysis.
"""

import json
import asyncio
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime, timedelta

# Optional import for Google AI
try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

from app.config.settings import get_settings
settings = get_settings()
from app.models.entities import Resume, JobDescription, MatchAnalysis, AIRecommendation
from app.models.database import APIUsage
from app.services.database_service import db_service


@dataclass
class GeminiResponse:
    """Response from Gemini API."""
    content: str
    usage_metadata: Dict[str, Any]
    processing_time: float
    model_used: str
    success: bool = True
    error_message: Optional[str] = None


class RateLimiter:
    """Thread-safe rate limiter for Gemini API calls."""
    
    def __init__(self, requests_per_minute: int = 60, requests_per_day: int = 1500):
        import threading
        self.requests_per_minute = requests_per_minute
        self.requests_per_day = requests_per_day
        self.minute_calls = []
        self.daily_calls = []
        self._lock = threading.RLock()  # Reentrant lock for thread safety
    
    def can_make_request(self) -> bool:
        """Check if we can make a request within rate limits (thread-safe)."""
        with self._lock:
            now = datetime.now()
            
            # Clean old entries
            self._cleanup_old_entries(now)
            
            # Check daily limit
            if len(self.daily_calls) >= self.requests_per_day:
                return False
            
            # Check per-minute limit
            if len(self.minute_calls) >= self.requests_per_minute:
                return False
            
            return True
    
    def record_request(self):
        """Record a new request (thread-safe)."""
        with self._lock:
            now = datetime.now()
            self.minute_calls.append(now)
            self.daily_calls.append(now)
    
    def _cleanup_old_entries(self, now: datetime):
        """Remove old entries outside the time windows (must be called with lock held)."""
        # Remove entries older than 1 minute
        minute_ago = now - timedelta(minutes=1)
        self.minute_calls = [call for call in self.minute_calls if call > minute_ago]
        
        # Remove entries older than 1 day
        day_ago = now - timedelta(days=1)
        self.daily_calls = [call for call in self.daily_calls if call > day_ago]
    
    def get_wait_time(self) -> int:
        """Get seconds to wait before next request (thread-safe)."""
        with self._lock:
            if not self.minute_calls:
                return 0
            
            now = datetime.now()
            minute_ago = now - timedelta(minutes=1)
            
            # Find oldest call in current minute
            recent_calls = [call for call in self.minute_calls if call > minute_ago]
            if len(recent_calls) >= self.requests_per_minute:
                oldest_call = min(recent_calls)
                wait_until = oldest_call + timedelta(minutes=1)
                return max(0, int((wait_until - now).total_seconds()))
            
            return 0


class GeminiClient:
    """Client for Google Gemini 1.5 Pro API."""
    
    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.model_name = "gemini-1.5-pro"
        self.rate_limiter = RateLimiter(
            requests_per_minute=settings.gemini_requests_per_minute,
            requests_per_day=settings.gemini_daily_limit
        )
        
        if not HAS_GENAI:
            raise ImportError("google-generativeai package is required for Gemini integration")
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not configured in settings")
        
        # Configure the API
        genai.configure(api_key=self.api_key)
        
        # Initialize model with safety settings
        try:
            # Try newer API first
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                }
            )
        except TypeError as e:
            if "unexpected keyword argument 'id'" in str(e):
                # Fallback for older versions
                self.model = genai.GenerativeModel(
                    model_name=self.model_name
                )
            else:
                raise e
    
    async def analyze_resume_match(self, resume: Resume, job_description: JobDescription) -> GeminiResponse:
        """Analyze resume-job match using Gemini."""
        if not self.rate_limiter.can_make_request():
            wait_time = self.rate_limiter.get_wait_time()
            raise ValueError(f"Rate limit exceeded. Wait {wait_time} seconds.")
        
        try:
            # Prepare the analysis prompt
            prompt = self._create_match_analysis_prompt(resume, job_description)
            
            start_time = time.time()
            
            # Make API call
            try:
                # Try newer API first
                generation_config = genai.types.GenerationConfig(
                    temperature=0.1,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=4000,
                    response_mime_type="application/json"
                )
            except (TypeError, AttributeError):
                # Fallback for older versions
                generation_config = {
                    "temperature": 0.1,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 4000
                }
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=generation_config
            )
            
            processing_time = time.time() - start_time
            self.rate_limiter.record_request()
            
            # Log API usage
            self._log_api_usage("analyze_resume_match", processing_time, True)
            
            # Handle usage metadata safely
            usage_metadata = {}
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                try:
                    if hasattr(response.usage_metadata, '_asdict'):
                        usage_metadata = response.usage_metadata._asdict()
                    else:
                        # Try to extract common fields
                        usage_metadata = {
                            "prompt_token_count": getattr(response.usage_metadata, 'prompt_token_count', 0),
                            "candidates_token_count": getattr(response.usage_metadata, 'candidates_token_count', 0),
                            "total_token_count": getattr(response.usage_metadata, 'total_token_count', 0)
                        }
                except Exception:
                    usage_metadata = {}
            
            return GeminiResponse(
                content=response.text,
                usage_metadata=usage_metadata,
                processing_time=processing_time,
                model_used=self.model_name,
                success=True
            )
            
        except Exception as e:
            processing_time = time.time() - start_time if 'start_time' in locals() else 0
            self._log_api_usage("analyze_resume_match", processing_time, False, str(e))
            
            return GeminiResponse(
                content="",
                usage_metadata={},
                processing_time=processing_time,
                model_used=self.model_name,
                success=False,
                error_message=str(e)
            )
    
    async def generate_optimizations(self, resume: Resume, job_description: JobDescription, 
                                   missing_keywords: List[str]) -> GeminiResponse:
        """Generate resume optimizations using Gemini."""
        if not self.rate_limiter.can_make_request():
            wait_time = self.rate_limiter.get_wait_time()
            raise ValueError(f"Rate limit exceeded. Wait {wait_time} seconds.")
        
        try:
            prompt = self._create_optimization_prompt(resume, job_description, missing_keywords)
            
            start_time = time.time()
            
            try:
                # Try newer API first
                generation_config = genai.types.GenerationConfig(
                    temperature=0.3,
                    top_p=0.9,
                    top_k=50,
                    max_output_tokens=3000,
                    response_mime_type="application/json"
                )
            except (TypeError, AttributeError):
                # Fallback for older versions
                generation_config = {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "top_k": 50,
                    "max_output_tokens": 3000
                }
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=generation_config
            )
            
            processing_time = time.time() - start_time
            self.rate_limiter.record_request()
            
            self._log_api_usage("generate_optimizations", processing_time, True)
            
            # Handle usage metadata safely
            usage_metadata = {}
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                try:
                    if hasattr(response.usage_metadata, '_asdict'):
                        usage_metadata = response.usage_metadata._asdict()
                    else:
                        # Try to extract common fields
                        usage_metadata = {
                            "prompt_token_count": getattr(response.usage_metadata, 'prompt_token_count', 0),
                            "candidates_token_count": getattr(response.usage_metadata, 'candidates_token_count', 0),
                            "total_token_count": getattr(response.usage_metadata, 'total_token_count', 0)
                        }
                except Exception:
                    usage_metadata = {}
            
            return GeminiResponse(
                content=response.text,
                usage_metadata=usage_metadata,
                processing_time=processing_time,
                model_used=self.model_name,
                success=True
            )
            
        except Exception as e:
            processing_time = time.time() - start_time if 'start_time' in locals() else 0
            self._log_api_usage("generate_optimizations", processing_time, False, str(e))
            
            return GeminiResponse(
                content="",
                usage_metadata={},
                processing_time=processing_time,
                model_used=self.model_name,
                success=False,
                error_message=str(e)
            )
    
    def _create_match_analysis_prompt(self, resume: Resume, job_description: JobDescription) -> str:
        """Create prompt for resume-job match analysis."""
        
        # Extract resume text
        resume_text = self._format_resume_for_analysis(resume)
        job_text = job_description.raw_text
        
        prompt = f"""
You are an expert resume analyst and career coach. Analyze how well this resume matches the given job description and provide detailed insights.

**JOB DESCRIPTION:**
{job_text}

**RESUME:**
{resume_text}

**ANALYSIS TASK:**
Provide a comprehensive analysis in the following JSON format:

{{
    "overall_match_score": <number 0-100>,
    "keyword_matches": [
        "keyword1", "keyword2", ...
    ],
    "missing_critical_keywords": [
        "missing_keyword1", "missing_keyword2", ...
    ],
    "experience_relevance": {{
        "highly_relevant": ["bullet1", "bullet2", ...],
        "moderately_relevant": ["bullet3", "bullet4", ...],
        "low_relevance": ["bullet5", "bullet6", ...]
    }},
    "skill_gaps": [
        "skill_gap1", "skill_gap2", ...
    ],
    "strengths": [
        "strength1", "strength2", ...
    ],
    "improvement_areas": [
        "area1", "area2", ...
    ],
    "recommendations": [
        "recommendation1", "recommendation2", ...
    ],
    "ats_compatibility_score": <number 0-100>,
    "industry_alignment": "excellent|good|fair|poor"
}}

**SCORING CRITERIA:**
- Overall match score: Consider keyword overlap, experience relevance, skill alignment
- ATS compatibility: Assess format, keyword density, section clarity
- Industry alignment: How well the background fits the target industry

**GUIDELINES:**
- Be objective and constructive
- Focus on actionable insights
- Consider both hard and soft skills
- Account for transferable skills
- Provide specific, actionable recommendations

Respond only with valid JSON.
"""
        
        return prompt
    
    def _create_optimization_prompt(self, resume: Resume, job_description: JobDescription, 
                                  missing_keywords: List[str]) -> str:
        """Create prompt for resume optimization suggestions."""
        
        resume_text = self._format_resume_for_analysis(resume)
        job_text = job_description.raw_text
        keywords_text = ", ".join(missing_keywords) if missing_keywords else "None identified"
        
        prompt = f"""
You are an expert resume writer specializing in ATS optimization and career coaching. Your task is to provide specific, actionable suggestions to improve this resume for the target job.

**JOB DESCRIPTION:**
{job_text}

**CURRENT RESUME:**
{resume_text}

**MISSING KEYWORDS TO INTEGRATE:**
{keywords_text}

**OPTIMIZATION TASK:**
Provide detailed optimization suggestions in the following JSON format:

{{
    "enhanced_bullets": [
        {{
            "original": "original bullet text",
            "enhanced": "improved bullet text with keywords",
            "reasoning": "explanation of improvements",
            "keywords_added": ["keyword1", "keyword2"],
            "confidence": <number 0.0-1.0>
        }}
    ],
    "new_bullet_suggestions": [
        {{
            "text": "suggested new bullet point",
            "section": "work_experience|skills|summary",
            "reasoning": "why this addition would help",
            "keywords_covered": ["keyword1", "keyword2"],
            "confidence": <number 0.0-1.0>
        }}
    ],
    "keyword_integration": [
        {{
            "keyword": "missing keyword",
            "suggested_context": "how to naturally integrate this keyword",
            "priority": "high|medium|low"
        }}
    ],
    "section_improvements": [
        {{
            "section": "summary|experience|skills|education",
            "suggestion": "specific improvement suggestion",
            "impact": "expected improvement in ATS score or relevance"
        }}
    ],
    "ats_optimizations": [
        "optimization1", "optimization2", ...
    ]
}}

**OPTIMIZATION PRINCIPLES:**
- Maintain truthfulness - never suggest false experience
- Integrate keywords naturally within existing context
- Enhance impact with metrics and achievements
- Improve ATS compatibility with better formatting
- Focus on relevant accomplishments for this role
- Use strong action verbs and quantifiable results

**QUALITY STANDARDS:**
- All suggestions must be realistic and ethical
- Enhanced bullets should feel natural, not keyword-stuffed
- Confidence scores should reflect the likelihood of improvement
- Prioritize high-impact, low-effort improvements

Respond only with valid JSON.
"""
        
        return prompt
    
    def _format_resume_for_analysis(self, resume: Resume) -> str:
        """Format resume data for AI analysis."""
        lines = []
        
        # Personal info
        if resume.personal_info.name:
            lines.append(f"Name: {resume.personal_info.name}")
        if resume.personal_info.email:
            lines.append(f"Email: {resume.personal_info.email}")
        if resume.personal_info.location:
            lines.append(f"Location: {resume.personal_info.location}")
        
        lines.append("")
        
        # Summary
        if resume.summary:
            lines.append("PROFESSIONAL SUMMARY:")
            lines.append(resume.summary)
            lines.append("")
        
        # Work Experience
        if resume.work_experience:
            lines.append("WORK EXPERIENCE:")
            for exp in resume.work_experience:
                lines.append(f"{exp.position} | {exp.company} | {exp.duration}")
                for bullet in exp.bullets:
                    lines.append(f"• {bullet.text}")
                lines.append("")
        
        # Skills
        if resume.skills:
            lines.append("SKILLS:")
            lines.append(", ".join(resume.skills))
            lines.append("")
        
        # Education
        if resume.education:
            lines.append("EDUCATION:")
            for edu in resume.education:
                lines.append(f"{edu.degree} | {edu.institution} | {edu.year}")
            lines.append("")
        
        # Certifications
        if resume.certifications:
            lines.append("CERTIFICATIONS:")
            for cert in resume.certifications:
                lines.append(f"• {cert}")
        
        return "\n".join(lines)
    
    def _log_api_usage(self, endpoint: str, response_time: float, success: bool, 
                      error_message: Optional[str] = None):
        """Log API usage to database with proper transaction handling."""
        try:
            with db_service.get_session() as db:
                try:
                    usage = APIUsage(
                        service="gemini",
                        endpoint=endpoint,
                        response_time_ms=int(response_time * 1000),
                        success=success,
                        error_message=error_message,
                        request_timestamp=datetime.now()
                    )
                    db.add(usage)
                    db.commit()
                except Exception as e:
                    db.rollback()
                    # Log the error but don't fail the main operation
                    logger.error(f"Failed to log API usage: {e}")
        except Exception:
            # Don't fail the main operation if logging fails
            pass
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        return {
            "daily_calls_used": len(self.rate_limiter.daily_calls),
            "daily_limit": self.rate_limiter.requests_per_day,
            "daily_calls_remaining": self.rate_limiter.requests_per_day - len(self.rate_limiter.daily_calls),
            "minute_calls_used": len(self.rate_limiter.minute_calls),
            "minute_limit": self.rate_limiter.requests_per_minute,
            "can_make_request": self.rate_limiter.can_make_request(),
            "wait_time_seconds": self.rate_limiter.get_wait_time()
        }
    
    def is_available(self) -> bool:
        """Check if Gemini client is available and configured."""
        return HAS_GENAI and bool(self.api_key)


# Convenience function for easy import
async def analyze_with_gemini(resume: Resume, job_description: JobDescription) -> GeminiResponse:
    """Analyze resume with Gemini API."""
    client = GeminiClient()
    return await client.analyze_resume_match(resume, job_description)