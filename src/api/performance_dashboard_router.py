"""
Performance Metrics Dashboard API Endpoints

Provides endpoints for performance monitoring dashboard.
Displays API response times, database performance, queue depths, and Redis metrics.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from typing import Dict, Any
import logging

from src.api.performance_metrics_service import get_performance_metrics_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/performance", tags=["performance-dashboard"])


# ============================================================================
# Performance Dashboard Data Endpoints
# ============================================================================

@router.get("/dashboard")
async def get_performance_dashboard(
    hours: int = Query(24, ge=1, le=720, description="Hours to analyze (1-720)")
) -> Dict[str, Any]:
    """
    Get comprehensive performance dashboard data.

    Includes:
    - API response time percentiles (p50, p95, p99)
    - Database query performance and cache hit rates
    - Worker queue depths and backlogs
    - Redis performance and hit rates
    - Celery task execution metrics

    Args:
        hours: Number of hours to analyze

    Returns:
        Complete performance dashboard data
    """
    try:
        perf_service = get_performance_metrics_service()
        return await perf_service.get_performance_dashboard_data(hours=hours)
    except Exception as e:
        logger.error(f"Failed to get performance dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api-response-times")
async def get_api_response_times(
    hours: int = Query(24, ge=1, le=720, description="Hours to analyze")
) -> Dict[str, Any]:
    """
    Get API response time statistics with percentiles.

    Args:
        hours: Number of hours to analyze

    Returns:
        API response time metrics (p50, p95, p99)
    """
    try:
        perf_service = get_performance_metrics_service()
        return await perf_service.get_api_response_times(hours=hours)
    except Exception as e:
        logger.error(f"Failed to get API response times: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database")
async def get_database_performance() -> Dict[str, Any]:
    """
    Get database performance metrics.

    Returns:
    - Connection pool statistics
    - Active connections
    - Slow query count
    - Database size
    - Cache hit ratio

    Returns:
        Database performance metrics
    """
    try:
        perf_service = get_performance_metrics_service()
        return await perf_service.get_database_performance()
    except Exception as e:
        logger.error(f"Failed to get database performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/worker-queues")
def get_worker_queue_depths() -> Dict[str, Any]:
    """
    Get worker queue depths and backlog information.

    Returns:
    - Queue lengths for all queues
    - Total backlog
    - High backlog queues
    - Queue status

    Returns:
        Worker queue metrics
    """
    try:
        perf_service = get_performance_metrics_service()
        return perf_service.get_worker_queue_depths()
    except Exception as e:
        logger.error(f"Failed to get worker queue depths: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/redis")
def get_redis_performance() -> Dict[str, Any]:
    """
    Get Redis performance metrics.

    Returns:
    - Cache hit rate
    - Memory usage
    - Connection statistics
    - Operations per second
    - Evicted keys

    Returns:
        Redis performance metrics
    """
    try:
        perf_service = get_performance_metrics_service()
        return perf_service.get_redis_performance()
    except Exception as e:
        logger.error(f"Failed to get Redis performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/celery-tasks")
def get_celery_task_metrics() -> Dict[str, Any]:
    """
    Get Celery task execution metrics.

    Returns:
    - Total executions
    - Success/failure rates
    - Per-task statistics
    - Slowest tasks

    Returns:
        Celery task metrics
    """
    try:
        perf_service = get_performance_metrics_service()
        return perf_service.get_celery_task_metrics()
    except Exception as e:
        logger.error(f"Failed to get Celery task metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HTML Dashboard
# ============================================================================

@router.get("/dashboard/view", response_class=HTMLResponse)
async def view_performance_dashboard() -> str:
    """
    Render HTML performance metrics dashboard.

    Provides a real-time web interface for engineers to monitor system performance.

    Returns:
        HTML dashboard page
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TutorMax Performance Dashboard</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                background: #1e1e1e;
                color: #d4d4d4;
                padding: 20px;
            }

            .container {
                max-width: 1600px;
                margin: 0 auto;
            }

            header {
                background: #252526;
                padding: 30px;
                border-radius: 8px;
                border: 1px solid #3e3e42;
                margin-bottom: 20px;
            }

            h1 {
                color: #4ec9b0;
                font-size: 28px;
                margin-bottom: 10px;
            }

            .subtitle {
                color: #858585;
                font-size: 14px;
            }

            .controls {
                margin: 20px 0;
                display: flex;
                gap: 15px;
                align-items: center;
            }

            .controls select, .controls button {
                padding: 8px 16px;
                background: #3e3e42;
                color: #d4d4d4;
                border: 1px solid #555;
                border-radius: 4px;
                font-family: inherit;
                font-size: 13px;
                cursor: pointer;
            }

            .controls button:hover {
                background: #505050;
            }

            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }

            .metric-card {
                background: #252526;
                padding: 20px;
                border-radius: 8px;
                border: 1px solid #3e3e42;
            }

            .metric-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
                padding-bottom: 10px;
                border-bottom: 1px solid #3e3e42;
            }

            .metric-title {
                color: #4ec9b0;
                font-size: 14px;
                font-weight: bold;
                text-transform: uppercase;
                letter-spacing: 1px;
            }

            .status-indicator {
                width: 10px;
                height: 10px;
                border-radius: 50%;
                display: inline-block;
            }

            .status-healthy {
                background: #4ec9b0;
                box-shadow: 0 0 10px #4ec9b0;
            }

            .status-degraded {
                background: #ce9178;
                box-shadow: 0 0 10px #ce9178;
            }

            .status-error {
                background: #f48771;
                box-shadow: 0 0 10px #f48771;
            }

            .metric-row {
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px solid #2d2d30;
            }

            .metric-row:last-child {
                border-bottom: none;
            }

            .metric-label {
                color: #858585;
                font-size: 13px;
            }

            .metric-value {
                color: #d4d4d4;
                font-size: 13px;
                font-weight: bold;
            }

            .metric-value.good {
                color: #4ec9b0;
            }

            .metric-value.warning {
                color: #ce9178;
            }

            .metric-value.bad {
                color: #f48771;
            }

            .loading {
                text-align: center;
                padding: 40px;
                color: #858585;
            }

            .chart-container {
                background: #252526;
                padding: 20px;
                border-radius: 8px;
                border: 1px solid #3e3e42;
                margin-bottom: 20px;
            }

            table {
                width: 100%;
                border-collapse: collapse;
            }

            th {
                color: #4ec9b0;
                text-align: left;
                padding: 10px;
                border-bottom: 2px solid #3e3e42;
                font-size: 12px;
                text-transform: uppercase;
            }

            td {
                padding: 10px;
                border-bottom: 1px solid #2d2d30;
                font-size: 13px;
            }

            .timestamp {
                color: #858585;
                font-size: 12px;
                margin-top: 20px;
                text-align: right;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>⚡ TutorMax Performance Dashboard</h1>
                <p class="subtitle">Real-time System Performance Monitoring for Engineers</p>
                <div class="controls">
                    <label for="timeRange">Time Range:</label>
                    <select id="timeRange" onchange="loadDashboard()">
                        <option value="1">Last Hour</option>
                        <option value="6">Last 6 Hours</option>
                        <option value="24" selected>Last 24 Hours</option>
                        <option value="168">Last 7 Days</option>
                    </select>
                    <button onclick="loadDashboard()">🔄 Refresh</button>
                    <span id="autoRefresh" style="margin-left: auto; color: #858585;">Auto-refresh: 30s</span>
                </div>
            </header>

            <div id="dashboard-content">
                <div class="loading">Loading performance metrics...</div>
            </div>
        </div>

        <script>
            async function loadDashboard() {
                const hours = document.getElementById('timeRange').value;
                const content = document.getElementById('dashboard-content');

                try {
                    content.innerHTML = '<div class="loading">Loading performance metrics...</div>';

                    const response = await fetch(`/api/performance/dashboard?hours=${hours}`);
                    const data = await response.json();

                    renderDashboard(data);
                } catch (error) {
                    content.innerHTML = `<div class="loading">Error: ${error.message}</div>`;
                }
            }

            function renderDashboard(data) {
                const content = document.getElementById('dashboard-content');
                const api = data.api_response_times;
                const db = data.database_performance;
                const queues = data.worker_queues;
                const redis = data.redis_performance;
                const tasks = data.celery_tasks;

                content.innerHTML = `
                    <div class="metrics-grid">
                        <!-- API Response Times -->
                        <div class="metric-card">
                            <div class="metric-header">
                                <span class="metric-title">API Response Times</span>
                                <span class="status-indicator ${api.meets_p95_sla ? 'status-healthy' : 'status-degraded'}"></span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">P50 (Median)</span>
                                <span class="metric-value">${api.p50_ms} ms</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">P95</span>
                                <span class="metric-value ${api.meets_p95_sla ? 'good' : 'warning'}">${api.p95_ms} ms</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">P99</span>
                                <span class="metric-value ${api.meets_p99_sla ? 'good' : 'warning'}">${api.p99_ms} ms</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Average</span>
                                <span class="metric-value">${api.average_ms} ms</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Samples</span>
                                <span class="metric-value">${api.sample_count}</span>
                            </div>
                        </div>

                        <!-- Database Performance -->
                        <div class="metric-card">
                            <div class="metric-header">
                                <span class="metric-title">Database Performance</span>
                                <span class="status-indicator status-${db.status}"></span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Cache Hit Ratio</span>
                                <span class="metric-value ${db.cache_hit_ratio > 90 ? 'good' : 'warning'}">${db.cache_hit_ratio}%</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Active Connections</span>
                                <span class="metric-value">${db.active_connections}</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Slow Queries</span>
                                <span class="metric-value ${db.slow_queries_count > 0 ? 'warning' : 'good'}">${db.slow_queries_count}</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Database Size</span>
                                <span class="metric-value">${db.database_size_mb} MB</span>
                            </div>
                        </div>

                        <!-- Redis Performance -->
                        <div class="metric-card">
                            <div class="metric-header">
                                <span class="metric-title">Redis Cache</span>
                                <span class="status-indicator status-${redis.status}"></span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Hit Rate</span>
                                <span class="metric-value ${redis.hit_rate_percentage > 80 ? 'good' : 'warning'}">${redis.hit_rate_percentage}%</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Memory Used</span>
                                <span class="metric-value">${redis.memory.used_mb} MB</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Ops/Sec</span>
                                <span class="metric-value">${redis.operations_per_second}</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Connected Clients</span>
                                <span class="metric-value">${redis.connections.connected_clients}</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Evicted Keys</span>
                                <span class="metric-value ${redis.evicted_keys > 0 ? 'warning' : 'good'}">${redis.evicted_keys}</span>
                            </div>
                        </div>

                        <!-- Worker Queues -->
                        <div class="metric-card">
                            <div class="metric-header">
                                <span class="metric-title">Worker Queues</span>
                                <span class="status-indicator status-${queues.status}"></span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Total Backlog</span>
                                <span class="metric-value ${queues.total_backlog > 1000 ? 'warning' : 'good'}">${queues.total_backlog}</span>
                            </div>
                            ${Object.entries(queues.queue_lengths).map(([name, length]) => `
                                <div class="metric-row">
                                    <span class="metric-label">${name}</span>
                                    <span class="metric-value ${length > 100 ? 'warning' : ''}">${length}</span>
                                </div>
                            `).join('')}
                        </div>

                        <!-- Celery Tasks -->
                        <div class="metric-card">
                            <div class="metric-header">
                                <span class="metric-title">Celery Tasks</span>
                                <span class="status-indicator status-${tasks.status}"></span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Success Rate</span>
                                <span class="metric-value ${tasks.overall_success_rate > 95 ? 'good' : 'warning'}">${tasks.overall_success_rate}%</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Total Executions</span>
                                <span class="metric-value">${tasks.total_executions}</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Successful</span>
                                <span class="metric-value good">${tasks.successful}</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Failed</span>
                                <span class="metric-value ${tasks.failed > 0 ? 'warning' : ''}">${tasks.failed}</span>
                            </div>
                        </div>

                        <!-- Overall Health -->
                        <div class="metric-card">
                            <div class="metric-header">
                                <span class="metric-title">Overall Health</span>
                                <span class="status-indicator status-${data.overall_health}"></span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">System Status</span>
                                <span class="metric-value ${data.overall_health === 'healthy' ? 'good' : 'warning'}">${data.overall_health.toUpperCase()}</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">API SLA</span>
                                <span class="metric-value ${api.meets_p95_sla ? 'good' : 'bad'}">${api.meets_p95_sla ? 'MET' : 'VIOLATED'}</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Database</span>
                                <span class="metric-value ${db.status === 'healthy' ? 'good' : 'warning'}">${db.status.toUpperCase()}</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Redis</span>
                                <span class="metric-value ${redis.status === 'healthy' ? 'good' : 'warning'}">${redis.status.toUpperCase()}</span>
                            </div>
                        </div>
                    </div>

                    <p class="timestamp">Last updated: ${new Date(data.timestamp).toLocaleString()}</p>
                `;
            }

            // Load dashboard on page load
            loadDashboard();

            // Auto-refresh every 30 seconds
            setInterval(loadDashboard, 30000);
        </script>
    </body>
    </html>
    """

    return html_content
