# Student Feedback Authentication - Quick Start Guide

## Overview

This guide provides quick instructions for using the student feedback authentication system in TutorMax.

## Architecture

```
Session Completes
    ↓
Generate Feedback Token (API)
    ↓
Send Email to Student/Parent
    ↓
Student Clicks Link
    ↓
Validate Token (Frontend)
    ↓
Display Feedback Form
    ↓
Submit Feedback (API)
    ↓
Store in Database
```

## API Endpoints

### 1. Request Feedback Token

**Endpoint**: `POST /api/feedback/request-token`

**When to call**: After a tutoring session completes

**Request**:
```json
{
    "session_id": "SES-123",
    "student_id": "STU-456",
    "student_email": "student@example.com",
    "send_email": true
}
```

**Response**:
```json
{
    "success": true,
    "token": "long-random-token-string",
    "feedback_url": "http://localhost:8000/feedback/submit?token=...",
    "expires_at": "2024-11-15T12:00:00Z",
    "session_id": "SES-123",
    "student_id": "STU-456",
    "email_sent": true,
    "parent_notification_sent": false
}
```

**Example (Python)**:
```python
import requests

response = requests.post(
    "http://localhost:8000/api/feedback/request-token",
    json={
        "session_id": "SES-123",
        "student_id": "STU-456",
        "student_email": "student@example.com",
        "send_email": True
    }
)

data = response.json()
print(f"Feedback URL: {data['feedback_url']}")
```

### 2. Validate Token

**Endpoint**: `POST /api/feedback/validate-token`

**When to call**: Before displaying the feedback form (frontend)

**Request**:
```json
{
    "token": "token-from-url-parameter"
}
```

**Response**:
```json
{
    "valid": true,
    "session_id": "SES-123",
    "student_id": "STU-456",
    "tutor_id": "TUT-789",
    "is_under_13": false,
    "requires_parent_consent": false,
    "expires_at": "2024-11-15T12:00:00Z",
    "message": "Token is valid"
}
```

**Example (JavaScript)**:
```javascript
const token = new URLSearchParams(window.location.search).get('token');

const response = await fetch('/api/feedback/validate-token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token })
});

const data = await response.json();

if (data.valid) {
    // Show feedback form
    if (data.requires_parent_consent) {
        // Show parent consent checkbox
    }
} else {
    // Show error: token invalid or expired
}
```

### 3. Submit Feedback

**Endpoint**: `POST /api/feedback/submit`

**When to call**: When student submits the feedback form

**Request**:
```json
{
    "token": "token-from-url",
    "overall_rating": 5,
    "subject_knowledge_rating": 5,
    "communication_rating": 5,
    "patience_rating": 4,
    "engagement_rating": 5,
    "helpfulness_rating": 5,
    "would_recommend": true,
    "improvement_areas": ["punctuality"],
    "free_text_feedback": "Great tutor! Very helpful.",
    "parent_consent_given": false
}
```

**Response**:
```json
{
    "success": true,
    "feedback_id": "FB-abc123",
    "session_id": "SES-123",
    "message": "Feedback submitted successfully",
    "timestamp": "2024-11-08T12:00:00Z"
}
```

**Example (JavaScript)**:
```javascript
const formData = {
    token: urlToken,
    overall_rating: 5,
    subject_knowledge_rating: 5,
    // ... other ratings
    would_recommend: true,
    free_text_feedback: "Great session!",
    parent_consent_given: parentConsentChecked
};

const response = await fetch('/api/feedback/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(formData)
});

const result = await response.json();

if (result.success) {
    // Show thank you message
} else {
    // Show error
}
```

## COPPA Compliance (Under-13 Students)

### Automatic Handling

The system automatically handles COPPA compliance:

1. **If student is under 13**:
   - Email sent to **parent** (not student)
   - Parent must provide consent before submission
   - Consent tracked in database

