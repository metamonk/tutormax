"""
Role-Based Access Control (RBAC) dependencies for FastAPI.

Provides role-checking dependencies that integrate with FastAPI-Users.
"""

from typing import List
from fastapi import Depends, HTTPException, status

from ...database.models import User, UserRole
from .fastapi_users_config import current_active_user


def require_roles(allowed_roles: List[UserRole]):
    """
    Dependency factory for role-based access control.

    Args:
        allowed_roles: List of roles that are allowed to access the endpoint

    Returns:
        FastAPI dependency function that validates user roles

    Example:
        @app.get("/admin", dependencies=[Depends(require_roles([UserRole.ADMIN]))])
        async def admin_endpoint():
            return {"message": "Admin only"}
    """
    async def role_checker(current_user: User = Depends(current_active_user)) -> User:
        """
        Check if current user has one of the required roles.

        Args:
            current_user: The authenticated user from FastAPI-Users

        Returns:
            The user if they have required role

        Raises:
            HTTPException: 403 if user doesn't have required role
        """
        if not current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned roles"
            )

        user_roles = set(current_user.roles)
        required_roles = set(allowed_roles)

        # Check if user has any of the required roles
        if not user_roles.intersection(required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have required role. Required: {[r.value for r in allowed_roles]}"
            )

        return current_user

    return role_checker


# Convenience dependencies for specific roles
require_admin = require_roles([UserRole.ADMIN])
require_operations_manager = require_roles([UserRole.ADMIN, UserRole.OPERATIONS_MANAGER])
require_people_ops = require_roles([UserRole.ADMIN, UserRole.OPERATIONS_MANAGER, UserRole.PEOPLE_OPS])
require_tutor = require_roles([UserRole.ADMIN, UserRole.TUTOR])
require_student = require_roles([UserRole.ADMIN, UserRole.STUDENT])


# Alias for backwards compatibility
get_current_user = current_active_user
get_current_active_user = current_active_user


__all__ = [
    'require_roles',
    'require_admin',
    'require_operations_manager',
    'require_people_ops',
    'require_tutor',
    'require_student',
    'get_current_user',
    'get_current_active_user',
]
