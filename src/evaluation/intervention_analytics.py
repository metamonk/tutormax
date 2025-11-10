"""
Intervention Analytics Module

Analyzes A/B test results to measure intervention effectiveness:
- Control vs treatment group comparison
- Statistical significance testing
- Per-intervention-type effectiveness
- Trigger threshold optimization recommendations
- Success metric calculation

Usage:
    analytics = InterventionAnalytics(experiment)
    results = analytics.analyze_experiment()
    recommendations = analytics.get_trigger_recommendations()
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime, timedelta
import json

from .intervention_ab_testing import (
    InterventionExperiment,
    ABTestGroup,
    OutcomeType,
    InterventionOutcomeRecord
)

logger = logging.getLogger(__name__)


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class GroupMetrics:
    """Metrics for a control or treatment group."""
    group: str
    sample_size: int

    # Outcome rates
    churn_rate: float = 0.0
    performance_improved_rate: float = 0.0
    performance_declined_rate: float = 0.0
    response_rate: float = 0.0
    action_completion_rate: float = 0.0

    # Metric changes
    avg_rating_change: float = 0.0
    engagement_score_change: float = 0.0
    sessions_completed_change: float = 0.0

    # Time metrics
    avg_time_to_improvement_days: Optional[float] = None
    avg_time_to_churn_days: Optional[float] = None

    # Raw data for statistical tests
    outcomes: List[InterventionOutcomeRecord] = field(default_factory=list)


@dataclass
class StatisticalTest:
    """Results of a statistical significance test."""
    metric: str
    control_value: float
    treatment_value: float
    absolute_difference: float
    relative_difference_pct: float
    p_value: float
    is_significant: bool  # p < 0.05
    confidence_interval_95: Tuple[float, float]
    sample_size_control: int
    sample_size_treatment: int


@dataclass
class InterventionTypeEffectiveness:
    """Effectiveness metrics for a specific intervention type."""
    intervention_type: str
    total_interventions: int

    # Success rates
    response_rate: float = 0.0
    improvement_rate: float = 0.0
    churn_prevention_rate: float = 0.0

    # Average outcomes
    avg_time_to_impact_days: Optional[float] = None
    avg_rating_improvement: float = 0.0
    avg_engagement_improvement: float = 0.0

    # Cost-effectiveness (if we had cost data)
    estimated_effectiveness_score: float = 0.0  # Composite score 0-100


@dataclass
class TriggerRecommendation:
    """Recommendation for adjusting intervention trigger thresholds."""
    intervention_type: str
    current_threshold: Dict
    recommended_threshold: Dict
    rationale: str
    expected_improvement: str
    confidence: str  # "low", "medium", "high"


@dataclass
class ExperimentAnalysisResults:
    """Complete analysis results for an A/B test experiment."""
    experiment_id: str
    experiment_name: str
    analysis_date: datetime

    # Group comparison
    control_metrics: GroupMetrics
    treatment_metrics: GroupMetrics

    # Statistical tests
    statistical_tests: List[StatisticalTest]

    # Intervention-specific analysis
    intervention_effectiveness: List[InterventionTypeEffectiveness]

    # Recommendations
    trigger_recommendations: List[TriggerRecommendation]

    # Overall assessment
    overall_effectiveness_score: float  # 0-100
    is_experiment_successful: bool
    key_findings: List[str]
    recommendations: List[str]


# ============================================================================
# INTERVENTION ANALYTICS
# ============================================================================

class InterventionAnalytics:
    """
    Analyzes intervention A/B test results to measure effectiveness.

    Performs:
    - Group comparison (control vs treatment)
    - Statistical significance testing
    - Per-intervention-type analysis
    - Trigger optimization recommendations
    """

    def __init__(
        self,
        experiment: InterventionExperiment,
        significance_level: float = 0.05,
        minimum_sample_size: int = 30
    ):
        """
        Initialize analytics engine.

        Args:
            experiment: Intervention experiment to analyze
            significance_level: P-value threshold for significance (default 0.05)
            minimum_sample_size: Minimum sample size for valid analysis
        """
        self.experiment = experiment
        self.significance_level = significance_level
        self.minimum_sample_size = minimum_sample_size

        logger.info(f"Initialized analytics for experiment: {experiment.config.name}")

    def analyze_experiment(self) -> ExperimentAnalysisResults:
        """
        Perform complete analysis of the experiment.

        Returns:
            Complete analysis results
        """
        logger.info(f"Analyzing experiment: {self.experiment.config.experiment_id}")

        # Calculate group metrics
        control_metrics = self._calculate_group_metrics(ABTestGroup.CONTROL)
        treatment_metrics = self._calculate_group_metrics(ABTestGroup.TREATMENT)

        # Statistical tests
        statistical_tests = self._perform_statistical_tests(control_metrics, treatment_metrics)

        # Per-intervention analysis
        intervention_effectiveness = self._analyze_intervention_types()

        # Generate recommendations
        trigger_recommendations = self._generate_trigger_recommendations(
            treatment_metrics,
            intervention_effectiveness
        )

        # Overall assessment
        overall_score, is_successful, findings, recommendations = self._assess_experiment(
            control_metrics,
            treatment_metrics,
            statistical_tests
        )

        # Compile results
        results = ExperimentAnalysisResults(
            experiment_id=self.experiment.config.experiment_id,
            experiment_name=self.experiment.config.name,
            analysis_date=datetime.now(),
            control_metrics=control_metrics,
            treatment_metrics=treatment_metrics,
            statistical_tests=statistical_tests,
            intervention_effectiveness=intervention_effectiveness,
            trigger_recommendations=trigger_recommendations,
            overall_effectiveness_score=overall_score,
            is_experiment_successful=is_successful,
            key_findings=findings,
            recommendations=recommendations
        )

        logger.info(f"Analysis complete. Overall effectiveness: {overall_score:.1f}/100")

        return results

    def _calculate_group_metrics(self, group: ABTestGroup) -> GroupMetrics:
        """Calculate metrics for a specific group."""
        # Get tutors in this group
        tutor_ids = [
            tid for tid, assignment in self.experiment.assignments.items()
            if assignment.group == group
        ]

        # Get outcomes for this group
        outcomes = [
            o for o in self.experiment.outcomes
            if o.tutor_id in tutor_ids
        ]

        if not outcomes:
            logger.warning(f"No outcomes found for group {group}")
            return GroupMetrics(group=group.value, sample_size=len(tutor_ids))

        # Calculate outcome rates
        total_outcomes = len(outcomes)
        churn_count = sum(1 for o in outcomes if o.outcome_type == OutcomeType.CHURNED)
        improved_count = sum(1 for o in outcomes if o.outcome_type == OutcomeType.PERFORMANCE_IMPROVED)
        declined_count = sum(1 for o in outcomes if o.outcome_type == OutcomeType.PERFORMANCE_DECLINED)
        responded_count = sum(1 for o in outcomes if o.outcome_type == OutcomeType.RESPONDED)
        completed_count = sum(1 for o in outcomes if o.outcome_type == OutcomeType.COMPLETED_ACTION)

        # Calculate metric changes
        rating_changes = [
            o.metrics_change.get('avg_rating', {}).get('absolute', 0)
            for o in outcomes if 'avg_rating' in o.metrics_change
        ]
        engagement_changes = [
            o.metrics_change.get('engagement_score', {}).get('absolute', 0)
            for o in outcomes if 'engagement_score' in o.metrics_change
        ]
        sessions_changes = [
            o.metrics_change.get('sessions_completed', {}).get('absolute', 0)
            for o in outcomes if 'sessions_completed' in o.metrics_change
        ]

        # Time metrics
        improvement_times = [
            o.time_to_outcome_days for o in outcomes
            if o.outcome_type == OutcomeType.PERFORMANCE_IMPROVED and o.time_to_outcome_days
        ]
        churn_times = [
            o.time_to_outcome_days for o in outcomes
            if o.outcome_type == OutcomeType.CHURNED and o.time_to_outcome_days
        ]

        metrics = GroupMetrics(
            group=group.value,
            sample_size=len(tutor_ids),
            churn_rate=churn_count / total_outcomes if total_outcomes > 0 else 0,
            performance_improved_rate=improved_count / total_outcomes if total_outcomes > 0 else 0,
            performance_declined_rate=declined_count / total_outcomes if total_outcomes > 0 else 0,
            response_rate=responded_count / total_outcomes if total_outcomes > 0 else 0,
            action_completion_rate=completed_count / total_outcomes if total_outcomes > 0 else 0,
            avg_rating_change=np.mean(rating_changes) if rating_changes else 0.0,
            engagement_score_change=np.mean(engagement_changes) if engagement_changes else 0.0,
            sessions_completed_change=np.mean(sessions_changes) if sessions_changes else 0.0,
            avg_time_to_improvement_days=np.mean(improvement_times) if improvement_times else None,
            avg_time_to_churn_days=np.mean(churn_times) if churn_times else None,
            outcomes=outcomes
        )

        logger.debug(f"Calculated metrics for {group}: churn_rate={metrics.churn_rate:.3f}, "
                    f"improvement_rate={metrics.performance_improved_rate:.3f}")

        return metrics

    def _perform_statistical_tests(
        self,
        control: GroupMetrics,
        treatment: GroupMetrics
    ) -> List[StatisticalTest]:
        """Perform statistical significance tests between groups."""
        tests = []

        # Test churn rate
        tests.append(self._proportion_test(
            "churn_rate",
            control.churn_rate,
            treatment.churn_rate,
            control.sample_size,
            treatment.sample_size
        ))

        # Test improvement rate
        tests.append(self._proportion_test(
            "performance_improved_rate",
            control.performance_improved_rate,
            treatment.performance_improved_rate,
            control.sample_size,
            treatment.sample_size
        ))

        # Test rating change (t-test)
        tests.append(self._mean_test(
            "avg_rating_change",
            control.avg_rating_change,
            treatment.avg_rating_change,
            control.sample_size,
            treatment.sample_size
        ))

        # Test engagement change
        tests.append(self._mean_test(
            "engagement_score_change",
            control.engagement_score_change,
            treatment.engagement_score_change,
            control.sample_size,
            treatment.sample_size
        ))

        return tests

    def _proportion_test(
        self,
        metric: str,
        control_prop: float,
        treatment_prop: float,
        n_control: int,
        n_treatment: int
    ) -> StatisticalTest:
        """
        Two-proportion z-test.

        Tests if two proportions are significantly different.
        """
        # Calculate pooled proportion
        pooled_prop = (control_prop * n_control + treatment_prop * n_treatment) / (n_control + n_treatment)

        # Calculate standard error
        se = np.sqrt(pooled_prop * (1 - pooled_prop) * (1/n_control + 1/n_treatment))

        # Calculate z-score
        z = (treatment_prop - control_prop) / se if se > 0 else 0

        # Calculate p-value (two-tailed)
        from scipy import stats
        p_value = 2 * (1 - stats.norm.cdf(abs(z)))

        # Calculate 95% confidence interval for difference
        ci_margin = 1.96 * se
        ci_lower = (treatment_prop - control_prop) - ci_margin
        ci_upper = (treatment_prop - control_prop) + ci_margin

        # Calculate relative difference
        rel_diff = ((treatment_prop - control_prop) / control_prop * 100) if control_prop > 0 else 0

        return StatisticalTest(
            metric=metric,
            control_value=control_prop,
            treatment_value=treatment_prop,
            absolute_difference=treatment_prop - control_prop,
            relative_difference_pct=rel_diff,
            p_value=p_value,
            is_significant=p_value < self.significance_level,
            confidence_interval_95=(ci_lower, ci_upper),
            sample_size_control=n_control,
            sample_size_treatment=n_treatment
        )

    def _mean_test(
        self,
        metric: str,
        control_mean: float,
        treatment_mean: float,
        n_control: int,
        n_treatment: int,
        assumed_std: float = 0.5  # Assumed standard deviation
    ) -> StatisticalTest:
        """
        Two-sample t-test for means.

        Tests if two means are significantly different.
        """
        # Calculate standard error (assuming equal variance)
        se = assumed_std * np.sqrt(1/n_control + 1/n_treatment)

        # Calculate t-statistic
        t = (treatment_mean - control_mean) / se if se > 0 else 0

        # Degrees of freedom
        df = n_control + n_treatment - 2

        # Calculate p-value (two-tailed)
        from scipy import stats
        p_value = 2 * (1 - stats.t.cdf(abs(t), df))

        # Calculate 95% confidence interval
        t_critical = stats.t.ppf(0.975, df)
        ci_margin = t_critical * se
        ci_lower = (treatment_mean - control_mean) - ci_margin
        ci_upper = (treatment_mean - control_mean) + ci_margin

        # Calculate relative difference
        rel_diff = ((treatment_mean - control_mean) / abs(control_mean) * 100) if control_mean != 0 else 0

        return StatisticalTest(
            metric=metric,
            control_value=control_mean,
            treatment_value=treatment_mean,
            absolute_difference=treatment_mean - control_mean,
            relative_difference_pct=rel_diff,
            p_value=p_value,
            is_significant=p_value < self.significance_level,
            confidence_interval_95=(ci_lower, ci_upper),
            sample_size_control=n_control,
            sample_size_treatment=n_treatment
        )

    def _analyze_intervention_types(self) -> List[InterventionTypeEffectiveness]:
        """Analyze effectiveness by intervention type."""
        # Group outcomes by intervention type
        by_type = defaultdict(list)
        for outcome in self.experiment.outcomes:
            by_type[outcome.intervention_type].append(outcome)

        effectiveness_list = []

        for intervention_type, outcomes in by_type.items():
            if not outcomes:
                continue

            total = len(outcomes)

            # Calculate rates
            response_count = sum(1 for o in outcomes if o.outcome_type == OutcomeType.RESPONDED)
            improved_count = sum(1 for o in outcomes if o.outcome_type == OutcomeType.PERFORMANCE_IMPROVED)
            churned_count = sum(1 for o in outcomes if o.outcome_type == OutcomeType.CHURNED)

            # Time to impact
            impact_times = [
                o.time_to_outcome_days for o in outcomes
                if o.outcome_type == OutcomeType.PERFORMANCE_IMPROVED and o.time_to_outcome_days
            ]

            # Metric improvements
            rating_improvements = [
                o.metrics_change.get('avg_rating', {}).get('absolute', 0)
                for o in outcomes
                if o.outcome_type == OutcomeType.PERFORMANCE_IMPROVED and 'avg_rating' in o.metrics_change
            ]

            engagement_improvements = [
                o.metrics_change.get('engagement_score', {}).get('absolute', 0)
                for o in outcomes
                if o.outcome_type == OutcomeType.PERFORMANCE_IMPROVED and 'engagement_score' in o.metrics_change
            ]

            # Calculate composite effectiveness score
            # Higher is better: response rate, improvement rate, lower churn
            effectiveness_score = (
                (response_count / total * 30) +  # 30% weight
                (improved_count / total * 40) +  # 40% weight
                ((1 - churned_count / total) * 30)  # 30% weight (inverted churn)
            ) * 100

            effectiveness = InterventionTypeEffectiveness(
                intervention_type=intervention_type,
                total_interventions=total,
                response_rate=response_count / total if total > 0 else 0,
                improvement_rate=improved_count / total if total > 0 else 0,
                churn_prevention_rate=1 - (churned_count / total) if total > 0 else 0,
                avg_time_to_impact_days=np.mean(impact_times) if impact_times else None,
                avg_rating_improvement=np.mean(rating_improvements) if rating_improvements else 0,
                avg_engagement_improvement=np.mean(engagement_improvements) if engagement_improvements else 0,
                estimated_effectiveness_score=effectiveness_score
            )

            effectiveness_list.append(effectiveness)

            logger.debug(f"Analyzed {intervention_type}: effectiveness={effectiveness_score:.1f}, "
                        f"improvement_rate={effectiveness.improvement_rate:.3f}")

        # Sort by effectiveness score
        effectiveness_list.sort(key=lambda x: x.estimated_effectiveness_score, reverse=True)

        return effectiveness_list

    def _generate_trigger_recommendations(
        self,
        treatment_metrics: GroupMetrics,
        intervention_effectiveness: List[InterventionTypeEffectiveness]
    ) -> List[TriggerRecommendation]:
        """Generate recommendations for trigger threshold adjustments."""
        recommendations = []

        # If treatment group shows significant improvement, recommend more aggressive triggers
        if treatment_metrics.performance_improved_rate > 0.3:  # 30% improvement rate
            recommendations.append(TriggerRecommendation(
                intervention_type="automated_coaching",
                current_threshold={"churn_score": 70, "performance_tier": "At Risk"},
                recommended_threshold={"churn_score": 60, "performance_tier": "Developing"},
                rationale=f"Treatment group showed {treatment_metrics.performance_improved_rate:.1%} "
                         f"improvement rate. Expanding trigger criteria could help more tutors.",
                expected_improvement=f"Could help additional {int(treatment_metrics.sample_size * 0.2)} tutors",
                confidence="high" if treatment_metrics.sample_size >= 50 else "medium"
            ))

        # Analyze each intervention type
        for effectiveness in intervention_effectiveness:
            if effectiveness.improvement_rate < 0.15:  # Less than 15% improvement
                # Recommend tightening criteria (less aggressive)
                recommendations.append(TriggerRecommendation(
                    intervention_type=effectiveness.intervention_type,
                    current_threshold={"churn_score": 60},
                    recommended_threshold={"churn_score": 70},
                    rationale=f"Low improvement rate ({effectiveness.improvement_rate:.1%}). "
                             f"Tightening criteria to focus on higher-risk cases.",
                    expected_improvement="Focus resources on cases more likely to improve",
                    confidence="medium" if effectiveness.total_interventions >= 20 else "low"
                ))

            elif effectiveness.improvement_rate > 0.4:  # Greater than 40% improvement
                # Recommend loosening criteria (more aggressive)
                recommendations.append(TriggerRecommendation(
                    intervention_type=effectiveness.intervention_type,
                    current_threshold={"churn_score": 70},
                    recommended_threshold={"churn_score": 60},
                    rationale=f"High improvement rate ({effectiveness.improvement_rate:.1%}). "
                             f"Expanding criteria to help more tutors.",
                    expected_improvement=f"Could reduce churn by estimated {int(effectiveness.churn_prevention_rate * 100)}%",
                    confidence="high" if effectiveness.total_interventions >= 30 else "medium"
                ))

        return recommendations

    def _assess_experiment(
        self,
        control: GroupMetrics,
        treatment: GroupMetrics,
        tests: List[StatisticalTest]
    ) -> Tuple[float, bool, List[str], List[str]]:
        """
        Assess overall experiment success.

        Returns:
            Tuple of (overall_score, is_successful, key_findings, recommendations)
        """
        findings = []
        recommendations = []

        # Check sample size
        if control.sample_size < self.minimum_sample_size or treatment.sample_size < self.minimum_sample_size:
            findings.append(f"⚠️ Small sample size (control: {control.sample_size}, treatment: {treatment.sample_size}). "
                          f"Minimum {self.minimum_sample_size} recommended per group.")
            recommendations.append("Continue collecting data to reach minimum sample size for reliable conclusions.")

        # Analyze key metrics
        significant_improvements = 0
        total_tests = len(tests)

        for test in tests:
            if test.is_significant:
                direction = "increased" if test.absolute_difference > 0 else "decreased"
                findings.append(
                    f"{'✓' if test.absolute_difference > 0 else '⚠️'} {test.metric} {direction} by "
                    f"{abs(test.relative_difference_pct):.1f}% (p={test.p_value:.4f})"
                )
                if test.absolute_difference > 0 and test.metric in ["performance_improved_rate", "avg_rating_change"]:
                    significant_improvements += 1

        # Calculate churn reduction
        churn_reduction = (control.churn_rate - treatment.churn_rate) / control.churn_rate * 100 if control.churn_rate > 0 else 0
        if churn_reduction > 0:
            findings.append(f"✓ Churn reduced by {churn_reduction:.1f}% in treatment group")

        # Calculate overall effectiveness score
        # Based on: churn reduction, improvement rate, statistical significance
        score = 0

        # Component 1: Churn reduction (40 points)
        if treatment.churn_rate < control.churn_rate:
            score += min(40, churn_reduction / 10 * 40)  # Up to 100% reduction = 40 points

        # Component 2: Improvement rate (30 points)
        if treatment.performance_improved_rate > control.performance_improved_rate:
            improvement_lift = (treatment.performance_improved_rate - control.performance_improved_rate) / \
                              (control.performance_improved_rate + 0.01)  # Avoid division by zero
            score += min(30, improvement_lift * 30)

        # Component 3: Statistical significance (30 points)
        if total_tests > 0:
            score += (significant_improvements / total_tests) * 30

        # Is experiment successful?
        is_successful = (
            score >= 60 and  # Overall score > 60
            treatment.churn_rate < control.churn_rate and  # Churn reduced
            treatment.performance_improved_rate > control.performance_improved_rate  # Performance improved
        )

        # Generate recommendations
        if is_successful:
            recommendations.append("✓ Experiment successful! Recommend rolling out interventions to all tutors.")
            recommendations.append(f"Expected impact: {churn_reduction:.1f}% churn reduction, "
                                 f"{(treatment.performance_improved_rate - control.performance_improved_rate) * 100:.1f}% "
                                 f"more tutors improving performance.")
        else:
            recommendations.append("⚠️ Results inconclusive. Recommend continuing experiment or refining intervention strategy.")
            if control.sample_size < self.minimum_sample_size * 2:
                recommendations.append("Consider increasing sample size for more reliable results.")

        return score, is_successful, findings, recommendations

    def generate_report(self, results: ExperimentAnalysisResults) -> str:
        """Generate a formatted text report."""
        report_lines = [
            "=" * 80,
            f"INTERVENTION A/B TEST ANALYSIS REPORT",
            "=" * 80,
            f"Experiment: {results.experiment_name}",
            f"ID: {results.experiment_id}",
            f"Analysis Date: {results.analysis_date.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "-" * 80,
            "EXPERIMENT SUMMARY",
            "-" * 80,
            f"Overall Effectiveness Score: {results.overall_effectiveness_score:.1f}/100",
            f"Experiment Successful: {'YES ✓' if results.is_experiment_successful else 'NO ⚠️'}",
            "",
            "-" * 80,
            "GROUP COMPARISON",
            "-" * 80,
            f"Control Group (n={results.control_metrics.sample_size}):",
            f"  Churn Rate: {results.control_metrics.churn_rate:.1%}",
            f"  Performance Improved: {results.control_metrics.performance_improved_rate:.1%}",
            f"  Avg Rating Change: {results.control_metrics.avg_rating_change:+.2f}",
            f"  Avg Engagement Change: {results.control_metrics.engagement_score_change:+.2f}",
            "",
            f"Treatment Group (n={results.treatment_metrics.sample_size}):",
            f"  Churn Rate: {results.treatment_metrics.churn_rate:.1%}",
            f"  Performance Improved: {results.treatment_metrics.performance_improved_rate:.1%}",
            f"  Avg Rating Change: {results.treatment_metrics.avg_rating_change:+.2f}",
            f"  Avg Engagement Change: {results.treatment_metrics.engagement_score_change:+.2f}",
            "",
            "-" * 80,
            "STATISTICAL SIGNIFICANCE TESTS",
            "-" * 80,
        ]

        for test in results.statistical_tests:
            sig_marker = "✓" if test.is_significant else "○"
            report_lines.extend([
                f"{sig_marker} {test.metric}:",
                f"    Control: {test.control_value:.4f}",
                f"    Treatment: {test.treatment_value:.4f}",
                f"    Difference: {test.absolute_difference:+.4f} ({test.relative_difference_pct:+.1f}%)",
                f"    P-value: {test.p_value:.4f} ({'SIGNIFICANT' if test.is_significant else 'not significant'})",
                f"    95% CI: [{test.confidence_interval_95[0]:.4f}, {test.confidence_interval_95[1]:.4f}]",
                ""
            ])

        report_lines.extend([
            "-" * 80,
            "INTERVENTION TYPE EFFECTIVENESS",
            "-" * 80,
        ])

        for eff in results.intervention_effectiveness:
            report_lines.extend([
                f"{eff.intervention_type} (n={eff.total_interventions}):",
                f"  Effectiveness Score: {eff.estimated_effectiveness_score:.1f}/100",
                f"  Response Rate: {eff.response_rate:.1%}",
                f"  Improvement Rate: {eff.improvement_rate:.1%}",
                f"  Churn Prevention: {eff.churn_prevention_rate:.1%}",
                f"  Avg Time to Impact: {eff.avg_time_to_impact_days:.1f} days" if eff.avg_time_to_impact_days else "  Avg Time to Impact: N/A",
                f"  Avg Rating Improvement: {eff.avg_rating_improvement:+.2f}",
                ""
            ])

        report_lines.extend([
            "-" * 80,
            "KEY FINDINGS",
            "-" * 80,
        ])
        for finding in results.key_findings:
            report_lines.append(f"  {finding}")

        report_lines.extend([
            "",
            "-" * 80,
            "RECOMMENDATIONS",
            "-" * 80,
        ])
        for rec in results.recommendations:
            report_lines.append(f"  {rec}")

        if results.trigger_recommendations:
            report_lines.extend([
                "",
                "-" * 80,
                "TRIGGER ADJUSTMENT RECOMMENDATIONS",
                "-" * 80,
            ])
            for trig_rec in results.trigger_recommendations:
                report_lines.extend([
                    f"{trig_rec.intervention_type}:",
                    f"  Current: {trig_rec.current_threshold}",
                    f"  Recommended: {trig_rec.recommended_threshold}",
                    f"  Rationale: {trig_rec.rationale}",
                    f"  Expected Improvement: {trig_rec.expected_improvement}",
                    f"  Confidence: {trig_rec.confidence}",
                    ""
                ])

        report_lines.append("=" * 80)

        return "\n".join(report_lines)

    def save_results(self, results: ExperimentAnalysisResults, filepath: str):
        """Save analysis results to JSON file."""

        def convert_value(val):
            """Convert numpy types to native Python types for JSON serialization."""
            if isinstance(val, (np.integer, np.floating)):
                return float(val)
            elif isinstance(val, np.ndarray):
                return val.tolist()
            elif isinstance(val, (np.bool_, bool)):
                return bool(val)
            elif isinstance(val, tuple):
                return tuple(convert_value(v) for v in val)
            elif isinstance(val, list):
                return [convert_value(v) for v in val]
            return val

        data = {
            "experiment_id": results.experiment_id,
            "experiment_name": results.experiment_name,
            "analysis_date": results.analysis_date.isoformat(),
            "overall_effectiveness_score": convert_value(results.overall_effectiveness_score),
            "is_experiment_successful": convert_value(results.is_experiment_successful),
            "control_metrics": {
                "group": results.control_metrics.group,
                "sample_size": results.control_metrics.sample_size,
                "churn_rate": convert_value(results.control_metrics.churn_rate),
                "performance_improved_rate": convert_value(results.control_metrics.performance_improved_rate),
                "avg_rating_change": convert_value(results.control_metrics.avg_rating_change),
                "avg_engagement_change": convert_value(results.control_metrics.engagement_score_change)
            },
            "treatment_metrics": {
                "group": results.treatment_metrics.group,
                "sample_size": results.treatment_metrics.sample_size,
                "churn_rate": convert_value(results.treatment_metrics.churn_rate),
                "performance_improved_rate": convert_value(results.treatment_metrics.performance_improved_rate),
                "avg_rating_change": convert_value(results.treatment_metrics.avg_rating_change),
                "avg_engagement_change": convert_value(results.treatment_metrics.engagement_score_change)
            },
            "statistical_tests": [
                {
                    "metric": test.metric,
                    "control_value": convert_value(test.control_value),
                    "treatment_value": convert_value(test.treatment_value),
                    "absolute_difference": convert_value(test.absolute_difference),
                    "relative_difference_pct": convert_value(test.relative_difference_pct),
                    "p_value": convert_value(test.p_value),
                    "is_significant": convert_value(test.is_significant),
                    "confidence_interval_95": convert_value(test.confidence_interval_95)
                }
                for test in results.statistical_tests
            ],
            "intervention_effectiveness": [
                {
                    "intervention_type": eff.intervention_type,
                    "total_interventions": eff.total_interventions,
                    "response_rate": convert_value(eff.response_rate),
                    "improvement_rate": convert_value(eff.improvement_rate),
                    "churn_prevention_rate": convert_value(eff.churn_prevention_rate),
                    "estimated_effectiveness_score": convert_value(eff.estimated_effectiveness_score)
                }
                for eff in results.intervention_effectiveness
            ],
            "trigger_recommendations": [
                {
                    "intervention_type": rec.intervention_type,
                    "current_threshold": rec.current_threshold,
                    "recommended_threshold": rec.recommended_threshold,
                    "rationale": rec.rationale,
                    "expected_improvement": rec.expected_improvement,
                    "confidence": rec.confidence
                }
                for rec in results.trigger_recommendations
            ],
            "key_findings": results.key_findings,
            "recommendations": results.recommendations
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved analysis results to {filepath}")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    from .intervention_ab_testing import create_churn_prevention_experiment, OutcomeType

    # Create and populate experiment with sample data
    experiment = create_churn_prevention_experiment()

    # Simulate tutor assignments and outcomes
    print("Simulating A/B test experiment...")

    # Control group tutors (no intervention)
    for i in range(1, 26):
        experiment.assign_tutor(f"C{i:03d}", force_group=ABTestGroup.CONTROL)
        # Simulate outcomes: higher churn, less improvement
        if i % 4 == 0:  # 25% churn
            experiment.record_outcome(
                f"C{i:03d}", f"intv_c{i}", "none", OutcomeType.CHURNED,
                {"avg_rating": 3.5}, {"avg_rating": 3.5}
            )
        elif i % 3 == 0:  # 33% improved
            experiment.record_outcome(
                f"C{i:03d}", f"intv_c{i}", "none", OutcomeType.PERFORMANCE_IMPROVED,
                {"avg_rating": 3.5, "engagement_score": 0.6},
                {"avg_rating": 3.8, "engagement_score": 0.65}
            )

    # Treatment group tutors (with intervention)
    for i in range(1, 26):
        experiment.assign_tutor(f"T{i:03d}", force_group=ABTestGroup.TREATMENT)
        # Simulate outcomes: lower churn, more improvement
        if i % 10 == 0:  # 10% churn (better than control)
            experiment.record_outcome(
                f"T{i:03d}", f"intv_t{i}", "automated_coaching", OutcomeType.CHURNED,
                {"avg_rating": 3.5}, {"avg_rating": 3.5}
            )
        elif i % 2 == 0:  # 50% improved (better than control)
            experiment.record_outcome(
                f"T{i:03d}", f"intv_t{i}", "automated_coaching", OutcomeType.PERFORMANCE_IMPROVED,
                {"avg_rating": 3.5, "engagement_score": 0.6},
                {"avg_rating": 4.1, "engagement_score": 0.75}
            )

    # Analyze experiment
    print("\nAnalyzing experiment...\n")
    analytics = InterventionAnalytics(experiment)
    results = analytics.analyze_experiment()

    # Generate and print report
    report = analytics.generate_report(results)
    print(report)

    # Save results
    analytics.save_results(results, "output/intervention_analysis_results.json")
    print("\nResults saved to output/intervention_analysis_results.json")
