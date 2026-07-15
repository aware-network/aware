from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Attention Ontology
from aware_attention_ontology.session.attention_session import AttentionSession
from aware_attention_ontology.session.attention_session_layout import AttentionSessionLayout

# Code
from aware_code.types import JsonObject

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_attention_ontology.stable_ids import stable_attention_session_id

# --- AWARE: USER_IMPORTS END


async def build(
    identity_session_id: UUID,
    key: str | None = None,
    title: str | None = None,
    description: str | None = None,
    purpose: str | None = None,
    status: str = "active",
    source_kind: str | None = None,
    source_ref: str | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> AttentionSession:
    """
    Construct one AttentionSession over an Identity Session.

    Contract:
    - Stable identity is the linked Identity Session.
    - Identity owns actor membership/role/provider participation.
    - Attention owns layout/section/focus transition state only.
    """

    # --- AWARE: LOGIC START build
    return AttentionSession(
        id=stable_attention_session_id(identity_session_id=identity_session_id),
        identity_session_id=identity_session_id,
        key=key,
        title=title,
        description=description,
        purpose=purpose,
        status=status or "active",
        source_kind=source_kind,
        source_ref=source_ref,
        metadata_json=metadata_json or JsonObject(),
    )
    # --- AWARE: LOGIC END build


async def mount_layout(
    attention_session: AttentionSession,
    layout_id: UUID,
    layout_config_id: UUID | None = None,
    key: str | None = None,
    order: int = 0,
    is_active: bool = True,
) -> AttentionSessionLayout:
    """
    Mount one Attention Layout into this AttentionSession.

    Contract:
    - Parent AttentionSession scope is injected by propagation.
    - Layout topology remains Attention-owned.
    - This is session-local layout state.
    """

    # --- AWARE: LOGIC START mount_layout
    session_layout = await AttentionSessionLayout.create_via_attention_session(
        attention_session_id=attention_session.id,
        layout_id=layout_id,
        layout_config_id=layout_config_id,
        key=key,
        order=order,
        is_active=is_active,
    )
    if all(existing.id != session_layout.id for existing in attention_session.layouts):
        attention_session.layouts.append(session_layout)
    if is_active:
        attention_session.active_layout = session_layout
    return session_layout
    # --- AWARE: LOGIC END mount_layout


async def set_active_layout(
    attention_session: AttentionSession, attention_session_layout_id: UUID
) -> AttentionSessionLayout:
    """
    Select the active session-local layout.
    """

    # --- AWARE: LOGIC START set_active_layout
    session_layout = next(
        (existing for existing in attention_session.layouts if existing.id == attention_session_layout_id),
        None,
    )
    if session_layout is None:
        session_layout = AttentionSessionLayout.by_id_cached(attention_session_layout_id)
    if session_layout is None:
        raise RuntimeError(
            "AttentionSession.set_active_layout requires a known session layout: "
            f"attention_session_layout_id={attention_session_layout_id}"
        )
    attention_session.active_layout = session_layout
    return session_layout
    # --- AWARE: LOGIC END set_active_layout
