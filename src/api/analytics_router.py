"""
Advanced Analytics API Router

Provides endpoints for advanced analytics features:
- Churn heatmaps
- Cohort analysis
- Intervention effectiveness tracking
- Enhanced predictive insights

Part of Task 9: Advanced Analytics Dashboard
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from src.api.analytics_service import (
    get_analytics_service,
    AnalyticsService,
    CohortPeriod,
    HeatmapGranularity
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["advanced-analytics"])


# ============================================================================
# CHURN HEATMAP ENDPOINTS
# ============================================================================

@router.get("/churn-heatmap")
async def get_churn_heatmap(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    granularity: HeatmapGranularity = Query(
        HeatmapGranularity.WEEKLY,
        description="Heatmap granularity (daily, weekly, monthly)"
    ),
    service: AnalyticsService = Depends(get_analytics_service)
) -> Dict[str, Any]:
    """
    Get churn heatmap data showing churn patterns over time.

    Returns a heatmap matrix showing:
    - Time periods on X-axis
    - Risk levels or cohorts on Y-axis
    - Churn rates as heatmap values

    Performance requirement: < 500ms response time

    Args:
        start_date: Start date for analysis (default: 90 days ago)
        end_date: End date for analysis (default: today)
        granularity: Time granularity (daily, weekly, monthly)

    Returns:
        Heatmap data with matrix, labels, and metadata
    """
    try:
        # Parse dates
        end = datetime.fromisoformat(end_date) if end_date else datetime.now()
        start = datetime.fromisoformat(start_date) if start_date else end - timedelta(days=90)

        # Get heatmap data
        heatmap_data = await service.get_churn_heatmap(
            start_date=start,
            end_date=end,
            granularity=granularity
        )

        return heatmap_data

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        logger.error(f"Failed to generate churn heatmap: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/churn-heatmap/by-tier")
async def get_churn_heatmap_by_tier(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    service: AnalyticsService = Depends(get_analytics_service)
) -> Dict[str, Any]:
    """
    Get churn heatmap segmented by performance tier.

    Shows churn patterns across different performance tiers over time.

    Args:
        start_date: Start date for analysis
        end_date: End date for analysis

    Returns:
        Heatmap data with performance tiers on Y-axis
    """
    try:
        end = datetime.fromisoformat(end_date) if end_date else datetime.now()
        start = datetime.fromisoformat(start_date) if start_date else end - timedelta(days=90)

        heatmap_data = await service.get_churn_heatmap_by_tier(
            start_date=start,
            end_date=end
        )

        return heatmap_data

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        logger.error(f"Failed to generate tier heatmap: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# COHORT ANALYSIS ENDPOINTS
# ============================================================================

@router.get("/cohort-analysis")
async def get_cohort_analysis(
    cohort_by: str = Query("month", description="Cohort grouping (month, quarter, subject)"),
    metric: str = Query("retention", description="Metric to analyze (retention, churn, performance)"),
    period: CohortPeriod = Query(
        CohortPeriod.MONTHLY,
        description="Analysis period (weekly, monthly, quarterly)"
    ),
    service: AnalyticsService = Depends(get_analytics_service)
) -> Dict[str, Any]:
    """
    Get cohort analysis showing tutor retention and performance over time.

    Tracks cohorts of tutors grouped by:
    - Onboarding month/quarter
    - Subject area
    - Initial performance tier

    Args:
        cohort_by: How to group cohorts (month, quarter, subject)
        metric: Metric to track (retention, churn, performance, revenue)
        period: Time period for tracking (weekly, monthly, quarterly)

    Returns:
        Cohort analysis data with matrix and insights
    """
    try:
        cohort_data = await service.get_cohort_analysis(
            cohort_by=cohort_by,
            metric=metric,
            period=period
        )

        return cohort_data

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {e}")
    except Exception as e:
        logger.error(f"Failed to generate cohort analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cohort-analysis/retention-curve")
async def get_retention_curve(
    cohort_id: Optional[str] = Query(None, description="Specific cohort ID"),
    service: AnalyticsService = Depends(get_analytics_service)
) -> Dict[str, Any]:
    """
    Get retention curve showing tutor retention rates over time.

    Args:
        cohort_id: Optional specific cohort to analyze

    Returns:
        Retention curve data with percentages over time
    """
    try:
        curve_data = await service.get_retention_curve(cohort_id=cohort_id)
        return curve_data

    except Exception as e:
        logger.error(f"Failed to generate retention curve: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# INTERVENTION EFFECTIVENESS ENDPOINTS
# ============================================================================

@router.get("/intervention-effectiveness")
async def get_intervention_effectiveness(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    intervention_type: Optional[str] = Query(None, description="Filter by intervention type"),
    service: AnalyticsService = Depends(get_analytics_service)
) -> Dict[str, Any]:
    """
    Get intervention effectiveness metrics showing impact of interventions.

    Analyzes:
    - Response rates by intervention type
    - Improvement rates after intervention
    - Time to improvement
    - Churn prevention success
    - ROI metrics

    Args:
        start_date: Start date for analysis
        end_date: End date for analysis
        intervention_type: Optional filter for specific intervention type

    Returns:
        Intervention effectiveness metrics and comparisons
    """
    try:
        end = datetime.fromisoformat(end_date) if end_date else datetime.now()
        start = datetime.fromisoformat(start_date) if start_date else end - timedelta(days=90)

        effectiveness_data = await service.get_intervention_effectiveness(
            start_date=start,
            end_date=end,
            intervention_type=intervention_type
        )

        return effectiveness_data

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        logger.error(f"Failed to analyze intervention effectiveness: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intervention-effectiveness/comparison")
async def get_intervention_comparison(
    service: AnalyticsService = Depends(get_analytics_service)
) -> Dict[str, Any]:
    """
    Compare effectiveness across different intervention types.

    Returns ranked list of interventions by:
    - Response rate
    - Success rate
    - Time to impact
    - Cost-effectiveness (if available)

    Returns:
        Comparative analysis of all intervention types
    """
    try:
        comparison_data = await service.get_intervention_comparison()
        return comparison_data

    except Exception as e:
        logger.error(f"Failed to compare interventions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intervention-effectiveness/funnel")
async def get_intervention_funnel(
    intervention_type: str = Query(..., description="Intervention type to analyze"),
    service: AnalyticsService = Depends(get_analytics_service)
) -> Dict[str, Any]:
    """
    Get intervention funnel showing progression through intervention stages.

    Tracks:
    - Triggered → Sent → Viewed → Responded → Completed → Improved

    Args:
        intervention_type: Type of intervention to analyze

    Returns:
        Funnel data with conversion rates at each stage
    """
    try:
        funnel_data = await service.get_intervention_funnel(intervention_type)
        return funnel_data

    except Exception as e:
        logger.error(f"Failed to generate intervention funnel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PREDICTIVE INSIGHTS ENDPOINTS
# ============================================================================

@router.get("/predictive-insights/trends")
async def get_predictive_trends(
    forecast_days: int = Query(30, ge=7, le=90, description="Days to forecast"),
    service: AnalyticsService = Depends(get_analytics_service)
) -> Dict[str, Any]:
    """
    Get predictive trends and forecasts.

    Provides forecasts for:
    - Expected churn rates
    - Performance tier distributions
    - Intervention needs
    - Resource requirements

    Args:
        forecast_days: Number of days to forecast (7-90)

    Returns:
        Trend forecasts with confidence intervals
    """
    try:
        trends_data = await service.get_predictive_trends(forecast_days=forecast_days)
        return trends_data

    except Exception as e:
        logger.error(f"Failed to generate predictive trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predictive-insights/risk-segments")
async def get_risk_segments(
    service: AnalyticsService = Depends(get_analytics_service)
) -> Dict[str, Any]:
    """
    Get segmentation analysis of tutors by risk level.

    Segments tutors into risk groups and identifies:
    - Common characteristics
    - Recommended interventions
    - Expected outcomes

    Returns:
        Risk segment analysis with recommendations
    """
    try:
        segments_data = await service.get_risk_segments()
        return segments_data

    except Exception as e:
        logger.error(f"Failed to analyze risk segments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SUMMARY & OVERVIEW ENDPOINTS
# ============================================================================

@router.get("/overview")
async def get_analytics_overview(
    service: AnalyticsService = Depends(get_analytics_service)
) -> Dict[str, Any]:
    """
    Get comprehensive analytics overview dashboard.

    Combines key metrics from all analytics modules:
    - Churn trends summary
    - Cohort performance highlights
    - Intervention effectiveness summary
    - Predictive insights snapshot

    Optimized for dashboard load time < 2 seconds.

    Returns:
        Complete analytics overview
    """
    try:
        overview_data = await service.get_analytics_overview()
        return overview_data

    except Exception as e:
        logger.error(f"Failed to generate analytics overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance-summary")
async def get_performance_summary(
    period: str = Query("30d", description="Time period (7d, 30d, 90d)"),
    service: AnalyticsService = Depends(get_analytics_service)
) -> Dict[str, Any]:
    """
    Get performance summary for specified time period.

    Args:
        period: Time period (7d, 30d, 90d)

    Returns:
        Performance metrics summary
    """
    try:
        # Parse period
        days = int(period.replace('d', ''))
        if days not in [7, 30, 90]:
            raise ValueError("Period must be 7d, 30d, or 90d")

        summary_data = await service.get_performance_summary(days=days)
        return summary_data

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate performance summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CACHE MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/cache/clear")
async def clear_analytics_cache(
    cache_key: Optional[str] = Query(None, description="Specific cache key to clear"),
    service: AnalyticsService = Depends(get_analytics_service)
) -> Dict[str, str]:
    """
    Clear analytics cache.

    Args:
        cache_key: Optional specific cache key to clear (clears all if not provided)

    Returns:
        Success message
    """
    try:
        await service.clear_cache(cache_key=cache_key)

        return {
            "status": "success",
            "message": f"Cleared cache: {cache_key if cache_key else 'all analytics caches'}"
        }

    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))
