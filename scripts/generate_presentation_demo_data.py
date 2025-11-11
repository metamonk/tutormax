#!/usr/bin/env python3
"""
Generate realistic demo data for TutorMax presentation.

Creates:
- Sarah Chen (At-Risk tutor with 72% churn risk)
- Mike Ross (New tutor with low first session success)
- Supporting cast of tutors for context
- Realistic sessions, feedback, and performance metrics
- Interventions and churn predictions
"""

import asyncio
import sys
import uuid
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from src.database.database import async_session_maker
from src.database.models import (
    Tutor, Session, StudentFeedback, Intervention, Student,
    TutorPerformanceMetric, ChurnPrediction, TutorStatus,
    InterventionStatus, InterventionType, PerformanceTier,
    RiskLevel, MetricWindow, BehavioralArchetype, SessionType
)


async def create_sarah_chen(session_db):
    """Create Sarah Chen - At-Risk tutor."""
    print("\n1️⃣  Creating Sarah Chen (At-Risk)...")

    sarah = Tutor(
        tutor_id="sarah_chen_001",
        name="Sarah Chen",
        email="sarah.chen@tutormax.com",
        onboarding_date=datetime.now() - timedelta(days=120),
        status=TutorStatus.ACTIVE,
        subjects=["Mathematics", "Physics"],
        education_level="Masters",
        location="San Francisco, CA",
        baseline_sessions_per_week=20.0,
        behavioral_archetype=BehavioralArchetype.AT_RISK
    )
    session_db.add(sarah)

    # Performance metrics (30-day window)
    metrics = TutorPerformanceMetric(
        metric_id=f"metric_sarah_{uuid.uuid4().hex[:8]}",
        tutor_id=sarah.tutor_id,
        calculation_date=datetime.now(),
        window=MetricWindow.THIRTY_DAY,
        sessions_completed=15,  # Down from 25
        avg_rating=4.1,  # Down from 4.5
        first_session_success_rate=0.75,
        reschedule_rate=0.25,  # High
        no_show_count=2,
        engagement_score=0.32,  # Low (down from 0.75)
        learning_objectives_met_pct=0.78,
        performance_tier=PerformanceTier.STRONG
    )
    session_db.add(metrics)

    # Churn prediction
    churn = ChurnPrediction(
        prediction_id=f"churn_sarah_{uuid.uuid4().hex[:8]}",
        tutor_id=sarah.tutor_id,
        prediction_date=datetime.now(),
        churn_score=72,  # 72% probability
        risk_level=RiskLevel.CRITICAL,
        window_1day_probability=0.45,
        window_7day_probability=0.58,
        window_30day_probability=0.72,
        window_90day_probability=0.68,
        contributing_factors={
            "declining_engagement": 0.9,
            "increased_reschedules": 0.8,
            "rating_drop": 0.7
        },
        model_version="v1.0"
    )
    session_db.add(churn)

    print("   ✓ Sarah Chen - Churn Risk: 72% (CRITICAL)")
    print("   - Average Rating: 4.1 (declining)")
    print("   - Engagement: 0.32 (low)")
    print("   - 15 sessions last 30 days (down from 25)")

    return sarah


async def create_mike_ross(session_db):
    """Create Mike Ross - New tutor."""
    print("\n2️⃣  Creating Mike Ross (New Tutor)...")

    mike = Tutor(
        tutor_id="mike_ross_001",
        name="Mike Ross",
        email="mike.ross@tutormax.com",
        onboarding_date=datetime.now() - timedelta(days=10),
        status=TutorStatus.ACTIVE,
        subjects=["Spanish", "English"],
        education_level="Bachelors",
        location="New York, NY",
        baseline_sessions_per_week=15.0,
        behavioral_archetype=BehavioralArchetype.NEW_TUTOR
    )
    session_db.add(mike)

    # Performance metrics (7-day window - he's new)
    metrics = TutorPerformanceMetric(
        metric_id=f"metric_mike_{uuid.uuid4().hex[:8]}",
        tutor_id=mike.tutor_id,
        calculation_date=datetime.now(),
        window=MetricWindow.SEVEN_DAY,
        sessions_completed=5,  # Only 5 total
        avg_rating=3.8,
        first_session_success_rate=0.40,  # Only 40% - 2 of 5 went well
        reschedule_rate=0.12,
        no_show_count=1,
        engagement_score=0.55,
        learning_objectives_met_pct=0.65,
        performance_tier=PerformanceTier.DEVELOPING
    )
    session_db.add(metrics)

    # Churn prediction (moderate risk for new tutor)
    churn = ChurnPrediction(
        prediction_id=f"churn_mike_{uuid.uuid4().hex[:8]}",
        tutor_id=mike.tutor_id,
        prediction_date=datetime.now(),
        churn_score=35,
        risk_level=RiskLevel.MEDIUM,
        window_1day_probability=0.15,
        window_7day_probability=0.22,
        window_30day_probability=0.35,
        window_90day_probability=0.45,
        contributing_factors={
            "new_tutor": 0.8,
            "low_first_session_success": 0.9,
            "below_average_rating": 0.6
        },
        model_version="v1.0"
    )
    session_db.add(churn)

    print("   ✓ Mike Ross - First Session Risk: HIGH")
    print("   - Average Rating: 3.8")
    print("   - First Session Success: 40%")
    print("   - Only 5 sessions completed (NEW)")

    return mike


