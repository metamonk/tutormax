"""
Load testing script for TutorMax API using Locust.

Simulates 30,000 sessions/day load (347 sessions/hour, ~6 sessions/minute).

Usage:
    locust -f tests/load_testing/locustfile.py --host=http://localhost:8000

Then open http://localhost:8089 to configure and start the test.

Target metrics:
- 30,000 sessions/day
- p95 API response time < 200ms
- Cache hit rate > 80%
- No failed requests under normal load
"""

import random
import json
from datetime import datetime, timedelta
from typing import Dict, Any

from locust import HttpUser, task, between, events
from locust.exception import RescheduleTask


class TutorMaxUser(HttpUser):
    """
    Simulates a TutorMax API user (data ingestion and dashboard access).
    """

    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    host = "http://localhost:8000"

    def on_start(self):
        """Called when a user starts. Initialize test data."""
        self.tutor_ids = [f"T{str(i).zfill(6)}" for i in range(1, 1001)]  # 1000 tutors
        self.student_ids = [f"S{str(i).zfill(6)}" for i in range(1, 5001)]  # 5000 students
        self.session_counter = 0

    # ==================== Health Check Tasks ====================

    @task(5)
    def health_check(self):
        """Check API health - lightweight request."""
        with self.client.get(
            "/health",
            catch_response=True,
            name="/health"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    # ==================== Data Ingestion Tasks ====================

    @task(10)
    def ingest_session(self):
        """Ingest a single session - primary workload."""
        tutor_id = random.choice(self.tutor_ids)
        student_id = random.choice(self.student_ids)
        self.session_counter += 1

        session_data = {
            "session_id": f"SES{self.session_counter:010d}",
            "tutor_id": tutor_id,
            "student_id": student_id,
            "session_number": random.randint(1, 50),
            "scheduled_start": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
            "actual_start": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
            "duration_minutes": random.choice([30, 45, 60]),
            "subject": random.choice(["Math", "Science", "English", "History"]),
            "session_type": random.choice(["1-on-1", "group"]),
            "tutor_initiated_reschedule": random.random() < 0.1,
            "no_show": random.random() < 0.05,
            "late_start_minutes": random.randint(0, 15) if random.random() < 0.2 else 0,
            "engagement_score": round(random.uniform(3.0, 5.0), 2),
            "learning_objectives_met": random.random() < 0.85,
            "technical_issues": random.random() < 0.1
        }

        with self.client.post(
            "/api/sessions",
            json=session_data,
            catch_response=True,
            name="/api/sessions [POST]"
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Session ingestion failed: {response.status_code}")

    @task(5)
    def ingest_sessions_batch(self):
        """Ingest batch of sessions - testing batch endpoint."""
        batch_size = random.randint(5, 20)
        sessions = []

        for i in range(batch_size):
            tutor_id = random.choice(self.tutor_ids)
            student_id = random.choice(self.student_ids)
            self.session_counter += 1

            sessions.append({
                "session_id": f"SES{self.session_counter:010d}",
                "tutor_id": tutor_id,
                "student_id": student_id,
                "session_number": random.randint(1, 50),
                "scheduled_start": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                "actual_start": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                "duration_minutes": random.choice([30, 45, 60]),
                "subject": random.choice(["Math", "Science", "English", "History"]),
                "session_type": random.choice(["1-on-1", "group"]),
                "tutor_initiated_reschedule": random.random() < 0.1,
                "no_show": random.random() < 0.05,
                "late_start_minutes": random.randint(0, 15) if random.random() < 0.2 else 0,
                "engagement_score": round(random.uniform(3.0, 5.0), 2),
                "learning_objectives_met": random.random() < 0.85,
                "technical_issues": random.random() < 0.1
            })

        with self.client.post(
            "/api/sessions/batch",
            json=sessions,
            catch_response=True,
            name=f"/api/sessions/batch [POST] (n={batch_size})"
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Batch ingestion failed: {response.status_code}")

    @task(8)
    def ingest_feedback(self):
        """Ingest student feedback."""
        tutor_id = random.choice(self.tutor_ids)
        student_id = random.choice(self.student_ids)
        session_id = f"SES{random.randint(1, self.session_counter or 1000):010d}"

        feedback_data = {
            "feedback_id": f"FB{random.randint(1, 100000):010d}",
            "session_id": session_id,
            "student_id": student_id,
            "tutor_id": tutor_id,
            "overall_rating": random.randint(1, 5),
            "is_first_session": random.random() < 0.1,
            "subject_knowledge_rating": random.randint(3, 5),
            "communication_rating": random.randint(3, 5),
            "patience_rating": random.randint(3, 5),
            "engagement_rating": random.randint(3, 5),
            "helpfulness_rating": random.randint(3, 5),
            "would_recommend": random.random() < 0.85,
            "improvement_areas": random.sample(
                ["communication", "patience", "subject_knowledge", "engagement"],
                random.randint(0, 2)
            ),
            "free_text_feedback": "Great session!" if random.random() < 0.7 else None,
            "submitted_at": datetime.now().isoformat()
        }

        with self.client.post(
            "/api/feedback",
            json=feedback_data,
            catch_response=True,
            name="/api/feedback [POST]"
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Feedback ingestion failed: {response.status_code}")

    # ==================== Dashboard/Read Tasks ====================

    @task(15)
    def get_prediction(self):
        """Get churn prediction for a tutor - frequently accessed."""
        tutor_id = random.choice(self.tutor_ids)

        with self.client.get(
            f"/api/predictions/{tutor_id}",
            catch_response=True,
            name="/api/predictions/{tutor_id} [GET]"
        ) as response:
            if response.status_code in [200, 404]:
                # 404 is acceptable if prediction doesn't exist yet
                response.success()
            else:
                response.failure(f"Get prediction failed: {response.status_code}")

    @task(12)
    def get_tutor_portal_data(self):
        """Get tutor portal dashboard data."""
        tutor_id = random.choice(self.tutor_ids)

        with self.client.get(
            f"/api/tutor-portal/{tutor_id}/dashboard",
            catch_response=True,
            name="/api/tutor-portal/{tutor_id}/dashboard [GET]"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Get portal data failed: {response.status_code}")

    @task(8)
    def get_performance_dashboard(self):
        """Get performance dashboard data."""
        with self.client.get(
            "/api/performance-dashboard/summary",
            catch_response=True,
            name="/api/performance-dashboard/summary [GET]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get dashboard failed: {response.status_code}")

    @task(5)
    def get_queue_stats(self):
        """Get queue statistics - monitoring endpoint."""
        with self.client.get(
            "/api/queue/stats",
            catch_response=True,
            name="/api/queue/stats [GET]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get queue stats failed: {response.status_code}")


class DashboardUser(HttpUser):
    """
    Simulates dashboard users (operations managers viewing performance data).
    """

    wait_time = between(5, 15)  # Dashboard users browse more slowly
    host = "http://localhost:8000"

    def on_start(self):
        """Initialize dashboard user."""
        self.tutor_ids = [f"T{str(i).zfill(6)}" for i in range(1, 1001)]

    @task(20)
    def view_performance_dashboard(self):
        """View main performance dashboard."""
        with self.client.get(
            "/api/performance-dashboard/summary",
            name="Dashboard: Summary"
        ) as response:
            pass

    @task(15)
    def view_tutor_list(self):
        """View tutor list with performance tiers."""
        with self.client.get(
            "/api/performance-dashboard/tutors?performance_tier=At Risk",
            name="Dashboard: At-Risk Tutors"
        ) as response:
            pass

    @task(10)
    def view_tutor_details(self):
        """View individual tutor details."""
        tutor_id = random.choice(self.tutor_ids)
        with self.client.get(
            f"/api/tutor-portal/{tutor_id}/dashboard",
            name="Dashboard: Tutor Details"
        ) as response:
            pass

    @task(8)
    def view_interventions(self):
        """View intervention queue."""
        with self.client.get(
            "/api/interventions?status=pending",
            name="Dashboard: Pending Interventions"
        ) as response:
            pass


# ==================== Custom Metrics ====================

@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """
    Initialize custom metrics tracking.
    """
    environment.custom_metrics = {
        "cache_hits": 0,
        "cache_misses": 0
    }


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    """
    Track custom metrics for each request.
    """
    # This would be enhanced to parse cache headers from responses
    # For now, it's a placeholder for custom metric tracking
    pass


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    Report custom metrics at test end.
    """
    print("\n" + "="*80)
    print("CUSTOM PERFORMANCE METRICS")
    print("="*80)

    if hasattr(environment, 'custom_metrics'):
        total_cache_requests = environment.custom_metrics.get('cache_hits', 0) + environment.custom_metrics.get('cache_misses', 0)
        cache_hit_rate = (
            environment.custom_metrics.get('cache_hits', 0) / total_cache_requests * 100
            if total_cache_requests > 0
            else 0
        )
        print(f"Cache Hit Rate: {cache_hit_rate:.2f}%")

    print("="*80 + "\n")
