"""
Base enricher class for data enrichment.

Provides common functionality for all data type enrichers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class EnrichmentResult:
    """Result of enrichment operation."""

    success: bool
    data: Dict[str, Any]
    derived_fields: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "derived_fields": self.derived_fields,
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }


class BaseEnricher(ABC):
    """
    Base class for all data enrichers.

    Each enricher is responsible for:
    1. Calculating derived fields
    2. Adding contextual information
    3. Preparing data for database persistence
    """

    def __init__(self):
        """Initialize enricher."""
        self.stats = {
            "enrichments_attempted": 0,
            "enrichments_successful": 0,
            "enrichments_failed": 0,
        }

    @abstractmethod
    def enrich(self, data: Dict[str, Any]) -> EnrichmentResult:
        """
        Enrich data with derived fields and context.

        Args:
            data: Raw validated data

        Returns:
            EnrichmentResult with enriched data
        """
        pass

    @abstractmethod
    def get_required_fields(self) -> List[str]:
        """
        Get list of required fields for enrichment.

        Returns:
            List of required field names
        """
        pass

    def validate_required_fields(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate that all required fields are present.

        Args:
            data: Data to validate

        Returns:
            List of missing field names
        """
        required = set(self.get_required_fields())
        present = set(data.keys())
        missing = required - present
        return list(missing)

    def safe_get(
        self,
        data: Dict[str, Any],
        key: str,
        default: Any = None,
        transform: Optional[callable] = None,
    ) -> Any:
        """
        Safely get value from dictionary with optional transformation.

        Args:
            data: Source dictionary
            key: Key to retrieve
            default: Default value if key missing
            transform: Optional transformation function

        Returns:
            Value (possibly transformed) or default
        """
        value = data.get(key, default)

        if value is not None and transform is not None:
            try:
                return transform(value)
            except Exception:
                return default

        return value

    def calculate_datetime_field(
        self, dt: datetime, field_type: str
    ) -> Optional[Any]:
        """
        Extract date/time component from datetime.

        Args:
            dt: Datetime object
            field_type: Type of field to extract (weekday, hour, week, month, etc.)

        Returns:
            Extracted value or None
        """
        if dt is None:
            return None

        try:
            if field_type == "weekday":
                return dt.weekday()  # 0 = Monday, 6 = Sunday
            elif field_type == "is_weekend":
                return dt.weekday() >= 5  # Saturday or Sunday
            elif field_type == "hour":
                return dt.hour
            elif field_type == "week_of_year":
                return dt.isocalendar()[1]
            elif field_type == "month_of_year":
                return dt.month
            elif field_type == "day_of_month":
                return dt.day
            elif field_type == "year":
                return dt.year
            else:
                return None
        except Exception:
            return None

    def get_stats(self) -> Dict[str, int]:
        """Get enricher statistics."""
        return self.stats.copy()

    def reset_stats(self) -> None:
        """Reset enricher statistics."""
        self.stats = {
            "enrichments_attempted": 0,
            "enrichments_successful": 0,
            "enrichments_failed": 0,
        }
