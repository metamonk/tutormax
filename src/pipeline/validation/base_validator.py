"""
Base validator class for data validation.

Provides foundation for all validator implementations with common
validation patterns, error handling, and result structures.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """Represents a validation error."""

    field: str
    message: str
    value: Any = None
    severity: str = "error"  # error, warning

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "field": self.field,
            "message": self.message,
            "value": self.value,
            "severity": self.severity,
        }


@dataclass
class ValidationResult:
    """Result of data validation."""

    valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    validated_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_error(self, field: str, message: str, value: Any = None):
        """Add a validation error."""
        self.errors.append(ValidationError(field, message, value, "error"))
        self.valid = False

    def add_warning(self, field: str, message: str, value: Any = None):
        """Add a validation warning."""
        self.warnings.append(ValidationError(field, message, value, "warning"))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "valid": self.valid,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "metadata": self.metadata,
        }


class BaseValidator(ABC):
    """
    Base class for all data validators.

    Provides common validation utilities and enforces validation interface.
    Subclasses must implement validate_data() method.
    """

    def __init__(self):
        """Initialize validator."""
        self.stats = {
            "total_validated": 0,
            "valid_count": 0,
            "invalid_count": 0,
        }

    @abstractmethod
    def validate_data(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate data dictionary.

        Args:
            data: Data dictionary to validate

        Returns:
            ValidationResult with validation status and errors
        """
        pass

    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Main validation entry point with statistics tracking.

        Args:
            data: Data dictionary to validate

        Returns:
            ValidationResult with validation status
        """
        try:
            result = self.validate_data(data)

            # Update statistics
            self.stats["total_validated"] += 1
            if result.valid:
                self.stats["valid_count"] += 1
            else:
                self.stats["invalid_count"] += 1

            return result

        except Exception as e:
            logger.error(f"Validation error: {e}", exc_info=True)
            result = ValidationResult(valid=False)
            result.add_error("_system", f"Validation exception: {str(e)}")
            self.stats["total_validated"] += 1
            self.stats["invalid_count"] += 1
            return result

    # Common validation helper methods

    def validate_required_fields(
        self,
        data: Dict[str, Any],
        required_fields: List[str],
        result: ValidationResult
    ) -> None:
        """
        Validate that required fields are present and not None.

        Args:
            data: Data dictionary
            required_fields: List of required field names
            result: ValidationResult to add errors to
        """
        for field in required_fields:
            if field not in data:
                result.add_error(field, f"Required field '{field}' is missing")
            elif data[field] is None:
                result.add_error(field, f"Required field '{field}' cannot be null")

    def validate_string_field(
        self,
        data: Dict[str, Any],
        field: str,
        result: ValidationResult,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        allowed_values: Optional[List[str]] = None
    ) -> None:
        """
        Validate a string field.

        Args:
            data: Data dictionary
            field: Field name
            result: ValidationResult to add errors to
            min_length: Minimum string length
            max_length: Maximum string length
            allowed_values: List of allowed values
        """
        if field not in data or data[field] is None:
            return

        value = data[field]

        if not isinstance(value, str):
            result.add_error(field, f"Field '{field}' must be a string", value)
            return

        if min_length is not None and len(value) < min_length:
            result.add_error(
                field,
                f"Field '{field}' must be at least {min_length} characters",
                value
            )

        if max_length is not None and len(value) > max_length:
            result.add_error(
                field,
                f"Field '{field}' must be at most {max_length} characters",
                value
            )

        if allowed_values is not None and value not in allowed_values:
            result.add_error(
                field,
                f"Field '{field}' must be one of {allowed_values}",
                value
            )

    def validate_int_field(
        self,
        data: Dict[str, Any],
        field: str,
        result: ValidationResult,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None
    ) -> None:
        """
        Validate an integer field.

        Args:
            data: Data dictionary
            field: Field name
            result: ValidationResult to add errors to
            min_value: Minimum allowed value
            max_value: Maximum allowed value
        """
        if field not in data or data[field] is None:
            return

        value = data[field]

        if not isinstance(value, int):
            result.add_error(field, f"Field '{field}' must be an integer", value)
            return

        if min_value is not None and value < min_value:
            result.add_error(
                field,
                f"Field '{field}' must be at least {min_value}",
                value
            )

        if max_value is not None and value > max_value:
            result.add_error(
                field,
                f"Field '{field}' must be at most {max_value}",
                value
            )

    def validate_float_field(
        self,
        data: Dict[str, Any],
        field: str,
        result: ValidationResult,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> None:
        """
        Validate a float field.

        Args:
            data: Data dictionary
            field: Field name
            result: ValidationResult to add errors to
            min_value: Minimum allowed value
            max_value: Maximum allowed value
        """
        if field not in data or data[field] is None:
            return

        value = data[field]

        if not isinstance(value, (int, float)):
            result.add_error(field, f"Field '{field}' must be a number", value)
            return

        value = float(value)

        if min_value is not None and value < min_value:
            result.add_error(
                field,
                f"Field '{field}' must be at least {min_value}",
                value
            )

        if max_value is not None and value > max_value:
            result.add_error(
                field,
                f"Field '{field}' must be at most {max_value}",
                value
            )

    def validate_bool_field(
        self,
        data: Dict[str, Any],
        field: str,
        result: ValidationResult
    ) -> None:
        """
        Validate a boolean field.

        Args:
            data: Data dictionary
            field: Field name
            result: ValidationResult to add errors to
        """
        if field not in data or data[field] is None:
            return

        value = data[field]

        if not isinstance(value, bool):
            result.add_error(field, f"Field '{field}' must be a boolean", value)

    def validate_email(
        self,
        data: Dict[str, Any],
        field: str,
        result: ValidationResult
    ) -> None:
        """
        Validate an email field.

        Args:
            data: Data dictionary
            field: Field name
            result: ValidationResult to add errors to
        """
        if field not in data or data[field] is None:
            return

        value = data[field]

        if not isinstance(value, str):
            result.add_error(field, f"Field '{field}' must be a string", value)
            return

        # Basic email validation
        if "@" not in value or "." not in value.split("@")[-1]:
            result.add_error(field, f"Field '{field}' must be a valid email", value)

    def validate_datetime_iso(
        self,
        data: Dict[str, Any],
        field: str,
        result: ValidationResult,
        allow_future: bool = True,
        max_future_days: Optional[int] = None
    ) -> None:
        """
        Validate an ISO format datetime field.

        Args:
            data: Data dictionary
            field: Field name
            result: ValidationResult to add errors to
            allow_future: Whether to allow future dates
            max_future_days: Maximum days in the future allowed
        """
        if field not in data or data[field] is None:
            return

        value = data[field]

        if not isinstance(value, str):
            result.add_error(field, f"Field '{field}' must be a string", value)
            return

        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))

            now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()

            if not allow_future and dt > now:
                result.add_error(
                    field,
                    f"Field '{field}' cannot be in the future",
                    value
                )

            if max_future_days is not None:
                max_future = now.replace(hour=23, minute=59, second=59)
                from datetime import timedelta
                max_future += timedelta(days=max_future_days)

                if dt > max_future:
                    result.add_error(
                        field,
                        f"Field '{field}' cannot be more than {max_future_days} days in the future",
                        value
                    )

        except (ValueError, TypeError) as e:
            result.add_error(
                field,
                f"Field '{field}' must be a valid ISO datetime",
                value
            )

    def validate_list_field(
        self,
        data: Dict[str, Any],
        field: str,
        result: ValidationResult,
        min_items: Optional[int] = None,
        max_items: Optional[int] = None,
        item_type: Optional[type] = None
    ) -> None:
        """
        Validate a list field.

        Args:
            data: Data dictionary
            field: Field name
            result: ValidationResult to add errors to
            min_items: Minimum number of items
            max_items: Maximum number of items
            item_type: Expected type of list items
        """
        if field not in data or data[field] is None:
            return

        value = data[field]

        if not isinstance(value, list):
            result.add_error(field, f"Field '{field}' must be a list", value)
            return

        if min_items is not None and len(value) < min_items:
            result.add_error(
                field,
                f"Field '{field}' must have at least {min_items} items",
                value
            )

        if max_items is not None and len(value) > max_items:
            result.add_error(
                field,
                f"Field '{field}' must have at most {max_items} items",
                value
            )

        if item_type is not None:
            for i, item in enumerate(value):
                if not isinstance(item, item_type):
                    result.add_error(
                        field,
                        f"Item {i} in '{field}' must be of type {item_type.__name__}",
                        item
                    )

    def get_stats(self) -> Dict[str, int]:
        """Get validation statistics."""
        return self.stats.copy()
