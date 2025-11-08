"""
Database package for TutorMax.
Provides ORM models, connection management, and utilities.
"""

from src.database.models import (
    Base,
    Tutor,
    Student,
    Session,
    StudentFeedback,
    TutorPerformanceMetric,
    ChurnPrediction,
    Intervention,
    TutorEvent,
)
from src.database.connection import (
    get_engine,
    get_session,
    init_db,
    close_db,
)

__all__ = [
    # Models
    "Base",
    "Tutor",
    "Student",
    "Session",
    "StudentFeedback",
    "TutorPerformanceMetric",
    "ChurnPrediction",
    "Intervention",
    "TutorEvent",
    # Connection utilities
    "get_engine",
    "get_session",
    "init_db",
    "close_db",
]
