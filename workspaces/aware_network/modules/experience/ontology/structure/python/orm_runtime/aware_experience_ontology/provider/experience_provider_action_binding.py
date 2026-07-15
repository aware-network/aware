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
    from aware_experience_ontology.invocation.experience_invocation_action_config import (
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

    @classmethod
    async def build_via_experience_provider(
        cls,
        experience_provider_id: UUID,
        binding_key: str,
        experience_invocation_action_config_id: UUID,
        provider_action_ref: str | None = None,
        required_contract_scope: str = "operation",
        selection_policy: str = "contract_required",
        status: str = "active",
        description: str | None = None,
    ) -> ExperienceProviderActionBinding:
        """
        Create one provider action binding under an ExperienceProvider.

        Contract:
        - Parent ExperienceProvider scope is propagated by constructor lowering.
        - Stable identity is `(experience_provider_id, binding_key)`.
        - The bound action stays Experience-owned; provider-owned operations bind
          to this object in the fulfillment migration.
        """

        payload = {
            "experience_provider_id": experience_provider_id,
            "binding_key": binding_key,
            "experience_invocation_action_config_id": experience_invocation_action_config_id,
            "provider_action_ref": provider_action_ref,
            "required_contract_scope": required_contract_scope,
            "selection_policy": selection_policy,
            "status": status,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_experience_provider", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ExperienceProviderActionBinding):
            return value
        return ExperienceProviderActionBinding.validate_invocation_value(value)


class ExperienceProviderActionBindingBuildViaExperienceProviderInput(BaseModel):
    experience_provider_id: UUID = Field(description="Foreign key for ExperienceProvider.action_bindings")
    binding_key: str
    experience_invocation_action_config_id: UUID
    provider_action_ref: str | None = Field(default=None)
    required_contract_scope: str = Field(default="operation")
    selection_policy: str = Field(default="contract_required")
    status: str = Field(default="active")
    description: str | None = Field(default=None)


class ExperienceProviderActionBindingBuildViaExperienceProviderOutput(BaseModel):
    value: ExperienceProviderActionBinding


FUNCTIONS = {
    "ExperienceProviderActionBinding": {
        "build_via_experience_provider": {
            "canonical": {
                "name": "build_via_experience_provider",
                "description": "Create one provider action binding under an ExperienceProvider.\n\nContract:\n- Parent ExperienceProvider scope is propagated by constructor lowering.\n- Stable identity is `(experience_provider_id, binding_key)`.\n- The bound action stays Experience-owned; provider-owned operations bind\n  to this object in the fulfillment migration.",
                "is_constructor": True,
            },
            "input": ExperienceProviderActionBindingBuildViaExperienceProviderInput,
            "output": ExperienceProviderActionBindingBuildViaExperienceProviderOutput,
        },
    },
}

__all__ = [
    "ExperienceProviderActionBinding",
    "ExperienceProviderActionBindingBuildViaExperienceProviderInput",
    "ExperienceProviderActionBindingBuildViaExperienceProviderOutput",
    "FUNCTIONS",
]
