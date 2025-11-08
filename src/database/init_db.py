"""
Database initialization script for TutorMax.
Creates tables and optionally seeds with sample data.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.connection import init_db, close_db, get_settings


async def main():
    """Initialize the database."""
    print("=" * 60)
    print("TutorMax Database Initialization")
    print("=" * 60)

    settings = get_settings()
    print(f"\nDatabase Configuration:")
    print(f"  Host: {settings.postgres_host}")
    print(f"  Port: {settings.postgres_port}")
    print(f"  Database: {settings.postgres_db}")
    print(f"  User: {settings.postgres_user}")

    # Warning about destructive operations
    print("\n" + "!" * 60)
    print("WARNING: This will create all database tables.")
    print("If tables already exist, this may fail.")
    print("Use Alembic migrations for production databases.")
    print("!" * 60)

    response = input("\nProceed with initialization? (yes/no): ")
    if response.lower() != "yes":
        print("Initialization cancelled.")
        return

    try:
        # Initialize database
        await init_db(drop_all=False)
        print("\nDatabase initialized successfully!")

        # Display next steps
        print("\n" + "=" * 60)
        print("Next Steps:")
        print("=" * 60)
        print("\n1. Verify database tables:")
        print("   psql -U tutormax -d tutormax -c '\\dt'")
        print("\n2. Run the synthetic data generator:")
        print("   python demo_data_generation.py")
        print("\n3. Use Alembic for future schema changes:")
        print("   alembic revision --autogenerate -m 'Description'")
        print("   alembic upgrade head")
        print("\n" + "=" * 60)

    except Exception as e:
        print(f"\nError during initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
