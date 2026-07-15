from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.connector.connector_session import ConnectorSession


class ConnectorProvider(BaseModel):
    """
    Connector provider configuration.
    Contract:
    - A ConnectorProvider identifies a concrete provider for a ConnectorConfig
    capability family.
    - Provider config is reusable and does not represent a live login/session.
    - ConnectorSession records concrete provider fulfillment context and links
    to the runtime Connector instance.
    """

    # Relationships
    sessions: list[ConnectorSession] = Field(default_factory=list)

    # Attributes
    provider_key: str
    provider_kind: str
    provider_ref: str | None = Field(default=None)
    label: str | None = Field(default=None)
    description: str | None = Field(default=None)
