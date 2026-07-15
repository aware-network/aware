from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.invocation.experience_invocation_action_config import (
        ExperienceInvocationActionConfig,
    )


class ExperienceProviderActionBinding(BaseModel):
    """
    Experience-owned provider action binding.
    Contract:
    - This is the public Experience action slot a provider may fulfill later.
    - Experience binds to ExperienceInvocationActionConfig only.
    - Concrete provider operation and contract fulfillment is declared by the
    provider ontology, not here.
    """

    # Relationships
    experience_invocation_action_config: ExperienceInvocationActionConfig

    # Attributes
    binding_key: str
    description: str | None = Field(default=None)
    provider_action_ref: str | None = Field(default=None)
    required_contract_scope: str = Field(default="operation")
    selection_policy: str = Field(default="contract_required")
    status: str = Field(default="active")
