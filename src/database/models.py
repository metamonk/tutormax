"""
SQLAlchemy ORM models for TutorMax database schema.
Implements the complete data model from PRD lines 562-703.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Boolean,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    ForeignKey,
    ARRAY,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


# Enums for type safety
class TutorStatus(str, enum.Enum):
    """Tutor account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    CHURNED = "churned"


class BehavioralArchetype(str, enum.Enum):
    """Tutor behavioral archetype (for synthetic data)."""
    HIGH_PERFORMER = "high_performer"
    AT_RISK = "at_risk"
    NEW_TUTOR = "new_tutor"
    STEADY = "steady"
    CHURNER = "churner"


class SessionType(str, enum.Enum):
    """Type of tutoring session."""
    ONE_ON_ONE = "1-on-1"
    GROUP = "group"


class PerformanceTier(str, enum.Enum):
    """Tutor performance tier."""
    EXEMPLARY = "Exemplary"
    STRONG = "Strong"
    DEVELOPING = "Developing"
    NEEDS_ATTENTION = "Needs Attention"
    AT_RISK = "At Risk"


class RiskLevel(str, enum.Enum):
    """Churn risk level."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class InterventionType(str, enum.Enum):
    """Type of intervention."""
    AUTOMATED_COACHING = "automated_coaching"
    TRAINING_MODULE = "training_module"
    FIRST_SESSION_CHECKIN = "first_session_checkin"
    RESCHEDULING_ALERT = "rescheduling_alert"
    MANAGER_COACHING = "manager_coaching"
    PEER_MENTORING = "peer_mentoring"
    PERFORMANCE_IMPROVEMENT_PLAN = "performance_improvement_plan"
    RETENTION_INTERVIEW = "retention_interview"
    RECOGNITION = "recognition"


class InterventionStatus(str, enum.Enum):
    """Intervention task status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class InterventionOutcome(str, enum.Enum):
    """Outcome of completed intervention."""
    IMPROVED = "improved"
    NO_CHANGE = "no_change"
    DECLINED = "declined"
    CHURNED = "churned"


class MetricWindow(str, enum.Enum):
    """Time window for metric calculation."""
    SEVEN_DAY = "7day"
    THIRTY_DAY = "30day"
    NINETY_DAY = "90day"


# ORM Models


