#!/usr/bin/env python3
"""
Demo script for churn prediction feature engineering.

Shows feature distributions and correlations with churn.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.feature_engineering import engineer_churn_features


def main():
    """Run feature engineering demo."""

    print("=" * 70)
    print("CHURN PREDICTION FEATURE ENGINEERING DEMO")
    print("=" * 70)
    print()

    # Load data
    print("Loading data...")
    tutors_df = pd.read_csv("output/churn_data/tutors.csv")
    sessions_df = pd.read_csv("output/churn_data/sessions.csv")
    feedback_df = pd.read_csv("output/churn_data/feedback.csv")

    print(f"  Tutors: {len(tutors_df):,}")
    print(f"  Sessions: {len(sessions_df):,}")
    print(f"  Feedback: {len(feedback_df):,}")
    print()

    # Engineer features
    features_df = engineer_churn_features(
        tutors_df,
        sessions_df,
        feedback_df,
        output_path="output/churn_data/features.csv"
    )

    print("\n" + "=" * 70)
    print("FEATURE ANALYSIS")
    print("=" * 70)

    # Feature summary
    print(f"\nTotal features: {len(features_df.columns) - 2}")  # Exclude tutor_id and will_churn
    print(f"Tutor count: {len(features_df):,}")

    # List all features
    feature_cols = [c for c in features_df.columns if c not in ['tutor_id', 'will_churn']]
    print(f"\nFeature categories:")

    categories = {
        'Static': [c for c in feature_cols if 'archetype' in c or c in ['baseline_sessions_per_week', 'tenure_days']],
        'Session Counts': [c for c in feature_cols if 'sessions_' in c and 'd' in c],
        'Performance': [c for c in feature_cols if 'avg_rating' in c or 'avg_engagement' in c],
        'Behavioral': [c for c in feature_cols if 'no_show' in c or 'reschedule' in c],
        'Trends': [c for c in feature_cols if 'decline' in c or 'increase' in c],
        'Composite': [c for c in feature_cols if 'score' in c or 'momentum' in c or 'consistency' in c],
    }

    for category, cols in categories.items():
        print(f"  {category}: {len(cols)} features")

    # Churn analysis
    if 'will_churn' in features_df.columns:
        print("\n" + "=" * 70)
        print("CHURN CORRELATION ANALYSIS")
        print("=" * 70)

        churners = features_df[features_df['will_churn'] == True]
        non_churners = features_df[features_df['will_churn'] == False]

        print(f"\nChurners: {len(churners):,} ({len(churners)/len(features_df)*100:.1f}%)")
        print(f"Non-churners: {len(non_churners):,} ({len(non_churners)/len(features_df)*100:.1f}%)")

        # Calculate correlations with churn
        numeric_cols = features_df.select_dtypes(include=[np.number]).columns
        correlations = []

        for col in numeric_cols:
            if col != 'will_churn':
                corr = features_df[col].corr(features_df['will_churn'].astype(int))
                if not pd.isna(corr):
                    correlations.append((col, corr))

        # Sort by absolute correlation
        correlations.sort(key=lambda x: abs(x[1]), reverse=True)

        print("\nTop 15 features correlated with churn:")
        print(f"{'Feature':<40} {'Correlation':>12}")
        print("-" * 55)
        for feat, corr in correlations[:15]:
            print(f"{feat:<40} {corr:>12.4f}")

        # Compare churner vs non-churner distributions for key features
        print("\n" + "=" * 70)
        print("KEY FEATURE COMPARISON")
        print("=" * 70)

        key_features = [
            'avg_engagement_30d',
            'no_show_rate_30d',
            'reschedule_rate_30d',
            'sessions_per_week_30d',
            'engagement_decline_7d_vs_30d',
            'behavioral_risk_score'
        ]

        print(f"\n{'Feature':<35} {'Churners':>12} {'Non-Churners':>12} {'Difference':>12}")
        print("-" * 75)

        for feat in key_features:
            if feat in features_df.columns:
                churner_mean = churners[feat].mean()
                non_churner_mean = non_churners[feat].mean()
                diff = churner_mean - non_churner_mean

                print(f"{feat:<35} {churner_mean:>12.4f} {non_churner_mean:>12.4f} {diff:>12.4f}")

    # Data quality checks
    print("\n" + "=" * 70)
    print("DATA QUALITY")
    print("=" * 70)

    print(f"\nMissing values:")
    missing_counts = features_df.isnull().sum()
    missing_features = missing_counts[missing_counts > 0]

    if len(missing_features) > 0:
        print(f"  Features with missing values: {len(missing_features)}")
        for feat, count in missing_features.items():
            print(f"    {feat}: {count} ({count/len(features_df)*100:.1f}%)")
    else:
        print("  ✓ No missing values!")

    # Feature value ranges
    print(f"\nFeature ranges (sample):")
    sample_features = ['avg_engagement_30d', 'no_show_rate_30d', 'sessions_30d']
    for feat in sample_features:
        if feat in features_df.columns:
            print(f"  {feat}:")
            print(f"    Min: {features_df[feat].min():.4f}")
            print(f"    Max: {features_df[feat].max():.4f}")
            print(f"    Mean: {features_df[feat].mean():.4f}")
            print(f"    Std: {features_df[feat].std():.4f}")

    print("\n" + "=" * 70)
    print("✓ Feature engineering analysis complete!")
    print("=" * 70)
    print("\nNext step: Train XGBoost model (Task 4.3)")
    print()


if __name__ == "__main__":
    main()
