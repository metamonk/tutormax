"""
Unit Tests for Intervention A/B Testing Framework

Tests the core functionality of:
- Experiment creation and configuration
- Tutor assignment (random and stratified)
- Outcome tracking
- Experiment persistence (save/load)
"""

import pytest
import tempfile
import json
from datetime import datetime, timedelta
from pathlib import Path

from src.evaluation.intervention_ab_testing import (
    InterventionExperiment,
    ExperimentConfig,
    ABTestGroup,
    OutcomeType,
    TutorAssignment,
    InterventionOutcomeRecord,
    create_churn_prevention_experiment
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def basic_config():
    """Create a basic experiment configuration."""
    return ExperimentConfig(
        experiment_id="test_exp_001",
        name="Test Experiment",
        description="Test experiment for unit tests",
        start_date=datetime.now(),
        assignment_strategy="random",
        control_allocation=0.5,
        treatment_allocation=0.5,
        intervention_types=["automated_coaching"],
        success_metrics=["churn_rate", "avg_rating"],
        minimum_sample_size=10,
        is_active=True
    )


@pytest.fixture
def stratified_config():
    """Create a stratified experiment configuration."""
    return ExperimentConfig(
        experiment_id="test_exp_002",
        name="Stratified Test Experiment",
        description="Test experiment with stratification",
        start_date=datetime.now(),
        assignment_strategy="stratified",
        stratification_keys=["risk_level", "performance_tier"],
        control_allocation=0.5,
        treatment_allocation=0.5,
        intervention_types=["automated_coaching", "manager_coaching"],
        success_metrics=["churn_rate", "avg_rating", "engagement_score"],
        minimum_sample_size=20,
        is_active=True
    )


@pytest.fixture
def experiment(basic_config):
    """Create a basic experiment."""
    return InterventionExperiment(config=basic_config)


@pytest.fixture
def stratified_experiment(stratified_config):
    """Create a stratified experiment."""
    return InterventionExperiment(config=stratified_config)


# ============================================================================
# TEST: EXPERIMENT INITIALIZATION
# ============================================================================

def test_experiment_creation(experiment):
    """Test experiment initialization."""
    assert experiment.config.experiment_id == "test_exp_001"
    assert experiment.config.name == "Test Experiment"
    assert experiment.config.assignment_strategy == "random"
    assert len(experiment.assignments) == 0
    assert len(experiment.outcomes) == 0


def test_create_churn_prevention_experiment():
    """Test helper function for creating churn prevention experiment."""
    experiment = create_churn_prevention_experiment(stratify=True)

    assert experiment.config.assignment_strategy == "stratified"
    assert "risk_level" in experiment.config.stratification_keys
    assert "performance_tier" in experiment.config.stratification_keys
    assert experiment.config.control_allocation == 0.5
    assert experiment.config.treatment_allocation == 0.5


# ============================================================================
# TEST: RANDOM ASSIGNMENT
# ============================================================================

def test_random_assignment(experiment):
    """Test random assignment to control/treatment groups."""
    # Assign 100 tutors
    for i in range(100):
        tutor_id = f"T{i:03d}"
        group = experiment.assign_tutor(tutor_id)
        assert group in [ABTestGroup.CONTROL, ABTestGroup.TREATMENT]

    # Check that both groups have tutors
    groups = experiment.get_group_assignments()
    assert len(groups[ABTestGroup.CONTROL.value]) > 0
    assert len(groups[ABTestGroup.TREATMENT.value]) > 0

    # Check roughly 50/50 split (with some tolerance)
    control_count = len(groups[ABTestGroup.CONTROL.value])
    treatment_count = len(groups[ABTestGroup.TREATMENT.value])
    ratio = control_count / treatment_count
    assert 0.6 <= ratio <= 1.7  # Allow 40% deviation for random sampling


def test_duplicate_assignment(experiment):
    """Test that duplicate assignments are prevented."""
    tutor_id = "T001"

    # First assignment
    group1 = experiment.assign_tutor(tutor_id)

    # Second assignment (should return same group)
    group2 = experiment.assign_tutor(tutor_id)

    assert group1 == group2
    assert len(experiment.assignments) == 1


def test_force_group_assignment(experiment):
    """Test forcing assignment to specific group."""
    # Force control group
    group = experiment.assign_tutor("T001", force_group=ABTestGroup.CONTROL)
    assert group == ABTestGroup.CONTROL

    # Force treatment group
    group = experiment.assign_tutor("T002", force_group=ABTestGroup.TREATMENT)
    assert group == ABTestGroup.TREATMENT


# ============================================================================
# TEST: STRATIFIED ASSIGNMENT
# ============================================================================

def test_stratified_assignment(stratified_experiment):
    """Test stratified assignment balances groups within strata."""
    # Create tutors with different characteristics
    tutors = [
        {"tutor_id": f"H{i:02d}", "risk_level": "HIGH", "performance_tier": "At Risk"}
        for i in range(20)
    ] + [
        {"tutor_id": f"M{i:02d}", "risk_level": "MEDIUM", "performance_tier": "Developing"}
        for i in range(20)
    ]

    # Assign all tutors
    for tutor in tutors:
        stratified_experiment.assign_tutor(
            tutor["tutor_id"],
            tutor_state=tutor
        )

    # Check that stratification buckets were created
    assert len(stratified_experiment.stratification_buckets) == 2

    # Check balance within each stratum
    for bucket_key, tutor_ids in stratified_experiment.stratification_buckets.items():
        control_count = sum(
            1 for tid in tutor_ids
            if stratified_experiment.assignments[tid].group == ABTestGroup.CONTROL
        )
        treatment_count = sum(
            1 for tid in tutor_ids
            if stratified_experiment.assignments[tid].group == ABTestGroup.TREATMENT
        )

        # Should be roughly balanced (within 1-2 tutors)
        assert abs(control_count - treatment_count) <= 2


# ============================================================================
# TEST: INTERVENTION DECISIONS
# ============================================================================

def test_should_receive_intervention(experiment):
    """Test intervention decision based on group assignment."""
    # Assign to treatment - should receive intervention
    experiment.assign_tutor("T001", force_group=ABTestGroup.TREATMENT)
    assert experiment.should_receive_intervention("T001") is True

    # Assign to control - should not receive intervention
    experiment.assign_tutor("T002", force_group=ABTestGroup.CONTROL)
    assert experiment.should_receive_intervention("T002") is False

    # Unknown tutor - defaults to True
    assert experiment.should_receive_intervention("T999") is True


# ============================================================================
# TEST: OUTCOME TRACKING
# ============================================================================

def test_record_outcome(experiment):
    """Test recording intervention outcomes."""
    # Assign tutor
    experiment.assign_tutor("T001", force_group=ABTestGroup.TREATMENT)

    # Record outcome
    metrics_before = {"avg_rating": 3.5, "engagement_score": 0.6}
    metrics_after = {"avg_rating": 4.2, "engagement_score": 0.75}

    outcome = experiment.record_outcome(
        tutor_id="T001",
        intervention_id="intv_001",
        intervention_type="automated_coaching",
        outcome_type=OutcomeType.PERFORMANCE_IMPROVED,
        metrics_before=metrics_before,
        metrics_after=metrics_after,
        notes="Tutor responded well"
    )

    # Check outcome was recorded
    assert len(experiment.outcomes) == 1
    assert outcome.tutor_id == "T001"
    assert outcome.intervention_id == "intv_001"
    assert outcome.outcome_type == OutcomeType.PERFORMANCE_IMPROVED

    # Check metrics change calculation
    assert "avg_rating" in outcome.metrics_change
    assert outcome.metrics_change["avg_rating"]["absolute"] == pytest.approx(0.7, abs=0.01)
    assert outcome.metrics_change["avg_rating"]["percent"] == pytest.approx(20.0, abs=1.0)


def test_outcome_types(experiment):
    """Test all outcome types can be recorded."""
    experiment.assign_tutor("T001", force_group=ABTestGroup.TREATMENT)

    outcome_types = [
        OutcomeType.PERFORMANCE_IMPROVED,
        OutcomeType.PERFORMANCE_STABLE,
        OutcomeType.PERFORMANCE_DECLINED,
        OutcomeType.CHURNED,
        OutcomeType.RESPONDED,
        OutcomeType.COMPLETED_ACTION
    ]

    for i, outcome_type in enumerate(outcome_types):
        experiment.record_outcome(
            tutor_id="T001",
            intervention_id=f"intv_{i:03d}",
            intervention_type="automated_coaching",
            outcome_type=outcome_type
        )

    assert len(experiment.outcomes) == len(outcome_types)


def test_time_to_outcome_calculation(experiment):
    """Test that time to outcome is calculated correctly."""
    # Assign tutor (sets assigned_at timestamp)
    experiment.assign_tutor("T001", force_group=ABTestGroup.TREATMENT)

    # Record outcome immediately
    outcome = experiment.record_outcome(
        tutor_id="T001",
        intervention_id="intv_001",
        intervention_type="automated_coaching",
        outcome_type=OutcomeType.PERFORMANCE_IMPROVED
    )

    # Time to outcome should be very small (< 1 second converted to days)
    assert outcome.time_to_outcome_days is not None
    assert outcome.time_to_outcome_days < 0.01  # Less than ~15 minutes


# ============================================================================
# TEST: EXPERIMENT STATISTICS
# ============================================================================

def test_get_group_assignments(experiment):
    """Test getting tutor IDs grouped by assignment."""
    # Assign tutors
    experiment.assign_tutor("T001", force_group=ABTestGroup.CONTROL)
    experiment.assign_tutor("T002", force_group=ABTestGroup.CONTROL)
    experiment.assign_tutor("T003", force_group=ABTestGroup.TREATMENT)
    experiment.assign_tutor("T004", force_group=ABTestGroup.TREATMENT)
    experiment.assign_tutor("T005", force_group=ABTestGroup.TREATMENT)

    groups = experiment.get_group_assignments()

    assert len(groups[ABTestGroup.CONTROL.value]) == 2
    assert len(groups[ABTestGroup.TREATMENT.value]) == 3
    assert "T001" in groups[ABTestGroup.CONTROL.value]
    assert "T003" in groups[ABTestGroup.TREATMENT.value]


def test_get_experiment_stats(experiment):
    """Test experiment statistics."""
    # Assign tutors
    for i in range(30):
        experiment.assign_tutor(f"T{i:03d}")

    # Record some outcomes
    for i in range(10):
        experiment.record_outcome(
            tutor_id=f"T{i:03d}",
            intervention_id=f"intv_{i:03d}",
            intervention_type="automated_coaching",
            outcome_type=OutcomeType.PERFORMANCE_IMPROVED
        )

    stats = experiment.get_experiment_stats()

    assert stats["experiment_id"] == "test_exp_001"
    assert stats["total_tutors"] == 30
    assert stats["total_outcomes"] == 10
    assert stats["meets_minimum_sample"] is True  # Minimum is 10 * 2 = 20


# ============================================================================
# TEST: PERSISTENCE (SAVE/LOAD)
# ============================================================================

def test_save_and_load_experiment(experiment):
    """Test saving and loading experiment to/from file."""
    # Populate experiment
    for i in range(10):
        tutor_id = f"T{i:03d}"
        experiment.assign_tutor(tutor_id)
        experiment.record_outcome(
            tutor_id=tutor_id,
            intervention_id=f"intv_{i:03d}",
            intervention_type="automated_coaching",
            outcome_type=OutcomeType.PERFORMANCE_IMPROVED,
            metrics_before={"avg_rating": 3.5},
            metrics_after={"avg_rating": 4.0}
        )

    # Save to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        filepath = f.name

    try:
        experiment.save_to_file(filepath)

        # Load from file
        loaded_experiment = InterventionExperiment.load_from_file(filepath)

        # Verify
        assert loaded_experiment.config.experiment_id == experiment.config.experiment_id
        assert len(loaded_experiment.assignments) == len(experiment.assignments)
        assert len(loaded_experiment.outcomes) == len(experiment.outcomes)

        # Check specific assignment
        assert "T001" in loaded_experiment.assignments
        assert loaded_experiment.assignments["T001"].tutor_id == "T001"

        # Check specific outcome (outcome order may vary, so check all tutors are present)
        outcome_tutor_ids = {outcome.tutor_id for outcome in loaded_experiment.outcomes}
        assert "T001" in outcome_tutor_ids
        assert "T005" in outcome_tutor_ids

    finally:
        # Cleanup
        Path(filepath).unlink()


def test_to_dict_serialization(experiment):
    """Test experiment serialization to dictionary."""
    # Populate experiment
    experiment.assign_tutor("T001", force_group=ABTestGroup.TREATMENT)
    experiment.record_outcome(
        tutor_id="T001",
        intervention_id="intv_001",
        intervention_type="automated_coaching",
        outcome_type=OutcomeType.PERFORMANCE_IMPROVED
    )

    # Serialize
    data = experiment.to_dict()

    # Verify structure
    assert "config" in data
    assert "assignments" in data
    assert "outcomes" in data
    assert "stats" in data

    # Verify config
    assert data["config"]["experiment_id"] == "test_exp_001"
    assert data["config"]["name"] == "Test Experiment"

    # Verify assignments
    assert "T001" in data["assignments"]
    assert data["assignments"]["T001"]["group"] == ABTestGroup.TREATMENT.value

    # Verify outcomes
    assert len(data["outcomes"]) == 1
    assert data["outcomes"][0]["tutor_id"] == "T001"


# ============================================================================
# TEST: EDGE CASES
# ============================================================================

def test_empty_experiment_stats(experiment):
    """Test stats with no data."""
    stats = experiment.get_experiment_stats()

    assert stats["total_tutors"] == 0
    assert stats["total_outcomes"] == 0
    assert stats["meets_minimum_sample"] is False


def test_outcome_without_assignment(experiment):
    """Test recording outcome for tutor not in experiment."""
    # Record outcome without prior assignment
    outcome = experiment.record_outcome(
        tutor_id="T999",
        intervention_id="intv_999",
        intervention_type="automated_coaching",
        outcome_type=OutcomeType.PERFORMANCE_IMPROVED
    )

    # Should still work, but time_to_outcome will be None
    assert outcome.tutor_id == "T999"
    assert outcome.time_to_outcome_days is None


def test_metrics_change_with_zero_division(experiment):
    """Test metrics change calculation handles zero values."""
    experiment.assign_tutor("T001")

    # Metrics with zero value (would cause division by zero for percent change)
    outcome = experiment.record_outcome(
        tutor_id="T001",
        intervention_id="intv_001",
        intervention_type="automated_coaching",
        outcome_type=OutcomeType.PERFORMANCE_IMPROVED,
        metrics_before={"sessions_completed": 0},
        metrics_after={"sessions_completed": 5}
    )

    # Should handle gracefully
    assert "sessions_completed" in outcome.metrics_change
    assert outcome.metrics_change["sessions_completed"]["absolute"] == 5
    assert outcome.metrics_change["sessions_completed"]["percent"] == 0  # Avoid division by zero


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
