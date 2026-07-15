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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_experience_ontology.provider.experience_provider_action_binding import ExperienceProviderActionBinding


class ExperienceProvider(ORMModel):
    """
    Experience-owned provider slot.
    Contract:
    - Experience declares which provider slots can fulfill its public actions.
    - Provider ontologies bind concrete fulfillment to this slot later.
    - This object intentionally does not reference provider-owned implementation classes.
    """

    # Relationships
    action_bindings: list[ExperienceProviderActionBinding] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)
    provider_key: str
    provider_kind: str = Field(default="provider")
    selection_policy: str = Field(default="contract_required")
    status: str = Field(default="active")
    title: str | None = Field(default=None)

    # Foreign Keys
    projection_experience_id: UUID = Field(description="Foreign key for ProjectionExperience.providers")

    async def bind_action(
        self,
        binding_key: str,
        experience_invocation_action_config_id: UUID,
        provider_action_ref: str | None = None,
        required_contract_scope: str = "operation",
        selection_policy: str = "contract_required",
        status: str = "active",
        description: str | None = None,
    ) -> ExperienceProviderActionBinding:
        """
        Bind one Experience action config to this provider slot.

        Contract:
        - Experience owns the public provider/action contract.
        - Provider-owned fulfillment binds concrete operations to this binding later.
        """

        payload = {
            "binding_key": binding_key,
            "experience_invocation_action_config_id": experience_invocation_action_config_id,
            "provider_action_ref": provider_action_ref,
            "required_contract_scope": required_contract_scope,
            "selection_policy": selection_policy,
            "status": status,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="bind_action", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.provider.experience_provider_action_binding import (
            ExperienceProviderActionBinding,
        )

        if isinstance(value, ExperienceProviderActionBinding):
            return value
        return ExperienceProviderActionBinding.validate_invocation_value(value)

    @classmethod
    async def build_via_projection_experience(
        cls,
        projection_experience_id: UUID,
        provider_key: str,
        provider_kind: str = "provider",
        selection_policy: str = "contract_required",
        status: str = "active",
        title: str | None = None,
        description: str | None = None,
        metadata_json: JsonObject | None = {},
    ) -> ExperienceProvider:
        """
        Create one public provider slot under a ProjectionExperience.

        Contract:
        - Parent ProjectionExperience scope is propagated by constructor lowering.
        - Stable identity is `(projection_experience_id, provider_key)`.
        - The provider slot is Experience-owned public contract, not a concrete
          implementation object.
        """

        payload = {
            "projection_experience_id": projection_experience_id,
            "provider_key": provider_key,
            "provider_kind": provider_kind,
            "selection_policy": selection_policy,
            "status": status,
            "title": title,
            "description": description,
            "metadata_json": metadata_json,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_projection_experience", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ExperienceProvider):
            return value
        return ExperienceProvider.validate_invocation_value(value)


class ExperienceProviderBindActionInput(BaseModel):
    binding_key: str
    experience_invocation_action_config_id: UUID
    provider_action_ref: str | None = Field(default=None)
    required_contract_scope: str = Field(default="operation")
    selection_policy: str = Field(default="contract_required")
    status: str = Field(default="active")
    description: str | None = Field(default=None)


class ExperienceProviderBindActionOutput(BaseModel):
    value: ExperienceProviderActionBinding


class ExperienceProviderBuildViaProjectionExperienceInput(BaseModel):
    projection_experience_id: UUID = Field(description="Foreign key for ProjectionExperience.providers")
    provider_key: str
    provider_kind: str = Field(default="provider")
    selection_policy: str = Field(default="contract_required")
    status: str = Field(default="active")
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class ExperienceProviderBuildViaProjectionExperienceOutput(BaseModel):
    value: ExperienceProvider


FUNCTIONS = {
    "ExperienceProvider": {
        "bind_action": {
            "canonical": {
                "name": "bind_action",
                "description": "Bind one Experience action config to this provider slot.\n\nContract:\n- Experience owns the public provider/action contract.\n- Provider-owned fulfillment binds concrete operations to this binding later.",
                "is_constructor": False,
            },
            "input": ExperienceProviderBindActionInput,
            "output": ExperienceProviderBindActionOutput,
        },
        "build_via_projection_experience": {
            "canonical": {
                "name": "build_via_projection_experience",
                "description": "Create one public provider slot under a ProjectionExperience.\n\nContract:\n- Parent ProjectionExperience scope is propagated by constructor lowering.\n- Stable identity is `(projection_experience_id, provider_key)`.\n- The provider slot is Experience-owned public contract, not a concrete\n  implementation object.",
                "is_constructor": True,
            },
            "input": ExperienceProviderBuildViaProjectionExperienceInput,
            "output": ExperienceProviderBuildViaProjectionExperienceOutput,
        },
    },
}

__all__ = [
    "ExperienceProvider",
    "ExperienceProviderBindActionInput",
    "ExperienceProviderBindActionOutput",
    "ExperienceProviderBuildViaProjectionExperienceInput",
    "ExperienceProviderBuildViaProjectionExperienceOutput",
    "FUNCTIONS",
]
