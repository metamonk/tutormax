#!/usr/bin/env python3
"""
Demo script for churn prediction data preparation.

Generates comprehensive synthetic dataset with:
- 300 tutors (15% will churn)
- 90 days of historical data
- Time-series patterns showing engagement decline
- Performance deterioration for churners
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.data_preparation import prepare_churn_dataset, ChurnConfig


def main():
    """Run data preparation for churn prediction."""

    print("=" * 70)
    print("CHURN PREDICTION DATA PREPARATION")
    print("=" * 70)
    print()

    # Configure data generation
    config = ChurnConfig(
        num_tutors=300,
        days_history=90,
        churn_rate=0.15,  # 15% churn rate
        feedback_rate=0.85,
        seed=42
    )

    print("Configuration:")
    print(f"  Tutors: {config.num_tutors}")
    print(f"  Days of history: {config.days_history}")
    print(f"  Expected churn rate: {config.churn_rate * 100:.0f}%")
    print(f"  Feedback rate: {config.feedback_rate * 100:.0f}%")
    print()

    # Prepare dataset
    tutors_df, sessions_df, feedback_df = prepare_churn_dataset(
        output_dir="output/churn_data",
        config=config
    )

    # Additional analysis
    print("\n" + "=" * 70)
    print("DATA QUALITY CHECKS")
    print("=" * 70)

    # Check for missing values
    print("\nMissing Values:")
    print(f"  Tutors: {tutors_df.isnull().sum().sum()} missing values")
    print(f"  Sessions: {sessions_df.isnull().sum().sum()} missing values")
    print(f"  Feedback: {feedback_df.isnull().sum().sum()} missing values")

    # Check churn distribution by archetype
    if "will_churn" in tutors_df.columns and "behavioral_archetype" in tutors_df.columns:
        print("\nChurn Distribution by Archetype:")
        churn_by_archetype = tutors_df.groupby("behavioral_archetype")["will_churn"].agg([
            ("total", "count"),
            ("churners", "sum"),
            ("churn_rate", "mean")
        ])
        print(churn_by_archetype.to_string())

    # Check temporal patterns
    if "scheduled_start" in sessions_df.columns:
        sessions_df["scheduled_start"] = pd.to_datetime(sessions_df["scheduled_start"])
        print("\nTemporal Coverage:")
        print(f"  Earliest session: {sessions_df['scheduled_start'].min()}")
        print(f"  Latest session: {sessions_df['scheduled_start'].max()}")
        print(f"  Days covered: {(sessions_df['scheduled_start'].max() - sessions_df['scheduled_start'].min()).days}")

    print("\n" + "=" * 70)
    print("✓ Data preparation complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Feature engineering (Task 4.2)")
    print("  2. Model training (Task 4.3)")
    print("  3. Model evaluation (Task 4.4)")
    print()


if __name__ == "__main__":
    import pandas as pd
    main()
