"""
Feedback data enricher.

Enriches feedback data with derived fields:
- is_positive: overall_rating >= 4
- is_poor: overall_rating < 3
- avg_category_rating: average of all category ratings
- category_variance: variance across ratings
- has_text_feedback: len(free_text_feedback) > 0
- feedback_delay_hours: hours between session and feedback submission
"""

from typing import Any, Dict, List
from datetime import datetime, timezone
from .base_enricher import BaseEnricher, EnrichmentResult


class FeedbackEnricher(BaseEnricher):
    """Enricher for student feedback data."""

    # Category rating fields
    CATEGORY_FIELDS = [
        "subject_knowledge_rating",
        "communication_rating",
        "patience_rating",
        "engagement_rating",
        "helpfulness_rating",
    ]

    def get_required_fields(self) -> List[str]:
        """Get required fields for feedback enrichment."""
        return [
            "feedback_id",
            "session_id",
            "student_id",
            "tutor_id",
            "overall_rating",
            "submitted_at",
        ]

    def enrich(self, data: Dict[str, Any]) -> EnrichmentResult:
        """
        Enrich feedback data with derived fields.

        Args:
            data: Validated feedback data

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
            # Is positive rating
            overall_rating = data.get("overall_rating", 0)
            is_positive = overall_rating >= 4
            enriched_data["is_positive"] = is_positive
            derived_fields["is_positive"] = is_positive

            # Is poor rating
            is_poor = overall_rating < 3
            enriched_data["is_poor"] = is_poor
            derived_fields["is_poor"] = is_poor

            # Average category rating
            category_ratings = self._get_category_ratings(data)
            if category_ratings:
                avg_category_rating = sum(category_ratings) / len(category_ratings)
                enriched_data["avg_category_rating"] = round(avg_category_rating, 2)
                derived_fields["avg_category_rating"] = round(avg_category_rating, 2)

                # Category variance
                category_variance = self._calculate_variance(category_ratings)
                enriched_data["category_variance"] = round(category_variance, 2)
                derived_fields["category_variance"] = round(category_variance, 2)

            # Has text feedback
            free_text = data.get("free_text_feedback", "")
            has_text_feedback = (
                isinstance(free_text, str) and len(free_text.strip()) > 0
            )
            enriched_data["has_text_feedback"] = has_text_feedback
            derived_fields["has_text_feedback"] = has_text_feedback

            # Feedback delay (if session_scheduled_start provided in metadata)
            session_scheduled_start = data.get("session_scheduled_start")
            submitted_at = self._parse_datetime(data.get("submitted_at"))

            if session_scheduled_start and submitted_at:
                scheduled_start_dt = self._parse_datetime(session_scheduled_start)
                if scheduled_start_dt:
                    delay_hours = self._calculate_feedback_delay(
                        scheduled_start_dt, submitted_at
                    )
                    enriched_data["feedback_delay_hours"] = delay_hours
                    derived_fields["feedback_delay_hours"] = delay_hours

            self.stats["enrichments_successful"] += 1

            return EnrichmentResult(
                success=True,
                data=enriched_data,
                derived_fields=derived_fields,
                metadata={
                    "enriched_at": datetime.now(timezone.utc).isoformat(),
                    "enricher": "FeedbackEnricher",
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

    def _get_category_ratings(self, data: Dict[str, Any]) -> List[float]:
        """
        Extract all non-null category ratings.

        Args:
            data: Feedback data

        Returns:
            List of category rating values
        """
        ratings = []

        for field in self.CATEGORY_FIELDS:
            value = data.get(field)
            if value is not None:
                try:
                    ratings.append(float(value))
                except (ValueError, TypeError):
                    pass

        return ratings

    def _calculate_variance(self, values: List[float]) -> float:
        """
        Calculate variance of values.

        Args:
            values: List of numeric values

        Returns:
            Variance
        """
        if not values:
            return 0.0

        mean = sum(values) / len(values)
        squared_diffs = [(x - mean) ** 2 for x in values]
        variance = sum(squared_diffs) / len(values)

        return variance

    def _calculate_feedback_delay(
        self, session_start: datetime, submitted_at: datetime
    ) -> float:
        """
        Calculate hours between session and feedback submission.

        Args:
            session_start: Session scheduled start time
            submitted_at: Feedback submission time

        Returns:
            Hours between session and feedback
        """
        # Make timezone-aware if needed
        if session_start.tzinfo is None:
            session_start = session_start.replace(tzinfo=timezone.utc)
        if submitted_at.tzinfo is None:
            submitted_at = submitted_at.replace(tzinfo=timezone.utc)

        delta = submitted_at - session_start
        hours = delta.total_seconds() / 3600

        return round(hours, 2)
