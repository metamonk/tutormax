"""
Tests for database models and connections.
"""

import pytest
from datetime import datetime
from sqlalchemy import select

from src.database import (
    Base,
    Tutor,
    Student,
    Session,
    StudentFeedback,
    TutorPerformanceMetric,
    ChurnPrediction,
    Intervention,
    TutorEvent,
    get_engine,
    get_session,
    close_db,
)
from src.database.models import (
    TutorStatus,
    BehavioralArchetype,
    SessionType,
    PerformanceTier,
    RiskLevel,
    InterventionType,
    InterventionStatus,
    MetricWindow,
)


@pytest.fixture(scope="function")
async def db_engine():
    """Create test database engine."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await close_db()


@pytest.mark.asyncio
async def test_create_tutor(db_engine):
    """Test creating a tutor."""
    async with get_session() as db:
        tutor = Tutor(
            tutor_id="test_tutor_001",
            name="Jane Doe",
            email="jane.doe@example.com",
            onboarding_date=datetime.utcnow(),
            status=TutorStatus.ACTIVE,
            subjects=["Mathematics", "Physics"],
            education_level="Masters",
            location="New York",
            baseline_sessions_per_week=15.0,
            behavioral_archetype=BehavioralArchetype.HIGH_PERFORMER,
        )
        db.add(tutor)
        await db.commit()

        # Verify
        result = await db.execute(
            select(Tutor).where(Tutor.tutor_id == "test_tutor_001")
        )
        retrieved = result.scalar_one()
        assert retrieved.name == "Jane Doe"
        assert retrieved.email == "jane.doe@example.com"
        assert retrieved.status == TutorStatus.ACTIVE
        assert "Mathematics" in retrieved.subjects


@pytest.mark.asyncio
async def test_create_student(db_engine):
    """Test creating a student."""
    async with get_session() as db:
        student = Student(
            student_id="test_student_001",
            name="John Smith",
            age=16,
            grade_level="10th",
            subjects_interested=["Mathematics", "Chemistry"],
        )
        db.add(student)
        await db.commit()

        # Verify
        result = await db.execute(
            select(Student).where(Student.student_id == "test_student_001")
        )
        retrieved = result.scalar_one()
        assert retrieved.name == "John Smith"
        assert retrieved.age == 16


@pytest.mark.asyncio
async def test_create_session_with_relationships(db_engine):
    """Test creating a session with tutor and student relationships."""
    async with get_session() as db:
        # Create tutor
        tutor = Tutor(
            tutor_id="test_tutor_002",
            name="Alice Teacher",
            email="alice@example.com",
            onboarding_date=datetime.utcnow(),
            status=TutorStatus.ACTIVE,
            subjects=["Mathematics"],
        )
        db.add(tutor)

        # Create student
        student = Student(
            student_id="test_student_002",
            name="Bob Student",
            age=15,
            grade_level="9th",
        )
        db.add(student)

        # Create session
        session = Session(
            session_id="test_session_001",
            tutor_id=tutor.tutor_id,
            student_id=student.student_id,
            session_number=1,
            scheduled_start=datetime.utcnow(),
            duration_minutes=60,
            subject="Mathematics",
            session_type=SessionType.ONE_ON_ONE,
            tutor_initiated_reschedule=False,
            no_show=False,
            late_start_minutes=5,
            engagement_score=0.85,
            learning_objectives_met=True,
            technical_issues=False,
        )
        db.add(session)
        await db.commit()

        # Verify relationships
        result = await db.execute(
            select(Session).where(Session.session_id == "test_session_001")
        )
        retrieved = result.scalar_one()
        assert retrieved.tutor_id == tutor.tutor_id
        assert retrieved.student_id == student.student_id


@pytest.mark.asyncio
async def test_create_student_feedback(db_engine):
    """Test creating student feedback."""
    async with get_session() as db:
        # Create dependencies
        tutor = Tutor(
            tutor_id="test_tutor_003",
            name="Carol Tutor",
            email="carol@example.com",
            onboarding_date=datetime.utcnow(),
            status=TutorStatus.ACTIVE,
            subjects=["Science"],
        )
        student = Student(
            student_id="test_student_003",
            name="Dave Student",
        )
        session = Session(
            session_id="test_session_002",
            tutor_id=tutor.tutor_id,
            student_id=student.student_id,
            session_number=1,
            scheduled_start=datetime.utcnow(),
            duration_minutes=60,
            subject="Science",
        )
        db.add_all([tutor, student, session])

        # Create feedback
        feedback = StudentFeedback(
            feedback_id="test_feedback_001",
            session_id=session.session_id,
            student_id=student.student_id,
            tutor_id=tutor.tutor_id,
            overall_rating=5,
            is_first_session=True,
            subject_knowledge_rating=5,
            communication_rating=4,
            patience_rating=5,
            engagement_rating=4,
            helpfulness_rating=5,
            would_recommend=True,
            free_text_feedback="Great session!",
            submitted_at=datetime.utcnow(),
        )
        db.add(feedback)
        await db.commit()

        # Verify
        result = await db.execute(
            select(StudentFeedback).where(
                StudentFeedback.feedback_id == "test_feedback_001"
            )
        )
        retrieved = result.scalar_one()
        assert retrieved.overall_rating == 5
        assert retrieved.is_first_session is True


@pytest.mark.asyncio
async def test_create_performance_metric(db_engine):
    """Test creating performance metrics."""
    async with get_session() as db:
        tutor = Tutor(
            tutor_id="test_tutor_004",
            name="Eve Tutor",
            email="eve@example.com",
            onboarding_date=datetime.utcnow(),
            status=TutorStatus.ACTIVE,
            subjects=["Math"],
        )
        db.add(tutor)

        metric = TutorPerformanceMetric(
            metric_id="test_metric_001",
            tutor_id=tutor.tutor_id,
            calculation_date=datetime.utcnow(),
            window=MetricWindow.THIRTY_DAY,
            sessions_completed=42,
            avg_rating=4.5,
            first_session_success_rate=0.85,
            reschedule_rate=0.10,
            no_show_count=2,
            engagement_score=0.90,
            learning_objectives_met_pct=0.88,
            response_time_avg_minutes=15.5,
            performance_tier=PerformanceTier.STRONG,
        )
        db.add(metric)
        await db.commit()

        # Verify
        result = await db.execute(
            select(TutorPerformanceMetric).where(
                TutorPerformanceMetric.metric_id == "test_metric_001"
            )
        )
        retrieved = result.scalar_one()
        assert retrieved.sessions_completed == 42
        assert retrieved.performance_tier == PerformanceTier.STRONG


@pytest.mark.asyncio
async def test_create_churn_prediction(db_engine):
    """Test creating churn prediction."""
    async with get_session() as db:
        tutor = Tutor(
            tutor_id="test_tutor_005",
            name="Frank Tutor",
            email="frank@example.com",
            onboarding_date=datetime.utcnow(),
            status=TutorStatus.ACTIVE,
            subjects=["English"],
        )
        db.add(tutor)

        prediction = ChurnPrediction(
            prediction_id="test_prediction_001",
            tutor_id=tutor.tutor_id,
            prediction_date=datetime.utcnow(),
            churn_score=68,
            risk_level=RiskLevel.HIGH,
            window_1day_probability=0.45,
            window_7day_probability=0.72,
            window_30day_probability=0.68,
            window_90day_probability=0.55,
            contributing_factors={
                "engagement_decline": 0.30,
                "reschedule_pattern": 0.25,
                "no_show_risk": 0.15,
            },
            model_version="v1.0.0",
        )
        db.add(prediction)
        await db.commit()

        # Verify
        result = await db.execute(
            select(ChurnPrediction).where(
                ChurnPrediction.prediction_id == "test_prediction_001"
            )
        )
        retrieved = result.scalar_one()
        assert retrieved.churn_score == 68
        assert retrieved.risk_level == RiskLevel.HIGH
        assert retrieved.contributing_factors["engagement_decline"] == 0.30


@pytest.mark.asyncio
async def test_create_intervention(db_engine):
    """Test creating intervention."""
    async with get_session() as db:
        tutor = Tutor(
            tutor_id="test_tutor_006",
            name="Grace Tutor",
            email="grace@example.com",
            onboarding_date=datetime.utcnow(),
            status=TutorStatus.ACTIVE,
            subjects=["History"],
        )
        db.add(tutor)

        intervention = Intervention(
            intervention_id="test_intervention_001",
            tutor_id=tutor.tutor_id,
            intervention_type=InterventionType.MANAGER_COACHING,
            trigger_reason="High churn score detected",
            recommended_date=datetime.utcnow(),
            assigned_to="manager_001",
            status=InterventionStatus.PENDING,
            notes="Schedule coaching session within 48 hours",
        )
        db.add(intervention)
        await db.commit()

        # Verify
        result = await db.execute(
            select(Intervention).where(
                Intervention.intervention_id == "test_intervention_001"
            )
        )
        retrieved = result.scalar_one()
        assert retrieved.intervention_type == InterventionType.MANAGER_COACHING
        assert retrieved.status == InterventionStatus.PENDING


@pytest.mark.asyncio
async def test_create_tutor_event(db_engine):
    """Test creating tutor event."""
    async with get_session() as db:
        tutor = Tutor(
            tutor_id="test_tutor_007",
            name="Henry Tutor",
            email="henry@example.com",
            onboarding_date=datetime.utcnow(),
            status=TutorStatus.ACTIVE,
            subjects=["Art"],
        )
        db.add(tutor)

        event = TutorEvent(
            event_id="test_event_001",
            tutor_id=tutor.tutor_id,
            event_type="login",
            event_timestamp=datetime.utcnow(),
            metadata={"ip_address": "192.168.1.1", "device": "mobile"},
        )
        db.add(event)
        await db.commit()

        # Verify
        result = await db.execute(
            select(TutorEvent).where(TutorEvent.event_id == "test_event_001")
        )
        retrieved = result.scalar_one()
        assert retrieved.event_type == "login"
        assert retrieved.metadata["device"] == "mobile"


@pytest.mark.asyncio
async def test_cascade_delete(db_engine):
    """Test cascade delete of related records."""
    async with get_session() as db:
        # Create tutor with related records
        tutor = Tutor(
            tutor_id="test_tutor_cascade",
            name="Cascade Test",
            email="cascade@example.com",
            onboarding_date=datetime.utcnow(),
            status=TutorStatus.ACTIVE,
            subjects=["Test"],
        )
        student = Student(
            student_id="test_student_cascade",
            name="Test Student",
        )
        session = Session(
            session_id="test_session_cascade",
            tutor_id=tutor.tutor_id,
            student_id=student.student_id,
            session_number=1,
            scheduled_start=datetime.utcnow(),
            duration_minutes=60,
            subject="Test",
        )
        db.add_all([tutor, student, session])
        await db.commit()

        # Delete tutor
        await db.delete(tutor)
        await db.commit()

        # Verify session was also deleted (cascade)
        result = await db.execute(
            select(Session).where(Session.session_id == "test_session_cascade")
        )
        assert result.scalar_one_or_none() is None
