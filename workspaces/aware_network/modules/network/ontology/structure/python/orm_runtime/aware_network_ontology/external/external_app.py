from __future__ import annotations

# Standard
from datetime import datetime
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Network Ontology
from aware_network_ontology.external.external_app_enums import ExternalAppStatus

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_instance

# Types
from aware_types import JsonObject


class ExternalApp(ORMModel):
    # Attributes
    error_count: int | None = Field(default=0)
    last_error: str | None = Field(default=None)
    last_error_at: datetime | None = Field(default=None)
    last_sync_at: datetime | None = Field(default=None)
    next_sync_at: datetime | None = Field(default=None)
    oauth_access_token: str | None = Field(default=None)
    oauth_expires_at: datetime | None = Field(default=None)
    oauth_refresh_token: str | None = Field(default=None)
    oauth_scope: list[str] = Field(default_factory=list)
    provider: str
    provider_email: str | None = Field(default=None)
    provider_metadata: JsonObject | None = Field(default_factory=JsonObject)
    provider_user_id: str | None = Field(default=None)
    rate_limit_remaining: int | None = Field(default=None)
    rate_limit_reset_at: datetime | None = Field(default=None)
    status: ExternalAppStatus = Field(default=ExternalAppStatus.inactive)
    webhook_expires_at: datetime | None = Field(default=None)
    webhook_id: str | None = Field(default=None)
    webhook_secret: str | None = Field(default=None)

    async def update_error(
        self, p_external_app_id: UUID, p_error: str, p_status: ExternalAppStatus | None = ExternalAppStatus.error
    ) -> None:
        """
        Updates error information for an external app.
        Parameters: p_external_app_id: The UUID of the external app
        p_error: Error message
        p_status: Optional new status (defaults to ERROR)
        Returns: void
        """

        payload = {"p_external_app_id": p_external_app_id, "p_error": p_error, "p_status": p_status}
        await invoke_instance(orm_model=self, function_name="update_error", payload=payload)
        return None

    async def update_oauth(
        self,
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

        payload = {
            "p_external_app_id": p_external_app_id,
            "p_access_token": p_access_token,
            "p_refresh_token": p_refresh_token,
            "p_expires_at": p_expires_at,
            "p_scope": p_scope,
        }
        await invoke_instance(orm_model=self, function_name="update_oauth", payload=payload)
        return None

    async def update_sync_status(
        self,
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

        payload = {
            "p_external_app_id": p_external_app_id,
            "p_last_sync_at": p_last_sync_at,
            "p_next_sync_at": p_next_sync_at,
            "p_rate_limit_remaining": p_rate_limit_remaining,
            "p_rate_limit_reset_at": p_rate_limit_reset_at,
        }
        await invoke_instance(orm_model=self, function_name="update_sync_status", payload=payload)
        return None

    async def update_webhook(
        self, p_external_app_id: UUID, p_webhook_id: str, p_webhook_secret: str, p_webhook_expires_at: datetime
    ) -> None:
        """
        Updates webhook settings for an external app.
        Parameters: p_external_app_id: The UUID of the external app
        p_webhook_id: Provider''s webhook/notification channel ID
        p_webhook_secret: Secret for webhook verification
        p_webhook_expires_at: Webhook expiration timestamp
        Returns: void
        """

        payload = {
            "p_external_app_id": p_external_app_id,
            "p_webhook_id": p_webhook_id,
            "p_webhook_secret": p_webhook_secret,
            "p_webhook_expires_at": p_webhook_expires_at,
        }
        await invoke_instance(orm_model=self, function_name="update_webhook", payload=payload)
        return None


class ExternalAppUpdateErrorInput(BaseModel):
    p_external_app_id: UUID
    p_error: str
    p_status: ExternalAppStatus | None = Field(default=ExternalAppStatus.error)


class ExternalAppUpdateErrorOutput(BaseModel):
    pass


class ExternalAppUpdateOauthInput(BaseModel):
    p_external_app_id: UUID
    p_access_token: str
    p_refresh_token: str
    p_expires_at: datetime
    p_scope: list[str] = Field(default_factory=list)


class ExternalAppUpdateOauthOutput(BaseModel):
    pass


class ExternalAppUpdateSyncStatusInput(BaseModel):
    p_external_app_id: UUID
    p_last_sync_at: datetime
    p_next_sync_at: datetime
    p_rate_limit_remaining: int | None = Field(default=None)
    p_rate_limit_reset_at: datetime | None = Field(default=None)


class ExternalAppUpdateSyncStatusOutput(BaseModel):
    pass


class ExternalAppUpdateWebhookInput(BaseModel):
    p_external_app_id: UUID
    p_webhook_id: str
    p_webhook_secret: str
    p_webhook_expires_at: datetime


class ExternalAppUpdateWebhookOutput(BaseModel):
    pass


FUNCTIONS = {
    "ExternalApp": {
        "update_error": {
            "canonical": {
                "name": "update_error",
                "description": "Updates error information for an external app.\nParameters: p_external_app_id: The UUID of the external app\np_error: Error message\np_status: Optional new status (defaults to ERROR)\nReturns: void",
                "is_constructor": False,
            },
            "input": ExternalAppUpdateErrorInput,
            "output": ExternalAppUpdateErrorOutput,
        },
        "update_oauth": {
            "canonical": {
                "name": "update_oauth",
                "description": "Updates OAuth credentials for an external app.\nParameters: p_external_app_id: The UUID of the external app\np_access_token: New OAuth access token\np_refresh_token: New OAuth refresh token\np_expires_at: Token expiration timestamp\np_scope: Array of OAuth scopes\nReturns: void",
                "is_constructor": False,
            },
            "input": ExternalAppUpdateOauthInput,
            "output": ExternalAppUpdateOauthOutput,
        },
        "update_sync_status": {
            "canonical": {
                "name": "update_sync_status",
                "description": "Updates sync status and rate limiting information for an external app.\nParameters: p_external_app_id: The UUID of the external app\np_last_sync_at: Timestamp of last successful sync\np_next_sync_at: Scheduled time for next sync\np_rate_limit_remaining: Optional remaining API calls\np_rate_limit_reset_at: Optional timestamp when rate limit resets\nReturns: void",
                "is_constructor": False,
            },
            "input": ExternalAppUpdateSyncStatusInput,
            "output": ExternalAppUpdateSyncStatusOutput,
        },
        "update_webhook": {
            "canonical": {
                "name": "update_webhook",
                "description": "Updates webhook settings for an external app.\nParameters: p_external_app_id: The UUID of the external app\np_webhook_id: Provider''s webhook/notification channel ID\np_webhook_secret: Secret for webhook verification\np_webhook_expires_at: Webhook expiration timestamp\nReturns: void",
                "is_constructor": False,
            },
            "input": ExternalAppUpdateWebhookInput,
            "output": ExternalAppUpdateWebhookOutput,
        },
    },
}

__all__ = [
    "ExternalApp",
    "ExternalAppUpdateErrorInput",
    "ExternalAppUpdateErrorOutput",
    "ExternalAppUpdateOauthInput",
    "ExternalAppUpdateOauthOutput",
    "ExternalAppUpdateSyncStatusInput",
    "ExternalAppUpdateSyncStatusOutput",
    "ExternalAppUpdateWebhookInput",
    "ExternalAppUpdateWebhookOutput",
    "FUNCTIONS",
]
