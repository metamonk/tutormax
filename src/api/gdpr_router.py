"""
GDPR API Router

FastAPI router providing GDPR compliance endpoints for data subject rights.

Endpoints:
- GET /gdpr/export-my-data - Export all user data (Right to Access)
- POST /gdpr/delete-my-data - Request account deletion (Right to Erasure)
- GET /gdpr/download-data-report - Download portable data (Right to Portability)
- PUT /gdpr/rectify-data - Correct user data (Right to Rectification)
- POST /gdpr/consent - Manage consent for data processing
- GET /gdpr/consent - Get consent status
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from io import BytesIO

from ..database.database import get_async_session
from src.database.models import User
from .auth.fastapi_users_config import current_active_user
from .compliance import gdpr_service, consent_manager, data_breach_notifier
from .audit_service import AuditService


# Pydantic schemas
class DataExportRequest(BaseModel):
    """Request schema for data export."""
    include_encrypted: bool = Field(
        default=False,
        description="Include decrypted sensitive data"
    )
    format: str = Field(
        default="json",
        description="Export format: 'json' or 'pdf'"
    )


class DataDeletionRequest(BaseModel):
    """Request schema for data deletion."""
    confirm: bool = Field(
        ...,
        description="User must confirm deletion by setting this to true"
    )
    reason: Optional[str] = Field(
        default=None,
        description="Optional reason for deletion"
    )
    retain_audit_logs: bool = Field(
        default=True,
        description="Whether to retain anonymized audit logs for compliance"
    )


class DataRectificationRequest(BaseModel):
    """Request schema for data rectification."""
    corrections: Dict[str, Any] = Field(
        ...,
        description="Dictionary of corrections to apply",
        example={
            "account": {
                "full_name": "Updated Name",
                "email": "newemail@example.com"
            },
            "tutor": {
                "education_level": "Master's Degree"
            }
        }
    )


class ConsentRequest(BaseModel):
    """Request schema for consent management."""
    purpose: str = Field(
        ...,
        description="Purpose of data processing",
        example="marketing"
    )
    granted: bool = Field(
        ...,
        description="Whether consent is granted or withdrawn"
    )


class ConsentStatusResponse(BaseModel):
    """Response schema for consent status."""
    user_id: int
    consents: Dict[str, Optional[bool]] = Field(
        description="Consent status for each purpose"
    )


class DataExportResponse(BaseModel):
    """Response schema for data export."""
    export_date: str
    user_id: int
    data_categories: List[str]
    record_counts: Dict[str, int]
    download_formats: List[str] = ["json", "pdf"]


# Initialize router
router = APIRouter(
    prefix="/gdpr",
    tags=["GDPR Compliance"],
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized"},
        404: {"description": "Resource not found"},
    }
)


@router.get(
    "/export-my-data",
    response_model=DataExportResponse,
    summary="Export all personal data",
    description="Export all personal data associated with your account (GDPR Article 15 - Right to Access)"
)
async def export_my_data(
    format: str = "json",
    include_encrypted: bool = False,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Export all personal data for the authenticated user.

    This endpoint implements GDPR Article 15 (Right to Access), providing users
    with a complete copy of their personal data in a structured format.

    Args:
        format: Export format ("json" or "pdf")
        include_encrypted: Whether to include decrypted sensitive data
        current_user: Authenticated user
        session: Database session

    Returns:
        Summary of available data with download information
    """
    try:
        # Export user data
        data = await gdpr_service.export_user_data(
            session=session,
            user_id=current_user.id,
            include_encrypted=include_encrypted,
            format=format
        )

        # Log data export
        await AuditService.log_data_access(
            session=session,
            user_id=current_user.id,
            resource_type="user",
            resource_id=str(current_user.id),
            action="gdpr_data_export",
            ip_address=None,
            user_agent=None,
            request_path="/gdpr/export-my-data",
            metadata={
                "format": format,
                "include_encrypted": include_encrypted,
            }
        )

        # Return summary (actual data download via separate endpoint)
        return DataExportResponse(
            export_date=data["export_metadata"]["export_date"],
            user_id=current_user.id,
            data_categories=[
                "account_information",
                "tutor_data" if data["tutor_data"] else None,
                "student_data" if data["student_data"] else None,
                "sessions",
                "feedback",
                "performance_metrics",
                "predictions",
                "interventions",
                "notifications",
                "audit_logs",
            ],
            record_counts={
                "sessions": len(data["sessions"]),
                "feedback": len(data["feedback"]),
                "performance_metrics": len(data["performance_metrics"]),
                "predictions": len(data["predictions"]),
                "interventions": len(data["interventions"]),
                "notifications": len(data["notifications"]),
                "audit_logs": len(data["audit_logs"]),
            },
        )

    except Exception as e:
        await AuditService.log(
            session=session,
            action="gdpr_data_export_failed",
            user_id=current_user.id,
            resource_type="user",
            resource_id=str(current_user.id),
            success=False,
            error_message=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export data: {str(e)}"
        )


