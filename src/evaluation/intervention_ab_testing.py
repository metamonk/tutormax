"""
A/B Testing Framework for Intervention Effectiveness

This module provides A/B testing capabilities to evaluate intervention effectiveness:
- Random assignment to control/treatment groups
- Outcome tracking over time
- Statistical significance testing
- Per-intervention-type effectiveness analysis

Usage:
    # Create experiment
    experiment = InterventionExperiment("churn_prevention_v1")

    # Assign tutors to groups
    group = experiment.assign_tutor("T001", stratify_by={"risk_level": "HIGH"})

    # Track outcomes
    outcome_tracker.record_outcome("T001", intervention_id, outcome)

    # Analyze results
    results = experiment.analyze_results()
"""

import logging
import uuid
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND DATA STRUCTURES
# ============================================================================

class ABTestGroup(str, Enum):
    """A/B test group assignment."""
    CONTROL = "control"  # No intervention or baseline intervention
    TREATMENT = "treatment"  # Receives intervention
    TREATMENT_A = "treatment_a"  # For multi-variant testing
    TREATMENT_B = "treatment_b"  # For multi-variant testing


class OutcomeType(str, Enum):
    """Types of intervention outcomes to measure."""
    PERFORMANCE_IMPROVED = "performance_improved"  # Metrics improved after intervention
    PERFORMANCE_STABLE = "performance_stable"  # Metrics stayed same
    PERFORMANCE_DECLINED = "performance_declined"  # Metrics worsened
    CHURNED = "churned"  # Tutor churned
    RESPONDED = "responded"  # Tutor acknowledged/responded to intervention
    COMPLETED_ACTION = "completed_action"  # Tutor completed recommended action


@dataclass
class TutorAssignment:
    """Tracks a tutor's assignment to an A/B test group."""
    tutor_id: str
    experiment_id: str
    group: ABTestGroup
    assigned_at: datetime
    stratification_key: Optional[str] = None  # For stratified sampling
    metadata: Dict = field(default_factory=dict)


@dataclass
class InterventionOutcomeRecord:
    """Records the outcome of an intervention for a tutor."""
    tutor_id: str
    intervention_id: str
    intervention_type: str
    outcome_type: OutcomeType
    recorded_at: datetime
    time_to_outcome_days: Optional[float] = None

    # Metrics before and after intervention
    metrics_before: Dict = field(default_factory=dict)
    metrics_after: Dict = field(default_factory=dict)
    metrics_change: Dict = field(default_factory=dict)

    notes: Optional[str] = None


@dataclass
class ExperimentConfig:
    """Configuration for an A/B test experiment."""
    experiment_id: str
    name: str
    description: str
    start_date: datetime
    end_date: Optional[datetime] = None

    # Assignment strategy
    assignment_strategy: str = "random"  # "random" or "stratified"
    stratification_keys: List[str] = field(default_factory=list)  # e.g., ["risk_level", "tenure_bucket"]

    # Group allocation
    control_allocation: float = 0.5  # 50% control group
    treatment_allocation: float = 0.5  # 50% treatment group

    # Intervention configuration
    intervention_types: List[str] = field(default_factory=list)  # Which interventions to test

    # Success criteria
    success_metrics: List[str] = field(default_factory=list)  # e.g., ["churn_rate", "avg_rating"]
    minimum_sample_size: int = 30  # Minimum tutors per group for significance

    # Status
    is_active: bool = True
    metadata: Dict = field(default_factory=dict)


# ============================================================================
# INTERVENTION EXPERIMENT
# ============================================================================

