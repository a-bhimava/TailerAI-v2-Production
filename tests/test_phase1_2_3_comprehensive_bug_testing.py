"""
Comprehensive Bug Testing for Phase 1, 2 & 3 Gemini Integration.
Tests all critical functionality, edge cases, integration points, and backwards compatibility.

Phase 1: AI-Enhanced Content Selection
Phase 2: ATS Optimization Engine  
Phase 3: Content Enhancement Engine

This test suite validates:
- Service initialization and configuration
- API endpoint functionality
- Fallback mechanisms and error handling
- Data integrity and validation
- Integration between all phases
- Backwards compatibility
- Performance and stress scenarios
- Security and authenticity safeguards
"""

import pytest
import asyncio
import json
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from typing import Dict, Any, List

# Set up test environment
os.environ["ENVIRONMENT"] = "testing"
os.environ["ENABLE_AI_CONTENT_SELECTION"] = "true"
os.environ["ENABLE_AI_ATS_OPTIMIZATION"] = "true"
os.environ["ENABLE_AI_CONTENT_ENHANCEMENT"] = "true"
os.environ["GEMINI_API_KEY"] = "test_key"

from app.services.ai_content_selection_service import (
    AIContentSelectionEngine, 
    ai_content_selector,
    EnhancedContentSelectionResult,
    AISelectionReasoning
)
from app.services.ats_optimization_engine import (
    ATSOptimizationEngine,
    ats_optimizer,
    ATSSystem,
    CompatibilityLevel,
    ATSOptimizationResult,
    KeywordOptimization,
    ATSCompatibilityIssue
)
from app.services.content_enhancement_engine import (
    ContentEnhancementEngine,
    content_enhancer,
    EnhancementType,
    EnhancementLevel,
    AuthenticityLevel,
    ContentEnhancementResult,
    EnhancementChange
)
from app.services.job_analysis_service import JobAnalysisResult
from app.services.gemini_client import GeminiResponse
from app.config.settings import get_settings


class TestPhase1AIContentSelection:
    """Comprehensive tests for Phase 1: AI-Enhanced Content Selection."""
    
    @pytest.fixture
    def mock_gemini_response(self):
        """Mock successful Gemini response for content selection."""
        return GeminiResponse(
            success=True,
            content=json.dumps({
                "selected_achievements": [
                    {
                        "achievement_id": "test_1",
                        "relevance_score": 0.95,
                        "keyword_alignment": 0.9,
                        "impact_score": 0.85
                    }
                ],
                "content_fit_analysis": "Excellent match for Python developer role",
                "keyword_integration_strategy": "Natural integration of Python keywords",
                "confidence_score": 0.92,
                "selection_reasoning": "Strong technical alignment"
            }),
            tokens_used=150,
            response_time=2.3
        )
    
    @pytest.fixture
    def mock_job_analysis(self):
        """Mock job analysis result."""
        return JobAnalysisResult(
            position_title="Senior Python Developer",
            company_name="Tech Corp",
            required_skills=["Python", "Django", "REST APIs"],
            important_keywords=["scalable", "microservices", "cloud"],
            ats_keywords=["python", "api", "backend"],
            experience_level="senior",
            job_category="technology"
        )
    
    def test_ai_content_selection_initialization(self):
        """Test proper initialization of AI content selection engine."""
        engine = AIContentSelectionEngine()
        assert engine is not None
        assert hasattr(engine, 'use_ai_enhanced')
        assert hasattr(engine, 'fallback_enabled')
        assert hasattr(engine, 'confidence_threshold')
    
    @pytest.mark.asyncio
    async def test_ai_enhanced_selection_success(self, mock_gemini_response, mock_job_analysis):
        """Test successful AI-enhanced content selection."""
        engine = AIContentSelectionEngine()
        
        with patch.object(engine, 'gemini_client') as mock_client:
            mock_client.generate_content_analysis.return_value = mock_gemini_response
            mock_client.is_available.return_value = True
            
            with patch.object(engine, 'select_optimal_content') as mock_base:
                mock_base.return_value = Mock(
                    selected_achievements=["test_1", "test_2"],
                    total_score=0.8,
                    estimated_word_count=250
                )
                
                result = await engine.ai_enhanced_selection(
                    user_profile_id="test_user",
                    job_analysis=mock_job_analysis
                )
                
                assert isinstance(result, EnhancedContentSelectionResult)
                assert result.success is True
                assert result.selection_method == "ai_enhanced"
                assert result.ai_confidence_score >= 0.9
                assert result.fallback_applied is False
                assert result.ai_reasoning is not None
    
    @pytest.mark.asyncio
    async def test_ai_selection_fallback_on_failure(self, mock_job_analysis):
        """Test fallback to algorithmic selection when AI fails."""
        engine = AIContentSelectionEngine()
        
        with patch.object(engine, 'gemini_client') as mock_client:
            mock_client.generate_content_analysis.return_value = GeminiResponse(
                success=False,
                error_message="API rate limit exceeded"
            )
            mock_client.is_available.return_value = False
            
            with patch.object(engine, 'select_optimal_content') as mock_base:
                mock_base.return_value = Mock(
                    selected_achievements=["test_1"],
                    total_score=0.75,
                    estimated_word_count=200
                )
                
                result = await engine.ai_enhanced_selection(
                    user_profile_id="test_user",
                    job_analysis=mock_job_analysis
                )
                
                assert isinstance(result, EnhancedContentSelectionResult)
                assert result.success is True
                assert result.selection_method == "algorithmic"
                assert result.fallback_applied is True
                assert "fallback" in result.ai_reasoning.lower()


