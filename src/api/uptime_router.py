"""
Uptime Monitoring and SLA Tracking API Endpoints

Provides endpoints for monitoring system uptime and SLA compliance.
Target: >99.5% uptime, <60min insight latency.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from src.api.uptime_service import get_uptime_monitor
from src.api.health_check_service import get_health_checker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


# ============================================================================
# Infrastructure Health Check Endpoints
# ============================================================================

@router.get("/health/comprehensive")
async def get_comprehensive_health() -> Dict[str, Any]:
    """
    Get comprehensive infrastructure health status.

    Performs detailed health checks on all services including:
    - PostgreSQL database
    - Redis cache/queue
    - Celery workers
    - API availability

    Includes alerting for degraded or unhealthy services.

    Returns:
        Complete health check report with alerts
    """
    try:
        health_checker = get_health_checker()
        return await health_checker.check_all()
    except Exception as e:
        logger.error(f"Comprehensive health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Uptime Monitoring Endpoints
# ============================================================================

@router.get("/uptime/current")
async def get_current_uptime() -> Dict[str, Any]:
    """
    Get current uptime status for all services.

    Performs health checks and returns current status.

    Returns:
        Current uptime status for all services
    """
    try:
        uptime_monitor = get_uptime_monitor()
        return await uptime_monitor.record_all_health_checks()
    except Exception as e:
        logger.error(f"Failed to get current uptime: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/uptime/report")
async def get_uptime_report(
    hours: int = Query(24, ge=1, le=720, description="Hours to look back (1-720)")
) -> Dict[str, Any]:
    """
    Get comprehensive uptime report for specified time period.

    Calculates uptime percentages, SLA compliance, and service metrics.

    Args:
        hours: Number of hours to analyze (default: 24)

    Returns:
        Detailed uptime report with SLA status
    """
    try:
        uptime_monitor = get_uptime_monitor()
        return await uptime_monitor.get_uptime_report(hours=hours)
    except Exception as e:
        logger.error(f"Failed to generate uptime report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/uptime/service/{service}")
async def get_service_uptime(
    service: str,
    hours: int = Query(24, ge=1, le=720, description="Hours to look back (1-720)")
) -> Dict[str, Any]:
    """
    Get uptime metrics for a specific service.

    Args:
        service: Service name (api, redis, postgresql, celery_workers)
        hours: Number of hours to analyze

    Returns:
        Service uptime metrics
    """
    try:
        uptime_monitor = get_uptime_monitor()

        # Validate service name
        if service not in uptime_monitor.SERVICES:
            raise HTTPException(
                status_code=404,
                detail=f"Service '{service}' not found. Available services: {list(uptime_monitor.SERVICES.keys())}"
            )

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        uptime_data = await uptime_monitor.calculate_uptime(service, start_time, end_time)

        return {
            "service_name": uptime_monitor.SERVICES[service],
            **uptime_data,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get service uptime for {service}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/uptime/incidents")
async def get_downtime_incidents(
    service: Optional[str] = Query(None, description="Filter by service name"),
    hours: int = Query(24, ge=1, le=720, description="Hours to look back (1-720)")
) -> Dict[str, Any]:
    """
    Get downtime incidents across all services or specific service.

    Args:
        service: Optional service name filter
        hours: Number of hours to look back

    Returns:
        List of downtime incidents
    """
    try:
        uptime_monitor = get_uptime_monitor()

        # Validate service name if provided
        if service and service not in uptime_monitor.SERVICES:
            raise HTTPException(
                status_code=404,
                detail=f"Service '{service}' not found. Available services: {list(uptime_monitor.SERVICES.keys())}"
            )

        incidents = await uptime_monitor.get_downtime_incidents(service=service, hours=hours)

        return {
            "period_hours": hours,
            "service_filter": service,
            "total_incidents": len(incidents),
            "incidents": incidents,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get downtime incidents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SLA Tracking Endpoints
# ============================================================================

@router.get("/sla/status")
async def get_sla_status(
    hours: int = Query(24, ge=1, le=720, description="Hours to look back (1-720)")
) -> Dict[str, Any]:
    """
    Get current SLA compliance status.

    Checks if system meets SLA targets:
    - >99.5% uptime
    - <60 minutes insight latency
    - API response times within thresholds

    Args:
        hours: Number of hours to analyze

    Returns:
        SLA compliance status
    """
    try:
        uptime_monitor = get_uptime_monitor()
        uptime_report = await uptime_monitor.get_uptime_report(hours=hours)

        # Calculate SLA status
        sla_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "period_hours": hours,
            "sla_targets": {
                "uptime_percentage": uptime_monitor.SLA_TARGET,
                "insight_latency_minutes": 60,
            },
            "current_metrics": {
                "overall_uptime": uptime_report["overall_uptime"],
                "meets_uptime_sla": uptime_report["meets_sla"],
            },
            "services": {},
            "overall_sla_compliance": uptime_report["meets_sla"],
        }

        # Add per-service SLA status
        for service_key, service_data in uptime_report["services"].items():
            sla_status["services"][service_key] = {
                "name": service_data["name"],
                "uptime_percentage": service_data["uptime_percentage"],
                "meets_sla": service_data["meets_sla"],
                "avg_latency_ms": service_data.get("avg_latency_ms", 0),
            }

        return sla_status
    except Exception as e:
        logger.error(f"Failed to get SLA status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sla/violations")
async def get_sla_violations(
    hours: int = Query(24, ge=1, le=720, description="Hours to look back (1-720)")
) -> Dict[str, Any]:
    """
    Get SLA violations within specified time period.

    Identifies services that failed to meet SLA targets.

    Args:
        hours: Number of hours to analyze

    Returns:
        List of SLA violations
    """
    try:
        uptime_monitor = get_uptime_monitor()
        uptime_report = await uptime_monitor.get_uptime_report(hours=hours)

        violations = []

        # Check each service for SLA violations
        for service_key, service_data in uptime_report["services"].items():
            if not service_data["meets_sla"]:
                violations.append({
                    "service": service_key,
                    "service_name": service_data["name"],
                    "uptime_percentage": service_data["uptime_percentage"],
                    "sla_target": uptime_monitor.SLA_TARGET,
                    "deficit": round(uptime_monitor.SLA_TARGET - service_data["uptime_percentage"], 3),
                    "failed_checks": service_data["failed_checks"],
                    "total_checks": service_data["total_checks"],
                })

        return {
            "period_hours": hours,
            "total_violations": len(violations),
            "overall_meets_sla": uptime_report["meets_sla"],
            "overall_uptime": uptime_report["overall_uptime"],
            "violations": violations,
        }
    except Exception as e:
        logger.error(f"Failed to get SLA violations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Health Check Scheduling Endpoint
# ============================================================================

@router.post("/uptime/check")
async def trigger_health_check() -> Dict[str, Any]:
    """
    Manually trigger a health check for all services.

    Records results to database for uptime tracking.

    Returns:
        Health check results
    """
    try:
        uptime_monitor = get_uptime_monitor()
        result = await uptime_monitor.record_all_health_checks()

        return {
            "success": True,
            "message": "Health check completed and recorded",
            **result,
        }
    except Exception as e:
        logger.error(f"Failed to trigger health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))
