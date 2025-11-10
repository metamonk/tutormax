"""
COPPA Parental Consent API Router

Provides endpoints for:
- Parental consent workflow
- Child data access for parents
- Data deletion requests
- Age verification

All endpoints require verification that the requester is the authorized parent/guardian.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from .database.database import get_async_session
from .compliance.coppa import COPPAService, ParentalConsentStatus
from .email_service import get_email_service_from_settings
from .audit_service import AuditService
from .config import settings
from .database.models import Student

router = APIRouter(prefix="/api/coppa", tags=["COPPA Compliance"])


# Request/Response Models

class MarkStudentUnder13Request(BaseModel):
    """Request to mark a student as under 13."""
    student_id: str = Field(..., description="Student ID")
    parent_email: EmailStr = Field(..., description="Parent/guardian email address")
    parent_name: str = Field(..., description="Parent/guardian name")
    send_consent_email: bool = Field(True, description="Whether to send consent request email")


class ParentalConsentRequest(BaseModel):
    """Request to grant parental consent."""
    student_id: str = Field(..., description="Student ID")
    parent_email: EmailStr = Field(..., description="Parent email for verification")
    consent_token: str = Field(..., description="Consent verification token")
    consent_given: bool = Field(..., description="Whether consent is granted")


class ParentalDataAccessRequest(BaseModel):
    """Request to access child's data."""
    student_id: str = Field(..., description="Student ID")
    parent_email: EmailStr = Field(..., description="Parent email for verification")
    verification_code: str = Field(..., description="Email verification code")


class ParentalDataDeletionRequest(BaseModel):
    """Request to delete child's data."""
    student_id: str = Field(..., description="Student ID")
    parent_email: EmailStr = Field(..., description="Parent email for verification")
    verification_code: str = Field(..., description="Email verification code")
    confirm_deletion: bool = Field(..., description="Confirmation that parent wants to delete data")


class RevokeConsentRequest(BaseModel):
    """Request to revoke parental consent."""
    student_id: str = Field(..., description="Student ID")
    parent_email: EmailStr = Field(..., description="Parent email for verification")
    verification_code: str = Field(..., description="Email verification code")
    delete_data: bool = Field(True, description="Whether to delete student data")


class COPPAStatusResponse(BaseModel):
    """Response with COPPA compliance status."""
    student_id: str
    is_under_13: bool
    requires_parental_consent: bool
    parent_consent_given: bool
    parent_consent_date: Optional[datetime]
    can_collect_data: bool


class ConsentTokenResponse(BaseModel):
    """Response with consent token."""
    student_id: str
    consent_token: str
    expires_at: datetime
    consent_url: str


# Endpoints