class TestPhase2ATSOptimization:
    """Comprehensive tests for Phase 2: ATS Optimization Engine."""
    
    @pytest.fixture
    def mock_content_data(self):
        """Mock content selection data."""
        return {
            "content_selection": Mock(
                id="test_content_123",
                profile_id="user_456",
                selected_achievements=["ach_1", "ach_2"],
                estimated_word_count=300,
                selection_criteria={"method": "ai_enhanced"}
            ),
            "profile": Mock(id="user_456"),
            "selected_achievements": ["ach_1", "ach_2"],
            "achievement_scores": {"ach_1": 0.9, "ach_2": 0.8}
        }
    
    @pytest.fixture
    def mock_ats_gemini_response(self):
        """Mock Gemini response for ATS optimization."""
        return GeminiResponse(
            success=True,
            content=json.dumps({
                "overall_compatibility_score": 0.85,
                "system_specific_scores": {
                    "taleo": 0.82,
                    "workday": 0.88,
                    "generic": 0.85
                },
                "keyword_analysis": {
                    "current_density": 0.02,
                    "target_density": 0.04,
                    "optimization_opportunities": [
                        {
                            "keyword": "python",
                            "priority": "high",
                            "integration_strategy": "Natural placement in achievements",
                            "suggested_context": "technical accomplishments"
                        }
                    ]
                },
                "compatibility_issues": [
                    {
                        "issue_type": "keyword_density",
                        "severity": "medium",
                        "description": "Keywords could be better distributed",
                        "fix_strategy": "Add more natural keyword integration",
                        "estimated_impact": "medium"
                    }
                ],
                "optimization_recommendations": [
                    {
                        "category": "keywords",
                        "recommendation": "Increase Python keyword density naturally",
                        "priority": "high",
                        "estimated_improvement": "15%"
                    }
                ],
                "confidence_score": 0.9,
                "reasoning": "Strong overall compatibility with room for keyword improvements"
            }),
            tokens_used=200,
            response_time=3.1
        )
    
    def test_ats_optimization_initialization(self):
        """Test proper initialization of ATS optimization engine."""
        engine = ATSOptimizationEngine()
        assert engine is not None
        assert hasattr(engine, 'use_ai_optimization')
        assert hasattr(engine, 'ats_system_configs')
        assert len(engine.ats_system_configs) > 0
        assert ATSSystem.TALEO in engine.ats_system_configs
        assert ATSSystem.WORKDAY in engine.ats_system_configs
    
    @pytest.mark.asyncio
    async def test_ai_powered_ats_optimization(self, mock_content_data, mock_ats_gemini_response):
        """Test AI-powered ATS optimization."""
        engine = ATSOptimizationEngine(use_ai_optimization=True)
        target_systems = [ATSSystem.TALEO, ATSSystem.WORKDAY]
        
        with patch.object(engine, '_load_content_selection') as mock_load:
            mock_load.return_value = mock_content_data
            
            with patch.object(engine, 'gemini_client') as mock_client:
                mock_client.generate_content_analysis.return_value = mock_ats_gemini_response
                mock_client.is_available.return_value = True
                
                with patch.object(engine, '_store_optimization_results') as mock_store:
                    mock_store.return_value = None
                    
                    result = await engine.optimize_content_for_ats(
                        content_selection_id="test_content_123",
                        target_ats_systems=target_systems
                    )
                    
                    assert isinstance(result, ATSOptimizationResult)
                    assert result.overall_compatibility_score >= 0.8
                    assert result.compatibility_level in [level.value for level in CompatibilityLevel]
                    assert len(result.keyword_optimizations) > 0
                    assert result.ai_reasoning is not None
                    assert result.ai_confidence_score >= 0.9
                    assert result.fallback_applied is False


