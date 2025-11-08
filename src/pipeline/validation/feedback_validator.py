"""
Feedback data validator.

Validates student feedback data according to business rules and constraints.
"""

from typing import Any, Dict
import logging

from .base_validator import BaseValidator, ValidationResult

logger = logging.getLogger(__name__)


class FeedbackValidator(BaseValidator):
    """
    Validates student feedback data.

    Validation Rules:
    - Valid session_id reference (format check)
    - Ratings in range (1-5)
    - Valid boolean fields
    - First session fields present when is_first_session=true
    - Free text within length limits
    """

    def validate_data(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate feedback data.

        Args:
            data: Feedback data dictionary

        Returns:
            ValidationResult with validation status and errors
        """
        result = ValidationResult(valid=True, validated_data=data.copy())

        # Required fields validation
        required_fields = [
            "feedback_id",
            "session_id",
            "student_id",
            "tutor_id",
            "overall_rating",
            "is_first_session",
            "subject_knowledge_rating",
            "communication_rating",
            "patience_rating",
            "engagement_rating",
            "helpfulness_rating",
            "submitted_at",
            "created_at",
        ]
        self.validate_required_fields(data, required_fields, result)

        # Return early if required fields are missing
        if not result.valid:
            return result

        # Validate feedback_id
        self.validate_string_field(
            data, "feedback_id", result,
            min_length=1, max_length=50
        )

        # Validate session_id (format check)
        self.validate_string_field(
            data, "session_id", result,
            min_length=1, max_length=50
        )

        # Validate student_id (format check)
        self.validate_string_field(
            data, "student_id", result,
            min_length=1, max_length=50
        )

        # Validate tutor_id (format check)
        self.validate_string_field(
            data, "tutor_id", result,
            min_length=1, max_length=50
        )

        # Validate overall_rating (1-5)
        self.validate_int_field(
            data, "overall_rating", result,
            min_value=1, max_value=5
        )

        # Validate is_first_session
        self.validate_bool_field(data, "is_first_session", result)

        # Validate all rating fields (1-5)
        rating_fields = [
            "subject_knowledge_rating",
            "communication_rating",
            "patience_rating",
            "engagement_rating",
            "helpfulness_rating",
        ]

        for field in rating_fields:
            self.validate_int_field(
                data, field, result,
                min_value=1, max_value=5
            )

        # Validate free_text_feedback (optional)
        if "free_text_feedback" in data and data["free_text_feedback"] is not None:
            self.validate_string_field(
                data, "free_text_feedback", result,
                max_length=5000
            )

        # Validate timestamps
        self.validate_datetime_iso(data, "submitted_at", result, allow_future=False)
        self.validate_datetime_iso(data, "created_at", result, allow_future=False)

        # Validate first session specific fields
        if data.get("is_first_session") is True:
            # would_recommend should be present for first sessions
            if "would_recommend" not in data or data["would_recommend"] is None:
                result.add_error(
                    "would_recommend",
                    "Field 'would_recommend' is required for first session feedback",
                    None
                )
            else:
                self.validate_bool_field(data, "would_recommend", result)

            # improvement_areas should be present for first sessions
            if "improvement_areas" not in data or data["improvement_areas"] is None:
                result.add_warning(
                    "improvement_areas",
                    "Field 'improvement_areas' is recommended for first session feedback",
                    None
                )
            elif isinstance(data["improvement_areas"], list):
                self.validate_list_field(
                    data, "improvement_areas", result,
                    max_items=10,
                    item_type=str
                )

        # Business rules validation
        self._validate_business_rules(data, result)

        # Add metadata
        result.metadata = {
            "validator": "FeedbackValidator",
            "feedback_id": data.get("feedback_id"),
            "session_id": data.get("session_id"),
            "tutor_id": data.get("tutor_id"),
            "overall_rating": data.get("overall_rating"),
            "is_first_session": data.get("is_first_session"),
        }

        return result

    def _validate_business_rules(
        self,
        data: Dict[str, Any],
        result: ValidationResult
    ) -> None:
        """
        Validate business rules for feedback data.

        Args:
            data: Feedback data
            result: ValidationResult to add errors to
        """
        # Rule: Overall rating should be roughly consistent with individual ratings
        individual_ratings = [
            data.get("subject_knowledge_rating"),
            data.get("communication_rating"),
            data.get("patience_rating"),
            data.get("engagement_rating"),
            data.get("helpfulness_rating"),
        ]

        # Check if all individual ratings are present and valid
        if all(isinstance(r, int) and 1 <= r <= 5 for r in individual_ratings):
            avg_rating = sum(individual_ratings) / len(individual_ratings)
            overall_rating = data.get("overall_rating")

            if isinstance(overall_rating, int):
                # Overall rating should be within 1.5 points of average
                if abs(overall_rating - avg_rating) > 1.5:
                    result.add_warning(
                        "overall_rating",
                        f"Overall rating ({overall_rating}) differs significantly from "
                        f"average of individual ratings ({avg_rating:.2f})",
                        overall_rating
                    )

        # Rule: Low ratings should have feedback text
        overall_rating = data.get("overall_rating")
        free_text = data.get("free_text_feedback", "")

        if isinstance(overall_rating, int) and overall_rating <= 2:
            if not free_text or len(free_text.strip()) < 10:
                result.add_warning(
                    "free_text_feedback",
                    "Low ratings (1-2) should include detailed feedback text",
                    free_text
                )

        # Rule: First session with low rating should have improvement_areas
        if data.get("is_first_session") is True and isinstance(overall_rating, int):
            if overall_rating <= 3:
                improvement_areas = data.get("improvement_areas", [])
                if not improvement_areas or len(improvement_areas) == 0:
                    result.add_warning(
                        "improvement_areas",
                        "First sessions with rating <= 3 should include improvement areas",
                        improvement_areas
                    )

        # Rule: would_recommend should align with overall rating
        would_recommend = data.get("would_recommend")
        if would_recommend is not None and isinstance(overall_rating, int):
            if would_recommend is True and overall_rating < 3:
                result.add_warning(
                    "would_recommend",
                    f"would_recommend=True but overall_rating is {overall_rating}",
                    would_recommend
                )
            elif would_recommend is False and overall_rating >= 4:
                result.add_warning(
                    "would_recommend",
                    f"would_recommend=False but overall_rating is {overall_rating}",
                    would_recommend
                )

        # Rule: submitted_at should be after created_at
        if "submitted_at" in data and "created_at" in data:
            try:
                from datetime import datetime
                submitted = datetime.fromisoformat(
                    data["submitted_at"].replace("Z", "+00:00")
                )
                created = datetime.fromisoformat(
                    data["created_at"].replace("Z", "+00:00")
                )

                if submitted < created:
                    result.add_error(
                        "submitted_at",
                        "submitted_at cannot be before created_at",
                        data["submitted_at"]
                    )

            except (ValueError, AttributeError):
                # Date format errors already caught
                pass
