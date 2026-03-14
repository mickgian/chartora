"""Email service using Resend.com for transactional emails."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from src.config.settings import Settings

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


async def send_password_reset_email(
    to_email: str,
    reset_token: str,
    settings: Settings,
) -> bool:
    """Send a password reset email via Resend.com.

    Returns True if sent successfully, False otherwise.
    """
    if not settings.resend_api_key:
        logger.warning("Resend API key not configured — skipping email to %s", to_email)
        return False

    reset_url = f"{settings.frontend_url}/reset-password?token={reset_token}"

    payload = {
        "from": settings.email_from,
        "to": [to_email],
        "subject": "Reset your Chartora password",
        "html": (
            "<h2>Password Reset</h2>"
            "<p>You requested a password reset for your Chartora account.</p>"
            f'<p><a href="{reset_url}">Click here to reset your password</a></p>'
            "<p>This link expires in 1 hour. If you didn't request this, "
            "you can safely ignore this email.</p>"
        ),
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                RESEND_API_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {settings.resend_api_key}",
                    "Content-Type": "application/json",
                },
                timeout=10.0,
            )
            if response.status_code < 300:
                logger.info("Password reset email sent to %s", to_email)
                return True
            logger.error(
                "Resend API error %s: %s", response.status_code, response.text
            )
            return False
    except httpx.HTTPError:
        logger.exception("Failed to send password reset email to %s", to_email)
        return False


async def send_alert_email(
    to_email: str,
    subject: str,
    html_body: str,
    settings: Settings,
) -> bool:
    """Send an alert email via Resend.com."""
    if not settings.resend_api_key:
        logger.warning("Resend API key not configured — skipping alert email")
        return False

    payload = {
        "from": settings.email_from,
        "to": [to_email],
        "subject": subject,
        "html": html_body,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                RESEND_API_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {settings.resend_api_key}",
                    "Content-Type": "application/json",
                },
                timeout=10.0,
            )
            return response.status_code < 300
    except httpx.HTTPError:
        logger.exception("Failed to send alert email to %s", to_email)
        return False
