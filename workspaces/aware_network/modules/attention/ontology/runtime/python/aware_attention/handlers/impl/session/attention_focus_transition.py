from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Attention Ontology
from aware_attention_ontology.session.attention_focus_transition import AttentionFocusTransition

# Code
from aware_code.types import JsonObject

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_attention_ontology.stable_ids import stable_attention_focus_transition_id

# --- AWARE: USER_IMPORTS END


async def create_via_attention_session_section(
    attention_session_section_id: UUID,
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
    Create one focus transition under an AttentionSessionSection.

    Contract:
    - Parent section scope and transition key provide stable replay identity.
    - FocusScope is required because every transition must resolve the
      session-local focus scope.
    - Other focus/observable/graph links are optional to allow partial
      transitions such as section activation before graph commit evidence is
      available.
    """

    # --- AWARE: LOGIC START create_via_attention_session_section
    return AttentionFocusTransition(
        id=stable_attention_focus_transition_id(
            attention_session_section_id=attention_session_section_id,
            focus_scope_id=focus_scope_id,
            transition_key=transition_key,
        ),
        attention_session_section_id=attention_session_section_id,
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
        transition_kind=transition_kind or "focus",
        rationale=rationale,
        source_kind=source_kind,
        source_ref=source_ref,
        metadata_json=metadata_json or JsonObject(),
    )
    # --- AWARE: LOGIC END create_via_attention_session_section
