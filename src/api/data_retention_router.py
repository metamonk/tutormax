"""
Data Retention & Compliance Management API Router

Provides admin endpoints for:
- Scanning for eligible archival/deletion records
- Archiving old data to cold storage
- Anonymizing data for analytics
- Processing GDPR deletion requests
- Generating compliance reports
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from .compliance.data_retention import (
    DataRetentionService,
    RetentionStatus,
    RetentionAction
)
from .compliance.ferpa import FERPAService
from .compliance.gdpr import GDPRService
from .auth.rbac import require_admin
from ..database.database import get_async_session
from src.database.models import User


router = APIRouter(prefix="/api/data-retention", tags=["Data Retention & Compliance"])


# Request/Response Models

class RetentionScanRequest(BaseModel):
    """Request to scan for retention actions."""
    dry_run: bool = Field(True, description="If true, only report without taking action")


class ArchivalRequest(BaseModel):
    """Request to archive data."""
    entity_type: str = Field(..., description="Type: 'student' or 'tutor'")
    entity_id: str = Field(..., description="Entity ID to archive")
    reason: str = Field("Manual archival by admin", description="Reason for archival")


class AnonymizationRequest(BaseModel):
    """Request to anonymize data."""
    entity_type: str = Field(..., description="Type: 'student' or 'tutor'")
    entity_id: str = Field(..., description="Entity ID to anonymize")


class DeletionRequest(BaseModel):
    """Request to delete user data (GDPR)."""
    user_id: int = Field(..., description="User ID to delete")
    deletion_reason: str = Field("GDPR Article 17 - Right to Erasure", description="Reason for deletion")


class ScheduledArchivalRequest(BaseModel):
    """Request to run scheduled archival."""
    perform_actions: bool = Field(False, description="If true, actually perform archival")


class RetentionReportRequest(BaseModel):
    """Request for retention compliance report."""
    start_date: Optional[str] = Field(None, description="Report start date (ISO format)")
    end_date: Optional[str] = Field(None, description="Report end date (ISO format)")


# Endpoints

@router.post("/scan", dependencies=[Depends(require_admin)])
async def scan_for_retention_actions(
    request: RetentionScanRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_admin)
):
    """
    Scan all records and identify those eligible for retention actions.

    **Admin only**. Scans database for:
    - Records past 7-year FERPA retention period (eligible for archival)
    - Records past 3-year threshold (eligible for anonymization)

    Returns detailed list of eligible records.
    """
    try:
        results = await DataRetentionService.scan_for_retention_actions(
            session=session,
            dry_run=request.dry_run
        )
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": results
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/archive", dependencies=[Depends(require_admin)])
async def archive_data(
    request: ArchivalRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_admin)
):
    """
    Archive data for a specific entity (student or tutor).

    **Admin only**. Moves data past retention period to cold storage.
    Maintains FERPA compliance by preserving data in archival storage.

    The data is:
    1. Exported to archival storage (audit log metadata)
    2. Removed from active tables
    3. Retrievable if needed for compliance/legal reasons
    """
    try:
        if request.entity_type == "student":
            result = await DataRetentionService.archive_student_data(
                session=session,
                student_id=request.entity_id,
                reason=request.reason,
                performed_by_user_id=current_user.id
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Entity type '{request.entity_type}' not yet supported for archival"
            )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Successfully archived {request.entity_type} {request.entity_id}",
                "data": result
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/anonymize", dependencies=[Depends(require_admin)])
async def anonymize_data(
    request: AnonymizationRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_admin)
):
    """
    Anonymize PII for analytics purposes.

    **Admin only**. Removes personally identifiable information while
    preserving statistical and behavioral data for research/analytics.

    Anonymized fields:
    - Student: name, parent_email, parent_consent_ip
    - Tutor: name, email, location

    Retained fields:
    - Student: age, grade_level, subjects_interested
    - Tutor: subjects, education_level, behavioral_archetype, performance metrics
    """
    try:
        result = await DataRetentionService.anonymize_data_for_analytics(
            session=session,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            performed_by_user_id=current_user.id
        )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Successfully anonymized {request.entity_type} {request.entity_id}",
                "data": result
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delete", dependencies=[Depends(require_admin)])
async def process_deletion_request(
    request: DeletionRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_admin)
):
    """
    Process GDPR 'Right to be Forgotten' deletion request.

    **Admin only**. Permanently deletes all user data per GDPR Article 17.

    This is different from archival:
    - Archival: Moves old data to cold storage (FERPA compliance)
    - Deletion: Permanent removal per user request (GDPR compliance)

    Deletes:
    - User account
    - All associated tutor/student records
    - Sessions, feedback, performance metrics
    - Interventions, predictions, events
    - Manager notes, notifications

    Retains:
    - Anonymized audit logs (for compliance)
    """
    try:
        result = await DataRetentionService.process_deletion_request(
            session=session,
            user_id=request.user_id,
            deletion_reason=request.deletion_reason,
            performed_by_user_id=current_user.id
        )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Successfully deleted user {request.user_id}",
                "data": result
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report", dependencies=[Depends(require_admin)])
async def get_retention_report(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_admin)
):
    """
    Generate comprehensive data retention compliance report.

    **Admin only**. Shows:
    - Current data inventory (active records)
    - Archival operations performed
    - Anonymization operations performed
    - Deletion requests processed
    - Compliance status

    Useful for audits and compliance reviews.
    """
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None

        report = await DataRetentionService.get_retention_report(
            session=session,
            start_date=start,
            end_date=end
        )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": report
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scheduled-archival", dependencies=[Depends(require_admin)])
async def run_scheduled_archival(
    request: ScheduledArchivalRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_admin)
):
    """
    Run scheduled automated archival process.

    **Admin only**. This endpoint can be:
    1. Called manually by an admin to trigger archival
    2. Called by a cron job/scheduled task for automation

    If `perform_actions=true`, actually archives eligible records.
    If `perform_actions=false`, performs dry run and reports what would be archived.

    Recommended to run monthly or quarterly.
    """
    try:
        result = await DataRetentionService.schedule_automated_archival(
            session=session,
            perform_actions=request.perform_actions
        )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Scheduled archival completed",
                "data": result
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/retention-policy", dependencies=[Depends(require_admin)])
async def get_retention_policy(
    current_user: User = Depends(require_admin)
):
    """
    Get current data retention policy details.

    **Admin only**. Returns policy configuration for all compliance frameworks.
    """
    try:
        ferpa_schedule = FERPAService.get_retention_schedule()

        policy = {
            "ferpa": ferpa_schedule,
            "gdpr": {
                "right_to_erasure": "GDPR Article 17",
                "right_to_access": "GDPR Article 15",
                "right_to_portability": "GDPR Article 20",
                "anonymization_after_days": DataRetentionService.GDPR_ANONYMIZATION_DAYS,
            },
            "automated_archival": {
                "enabled": True,
                "ferpa_retention_days": DataRetentionService.FERPA_RETENTION_DAYS,
                "grace_period_days": DataRetentionService.ARCHIVAL_GRACE_PERIOD_DAYS,
                "audit_log_retention_days": DataRetentionService.AUDIT_LOG_RETENTION_DAYS,
            },
            "data_lifecycle": {
                "stages": [
                    {
                        "stage": "active",
                        "description": "Within retention period, full PII retained",
                        "max_age_days": DataRetentionService.FERPA_RETENTION_DAYS
                    },
                    {
                        "stage": "eligible_for_anonymization",
                        "description": "Can remove PII, keep for analytics",
                        "after_days": DataRetentionService.GDPR_ANONYMIZATION_DAYS
                    },
                    {
                        "stage": "eligible_for_archival",
                        "description": "Can move to cold storage",
                        "after_days": DataRetentionService.FERPA_RETENTION_DAYS
                    },
                    {
                        "stage": "archived",
                        "description": "In cold storage, retrievable for legal/compliance"
                    },
                    {
                        "stage": "deleted",
                        "description": "Permanently removed (user request only)"
                    }
                ]
            }
        }

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": policy
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check/{entity_type}/{entity_id}", dependencies=[Depends(require_admin)])
async def check_retention_status(
    entity_type: str,
    entity_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_admin)
):
    """
    Check retention status for a specific entity.

    **Admin only**. Returns:
    - Current retention status
    - Eligibility for archival/anonymization
    - Days until eligible for each action
    - Last activity date
    """
    try:
        if entity_type == "student":
            status = await FERPAService.check_retention_policy(
                session=session,
                student_id=entity_id
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Entity type '{entity_type}' not supported"
            )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": status
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
