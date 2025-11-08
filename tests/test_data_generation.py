"""
Tests for synthetic data generation modules.

Validates data integrity, correlations, and adherence to PRD specifications.
"""

import pytest
from datetime import datetime, timedelta

from src.data_generation.tutor_generator import TutorGenerator, BehavioralArchetype
from src.data_generation.session_generator import SessionGenerator
from src.data_generation.feedback_generator import FeedbackGenerator


class TestTutorGenerator:
    """Tests for TutorGenerator"""

    def test_generate_single_tutor(self):
        """Test generating a single tutor profile"""
        generator = TutorGenerator(seed=42)
        tutor = generator.generate_tutor()

        # Verify required fields
        assert "tutor_id" in tutor
        assert "name" in tutor
        assert "email" in tutor
        assert "subjects" in tutor
        assert "behavioral_archetype" in tutor
        assert "baseline_sessions_per_week" in tutor

        # Verify data types
        assert isinstance(tutor["age"], int)
        assert 22 <= tutor["age"] <= 65
        assert isinstance(tutor["subjects"], list)
        assert len(tutor["subjects"]) >= 1
        assert 5 <= tutor["baseline_sessions_per_week"] <= 30

    def test_archetype_distribution(self):
        """Test that archetype distribution matches PRD specs"""
        generator = TutorGenerator(seed=42)
        tutors = generator.generate_tutors(count=1000)

        stats = generator.get_archetype_stats(tutors)

        # Check that all archetypes are represented
        expected_archetypes = [
            "high_performer", "at_risk", "new_tutor", "steady", "churner"
        ]
        for archetype in expected_archetypes:
            assert archetype in stats

        # Check approximate distribution (allow 5% variance)
        assert 25 <= stats["high_performer"]["percentage"] <= 35  # Target: 30%
        assert 15 <= stats["at_risk"]["percentage"] <= 25  # Target: 20%
        assert 20 <= stats["new_tutor"]["percentage"] <= 30  # Target: 25%
        assert 15 <= stats["steady"]["percentage"] <= 25  # Target: 20%
        assert 2 <= stats["churner"]["percentage"] <= 8  # Target: 5%

    def test_new_tutor_tenure(self):
        """Test that new tutors have tenure < 30 days"""
        generator = TutorGenerator(seed=42)
        tutor = generator.generate_tutor(
            archetype=BehavioralArchetype.NEW_TUTOR
        )

        assert tutor["tenure_days"] < 30

    def test_high_performer_sessions(self):
        """Test that high performers have above-average baseline sessions"""
        generator = TutorGenerator(seed=42)
        tutor = generator.generate_tutor(
            archetype=BehavioralArchetype.HIGH_PERFORMER
        )

        assert tutor["baseline_sessions_per_week"] >= 18

    def test_reproducibility(self):
        """Test that same seed produces same results"""
        gen1 = TutorGenerator(seed=42)
        gen2 = TutorGenerator(seed=42)

        tutor1 = gen1.generate_tutor()
        tutor2 = gen2.generate_tutor()

        # Same seed should produce identical tutors
        assert tutor1["name"] == tutor2["name"]
        assert tutor1["behavioral_archetype"] == tutor2["behavioral_archetype"]


