# Test Users for TutorMax

## Available Test Users

The following test users have been created in the database for testing purposes:

### 1. Admin User
- **Email:** admin@tutormax.com
- **Password:** admin123
- **Roles:** admin, superuser
- **Permissions:** Full system access, can manage all users and resources

### 2. Tutor User
- **Email:** tutor@tutormax.com
- **Password:** tutor123
- **Roles:** tutor
- **Permissions:** Access to tutor portal, view own sessions and metrics

### 3. Student User
- **Email:** student@tutormax.com
- **Password:** student123
- **Roles:** student
- **Permissions:** Submit feedback, view own sessions

## API Endpoints

### Authentication

#### Login
```bash
POST /auth/jwt/login
Content-Type: application/x-www-form-urlencoded

username=admin@tutormax.com&password=admin123
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

#### Using cURL
```bash
# Login as admin
curl -X POST http://localhost:8000/auth/jwt/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@tutormax.com&password=admin123"

# Login as tutor
curl -X POST http://localhost:8000/auth/jwt/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=tutor@tutormax.com&password=tutor123"

# Login as student
curl -X POST http://localhost:8000/auth/jwt/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=student@tutormax.com&password=student123"
```

#### Register New User
```bash
POST /auth/register
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "securepassword",
  "full_name": "New User"
}
```

### Using Access Token

Once you have the access token, include it in the Authorization header:

```bash
curl -X GET http://localhost:8000/users/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

## Creating Additional Test Users

To create more test users or recreate the default ones:

```bash
# Run the user creation script
python3 scripts/create_test_user.py
```

The script will:
1. Check for existing users in the database
2. Display current users if any exist
3. Ask if you want to create additional users
4. Create the three default test users (admin, tutor, student)

## Checking Existing Users

To check what users exist in the database:

```bash
# Run the database check script
python3 scripts/check_database_data.py
```

Or query directly via the API (requires admin access):

```bash
# Get all users (admin only)
curl -X GET http://localhost:8000/api/admin/users \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"

# Get users by role (admin only)
curl -X GET http://localhost:8000/api/admin/users/by-role/tutor \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

## Password Requirements

Default password policy (configured in `.env`):
- Minimum length: 8 characters
- Requires uppercase letter: Yes
- Requires lowercase letter: Yes
- Requires digit: Yes
- Requires special character: No

## Security Notes

⚠️ **IMPORTANT:** These are TEST credentials only!

- **DO NOT use these credentials in production**
- Change all passwords before deploying to production
- Use strong, unique passwords for production users
- Consider enabling two-factor authentication
- Rotate passwords regularly

## Testing Different Roles

### Admin Testing
Login as admin to test:
- User management (`/api/admin/users`)
- System configuration
- Access to all resources
- Audit logs (`/api/audit/logs`)

### Tutor Testing
Login as tutor to test:
- Tutor portal (`/api/tutor/portal/*`)
- Session management
- Performance metrics view
- Student feedback view

### Student Testing
Login as student to test:
- Feedback submission
- Session viewing
- Limited permissions

## Token Expiration

- **Access Token:** 30 minutes (default)
- **Refresh Token:** 7 days (default)

Configure in `.env`:
```bash
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

## Troubleshooting

### Login Failed
- Check email and password are correct
- Verify user exists in database
- Check user is active (`is_active=true`)
- Review API logs for error details

### Token Invalid
- Token may have expired (30 minutes)
- Obtain a new token by logging in again
- Check token is properly formatted in Authorization header

### Permission Denied
- User may not have required role
- Check endpoint requires correct permissions
- Verify RBAC configuration

## Related Documentation

- **Authentication System:** `/docs/SECURITY_HARDENING.md`
- **RBAC Configuration:** `/src/api/auth/rbac.py`
- **User Management:** `/src/api/auth/admin_router.py`
- **Audit Logging:** `/docs/AUDIT_LOGGING_QUICKSTART.md`
- **API Documentation:** http://localhost:8000/docs (when API is running)
