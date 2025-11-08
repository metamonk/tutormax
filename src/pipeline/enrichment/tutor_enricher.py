"""
Tutor data enricher.

Enriches tutor data with derived fields:
- is_new_tutor: tenure_days < 30
- experience_level: based on tenure (junior <90, mid 90-365, senior >365)
- subject_count: number of subjects taught
- is_active_today: based on updated_at
- tenure_days: days since onboarding
"""

from typing import Any, Dict, List
from datetime import datetime, timezone
from .base_enricher import BaseEnricher, EnrichmentResult


class TutorEnricher(BaseEnricher):
    """Enricher for tutor data."""

    def get_required_fields(self) -> List[str]:
        """Get required fields for tutor enrichment."""
        return [
            "tutor_id",
            "name",
            "email",
            "onboarding_date",
            "status",
            "subjects",
        ]

    def enrich(self, data: Dict[str, Any]) -> EnrichmentResult:
        """
        Enrich tutor data with derived fields.

        Args:
            data: Validated tutor data

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
            # Calculate tenure days
            onboarding_date = self._parse_datetime(data.get("onboarding_date"))
            if onboarding_date:
                tenure_days = self._calculate_tenure_days(onboarding_date)
                enriched_data["tenure_days"] = tenure_days
                derived_fields["tenure_days"] = tenure_days

                # Determine if new tutor
                is_new_tutor = tenure_days < 30
                enriched_data["is_new_tutor"] = is_new_tutor
                derived_fields["is_new_tutor"] = is_new_tutor

                # Determine experience level
                experience_level = self._calculate_experience_level(tenure_days)
                enriched_data["experience_level"] = experience_level
                derived_fields["experience_level"] = experience_level

            # Count subjects
            subjects = data.get("subjects", [])
            if isinstance(subjects, list):
                subject_count = len(subjects)
                enriched_data["subject_count"] = subject_count
                derived_fields["subject_count"] = subject_count

            # Check if active today
            updated_at = self._parse_datetime(data.get("updated_at"))
            if updated_at:
                is_active_today = self._is_active_today(updated_at)
                enriched_data["is_active_today"] = is_active_today
                derived_fields["is_active_today"] = is_active_today

            self.stats["enrichments_successful"] += 1

            return EnrichmentResult(
                success=True,
                data=enriched_data,
                derived_fields=derived_fields,
                metadata={
                    "enriched_at": datetime.now(timezone.utc).isoformat(),
                    "enricher": "TutorEnricher",
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

    def _calculate_tenure_days(self, onboarding_date: datetime) -> int:
        """
        Calculate days since onboarding.

        Args:
            onboarding_date: Tutor onboarding date

        Returns:
            Number of days since onboarding
        """
        now = datetime.now(timezone.utc)

        # Make onboarding_date timezone-aware if needed
        if onboarding_date.tzinfo is None:
            onboarding_date = onboarding_date.replace(tzinfo=timezone.utc)

        delta = now - onboarding_date
        return max(0, delta.days)

    def _calculate_experience_level(self, tenure_days: int) -> str:
        """
        Calculate experience level based on tenure.

        Args:
            tenure_days: Days since onboarding

        Returns:
            Experience level (junior, mid, senior)
        """
        if tenure_days < 90:
            return "junior"
        elif tenure_days < 365:
            return "mid"
        else:
            return "senior"

    def _is_active_today(self, updated_at: datetime) -> bool:
        """
        Check if tutor was active today.

        Args:
            updated_at: Last updated timestamp

        Returns:
            True if updated today
        """
        now = datetime.now(timezone.utc)

        # Make updated_at timezone-aware if needed
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)

        return updated_at.date() == now.date()
