from __future__ import annotations

# Standard
from datetime import datetime

# Third-party
from pydantic import Field

# Network Ontology Orm Models
from aware_network_ontology_orm_models.external.external_app_enums import ExternalAppStatus

# Orm
from aware_orm.models.orm_model import ORMModel

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