2. **Parent consent flow**:
   ```javascript
   // In frontend, check if consent required
   if (validationData.requires_parent_consent) {
       // Show checkbox:
       // ☐ I am the parent/guardian and consent to this feedback
   }

   // On submit, include consent
   const formData = {
       // ... other fields
       parent_consent_given: true,
       parent_signature: "Parent Name"
   };
   ```

### Recording Parent Consent Separately

**Endpoint**: `POST /api/feedback/parent-consent`

```json
{
    "student_id": "STU-456",
    "parent_email": "parent@example.com",
    "parent_name": "Jane Doe",
    "consent_given": true
}
```

## Email Configuration

### Setup SMTP (Required for Email Sending)

Add to `.env` file:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
SMTP_FROM_EMAIL=noreply@tutormax.com
SMTP_FROM_NAME=TutorMax
```

### Gmail Setup

1. Enable 2-factor authentication
2. Generate app-specific password
3. Use app password in `SMTP_PASSWORD`

### Test Email Configuration

```python
from src.api.email_service import get_email_service_from_settings

email_service = get_email_service_from_settings()

if email_service:
    success = email_service.send_feedback_invitation(
        student_email="test@example.com",
        student_name="Test Student",
        tutor_name="Test Tutor",
        session_date="November 8, 2024",
        feedback_url="http://localhost:8000/feedback/submit?token=test",
        expires_at="November 15, 2024"
    )
    print("Email sent!" if success else "Email failed!")
else:
    print("Email service not configured")
```

## Database Migration

Apply the COPPA fields migration:

```bash
# Create migration (already done)
# alembic revision --autogenerate -m "Add COPPA fields to students"

# Apply migration
cd /path/to/tutormax
alembic upgrade head

# Or using Python
python3 -m alembic upgrade head
```

## Integration Examples

### After Session Completion (Backend)

```python
from src.api.feedback_token_utils import FeedbackTokenManager, generate_feedback_url
from src.api.redis_service import redis_service
from src.api.email_service import get_email_service_from_settings

async def handle_session_completed(session_id: str, student_id: str, db: Session):
    # Get session and student info
    session = await db.get(Session, session_id)
    student = await db.get(Student, student_id)

    # Create token manager
    token_manager = FeedbackTokenManager(redis_service)

    # Generate token
    token = await token_manager.create_feedback_token(
        session_id=session_id,
        student_id=student_id,
        tutor_id=session.tutor_id,
        student_email=student.email if not student.is_under_13 else None,
        parent_email=student.parent_email if student.is_under_13 else None,
        is_under_13=student.is_under_13
    )

    # Generate URL
    feedback_url = generate_feedback_url(token)

    # Send email
    email_service = get_email_service_from_settings()
    if email_service:
        if student.is_under_13 and student.parent_email:
            email_service.send_parent_notification(
                parent_email=student.parent_email,
                parent_name="Parent",
                student_name=student.name,
                tutor_name=session.tutor.name,
                session_date=session.scheduled_start.strftime("%B %d, %Y"),
                feedback_url=feedback_url
            )
        elif student.email:
            email_service.send_feedback_invitation(
                student_email=student.email,
                student_name=student.name,
                tutor_name=session.tutor.name,
                session_date=session.scheduled_start.strftime("%B %d, %Y"),
                feedback_url=feedback_url,
                expires_at="7 days"
            )
```

### Frontend Feedback Form (React Example)

```jsx
import React, { useState, useEffect } from 'react';

