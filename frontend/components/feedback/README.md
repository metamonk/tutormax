# Student Feedback Components

This directory contains the student feedback form components for TutorMax.

## Components

### StudentFeedbackForm
A comprehensive feedback form for students to rate their tutoring sessions.

**Features:**
- Star ratings using Kibo UI Rating component
- Multiple rating categories:
  - Overall session rating
  - Tutor helpfulness
  - Content clarity
  - Subject knowledge
  - Communication
- Yes/No recommendation toggle
- Multi-select improvement areas
- Optional text comments
- COPPA compliance for under-13 students
- Form validation with Zod
- Loading and error states
- Success message after submission

**Props:**
```typescript
interface StudentFeedbackFormProps {
  token: string;                    // Feedback token from email
  sessionInfo: {
    tutor_name?: string;
    session_date?: string;
    subject?: string;
  };
  requiresParentConsent?: boolean;  // For under-13 students
  isUnder13?: boolean;              // COPPA compliance flag
  onSuccess?: () => void;           // Callback after successful submission
}
```

**Usage:**
```tsx
import { StudentFeedbackForm } from '@/components/feedback';

<StudentFeedbackForm
  token={feedbackToken}
  sessionInfo={{
    tutor_name: "John Doe",
    session_date: "2024-11-09",
    subject: "Mathematics"
  }}
  requiresParentConsent={false}
  isUnder13={false}
  onSuccess={() => console.log('Feedback submitted!')}
/>
```

## Pages

### /feedback/[token]
Public feedback page that validates the token and displays the feedback form.

**Features:**
- Token validation on page load
- Session information display
- Handles expired/invalid tokens
- Prevents duplicate submissions
- COPPA compliance notice for under-13 students
- Privacy policy link
- Success message after submission

**URL:**
```
http://localhost:3000/feedback/[token]
```

## API Integration

The components use the following API endpoints:

### POST /api/feedback/validate-token
Validates a feedback token and returns session information.

**Request:**
```json
{
  "token": "abc123xyz789..."
}
```

**Response:**
```json
{
  "valid": true,
  "session_id": "SES-001",
  "student_id": "STU-001",
  "tutor_id": "TUT-001",
  "tutor_name": "John Doe",
  "session_date": "2024-11-09T10:00:00",
  "subject": "Mathematics",
  "is_under_13": false,
  "requires_parent_consent": false,
  "expires_at": "2024-11-16T10:00:00",
  "message": "Token is valid"
}
```

### POST /api/feedback/submit
Submits student feedback.

**Request:**
```json
{
  "token": "abc123xyz789...",
  "overall_rating": 5,
  "subject_knowledge_rating": 5,
  "communication_rating": 5,
  "patience_rating": 4,
  "engagement_rating": 5,
  "helpfulness_rating": 5,
  "would_recommend": true,
  "improvement_areas": ["punctuality"],
  "free_text_feedback": "Great tutor!",
  "parent_consent_given": false,
  "parent_signature": null
}
```

**Response:**
```json
{
  "success": true,
  "feedback_id": "FB-001",
  "session_id": "SES-001",
  "message": "Feedback submitted successfully",
  "timestamp": "2024-11-09T10:00:00"
}
```

## COPPA Compliance

For students under 13:
- Parent consent checkbox is required
- Parent/guardian name field is required
- Privacy notice is displayed
- Parent email notification is sent (backend)

## Styling

- Uses Tailwind CSS v4
- shadcn/ui components for form elements
- Kibo UI rating component for star ratings
- Responsive design with mobile-first approach
- Large touch targets for mobile devices
- Accessible form labels and error messages

## Testing

To test the feedback flow:

1. Generate a feedback token using the backend API
2. Navigate to `/feedback/[token]`
3. Fill out the form
4. Submit and verify success message

Example test token generation (backend):
```python
from src.api.feedback_token_utils import FeedbackTokenManager

token = await token_manager.create_feedback_token(
    session_id="SES-001",
    student_id="STU-001",
    tutor_id="TUT-001",
    student_email="student@example.com"
)
```

## Dependencies

- Next.js 16 App Router
- React 19
- TypeScript
- react-hook-form
- zod
- Kibo UI (rating component)
- shadcn/ui (form, input, textarea, button, checkbox, radio-group)
- Tailwind CSS v4
