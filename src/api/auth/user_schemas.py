"""
Pydantic schemas for User CRUD operations with FastAPI-Users.
"""

from typing import List, Optional
from fastapi_users import schemas
from pydantic import EmailStr, Field, ConfigDict

from ...database.models import UserRole, OAuthProvider


class UserRead(schemas.BaseUser[int]):
    """
    Schema for reading user data (responses).

    Inherits from FastAPI-Users BaseUser which provides:
    - id, email, is_active, is_superuser, is_verified
    """
    full_name: str
    roles: List[UserRole]
    oauth_provider: Optional[OAuthProvider] = None
    tutor_id: Optional[str] = None
    student_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserCreate(schemas.BaseUserCreate):
    """
    Schema for creating a new user (registration).

    Inherits from FastAPI-Users BaseUserCreate which provides:
    - email, password, is_active, is_superuser, is_verified
    """
    full_name: str
    roles: Optional[List[UserRole]] = None  # Will default to [STUDENT] if not provided


class UserUpdate(schemas.BaseUserUpdate):
    """
    Schema for updating user data.

    Inherits from FastAPI-Users BaseUserUpdate which provides:
    - password, email, is_active, is_superuser, is_verified
    """
    full_name: Optional[str] = None
    roles: Optional[List[UserRole]] = None
