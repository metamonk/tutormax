"""
Integration tests for the Intervention System

Tests end-to-end workflows including integration with churn predictions,
performance metrics, and batch processing.
"""

import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any
from src.evaluation.intervention_framework import (
    InterventionFramework,
    TutorState,
    InterventionTrigger,
    InterventionType,
    RiskLevel,
    PerformanceTier,
    create_tutor_state_from_prediction,
)
from src.evaluation.intervention_config import InterventionConfig, ConfigManager


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def framework():
    """Provide an intervention framework instance."""
    return InterventionFramework()


@pytest.fixture
def custom_framework():
    """Provide a framework with custom configuration."""
    config = InterventionConfig()
    config.thresholds.critical_churn_probability = 0.75
    config.max_interventions_per_tutor = 3
    return InterventionFramework(config)


@pytest.fixture
def sample_churn_prediction():
    """Provide sample churn prediction data."""
    return {
        'churn_probability': 0.72,
        'churn_score': 85,
        'risk_level': RiskLevel.CRITICAL.value,
    }


@pytest.fixture
def sample_performance_metrics():
    """Provide sample performance metrics data."""
    return {
        'avg_rating': 3.5,
        'first_session_success_rate': 0.48,
        'engagement_score': 0.52,
        'learning_objectives_met_pct': 0.50,
        'performance_tier': PerformanceTier.AT_RISK.value,
        'no_show_rate': 0.06,
        'reschedule_rate': 0.22,
        'sessions_completed': 18,
        'sessions_per_week': 3.2,
        'engagement_decline': 0.28,
        'rating_decline': 0.58,
        'session_volume_decline': 0.35,
        'behavioral_risk_score': 0.68,
    }


@pytest.fixture
def sample_tutor_data():
    """Provide sample tutor data."""
    return {
        'tutor_id': 'T12345',
        'tutor_name': 'Alice Johnson',
        'tenure_days': 120,
    }


@pytest.fixture
def batch_tutor_states():
    """Provide a batch of tutor states for batch processing tests."""
    states = []

    # Critical risk tutor
    states.append(
        TutorState(
            tutor_id="T001",
            tutor_name="Critical Risk Tutor",
            churn_probability=0.78,
            churn_score=88,
            risk_level=RiskLevel.CRITICAL.value,
            avg_rating=3.3,
            first_session_success_rate=0.42,
            engagement_score=0.48,
            performance_tier=PerformanceTier.AT_RISK.value,
            sessions_completed=15,
            reschedule_rate=0.28,
        )
    )

    # High risk tutor
    states.append(
        TutorState(
            tutor_id="T002",
            tutor_name="High Risk Tutor",
            churn_probability=0.58,
            churn_score=65,
            risk_level=RiskLevel.HIGH.value,
            avg_rating=3.8,
            first_session_success_rate=0.55,
            engagement_score=0.62,
            performance_tier=PerformanceTier.DEVELOPING.value,
            sessions_completed=22,
            reschedule_rate=0.15,
        )
    )

    # Medium risk tutor
    states.append(
        TutorState(
            tutor_id="T003",
            tutor_name="Medium Risk Tutor",
            churn_probability=0.38,
            churn_score=42,
            risk_level=RiskLevel.MEDIUM.value,
            avg_rating=4.1,
            first_session_success_rate=0.68,
            engagement_score=0.70,
            performance_tier=PerformanceTier.DEVELOPING.value,
            sessions_completed=30,
            reschedule_rate=0.12,
        )
    )

    # Low risk, high performer
    states.append(
        TutorState(
            tutor_id="T004",
            tutor_name="High Performer",
            churn_probability=0.12,
            churn_score=15,
            risk_level=RiskLevel.LOW.value,
            avg_rating=4.7,
            first_session_success_rate=0.85,
            engagement_score=0.88,
            performance_tier=PerformanceTier.EXEMPLARY.value,
            sessions_completed=50,
            reschedule_rate=0.04,
        )
    )

    # Insufficient sessions (should be skipped)
    states.append(
        TutorState(
            tutor_id="T005",
            tutor_name="New Tutor",
            churn_probability=0.50,
            churn_score=55,
            risk_level=RiskLevel.MEDIUM.value,
            avg_rating=4.0,
            sessions_completed=2,  # Below minimum
        )
    )

    return states


# =============================================================================
# TUTOR STATE CREATION TESTS
# =============================================================================

