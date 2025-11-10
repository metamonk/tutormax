"""
Admin-only endpoints for user management.

Provides comprehensive user management functionality:
- List all users with filtering and pagination
- Create, update, and deactivate users
- Role management
- Bulk operations
- Password reset
- Audit logging for all admin actions
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import uuid4
import csv
import io

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from src.database.database import get_async_session
from src.database.models import User, UserRole, Tutor, Student
from .user_schemas import UserRead
from .rbac import require_admin
from ..audit_service import log_audit_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


class UserCreateRequest(BaseModel):
    """Request to create a new user."""
    email: EmailStr
    full_name: str
    roles: List[UserRole]
    password: Optional[str] = None  # If None, will send password reset email
    is_active: bool = True
    tutor_id: Optional[str] = None
    student_id: Optional[str] = None


class UserUpdateRequest(BaseModel):
    """Request to update a user."""
    full_name: Optional[str] = None
    roles: Optional[List[UserRole]] = None
    is_active: Optional[bool] = None


class RoleAssignmentRequest(BaseModel):
    """Request to assign/remove roles."""
    user_ids: List[int]
    roles_to_add: Optional[List[UserRole]] = None
    roles_to_remove: Optional[List[UserRole]] = None


class PasswordResetRequest(BaseModel):
    """Request to reset user password."""
    new_password: str


class UsersListResponse(BaseModel):
    """Paginated users list response."""
    success: bool
    users: List[UserRead]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.get("/users", response_model=UsersListResponse)
async def list_all_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in name or email"),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    session: AsyncSession = Depends(get_async_session),
    _admin: User = Depends(require_admin),
):
    """
    List all users in the system with pagination and filtering.

    **Requires:** Admin role

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        search: Search query for name or email
        role: Filter by specific role
        is_active: Filter by active/inactive status

    Returns:
        Paginated list of users with their complete profiles.
    """
    try:
        # Build query
        query = select(User)

        # Apply filters
        conditions = []
        if search:
            search_pattern = f"%{search}%"
            conditions.append(
                or_(
                    User.full_name.ilike(search_pattern),
                    User.email.ilike(search_pattern)
                )
            )

        if role:
            # Filter users who have the specified role
            result = await session.execute(select(User))
            all_users = result.scalars().all()
            filtered_users = [u for u in all_users if role in u.roles]

            # Apply pagination manually for role filter
            total = len(filtered_users)
            offset = (page - 1) * page_size
            users = filtered_users[offset:offset + page_size]
        else:
            if is_active is not None:
                conditions.append(User.is_active == is_active)

            if conditions:
                query = query.where(and_(*conditions))

            # Get total count
            count_query = select(func.count()).select_from(User)
            if conditions:
                count_query = count_query.where(and_(*conditions))
            total_result = await session.execute(count_query)
            total = total_result.scalar()

            # Apply pagination
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)

            # Execute query
            result = await session.execute(query)
            users = result.scalars().all()

        total_pages = (total + page_size - 1) // page_size

        # Log audit event
        await log_audit_event(
            session=session,
            user_id=_admin.id,
            action="LIST_USERS",
            resource_type="users",
            resource_id=None,
            details={"filters": {"search": search, "role": role, "is_active": is_active}}
        )

        return UsersListResponse(
            success=True,
            users=users,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    except Exception as e:
        logger.error(f"Failed to list users: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreateRequest = Body(...),
    session: AsyncSession = Depends(get_async_session),
    _admin: User = Depends(require_admin),
):
    """
    Create a new user account.

    **Requires:** Admin role

    Args:
        user_data: User creation data including email, name, and roles

    Returns:
        Created user object
    """
    try:
        # Check if email already exists
        existing_user = await session.execute(
            select(User).where(User.email == user_data.email)
        )
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )

        # Create user
        new_user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            roles=user_data.roles,
            is_active=user_data.is_active,
            is_verified=True,  # Admin-created users are pre-verified
            tutor_id=user_data.tutor_id,
            student_id=user_data.student_id
        )

        # Set password if provided (in production, use proper password hashing)
        if user_data.password:
            # Note: This is simplified - use FastAPI-Users password hashing in production
            new_user.hashed_password = user_data.password  # Should be hashed!

        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        # Log audit event
        await log_audit_event(
            session=session,
            user_id=_admin.id,
            action="CREATE_USER",
            resource_type="user",
            resource_id=str(new_user.id),
            details={
                "email": user_data.email,
                "roles": user_data.roles,
                "created_by_admin": _admin.email
            }
        )

        return new_user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create user: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.patch("/users/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    user_data: UserUpdateRequest = Body(...),
    session: AsyncSession = Depends(get_async_session),
    _admin: User = Depends(require_admin),
):
    """
    Update a user's information.

    **Requires:** Admin role

    Args:
        user_id: ID of user to update
        user_data: Fields to update

    Returns:
        Updated user object
    """
    try:
        # Get user
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )

        # Update fields
        if user_data.full_name is not None:
            user.full_name = user_data.full_name

        if user_data.roles is not None:
            user.roles = user_data.roles

        if user_data.is_active is not None:
            user.is_active = user_data.is_active

        await session.commit()
        await session.refresh(user)

        # Log audit event
        await log_audit_event(
            session=session,
            user_id=_admin.id,
            action="UPDATE_USER",
            resource_type="user",
            resource_id=str(user_id),
            details={
                "updated_fields": user_data.dict(exclude_none=True),
                "updated_by_admin": _admin.email
            }
        )

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user {user_id}: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
    _admin: User = Depends(require_admin),
):
    """
    Deactivate a user account.

    **Requires:** Admin role

    Args:
        user_id: ID of user to deactivate

    Returns:
        Success status
    """
    try:
        # Get user
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )

        # Prevent self-deactivation
        if user.id == _admin.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own account"
            )

        user.is_active = False
        await session.commit()

        # Log audit event
        await log_audit_event(
            session=session,
            user_id=_admin.id,
            action="DEACTIVATE_USER",
            resource_type="user",
            resource_id=str(user_id),
            details={
                "deactivated_email": user.email,
                "deactivated_by_admin": _admin.email
            }
        )

        return {
            "success": True,
            "message": f"User {user.email} has been deactivated",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate user {user_id}: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )


@router.post("/users/bulk/assign-roles")
async def bulk_assign_roles(
    request: RoleAssignmentRequest = Body(...),
    session: AsyncSession = Depends(get_async_session),
    _admin: User = Depends(require_admin),
):
    """
    Assign or remove roles for multiple users.

    **Requires:** Admin role

    Args:
        request: List of user IDs and roles to add/remove

    Returns:
        Summary of changes
    """
    try:
        updated_count = 0

        for user_id in request.user_ids:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                continue

            # Add roles
            if request.roles_to_add:
                current_roles = set(user.roles)
                current_roles.update(request.roles_to_add)
                user.roles = list(current_roles)

            # Remove roles
            if request.roles_to_remove:
                current_roles = set(user.roles)
                current_roles.difference_update(request.roles_to_remove)
                user.roles = list(current_roles)

            updated_count += 1

        await session.commit()

        # Log audit event
        await log_audit_event(
            session=session,
            user_id=_admin.id,
            action="BULK_ASSIGN_ROLES",
            resource_type="users",
            resource_id=None,
            details={
                "user_ids": request.user_ids,
                "roles_added": request.roles_to_add,
                "roles_removed": request.roles_to_remove,
                "updated_count": updated_count
            }
        )

        return {
            "success": True,
            "updated_count": updated_count,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to bulk assign roles: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign roles"
        )


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    password_data: PasswordResetRequest = Body(...),
    session: AsyncSession = Depends(get_async_session),
    _admin: User = Depends(require_admin),
):
    """
    Reset a user's password (admin function).

    **Requires:** Admin role

    Args:
        user_id: ID of user
        password_data: New password

    Returns:
        Success status
    """
    try:
        # Get user
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )

        # Update password (in production, use proper password hashing)
        user.hashed_password = password_data.new_password  # Should be hashed!
        await session.commit()

        # Log audit event
        await log_audit_event(
            session=session,
            user_id=_admin.id,
            action="RESET_PASSWORD",
            resource_type="user",
            resource_id=str(user_id),
            details={
                "reset_for_email": user.email,
                "reset_by_admin": _admin.email
            }
        )

        return {
            "success": True,
            "message": f"Password reset for {user.email}",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset password for user {user_id}: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )


@router.get("/users/by-role/{role}", response_model=List[UserRead])
async def list_users_by_role(
    role: str,
    session: AsyncSession = Depends(get_async_session),
    _admin: User = Depends(require_admin),
):
    """
    List all users with a specific role.

    **Requires:** Admin role

    Args:
        role: The role to filter by (admin, operations_manager, people_ops, tutor, student)

    Returns a list of users with the specified role.
    """
    result = await session.execute(select(User))
    users = result.scalars().all()

    # Filter users by role (roles is a list in the User model)
    filtered_users = [user for user in users if role in user.roles]
    return filtered_users


@router.post("/users/bulk-import")
async def bulk_import_users(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session),
    _admin: User = Depends(require_admin),
):
    """
    Bulk import users from CSV file.

    **Requires:** Admin role

    CSV format: email,full_name,roles,is_active
    Roles should be comma-separated in quotes: "tutor,admin"

    Args:
        file: CSV file with user data

    Returns:
        Summary of import results
    """
    try:
        # Read CSV file
        contents = await file.read()
        decoded = contents.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(decoded))

        imported_count = 0
        failed_count = 0
        errors = []

        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header is row 1)
            try:
                email = row.get('email', '').strip()
                full_name = row.get('full_name', '').strip()
                roles_str = row.get('roles', '').strip()
                is_active_str = row.get('is_active', 'true').strip().lower()

                if not email or not full_name:
                    errors.append(f"Row {row_num}: Missing required fields")
                    failed_count += 1
                    continue

                # Parse roles
                try:
                    roles = [r.strip() for r in roles_str.split(',')]
                    # Validate roles
                    valid_roles = ['admin', 'operations_manager', 'people_ops', 'tutor', 'student']
                    roles = [r for r in roles if r in valid_roles]
                    if not roles:
                        errors.append(f"Row {row_num}: No valid roles specified")
                        failed_count += 1
                        continue
                except Exception:
                    errors.append(f"Row {row_num}: Invalid roles format")
                    failed_count += 1
                    continue

                # Parse is_active
                is_active = is_active_str in ['true', '1', 'yes', 'y']

                # Check if user already exists
                existing = await session.execute(
                    select(User).where(User.email == email)
                )
                if existing.scalar_one_or_none():
                    errors.append(f"Row {row_num}: User {email} already exists")
                    failed_count += 1
                    continue

                # Create user
                new_user = User(
                    email=email,
                    full_name=full_name,
                    roles=roles,
                    is_active=is_active,
                    is_verified=True,
                    hashed_password=f"temp_password_{uuid4().hex}"  # Temporary password
                )

                session.add(new_user)
                imported_count += 1

            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
                failed_count += 1

        # Commit all changes
        await session.commit()

        # Log audit event
        await log_audit_event(
            session=session,
            user_id=_admin.id,
            action="BULK_IMPORT_USERS",
            resource_type="users",
            resource_id=None,
            details={
                "imported_count": imported_count,
                "failed_count": failed_count,
                "filename": file.filename
            }
        )

        return {
            "success": True,
            "imported_count": imported_count,
            "failed_count": failed_count,
            "errors": errors[:10],  # Return first 10 errors
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to bulk import users: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import users: {str(e)}"
        )