async def create_high_performers(session_db):
    """Create high-performing tutors for context."""
    print("\n3️⃣  Creating High Performers...")

    tutors = []
    names = [
        ("Jessica Pearson", "jessica.pearson@tutormax.com", ["Computer Science", "Mathematics"]),
        ("Harvey Specter", "harvey.specter@tutormax.com", ["Chemistry", "Biology"]),
        ("Rachel Zane", "rachel.zane@tutormax.com", ["English", "History"])
    ]

    for idx, (name, email, subjects) in enumerate(names):
        tutor = Tutor(
            tutor_id=f"hp_{idx:03d}",
            name=name,
            email=email,
            onboarding_date=datetime.now() - timedelta(days=random.randint(180, 365)),
            status=TutorStatus.ACTIVE,
            subjects=subjects,
            education_level=random.choice(["Masters", "PhD"]),
            location=random.choice(["Boston, MA", "Seattle, WA", "Austin, TX"]),
            baseline_sessions_per_week=random.uniform(25, 35),
            behavioral_archetype=BehavioralArchetype.HIGH_PERFORMER
        )
        session_db.add(tutor)
        tutors.append(tutor)

        # Excellent metrics
        metrics = TutorPerformanceMetric(
            metric_id=f"metric_{tutor.tutor_id}_{uuid.uuid4().hex[:8]}",
            tutor_id=tutor.tutor_id,
            calculation_date=datetime.now(),
            window=MetricWindow.THIRTY_DAY,
            sessions_completed=random.randint(45, 60),
            avg_rating=random.uniform(4.7, 5.0),
            first_session_success_rate=random.uniform(0.88, 0.95),
            reschedule_rate=random.uniform(0.01, 0.03),
            no_show_count=random.randint(0, 1),
            engagement_score=random.uniform(0.85, 0.95),
            learning_objectives_met_pct=random.uniform(0.90, 0.98),
            performance_tier=PerformanceTier.EXEMPLARY
        )
        session_db.add(metrics)

        # Low churn risk
        churn = ChurnPrediction(
            prediction_id=f"churn_{tutor.tutor_id}_{uuid.uuid4().hex[:8]}",
            tutor_id=tutor.tutor_id,
            prediction_date=datetime.now(),
            churn_score=random.randint(3, 10),
            risk_level=RiskLevel.LOW,
            window_1day_probability=random.uniform(0.01, 0.05),
            window_7day_probability=random.uniform(0.02, 0.08),
            window_30day_probability=random.uniform(0.03, 0.10),
            window_90day_probability=random.uniform(0.05, 0.12),
            contributing_factors={"stable_performance": 0.9},
            model_version="v1.0"
        )
        session_db.add(churn)

        print(f"   ✓ {name} - Performance: EXEMPLARY")

    return tutors


async def create_students(session_db):
    """Create demo students."""
    print("\n4️⃣  Creating Students...")

    students = []
    for i in range(20):
        student = Student(
            student_id=f"student_{i:03d}",
            name=f"Student {chr(65 + i)}",  # Student A, B, C, etc.
            age=random.randint(12, 18),
            grade_level=str(random.randint(7, 12))
        )
        session_db.add(student)
        students.append(student)

    print(f"   ✓ Created {len(students)} students")
    return students


