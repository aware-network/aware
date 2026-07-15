from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from uuid import UUID

# Network Ontology
from aware_network_ontology.external.external_app_enums import ExternalAppStatus
from aware_network_ontology.external.external_app import ExternalApp

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def update_error(
    external_app: ExternalApp,
    p_external_app_id: UUID,
    p_error: str,
    p_status: ExternalAppStatus | None = ExternalAppStatus.error,
) -> None:
    """
    Updates error information for an external app.
    Parameters: p_external_app_id: The UUID of the external app
    p_error: Error message
    p_status: Optional new status (defaults to ERROR)
    Returns: void
    """

    # --- AWARE: LOGIC START update_error
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END update_error


async def update_oauth(
    external_app: ExternalApp,
    p_external_app_id: UUID,
    p_access_token: str,
    p_refresh_token: str,
    p_expires_at: datetime,
    p_scope: list[str],
) -> None:
    """
    Updates OAuth credentials for an external app.
    Parameters: p_external_app_id: The UUID of the external app
    p_access_token: New OAuth access token
    p_refresh_token: New OAuth refresh token
    p_expires_at: Token expiration timestamp
    p_scope: Array of OAuth scopes
    Returns: void
    """

    # --- AWARE: LOGIC START update_oauth
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END update_oauth


async def update_sync_status(
    external_app: ExternalApp,
    p_external_app_id: UUID,
    p_last_sync_at: datetime,
    p_next_sync_at: datetime,
    p_rate_limit_remaining: int | None = None,
    p_rate_limit_reset_at: datetime | None = None,
) -> None:
    """
    Updates sync status and rate limiting information for an external app.
    Parameters: p_external_app_id: The UUID of the external app
    p_last_sync_at: Timestamp of last successful sync
    p_next_sync_at: Scheduled time for next sync
    p_rate_limit_remaining: Optional remaining API calls
    p_rate_limit_reset_at: Optional timestamp when rate limit resets
    Returns: void
    """

    # --- AWARE: LOGIC START update_sync_status
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END update_sync_status


async def update_webhook(
    external_app: ExternalApp,
    p_external_app_id: UUID,
    p_webhook_id: str,
    p_webhook_secret: str,
    p_webhook_expires_at: datetime,
) -> None:
    """
    Updates webhook settings for an external app.
    Parameters: p_external_app_id: The UUID of the external app
    p_webhook_id: Provider''s webhook/notification channel ID
    p_webhook_secret: Secret for webhook verification
    p_webhook_expires_at: Webhook expiration timestamp
    Returns: void
    """

    # --- AWARE: LOGIC START update_webhook
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END update_webhook
