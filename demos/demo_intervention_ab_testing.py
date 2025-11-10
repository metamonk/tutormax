"""
Comprehensive Demo: Intervention A/B Testing and Optimization

This demo showcases the complete workflow for testing intervention effectiveness:
1. Set up A/B test experiment
2. Assign tutors to control/treatment groups
3. Simulate intervention delivery
4. Record outcomes over time
5. Analyze results with statistical tests
6. Generate trigger optimization recommendations
7. Apply optimizations

Run: python demos/demo_intervention_ab_testing.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import random
import numpy as np
from datetime import datetime, timedelta

from src.evaluation.intervention_ab_testing import (
    InterventionExperiment,
    ExperimentConfig,
    ABTestGroup,
    OutcomeType,
    create_churn_prevention_experiment
)
from src.evaluation.intervention_analytics import InterventionAnalytics
from src.evaluation.trigger_optimizer import TriggerOptimizer
from src.evaluation.intervention_config import InterventionConfig


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80 + "\n")


def print_subsection(title: str):
    """Print a subsection header."""
    print("\n" + "-" * 80)
    print(title)
    print("-" * 80 + "\n")


def simulate_tutor_data(risk_level: str) -> dict:
    """Generate realistic tutor state data."""
    if risk_level == "CRITICAL":
        return {
            "risk_level": risk_level,
            "performance_tier": random.choice(["At Risk", "Needs Attention"]),
            "churn_score": random.randint(80, 95),
            "avg_rating": round(random.uniform(2.5, 3.5), 2),
            "engagement_score": round(random.uniform(0.3, 0.55), 2),
            "sessions_per_week": round(random.uniform(1.0, 2.5), 1)
        }
    elif risk_level == "HIGH":
        return {
            "risk_level": risk_level,
            "performance_tier": random.choice(["Developing", "Needs Attention"]),
            "churn_score": random.randint(60, 79),
            "avg_rating": round(random.uniform(3.2, 3.8), 2),
            "engagement_score": round(random.uniform(0.5, 0.65), 2),
            "sessions_per_week": round(random.uniform(2.0, 3.5), 1)
        }
    else:  # MEDIUM
        return {
            "risk_level": risk_level,
            "performance_tier": random.choice(["Developing", "Strong"]),
            "churn_score": random.randint(40, 59),
            "avg_rating": round(random.uniform(3.5, 4.2), 2),
            "engagement_score": round(random.uniform(0.6, 0.75), 2),
            "sessions_per_week": round(random.uniform(3.0, 5.0), 1)
        }


def simulate_intervention_outcomes(
    experiment: InterventionExperiment,
    tutor_id: str,
    tutor_data: dict,
    group: ABTestGroup,
    intervention_type: str = "automated_coaching"
):
    """
    Simulate realistic intervention outcomes based on group assignment.

    Treatment group: Better outcomes (lower churn, more improvement)
    Control group: Baseline outcomes
    """
    intervention_id = f"intv_{tutor_id}"

    # Metrics before intervention
    metrics_before = {
        "avg_rating": tutor_data["avg_rating"],
        "engagement_score": tutor_data["engagement_score"],
        "sessions_completed": int(tutor_data["sessions_per_week"] * 4)  # Monthly
    }

    # Simulate outcomes based on group
    is_treatment = group in [ABTestGroup.TREATMENT, ABTestGroup.TREATMENT_A]

    # Risk-based probabilities
    if tutor_data["risk_level"] == "CRITICAL":
        # Critical risk tutors are harder to save
        churn_prob = 0.15 if is_treatment else 0.35
        improve_prob = 0.40 if is_treatment else 0.20
    elif tutor_data["risk_level"] == "HIGH":
        churn_prob = 0.08 if is_treatment else 0.20
        improve_prob = 0.55 if is_treatment else 0.30
    else:  # MEDIUM
        churn_prob = 0.03 if is_treatment else 0.10
        improve_prob = 0.70 if is_treatment else 0.45

    # Determine outcome
    rand = random.random()

    if rand < churn_prob:
        # Churned - metrics stay same or decline
        outcome_type = OutcomeType.CHURNED
        rating_change = -round(random.uniform(0, 0.3), 2)
        engagement_change = -round(random.uniform(0, 0.1), 2)
        sessions_change = -random.randint(0, 3)

    elif rand < churn_prob + improve_prob:
        # Improved - metrics increase
        outcome_type = OutcomeType.PERFORMANCE_IMPROVED

        if is_treatment:
            # Treatment group shows better improvement
            rating_change = round(random.uniform(0.3, 0.8), 2)
            engagement_change = round(random.uniform(0.10, 0.25), 2)
            sessions_change = random.randint(3, 8)
        else:
            # Control group shows moderate improvement
            rating_change = round(random.uniform(0.1, 0.4), 2)
            engagement_change = round(random.uniform(0.05, 0.12), 2)
            sessions_change = random.randint(1, 4)

    else:
        # Stable - small changes
        outcome_type = OutcomeType.PERFORMANCE_STABLE
        rating_change = round(random.uniform(-0.1, 0.2), 2)
        engagement_change = round(random.uniform(-0.05, 0.08), 2)
        sessions_change = random.randint(-1, 2)

    # Calculate metrics after
    metrics_after = {
        "avg_rating": round(max(1.0, min(5.0, metrics_before["avg_rating"] + rating_change)), 2),
        "engagement_score": round(max(0.0, min(1.0, metrics_before["engagement_score"] + engagement_change)), 2),
        "sessions_completed": max(0, metrics_before["sessions_completed"] + sessions_change)
    }

    # Record outcome
    experiment.record_outcome(
        tutor_id=tutor_id,
        intervention_id=intervention_id,
        intervention_type=intervention_type,
        outcome_type=outcome_type,
        metrics_before=metrics_before,
        metrics_after=metrics_after,
        notes=f"Simulated outcome for {group.value} group"
    )

    return outcome_type


def main():
    """Run the complete A/B testing and optimization demo."""

    print_section("INTERVENTION A/B TESTING & OPTIMIZATION DEMO")

    print("""
