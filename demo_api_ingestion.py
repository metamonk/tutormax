"""
Demonstration script for the FastAPI data ingestion pipeline.

This script generates synthetic data and sends it to the API endpoints,
demonstrating the complete data flow from generation to Redis queuing.
"""

import asyncio
import sys
from datetime import datetime
from typing import List, Dict

import httpx
from src.data_generation.tutor_generator import TutorGenerator
from src.data_generation.session_generator import SessionGenerator
from src.data_generation.feedback_generator import FeedbackGenerator


# API configuration
API_BASE_URL = "http://localhost:8000"
API_TIMEOUT = 30.0


class APIIngestionDemo:
    """Demonstrates the data ingestion API with synthetic data."""

    def __init__(self, api_base_url: str = API_BASE_URL):
        """
        Initialize the demo.

        Args:
            api_base_url: Base URL of the API
        """
        self.api_base_url = api_base_url
        self.tutor_gen = TutorGenerator(seed=42)
        self.session_gen = SessionGenerator(seed=42)
        self.feedback_gen = FeedbackGenerator(seed=42)

    async def check_health(self) -> bool:
        """
        Check if the API is healthy and Redis is connected.

        Returns:
            True if healthy, False otherwise
        """
        print("\n=== Checking API Health ===")
        try:
            async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
                response = await client.get(f"{self.api_base_url}/health")
                data = response.json()

                print(f"Status: {data['status']}")
                print(f"Redis Connected: {data['redis_connected']}")
                print(f"Version: {data['version']}")
                print(f"Timestamp: {data['timestamp']}")

                return data['redis_connected']

        except Exception as e:
            print(f"Error checking health: {e}")
            return False

    async def ingest_tutors(self, count: int = 5) -> List[str]:
        """
        Generate and ingest tutor profiles.

        Args:
            count: Number of tutors to generate

        Returns:
            List of tutor IDs that were successfully ingested
        """
        print(f"\n=== Ingesting {count} Tutors ===")

        # Generate tutors
        tutors = self.tutor_gen.generate_tutors(count=count)
        tutor_ids = []

        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            for tutor in tutors:
                try:
                    response = await client.post(
                        f"{self.api_base_url}/api/tutors",
                        json=tutor
                    )
                    response.raise_for_status()
                    result = response.json()

                    if result['success']:
                        tutor_ids.append(tutor['tutor_id'])
                        print(f"  ✓ {tutor['tutor_id']} - {tutor['name']} ({tutor['behavioral_archetype']})")
                    else:
                        print(f"  ✗ Failed to ingest {tutor['tutor_id']}: {result.get('message')}")

                except Exception as e:
                    print(f"  ✗ Error ingesting {tutor['tutor_id']}: {e}")

        print(f"Successfully ingested {len(tutor_ids)}/{count} tutors")
        return tutor_ids

    async def ingest_tutors_batch(self, count: int = 10) -> int:
        """
        Generate and ingest tutor profiles in batch.

        Args:
            count: Number of tutors to generate

        Returns:
            Number of tutors successfully ingested
        """
        print(f"\n=== Batch Ingesting {count} Tutors ===")

        # Generate tutors
        tutors = self.tutor_gen.generate_tutors(count=count)

        try:
            async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
                response = await client.post(
                    f"{self.api_base_url}/api/tutors/batch",
                    json=tutors
                )
                response.raise_for_status()
                result = response.json()

                print(f"  Result: {result['message']}")
                print(f"  Success: {result['count']}/{count}")

                if result['errors']:
                    print(f"  Errors: {len(result['errors'])}")

                return result['count']

        except Exception as e:
            print(f"  ✗ Batch ingestion failed: {e}")
            return 0

    async def ingest_sessions(self, tutors: List[Dict], count: int = 20) -> List[str]:
        """
        Generate and ingest session data.

        Args:
            tutors: List of tutor profiles
            count: Number of sessions to generate

        Returns:
            List of session IDs that were successfully ingested
        """
        print(f"\n=== Ingesting {count} Sessions ===")

        sessions = []
        session_ids = []

        # Generate sessions
        for _ in range(count):
            tutor = tutors[_ % len(tutors)]  # Cycle through tutors
            session = self.session_gen.generate_session(tutor=tutor)
            sessions.append(session)

        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            for session in sessions:
                try:
                    response = await client.post(
                        f"{self.api_base_url}/api/sessions",
                        json=session
                    )
                    response.raise_for_status()
                    result = response.json()

                    if result['success']:
                        session_ids.append(session['session_id'])
                        status = "No-show" if session['no_show'] else f"Eng: {session['engagement_score']:.2f}"
                        print(f"  ✓ {session['session_id'][:8]}... - {session['subject']} ({status})")
                    else:
                        print(f"  ✗ Failed to ingest session: {result.get('message')}")

                except Exception as e:
                    print(f"  ✗ Error ingesting session: {e}")

        print(f"Successfully ingested {len(session_ids)}/{count} sessions")
        return session_ids

    async def ingest_feedback(
        self,
        sessions: List[Dict],
        tutors_by_id: Dict[str, Dict],
        count: int = 15
    ) -> List[str]:
        """
        Generate and ingest feedback data.

        Args:
            sessions: List of session data
            tutors_by_id: Dict mapping tutor_id to tutor profile
            count: Number of feedback entries to generate

        Returns:
            List of feedback IDs that were successfully ingested
        """
        print(f"\n=== Ingesting {count} Feedback Entries ===")

        feedbacks = []
        feedback_ids = []

        # Generate feedback for sessions (not all sessions get feedback)
        selected_sessions = sessions[:count]

        for session in selected_sessions:
            tutor = tutors_by_id.get(session['tutor_id'])
            if not tutor:
                continue

            feedback = self.feedback_gen.generate_feedback(session=session, tutor=tutor)
            if feedback:  # Skip None (no-show sessions)
                feedbacks.append(feedback)

        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            for feedback in feedbacks:
                try:
                    response = await client.post(
                        f"{self.api_base_url}/api/feedback",
                        json=feedback
                    )
                    response.raise_for_status()
                    result = response.json()

                    if result['success']:
                        feedback_ids.append(feedback['feedback_id'])
                        stars = "⭐" * feedback['overall_rating']
                        print(f"  ✓ {feedback['feedback_id'][:8]}... - {stars} ({feedback['overall_rating']}/5)")
                    else:
                        print(f"  ✗ Failed to ingest feedback: {result.get('message')}")

                except Exception as e:
                    print(f"  ✗ Error ingesting feedback: {e}")

        print(f"Successfully ingested {len(feedback_ids)}/{count} feedback entries")
        return feedback_ids

    async def get_queue_stats(self) -> Dict:
        """
        Get current queue statistics.

        Returns:
            Queue statistics dictionary
        """
        print("\n=== Queue Statistics ===")

        try:
            async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
                response = await client.get(f"{self.api_base_url}/api/queue/stats")
                response.raise_for_status()
                data = response.json()

                queues = data['queues']
                print(f"Tutors in queue: {queues['tutors']}")
                print(f"Sessions in queue: {queues['sessions']}")
                print(f"Feedbacks in queue: {queues['feedbacks']}")
                print(f"Total items: {sum(queues.values())}")

                return queues

        except Exception as e:
            print(f"Error getting queue stats: {e}")
            return {}

    async def run_demo(self):
        """Run the complete demonstration."""
        print("=" * 60)
        print("TutorMax API Data Ingestion Demonstration")
        print("=" * 60)

        # Check health
        is_healthy = await self.check_health()
        if not is_healthy:
            print("\n❌ API is not healthy or Redis is not connected!")
            print("Please ensure:")
            print("  1. FastAPI server is running (python -m src.api.main)")
            print("  2. Redis server is running (redis-server)")
            sys.exit(1)

        # Generate and ingest tutors (individual)
        tutors_data = self.tutor_gen.generate_tutors(count=5)
        tutor_ids = await self.ingest_tutors(count=5)

        # Batch ingest more tutors
        await self.ingest_tutors_batch(count=10)

        # Create tutor lookup dict
        tutors_by_id = {t['tutor_id']: t for t in tutors_data}

        # Generate and ingest sessions
        sessions_data = []
        for _ in range(30):
            tutor = tutors_data[_ % len(tutors_data)]
            session = self.session_gen.generate_session(tutor=tutor)
            sessions_data.append(session)

        session_ids = await self.ingest_sessions(tutors=tutors_data, count=30)

        # Generate and ingest feedback
        feedback_ids = await self.ingest_feedback(
            sessions=sessions_data,
            tutors_by_id=tutors_by_id,
            count=25
        )

        # Get final queue statistics
        await self.get_queue_stats()

        print("\n" + "=" * 60)
        print("Demo Summary:")
        print(f"  Tutors ingested: {len(tutor_ids) + 10}")  # 5 individual + 10 batch
        print(f"  Sessions ingested: {len(session_ids)}")
        print(f"  Feedback ingested: {len(feedback_ids)}")
        print("=" * 60)
        print("\n✓ Demo completed successfully!")
        print("\nNext steps:")
        print("  - View API docs: http://localhost:8000/docs")
        print("  - Check queue stats: curl http://localhost:8000/api/queue/stats")
        print("  - Process queued data with the data validation module (Task 2.2)")


async def main():
    """Main entry point."""
    demo = APIIngestionDemo()
    await demo.run_demo()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        sys.exit(1)