class TestSessionGenerator:
    """Tests for SessionGenerator"""

    def test_generate_single_session(self):
        """Test generating a single session"""
        tutor_gen = TutorGenerator(seed=42)
        session_gen = SessionGenerator(seed=42)

        tutor = tutor_gen.generate_tutor()
        session = session_gen.generate_session(tutor)

        # Verify required fields
        assert "session_id" in session
        assert "tutor_id" in session
        assert "student_id" in session
        assert "session_number" in session
        assert "engagement_score" in session

        # Verify data types and ranges
        assert isinstance(session["session_number"], int)
        assert session["session_number"] >= 1
        assert 0.0 <= session["engagement_score"] <= 1.0
        assert session["duration_minutes"] in [0, 30, 45, 60, 90, 120]

    def test_first_session_tracking(self):
        """Test that first sessions are properly tracked"""
        tutor_gen = TutorGenerator(seed=42)
        session_gen = SessionGenerator(seed=42)

        tutor = tutor_gen.generate_tutor()

        # Generate multiple sessions for same tutor-student pair
        session1 = session_gen.generate_session(tutor, student_id="student_001")
        session2 = session_gen.generate_session(tutor, student_id="student_001")
        session3 = session_gen.generate_session(tutor, student_id="student_002")

        assert session1["session_number"] == 1
        assert session1["is_first_session"] is True
        assert session2["session_number"] == 2
        assert session2["is_first_session"] is False
        assert session3["session_number"] == 1  # Different student
        assert session3["is_first_session"] is True

    def test_high_performer_low_reschedule_rate(self):
        """Test that high performers have low reschedule rates"""
        tutor_gen = TutorGenerator(seed=42)
        session_gen = SessionGenerator(seed=42)

        tutor = tutor_gen.generate_tutor(
            archetype=BehavioralArchetype.HIGH_PERFORMER
        )

        # Generate many sessions
        sessions = [
            session_gen.generate_session(tutor)
            for _ in range(100)
        ]

        reschedule_rate = sum(
            1 for s in sessions if s["tutor_initiated_reschedule"]
        ) / len(sessions)

        # High performers should have <5% reschedule rate
        assert reschedule_rate < 0.05

    def test_churner_high_no_show_rate(self):
        """Test that churners have elevated no-show rates"""
        tutor_gen = TutorGenerator(seed=42)
        session_gen = SessionGenerator(seed=42)

        tutor = tutor_gen.generate_tutor(
            archetype=BehavioralArchetype.CHURNER
        )

        # Generate many sessions
        sessions = [
            session_gen.generate_session(tutor)
            for _ in range(100)
        ]

        no_show_rate = sum(
            1 for s in sessions if s["no_show"]
        ) / len(sessions)

        # Churners should have >10% no-show rate
        assert no_show_rate > 0.10

    def test_daily_session_generation(self):
        """Test generating 3000 sessions per day"""
        tutor_gen = TutorGenerator(seed=42)
        session_gen = SessionGenerator(seed=42)

        # Generate 300 tutors (typical active count)
        tutors = tutor_gen.generate_tutors(count=300)

        # Generate sessions for a day
        sessions = session_gen.generate_sessions_for_day(
            tutors=tutors,
            target_count=3000
        )

        # Should generate close to target (within 20% variance)
        assert 2400 <= len(sessions) <= 3600

        # Verify stats
        stats = session_gen.get_session_stats(sessions)
        assert stats["total_sessions"] > 0
        assert "avg_engagement_score" in stats