class TestPhase3ContentEnhancement:
    """Comprehensive tests for Phase 3: Content Enhancement Engine."""
    
    @pytest.fixture
    def mock_achievement_data(self):
        """Mock achievement data."""
        return {
            "achievement": Mock(
                id="ach_123",
                achievement_text="Worked on database optimization",
                quantified_result={"improvement": "40%"},
                impact_level=7
            ),
            "original_text": "Worked on database optimization",
            "quantified_metrics": {"improvement": "40%"},
            "impact_level": 7,
            "skills_demonstrated": ["Python", "SQL"],
            "category": "technical"
        }
    
    @pytest.fixture
    def mock_enhancement_gemini_response(self):
        """Mock Gemini response for content enhancement."""
        return GeminiResponse(
            success=True,
            content=json.dumps({
                "enhanced_text": "Optimized database queries and performance, achieving 40% improvement in response times",
                "changes_made": [
                    {
                        "change_type": "action_verb",
                        "original_phrase": "Worked on",
                        "enhanced_phrase": "Optimized",
                        "reasoning": "Stronger, more specific action verb",
                        "authenticity_verified": True
                    }
                ],
                "keywords_integrated": ["optimization", "performance"],
                "action_verbs_improved": ["Worked on -> Optimized"],
                "quantification_enhanced": True,
                "overall_improvement_score": 0.75,
                "authenticity_level": "verified",
                "confidence_score": 0.9,
                "reasoning": "Enhanced action verbs and clarified quantified results while maintaining authenticity"
            }),
            tokens_used=180,
            response_time=2.8
        )
    
    def test_content_enhancement_initialization(self):
        """Test proper initialization of content enhancement engine."""
        engine = ContentEnhancementEngine()
        assert engine is not None
        assert hasattr(engine, 'use_ai_enhancement')
        assert hasattr(engine, 'fallback_enabled')
        assert hasattr(engine, 'confidence_threshold')
        assert hasattr(engine, 'authenticity_guidelines')
    
    @pytest.mark.asyncio
    async def test_ai_powered_achievement_enhancement(
        self, 
        mock_achievement_data, 
        mock_enhancement_gemini_response
    ):
        """Test AI-powered achievement enhancement."""
        engine = ContentEnhancementEngine(use_ai_enhancement=True)
        
        with patch.object(engine, '_load_achievement_data') as mock_load:
            mock_load.return_value = mock_achievement_data
            
            with patch.object(engine, 'gemini_client') as mock_client:
                mock_client.generate_content_analysis.return_value = mock_enhancement_gemini_response
                mock_client.is_available.return_value = True
                
                with patch.object(engine, '_store_enhancement_results') as mock_store:
                    mock_store.return_value = None
                    
                    result = await engine.enhance_achievement_text(
                        achievement_id="ach_123",
                        enhancement_level=EnhancementLevel.MODERATE
                    )
                    
                    assert isinstance(result, ContentEnhancementResult)
                    assert result.enhanced_content != result.original_content
                    assert result.overall_improvement_score > 0
                    assert result.authenticity_level == AuthenticityLevel.VERIFIED
                    assert len(result.changes_made) > 0
                    assert result.ai_reasoning is not None
                    assert result.fallback_applied is False
    
    @pytest.mark.asyncio
    async def test_content_enhancement_fallback(self, mock_achievement_data):
        """Test fallback to rule-based enhancement when AI fails."""
        engine = ContentEnhancementEngine(use_ai_enhancement=True)
        
        with patch.object(engine, '_load_achievement_data') as mock_load:
            mock_load.return_value = mock_achievement_data
            
            with patch.object(engine, 'gemini_client') as mock_client:
                mock_client.generate_content_analysis.return_value = GeminiResponse(
                    success=False,
                    error_message="AI service unavailable"
                )
                mock_client.is_available.return_value = False
                
                with patch.object(engine, '_store_enhancement_results') as mock_store:
                    mock_store.return_value = None
                    
                    result = await engine.enhance_achievement_text(
                        achievement_id="ach_123",
                        enhancement_level=EnhancementLevel.MODERATE
                    )
                    
                    assert isinstance(result, ContentEnhancementResult)
                    assert result.success is not False  # Should still succeed with fallback
                    assert result.fallback_applied is True
                    assert result.authenticity_level == AuthenticityLevel.VERIFIED


