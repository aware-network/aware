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

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_environment_ontology.process.process_config import ProcessConfig
    from aware_environment_ontology.thread.thread_config import ThreadConfig
    from aware_meta_ontology.graph.projection.object_projection_graph import ObjectProjectionGraph


class EnvironmentProviderGrant(ORMModel):
    """
    Provider-neutral grant over an EnvironmentProfileConfig scope.
    Contract:
    - Environment owns the grant contract.
    - Experience may bind to the grant, but Environment never references Experience.
    - Service/provider fulfillment remains outside this ontology.
    """

    # Relationships
    process_config: ProcessConfig | None = Field(default=None)
    thread_config: ThreadConfig | None = Field(default=None)
    object_projection_graph: ObjectProjectionGraph | None = Field(default=None)

    # Attributes
    action_scope: str | None = Field(default=None)
    description: str | None = Field(default=None)
    grant_key: str
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)
    scope_kind: str = Field(default="profile")
    status: str = Field(default="active")

    # Foreign Keys
    environment_provider_id: UUID = Field(description="Foreign key for EnvironmentProvider.grants")
    process_config_id: UUID | None = Field(
        default=None, description="Foreign key for EnvironmentProviderGrant.process_config"
    )
    thread_config_id: UUID | None = Field(
        default=None, description="Foreign key for EnvironmentProviderGrant.thread_config"
    )
    object_projection_graph_id: UUID | None = Field(
        default=None, description="Foreign key for EnvironmentProviderGrant.object_projection_graph"
    )

    @classmethod
    async def build_via_environment_provider(
        cls,
        environment_provider_id: UUID,
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
        Create one Environment provider grant.

        Contract:
        - Stable identity is `(environment_provider_id, grant_key)`.
        - Optional scope refs constrain the granted Environment surface.
        - No Experience or Service class reference is allowed here.
        """

        payload = {
            "environment_provider_id": environment_provider_id,
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
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_environment_provider", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentProviderGrant):
            return value
        return EnvironmentProviderGrant.validate_invocation_value(value)


class EnvironmentProviderGrantBuildViaEnvironmentProviderInput(BaseModel):
    environment_provider_id: UUID = Field(description="Foreign key for EnvironmentProvider.grants")
    grant_key: str
    scope_kind: str = Field(default="profile")
    process_config_id: UUID | None = Field(default=None)
    thread_config_id: UUID | None = Field(default=None)
    object_projection_graph_id: UUID | None = Field(default=None)
    action_scope: str | None = Field(default=None)
    status: str = Field(default="active")
    description: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class EnvironmentProviderGrantBuildViaEnvironmentProviderOutput(BaseModel):
    value: EnvironmentProviderGrant


FUNCTIONS = {
    "EnvironmentProviderGrant": {
        "build_via_environment_provider": {
            "canonical": {
                "name": "build_via_environment_provider",
                "description": "Create one Environment provider grant.\n\nContract:\n- Stable identity is `(environment_provider_id, grant_key)`.\n- Optional scope refs constrain the granted Environment surface.\n- No Experience or Service class reference is allowed here.",
                "is_constructor": True,
            },
            "input": EnvironmentProviderGrantBuildViaEnvironmentProviderInput,
            "output": EnvironmentProviderGrantBuildViaEnvironmentProviderOutput,
        },
    },
}

__all__ = [
    "EnvironmentProviderGrant",
    "EnvironmentProviderGrantBuildViaEnvironmentProviderInput",
    "EnvironmentProviderGrantBuildViaEnvironmentProviderOutput",
    "FUNCTIONS",
]
