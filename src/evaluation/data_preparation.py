"""
Data preparation module for churn prediction.

Generates comprehensive time-series synthetic data showing:
- Engagement decline patterns
- Performance trend deterioration
- Reschedule pattern increases
- Historical behavior for churned vs active tutors
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import pandas as pd
import numpy as np
from dataclasses import dataclass

from src.data_generation.tutor_generator import TutorGenerator, BehavioralArchetype
from src.data_generation.session_generator import SessionGenerator
from src.data_generation.feedback_generator import FeedbackGenerator


@dataclass
class ChurnConfig:
    """Configuration for churn data generation."""
    num_tutors: int = 300
    days_history: int = 90
    churn_rate: float = 0.15  # 15% of tutors will churn
    sessions_per_day_mean: int = 3000
    feedback_rate: float = 0.85
    seed: int = 42


class ChurnDataGenerator:
    """
    Generates comprehensive synthetic data for churn prediction with time-series patterns.
    """

    def __init__(self, config: Optional[ChurnConfig] = None):
        """
        Initialize churn data generator.

        Args:
            config: Configuration for data generation
        """
        self.config = config or ChurnConfig()
        self.random = random.Random(self.config.seed)
        self.np_random = np.random.RandomState(self.config.seed)

        # Initialize base generators
        self.tutor_gen = TutorGenerator(seed=self.config.seed)
        self.session_gen = SessionGenerator(seed=self.config.seed)
        self.feedback_gen = FeedbackGenerator(seed=self.config.seed)

        # Track generated data
        self.tutors: List[Dict] = []
        self.all_sessions: List[Dict] = []
        self.all_feedback: List[Dict] = []

    def generate_historical_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Generate comprehensive historical data with churn patterns.

        Returns:
            Tuple of (tutors_df, sessions_df, feedback_df)
        """
        print(f"Generating {self.config.num_tutors} tutors with {self.config.days_history} days of history...")

        # Generate tutors with assigned churn status
        self.tutors = self._generate_tutors_with_churn_labels()

        # Generate daily sessions for each day in history
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.config.days_history)

        print(f"Generating sessions from {start_date.date()} to {end_date.date()}...")

        current_date = start_date
        day_num = 0

        while current_date <= end_date:
            # Generate sessions for this day with progression patterns
            day_sessions = self._generate_day_sessions(current_date, day_num)
            self.all_sessions.extend(day_sessions)

            current_date += timedelta(days=1)
            day_num += 1

            if day_num % 10 == 0:
                print(f"  Generated day {day_num}/{self.config.days_history} ({len(self.all_sessions):,} sessions so far)")

        print(f"Total sessions generated: {len(self.all_sessions):,}")

        # Generate feedback for sessions
        print("Generating student feedback...")
        tutors_dict = {t["tutor_id"]: t for t in self.tutors}
        self.all_feedback = self.feedback_gen.generate_feedback_for_sessions(
            sessions=self.all_sessions,
            tutors=tutors_dict,
            feedback_rate=self.config.feedback_rate
        )

        print(f"Total feedback generated: {len(self.all_feedback):,}")

        # Convert to DataFrames
        tutors_df = pd.DataFrame(self.tutors)
        sessions_df = pd.DataFrame(self.all_sessions)
        feedback_df = pd.DataFrame(self.all_feedback)

        # Clean and validate
        tutors_df, sessions_df, feedback_df = self._clean_and_validate(
            tutors_df, sessions_df, feedback_df
        )

        print("\nData generation complete!")
        self._print_summary_stats(tutors_df, sessions_df, feedback_df)

        return tutors_df, sessions_df, feedback_df

    def _generate_tutors_with_churn_labels(self) -> List[Dict]:
        """Generate tutors with churn labels and patterns."""
        tutors = self.tutor_gen.generate_tutors(count=self.config.num_tutors)

        # Assign churn labels
        num_churners = int(self.config.num_tutors * self.config.churn_rate)

        # Prioritize churner archetype for churn, but also include some at_risk
        churner_candidates = [
            t for t in tutors
            if t["behavioral_archetype"] in ["churner", "at_risk"]
        ]
        non_churner_candidates = [
            t for t in tutors
            if t["behavioral_archetype"] not in ["churner", "at_risk"]
        ]

        # Select churners (prioritize churner archetype)
        self.random.shuffle(churner_candidates)
        self.random.shuffle(non_churner_candidates)

        churners = churner_candidates[:num_churners]
        if len(churners) < num_churners:
            # Need more churners, take some from at-risk
            additional = num_churners - len(churners)
            churners.extend(non_churner_candidates[:additional])
            non_churners = non_churner_candidates[additional:]
        else:
            non_churners = non_churner_candidates

        # Add remaining non-churners
        non_churners.extend(churner_candidates[num_churners:])

        # Label tutors
        for tutor in churners:
            tutor["will_churn"] = True
            # Assign churn day (randomly in last 30 days)
            tutor["churn_day"] = self.random.randint(
                self.config.days_history - 30,
                self.config.days_history
            )

        for tutor in non_churners:
            tutor["will_churn"] = False
            tutor["churn_day"] = None

        all_tutors = churners + non_churners
        self.random.shuffle(all_tutors)

        return all_tutors

    def _generate_day_sessions(self, date: datetime, day_num: int) -> List[Dict]:
        """
        Generate sessions for a single day with behavioral progression.

        Args:
            date: Date for sessions
            day_num: Day number in the sequence (0-indexed)

        Returns:
            List of session dictionaries
        """
        day_sessions = []

        # Calculate progression factor for each tutor
        for tutor in self.tutors:
            # Skip if tutor has already churned
            if tutor.get("will_churn") and tutor.get("churn_day") <= day_num:
                continue

            # Determine session count based on progression
            base_sessions_per_week = tutor["baseline_sessions_per_week"]
            sessions_per_day = base_sessions_per_week / 7

            # Apply progression factor
            if tutor.get("will_churn"):
                # Churners: decline in sessions over time
                progression_factor = self._get_churn_progression_factor(
                    day_num, tutor["churn_day"]
                )
            else:
                # Non-churners: stable or slight growth
                progression_factor = 1.0 + self.np_random.uniform(-0.1, 0.2)

            # Calculate sessions for this day with some randomness
            expected_sessions = sessions_per_day * progression_factor
            actual_sessions = max(0, int(self.np_random.poisson(expected_sessions)))

            # Generate sessions
            for _ in range(actual_sessions):
                session = self.session_gen.generate_session(
                    tutor=tutor,
                    scheduled_date=date + timedelta(
                        hours=self.random.randint(8, 20),
                        minutes=self.random.randint(0, 59)
                    )
                )

                # Apply churn-related modifications
                if tutor.get("will_churn"):
                    session = self._apply_churn_patterns(session, day_num, tutor["churn_day"])

                day_sessions.append(session)

        return day_sessions

    def _get_churn_progression_factor(self, current_day: int, churn_day: int) -> float:
        """
        Calculate progression factor for churning tutors.

        Returns factor that decreases as tutor approaches churn.
        """
        days_until_churn = churn_day - current_day

        if days_until_churn <= 0:
            return 0.0  # Already churned

        # Decline accelerates as churn approaches
        if days_until_churn <= 7:
            return 0.3 + self.np_random.uniform(-0.1, 0.1)
        elif days_until_churn <= 14:
            return 0.5 + self.np_random.uniform(-0.1, 0.1)
        elif days_until_churn <= 30:
            return 0.7 + self.np_random.uniform(-0.1, 0.1)
        else:
            return 0.9 + self.np_random.uniform(-0.1, 0.1)

    def _apply_churn_patterns(
        self,
        session: Dict,
        current_day: int,
        churn_day: int
    ) -> Dict:
        """
        Modify session data to reflect churn patterns.

        Increases no-shows, reschedules, decreases engagement as churn approaches.
        """
        days_until_churn = churn_day - current_day

        if days_until_churn <= 0:
            return session

        # Increase no-show probability
        if days_until_churn <= 14:
            if self.random.random() < 0.25:  # 25% no-show rate
                session["no_show"] = True

        # Increase reschedule probability
        if days_until_churn <= 30:
            if self.random.random() < 0.20:  # 20% reschedule rate
                session["tutor_initiated_reschedule"] = True

        # Decrease engagement score
        if days_until_churn <= 30:
            decline_factor = 0.5 + (days_until_churn / 60)  # More decline as churn approaches
            session["engagement_score"] = max(
                0.0,
                session["engagement_score"] * decline_factor
            )

        # Decrease learning objectives met
        if days_until_churn <= 21:
            if self.random.random() > 0.6:  # 40% not met
                session["learning_objectives_met"] = False

        return session

    def _clean_and_validate(
        self,
        tutors_df: pd.DataFrame,
        sessions_df: pd.DataFrame,
        feedback_df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Clean and validate generated data.

        - Remove anomalies
        - Handle missing values
        - Validate data types and ranges
        """
        print("\nCleaning and validating data...")

        # Tutors cleanup
        initial_tutors = len(tutors_df)
        tutors_df = tutors_df.dropna(subset=["tutor_id", "name", "email"])
        tutors_df = tutors_df.drop_duplicates(subset=["tutor_id"])
        print(f"  Tutors: {initial_tutors} -> {len(tutors_df)} (removed {initial_tutors - len(tutors_df)} invalid)")

        # Sessions cleanup
        initial_sessions = len(sessions_df)
        sessions_df = sessions_df.dropna(subset=["session_id", "tutor_id", "student_id"])
        sessions_df = sessions_df.drop_duplicates(subset=["session_id"])

        # Validate tutors exist
        valid_tutor_ids = set(tutors_df["tutor_id"])
        sessions_df = sessions_df[sessions_df["tutor_id"].isin(valid_tutor_ids)]
        print(f"  Sessions: {initial_sessions} -> {len(sessions_df)} (removed {initial_sessions - len(sessions_df)} invalid)")

        # Feedback cleanup
        initial_feedback = len(feedback_df)
        feedback_df = feedback_df.dropna(subset=["feedback_id", "session_id", "overall_rating"])
        feedback_df = feedback_df.drop_duplicates(subset=["feedback_id"])

        # Validate sessions exist
        valid_session_ids = set(sessions_df["session_id"])
        feedback_df = feedback_df[feedback_df["session_id"].isin(valid_session_ids)]
        print(f"  Feedback: {initial_feedback} -> {len(feedback_df)} (removed {initial_feedback - len(feedback_df)} invalid)")

        # Validate data ranges
        assert tutors_df["baseline_sessions_per_week"].between(0, 50).all(), "Invalid session baseline"
        assert sessions_df["engagement_score"].between(0, 1).all(), "Invalid engagement scores"
        assert feedback_df["overall_rating"].between(1, 5).all(), "Invalid ratings"

        print("  Data validation passed!")

        return tutors_df, sessions_df, feedback_df

    def _print_summary_stats(
        self,
        tutors_df: pd.DataFrame,
        sessions_df: pd.DataFrame,
        feedback_df: pd.DataFrame
    ):
        """Print summary statistics of generated data."""
        print("\n" + "=" * 60)
        print("DATASET SUMMARY")
        print("=" * 60)

        print(f"\nTutors: {len(tutors_df):,}")
        if "will_churn" in tutors_df.columns:
            churn_counts = tutors_df["will_churn"].value_counts()
            print(f"  Will churn: {churn_counts.get(True, 0):,} ({churn_counts.get(True, 0)/len(tutors_df)*100:.1f}%)")
            print(f"  Will stay:  {churn_counts.get(False, 0):,} ({churn_counts.get(False, 0)/len(tutors_df)*100:.1f}%)")

        print(f"\nSessions: {len(sessions_df):,}")
        print(f"  Avg per tutor: {len(sessions_df)/len(tutors_df):.1f}")
        print(f"  No-show rate: {sessions_df['no_show'].mean()*100:.2f}%")
        print(f"  Reschedule rate: {sessions_df['tutor_initiated_reschedule'].mean()*100:.2f}%")
        print(f"  Avg engagement: {sessions_df['engagement_score'].mean():.3f}")

        print(f"\nFeedback: {len(feedback_df):,}")
        print(f"  Feedback rate: {len(feedback_df)/len(sessions_df)*100:.1f}%")
        print(f"  Avg rating: {feedback_df['overall_rating'].mean():.2f}/5.0")

        print("=" * 60)


def prepare_churn_dataset(
    output_dir: str = "output/churn_data",
    config: Optional[ChurnConfig] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Prepare and save churn prediction dataset.

    Args:
        output_dir: Directory to save prepared data
        config: Data generation configuration

    Returns:
        Tuple of (tutors_df, sessions_df, feedback_df)
    """
    import os

    os.makedirs(output_dir, exist_ok=True)

    # Generate data
    generator = ChurnDataGenerator(config)
    tutors_df, sessions_df, feedback_df = generator.generate_historical_data()

    # Save to CSV
    print(f"\nSaving data to {output_dir}/...")
    tutors_df.to_csv(f"{output_dir}/tutors.csv", index=False)
    sessions_df.to_csv(f"{output_dir}/sessions.csv", index=False)
    feedback_df.to_csv(f"{output_dir}/feedback.csv", index=False)

    print("  tutors.csv")
    print("  sessions.csv")
    print("  feedback.csv")
    print("\n✓ Data preparation complete!")

    return tutors_df, sessions_df, feedback_df


if __name__ == "__main__":
    # Demo execution
    prepare_churn_dataset()
