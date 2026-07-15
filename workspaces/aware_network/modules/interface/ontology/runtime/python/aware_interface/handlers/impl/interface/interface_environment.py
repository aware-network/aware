from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.interface.interface_environment import InterfaceEnvironment

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_interface.stable_ids import stable_interface_environment_id
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def create_via_interface(interface_id: UUID, environment_id: UUID) -> InterfaceEnvironment:
    """
    Creates a deterministic Interface -> Environment access association.
    """

    # --- AWARE: LOGIC START create_via_interface
    interface_environment_id = stable_interface_environment_id(
        interface_id=interface_id,
        environment_id=environment_id,
    )
    try:
        session = current_handler_session()
    except RuntimeError:
        session = None
    if session is not None:
        existing = session.imap_get(InterfaceEnvironment, interface_environment_id)
        if existing is not None:
            return existing
    return InterfaceEnvironment(
        id=interface_environment_id,
        interface_id=interface_id,
        environment_id=environment_id,
    )
    # --- AWARE: LOGIC END create_via_interface