class TestFeedbackGenerator:
    """Tests for FeedbackGenerator"""

    def test_generate_single_feedback(self):
        """Test generating feedback for a session"""
        tutor_gen = TutorGenerator(seed=42)
        session_gen = SessionGenerator(seed=42)
        feedback_gen = FeedbackGenerator(seed=42)

        tutor = tutor_gen.generate_tutor()
        session = session_gen.generate_session(tutor)
        feedback = feedback_gen.generate_feedback(session, tutor)

        if feedback:  # May be None for no-shows
            # Verify required fields
            assert "feedback_id" in feedback
            assert "session_id" in feedback
            assert "overall_rating" in feedback
            assert "subject_knowledge_rating" in feedback

            # Verify ratings are in valid range (1-5)
            assert 1 <= feedback["overall_rating"] <= 5
            assert 1 <= feedback["subject_knowledge_rating"] <= 5
            assert 1 <= feedback["communication_rating"] <= 5

    def test_no_feedback_for_no_shows(self):
        """Test that no-show sessions don't get feedback"""
        tutor_gen = TutorGenerator(seed=42)
        session_gen = SessionGenerator(seed=42)
        feedback_gen = FeedbackGenerator(seed=42)

        tutor = tutor_gen.generate_tutor(
            archetype=BehavioralArchetype.CHURNER
        )

        # Generate sessions until we get a no-show
        for _ in range(100):
            session = session_gen.generate_session(tutor)
            if session["no_show"]:
                feedback = feedback_gen.generate_feedback(session, tutor)
                assert feedback is None
                break

    def test_first_session_feedback_fields(self):
        """Test that first sessions have additional feedback fields"""
        tutor_gen = TutorGenerator(seed=42)
        session_gen = SessionGenerator(seed=42)
        feedback_gen = FeedbackGenerator(seed=42)

        tutor = tutor_gen.generate_tutor()
        session = session_gen.generate_session(tutor, student_id="student_001")

        # Ensure it's a first session
        assert session["is_first_session"] is True

        feedback = feedback_gen.generate_feedback(session, tutor)

        if feedback:
            assert "would_recommend" in feedback
            assert "improvement_areas" in feedback
            assert isinstance(feedback["would_recommend"], bool)
            assert isinstance(feedback["improvement_areas"], list)

    def test_poor_rating_correlation(self):
        """Test that poor sessions get poor ratings"""
        tutor_gen = TutorGenerator(seed=42)
        session_gen = SessionGenerator(seed=42)
        feedback_gen = FeedbackGenerator(seed=42)

        # Create churner with poor sessions
        tutor = tutor_gen.generate_tutor(
            archetype=BehavioralArchetype.CHURNER
        )

        sessions = [
            session_gen.generate_session(tutor)
            for _ in range(50)
        ]

        feedbacks = feedback_gen.generate_feedback_for_sessions(
            sessions=sessions,
            tutors={tutor["tutor_id"]: tutor},
            feedback_rate=1.0  # 100% feedback rate for testing
        )

        if feedbacks:
            avg_rating = sum(f["overall_rating"] for f in feedbacks) / len(feedbacks)
            # Churner sessions should average below 4
            assert avg_rating < 4.0

    def test_feedback_stats(self):
        """Test feedback statistics calculation"""
        tutor_gen = TutorGenerator(seed=42)
        session_gen = SessionGenerator(seed=42)
        feedback_gen = FeedbackGenerator(seed=42)

        tutors = tutor_gen.generate_tutors(count=10)
        tutors_dict = {t["tutor_id"]: t for t in tutors}

        sessions = []
        for tutor in tutors:
            sessions.extend([
                session_gen.generate_session(tutor)
                for _ in range(10)
            ])

        feedbacks = feedback_gen.generate_feedback_for_sessions(
            sessions=sessions,
            tutors=tutors_dict,
            feedback_rate=0.85
        )

        stats = feedback_gen.get_feedback_stats(feedbacks)

        assert "total_feedbacks" in stats
        assert "avg_overall_rating" in stats
        assert "first_session_count" in stats
        assert stats["avg_overall_rating"] >= 1.0
        assert stats["avg_overall_rating"] <= 5.0


class TestDataIntegration:
    """Integration tests for complete data generation pipeline"""

    def test_end_to_end_generation(self):
        """Test complete data generation pipeline"""
        # Initialize generators
        tutor_gen = TutorGenerator(seed=42)
        session_gen = SessionGenerator(seed=42)
        feedback_gen = FeedbackGenerator(seed=42)

        # Generate tutors
        tutors = tutor_gen.generate_tutors(count=100)
        assert len(tutors) == 100

        # Generate sessions
        sessions = session_gen.generate_sessions_for_day(
            tutors=tutors,
            target_count=1000
        )
        assert len(sessions) > 0

        # Generate feedback
        tutors_dict = {t["tutor_id"]: t for t in tutors}
        feedbacks = feedback_gen.generate_feedback_for_sessions(
            sessions=sessions,
            tutors=tutors_dict
        )

        # Verify data consistency
        assert len(feedbacks) > 0
        assert all(
            f["session_id"] in [s["session_id"] for s in sessions]
            for f in feedbacks
        )

    def test_archetype_behavior_correlation(self):
        """Test that session behaviors correlate with tutor archetypes"""
        tutor_gen = TutorGenerator(seed=42)
        session_gen = SessionGenerator(seed=42)

        # High performer
        hp_tutor = tutor_gen.generate_tutor(
            archetype=BehavioralArchetype.HIGH_PERFORMER
        )
        hp_sessions = [
            session_gen.generate_session(hp_tutor) for _ in range(50)
        ]
        hp_avg_engagement = sum(
            s["engagement_score"] for s in hp_sessions
        ) / len(hp_sessions)

        # Churner
        churner_tutor = tutor_gen.generate_tutor(
            archetype=BehavioralArchetype.CHURNER
        )
        churner_sessions = [
            session_gen.generate_session(churner_tutor) for _ in range(50)
        ]
        churner_avg_engagement = sum(
            s["engagement_score"] for s in churner_sessions
        ) / len(churner_sessions)

        # High performers should have significantly higher engagement
        assert hp_avg_engagement > churner_avg_engagement + 0.2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
