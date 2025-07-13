"""
Job Description Analysis Engine for TailerAI v2.0.
Implements PRD-004: Intelligent job description analysis using AI and NLP.
Following project blueprint best practices for AI integration and caching.
"""

import logging
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.database import JobAnalysis
from app.models.entities import JobDescription, JobRequirement
from app.services.database_service import db_service, DatabaseError
from app.services.gemini_client import GeminiClient, GeminiResponse
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class JobAnalysisResult:
    """Comprehensive job description analysis result."""
    # Basic job information
    company_name: str
    position_title: str
    industry: str
    seniority_level: str
    employment_type: str
    
    # Skills and requirements
    required_skills: List[str]
    preferred_skills: List[str]
    key_requirements: List[str]
    
    # ATS optimization
    important_keywords: List[str]
    ats_keywords: List[str]
    keyword_frequency: Dict[str, int]
    
    # Analysis metadata
    confidence_score: float
    analysis_model: str
    job_description_hash: str
    
    # Performance insights
    difficulty_level: str  # "entry", "mid", "senior", "expert"
    competition_level: str  # "low", "medium", "high"
    
    # Optional fields (must come after required fields)
    analysis_id: Optional[str] = None  # Database ID for foreign key references
    salary_range_estimate: Optional[str] = None
    
    def to_job_description_entity(self, raw_text: str) -> JobDescription:
        """Convert to JobDescription entity for compatibility."""
        requirements = []
        
        # Add required skills as requirements
        for skill in self.required_skills:
            requirements.append(JobRequirement(
                text=skill,
                category="technical",
                importance="required",
                keywords=[skill]
            ))
        
        # Add preferred skills as requirements
        for skill in self.preferred_skills:
            requirements.append(JobRequirement(
                text=skill,
                category="technical",
                importance="preferred",
                keywords=[skill]
            ))
        
        return JobDescription(
            raw_text=raw_text,
            company=self.company_name,
            position=self.position_title,
            requirements=requirements,
            skills_needed=self.required_skills + self.preferred_skills,
            industry=self.industry,
            seniority_level=self.seniority_level
        )


class JobDescriptionAnalysisError(Exception):
    """Custom exception for job description analysis operations."""
    pass


