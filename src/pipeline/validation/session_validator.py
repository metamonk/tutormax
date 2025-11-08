"""
Session data validator.

Validates tutoring session data according to business rules and constraints.
"""

from typing import Any, Dict
from datetime import datetime, timedelta
import logging

from .base_validator import BaseValidator, ValidationResult

logger = logging.getLogger(__name__)


class SessionValidator(BaseValidator):
    """
    Validates tutoring session data.

    Validation Rules:
    - Valid tutor_id and student_id references (format check)
    - Valid session number (>= 1)
    - Duration in allowed values (30, 45, 60, 90 minutes)
    - Engagement score (0.0-1.0)
    - Valid subject
    - Scheduled date not in future by more than 30 days
    - Valid session type
    - Late start minutes <= duration
    - No-show sessions have no actual_start
    """

    # Valid enum values
    VALID_SESSION_TYPES = ["1-on-1", "group", "workshop"]

    # Valid durations (in minutes)
    VALID_DURATIONS = [30, 45, 60, 90]

    # Valid subjects (same as tutor validator)
    VALID_SUBJECTS = [
        # STEM
        "Mathematics", "Algebra", "Calculus", "Geometry",
        "Physics", "Chemistry", "Biology", "Computer Science",
        # Language
        "English", "Writing", "Literature", "Spanish", "French",
        # Test Prep
        "SAT Prep", "ACT Prep", "AP Test Prep", "GRE Prep"
    ]

    def validate_data(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate session data.

        Args:
            data: Session data dictionary

        Returns:
            ValidationResult with validation status and errors
        """
        result = ValidationResult(valid=True, validated_data=data.copy())

        # Required fields validation
        required_fields = [
            "session_id",
            "tutor_id",
            "student_id",
            "session_number",
            "is_first_session",
            "scheduled_start",
            "duration_minutes",
            "subject",
            "tutor_initiated_reschedule",
            "no_show",
            "late_start_minutes",
            "engagement_score",
            "learning_objectives_met",
            "technical_issues",
            "created_at",
            "updated_at",
        ]
        self.validate_required_fields(data, required_fields, result)

        # Return early if required fields are missing
        if not result.valid:
            return result

        # Validate session_id
        self.validate_string_field(
            data, "session_id", result,
            min_length=1, max_length=50
        )

        # Validate tutor_id (format check)
        self.validate_string_field(
            data, "tutor_id", result,
            min_length=1, max_length=50
        )

        # Validate student_id (format check)
        self.validate_string_field(
            data, "student_id", result,
            min_length=1, max_length=50
        )

        # Validate session_number (>= 1)
        self.validate_int_field(
            data, "session_number", result,
            min_value=1
        )

        # Validate is_first_session
        self.validate_bool_field(data, "is_first_session", result)

        # Validate scheduled_start (not more than 30 days in future)
        self.validate_datetime_iso(
            data, "scheduled_start", result,
            allow_future=True,
            max_future_days=30
        )

        # Validate actual_start (optional, can be null for no-shows)
        if "actual_start" in data and data["actual_start"] is not None:
            self.validate_datetime_iso(
                data, "actual_start", result,
                allow_future=False
            )

        # Validate duration_minutes
        self.validate_int_field(
            data, "duration_minutes", result,
            min_value=0, max_value=300
        )

        # Check if duration is in allowed values
        if "duration_minutes" in data and isinstance(data["duration_minutes"], int):
            if data["duration_minutes"] not in self.VALID_DURATIONS:
                result.add_warning(
                    "duration_minutes",
                    f"Duration {data['duration_minutes']} is not a standard value. "
                    f"Expected one of {self.VALID_DURATIONS}",
                    data["duration_minutes"]
                )

        # Validate subject
        self.validate_string_field(
            data, "subject", result,
            min_length=1, max_length=100
        )

        # Validate subject value
        if "subject" in data and isinstance(data["subject"], str):
            if data["subject"] not in self.VALID_SUBJECTS:
                result.add_error(
                    "subject",
                    f"Invalid subject: '{data['subject']}'. Must be one of {self.VALID_SUBJECTS}",
                    data["subject"]
                )

        # Validate session_type (optional)
        if "session_type" in data:
            self.validate_string_field(
                data, "session_type", result,
                allowed_values=self.VALID_SESSION_TYPES
            )

        # Validate boolean fields
        self.validate_bool_field(data, "tutor_initiated_reschedule", result)
        self.validate_bool_field(data, "no_show", result)
        self.validate_bool_field(data, "technical_issues", result)

        # Validate learning_objectives_met (boolean)
        self.validate_bool_field(data, "learning_objectives_met", result)

        # Validate late_start_minutes
        self.validate_int_field(
            data, "late_start_minutes", result,
            min_value=0, max_value=60
        )

        # Validate engagement_score (0.0-1.0)
        self.validate_float_field(
            data, "engagement_score", result,
            min_value=0.0, max_value=1.0
        )

        # Validate timestamps
        self.validate_datetime_iso(data, "created_at", result, allow_future=False)
        self.validate_datetime_iso(data, "updated_at", result, allow_future=False)

        # Business rules validation
        self._validate_business_rules(data, result)

        # Add metadata
        result.metadata = {
            "validator": "SessionValidator",
            "session_id": data.get("session_id"),
            "tutor_id": data.get("tutor_id"),
            "student_id": data.get("student_id"),
            "is_first_session": data.get("is_first_session"),
        }

        return result

    def _validate_business_rules(
        self,
        data: Dict[str, Any],
        result: ValidationResult
    ) -> None:
        """
        Validate business rules for session data.

        Args:
            data: Session data
            result: ValidationResult to add errors to
        """
        # Rule: No-show sessions should not have actual_start
        if data.get("no_show") is True:
            if data.get("actual_start") is not None:
                result.add_error(
                    "actual_start",
                    "No-show sessions should not have an actual_start time",
                    data.get("actual_start")
                )

        # Rule: Non-no-show sessions should have actual_start
        if data.get("no_show") is False:
            if data.get("actual_start") is None:
                result.add_warning(
                    "actual_start",
                    "Non-no-show sessions should have an actual_start time",
                    None
                )

        # Rule: Late start should not exceed duration
        duration = data.get("duration_minutes", 0)
        late_start = data.get("late_start_minutes", 0)

        if isinstance(duration, int) and isinstance(late_start, int):
            if late_start > duration:
                result.add_error(
                    "late_start_minutes",
                    f"Late start ({late_start} min) cannot exceed duration ({duration} min)",
                    late_start
                )

        # Rule: Actual start should be close to scheduled start
        if "scheduled_start" in data and "actual_start" in data:
            if data["actual_start"] is not None:
                try:
                    scheduled = datetime.fromisoformat(
                        data["scheduled_start"].replace("Z", "+00:00")
                    )
                    actual = datetime.fromisoformat(
                        data["actual_start"].replace("Z", "+00:00")
                    )

                    time_diff = abs((actual - scheduled).total_seconds() / 60)

                    # Warn if difference is more than late_start_minutes suggests
                    if time_diff > late_start + 5:  # 5 min grace period
                        result.add_warning(
                            "actual_start",
                            f"Actual start differs from scheduled by {time_diff:.1f} minutes, "
                            f"but late_start_minutes is {late_start}",
                            data["actual_start"]
                        )

                except (ValueError, AttributeError):
                    # Date format errors already caught
                    pass

        # Rule: First session should have session_number = 1
        if data.get("is_first_session") is True:
            if data.get("session_number") != 1:
                result.add_warning(
                    "session_number",
                    f"First session should have session_number=1, got {data.get('session_number')}",
                    data.get("session_number")
                )

        # Rule: Engagement score for no-shows should be low or 0
        if data.get("no_show") is True:
            engagement = data.get("engagement_score")
            if isinstance(engagement, (int, float)) and engagement > 0.1:
                result.add_warning(
                    "engagement_score",
                    f"No-show session has unexpectedly high engagement score: {engagement}",
                    engagement
                )