async def create_sessions_for_tutor(session_db, tutor, students, session_count, days_back):
    """Create sessions for a specific tutor."""
    sessions = []

    for i in range(session_count):
        days_ago = random.uniform(0, days_back)
        scheduled_date = datetime.now() - timedelta(days=days_ago)
        student = random.choice(students)

        # Determine if session was completed, no-show, or cancelled
        status_choices = ["completed", "no_show", "cancelled"]
        status_weights = [0.85, 0.10, 0.05]
        status = random.choices(status_choices, weights=status_weights)[0]

        sess = Session(
            session_id=f"session_{tutor.tutor_id}_{i:03d}",
            tutor_id=tutor.tutor_id,
            student_id=student.student_id,
            session_number=i + 1,
            subject=random.choice(tutor.subjects),
            scheduled_start=scheduled_date,
            actual_start=scheduled_date + timedelta(minutes=random.randint(0, 10)) if status == "completed" else None,
            duration_minutes=random.randint(45, 60),
            session_type=SessionType.ONE_ON_ONE,
            tutor_initiated_reschedule=(random.random() < 0.15),
            no_show=(status == "no_show"),
            technical_issues=(random.random() < 0.05),
            engagement_score=random.uniform(0.4, 0.9) if status == "completed" else None,
            learning_objectives_met=random.choice([True, False]) if status == "completed" else None
        )
        session_db.add(sess)
        sessions.append(sess)

        # Create feedback for completed sessions (85% rate)
        if status == "completed" and random.random() < 0.85:
            # Base rating on tutor performance
            if tutor.name == "Sarah Chen":
                base_rating = 4.1
            elif tutor.name == "Mike Ross":
                base_rating = 3.8
            elif tutor.behavioral_archetype == BehavioralArchetype.HIGH_PERFORMER:
                base_rating = random.uniform(4.7, 5.0)
            else:
                base_rating = random.uniform(4.0, 4.5)

            overall_rating = max(1, min(5, int(base_rating + random.uniform(-0.5, 0.5))))

            feedback = StudentFeedback(
                feedback_id=f"feedback_{sess.session_id}",
                session_id=sess.session_id,
                tutor_id=tutor.tutor_id,
                student_id=student.student_id,
                overall_rating=overall_rating,
                is_first_session=(i < 3),
                subject_knowledge_rating=overall_rating,
                communication_rating=max(1, min(5, overall_rating + random.randint(-1, 1))),
                patience_rating=max(1, min(5, overall_rating + random.randint(-1, 1))),
                engagement_rating=overall_rating,
                helpfulness_rating=overall_rating,
                free_text_feedback=f"{'Great' if overall_rating >= 4 else 'Okay'} session!",
                would_recommend=(overall_rating >= 4),
                submitted_at=scheduled_date + timedelta(hours=2)
            )
            session_db.add(feedback)

    return sessions


async def create_all_sessions(session_db, tutors, students):
    """Create sessions for all tutors."""
    print("\n5️⃣  Generating Sessions...")

    all_sessions = []

    for tutor in tutors:
        if tutor.name == "Sarah Chen":
            count, days = 15, 30  # 15 sessions in last 30 days
            print(f"   📊 Sarah Chen: {count} sessions (DECLINING)")
        elif tutor.name == "Mike Ross":
            count, days = 5, 10  # Only 5 sessions
            print(f"   📊 Mike Ross: {count} sessions (NEW)")
        elif tutor.behavioral_archetype == BehavioralArchetype.HIGH_PERFORMER:
            count, days = random.randint(45, 60), 30
            print(f"   📊 {tutor.name}: {count} sessions (HIGH PERFORMER)")
        else:
            count, days = random.randint(20, 35), 30

        sessions = await create_sessions_for_tutor(session_db, tutor, students, count, days)
        all_sessions.extend(sessions)

    print(f"\n   ✅ Generated {len(all_sessions)} total sessions")
    return all_sessions


async def create_interventions(session_db, tutors):
    """Create interventions for at-risk tutors."""
    print("\n6️⃣  Creating Interventions...")

    intervention_count = 0

    for tutor in tutors:
        # Get churn prediction
        churn_result = await session_db.execute(
            select(ChurnPrediction).where(ChurnPrediction.tutor_id == tutor.tutor_id)
        )
        churn = churn_result.scalar_one_or_none()

        if not churn:
            continue

        # Create interventions based on risk level
        if churn.churn_score >= 70:  # Critical risk
            intervention_types = [
                (InterventionType.MANAGER_COACHING, "high"),
                (InterventionType.RETENTION_INTERVIEW, "critical"),
                (InterventionType.PERFORMANCE_IMPROVEMENT_PLAN, "high")
            ]
        elif churn.churn_score >= 30:  # Medium risk
            intervention_types = [
                (InterventionType.AUTOMATED_COACHING, "medium"),
                (InterventionType.TRAINING_MODULE, "medium")
            ]
        else:
            continue

        for int_type, priority in intervention_types:
            intervention = Intervention(
                intervention_id=f"int_{tutor.tutor_id}_{uuid.uuid4().hex[:8]}",
                tutor_id=tutor.tutor_id,
                intervention_type=int_type,
                trigger_reason=f"Churn risk: {churn.churn_score}%",
                recommended_date=datetime.now(),
                assigned_to="operations_manager",
                status=random.choice([InterventionStatus.PENDING, InterventionStatus.IN_PROGRESS]),
                due_date=datetime.now() + timedelta(days=random.randint(1, 7))
            )
            session_db.add(intervention)
            intervention_count += 1

    print(f"   ✅ Created {intervention_count} interventions")