class JobDescriptionAnalyzer:
    """
    Comprehensive job description analysis service.
    Implements intelligent analysis with AI and caching for performance.
    """
    
    def __init__(self):
        self.logger = logger
        self.gemini_client = GeminiClient()
        self.cache_duration_hours = 168  # 1 week cache
    
    async def analyze_job_description(self, job_text: str, job_url: Optional[str] = None) -> JobAnalysisResult:
        """
        Analyze job description with AI and return comprehensive results.
        Uses caching to avoid redundant API calls.
        """
        try:
            # Generate hash for caching
            job_hash = self._generate_job_hash(job_text)
            
            # Check cache first
            cached_analysis = self._get_cached_analysis(job_hash)
            if cached_analysis:
                self.logger.info(f"Using cached analysis for job hash: {job_hash[:8]}...")
                return cached_analysis
            
            # Perform new analysis
            self.logger.info(f"Performing new job analysis for hash: {job_hash[:8]}...")
            analysis_result = await self._perform_ai_analysis(job_text)
            analysis_result.job_description_hash = job_hash
            
            # Cache the results and get database ID
            analysis_id = self._cache_analysis_results(analysis_result, job_text)
            analysis_result.analysis_id = analysis_id
            
            self.logger.info(f"Job analysis completed successfully: {analysis_result.position_title} at {analysis_result.company_name}")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"Job analysis failed: {str(e)}")
            raise JobDescriptionAnalysisError(f"Failed to analyze job description: {str(e)}")
    
    async def _perform_ai_analysis(self, job_text: str) -> JobAnalysisResult:
        """Perform AI-powered job description analysis using Gemini."""
        try:
            # Create analysis prompt
            prompt = self._create_job_analysis_prompt(job_text)
            
            # Make Gemini API call
            response = await self._call_gemini_api(prompt)
            
            if not response.success:
                raise JobDescriptionAnalysisError(f"AI analysis failed: {response.error_message}")
            
            # Parse AI response
            analysis_data = self._parse_ai_response(response.content)
            
            # Create analysis result
            return JobAnalysisResult(
                company_name=analysis_data.get("company_name", ""),
                position_title=analysis_data.get("position_title", ""),
                industry=analysis_data.get("industry", ""),
                seniority_level=analysis_data.get("seniority_level", ""),
                employment_type=analysis_data.get("employment_type", "full_time"),
                required_skills=analysis_data.get("required_skills", []),
                preferred_skills=analysis_data.get("preferred_skills", []),
                key_requirements=analysis_data.get("key_requirements", []),
                important_keywords=analysis_data.get("important_keywords", []),
                ats_keywords=analysis_data.get("ats_keywords", []),
                keyword_frequency=analysis_data.get("keyword_frequency", {}),
                confidence_score=analysis_data.get("confidence_score", 0.0),
                analysis_model="gemini-1.5-pro",
                job_description_hash="",  # Will be set by caller
                difficulty_level=analysis_data.get("difficulty_level", "mid"),
                competition_level=analysis_data.get("competition_level", "medium"),
                salary_range_estimate=analysis_data.get("salary_range_estimate")
            )
            
        except Exception as e:
            self.logger.error(f"AI analysis failed: {str(e)}")
            raise JobDescriptionAnalysisError(f"AI analysis error: {str(e)}")
    
    def _create_job_analysis_prompt(self, job_text: str) -> str:
        """Create comprehensive job analysis prompt for Gemini."""
        return f"""
You are an expert job market analyst and ATS specialist. Analyze this job description comprehensively and extract structured information for resume optimization.

**JOB DESCRIPTION:**
{job_text}

**ANALYSIS TASK:**
Provide comprehensive analysis in the following JSON format:

{{
    "company_name": "<company name>",
    "position_title": "<exact job title>",
    "industry": "<industry sector>",
    "seniority_level": "entry|mid|senior|executive",
    "employment_type": "full_time|part_time|contract|freelance|internship",
    "required_skills": [
        "skill1", "skill2", ...
    ],
    "preferred_skills": [
        "skill1", "skill2", ...
    ],
    "key_requirements": [
        "requirement1", "requirement2", ...
    ],
    "important_keywords": [
        "keyword1", "keyword2", ...
    ],
    "ats_keywords": [
        "ats_keyword1", "ats_keyword2", ...
    ],
    "keyword_frequency": {{
        "keyword1": 3,
        "keyword2": 2,
        ...
    }},
    "confidence_score": <0.0-1.0>,
    "difficulty_level": "entry|mid|senior|expert",
    "competition_level": "low|medium|high",
    "salary_range_estimate": "<salary range or null>"
}}

**ANALYSIS GUIDELINES:**

1. **Skills Classification:**
   - required_skills: Must-have technical and core skills
   - preferred_skills: Nice-to-have or bonus skills
   - Extract both technical and soft skills

2. **Keyword Extraction:**
   - important_keywords: Most critical terms for this role
   - ats_keywords: Terms that ATS systems prioritize
   - keyword_frequency: Count of key term appearances

3. **Requirements Analysis:**
   - key_requirements: Core job responsibilities and qualifications
   - Focus on experience level, education, certifications

4. **Classification:**
   - seniority_level: Based on years of experience and responsibility
   - difficulty_level: Technical complexity and skill requirements
   - competition_level: Market demand and candidate pool

5. **Quality Standards:**
   - confidence_score: Your confidence in the analysis accuracy
   - Be precise with company names and job titles
   - Use consistent terminology for industries and skills

**IMPORTANT:**
- Extract information exactly as stated, don't infer beyond the text
- Prioritize ATS-friendly keywords that appear multiple times
- Focus on quantifiable requirements (X years experience, specific technologies)
- Return only valid JSON without additional commentary

Respond only with valid JSON.
"""
    
    async def _call_gemini_api(self, prompt: str) -> GeminiResponse:
        """Make API call to Gemini with proper error handling."""
        try:
            # Use the existing Gemini client's generation method
            import asyncio
            import time
            
            if not self.gemini_client.rate_limiter.can_make_request():
                wait_time = self.gemini_client.rate_limiter.get_wait_time()
                raise JobDescriptionAnalysisError(f"Rate limit exceeded. Wait {wait_time} seconds.")
            
            start_time = time.time()
            
            # Configure for job analysis  
            generation_config = {
                "temperature": 0.1,  # Low temperature for consistent analysis
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 3000
            }
            
            response = await asyncio.to_thread(
                self.gemini_client.model.generate_content,
                prompt,
                generation_config=generation_config
            )
            
            processing_time = time.time() - start_time
            self.gemini_client.rate_limiter.record_request()
            
            # Log API usage
            self.gemini_client._log_api_usage("job_analysis", processing_time, True)
            
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
                model_used="gemini-1.5-pro",
                success=True
            )
            
        except Exception as e:
            processing_time = time.time() - start_time if 'start_time' in locals() else 0
            self.gemini_client._log_api_usage("job_analysis", processing_time, False, str(e))
            
            return GeminiResponse(
                content="",
                usage_metadata={},
                processing_time=processing_time,
                model_used="gemini-1.5-pro",
                success=False,
                error_message=str(e)
            )
    
    def _parse_ai_response(self, response_content: str) -> Dict[str, Any]:
        """Parse and validate AI response JSON."""
        try:
            # Debug logging
            self.logger.debug(f"AI Response length: {len(response_content)}")
            self.logger.debug(f"AI Response preview: {response_content[:200]}...")
            
            if not response_content or response_content.strip() == "":
                self.logger.error("Received empty response from AI")
                raise JobDescriptionAnalysisError("Empty response from AI service")
            
            # Clean up response content - remove markdown code blocks if present
            cleaned_content = response_content.strip()
            if cleaned_content.startswith("```json"):
                # Remove ```json from start and ``` from end
                cleaned_content = cleaned_content[7:]  # Remove ```json
                if cleaned_content.endswith("```"):
                    cleaned_content = cleaned_content[:-3]  # Remove trailing ```
                cleaned_content = cleaned_content.strip()
            elif cleaned_content.startswith("```"):
                # Remove generic code blocks
                lines = cleaned_content.split('\n')
                if lines[0].strip() == "```" or lines[0].strip().startswith("```"):
                    lines = lines[1:]  # Remove first line
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]  # Remove last line
                cleaned_content = '\n'.join(lines).strip()
            
            self.logger.debug(f"Cleaned content: {cleaned_content[:200]}...")
            
            data = json.loads(cleaned_content)
            
            # Validate required fields
            required_fields = [
                "company_name", "position_title", "industry", "seniority_level",
                "required_skills", "preferred_skills", "important_keywords", "confidence_score"
            ]
            
            for field in required_fields:
                if field not in data:
                    self.logger.warning(f"Missing required field in AI response: {field}")
                    data[field] = [] if field.endswith("_skills") or field.endswith("_keywords") else ""
            
            # Ensure numeric fields
            data["confidence_score"] = float(data.get("confidence_score", 0.0))
            
            # Ensure list fields are lists
            list_fields = ["required_skills", "preferred_skills", "key_requirements", 
                          "important_keywords", "ats_keywords"]
            for field in list_fields:
                if not isinstance(data.get(field), list):
                    data[field] = []
            
            # Ensure dict fields are dicts
            if not isinstance(data.get("keyword_frequency"), dict):
                data["keyword_frequency"] = {}
            
            return data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse AI response JSON: {e}")
            self.logger.error(f"Raw response content: '{response_content}'")
            self.logger.error(f"Cleaned content: '{cleaned_content}'" if 'cleaned_content' in locals() else "No cleaned content")
            self.logger.error(f"Response type: {type(response_content)}")
            raise JobDescriptionAnalysisError(f"Invalid AI response format: {e}")
    
    def _generate_job_hash(self, job_text: str) -> str:
        """Generate SHA256 hash of job description for caching."""
        # Normalize text for consistent hashing
        normalized_text = job_text.strip().lower()
        return hashlib.sha256(normalized_text.encode('utf-8')).hexdigest()
    
    def _get_cached_analysis(self, job_hash: str) -> Optional[JobAnalysisResult]:
        """Retrieve cached analysis if available and not expired."""
        try:
            with db_service.get_session() as session:
                # Query for cached analysis
                cached = session.query(JobAnalysis).filter_by(
                    job_description_hash=job_hash
                ).first()
                
                if not cached:
                    return None
                
                # Check if cache is still valid
                cache_expiry = cached.created_at + timedelta(hours=self.cache_duration_hours)
                if datetime.utcnow() > cache_expiry:
                    self.logger.info(f"Cache expired for job hash: {job_hash[:8]}...")
                    return None
                
                # Update usage tracking
                cached.usage_count += 1
                cached.last_used = datetime.utcnow()
                session.commit()
                
                # Convert database model to result object
                return JobAnalysisResult(
                    company_name=cached.company_name or "",
                    position_title=cached.position_title or "",
                    industry=cached.industry or "",
                    seniority_level=cached.seniority_level or "",
                    employment_type=cached.employment_type or "full_time",
                    required_skills=cached.required_skills or [],
                    preferred_skills=cached.preferred_skills or [],
                    key_requirements=cached.key_requirements or [],
                    important_keywords=cached.important_keywords or [],
                    ats_keywords=cached.ats_keywords or [],
                    keyword_frequency=cached.keyword_frequency or {},
                    confidence_score=cached.confidence_score or 0.0,
                    analysis_model=cached.analysis_model or "gemini-1.5-pro",
                    job_description_hash=cached.job_description_hash,
                    analysis_id=str(cached.id),  # Include database ID
                    difficulty_level="mid",  # Default for legacy data
                    competition_level="medium"  # Default for legacy data
                )
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error retrieving cached analysis: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error retrieving cached analysis: {e}")
            return None
    
    def _cache_analysis_results(self, analysis: JobAnalysisResult, job_text: str) -> Optional[str]:
        """Cache analysis results to database."""
        try:
            with db_service.get_session() as session:
                # Create database record
                job_analysis = JobAnalysis(
                    job_description_hash=analysis.job_description_hash,
                    company_name=analysis.company_name,
                    position_title=analysis.position_title,
                    required_skills=analysis.required_skills,
                    preferred_skills=analysis.preferred_skills,
                    key_requirements=analysis.key_requirements,
                    industry=analysis.industry,
                    seniority_level=analysis.seniority_level,
                    employment_type=analysis.employment_type,
                    important_keywords=analysis.important_keywords,
                    keyword_frequency=analysis.keyword_frequency,
                    ats_keywords=analysis.ats_keywords,
                    confidence_score=analysis.confidence_score,
                    analysis_model=analysis.analysis_model,
                    usage_count=1,
                    last_used=datetime.utcnow()
                )
                
                session.add(job_analysis)
                session.commit()
                session.refresh(job_analysis)
                
                self.logger.info(f"Cached job analysis: {analysis.position_title} at {analysis.company_name}")
                return str(job_analysis.id)
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error caching analysis: {e}")
            # Don't raise exception - caching failure shouldn't break analysis
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error caching analysis: {e}")
            return None
    
    def get_analysis_stats(self) -> Dict[str, Any]:
        """Get statistics about job analysis usage."""
        try:
            with db_service.get_session() as session:
                total_analyses = session.query(JobAnalysis).count()
                
                # Recent analyses (last 7 days)
                week_ago = datetime.utcnow() - timedelta(days=7)
                recent_analyses = session.query(JobAnalysis).filter(
                    JobAnalysis.created_at >= week_ago
                ).count()
                
                # Most analyzed positions
                from sqlalchemy import func
                top_positions = session.query(
                    JobAnalysis.position_title,
                    func.count(JobAnalysis.id).label('count')
                ).group_by(JobAnalysis.position_title).order_by(
                    func.count(JobAnalysis.id).desc()
                ).limit(5).all()
                
                return {
                    "total_analyses": total_analyses,
                    "analyses_this_week": recent_analyses,
                    "cache_hit_rate": self._calculate_cache_hit_rate(),
                    "top_positions": [{"position": pos, "count": count} for pos, count in top_positions],
                    "gemini_usage": self.gemini_client.get_usage_stats()
                }
                
        except Exception as e:
            self.logger.error(f"Error getting analysis stats: {e}")
            return {"error": str(e)}
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate from recent usage."""
        try:
            with db_service.get_session() as session:
                # Get analyses from last 24 hours
                day_ago = datetime.utcnow() - timedelta(days=1)
                recent_analyses = session.query(JobAnalysis).filter(
                    JobAnalysis.last_used >= day_ago
                ).all()
                
                if not recent_analyses:
                    return 0.0
                
                cache_hits = sum(1 for analysis in recent_analyses if analysis.usage_count > 1)
                return cache_hits / len(recent_analyses)
                
        except Exception as e:
            self.logger.error(f"Error calculating cache hit rate: {e}")
            return 0.0


# Global service instance
job_analyzer = JobDescriptionAnalyzer()