"""
Authentication module for TutorMax API.

Powered by FastAPI-Users with custom RBAC integration.
Provides JWT authentication, user management, role-based access control, and OAuth/SSO.
"""

from .fastapi_users_config import (
    fastapi_users,
    auth_backend,
    current_active_user,
    current_superuser,
)
from .user_schemas import UserRead, UserCreate, UserUpdate
from .rbac import (
    require_roles,
    require_admin,
    require_operations_manager,
    require_people_ops,
    require_tutor,
    require_student,
    get_current_user,
    get_current_active_user,
)

# Import admin router
from . import admin_router

# Import OAuth configuration
from .oauth_config import get_oauth_routers

# Export pre-configured routers from FastAPI-Users
auth_router = fastapi_users.get_auth_router(auth_backend)
register_router = fastapi_users.get_register_router(UserRead, UserCreate)
reset_password_router = fastapi_users.get_reset_password_router()
verify_router = fastapi_users.get_verify_router(UserRead)
users_router = fastapi_users.get_users_router(UserRead, UserUpdate)

# OAuth routers
google_oauth_router, microsoft_oauth_router = get_oauth_routers(auth_backend)

__all__ = [
    # FastAPI-Users core
    'fastapi_users',
    'auth_backend',
    'current_active_user',
    'current_superuser',
    # Routers
    'auth_router',
    'register_router',
    'reset_password_router',
    'verify_router',
    'users_router',
    'admin_router',
    'google_oauth_router',
    'microsoft_oauth_router',
    # Schemas
    'UserRead',
    'UserCreate',
    'UserUpdate',
    # RBAC
    'get_current_user',
    'get_current_active_user',
    'require_roles',
    'require_admin',
    'require_operations_manager',
    'require_people_ops',
    'require_tutor',
    'require_student',
]