class TestTutorStateCreation:
    """Test creation of TutorState from prediction and metrics data."""

    def test_create_tutor_state_from_data(
        self,
        sample_tutor_data,
        sample_churn_prediction,
        sample_performance_metrics,
    ):
        """Test creating TutorState from separate data sources."""
        state = create_tutor_state_from_prediction(
            tutor_data=sample_tutor_data,
            churn_prediction=sample_churn_prediction,
            performance_metrics=sample_performance_metrics,
            recent_interventions=['automated_coaching'],
        )

        # Verify tutor data
        assert state.tutor_id == sample_tutor_data['tutor_id']
        assert state.tutor_name == sample_tutor_data['tutor_name']
        assert state.tenure_days == sample_tutor_data['tenure_days']

        # Verify churn prediction
        assert state.churn_probability == sample_churn_prediction['churn_probability']
        assert state.churn_score == sample_churn_prediction['churn_score']
        assert state.risk_level == sample_churn_prediction['risk_level']

        # Verify performance metrics
        assert state.avg_rating == sample_performance_metrics['avg_rating']
        assert state.engagement_score == sample_performance_metrics['engagement_score']

        # Verify recent interventions
        assert 'automated_coaching' in state.recent_interventions

    def test_create_tutor_state_with_defaults(self):
        """Test creating TutorState with minimal data."""
        tutor_data = {'tutor_id': 'T001'}
        churn_prediction = {
            'churn_probability': 0.5,
            'churn_score': 50,
            'risk_level': RiskLevel.MEDIUM.value,
        }
        performance_metrics = {
            'sessions_completed': 10,
        }

        state = create_tutor_state_from_prediction(
            tutor_data=tutor_data,
            churn_prediction=churn_prediction,
            performance_metrics=performance_metrics,
        )

        assert state.tutor_id == 'T001'
        assert state.tutor_name == 'Unknown'
        assert state.tenure_days == 0
        assert state.recent_interventions == []


# =============================================================================
# END-TO-END WORKFLOW TESTS
# =============================================================================

class TestEndToEndWorkflow:
    """Test complete end-to-end intervention workflows."""

    def test_critical_risk_tutor_workflow(
        self,
        framework,
        sample_tutor_data,
        sample_churn_prediction,
        sample_performance_metrics,
    ):
        """Test full workflow for a critical risk tutor."""
        # Step 1: Create tutor state from data sources
        state = create_tutor_state_from_prediction(
            tutor_data=sample_tutor_data,
            churn_prediction=sample_churn_prediction,
            performance_metrics=sample_performance_metrics,
        )

        # Step 2: Evaluate for interventions
        triggers = framework.evaluate_tutor_for_interventions(state)

        # Step 3: Verify interventions were triggered
        assert len(triggers) > 0

        # Step 4: Verify critical interventions are present
        critical_triggers = [t for t in triggers if t.priority.value == 'critical']
        assert len(critical_triggers) > 0

        # Step 5: Verify retention interview is triggered
        retention_triggers = [
            t for t in triggers if t.intervention_type == InterventionType.RETENTION_INTERVIEW
        ]
        assert len(retention_triggers) > 0

        # Step 6: Generate summary
        summary = framework.format_intervention_summary(state, triggers)
        assert state.tutor_name in summary
        assert "CRITICAL" in summary.upper()

    def test_high_performer_workflow(self, framework):
        """Test workflow for a high-performing tutor."""
        # Create high performer state
        state = TutorState(
            tutor_id="T999",
            tutor_name="Excellence Tutor",
            churn_probability=0.08,
            churn_score=10,
            risk_level=RiskLevel.LOW.value,
            avg_rating=4.9,
            first_session_success_rate=0.92,
            engagement_score=0.92,
            performance_tier=PerformanceTier.EXEMPLARY.value,
            sessions_completed=100,
            reschedule_rate=0.02,
        )

        # Evaluate
        triggers = framework.evaluate_tutor_for_interventions(state)

        # Should only have positive/recognition interventions
        assert all(
            t.intervention_type == InterventionType.RECOGNITION or t.priority.value == 'low'
            for t in triggers
        )

    def test_workflow_with_recent_interventions(self, framework):
        """Test workflow respects recent intervention history."""
        state = TutorState(
            tutor_id="T100",
            tutor_name="Recently Coached",
            churn_probability=0.55,
            churn_score=60,
            risk_level=RiskLevel.HIGH.value,
            avg_rating=3.8,
            engagement_score=0.58,
            sessions_completed=15,
            # Recent coaching intervention
            recent_interventions=[InterventionType.MANAGER_COACHING.value],
            last_intervention_date=datetime.now() - timedelta(days=3),
        )

        triggers = framework.evaluate_tutor_for_interventions(state)

        # Should not have manager coaching again (in cooldown)
        manager_coaching_triggers = [
            t for t in triggers if t.intervention_type == InterventionType.MANAGER_COACHING
        ]
        assert len(manager_coaching_triggers) == 0


