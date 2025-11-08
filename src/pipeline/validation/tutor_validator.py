"""
Tutor data validator.

Validates tutor profile data according to business rules and constraints.
"""

from typing import Any, Dict
import logging

from .base_validator import BaseValidator, ValidationResult

logger = logging.getLogger(__name__)


class TutorValidator(BaseValidator):
    """
    Validates tutor profile data.

    Validation Rules:
    - Email format validation
    - Age range (22-65)
    - Tenure >= 0
    - Baseline sessions (5-30)
    - Valid behavioral archetype
    - Valid subjects
    - Valid status
    - Valid subject type
    """

    # Valid enum values
    VALID_ARCHETYPES = [
        "high_performer",
        "at_risk",
        "new_tutor",
        "steady",
        "churner"
    ]

    VALID_SUBJECT_TYPES = ["STEM", "Language", "TestPrep"]

    VALID_STATUSES = ["active", "inactive", "suspended"]

    # Valid subjects
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
        Validate tutor profile data.

        Args:
            data: Tutor profile dictionary

        Returns:
            ValidationResult with validation status and errors
        """
        result = ValidationResult(valid=True, validated_data=data.copy())

        # Required fields validation
        required_fields = [
            "tutor_id",
            "name",
            "email",
            "age",
            "location",
            "education_level",
            "subjects",
            "subject_type",
            "onboarding_date",
            "tenure_days",
            "behavioral_archetype",
            "baseline_sessions_per_week",
            "created_at",
            "updated_at",
        ]
        self.validate_required_fields(data, required_fields, result)

        # Return early if required fields are missing
        if not result.valid:
            return result

        # Validate tutor_id
        self.validate_string_field(
            data, "tutor_id", result,
            min_length=1, max_length=50
        )

        # Validate name
        self.validate_string_field(
            data, "name", result,
            min_length=1, max_length=255
        )

        # Validate email
        self.validate_email(data, "email", result)

        # Validate age (22-65 per requirements)
        self.validate_int_field(
            data, "age", result,
            min_value=22, max_value=65
        )

        # Validate location
        self.validate_string_field(
            data, "location", result,
            min_length=1, max_length=255
        )

        # Validate education_level
        self.validate_string_field(
            data, "education_level", result,
            min_length=1, max_length=100
        )

        # Validate subjects
        self.validate_list_field(
            data, "subjects", result,
            min_items=1, max_items=10,
            item_type=str
        )

        # Validate subject values
        if "subjects" in data and isinstance(data["subjects"], list):
            for subject in data["subjects"]:
                if subject not in self.VALID_SUBJECTS:
                    result.add_error(
                        "subjects",
                        f"Invalid subject: '{subject}'. Must be one of {self.VALID_SUBJECTS}",
                        subject
                    )

        # Validate subject_type
        self.validate_string_field(
            data, "subject_type", result,
            allowed_values=self.VALID_SUBJECT_TYPES
        )

        # Validate dates
        self.validate_datetime_iso(
            data, "onboarding_date", result,
            allow_future=False
        )
        self.validate_datetime_iso(
            data, "created_at", result,
            allow_future=False
        )
        self.validate_datetime_iso(
            data, "updated_at", result,
            allow_future=False
        )

        # Validate tenure_days
        self.validate_int_field(
            data, "tenure_days", result,
            min_value=0
        )

        # Validate behavioral_archetype
        self.validate_string_field(
            data, "behavioral_archetype", result,
            allowed_values=self.VALID_ARCHETYPES
        )

        # Validate baseline_sessions_per_week (5-30 per requirements)
        self.validate_int_field(
            data, "baseline_sessions_per_week", result,
            min_value=5, max_value=30
        )

        # Validate status (optional field)
        if "status" in data:
            self.validate_string_field(
                data, "status", result,
                allowed_values=self.VALID_STATUSES
            )

        # Business rule: Check date consistency
        if "onboarding_date" in data and "created_at" in data:
            try:
                from datetime import datetime
                onboarding = datetime.fromisoformat(
                    data["onboarding_date"].replace("Z", "+00:00")
                )
                created = datetime.fromisoformat(
                    data["created_at"].replace("Z", "+00:00")
                )

                if created < onboarding:
                    result.add_warning(
                        "created_at",
                        "created_at is before onboarding_date",
                        data["created_at"]
                    )
            except (ValueError, AttributeError):
                # Date format errors already caught above
                pass

        # Add metadata
        result.metadata = {
            "validator": "TutorValidator",
            "tutor_id": data.get("tutor_id"),
            "behavioral_archetype": data.get("behavioral_archetype"),
        }

        return result