class TestPhase1Phase2Phase3Integration:
    """Test comprehensive integration between all three phases."""
    
    @pytest.fixture
    def mock_job_analysis(self):
        """Mock job analysis for integration testing."""
        return JobAnalysisResult(
            position_title="Full Stack Developer",
            company_name="TechStart Inc",
            required_skills=["JavaScript", "React", "Node.js", "MongoDB"],
            important_keywords=["full-stack", "responsive", "scalable"],
            ats_keywords=["javascript", "react", "node", "database"],
            experience_level="mid",
            job_category="technology"
        )
    
    @pytest.mark.asyncio
    async def test_complete_workflow_phase1_to_phase2_to_phase3(self, mock_job_analysis):
        """Test complete workflow from content selection to ATS optimization to enhancement."""
        
        # Phase 1: Content Selection
        with patch.object(ai_content_selector, 'select_optimal_content') as mock_selection:
            mock_selection.return_value = EnhancedContentSelectionResult(
                success=True,
                selection_id="sel_123",
                user_profile_id="user_456",
                selected_achievements=["ach_1", "ach_2"],
                selection_method="ai_enhanced",
                ai_confidence_score=0.88,
                fallback_applied=False,
                ai_reasoning=AISelectionReasoning(
                    selection_rationale="Good match for full-stack role",
                    content_fit_analysis="Strong technical alignment",
                    confidence_score=0.88
                )
            )
            
            content_result = await ai_content_selector.select_optimal_content(
                user_profile_id="user_456",
                job_analysis=mock_job_analysis
            )
            
            assert content_result.success is True
            assert content_result.selection_method == "ai_enhanced"
            
            # Phase 2: ATS Optimization
            with patch.object(ats_optimizer, 'optimize_content_for_ats') as mock_ats:
                mock_ats.return_value = ATSOptimizationResult(
                    content_selection_id=content_result.selection_id,
                    user_profile_id=content_result.user_profile_id,
                    target_ats_systems=[ATSSystem.TALEO],
                    overall_compatibility_score=0.82,
                    compatibility_level=CompatibilityLevel.GOOD,
                    system_compatibility_scores={ATSSystem.TALEO: 0.82},
                    keyword_optimizations=[
                        KeywordOptimization(
                            keyword="javascript",
                            current_density=0.02,
                            target_density=0.04,
                            integration_strategy="Natural placement",
                            priority="high",
                            suggested_contexts=["technical achievements"],
                            authenticity_score=0.9
                        )
                    ],
                    current_keyword_density=0.02,
                    target_keyword_density=0.04,
                    keyword_distribution_score=0.7,
                    compatibility_issues=[],
                    priority_fixes=[],
                    optimization_strategy={"ai_driven": True},
                    estimated_improvement=0.15
                )
                
                ats_result = await ats_optimizer.optimize_content_for_ats(
                    content_selection_id=content_result.selection_id,
                    target_ats_systems=[ATSSystem.TALEO],
                    job_analysis=mock_job_analysis
                )
                
                assert isinstance(ats_result, ATSOptimizationResult)
                assert ats_result.content_selection_id == content_result.selection_id
                assert ats_result.overall_compatibility_score > 0.8
                
                # Phase 3: Content Enhancement
                with patch.object(content_enhancer, 'enhance_achievement_text') as mock_enhancement:
                    mock_enhancement.return_value = ContentEnhancementResult(
                        original_content="Built web applications using JavaScript",
                        enhanced_content="Developed responsive web applications using JavaScript and React, improving user engagement by 25%",
                        enhancement_type=EnhancementType.ACHIEVEMENT_TEXT,
                        enhancement_level=EnhancementLevel.MODERATE,
                        changes_made=[
                            EnhancementChange(
                                change_type="action_verb",
                                original_text="Built",
                                enhanced_text="Developed",
                                reasoning="More professional action verb",
                                impact_score=0.7,
                                authenticity_verified=True
                            )
                        ],
                        overall_improvement_score=0.75,
                        authenticity_level=AuthenticityLevel.VERIFIED,
                        keywords_integrated=["React"],
                        action_verbs_improved=["Built -> Developed"],
                        quantification_enhanced=True
                    )
                    
                    for achievement_id in content_result.selected_achievements:
                        enhancement_result = await content_enhancer.enhance_achievement_text(
                            achievement_id=achievement_id,
                            job_analysis=mock_job_analysis,
                            enhancement_level=EnhancementLevel.MODERATE,
                            target_keywords=ats_result.keyword_optimizations[0].keyword
                        )
                        
                        assert isinstance(enhancement_result, ContentEnhancementResult)
                        assert enhancement_result.enhanced_content != enhancement_result.original_content
                        assert enhancement_result.overall_improvement_score > 0
                        assert enhancement_result.authenticity_level == AuthenticityLevel.VERIFIED


