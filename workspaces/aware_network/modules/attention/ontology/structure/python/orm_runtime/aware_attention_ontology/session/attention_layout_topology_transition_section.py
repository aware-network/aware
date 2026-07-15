from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_attention_ontology.session.attention_session_section import AttentionSessionSection


class AttentionLayoutTopologyTransitionSection(ORMModel):
    """
    Ordered active membership for one admitted section in one topology revision.
    Contract:
    - Parent constructor is AttentionLayoutTopologyTransition.
    - The section anchor is stable and remains under AttentionSessionLayout even
    when omitted from a later topology revision.
    """

    # Relationships
    attention_session_section: AttentionSessionSection | None = Field(default=None)

    # Attributes
    order: int

    # Foreign Keys
    attention_layout_topology_transition_id: UUID = Field(
        description="Foreign key for AttentionLayoutTopologyTransition.section_states"
    )
    attention_session_section_id: UUID = Field(
        description="Foreign key for AttentionLayoutTopologyTransitionSection.attention_session_section"
    )

    @classmethod
    async def create_via_attention_layout_topology_transition(
        cls, attention_layout_topology_transition_id: UUID, attention_session_section_id: UUID, order: int
    ) -> AttentionLayoutTopologyTransitionSection:
        """Create one typed row in an already-validated full topology vector."""

        payload = {
            "attention_layout_topology_transition_id": attention_layout_topology_transition_id,
            "attention_session_section_id": attention_session_section_id,
            "order": order,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_attention_layout_topology_transition", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, AttentionLayoutTopologyTransitionSection):
            return value
        return AttentionLayoutTopologyTransitionSection.validate_invocation_value(value)


class AttentionLayoutTopologyTransitionSectionCreateViaAttentionLayoutTopologyTransitionInput(BaseModel):
    attention_layout_topology_transition_id: UUID = Field(
        description="Foreign key for AttentionLayoutTopologyTransition.section_states"
    )
    attention_session_section_id: UUID
    order: int


class AttentionLayoutTopologyTransitionSectionCreateViaAttentionLayoutTopologyTransitionOutput(BaseModel):
    value: AttentionLayoutTopologyTransitionSection


FUNCTIONS = {
    "AttentionLayoutTopologyTransitionSection": {
        "create_via_attention_layout_topology_transition": {
            "canonical": {
                "name": "create_via_attention_layout_topology_transition",
                "description": "Create one typed row in an already-validated full topology vector.",
                "is_constructor": True,
            },
            "input": AttentionLayoutTopologyTransitionSectionCreateViaAttentionLayoutTopologyTransitionInput,
            "output": AttentionLayoutTopologyTransitionSectionCreateViaAttentionLayoutTopologyTransitionOutput,
        },
    },
}

__all__ = [
    "AttentionLayoutTopologyTransitionSection",
    "AttentionLayoutTopologyTransitionSectionCreateViaAttentionLayoutTopologyTransitionInput",
    "AttentionLayoutTopologyTransitionSectionCreateViaAttentionLayoutTopologyTransitionOutput",
    "FUNCTIONS",
]
