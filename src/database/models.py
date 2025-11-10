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
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable
import enum


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


# FastAPI Users needs its own base - we'll create User first, then use its metadata for other models
# This avoids registry conflicts with SQLAlchemy 2.0


# Enums for type safety
class UserRole(str, enum.Enum):
    """User role for RBAC."""
    ADMIN = "admin"
    OPERATIONS_MANAGER = "operations_manager"
    PEOPLE_OPS = "people_ops"
    TUTOR = "tutor"
    STUDENT = "student"


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


class NotificationType(str, enum.Enum):
    """Type of notification."""
    EMAIL = "email"
    IN_APP = "in_app"
    BOTH = "both"


class NotificationStatus(str, enum.Enum):
    """Status of notification delivery."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    READ = "read"


class NotificationPriority(str, enum.Enum):
    """Priority level for notifications."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MetricWindow(str, enum.Enum):
    """Time window for metric calculation."""
    SEVEN_DAY = "7day"
    THIRTY_DAY = "30day"
    NINETY_DAY = "90day"


class OAuthProvider(str, enum.Enum):
    """OAuth provider for SSO."""
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    CUSTOM = "custom"
    LOCAL = "local"  # For email/password authentication


# ORM Models


class User(Base, SQLAlchemyBaseUserTable[int]):
    """
    User entity for authentication and RBAC.
    Represents all users in the system (tutors, students, staff).

    Inherits from:
    - Base: Provides SQLAlchemy registry and metadata
    - SQLAlchemyBaseUserTable[int]: Provides FastAPI-Users standard fields
      (email, hashed_password, is_active, is_superuser, is_verified)

    Note: The id field must be explicitly defined when using SQLAlchemy 2.0.
    """
    __tablename__ = "users"

    # Primary key - required for SQLAlchemy 2.0 with FastAPI-Users
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Custom fields beyond FastAPI-Users base
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)

    # OAuth fields
    oauth_provider: Mapped[Optional[OAuthProvider]] = mapped_column(
        SQLEnum(OAuthProvider, native_enum=False),
        nullable=True  # Null for local auth
    )
    oauth_subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # OAuth provider's user ID

    # Role and status
    roles: Mapped[List[UserRole]] = mapped_column(
        ARRAY(SQLEnum(UserRole, native_enum=False)),
        nullable=False,
        default=[]
    )

    # Linked entity IDs (if applicable)
    tutor_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        ForeignKey("tutors.tutor_id", ondelete="SET NULL"),
        nullable=True,
        unique=True
    )
    student_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        ForeignKey("students.student_id", ondelete="SET NULL"),
        nullable=True,
        unique=True
    )

    # Security tracking
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

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

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, roles={self.roles})>"


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
    manager_notes: Mapped[List["ManagerNote"]] = relationship(
        "ManagerNote",
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

    # COPPA Compliance fields (for students under 13)
    is_under_13: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    parent_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    parent_consent_given: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    parent_consent_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    parent_consent_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

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
    event_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    # Relationships
    tutor: Mapped["Tutor"] = relationship("Tutor", back_populates="events")

    def __repr__(self) -> str:
        return f"<TutorEvent(event_id={self.event_id}, tutor_id={self.tutor_id}, type={self.event_type})>"


class Notification(Base):
    """
    Notification entity for intervention and system notifications.
    Tracks both email and in-app notifications sent to tutors and staff.
    """
    __tablename__ = "notifications"

    notification_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    recipient_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Tutor ID or staff member ID"
    )
    recipient_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )
    notification_type: Mapped[NotificationType] = mapped_column(
        SQLEnum(NotificationType, native_enum=False),
        nullable=False
    )
    priority: Mapped[NotificationPriority] = mapped_column(
        SQLEnum(NotificationPriority, native_enum=False),
        default=NotificationPriority.MEDIUM,
        nullable=False,
        index=True
    )
    status: Mapped[NotificationStatus] = mapped_column(
        SQLEnum(NotificationStatus, native_enum=False),
        default=NotificationStatus.PENDING,
        nullable=False,
        index=True
    )

    # Content
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    html_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Context
    intervention_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        ForeignKey("interventions.intervention_id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    intervention_type: Mapped[Optional[InterventionType]] = mapped_column(
        SQLEnum(InterventionType, native_enum=False),
        nullable=True
    )

    # Delivery tracking
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    failed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Metadata (using 'notification_metadata' to avoid SQLAlchemy reserved word)
    notification_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)

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
    intervention: Mapped[Optional["Intervention"]] = relationship("Intervention", backref="notifications")

    def __repr__(self) -> str:
        return f"<Notification(notification_id={self.notification_id}, recipient={self.recipient_id}, status={self.status})>"


