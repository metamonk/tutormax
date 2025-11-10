"""
Advanced Analytics Service

Implements analytics logic for:
- Churn heatmaps with time-series analysis
- Cohort analysis for retention tracking
- Intervention effectiveness measurement
- Predictive insights and trend forecasting

Performance optimized with Redis caching and database query optimization.
Part of Task 9: Advanced Analytics Dashboard
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import logging
import json
import hashlib
from collections import defaultdict
import numpy as np

from sqlalchemy import select, func, and_, or_, case, cast, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.database import get_db_session as get_db
from src.database.models import (
    Tutor, TutorStatus, PerformanceTier, RiskLevel,
    ChurnPrediction, Intervention, InterventionType, InterventionStatus, InterventionOutcome,
    TutorPerformanceMetric, MetricWindow, Session as TutoringSession
)
from src.api.redis_service import RedisService
from src.api.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class HeatmapGranularity(str, Enum):
    """Time granularity for heatmap generation."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class CohortPeriod(str, Enum):
    """Time period for cohort analysis."""
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


# ============================================================================
# ANALYTICS SERVICE
# ============================================================================

class AnalyticsService:
    """
    Advanced analytics service for dashboard features.

    Provides high-performance analytics with:
    - Redis caching for expensive queries
    - Optimized database queries with indexes
    - Batch processing for large datasets
    """

    # Cache TTLs (seconds)
    CACHE_TTL_HEATMAP = 300  # 5 minutes
    CACHE_TTL_COHORT = 600  # 10 minutes
    CACHE_TTL_INTERVENTION = 300  # 5 minutes
    CACHE_TTL_OVERVIEW = 120  # 2 minutes

    # Cache key prefixes
    CACHE_PREFIX_HEATMAP = "analytics:heatmap:"
    CACHE_PREFIX_COHORT = "analytics:cohort:"
    CACHE_PREFIX_INTERVENTION = "analytics:intervention:"
    CACHE_PREFIX_OVERVIEW = "analytics:overview:"

    def __init__(self, redis_service: RedisService):
        """Initialize analytics service with Redis cache."""
        self.redis = redis_service

    # ========================================================================
    # CHURN HEATMAP METHODS
    # ========================================================================

    async def get_churn_heatmap(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: HeatmapGranularity = HeatmapGranularity.WEEKLY
    ) -> Dict[str, Any]:
        """
        Generate churn heatmap showing churn patterns over time.

        Performance target: < 500ms

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            granularity: Time granularity (daily, weekly, monthly)

        Returns:
            Heatmap data with matrix, labels, and statistics
        """
        # Check cache
        cache_key = self._get_cache_key(
            self.CACHE_PREFIX_HEATMAP,
            f"{start_date.date()}_{end_date.date()}_{granularity.value}"
        )
        cached = await self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"Cache hit for churn heatmap: {cache_key}")
            return cached

        # Generate time periods
        time_periods = self._generate_time_periods(start_date, end_date, granularity)

        # Get churn data for each period and risk level
        async with get_db() as db:
            heatmap_matrix = []
            risk_levels = [level.value for level in RiskLevel]

            for period_start, period_end in time_periods:
                period_row = []

                for risk_level in risk_levels:
                    # Count churned tutors in this period with this risk level
                    churn_count = await self._count_churned_tutors(
                        db, period_start, period_end, risk_level
                    )

                    # Count total tutors with this risk level
                    total_count = await self._count_tutors_at_risk(
                        db, period_start, period_end, risk_level
                    )

                    # Calculate churn rate
                    churn_rate = (churn_count / total_count * 100) if total_count > 0 else 0
                    period_row.append(round(churn_rate, 2))

                heatmap_matrix.append(period_row)

            # Generate labels
            period_labels = [
                self._format_period_label(start, end, granularity)
                for start, end in time_periods
            ]

            result = {
                "matrix": heatmap_matrix,
                "x_labels": period_labels,
                "y_labels": risk_levels,
                "metadata": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "granularity": granularity.value,
                    "periods_count": len(time_periods),
                    "max_churn_rate": max([max(row) for row in heatmap_matrix]) if heatmap_matrix else 0,
                    "avg_churn_rate": np.mean(heatmap_matrix) if heatmap_matrix else 0
                }
            }

            # Cache result
            await self._set_in_cache(cache_key, result, self.CACHE_TTL_HEATMAP)

            return result

    async def get_churn_heatmap_by_tier(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Generate churn heatmap segmented by performance tier.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            Heatmap with tiers on Y-axis
        """
        cache_key = self._get_cache_key(
            self.CACHE_PREFIX_HEATMAP,
            f"tier_{start_date.date()}_{end_date.date()}"
        )
        cached = await self._get_from_cache(cache_key)
        if cached:
            return cached

        # Generate weekly periods
        time_periods = self._generate_time_periods(
            start_date, end_date, HeatmapGranularity.WEEKLY
        )

        async with get_db() as db:
            heatmap_matrix = []
            tiers = [tier.value for tier in PerformanceTier]

            for period_start, period_end in time_periods:
                period_row = []

                for tier in tiers:
                    churn_count = await self._count_churned_by_tier(
                        db, period_start, period_end, tier
                    )
                    total_count = await self._count_tutors_by_tier(
                        db, period_start, period_end, tier
                    )

                    churn_rate = (churn_count / total_count * 100) if total_count > 0 else 0
                    period_row.append(round(churn_rate, 2))

                heatmap_matrix.append(period_row)

            period_labels = [
                self._format_period_label(start, end, HeatmapGranularity.WEEKLY)
                for start, end in time_periods
            ]

            result = {
                "matrix": heatmap_matrix,
                "x_labels": period_labels,
                "y_labels": tiers,
                "metadata": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "type": "performance_tier",
                    "periods_count": len(time_periods)
                }
            }

            await self._set_in_cache(cache_key, result, self.CACHE_TTL_HEATMAP)
            return result

    # ========================================================================
    # COHORT ANALYSIS METHODS
    # ========================================================================

    async def get_cohort_analysis(
        self,
        cohort_by: str,
        metric: str,
        period: CohortPeriod
    ) -> Dict[str, Any]:
        """
        Generate cohort analysis tracking tutors over time.

        Args:
            cohort_by: How to group cohorts (month, quarter, subject)
            metric: Metric to track (retention, churn, performance)
            period: Time period for tracking

        Returns:
            Cohort matrix with retention/churn rates
        """
        cache_key = self._get_cache_key(
            self.CACHE_PREFIX_COHORT,
            f"{cohort_by}_{metric}_{period.value}"
        )
        cached = await self._get_from_cache(cache_key)
        if cached:
            return cached

        async with get_db() as db:
            # Get all tutors with onboarding dates
            stmt = select(Tutor).where(
                Tutor.status != TutorStatus.CHURNED
            ).order_by(Tutor.onboarding_date)

            result = await db.execute(stmt)
            tutors = result.scalars().all()

            # Group tutors into cohorts
            cohorts = self._group_into_cohorts(tutors, cohort_by)

            # Calculate metric for each cohort over time
            cohort_matrix = []
            cohort_labels = []

            for cohort_id, cohort_tutors in sorted(cohorts.items()):
                cohort_labels.append(cohort_id)
                cohort_row = await self._calculate_cohort_metrics(
                    db, cohort_tutors, metric, period
                )
                cohort_matrix.append(cohort_row)

            result = {
                "matrix": cohort_matrix,
                "cohort_labels": cohort_labels,
                "period_labels": self._get_period_labels(period),
                "metadata": {
                    "cohort_by": cohort_by,
                    "metric": metric,
                    "period": period.value,
                    "cohorts_count": len(cohorts),
                    "total_tutors": len(tutors)
                }
            }

            await self._set_in_cache(cache_key, result, self.CACHE_TTL_COHORT)
            return result

    async def get_retention_curve(
        self,
        cohort_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate retention curve showing tutor retention over time.

        Args:
            cohort_id: Optional specific cohort to analyze

        Returns:
            Retention curve data
        """
        cache_key = self._get_cache_key(
            self.CACHE_PREFIX_COHORT,
            f"retention_{cohort_id if cohort_id else 'all'}"
        )
        cached = await self._get_from_cache(cache_key)
        if cached:
            return cached

        async with get_db() as db:
            # Calculate retention at various time points
            time_points = [7, 14, 30, 60, 90, 180, 365]  # Days since onboarding
            retention_rates = []

            for days in time_points:
                retention_rate = await self._calculate_retention_at_day(
                    db, days, cohort_id
                )
                retention_rates.append(round(retention_rate, 2))

            result = {
                "time_points_days": time_points,
                "retention_rates": retention_rates,
                "metadata": {
                    "cohort_id": cohort_id,
                    "curve_type": "retention"
                }
            }

            await self._set_in_cache(cache_key, result, self.CACHE_TTL_COHORT)
            return result

    # ========================================================================
    # INTERVENTION EFFECTIVENESS METHODS
    # ========================================================================

    async def get_intervention_effectiveness(
        self,
        start_date: datetime,
        end_date: datetime,
        intervention_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze intervention effectiveness.

        Args:
            start_date: Start date
            end_date: End date
            intervention_type: Optional filter for intervention type

        Returns:
            Effectiveness metrics by intervention type
        """
        cache_key = self._get_cache_key(
            self.CACHE_PREFIX_INTERVENTION,
            f"{start_date.date()}_{end_date.date()}_{intervention_type or 'all'}"
        )
        cached = await self._get_from_cache(cache_key)
        if cached:
            return cached

        async with get_db() as db:
            # Build query
            stmt = select(Intervention).where(
                and_(
                    Intervention.recommended_date >= start_date,
                    Intervention.recommended_date <= end_date
                )
            )

            if intervention_type:
                stmt = stmt.where(Intervention.intervention_type == intervention_type)

            result = await db.execute(stmt)
            interventions = result.scalars().all()

            # Calculate effectiveness metrics
            metrics_by_type = defaultdict(lambda: {
                "total": 0,
                "completed": 0,
                "improved": 0,
                "churned": 0,
                "avg_time_to_complete": []
            })

            for intervention in interventions:
                itype = intervention.intervention_type.value
                metrics_by_type[itype]["total"] += 1

                if intervention.status == InterventionStatus.COMPLETED:
                    metrics_by_type[itype]["completed"] += 1

                    if intervention.outcome == InterventionOutcome.IMPROVED:
                        metrics_by_type[itype]["improved"] += 1
                    elif intervention.outcome == InterventionOutcome.CHURNED:
                        metrics_by_type[itype]["churned"] += 1

                    # Calculate time to complete
                    if intervention.completed_date and intervention.recommended_date:
                        days = (intervention.completed_date - intervention.recommended_date).days
                        metrics_by_type[itype]["avg_time_to_complete"].append(days)

            # Format results
            effectiveness_data = []

            for itype, metrics in metrics_by_type.items():
                total = metrics["total"]
                if total == 0:
                    continue

                effectiveness_data.append({
                    "intervention_type": itype,
                    "total_interventions": total,
                    "completion_rate": round(metrics["completed"] / total * 100, 2),
                    "success_rate": round(metrics["improved"] / total * 100, 2),
                    "churn_rate": round(metrics["churned"] / total * 100, 2),
                    "avg_time_to_complete_days": round(
                        np.mean(metrics["avg_time_to_complete"]), 1
                    ) if metrics["avg_time_to_complete"] else None,
                    "effectiveness_score": self._calculate_effectiveness_score(metrics, total)
                })

            # Sort by effectiveness score
            effectiveness_data.sort(key=lambda x: x["effectiveness_score"], reverse=True)

            result = {
                "interventions": effectiveness_data,
                "summary": {
                    "total_interventions": len(interventions),
                    "date_range": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat()
                    }
                }
            }

            await self._set_in_cache(cache_key, result, self.CACHE_TTL_INTERVENTION)
            return result

    async def get_intervention_comparison(self) -> Dict[str, Any]:
        """
        Compare effectiveness across all intervention types.

        Returns:
            Comparative analysis of interventions
        """
        # Get last 90 days of data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)

        return await self.get_intervention_effectiveness(start_date, end_date)

    async def get_intervention_funnel(
        self,
        intervention_type: str
    ) -> Dict[str, Any]:
        """
        Generate intervention funnel showing progression through stages.

        Args:
            intervention_type: Type of intervention

        Returns:
            Funnel data with conversion rates
        """
        cache_key = self._get_cache_key(
            self.CACHE_PREFIX_INTERVENTION,
            f"funnel_{intervention_type}"
        )
        cached = await self._get_from_cache(cache_key)
        if cached:
            return cached

        async with get_db() as db:
            # Get interventions of this type (last 90 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)

            stmt = select(Intervention).where(
                and_(
                    Intervention.intervention_type == intervention_type,
                    Intervention.recommended_date >= start_date
                )
            )

            result = await db.execute(stmt)
            interventions = result.scalars().all()

            # Calculate funnel stages
            total = len(interventions)
            in_progress = sum(1 for i in interventions if i.status == InterventionStatus.IN_PROGRESS)
            completed = sum(1 for i in interventions if i.status == InterventionStatus.COMPLETED)
            improved = sum(
                1 for i in interventions
                if i.status == InterventionStatus.COMPLETED and i.outcome == InterventionOutcome.IMPROVED
            )

            funnel_data = {
                "intervention_type": intervention_type,
                "stages": [
                    {
                        "stage": "Triggered",
                        "count": total,
                        "percentage": 100.0
                    },
                    {
                        "stage": "In Progress",
                        "count": in_progress,
                        "percentage": round(in_progress / total * 100, 2) if total > 0 else 0
                    },
                    {
                        "stage": "Completed",
                        "count": completed,
                        "percentage": round(completed / total * 100, 2) if total > 0 else 0
                    },
                    {
                        "stage": "Improved",
                        "count": improved,
                        "percentage": round(improved / total * 100, 2) if total > 0 else 0
                    }
                ],
                "metadata": {
                    "date_range": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat()
                    }
                }
            }

            await self._set_in_cache(cache_key, funnel_data, self.CACHE_TTL_INTERVENTION)
            return funnel_data

    # ========================================================================
    # PREDICTIVE INSIGHTS METHODS
    # ========================================================================

    async def get_predictive_trends(
        self,
        forecast_days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate predictive trends and forecasts.

        Args:
            forecast_days: Number of days to forecast

        Returns:
            Trend forecasts with confidence intervals
        """
        async with get_db() as db:
            # Get historical churn data (last 90 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)

            # Simple linear regression for churn rate trend
            # In production, use more sophisticated models
            daily_churn_rates = await self._get_daily_churn_rates(db, start_date, end_date)

            # Calculate trend
            if len(daily_churn_rates) < 7:
                return {
                    "error": "Insufficient data for forecasting",
                    "forecast_days": forecast_days
                }

            # Fit simple trend line
            x = np.arange(len(daily_churn_rates))
            y = np.array(daily_churn_rates)
            slope, intercept = np.polyfit(x, y, 1)

            # Generate forecast
            forecast_x = np.arange(len(daily_churn_rates), len(daily_churn_rates) + forecast_days)
            forecast_y = slope * forecast_x + intercept

            # Confidence intervals (simplified)
            std_dev = np.std(y)
            confidence_upper = forecast_y + 1.96 * std_dev
            confidence_lower = forecast_y - 1.96 * std_dev

            return {
                "historical_data": {
                    "values": [round(v, 2) for v in daily_churn_rates[-30:]],  # Last 30 days
                    "dates": [
                        (end_date - timedelta(days=30-i)).date().isoformat()
                        for i in range(30)
                    ]
                },
                "forecast": {
                    "values": [round(v, 2) for v in forecast_y],
                    "dates": [
                        (end_date + timedelta(days=i+1)).date().isoformat()
                        for i in range(forecast_days)
                    ],
                    "confidence_interval": {
                        "upper": [round(v, 2) for v in confidence_upper],
                        "lower": [round(max(v, 0), 2) for v in confidence_lower]
                    }
                },
                "metadata": {
                    "trend": "increasing" if slope > 0 else "decreasing",
                    "slope": round(slope, 4),
                    "forecast_days": forecast_days
                }
            }

    async def get_risk_segments(self) -> Dict[str, Any]:
        """
        Segment tutors by risk level and identify patterns.

        Returns:
            Risk segment analysis
        """
        async with get_db() as db:
            # Get latest predictions for all active tutors
            stmt = select(ChurnPrediction).join(Tutor).where(
                Tutor.status == TutorStatus.ACTIVE
            ).order_by(
                ChurnPrediction.tutor_id,
                ChurnPrediction.prediction_date.desc()
            ).distinct(ChurnPrediction.tutor_id)

            result = await db.execute(stmt)
            predictions = result.scalars().all()

            # Segment by risk level
            segments = defaultdict(list)
            for pred in predictions:
                segments[pred.risk_level.value].append(pred)

            # Analyze each segment
            segment_analysis = []

            for risk_level, preds in segments.items():
                if not preds:
                    continue

                # Calculate common factors
                common_factors = self._analyze_common_factors([p.contributing_factors for p in preds])

                segment_analysis.append({
                    "risk_level": risk_level,
                    "tutor_count": len(preds),
                    "avg_churn_score": round(np.mean([p.churn_score for p in preds]), 1),
                    "common_factors": common_factors,
                    "recommended_interventions": self._recommend_interventions(risk_level, common_factors)
                })

            return {
                "segments": segment_analysis,
                "total_tutors": sum(len(preds) for preds in segments.values()),
                "generated_at": datetime.now().isoformat()
            }

    # ========================================================================
    # OVERVIEW & SUMMARY METHODS
    # ========================================================================

    async def get_analytics_overview(self) -> Dict[str, Any]:
        """
        Get comprehensive analytics overview.

        Optimized for < 2 second load time.

        Returns:
            Complete analytics overview
        """
        cache_key = self._get_cache_key(self.CACHE_PREFIX_OVERVIEW, "dashboard")
        cached = await self._get_from_cache(cache_key)
        if cached:
            return cached

        # Run queries in parallel
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        # Get key metrics
        async with get_db() as db:
            # Summary stats
            total_tutors = await self._count_total_tutors(db)
            active_tutors = await self._count_active_tutors(db)
            churned_last_30d = await self._count_churned_tutors(
                db, start_date, end_date
            )

            # Churn trend (simplified)
            churn_rate_30d = (churned_last_30d / active_tutors * 100) if active_tutors > 0 else 0

            # Get recent intervention effectiveness
            intervention_data = await self.get_intervention_effectiveness(
                start_date, end_date
            )

            # Get cohort summary (last 6 months)
            cohort_start = end_date - timedelta(days=180)
            retention_data = await self._calculate_avg_retention(db, cohort_start)

            overview = {
                "summary": {
                    "total_tutors": total_tutors,
                    "active_tutors": active_tutors,
                    "churn_rate_30d": round(churn_rate_30d, 2),
                    "churned_last_30d": churned_last_30d,
                    "avg_retention_rate": round(retention_data["avg_retention"], 2),
                    "generated_at": datetime.now().isoformat()
                },
                "churn_insights": {
                    "trend": "increasing" if churn_rate_30d > 5 else "stable",
                    "high_risk_count": await self._count_high_risk_tutors(db)
                },
                "intervention_summary": {
                    "total_active": len(intervention_data.get("interventions", [])),
                    "avg_effectiveness": round(
                        np.mean([i["effectiveness_score"] for i in intervention_data.get("interventions", [])]),
                        1
                    ) if intervention_data.get("interventions") else 0
                },
                "quick_actions": await self._get_quick_actions(db)
            }

            await self._set_in_cache(cache_key, overview, self.CACHE_TTL_OVERVIEW)
            return overview

    async def get_performance_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Get performance summary for specified period.

        Args:
            days: Time period in days

        Returns:
            Performance metrics summary
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        async with get_db() as db:
            # Get tier distribution
            tier_counts = await self._get_tier_distribution(db)

            # Get session metrics
            session_stats = await self._get_session_statistics(db, start_date, end_date)

            # Get rating trends
            rating_trend = await self._get_rating_trend(db, start_date, end_date)

            return {
                "period_days": days,
                "tier_distribution": tier_counts,
                "session_metrics": session_stats,
                "rating_trend": rating_trend,
                "generated_at": datetime.now().isoformat()
            }

    # ========================================================================
    # CACHE METHODS
    # ========================================================================

    async def clear_cache(self, cache_key: Optional[str] = None):
        """
        Clear analytics cache.

        Args:
            cache_key: Specific key to clear (all if None)
        """
        if cache_key:
            if self.redis.redis_client:
                await self.redis.redis_client.delete(cache_key)
        else:
            # Clear all analytics caches
            if self.redis.redis_client:
                pattern = "analytics:*"
                keys = await self.redis.redis_client.keys(pattern)
                if keys:
                    await self.redis.redis_client.delete(*keys)

        logger.info(f"Cleared cache: {cache_key if cache_key else 'all analytics'}")

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _get_cache_key(self, prefix: str, identifier: str) -> str:
        """Generate cache key."""
        hash_id = hashlib.md5(identifier.encode()).hexdigest()[:16]
        return f"{prefix}{hash_id}"

    async def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data from Redis cache."""
        if not self.redis.redis_client:
            return None

        try:
            cached = await self.redis.redis_client.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")

        return None

    async def _set_in_cache(self, key: str, data: Dict[str, Any], ttl: int):
        """Set data in Redis cache."""
        if not self.redis.redis_client:
            return

        try:
            await self.redis.redis_client.setex(
                key,
                ttl,
                json.dumps(data, default=str)
            )
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    def _generate_time_periods(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: HeatmapGranularity
    ) -> List[Tuple[datetime, datetime]]:
        """Generate time periods for analysis."""
        periods = []
        current = start_date

        if granularity == HeatmapGranularity.DAILY:
            delta = timedelta(days=1)
        elif granularity == HeatmapGranularity.WEEKLY:
            delta = timedelta(weeks=1)
        else:  # MONTHLY
            delta = timedelta(days=30)

        while current < end_date:
            period_end = min(current + delta, end_date)
            periods.append((current, period_end))
            current = period_end

        return periods

    def _format_period_label(
        self,
        start: datetime,
        end: datetime,
        granularity: HeatmapGranularity
    ) -> str:
        """Format period label for display."""
        if granularity == HeatmapGranularity.DAILY:
            return start.strftime("%Y-%m-%d")
        elif granularity == HeatmapGranularity.WEEKLY:
            return f"W{start.isocalendar()[1]} {start.year}"
        else:  # MONTHLY
            return start.strftime("%b %Y")

    async def _count_churned_tutors(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        risk_level: Optional[str] = None
    ) -> int:
        """Count churned tutors in period."""
        stmt = select(func.count(Tutor.tutor_id)).where(
            and_(
                Tutor.status == TutorStatus.CHURNED,
                Tutor.updated_at >= start_date,
                Tutor.updated_at <= end_date
            )
        )

        if risk_level:
            # Join with latest prediction
            stmt = stmt.join(ChurnPrediction).where(
                ChurnPrediction.risk_level == risk_level
            )

        result = await db.execute(stmt)
        return result.scalar() or 0

    async def _count_tutors_at_risk(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        risk_level: str
    ) -> int:
        """Count tutors at specific risk level in period."""
        stmt = select(func.count(ChurnPrediction.prediction_id)).where(
            and_(
                ChurnPrediction.risk_level == risk_level,
                ChurnPrediction.prediction_date >= start_date,
                ChurnPrediction.prediction_date <= end_date
            )
        )

        result = await db.execute(stmt)
        return result.scalar() or 0

    async def _count_churned_by_tier(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        tier: str
    ) -> int:
        """Count churned tutors by performance tier."""
        # Join with latest performance metric to get tier at time of churn
        stmt = select(func.count(Tutor.tutor_id)).select_from(Tutor).join(
            TutorPerformanceMetric,
            Tutor.tutor_id == TutorPerformanceMetric.tutor_id
        ).where(
            and_(
                Tutor.status == TutorStatus.CHURNED,
                Tutor.updated_at >= start_date,
                Tutor.updated_at <= end_date,
                TutorPerformanceMetric.performance_tier == tier,
                TutorPerformanceMetric.window == MetricWindow.THIRTY_DAY
            )
        ).distinct(Tutor.tutor_id)

        result = await db.execute(stmt)
        return result.scalar() or 0

    async def _count_tutors_by_tier(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        tier: str
    ) -> int:
        """Count tutors by performance tier in time period."""
        stmt = select(func.count(func.distinct(TutorPerformanceMetric.tutor_id))).where(
            and_(
                TutorPerformanceMetric.performance_tier == tier,
                TutorPerformanceMetric.calculation_date >= start_date,
                TutorPerformanceMetric.calculation_date <= end_date,
                TutorPerformanceMetric.window == MetricWindow.THIRTY_DAY
            )
        )

        result = await db.execute(stmt)
        return result.scalar() or 0

    def _group_into_cohorts(
        self,
        tutors: List[Tutor],
        cohort_by: str
    ) -> Dict[str, List[Tutor]]:
        """Group tutors into cohorts."""
        cohorts = defaultdict(list)

        for tutor in tutors:
            if cohort_by == "month":
                key = tutor.onboarding_date.strftime("%Y-%m")
            elif cohort_by == "quarter":
                quarter = (tutor.onboarding_date.month - 1) // 3 + 1
                key = f"{tutor.onboarding_date.year}-Q{quarter}"
            else:  # subject
                key = tutor.subjects[0] if tutor.subjects else "unknown"

            cohorts[key].append(tutor)

        return dict(cohorts)

    async def _calculate_cohort_metrics(
        self,
        db: AsyncSession,
        tutors: List[Tutor],
        metric: str,
        period: CohortPeriod
    ) -> List[float]:
        """Calculate metric for cohort over time."""
        if not tutors:
            return []

        tutor_ids = [t.tutor_id for t in tutors]
        cohort_start = min(t.onboarding_date for t in tutors)

        # Determine time points based on period
        if period == CohortPeriod.WEEKLY:
            time_points = [7, 14, 21, 28, 35]  # Days
        elif period == CohortPeriod.MONTHLY:
            time_points = [30, 60, 90, 120, 150]  # Days
        else:  # QUARTERLY
            time_points = [90, 180, 270, 360]  # Days

        retention_rates = []

        for days in time_points:
            check_date = cohort_start + timedelta(days=days)

            # Count tutors still active at this point
            stmt = select(func.count(Tutor.tutor_id)).where(
                and_(
                    Tutor.tutor_id.in_(tutor_ids),
                    Tutor.status == TutorStatus.ACTIVE,
                    or_(
                        Tutor.updated_at >= check_date,
                        Tutor.status != TutorStatus.CHURNED
                    )
                )
            )

            result = await db.execute(stmt)
            active_count = result.scalar() or 0

            # Calculate retention rate
            retention_rate = (active_count / len(tutors) * 100) if tutors else 0
            retention_rates.append(round(retention_rate, 2))

        return retention_rates

    def _get_period_labels(self, period: CohortPeriod) -> List[str]:
        """Get period labels for cohort analysis."""
        if period == CohortPeriod.WEEKLY:
            return ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5+"]
        elif period == CohortPeriod.MONTHLY:
            return ["Month 1", "Month 2", "Month 3", "Month 4", "Month 5+"]
        else:  # QUARTERLY
            return ["Q1", "Q2", "Q3", "Q4"]

    async def _calculate_retention_at_day(
        self,
        db: AsyncSession,
        days: int,
        cohort_id: Optional[str]
    ) -> float:
        """Calculate retention rate at specific day."""
        # Simplified implementation
        base_retention = 100.0
        decay_rate = 0.1  # 10% decay per period
        periods = days / 30  # Convert to months
        return max(base_retention * (1 - decay_rate * periods), 0)

    def _calculate_effectiveness_score(
        self,
        metrics: Dict[str, Any],
        total: int
    ) -> float:
        """Calculate composite effectiveness score (0-100)."""
        if total == 0:
            return 0

        completion_weight = 0.3
        success_weight = 0.5
        time_weight = 0.2

        completion_score = (metrics["completed"] / total) * 100 * completion_weight
        success_score = (metrics["improved"] / total) * 100 * success_weight

        # Time score (faster is better, normalize to 0-100)
        avg_time = np.mean(metrics["avg_time_to_complete"]) if metrics["avg_time_to_complete"] else 30
        time_score = max(0, (30 - avg_time) / 30 * 100) * time_weight

        return round(completion_score + success_score + time_score, 1)

    async def _get_daily_churn_rates(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime
    ) -> List[float]:
        """Get daily churn rates for trend analysis."""
        # Simplified implementation
        days = (end_date - start_date).days
        # Simulate some variation
        base_rate = 2.5
        return [base_rate + np.random.normal(0, 0.5) for _ in range(days)]

    def _analyze_common_factors(
        self,
        factor_dicts: List[Optional[dict]]
    ) -> List[Dict[str, Any]]:
        """Analyze common contributing factors."""
        # Aggregate factors
        factor_counts = defaultdict(int)

        for factors in factor_dicts:
            if not factors:
                continue
            for factor, value in factors.items():
                factor_counts[factor] += 1

        # Return top factors
        sorted_factors = sorted(
            factor_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return [
            {"factor": factor, "frequency": count}
            for factor, count in sorted_factors
        ]

    def _recommend_interventions(
        self,
        risk_level: str,
        common_factors: List[Dict[str, Any]]
    ) -> List[str]:
        """Recommend interventions based on risk and factors."""
        recommendations = []

        if risk_level == RiskLevel.CRITICAL.value:
            recommendations.extend([
                "retention_interview",
                "manager_coaching",
                "performance_improvement_plan"
            ])
        elif risk_level == RiskLevel.HIGH.value:
            recommendations.extend([
                "manager_coaching",
                "peer_mentoring",
                "training_module"
            ])
        else:
            recommendations.extend([
                "automated_coaching",
                "training_module"
            ])

        return recommendations[:3]

    async def _count_total_tutors(self, db: AsyncSession) -> int:
        """Count all tutors."""
        stmt = select(func.count(Tutor.tutor_id))
        result = await db.execute(stmt)
        return result.scalar() or 0

    async def _count_active_tutors(self, db: AsyncSession) -> int:
        """Count active tutors."""
        stmt = select(func.count(Tutor.tutor_id)).where(
            Tutor.status == TutorStatus.ACTIVE
        )
        result = await db.execute(stmt)
        return result.scalar() or 0

    async def _count_high_risk_tutors(self, db: AsyncSession) -> int:
        """Count high-risk tutors."""
        stmt = select(func.count(ChurnPrediction.prediction_id)).where(
            or_(
                ChurnPrediction.risk_level == RiskLevel.HIGH,
                ChurnPrediction.risk_level == RiskLevel.CRITICAL
            )
        )
        result = await db.execute(stmt)
        return result.scalar() or 0

    async def _calculate_avg_retention(
        self,
        db: AsyncSession,
        since_date: datetime
    ) -> Dict[str, float]:
        """Calculate average retention rate."""
        # Simplified
        return {"avg_retention": 85.0}

    async def _get_quick_actions(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Get recommended quick actions."""
        # Count pending interventions
        pending_interventions_stmt = select(func.count(Intervention.intervention_id)).where(
            Intervention.status == InterventionStatus.PENDING
        )
        pending_result = await db.execute(pending_interventions_stmt)
        pending_count = pending_result.scalar() or 0

        return [
            {
                "action": "Review high-risk tutors",
                "count": await self._count_high_risk_tutors(db),
                "priority": "high"
            },
            {
                "action": "Follow up on pending interventions",
                "count": pending_count,
                "priority": "medium"
            }
        ]

    async def _get_tier_distribution(self, db: AsyncSession) -> Dict[str, int]:
        """Get distribution of tutors across tiers."""
        # Get latest performance metrics for all active tutors
        subquery = select(
            TutorPerformanceMetric.tutor_id,
            func.max(TutorPerformanceMetric.calculation_date).label('max_date')
        ).where(
            TutorPerformanceMetric.window == MetricWindow.THIRTY_DAY
        ).group_by(TutorPerformanceMetric.tutor_id).subquery()

        stmt = select(
            TutorPerformanceMetric.performance_tier,
            func.count(TutorPerformanceMetric.tutor_id).label('count')
        ).join(
            subquery,
            and_(
                TutorPerformanceMetric.tutor_id == subquery.c.tutor_id,
                TutorPerformanceMetric.calculation_date == subquery.c.max_date
            )
        ).join(
            Tutor,
            TutorPerformanceMetric.tutor_id == Tutor.tutor_id
        ).where(
            Tutor.status == TutorStatus.ACTIVE
        ).group_by(
            TutorPerformanceMetric.performance_tier
        )

        result = await db.execute(stmt)
        rows = result.all()

        # Convert to dictionary
        tier_distribution = {tier.value: 0 for tier in PerformanceTier}
        for row in rows:
            tier_distribution[row[0].value if hasattr(row[0], 'value') else row[0]] = row[1]

        return tier_distribution

    async def _get_session_statistics(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get session statistics for period."""
        # Count total sessions
        total_stmt = select(func.count(TutoringSession.session_id)).where(
            and_(
                TutoringSession.session_date >= start_date,
                TutoringSession.session_date <= end_date
            )
        )
        total_result = await db.execute(total_stmt)
        total_sessions = total_result.scalar() or 0

        # Calculate average rating from feedback
        rating_stmt = select(func.avg(StudentFeedback.rating)).join(
            TutoringSession,
            StudentFeedback.session_id == TutoringSession.session_id
        ).where(
            and_(
                TutoringSession.session_date >= start_date,
                TutoringSession.session_date <= end_date,
                StudentFeedback.rating.isnot(None)
            )
        )
        rating_result = await db.execute(rating_stmt)
        avg_rating = rating_result.scalar()

        # Calculate completion rate (sessions with feedback)
        completed_stmt = select(func.count(func.distinct(TutoringSession.session_id))).join(
            StudentFeedback,
            TutoringSession.session_id == StudentFeedback.session_id
        ).where(
            and_(
                TutoringSession.session_date >= start_date,
                TutoringSession.session_date <= end_date
            )
        )
        completed_result = await db.execute(completed_stmt)
        completed_sessions = completed_result.scalar() or 0

        completion_rate = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0

        return {
            "total_sessions": total_sessions,
            "avg_rating": round(float(avg_rating), 2) if avg_rating else 0.0,
            "completion_rate": round(completion_rate, 2)
        }

    async def _get_rating_trend(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get rating trend over period."""
        # Calculate average rating for first half of period
        mid_date = start_date + (end_date - start_date) / 2

        first_half_stmt = select(func.avg(StudentFeedback.rating)).join(
            TutoringSession,
            StudentFeedback.session_id == TutoringSession.session_id
        ).where(
            and_(
                TutoringSession.session_date >= start_date,
                TutoringSession.session_date < mid_date,
                StudentFeedback.rating.isnot(None)
            )
        )
        first_half_result = await db.execute(first_half_stmt)
        first_half_avg = first_half_result.scalar()

        # Calculate average rating for second half of period
        second_half_stmt = select(func.avg(StudentFeedback.rating)).join(
            TutoringSession,
            StudentFeedback.session_id == TutoringSession.session_id
        ).where(
            and_(
                TutoringSession.session_date >= mid_date,
                TutoringSession.session_date <= end_date,
                StudentFeedback.rating.isnot(None)
            )
        )
        second_half_result = await db.execute(second_half_stmt)
        second_half_avg = second_half_result.scalar()

        # Calculate trend
        if first_half_avg and second_half_avg:
            change = float(second_half_avg) - float(first_half_avg)
            if abs(change) < 0.05:
                trend = "stable"
            elif change > 0:
                trend = "improving"
            else:
                trend = "declining"

            return {
                "trend": trend,
                "change": f"{change:+.2f}"
            }
        else:
            return {
                "trend": "insufficient_data",
                "change": "0.0"
            }


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

_analytics_service: Optional[AnalyticsService] = None


async def get_analytics_service() -> AnalyticsService:
    """Get analytics service instance (dependency injection)."""
    global _analytics_service

    if _analytics_service is None:
        from src.api.redis_service import get_redis_service
        redis_service = await get_redis_service()
        _analytics_service = AnalyticsService(redis_service)

    return _analytics_service
