"""
SLA Dashboard API Endpoints

Provides endpoints for SLA tracking and dashboard visualization.
Tracks key metrics: insight latency (<60 min), uptime (>99.5%), API response times.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from src.api.sla_tracking_service import get_sla_tracking_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sla", tags=["sla-dashboard"])


# ============================================================================
# SLA Dashboard Data Endpoints
# ============================================================================

@router.get("/dashboard")
async def get_sla_dashboard(
    hours: int = Query(24, ge=1, le=720, description="Hours to analyze (1-720)")
) -> Dict[str, Any]:
    """
    Get comprehensive SLA dashboard data.

    Includes:
    - Insight latency metrics (<60 min target)
    - System uptime (>99.5% target)
    - API response time percentiles (p50, p95, p99)
    - Overall SLA compliance status

    Args:
        hours: Number of hours to analyze

    Returns:
        Complete SLA dashboard data
    """
    try:
        sla_service = get_sla_tracking_service()
        return await sla_service.get_sla_dashboard_data(hours=hours)
    except Exception as e:
        logger.error(f"Failed to get SLA dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insight-latency")
async def get_insight_latency_metrics(
    hours: int = Query(24, ge=1, le=720, description="Hours to analyze (1-720)")
) -> Dict[str, Any]:
    """
    Get insight latency metrics.

    Tracks time from session end to dashboard update.
    Target: <60 minutes per PRD requirements.

    Args:
        hours: Number of hours to analyze

    Returns:
        Insight latency statistics
    """
    try:
        sla_service = get_sla_tracking_service()
        return await sla_service.calculate_average_insight_latency(hours=hours)
    except Exception as e:
        logger.error(f"Failed to get insight latency metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api-response-times")
async def get_api_response_times(
    endpoint: Optional[str] = Query(None, description="Specific endpoint to analyze"),
    hours: int = Query(24, ge=1, le=720, description="Hours to analyze (1-720)")
) -> Dict[str, Any]:
    """
    Get API response time statistics.

    Returns p50, p95, and p99 percentiles.
    Targets: p95 < 500ms, p99 < 1000ms

    Args:
        endpoint: Specific endpoint to analyze (optional)
        hours: Number of hours to analyze

    Returns:
        API response time statistics
    """
    try:
        sla_service = get_sla_tracking_service()
        return await sla_service.calculate_api_response_time_stats(
            endpoint=endpoint,
            hours=hours
        )
    except Exception as e:
        logger.error(f"Failed to get API response time stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/violations")
async def get_sla_violations(
    hours: int = Query(24, ge=1, le=720, description="Hours to look back (1-720)")
) -> Dict[str, Any]:
    """
    Get all SLA violations in the specified time period.

    Args:
        hours: Number of hours to look back

    Returns:
        List of SLA violations
    """
    try:
        sla_service = get_sla_tracking_service()
        violations = await sla_service.get_sla_violations(hours=hours)

        return {
            "period_hours": hours,
            "total_violations": len(violations),
            "violations": violations,
        }
    except Exception as e:
        logger.error(f"Failed to get SLA violations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/track-insight-latency")
async def track_insight_latency(
    session_id: str,
    session_end_time: str,
    dashboard_update_time: Optional[str] = None
) -> Dict[str, Any]:
    """
    Track insight latency for a session.

    Use this endpoint when performance metrics are updated on the dashboard
    to track how long it took from session end.

    Args:
        session_id: Session identifier
        session_end_time: ISO format timestamp of session end
        dashboard_update_time: ISO format timestamp of dashboard update (defaults to now)

    Returns:
        Latency tracking result
    """
    try:
        sla_service = get_sla_tracking_service()

        # Parse timestamps
        session_end = datetime.fromisoformat(session_end_time.replace('Z', '+00:00'))
        dashboard_update = None
        if dashboard_update_time:
            dashboard_update = datetime.fromisoformat(dashboard_update_time.replace('Z', '+00:00'))

        result = await sla_service.track_insight_latency(
            session_id=session_id,
            session_end_time=session_end,
            dashboard_update_time=dashboard_update
        )

        return {
            "success": True,
            **result
        }
    except Exception as e:
        logger.error(f"Failed to track insight latency: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/track-api-response")
async def track_api_response(
    endpoint: str,
    response_time_ms: float,
    status_code: int = 200
) -> Dict[str, Any]:
    """
    Track API response time for a specific endpoint.

    Args:
        endpoint: API endpoint path
        response_time_ms: Response time in milliseconds
        status_code: HTTP status code

    Returns:
        Tracking result
    """
    try:
        sla_service = get_sla_tracking_service()

        result = await sla_service.track_api_response_time(
            endpoint=endpoint,
            response_time_ms=response_time_ms,
            status_code=status_code
        )

        return {
            "success": True,
            **result
        }
    except Exception as e:
        logger.error(f"Failed to track API response time: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HTML Dashboard
# ============================================================================

@router.get("/dashboard/view", response_class=HTMLResponse)
async def view_sla_dashboard() -> str:
    """
    Render HTML SLA dashboard.

    Provides a simple web interface to view SLA metrics without Grafana.

    Returns:
        HTML dashboard page
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TutorMax SLA Dashboard</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: #f5f7fa;
                padding: 20px;
            }

            .container {
                max-width: 1400px;
                margin: 0 auto;
            }

            header {
                background: white;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                margin-bottom: 30px;
            }

            h1 {
                color: #2c3e50;
                font-size: 32px;
                margin-bottom: 10px;
            }

            .subtitle {
                color: #7f8c8d;
                font-size: 16px;
            }

            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }

            .metric-card {
                background: white;
                padding: 25px;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                transition: transform 0.2s;
            }

            .metric-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }

            .metric-label {
                color: #7f8c8d;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 10px;
            }

            .metric-value {
                font-size: 48px;
                font-weight: bold;
                margin-bottom: 10px;
            }

            .metric-value.success {
                color: #27ae60;
            }

            .metric-value.warning {
                color: #f39c12;
            }

            .metric-value.danger {
                color: #e74c3c;
            }

            .metric-detail {
                color: #95a5a6;
                font-size: 14px;
            }

            .status-badge {
                display: inline-block;
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
                margin-top: 10px;
            }

            .status-badge.success {
                background: #d4edda;
                color: #155724;
            }

            .status-badge.danger {
                background: #f8d7da;
                color: #721c24;
            }

            .chart-container {
                background: white;
                padding: 25px;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                margin-bottom: 30px;
            }

            .loading {
                text-align: center;
                padding: 40px;
                color: #7f8c8d;
            }

            .refresh-btn {
                background: #3498db;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: background 0.2s;
            }

            .refresh-btn:hover {
                background: #2980b9;
            }

            .time-selector {
                margin: 20px 0;
            }

            .time-selector select {
                padding: 10px;
                border-radius: 8px;
                border: 1px solid #ddd;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🎯 TutorMax SLA Dashboard</h1>
                <p class="subtitle">Real-time Service Level Agreement Monitoring</p>
                <div class="time-selector">
                    <label for="timeRange">Time Range: </label>
                    <select id="timeRange" onchange="loadDashboard()">
                        <option value="1">Last Hour</option>
                        <option value="6">Last 6 Hours</option>
                        <option value="24" selected>Last 24 Hours</option>
                        <option value="168">Last 7 Days</option>
                        <option value="720">Last 30 Days</option>
                    </select>
                    <button class="refresh-btn" onclick="loadDashboard()">🔄 Refresh</button>
                </div>
            </header>

            <div id="dashboard-content">
                <div class="loading">Loading SLA metrics...</div>
            </div>
        </div>

        <script>
            async function loadDashboard() {
                const hours = document.getElementById('timeRange').value;
                const content = document.getElementById('dashboard-content');

                try {
                    content.innerHTML = '<div class="loading">Loading SLA metrics...</div>';

                    const response = await fetch(`/api/sla/dashboard?hours=${hours}`);
                    const data = await response.json();

                    renderDashboard(data);
                } catch (error) {
                    content.innerHTML = `<div class="loading">Error loading dashboard: ${error.message}</div>`;
                }
            }

            function renderDashboard(data) {
                const content = document.getElementById('dashboard-content');

                const insightLatency = data.insight_latency;
                const apiResponse = data.api_response_times;
                const uptime = data.system_uptime;
                const overallSLA = data.overall_sla_met;

                content.innerHTML = `
                    <div class="metrics-grid">
                        <div class="metric-card">
                            <div class="metric-label">Overall SLA Status</div>
                            <div class="metric-value ${overallSLA ? 'success' : 'danger'}">
                                ${overallSLA ? '✓' : '✗'}
                            </div>
                            <div class="metric-detail">
                                ${overallSLA ? 'All SLAs Met' : 'SLA Violations Detected'}
                            </div>
                            <span class="status-badge ${overallSLA ? 'success' : 'danger'}">
                                ${overallSLA ? 'Compliant' : 'Non-Compliant'}
                            </span>
                        </div>

                        <div class="metric-card">
                            <div class="metric-label">Insight Latency (Avg)</div>
                            <div class="metric-value ${insightLatency.meets_sla_percentage >= 95 ? 'success' : 'danger'}">
                                ${insightLatency.average_latency_minutes}
                            </div>
                            <div class="metric-detail">
                                minutes (target: <60 min)<br>
                                SLA Compliance: ${insightLatency.meets_sla_percentage}%<br>
                                P95: ${insightLatency.p95_latency_minutes} min<br>
                                Samples: ${insightLatency.sample_count}
                            </div>
                        </div>

                        <div class="metric-card">
                            <div class="metric-label">System Uptime</div>
                            <div class="metric-value ${uptime.meets_sla ? 'success' : 'danger'}">
                                ${uptime.overall_uptime}%
                            </div>
                            <div class="metric-detail">
                                Target: >${uptime.target}%
                            </div>
                            <span class="status-badge ${uptime.meets_sla ? 'success' : 'danger'}">
                                ${uptime.meets_sla ? 'Meeting SLA' : 'Below Target'}
                            </span>
                        </div>

                        <div class="metric-card">
                            <div class="metric-label">API Response Time (P95)</div>
                            <div class="metric-value ${apiResponse.meets_p95_sla ? 'success' : 'warning'}">
                                ${apiResponse.p95_ms}
                            </div>
                            <div class="metric-detail">
                                ms (target: <500ms)<br>
                                P50: ${apiResponse.p50_ms}ms<br>
                                P99: ${apiResponse.p99_ms}ms<br>
                                Samples: ${apiResponse.sample_count}
                            </div>
                        </div>
                    </div>

                    <div class="chart-container">
                        <h2 style="margin-bottom: 20px; color: #2c3e50;">SLA Compliance Summary</h2>
                        <table style="width: 100%; border-collapse: collapse;">
                            <thead>
                                <tr style="border-bottom: 2px solid #ddd;">
                                    <th style="padding: 12px; text-align: left;">Metric</th>
                                    <th style="padding: 12px; text-align: right;">Current Value</th>
                                    <th style="padding: 12px; text-align: right;">Target</th>
                                    <th style="padding: 12px; text-align: center;">Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr style="border-bottom: 1px solid #eee;">
                                    <td style="padding: 12px;">Insight Latency (Avg)</td>
                                    <td style="padding: 12px; text-align: right;">${insightLatency.average_latency_minutes} min</td>
                                    <td style="padding: 12px; text-align: right;"><60 min</td>
                                    <td style="padding: 12px; text-align: center;">
                                        <span class="status-badge ${insightLatency.meets_sla_percentage >= 95 ? 'success' : 'danger'}">
                                            ${insightLatency.meets_sla_percentage >= 95 ? 'PASS' : 'FAIL'}
                                        </span>
                                    </td>
                                </tr>
                                <tr style="border-bottom: 1px solid #eee;">
                                    <td style="padding: 12px;">System Uptime</td>
                                    <td style="padding: 12px; text-align: right;">${uptime.overall_uptime}%</td>
                                    <td style="padding: 12px; text-align: right;">>${uptime.target}%</td>
                                    <td style="padding: 12px; text-align: center;">
                                        <span class="status-badge ${uptime.meets_sla ? 'success' : 'danger'}">
                                            ${uptime.meets_sla ? 'PASS' : 'FAIL'}
                                        </span>
                                    </td>
                                </tr>
                                <tr style="border-bottom: 1px solid #eee;">
                                    <td style="padding: 12px;">API Response (P95)</td>
                                    <td style="padding: 12px; text-align: right;">${apiResponse.p95_ms} ms</td>
                                    <td style="padding: 12px; text-align: right;"><500 ms</td>
                                    <td style="padding: 12px; text-align: center;">
                                        <span class="status-badge ${apiResponse.meets_p95_sla ? 'success' : 'danger'}">
                                            ${apiResponse.meets_p95_sla ? 'PASS' : 'FAIL'}
                                        </span>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px;">API Response (P99)</td>
                                    <td style="padding: 12px; text-align: right;">${apiResponse.p99_ms} ms</td>
                                    <td style="padding: 12px; text-align: right;"><1000 ms</td>
                                    <td style="padding: 12px; text-align: center;">
                                        <span class="status-badge ${apiResponse.meets_p99_sla ? 'success' : 'danger'}">
                                            ${apiResponse.meets_p99_sla ? 'PASS' : 'FAIL'}
                                        </span>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                `;
            }

            // Load dashboard on page load
            loadDashboard();

            // Auto-refresh every 60 seconds
            setInterval(loadDashboard, 60000);
        </script>
    </body>
    </html>
    """

    return html_content
