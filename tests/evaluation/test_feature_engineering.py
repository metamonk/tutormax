"""
Tests for churn prediction feature engineering.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.evaluation.feature_engineering import ChurnFeatureEngineer, engineer_churn_features


class TestChurnFeatureEngineer:
    """Tests for ChurnFeatureEngineer."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        # Sample tutors
        tutors_df = pd.DataFrame({
            'tutor_id': ['t1', 't2', 't3'],
            'baseline_sessions_per_week': [15, 10, 20],
            'tenure_days': [100, 50, 200],
            'behavioral_archetype': ['high_performer', 'churner', 'steady'],
            'will_churn': [False, True, False]
        })

        # Sample sessions
        now = pd.Timestamp.now()
        sessions_df = pd.DataFrame({
            'session_id': ['s1', 's2', 's3', 's4', 's5'],
            'tutor_id': ['t1', 't1', 't2', 't2', 't3'],
            'student_id': ['st1', 'st1', 'st2', 'st2', 'st3'],
            'scheduled_start': [
                now - pd.Timedelta(days=5),
                now - pd.Timedelta(days=3),
                now - pd.Timedelta(days=10),
                now - pd.Timedelta(days=2),
                now - pd.Timedelta(days=1)
            ],
            'is_first_session': [True, False, True, False, True],
            'no_show': [False, False, True, False, False],
            'tutor_initiated_reschedule': [False, False, True, True, False],
            'engagement_score': [0.8, 0.9, 0.3, 0.4, 0.85],
            'learning_objectives_met': [True, True, False, False, True]
        })

        # Sample feedback
        feedback_df = pd.DataFrame({
            'session_id': ['s1', 's2', 's3', 's5'],
            'overall_rating': [5, 5, 2, 4],
            'subject_knowledge_rating': [5, 5, 2, 4],
            'communication_rating': [5, 5, 3, 4],
            'submitted_at': [
                now - pd.Timedelta(days=4),
                now - pd.Timedelta(days=2),
                now - pd.Timedelta(days=9),
                now - pd.Timedelta(days=0.5)
            ]
        })

        return tutors_df, sessions_df, feedback_df

    def test_feature_creation(self, sample_data):
        """Test that features are created successfully."""
        tutors_df, sessions_df, feedback_df = sample_data

        engineer = ChurnFeatureEngineer()
        features_df = engineer.create_features(tutors_df, sessions_df, feedback_df)

        # Should have one row per tutor
        assert len(features_df) == len(tutors_df)

        # Should have tutor_id column
        assert 'tutor_id' in features_df.columns

        # Should have some engineered features
        assert len(features_df.columns) > 10

    def test_static_features(self, sample_data):
        """Test that static features are added."""
        tutors_df, sessions_df, feedback_df = sample_data

        engineer = ChurnFeatureEngineer()
        features_df = engineer.create_features(tutors_df, sessions_df, feedback_df)

        # Should include baseline sessions
        assert 'baseline_sessions_per_week' in features_df.columns

        # Should include tenure
        assert 'tenure_days' in features_df.columns

        # Should include archetype encoding
        archetype_cols = [c for c in features_df.columns if 'archetype_' in c]
        assert len(archetype_cols) > 0

    def test_time_window_features(self, sample_data):
        """Test that time-windowed features are created."""
        tutors_df, sessions_df, feedback_df = sample_data

        engineer = ChurnFeatureEngineer()
        features_df = engineer.create_features(tutors_df, sessions_df, feedback_df)

        # Check for 7-day window features
        assert 'sessions_7d' in features_df.columns
        assert 'avg_engagement_7d' in features_df.columns
        assert 'no_show_rate_7d' in features_df.columns

        # Check for 30-day window features
        assert 'sessions_30d' in features_df.columns
        assert 'avg_rating_30d' in features_df.columns

    def test_trend_features(self, sample_data):
        """Test that trend features are created."""
        tutors_df, sessions_df, feedback_df = sample_data

        engineer = ChurnFeatureEngineer()
        features_df = engineer.create_features(tutors_df, sessions_df, feedback_df)

        # Check for decline features
        decline_cols = [c for c in features_df.columns if 'decline' in c or 'increase' in c]
        assert len(decline_cols) > 0

    def test_composite_features(self, sample_data):
        """Test that composite features are created."""
        tutors_df, sessions_df, feedback_df = sample_data

        engineer = ChurnFeatureEngineer()
        features_df = engineer.create_features(tutors_df, sessions_df, feedback_df)

        # Check for composite score features
        assert 'behavioral_risk_score' in features_df.columns or 'engagement_momentum' in features_df.columns

    def test_no_missing_values(self, sample_data):
        """Test that missing values are handled."""
        tutors_df, sessions_df, feedback_df = sample_data

        engineer = ChurnFeatureEngineer()
        features_df = engineer.create_features(tutors_df, sessions_df, feedback_df)

        # Should have no missing values (except possibly will_churn if not in input)
        numeric_cols = features_df.select_dtypes(include=[np.number]).columns
        missing_counts = features_df[numeric_cols].isnull().sum()
        assert missing_counts.sum() == 0

    def test_feature_ranges(self, sample_data):
        """Test that features have reasonable value ranges."""
        tutors_df, sessions_df, feedback_df = sample_data

        engineer = ChurnFeatureEngineer()
        features_df = engineer.create_features(tutors_df, sessions_df, feedback_df)

        # Rates should be between 0 and 1
        rate_cols = [c for c in features_df.columns if 'rate' in c]
        for col in rate_cols:
            assert features_df[col].min() >= 0
            assert features_df[col].max() <= 1

        # Session counts should be non-negative
        session_cols = [c for c in features_df.columns if 'sessions_' in c and 'd' in c]
        for col in session_cols:
            assert features_df[col].min() >= 0

    def test_engineer_churn_features_full_dataset(self):
        """Test feature engineering on full generated dataset."""
        # Load actual generated data
        data_dir = Path("output/churn_data")

        if not data_dir.exists():
            pytest.skip("Churn data not generated yet")

        tutors_df = pd.read_csv(data_dir / "tutors.csv")
        sessions_df = pd.read_csv(data_dir / "sessions.csv")
        feedback_df = pd.read_csv(data_dir / "feedback.csv")

        features_df = engineer_churn_features(tutors_df, sessions_df, feedback_df)

        # Basic checks
        assert len(features_df) == len(tutors_df)
        assert 'tutor_id' in features_df.columns
        assert 'will_churn' in features_df.columns

        # Should have substantial number of features
        assert len(features_df.columns) > 30

        # No missing values
        assert features_df.isnull().sum().sum() == 0

    def test_churn_correlation(self):
        """Test that features correlate with churn label."""
        data_dir = Path("output/churn_data")

        if not data_dir.exists():
            pytest.skip("Churn data not generated yet")

        tutors_df = pd.read_csv(data_dir / "tutors.csv")
        sessions_df = pd.read_csv(data_dir / "sessions.csv")
        feedback_df = pd.read_csv(data_dir / "feedback.csv")

        features_df = engineer_churn_features(tutors_df, sessions_df, feedback_df)

        # At least some features should correlate with churn
        numeric_cols = features_df.select_dtypes(include=[np.number]).columns
        correlations = []

        for col in numeric_cols:
            if col != 'will_churn':
                corr = features_df[col].corr(features_df['will_churn'].astype(int))
                if not pd.isna(corr):
                    correlations.append(abs(corr))

        # At least one feature should have |correlation| > 0.3
        assert max(correlations) > 0.3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
