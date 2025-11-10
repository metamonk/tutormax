"""
Celery worker task for continuous synthetic data generation.

This module implements a Celery task that generates synthetic tutoring session data
using the existing TutorGenerator and SessionGenerator from src/data_generation/.
Data is stored in PostgreSQL via synchronous SQLAlchemy sessions.

Tasks:
    - generate_synthetic_data: Main task for generating synthetic data batches
    - generate_data_continuous: Scheduled task for continuous generation
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import uuid4

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session
from celery import Task
from celery.exceptions import SoftTimeLimitExceeded

from src.workers.celery_app import celery_app
from src.data_generation.tutor_generator import TutorGenerator, BehavioralArchetype
from src.data_generation.session_generator import SessionGenerator
from src.database.models import Tutor, Student, Session as SessionModel
from src.api.config import settings


# Configure logging
logger = logging.getLogger(__name__)


# Synchronous database engine for Celery workers
# Celery runs in a synchronous context, so we need psycopg2 instead of asyncpg
SYNC_DATABASE_URL = (
    f"postgresql+psycopg2://{settings.postgres_user}:{settings.postgres_password}"
    f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
)

sync_engine = create_engine(
    SYNC_DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=False,
)

# Create session factory
SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
)


def get_db() -> Session:
    """Get a synchronous database session for Celery workers."""
    return SyncSessionLocal()


class DataGeneratorTask(Task):
    """
    Base task class for data generation with custom error handling.

    Provides:
        - Automatic retry on transient failures
        - Logging for monitoring
        - Error handling for database issues
    """

    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 60}
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes max
    retry_jitter = True


@celery_app.task(
    bind=True,
    base=DataGeneratorTask,
    name="data_generator.generate_synthetic_data",
    queue="data_generation",
    soft_time_limit=1800,  # 30 minutes
    time_limit=2400,  # 40 minutes hard limit
)
def generate_synthetic_data(
    self,
    num_tutors: Optional[int] = None,
    num_sessions: Optional[int] = None,
    target_date: Optional[str] = None,
    seed: Optional[int] = None,
) -> Dict:
    """
    Generate synthetic tutors and sessions.

    This task can be called both as a scheduled task and manually.
    It generates synthetic data in configurable batches and stores them in PostgreSQL.

    Args:
        num_tutors: Number of tutors to generate (default: 10)
        num_sessions: Target number of sessions to generate (default: 100)
        target_date: ISO format date for session generation (default: today)
        seed: Random seed for reproducibility (default: None)

    Returns:
        Dict with generation statistics:
            - tutors_created: Number of new tutors created
            - sessions_created: Number of sessions created
            - students_created: Number of new students created
            - duration_seconds: Time taken
            - errors: List of any errors encountered

    Example:
        # Call manually
        result = generate_synthetic_data.delay(num_tutors=50, num_sessions=500)

        # Call with specific date
        result = generate_synthetic_data.delay(
            num_tutors=20,
            num_sessions=200,
            target_date="2024-01-15"
        )
    """
    start_time = datetime.utcnow()

    # Set defaults
    num_tutors = num_tutors or 10
    num_sessions = num_sessions or 100

    # Parse target date
    if target_date:
        try:
            session_date = datetime.fromisoformat(target_date)
        except ValueError:
            logger.error(f"Invalid date format: {target_date}")
            session_date = datetime.now()
    else:
        session_date = datetime.now()

    logger.info(
        f"Starting data generation: {num_tutors} tutors, "
        f"{num_sessions} sessions, date={session_date.date()}"
    )

    stats = {
        "tutors_created": 0,
        "sessions_created": 0,
        "students_created": 0,
        "tutors_existing": 0,
        "duration_seconds": 0,
        "errors": [],
    }

    db = None

    try:
        # Initialize generators
        tutor_gen = TutorGenerator(seed=seed)
        session_gen = SessionGenerator(seed=seed)

        # Get database session
        db = get_db()

        # Check for existing tutors
        existing_tutors_result = db.execute(select(Tutor))
        existing_tutors = existing_tutors_result.scalars().all()

        tutors_to_use = []

        # Generate new tutors if needed
        if len(existing_tutors) < num_tutors:
            new_tutor_count = num_tutors - len(existing_tutors)
            logger.info(f"Generating {new_tutor_count} new tutors")

            for _ in range(new_tutor_count):
                tutor_data = tutor_gen.generate_tutor()

                # Create Tutor ORM object
                tutor = Tutor(
                    tutor_id=tutor_data["tutor_id"],
                    name=tutor_data["name"],
                    email=tutor_data["email"],
                    onboarding_date=datetime.fromisoformat(tutor_data["onboarding_date"]),
                    status=tutor_data.get("status", "active"),
                    subjects=tutor_data["subjects"],
                    education_level=tutor_data.get("education_level"),
                    location=tutor_data.get("location"),
                    baseline_sessions_per_week=tutor_data["baseline_sessions_per_week"],
                    behavioral_archetype=tutor_data["behavioral_archetype"],
                )

                db.add(tutor)
                tutors_to_use.append(tutor_data)
                stats["tutors_created"] += 1

            # Commit tutors
            db.commit()
            logger.info(f"Created {stats['tutors_created']} new tutors")

        # Use existing tutors
        tutors_to_use.extend([
            {
                "tutor_id": t.tutor_id,
                "name": t.name,
                "email": t.email,
                "subjects": t.subjects,
                "behavioral_archetype": t.behavioral_archetype.value if t.behavioral_archetype else "steady",
                "baseline_sessions_per_week": t.baseline_sessions_per_week or 15.0,
            }
            for t in existing_tutors
        ])

        stats["tutors_existing"] = len(existing_tutors)

        logger.info(f"Using {len(tutors_to_use)} tutors for session generation")

        # Generate sessions for the day
        logger.info(f"Generating {num_sessions} sessions")
        sessions_data = session_gen.generate_sessions_for_day(
            tutors=tutors_to_use,
            target_count=num_sessions,
            date=session_date
        )

        # Track created students
        created_students = set()

        # Store sessions in database
        for session_data in sessions_data:
            try:
                # Check if student exists, create if not
                student_id = session_data["student_id"]

                existing_student = db.execute(
                    select(Student).where(Student.student_id == student_id)
                ).scalar_one_or_none()

                if not existing_student and student_id not in created_students:
                    # Generate student data
                    student = Student(
                        student_id=student_id,
                        name=f"Student {student_id.split('_')[1]}",
                        age=None,
                        grade_level=None,
                        subjects_interested=[],
                    )
                    db.add(student)
                    created_students.add(student_id)
                    stats["students_created"] += 1

                # Create session
                session = SessionModel(
                    session_id=session_data["session_id"],
                    tutor_id=session_data["tutor_id"],
                    student_id=session_data["student_id"],
                    session_number=session_data["session_number"],
                    scheduled_start=datetime.fromisoformat(session_data["scheduled_start"]),
                    actual_start=datetime.fromisoformat(session_data["actual_start"]) if session_data["actual_start"] else None,
                    duration_minutes=session_data["duration_minutes"],
                    subject=session_data["subject"],
                    session_type=session_data["session_type"],
                    tutor_initiated_reschedule=session_data["tutor_initiated_reschedule"],
                    no_show=session_data["no_show"],
                    late_start_minutes=session_data["late_start_minutes"],
                    engagement_score=session_data["engagement_score"],
                    learning_objectives_met=session_data["learning_objectives_met"],
                    technical_issues=session_data["technical_issues"],
                )

                db.add(session)
                stats["sessions_created"] += 1

            except Exception as e:
                error_msg = f"Error creating session {session_data['session_id']}: {str(e)}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
                continue

        # Commit all sessions
        db.commit()

        logger.info(
            f"Data generation complete: {stats['tutors_created']} tutors, "
            f"{stats['sessions_created']} sessions, "
            f"{stats['students_created']} students created"
        )

    except SoftTimeLimitExceeded:
        error_msg = "Task soft time limit exceeded"
        logger.error(error_msg)
        stats["errors"].append(error_msg)
        if db:
            db.rollback()
        raise

    except Exception as e:
        error_msg = f"Error in data generation: {str(e)}"
        logger.error(error_msg, exc_info=True)
        stats["errors"].append(error_msg)
        if db:
            db.rollback()
        raise

    finally:
        if db:
            db.close()

    # Calculate duration
    end_time = datetime.utcnow()
    stats["duration_seconds"] = (end_time - start_time).total_seconds()

    return stats


@celery_app.task(
    bind=True,
    base=DataGeneratorTask,
    name="data_generator.generate_data_continuous",
    queue="data_generation",
)
def generate_data_continuous(self, batch_size: int = 100) -> Dict:
    """
    Continuous data generation task for scheduled execution.

    This task is designed to be called periodically by Celery Beat
    to maintain a steady stream of synthetic data generation.

    Args:
        batch_size: Number of sessions to generate per execution (default: 100)

    Returns:
        Dict with generation statistics from generate_synthetic_data

    Example:
        # Add to Celery Beat schedule in celery_app.py:
        'generate-data-hourly': {
            'task': 'data_generator.generate_data_continuous',
            'schedule': crontab(minute=0),  # Every hour
            'kwargs': {'batch_size': 125},  # ~3000 per day
        }
    """
    logger.info(f"Starting continuous data generation (batch_size={batch_size})")

    # Call the main generation task
    # Generate a few tutors per batch to maintain diversity
    num_tutors = max(5, batch_size // 20)  # ~5% tutors to sessions ratio

    return generate_synthetic_data(
        num_tutors=num_tutors,
        num_sessions=batch_size,
        target_date=None,  # Use current date
        seed=None,  # Random seed
    )


@celery_app.task(
    bind=True,
    name="data_generator.cleanup_old_data",
    queue="data_generation",
)
def cleanup_old_data(self, days_to_keep: int = 90) -> Dict:
    """
    Clean up old synthetic data to prevent database bloat.

    This task removes sessions and orphaned students older than the specified
    retention period. Tutors are kept for historical analysis.

    Args:
        days_to_keep: Number of days of data to retain (default: 90)

    Returns:
        Dict with cleanup statistics:
            - sessions_deleted: Number of sessions removed
            - students_deleted: Number of students removed
            - cutoff_date: Date before which data was deleted

    Example:
        # Add to Celery Beat schedule:
        'cleanup-old-data-weekly': {
            'task': 'data_generator.cleanup_old_data',
            'schedule': crontab(day_of_week=0, hour=3, minute=0),  # Sunday 3am
            'kwargs': {'days_to_keep': 90},
        }
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

    logger.info(f"Starting data cleanup: removing data before {cutoff_date.date()}")

    stats = {
        "sessions_deleted": 0,
        "students_deleted": 0,
        "cutoff_date": cutoff_date.isoformat(),
    }

    db = None

    try:
        db = get_db()

        # Delete old sessions
        old_sessions = db.execute(
            select(SessionModel).where(SessionModel.scheduled_start < cutoff_date)
        ).scalars().all()

        for session in old_sessions:
            db.delete(session)
            stats["sessions_deleted"] += 1

        db.commit()

        # Find and delete orphaned students (students with no sessions)
        all_students = db.execute(select(Student)).scalars().all()

        for student in all_students:
            sessions_count = db.execute(
                select(SessionModel).where(SessionModel.student_id == student.student_id)
            ).scalars().first()

            if not sessions_count:
                db.delete(student)
                stats["students_deleted"] += 1

        db.commit()

        logger.info(
            f"Cleanup complete: {stats['sessions_deleted']} sessions, "
            f"{stats['students_deleted']} students deleted"
        )

    except Exception as e:
        error_msg = f"Error in data cleanup: {str(e)}"
        logger.error(error_msg, exc_info=True)
        if db:
            db.rollback()
        raise

    finally:
        if db:
            db.close()

    return stats
