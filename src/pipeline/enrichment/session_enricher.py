"""
Session data enricher.

Enriches session data with derived fields:
- is_weekend: scheduled_start day is Sat/Sun
- time_of_day: morning/afternoon/evening from scheduled_start hour
- is_late_start: late_start_minutes > 5
- actual_duration_minutes: calculated from actual_start if available
- week_of_year: ISO week number from scheduled_start
- month_of_year: month from scheduled_start
"""

from typing import Any, Dict, List
from datetime import datetime, timezone
from .base_enricher import BaseEnricher, EnrichmentResult


class SessionEnricher(BaseEnricher):
    """Enricher for session data."""

    def get_required_fields(self) -> List[str]:
        """Get required fields for session enrichment."""
        return [
            "session_id",
            "tutor_id",
            "student_id",
            "scheduled_start",
            "duration_minutes",
            "subject",
        ]

    def enrich(self, data: Dict[str, Any]) -> EnrichmentResult:
        """
        Enrich session data with derived fields.

        Args:
            data: Validated session data

        Returns:
            EnrichmentResult with enriched data
        """
        self.stats["enrichments_attempted"] += 1

        # Validate required fields
        missing_fields = self.validate_required_fields(data)
        if missing_fields:
            self.stats["enrichments_failed"] += 1
            return EnrichmentResult(
                success=False,
                data=data,
                errors=[f"Missing required fields: {', '.join(missing_fields)}"],
            )

        enriched_data = data.copy()
        derived_fields = {}

        try:
            # Parse scheduled_start
            scheduled_start = self._parse_datetime(data.get("scheduled_start"))

            if scheduled_start:
                # Is weekend
                is_weekend = self.calculate_datetime_field(
                    scheduled_start, "is_weekend"
                )
                enriched_data["is_weekend"] = is_weekend
                derived_fields["is_weekend"] = is_weekend

                # Time of day
                time_of_day = self._calculate_time_of_day(scheduled_start)
                enriched_data["time_of_day"] = time_of_day
                derived_fields["time_of_day"] = time_of_day

                # Week of year
                week_of_year = self.calculate_datetime_field(
                    scheduled_start, "week_of_year"
                )
                enriched_data["week_of_year"] = week_of_year
                derived_fields["week_of_year"] = week_of_year

                # Month of year
                month_of_year = self.calculate_datetime_field(
                    scheduled_start, "month_of_year"
                )
                enriched_data["month_of_year"] = month_of_year
                derived_fields["month_of_year"] = month_of_year

            # Is late start
            late_start_minutes = data.get("late_start_minutes", 0)
            is_late_start = late_start_minutes > 5
            enriched_data["is_late_start"] = is_late_start
            derived_fields["is_late_start"] = is_late_start

            # Actual duration (if actual_start provided)
            actual_start = self._parse_datetime(data.get("actual_start"))
            if actual_start and scheduled_start:
                actual_duration = self._calculate_actual_duration(
                    scheduled_start,
                    actual_start,
                    data.get("duration_minutes", 0),
                )
                enriched_data["actual_duration_minutes"] = actual_duration
                derived_fields["actual_duration_minutes"] = actual_duration

            self.stats["enrichments_successful"] += 1

            return EnrichmentResult(
                success=True,
                data=enriched_data,
                derived_fields=derived_fields,
                metadata={
                    "enriched_at": datetime.now(timezone.utc).isoformat(),
                    "enricher": "SessionEnricher",
                },
            )

        except Exception as e:
            self.stats["enrichments_failed"] += 1
            return EnrichmentResult(
                success=False,
                data=data,
                errors=[f"Enrichment failed: {str(e)}"],
            )

    def _parse_datetime(self, dt_value: Any) -> datetime:
        """
        Parse datetime from various formats.

        Args:
            dt_value: Datetime value (string, datetime, etc.)

        Returns:
            Parsed datetime object or None
        """
        if dt_value is None:
            return None

        if isinstance(dt_value, datetime):
            return dt_value

        if isinstance(dt_value, str):
            try:
                # Try ISO format
                return datetime.fromisoformat(dt_value.replace("Z", "+00:00"))
            except Exception:
                try:
                    # Try common formats
                    return datetime.strptime(dt_value, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    return None

        return None

    def _calculate_time_of_day(self, dt: datetime) -> str:
        """
        Calculate time of day category from datetime.

        Args:
            dt: Datetime object

        Returns:
            Time of day category (morning, afternoon, evening)
        """
        hour = dt.hour

        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 22:
            return "evening"
        else:
            return "night"

    def _calculate_actual_duration(
        self,
        scheduled_start: datetime,
        actual_start: datetime,
        planned_duration: int,
    ) -> int:
        """
        Calculate actual session duration.

        Uses actual_start + planned_duration to estimate actual duration.

        Args:
            scheduled_start: Scheduled start time
            actual_start: Actual start time
            planned_duration: Planned duration in minutes

        Returns:
            Actual duration in minutes
        """
        # Make timezone-aware if needed
        if scheduled_start.tzinfo is None:
            scheduled_start = scheduled_start.replace(tzinfo=timezone.utc)
        if actual_start.tzinfo is None:
            actual_start = actual_start.replace(tzinfo=timezone.utc)

        # Calculate delay in minutes
        delay = (actual_start - scheduled_start).total_seconds() / 60

        # Actual duration = planned duration (we don't have actual end time)
        # In a real system, you'd calculate from actual_end - actual_start
        return max(0, int(planned_duration))
