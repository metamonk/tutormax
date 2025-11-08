"""
Enrichment engine for coordinating data enrichment.

Routes data to appropriate enrichers and manages enrichment process.
"""

from typing import Any, Dict, Optional
import logging

from .base_enricher import EnrichmentResult
from .tutor_enricher import TutorEnricher
from .session_enricher import SessionEnricher
from .feedback_enricher import FeedbackEnricher

logger = logging.getLogger(__name__)


class EnrichmentEngine:
    """
    Enrichment engine that routes data to appropriate enrichers.

    Manages the enrichment process and provides a unified interface
    for enriching different data types.
    """

    def __init__(self):
        """Initialize enrichment engine with enrichers."""
        self.enrichers = {
            "tutor": TutorEnricher(),
            "session": SessionEnricher(),
            "feedback": FeedbackEnricher(),
        }

        self.stats = {
            "total_enriched": 0,
            "total_failed": 0,
            "by_type": {
                "tutor": {"success": 0, "failed": 0},
                "session": {"success": 0, "failed": 0},
                "feedback": {"success": 0, "failed": 0},
            },
        }

    def enrich(self, data: Dict[str, Any], data_type: str) -> EnrichmentResult:
        """
        Enrich data using appropriate enricher.

        Args:
            data: Data to enrich
            data_type: Type of data (tutor, session, feedback)

        Returns:
            EnrichmentResult
        """
        # Get enricher
        enricher = self.enrichers.get(data_type)

        if not enricher:
            logger.error(f"No enricher found for type: {data_type}")
            return EnrichmentResult(
                success=False,
                data=data,
                errors=[f"Unknown data type: {data_type}"],
            )

        # Enrich data
        result = enricher.enrich(data)

        # Update stats
        if result.success:
            self.stats["total_enriched"] += 1
            self.stats["by_type"][data_type]["success"] += 1
        else:
            self.stats["total_failed"] += 1
            self.stats["by_type"][data_type]["failed"] += 1

        return result

    def get_stats(self) -> Dict[str, Any]:
        """
        Get enrichment statistics.

        Returns:
            Statistics dictionary
        """
        stats = self.stats.copy()

        # Add enricher-specific stats
        for data_type, enricher in self.enrichers.items():
            stats["by_type"][data_type]["enricher_stats"] = enricher.get_stats()

        return stats

    def reset_stats(self) -> None:
        """Reset all statistics."""
        self.stats = {
            "total_enriched": 0,
            "total_failed": 0,
            "by_type": {
                "tutor": {"success": 0, "failed": 0},
                "session": {"success": 0, "failed": 0},
                "feedback": {"success": 0, "failed": 0},
            },
        }

        for enricher in self.enrichers.values():
            enricher.reset_stats()