@router.get(
    "/download-data-report",
    summary="Download portable data report",
    description="Download your data in a portable format (GDPR Article 20 - Right to Data Portability)"
)
async def download_data_report(
    format: str = "json",
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Download user data in a portable format.

    This endpoint implements GDPR Article 20 (Right to Data Portability),
    providing data in a structured, commonly used, and machine-readable format.

    Args:
        format: Download format ("json" or "pdf")
        current_user: Authenticated user
        session: Database session

    Returns:
        Downloadable file with user data
    """
    try:
        # Generate portable data
        data_bytes, mime_type = await gdpr_service.generate_portable_data(
            session=session,
            user_id=current_user.id,
            format=format
        )

        # Log data export
        await AuditService.log_data_access(
            session=session,
            user_id=current_user.id,
            resource_type="user",
            resource_id=str(current_user.id),
            action="gdpr_data_download",
            ip_address=None,
            user_agent=None,
            request_path="/gdpr/download-data-report",
            metadata={"format": format}
        )

        # Determine filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        extension = "json" if format == "json" else "pdf"
        filename = f"tutormax_data_export_{current_user.id}_{timestamp}.{extension}"

        # Return file as download
        return StreamingResponse(
            BytesIO(data_bytes),
            media_type=mime_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        await AuditService.log(
            session=session,
            action="gdpr_data_download_failed",
            user_id=current_user.id,
            resource_type="user",
            resource_id=str(current_user.id),
            success=False,
            error_message=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate data report: {str(e)}"
        )


@router.post(
    "/delete-my-data",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request account deletion",
    description="Request permanent deletion of your account and all personal data (GDPR Article 17 - Right to Erasure)"
)
async def delete_my_data(
    request: DataDeletionRequest,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Request permanent deletion of user account and all associated data.

    This endpoint implements GDPR Article 17 (Right to Erasure/"Right to be Forgotten").

    **WARNING**: This action is irreversible and will permanently delete all data.

    Args:
        request: Deletion request with confirmation
        current_user: Authenticated user
        session: Database session

    Returns:
        Deletion confirmation and summary
    """
    # Require explicit confirmation
    if not request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must confirm deletion by setting 'confirm' to true"
        )

    try:
        # Perform deletion
        deletion_reason = request.reason or "User request (GDPR Article 17 - Right to Erasure)"
        summary = await gdpr_service.delete_user_data(
            session=session,
            user_id=current_user.id,
            deletion_reason=deletion_reason,
            retain_audit_logs=request.retain_audit_logs
        )

        return {
            "message": "Account deletion completed successfully",
            "deletion_date": summary["deletion_date"],
            "summary": summary,
            "note": "You have been logged out. Your account and data have been permanently deleted."
        }

    except Exception as e:
        await AuditService.log(
            session=session,
            action="gdpr_data_deletion_failed",
            user_id=current_user.id,
            resource_type="user",
            resource_id=str(current_user.id),
            success=False,
            error_message=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )


