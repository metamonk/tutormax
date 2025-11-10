"""
Intervention Management API endpoints.

Provides REST endpoints for operations managers to view, assign, track,
and complete interventions for at-risk tutors.
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from pydantic import BaseModel, Field

from .config import settings
from ..database.database import get_async_session
from src.database.models import (
    Intervention,
    Tutor,
    InterventionType,
    InterventionStatus,
    InterventionOutcome,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix=f"{settings.api_prefix}/interventions",
    tags=["Intervention Management"]
)


# ============================================================================
# Pydantic Schemas
# ============================================================================

class InterventionResponse(BaseModel):
    """Response model for intervention data."""
    intervention_id: str
    tutor_id: str
    tutor_name: Optional[str] = None
    intervention_type: str
    trigger_reason: Optional[str] = None
    recommended_date: datetime
    assigned_to: Optional[str] = None
    status: str
    due_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    outcome: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Computed fields
    days_until_due: Optional[int] = None
    is_overdue: bool = False
    sla_percentage: Optional[float] = None

    class Config:
        from_attributes = True


class InterventionAssignRequest(BaseModel):
    """Request model for assigning an intervention."""
    assigned_to: str = Field(..., description="User ID or name of the person assigned")


class InterventionStatusUpdate(BaseModel):
    """Request model for updating intervention status."""
    status: str = Field(..., description="New status (pending, in_progress, completed, cancelled)")


class InterventionOutcomeRequest(BaseModel):
    """Request model for recording intervention outcome."""
    outcome: str = Field(..., description="Outcome (improved, no_change, declined, churned)")
    notes: Optional[str] = Field(None, description="Additional notes about the outcome")


class InterventionStats(BaseModel):
    """Statistics about interventions."""
    total: int
    pending: int
    in_progress: int
    completed: int
    cancelled: int
    overdue: int
    due_today: int
    due_this_week: int
    by_type: dict


# ============================================================================
# Helper Functions
# ============================================================================

def calculate_intervention_metadata(intervention: Intervention) -> dict:
    """Calculate computed fields for an intervention."""
    metadata = {}

    if intervention.due_date:
        now = datetime.utcnow()
        delta = intervention.due_date - now
        metadata['days_until_due'] = delta.days
        metadata['is_overdue'] = delta.days < 0

        # Calculate SLA percentage (time elapsed / total time)
        if intervention.recommended_date:
            total_time = (intervention.due_date - intervention.recommended_date).total_seconds()
            elapsed_time = (now - intervention.recommended_date).total_seconds()
            if total_time > 0:
                metadata['sla_percentage'] = min(100.0, (elapsed_time / total_time) * 100)

    return metadata


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/", response_model=List[InterventionResponse])
async def get_interventions(
    status: Optional[str] = Query(None, description="Filter by status"),
    assigned_to: Optional[str] = Query(None, description="Filter by assigned user"),
    intervention_type: Optional[str] = Query(None, description="Filter by intervention type"),
    tutor_id: Optional[str] = Query(None, description="Filter by tutor ID"),
    include_overdue: Optional[bool] = Query(None, description="Include only overdue interventions"),
    limit: int = Query(100, le=500, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get interventions with optional filtering.

    Returns a list of interventions based on the provided filters.
    Results are ordered by due date (earliest first), with overdue items at the top.
    """
    try:
        # Build query
        query = select(Intervention).join(Tutor, Intervention.tutor_id == Tutor.tutor_id)

        # Apply filters
        conditions = []

        if status:
            try:
                status_enum = InterventionStatus(status)
                conditions.append(Intervention.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status}"
                )

        if assigned_to:
            conditions.append(Intervention.assigned_to == assigned_to)

        if intervention_type:
            try:
                type_enum = InterventionType(intervention_type)
                conditions.append(Intervention.intervention_type == type_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid intervention type: {intervention_type}"
                )

        if tutor_id:
            conditions.append(Intervention.tutor_id == tutor_id)

        if include_overdue:
            conditions.append(
                and_(
                    Intervention.due_date.isnot(None),
                    Intervention.due_date < datetime.utcnow()
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        # Order by: overdue first, then by due date
        query = query.order_by(
            desc(Intervention.due_date < datetime.utcnow()),
            Intervention.due_date.asc()
        )

        # Apply pagination
        query = query.offset(offset).limit(limit)

        # Execute query
        result = await db.execute(query)
        interventions = result.scalars().all()

        # Build response with computed fields
        response = []
        for intervention in interventions:
            # Get tutor name
            tutor_result = await db.execute(
                select(Tutor.tutor_name).where(Tutor.tutor_id == intervention.tutor_id)
            )
            tutor_name = tutor_result.scalar_one_or_none()

            # Calculate metadata
            metadata = calculate_intervention_metadata(intervention)

            intervention_data = InterventionResponse(
                intervention_id=intervention.intervention_id,
                tutor_id=intervention.tutor_id,
                tutor_name=tutor_name,
                intervention_type=intervention.intervention_type.value,
                trigger_reason=intervention.trigger_reason,
                recommended_date=intervention.recommended_date,
                assigned_to=intervention.assigned_to,
                status=intervention.status.value,
                due_date=intervention.due_date,
                completed_date=intervention.completed_date,
                outcome=intervention.outcome.value if intervention.outcome else None,
                notes=intervention.notes,
                created_at=intervention.created_at,
                updated_at=intervention.updated_at,
                **metadata
            )
            response.append(intervention_data)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching interventions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching interventions: {str(e)}"
        )


@router.get("/stats", response_model=InterventionStats)
async def get_intervention_stats(
    assigned_to: Optional[str] = Query(None, description="Filter stats by assigned user"),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get statistics about interventions.

    Returns counts by status, overdue count, and counts by intervention type.
    """
    try:
        # Base query
        base_query = select(Intervention)

        if assigned_to:
            base_query = base_query.where(Intervention.assigned_to == assigned_to)

        # Get total count
        total_result = await db.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total = total_result.scalar() or 0

        # Get counts by status
        status_counts = {
            'pending': 0,
            'in_progress': 0,
            'completed': 0,
            'cancelled': 0,
        }

        for status_value in InterventionStatus:
            query = base_query.where(Intervention.status == status_value)
            count_result = await db.execute(
                select(func.count()).select_from(query.subquery())
            )
            count = count_result.scalar() or 0
            status_counts[status_value.value] = count

        # Get overdue count
        overdue_query = base_query.where(
            and_(
                Intervention.due_date.isnot(None),
                Intervention.due_date < datetime.utcnow(),
                Intervention.status.in_([InterventionStatus.PENDING, InterventionStatus.IN_PROGRESS])
            )
        )
        overdue_result = await db.execute(
            select(func.count()).select_from(overdue_query.subquery())
        )
        overdue = overdue_result.scalar() or 0

        # Get due today count
        from datetime import date
        today_start = datetime.combine(date.today(), datetime.min.time())
        today_end = datetime.combine(date.today(), datetime.max.time())

        due_today_query = base_query.where(
            and_(
                Intervention.due_date.between(today_start, today_end),
                Intervention.status.in_([InterventionStatus.PENDING, InterventionStatus.IN_PROGRESS])
            )
        )
        due_today_result = await db.execute(
            select(func.count()).select_from(due_today_query.subquery())
        )
        due_today = due_today_result.scalar() or 0

        # Get due this week count
        from datetime import timedelta
        week_end = today_start + timedelta(days=7)

        due_week_query = base_query.where(
            and_(
                Intervention.due_date.between(today_start, week_end),
                Intervention.status.in_([InterventionStatus.PENDING, InterventionStatus.IN_PROGRESS])
            )
        )
        due_week_result = await db.execute(
            select(func.count()).select_from(due_week_query.subquery())
        )
        due_this_week = due_week_result.scalar() or 0

        # Get counts by type
        by_type = {}
        for intervention_type in InterventionType:
            type_query = base_query.where(Intervention.intervention_type == intervention_type)
            type_result = await db.execute(
                select(func.count()).select_from(type_query.subquery())
            )
            count = type_result.scalar() or 0
            by_type[intervention_type.value] = count

        return InterventionStats(
            total=total,
            pending=status_counts['pending'],
            in_progress=status_counts['in_progress'],
            completed=status_counts['completed'],
            cancelled=status_counts['cancelled'],
            overdue=overdue,
            due_today=due_today,
            due_this_week=due_this_week,
            by_type=by_type,
        )

    except Exception as e:
        logger.error(f"Error fetching intervention stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching intervention stats: {str(e)}"
        )


@router.get("/{intervention_id}", response_model=InterventionResponse)
async def get_intervention(
    intervention_id: str,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get a specific intervention by ID.
    """
    try:
        result = await db.execute(
            select(Intervention).where(Intervention.intervention_id == intervention_id)
        )
        intervention = result.scalar_one_or_none()

        if not intervention:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Intervention {intervention_id} not found"
            )

        # Get tutor name
        tutor_result = await db.execute(
            select(Tutor.tutor_name).where(Tutor.tutor_id == intervention.tutor_id)
        )
        tutor_name = tutor_result.scalar_one_or_none()

        # Calculate metadata
        metadata = calculate_intervention_metadata(intervention)

        return InterventionResponse(
            intervention_id=intervention.intervention_id,
            tutor_id=intervention.tutor_id,
            tutor_name=tutor_name,
            intervention_type=intervention.intervention_type.value,
            trigger_reason=intervention.trigger_reason,
            recommended_date=intervention.recommended_date,
            assigned_to=intervention.assigned_to,
            status=intervention.status.value,
            due_date=intervention.due_date,
            completed_date=intervention.completed_date,
            outcome=intervention.outcome.value if intervention.outcome else None,
            notes=intervention.notes,
            created_at=intervention.created_at,
            updated_at=intervention.updated_at,
            **metadata
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching intervention: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching intervention: {str(e)}"
        )


@router.post("/{intervention_id}/assign", response_model=InterventionResponse)
async def assign_intervention(
    intervention_id: str,
    request: InterventionAssignRequest,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Assign an intervention to a specific user (manager/coach).

    This is the one-click assignment feature from the PRD.
    """
    try:
        result = await db.execute(
            select(Intervention).where(Intervention.intervention_id == intervention_id)
        )
        intervention = result.scalar_one_or_none()

        if not intervention:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Intervention {intervention_id} not found"
            )

        # Update assignment
        intervention.assigned_to = request.assigned_to
        intervention.updated_at = datetime.utcnow()

        # If not already in progress, set to in_progress
        if intervention.status == InterventionStatus.PENDING:
            intervention.status = InterventionStatus.IN_PROGRESS

        await db.commit()
        await db.refresh(intervention)

        # Get tutor name
        tutor_result = await db.execute(
            select(Tutor.tutor_name).where(Tutor.tutor_id == intervention.tutor_id)
        )
        tutor_name = tutor_result.scalar_one_or_none()

        # Calculate metadata
        metadata = calculate_intervention_metadata(intervention)

        logger.info(f"Intervention {intervention_id} assigned to {request.assigned_to}")

        return InterventionResponse(
            intervention_id=intervention.intervention_id,
            tutor_id=intervention.tutor_id,
            tutor_name=tutor_name,
            intervention_type=intervention.intervention_type.value,
            trigger_reason=intervention.trigger_reason,
            recommended_date=intervention.recommended_date,
            assigned_to=intervention.assigned_to,
            status=intervention.status.value,
            due_date=intervention.due_date,
            completed_date=intervention.completed_date,
            outcome=intervention.outcome.value if intervention.outcome else None,
            notes=intervention.notes,
            created_at=intervention.created_at,
            updated_at=intervention.updated_at,
            **metadata
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning intervention: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error assigning intervention: {str(e)}"
        )


@router.patch("/{intervention_id}/status", response_model=InterventionResponse)
async def update_intervention_status(
    intervention_id: str,
    request: InterventionStatusUpdate,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Update the status of an intervention.

    Supports the workflow: pending → in_progress → completed
    """
    try:
        result = await db.execute(
            select(Intervention).where(Intervention.intervention_id == intervention_id)
        )
        intervention = result.scalar_one_or_none()

        if not intervention:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Intervention {intervention_id} not found"
            )

        # Validate status
        try:
            new_status = InterventionStatus(request.status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {request.status}"
            )

        # Update status
        intervention.status = new_status
        intervention.updated_at = datetime.utcnow()

        # Set completed_date if status is completed
        if new_status == InterventionStatus.COMPLETED:
            intervention.completed_date = datetime.utcnow()

        await db.commit()
        await db.refresh(intervention)

        # Get tutor name
        tutor_result = await db.execute(
            select(Tutor.tutor_name).where(Tutor.tutor_id == intervention.tutor_id)
        )
        tutor_name = tutor_result.scalar_one_or_none()

        # Calculate metadata
        metadata = calculate_intervention_metadata(intervention)

        logger.info(f"Intervention {intervention_id} status updated to {request.status}")

        return InterventionResponse(
            intervention_id=intervention.intervention_id,
            tutor_id=intervention.tutor_id,
            tutor_name=tutor_name,
            intervention_type=intervention.intervention_type.value,
            trigger_reason=intervention.trigger_reason,
            recommended_date=intervention.recommended_date,
            assigned_to=intervention.assigned_to,
            status=intervention.status.value,
            due_date=intervention.due_date,
            completed_date=intervention.completed_date,
            outcome=intervention.outcome.value if intervention.outcome else None,
            notes=intervention.notes,
            created_at=intervention.created_at,
            updated_at=intervention.updated_at,
            **metadata
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating intervention status: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating intervention status: {str(e)}"
        )


@router.post("/{intervention_id}/outcome", response_model=InterventionResponse)
async def record_intervention_outcome(
    intervention_id: str,
    request: InterventionOutcomeRequest,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Record the outcome of a completed intervention.

    This endpoint allows managers to log the result of their intervention
    actions (improved, no_change, declined, churned).
    """
    try:
        result = await db.execute(
            select(Intervention).where(Intervention.intervention_id == intervention_id)
        )
        intervention = result.scalar_one_or_none()

        if not intervention:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Intervention {intervention_id} not found"
            )

        # Validate outcome
        try:
            outcome_enum = InterventionOutcome(request.outcome)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid outcome: {request.outcome}"
            )

        # Update outcome and notes
        intervention.outcome = outcome_enum
        if request.notes:
            intervention.notes = request.notes
        intervention.updated_at = datetime.utcnow()

        # Auto-complete if not already completed
        if intervention.status != InterventionStatus.COMPLETED:
            intervention.status = InterventionStatus.COMPLETED
            intervention.completed_date = datetime.utcnow()

        await db.commit()
        await db.refresh(intervention)

        # Get tutor name
        tutor_result = await db.execute(
            select(Tutor.tutor_name).where(Tutor.tutor_id == intervention.tutor_id)
        )
        tutor_name = tutor_result.scalar_one_or_none()

        # Calculate metadata
        metadata = calculate_intervention_metadata(intervention)

        logger.info(f"Intervention {intervention_id} outcome recorded: {request.outcome}")

        return InterventionResponse(
            intervention_id=intervention.intervention_id,
            tutor_id=intervention.tutor_id,
            tutor_name=tutor_name,
            intervention_type=intervention.intervention_type.value,
            trigger_reason=intervention.trigger_reason,
            recommended_date=intervention.recommended_date,
            assigned_to=intervention.assigned_to,
            status=intervention.status.value,
            due_date=intervention.due_date,
            completed_date=intervention.completed_date,
            outcome=intervention.outcome.value if intervention.outcome else None,
            notes=intervention.notes,
            created_at=intervention.created_at,
            updated_at=intervention.updated_at,
            **metadata
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording intervention outcome: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recording intervention outcome: {str(e)}"
        )
