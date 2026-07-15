from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.invocation.experience_invocation_action_config import (
        ExperienceInvocationActionConfig,
    )


class ExperienceProviderActionBinding(ORMModel):
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

    # Foreign Keys
    experience_provider_id: UUID = Field(description="Foreign key for ExperienceProvider.action_bindings")
    experience_invocation_action_config_id: UUID | None = Field(
        default=None, description="Foreign key for ExperienceProviderActionBinding.experience_invocation_action_config"
    )
