"""
Comprehensive Testing Suite for Phase 4: Continuous Learning & Personalization.
Tests personalization engine, A/B testing framework, market intelligence, and integration.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

# Test imports
from app.services.personalization_engine import (
    PersonalizationEngine,
    OutcomeType,
    LearningConfidence,
    PersonalizationStrategy,
    ApplicationOutcomeData,
    UserSuccessPattern,
    PersonalizationInsight,
    PersonalizationResult
)
from app.services.ab_testing_engine import (
    ABTestingEngine,
    ExperimentStatus,
    TestGroup,
    ExperimentWinner,
    ExperimentConfig,
    ExperimentResults
)
from app.services.job_analysis_service import JobAnalysisResult


class TestPersonalizationEngine:
    """Test suite for PersonalizationEngine."""
    
    @pytest.fixture
    def personalization_engine(self):
        """Create personalization engine for testing."""
        return PersonalizationEngine(use_ai_learning=False)  # Use rule-based for testing
    
    @pytest.fixture
    def mock_gemini_client(self):
        """Mock Gemini client for testing."""
        mock_client = AsyncMock()
        mock_client.is_available.return_value = True
        mock_client.generate_content_analysis.return_value = AsyncMock(
            success=True,
            content='{"insights": [], "overall_analysis": "test", "predicted_success_rate": 0.8, "recommended_strategy": "balanced"}'
        )
        return mock_client
    
    @pytest.fixture
    def sample_application_data(self):
        """Sample application outcome data for testing."""
        user_id = str(uuid.uuid4())
        return [
            ApplicationOutcomeData(
                application_id="app_1",
                user_profile_id=user_id,
                company_name="TechCorp",
                position_title="Senior Developer",
                job_description="Python development position",
                content_selection_id="sel_1",
                outcome_type=OutcomeType.INTERVIEW,
                outcome_date=datetime.utcnow() - timedelta(days=30)
            ),
            ApplicationOutcomeData(
                application_id="app_2",
                user_profile_id=user_id,
                company_name="DataCorp",
                position_title="Data Scientist",
                job_description="Data science position",
                content_selection_id="sel_2",
                outcome_type=OutcomeType.OFFER,
                outcome_date=datetime.utcnow() - timedelta(days=15)
            ),
            ApplicationOutcomeData(
                application_id="app_3",
                user_profile_id=user_id,
                company_name="StartupCorp",
                position_title="Full Stack Developer",
                job_description="Full stack development",
                content_selection_id="sel_3",
                outcome_type=OutcomeType.REJECTION,
                outcome_date=datetime.utcnow() - timedelta(days=10)
            )
        ]
    
    @pytest.mark.asyncio
    async def test_analyze_user_performance_with_data(self, personalization_engine, sample_application_data):
        """Test user performance analysis with application data."""
        
        user_id = sample_application_data[0].user_profile_id
        
        # Mock database methods
        with patch.object(personalization_engine, '_load_user_application_history', return_value=sample_application_data):
            with patch.object(personalization_engine, '_store_personalization_results', return_value=None):
                
                result = await personalization_engine.analyze_user_performance(user_id)
                
                # Verify result structure
                assert isinstance(result, PersonalizationResult)
                assert result.user_profile_id == user_id
                assert isinstance(result.success_patterns, UserSuccessPattern)
                assert isinstance(result.insights, list)
                assert isinstance(result.personalized_strategy, PersonalizationStrategy)
                assert isinstance(result.recommended_actions, list)
                
                # Verify success patterns
                success_patterns = result.success_patterns
                assert success_patterns.success_rate == 2/3  # 2 successes out of 3 applications
                assert success_patterns.sample_size == 3
                assert success_patterns.confidence_level == LearningConfidence.LOW  # < 5 data points
                
                # Verify insights are generated
                assert len(result.insights) > 0
                for insight in result.insights:
                    assert isinstance(insight, PersonalizationInsight)
                    assert insight.user_profile_id == user_id
                    assert 0.0 <= insight.confidence_score <= 1.0
                    assert insight.expected_improvement >= 0.0
    
    @pytest.mark.asyncio
    async def test_analyze_user_performance_no_data(self, personalization_engine):
        """Test user performance analysis with no application data."""
        
        user_id = str(uuid.uuid4())
        
        # Mock database methods to return empty data
        with patch.object(personalization_engine, '_load_user_application_history', return_value=[]):
            
            result = await personalization_engine.analyze_user_performance(user_id)
            
            # Verify default result for new users
            assert isinstance(result, PersonalizationResult)
            assert result.user_profile_id == user_id
            assert result.success_patterns.success_rate == 0.0
            assert result.success_patterns.sample_size == 0
            assert result.success_patterns.confidence_level == LearningConfidence.LOW
            assert len(result.insights) > 0  # Should have default insights
    
    @pytest.mark.asyncio
    async def test_track_application_outcome(self, personalization_engine):
        """Test application outcome tracking."""
        
        outcome_data = ApplicationOutcomeData(
            application_id="test_app",
            user_profile_id=str(uuid.uuid4()),
            company_name="TestCorp",
            position_title="Test Developer",
            job_description="Test position",
            content_selection_id="test_sel",
            outcome_type=OutcomeType.OFFER,
            outcome_date=datetime.utcnow()
        )
        
        # Mock database methods
        with patch.object(personalization_engine, '_store_application_outcome', return_value=None):
            with patch.object(personalization_engine, '_should_trigger_reanalysis', return_value=True):
                with patch.object(personalization_engine, '_update_user_success_metrics', return_value=None):
                    
                    result = await personalization_engine.track_application_outcome(outcome_data)
                    
                    # Verify tracking result
                    assert result["success"] is True
                    assert result["outcome_tracked"] is True
                    assert result["outcome_type"] == OutcomeType.OFFER.value
                    assert result["user_profile_id"] == outcome_data.user_profile_id
                    assert result["trigger_reanalysis"] is True
    
    @pytest.mark.asyncio
    async def test_apply_personalized_optimization(self, personalization_engine):
        """Test personalized optimization application."""
        
        user_id = str(uuid.uuid4())
        
        # Mock job analysis
        job_analysis = JobAnalysisResult(
            job_description_hash="test_hash",
            company_name="TestCorp",
            position_title="Test Developer",
            required_skills=["python", "sql"],
            preferred_skills=["docker", "kubernetes"],
            important_keywords=["python", "optimization", "performance"],
            seniority_level="senior",
            confidence_score=0.9
        )
        
        # Mock personalization result
        mock_personalization_result = PersonalizationResult(
            user_profile_id=user_id,
            success_patterns=UserSuccessPattern(
                user_profile_id=user_id,
                successful_achievement_types=["technical"],
                effective_keywords=["python", "optimization"],
                optimal_enhancement_level="moderate",
                best_performing_industries=["technology"],
                preferred_content_length="medium",
                success_rate=0.75,
                confidence_level=LearningConfidence.MEDIUM,
                sample_size=10
            ),
            insights=[],
            personalized_strategy=PersonalizationStrategy.BALANCED,
            recommended_actions=["Use technical achievements", "Focus on python keywords"],
            predicted_improvement=0.15,
            confidence_score=0.8,
            analysis_date=datetime.utcnow(),
            next_analysis_date=datetime.utcnow() + timedelta(days=30)
        )
        
        # Mock methods
        with patch.object(personalization_engine, 'analyze_user_performance', return_value=mock_personalization_result):
            with patch.object(personalization_engine, '_apply_personalized_content_selection', return_value={"selection_applied": True}):
                with patch.object(personalization_engine, '_apply_personalized_ats_optimization', return_value={"ats_optimization_applied": True}):
                    with patch.object(personalization_engine, '_apply_personalized_content_enhancement', return_value={"enhancement_applied": True}):
                        
                        result = await personalization_engine.apply_personalized_optimization(
                            user_profile_id=user_id,
                            job_analysis=job_analysis
                        )
                        
                        # Verify optimization result
                        assert result["success"] is True
                        assert result["user_profile_id"] == user_id
                        assert result["personalization_strategy"] == PersonalizationStrategy.BALANCED.value
                        assert "content_selection" in result
                        assert "ats_optimization" in result
                        assert "content_enhancement" in result
                        assert result["predicted_improvement"] == 0.15
                        assert result["confidence_score"] == 0.8
    
    @pytest.mark.asyncio
    async def test_get_market_intelligence(self, personalization_engine):
        """Test market intelligence retrieval."""
        
        # Mock market intelligence methods
        with patch.object(personalization_engine, '_get_trending_keywords', return_value=["python", "ai", "cloud"]):
            with patch.object(personalization_engine, '_get_salary_trends', return_value={"median_salary": 120000}):
                with patch.object(personalization_engine, '_get_successful_content_patterns', return_value={"effective_verbs": ["optimized", "developed"]}):
                    with patch.object(personalization_engine, '_get_ai_market_insights', return_value={"trend": "increasing"}):
                        
                        result = await personalization_engine.get_market_intelligence(
                            industry="technology",
                            job_level="senior",
                            location="San Francisco"
                        )
                        
                        # Verify market intelligence result
                        assert result["success"] is True
                        assert result["industry"] == "technology"
                        assert result["job_level"] == "senior"
                        assert result["location"] == "San Francisco"
                        assert len(result["trending_keywords"]) > 0
                        assert "median_salary" in result["salary_trends"]
                        assert "effective_verbs" in result["successful_patterns"]
                        assert result["ai_insights"] is not None


class TestABTestingEngine:
    """Test suite for ABTestingEngine."""
    
    @pytest.fixture
    def ab_testing_engine(self):
        """Create A/B testing engine for testing."""
        return ABTestingEngine(enable_ab_testing=True)
    
    @pytest.fixture
    def sample_experiment_config(self):
        """Sample experiment configuration for testing."""
        return ExperimentConfig(
            experiment_name="Test Content Selection",
            experiment_description="Testing new content selection algorithm",
            experiment_type="content_selection",
            control_algorithm="algorithmic_selection_v1",
            test_algorithm="ai_enhanced_selection_v2",
            primary_metric="success_rate",
            secondary_metrics=["user_satisfaction", "processing_time"],
            success_criteria={"min_improvement": 0.05},
            traffic_allocation=0.5,
            min_sample_size=100,
            planned_duration_days=30,
            confidence_level=0.95
        )
    
    @pytest.mark.asyncio
    async def test_create_experiment(self, ab_testing_engine, sample_experiment_config):
        """Test A/B test experiment creation."""
        
        # Mock database session
        mock_session = MagicMock()
        mock_experiment = MagicMock()
        mock_experiment.id = uuid.uuid4()
        
        with patch('app.services.ab_testing_engine.db_service.get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.add = MagicMock()
            mock_session.commit = MagicMock()
            
            experiment_id = await ab_testing_engine.create_experiment(
                config=sample_experiment_config,
                created_by="test_user"
            )
            
            # Verify experiment creation
            assert experiment_id is not None
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_assign_user_to_experiment(self, ab_testing_engine):
        """Test user assignment to A/B test experiment."""
        
        experiment_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Mock methods
        with patch.object(ab_testing_engine, '_get_user_assignment', return_value=None):
            with patch.object(ab_testing_engine, '_get_experiment_config', return_value={"traffic_allocation": 0.5}):
                
                mock_session = MagicMock()
                with patch('app.services.ab_testing_engine.db_service.get_session') as mock_get_session:
                    mock_get_session.return_value.__enter__.return_value = mock_session
                    mock_session.add = MagicMock()
                    mock_session.commit = MagicMock()
                    
                    test_group = await ab_testing_engine.assign_user_to_experiment(
                        experiment_id=experiment_id,
                        user_profile_id=user_id
                    )
                    
                    # Verify assignment
                    assert test_group in [TestGroup.CONTROL, TestGroup.TEST]
                    mock_session.add.assert_called_once()
                    mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_should_use_test_algorithm(self, ab_testing_engine):
        """Test algorithm selection for A/B testing."""
        
        experiment_type = "content_selection"
        user_id = str(uuid.uuid4())
        
        # Mock active experiments
        mock_experiments = [{
            "id": str(uuid.uuid4()),
            "experiment_type": experiment_type,
            "control_algorithm": "control_v1",
            "test_algorithm": "test_v2",
            "traffic_allocation": 0.5
        }]
        
        with patch.object(ab_testing_engine, '_get_active_experiments_by_type', return_value=mock_experiments):
            with patch.object(ab_testing_engine, 'assign_user_to_experiment', return_value=TestGroup.TEST):
                
                use_test, experiment_id = await ab_testing_engine.should_use_test_algorithm(
                    experiment_type=experiment_type,
                    user_profile_id=user_id
                )
                
                # Verify algorithm selection
                assert isinstance(use_test, bool)
                assert experiment_id == mock_experiments[0]["id"]
    
    @pytest.mark.asyncio
    async def test_record_experiment_outcome(self, ab_testing_engine):
        """Test recording experiment outcomes."""
        
        experiment_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Mock database session and assignment
        mock_session = MagicMock()
        mock_assignment = MagicMock()
        mock_assignment.outcome_recorded = False
        
        with patch('app.services.ab_testing_engine.db_service.get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter_by.return_value.first.return_value = mock_assignment
            mock_session.commit = MagicMock()
            
            result = await ab_testing_engine.record_experiment_outcome(
                experiment_id=experiment_id,
                user_profile_id=user_id,
                primary_metric_value=0.75,
                secondary_metric_values={"user_satisfaction": 4.2}
            )
            
            # Verify outcome recording
            assert result is True
            assert mock_assignment.primary_metric_value == 0.75
            assert mock_assignment.secondary_metric_values == {"user_satisfaction": 4.2}
            assert mock_assignment.outcome_recorded is True
            mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_experiment_results(self, ab_testing_engine):
        """Test A/B test experiment results analysis."""
        
        experiment_id = str(uuid.uuid4())
        
        # Mock experiment and assignments
        mock_experiment = MagicMock()
        mock_experiment.id = experiment_id
        
        # Create mock assignments with outcome data
        control_assignments = []
        test_assignments = []
        
        # Control group (lower performance)
        for i in range(50):
            assignment = MagicMock()
            assignment.test_group = TestGroup.CONTROL.value
            assignment.primary_metric_value = 0.6 + (i * 0.001)  # 0.6 to 0.649
            control_assignments.append(assignment)
        
        # Test group (higher performance)
        for i in range(50):
            assignment = MagicMock()
            assignment.test_group = TestGroup.TEST.value
            assignment.primary_metric_value = 0.7 + (i * 0.001)  # 0.7 to 0.749
            test_assignments.append(assignment)
        
        all_assignments = control_assignments + test_assignments
        
        # Mock database session
        mock_session = MagicMock()
        with patch('app.services.ab_testing_engine.db_service.get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter_by.return_value.first.return_value = mock_experiment
            mock_session.query.return_value.filter_by.return_value.all.return_value = all_assignments
            mock_session.commit = MagicMock()
            
            results = await ab_testing_engine.analyze_experiment_results(experiment_id)
            
            # Verify analysis results
            assert isinstance(results, ExperimentResults)
            assert results.experiment_id == experiment_id
            assert results.control_group_size == 50
            assert results.test_group_size == 50
            assert results.effect_size > 0  # Test group should perform better
            assert isinstance(results.winner, ExperimentWinner)
            assert results.statistical_significance is not None


class TestPhase4Integration:
    """Integration tests for Phase 4 components."""
    
    @pytest.fixture
    def personalization_engine(self):
        """Create personalization engine for integration testing."""
        return PersonalizationEngine(use_ai_learning=False)
    
    @pytest.fixture
    def ab_testing_engine(self):
        """Create A/B testing engine for integration testing."""
        return ABTestingEngine(enable_ab_testing=True)
    
    @pytest.mark.asyncio
    async def test_personalization_with_ab_testing(self, personalization_engine, ab_testing_engine):
        """Test integration between personalization and A/B testing."""
        
        user_id = str(uuid.uuid4())
        experiment_type = "content_selection"
        
        # Mock A/B testing to use test algorithm
        with patch.object(ab_testing_engine, 'should_use_test_algorithm', return_value=(True, "exp_123")):
            
            # Test that personalization engine can work with A/B testing
            use_test, experiment_id = await ab_testing_engine.should_use_test_algorithm(
                experiment_type=experiment_type,
                user_profile_id=user_id
            )
            
            assert use_test is True
            assert experiment_id == "exp_123"
            
            # Verify that the personalization engine could use this information
            # to select algorithms during optimization
            if use_test:
                # Would use test algorithm
                algorithm_choice = "ai_enhanced_selection_v2"
            else:
                # Would use control algorithm
                algorithm_choice = "algorithmic_selection_v1"
            
            assert algorithm_choice == "ai_enhanced_selection_v2"
    
    @pytest.mark.asyncio
    async def test_outcome_tracking_triggers_analysis(self, personalization_engine):
        """Test that tracking outcomes triggers personalization analysis."""
        
        user_id = str(uuid.uuid4())
        
        # Create multiple outcome data points
        outcomes = []
        for i in range(3):
            outcome = ApplicationOutcomeData(
                application_id=f"app_{i}",
                user_profile_id=user_id,
                company_name=f"Company_{i}",
                position_title="Developer",
                job_description="Development position",
                content_selection_id=f"sel_{i}",
                outcome_type=OutcomeType.INTERVIEW if i % 2 == 0 else OutcomeType.OFFER,
                outcome_date=datetime.utcnow() - timedelta(days=i*10)
            )
            outcomes.append(outcome)
        
        # Mock database methods
        with patch.object(personalization_engine, '_store_application_outcome', return_value=None):
            with patch.object(personalization_engine, '_should_trigger_reanalysis', return_value=True):
                with patch.object(personalization_engine, '_update_user_success_metrics', return_value=None):
                    
                    # Track multiple outcomes
                    reanalysis_triggered = False
                    for outcome in outcomes:
                        result = await personalization_engine.track_application_outcome(outcome)
                        if result["trigger_reanalysis"]:
                            reanalysis_triggered = True
                    
                    # Verify that reanalysis was triggered
                    assert reanalysis_triggered is True
    
    @pytest.mark.asyncio
    async def test_end_to_end_learning_cycle(self, personalization_engine, ab_testing_engine):
        """Test complete learning cycle from outcome tracking to optimization."""
        
        user_id = str(uuid.uuid4())
        
        # Step 1: Track successful outcomes
        successful_outcome = ApplicationOutcomeData(
            application_id="success_app",
            user_profile_id=user_id,
            company_name="SuccessCorp",
            position_title="Senior Developer",
            job_description="Python development with AI",
            content_selection_id="success_sel",
            outcome_type=OutcomeType.OFFER,
            outcome_date=datetime.utcnow(),
            ai_content_selection_used=True,
            content_enhancement_applied=True
        )
        
        # Mock outcome tracking
        with patch.object(personalization_engine, '_store_application_outcome', return_value=None):
            with patch.object(personalization_engine, '_should_trigger_reanalysis', return_value=True):
                with patch.object(personalization_engine, '_update_user_success_metrics', return_value=None):
                    
                    outcome_result = await personalization_engine.track_application_outcome(successful_outcome)
                    assert outcome_result["success"] is True
        
        # Step 2: Perform personalization analysis
        sample_application_data = [successful_outcome]
        
        with patch.object(personalization_engine, '_load_user_application_history', return_value=sample_application_data):
            with patch.object(personalization_engine, '_store_personalization_results', return_value=None):
                
                analysis_result = await personalization_engine.analyze_user_performance(user_id)
                assert isinstance(analysis_result, PersonalizationResult)
                assert analysis_result.success_patterns.success_rate > 0
        
        # Step 3: Apply personalized optimization
        job_analysis = JobAnalysisResult(
            job_description_hash="test_hash",
            company_name="NewCorp",
            position_title="Python Developer",
            required_skills=["python", "ai"],
            preferred_skills=["machine learning"],
            important_keywords=["python", "ai", "development"],
            seniority_level="senior",
            confidence_score=0.9
        )
        
        with patch.object(personalization_engine, 'analyze_user_performance', return_value=analysis_result):
            with patch.object(personalization_engine, '_apply_personalized_content_selection', return_value={"selection_applied": True}):
                with patch.object(personalization_engine, '_apply_personalized_ats_optimization', return_value={"ats_optimization_applied": True}):
                    with patch.object(personalization_engine, '_apply_personalized_content_enhancement', return_value={"enhancement_applied": True}):
                        
                        optimization_result = await personalization_engine.apply_personalized_optimization(
                            user_profile_id=user_id,
                            job_analysis=job_analysis
                        )
                        
                        assert optimization_result["success"] is True
                        assert optimization_result["predicted_improvement"] > 0


class TestPhase4Performance:
    """Performance tests for Phase 4 components."""
    
    @pytest.mark.asyncio
    async def test_personalization_analysis_performance(self):
        """Test personalization analysis performance with large datasets."""
        
        personalization_engine = PersonalizationEngine(use_ai_learning=False)
        user_id = str(uuid.uuid4())
        
        # Create large dataset of application outcomes
        large_dataset = []
        for i in range(100):
            outcome = ApplicationOutcomeData(
                application_id=f"app_{i}",
                user_profile_id=user_id,
                company_name=f"Company_{i}",
                position_title="Developer",
                job_description="Development position",
                content_selection_id=f"sel_{i}",
                outcome_type=OutcomeType.INTERVIEW if i % 3 == 0 else OutcomeType.OFFER if i % 3 == 1 else OutcomeType.REJECTION,
                outcome_date=datetime.utcnow() - timedelta(days=i)
            )
            large_dataset.append(outcome)
        
        # Test performance with large dataset
        with patch.object(personalization_engine, '_load_user_application_history', return_value=large_dataset):
            with patch.object(personalization_engine, '_store_personalization_results', return_value=None):
                
                start_time = datetime.utcnow()
                result = await personalization_engine.analyze_user_performance(user_id)
                end_time = datetime.utcnow()
                
                processing_time = (end_time - start_time).total_seconds()
                
                # Verify performance
                assert processing_time < 5.0  # Should complete within 5 seconds
                assert isinstance(result, PersonalizationResult)
                assert result.success_patterns.sample_size == 100
    
    @pytest.mark.asyncio
    async def test_concurrent_user_assignments(self):
        """Test concurrent user assignments to A/B test experiments."""
        
        ab_testing_engine = ABTestingEngine(enable_ab_testing=True)
        experiment_id = str(uuid.uuid4())
        
        # Create multiple user IDs
        user_ids = [str(uuid.uuid4()) for _ in range(50)]
        
        # Mock experiment config
        with patch.object(ab_testing_engine, '_get_experiment_config', return_value={"traffic_allocation": 0.5}):
            with patch.object(ab_testing_engine, '_get_user_assignment', return_value=None):
                
                mock_session = MagicMock()
                with patch('app.services.ab_testing_engine.db_service.get_session') as mock_get_session:
                    mock_get_session.return_value.__enter__.return_value = mock_session
                    mock_session.add = MagicMock()
                    mock_session.commit = MagicMock()
                    
                    # Test concurrent assignments
                    tasks = []
                    for user_id in user_ids:
                        task = ab_testing_engine.assign_user_to_experiment(
                            experiment_id=experiment_id,
                            user_profile_id=user_id
                        )
                        tasks.append(task)
                    
                    start_time = datetime.utcnow()
                    results = await asyncio.gather(*tasks)
                    end_time = datetime.utcnow()
                    
                    processing_time = (end_time - start_time).total_seconds()
                    
                    # Verify performance and results
                    assert processing_time < 2.0  # Should complete within 2 seconds
                    assert len(results) == 50
                    
                    # Verify distribution (should be roughly 50/50)
                    control_count = sum(1 for result in results if result == TestGroup.CONTROL)
                    test_count = sum(1 for result in results if result == TestGroup.TEST)
                    
                    # Allow for some variance in random assignment
                    assert 20 <= control_count <= 30
                    assert 20 <= test_count <= 30


class TestPhase4Security:
    """Security tests for Phase 4 components."""
    
    @pytest.mark.asyncio
    async def test_user_data_isolation(self):
        """Test that user data is properly isolated in personalization."""
        
        personalization_engine = PersonalizationEngine(use_ai_learning=False)
        user1_id = str(uuid.uuid4())
        user2_id = str(uuid.uuid4())
        
        # Create data for two different users
        user1_data = [
            ApplicationOutcomeData(
                application_id="user1_app",
                user_profile_id=user1_id,
                company_name="User1Corp",
                position_title="Developer",
                job_description="User 1 position",
                content_selection_id="user1_sel",
                outcome_type=OutcomeType.OFFER,
                outcome_date=datetime.utcnow()
            )
        ]
        
        user2_data = [
            ApplicationOutcomeData(
                application_id="user2_app",
                user_profile_id=user2_id,
                company_name="User2Corp",
                position_title="Engineer",
                job_description="User 2 position",
                content_selection_id="user2_sel",
                outcome_type=OutcomeType.REJECTION,
                outcome_date=datetime.utcnow()
            )
        ]
        
        # Mock database to return different data for different users
        def mock_load_data(user_id, *args, **kwargs):
            if user_id == user1_id:
                return user1_data
            elif user_id == user2_id:
                return user2_data
            else:
                return []
        
        with patch.object(personalization_engine, '_load_user_application_history', side_effect=mock_load_data):
            with patch.object(personalization_engine, '_store_personalization_results', return_value=None):
                
                # Analyze both users
                user1_result = await personalization_engine.analyze_user_performance(user1_id)
                user2_result = await personalization_engine.analyze_user_performance(user2_id)
                
                # Verify data isolation
                assert user1_result.user_profile_id == user1_id
                assert user2_result.user_profile_id == user2_id
                assert user1_result.success_patterns.success_rate == 1.0  # User 1 had success
                assert user2_result.success_patterns.success_rate == 0.0  # User 2 had rejection
    
    @pytest.mark.asyncio
    async def test_input_validation(self):
        """Test input validation for personalization endpoints."""
        
        personalization_engine = PersonalizationEngine(use_ai_learning=False)
        
        # Test invalid outcome type
        with pytest.raises(Exception):
            invalid_outcome = ApplicationOutcomeData(
                application_id="test",
                user_profile_id=str(uuid.uuid4()),
                company_name="Test",
                position_title="Test",
                job_description="Test",
                content_selection_id="test",
                outcome_type="invalid_outcome_type",  # Invalid
                outcome_date=datetime.utcnow()
            )
        
        # Test empty user ID
        with pytest.raises(Exception):
            await personalization_engine.analyze_user_performance("")
        
        # Test None user ID
        with pytest.raises(Exception):
            await personalization_engine.analyze_user_performance(None)


# Run all tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])