async def print_summary(session_db):
    """Print summary of generated data."""
    print("\n" + "=" * 60)
    print("📊 PRESENTATION DEMO DATA SUMMARY")
    print("=" * 60)

    # Count tutors
    tutor_count = await session_db.execute(select(func.count(Tutor.tutor_id)))
    print(f"\n👥 Tutors: {tutor_count.scalar()}")

    # Key tutors
    key_tutors = await session_db.execute(
        select(Tutor).where(Tutor.name.in_(["Sarah Chen", "Mike Ross"]))
    )
    print("\n🎯 Key Demo Tutors:")
    for tutor in key_tutors.scalars():
        # Get churn prediction
        churn_result = await session_db.execute(
            select(ChurnPrediction).where(ChurnPrediction.tutor_id == tutor.tutor_id)
        )
        churn = churn_result.scalar_one_or_none()

        # Get metrics
        metrics_result = await session_db.execute(
            select(TutorPerformanceMetric).where(TutorPerformanceMetric.tutor_id == tutor.tutor_id)
        )
        metrics = metrics_result.scalar_one_or_none()

        print(f"\n   {tutor.name}:")
        print(f"   - Email: {tutor.email}")
        print(f"   - Tutor ID: {tutor.tutor_id}")
        if churn:
            print(f"   - Churn Risk (30d): {churn.window_30day_probability:.0%}")
            print(f"   - Risk Level: {churn.risk_level.value}")
        if metrics:
            print(f"   - Average Rating: {metrics.avg_rating:.1f}")
            print(f"   - Engagement: {metrics.engagement_score:.2f}")
            print(f"   - First Session Success: {metrics.first_session_success_rate:.0%}")
            print(f"   - Sessions (last {metrics.window.value}): {metrics.sessions_completed}")

    # Other counts
    session_count = await session_db.execute(select(func.count(Session.session_id)))
    feedback_count = await session_db.execute(select(func.count(StudentFeedback.feedback_id)))
    intervention_count = await session_db.execute(select(func.count(Intervention.intervention_id)))

    print(f"\n📅 Sessions: {session_count.scalar()}")
    print(f"⭐ Feedback Records: {feedback_count.scalar()}")
    print(f"🚨 Interventions: {intervention_count.scalar()}")

    print("\n" + "=" * 60)
    print("✅ DEMO DATA GENERATION COMPLETE!")
    print("=" * 60)

    print("\n📝 Next Steps:")
    print("1. Start backend: python -m uvicorn src.main:app --reload")
    print("2. Start frontend: cd frontend && pnpm dev")
    print("3. Login: admin@tutormax.com / admin123")
    print("4. View dashboard: http://localhost:3000/dashboard")
    print("5. Sarah Chen profile: http://localhost:3000/tutor/sarah_chen_001")
    print("6. Mike Ross profile: http://localhost:3000/tutor/mike_ross_001")
    print("7. Interventions: http://localhost:3000/interventions")
    print("\n" + "=" * 60)


async def main():
    """Main execution."""
    print("\n" + "=" * 60)
    print("🎬 TutorMax Presentation Demo Data Generator")
    print("=" * 60)
    print("\nCreates:")
    print("  • Sarah Chen (72% churn risk)")
    print("  • Mike Ross (40% first session success)")
    print("  • 3 High Performers")
    print("  • 20 Students")
    print("  • Realistic sessions & feedback")
    print("  • Performance metrics")
    print("  • Churn predictions")
    print("  • Interventions")

    response = input("\n▶️  Continue? (y/N): ").strip().lower()
    if response != 'y':
        print("Cancelled.")
        return

    async with async_session_maker() as session_db:
        try:
            # Create tutors
            sarah = await create_sarah_chen(session_db)
            mike = await create_mike_ross(session_db)
            high_performers = await create_high_performers(session_db)

            all_tutors = [sarah, mike] + high_performers

            # Create students
            students = await create_students(session_db)

            # Commit tutors and students
            await session_db.commit()

            # Create sessions and feedback
            await create_all_sessions(session_db, all_tutors, students)

            # Create interventions
            await create_interventions(session_db, all_tutors)

            # Commit everything
            await session_db.commit()

            # Print summary
            await print_summary(session_db)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await session_db.rollback()
            sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