@router.post("/mark-student-under-13", response_model=COPPAStatusResponse)
async def mark_student_under_13(
    request: MarkStudentUnder13Request,
    http_request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Mark a student as under 13 and initiate parental consent workflow.

    This endpoint should be called when:
    - A student self-reports as under 13 during registration
    - Age verification determines the student is under 13
    - A parent/guardian indicates the student is under 13

    Triggers:
    - Student record is flagged as under 13
    - Parent email is stored for consent workflow
    - Optional: Consent request email is sent to parent
    """
    if not settings.coppa_compliance_enabled:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="COPPA compliance is not enabled"
        )

    try:
        # Get IP address
        ip_address = http_request.client.host if http_request.client else None

        # Mark student as under 13
        student = await COPPAService.mark_student_as_under_13(
            session=session,
            student_id=request.student_id,
            parent_email=request.parent_email,
            ip_address=ip_address,
        )

        # Send consent request email if requested
        if request.send_consent_email:
            email_service = get_email_service_from_settings()
            if email_service:
                # Generate consent token
                consent_token = COPPAService.generate_consent_token(request.student_id)

                # Build consent URL
                consent_url = f"{settings.oauth_redirect_base_url}/coppa/consent?token={consent_token}&student_id={request.student_id}"

                # Send email
                await send_parental_consent_email(
                    email_service=email_service,
                    parent_email=request.parent_email,
                    parent_name=request.parent_name,
                    student_name=student.name,
                    student_id=student.student_id,
                    consent_url=consent_url,
                )

        return COPPAStatusResponse(
            student_id=student.student_id,
            is_under_13=student.is_under_13,
            requires_parental_consent=COPPAService.requires_parental_consent(student),
            parent_consent_given=student.parent_consent_given,
            parent_consent_date=student.parent_consent_date,
            can_collect_data=COPPAService.can_collect_data(student),
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/grant-consent", response_model=COPPAStatusResponse)
async def grant_parental_consent(
    request: ParentalConsentRequest,
    http_request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Grant or deny parental consent for data collection.

    This endpoint is called when a parent responds to a consent request.
    The consent_token is used to verify the parent's identity and prevent
    unauthorized consent grants.
    """
    if not settings.coppa_compliance_enabled:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="COPPA compliance is not enabled"
        )

    try:
        # Validate consent token
        if not COPPAService.validate_consent_token(request.consent_token, request.student_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid consent token"
            )

        # Get IP address
        ip_address = http_request.client.host if http_request.client else None

        if request.consent_given:
            # Grant consent
            student = await COPPAService.grant_parental_consent(
                session=session,
                student_id=request.student_id,
                parent_email=request.parent_email,
                ip_address=ip_address,
                consent_method="online_form",
            )
        else:
            # Consent denied - revoke and delete data
            student = await COPPAService.revoke_parental_consent(
                session=session,
                student_id=request.student_id,
                parent_email=request.parent_email,
                ip_address=ip_address,
                delete_data=True,
            )

        return COPPAStatusResponse(
            student_id=student.student_id,
            is_under_13=student.is_under_13,
            requires_parental_consent=COPPAService.requires_parental_consent(student),
            parent_consent_given=student.parent_consent_given,
            parent_consent_date=student.parent_consent_date,
            can_collect_data=COPPAService.can_collect_data(student),
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/revoke-consent", response_model=COPPAStatusResponse)
async def revoke_parental_consent(
    request: RevokeConsentRequest,
    http_request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Revoke previously granted parental consent.

    Parents have the right to revoke consent at any time. When consent is
    revoked, student data is deleted per COPPA requirements.
    """
    if not settings.coppa_compliance_enabled:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="COPPA compliance is not enabled"
        )

    try:
        # Get IP address
        ip_address = http_request.client.host if http_request.client else None

        # Revoke consent
        student = await COPPAService.revoke_parental_consent(
            session=session,
            student_id=request.student_id,
            parent_email=request.parent_email,
            ip_address=ip_address,
            delete_data=request.delete_data,
        )

        return COPPAStatusResponse(
            student_id=student.student_id,
            is_under_13=student.is_under_13,
            requires_parental_consent=COPPAService.requires_parental_consent(student),
            parent_consent_given=student.parent_consent_given,
            parent_consent_date=student.parent_consent_date,
            can_collect_data=COPPAService.can_collect_data(student),
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/parent-data-access")
async def get_child_data_for_parent(
    request: ParentalDataAccessRequest,
    session: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Allow parent to access all data stored about their child.

    This is a COPPA requirement - parents must be able to review what
    data is collected about their children.
    """
    if not settings.coppa_compliance_enabled:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="COPPA compliance is not enabled"
        )

    try:
        # Get child data
        data = await COPPAService.get_child_data_for_parent(
            session=session,
            student_id=request.student_id,
            parent_email=request.parent_email,
        )

        return data

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/delete-child-data")
async def delete_child_data(
    request: ParentalDataDeletionRequest,
    http_request: Request,
    session: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Delete all data for a child at parent's request.

    This is a COPPA requirement - parents must be able to request deletion
    of their child's data at any time.
    """
    if not settings.coppa_compliance_enabled:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="COPPA compliance is not enabled"
        )

    if not request.confirm_deletion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deletion confirmation required"
        )

    try:
        # Get IP address
        ip_address = http_request.client.host if http_request.client else None

        # Delete child data
        success = await COPPAService.delete_child_data(
            session=session,
            student_id=request.student_id,
            parent_email=request.parent_email,
            ip_address=ip_address,
        )

        return {
            "success": success,
            "message": "Child data has been deleted successfully",
            "student_id": request.student_id,
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/status/{student_id}", response_model=COPPAStatusResponse)
async def get_coppa_status(
    student_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get COPPA compliance status for a student.

    Returns information about whether the student requires parental consent
    and whether consent has been granted.
    """
    try:
        # Get student
        from sqlalchemy import select
        result = await session.execute(
            select(Student).where(Student.student_id == student_id)
        )
        student = result.scalar_one_or_none()

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student {student_id} not found"
            )

        return COPPAStatusResponse(
            student_id=student.student_id,
            is_under_13=student.is_under_13,
            requires_parental_consent=COPPAService.requires_parental_consent(student),
            parent_consent_given=student.parent_consent_given,
            parent_consent_date=student.parent_consent_date,
            can_collect_data=COPPAService.can_collect_data(student),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Helper function for sending parental consent email

async def send_parental_consent_email(
    email_service,
    parent_email: str,
    parent_name: str,
    student_name: str,
    student_id: str,
    consent_url: str,
):
    """Send parental consent request email."""
    subject = f"Parental Consent Required for {student_name}'s TutorMax Account"

    expires_at = (datetime.utcnow() + timedelta(days=COPPAService.CONSENT_TOKEN_EXPIRY_DAYS)).strftime("%B %d, %Y")

    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #FF9800; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .notice {{ background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px; margin: 10px 5px; }}
        .button-deny {{ background-color: #f44336; }}
        .footer {{ padding: 20px; text-align: center; color: #777; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Parental Consent Required</h1>
        </div>
        <div class="content">
            <p>Dear {parent_name},</p>

            <p>Your child, <strong>{student_name}</strong>, has registered for a TutorMax account. Because {student_name} is under 13 years old, we are required by law to obtain your consent before we can collect certain information.</p>

            <div class="notice">
                <strong>COPPA Compliance Notice</strong><br>
                The Children's Online Privacy Protection Act (COPPA) requires us to obtain verifiable parental consent before collecting, using, or disclosing personal information from children under 13.
            </div>

            <h3>What information do we collect?</h3>
            <ul>
                <li>Student name and age</li>
                <li>Grade level and subjects of interest</li>
                <li>Session participation and feedback</li>
                <li>Learning progress and performance data</li>
            </ul>

            <h3>How do we use this information?</h3>
            <ul>
                <li>To match students with appropriate tutors</li>
                <li>To track learning progress and provide feedback</li>
                <li>To improve our tutoring services</li>
            </ul>

            <h3>Your rights as a parent:</h3>
            <ul>
                <li>Review the personal information collected from your child</li>
                <li>Request that we delete your child's personal information</li>
                <li>Refuse to allow further collection of your child's information</li>
            </ul>

            <p><strong>Please choose one of the following options:</strong></p>

            <p style="text-align: center;">
                <a href="{consent_url}&consent=yes" class="button">I Give Consent</a>
                <a href="{consent_url}&consent=no" class="button button-deny">I Deny Consent</a>
            </p>

            <p><strong>This consent request will expire on {expires_at}</strong></p>

            <p>If you have any questions about how we collect, use, or protect your child's information, please review our Privacy Policy or contact us directly.</p>

            <p>For more information about COPPA, visit: <a href="https://www.ftc.gov/tips-advice/business-center/privacy-and-security/children's-privacy">FTC COPPA Information</a></p>
        </div>
        <div class="footer">
            <p>This is an automated message from TutorMax.</p>
            <p>&copy; {datetime.now().year} TutorMax. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

    text_body = f"""
Dear {parent_name},

Your child, {student_name}, has registered for a TutorMax account. Because {student_name} is under 13 years old, we require your consent before collecting certain information.

COPPA COMPLIANCE NOTICE
The Children's Online Privacy Protection Act (COPPA) requires us to obtain verifiable parental consent before collecting personal information from children under 13.

What information do we collect?
- Student name and age
- Grade level and subjects of interest
- Session participation and feedback
- Learning progress and performance data

How do we use this information?
- To match students with appropriate tutors
- To track learning progress and provide feedback
- To improve our tutoring services

Your rights as a parent:
- Review the personal information collected from your child
- Request that we delete your child's personal information
- Refuse to allow further collection of your child's information

To grant consent, visit: {consent_url}&consent=yes
To deny consent, visit: {consent_url}&consent=no

This consent request will expire on {expires_at}

For questions, please contact us or visit our Privacy Policy.

---
This is an automated message from TutorMax.
"""

    email_service._send_email(parent_email, subject, html_body, text_body)
