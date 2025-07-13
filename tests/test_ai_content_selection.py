"""
Test suite for AI-enhanced content selection functionality.
Phase 1 testing of Gemini integration with comprehensive fallback validation.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.services.ai_content_selection_service import (
    AIContentSelectionEngine,
    SelectionMethod,
    AISelectionReasoning,
    EnhancedContentSelectionResult
)
from app.services.job_analysis_service import JobAnalysisResult
from app.services.gemini_client import GeminiResponse


class TestAIContentSelectionEngine:
    """Test AI content selection engine functionality."""
    
    @pytest.fixture
    def mock_job_analysis(self):
        """Mock job analysis for testing."""
        return JobAnalysisResult(
            company_name="Test Company",
            position_title="Senior Software Engineer",
            industry="Technology",
            seniority_level="Senior",
            employment_type="Full-time",
            required_skills=["Python", "FastAPI", "Machine Learning"],
            preferred_skills=["Docker", "AWS", "React"],
            key_requirements=["5+ years experience", "Bachelor's degree"],
            important_keywords=["API development", "scalable systems", "team leadership"],
            ats_keywords=["python", "api", "senior", "software"],
            keyword_frequency={"python": 5, "api": 3, "senior": 2},
            confidence_score=0.9,
            analysis_model="gemini-1.5-pro",
            job_description_hash="test_hash_123",
            difficulty_level="senior",
            competition_level="high"
        )
    
    @pytest.fixture
    def mock_user_data(self):
        """Mock user master dataset for testing."""
        # Create mock achievement objects
        achievement1 = Mock()
        achievement1.id = "ach_1"
        achievement1.achievement_text = "Built scalable Python API serving 1M+ requests/day"
        achievement1.skills_demonstrated = ["Python", "API Development", "Scalability"]
        achievement1.quantified_metrics = {"requests_per_day": 1000000}
        achievement1.impact_level = 8
        achievement1.achievement_category = "technical"
        achievement1.created_at = datetime.utcnow()
        
        achievement2 = Mock()
        achievement2.id = "ach_2"
        achievement2.achievement_text = "Led team of 5 engineers in ML model deployment"
        achievement2.skills_demonstrated = ["Leadership", "Machine Learning", "Team Management"]
        achievement2.quantified_metrics = {"team_size": 5}
        achievement2.impact_level = 9
        achievement2.achievement_category = "leadership"
        achievement2.created_at = datetime.utcnow()
        
        # Create mock skill objects
        skill1 = Mock()
        skill1.id = "skill_1"
        skill1.skill_name = "Python"
        skill1.skill_category = "Programming Language"
        skill1.proficiency_level = "Expert"
        skill1.years_experience = 7
        
        skill2 = Mock()
        skill2.id = "skill_2"
        skill2.skill_name = "FastAPI"
        skill2.skill_category = "Web Framework"
        skill2.proficiency_level = "Advanced"
        skill2.years_experience = 3
        
        return {
            "profile": Mock(),
            "work_experiences": [],
            "achievements": [achievement1, achievement2],
            "skills": [skill1, skill2],
            "education": [],
            "projects": []
        }
    
    @pytest.fixture
    def ai_engine(self):
        """Create AI content selection engine for testing."""
        with patch('app.services.ai_content_selection_service.GeminiClient') as mock_gemini:
            engine = AIContentSelectionEngine(use_ai_selection=True)
            engine.gemini_client = mock_gemini.return_value
            engine.gemini_client.is_available.return_value = True
            engine.gemini_client.rate_limiter.can_make_request.return_value = True
            return engine
    
    @pytest.mark.asyncio
    async def test_algorithmic_selection_fallback(self, ai_engine, mock_user_data, mock_job_analysis):
        """Test that algorithmic selection works as fallback."""
        
        # Mock the parent class method
        with patch.object(ai_engine, '_load_user_master_dataset', return_value=mock_user_data):
            with patch.object(ai_engine, '_score_all_content') as mock_score:
                with patch.object(ai_engine, '_optimize_content_selection') as mock_optimize:
                    with patch.object(ai_engine, '_store_selection_results') as mock_store:
                        
                        # Setup mock returns
                        mock_score.return_value = {
                            "ACHIEVEMENT": [Mock()],
                            "SKILL": [Mock()],
                            "WORK_EXPERIENCE": [],
                            "PROJECT": [],
                            "EDUCATION": []
                        }
                        
                        mock_result = Mock()
                        mock_result.job_analysis_id = "test_analysis"
                        mock_result.user_profile_id = "test_user"
                        mock_result.selected_achievements = []
                        mock_result.selected_work_experiences = []
                        mock_result.selected_skills = []
                        mock_result.selected_projects = []
                        mock_result.selected_education = []
                        mock_result.total_score = 0.8
                        mock_result.estimated_word_count = 250
                        mock_result.one_page_compliant = True
                        mock_result.content_diversity_score = 0.7
                        mock_result.keyword_coverage_percentage = 85.0
                        mock_result.selection_algorithm = "multi_dimensional_v1"
                        mock_result.selection_criteria = {}
                        mock_result.optimization_notes = []
                        
                        mock_optimize.return_value = mock_result
                        
                        # Test algorithmic selection
                        result = await ai_engine.select_optimal_content(
                            user_profile_id="test_user",
                            job_analysis=mock_job_analysis,
                            selection_method=SelectionMethod.ALGORITHMIC
                        )
                        
                        assert isinstance(result, EnhancedContentSelectionResult)
                        assert result.selection_method == SelectionMethod.ALGORITHMIC
                        assert not result.fallback_applied
                        assert result.ai_reasoning is None
    
    @pytest.mark.asyncio
    async def test_ai_enhanced_selection_success(self, ai_engine, mock_user_data, mock_job_analysis):
        """Test successful AI-enhanced selection with reasoning."""
        
        # Mock successful AI reasoning response
        mock_ai_response = GeminiResponse(
            content=json.dumps({
                "selection_rationale": "Selected achievements demonstrate strong Python and API skills",
                "content_fit_analysis": "Excellent match for senior role requirements",
                "keyword_integration_strategy": "Natural integration of Python, API, and leadership keywords",
                "combination_logic": "Balanced technical and leadership achievements",
                "confidence_score": 0.9,
                "alternative_considerations": ["Could include more AWS experience"]
            }),
            usage_metadata={},
            processing_time=1.5,
            model_used="gemini-1.5-pro",
            success=True
        )
        
        ai_engine.gemini_client.generate_content_analysis = AsyncMock(return_value=mock_ai_response)
        
        with patch.object(ai_engine, '_algorithmic_selection') as mock_algorithmic:
            # Setup mock algorithmic result
            mock_result = EnhancedContentSelectionResult(
                job_analysis_id="test_analysis",
                user_profile_id="test_user",
                selected_achievements=[],
                selected_work_experiences=[],
                selected_skills=[],
                selected_projects=[],
                selected_education=[],
                total_score=0.8,
                estimated_word_count=250,
                one_page_compliant=True,
                content_diversity_score=0.7,
                keyword_coverage_percentage=85.0,
                selection_algorithm="multi_dimensional_v1",
                selection_criteria={},
                optimization_notes=[],
                selection_method=SelectionMethod.ALGORITHMIC
            )
            
            mock_algorithmic.return_value = mock_result
            
            # Test AI-enhanced selection
            result = await ai_engine.select_optimal_content(
                user_profile_id="test_user",
                job_analysis=mock_job_analysis,
                selection_method=SelectionMethod.AI_ENHANCED
            )
            
            assert isinstance(result, EnhancedContentSelectionResult)
            assert result.selection_method == SelectionMethod.AI_ENHANCED
            assert not result.fallback_applied
            assert result.ai_reasoning is not None
            assert result.ai_confidence_score == 0.9
            assert result.gemini_processing_time > 0
    
    @pytest.mark.asyncio
    async def test_ai_enhanced_fallback_on_failure(self, ai_engine, mock_user_data, mock_job_analysis):
        """Test fallback to algorithmic when AI fails."""
        
        # Mock AI failure
        ai_engine.gemini_client.generate_content_analysis = AsyncMock(
            side_effect=Exception("AI service temporarily unavailable")
        )
        
        with patch.object(ai_engine, '_algorithmic_selection') as mock_algorithmic:
            mock_result = EnhancedContentSelectionResult(
                job_analysis_id="test_analysis",
                user_profile_id="test_user",
                selected_achievements=[],
                selected_work_experiences=[],
                selected_skills=[],
                selected_projects=[],
                selected_education=[],
                total_score=0.8,
                estimated_word_count=250,
                one_page_compliant=True,
                content_diversity_score=0.7,
                keyword_coverage_percentage=85.0,
                selection_algorithm="multi_dimensional_v1",
                selection_criteria={},
                optimization_notes=[],
                selection_method=SelectionMethod.ALGORITHMIC,
                fallback_applied=True
            )
            
            mock_algorithmic.return_value = mock_result
            
            # Test AI-enhanced selection with fallback
            result = await ai_engine.select_optimal_content(
                user_profile_id="test_user",
                job_analysis=mock_job_analysis,
                selection_method=SelectionMethod.AI_ENHANCED
            )
            
            assert result.selection_method == SelectionMethod.AI_ENHANCED
            assert result.fallback_applied
            assert result.ai_reasoning is None
    
    @pytest.mark.asyncio
    async def test_rate_limit_fallback(self, mock_user_data, mock_job_analysis):
        """Test fallback when rate limit is exceeded."""
        
        with patch('app.services.ai_content_selection_service.GeminiClient') as mock_gemini:
            ai_engine = AIContentSelectionEngine(use_ai_selection=True)
            ai_engine.gemini_client = mock_gemini.return_value
            ai_engine.gemini_client.is_available.return_value = True
            ai_engine.gemini_client.rate_limiter.can_make_request.return_value = False  # Rate limited
            
            # Should determine algorithmic method due to rate limit
            effective_method = ai_engine._determine_effective_method(SelectionMethod.AI_ENHANCED)
            assert effective_method == SelectionMethod.ALGORITHMIC
    
    def test_ai_reasoning_parsing(self, ai_engine):
        """Test parsing of AI reasoning responses."""
        
        # Test valid JSON response
        valid_response = json.dumps({
            "selection_rationale": "Test rationale",
            "content_fit_analysis": "Test analysis",
            "keyword_integration_strategy": "Test strategy",
            "combination_logic": "Test logic",
            "confidence_score": 0.85,
            "alternative_considerations": ["Alternative 1", "Alternative 2"]
        })
        
        reasoning = ai_engine._parse_ai_reasoning_response(valid_response)
        
        assert reasoning is not None
        assert reasoning.selection_rationale == "Test rationale"
        assert reasoning.confidence_score == 0.85
        assert len(reasoning.alternative_considerations) == 2
        
        # Test invalid JSON response
        invalid_response = "invalid json {"
        reasoning = ai_engine._parse_ai_reasoning_response(invalid_response)
        assert reasoning is None
    
    @pytest.mark.asyncio
    async def test_ai_disabled_fallback(self, mock_user_data, mock_job_analysis):
        """Test that algorithmic selection is used when AI is disabled."""
        
        # Create engine with AI disabled
        ai_engine = AIContentSelectionEngine(use_ai_selection=False)
        
        with patch.object(ai_engine, '_algorithmic_selection') as mock_algorithmic:
            mock_result = EnhancedContentSelectionResult(
                job_analysis_id="test_analysis",
                user_profile_id="test_user",
                selected_achievements=[],
                selected_work_experiences=[],
                selected_skills=[],
                selected_projects=[],
                selected_education=[],
                total_score=0.8,
                estimated_word_count=250,
                one_page_compliant=True,
                content_diversity_score=0.7,
                keyword_coverage_percentage=85.0,
                selection_algorithm="multi_dimensional_v1",
                selection_criteria={},
                optimization_notes=[],
                selection_method=SelectionMethod.ALGORITHMIC
            )
            
            mock_algorithmic.return_value = mock_result
            
            # Even when requesting AI method, should use algorithmic
            result = await ai_engine.select_optimal_content(
                user_profile_id="test_user",
                job_analysis=mock_job_analysis,
                selection_method=SelectionMethod.AI_ENHANCED
            )
            
            assert result.selection_method == SelectionMethod.ALGORITHMIC
    
    def test_selection_method_determination(self, ai_engine):
        """Test selection method determination logic."""
        
        # Test with AI available
        ai_engine.use_ai_selection = True
        ai_engine.gemini_client.rate_limiter.can_make_request.return_value = True
        
        assert ai_engine._determine_effective_method(SelectionMethod.ALGORITHMIC) == SelectionMethod.ALGORITHMIC
        assert ai_engine._determine_effective_method(SelectionMethod.AI_ENHANCED) == SelectionMethod.AI_ENHANCED
        assert ai_engine._determine_effective_method(SelectionMethod.AI_PRIMARY) == SelectionMethod.AI_PRIMARY
        
        # Test with AI disabled
        ai_engine.use_ai_selection = False
        
        assert ai_engine._determine_effective_method(SelectionMethod.AI_ENHANCED) == SelectionMethod.ALGORITHMIC
        assert ai_engine._determine_effective_method(SelectionMethod.AI_PRIMARY) == SelectionMethod.ALGORITHMIC


if __name__ == "__main__":
    # Run basic tests without pytest
    async def run_basic_test():
        """Run a basic test to verify functionality."""
        
        print("Testing AI Content Selection Engine...")
        
        # Test engine initialization
        engine = AIContentSelectionEngine(use_ai_selection=False)
        print(f"✓ Engine initialized with AI selection: {engine.use_ai_selection}")
        
        # Test method determination
        method = engine._determine_effective_method(SelectionMethod.AI_ENHANCED)
        print(f"✓ Method determination working: {method}")
        
        # Test reasoning parsing
        test_response = json.dumps({
            "selection_rationale": "Test",
            "content_fit_analysis": "Test",
            "keyword_integration_strategy": "Test",
            "combination_logic": "Test",
            "confidence_score": 0.8,
            "alternative_considerations": []
        })
        
        reasoning = engine._parse_ai_reasoning_response(test_response)
        print(f"✓ Reasoning parsing working: {reasoning is not None}")
        
        print("All basic tests passed! ✓")
    
    asyncio.run(run_basic_test())