# Environment Variables Setup

This document describes the environment variables required for the TutorMax Next.js frontend.

## Quick Start

1. Copy the example file:
   ```bash
   cp .env.local.example .env.local
   ```

2. Update the values in `.env.local` if needed (defaults work for local development)

3. Start the development server:
   ```bash
   pnpm dev
   ```

## Environment Variables

### Required Variables

All client-side environment variables **must** use the `NEXT_PUBLIC_` prefix to be accessible in the browser.

#### `NEXT_PUBLIC_API_URL`
- **Description**: Base URL for the TutorMax backend API
- **Default**: `http://localhost:8000`
- **Production**: Update to your production API domain (e.g., `https://api.tutormax.com`)
- **Used for**: All HTTP API requests (authentication, user management, data fetching)

#### `NEXT_PUBLIC_WS_URL`
- **Description**: WebSocket URL for real-time dashboard updates
- **Default**: `ws://localhost:8000/ws/dashboard`
- **Production**: Update to your production WebSocket endpoint (e.g., `wss://api.tutormax.com/ws/dashboard`)
- **Used for**: Real-time metrics, alerts, and intervention updates

### Optional Variables

#### `NODE_ENV`
- **Description**: Node environment mode
- **Values**: `development`, `production`, `test`
- **Default**: Set automatically by Next.js
- **Note**: Only set this manually if you need to override the default behavior

## Backend API Endpoints

The following endpoints are available from the backend API:

### Authentication
- `POST /auth/jwt/login` - User login (returns JWT token)
- `POST /auth/jwt/logout` - User logout
- `POST /auth/register` - User registration
- `POST /auth/forgot-password` - Request password reset
- `POST /auth/reset-password` - Reset password with token
- `POST /auth/request-verify-token` - Request email verification
- `POST /auth/verify` - Verify email with token

### User Management
- `GET /users/me` - Get current authenticated user
- `PATCH /users/me` - Update current user
- `GET /users/{id}` - Get user by ID (admin only)
- `PATCH /users/{id}` - Update user (admin only)
- `DELETE /users/{id}` - Delete user (admin only)

### Admin
- `GET /api/admin/users` - List all users (admin only)
- `GET /api/admin/users/by-role/{role}` - Filter users by role (admin only)

### WebSocket
- `GET /ws/dashboard` - WebSocket connection for real-time dashboard updates

## Production Configuration

When deploying to production:

1. **Update API URLs**:
   ```env
   NEXT_PUBLIC_API_URL=https://api.tutormax.com
   NEXT_PUBLIC_WS_URL=wss://api.tutormax.com/ws/dashboard
   ```

2. **Use HTTPS/WSS**: Always use secure protocols (`https://` and `wss://`) in production

3. **Environment-specific files**:
   - `.env.local` - Local development (gitignored)
   - `.env.production` - Production build defaults
   - `.env.development` - Development build defaults

4. **Vercel/Platform-specific**:
   - Add environment variables in your deployment platform's dashboard
   - Vercel: Settings → Environment Variables
   - Netlify: Site settings → Build & deploy → Environment

## Troubleshooting

### Variables not loading
- Make sure variables start with `NEXT_PUBLIC_` for client-side access
- Restart the dev server after changing `.env.local`
- Clear `.next` cache: `rm -rf .next && pnpm dev`

### API connection errors
- Verify backend is running: `curl http://localhost:8000/docs`
- Check CORS settings in backend allow your frontend origin
- Verify `NEXT_PUBLIC_API_URL` doesn't have trailing slash

### WebSocket connection errors
- Ensure WebSocket endpoint is correct: `/ws/dashboard`
- Check backend WebSocket server is running
- Verify firewall/proxy allows WebSocket connections
- Use `wss://` (not `ws://`) in production

## Security Notes

- Never commit `.env.local` to git (it's in `.gitignore`)
- Use `.env.local.example` for sharing configuration templates
- Keep production secrets in your deployment platform's environment variables
- Rotate API keys and tokens regularly
- Use environment-specific values (never hardcode URLs in code)
