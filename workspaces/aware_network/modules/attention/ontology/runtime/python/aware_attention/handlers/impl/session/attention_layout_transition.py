from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Attention Ontology
from aware_attention_ontology.session.attention_layout_transition import AttentionLayoutTransition
from aware_attention_ontology.session.attention_layout_transition_section import AttentionLayoutTransitionSection

# Code
from aware_code.types import JsonObject

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_attention_ontology.stable_ids import stable_attention_layout_transition_id

# --- AWARE: USER_IMPORTS END


async def attach_section_state(
    attention_layout_transition: AttentionLayoutTransition,
    attention_session_section_id: UUID,
    order: int,
    weight_micros: int,
    is_visible: bool = True,
    is_collapsed: bool = False,
) -> AttentionLayoutTransitionSection:
    """
    Construct one typed row through its immutable transition parent.

    This constructor is an internal composition primitive. The public
    atomic boundary remains AttentionSessionLayout.apply_layout_transition.
    """

    # --- AWARE: LOGIC START attach_section_state
    section_state = await AttentionLayoutTransitionSection.create_via_attention_layout_transition(
        attention_layout_transition_id=attention_layout_transition.id,
        attention_session_section_id=attention_session_section_id,
        order=order,
        weight_micros=weight_micros,
        is_visible=is_visible,
        is_collapsed=is_collapsed,
    )
    if all(existing.id != section_state.id for existing in attention_layout_transition.section_states):
        attention_layout_transition.section_states.append(section_state)
    return section_state
    # --- AWARE: LOGIC END attach_section_state


async def create_via_attention_session_layout(
    attention_session_layout_id: UUID,
    client_intent_id: str,
    previous_transition_id: UUID | None = None,
    topology_transition_id: UUID | None = None,
    sequence: int = 0,
    transition_kind: str = "layout",
    source_kind: str | None = None,
    source_ref: str | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> AttentionLayoutTransition:
    """
    Create one immutable layout-transition header.

    The owning AttentionSessionLayout plus client_intent_id provide stable
    replay identity. Section-state rows are constructed only after the
    parent handler validates the complete vector.
    """

    # --- AWARE: LOGIC START create_via_attention_session_layout
    return AttentionLayoutTransition(
        id=stable_attention_layout_transition_id(
            attention_session_layout_id=attention_session_layout_id,
            client_intent_id=client_intent_id,
        ),
        attention_session_layout_id=attention_session_layout_id,
        client_intent_id=client_intent_id,
        previous_transition_id=previous_transition_id,
        topology_transition_id=topology_transition_id,
        sequence=sequence,
        transition_kind=transition_kind or "layout",
        source_kind=source_kind,
        source_ref=source_ref,
        metadata_json=metadata_json or JsonObject(),
    )
    # --- AWARE: LOGIC END create_via_attention_session_layout
