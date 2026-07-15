from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Attention Ontology
from aware_attention_ontology.session.attention_layout_topology_transition_section import (
    AttentionLayoutTopologyTransitionSection,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_attention_ontology.stable_ids import (
    stable_attention_layout_topology_transition_section_id,
)

# --- AWARE: USER_IMPORTS END


async def create_via_attention_layout_topology_transition(
    attention_layout_topology_transition_id: UUID, attention_session_section_id: UUID, order: int
) -> AttentionLayoutTopologyTransitionSection:
    """
    Create one typed row in an already-validated full topology vector.
    """

    # --- AWARE: LOGIC START create_via_attention_layout_topology_transition
    return AttentionLayoutTopologyTransitionSection(
        id=stable_attention_layout_topology_transition_section_id(
            attention_layout_topology_transition_id=(attention_layout_topology_transition_id),
            attention_session_section_id=attention_session_section_id,
        ),
        attention_layout_topology_transition_id=(attention_layout_topology_transition_id),
        attention_session_section_id=attention_session_section_id,
        order=order,
    )
    # --- AWARE: LOGIC END create_via_attention_layout_topology_transition
