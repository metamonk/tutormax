"""
Validation engine for orchestrating data validation.

Provides a unified interface for validating different data types
and routing data to appropriate validators.
"""

from typing import Any, Dict, Optional
import logging

from .base_validator import ValidationResult
from .tutor_validator import TutorValidator
from .session_validator import SessionValidator
from .feedback_validator import FeedbackValidator

logger = logging.getLogger(__name__)


class ValidationEngine:
    """
    Orchestrates data validation across different data types.

    Routes incoming data to the appropriate validator based on data type.
    Provides unified validation interface and statistics tracking.
    """

    def __init__(self):
        """Initialize validation engine with all validators."""
        self.validators = {
            "tutor": TutorValidator(),
            "session": SessionValidator(),
            "feedback": FeedbackValidator(),
        }

        self.stats = {
            "total_validated": 0,
            "valid_count": 0,
            "invalid_count": 0,
            "by_type": {
                "tutor": {"valid": 0, "invalid": 0},
                "session": {"valid": 0, "invalid": 0},
                "feedback": {"valid": 0, "invalid": 0},
            }
        }

    def validate(
        self,
        data: Dict[str, Any],
        data_type: str
    ) -> ValidationResult:
        """
        Validate data based on its type.

        Args:
            data: Data dictionary to validate
            data_type: Type of data ('tutor', 'session', 'feedback')

        Returns:
            ValidationResult with validation status and errors
        """
        data_type = data_type.lower()

        if data_type not in self.validators:
            result = ValidationResult(valid=False)
            result.add_error(
                "_type",
                f"Unknown data type: '{data_type}'. "
                f"Must be one of {list(self.validators.keys())}",
                data_type
            )
            return result

        try:
            # Get appropriate validator
            validator = self.validators[data_type]

            # Validate data
            result = validator.validate(data)

            # Update stats
            self.stats["total_validated"] += 1
            if result.valid:
                self.stats["valid_count"] += 1
                self.stats["by_type"][data_type]["valid"] += 1
            else:
                self.stats["invalid_count"] += 1
                self.stats["by_type"][data_type]["invalid"] += 1

            logger.debug(
                f"Validated {data_type} data: valid={result.valid}, "
                f"errors={len(result.errors)}, warnings={len(result.warnings)}"
            )

            return result

        except Exception as e:
            logger.error(f"Validation error for {data_type}: {e}", exc_info=True)
            result = ValidationResult(valid=False)
            result.add_error(
                "_system",
                f"Validation exception: {str(e)}",
                data_type
            )
            self.stats["total_validated"] += 1
            self.stats["invalid_count"] += 1
            self.stats["by_type"][data_type]["invalid"] += 1
            return result

    def validate_tutor(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate tutor data."""
        return self.validate(data, "tutor")

    def validate_session(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate session data."""
        return self.validate(data, "session")

    def validate_feedback(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate feedback data."""
        return self.validate(data, "feedback")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get validation statistics.

        Returns:
            Dictionary containing validation statistics
        """
        stats = self.stats.copy()

        # Add individual validator stats
        stats["validators"] = {}
        for data_type, validator in self.validators.items():
            stats["validators"][data_type] = validator.get_stats()

        return stats

    def reset_stats(self) -> None:
        """Reset all validation statistics."""
        self.stats = {
            "total_validated": 0,
            "valid_count": 0,
            "invalid_count": 0,
            "by_type": {
                "tutor": {"valid": 0, "invalid": 0},
                "session": {"valid": 0, "invalid": 0},
                "feedback": {"valid": 0, "invalid": 0},
            }
        }

        # Reset individual validator stats
        for validator in self.validators.values():
            validator.stats = {
                "total_validated": 0,
                "valid_count": 0,
                "invalid_count": 0,
            }
