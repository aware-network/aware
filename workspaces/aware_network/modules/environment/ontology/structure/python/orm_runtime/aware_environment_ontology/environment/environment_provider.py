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
    from aware_environment_ontology.environment.environment_provider_grant import EnvironmentProviderGrant


class EnvironmentProvider(ORMModel):
    """
    Provider-neutral Environment slot.
    Contract:
    - Environment declares approved provider slots without importing Experience.
    - Experiences bind to these slots in the Experience-owned provider rail.
    - Concrete service fulfillment remains outside Environment ontology.
    """

    # Relationships
    grants: list[EnvironmentProviderGrant] = Field(default_factory=list)

    # Attributes
    contract_ref: str | None = Field(default=None)
    description: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)
    provider_key: str
    provider_kind: str = Field(default="provider")
    selection_policy: str = Field(default="contract_required")
    status: str = Field(default="active")
    title: str | None = Field(default=None)

    # Foreign Keys
    environment_profile_config_id: UUID = Field(description="Foreign key for EnvironmentProfileConfig.providers")

    async def grant_scope(
        self,
        grant_key: str,
        scope_kind: str = "profile",
        process_config_id: UUID | None = None,
        thread_config_id: UUID | None = None,
        object_projection_graph_id: UUID | None = None,
        action_scope: str | None = None,
        status: str = "active",
        description: str | None = None,
        metadata_json: JsonObject | None = {},
    ) -> EnvironmentProviderGrant:
        """
        Grant this provider slot a scoped Environment capability.

        Contract:
        - Grants are provider-neutral and Experience-free.
        - Experience resolves these grants before issuing graph gateway context.
        """

        payload = {
            "grant_key": grant_key,
            "scope_kind": scope_kind,
            "process_config_id": process_config_id,
            "thread_config_id": thread_config_id,
            "object_projection_graph_id": object_projection_graph_id,
            "action_scope": action_scope,
            "status": status,
            "description": description,
            "metadata_json": metadata_json,
        }
        result = await invoke_instance(orm_model=self, function_name="grant_scope", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_environment_ontology.environment.environment_provider_grant import EnvironmentProviderGrant

        if isinstance(value, EnvironmentProviderGrant):
            return value
        return EnvironmentProviderGrant.validate_invocation_value(value)

    @classmethod
    async def build_via_environment_profile_config(
        cls,
        environment_profile_config_id: UUID,
        provider_key: str,
        provider_kind: str = "provider",
        contract_ref: str | None = None,
        selection_policy: str = "contract_required",
        status: str = "active",
        title: str | None = None,
        description: str | None = None,
        metadata_json: JsonObject | None = {},
    ) -> EnvironmentProvider:
        """
        Create one provider-neutral slot under an EnvironmentProfileConfig.

        Contract:
        - Parent EnvironmentProfileConfig scope is propagated by constructor lowering.
        - Stable identity is `(environment_profile_config_id, provider_key)`.
        """

        payload = {
            "environment_profile_config_id": environment_profile_config_id,
            "provider_key": provider_key,
            "provider_kind": provider_kind,
            "contract_ref": contract_ref,
            "selection_policy": selection_policy,
            "status": status,
            "title": title,
            "description": description,
            "metadata_json": metadata_json,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_environment_profile_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentProvider):
            return value
        return EnvironmentProvider.validate_invocation_value(value)


class EnvironmentProviderGrantScopeInput(BaseModel):
    grant_key: str
    scope_kind: str = Field(default="profile")
    process_config_id: UUID | None = Field(default=None)
    thread_config_id: UUID | None = Field(default=None)
    object_projection_graph_id: UUID | None = Field(default=None)
    action_scope: str | None = Field(default=None)
    status: str = Field(default="active")
    description: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class EnvironmentProviderGrantScopeOutput(BaseModel):
    value: EnvironmentProviderGrant


class EnvironmentProviderBuildViaEnvironmentProfileConfigInput(BaseModel):
    environment_profile_config_id: UUID = Field(description="Foreign key for EnvironmentProfileConfig.providers")
    provider_key: str
    provider_kind: str = Field(default="provider")
    contract_ref: str | None = Field(default=None)
    selection_policy: str = Field(default="contract_required")
    status: str = Field(default="active")
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class EnvironmentProviderBuildViaEnvironmentProfileConfigOutput(BaseModel):
    value: EnvironmentProvider


FUNCTIONS = {
    "EnvironmentProvider": {
        "grant_scope": {
            "canonical": {
                "name": "grant_scope",
                "description": "Grant this provider slot a scoped Environment capability.\n\nContract:\n- Grants are provider-neutral and Experience-free.\n- Experience resolves these grants before issuing graph gateway context.",
                "is_constructor": False,
            },
            "input": EnvironmentProviderGrantScopeInput,
            "output": EnvironmentProviderGrantScopeOutput,
        },
        "build_via_environment_profile_config": {
            "canonical": {
                "name": "build_via_environment_profile_config",
                "description": "Create one provider-neutral slot under an EnvironmentProfileConfig.\n\nContract:\n- Parent EnvironmentProfileConfig scope is propagated by constructor lowering.\n- Stable identity is `(environment_profile_config_id, provider_key)`.",
                "is_constructor": True,
            },
            "input": EnvironmentProviderBuildViaEnvironmentProfileConfigInput,
            "output": EnvironmentProviderBuildViaEnvironmentProfileConfigOutput,
        },
    },
}

__all__ = [
    "EnvironmentProvider",
    "EnvironmentProviderGrantScopeInput",
    "EnvironmentProviderGrantScopeOutput",
    "EnvironmentProviderBuildViaEnvironmentProfileConfigInput",
    "EnvironmentProviderBuildViaEnvironmentProfileConfigOutput",
    "FUNCTIONS",
]
