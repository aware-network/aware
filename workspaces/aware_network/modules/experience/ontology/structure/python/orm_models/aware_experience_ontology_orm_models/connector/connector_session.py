from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.connector.connector import Connector


class ConnectorSession(ORMModel):
    """
    Connector provider session.
    Contract:
    - A ConnectorSession is the concrete provider/session fulfillment context.
    - It links a provider config to one runtime Connector instance.
    - Connector owns the fulfilled Sensor/Actuator instances and invocation
    receipts remain on the shared Experience invocation spine.
    """

    # Relationships
    connector: Connector | None = Field(default=None)

    # Attributes
    session_key: str
    session_ref: str | None = Field(default=None)
    host_ref: str | None = Field(default=None)
    principal_ref: str | None = Field(default=None)
    status: str = Field(default="active")

    # Foreign Keys
    connector_provider_id: UUID = Field(description="Foreign key for ConnectorProvider.sessions")
    connector_id: UUID = Field(description="Foreign key for ConnectorSession.connector")
