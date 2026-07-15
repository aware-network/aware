from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.connector.connector import Connector


class ConnectorSession(BaseModel):
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