class AuditLog(Base):
    """
    Audit log entity for security and compliance tracking.
    Records all sensitive operations, data access, and authentication events.
    """
    __tablename__ = "audit_logs"

    log_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # e.g., "login", "data_access", "update"
    resource_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # e.g., "tutor", "session"
    resource_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv6 max length
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    request_method: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # GET, POST, etc.
    request_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    audit_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    def __repr__(self) -> str:
        return f"<AuditLog(log_id={self.log_id}, user_id={self.user_id}, action={self.action})>"


class ManagerNote(Base):
    """
    Manager notes entity for tutor profile annotations.
    Allows operations managers to add private notes about tutors.
    """
    __tablename__ = "manager_notes"

    note_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tutor_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("tutors.tutor_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    author_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    author_name: Mapped[str] = mapped_column(String(200), nullable=False)
    note_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_important: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    tutor: Mapped["Tutor"] = relationship("Tutor", back_populates="manager_notes")

    def __repr__(self) -> str:
        return f"<ManagerNote(note_id={self.note_id}, tutor_id={self.tutor_id}, author={self.author_name})>"


class ServiceHealthCheck(Base):
    """
    Service health check records for uptime monitoring.

    Tracks health check results for all system services to ensure
    >99.5% uptime SLA (PRD requirement).
    """
    __tablename__ = "service_health_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # up, down, degraded
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    def __repr__(self) -> str:
        return f"<ServiceHealthCheck(id={self.id}, service={self.service_name}, status={self.status})>"


class SLAMetric(Base):
    """
    SLA metrics tracking for performance monitoring.

    Tracks key SLA metrics like insight latency (<60 min requirement)
    and API response times.
    """
    __tablename__ = "sla_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    metric_unit: Mapped[str] = mapped_column(String(50), nullable=False)  # seconds, milliseconds, percentage
    threshold: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # SLA threshold
    meets_sla: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    def __repr__(self) -> str:
        return f"<SLAMetric(id={self.id}, metric={self.metric_name}, value={self.metric_value}, meets_sla={self.meets_sla})>"


class FirstSessionPrediction(Base):
    """
    First session success prediction entity.

    Stores ML predictions for upcoming first sessions to enable
    proactive tutor preparation and risk mitigation.
    """
    __tablename__ = "first_session_predictions"

    prediction_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
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

    # Prediction results
    prediction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    risk_probability: Mapped[float] = mapped_column(Float, nullable=False)  # 0-1
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-100
    risk_level: Mapped[RiskLevel] = mapped_column(
        SQLEnum(RiskLevel, native_enum=False),
        nullable=False,
        index=True
    )
    risk_prediction: Mapped[int] = mapped_column(Integer, nullable=False)  # 0 or 1

    # Model metadata
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    top_risk_factors: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Alert tracking
    alert_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    alert_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Actual outcome (filled in after session)
    actual_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    actual_poor_session: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    prediction_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

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

    def __repr__(self) -> str:
        return f"<FirstSessionPrediction(prediction_id={self.prediction_id}, session_id={self.session_id}, risk={self.risk_level})>"


class ModelPerformanceLog(Base):
    """
    Model performance tracking entity.

    Tracks prediction accuracy and performance metrics over time
    for model monitoring and retraining decisions.
    """
    __tablename__ = "model_performance_logs"

    log_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # "first_session", "churn", etc.
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)

    # Performance metrics
    evaluation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    precision: Mapped[float] = mapped_column(Float, nullable=False)
    recall: Mapped[float] = mapped_column(Float, nullable=False)
    f1_score: Mapped[float] = mapped_column(Float, nullable=False)
    auc_roc: Mapped[float] = mapped_column(Float, nullable=False)

    # Sample info
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    time_window_days: Mapped[int] = mapped_column(Integer, nullable=False)

    # Additional metrics
    metrics_detail: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<ModelPerformanceLog(log_id={self.log_id}, model={self.model_type}, accuracy={self.accuracy:.3f})>"
