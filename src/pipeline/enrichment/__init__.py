"""
Data enrichment pipeline module.

This module handles enrichment of validated data with derived fields
and additional context before database persistence.
"""

from .base_enricher import BaseEnricher, EnrichmentResult
from .tutor_enricher import TutorEnricher
from .session_enricher import SessionEnricher
from .feedback_enricher import FeedbackEnricher
from .enrichment_engine import EnrichmentEngine

__all__ = [
    "BaseEnricher",
    "EnrichmentResult",
    "TutorEnricher",
    "SessionEnricher",
    "FeedbackEnricher",
    "EnrichmentEngine",
]
