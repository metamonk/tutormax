#!/usr/bin/env python3
"""
Create a test user for authentication testing.

This script creates a test admin user and a test regular user.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from src.database.database import async_session_maker
from src.database.models import User, UserRole, Tutor
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def check_and_create_users():
    """Check for existing users and create test users if needed."""

    print("=" * 60)
    print("TutorMax User Management")
    print("=" * 60)

    async with async_session_maker() as session:
        # Check for existing users
        result = await session.execute(select(User))
        existing_users = result.scalars().all()

        if existing_users:
            print(f"\n✓ Found {len(existing_users)} existing user(s):\n")
            for user in existing_users:
                print(f"  ID: {user.id}")
                print(f"  Email: {user.email}")
                print(f"  Name: {user.full_name}")
                print(f"  Roles: {user.roles}")
                print(f"  Superuser: {user.is_superuser}")
                print(f"  Active: {user.is_active}")
                print()

            print("=" * 60)
            response = input("\nCreate additional test users? (y/N): ").strip().lower()
            if response != 'y':
                print("Exiting...")
                return
        else:
            print("\n✗ No users found in database")
            print("\nCreating test users...")

        # Create test admin user
        admin_email = "admin@tutormax.com"
        admin_exists = await session.execute(
            select(User).where(User.email == admin_email)
        )
        if not admin_exists.scalar():
            admin_user = User(
                email=admin_email,
                hashed_password=pwd_context.hash("admin123"),  # CHANGE IN PRODUCTION!
                full_name="Admin User",
                roles=[UserRole.ADMIN],
                is_active=True,
                is_superuser=True,
                is_verified=True,
            )
            session.add(admin_user)
            print(f"\n✓ Created admin user: {admin_email}")
            print(f"  Password: admin123")
        else:
            print(f"\n• Admin user already exists: {admin_email}")

        # Create test tutor user
        tutor_email = "tutor@tutormax.com"
        tutor_exists = await session.execute(
            select(User).where(User.email == tutor_email)
        )
        existing_tutor_user = tutor_exists.scalar()

        # Get a tutor record to link to
        first_tutor = await session.execute(select(Tutor).limit(1))
        tutor_record = first_tutor.scalar()
        tutor_id = tutor_record.tutor_id if tutor_record else None

        if not existing_tutor_user:
            tutor_user = User(
                email=tutor_email,
                hashed_password=pwd_context.hash("tutor123"),  # CHANGE IN PRODUCTION!
                full_name="Test Tutor",
                roles=[UserRole.TUTOR],
                is_active=True,
                is_superuser=False,
                is_verified=True,
                tutor_id=tutor_id,
            )
            session.add(tutor_user)
            print(f"\n✓ Created tutor user: {tutor_email}")
            print(f"  Password: tutor123")
            print(f"  Linked to tutor: {tutor_id}")
        else:
            # Update existing tutor user to have tutor_id if missing
            if not existing_tutor_user.tutor_id and tutor_id:
                existing_tutor_user.tutor_id = tutor_id
                print(f"\n• Tutor user already exists: {tutor_email}")
                print(f"  Updated with tutor_id: {tutor_id}")
            else:
                print(f"\n• Tutor user already exists: {tutor_email}")

        # Create test student user
        student_email = "student@tutormax.com"
        student_exists = await session.execute(
            select(User).where(User.email == student_email)
        )
        if not student_exists.scalar():
            student_user = User(
                email=student_email,
                hashed_password=pwd_context.hash("student123"),  # CHANGE IN PRODUCTION!
                full_name="Test Student",
                roles=[UserRole.STUDENT],
                is_active=True,
                is_superuser=False,
                is_verified=True,
            )
            session.add(student_user)
            print(f"\n✓ Created student user: {student_email}")
            print(f"  Password: student123")
        else:
            print(f"\n• Student user already exists: {student_email}")

        # Commit all changes
        await session.commit()

        print("\n" + "=" * 60)
        print("Test Users Summary")
        print("=" * 60)
        print("\n1. Admin User:")
        print("   Email: admin@tutormax.com")
        print("   Password: admin123")
        print("   Roles: admin, superuser")
        print("\n2. Tutor User:")
        print("   Email: tutor@tutormax.com")
        print("   Password: tutor123")
        print("   Roles: tutor")
        print("\n3. Student User:")
        print("   Email: student@tutormax.com")
        print("   Password: student123")
        print("   Roles: student")
        print("\n" + "=" * 60)
        print("\n⚠️  WARNING: These are TEST credentials only!")
        print("    CHANGE passwords in production!")
        print("\nLogin endpoint: POST /auth/jwt/login")
        print("Register endpoint: POST /auth/register")
        print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(check_and_create_users())
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
