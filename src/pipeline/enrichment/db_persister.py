"""
Database persistence layer for enriched data.

Handles upsert operations, foreign key validation, and batch processing.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Tutor, Student, Session, StudentFeedback
from src.database.connection import get_session

logger = logging.getLogger(__name__)


class DatabasePersister:
    """
    Handles persistence of enriched data to PostgreSQL.

    Features:
    - Upsert operations (insert or update)
    - Foreign key validation
    - Batch processing
    - Transaction support
    - Error handling with rollback
    """

    def __init__(self):
        """Initialize database persister."""
        self.stats = {
            "total_persisted": 0,
            "total_failed": 0,
            "by_type": {
                "tutor": {"inserted": 0, "updated": 0, "failed": 0},
                "student": {"inserted": 0, "updated": 0, "failed": 0},
                "session": {"inserted": 0, "updated": 0, "failed": 0},
                "feedback": {"inserted": 0, "updated": 0, "failed": 0},
            },
        }

    async def persist_tutor(
        self, data: Dict[str, Any], session: AsyncSession
    ) -> bool:
        """
        Persist tutor data to database.

        Args:
            data: Enriched tutor data
            session: Database session

        Returns:
            True if successful, False otherwise
        """
        try:
            # Build upsert statement
            stmt = insert(Tutor).values(**data)
            stmt = stmt.on_conflict_do_update(
                index_elements=["tutor_id"],
                set_={
                    "name": stmt.excluded.name,
                    "email": stmt.excluded.email,
                    "onboarding_date": stmt.excluded.onboarding_date,
                    "status": stmt.excluded.status,
                    "subjects": stmt.excluded.subjects,
                    "education_level": stmt.excluded.education_level,
                    "location": stmt.excluded.location,
                    "baseline_sessions_per_week": stmt.excluded.baseline_sessions_per_week,
                    "behavioral_archetype": stmt.excluded.behavioral_archetype,
                    "updated_at": datetime.utcnow(),
                },
            )

            await session.execute(stmt)
            self.stats["total_persisted"] += 1

            logger.debug(f"Persisted tutor: {data.get('tutor_id')}")
            return True

        except Exception as e:
            self.stats["by_type"]["tutor"]["failed"] += 1
            self.stats["total_failed"] += 1
            logger.error(f"Failed to persist tutor: {e}", exc_info=True)
            return False

    async def persist_student(
        self, data: Dict[str, Any], session: AsyncSession
    ) -> bool:
        """
        Persist student data to database.

        Args:
            data: Student data
            session: Database session

        Returns:
            True if successful, False otherwise
        """
        try:
            # Build upsert statement
            stmt = insert(Student).values(**data)
            stmt = stmt.on_conflict_do_update(
                index_elements=["student_id"],
                set_={
                    "name": stmt.excluded.name,
                    "age": stmt.excluded.age,
                    "grade_level": stmt.excluded.grade_level,
                    "subjects_interested": stmt.excluded.subjects_interested,
                    "updated_at": datetime.utcnow(),
                },
            )

            await session.execute(stmt)
            self.stats["total_persisted"] += 1

            logger.debug(f"Persisted student: {data.get('student_id')}")
            return True

        except Exception as e:
            self.stats["by_type"]["student"]["failed"] += 1
            self.stats["total_failed"] += 1
            logger.error(f"Failed to persist student: {e}", exc_info=True)
            return False

    async def persist_session(
        self, data: Dict[str, Any], session: AsyncSession
    ) -> bool:
        """
        Persist session data to database.

        Args:
            data: Enriched session data
            session: Database session

        Returns:
            True if successful, False otherwise
        """
        try:
            # Verify foreign keys exist
            tutor_id = data.get("tutor_id")
            student_id = data.get("student_id")

            if not await self._verify_tutor_exists(tutor_id, session):
                logger.warning(f"Tutor {tutor_id} not found, skipping session")
                self.stats["by_type"]["session"]["failed"] += 1
                self.stats["total_failed"] += 1
                return False

            if not await self._verify_student_exists(student_id, session):
                logger.warning(f"Student {student_id} not found, skipping session")
                self.stats["by_type"]["session"]["failed"] += 1
                self.stats["total_failed"] += 1
                return False

            # Build upsert statement
            stmt = insert(Session).values(**data)
            stmt = stmt.on_conflict_do_update(
                index_elements=["session_id"],
                set_={
                    "tutor_id": stmt.excluded.tutor_id,
                    "student_id": stmt.excluded.student_id,
                    "session_number": stmt.excluded.session_number,
                    "scheduled_start": stmt.excluded.scheduled_start,
                    "actual_start": stmt.excluded.actual_start,
                    "duration_minutes": stmt.excluded.duration_minutes,
                    "subject": stmt.excluded.subject,
                    "session_type": stmt.excluded.session_type,
                    "tutor_initiated_reschedule": stmt.excluded.tutor_initiated_reschedule,
                    "no_show": stmt.excluded.no_show,
                    "late_start_minutes": stmt.excluded.late_start_minutes,
                    "engagement_score": stmt.excluded.engagement_score,
                    "learning_objectives_met": stmt.excluded.learning_objectives_met,
                    "technical_issues": stmt.excluded.technical_issues,
                    "updated_at": datetime.utcnow(),
                },
            )

            await session.execute(stmt)
            self.stats["total_persisted"] += 1

            logger.debug(f"Persisted session: {data.get('session_id')}")
            return True

        except Exception as e:
            self.stats["by_type"]["session"]["failed"] += 1
            self.stats["total_failed"] += 1
            logger.error(f"Failed to persist session: {e}", exc_info=True)
            return False

    async def persist_feedback(
        self, data: Dict[str, Any], session: AsyncSession
    ) -> bool:
        """
        Persist feedback data to database.

        Args:
            data: Enriched feedback data
            session: Database session

        Returns:
            True if successful, False otherwise
        """
        try:
            # Verify foreign keys exist
            tutor_id = data.get("tutor_id")
            student_id = data.get("student_id")
            session_id = data.get("session_id")

            if not await self._verify_tutor_exists(tutor_id, session):
                logger.warning(f"Tutor {tutor_id} not found, skipping feedback")
                self.stats["by_type"]["feedback"]["failed"] += 1
                self.stats["total_failed"] += 1
                return False

            if not await self._verify_student_exists(student_id, session):
                logger.warning(f"Student {student_id} not found, skipping feedback")
                self.stats["by_type"]["feedback"]["failed"] += 1
                self.stats["total_failed"] += 1
                return False

            if not await self._verify_session_exists(session_id, session):
                logger.warning(f"Session {session_id} not found, skipping feedback")
                self.stats["by_type"]["feedback"]["failed"] += 1
                self.stats["total_failed"] += 1
                return False

            # Build upsert statement
            stmt = insert(StudentFeedback).values(**data)
            stmt = stmt.on_conflict_do_update(
                index_elements=["feedback_id"],
                set_={
                    "session_id": stmt.excluded.session_id,
                    "student_id": stmt.excluded.student_id,
                    "tutor_id": stmt.excluded.tutor_id,
                    "overall_rating": stmt.excluded.overall_rating,
                    "is_first_session": stmt.excluded.is_first_session,
                    "subject_knowledge_rating": stmt.excluded.subject_knowledge_rating,
                    "communication_rating": stmt.excluded.communication_rating,
                    "patience_rating": stmt.excluded.patience_rating,
                    "engagement_rating": stmt.excluded.engagement_rating,
                    "helpfulness_rating": stmt.excluded.helpfulness_rating,
                    "would_recommend": stmt.excluded.would_recommend,
                    "improvement_areas": stmt.excluded.improvement_areas,
                    "free_text_feedback": stmt.excluded.free_text_feedback,
                    "submitted_at": stmt.excluded.submitted_at,
                },
            )

            await session.execute(stmt)
            self.stats["total_persisted"] += 1

            logger.debug(f"Persisted feedback: {data.get('feedback_id')}")
            return True

        except Exception as e:
            self.stats["by_type"]["feedback"]["failed"] += 1
            self.stats["total_failed"] += 1
            logger.error(f"Failed to persist feedback: {e}", exc_info=True)
            return False

    async def persist_batch(
        self, items: List[Dict[str, Any]], data_type: str
    ) -> Dict[str, int]:
        """
        Persist a batch of items in a single transaction.

        Args:
            items: List of enriched data items
            data_type: Type of data (tutor, session, feedback)

        Returns:
            Dict with success/failed counts
        """
        results = {"success": 0, "failed": 0}

        async with get_session() as session:
            try:
                for item in items:
                    if data_type == "tutor":
                        success = await self.persist_tutor(item, session)
                    elif data_type == "session":
                        success = await self.persist_session(item, session)
                    elif data_type == "feedback":
                        success = await self.persist_feedback(item, session)
                    else:
                        logger.error(f"Unknown data type: {data_type}")
                        success = False

                    if success:
                        results["success"] += 1
                    else:
                        results["failed"] += 1

                # Commit transaction
                await session.commit()
                logger.info(
                    f"Batch persisted: {results['success']} success, {results['failed']} failed"
                )

            except Exception as e:
                await session.rollback()
                logger.error(f"Batch persistence failed: {e}", exc_info=True)
                results["failed"] = len(items)
                results["success"] = 0

        return results

    async def _verify_tutor_exists(
        self, tutor_id: str, session: AsyncSession
    ) -> bool:
        """Check if tutor exists in database."""
        if not tutor_id:
            return False

        result = await session.execute(
            select(Tutor).where(Tutor.tutor_id == tutor_id)
        )
        return result.scalar_one_or_none() is not None

    async def _verify_student_exists(
        self, student_id: str, session: AsyncSession
    ) -> bool:
        """Check if student exists in database."""
        if not student_id:
            return False

        result = await session.execute(
            select(Student).where(Student.student_id == student_id)
        )
        return result.scalar_one_or_none() is not None

    async def _verify_session_exists(
        self, session_id: str, db_session: AsyncSession
    ) -> bool:
        """Check if session exists in database."""
        if not session_id:
            return False

        result = await db_session.execute(
            select(Session).where(Session.session_id == session_id)
        )
        return result.scalar_one_or_none() is not None

    def get_stats(self) -> Dict[str, Any]:
        """Get persistence statistics."""
        return self.stats.copy()

    def reset_stats(self) -> None:
        """Reset persistence statistics."""
        self.stats = {
            "total_persisted": 0,
            "total_failed": 0,
            "by_type": {
                "tutor": {"inserted": 0, "updated": 0, "failed": 0},
                "student": {"inserted": 0, "updated": 0, "failed": 0},
                "session": {"inserted": 0, "updated": 0, "failed": 0},
                "feedback": {"inserted": 0, "updated": 0, "failed": 0},
            },
        }
