from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Attention Ontology
from aware_attention_ontology.session.attention_layout_transition_section import AttentionLayoutTransitionSection

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_attention_ontology.stable_ids import (
    stable_attention_layout_transition_section_id,
)

# --- AWARE: USER_IMPORTS END


async def create_via_attention_layout_transition(
    attention_layout_transition_id: UUID,
    attention_session_section_id: UUID,
    order: int,
    weight_micros: int,
    is_visible: bool = True,
    is_collapsed: bool = False,
) -> AttentionLayoutTransitionSection:
    """
    Create one typed row in an already-validated full layout vector.
    """

    # --- AWARE: LOGIC START create_via_attention_layout_transition
    return AttentionLayoutTransitionSection(
        id=stable_attention_layout_transition_section_id(
            attention_layout_transition_id=attention_layout_transition_id,
            attention_session_section_id=attention_session_section_id,
        ),
        attention_layout_transition_id=attention_layout_transition_id,
        attention_session_section_id=attention_session_section_id,
        order=order,
        weight_micros=weight_micros,
        is_visible=is_visible,
        is_collapsed=is_collapsed,
    )
    # --- AWARE: LOGIC END create_via_attention_layout_transition
