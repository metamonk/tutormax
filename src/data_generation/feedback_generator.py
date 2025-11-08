"""
Student feedback data generator for TutorMax system.

Generates synthetic student feedback correlated with session quality
and tutor performance as defined in the PRD.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random
from uuid import uuid4

from faker import Faker
import numpy as np

from .tutor_generator import BehavioralArchetype


class FeedbackGenerator:
    """
    Generates synthetic student feedback for sessions.

    Feedback correlates with:
    - Tutor behavioral archetype
    - Session quality (engagement score, objectives met, late start)
    - First session indicator
    """

    # Positive feedback templates
    POSITIVE_FEEDBACK = [
        "Great session, very helpful!",
        "Excellent tutor, explained concepts clearly",
        "Patient and knowledgeable, would recommend",
        "Really helped me understand the material",
        "Very engaging and supportive",
        "Made learning fun and easy to understand",
        "Prepared well and answered all my questions",
        "Great at breaking down complex topics",
    ]

    # Neutral feedback templates
    NEUTRAL_FEEDBACK = [
        "Session was okay, covered the material",
        "Tutor was helpful overall",
        "Got through what we needed to cover",
        "Decent session, nothing special",
        "Tutor knew the subject well",
    ]

    # Negative feedback templates
    NEGATIVE_FEEDBACK = [
        "Tutor seemed unprepared",
        "Session started late and felt rushed",
        "Difficult to understand explanations",
        "Tutor seemed distracted during session",
        "Not very patient with my questions",
        "Technical issues interrupted the lesson",
        "Tutor didn't seem engaged",
    ]

    # First session specific feedback
    FIRST_SESSION_POSITIVE = [
        "Great first impression, looking forward to more sessions!",
        "Tutor made me feel comfortable right away",
        "Excellent start, very encouraging",
    ]

    FIRST_SESSION_NEGATIVE = [
        "Not what I expected for a first session",
        "Tutor seemed nervous and unprepared",
        "Started late which wasn't a good first impression",
    ]

    # Improvement areas for poor first sessions
    IMPROVEMENT_AREAS = [
        "late",
        "unprepared",
        "unclear",
        "not_patient",
        "technical_issues"
    ]

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the feedback generator.

        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)
            np.random.seed(seed)

        self.fake = Faker()
        if seed is not None:
            self.fake.seed_instance(seed)

        self._feedback_counter = 0

    def generate_feedback(
        self,
        session: Dict,
        tutor: Dict,
        feedback_id: Optional[str] = None,
        submitted_at: Optional[datetime] = None
    ) -> Dict:
        """
        Generate student feedback for a session.

        Args:
            session: Session data dictionary
            tutor: Tutor profile dictionary
            feedback_id: Optional custom feedback ID
            submitted_at: Optional submission timestamp

        Returns:
            Dict containing feedback data
        """
        self._feedback_counter += 1

        # Generate feedback ID
        if feedback_id is None:
            feedback_id = str(uuid4())

        # No feedback for no-show sessions
        if session["no_show"]:
            return None

        # Get session details
        is_first_session = session["is_first_session"]
        engagement_score = session["engagement_score"]
        late_start = session["late_start_minutes"]
        objectives_met = session["learning_objectives_met"]
        technical_issues = session["technical_issues"]

        # Get tutor archetype
        archetype = BehavioralArchetype(tutor["behavioral_archetype"])

        # Determine overall quality score (used to generate ratings)
        quality_score = self._calculate_quality_score(
            archetype,
            engagement_score,
            objectives_met,
            late_start,
            technical_issues,
            is_first_session
        )

        # Generate overall rating (1-5)
        overall_rating = self._generate_overall_rating(quality_score)

        # Generate category ratings
        category_ratings = self._generate_category_ratings(
            overall_rating,
            quality_score,
            archetype,
            technical_issues
        )

        # Generate text feedback
        free_text = self._generate_text_feedback(
            overall_rating,
            is_first_session,
            late_start,
            technical_issues
        )

        # Submission timing (2 hours to 24 hours after session)
        if submitted_at is None:
            session_start = datetime.fromisoformat(
                session["actual_start"] if session["actual_start"] else session["scheduled_start"]
            )
            hours_delay = random.uniform(2, 24)
            submitted_at = session_start + timedelta(hours=hours_delay)

        feedback_data = {
            "feedback_id": feedback_id,
            "session_id": session["session_id"],
            "student_id": session["student_id"],
            "tutor_id": session["tutor_id"],
            "overall_rating": overall_rating,
            "is_first_session": is_first_session,
            "subject_knowledge_rating": category_ratings["subject_knowledge"],
            "communication_rating": category_ratings["communication"],
            "patience_rating": category_ratings["patience"],
            "engagement_rating": category_ratings["engagement"],
            "helpfulness_rating": category_ratings["helpfulness"],
            "free_text_feedback": free_text,
            "submitted_at": submitted_at.isoformat(),
            "created_at": datetime.now().isoformat(),
        }

        # Add first session specific fields
        if is_first_session:
            would_recommend = overall_rating >= 4
            improvement_areas = []

            if not would_recommend:
                # Select improvement areas based on session issues
                if late_start > 5:
                    improvement_areas.append("late")
                if not objectives_met:
                    improvement_areas.extend(["unprepared", "unclear"])
                if technical_issues:
                    improvement_areas.append("technical_issues")
                if category_ratings["patience"] < 3:
                    improvement_areas.append("not_patient")

                # Ensure at least one improvement area
                if not improvement_areas:
                    improvement_areas.append(random.choice(self.IMPROVEMENT_AREAS))

            feedback_data["would_recommend"] = would_recommend
            feedback_data["improvement_areas"] = improvement_areas

        return feedback_data

    def generate_feedback_for_sessions(
        self,
        sessions: List[Dict],
        tutors: Dict[str, Dict],
        feedback_rate: float = 0.85
    ) -> List[Dict]:
        """
        Generate feedback for multiple sessions.

        Args:
            sessions: List of session dictionaries
            tutors: Dict mapping tutor_id to tutor profile
            feedback_rate: Percentage of sessions that receive feedback (default: 85%)

        Returns:
            List of feedback dictionaries
        """
        feedbacks = []

        for session in sessions:
            # Skip no-shows
            if session["no_show"]:
                continue

            # Only generate feedback based on feedback_rate
            if random.random() > feedback_rate:
                continue

            tutor = tutors.get(session["tutor_id"])
            if not tutor:
                continue

            feedback = self.generate_feedback(session, tutor)
            if feedback:
                feedbacks.append(feedback)

        return feedbacks

    def _calculate_quality_score(
        self,
        archetype: BehavioralArchetype,
        engagement_score: float,
        objectives_met: bool,
        late_start: int,
        technical_issues: bool,
        is_first_session: bool
    ) -> float:
        """
        Calculate overall session quality score (0-1).

        This is used as a base for generating ratings.
        """
        # Start with engagement score
        quality = engagement_score

        # Adjust for objectives met
        if not objectives_met:
            quality -= 0.15

        # Penalize late starts
        if late_start > 10:
            quality -= 0.20
        elif late_start > 5:
            quality -= 0.10

        # Penalize technical issues
        if technical_issues:
            quality -= 0.15

        # First sessions for new tutors tend to be rated lower
        if is_first_session and archetype == BehavioralArchetype.NEW_TUTOR:
            quality -= 0.10

        # Ensure quality stays in valid range
        quality = max(0.0, min(1.0, quality))

        return quality

    def _generate_overall_rating(self, quality_score: float) -> int:
        """
        Generate overall rating (1-5) from quality score.

        Distribution:
        - 0.0-0.4: Mostly 1-2 stars (poor)
        - 0.4-0.6: Mostly 2-3 stars (mediocre)
        - 0.6-0.8: Mostly 3-4 stars (good)
        - 0.8-1.0: Mostly 4-5 stars (excellent)
        """
        if quality_score < 0.4:
            # Poor quality
            return random.choices([1, 2, 3], weights=[0.4, 0.5, 0.1], k=1)[0]
        elif quality_score < 0.6:
            # Mediocre
            return random.choices([2, 3, 4], weights=[0.2, 0.6, 0.2], k=1)[0]
        elif quality_score < 0.8:
            # Good
            return random.choices([3, 4, 5], weights=[0.1, 0.6, 0.3], k=1)[0]
        else:
            # Excellent
            return random.choices([4, 5], weights=[0.3, 0.7], k=1)[0]

    def _generate_category_ratings(
        self,
        overall_rating: int,
        quality_score: float,
        archetype: BehavioralArchetype,
        technical_issues: bool
    ) -> Dict[str, int]:
        """
        Generate category-specific ratings (1-5).

        Categories: subject_knowledge, communication, patience, engagement, helpfulness
        Ratings cluster around overall rating with some variance.
        """
        ratings = {}

        categories = [
            "subject_knowledge",
            "communication",
            "patience",
            "engagement",
            "helpfulness"
        ]

        for category in categories:
            # Base rating on overall rating with small variance
            base = overall_rating

            # Subject knowledge tends to be higher for established tutors
            if category == "subject_knowledge" and archetype == BehavioralArchetype.HIGH_PERFORMER:
                base = min(5, base + 1)

            # Engagement correlates directly with quality score
            if category == "engagement":
                if quality_score > 0.85:
                    base = min(5, base + 1)
                elif quality_score < 0.5:
                    base = max(1, base - 1)

            # Patience might be rated lower for churners/at-risk
            if category == "patience" and archetype in [BehavioralArchetype.CHURNER, BehavioralArchetype.AT_RISK]:
                base = max(1, base - 1)

            # Add small random variance (+/- 1, staying in 1-5 range)
            variance = random.choice([-1, 0, 0, 1])  # Bias toward 0 (no change)
            rating = max(1, min(5, base + variance))

            ratings[category] = rating

        return ratings

    def _generate_text_feedback(
        self,
        overall_rating: int,
        is_first_session: bool,
        late_start: int,
        technical_issues: bool
    ) -> str:
        """
        Generate free-text feedback based on rating and session characteristics.
        """
        # 30% chance of no text feedback (student skips)
        if random.random() < 0.30:
            return ""

        # Select feedback template based on rating
        if overall_rating >= 4:
            # Positive feedback
            if is_first_session:
                templates = self.POSITIVE_FEEDBACK + self.FIRST_SESSION_POSITIVE
            else:
                templates = self.POSITIVE_FEEDBACK
        elif overall_rating == 3:
            # Neutral feedback
            templates = self.NEUTRAL_FEEDBACK
        else:
            # Negative feedback
            if is_first_session:
                templates = self.NEGATIVE_FEEDBACK + self.FIRST_SESSION_NEGATIVE
            else:
                templates = self.NEGATIVE_FEEDBACK

        feedback = random.choice(templates)

        # Add specific mentions for late starts or technical issues
        if late_start > 10:
            feedback += " Session started quite late."
        elif late_start > 5:
            feedback += " Session started a bit late."

        if technical_issues:
            feedback += " Had some technical difficulties."

        return feedback

    def get_feedback_stats(self, feedbacks: List[Dict]) -> Dict:
        """
        Calculate feedback statistics.

        Args:
            feedbacks: List of generated feedback

        Returns:
            Dict with feedback statistics
        """
        if not feedbacks:
            return {}

        total = len(feedbacks)

        # Overall rating distribution
        rating_counts = {i: 0 for i in range(1, 6)}
        for feedback in feedbacks:
            rating_counts[feedback["overall_rating"]] += 1

        avg_overall = np.mean([f["overall_rating"] for f in feedbacks])

        # First session statistics
        first_session_feedbacks = [f for f in feedbacks if f["is_first_session"]]
        first_session_count = len(first_session_feedbacks)

        first_session_avg = 0
        would_recommend_rate = 0
        if first_session_count > 0:
            first_session_avg = np.mean([f["overall_rating"] for f in first_session_feedbacks])
            would_recommend_count = sum(1 for f in first_session_feedbacks if f.get("would_recommend", True))
            would_recommend_rate = round(would_recommend_count / first_session_count * 100, 2)

        # Poor ratings (<3)
        poor_ratings = sum(1 for f in feedbacks if f["overall_rating"] < 3)

        stats = {
            "total_feedbacks": total,
            "avg_overall_rating": round(avg_overall, 2),
            "rating_distribution": rating_counts,
            "poor_rating_count": poor_ratings,
            "poor_rating_rate": round(poor_ratings / total * 100, 2),
            "first_session_count": first_session_count,
            "first_session_avg_rating": round(first_session_avg, 2) if first_session_count > 0 else 0,
            "would_recommend_rate": would_recommend_rate,
            "text_feedback_provided": sum(1 for f in feedbacks if f["free_text_feedback"]),
            "text_feedback_rate": round(sum(1 for f in feedbacks if f["free_text_feedback"]) / total * 100, 2),
        }

        return stats
