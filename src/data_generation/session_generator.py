"""
Session data generator for TutorMax system.

Generates synthetic session data with realistic patterns correlated
to tutor behavioral archetypes as defined in the PRD.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import random
from uuid import uuid4

from faker import Faker
import numpy as np

from .tutor_generator import BehavioralArchetype, Subject


class SessionGenerator:
    """
    Generates synthetic session data with realistic temporal patterns.

    Sessions correlate with tutor behavioral archetypes:
    - High Performers: Low reschedules, on-time, high engagement
    - At-Risk: Increasing reschedules, declining engagement
    - Churners: High reschedules, no-shows
    - New Tutors: Variable performance
    - Steady: Average metrics
    """

    # Time slots for sessions (hour of day)
    TIME_SLOTS = {
        "morning": list(range(6, 12)),      # 6am-12pm
        "afternoon": list(range(12, 17)),   # 12pm-5pm
        "evening": list(range(17, 22)),     # 5pm-10pm
    }

    # Session duration options (in minutes)
    SESSION_DURATIONS = [30, 45, 60, 90, 120]

    # Typical session duration weights
    DURATION_WEIGHTS = [0.10, 0.20, 0.50, 0.15, 0.05]

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the session generator.

        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)
            np.random.seed(seed)

        self.fake = Faker()
        if seed is not None:
            self.fake.seed_instance(seed)

        self._session_counter = 0
        self._student_counter = 0

        # Track student-tutor pairings and session counts
        self._pairing_sessions: Dict[Tuple[str, str], int] = {}
        self._student_cache: Dict[str, Dict] = {}

    def generate_session(
        self,
        tutor: Dict,
        student_id: Optional[str] = None,
        scheduled_date: Optional[datetime] = None,
        session_id: Optional[str] = None
    ) -> Dict:
        """
        Generate a single session for a tutor.

        Args:
            tutor: Tutor profile dictionary
            student_id: Optional specific student ID
            scheduled_date: Optional scheduled date/time
            session_id: Optional custom session ID

        Returns:
            Dict containing session data
        """
        self._session_counter += 1

        # Generate session ID
        if session_id is None:
            session_id = str(uuid4())

        # Get or create student
        if student_id is None:
            student_id = self._get_or_create_student()

        # Determine session number for this tutor-student pairing
        pairing_key = (tutor["tutor_id"], student_id)
        session_number = self._pairing_sessions.get(pairing_key, 0) + 1
        self._pairing_sessions[pairing_key] = session_number

        is_first_session = session_number == 1

        # Generate schedule timing
        if scheduled_date is None:
            scheduled_date = self._generate_schedule_time()

        # Get tutor archetype
        archetype = BehavioralArchetype(tutor["behavioral_archetype"])

        # Generate session behaviors based on archetype
        behaviors = self._generate_session_behaviors(
            archetype,
            is_first_session,
            scheduled_date
        )

        # Calculate actual start time
        actual_start = scheduled_date + timedelta(
            minutes=behaviors["late_start_minutes"]
        )

        # Select subject from tutor's expertise
        subject = random.choice(tutor["subjects"])

        # Generate session duration
        duration = random.choices(
            self.SESSION_DURATIONS,
            weights=self.DURATION_WEIGHTS,
            k=1
        )[0]

        # Generate engagement score based on archetype
        engagement_score = self._generate_engagement_score(
            archetype,
            is_first_session,
            behaviors["no_show"]
        )

        session_data = {
            "session_id": session_id,
            "tutor_id": tutor["tutor_id"],
            "student_id": student_id,
            "session_number": session_number,
            "is_first_session": is_first_session,
            "scheduled_start": scheduled_date.isoformat(),
            "actual_start": actual_start.isoformat() if not behaviors["no_show"] else None,
            "duration_minutes": duration if not behaviors["no_show"] else 0,
            "subject": subject,
            "session_type": "1-on-1",  # Could be expanded to include groups
            "tutor_initiated_reschedule": behaviors["tutor_initiated_reschedule"],
            "no_show": behaviors["no_show"],
            "late_start_minutes": behaviors["late_start_minutes"],
            "engagement_score": engagement_score,
            "learning_objectives_met": behaviors["objectives_met"],
            "technical_issues": behaviors["technical_issues"],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        return session_data

    def generate_sessions_for_day(
        self,
        tutors: List[Dict],
        target_count: int = 3000,
        date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Generate sessions for a day across multiple tutors.

        Args:
            tutors: List of tutor profiles
            target_count: Target number of sessions (default: 3000/day per PRD)
            date: Date to generate sessions for (default: today)

        Returns:
            List of session dictionaries
        """
        if date is None:
            date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        sessions = []

        # Distribute sessions across tutors based on their baseline
        total_baseline = sum(t["baseline_sessions_per_week"] for t in tutors)

        for tutor in tutors:
            # Calculate this tutor's share of daily sessions
            # baseline_sessions_per_week represents weekly capacity
            # We distribute the daily target proportionally
            tutor_ratio = tutor["baseline_sessions_per_week"] / total_baseline
            tutor_session_count = int(target_count * tutor_ratio)

            # Add some randomness (+/- 30%)
            variance = max(1, int(tutor_session_count * 0.3))
            tutor_session_count = random.randint(
                max(0, tutor_session_count - variance),
                tutor_session_count + variance
            )

            # Generate sessions for this tutor
            for _ in range(tutor_session_count):
                # Schedule throughout the day
                scheduled_time = self._generate_schedule_time(base_date=date)
                session = self.generate_session(
                    tutor=tutor,
                    scheduled_date=scheduled_time
                )
                sessions.append(session)

        return sessions

    def _get_or_create_student(self) -> str:
        """Get existing student or create new one."""
        # 70% chance to use existing student, 30% new student
        if self._student_cache and random.random() < 0.7:
            return random.choice(list(self._student_cache.keys()))

        # Create new student
        self._student_counter += 1
        student_id = f"student_{self._student_counter:05d}"

        self._student_cache[student_id] = {
            "student_id": student_id,
            "name": self.fake.name(),
            "age": random.randint(10, 18),
            "grade_level": random.randint(5, 12),
        }

        return student_id

    def _generate_schedule_time(
        self,
        base_date: Optional[datetime] = None
    ) -> datetime:
        """
        Generate realistic session scheduling time.

        Follows temporal patterns:
        - More sessions on weekdays vs weekends
        - Peak hours: afternoon and evening
        - Morning sessions cluster around weekends
        """
        if base_date is None:
            base_date = datetime.now()

        # Ensure we're working with a date
        base_date = base_date.replace(hour=0, minute=0, second=0, microsecond=0)

        # Add random day offset (within a week for variability)
        day_offset = random.randint(0, 6)
        session_date = base_date + timedelta(days=day_offset)

        # Weight by day of week (more on weekdays)
        is_weekend = session_date.weekday() >= 5
        if is_weekend and random.random() < 0.3:  # 30% chance to skip weekend
            # Shift to weekday
            session_date -= timedelta(days=random.randint(1, 2))

        # Select time slot (weighted)
        time_slot_weights = {
            "morning": 0.20,
            "afternoon": 0.35,
            "evening": 0.45,
        }

        time_slot = random.choices(
            list(time_slot_weights.keys()),
            weights=list(time_slot_weights.values()),
            k=1
        )[0]

        # Select specific hour within slot
        hour = random.choice(self.TIME_SLOTS[time_slot])
        minute = random.choice([0, 15, 30, 45])  # Quarter-hour intervals

        return session_date.replace(hour=hour, minute=minute)

    def _generate_session_behaviors(
        self,
        archetype: BehavioralArchetype,
        is_first_session: bool,
        scheduled_date: datetime
    ) -> Dict:
        """
        Generate session behaviors based on tutor archetype.

        Implements PRD patterns:
        - High reschedule rates predict churn
        - No-shows cluster in morning slots and Mondays
        - First session failures correlate with tenure
        """
        behaviors = {
            "tutor_initiated_reschedule": False,
            "no_show": False,
            "late_start_minutes": 0,
            "objectives_met": True,
            "technical_issues": False,
        }

        # Reschedule probability by archetype
        reschedule_probs = {
            BehavioralArchetype.HIGH_PERFORMER: 0.02,
            BehavioralArchetype.STEADY: 0.08,
            BehavioralArchetype.NEW_TUTOR: 0.12,
            BehavioralArchetype.AT_RISK: 0.25,
            BehavioralArchetype.CHURNER: 0.40,
        }

        # No-show probability by archetype
        no_show_probs = {
            BehavioralArchetype.HIGH_PERFORMER: 0.01,
            BehavioralArchetype.STEADY: 0.03,
            BehavioralArchetype.NEW_TUTOR: 0.08,
            BehavioralArchetype.AT_RISK: 0.12,
            BehavioralArchetype.CHURNER: 0.25,
        }

        # Check for reschedule
        behaviors["tutor_initiated_reschedule"] = (
            random.random() < reschedule_probs[archetype]
        )

        # Check for no-show (higher on Mondays and mornings per PRD)
        no_show_prob = no_show_probs[archetype]
        if scheduled_date.weekday() == 0:  # Monday
            no_show_prob *= 1.5
        if scheduled_date.hour < 12:  # Morning
            no_show_prob *= 1.3

        behaviors["no_show"] = random.random() < no_show_prob

        # Late start (only if not no-show)
        if not behaviors["no_show"]:
            if archetype == BehavioralArchetype.HIGH_PERFORMER:
                # Usually on time
                late_minutes = random.choices([0, 2, 5], weights=[0.85, 0.10, 0.05], k=1)[0]
            elif archetype == BehavioralArchetype.CHURNER:
                # Often late
                late_minutes = random.choices([0, 5, 10, 15], weights=[0.30, 0.30, 0.25, 0.15], k=1)[0]
            else:
                # Moderate lateness
                late_minutes = random.choices([0, 2, 5, 10], weights=[0.65, 0.20, 0.10, 0.05], k=1)[0]

            behaviors["late_start_minutes"] = late_minutes

            # First sessions with >10 min late start are flagged (PRD)
            if is_first_session and late_minutes > 10:
                behaviors["objectives_met"] = False

        # Learning objectives met (lower for at-risk and churners)
        if archetype in [BehavioralArchetype.AT_RISK, BehavioralArchetype.CHURNER]:
            behaviors["objectives_met"] = random.random() < 0.70
        else:
            behaviors["objectives_met"] = random.random() < 0.92

        # Technical issues (rare, slightly higher for new tutors)
        tech_issue_prob = 0.05 if archetype == BehavioralArchetype.NEW_TUTOR else 0.02
        behaviors["technical_issues"] = random.random() < tech_issue_prob

        return behaviors

    def _generate_engagement_score(
        self,
        archetype: BehavioralArchetype,
        is_first_session: bool,
        is_no_show: bool
    ) -> float:
        """
        Generate engagement score (0-1) based on archetype.

        High performers: 0.80-1.0
        Steady: 0.65-0.85
        New tutors: 0.50-0.90 (variable)
        At-risk: 0.40-0.70
        Churners: 0.20-0.50
        """
        if is_no_show:
            return 0.0

        engagement_ranges = {
            BehavioralArchetype.HIGH_PERFORMER: (0.80, 1.0),
            BehavioralArchetype.STEADY: (0.65, 0.85),
            BehavioralArchetype.NEW_TUTOR: (0.50, 0.90),
            BehavioralArchetype.AT_RISK: (0.40, 0.70),
            BehavioralArchetype.CHURNER: (0.20, 0.50),
        }

        min_score, max_score = engagement_ranges[archetype]
        score = random.uniform(min_score, max_score)

        # First sessions tend to be slightly lower
        if is_first_session:
            score *= 0.95

        return round(score, 3)

    def get_session_stats(self, sessions: List[Dict]) -> Dict:
        """
        Calculate session statistics.

        Args:
            sessions: List of generated sessions

        Returns:
            Dict with session statistics
        """
        if not sessions:
            return {}

        total = len(sessions)
        first_sessions = sum(1 for s in sessions if s["is_first_session"])
        reschedules = sum(1 for s in sessions if s["tutor_initiated_reschedule"])
        no_shows = sum(1 for s in sessions if s["no_show"])
        late_starts = sum(1 for s in sessions if s["late_start_minutes"] > 5)
        objectives_met = sum(1 for s in sessions if s["learning_objectives_met"])

        avg_engagement = np.mean([s["engagement_score"] for s in sessions])

        stats = {
            "total_sessions": total,
            "first_sessions": first_sessions,
            "first_session_rate": round(first_sessions / total * 100, 2),
            "reschedule_count": reschedules,
            "reschedule_rate": round(reschedules / total * 100, 2),
            "no_show_count": no_shows,
            "no_show_rate": round(no_shows / total * 100, 2),
            "late_start_count": late_starts,
            "late_start_rate": round(late_starts / total * 100, 2),
            "objectives_met_count": objectives_met,
            "objectives_met_rate": round(objectives_met / total * 100, 2),
            "avg_engagement_score": round(avg_engagement, 3),
        }

        return stats