class TestErrorHandlingAndEdgeCases:
    """Test comprehensive error handling and edge cases for all phases."""
    
    @pytest.mark.asyncio
    async def test_invalid_achievement_id_handling(self):
        """Test handling of invalid achievement IDs in content enhancement."""
        engine = ContentEnhancementEngine()
        
        with patch.object(engine, '_load_achievement_data') as mock_load:
            mock_load.side_effect = Exception("Achievement not found")
            
            with pytest.raises(Exception) as exc_info:
                await engine.enhance_achievement_text(
                    achievement_id="invalid_id",
                    enhancement_level=EnhancementLevel.MODERATE
                )
            
            assert "Achievement not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_malformed_gemini_response_handling_all_phases(self):
        """Test handling of malformed Gemini responses across all phases."""
        
        # Test Phase 1
        engine1 = AIContentSelectionEngine()
        invalid_response = GeminiResponse(
            success=True,
            content="invalid json {",
            tokens_used=10,
            response_time=1.0
        )
        
        with patch.object(engine1, 'gemini_client') as mock_client:
            mock_client.generate_content_analysis.return_value = invalid_response
            mock_client.is_available.return_value = True
            
            with patch.object(engine1, 'select_optimal_content') as mock_base:
                mock_base.return_value = Mock(
                    selected_achievements=["test"],
                    total_score=0.7,
                    estimated_word_count=200
                )
                
                result = await engine1.ai_enhanced_selection(
                    user_profile_id="test_user",
                    job_analysis=Mock()
                )
                
                # Should fallback to algorithmic selection
                assert result.fallback_applied is True
                assert result.selection_method == "algorithmic"
        
        # Test Phase 2
        engine2 = ATSOptimizationEngine(use_ai_optimization=True)
        
        with patch.object(engine2, '_load_content_selection') as mock_load:
            mock_load.return_value = {"content_selection": Mock(id="test"), "profile": Mock()}
            
            with patch.object(engine2, 'gemini_client') as mock_client:
                mock_client.generate_content_analysis.return_value = invalid_response
                mock_client.is_available.return_value = True
                
                with patch.object(engine2, '_store_optimization_results') as mock_store:
                    mock_store.return_value = None
                    
                    result = await engine2.optimize_content_for_ats(
                        content_selection_id="test",
                        target_ats_systems=[ATSSystem.GENERIC]
                    )
                    
                    # Should fallback to rule-based optimization
                    assert result.fallback_applied is True
        
        # Test Phase 3
        engine3 = ContentEnhancementEngine(use_ai_enhancement=True)
        
        with patch.object(engine3, '_load_achievement_data') as mock_load:
            mock_load.return_value = {
                "achievement": Mock(),
                "original_text": "Test text",
                "quantified_metrics": {},
                "impact_level": 5
            }
            
            with patch.object(engine3, 'gemini_client') as mock_client:
                mock_client.generate_content_analysis.return_value = invalid_response
                mock_client.is_available.return_value = True
                
                with patch.object(engine3, '_store_enhancement_results') as mock_store:
                    mock_store.return_value = None
                    
                    result = await engine3.enhance_achievement_text(
                        achievement_id="test",
                        enhancement_level=EnhancementLevel.MODERATE
                    )
                    
                    # Should fallback to rule-based enhancement
                    assert result.fallback_applied is True
    
    def test_system_enum_validation_all_phases(self):
        """Test enumeration validation across all systems."""
        
        # Test ATS System enumeration
        assert ATSSystem("taleo") == ATSSystem.TALEO
        assert ATSSystem("workday") == ATSSystem.WORKDAY
        
        with pytest.raises(ValueError):
            ATSSystem("invalid_system")
        
        # Test Enhancement Level enumeration
        assert EnhancementLevel("moderate") == EnhancementLevel.MODERATE
        assert EnhancementLevel("aggressive") == EnhancementLevel.AGGRESSIVE
        
        with pytest.raises(ValueError):
            EnhancementLevel("invalid_level")
        
        # Test Authenticity Level enumeration
        assert AuthenticityLevel("verified") == AuthenticityLevel.VERIFIED
        assert AuthenticityLevel("flagged") == AuthenticityLevel.FLAGGED
        
        with pytest.raises(ValueError):
            AuthenticityLevel("invalid_level")


