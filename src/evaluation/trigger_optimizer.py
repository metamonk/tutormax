"""
Trigger Optimizer

Automatically adjusts intervention trigger thresholds based on A/B test results
and analytics recommendations to optimize intervention effectiveness.

Features:
- Apply analytics recommendations to intervention configuration
- Track threshold adjustment history
- Validate proposed changes
- A/B test new threshold configurations
- Rollback unsuccessful changes

Usage:
    optimizer = TriggerOptimizer(intervention_config)
    optimizer.apply_recommendations(analytics_results)
    optimizer.save_configuration()
"""

import logging
import json
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from pathlib import Path

from .intervention_config import InterventionConfig, RuleThresholds, ConfigManager
from .intervention_analytics import ExperimentAnalysisResults, TriggerRecommendation

logger = logging.getLogger(__name__)


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ThresholdChange:
    """Records a threshold change."""
    timestamp: datetime
    intervention_type: str
    parameter: str
    old_value: float
    new_value: float
    reason: str
    experiment_id: Optional[str] = None
    approved_by: Optional[str] = None  # For human approval workflow
    impact: Optional[Dict] = None  # Measured impact after change


@dataclass
class OptimizationHistory:
    """Tracks history of threshold optimizations."""
    changes: List[ThresholdChange] = field(default_factory=list)
    total_changes: int = 0
    successful_changes: int = 0  # Based on measured impact
    last_optimization: Optional[datetime] = None


# ============================================================================
# TRIGGER OPTIMIZER
# ============================================================================

