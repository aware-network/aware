from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Interface Ontology
from aware_interface_ontology.interface.interface_session_experience_session import InterfaceSessionExperienceSession

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_interface_ontology.stable_ids import (
    stable_interface_session_experience_session_id,
)
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_interface_session(
    interface_session_id: UUID,
    experience_session_id: UUID,
    status: str = "active",
    metadata_json: JsonObject | None = JsonObject(),
) -> InterfaceSessionExperienceSession:
    """
    Construct one InterfaceSession -> ExperienceSession portal row.

    Stable identity is InterfaceSession plus ExperienceSession. The target
    remains Experience-owned and no active-selection semantics are added.
    """

    # --- AWARE: LOGIC START build_via_interface_session
    if not isinstance(interface_session_id, UUID):
        raise TypeError(
            "InterfaceSessionExperienceSession.build_via_interface_session requires " "interface_session_id (UUID)"
        )
    if not isinstance(experience_session_id, UUID):
        raise TypeError(
            "InterfaceSessionExperienceSession.build_via_interface_session requires " "experience_session_id (UUID)"
        )

    mount_id = stable_interface_session_experience_session_id(
        interface_session_id=interface_session_id,
        experience_session_id=experience_session_id,
    )
    handler_session = current_handler_session()
    existing = handler_session.imap_get(InterfaceSessionExperienceSession, mount_id)
    if existing is not None:
        if (
            existing.interface_session_id != interface_session_id
            or existing.experience_session_id != experience_session_id
        ):
            raise RuntimeError(
                "InterfaceSessionExperienceSession.build_via_interface_session "
                f"mismatch for existing row: mount_id={mount_id}"
            )
        return existing

    return InterfaceSessionExperienceSession(
        id=mount_id,
        interface_session_id=interface_session_id,
        experience_session_id=experience_session_id,
        experience_session=None,
        status=status,
        metadata_json=metadata_json,
    )
    # --- AWARE: LOGIC END build_via_interface_session