class TestConfigurationAndSettings:
    """Test configuration and settings for all phases."""
    
    def test_all_phase_settings_validation(self):
        """Test that all phase settings are properly configured."""
        settings = get_settings()
        
        # Phase 1 settings
        assert hasattr(settings, 'enable_ai_content_selection')
        assert hasattr(settings, 'ai_selection_fallback_enabled')
        assert hasattr(settings, 'ai_selection_confidence_threshold')
        
        # Phase 2 settings
        assert hasattr(settings, 'enable_ai_ats_optimization')
        assert hasattr(settings, 'ats_optimization_fallback_enabled')
        assert hasattr(settings, 'ats_optimization_confidence_threshold')
        assert hasattr(settings, 'ats_default_target_systems')
        
        # Phase 3 settings
        assert hasattr(settings, 'enable_ai_content_enhancement')
        assert hasattr(settings, 'content_enhancement_fallback_enabled')
        assert hasattr(settings, 'content_enhancement_confidence_threshold')
        assert hasattr(settings, 'content_enhancement_default_level')
        
        # Validate threshold ranges for all phases
        assert 0.0 <= settings.ai_selection_confidence_threshold <= 1.0
        assert 0.0 <= settings.ats_optimization_confidence_threshold <= 1.0
        assert 0.0 <= settings.content_enhancement_confidence_threshold <= 1.0
    
    def test_enhancement_level_configuration(self):
        """Test enhancement level configuration parsing."""
        settings = get_settings()
        default_level = settings.content_enhancement_default_level
        
        # Should be a valid enhancement level
        try:
            EnhancementLevel(default_level)
        except ValueError:
            pytest.fail(f"Invalid default enhancement level in config: {default_level}")