This demo demonstrates the complete workflow for testing and optimizing
intervention effectiveness using A/B testing methodology.

Workflow:
1. Create experiment with stratified sampling
2. Assign tutors to control (no intervention) vs treatment (with intervention)
3. Simulate interventions and track outcomes
4. Analyze results with statistical significance tests
5. Generate trigger optimization recommendations
6. Apply optimizations to improve future interventions
""")

    # ============================================================================
    # STEP 1: Create A/B Test Experiment
    # ============================================================================

    print_section("STEP 1: Create A/B Test Experiment")

    experiment = create_churn_prevention_experiment(
        experiment_name="Churn Prevention Pilot - Q4 2025",
        stratify=True  # Use stratified sampling for balanced groups
    )

    print(f"Experiment Created: {experiment.config.name}")
    print(f"ID: {experiment.config.experiment_id}")
    print(f"Assignment Strategy: {experiment.config.assignment_strategy}")
    print(f"Stratification Keys: {experiment.config.stratification_keys}")
    print(f"Success Metrics: {', '.join(experiment.config.success_metrics)}")

    # ============================================================================
    # STEP 2: Assign Tutors to Groups
    # ============================================================================

    print_section("STEP 2: Assign Tutors to Control/Treatment Groups")

    # Generate tutors across different risk levels
    risk_distribution = {
        "CRITICAL": 20,
        "HIGH": 30,
        "MEDIUM": 30
    }

    all_tutors = []

    for risk_level, count in risk_distribution.items():
        for i in range(count):
            tutor_id = f"{risk_level[0]}{i+1:03d}"  # C001, H001, M001, etc.
            tutor_data = simulate_tutor_data(risk_level)
            tutor_data['tutor_id'] = tutor_id
            all_tutors.append(tutor_data)

            # Assign to group using stratified sampling
            group = experiment.assign_tutor(tutor_id, tutor_data)
            tutor_data['group'] = group

    print(f"Total Tutors Assigned: {len(all_tutors)}")

    # Show group distribution
    stats = experiment.get_experiment_stats()
    print(f"\nGroup Distribution:")
    print(f"  Control Group: {stats['control_count']} tutors (no intervention)")
    print(f"  Treatment Group: {stats['treatment_count']} tutors (receive interventions)")

    # Show stratification balance
    print(f"\nStratification Buckets: {stats['stratification_buckets']}")
    print("\nSample of Assignments:")
    for tutor in all_tutors[:10]:
        print(f"  {tutor['tutor_id']}: {tutor['risk_level']:8s} / {tutor['performance_tier']:18s} -> {tutor['group'].value:10s}")

    # ============================================================================
    # STEP 3: Simulate Interventions and Outcomes
    # ============================================================================

    print_section("STEP 3: Simulate Interventions and Track Outcomes")

    print("Simulating 8 weeks of interventions and outcomes...\n")

    outcome_counts = {
        "control": {"churned": 0, "improved": 0, "stable": 0},
        "treatment": {"churned": 0, "improved": 0, "stable": 0}
    }

    # Simulate interventions for each tutor
    for tutor in all_tutors:
        # Only treatment group receives interventions
        if experiment.should_receive_intervention(tutor['tutor_id']):
            intervention_type = "automated_coaching" if tutor['risk_level'] != "CRITICAL" else "manager_coaching"
        else:
            intervention_type = "none"

        # Simulate outcome
        outcome = simulate_intervention_outcomes(
            experiment=experiment,
            tutor_id=tutor['tutor_id'],
            tutor_data=tutor,
            group=tutor['group'],
            intervention_type=intervention_type
        )

        # Track outcome
        group_key = "treatment" if tutor['group'] == ABTestGroup.TREATMENT else "control"
        if outcome == OutcomeType.CHURNED:
            outcome_counts[group_key]["churned"] += 1
        elif outcome == OutcomeType.PERFORMANCE_IMPROVED:
            outcome_counts[group_key]["improved"] += 1
        else:
            outcome_counts[group_key]["stable"] += 1

    print(f"Outcomes recorded: {stats['total_outcomes']} total")
    print(f"\nControl Group Outcomes:")
    print(f"  Churned: {outcome_counts['control']['churned']}")
    print(f"  Improved: {outcome_counts['control']['improved']}")
    print(f"  Stable: {outcome_counts['control']['stable']}")
    print(f"\nTreatment Group Outcomes:")
    print(f"  Churned: {outcome_counts['treatment']['churned']}")
    print(f"  Improved: {outcome_counts['treatment']['improved']}")
    print(f"  Stable: {outcome_counts['treatment']['stable']}")

    # Save experiment
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    experiment.save_to_file("output/intervention_ab_test_experiment.json")
    print(f"\nExperiment saved to output/intervention_ab_test_experiment.json")

    # ============================================================================
    # STEP 4: Analyze Results
    # ============================================================================

    print_section("STEP 4: Analyze A/B Test Results")

    print("Running statistical analysis...\n")

    analytics = InterventionAnalytics(
        experiment=experiment,
        significance_level=0.05,
        minimum_sample_size=25
    )

    results = analytics.analyze_experiment()

    # Display key metrics
    print(f"Overall Effectiveness Score: {results.overall_effectiveness_score:.1f}/100")
    print(f"Experiment Successful: {'YES ✓' if results.is_experiment_successful else 'NO ⚠️'}")

    print_subsection("Group Comparison")

    print(f"Control Group (n={results.control_metrics.sample_size}):")
    print(f"  Churn Rate: {results.control_metrics.churn_rate:.1%}")
    print(f"  Performance Improved: {results.control_metrics.performance_improved_rate:.1%}")
    print(f"  Avg Rating Change: {results.control_metrics.avg_rating_change:+.2f}")
    print(f"  Avg Engagement Change: {results.control_metrics.engagement_score_change:+.2f}")

    print(f"\nTreatment Group (n={results.treatment_metrics.sample_size}):")
    print(f"  Churn Rate: {results.treatment_metrics.churn_rate:.1%}")
    print(f"  Performance Improved: {results.treatment_metrics.performance_improved_rate:.1%}")
    print(f"  Avg Rating Change: {results.treatment_metrics.avg_rating_change:+.2f}")
    print(f"  Avg Engagement Change: {results.treatment_metrics.engagement_score_change:+.2f}")

    print_subsection("Statistical Significance Tests")

    for test in results.statistical_tests:
        sig = "✓ SIGNIFICANT" if test.is_significant else "○ not significant"
        print(f"{test.metric}:")
        print(f"  Difference: {test.absolute_difference:+.4f} ({test.relative_difference_pct:+.1f}%)")
        print(f"  P-value: {test.p_value:.4f} ({sig})")
        print()

    print_subsection("Key Findings")
    for finding in results.key_findings:
        print(f"  {finding}")

    print_subsection("Recommendations")
    for rec in results.recommendations:
        print(f"  {rec}")

    # Generate and save full report
    report = analytics.generate_report(results)
    with open("output/intervention_ab_test_report.txt", 'w') as f:
        f.write(report)
    print(f"\nFull report saved to output/intervention_ab_test_report.txt")

    analytics.save_results(results, "output/intervention_ab_test_results.json")
    print(f"Results data saved to output/intervention_ab_test_results.json")

    # ============================================================================
    # STEP 5: Trigger Optimization
    # ============================================================================

    print_section("STEP 5: Apply Trigger Optimizations")

    if not results.trigger_recommendations:
        print("No trigger recommendations generated.")
        print("(This may happen if the experiment didn't show strong enough results)")
    else:
        print(f"Generated {len(results.trigger_recommendations)} trigger recommendations\n")

        # Create optimizer
        config = InterventionConfig()
        optimizer = TriggerOptimizer(config=config, auto_apply=False)

        print_subsection("Current Trigger Thresholds")
        print(f"  Critical Churn Score: {config.thresholds.critical_churn_probability}")
        print(f"  High Priority Churn Score: {config.thresholds.high_churn_probability}")
        print(f"  Medium Priority Churn Score: {config.thresholds.medium_churn_probability}")
        print(f"  Low Rating Threshold: {config.thresholds.low_rating}")
        print(f"  Low Engagement Threshold: {config.thresholds.low_engagement_score}")

        print_subsection("Recommended Changes")
        for rec in results.trigger_recommendations:
            print(f"{rec.intervention_type}:")
            print(f"  Current: {rec.current_threshold}")
            print(f"  Recommended: {rec.recommended_threshold}")
            print(f"  Rationale: {rec.rationale}")
            print(f"  Confidence: {rec.confidence}")
            print()

        # Preview changes (dry run)
        print_subsection("Preview Changes (Dry Run)")
        summary = optimizer.apply_recommendations(
            results,
            confidence_threshold="medium",
            dry_run=True
        )
        print(f"Would apply {summary['applied_changes']} changes:")
        for change in summary['changes']:
            print(f"  {change.intervention_type}.{change.parameter}: {change.old_value} -> {change.new_value}")

        # Apply changes
        print_subsection("Applying Optimizations")
        summary = optimizer.apply_recommendations(
            results,
            confidence_threshold="medium",
            dry_run=False
        )
        print(f"✓ Applied {summary['applied_changes']} optimizations")
        print(f"○ Skipped {summary['skipped_changes']} (below confidence threshold)")

        # Show updated thresholds
        print_subsection("Updated Trigger Thresholds")
        print(f"  Critical Churn Score: {config.thresholds.critical_churn_probability}")
        print(f"  High Priority Churn Score: {config.thresholds.high_churn_probability}")
        print(f"  Medium Priority Churn Score: {config.thresholds.medium_churn_probability}")
        print(f"  Low Rating Threshold: {config.thresholds.low_rating}")
        print(f"  Low Engagement Threshold: {config.thresholds.low_engagement_score}")

        # Show optimization history
        print_subsection("Optimization History")
        print(optimizer.get_optimization_report())

    # ============================================================================
    # Summary
    # ============================================================================

    print_section("DEMO COMPLETE - SUMMARY")

    print(f"""
Experiment: {experiment.config.name}
Total Tutors: {len(all_tutors)}
Outcomes Tracked: {len(experiment.outcomes)}

Results:
  • Overall Effectiveness: {results.overall_effectiveness_score:.1f}/100
  • Churn Reduction: {(results.control_metrics.churn_rate - results.treatment_metrics.churn_rate) / results.control_metrics.churn_rate * 100:.1f}%
  • Performance Improvement Increase: {(results.treatment_metrics.performance_improved_rate - results.control_metrics.performance_improved_rate) * 100:.1f}%
  • Experiment Success: {'YES ✓' if results.is_experiment_successful else 'NO ⚠️'}

Output Files:
  ✓ output/intervention_ab_test_experiment.json (experiment data)
  ✓ output/intervention_ab_test_report.txt (full analysis report)
  ✓ output/intervention_ab_test_results.json (results data)

Next Steps:
  1. Review the full analysis report for detailed findings
  2. Validate optimizations in production environment
  3. Monitor impact of threshold changes on intervention effectiveness
  4. Plan follow-up experiments to test new intervention strategies
""")

    print("=" * 80)


if __name__ == "__main__":
    # Set random seed for reproducibility
    random.seed(42)
    np.random.seed(42)

    main()
