"""
Tutor performance evaluation module.

This module contains the core performance evaluation engine components:
- PerformanceCalculator: Calculates performance metrics for tutors
- DailyMetricsAggregator: Batch processes daily metrics for all tutors
- PerformanceTier assignment logic
"""

from .performance_calculator import PerformanceCalculator, PerformanceMetrics
from .daily_aggregator import (
    DailyMetricsAggregator,
    AggregationResult,
    AggregationSummary,
    run_daily_aggregation,
)

__all__ = [
    "PerformanceCalculator",
    "PerformanceMetrics",
    "DailyMetricsAggregator",
    "AggregationResult",
    "AggregationSummary",
    "run_daily_aggregation",
]
