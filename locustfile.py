"""
TutorMax Load Testing with Locust

This file defines load testing scenarios for the TutorMax platform.
Target: 30,000 sessions/day = ~21 sessions/minute = ~0.35 sessions/second

Run with:
    locust -f locustfile.py --host=http://localhost:8000

For headless mode:
    locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 5m --headless
"""

import random
import json
from datetime import datetime, timedelta
from locust import HttpUser, task, between, SequentialTaskSet


class DashboardBrowsingBehavior(SequentialTaskSet):
    """
    Simulates operations manager browsing the dashboard.
    Most common user behavior - viewing real-time data.
    """

    @task
    def login(self):
        """Authenticate user"""
        self.client.post("/api/auth/login", json={
            "username": "ops_manager@tutormax.com",
            "password": "test_password"
        })

    @task
    def view_dashboard(self):
        """View main dashboard"""
        with self.client.get("/api/dashboard/metrics", name="/api/dashboard/metrics", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Dashboard failed: {response.status_code}")

    @task
    def view_performance_analytics(self):
        """View performance analytics"""
        self.client.get("/api/performance/analytics")

    @task
    def view_critical_alerts(self):
        """View critical alerts"""
        self.client.get("/api/alerts?status=active")

    @task
    def view_intervention_tasks(self):
        """View pending interventions"""
        self.client.get("/api/interventions?status=pending")


class SessionCreationBehavior(SequentialTaskSet):
    """
    Simulates session creation workflow.
    Target: 30,000 sessions/day
    """

    def on_start(self):
        """Initialize session data"""
        self.tutor_id = random.randint(1, 100)
        self.student_id = random.randint(1, 500)

    @task
    def create_session(self):
        """Create a tutoring session"""
        session_data = {
            "tutor_id": self.tutor_id,
            "student_id": self.student_id,
            "subject": random.choice(["Math", "Science", "English", "History", "Programming"]),
            "scheduled_start": (datetime.now() + timedelta(days=random.randint(1, 7))).isoformat(),
            "duration_minutes": random.choice([30, 60, 90]),
            "session_type": random.choice(["one-on-one", "group"]),
        }

        with self.client.post("/api/sessions", json=session_data, name="/api/sessions [CREATE]", catch_response=True) as response:
            if response.status_code in [200, 201]:
                response.success()
                # Store session ID for later use
                try:
                    self.session_id = response.json().get("id")
                except:
                    pass
            else:
                response.failure(f"Session creation failed: {response.status_code}")

    @task
    def update_session(self):
        """Update session with actual start time"""
        if hasattr(self, 'session_id'):
            self.client.patch(f"/api/sessions/{self.session_id}", json={
                "actual_start": datetime.now().isoformat()
            })


class TutorPerformanceBehavior(SequentialTaskSet):
    """
    Simulates viewing tutor performance data.
    Used by operations managers.
    """

    def on_start(self):
        """Initialize tutor IDs"""
        self.tutor_ids = list(range(1, 101))

    @task(3)
    def view_tutor_list(self):
        """View list of tutors with metrics"""
        self.client.get("/api/tutors?include_metrics=true")

    @task(2)
    def view_specific_tutor(self):
        """View specific tutor profile"""
        tutor_id = random.choice(self.tutor_ids)
        self.client.get(f"/api/tutors/{tutor_id}")

    @task(2)
    def view_tutor_sessions(self):
        """View tutor's recent sessions"""
        tutor_id = random.choice(self.tutor_ids)
        self.client.get(f"/api/tutors/{tutor_id}/sessions?limit=50")

    @task(1)
    def view_tutor_recommendations(self):
        """View training recommendations for tutor"""
        tutor_id = random.choice(self.tutor_ids)
        self.client.get(f"/api/tutors/{tutor_id}/recommendations")


class InterventionManagementBehavior(SequentialTaskSet):
    """
    Simulates intervention management workflow.
    Operations managers assigning and tracking interventions.
    """

    @task(3)
    def view_intervention_queue(self):
        """View intervention queue"""
        self.client.get("/api/interventions?status=pending&sort=priority")

    @task(2)
    def view_intervention_details(self):
        """View specific intervention"""
        intervention_id = random.randint(1, 100)
        self.client.get(f"/api/interventions/{intervention_id}")

    @task(1)
    def assign_intervention(self):
        """Assign intervention to a tutor"""
        intervention_id = random.randint(1, 100)
        self.client.post(f"/api/interventions/{intervention_id}/assign", json={
            "assigned_to": f"ops_manager_{random.randint(1, 10)}@tutormax.com",
            "priority": random.choice(["high", "medium", "low"])
        })

    @task(1)
    def record_outcome(self):
        """Record intervention outcome"""
        intervention_id = random.randint(1, 100)
        self.client.post(f"/api/interventions/{intervention_id}/outcome", json={
            "status": "completed",
            "outcome": random.choice(["improved", "no_change", "declined"]),
            "notes": "Intervention completed successfully"
        })


class AdminUserManagementBehavior(SequentialTaskSet):
    """
    Simulates admin managing users.
    Lower frequency but important for testing admin endpoints.
    """

    @task(4)
    def view_users(self):
        """View user list"""
        self.client.get("/api/admin/users?page=1&limit=50")

    @task(2)
    def search_users(self):
        """Search for specific user"""
        search_term = random.choice(["john", "smith", "tutor", "admin"])
        self.client.get(f"/api/admin/users?search={search_term}")

    @task(1)
    def view_user_details(self):
        """View specific user"""
        user_id = random.randint(1, 200)
        self.client.get(f"/api/admin/users/{user_id}")

    @task(1)
    def update_user_roles(self):
        """Update user roles"""
        user_id = random.randint(1, 200)
        self.client.patch(f"/api/admin/users/{user_id}/roles", json={
            "roles": ["tutor"]
        })


class StudentFeedbackBehavior(SequentialTaskSet):
    """
    Simulates students providing feedback after sessions.
    """

    def on_start(self):
        """Initialize feedback token"""
        self.token = f"feedback_token_{random.randint(1000, 9999)}"

    @task
    def submit_feedback(self):
        """Submit session feedback"""
        feedback_data = {
            "rating": random.randint(3, 5),
            "tutor_knowledge": random.randint(3, 5),
            "communication": random.randint(3, 5),
            "helpfulness": random.randint(3, 5),
            "would_recommend": random.choice([True, False]),
            "comments": "Great session, learned a lot!"
        }

        self.client.post(f"/api/feedback/{self.token}", json=feedback_data, name="/api/feedback/[token]")


# ============================================================================
# User Types with Different Behaviors
# ============================================================================

class DashboardUser(HttpUser):
    """
    Operations manager viewing dashboard (most common).
    Weight: 40% of users
    """
    wait_time = between(5, 15)
    tasks = [DashboardBrowsingBehavior]
    weight = 40


class SessionCreator(HttpUser):
    """
    Users creating new tutoring sessions.
    Weight: 20% of users (high session creation rate)
    """
    wait_time = between(10, 30)
    tasks = [SessionCreationBehavior]
    weight = 20


class TutorPerformanceViewer(HttpUser):
    """
    Managers viewing tutor performance data.
    Weight: 15% of users
    """
    wait_time = between(8, 20)
    tasks = [TutorPerformanceBehavior]
    weight = 15


class InterventionManager(HttpUser):
    """
    Operations team managing interventions.
    Weight: 15% of users
    """
    wait_time = between(10, 25)
    tasks = [InterventionManagementBehavior]
    weight = 15


class AdminUser(HttpUser):
    """
    Admins managing users and system settings.
    Weight: 5% of users (lower frequency)
    """
    wait_time = between(15, 40)
    tasks = [AdminUserManagementBehavior]
    weight = 5


class StudentFeedbackUser(HttpUser):
    """
    Students submitting feedback after sessions.
    Weight: 5% of users
    """
    wait_time = between(60, 180)
    tasks = [StudentFeedbackBehavior]
    weight = 5
