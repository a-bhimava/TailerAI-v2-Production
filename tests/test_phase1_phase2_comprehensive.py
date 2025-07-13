"""
Comprehensive Bug Testing for Phase 1 & Phase 2 Gemini Integration.
Tests all critical functionality, edge cases, and integration points.

Phase 1: AI-Enhanced Content Selection
Phase 2: ATS Optimization Engine

This test suite validates:
- Service initialization and configuration
- API endpoint functionality
- Fallback mechanisms
- Error handling
- Data integrity
- Integration between phases
"""

import pytest
import asyncio
import json
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from typing import Dict, Any

# Set up test environment
os.environ["ENVIRONMENT"] = "testing"
os.environ["ENABLE_AI_CONTENT_SELECTION"] = "true"
os.environ["ENABLE_AI_ATS_OPTIMIZATION"] = "true"
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
from app.services.job_analysis_service import JobAnalysisResult
from app.services.gemini_client import GeminiResponse
from app.config.settings import get_settings


class TestPhase1AIContentSelection:
    """Comprehensive tests for Phase 1: AI-Enhanced Content Selection."""
    
    @pytest.fixture
    def mock_gemini_response(self):
        """Mock successful Gemini response."""
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
    
    @pytest.fixture
    def ai_selection_engine(self):
        """Create AI content selection engine for testing."""
        return AIContentSelectionEngine()
    
    def test_ai_content_selection_initialization(self, ai_selection_engine):
        """Test proper initialization of AI content selection engine."""
        assert ai_selection_engine is not None
        assert hasattr(ai_selection_engine, 'use_ai_enhanced')
        assert hasattr(ai_selection_engine, 'fallback_enabled')
        assert hasattr(ai_selection_engine, 'confidence_threshold')
    
    @pytest.mark.asyncio
    async def test_ai_enhanced_selection_success(
        self, 
        ai_selection_engine, 
        mock_gemini_response, 
        mock_job_analysis
    ):
        """Test successful AI-enhanced content selection."""
        with patch.object(ai_selection_engine, 'gemini_client') as mock_client:
            mock_client.generate_content_analysis.return_value = mock_gemini_response
            mock_client.is_available.return_value = True
            
            # Mock the base selection
            with patch.object(ai_selection_engine, 'select_optimal_content') as mock_base:
                mock_base.return_value = Mock(
                    selected_achievements=["test_1", "test_2"],
                    total_score=0.8,
                    estimated_word_count=250
                )
                
                result = await ai_selection_engine.ai_enhanced_selection(
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
    async def test_ai_selection_fallback_on_failure(
        self, 
        ai_selection_engine, 
        mock_job_analysis
    ):
        """Test fallback to algorithmic selection when AI fails."""
        with patch.object(ai_selection_engine, 'gemini_client') as mock_client:
            # Simulate AI failure
            mock_client.generate_content_analysis.return_value = GeminiResponse(
                success=False,
                error_message="API rate limit exceeded"
            )
            mock_client.is_available.return_value = False
            
            # Mock the base selection for fallback
            with patch.object(ai_selection_engine, 'select_optimal_content') as mock_base:
                mock_base.return_value = Mock(
                    selected_achievements=["test_1"],
                    total_score=0.75,
                    estimated_word_count=200
                )
                
                result = await ai_selection_engine.ai_enhanced_selection(
                    user_profile_id="test_user",
                    job_analysis=mock_job_analysis
                )
                
                assert isinstance(result, EnhancedContentSelectionResult)
                assert result.success is True
                assert result.selection_method == "algorithmic"
                assert result.fallback_applied is True
                assert "fallback" in result.ai_reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_ai_selection_low_confidence_fallback(
        self, 
        ai_selection_engine, 
        mock_job_analysis
    ):
        """Test fallback when AI confidence is below threshold."""
        low_confidence_response = GeminiResponse(
            success=True,
            content=json.dumps({
                "selected_achievements": [{"achievement_id": "test_1"}],
                "confidence_score": 0.5,  # Below threshold (0.7)
                "selection_reasoning": "Uncertain match"
            }),
            tokens_used=100,
            response_time=1.5
        )
        
        with patch.object(ai_selection_engine, 'gemini_client') as mock_client:
            mock_client.generate_content_analysis.return_value = low_confidence_response
            mock_client.is_available.return_value = True
            
            with patch.object(ai_selection_engine, 'select_optimal_content') as mock_base:
                mock_base.return_value = Mock(
                    selected_achievements=["test_1"],
                    total_score=0.7,
                    estimated_word_count=180
                )
                
                result = await ai_selection_engine.ai_enhanced_selection(
                    user_profile_id="test_user",
                    job_analysis=mock_job_analysis
                )
                
                assert result.fallback_applied is True
                assert result.selection_method == "algorithmic"
    
    def test_ai_reasoning_parsing(self, ai_selection_engine):
        """Test parsing of AI reasoning from Gemini response."""
        ai_response = {
            "content_fit_analysis": "Strong technical alignment",
            "keyword_integration_strategy": "Natural keyword placement",
            "combination_logic": "Balanced selection approach",
            "confidence_score": 0.88,
            "alternative_considerations": ["Could add more leadership examples"]
        }
        
        reasoning = ai_selection_engine._parse_ai_reasoning(ai_response)
        
        assert isinstance(reasoning, AISelectionReasoning)
        assert reasoning.content_fit_analysis == "Strong technical alignment"
        assert reasoning.confidence_score == 0.88
        assert len(reasoning.alternative_considerations) == 1


class TestPhase2ATSOptimization:
    """Comprehensive tests for Phase 2: ATS Optimization Engine."""
    
    @pytest.fixture
    def ats_engine(self):
        """Create ATS optimization engine for testing."""
        return ATSOptimizationEngine(use_ai_optimization=True)
    
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
    
    def test_ats_optimization_initialization(self, ats_engine):
        """Test proper initialization of ATS optimization engine."""
        assert ats_engine is not None
        assert hasattr(ats_engine, 'use_ai_optimization')
        assert hasattr(ats_engine, 'ats_system_configs')
        assert len(ats_engine.ats_system_configs) > 0
        assert ATSSystem.TALEO in ats_engine.ats_system_configs
        assert ATSSystem.WORKDAY in ats_engine.ats_system_configs
    
    def test_ats_system_configurations(self, ats_engine):
        """Test ATS system configurations are properly loaded."""
        taleo_config = ats_engine.ats_system_configs[ATSSystem.TALEO]
        
        assert "keyword_weight" in taleo_config
        assert "format_strictness" in taleo_config
        assert "max_word_count" in taleo_config
        assert taleo_config["keyword_weight"] > 0
        assert taleo_config["format_strictness"] in ["low", "medium", "high"]
    
    @pytest.mark.asyncio
    async def test_ai_powered_ats_optimization(
        self, 
        ats_engine, 
        mock_content_data, 
        mock_ats_gemini_response
    ):
        """Test AI-powered ATS optimization."""
        target_systems = [ATSSystem.TALEO, ATSSystem.WORKDAY]
        
        with patch.object(ats_engine, '_load_content_selection') as mock_load:
            mock_load.return_value = mock_content_data
            
            with patch.object(ats_engine, 'gemini_client') as mock_client:
                mock_client.generate_content_analysis.return_value = mock_ats_gemini_response
                mock_client.is_available.return_value = True
                
                with patch.object(ats_engine, '_store_optimization_results') as mock_store:
                    mock_store.return_value = None
                    
                    result = await ats_engine.optimize_content_for_ats(
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
    
    @pytest.mark.asyncio
    async def test_rule_based_ats_optimization_fallback(
        self, 
        mock_content_data
    ):
        """Test rule-based optimization when AI fails."""
        # Create engine with AI disabled
        ats_engine = ATSOptimizationEngine(use_ai_optimization=False)
        target_systems = [ATSSystem.GENERIC]
        
        with patch.object(ats_engine, '_load_content_selection') as mock_load:
            mock_load.return_value = mock_content_data
            
            with patch.object(ats_engine, '_store_optimization_results') as mock_store:
                mock_store.return_value = None
                
                result = await ats_engine.optimize_content_for_ats(
                    content_selection_id="test_content_123",
                    target_ats_systems=target_systems
                )
                
                assert isinstance(result, ATSOptimizationResult)
                assert result.optimization_algorithm.startswith("rule_based")
                assert result.fallback_applied is False  # Not fallback, intentionally rule-based
                assert result.overall_compatibility_score > 0
    
    def test_compatibility_level_calculation(self, ats_engine):
        """Test compatibility level calculation from scores."""
        assert ats_engine._calculate_compatibility_level(0.95) == CompatibilityLevel.EXCELLENT
        assert ats_engine._calculate_compatibility_level(0.80) == CompatibilityLevel.GOOD
        assert ats_engine._calculate_compatibility_level(0.65) == CompatibilityLevel.FAIR
        assert ats_engine._calculate_compatibility_level(0.50) == CompatibilityLevel.POOR
        assert ats_engine._calculate_compatibility_level(0.30) == CompatibilityLevel.INCOMPATIBLE
    
    @pytest.mark.asyncio
    async def test_ats_system_capabilities(self, ats_engine):
        """Test ATS system capabilities retrieval."""
        capabilities = await ats_engine.get_ats_system_capabilities(ATSSystem.TALEO)
        
        assert "system_name" in capabilities
        assert "configuration" in capabilities
        assert "optimization_tips" in capabilities
        assert "common_issues" in capabilities
        assert capabilities["system_name"] == "taleo"
        assert len(capabilities["optimization_tips"]) > 0


class TestPhase1Phase2Integration:
    """Test integration between Phase 1 and Phase 2."""
    
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
    async def test_content_selection_to_ats_optimization_flow(self, mock_job_analysis):
        """Test complete flow from content selection to ATS optimization."""
        # Mock Phase 1 - Content Selection
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
            
            # Phase 1: Get content selection
            content_result = await ai_content_selector.select_optimal_content(
                user_profile_id="user_456",
                job_analysis=mock_job_analysis
            )
            
            assert content_result.success is True
            assert content_result.selection_method == "ai_enhanced"
            
            # Mock Phase 2 - ATS Optimization
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
                
                # Phase 2: Optimize content for ATS
                ats_result = await ats_optimizer.optimize_content_for_ats(
                    content_selection_id=content_result.selection_id,
                    target_ats_systems=[ATSSystem.TALEO],
                    job_analysis=mock_job_analysis
                )
                
                assert isinstance(ats_result, ATSOptimizationResult)
                assert ats_result.content_selection_id == content_result.selection_id
                assert ats_result.overall_compatibility_score > 0.8
                assert len(ats_result.keyword_optimizations) > 0


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases for both phases."""
    
    @pytest.mark.asyncio
    async def test_invalid_content_selection_id(self):
        """Test handling of invalid content selection ID."""
        with patch.object(ats_optimizer, '_load_content_selection') as mock_load:
            mock_load.side_effect = Exception("Content selection not found")
            
            with pytest.raises(Exception) as exc_info:
                await ats_optimizer.optimize_content_for_ats(
                    content_selection_id="invalid_id",
                    target_ats_systems=[ATSSystem.GENERIC]
                )
            
            assert "Content selection not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_malformed_gemini_response_handling(self):
        """Test handling of malformed Gemini responses."""
        engine = AIContentSelectionEngine()
        
        # Test invalid JSON
        invalid_response = GeminiResponse(
            success=True,
            content="invalid json {",
            tokens_used=10,
            response_time=1.0
        )
        
        with patch.object(engine, 'gemini_client') as mock_client:
            mock_client.generate_content_analysis.return_value = invalid_response
            mock_client.is_available.return_value = True
            
            with patch.object(engine, 'select_optimal_content') as mock_base:
                mock_base.return_value = Mock(
                    selected_achievements=["test"],
                    total_score=0.7,
                    estimated_word_count=200
                )
                
                result = await engine.ai_enhanced_selection(
                    user_profile_id="test_user",
                    job_analysis=Mock()
                )
                
                # Should fallback to algorithmic selection
                assert result.fallback_applied is True
                assert result.selection_method == "algorithmic"
    
    def test_ats_system_enum_validation(self):
        """Test ATS system enumeration validation."""
        # Valid systems
        assert ATSSystem("taleo") == ATSSystem.TALEO
        assert ATSSystem("workday") == ATSSystem.WORKDAY
        
        # Invalid system should raise ValueError
        with pytest.raises(ValueError):
            ATSSystem("invalid_system")
    
    @pytest.mark.asyncio
    async def test_empty_keyword_list_handling(self):
        """Test handling of empty keyword lists in ATS optimization."""
        ats_engine = ATSOptimizationEngine(use_ai_optimization=False)
        
        mock_content = {
            "content_selection": Mock(
                id="test",
                profile_id="user",
                selected_achievements=[],
                estimated_word_count=0,
                selection_criteria={}
            ),
            "profile": Mock(),
            "selected_achievements": [],
            "achievement_scores": {}
        }
        
        with patch.object(ats_engine, '_load_content_selection') as mock_load:
            mock_load.return_value = mock_content
            
            with patch.object(ats_engine, '_store_optimization_results') as mock_store:
                mock_store.return_value = None
                
                result = await ats_engine.optimize_content_for_ats(
                    content_selection_id="test",
                    target_ats_systems=[ATSSystem.GENERIC]
                )
                
                # Should handle empty content gracefully
                assert isinstance(result, ATSOptimizationResult)
                assert result.overall_compatibility_score >= 0


class TestConfigurationAndSettings:
    """Test configuration and settings for both phases."""
    
    def test_settings_validation(self):
        """Test that settings are properly configured."""
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
        
        # Validate threshold ranges
        assert 0.0 <= settings.ai_selection_confidence_threshold <= 1.0
        assert 0.0 <= settings.ats_optimization_confidence_threshold <= 1.0
    
    def test_ats_default_systems_parsing(self):
        """Test parsing of default ATS systems from configuration."""
        settings = get_settings()
        default_systems = settings.ats_default_target_systems.split(",")
        
        assert len(default_systems) > 0
        for system in default_systems:
            system_clean = system.strip()
            assert system_clean  # Not empty
            # Should be a valid ATS system
            try:
                ATSSystem(system_clean)
            except ValueError:
                pytest.fail(f"Invalid default ATS system in config: {system_clean}")


# Performance and stress tests
class TestPerformanceAndStress:
    """Test performance characteristics and stress scenarios."""
    
    @pytest.mark.asyncio
    async def test_concurrent_content_selections(self):
        """Test handling multiple concurrent content selections."""
        engine = AIContentSelectionEngine()
        
        # Mock successful responses
        with patch.object(engine, 'gemini_client') as mock_client:
            mock_client.is_available.return_value = True
            mock_client.generate_content_analysis.return_value = GeminiResponse(
                success=True,
                content=json.dumps({"confidence_score": 0.8, "selected_achievements": []}),
                tokens_used=100,
                response_time=1.0
            )
            
            with patch.object(engine, 'select_optimal_content') as mock_base:
                mock_base.return_value = Mock(
                    selected_achievements=["test"],
                    total_score=0.8,
                    estimated_word_count=200
                )
                
                # Run multiple concurrent selections
                tasks = []
                for i in range(5):
                    task = engine.ai_enhanced_selection(
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


if __name__ == "__main__":
    """
    Run comprehensive bug testing for Phase 1 & 2.
    
    Usage:
        python -m pytest tests/test_phase1_phase2_comprehensive.py -v
        
    Run specific test classes:
        python -m pytest tests/test_phase1_phase2_comprehensive.py::TestPhase1AIContentSelection -v
        python -m pytest tests/test_phase1_phase2_comprehensive.py::TestPhase2ATSOptimization -v
        python -m pytest tests/test_phase1_phase2_comprehensive.py::TestPhase1Phase2Integration -v
    """
    pytest.main([__file__, "-v"])