from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Identity Ontology
from aware_identity_ontology.identity.identity_connection_enums import ConnectionRequestStatus
from aware_identity_ontology.identity.identity_connection import IdentityConnection

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Identity Runtime
from aware_identity.context import current_actor_id, current_branch_id
from aware_identity_ontology.stable_ids import (
    stable_actor_id,
    stable_identity_connection_id,
)


def _connection_status(value: object) -> ConnectionRequestStatus:
    if isinstance(value, ConnectionRequestStatus):
        return value
    return ConnectionRequestStatus(getattr(value, "value", value))


# --- AWARE: USER_IMPORTS END


async def request(
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

    # --- AWARE: LOGIC START request
    requester_identity_id = (
        requester_identity_id if isinstance(requester_identity_id, UUID) else UUID(str(requester_identity_id))
    )
    recipient_identity_id = (
        recipient_identity_id if isinstance(recipient_identity_id, UUID) else UUID(str(recipient_identity_id))
    )
    if requester_identity_id == recipient_identity_id:
        raise ValueError("IdentityConnection.request requires distinct identities")

    expected_actor_id = stable_actor_id(identity_id=requester_identity_id)
    actual_actor_id = current_actor_id()
    if actual_actor_id != expected_actor_id:
        raise ValueError(
            "forbidden: actor_id does not match requester identity (anti-claim): "
            f"actor_id={actual_actor_id} expected={expected_actor_id}"
        )

    normalized_type = (connection_type or "").casefold().strip() or "connect"
    expected_connection_id = stable_identity_connection_id(
        requester_identity_id=requester_identity_id,
        recipient_identity_id=recipient_identity_id,
        connection_type=normalized_type,
    )

    actual_branch_id = current_branch_id()
    if actual_branch_id != expected_connection_id:
        raise ValueError(
            "forbidden: branch_id does not match stable IdentityConnection id: "
            f"branch_id={actual_branch_id} expected={expected_connection_id}"
        )

    return IdentityConnection(
        id=expected_connection_id,
        requester_identity_id=requester_identity_id,
        recipient_identity_id=recipient_identity_id,
        connection_type=normalized_type,
        metadata=metadata,
        status=ConnectionRequestStatus.pending,
    )
    # --- AWARE: LOGIC END request


async def respond(identity_connection: IdentityConnection, status: ConnectionRequestStatus) -> IdentityConnection:
    """
    Accept or reject a pending IdentityConnection request (v0).

    Canonical contract:
    - Only the recipient may respond (anti-claim on recipient identity).
    - Allowed transitions: pending -> accepted|rejected (idempotent).
    """

    # --- AWARE: LOGIC START respond
    if identity_connection.requester_identity_id is None:
        raise ValueError("IdentityConnection.respond requires requester_identity_id")
    if identity_connection.recipient_identity_id is None:
        raise ValueError("IdentityConnection.respond requires recipient_identity_id")
    requester_identity_id = (
        identity_connection.requester_identity_id
        if isinstance(identity_connection.requester_identity_id, UUID)
        else UUID(str(identity_connection.requester_identity_id))
    )
    recipient_identity_id = (
        identity_connection.recipient_identity_id
        if isinstance(identity_connection.recipient_identity_id, UUID)
        else UUID(str(identity_connection.recipient_identity_id))
    )
    connection_id = (
        identity_connection.id
        if identity_connection.id is None or isinstance(identity_connection.id, UUID)
        else UUID(str(identity_connection.id))
    )

    normalized_type = (identity_connection.connection_type or "").casefold().strip() or "connect"
    expected_connection_id = stable_identity_connection_id(
        requester_identity_id=requester_identity_id,
        recipient_identity_id=recipient_identity_id,
        connection_type=normalized_type,
    )

    if connection_id != expected_connection_id:
        raise ValueError(
            "IdentityConnection invariant violated: id does not match stable id: "
            f"id={identity_connection.id} expected={expected_connection_id}"
        )

    actual_branch_id = current_branch_id()
    if actual_branch_id != expected_connection_id:
        raise ValueError(
            "forbidden: branch_id does not match IdentityConnection id: "
            f"branch_id={actual_branch_id} expected={expected_connection_id}"
        )

    requested_status = _connection_status(status)
    if requested_status == ConnectionRequestStatus.pending:
        raise ValueError("IdentityConnection.respond requires status in {'accepted','rejected'}")

    expected_actor_id = stable_actor_id(identity_id=recipient_identity_id)
    actual_actor_id = current_actor_id()
    if actual_actor_id != expected_actor_id:
        raise ValueError(
            "forbidden: actor_id does not match recipient identity (anti-claim): "
            f"actor_id={actual_actor_id} expected={expected_actor_id}"
        )

    current_status = _connection_status(identity_connection.status)
    if current_status == requested_status:
        return identity_connection

    if current_status != ConnectionRequestStatus.pending:
        raise ValueError("IdentityConnection.respond forbidden: request already finalized: " f"status={current_status}")

    identity_connection.status = requested_status
    return identity_connection
    # --- AWARE: LOGIC END respond
