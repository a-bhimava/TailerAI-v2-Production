"""
A/B Testing Engine for TailerAI v2.0.
Phase 4 implementation of continuous algorithm optimization through experimentation.
Enables data-driven improvement of personalization and content optimization algorithms.
"""

import logging
import json
import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import hashlib

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, and_, or_

from app.models.database import (
    ABTestExperiment, ABTestAssignment, LearningEvent, UserProfile
)
from app.services.database_service import db_service, DatabaseError
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ExperimentStatus(str, Enum):
    """A/B test experiment status."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TestGroup(str, Enum):
    """A/B test group assignment."""
    CONTROL = "control"
    TEST = "test"


class ExperimentWinner(str, Enum):
    """A/B test experiment winner."""
    CONTROL = "control"
    TEST = "test"
    INCONCLUSIVE = "inconclusive"


@dataclass
class ExperimentConfig:
    """Configuration for A/B test experiment."""
    experiment_name: str
    experiment_description: str
    experiment_type: str  # "content_selection", "enhancement_level", "keyword_strategy"
    control_algorithm: str
    test_algorithm: str
    primary_metric: str  # "success_rate", "user_satisfaction", "improvement_score"
    secondary_metrics: List[str]
    success_criteria: Dict[str, Any]
    traffic_allocation: float = 0.5  # Percentage of users in test group
    min_sample_size: int = 100
    planned_duration_days: int = 30
    confidence_level: float = 0.95


@dataclass
class ExperimentResults:
    """Results of A/B test experiment."""
    experiment_id: str
    control_group_size: int
    test_group_size: int
    control_group_results: Dict[str, Any]
    test_group_results: Dict[str, Any]
    statistical_significance: float
    effect_size: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    winner: ExperimentWinner
    conclusion_notes: str
    implementation_decision: str


@dataclass
class UserAssignment:
    """User assignment to A/B test experiment."""
    experiment_id: str
    user_profile_id: str
    test_group: TestGroup
    assignment_date: datetime
    user_segment: Optional[str] = None
    user_characteristics: Optional[Dict[str, Any]] = None


class ABTestingError(Exception):
    """Custom exception for A/B testing operations."""
    pass


class ABTestingEngine:
    """
    A/B testing engine for continuous algorithm optimization.
    Enables data-driven improvement of personalization algorithms.
    """
    
    def __init__(self, enable_ab_testing: bool = None):
        """
        Initialize A/B testing engine.
        
        Args:
            enable_ab_testing: Override setting for A/B testing. If None, uses settings.
        """
        self.logger = logger
        
        # Configuration
        self.enable_ab_testing = enable_ab_testing if enable_ab_testing is not None else getattr(settings, 'enable_ab_testing', False)
        self.default_duration_days = getattr(settings, 'ab_test_default_duration_days', 30)
        self.min_sample_size = getattr(settings, 'ab_test_min_sample_size', 100)
        self.confidence_level = getattr(settings, 'ab_test_confidence_level', 0.95)
        
        # Active experiments cache
        self._active_experiments = {}
        self._user_assignments = {}
    
    async def create_experiment(
        self,
        config: ExperimentConfig,
        created_by: str = "system"
    ) -> str:
        """
        Create a new A/B test experiment.
        
        Args:
            config: Experiment configuration
            created_by: Who created the experiment
            
        Returns:
            Experiment ID
        """
        try:
            logger.info(f"Creating A/B test experiment: {config.experiment_name}")
            
            # Validate configuration
            self._validate_experiment_config(config)
            
            with db_service.get_session() as session:
                experiment = ABTestExperiment(
                    experiment_name=config.experiment_name,
                    experiment_description=config.experiment_description,
                    experiment_type=config.experiment_type,
                    control_algorithm=config.control_algorithm,
                    test_algorithm=config.test_algorithm,
                    experiment_config=asdict(config),
                    primary_metric=config.primary_metric,
                    secondary_metrics=config.secondary_metrics,
                    success_criteria=config.success_criteria,
                    traffic_allocation=config.traffic_allocation,
                    min_sample_size=config.min_sample_size,
                    planned_duration_days=config.planned_duration_days,
                    confidence_level=config.confidence_level,
                    status=ExperimentStatus.DRAFT.value,
                    created_by=created_by,
                    created_at=datetime.utcnow()
                )
                
                session.add(experiment)
                session.commit()
                
                experiment_id = str(experiment.id)
                
                logger.info(f"A/B test experiment created: {experiment_id}")
                return experiment_id
                
        except SQLAlchemyError as e:
            logger.error(f"Database error creating experiment: {e}")
            raise ABTestingError(f"Failed to create experiment: {e}")
    
    async def start_experiment(self, experiment_id: str) -> bool:
        """
        Start an A/B test experiment.
        
        Args:
            experiment_id: ID of experiment to start
            
        Returns:
            True if started successfully
        """
        try:
            logger.info(f"Starting A/B test experiment: {experiment_id}")
            
            with db_service.get_session() as session:
                experiment = session.query(ABTestExperiment).filter_by(id=experiment_id).first()
                
                if not experiment:
                    raise ABTestingError(f"Experiment not found: {experiment_id}")
                
                if experiment.status != ExperimentStatus.DRAFT.value:
                    raise ABTestingError(f"Cannot start experiment in status: {experiment.status}")
                
                # Update experiment status
                experiment.status = ExperimentStatus.ACTIVE.value
                experiment.start_date = datetime.utcnow()
                experiment.end_date = datetime.utcnow() + timedelta(days=experiment.planned_duration_days)
                experiment.updated_at = datetime.utcnow()
                
                session.commit()
                
                # Cache active experiment
                self._active_experiments[experiment_id] = {
                    "experiment_type": experiment.experiment_type,
                    "control_algorithm": experiment.control_algorithm,
                    "test_algorithm": experiment.test_algorithm,
                    "traffic_allocation": experiment.traffic_allocation,
                    "primary_metric": experiment.primary_metric
                }
                
                logger.info(f"A/B test experiment started: {experiment_id}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Database error starting experiment: {e}")
            raise ABTestingError(f"Failed to start experiment: {e}")
    
    async def assign_user_to_experiment(
        self,
        experiment_id: str,
        user_profile_id: str,
        user_segment: Optional[str] = None,
        user_characteristics: Optional[Dict[str, Any]] = None
    ) -> TestGroup:
        """
        Assign user to A/B test experiment.
        
        Args:
            experiment_id: ID of experiment
            user_profile_id: ID of user to assign
            user_segment: User segment for stratified testing
            user_characteristics: User properties for analysis
            
        Returns:
            Assigned test group
        """
        try:
            # Check if user already assigned
            existing_assignment = await self._get_user_assignment(experiment_id, user_profile_id)
            if existing_assignment:
                return TestGroup(existing_assignment.test_group)
            
            # Get experiment configuration
            experiment_config = await self._get_experiment_config(experiment_id)
            if not experiment_config:
                raise ABTestingError(f"Experiment not found: {experiment_id}")
            
            # Determine test group assignment
            test_group = self._assign_test_group(
                user_profile_id, 
                experiment_config["traffic_allocation"]
            )
            
            # Store assignment
            with db_service.get_session() as session:
                assignment = ABTestAssignment(
                    experiment_id=experiment_id,
                    user_profile_id=user_profile_id,
                    test_group=test_group.value,
                    assignment_date=datetime.utcnow(),
                    assignment_method="random",
                    user_segment=user_segment,
                    user_characteristics=user_characteristics or {},
                    is_active=True
                )
                
                session.add(assignment)
                session.commit()
                
                # Cache assignment
                cache_key = f"{experiment_id}:{user_profile_id}"
                self._user_assignments[cache_key] = {
                    "test_group": test_group.value,
                    "assignment_date": assignment.assignment_date,
                    "is_active": True
                }
                
                logger.info(f"User {user_profile_id} assigned to {test_group.value} group in experiment {experiment_id}")
                return test_group
                
        except SQLAlchemyError as e:
            logger.error(f"Database error assigning user to experiment: {e}")
            raise ABTestingError(f"Failed to assign user to experiment: {e}")
    
    async def should_use_test_algorithm(
        self,
        experiment_type: str,
        user_profile_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if user should use test algorithm for experiment type.
        
        Args:
            experiment_type: Type of experiment
            user_profile_id: User profile ID
            
        Returns:
            Tuple of (should_use_test, experiment_id)
        """
        if not self.enable_ab_testing:
            return False, None
        
        try:
            # Find active experiment for this type
            active_experiments = await self._get_active_experiments_by_type(experiment_type)
            
            if not active_experiments:
                return False, None
            
            # Use first active experiment (could be extended for multiple experiments)
            experiment = active_experiments[0]
            experiment_id = experiment["id"]
            
            # Get or create user assignment
            assignment = await self._get_user_assignment(experiment_id, user_profile_id)
            
            if not assignment:
                # Auto-assign user to experiment
                test_group = await self.assign_user_to_experiment(experiment_id, user_profile_id)
            else:
                test_group = TestGroup(assignment.test_group)
            
            # Return whether to use test algorithm
            use_test = test_group == TestGroup.TEST
            return use_test, experiment_id
            
        except Exception as e:
            logger.error(f"Error checking test algorithm usage: {e}")
            return False, None
    
    async def record_experiment_outcome(
        self,
        experiment_id: str,
        user_profile_id: str,
        primary_metric_value: float,
        secondary_metric_values: Optional[Dict[str, float]] = None
    ) -> bool:
        """
        Record outcome for user in A/B test experiment.
        
        Args:
            experiment_id: ID of experiment
            user_profile_id: User profile ID
            primary_metric_value: Value of primary metric
            secondary_metric_values: Values of secondary metrics
            
        Returns:
            True if recorded successfully
        """
        try:
            logger.info(f"Recording experiment outcome for user {user_profile_id} in experiment {experiment_id}")
            
            with db_service.get_session() as session:
                assignment = session.query(ABTestAssignment).filter_by(
                    experiment_id=experiment_id,
                    user_profile_id=user_profile_id
                ).first()
                
                if not assignment:
                    logger.warning(f"No assignment found for user {user_profile_id} in experiment {experiment_id}")
                    return False
                
                # Update assignment with outcome
                assignment.primary_metric_value = primary_metric_value
                assignment.secondary_metric_values = secondary_metric_values or {}
                assignment.outcome_recorded = True
                assignment.outcome_date = datetime.utcnow()
                assignment.updated_at = datetime.utcnow()
                
                session.commit()
                
                logger.info(f"Experiment outcome recorded: primary={primary_metric_value}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Database error recording experiment outcome: {e}")
            return False
    
    async def analyze_experiment_results(
        self,
        experiment_id: str
    ) -> ExperimentResults:
        """
        Analyze A/B test experiment results.
        
        Args:
            experiment_id: ID of experiment to analyze
            
        Returns:
            Experiment results with statistical analysis
        """
        try:
            logger.info(f"Analyzing experiment results: {experiment_id}")
            
            with db_service.get_session() as session:
                experiment = session.query(ABTestExperiment).filter_by(id=experiment_id).first()
                
                if not experiment:
                    raise ABTestingError(f"Experiment not found: {experiment_id}")
                
                # Get assignments with outcomes
                assignments = session.query(ABTestAssignment).filter_by(
                    experiment_id=experiment_id,
                    outcome_recorded=True
                ).all()
                
                if not assignments:
                    raise ABTestingError("No outcome data available for analysis")
                
                # Separate control and test groups
                control_group = [a for a in assignments if a.test_group == TestGroup.CONTROL.value]
                test_group = [a for a in assignments if a.test_group == TestGroup.TEST.value]
                
                if len(control_group) < 10 or len(test_group) < 10:
                    raise ABTestingError("Insufficient data for statistical analysis")
                
                # Calculate group statistics
                control_values = [a.primary_metric_value for a in control_group]
                test_values = [a.primary_metric_value for a in test_group]
                
                control_mean = statistics.mean(control_values)
                test_mean = statistics.mean(test_values)
                
                control_results = {
                    "size": len(control_group),
                    "mean": control_mean,
                    "std": statistics.stdev(control_values) if len(control_values) > 1 else 0,
                    "values": control_values
                }
                
                test_results = {
                    "size": len(test_group),
                    "mean": test_mean,
                    "std": statistics.stdev(test_values) if len(test_values) > 1 else 0,
                    "values": test_values
                }
                
                # Statistical analysis (simplified)
                effect_size = (test_mean - control_mean) / control_mean if control_mean != 0 else 0
                
                # Simplified statistical significance calculation
                # In production, would use proper statistical tests (t-test, chi-square, etc.)
                if abs(effect_size) > 0.05 and len(control_group) > 30 and len(test_group) > 30:
                    statistical_significance = 0.01  # Significant
                else:
                    statistical_significance = 0.10  # Not significant
                
                # Confidence interval (simplified)
                margin_of_error = 0.02 * effect_size  # Simplified calculation
                confidence_interval_lower = effect_size - margin_of_error
                confidence_interval_upper = effect_size + margin_of_error
                
                # Determine winner
                if statistical_significance < 0.05:
                    if test_mean > control_mean:
                        winner = ExperimentWinner.TEST
                        conclusion = f"Test algorithm shows {effect_size:.2%} improvement"
                    else:
                        winner = ExperimentWinner.CONTROL
                        conclusion = f"Control algorithm performs {abs(effect_size):.2%} better"
                else:
                    winner = ExperimentWinner.INCONCLUSIVE
                    conclusion = "No statistically significant difference found"
                
                # Update experiment with results
                experiment.control_group_size = len(control_group)
                experiment.test_group_size = len(test_group)
                experiment.control_group_results = control_results
                experiment.test_group_results = test_results
                experiment.statistical_significance = statistical_significance
                experiment.effect_size = effect_size
                experiment.confidence_interval_lower = confidence_interval_lower
                experiment.confidence_interval_upper = confidence_interval_upper
                experiment.winner = winner.value
                experiment.conclusion_notes = conclusion
                experiment.updated_at = datetime.utcnow()
                
                session.commit()
                
                results = ExperimentResults(
                    experiment_id=experiment_id,
                    control_group_size=len(control_group),
                    test_group_size=len(test_group),
                    control_group_results=control_results,
                    test_group_results=test_results,
                    statistical_significance=statistical_significance,
                    effect_size=effect_size,
                    confidence_interval_lower=confidence_interval_lower,
                    confidence_interval_upper=confidence_interval_upper,
                    winner=winner,
                    conclusion_notes=conclusion,
                    implementation_decision="pending"
                )
                
                logger.info(f"Experiment analysis completed. Winner: {winner.value}, Effect size: {effect_size:.4f}")
                return results
                
        except SQLAlchemyError as e:
            logger.error(f"Database error analyzing experiment: {e}")
            raise ABTestingError(f"Failed to analyze experiment: {e}")
    
    async def complete_experiment(
        self,
        experiment_id: str,
        implementation_decision: str = "pending"
    ) -> bool:
        """
        Complete an A/B test experiment.
        
        Args:
            experiment_id: ID of experiment to complete
            implementation_decision: Decision on implementation
            
        Returns:
            True if completed successfully
        """
        try:
            logger.info(f"Completing A/B test experiment: {experiment_id}")
            
            with db_service.get_session() as session:
                experiment = session.query(ABTestExperiment).filter_by(id=experiment_id).first()
                
                if not experiment:
                    raise ABTestingError(f"Experiment not found: {experiment_id}")
                
                # Update experiment status
                experiment.status = ExperimentStatus.COMPLETED.value
                experiment.end_date = datetime.utcnow()
                experiment.implementation_decision = implementation_decision
                experiment.updated_at = datetime.utcnow()
                
                session.commit()
                
                # Remove from active experiments cache
                if experiment_id in self._active_experiments:
                    del self._active_experiments[experiment_id]
                
                logger.info(f"A/B test experiment completed: {experiment_id}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Database error completing experiment: {e}")
            raise ABTestingError(f"Failed to complete experiment: {e}")
    
    def _validate_experiment_config(self, config: ExperimentConfig):
        """Validate experiment configuration."""
        
        if not config.experiment_name:
            raise ABTestingError("Experiment name is required")
        
        if not config.control_algorithm or not config.test_algorithm:
            raise ABTestingError("Both control and test algorithms are required")
        
        if config.control_algorithm == config.test_algorithm:
            raise ABTestingError("Control and test algorithms must be different")
        
        if not 0.1 <= config.traffic_allocation <= 0.9:
            raise ABTestingError("Traffic allocation must be between 0.1 and 0.9")
        
        if config.min_sample_size < 20:
            raise ABTestingError("Minimum sample size must be at least 20")
        
        if config.planned_duration_days < 7:
            raise ABTestingError("Experiment duration must be at least 7 days")
    
    def _assign_test_group(self, user_profile_id: str, traffic_allocation: float) -> TestGroup:
        """Assign user to test group using consistent hashing."""
        
        # Use consistent hashing for deterministic assignment
        hash_input = f"{user_profile_id}:ab_test_assignment"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        assignment_ratio = (hash_value % 10000) / 10000
        
        if assignment_ratio < traffic_allocation:
            return TestGroup.TEST
        else:
            return TestGroup.CONTROL
    
    async def _get_experiment_config(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Get experiment configuration."""
        
        # Check cache first
        if experiment_id in self._active_experiments:
            return self._active_experiments[experiment_id]
        
        try:
            with db_service.get_session() as session:
                experiment = session.query(ABTestExperiment).filter_by(id=experiment_id).first()
                
                if not experiment or experiment.status != ExperimentStatus.ACTIVE.value:
                    return None
                
                config = {
                    "experiment_type": experiment.experiment_type,
                    "control_algorithm": experiment.control_algorithm,
                    "test_algorithm": experiment.test_algorithm,
                    "traffic_allocation": experiment.traffic_allocation,
                    "primary_metric": experiment.primary_metric
                }
                
                # Cache for future use
                self._active_experiments[experiment_id] = config
                return config
                
        except SQLAlchemyError as e:
            logger.error(f"Database error getting experiment config: {e}")
            return None
    
    async def _get_user_assignment(
        self,
        experiment_id: str,
        user_profile_id: str
    ) -> Optional[ABTestAssignment]:
        """Get user assignment for experiment."""
        
        # Check cache first
        cache_key = f"{experiment_id}:{user_profile_id}"
        if cache_key in self._user_assignments:
            cached = self._user_assignments[cache_key]
            if cached["is_active"]:
                # Return mock assignment object
                assignment = type('Assignment', (), {
                    'test_group': cached["test_group"],
                    'assignment_date': cached["assignment_date"],
                    'is_active': cached["is_active"]
                })()
                return assignment
        
        try:
            with db_service.get_session() as session:
                assignment = session.query(ABTestAssignment).filter_by(
                    experiment_id=experiment_id,
                    user_profile_id=user_profile_id,
                    is_active=True
                ).first()
                
                if assignment:
                    # Cache assignment
                    self._user_assignments[cache_key] = {
                        "test_group": assignment.test_group,
                        "assignment_date": assignment.assignment_date,
                        "is_active": assignment.is_active
                    }
                
                return assignment
                
        except SQLAlchemyError as e:
            logger.error(f"Database error getting user assignment: {e}")
            return None
    
    async def _get_active_experiments_by_type(self, experiment_type: str) -> List[Dict[str, Any]]:
        """Get active experiments by type."""
        
        try:
            with db_service.get_session() as session:
                experiments = session.query(ABTestExperiment).filter_by(
                    experiment_type=experiment_type,
                    status=ExperimentStatus.ACTIVE.value
                ).all()
                
                result = []
                for exp in experiments:
                    # Check if experiment hasn't expired
                    if exp.end_date and datetime.utcnow() > exp.end_date:
                        # Auto-complete expired experiment
                        exp.status = ExperimentStatus.COMPLETED.value
                        exp.updated_at = datetime.utcnow()
                        session.commit()
                        continue
                    
                    result.append({
                        "id": str(exp.id),
                        "experiment_type": exp.experiment_type,
                        "control_algorithm": exp.control_algorithm,
                        "test_algorithm": exp.test_algorithm,
                        "traffic_allocation": exp.traffic_allocation,
                        "primary_metric": exp.primary_metric
                    })
                
                return result
                
        except SQLAlchemyError as e:
            logger.error(f"Database error getting active experiments: {e}")
            return []


# Global instance for easy access
ab_testing_engine = ABTestingEngine()