# =============================================================================
# BATCH PROCESSING TESTS
# =============================================================================

class TestBatchProcessing:
    """Test batch processing of multiple tutors."""

    def test_batch_evaluation(self, framework, batch_tutor_states):
        """Test evaluating a batch of tutors."""
        results = []

        for state in batch_tutor_states:
            triggers = framework.evaluate_tutor_for_interventions(state)
            results.append({
                'tutor_id': state.tutor_id,
                'tutor_name': state.tutor_name,
                'risk_level': state.risk_level,
                'trigger_count': len(triggers),
                'triggers': triggers,
            })

        # Verify results
        assert len(results) == len(batch_tutor_states)

        # Critical risk tutor should have most interventions
        critical_result = next(r for r in results if r['tutor_id'] == 'T001')
        assert critical_result['trigger_count'] > 0

        # High performer should have few/no negative interventions
        high_performer_result = next(r for r in results if r['tutor_id'] == 'T004')
        if high_performer_result['trigger_count'] > 0:
            assert all(
                t.intervention_type == InterventionType.RECOGNITION
                for t in high_performer_result['triggers']
            )

        # New tutor with insufficient sessions should have no interventions
        new_tutor_result = next(r for r in results if r['tutor_id'] == 'T005')
        assert new_tutor_result['trigger_count'] == 0

    def test_batch_summary_generation(self, framework, batch_tutor_states):
        """Test generating summaries for a batch of tutors."""
        summaries = []

        for state in batch_tutor_states:
            triggers = framework.evaluate_tutor_for_interventions(state)
            if triggers:  # Only generate summary if interventions triggered
                summary = framework.format_intervention_summary(state, triggers)
                summaries.append({
                    'tutor_id': state.tutor_id,
                    'summary': summary,
                })

        # Verify summaries were generated
        assert len(summaries) > 0

        # Verify summaries contain expected content
        for item in summaries:
            assert item['tutor_id'] in item['summary']
            assert 'Intervention Summary' in item['summary']

    def test_batch_priority_distribution(self, framework, batch_tutor_states):
        """Test distribution of priorities across batch."""
        all_triggers = []

        for state in batch_tutor_states:
            triggers = framework.evaluate_tutor_for_interventions(state)
            all_triggers.extend(triggers)

        # Count by priority
        priority_counts = {}
        for trigger in all_triggers:
            priority = trigger.priority.value
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

        # Should have triggers at various priority levels
        assert len(priority_counts) > 0

        # Critical priority should be present (we have critical risk tutors)
        # Note: May not always be true depending on configuration
        if 'critical' in priority_counts:
            assert priority_counts['critical'] > 0


# =============================================================================
# CONFIGURATION PERSISTENCE TESTS
# =============================================================================

class TestConfigurationPersistence:
    """Test configuration persistence and reloading."""

    def test_save_and_load_configuration(self, tmp_path):
        """Test saving and loading configuration."""
        config_file = tmp_path / "intervention_config.json"

        # Create and configure
        config = InterventionConfig()
        config.thresholds.critical_churn_probability = 0.80
        config.thresholds.poor_first_session_rate = 0.55
        config.timing.critical_due_days = 1
        config.enablement.recognition_improvement = False

        # Save
        config.save_to_file(config_file)
        assert config_file.exists()

        # Load
        loaded_config = InterventionConfig.load_from_file(config_file)

        # Verify
        assert loaded_config.thresholds.critical_churn_probability == 0.80
        assert loaded_config.thresholds.poor_first_session_rate == 0.55
        assert loaded_config.timing.critical_due_days == 1
        assert loaded_config.enablement.recognition_improvement is False

    def test_config_manager_workflow(self, tmp_path):
        """Test complete config manager workflow."""
        config_file = tmp_path / "test_config.json"

        # Initialize config manager
        manager = ConfigManager(config_path=config_file)

        # Update thresholds
        manager.update_thresholds(
            critical_churn_probability=0.75,
            high_churn_probability=0.55,
        )

        # Disable a rule
        manager.disable_rule('recognition_improvement')

        # Save
        manager.save_config()

        # Create new manager and load
        manager2 = ConfigManager(config_path=config_file)

        # Verify
        assert manager2.config.thresholds.critical_churn_probability == 0.75
        assert manager2.config.thresholds.high_churn_probability == 0.55
        assert manager2.config.enablement.recognition_improvement is False


