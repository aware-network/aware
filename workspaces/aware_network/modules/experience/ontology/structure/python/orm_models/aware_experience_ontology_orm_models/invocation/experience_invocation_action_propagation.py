from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.invocation.experience_invocation_action import ExperienceInvocationAction


class ExperienceInvocationActionPropagation(ORMModel):
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

    # Foreign Keys
    experience_invocation_action_id: UUID = Field(description="Foreign key for ExperienceInvocationAction.propagations")
    target_invocation_action_id: UUID = Field(
        description="Foreign key for ExperienceInvocationActionPropagation.target_invocation_action"
    )
