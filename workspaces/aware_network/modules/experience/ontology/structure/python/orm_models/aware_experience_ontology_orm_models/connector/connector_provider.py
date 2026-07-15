from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.connector.connector_session import ConnectorSession


class ConnectorProvider(ORMModel):
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

    # Foreign Keys
    connector_config_id: UUID = Field(description="Foreign key for ConnectorConfig.providers")
