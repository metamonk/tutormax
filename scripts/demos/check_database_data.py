#!/usr/bin/env python3
"""
Check what data exists in the database.
"""

import asyncio
from sqlalchemy import select, func
from src.database.connection import get_session
from src.database.models import (
    Tutor,
    Student,
    Session,
    StudentFeedback,
    TutorPerformanceMetric,
    ChurnPrediction,
    TutorEvent,
)


async def main():
    """Check database data counts."""
    print("=" * 60)
    print("Database Data Check")
    print("=" * 60)

    async with get_session() as db:
        # Count records in each table
        tutors_count = await db.scalar(select(func.count()).select_from(Tutor))
        students_count = await db.scalar(select(func.count()).select_from(Student))
        sessions_count = await db.scalar(select(func.count()).select_from(Session))
        feedback_count = await db.scalar(select(func.count()).select_from(StudentFeedback))
        metrics_count = await db.scalar(select(func.count()).select_from(TutorPerformanceMetric))
        predictions_count = await db.scalar(select(func.count()).select_from(ChurnPrediction))
        events_count = await db.scalar(select(func.count()).select_from(TutorEvent))

        print(f"\nTable Record Counts:")
        print(f"  Tutors:               {tutors_count:,}")
        print(f"  Students:             {students_count:,}")
        print(f"  Sessions:             {sessions_count:,}")
        print(f"  Student Feedback:     {feedback_count:,}")
        print(f"  Performance Metrics:  {metrics_count:,}")
        print(f"  Churn Predictions:    {predictions_count:,}")
        print(f"  Tutor Events:         {events_count:,}")

        if tutors_count > 0:
            # Get sample tutors
            result = await db.execute(select(Tutor).limit(3))
            sample_tutors = result.scalars().all()

            print(f"\nSample Tutors:")
            for tutor in sample_tutors:
                print(f"  - {tutor.name} ({tutor.tutor_id})")
                print(f"    Status: {tutor.status}, Archetype: {tutor.behavioral_archetype}")
                print(f"    Subjects: {', '.join(tutor.subjects)}")

        if sessions_count > 0:
            # Check date range of sessions
            result = await db.execute(
                select(
                    func.min(Session.scheduled_start),
                    func.max(Session.scheduled_start)
                )
            )
            min_date, max_date = result.one()
            print(f"\nSession Date Range:")
            print(f"  Earliest: {min_date}")
            print(f"  Latest:   {max_date}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
