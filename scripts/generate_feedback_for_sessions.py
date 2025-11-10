"""
Generate student feedback for existing sessions.

This script creates feedback for sessions that don't have feedback yet.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import logging

from src.database.models import Session, Tutor, StudentFeedback
from src.data_generation.feedback_generator import FeedbackGenerator
from src.api.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = f"postgresql+psycopg2://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def main():
    """Generate feedback for sessions without feedback."""

    print("=" * 70)
    print("GENERATING STUDENT FEEDBACK FOR SESSIONS")
    print("=" * 70)

    db = SessionLocal()

    try:
        # Get all sessions without feedback
        sessions = db.query(Session).all()
        tutors_dict = {t.tutor_id: t for t in db.query(Tutor).all()}

        # Get existing feedback session IDs
        existing_feedback = {f.session_id for f in db.query(StudentFeedback.session_id).all()}

        sessions_without_feedback = [
            s for s in sessions if s.session_id not in existing_feedback
        ]

        print(f"\nFound {len(sessions)} total sessions")
        print(f"Existing feedback: {len(existing_feedback)}")
        print(f"Sessions needing feedback: {len(sessions_without_feedback)}")

        if not sessions_without_feedback:
            print("\n✓ All sessions already have feedback!")
            return

        # Initialize feedback generator
        feedback_gen = FeedbackGenerator(seed=42)

        # Generate feedback for each session
        feedback_created = 0

        for session in sessions_without_feedback:
            # Get tutor info
            tutor = tutors_dict.get(session.tutor_id)
            if not tutor:
                logger.warning(f"Tutor {session.tutor_id} not found for session {session.session_id}")
                continue

            # Convert session to dict for generator
            session_dict = {
                "session_id": session.session_id,
                "tutor_id": session.tutor_id,
                "student_id": session.student_id,
                "is_first_session": session.session_number == 1,
                "engagement_score": session.engagement_score or 0.7,
                "late_start_minutes": session.late_start_minutes or 0,
                "learning_objectives_met": session.learning_objectives_met if session.learning_objectives_met is not None else True,
                "technical_issues": session.technical_issues if session.technical_issues is not None else False,
                "no_show": session.no_show if session.no_show is not None else False,
            }

            # Convert tutor to dict
            tutor_dict = {
                "tutor_id": tutor.tutor_id,
                "name": tutor.name,
                "behavioral_archetype": tutor.behavioral_archetype,
            }

            # Generate feedback
            feedback_data = feedback_gen.generate_feedback(
                session=session_dict,
                tutor=tutor_dict,
                submitted_at=session.scheduled_start + timedelta(hours=1)
            )

            if feedback_data is None:
                # No-show session, skip
                continue

            # Create StudentFeedback record
            feedback = StudentFeedback(
                feedback_id=feedback_data["feedback_id"],
                session_id=session.session_id,
                student_id=session.student_id,
                tutor_id=session.tutor_id,
                overall_rating=feedback_data["overall_rating"],
                subject_knowledge_rating=feedback_data["subject_knowledge_rating"],
                communication_rating=feedback_data["communication_rating"],
                patience_rating=feedback_data["patience_rating"],
                engagement_rating=feedback_data["engagement_rating"],
                helpfulness_rating=feedback_data["helpfulness_rating"],
                would_recommend=feedback_data.get("would_recommend", feedback_data["overall_rating"] >= 4),
                is_first_session=feedback_data["is_first_session"],
                improvement_areas=feedback_data.get("improvement_areas", []),
                free_text_feedback=feedback_data.get("free_text_feedback", ""),
                submitted_at=datetime.fromisoformat(feedback_data["submitted_at"]) if isinstance(feedback_data["submitted_at"], str) else feedback_data["submitted_at"]
            )

            db.add(feedback)
            feedback_created += 1

            # Commit in batches of 50
            if feedback_created % 50 == 0:
                db.commit()
                print(f"  Created {feedback_created} feedback records...")

        # Final commit
        db.commit()

        print(f"\n✓ Successfully created {feedback_created} feedback records!")

        # Summary statistics
        first_session_feedback = db.query(StudentFeedback).filter(
            StudentFeedback.is_first_session == True
        ).all()

        if first_session_feedback:
            poor_first_sessions = sum(1 for f in first_session_feedback if f.overall_rating < 3)
            poor_rate = poor_first_sessions / len(first_session_feedback)

            print(f"\nFirst session feedback summary:")
            print(f"  Total first session feedback: {len(first_session_feedback)}")
            print(f"  Poor first sessions (rating < 3): {poor_first_sessions} ({poor_rate:.1%})")

    except Exception as e:
        logger.error(f"Error generating feedback: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()

    finally:
        db.close()


if __name__ == "__main__":
    main()
