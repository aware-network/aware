from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.interface.interface_window import InterfaceWindow
from aware_interface_ontology.interface.interface_window_navigation_context import InterfaceWindowNavigationContext

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Standard
from aware_interface.stable_ids import stable_interface_window_id, stable_interface_window_navigation_context_id

# --- AWARE: USER_IMPORTS END


async def attach_navigation_context(
    interface_window: InterfaceWindow, interface_environment_id: UUID, environment_navigation_context_id: UUID
) -> InterfaceWindowNavigationContext:
    """
    Creates (or ensures) a window target over an Interface-authorized
    EnvironmentNavigationContext.

    Contract:
    - InterfaceWindow follows Environment navigation context truth.
    - The selected Process/Thread target resolves from the navigation context.
    - The selected Thread's active layout remains Environment/Attention truth.
    """

    # --- AWARE: LOGIC START attach_navigation_context
    if interface_window.id is None:
        raise RuntimeError("InterfaceWindow.attach_navigation_context requires InterfaceWindow.id")
    if not isinstance(interface_environment_id, UUID):
        raise TypeError("InterfaceWindow.attach_navigation_context requires interface_environment_id (UUID)")
    if not isinstance(environment_navigation_context_id, UUID):
        raise TypeError("InterfaceWindow.attach_navigation_context requires environment_navigation_context_id (UUID)")

    link_id = stable_interface_window_navigation_context_id(
        interface_window_id=interface_window.id,
        interface_environment_id=interface_environment_id,
        environment_navigation_context_id=environment_navigation_context_id,
    )
    for existing in interface_window.window_navigation_contexts:
        if existing.id == link_id or (
            existing.interface_environment_id == interface_environment_id
            and existing.environment_navigation_context_id == environment_navigation_context_id
        ):
            return existing

    link = InterfaceWindowNavigationContext.model_construct(
        id=link_id,
        interface_window_id=interface_window.id,
        interface_environment=None,
        interface_environment_id=interface_environment_id,
        environment_navigation_context=None,
        environment_navigation_context_id=environment_navigation_context_id,
    )
    interface_window.window_navigation_contexts.append(link)
    return link
    # --- AWARE: LOGIC END attach_navigation_context


async def set_active_navigation_context(
    interface_window: InterfaceWindow, interface_environment_id: UUID, environment_navigation_context_id: UUID
) -> InterfaceWindowNavigationContext:
    """
    Selects the protected EnvironmentNavigationContext this InterfaceWindow
    follows.

    Contract:
    - Mutates only the InterfaceWindow active navigation-context pointer.
    - Does not mutate the EnvironmentNavigationContext target.
    - Thread selection changes happen through
      EnvironmentNavigationContext.select_target.
    """

    # --- AWARE: LOGIC START set_active_navigation_context
    link = await attach_navigation_context(
        interface_window=interface_window,
        interface_environment_id=interface_environment_id,
        environment_navigation_context_id=environment_navigation_context_id,
    )
    interface_window.active_navigation_context = link
    interface_window.active_navigation_context_id = link.id
    return link
    # --- AWARE: LOGIC END set_active_navigation_context


async def create_via_interface(interface_id: UUID, window_id: UUID) -> InterfaceWindow:
    """
    Creates a new InterfaceWindow.
    """

    # --- AWARE: LOGIC START create_via_interface
    interface_window_id = stable_interface_window_id(interface_id=interface_id, window_id=window_id)
    return InterfaceWindow(id=interface_window_id, interface_id=interface_id, window_id=window_id)
    # --- AWARE: LOGIC END create_via_interface
