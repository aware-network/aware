from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.interface.interface_window_navigation_context import InterfaceWindowNavigationContext

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_interface.stable_ids import stable_interface_window_navigation_context_id
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def create_via_interface_window(
    interface_window_id: UUID, interface_environment_id: UUID, environment_navigation_context_id: UUID
) -> InterfaceWindowNavigationContext:
    """
    Creates a deterministic InterfaceWindow -> InterfaceEnvironment /
    EnvironmentNavigationContext target association.
    """

    # --- AWARE: LOGIC START create_via_interface_window
    link_id = stable_interface_window_navigation_context_id(
        interface_window_id=interface_window_id,
        interface_environment_id=interface_environment_id,
        environment_navigation_context_id=environment_navigation_context_id,
    )
    try:
        session = current_handler_session()
    except RuntimeError:
        session = None
    if session is not None:
        existing = session.imap_get(InterfaceWindowNavigationContext, link_id)
        if existing is not None:
            return existing
    return InterfaceWindowNavigationContext(
        id=link_id,
        interface_window_id=interface_window_id,
        interface_environment_id=interface_environment_id,
        environment_navigation_context_id=environment_navigation_context_id,
    )
    # --- AWARE: LOGIC END create_via_interface_window
