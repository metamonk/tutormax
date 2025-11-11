# OAuth/SSO Setup Guide

This guide explains how to set up and test OAuth/SSO authentication with Google and Microsoft.

## Overview

TutorMax supports OAuth 2.0 authentication with:
- **Google OAuth** (Google Workspace accounts)
- **Microsoft OAuth** (Microsoft 365/Azure AD accounts)

## OAuth Endpoints

Once configured, the following endpoints are available:

### Google OAuth
- **Authorization URL**: `GET /auth/google/authorize`
  - Redirects user to Google login
  - Returns OAuth state for CSRF protection

- **Callback URL**: `GET /auth/google/callback`
  - Handles OAuth callback from Google
  - Returns JWT access token on success
  - Automatically creates user account if email doesn't exist

### Microsoft OAuth
- **Authorization URL**: `GET /auth/microsoft/authorize`
  - Redirects user to Microsoft login

- **Callback URL**: `GET /auth/microsoft/callback`
  - Handles OAuth callback from Microsoft
  - Returns JWT access token on success

## Setup Instructions

### 1. Google OAuth Setup

1. **Create Google OAuth 2.0 Credentials**:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or select existing one
   - Navigate to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client ID"
   - Select "Web application"
   - Add authorized redirect URI: `http://localhost:8000/auth/google/callback`
   - For production, add: `https://yourdomain.com/auth/google/callback`

2. **Update .env file**:
   ```bash
   GOOGLE_CLIENT_ID="your-google-client-id.apps.googleusercontent.com"
   GOOGLE_CLIENT_SECRET="your-google-client-secret"
   OAUTH_REDIRECT_BASE_URL="http://localhost:8000"  # Update for production
   ```

### 2. Microsoft OAuth Setup

1. **Register Application in Azure AD**:
   - Go to [Azure Portal](https://portal.azure.com)
   - Navigate to "Azure Active Directory" > "App registrations"
   - Click "New registration"
   - Set name: "TutorMax"
   - Select "Accounts in any organizational directory and personal Microsoft accounts"
   - Add redirect URI: `http://localhost:8000/auth/microsoft/callback`
   - For production, add: `https://yourdomain.com/auth/microsoft/callback`

2. **Create Client Secret**:
   - In your app registration, go to "Certificates & secrets"
   - Click "New client secret"
   - Copy the secret value (shown once!)

3. **Update .env file**:
   ```bash
   MICROSOFT_CLIENT_ID="your-microsoft-client-id"
   MICROSOFT_CLIENT_SECRET="your-microsoft-client-secret"
   OAUTH_REDIRECT_BASE_URL="http://localhost:8000"  # Update for production
   ```

## Testing OAuth Flow

### Manual Testing

1. **Start the API server**:
   ```bash
   uvicorn src.api.main:app --reload
   ```

2. **Test Google OAuth**:
   - Open browser to: `http://localhost:8000/auth/google/authorize`
   - You'll be redirected to Google login
   - After login, you'll be redirected back with JWT token
   - Token format: `{"access_token": "...", "token_type": "bearer"}`

3. **Test Microsoft OAuth**:
   - Open browser to: `http://localhost:8000/auth/microsoft/authorize`
   - You'll be redirected to Microsoft login
   - After login, you'll be redirected back with JWT token

### Frontend Integration

To integrate OAuth in the frontend login page:

```typescript
// Login component
const handleGoogleLogin = () => {
  // Redirect to Google OAuth
  window.location.href = `${API_BASE_URL}/auth/google/authorize`;
};

const handleMicrosoftLogin = () => {
  // Redirect to Microsoft OAuth
  window.location.href = `${API_BASE_URL}/auth/microsoft/authorize`;
};

// Callback handling (in callback route)
useEffect(() => {
  const params = new URLSearchParams(window.location.search);
  const accessToken = params.get('access_token');

  if (accessToken) {
    // Store token
    localStorage.setItem('token', accessToken);
    // Redirect to dashboard
    router.push('/dashboard');
  }
}, []);
```

### Testing with Postman/cURL

```bash
# Step 1: Get authorization URL
curl http://localhost:8000/auth/google/authorize

# Step 2: Copy the authorization_url from response and open in browser
# Step 3: After login, you'll be redirected to callback with token

# Test authenticated request with token
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  http://localhost:8000/api/users/me
```

## User Account Linking

The OAuth integration supports **account linking** via email:
- If a user with the same email already exists (registered via email/password), the OAuth account will be linked to the existing user
- If no user exists, a new account is created automatically
- OAuth users can still set a password later to enable email/password login

## Security Features

1. **State Parameter**: CSRF protection using OAuth state parameter
2. **Token Security**: JWT tokens with configurable expiration
3. **Email Verification**: OAuth-authenticated users are automatically verified
4. **Account Association**: Prevents duplicate accounts for same email

## Troubleshooting

### "Invalid client" error
- Verify CLIENT_ID and CLIENT_SECRET are correct
- Check that redirect URI matches exactly (including http/https)

### "Redirect URI mismatch" error
- Add the callback URL to your OAuth app configuration
- Ensure OAUTH_REDIRECT_BASE_URL in .env matches your server URL

### "User not found" after OAuth
- Check database connection
- Verify User model includes oauth_provider and oauth_subject fields
- Check logs for user creation errors

## Production Checklist

- [ ] Update OAUTH_REDIRECT_BASE_URL to production domain
- [ ] Add production callback URLs to Google/Microsoft OAuth apps
- [ ] Use HTTPS for all OAuth redirects
- [ ] Rotate CLIENT_SECRET regularly
- [ ] Monitor failed OAuth attempts in audit logs
- [ ] Test account linking with existing users
- [ ] Verify CORS settings allow OAuth redirects

## API Documentation

Once the server is running, view complete OAuth API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

Look for the "auth" and "oauth" tags to find OAuth endpoints.
