"""
Performance Calculator - Core metrics calculation engine.

Calculates tutor performance metrics based on session data, feedback, and events.
Implements the 6 core metrics defined in the PRD.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import (
    Tutor,
    Session,
    StudentFeedback,
    TutorEvent,
    TutorPerformanceMetric,
    MetricWindow,
    PerformanceTier,
)


@dataclass
class PerformanceMetrics:
    """Container for calculated performance metrics."""

    tutor_id: str
    calculation_date: datetime
    window: MetricWindow
    sessions_completed: int
    avg_rating: Optional[float]
    first_session_success_rate: Optional[float]
    reschedule_rate: Optional[float]
    no_show_count: int
    engagement_score: Optional[float]
    learning_objectives_met_pct: Optional[float]
    response_time_avg_minutes: Optional[float]
    performance_tier: Optional[PerformanceTier]

    # Additional context
    total_sessions_scheduled: int = 0
    first_sessions_count: int = 0
    reschedule_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database persistence."""
        data = asdict(self)
        # Convert enums to values
        if self.window:
            data['window'] = self.window.value
        if self.performance_tier:
            data['performance_tier'] = self.performance_tier.value
        return data


class PerformanceCalculator:
    """
    Calculates tutor performance metrics.

    Core metrics (from PRD):
    1. Session Rating Average (30-day mean)
    2. First Session Success Rate (% rated ≥4)
    3. Reschedule Rate (tutor-initiated / total)
    4. No-Show Rate (%)
    5. Engagement Score (composite)
    6. Learning Objectives Met %
    """

    def __init__(self, db_session: AsyncSession):
        """
        Initialize calculator.

        Args:
            db_session: Async database session
        """
        self.db = db_session
        self.stats = {
            "calculations_performed": 0,
            "calculations_successful": 0,
            "calculations_failed": 0,
        }

    async def calculate_metrics(
        self,
        tutor_id: str,
        window: MetricWindow,
        reference_date: Optional[datetime] = None,
    ) -> PerformanceMetrics:
        """
        Calculate all performance metrics for a tutor.

        Args:
            tutor_id: ID of tutor to evaluate
            window: Time window for calculation (7day, 30day, 90day)
            reference_date: Date to calculate from (defaults to now)

        Returns:
            PerformanceMetrics object with all calculated values
        """
        self.stats["calculations_performed"] += 1

        if reference_date is None:
            reference_date = datetime.utcnow()

        # Calculate window start date
        window_days = self._get_window_days(window)
        window_start = reference_date - timedelta(days=window_days)

        try:
            # Gather all required data
            sessions = await self._get_sessions(tutor_id, window_start, reference_date)
            feedback = await self._get_feedback(tutor_id, window_start, reference_date)
            events = await self._get_tutor_events(tutor_id, window_start, reference_date)

            # Calculate individual metrics
            sessions_completed = self._calculate_sessions_completed(sessions)
            avg_rating = self._calculate_avg_rating(feedback)
            first_session_success_rate = self._calculate_first_session_success_rate(
                sessions, feedback
            )
            reschedule_rate, reschedule_count = self._calculate_reschedule_rate(sessions)
            no_show_count = self._calculate_no_show_count(sessions)
            engagement_score = self._calculate_engagement_score(sessions, events)
            learning_objectives_met_pct = self._calculate_learning_objectives_met(sessions)
            response_time_avg = self._calculate_response_time(events)

            # Assign performance tier
            performance_tier = self._assign_performance_tier(
                avg_rating=avg_rating,
                first_session_success_rate=first_session_success_rate,
                reschedule_rate=reschedule_rate,
                no_show_count=no_show_count,
                engagement_score=engagement_score,
                learning_objectives_met_pct=learning_objectives_met_pct,
            )

            self.stats["calculations_successful"] += 1

            return PerformanceMetrics(
                tutor_id=tutor_id,
                calculation_date=reference_date,
                window=window,
                sessions_completed=sessions_completed,
                avg_rating=avg_rating,
                first_session_success_rate=first_session_success_rate,
                reschedule_rate=reschedule_rate,
                no_show_count=no_show_count,
                engagement_score=engagement_score,
                learning_objectives_met_pct=learning_objectives_met_pct,
                response_time_avg_minutes=response_time_avg,
                performance_tier=performance_tier,
                total_sessions_scheduled=len(sessions),
                first_sessions_count=len([s for s in sessions if s.session_number == 1]),
                reschedule_count=reschedule_count,
            )

        except Exception as e:
            self.stats["calculations_failed"] += 1
            raise Exception(f"Failed to calculate metrics for tutor {tutor_id}: {str(e)}")

    async def save_metrics(self, metrics: PerformanceMetrics) -> str:
        """
        Persist calculated metrics to database.

        Args:
            metrics: Calculated performance metrics

        Returns:
            metric_id of saved record
        """
        metric_id = f"metric_{uuid.uuid4().hex[:12]}"

        db_metric = TutorPerformanceMetric(
            metric_id=metric_id,
            tutor_id=metrics.tutor_id,
            calculation_date=metrics.calculation_date,
            window=metrics.window,
            sessions_completed=metrics.sessions_completed,
            avg_rating=metrics.avg_rating,
            first_session_success_rate=metrics.first_session_success_rate,
            reschedule_rate=metrics.reschedule_rate,
            no_show_count=metrics.no_show_count,
            engagement_score=metrics.engagement_score,
            learning_objectives_met_pct=metrics.learning_objectives_met_pct,
            response_time_avg_minutes=metrics.response_time_avg_minutes,
            performance_tier=metrics.performance_tier,
        )

        self.db.add(db_metric)
        await self.db.flush()

        return metric_id

    # ==================== Data Retrieval Methods ====================

    async def _get_sessions(
        self, tutor_id: str, start_date: datetime, end_date: datetime
    ) -> List[Session]:
        """Get all sessions for tutor in window."""
        query = select(Session).where(
            and_(
                Session.tutor_id == tutor_id,
                Session.scheduled_start >= start_date,
                Session.scheduled_start < end_date,
            )
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def _get_feedback(
        self, tutor_id: str, start_date: datetime, end_date: datetime
    ) -> List[StudentFeedback]:
        """Get all feedback for tutor's sessions in window."""
        query = (
            select(StudentFeedback)
            .join(Session, StudentFeedback.session_id == Session.session_id)
            .where(
                and_(
                    StudentFeedback.tutor_id == tutor_id,
                    Session.scheduled_start >= start_date,
                    Session.scheduled_start < end_date,
                )
            )
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def _get_tutor_events(
        self, tutor_id: str, start_date: datetime, end_date: datetime
    ) -> List[TutorEvent]:
        """Get all tutor events in window."""
        query = select(TutorEvent).where(
            and_(
                TutorEvent.tutor_id == tutor_id,
                TutorEvent.event_timestamp >= start_date,
                TutorEvent.event_timestamp < end_date,
            )
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ==================== Metric Calculation Methods ====================

    def _calculate_sessions_completed(self, sessions: List[Session]) -> int:
        """
        Metric 1: Count of completed sessions.

        Completed = not no_show and actual_start is not None
        """
        return len([s for s in sessions if not s.no_show and s.actual_start is not None])

    def _calculate_avg_rating(self, feedback: List[StudentFeedback]) -> Optional[float]:
        """
        Metric 2: Session Rating Average.

        Mean of overall_rating from feedback (1-5 scale).
        Threshold: <3.5 = underperforming
        """
        if not feedback:
            return None

        ratings = [f.overall_rating for f in feedback if f.overall_rating is not None]
        if not ratings:
            return None

        return round(sum(ratings) / len(ratings), 2)

    def _calculate_first_session_success_rate(
        self, sessions: List[Session], feedback: List[StudentFeedback]
    ) -> Optional[float]:
        """
        Metric 3: First Session Success Rate.

        % of first sessions (session_number=1) with rating ≥4.
        Threshold: <70% = flag
        """
        # Get first sessions
        first_sessions = [s for s in sessions if s.session_number == 1]
        if not first_sessions:
            return None

        # Create feedback lookup
        feedback_map = {f.session_id: f for f in feedback}

        # Count successful first sessions
        successful = 0
        total = 0

        for session in first_sessions:
            if session.session_id in feedback_map:
                total += 1
                rating = feedback_map[session.session_id].overall_rating
                if rating and rating >= 4.0:
                    successful += 1

        if total == 0:
            return None

        return round((successful / total) * 100, 2)

    def _calculate_reschedule_rate(
        self, sessions: List[Session]
    ) -> tuple[Optional[float], int]:
        """
        Metric 4: Reschedule Rate.

        (Tutor-initiated reschedules / Total sessions) × 100
        Threshold: >15% = high

        Returns:
            (reschedule_rate_pct, reschedule_count)
        """
        if not sessions:
            return None, 0

        reschedules = len([s for s in sessions if s.tutor_initiated_reschedule])
        total = len(sessions)

        rate = round((reschedules / total) * 100, 2)
        return rate, reschedules

    def _calculate_no_show_count(self, sessions: List[Session]) -> int:
        """
        Metric 5: No-Show Count.

        Count of sessions where no_show = True.
        Threshold: >5% of sessions = concerning
        """
        return len([s for s in sessions if s.no_show])

    def _calculate_engagement_score(
        self, sessions: List[Session], events: List[TutorEvent]
    ) -> Optional[float]:
        """
        Metric 6: Engagement Score.

        Composite score (0-100) based on:
        - Login frequency (40%)
        - Session engagement scores (40%)
        - Timely session starts (20%)
        """
        if not sessions:
            return None

        # Component 1: Login frequency (40%)
        login_events = [e for e in events if e.event_type == "login"]
        login_score = min(len(login_events) / max(len(sessions), 1) * 100, 100)

        # Component 2: Session engagement scores (40%)
        engagement_scores = [
            s.engagement_score for s in sessions if s.engagement_score is not None
        ]
        if engagement_scores:
            session_score = sum(engagement_scores) / len(engagement_scores)
        else:
            session_score = 50.0  # Neutral default

        # Component 3: On-time starts (20%)
        late_sessions = len([s for s in sessions if s.late_start_minutes > 10])
        on_time_pct = ((len(sessions) - late_sessions) / len(sessions)) * 100

        # Weighted composite
        composite = (login_score * 0.4) + (session_score * 0.4) + (on_time_pct * 0.2)

        return round(composite, 2)

    def _calculate_learning_objectives_met(self, sessions: List[Session]) -> Optional[float]:
        """
        Metric 7: Learning Objectives Met %.

        % of sessions where learning_objectives_met = True.
        Threshold: <80% = needs improvement
        """
        if not sessions:
            return None

        objectives_data = [
            s for s in sessions if s.learning_objectives_met is not None
        ]

        if not objectives_data:
            return None

        met_count = len([s for s in objectives_data if s.learning_objectives_met])
        return round((met_count / len(objectives_data)) * 100, 2)

    def _calculate_response_time(self, events: List[TutorEvent]) -> Optional[float]:
        """
        Secondary Metric: Response Time Average.

        Average response time to student messages in minutes.
        Requires events with type='message_response' and response_time metadata.
        """
        response_events = [
            e for e in events
            if e.event_type == "message_response"
            and e.event_metadata
            and "response_time_minutes" in e.event_metadata
        ]

        if not response_events:
            return None

        response_times = [e.event_metadata["response_time_minutes"] for e in response_events]
        return round(sum(response_times) / len(response_times), 2)

    # ==================== Performance Tier Assignment ====================

    def _assign_performance_tier(
        self,
        avg_rating: Optional[float],
        first_session_success_rate: Optional[float],
        reschedule_rate: Optional[float],
        no_show_count: int,
        engagement_score: Optional[float],
        learning_objectives_met_pct: Optional[float],
    ) -> PerformanceTier:
        """
        Assign performance tier based on metric thresholds.

        Tiers (from PRD):
        - Exemplary: Top 10% (all metrics green)
        - Strong: Above average, no red flags
        - Developing: Average, some improvement areas
        - Needs Attention: Below average, intervention needed
        - At Risk: Critical issues, high churn probability
        """
        red_flags = 0
        green_flags = 0

        # Check avg_rating
        if avg_rating is not None:
            if avg_rating >= 4.5:
                green_flags += 1
            elif avg_rating < 3.5:
                red_flags += 1

        # Check first_session_success_rate
        if first_session_success_rate is not None:
            if first_session_success_rate >= 85:
                green_flags += 1
            elif first_session_success_rate < 70:
                red_flags += 1

        # Check reschedule_rate
        if reschedule_rate is not None:
            if reschedule_rate <= 10:
                green_flags += 1
            elif reschedule_rate > 15:
                red_flags += 1

        # Check no_show_count (relative to total sessions)
        if no_show_count > 3:
            red_flags += 1
        elif no_show_count == 0:
            green_flags += 1

        # Check engagement_score
        if engagement_score is not None:
            if engagement_score >= 80:
                green_flags += 1
            elif engagement_score < 60:
                red_flags += 1

        # Check learning_objectives_met_pct
        if learning_objectives_met_pct is not None:
            if learning_objectives_met_pct >= 90:
                green_flags += 1
            elif learning_objectives_met_pct < 80:
                red_flags += 1

        # Assign tier based on flags
        if green_flags >= 5 and red_flags == 0:
            return PerformanceTier.EXEMPLARY
        elif red_flags >= 3:
            return PerformanceTier.AT_RISK
        elif red_flags >= 1:
            return PerformanceTier.NEEDS_ATTENTION
        elif green_flags >= 3:
            return PerformanceTier.STRONG
        else:
            return PerformanceTier.DEVELOPING

    # ==================== Utility Methods ====================

    def _get_window_days(self, window: MetricWindow) -> int:
        """Convert MetricWindow enum to number of days."""
        mapping = {
            MetricWindow.SEVEN_DAY: 7,
            MetricWindow.THIRTY_DAY: 30,
            MetricWindow.NINETY_DAY: 90,
        }
        return mapping.get(window, 30)

    def get_stats(self) -> Dict[str, int]:
        """Get calculator statistics."""
        return self.stats.copy()

    def reset_stats(self) -> None:
        """Reset calculator statistics."""
        self.stats = {
            "calculations_performed": 0,
            "calculations_successful": 0,
            "calculations_failed": 0,
        }
