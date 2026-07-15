from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.invocation.experience_invocation_action import ExperienceInvocationAction


class ExperienceInvocationActionPropagation(BaseModel):
    """
    Causal propagation edge between two Experience invocation actions.
    Contract:
    - Actions can invoke or delegate to other actions without collapsing their
    receipts.
    - Each action owns its own API/SDK/service call, actor, commit, and event
    provenance.
    """

    # Relationships
    target_invocation_action: ExperienceInvocationAction | None = Field(default=None)

    # Attributes
    propagation_kind: str = Field(default="invokes")
    description: str | None = Field(default=None)
