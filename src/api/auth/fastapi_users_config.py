"""
FastAPI-Users configuration for TutorMax authentication system.

This module sets up:
- User manager for CRUD operations
- Authentication backends (JWT)
- FastAPI-Users instance with all auth routers
"""

from typing import Optional
import uuid
from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, IntegerIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.models import User, UserRole
from ...database.database import get_async_session, async_session_maker
from ..config import settings


# Secret for JWT (use settings)
SECRET = settings.secret_key


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    """
    User manager for handling user operations.

    Provides hooks for:
    - User registration
    - Password reset
    - Email verification
    - User updates
    """

    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        """Called after successful user registration."""
        print(f"User {user.id} ({user.email}) has registered.")
        # Future enhancement: Send welcome email to new users
        # Use email_service.py to send branded welcome email with:
        # - Account confirmation
        # - Next steps for onboarding
        # - Links to resources and documentation
        # - Support contact information
        #
        # Implementation example:
        #   from src.api.email_service import EmailService
        #   email_service = EmailService()
        #   await email_service.send_welcome_email(
        #       to_email=user.email,
        #       user_name=user.email.split('@')[0],
        #       role=user.role.value
        #   )

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Called after password reset is requested."""
        print(f"User {user.id} has forgotten their password. Reset token: {token}")
        # Future enhancement: Send password reset email
        # Use email_service.py to send secure password reset email with:
        # - Time-limited reset link (e.g., valid for 1 hour)
        # - Security warning if user didn't request reset
        # - Alternative contact method if suspicious activity
        #
        # Implementation example:
        #   from src.api.email_service import EmailService
        #   email_service = EmailService()
        #   reset_url = f"{settings.frontend_url}/reset-password?token={token}"
        #   await email_service.send_password_reset_email(
        #       to_email=user.email,
        #       reset_url=reset_url,
        #       expires_in_minutes=60
        #   )

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Called after email verification is requested."""
        print(f"Verification requested for user {user.id}. Token: {token}")
        # Future enhancement: Send email verification email
        # Use email_service.py to send verification email with:
        # - Verification link (e.g., valid for 24 hours)
        # - Benefits of verifying email (access to features)
        # - Resend option if link expires
        #
        # Implementation example:
        #   from src.api.email_service import EmailService
        #   email_service = EmailService()
        #   verify_url = f"{settings.frontend_url}/verify-email?token={token}"
        #   await email_service.send_verification_email(
        #       to_email=user.email,
        #       verify_url=verify_url,
        #       expires_in_hours=24
        #   )

    async def on_after_login(
        self,
        user: User,
        request: Optional[Request] = None,
        response: Optional[Request] = None,
    ):
        """Called after successful login."""
        from datetime import datetime
        from sqlalchemy import update
        print(f"User {user.id} ({user.email}) logged in.")

        # Update last_login timestamp using a new session
        async with async_session_maker() as session:
            # Use UPDATE statement instead of adding the user object to avoid session conflicts
            # The user object is already attached to a different session from authentication
            await session.execute(
                update(User)
                .where(User.id == user.id)
                .values(
                    last_login=datetime.utcnow(),
                    failed_login_attempts=0
                )
            )
            await session.commit()

            # Log authentication event
            from ..audit_service import AuditService

            ip_address = None
            user_agent = None

            if request:
                # Get IP address
                if hasattr(request, 'client') and request.client:
                    ip_address = request.client.host
                # Check for forwarded IP
                forwarded_for = request.headers.get("X-Forwarded-For")
                if forwarded_for:
                    ip_address = forwarded_for.split(",")[0].strip()

                # Get user agent
                user_agent = request.headers.get("User-Agent")

            await AuditService.log_authentication(
                session=session,
                action=AuditService.ACTION_LOGIN,
                user_id=user.id,
                email=user.email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True,
            )

    async def create(self, user_create, safe: bool = False, request: Optional[Request] = None):
        """
        Create a new user with default role.

        Override to set default role for new users.
        """
        # Set default role to STUDENT if not specified
        user_dict = user_create.model_dump() if hasattr(user_create, 'model_dump') else user_create.dict()

        # Add default role if roles not provided
        if 'roles' not in user_dict or not user_dict['roles']:
            user_dict['roles'] = [UserRole.STUDENT]

        # Call parent create method
        return await super().create(user_create, safe=safe, request=request)


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    """
    Dependency to get the user database adapter.

    This provides all CRUD operations for users automatically!
    """
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    """
    Dependency to get the user manager.

    The user manager handles all user operations.
    """
    yield UserManager(user_db)


def get_jwt_strategy() -> JWTStrategy:
    """
    Get JWT authentication strategy.

    Returns:
        JWTStrategy configured with app settings
    """
    return JWTStrategy(
        secret=SECRET,
        lifetime_seconds=settings.access_token_expire_minutes * 60,
        algorithm=settings.jwt_algorithm
    )


# Configure authentication transport (Bearer token in header)
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

# Configure authentication backend
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# Initialize FastAPI-Users
fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

# Get current user dependencies
current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)