@router.put(
    "/rectify-data",
    summary="Correct personal data",
    description="Request correction of inaccurate personal data (GDPR Article 16 - Right to Rectification)"
)
async def rectify_data(
    request: DataRectificationRequest,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Request correction of inaccurate or incomplete personal data.

    This endpoint implements GDPR Article 16 (Right to Rectification).

    Args:
        request: Corrections to apply
        current_user: Authenticated user
        session: Database session

    Returns:
        Summary of applied corrections
    """
    try:
        # Apply corrections
        summary = await gdpr_service.rectify_user_data(
            session=session,
            user_id=current_user.id,
            corrections=request.corrections,
            requesting_user_id=current_user.id
        )

        return {
            "message": "Data corrections applied successfully",
            "rectification_date": summary["rectification_date"],
            "changes_applied": summary["changes_applied"],
            "changes_rejected": summary["changes_rejected"],
        }

    except Exception as e:
        await AuditService.log(
            session=session,
            action="gdpr_data_rectification_failed",
            user_id=current_user.id,
            resource_type="user",
            resource_id=str(current_user.id),
            success=False,
            error_message=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rectify data: {str(e)}"
        )


@router.post(
    "/consent",
    summary="Manage data processing consent",
    description="Grant or withdraw consent for specific data processing purposes (GDPR Article 7)"
)
async def manage_consent(
    request: ConsentRequest,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Grant or withdraw consent for data processing.

    This endpoint implements GDPR Article 7 (Conditions for consent).

    Valid purposes:
    - marketing: Marketing communications
    - analytics: Usage analytics and statistics
    - personalization: Personalized content and recommendations
    - third_party_sharing: Sharing data with third parties
    - profiling: Automated profiling and decision making

    Args:
        request: Consent request
        current_user: Authenticated user
        session: Database session

    Returns:
        Consent confirmation
    """
    try:
        # Record consent
        await consent_manager.record_consent(
            session=session,
            user_id=current_user.id,
            purpose=request.purpose,
            granted=request.granted,
            ip_address=None,
            user_agent=None
        )

        action = "granted" if request.granted else "withdrawn"
        return {
            "message": f"Consent {action} successfully",
            "purpose": request.purpose,
            "granted": request.granted,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to manage consent: {str(e)}"
        )


@router.get(
    "/consent",
    response_model=ConsentStatusResponse,
    summary="Get consent status",
    description="View current consent status for all data processing purposes"
)
async def get_consent_status(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get current consent status for all purposes.

    Args:
        current_user: Authenticated user
        session: Database session

    Returns:
        Consent status for each purpose
    """
    purposes = [
        consent_manager.PURPOSE_MARKETING,
        consent_manager.PURPOSE_ANALYTICS,
        consent_manager.PURPOSE_PERSONALIZATION,
        consent_manager.PURPOSE_THIRD_PARTY_SHARING,
        consent_manager.PURPOSE_PROFILING,
    ]

    consents = {}
    for purpose in purposes:
        status = await consent_manager.get_consent_status(
            session=session,
            user_id=current_user.id,
            purpose=purpose
        )
        consents[purpose] = status

    return ConsentStatusResponse(
        user_id=current_user.id,
        consents=consents
    )


@router.delete(
    "/consent",
    summary="Withdraw all consents",
    description="Withdraw all data processing consents at once"
)
async def withdraw_all_consents(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Withdraw all consents for data processing.

    Args:
        current_user: Authenticated user
        session: Database session

    Returns:
        Number of consents withdrawn
    """
    try:
        count = await consent_manager.withdraw_all_consents(
            session=session,
            user_id=current_user.id,
            ip_address=None
        )

        return {
            "message": "All consents withdrawn successfully",
            "consents_withdrawn": count,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to withdraw consents: {str(e)}"
        )