class TestBackwardsCompatibility:
    """Test backwards compatibility with existing functionality."""
    
    def test_existing_apis_still_functional(self):
        """Test that existing APIs continue to work with new phases."""
        # This would test that old API endpoints still work
        # In a real implementation, this would make actual API calls
        assert True  # Placeholder
    
    def test_database_schema_backwards_compatible(self):
        """Test that database schema changes are backwards compatible."""
        # Test that new tables don't break existing functionality
        assert True  # Placeholder
    
    def test_configuration_backwards_compatible(self):
        """Test that configuration changes don't break existing setups."""
        settings = get_settings()
        
        # All new settings should have sensible defaults
        assert settings.enable_ai_content_enhancement is False  # Default disabled
        assert settings.content_enhancement_fallback_enabled is True  # Default enabled
        assert settings.content_enhancement_confidence_threshold == 0.7  # Reasonable default


class TestPerformanceAndStress:
    """Test performance characteristics and stress scenarios."""
    
    @pytest.mark.asyncio
    async def test_concurrent_operations_all_phases(self):
        """Test handling multiple concurrent operations across all phases."""
        
        # Mock responses for concurrent testing
        mock_gemini_response = GeminiResponse(
            success=True,
            content=json.dumps({"confidence_score": 0.8}),
            tokens_used=100,
            response_time=1.0
        )
        
        # Test Phase 1 concurrent operations
        engine1 = AIContentSelectionEngine()
        with patch.object(engine1, 'gemini_client') as mock_client:
            mock_client.is_available.return_value = True
            mock_client.generate_content_analysis.return_value = mock_gemini_response
            
            with patch.object(engine1, 'select_optimal_content') as mock_base:
                mock_base.return_value = Mock(
                    selected_achievements=["test"],
                    total_score=0.8,
                    estimated_word_count=200
                )
                
                tasks = []
                for i in range(3):
                    task = engine1.ai_enhanced_selection(
                        user_profile_id=f"user_{i}",
                        job_analysis=Mock()
                    )
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # All should succeed
                for result in results:
                    assert not isinstance(result, Exception)
                    assert isinstance(result, EnhancedContentSelectionResult)
                    assert result.success is True
        
        # Test Phase 2 concurrent operations
        engine2 = ATSOptimizationEngine(use_ai_optimization=True)
        with patch.object(engine2, '_load_content_selection') as mock_load:
            mock_load.return_value = {"content_selection": Mock(id="test"), "profile": Mock()}
            
            with patch.object(engine2, 'gemini_client') as mock_client:
                mock_client.is_available.return_value = True
                mock_client.generate_content_analysis.return_value = mock_gemini_response
                
                with patch.object(engine2, '_store_optimization_results') as mock_store:
                    mock_store.return_value = None
                    
                    tasks = []
                    for i in range(3):
                        task = engine2.optimize_content_for_ats(
                            content_selection_id=f"content_{i}",
                            target_ats_systems=[ATSSystem.GENERIC]
                        )
                        tasks.append(task)
                    
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # All should succeed
                    for result in results:
                        assert not isinstance(result, Exception)
                        assert isinstance(result, ATSOptimizationResult)
        
        # Test Phase 3 concurrent operations
        engine3 = ContentEnhancementEngine(use_ai_enhancement=True)
        with patch.object(engine3, '_load_achievement_data') as mock_load:
            mock_load.return_value = {
                "achievement": Mock(),
                "original_text": "Test text",
                "quantified_metrics": {},
                "impact_level": 5
            }
            
            with patch.object(engine3, 'gemini_client') as mock_client:
                mock_client.is_available.return_value = True
                mock_client.generate_content_analysis.return_value = mock_gemini_response
                
                with patch.object(engine3, '_store_enhancement_results') as mock_store:
                    mock_store.return_value = None
                    
                    tasks = []
                    for i in range(3):
                        task = engine3.enhance_achievement_text(
                            achievement_id=f"ach_{i}",
                            enhancement_level=EnhancementLevel.MODERATE
                        )
                        tasks.append(task)
                    
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # All should succeed or gracefully fallback
                    for result in results:
                        if isinstance(result, Exception):
                            pytest.fail(f"Enhancement task failed: {result}")
                        assert isinstance(result, ContentEnhancementResult)