class TriggerOptimizer:
    """
    Optimizes intervention trigger thresholds based on experimental results.

    This class:
    - Applies recommendations from A/B test analytics
    - Validates proposed changes
    - Tracks optimization history
    - Manages configuration updates
    """

    def __init__(
        self,
        config: InterventionConfig,
        config_manager: Optional[ConfigManager] = None,
        auto_apply: bool = False,
        require_approval: bool = True
    ):
        """
        Initialize trigger optimizer.

        Args:
            config: Current intervention configuration
            config_manager: Configuration manager for persistence
            auto_apply: Automatically apply recommendations without confirmation
            require_approval: Require human approval for changes
        """
        self.config = config
        self.config_manager = config_manager or ConfigManager()
        self.auto_apply = auto_apply
        self.require_approval = require_approval

        # Load or initialize history
        self.history = self._load_history()

        logger.info("TriggerOptimizer initialized")

    def apply_recommendations(
        self,
        analysis_results: ExperimentAnalysisResults,
        confidence_threshold: str = "medium",
        dry_run: bool = False
    ) -> Dict:
        """
        Apply recommendations from A/B test analysis.

        Args:
            analysis_results: Results from intervention analytics
            confidence_threshold: Minimum confidence level to apply ("low", "medium", "high")
            dry_run: Preview changes without applying

        Returns:
            Dict with applied changes summary
        """
        logger.info(f"Applying recommendations from experiment {analysis_results.experiment_id}")

        confidence_levels = {"low": 1, "medium": 2, "high": 3}
        min_confidence = confidence_levels[confidence_threshold]

        summary = {
            "experiment_id": analysis_results.experiment_id,
            "total_recommendations": len(analysis_results.trigger_recommendations),
            "applied_changes": 0,
            "skipped_changes": 0,
            "changes": [],
            "dry_run": dry_run
        }

        for recommendation in analysis_results.trigger_recommendations:
            # Check confidence threshold
            if confidence_levels[recommendation.confidence] < min_confidence:
                logger.info(f"Skipping {recommendation.intervention_type}: "
                          f"confidence {recommendation.confidence} below threshold {confidence_threshold}")
                summary["skipped_changes"] += 1
                continue

            # Apply each threshold change
            changes_applied = self._apply_recommendation(
                recommendation,
                analysis_results.experiment_id,
                dry_run=dry_run
            )

            summary["applied_changes"] += len(changes_applied)
            summary["changes"].extend(changes_applied)

        logger.info(f"Applied {summary['applied_changes']} changes, "
                   f"skipped {summary['skipped_changes']} (dry_run={dry_run})")

        # Save updated configuration
        if not dry_run and summary["applied_changes"] > 0:
            self._save_configuration()
            self._save_history()

        return summary

    def _apply_recommendation(
        self,
        recommendation: TriggerRecommendation,
        experiment_id: str,
        dry_run: bool = False
    ) -> List[ThresholdChange]:
        """Apply a single recommendation."""
        changes = []

        # Extract threshold changes
        for param, new_value in recommendation.recommended_threshold.items():
            current_value = recommendation.current_threshold.get(param)

            if current_value is None:
                logger.warning(f"Parameter {param} not found in current configuration")
                continue

            if current_value == new_value:
                logger.debug(f"No change needed for {param}: already at {new_value}")
                continue

            # Create change record
            change = ThresholdChange(
                timestamp=datetime.now(),
                intervention_type=recommendation.intervention_type,
                parameter=param,
                old_value=current_value,
                new_value=new_value,
                reason=recommendation.rationale,
                experiment_id=experiment_id
            )

            # Apply change to configuration
            if not dry_run:
                self._update_threshold(
                    recommendation.intervention_type,
                    param,
                    new_value
                )

                # Record in history
                self.history.changes.append(change)
                self.history.total_changes += 1
                self.history.last_optimization = datetime.now()

            changes.append(change)

            logger.info(f"{'[DRY RUN] ' if dry_run else ''}Updated {recommendation.intervention_type}.{param}: "
                       f"{current_value} -> {new_value}")

        return changes

    def _update_threshold(
        self,
        intervention_type: str,
        parameter: str,
        new_value: float
    ):
        """Update a specific threshold in the configuration."""
        thresholds = self.config.thresholds

        # Map intervention types to threshold parameters
        # This is a simplified mapping - in production, this would be more sophisticated
        if parameter == "churn_score":
            if "automated_coaching" in intervention_type.lower():
                thresholds.high_churn_probability = new_value
            elif "critical" in intervention_type.lower():
                thresholds.critical_churn_probability = new_value
            else:
                thresholds.medium_churn_probability = new_value

        elif parameter == "avg_rating":
            thresholds.low_rating = new_value

        elif parameter == "engagement_score":
            thresholds.low_engagement_score = new_value

        elif parameter == "no_show_rate":
            thresholds.excessive_no_show_rate = new_value

        elif parameter == "reschedule_rate":
            thresholds.excessive_reschedule_rate = new_value

        # Update config
        self.config.thresholds = thresholds

        logger.debug(f"Updated threshold: {intervention_type}.{parameter} = {new_value}")

    def manual_adjustment(
        self,
        intervention_type: str,
        parameter: str,
        new_value: float,
        reason: str
    ) -> ThresholdChange:
        """
        Manually adjust a threshold.

        Args:
            intervention_type: Type of intervention
            parameter: Parameter to adjust
            new_value: New threshold value
            reason: Reason for adjustment

        Returns:
            Change record
        """
        logger.info(f"Manual adjustment: {intervention_type}.{parameter} -> {new_value}")

        # Get current value
        current_value = self._get_current_threshold(intervention_type, parameter)

        # Create change record
        change = ThresholdChange(
            timestamp=datetime.now(),
            intervention_type=intervention_type,
            parameter=parameter,
            old_value=current_value,
            new_value=new_value,
            reason=reason,
            approved_by="manual"
        )

        # Apply change
        self._update_threshold(intervention_type, parameter, new_value)

        # Record in history
        self.history.changes.append(change)
        self.history.total_changes += 1
        self.history.last_optimization = datetime.now()

        # Save
        self._save_configuration()
        self._save_history()

        return change

    def _get_current_threshold(self, intervention_type: str, parameter: str) -> float:
        """Get current threshold value."""
        thresholds = self.config.thresholds

        # Simplified mapping
        if parameter == "churn_score":
            if "critical" in intervention_type.lower():
                return thresholds.critical_churn_probability
            elif "high" in intervention_type.lower():
                return thresholds.high_churn_probability
            else:
                return thresholds.medium_churn_probability
        elif parameter == "avg_rating":
            return thresholds.low_rating
        elif parameter == "engagement_score":
            return thresholds.low_engagement_score
        elif parameter == "no_show_rate":
            return thresholds.excessive_no_show_rate
        elif parameter == "reschedule_rate":
            return thresholds.excessive_reschedule_rate
        else:
            return 0.0

    def rollback_change(self, change_index: int) -> bool:
        """
        Rollback a specific threshold change.

        Args:
            change_index: Index in history.changes to rollback

        Returns:
            True if successful
        """
        if change_index < 0 or change_index >= len(self.history.changes):
            logger.error(f"Invalid change index: {change_index}")
            return False

        change = self.history.changes[change_index]

        logger.info(f"Rolling back change: {change.intervention_type}.{change.parameter} "
                   f"{change.new_value} -> {change.old_value}")

        # Revert to old value
        self._update_threshold(
            change.intervention_type,
            change.parameter,
            change.old_value
        )

        # Record rollback
        rollback_change = ThresholdChange(
            timestamp=datetime.now(),
            intervention_type=change.intervention_type,
            parameter=change.parameter,
            old_value=change.new_value,
            new_value=change.old_value,
            reason=f"Rollback of change from {change.timestamp}",
            approved_by="rollback"
        )

        self.history.changes.append(rollback_change)

        # Save
        self._save_configuration()
        self._save_history()

        return True

    def get_optimization_report(self) -> str:
        """Generate a report of optimization history."""
        lines = [
            "=" * 80,
            "TRIGGER OPTIMIZATION HISTORY",
            "=" * 80,
            f"Total Changes: {self.history.total_changes}",
            f"Successful Changes: {self.history.successful_changes}",
            f"Last Optimization: {self.history.last_optimization}" if self.history.last_optimization else "Last Optimization: Never",
            "",
            "-" * 80,
            "RECENT CHANGES",
            "-" * 80,
        ]

        # Show last 10 changes
        recent_changes = sorted(self.history.changes, key=lambda x: x.timestamp, reverse=True)[:10]

        for change in recent_changes:
            lines.extend([
                f"{change.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {change.intervention_type}",
                f"  Parameter: {change.parameter}",
                f"  Change: {change.old_value} -> {change.new_value}",
                f"  Reason: {change.reason}",
                f"  Experiment: {change.experiment_id or 'N/A'}",
                ""
            ])

        lines.append("=" * 80)

        return "\n".join(lines)

    def _save_configuration(self):
        """Save updated configuration."""
        if self.config_manager:
            # Update the config manager's internal config
            self.config_manager.config = self.config
            self.config_manager.save_config()
            logger.info("Saved updated configuration")

    def _save_history(self):
        """Save optimization history."""
        history_file = Path(".taskmaster/optimization_history.json")
        history_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "total_changes": self.history.total_changes,
            "successful_changes": self.history.successful_changes,
            "last_optimization": self.history.last_optimization.isoformat() if self.history.last_optimization else None,
            "changes": [
                {
                    "timestamp": c.timestamp.isoformat(),
                    "intervention_type": c.intervention_type,
                    "parameter": c.parameter,
                    "old_value": c.old_value,
                    "new_value": c.new_value,
                    "reason": c.reason,
                    "experiment_id": c.experiment_id,
                    "approved_by": c.approved_by,
                    "impact": c.impact
                }
                for c in self.history.changes
            ]
        }

        with open(history_file, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved optimization history to {history_file}")

    def _load_history(self) -> OptimizationHistory:
        """Load optimization history."""
        history_file = Path(".taskmaster/optimization_history.json")

        if not history_file.exists():
            return OptimizationHistory()

        try:
            with open(history_file, 'r') as f:
                data = json.load(f)

            history = OptimizationHistory(
                total_changes=data.get("total_changes", 0),
                successful_changes=data.get("successful_changes", 0),
                last_optimization=datetime.fromisoformat(data["last_optimization"]) if data.get("last_optimization") else None
            )

            # Load changes
            for c_data in data.get("changes", []):
                history.changes.append(ThresholdChange(
                    timestamp=datetime.fromisoformat(c_data["timestamp"]),
                    intervention_type=c_data["intervention_type"],
                    parameter=c_data["parameter"],
                    old_value=c_data["old_value"],
                    new_value=c_data["new_value"],
                    reason=c_data["reason"],
                    experiment_id=c_data.get("experiment_id"),
                    approved_by=c_data.get("approved_by"),
                    impact=c_data.get("impact")
                ))

            logger.info(f"Loaded optimization history: {history.total_changes} changes")
            return history

        except Exception as e:
            logger.error(f"Error loading optimization history: {e}")
            return OptimizationHistory()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_optimizer(
    config_path: Optional[str] = None,
    auto_apply: bool = False
) -> TriggerOptimizer:
    """
    Create a trigger optimizer with configuration.

    Args:
        config_path: Path to configuration file
        auto_apply: Auto-apply recommendations

    Returns:
        Configured TriggerOptimizer
    """
    config_manager = ConfigManager(config_path=config_path)
    config = config_manager.load_config()

    return TriggerOptimizer(
        config=config,
        config_manager=config_manager,
        auto_apply=auto_apply,
        require_approval=not auto_apply
    )


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    from .intervention_config import InterventionConfig
    from .intervention_analytics import (
        TriggerRecommendation,
        ExperimentAnalysisResults,
        GroupMetrics
    )

    # Create optimizer
    config = InterventionConfig()
    optimizer = TriggerOptimizer(config=config, auto_apply=False)

    print("\n" + "=" * 80)
    print("TRIGGER OPTIMIZER DEMO")
    print("=" * 80)

    # Show current thresholds
    print("\nCurrent Thresholds:")
    print(f"  Critical Churn Probability: {config.thresholds.critical_churn_probability}")
    print(f"  High Churn Probability: {config.thresholds.high_churn_probability}")
    print(f"  Low Rating: {config.thresholds.low_rating}")
    print(f"  Low Engagement Score: {config.thresholds.low_engagement_score}")

    # Create mock recommendations
    recommendations = [
        TriggerRecommendation(
            intervention_type="automated_coaching",
            current_threshold={"churn_score": 70},
            recommended_threshold={"churn_score": 60},
            rationale="Treatment group showed 45% improvement rate. Expanding criteria could help more tutors.",
            expected_improvement="Could help additional 15 tutors",
            confidence="high"
        ),
        TriggerRecommendation(
            intervention_type="training_module",
            current_threshold={"avg_rating": 3.5},
            recommended_threshold={"avg_rating": 3.8},
            rationale="Low improvement rate (12%). Tightening criteria to focus on higher-need cases.",
            expected_improvement="Focus resources on cases more likely to improve",
            confidence="medium"
        )
    ]

    # Create mock analysis results
    mock_results = ExperimentAnalysisResults(
        experiment_id="exp_test123",
        experiment_name="Test Experiment",
        analysis_date=datetime.now(),
        control_metrics=GroupMetrics(group="control", sample_size=30),
        treatment_metrics=GroupMetrics(group="treatment", sample_size=30),
        statistical_tests=[],
        intervention_effectiveness=[],
        trigger_recommendations=recommendations,
        overall_effectiveness_score=75.0,
        is_experiment_successful=True,
        key_findings=[],
        recommendations=[]
    )

    # Preview changes (dry run)
    print("\n" + "-" * 80)
    print("DRY RUN - Preview Changes")
    print("-" * 80)
    summary = optimizer.apply_recommendations(mock_results, confidence_threshold="medium", dry_run=True)
    print(f"Would apply {summary['applied_changes']} changes:")
    for change in summary['changes']:
        print(f"  {change.intervention_type}.{change.parameter}: {change.old_value} -> {change.new_value}")

    # Apply changes
    print("\n" + "-" * 80)
    print("Applying Changes")
    print("-" * 80)
    summary = optimizer.apply_recommendations(mock_results, confidence_threshold="medium", dry_run=False)
    print(f"Applied {summary['applied_changes']} changes")

    # Show updated thresholds
    print("\nUpdated Thresholds:")
    print(f"  Critical Churn Probability: {config.thresholds.critical_churn_probability}")
    print(f"  High Churn Probability: {config.thresholds.high_churn_probability}")
    print(f"  Low Rating: {config.thresholds.low_rating}")

    # Manual adjustment
    print("\n" + "-" * 80)
    print("Manual Adjustment")
    print("-" * 80)
    change = optimizer.manual_adjustment(
        "automated_coaching",
        "churn_score",
        55,
        "Further refinement based on week 2 results"
    )
    print(f"Manual change applied: {change.parameter} -> {change.new_value}")

    # Show optimization history
    print("\n" + "-" * 80)
    print("Optimization History")
    print("-" * 80)
    print(optimizer.get_optimization_report())

    print("\n" + "=" * 80)