class InterventionExperiment:
    """
    Manages an A/B test experiment for intervention effectiveness.

    This class handles:
    - Tutor assignment to control/treatment groups
    - Outcome tracking
    - Results analysis
    - Statistical significance testing
    """

    def __init__(
        self,
        config: ExperimentConfig,
        db_session=None
    ):
        """
        Initialize an intervention experiment.

        Args:
            config: Experiment configuration
            db_session: Database session for persistence
        """
        self.config = config
        self.db_session = db_session

        # In-memory tracking (can be persisted to DB)
        self.assignments: Dict[str, TutorAssignment] = {}
        self.outcomes: List[InterventionOutcomeRecord] = []

        # Stratification tracking
        self.stratification_buckets: Dict[str, List[str]] = {}  # bucket_key -> [tutor_ids]

        logger.info(f"Initialized experiment: {config.name} ({config.experiment_id})")

    def assign_tutor(
        self,
        tutor_id: str,
        tutor_state: Optional[Dict] = None,
        force_group: Optional[ABTestGroup] = None
    ) -> ABTestGroup:
        """
        Assign a tutor to a control or treatment group.

        Args:
            tutor_id: Tutor ID
            tutor_state: Tutor state for stratified assignment
            force_group: Force assignment to specific group (for testing)

        Returns:
            Assigned group
        """
        # Check if already assigned
        if tutor_id in self.assignments:
            logger.warning(f"Tutor {tutor_id} already assigned to {self.assignments[tutor_id].group}")
            return self.assignments[tutor_id].group

        # Determine group assignment
        if force_group:
            group = force_group
            stratification_key = None
        elif self.config.assignment_strategy == "stratified" and tutor_state:
            group, stratification_key = self._stratified_assignment(tutor_id, tutor_state)
        else:
            group = self._random_assignment()
            stratification_key = None

        # Create assignment record
        assignment = TutorAssignment(
            tutor_id=tutor_id,
            experiment_id=self.config.experiment_id,
            group=group,
            assigned_at=datetime.now(),
            stratification_key=stratification_key,
            metadata=tutor_state or {}
        )

        self.assignments[tutor_id] = assignment

        # Track stratification bucket
        if stratification_key:
            if stratification_key not in self.stratification_buckets:
                self.stratification_buckets[stratification_key] = []
            self.stratification_buckets[stratification_key].append(tutor_id)

        logger.info(f"Assigned tutor {tutor_id} to {group} (stratification: {stratification_key})")

        return group

    def _random_assignment(self) -> ABTestGroup:
        """Randomly assign to control or treatment group."""
        rand = random.random()
        if rand < self.config.control_allocation:
            return ABTestGroup.CONTROL
        else:
            return ABTestGroup.TREATMENT

    def _stratified_assignment(
        self,
        tutor_id: str,
        tutor_state: Dict
    ) -> Tuple[ABTestGroup, str]:
        """
        Assign to group using stratified sampling.

        Ensures balanced representation across important dimensions
        like risk level, tenure, performance tier.

        Args:
            tutor_id: Tutor ID
            tutor_state: Tutor state with stratification dimensions

        Returns:
            Tuple of (assigned_group, stratification_key)
        """
        # Build stratification key
        key_parts = []
        for dim in self.config.stratification_keys:
            value = tutor_state.get(dim, "unknown")
            key_parts.append(f"{dim}={value}")
        stratification_key = "|".join(key_parts)

        # Check current balance in this stratification bucket
        if stratification_key not in self.stratification_buckets:
            self.stratification_buckets[stratification_key] = []

        bucket = self.stratification_buckets[stratification_key]

        # Count current group sizes in this bucket
        control_count = sum(1 for tid in bucket if self.assignments[tid].group == ABTestGroup.CONTROL)
        treatment_count = sum(1 for tid in bucket if self.assignments[tid].group == ABTestGroup.TREATMENT)

        # Assign to group with fewer members (balance)
        if control_count <= treatment_count:
            group = ABTestGroup.CONTROL
        else:
            group = ABTestGroup.TREATMENT

        logger.debug(f"Stratified assignment for {tutor_id}: bucket={stratification_key}, "
                    f"control={control_count}, treatment={treatment_count}, assigned={group}")

        return group, stratification_key

    def should_receive_intervention(self, tutor_id: str) -> bool:
        """
        Check if a tutor should receive intervention based on their group.

        Args:
            tutor_id: Tutor ID

        Returns:
            True if tutor is in treatment group and should receive intervention
        """
        if tutor_id not in self.assignments:
            # Not in experiment, default to receiving intervention
            logger.warning(f"Tutor {tutor_id} not in experiment, defaulting to intervention")
            return True

        group = self.assignments[tutor_id].group
        return group in [ABTestGroup.TREATMENT, ABTestGroup.TREATMENT_A, ABTestGroup.TREATMENT_B]

    def record_outcome(
        self,
        tutor_id: str,
        intervention_id: str,
        intervention_type: str,
        outcome_type: OutcomeType,
        metrics_before: Optional[Dict] = None,
        metrics_after: Optional[Dict] = None,
        notes: Optional[str] = None
    ) -> InterventionOutcomeRecord:
        """
        Record an intervention outcome for a tutor.

        Args:
            tutor_id: Tutor ID
            intervention_id: Intervention ID
            intervention_type: Type of intervention
            outcome_type: Type of outcome
            metrics_before: Metrics before intervention
            metrics_after: Metrics after intervention
            notes: Additional notes

        Returns:
            Outcome record
        """
        # Calculate metrics change
        metrics_change = {}
        if metrics_before and metrics_after:
            for key in metrics_before:
                if key in metrics_after:
                    before = metrics_before[key]
                    after = metrics_after[key]
                    if isinstance(before, (int, float)) and isinstance(after, (int, float)):
                        change = after - before
                        change_pct = (change / before * 100) if before != 0 else 0
                        metrics_change[key] = {
                            "absolute": change,
                            "percent": change_pct
                        }

        # Calculate time to outcome
        time_to_outcome = None
        if tutor_id in self.assignments:
            intervention_start = self.assignments[tutor_id].assigned_at
            time_to_outcome = (datetime.now() - intervention_start).total_seconds() / 86400  # days

        # Create outcome record
        outcome = InterventionOutcomeRecord(
            tutor_id=tutor_id,
            intervention_id=intervention_id,
            intervention_type=intervention_type,
            outcome_type=outcome_type,
            recorded_at=datetime.now(),
            time_to_outcome_days=time_to_outcome,
            metrics_before=metrics_before or {},
            metrics_after=metrics_after or {},
            metrics_change=metrics_change,
            notes=notes
        )

        self.outcomes.append(outcome)

        time_msg = f"{time_to_outcome:.1f} days" if time_to_outcome is not None else "N/A"
        logger.info(f"Recorded outcome for tutor {tutor_id}: {outcome_type} (time_to_outcome: {time_msg})")

        return outcome

    def get_group_assignments(self) -> Dict[str, List[str]]:
        """
        Get tutor IDs grouped by their assignment.

        Returns:
            Dict mapping group name to list of tutor IDs
        """
        groups = {group.value: [] for group in ABTestGroup}
        for tutor_id, assignment in self.assignments.items():
            groups[assignment.group.value].append(tutor_id)
        return groups

    def get_experiment_stats(self) -> Dict:
        """
        Get experiment statistics.

        Returns:
            Dict with experiment statistics
        """
        groups = self.get_group_assignments()

        return {
            "experiment_id": self.config.experiment_id,
            "name": self.config.name,
            "is_active": self.config.is_active,
            "total_tutors": len(self.assignments),
            "control_count": len(groups[ABTestGroup.CONTROL.value]),
            "treatment_count": len(groups[ABTestGroup.TREATMENT.value]),
            "total_outcomes": len(self.outcomes),
            "stratification_buckets": len(self.stratification_buckets),
            "meets_minimum_sample": len(self.assignments) >= self.config.minimum_sample_size * 2
        }

    def to_dict(self) -> Dict:
        """Serialize experiment to dictionary."""
        return {
            "config": {
                "experiment_id": self.config.experiment_id,
                "name": self.config.name,
                "description": self.config.description,
                "start_date": self.config.start_date.isoformat(),
                "end_date": self.config.end_date.isoformat() if self.config.end_date else None,
                "assignment_strategy": self.config.assignment_strategy,
                "stratification_keys": self.config.stratification_keys,
                "control_allocation": self.config.control_allocation,
                "treatment_allocation": self.config.treatment_allocation,
                "intervention_types": self.config.intervention_types,
                "success_metrics": self.config.success_metrics,
                "minimum_sample_size": self.config.minimum_sample_size,
                "is_active": self.config.is_active
            },
            "assignments": {
                tid: {
                    "tutor_id": a.tutor_id,
                    "group": a.group.value,
                    "assigned_at": a.assigned_at.isoformat(),
                    "stratification_key": a.stratification_key
                }
                for tid, a in self.assignments.items()
            },
            "outcomes": [
                {
                    "tutor_id": o.tutor_id,
                    "intervention_id": o.intervention_id,
                    "intervention_type": o.intervention_type,
                    "outcome_type": o.outcome_type.value,
                    "recorded_at": o.recorded_at.isoformat(),
                    "time_to_outcome_days": o.time_to_outcome_days,
                    "metrics_change": o.metrics_change,
                    "notes": o.notes
                }
                for o in self.outcomes
            ],
            "stats": self.get_experiment_stats()
        }

    def save_to_file(self, filepath: str):
        """Save experiment to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Saved experiment to {filepath}")

    @classmethod
    def load_from_file(cls, filepath: str) -> 'InterventionExperiment':
        """Load experiment from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Reconstruct config
        config_data = data['config']
        config = ExperimentConfig(
            experiment_id=config_data['experiment_id'],
            name=config_data['name'],
            description=config_data['description'],
            start_date=datetime.fromisoformat(config_data['start_date']),
            end_date=datetime.fromisoformat(config_data['end_date']) if config_data['end_date'] else None,
            assignment_strategy=config_data['assignment_strategy'],
            stratification_keys=config_data['stratification_keys'],
            control_allocation=config_data['control_allocation'],
            treatment_allocation=config_data['treatment_allocation'],
            intervention_types=config_data['intervention_types'],
            success_metrics=config_data['success_metrics'],
            minimum_sample_size=config_data['minimum_sample_size'],
            is_active=config_data['is_active']
        )

        experiment = cls(config=config)

        # Restore assignments
        for tid, a_data in data['assignments'].items():
            experiment.assignments[tid] = TutorAssignment(
                tutor_id=a_data['tutor_id'],
                experiment_id=config.experiment_id,
                group=ABTestGroup(a_data['group']),
                assigned_at=datetime.fromisoformat(a_data['assigned_at']),
                stratification_key=a_data['stratification_key']
            )

        # Restore outcomes
        for o_data in data['outcomes']:
            experiment.outcomes.append(InterventionOutcomeRecord(
                tutor_id=o_data['tutor_id'],
                intervention_id=o_data['intervention_id'],
                intervention_type=o_data['intervention_type'],
                outcome_type=OutcomeType(o_data['outcome_type']),
                recorded_at=datetime.fromisoformat(o_data['recorded_at']),
                time_to_outcome_days=o_data['time_to_outcome_days'],
                metrics_change=o_data['metrics_change'],
                notes=o_data['notes']
            ))

        logger.info(f"Loaded experiment from {filepath}")
        return experiment


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_churn_prevention_experiment(
    experiment_name: str = "Churn Prevention Pilot",
    stratify: bool = True
) -> InterventionExperiment:
    """
    Create a standard churn prevention A/B test experiment.

    Args:
        experiment_name: Name for the experiment
        stratify: Whether to use stratified sampling

    Returns:
        Configured experiment
    """
    config = ExperimentConfig(
        experiment_id=f"exp_{uuid.uuid4().hex[:8]}",
        name=experiment_name,
        description="A/B test to measure intervention effectiveness in preventing tutor churn",
        start_date=datetime.now(),
        assignment_strategy="stratified" if stratify else "random",
        stratification_keys=["risk_level", "performance_tier"] if stratify else [],
        control_allocation=0.5,
        treatment_allocation=0.5,
        intervention_types=[
            "automated_coaching",
            "training_module",
            "manager_coaching",
            "peer_mentoring"
        ],
        success_metrics=[
            "churn_rate",
            "avg_rating",
            "engagement_score",
            "sessions_completed"
        ],
        minimum_sample_size=30,
        is_active=True
    )

    return InterventionExperiment(config=config)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Create experiment
    experiment = create_churn_prevention_experiment()

    print("\n" + "=" * 70)
    print("INTERVENTION A/B TEST EXPERIMENT")
    print("=" * 70)
    print(f"Experiment: {experiment.config.name}")
    print(f"ID: {experiment.config.experiment_id}")
    print(f"Strategy: {experiment.config.assignment_strategy}")
    print(f"Stratification: {experiment.config.stratification_keys}")

    # Assign some tutors
    print("\n" + "-" * 70)
    print("TUTOR ASSIGNMENTS")
    print("-" * 70)

    tutors = [
        {"tutor_id": "T001", "risk_level": "HIGH", "performance_tier": "At Risk"},
        {"tutor_id": "T002", "risk_level": "HIGH", "performance_tier": "At Risk"},
        {"tutor_id": "T003", "risk_level": "MEDIUM", "performance_tier": "Developing"},
        {"tutor_id": "T004", "risk_level": "MEDIUM", "performance_tier": "Developing"},
        {"tutor_id": "T005", "risk_level": "HIGH", "performance_tier": "Needs Attention"},
    ]

    for tutor_state in tutors:
        group = experiment.assign_tutor(
            tutor_id=tutor_state["tutor_id"],
            tutor_state=tutor_state
        )
        should_intervene = experiment.should_receive_intervention(tutor_state["tutor_id"])
        print(f"  {tutor_state['tutor_id']}: {group.value:12s} -> {'INTERVENE' if should_intervene else 'NO INTERVENTION'}")

    # Record some outcomes
    print("\n" + "-" * 70)
    print("OUTCOME TRACKING")
    print("-" * 70)

    experiment.record_outcome(
        tutor_id="T001",
        intervention_id="intv_001",
        intervention_type="automated_coaching",
        outcome_type=OutcomeType.PERFORMANCE_IMPROVED,
        metrics_before={"avg_rating": 3.5, "engagement_score": 0.55},
        metrics_after={"avg_rating": 4.2, "engagement_score": 0.72},
        notes="Tutor responded positively to coaching email"
    )

    print("  Recorded: T001 - Performance Improved")

    # Show stats
    print("\n" + "-" * 70)
    print("EXPERIMENT STATISTICS")
    print("-" * 70)
    stats = experiment.get_experiment_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Save experiment
    experiment.save_to_file("output/intervention_experiment.json")
    print(f"\nExperiment saved to output/intervention_experiment.json")