class Tutor(Base):
    """
    Tutor entity (PRD lines 567-581).
    Represents tutors on the platform.
    """
    __tablename__ = "tutors"

    tutor_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    onboarding_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[TutorStatus] = mapped_column(
        SQLEnum(TutorStatus, native_enum=False),
        default=TutorStatus.ACTIVE,
        nullable=False,
        index=True
    )
    subjects: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    education_level: Mapped[str] = mapped_column(String(100), nullable=True)
    location: Mapped[str] = mapped_column(String(200), nullable=True)
    baseline_sessions_per_week: Mapped[float] = mapped_column(Float, nullable=True)
    behavioral_archetype: Mapped[Optional[BehavioralArchetype]] = mapped_column(
        SQLEnum(BehavioralArchetype, native_enum=False),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    sessions: Mapped[List["Session"]] = relationship(
        "Session",
        back_populates="tutor",
        cascade="all, delete-orphan"
    )
    feedback: Mapped[List["StudentFeedback"]] = relationship(
        "StudentFeedback",
        back_populates="tutor",
        cascade="all, delete-orphan"
    )
    performance_metrics: Mapped[List["TutorPerformanceMetric"]] = relationship(
        "TutorPerformanceMetric",
        back_populates="tutor",
        cascade="all, delete-orphan"
    )
    churn_predictions: Mapped[List["ChurnPrediction"]] = relationship(
        "ChurnPrediction",
        back_populates="tutor",
        cascade="all, delete-orphan"
    )
    interventions: Mapped[List["Intervention"]] = relationship(
        "Intervention",
        back_populates="tutor",
        cascade="all, delete-orphan"
    )
    events: Mapped[List["TutorEvent"]] = relationship(
        "TutorEvent",
        back_populates="tutor",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Tutor(tutor_id={self.tutor_id}, name={self.name}, status={self.status})>"


class Student(Base):
    """
    Student entity (PRD lines 584-593).
    Represents students on the platform.
    """
    __tablename__ = "students"

    student_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=True)
    grade_level: Mapped[str] = mapped_column(String(50), nullable=True)
    subjects_interested: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    sessions: Mapped[List["Session"]] = relationship(
        "Session",
        back_populates="student",
        cascade="all, delete-orphan"
    )
    feedback: Mapped[List["StudentFeedback"]] = relationship(
        "StudentFeedback",
        back_populates="student",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Student(student_id={self.student_id}, name={self.name})>"


class Session(Base):
    """
    Session entity (PRD lines 596-615).
    Represents individual tutoring sessions.
    """
    __tablename__ = "sessions"

    session_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tutor_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("tutors.tutor_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    student_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("students.student_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    session_number: Mapped[int] = mapped_column(Integer, nullable=False)
    scheduled_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    actual_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    subject: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    session_type: Mapped[SessionType] = mapped_column(
        SQLEnum(SessionType, native_enum=False),
        default=SessionType.ONE_ON_ONE,
        nullable=False
    )
    tutor_initiated_reschedule: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    no_show: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    late_start_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    engagement_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    learning_objectives_met: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    technical_issues: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    tutor: Mapped["Tutor"] = relationship("Tutor", back_populates="sessions")
    student: Mapped["Student"] = relationship("Student", back_populates="sessions")
    feedback: Mapped[Optional["StudentFeedback"]] = relationship(
        "StudentFeedback",
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Session(session_id={self.session_id}, tutor_id={self.tutor_id}, student_id={self.student_id})>"


class StudentFeedback(Base):
    """
    Student feedback entity (PRD lines 618-636).
    Stores student ratings and feedback for sessions.
    """
    __tablename__ = "student_feedback"

    feedback_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    student_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("students.student_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    tutor_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("tutors.tutor_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    overall_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    is_first_session: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    subject_knowledge_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    communication_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    patience_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    engagement_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    helpfulness_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    would_recommend: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    improvement_areas: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    free_text_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="feedback")
    student: Mapped["Student"] = relationship("Student", back_populates="feedback")
    tutor: Mapped["Tutor"] = relationship("Tutor", back_populates="feedback")

    def __repr__(self) -> str:
        return f"<StudentFeedback(feedback_id={self.feedback_id}, session_id={self.session_id}, rating={self.overall_rating})>"


class TutorPerformanceMetric(Base):
    """
    Tutor performance metrics entity (PRD lines 639-656).
    Stores calculated/aggregated performance metrics.
    """
    __tablename__ = "tutor_performance_metrics"

    metric_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tutor_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("tutors.tutor_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    calculation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    window: Mapped[MetricWindow] = mapped_column(
        SQLEnum(MetricWindow, native_enum=False),
        nullable=False
    )
    sessions_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    first_session_success_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reschedule_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    no_show_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    engagement_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    learning_objectives_met_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    response_time_avg_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    performance_tier: Mapped[Optional[PerformanceTier]] = mapped_column(
        SQLEnum(PerformanceTier, native_enum=False),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    tutor: Mapped["Tutor"] = relationship("Tutor", back_populates="performance_metrics")

    def __repr__(self) -> str:
        return f"<TutorPerformanceMetric(metric_id={self.metric_id}, tutor_id={self.tutor_id}, window={self.window})>"


class ChurnPrediction(Base):
    """
    Churn prediction entity (PRD lines 659-674).
    Stores ML-based churn predictions for tutors.
    """
    __tablename__ = "churn_predictions"

    prediction_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tutor_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("tutors.tutor_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    prediction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    churn_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(
        SQLEnum(RiskLevel, native_enum=False),
        nullable=False,
        index=True
    )
    window_1day_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    window_7day_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    window_30day_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    window_90day_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    contributing_factors: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    tutor: Mapped["Tutor"] = relationship("Tutor", back_populates="churn_predictions")

    def __repr__(self) -> str:
        return f"<ChurnPrediction(prediction_id={self.prediction_id}, tutor_id={self.tutor_id}, score={self.churn_score})>"


class Intervention(Base):
    """
    Intervention entity (PRD lines 677-692).
    Tracks intervention tasks for at-risk tutors.
    """
    __tablename__ = "interventions"

    intervention_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tutor_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("tutors.tutor_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    intervention_type: Mapped[InterventionType] = mapped_column(
        SQLEnum(InterventionType, native_enum=False),
        nullable=False
    )
    trigger_reason: Mapped[str] = mapped_column(Text, nullable=True)
    recommended_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    assigned_to: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[InterventionStatus] = mapped_column(
        SQLEnum(InterventionStatus, native_enum=False),
        default=InterventionStatus.PENDING,
        nullable=False,
        index=True
    )
    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    completed_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    outcome: Mapped[Optional[InterventionOutcome]] = mapped_column(
        SQLEnum(InterventionOutcome, native_enum=False),
        nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    tutor: Mapped["Tutor"] = relationship("Tutor", back_populates="interventions")

    def __repr__(self) -> str:
        return f"<Intervention(intervention_id={self.intervention_id}, tutor_id={self.tutor_id}, type={self.intervention_type})>"


class TutorEvent(Base):
    """
    Tutor event entity (PRD lines 695-703).
    Tracks tutor behavior events for pattern detection.
    """
    __tablename__ = "tutor_events"

    event_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tutor_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("tutors.tutor_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    event_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    # Relationships
    tutor: Mapped["Tutor"] = relationship("Tutor", back_populates="events")

    def __repr__(self) -> str:
        return f"<TutorEvent(event_id={self.event_id}, tutor_id={self.tutor_id}, type={self.event_type})>"
