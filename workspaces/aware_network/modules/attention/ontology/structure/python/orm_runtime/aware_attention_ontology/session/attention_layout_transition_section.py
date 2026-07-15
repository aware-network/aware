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


class AttentionLayoutTransitionSection(ORMModel):
    """
    Typed geometry state for one mounted section in one layout transition.
    Contract:
    - Parent constructor is AttentionLayoutTransition.
    - weight_micros is shared integer truth; active weights normalize exactly
    to 1_000_000 across the complete transition vector.
    - Hidden or collapsed sections have zero weight.
    """

    # Relationships
    attention_session_section: AttentionSessionSection | None = Field(default=None)

    # Attributes
    order: int
    weight_micros: int
    is_visible: bool = Field(default=True)
    is_collapsed: bool = Field(default=False)

    # Foreign Keys
    attention_layout_transition_id: UUID = Field(description="Foreign key for AttentionLayoutTransition.section_states")
    attention_session_section_id: UUID | None = Field(
        default=None, description="Foreign key for AttentionLayoutTransitionSection.attention_session_section"
    )

    @classmethod
    async def create_via_attention_layout_transition(
        cls,
        attention_layout_transition_id: UUID,
        attention_session_section_id: UUID,
        order: int,
        weight_micros: int,
        is_visible: bool = True,
        is_collapsed: bool = False,
    ) -> AttentionLayoutTransitionSection:
        """Create one typed row in an already-validated full layout vector."""

        payload = {
            "attention_layout_transition_id": attention_layout_transition_id,
            "attention_session_section_id": attention_session_section_id,
            "order": order,
            "weight_micros": weight_micros,
            "is_visible": is_visible,
            "is_collapsed": is_collapsed,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_attention_layout_transition", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, AttentionLayoutTransitionSection):
            return value
        return AttentionLayoutTransitionSection.validate_invocation_value(value)


class AttentionLayoutTransitionSectionCreateViaAttentionLayoutTransitionInput(BaseModel):
    attention_layout_transition_id: UUID = Field(description="Foreign key for AttentionLayoutTransition.section_states")
    attention_session_section_id: UUID
    order: int
    weight_micros: int
    is_visible: bool = Field(default=True)
    is_collapsed: bool = Field(default=False)


class AttentionLayoutTransitionSectionCreateViaAttentionLayoutTransitionOutput(BaseModel):
    value: AttentionLayoutTransitionSection


FUNCTIONS = {
    "AttentionLayoutTransitionSection": {
        "create_via_attention_layout_transition": {
            "canonical": {
                "name": "create_via_attention_layout_transition",
                "description": "Create one typed row in an already-validated full layout vector.",
                "is_constructor": True,
            },
            "input": AttentionLayoutTransitionSectionCreateViaAttentionLayoutTransitionInput,
            "output": AttentionLayoutTransitionSectionCreateViaAttentionLayoutTransitionOutput,
        },
    },
}

__all__ = [
    "AttentionLayoutTransitionSection",
    "AttentionLayoutTransitionSectionCreateViaAttentionLayoutTransitionInput",
    "AttentionLayoutTransitionSectionCreateViaAttentionLayoutTransitionOutput",
    "FUNCTIONS",
]
