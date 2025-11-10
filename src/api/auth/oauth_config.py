"""
OAuth configuration for Google and Microsoft SSO.

This module configures OAuth clients and routers for social authentication.
Supports both Google and Microsoft OAuth 2.0 flows.
"""

from typing import Optional, cast
from httpx_oauth.clients.google import GoogleOAuth2
from httpx_oauth.clients.microsoft import MicrosoftGraphOAuth2
from fastapi import Request
from fastapi_users.authentication import AuthenticationBackend

from ..config import settings
from .fastapi_users_config import fastapi_users


# Google OAuth Client
google_oauth_client = GoogleOAuth2(
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
)

# Microsoft OAuth Client
microsoft_oauth_client = MicrosoftGraphOAuth2(
    client_id=settings.microsoft_client_id,
    client_secret=settings.microsoft_client_secret,
)


def get_oauth_routers(backend: AuthenticationBackend):
    """
    Get OAuth routers for Google and Microsoft.

    Args:
        backend: Authentication backend to use for OAuth flows

    Returns:
        Tuple of (google_router, microsoft_router)
    """
    # Google OAuth router
    google_oauth_router = fastapi_users.get_oauth_router(
        oauth_client=google_oauth_client,
        backend=backend,
        state_secret=settings.secret_key,
        redirect_url=f"{settings.oauth_redirect_base_url}/auth/google/callback",
        # Associate OAuth account with existing user if email matches
        associate_by_email=True,
    )

    # Microsoft OAuth router
    microsoft_oauth_router = fastapi_users.get_oauth_router(
        oauth_client=microsoft_oauth_client,
        backend=backend,
        state_secret=settings.secret_key,
        redirect_url=f"{settings.oauth_redirect_base_url}/auth/microsoft/callback",
        # Associate OAuth account with existing user if email matches
        associate_by_email=True,
    )

    return google_oauth_router, microsoft_oauth_router
