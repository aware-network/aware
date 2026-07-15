from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Environment Ontology
from aware_environment_ontology.environment.environment_navigation_context import EnvironmentNavigationContext
from aware_environment_ontology.environment.environment_session import EnvironmentSession
from aware_environment_ontology.environment.environment_session_attention_session import (
    EnvironmentSessionAttentionSession,
)
from aware_environment_ontology.environment.environment_session_thread import EnvironmentSessionThread

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import current_handler_session
from aware_environment_ontology.stable_ids import (
    stable_environment_navigation_context_id,
    stable_environment_session_id,
)

# --- AWARE: USER_IMPORTS END


async def create_navigation_context(
    environment_session: EnvironmentSession,
    key: str,
    session_thread_id: UUID,
    title: str | None = None,
    status: str = "active",
    is_default: bool = False,
) -> EnvironmentNavigationContext:
    """
    Create one shared navigation context under this EnvironmentSession.

    Contract:
    - Stable identity is EnvironmentSession path + `key`.
    - This is a shared tab/window-like OS pointer.
    - Multiple contexts may exist per EnvironmentSession.
    - SessionThread target history is derived from commits over this
      context; no custom navigation-event object exists in v0.
    - Attention focus and Experience lenses remain separate downstream
      rails.
    """

    # --- AWARE: LOGIC START create_navigation_context
    if environment_session.id is None:
        raise RuntimeError("EnvironmentSession.create_navigation_context requires EnvironmentSession.id")

    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError("EnvironmentSession.create_navigation_context requires non-empty key")

    created_id = stable_environment_navigation_context_id(
        environment_session_id=environment_session.id,
        key=normalized_key,
    )
    for existing in environment_session.navigation_contexts:
        if existing.id == created_id:
            return existing

    created = EnvironmentNavigationContext(
        id=created_id,
        environment_session_id=environment_session.id,
        key=normalized_key,
        title=title,
        status=status,
        session_thread_id=session_thread_id,
        is_default=is_default,
    )
    environment_session.navigation_contexts.append(created)
    return created
    # --- AWARE: LOGIC END create_navigation_context


async def attach_attention_session(
    environment_session: EnvironmentSession,
    attention_session_id: UUID,
    key: str | None = None,
    title: str | None = None,
    status: str = "active",
    metadata_json: JsonObject | None = JsonObject(),
) -> EnvironmentSessionAttentionSession:
    """
    Attach one AttentionSession portal to this EnvironmentSession.

    Contract:
    - Stable identity is EnvironmentSession path + AttentionSession.
    - AttentionSession remains Attention-owned source truth.
    - This is a pure Environment session relationship object, not a
      capability object.
    """

    # --- AWARE: LOGIC START attach_attention_session
    if environment_session.id is None:
        raise RuntimeError("EnvironmentSession.attach_attention_session requires EnvironmentSession.id")

    created = await EnvironmentSessionAttentionSession.build_via_environment_session(
        environment_session_id=environment_session.id,
        attention_session_id=attention_session_id,
        key=key,
        title=title,
        status=status,
        metadata_json=metadata_json,
    )
    for existing in environment_session.attention_sessions:
        if existing.id == created.id:
            return existing

    environment_session.attention_sessions.append(created)
    return created
    # --- AWARE: LOGIC END attach_attention_session


async def resolve_thread(
    environment_session: EnvironmentSession,
    thread_id: UUID,
    thread_layout_id: UUID,
    attention_session_id: UUID | None = None,
    key: str | None = None,
    title: str | None = None,
    status: str = "active",
    metadata_json: JsonObject | None = JsonObject(),
) -> EnvironmentSessionThread:
    """
    Resolve one EnvironmentSession-local Thread/Layout row.

    Contract:
    - Stable identity is EnvironmentSession path + Thread + ThreadLayout.
    - NavigationContext points to this row when selected.
    - ThreadLayout is session-scoped here, not Thread-global active state.
    - Optional attention_session_id points at an
      EnvironmentSessionAttentionSession row owned by this session.
    """

    # --- AWARE: LOGIC START resolve_thread
    if environment_session.id is None:
        raise RuntimeError("EnvironmentSession.resolve_thread requires EnvironmentSession.id")

    created = await EnvironmentSessionThread.build_via_environment_session(
        environment_session_id=environment_session.id,
        thread_id=thread_id,
        thread_layout_id=thread_layout_id,
        attention_session_id=attention_session_id,
        key=key,
        title=title,
        status=status,
        metadata_json=metadata_json,
    )
    for existing in environment_session.session_threads:
        if existing.id == created.id:
            return existing

    environment_session.session_threads.append(created)
    return created
    # --- AWARE: LOGIC END resolve_thread


async def build_via_environment(
    environment_id: UUID,
    identity_session_id: UUID,
    session_config_id: UUID | None = None,
    key: str | None = None,
    title: str | None = None,
    description: str | None = None,
    purpose: str | None = None,
    status: str = "active",
    source_kind: str | None = None,
    source_ref: str | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> EnvironmentSession:
    """
    Construct one EnvironmentSession under an Environment.

    Contract:
    - Stable identity is Environment path + Identity Session.
    - `session_config_id` is optional non-key session defaults/provenance.
    - `identity_session_id` resolves the required Identity Session portal
      and must not be inferred from keys.
    - Actor membership, ActorRole evidence, and provider sessions live on
      the linked Identity Session.
    """

    # --- AWARE: LOGIC START build_via_environment
    environment_session_id = stable_environment_session_id(
        environment_id=environment_id,
        identity_session_id=identity_session_id,
    )
    handler_session = current_handler_session()
    existing = handler_session.imap_get(EnvironmentSession, environment_session_id)
    if existing is not None:
        if existing.environment_id != environment_id or existing.identity_session_id != identity_session_id:
            raise RuntimeError(
                "EnvironmentSession.build_via_environment mismatch "
                f"for existing session: environment_session_id={environment_session_id}"
            )
        return existing

    return EnvironmentSession(
        id=environment_session_id,
        environment_id=environment_id,
        session_config_id=session_config_id,
        identity_session_id=identity_session_id,
        key=key,
        title=title,
        description=description,
        purpose=purpose,
        status=status,
        source_kind=source_kind,
        source_ref=source_ref,
        metadata_json=metadata_json,
    )
    # --- AWARE: LOGIC END build_via_environment
