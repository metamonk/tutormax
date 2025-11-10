# GDPR Router Integration Example

## Quick Start

To add the GDPR compliance endpoints to your TutorMax API:

### 1. Import the GDPR Router

Edit `/Users/zeno/Projects/tutormax/src/api/main.py`:

```python
# Add this import at the top with other router imports
from .gdpr_router import router as gdpr_router
```

### 2. Include the Router

Add this line in the "Application routers" section (around line 140):

```python
# Application routers
app.include_router(prediction_router)
app.include_router(websocket_router)
app.include_router(tutor_portal_router)
app.include_router(tutor_profile_router)
app.include_router(worker_monitoring_router)
app.include_router(feedback_auth_router)
app.include_router(audit_router)
app.include_router(gdpr_router)  # Add this line
```

### 3. Install Dependencies

```bash
pip install reportlab==4.0.9
```

Or use requirements.txt:
```bash
pip install -r requirements.txt
```

### 4. Test the Integration

Start the API server:
```bash
uvicorn src.api.main:app --reload
```

Visit the API docs to see the new GDPR endpoints:
```
http://localhost:8000/docs#/GDPR%20Compliance
```

## Available Endpoints

Once integrated, the following endpoints will be available:

- `GET /api/gdpr/export-my-data` - Export all user data
- `GET /api/gdpr/download-data-report` - Download portable data
- `POST /api/gdpr/delete-my-data` - Request account deletion
- `PUT /api/gdpr/rectify-data` - Correct user data
- `POST /api/gdpr/consent` - Manage consent
- `GET /api/gdpr/consent` - Get consent status
- `DELETE /api/gdpr/consent` - Withdraw all consents

## Testing

Use the interactive API documentation at `http://localhost:8000/docs` to test all endpoints.

All endpoints require authentication with a JWT token.

See `/Users/zeno/Projects/tutormax/docs/GDPR_COMPLIANCE.md` for complete documentation.
