from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.interface.interface_enums import (
    InterfaceOs,
    InterfaceSessionState,
)
from aware_interface_ontology.interface.interface import Interface
from aware_interface_ontology.interface.interface_environment import InterfaceEnvironment
from aware_interface_ontology.interface.interface_session import InterfaceSession
from aware_interface_ontology.interface.interface_window import InterfaceWindow
from aware_interface_ontology.interface.interface_window_navigation_context import InterfaceWindowNavigationContext

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Standard
from aware_interface.stable_ids import stable_interface_environment_id, stable_interface_id, stable_interface_window_id
from aware_interface.handlers.impl.interface.interface_window import (
    set_active_navigation_context as set_interface_window_active_navigation_context,
)
from aware_meta.runtime.handler_context import current_handler_context

# --- AWARE: USER_IMPORTS END


async def attach_window(interface: Interface, window_id: UUID) -> InterfaceWindow:
    """
    Creates (or ensures) an InterfaceWindow link for an existing Window.

    Canonical v0:
    - Window instances live in the `window` projection lane (separate receipt).
    - This function commits only the link object (`InterfaceWindow`) in the `interface` lane.
    - InterfaceWindow id is derived deterministically from (interface_id, window_id).
    - Idempotent: safe to call multiple times for the same `window_id`.

    Projection boundary:
    - `InterfaceWindow::window` is a portal to the `window` projection.
    - The caller must create/ensure the target `window.Window` separately (e.g. via
    `window.Window.build(window_id)`).
    """

    # --- AWARE: LOGIC START attach_window
    if interface.id is None:
        raise RuntimeError("Interface.attach_window requires Interface.id")
    if not isinstance(window_id, UUID):
        raise TypeError("Interface.attach_window requires window_id (UUID)")

    interface_id = interface.id
    link_id = stable_interface_window_id(interface_id=interface_id, window_id=window_id)

    # Idempotent: return the existing link if already present.
    for existing in interface.interface_windows:
        if existing.id == link_id or existing.window_id == window_id:
            return existing

    link = InterfaceWindow.model_construct(
        id=link_id,
        interface_id=interface_id,
        window=None,
        window_id=window_id,
        window_navigation_contexts=[],
        active_navigation_context=None,
        active_navigation_context_id=None,
    )
    interface.interface_windows.append(link)
    return link
    # --- AWARE: LOGIC END attach_window


async def attach_environment(interface: Interface, environment_id: UUID) -> InterfaceEnvironment:
    """
    Creates (or ensures) an InterfaceEnvironment access association.

    Contract:
    - Interface owns the Environment access contract.
    - Window thread targets must reference this association instead of granting Environment access
      from raw Window state.
    - Idempotent: safe to call multiple times for the same `environment_id`.
    """

    # --- AWARE: LOGIC START attach_environment
    if interface.id is None:
        raise RuntimeError("Interface.attach_environment requires Interface.id")
    if not isinstance(environment_id, UUID):
        raise TypeError("Interface.attach_environment requires environment_id (UUID)")

    interface_environment_id = stable_interface_environment_id(
        interface_id=interface.id,
        environment_id=environment_id,
    )
    for existing in interface.environments:
        if existing.id == interface_environment_id or existing.environment_id == environment_id:
            return existing

    link = InterfaceEnvironment.model_construct(
        id=interface_environment_id,
        interface_id=interface.id,
        environment=None,
        environment_id=environment_id,
    )
    interface.environments.append(link)
    return link
    # --- AWARE: LOGIC END attach_environment


async def start_session(
    interface: Interface,
    identity_session_id: UUID,
    name: str,
    state: InterfaceSessionState = InterfaceSessionState.active,
) -> InterfaceSession:
    """
    Start or attach one commit-backed InterfaceSession.

    Contract:
    - `identity_session_id` is canonical Identity participation evidence.
    - Identity Session membership admits every participant; the shared
      InterfaceSession is not owned by one InterfaceIdentity.
    - The commit records durable client/session provenance before any
      transport binding is registered.
    - Network connection and bearer-token lifecycle remain ephemeral
      transport concerns.
    """

    # --- AWARE: LOGIC START start_session
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END start_session


async def set_active_window_navigation_context(
    interface: Interface, window_id: UUID, environment_id: UUID, environment_navigation_context_id: UUID
) -> InterfaceWindowNavigationContext:
    """
    Ensures Interface Environment access, ensures the InterfaceWindow link,
    and selects the protected EnvironmentNavigationContext target for that
    window inside the Interface commit.

    Contract:
    - Interface follows navigation-context truth, not raw Thread truth.
    - Process/Thread selection is mutated through the Environment
      NavigationContext API/service rail.
    """

    # --- AWARE: LOGIC START set_active_window_navigation_context
    environment_link = await attach_environment(interface=interface, environment_id=environment_id)
    window_link = await attach_window(interface=interface, window_id=window_id)
    if environment_link.id is None:
        raise RuntimeError("Interface.set_active_window_navigation_context requires InterfaceEnvironment.id")
    return await set_interface_window_active_navigation_context(
        interface_window=window_link,
        interface_environment_id=environment_link.id,
        environment_navigation_context_id=environment_navigation_context_id,
    )
    # --- AWARE: LOGIC END set_active_window_navigation_context


async def build_via_interface_config(interface_config_id: UUID, os: InterfaceOs, version: str) -> Interface:
    """
    Create one Interface runtime instance under InterfaceConfig.
    """

    # --- AWARE: LOGIC START build_via_interface_config
    stable_os = os.value if hasattr(os, "value") else str(os)
    branch_bound_interface_id: UUID | None = None
    try:
        handler_ctx = current_handler_context()
    except RuntimeError:
        handler_ctx = None
    if handler_ctx is not None and handler_ctx.branch_id != interface_config_id:
        branch_bound_interface_id = handler_ctx.branch_id

    interface_id = branch_bound_interface_id or stable_interface_id(
        interface_config_id=interface_config_id,
        os=stable_os,
        version=version,
    )
    return Interface(
        id=interface_id,
        interface_config_id=interface_config_id,
        os=os,
        version=version,
    )
    # --- AWARE: LOGIC END build_via_interface_config
