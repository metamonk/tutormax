"""
Feature engineering for churn prediction.

Creates comprehensive features across multiple time windows including:
- Performance metrics (ratings, engagement, objectives met)
- Behavioral patterns (no-shows, reschedules, consistency)
- Trend features (engagement decline, performance deterioration)
- Temporal features (tenure, recency, frequency)
"""

from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class ChurnFeatureEngineer:
    """
    Engineer features for tutor churn prediction.

    Creates features across multiple time windows and calculates trends.
    """

    # Time windows for feature calculation (days)
    TIME_WINDOWS = [7, 14, 30, 90]

    def __init__(self, reference_date: Optional[datetime] = None):
        """
        Initialize feature engineer.

        Args:
            reference_date: Reference date for calculating features (default: now)
        """
        self.reference_date = reference_date or pd.Timestamp.now()

    def create_features(
        self,
        tutors_df: pd.DataFrame,
        sessions_df: pd.DataFrame,
        feedback_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Create comprehensive feature matrix for churn prediction.

        Args:
            tutors_df: Tutor profiles
            sessions_df: Session history
            feedback_df: Student feedback

        Returns:
            DataFrame with features for each tutor
        """
        print("=" * 70)
        print("FEATURE ENGINEERING")
        print("=" * 70)
        print(f"\nReference date: {self.reference_date}")
        print(f"Time windows: {self.TIME_WINDOWS} days")

        # Ensure datetime types
        sessions_df = sessions_df.copy()
        sessions_df['scheduled_start'] = pd.to_datetime(sessions_df['scheduled_start'])
        feedback_df = feedback_df.copy()
        feedback_df['submitted_at'] = pd.to_datetime(feedback_df['submitted_at'])

        # Merge feedback into sessions
        sessions_with_feedback = sessions_df.merge(
            feedback_df[['session_id', 'overall_rating', 'subject_knowledge_rating',
                        'communication_rating']],
            on='session_id',
            how='left'
        )

        print(f"\nData shapes:")
        print(f"  Tutors: {len(tutors_df):,}")
        print(f"  Sessions: {len(sessions_df):,}")
        print(f"  Sessions with feedback: {sessions_with_feedback['overall_rating'].notna().sum():,}")

        # Initialize feature dataframe
        features_df = tutors_df[['tutor_id']].copy()

        # Add static tutor features
        print("\n1. Creating static tutor features...")
        features_df = self._add_static_features(features_df, tutors_df)

        # Add time-windowed features
        print("2. Creating time-windowed features...")
        for window in self.TIME_WINDOWS:
            print(f"   Processing {window}-day window...")
            window_features = self._create_window_features(
                tutors_df['tutor_id'],
                sessions_with_feedback,
                window
            )
            features_df = features_df.merge(window_features, on='tutor_id', how='left')

        # Add trend features
        print("3. Creating trend features...")
        features_df = self._add_trend_features(features_df)

        # Add composite features
        print("4. Creating composite features...")
        features_df = self._add_composite_features(features_df)

        # Fill missing values
        print("5. Handling missing values...")
        features_df = self._handle_missing_values(features_df)

        # Add target variable if available
        if 'will_churn' in tutors_df.columns:
            features_df = features_df.merge(
                tutors_df[['tutor_id', 'will_churn']],
                on='tutor_id',
                how='left'
            )

        print(f"\n✓ Feature engineering complete!")
        print(f"  Total features: {len(features_df.columns) - 1}")  # Exclude tutor_id
        print(f"  Tutor count: {len(features_df):,}")

        return features_df

    def _add_static_features(
        self,
        features_df: pd.DataFrame,
        tutors_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Add static tutor features."""
        static_features = tutors_df[[
            'tutor_id',
            'baseline_sessions_per_week',
            'tenure_days'
        ]].copy()

        # Add categorical encoding for behavioral archetype
        if 'behavioral_archetype' in tutors_df.columns:
            archetype_dummies = pd.get_dummies(
                tutors_df['behavioral_archetype'],
                prefix='archetype'
            )
            static_features = pd.concat([static_features, archetype_dummies], axis=1)

        return features_df.merge(static_features, on='tutor_id', how='left')

    def _create_window_features(
        self,
        tutor_ids: pd.Series,
        sessions_df: pd.DataFrame,
        window_days: int
    ) -> pd.DataFrame:
        """
        Create features for a specific time window.

        Args:
            tutor_ids: Series of tutor IDs
            sessions_df: Sessions with feedback merged
            window_days: Number of days in window

        Returns:
            DataFrame with window-specific features
        """
        window_start = self.reference_date - timedelta(days=window_days)
        window_sessions = sessions_df[
            sessions_df['scheduled_start'] >= window_start
        ].copy()

        # Aggregate by tutor
        features = []

        for tutor_id in tutor_ids:
            tutor_sessions = window_sessions[window_sessions['tutor_id'] == tutor_id]

            feature_dict = {
                'tutor_id': tutor_id,
                f'sessions_{window_days}d': len(tutor_sessions),
                f'no_show_rate_{window_days}d': tutor_sessions['no_show'].mean() if len(tutor_sessions) > 0 else 0,
                f'reschedule_rate_{window_days}d': tutor_sessions['tutor_initiated_reschedule'].mean() if len(tutor_sessions) > 0 else 0,
                f'avg_engagement_{window_days}d': tutor_sessions['engagement_score'].mean() if len(tutor_sessions) > 0 else np.nan,
                f'avg_rating_{window_days}d': tutor_sessions['overall_rating'].mean() if len(tutor_sessions) > 0 else np.nan,
                f'objectives_met_rate_{window_days}d': tutor_sessions['learning_objectives_met'].mean() if len(tutor_sessions) > 0 else np.nan,
                f'first_session_count_{window_days}d': tutor_sessions['is_first_session'].sum() if len(tutor_sessions) > 0 else 0,
            }

            # Calculate first session success rate
            first_sessions = tutor_sessions[tutor_sessions['is_first_session'] == True]
            if len(first_sessions) > 0:
                feature_dict[f'first_session_success_rate_{window_days}d'] = (
                    first_sessions['overall_rating'] >= 4
                ).mean()
            else:
                feature_dict[f'first_session_success_rate_{window_days}d'] = np.nan

            # Session frequency (sessions per week)
            feature_dict[f'sessions_per_week_{window_days}d'] = (
                len(tutor_sessions) / (window_days / 7) if window_days > 0 else 0
            )

            # Engagement volatility (std of engagement scores)
            feature_dict[f'engagement_volatility_{window_days}d'] = (
                tutor_sessions['engagement_score'].std() if len(tutor_sessions) > 1 else 0
            )

            features.append(feature_dict)

        return pd.DataFrame(features)

    def _add_trend_features(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """
        Add trend features comparing different time windows.

        Calculates changes between short and long windows to detect decline.
        """
        trend_features = features_df.copy()

        # Engagement trends
        if 'avg_engagement_7d' in features_df.columns and 'avg_engagement_30d' in features_df.columns:
            trend_features['engagement_decline_7d_vs_30d'] = (
                features_df['avg_engagement_30d'] - features_df['avg_engagement_7d']
            )

        if 'avg_engagement_30d' in features_df.columns and 'avg_engagement_90d' in features_df.columns:
            trend_features['engagement_decline_30d_vs_90d'] = (
                features_df['avg_engagement_90d'] - features_df['avg_engagement_30d']
            )

        # Rating trends
        if 'avg_rating_7d' in features_df.columns and 'avg_rating_30d' in features_df.columns:
            trend_features['rating_decline_7d_vs_30d'] = (
                features_df['avg_rating_30d'] - features_df['avg_rating_7d']
            )

        # Session volume trends
        if 'sessions_per_week_7d' in features_df.columns and 'sessions_per_week_30d' in features_df.columns:
            trend_features['session_volume_decline_7d_vs_30d'] = (
                features_df['sessions_per_week_30d'] - features_df['sessions_per_week_7d']
            )

        if 'sessions_per_week_30d' in features_df.columns and 'sessions_per_week_90d' in features_df.columns:
            trend_features['session_volume_decline_30d_vs_90d'] = (
                features_df['sessions_per_week_90d'] - features_df['sessions_per_week_30d']
            )

        # Reschedule rate increase (negative is good, positive is bad)
        if 'reschedule_rate_7d' in features_df.columns and 'reschedule_rate_30d' in features_df.columns:
            trend_features['reschedule_increase_7d_vs_30d'] = (
                features_df['reschedule_rate_7d'] - features_df['reschedule_rate_30d']
            )

        # No-show rate increase
        if 'no_show_rate_7d' in features_df.columns and 'no_show_rate_30d' in features_df.columns:
            trend_features['no_show_increase_7d_vs_30d'] = (
                features_df['no_show_rate_7d'] - features_df['no_show_rate_30d']
            )

        return trend_features

    def _add_composite_features(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """
        Add composite features derived from multiple base features.
        """
        composite_features = features_df.copy()

        # Engagement momentum (positive = improving, negative = declining)
        engagement_cols = [c for c in features_df.columns if 'engagement_decline' in c]
        if engagement_cols:
            composite_features['engagement_momentum'] = -features_df[engagement_cols].mean(axis=1)

        # Performance consistency (lower is more consistent)
        volatility_cols = [c for c in features_df.columns if 'volatility' in c]
        if volatility_cols:
            composite_features['performance_consistency'] = 1 / (1 + features_df[volatility_cols].mean(axis=1))

        # Behavioral risk score (higher = more risk)
        risk_components = []
        if 'no_show_rate_30d' in features_df.columns:
            risk_components.append(features_df['no_show_rate_30d'] * 2.0)  # Weight no-shows heavily
        if 'reschedule_rate_30d' in features_df.columns:
            risk_components.append(features_df['reschedule_rate_30d'] * 1.5)
        if 'avg_engagement_30d' in features_df.columns:
            risk_components.append((1 - features_df['avg_engagement_30d']) * 1.0)
        if 'avg_rating_30d' in features_df.columns:
            risk_components.append((5 - features_df['avg_rating_30d']) / 5 * 1.0)

        if risk_components:
            composite_features['behavioral_risk_score'] = sum(risk_components) / len(risk_components)

        # Activity level (sessions per week relative to baseline)
        if 'sessions_per_week_30d' in features_df.columns and 'baseline_sessions_per_week' in features_df.columns:
            composite_features['activity_vs_baseline'] = (
                features_df['sessions_per_week_30d'] / features_df['baseline_sessions_per_week'].replace(0, 1)
            )

        return composite_features

    def _handle_missing_values(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle missing values in features.

        Strategy:
        - Rates (0-1): Fill with 0
        - Counts: Fill with 0
        - Averages: Fill with median
        - Trends: Fill with 0 (no change)
        """
        df = features_df.copy()

        for col in df.columns:
            if col == 'tutor_id' or col == 'will_churn':
                continue

            if df[col].isna().any():
                if 'rate' in col or 'decline' in col or 'increase' in col or 'momentum' in col:
                    df[col] = df[col].fillna(0)
                elif 'count' in col or 'sessions_' in col:
                    df[col] = df[col].fillna(0)
                elif 'avg_' in col or 'volatility' in col:
                    median_val = df[col].median()
                    df[col] = df[col].fillna(median_val if not pd.isna(median_val) else 0)
                elif 'score' in col:
                    df[col] = df[col].fillna(df[col].median() if df[col].notna().any() else 0)
                else:
                    # Default: fill with median or 0
                    median_val = df[col].median()
                    df[col] = df[col].fillna(median_val if not pd.isna(median_val) else 0)

        return df


def engineer_churn_features(
    tutors_df: pd.DataFrame,
    sessions_df: pd.DataFrame,
    feedback_df: pd.DataFrame,
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Convenience function to engineer features for churn prediction.

    Args:
        tutors_df: Tutor profiles
        sessions_df: Session history
        feedback_df: Student feedback
        output_path: Optional path to save features CSV

    Returns:
        DataFrame with engineered features
    """
    engineer = ChurnFeatureEngineer()
    features_df = engineer.create_features(tutors_df, sessions_df, feedback_df)

    if output_path:
        features_df.to_csv(output_path, index=False)
        print(f"\n✓ Features saved to: {output_path}")

    return features_df


if __name__ == "__main__":
    # Demo execution
    import sys

    # Load data
    tutors_df = pd.read_csv("output/churn_data/tutors.csv")
    sessions_df = pd.read_csv("output/churn_data/sessions.csv")
    feedback_df = pd.read_csv("output/churn_data/feedback.csv")

    # Engineer features
    features_df = engineer_churn_features(
        tutors_df,
        sessions_df,
        feedback_df,
        output_path="output/churn_data/features.csv"
    )

    print(f"\nFeature matrix shape: {features_df.shape}")
    print(f"\nSample features:")
    print(features_df.head())
