"""
Tests for churn prediction data preparation.
"""

import pytest
import pandas as pd
import tempfile
import shutil
from pathlib import Path

from src.evaluation.data_preparation import ChurnDataGenerator, ChurnConfig, prepare_churn_dataset


class TestChurnDataGenerator:
    """Tests for ChurnDataGenerator."""

    def test_data_generation_basic(self):
        """Test basic data generation works."""
        config = ChurnConfig(
            num_tutors=50,
            days_history=7,
            churn_rate=0.2,
            seed=42
        )

        generator = ChurnDataGenerator(config)
        tutors_df, sessions_df, feedback_df = generator.generate_historical_data()

        # Verify data was generated
        assert len(tutors_df) == 50
        assert len(sessions_df) > 0
        assert len(feedback_df) > 0

        # Verify no nulls in critical columns
        assert tutors_df["tutor_id"].notna().all()
        assert sessions_df["session_id"].notna().all()
        assert feedback_df["feedback_id"].notna().all()

    def test_churn_label_distribution(self):
        """Test that churn labels are assigned correctly."""
        config = ChurnConfig(
            num_tutors=100,
            days_history=30,
            churn_rate=0.15,
            seed=42
        )

        generator = ChurnDataGenerator(config)
        tutors_df, _, _ = generator.generate_historical_data()

        # Check churn rate is approximately correct (allow 10% variance)
        actual_churn_rate = tutors_df["will_churn"].mean()
        assert 0.10 <= actual_churn_rate <= 0.20

        # Verify churners have churn_day assigned
        churners = tutors_df[tutors_df["will_churn"] == True]
        assert churners["churn_day"].notna().all()

        # Verify non-churners don't have churn_day
        non_churners = tutors_df[tutors_df["will_churn"] == False]
        assert non_churners["churn_day"].isna().all()

    def test_temporal_coverage(self):
        """Test that sessions cover the full time period."""
        config = ChurnConfig(
            num_tutors=30,
            days_history=30,
            seed=42
        )

        generator = ChurnDataGenerator(config)
        _, sessions_df, _ = generator.generate_historical_data()

        # Convert to datetime
        sessions_df["scheduled_start"] = pd.to_datetime(sessions_df["scheduled_start"])

        # Check time range
        time_range = (sessions_df["scheduled_start"].max() - sessions_df["scheduled_start"].min()).days
        assert time_range >= 25  # Allow some variance

    def test_churn_patterns_in_sessions(self):
        """Test that churning tutors show declining patterns."""
        config = ChurnConfig(
            num_tutors=100,
            days_history=60,
            churn_rate=0.3,
            seed=42
        )

        generator = ChurnDataGenerator(config)
        tutors_df, sessions_df, _ = generator.generate_historical_data()

        # Get churners
        churners = tutors_df[tutors_df["will_churn"] == True]

        if len(churners) > 0:
            churner_id = churners.iloc[0]["tutor_id"]
            churner_sessions = sessions_df[sessions_df["tutor_id"] == churner_id]

            # Churners should have some no-shows and reschedules
            no_show_rate = churner_sessions["no_show"].mean()
            reschedule_rate = churner_sessions["tutor_initiated_reschedule"].mean()

            # At least one of these should be elevated
            assert no_show_rate > 0.05 or reschedule_rate > 0.10

    def test_data_validation(self):
        """Test that data validation catches issues."""
        config = ChurnConfig(
            num_tutors=50,
            days_history=14,
            seed=42
        )

        generator = ChurnDataGenerator(config)
        tutors_df, sessions_df, feedback_df = generator.generate_historical_data()

        # Verify data constraints
        assert tutors_df["baseline_sessions_per_week"].between(0, 50).all()
        assert sessions_df["engagement_score"].between(0, 1).all()
        assert feedback_df["overall_rating"].between(1, 5).all()

        # Verify referential integrity
        tutor_ids = set(tutors_df["tutor_id"])
        session_tutor_ids = set(sessions_df["tutor_id"])
        assert session_tutor_ids.issubset(tutor_ids)

        session_ids = set(sessions_df["session_id"])
        feedback_session_ids = set(feedback_df["session_id"])
        assert feedback_session_ids.issubset(session_ids)

    def test_prepare_churn_dataset(self):
        """Test end-to-end dataset preparation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ChurnConfig(
                num_tutors=30,
                days_history=7,
                seed=42
            )

            tutors_df, sessions_df, feedback_df = prepare_churn_dataset(
                output_dir=tmpdir,
                config=config
            )

            # Verify files were created
            assert Path(tmpdir, "tutors.csv").exists()
            assert Path(tmpdir, "sessions.csv").exists()
            assert Path(tmpdir, "feedback.csv").exists()

            # Verify data can be read back
            tutors_loaded = pd.read_csv(Path(tmpdir, "tutors.csv"))
            assert len(tutors_loaded) == len(tutors_df)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