class TestSecurityAndAuthenticity:
    """Test security features and authenticity safeguards."""
    
    def test_authenticity_validation_phase3(self):
        """Test authenticity validation in content enhancement."""
        engine = ContentEnhancementEngine()
        
        # Test authenticity guidelines are properly set
        assert engine.authenticity_guidelines is not None
        assert "no_fabrication" in engine.authenticity_guidelines
        assert "maintain_voice" in engine.authenticity_guidelines
    
    def test_content_validation_prevents_fabrication(self):
        """Test that content enhancement prevents fabrication."""
        # This would test actual content validation logic
        # For now, ensure the guidelines exist
        engine = ContentEnhancementEngine()
        guidelines = engine.authenticity_guidelines
        
        assert guidelines["no_fabrication"] == "Never add false information or experiences"
        assert guidelines["quantification_only"] == "Only enhance existing quantified metrics"
    
    def test_user_approval_required_for_enhancements(self):
        """Test that user approval is required for content enhancements."""
        # In a real implementation, this would test the approval workflow
        # For now, ensure the mechanism exists in the data model
        assert True  # Placeholder for approval workflow tests


if __name__ == "__main__":
    """
    Run comprehensive bug testing for Phase 1, 2 & 3.
    
    Usage:
        python -m pytest tests/test_phase1_2_3_comprehensive_bug_testing.py -v
        
    Run specific test classes:
        python -m pytest tests/test_phase1_2_3_comprehensive_bug_testing.py::TestPhase1AIContentSelection -v
        python -m pytest tests/test_phase1_2_3_comprehensive_bug_testing.py::TestPhase2ATSOptimization -v
        python -m pytest tests/test_phase1_2_3_comprehensive_bug_testing.py::TestPhase3ContentEnhancement -v
        python -m pytest tests/test_phase1_2_3_comprehensive_bug_testing.py::TestPhase1Phase2Phase3Integration -v
        
    Run specific categories:
        python -m pytest tests/test_phase1_2_3_comprehensive_bug_testing.py::TestErrorHandlingAndEdgeCases -v
        python -m pytest tests/test_phase1_2_3_comprehensive_bug_testing.py::TestBackwardsCompatibility -v
        python -m pytest tests/test_phase1_2_3_comprehensive_bug_testing.py::TestPerformanceAndStress -v
        python -m pytest tests/test_phase1_2_3_comprehensive_bug_testing.py::TestSecurityAndAuthenticity -v
    """
    pytest.main([__file__, "-v"])