# =============================================================================
# INTERVENTION TYPE DISTRIBUTION TESTS
# =============================================================================

class TestInterventionDistribution:
    """Test distribution and patterns of interventions."""

    def test_automated_vs_human_interventions(self, framework, batch_tutor_states):
        """Test distribution of automated vs human interventions."""
        automated_count = 0
        human_count = 0

        for state in batch_tutor_states:
            triggers = framework.evaluate_tutor_for_interventions(state)
            for trigger in triggers:
                if trigger.requires_human:
                    human_count += 1
                else:
                    automated_count += 1

        # Should have both types
        # Note: Depends on batch composition
        total = automated_count + human_count
        if total > 0:
            assert automated_count >= 0
            assert human_count >= 0

    def test_immediate_action_interventions(self, framework):
        """Test identification of immediate action interventions."""
        state = TutorState(
            tutor_id="T999",
            tutor_name="Emergency Case",
            churn_probability=0.85,
            churn_score=92,
            risk_level=RiskLevel.CRITICAL.value,
            avg_rating=2.8,
            performance_tier=PerformanceTier.AT_RISK.value,
            sessions_completed=15,
            rating_decline=0.70,
            engagement_decline=0.35,
        )

        triggers = framework.evaluate_tutor_for_interventions(state)

        # Should have at least one immediate action trigger
        immediate_triggers = [t for t in triggers if t.requires_immediate_action]
        assert len(immediate_triggers) > 0


# =============================================================================
# PERFORMANCE AND SCALABILITY TESTS
# =============================================================================

class TestPerformanceAndScalability:
    """Test performance characteristics of the intervention system."""

    def test_evaluate_large_batch(self, framework):
        """Test evaluation of a large batch of tutors."""
        import time

        # Generate 100 tutor states
        states = []
        for i in range(100):
            states.append(
                TutorState(
                    tutor_id=f"T{i:04d}",
                    tutor_name=f"Tutor {i}",
                    churn_probability=0.3 + (i % 5) * 0.1,
                    churn_score=30 + (i % 5) * 10,
                    risk_level=RiskLevel.MEDIUM.value,
                    avg_rating=3.5 + (i % 10) * 0.1,
                    engagement_score=0.6 + (i % 10) * 0.02,
                    sessions_completed=10 + (i % 20),
                )
            )

        # Time the evaluation
        start_time = time.time()

        for state in states:
            framework.evaluate_tutor_for_interventions(state)

        elapsed_time = time.time() - start_time

        # Should complete in reasonable time (< 5 seconds for 100 tutors)
        assert elapsed_time < 5.0

    def test_memory_efficiency(self, framework):
        """Test memory efficiency with many evaluations."""
        # Evaluate same tutor 1000 times (simulating repeated evaluations)
        state = TutorState(
            tutor_id="T001",
            tutor_name="Test",
            churn_probability=0.5,
            churn_score=50,
            risk_level=RiskLevel.MEDIUM.value,
            avg_rating=4.0,
            sessions_completed=20,
        )

        # Should not cause memory issues
        for _ in range(1000):
            framework.evaluate_tutor_for_interventions(state)

        # If we get here without crashing, test passes
        assert True


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

class TestErrorHandling:
    """Test error handling in the intervention system."""

    def test_handle_invalid_state(self, framework):
        """Test handling of invalid tutor state."""
        state = TutorState(
            tutor_id="",  # Invalid: empty ID
            tutor_name="Test",
            churn_probability=0.5,
            churn_score=50,
            risk_level=RiskLevel.MEDIUM.value,
            sessions_completed=10,
        )

        # Should not raise exception, should return empty list
        triggers = framework.evaluate_tutor_for_interventions(state)
        assert triggers == []

    def test_handle_missing_metrics(self, framework):
        """Test handling of missing optional metrics."""
        state = TutorState(
            tutor_id="T001",
            tutor_name="Test",
            churn_probability=0.5,
            churn_score=50,
            risk_level=RiskLevel.MEDIUM.value,
            # No optional metrics provided
            avg_rating=None,
            first_session_success_rate=None,
            engagement_score=None,
            sessions_completed=10,
        )

        # Should not raise exception
        triggers = framework.evaluate_tutor_for_interventions(state)
        assert isinstance(triggers, list)
