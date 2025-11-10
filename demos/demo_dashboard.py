"""
Demo: Operations Dashboard with Real-Time WebSocket Updates

Demonstrates the complete dashboard functionality including:
- Real-time metrics updates via WebSocket
- Critical alerts generation
- Intervention task management
- Performance analytics

This demo simulates the full system workflow for ops/people ops monitoring.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import get_session
from src.database.models import Tutor, Session, TutorPerformanceMetric, StudentFeedback
from src.evaluation.performance_calculator import PerformanceCalculator, MetricWindow
from src.api.alert_service import AlertService
from src.api.websocket_service import ConnectionManager
from sqlalchemy import select


async def create_test_data():
    """
    Create test data with various performance levels.
    """
    print("\n" + "=" * 60)
    print("Creating Test Data for Dashboard Demo")
    print("=" * 60)

    async for db in get_session():
        # Create 5 tutors with different performance levels
        tutors_data = [
            {
                "tutor_id": "tutor_dashboard_001",
                "name": "Alice Johnson",
                "email": "alice@example.com",
                "rating": 4.8,  # Exemplary
                "sessions_completed": 45,
            },
            {
                "tutor_id": "tutor_dashboard_002",
                "name": "Bob Smith",
                "email": "bob@example.com",
                "rating": 4.2,  # Strong
                "sessions_completed": 32,
            },
            {
                "tutor_id": "tutor_dashboard_003",
                "name": "Carol Davis",
                "email": "carol@example.com",
                "rating": 3.5,  # Developing
                "sessions_completed": 28,
            },
            {
                "tutor_id": "tutor_dashboard_004",
                "name": "David Wilson",
                "email": "david@example.com",
                "rating": 2.8,  # Needs Support - CRITICAL
                "sessions_completed": 15,
            },
            {
                "tutor_id": "tutor_dashboard_005",
                "name": "Eve Martinez",
                "email": "eve@example.com",
                "rating": 4.5,  # Strong
                "sessions_completed": 38,
            },
        ]

        tutors = []
        for tutor_data in tutors_data:
            # Check if tutor exists
            query = select(Tutor).where(Tutor.tutor_id == tutor_data["tutor_id"])
            result = await db.execute(query)
            existing_tutor = result.scalars().first()

            if not existing_tutor:
                tutor = Tutor(
                    tutor_id=tutor_data["tutor_id"],
                    name=tutor_data["name"],
                    email=tutor_data["email"],
                    subjects_taught=["Math", "Science"],
                    years_experience=3,
                    education_level="Masters",
                    languages=["English"],
                    hourly_rate=50.0,
                    timezone="UTC",
                )
                db.add(tutor)
                tutors.append(tutor)
                print(f"✓ Created tutor: {tutor_data['name']} ({tutor_data['tutor_id']})")
            else:
                tutors.append(existing_tutor)
                print(f"  Using existing tutor: {tutor_data['name']}")

        await db.commit()

        # Create sessions and feedback for each tutor
        for tutor, tutor_data in zip(tutors, tutors_data):
            sessions_count = tutor_data["sessions_completed"]
            base_rating = tutor_data["rating"]

            for i in range(sessions_count):
                session_date = datetime.now() - timedelta(days=sessions_count - i)

                session = Session(
                    session_id=f"session_{tutor.tutor_id}_{i}",
                    tutor_id=tutor.tutor_id,
                    student_id=f"student_{i % 10}",
                    subject="Math",
                    start_time=session_date,
                    end_time=session_date + timedelta(hours=1),
                    status="completed",
                    duration_minutes=60,
                    # Simulate some no-shows for the struggling tutor
                    no_show=(tutor_data["rating"] < 3.0 and i % 3 == 0),
                    rescheduled=(tutor_data["rating"] < 3.5 and i % 4 == 0),
                )
                db.add(session)

                # Add feedback
                # Vary ratings slightly around base rating
                import random
                rating_variance = random.uniform(-0.3, 0.3)
                session_rating = max(1, min(5, base_rating + rating_variance))

                feedback = StudentFeedback(
                    feedback_id=f"feedback_{tutor.tutor_id}_{i}",
                    session_id=session.session_id,
                    tutor_id=tutor.tutor_id,
                    student_id=session.student_id,
                    rating=session_rating,
                    feedback_text="Session went well" if session_rating >= 4 else "Could be better",
                    submitted_at=session_date + timedelta(hours=2),
                    # Simulate varying engagement scores
                    engagement_score=max(50, min(100, session_rating * 20 + random.uniform(-5, 5))),
                    learning_objectives_met=session_rating >= 4,
                )
                db.add(feedback)

        await db.commit()
        print(f"\n✓ Created sessions and feedback for all tutors")

        return tutors


async def calculate_metrics_for_all_tutors(tutors):
    """
    Calculate performance metrics for all tutors.
    """
    print("\n" + "=" * 60)
    print("Calculating Performance Metrics")
    print("=" * 60)

    async for db in get_session():
        calculator = PerformanceCalculator(db)
        all_metrics = []

        for tutor in tutors:
            # Calculate 30-day metrics
            metrics = await calculator.calculate_metrics(
                tutor_id=tutor.tutor_id,
                window=MetricWindow.THIRTY_DAY
            )

            await calculator.save_metrics(metrics)
            all_metrics.append(metrics)

            print(f"✓ {tutor.name}: {metrics.performance_tier} tier")
            print(f"  Rating: {metrics.avg_rating:.2f}, Engagement: {metrics.engagement_score:.1f}")

        await db.commit()
        return all_metrics


async def generate_alerts_and_interventions(metrics_list, tutors):
    """
    Generate alerts and intervention tasks based on metrics.
    """
    print("\n" + "=" * 60)
    print("Generating Alerts and Interventions")
    print("=" * 60)

    alert_service = AlertService()
    all_alerts = []
    all_tasks = []

    for metrics, tutor in zip(metrics_list, tutors):
        # Generate alerts
        alerts = alert_service.generate_alerts(metrics, tutor.name)
        all_alerts.extend(alerts)

        if alerts:
            print(f"\n{tutor.name}:")
            for alert in alerts:
                print(f"  [{alert['alert_type'].upper()}] {alert['title']}")

        # Generate intervention tasks
        tasks = alert_service.generate_intervention_tasks(metrics, tutor.name, alerts)
        all_tasks.extend(tasks)

        if tasks:
            for task in tasks:
                print(f"  [TASK] {task['title']} (Priority: {task['priority']})")

    critical_count = sum(1 for a in all_alerts if a['alert_type'] == 'critical')
    warning_count = sum(1 for a in all_alerts if a['alert_type'] == 'warning')

    print(f"\n✓ Generated {len(all_alerts)} alerts ({critical_count} critical, {warning_count} warnings)")
    print(f"✓ Generated {len(all_tasks)} intervention tasks")

    return all_alerts, all_tasks


async def simulate_websocket_updates(metrics_list, tutors, alerts, tasks):
    """
    Simulate WebSocket updates being sent to dashboard.
    """
    print("\n" + "=" * 60)
    print("Simulating WebSocket Updates to Dashboard")
    print("=" * 60)

    manager = ConnectionManager()

    # Simulate metrics updates
    print("\n1. Broadcasting Metrics Updates:")
    for metrics, tutor in zip(metrics_list, tutors):
        metrics_data = {
            "tutor_id": metrics.tutor_id,
            "tutor_name": tutor.name,
            "window": metrics.window,
            "calculation_date": metrics.calculation_date.isoformat(),
            "sessions_completed": metrics.sessions_completed,
            "avg_rating": metrics.avg_rating,
            "first_session_success_rate": metrics.first_session_success_rate,
            "reschedule_rate": metrics.reschedule_rate,
            "no_show_count": metrics.no_show_count,
            "engagement_score": metrics.engagement_score,
            "learning_objectives_met_pct": metrics.learning_objectives_met_pct,
            "performance_tier": metrics.performance_tier,
        }

        print(f"   → Metrics update for {tutor.name}")
        # In production: await manager.broadcast("metrics_update", metrics_data)

    # Simulate alert broadcasts
    print("\n2. Broadcasting Critical Alerts:")
    for alert in alerts[:3]:  # Show first 3 alerts
        print(f"   → Alert: {alert['title']}")
        # In production: await manager.broadcast("alert", alert)

    # Simulate intervention task broadcasts
    print("\n3. Broadcasting Intervention Tasks:")
    for task in tasks[:3]:  # Show first 3 tasks
        print(f"   → Task: {task['title']} (Priority: {task['priority']})")
        # In production: await manager.broadcast("intervention", task)

    # Simulate analytics update
    print("\n4. Broadcasting Analytics Summary:")
    async for db in get_session():
        from sqlalchemy import func
        from src.database.models import TutorPerformanceMetric

        # Get performance distribution
        metrics_query = select(TutorPerformanceMetric).where(
            TutorPerformanceMetric.window == "30day"
        )
        result = await db.execute(metrics_query)
        all_metrics = result.scalars().all()

        performance_distribution = {
            "Needs Support": 0,
            "Developing": 0,
            "Strong": 0,
            "Exemplary": 0,
        }

        for m in all_metrics:
            performance_distribution[m.performance_tier] += 1

        analytics = {
            "total_tutors": len(tutors),
            "active_tutors": len(all_metrics),
            "performance_distribution": performance_distribution,
            "avg_rating": sum(m.avg_rating for m in all_metrics) / len(all_metrics),
            "avg_engagement_score": sum(m.engagement_score for m in all_metrics) / len(all_metrics),
            "total_sessions_7day": sum(m.sessions_completed for m in all_metrics),
            "total_sessions_30day": sum(m.sessions_completed for m in all_metrics),
            "alerts_count": {
                "critical": sum(1 for a in alerts if a['alert_type'] == 'critical'),
                "warning": sum(1 for a in alerts if a['alert_type'] == 'warning'),
                "info": 0,
            },
        }

        print(f"   → Analytics: {analytics['active_tutors']} active tutors")
        print(f"   → Distribution: {performance_distribution}")
        # In production: await manager.broadcast("analytics_update", analytics)

        break

    print("\n✓ All updates simulated (in production, these would be sent via WebSocket)")


async def main():
    """
    Main demo function.
    """
    print("\n" + "=" * 60)
    print("OPERATIONS DASHBOARD DEMO")
    print("Real-Time Monitoring System with WebSocket Updates")
    print("=" * 60)

    try:
        # Step 1: Create test data
        tutors = await create_test_data()

        # Step 2: Calculate metrics
        metrics_list = await calculate_metrics_for_all_tutors(tutors)

        # Step 3: Generate alerts and interventions
        alerts, tasks = await generate_alerts_and_interventions(metrics_list, tutors)

        # Step 4: Simulate WebSocket updates
        await simulate_websocket_updates(metrics_list, tutors, alerts, tasks)

        # Summary
        print("\n" + "=" * 60)
        print("DEMO SUMMARY")
        print("=" * 60)
        print(f"\nCreated:")
        print(f"  • {len(tutors)} tutors with varying performance levels")
        print(f"  • {len(metrics_list)} performance metric calculations")
        print(f"  • {len(alerts)} critical alerts")
        print(f"  • {len(tasks)} intervention tasks")

        print(f"\nDashboard Features Demonstrated:")
        print(f"  ✓ Real-time metrics updates")
        print(f"  ✓ Critical alerts with severity levels")
        print(f"  ✓ Intervention task generation")
        print(f"  ✓ Performance analytics aggregation")
        print(f"  ✓ WebSocket broadcasting (simulated)")

        print(f"\nTo view the dashboard:")
        print(f"  1. Start the FastAPI server:")
        print(f"     python -m uvicorn src.api.main:app --reload")
        print(f"  2. Start the React dashboard:")
        print(f"     cd frontend && npm start")
        print(f"  3. Open http://localhost:3000 in your browser")

        print("\n" + "=" * 60)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ Error in demo: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