function FeedbackForm() {
    const [token, setToken] = useState('');
    const [tokenData, setTokenData] = useState(null);
    const [rating, setRating] = useState(5);
    const [feedback, setFeedback] = useState('');
    const [parentConsent, setParentConsent] = useState(false);

    useEffect(() => {
        // Get token from URL
        const params = new URLSearchParams(window.location.search);
        const urlToken = params.get('token');
        setToken(urlToken);

        // Validate token
        if (urlToken) {
            validateToken(urlToken);
        }
    }, []);

    async function validateToken(token) {
        const response = await fetch('/api/feedback/validate-token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token })
        });

        const data = await response.json();

        if (data.valid) {
            setTokenData(data);
        } else {
            alert('Invalid or expired feedback link');
        }
    }

    async function submitFeedback(e) {
        e.preventDefault();

        const formData = {
            token,
            overall_rating: rating,
            free_text_feedback: feedback,
            parent_consent_given: parentConsent
        };

        const response = await fetch('/api/feedback/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (result.success) {
            alert('Thank you for your feedback!');
        } else {
            alert('Error submitting feedback');
        }
    }

    if (!tokenData) {
        return <div>Loading...</div>;
    }

    return (
        <form onSubmit={submitFeedback}>
            <h2>Session Feedback</h2>

            <div>
                <label>Overall Rating (1-5):</label>
                <input
                    type="number"
                    min="1"
                    max="5"
                    value={rating}
                    onChange={(e) => setRating(parseInt(e.target.value))}
                />
            </div>

            <div>
                <label>Comments:</label>
                <textarea
                    value={feedback}
                    onChange={(e) => setFeedback(e.target.value)}
                />
            </div>

            {tokenData.requires_parent_consent && (
                <div>
                    <label>
                        <input
                            type="checkbox"
                            checked={parentConsent}
                            onChange={(e) => setParentConsent(e.target.checked)}
                            required
                        />
                        I am the parent/guardian and consent to this feedback
                    </label>
                </div>
            )}

            <button type="submit">Submit Feedback</button>
        </form>
    );
}

export default FeedbackForm;
```

## Security Considerations

### Token Security
- ✅ Tokens are cryptographically random (256-bit)
- ✅ Tokens expire after 7 days
- ✅ Tokens are single-use only
- ✅ Tokens stored in Redis (automatic cleanup)

### COPPA Compliance
- ✅ Age verification via `is_under_13` flag
- ✅ Parent consent required and tracked
- ✅ Parent email used instead of student email
- ✅ Consent timestamp and IP recorded

### Rate Limiting
Consider adding rate limiting to prevent abuse:
```python
# In production, add rate limiting
@router.post("/request-token")
@rate_limit(requests=5, window=3600)  # 5 tokens per hour
async def request_feedback_token(...):
    ...
```

## Troubleshooting

### Email Not Sending
1. Check SMTP configuration in `.env`
2. Verify SMTP credentials
3. Check server logs for errors
4. Test with a simple email client

### Token Validation Fails
1. Check Redis is running
2. Verify token hasn't expired (7 days)
3. Check token hasn't been used already
4. Ensure token matches exactly (no extra spaces)

### COPPA Consent Issues
1. Verify student has `is_under_13` flag set
2. Check parent_email is configured
3. Ensure parent consent checkbox is checked
4. Review consent tracking in database

## Monitoring

### Key Metrics to Track
- Token generation rate
- Email delivery success rate
- Token validation success/failure rate
- Feedback submission rate
- COPPA consent compliance rate

### Log Analysis
```bash
# Check for token generation
grep "Created feedback token" /var/log/tutormax/app.log

# Check for email failures
grep "Failed to send email" /var/log/tutormax/app.log

# Check for COPPA consent
grep "Parent consent recorded" /var/log/tutormax/app.log
```

## Support

For issues or questions:
1. Check the main implementation doc: `TASK_14.3_FEEDBACK_AUTH_IMPLEMENTATION.md`
2. Review the code in `src/api/feedback_auth_router.py`
3. Run tests: `pytest tests/test_feedback_auth.py`

## Next Steps

1. Configure SMTP settings
2. Test email delivery
3. Create frontend feedback form
4. Integrate with session completion workflow
5. Monitor token usage and feedback submission
6. Review COPPA compliance with legal team
