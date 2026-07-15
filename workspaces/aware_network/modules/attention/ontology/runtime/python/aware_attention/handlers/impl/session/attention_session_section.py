from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Attention Ontology
from aware_attention_ontology.session.attention_focus_transition import AttentionFocusTransition
from aware_attention_ontology.session.attention_session_section import AttentionSessionSection

# Code
from aware_code.types import JsonObject

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_attention_ontology.stable_ids import stable_attention_session_section_id

# --- AWARE: USER_IMPORTS END


async def append_transition(
    attention_session_section: AttentionSessionSection,
    transition_key: str,
    focus_scope_id: UUID,
    focus_id: UUID | None = None,
    observable_id: UUID | None = None,
    object_projection_graph_identity_id: UUID | None = None,
    object_instance_graph_branch_id: UUID | None = None,
    object_instance_graph_commit_id: UUID | None = None,
    previous_transition_id: UUID | None = None,
    sequence: int = 0,
    projection_hash: str | None = None,
    transition_kind: str = "focus",
    rationale: str | None = None,
    source_kind: str | None = None,
    source_ref: str | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> AttentionFocusTransition:
    """
    Append one replayable focus transition under this session section.

    Contract:
    - This is source truth for replay.
    - It is not an all-in-one read snapshot.
    - Consumers may later derive read DTOs from this row plus session
      layout/section state.
    """

    # --- AWARE: LOGIC START append_transition
    transition = await AttentionFocusTransition.create_via_attention_session_section(
        attention_session_section_id=attention_session_section.id,
        transition_key=transition_key,
        focus_scope_id=focus_scope_id,
        focus_id=focus_id,
        observable_id=observable_id,
        object_projection_graph_identity_id=object_projection_graph_identity_id,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
        previous_transition_id=previous_transition_id,
        sequence=sequence,
        projection_hash=projection_hash,
        transition_kind=transition_kind,
        rationale=rationale,
        source_kind=source_kind,
        source_ref=source_ref,
        metadata_json=metadata_json,
    )
    if all(existing.id != transition.id for existing in attention_session_section.transitions):
        attention_session_section.transitions.append(transition)
    attention_session_section.active_transition = transition
    return transition
    # --- AWARE: LOGIC END append_transition


async def set_active_transition(
    attention_session_section: AttentionSessionSection, attention_focus_transition_id: UUID
) -> AttentionFocusTransition:
    """
    Select the active transition for this session-local section.
    """

    # --- AWARE: LOGIC START set_active_transition
    transition = next(
        (
            existing
            for existing in attention_session_section.transitions
            if existing.id == attention_focus_transition_id
        ),
        None,
    )
    if transition is None:
        transition = AttentionFocusTransition.by_id_cached(attention_focus_transition_id)
    if transition is None:
        raise RuntimeError(
            "AttentionSessionSection.set_active_transition requires a known transition: "
            f"attention_focus_transition_id={attention_focus_transition_id}"
        )
    attention_session_section.active_transition = transition
    return transition
    # --- AWARE: LOGIC END set_active_transition


async def create_via_attention_session_layout(
    attention_session_layout_id: UUID,
    layout_section_id: UUID,
    section_id: UUID,
    section_key: str | None = None,
    order: int = 0,
    is_active: bool = True,
) -> AttentionSessionSection:
    """
    Create one session-local section state row.
    """

    # --- AWARE: LOGIC START create_via_attention_session_layout
    return AttentionSessionSection(
        id=stable_attention_session_section_id(
            attention_session_layout_id=attention_session_layout_id,
            layout_section_id=layout_section_id,
            section_id=section_id,
        ),
        attention_session_layout_id=attention_session_layout_id,
        layout_section_id=layout_section_id,
        section_id=section_id,
        section_key=section_key,
        order=order,
        is_active=is_active,
    )
    # --- AWARE: LOGIC END create_via_attention_session_layout
