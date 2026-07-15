from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Environment Ontology
from aware_environment_ontology.environment.environment_navigation_context import EnvironmentNavigationContext

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import current_handler_session
from aware_environment_ontology.stable_ids import (
    stable_environment_navigation_context_id,
)

# --- AWARE: USER_IMPORTS END


async def select_target(
    environment_navigation_context: EnvironmentNavigationContext, session_thread_id: UUID
) -> EnvironmentNavigationContext:
    """
    Select the current session-thread target for this navigation context.

    Contract:
    - Mutates only the invoked EnvironmentNavigationContext.
    - Updates only the EnvironmentSessionThread relationship FK.
    - Does not mutate EnvironmentSession or create a session singleton
      cursor.
    - History is the commit trail over this context.
    """

    # --- AWARE: LOGIC START select_target
    environment_navigation_context.session_thread_id = session_thread_id
    environment_navigation_context.session_thread = None
    return environment_navigation_context
    # --- AWARE: LOGIC END select_target


async def build_via_environment_session(
    environment_session_id: UUID,
    key: str,
    session_thread_id: UUID,
    title: str | None = None,
    status: str = "active",
    is_default: bool = False,
) -> EnvironmentNavigationContext:
    """
    Construct one EnvironmentNavigationContext under an EnvironmentSession.

    Contract:
    - Stable identity is EnvironmentSession path + `key`.
    - `session_thread_id` binds the EnvironmentSessionThread target pin.
    - No parent id is authored here; parent context is propagated by
      containment path.
    """

    # --- AWARE: LOGIC START build_via_environment_session
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError("EnvironmentNavigationContext.build_via_environment_session requires non-empty key")

    navigation_context_id = stable_environment_navigation_context_id(
        environment_session_id=environment_session_id,
        key=normalized_key,
    )
    handler_session = current_handler_session()
    existing = handler_session.imap_get(EnvironmentNavigationContext, navigation_context_id)
    if existing is not None:
        existing_key = (existing.key or "").strip()
        if existing.environment_session_id != environment_session_id or existing_key != normalized_key:
            raise RuntimeError(
                "EnvironmentNavigationContext.build_via_environment_session mismatch "
                f"for existing context: environment_navigation_context_id={navigation_context_id}"
            )
        return existing

    return EnvironmentNavigationContext(
        id=navigation_context_id,
        environment_session_id=environment_session_id,
        session_thread_id=session_thread_id,
        key=normalized_key,
        title=title,
        status=status,
        is_default=is_default,
    )
    # --- AWARE: LOGIC END build_via_environment_session
