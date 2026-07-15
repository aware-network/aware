from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Identity Ontology
from aware_identity_ontology.identity.identity_connection_enums import ConnectionRequestStatus

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_identity_ontology.identity.identity import Identity


class IdentityConnection(ORMModel):
    # Relationships
    requester_identity: Identity | None = Field(default=None, exclude=True)
    recipient_identity: Identity | None = Field(default=None, exclude=True)

    # Attributes
    connection_type: str = Field(default="connect")
    metadata: JsonObject | None = Field(default=None)
    status: ConnectionRequestStatus = Field(default=ConnectionRequestStatus.pending)

    # Foreign Keys
    requester_identity_id: UUID = Field(description="Foreign key for IdentityConnection.requester_identity")
    recipient_identity_id: UUID = Field(description="Foreign key for IdentityConnection.recipient_identity")

    @classmethod
    async def request(
        cls,
        requester_identity_id: UUID,
        recipient_identity_id: UUID,
        connection_type: str = "connect",
        metadata: JsonObject | None = None,
    ) -> IdentityConnection:
        """
        Create a connection lane between two identities (v0).

        Canonical contract:
        - IdentityConnection is a first-class lane in the `identity_connection` projection.
        - This constructor initializes the lane with status=`pending` (a request).
        - Anti-claim: only the requester may create the request.
        - Branch id MUST be stable and derived from (requester_identity_id, recipient_identity_id,
        connection_type).
        """

        payload = {
            "requester_identity_id": requester_identity_id,
            "recipient_identity_id": recipient_identity_id,
            "connection_type": connection_type,
            "metadata": metadata,
        }
        result = await invoke_constructor(orm_class=cls, function_name="request", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, IdentityConnection):
            return value
        return IdentityConnection.validate_invocation_value(value)

    async def respond(self, status: ConnectionRequestStatus) -> IdentityConnection:
        """
        Accept or reject a pending IdentityConnection request (v0).

        Canonical contract:
        - Only the recipient may respond (anti-claim on recipient identity).
        - Allowed transitions: pending -> accepted|rejected (idempotent).
        """

        payload = {"status": status}
        result = await invoke_instance(orm_model=self, function_name="respond", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, IdentityConnection):
            return value
        return IdentityConnection.validate_invocation_value(value)


class IdentityConnectionRequestInput(BaseModel):
    requester_identity_id: UUID
    recipient_identity_id: UUID
    connection_type: str = Field(default="connect")
    metadata: JsonObject | None = Field(default=None)


class IdentityConnectionRequestOutput(BaseModel):
    value: IdentityConnection


class IdentityConnectionRespondInput(BaseModel):
    status: ConnectionRequestStatus


class IdentityConnectionRespondOutput(BaseModel):
    value: IdentityConnection


FUNCTIONS = {
    "IdentityConnection": {
        "request": {
            "canonical": {
                "name": "request",
                "description": "Create a connection lane between two identities (v0).\n\nCanonical contract:\n- IdentityConnection is a first-class lane in the `identity_connection` projection.\n- This constructor initializes the lane with status=`pending` (a request).\n- Anti-claim: only the requester may create the request.\n- Branch id MUST be stable and derived from (requester_identity_id, recipient_identity_id, connection_type).",
                "is_constructor": True,
            },
            "input": IdentityConnectionRequestInput,
            "output": IdentityConnectionRequestOutput,
        },
        "respond": {
            "canonical": {
                "name": "respond",
                "description": "Accept or reject a pending IdentityConnection request (v0).\n\nCanonical contract:\n- Only the recipient may respond (anti-claim on recipient identity).\n- Allowed transitions: pending -> accepted|rejected (idempotent).",
                "is_constructor": False,
            },
            "input": IdentityConnectionRespondInput,
            "output": IdentityConnectionRespondOutput,
        },
    },
}

__all__ = [
    "IdentityConnection",
    "IdentityConnectionRequestInput",
    "IdentityConnectionRequestOutput",
    "IdentityConnectionRespondInput",
    "IdentityConnectionRespondOutput",
    "FUNCTIONS",
]
