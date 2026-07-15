from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Api Ontology
from aware_api_ontology.api.api_view_stream_enums import ApiViewStreamMode

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_api_ontology.api.api_view_capability_endpoint import ApiViewCapabilityEndpoint
    from aware_api_ontology.api.api_view_stream_policy import ApiViewStreamPolicy
    from aware_meta_ontology.class_.class_config import ClassConfig
    from aware_meta_ontology.graph.projection.object_projection_graph_observable import ObjectProjectionGraphObservable


class ApiView(ORMModel):
    """
    API-owned readable view-state contract.
    Contract:
    - `ApiCapabilityEndpoint` is for doing.
    - `ApiView` is for seeing.
    - The observable remains Meta-owned.
    - The state model is the exact DTO/ClassConfig a service must fulfill.
    """

    # Relationships
    object_projection_graph_observable: ObjectProjectionGraphObservable | None = Field(default=None, exclude=True)
    state_model: ClassConfig | None = Field(default=None, exclude=True)
    stream_policy: ApiViewStreamPolicy | None = Field(default=None)
    capability_endpoints: list[ApiViewCapabilityEndpoint] = Field(default_factory=list)

    # Attributes
    name: str
    view_ref: str
    view_key: str | None = Field(default=None)
    description: str | None = Field(default=None)

    # Foreign Keys
    api_id: UUID = Field(description="Foreign key for Api.api_views")
    object_projection_graph_observable_id: UUID = Field(
        description="Foreign key for ApiView.object_projection_graph_observable"
    )
    state_model_id: UUID = Field(description="Foreign key for ApiView.state_model")

    async def set_stream_policy(
        self, stream_mode: ApiViewStreamMode, description: str | None = None
    ) -> ApiViewStreamPolicy:
        """Bind one optional stream policy to this readable API view."""

        payload = {"stream_mode": stream_mode, "description": description}
        result = await invoke_instance(orm_model=self, function_name="set_stream_policy", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_api_ontology.api.api_view_stream_policy import ApiViewStreamPolicy

        if isinstance(value, ApiViewStreamPolicy):
            return value
        return ApiViewStreamPolicy.validate_invocation_value(value)

    async def bind_capability_endpoint(
        self, action_key: str, api_capability_endpoint_id: UUID, endpoint_ref: str, description: str | None = None
    ) -> ApiViewCapabilityEndpoint:
        """
        Bind one service-callable API capability endpoint to this readable API view.

        Contract:
        - API view actions are endpoint-backed.
        - `endpoint_ref` is the authored stable API endpoint reference.
        - No endpointless view action rail exists at API level.
        """

        payload = {
            "action_key": action_key,
            "api_capability_endpoint_id": api_capability_endpoint_id,
            "endpoint_ref": endpoint_ref,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="bind_capability_endpoint", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_api_ontology.api.api_view_capability_endpoint import ApiViewCapabilityEndpoint

        if isinstance(value, ApiViewCapabilityEndpoint):
            return value
        return ApiViewCapabilityEndpoint.validate_invocation_value(value)

    @classmethod
    async def create_via_api(
        cls,
        api_id: UUID,
        object_projection_graph_observable_id: UUID,
        name: str,
        state_model_id: UUID,
        view_ref: str,
        view_key: str | None = None,
        description: str | None = None,
    ) -> ApiView:
        """
        Create one deterministic API view-state contract under Api.

        Contract:
        - `ApiView.id` is deterministic for `(api_id, object_projection_graph_observable_id, name)`.
        - `view_ref` is the service/experience-facing stable API view reference.
        - `view_key` is optional renderer-facing shorthand and is not endpoint identity.
        """

        payload = {
            "api_id": api_id,
            "object_projection_graph_observable_id": object_projection_graph_observable_id,
            "name": name,
            "state_model_id": state_model_id,
            "view_ref": view_ref,
            "view_key": view_key,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_api", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ApiView):
            return value
        return ApiView.validate_invocation_value(value)


class ApiViewSetStreamPolicyInput(BaseModel):
    stream_mode: ApiViewStreamMode
    description: str | None = Field(default=None)


class ApiViewSetStreamPolicyOutput(BaseModel):
    value: ApiViewStreamPolicy


class ApiViewBindCapabilityEndpointInput(BaseModel):
    action_key: str
    api_capability_endpoint_id: UUID
    endpoint_ref: str
    description: str | None = Field(default=None)


class ApiViewBindCapabilityEndpointOutput(BaseModel):
    value: ApiViewCapabilityEndpoint


class ApiViewCreateViaApiInput(BaseModel):
    api_id: UUID = Field(description="Foreign key for Api.api_views")
    object_projection_graph_observable_id: UUID
    name: str
    state_model_id: UUID
    view_ref: str
    view_key: str | None = Field(default=None)
    description: str | None = Field(default=None)


class ApiViewCreateViaApiOutput(BaseModel):
    value: ApiView


FUNCTIONS = {
    "ApiView": {
        "set_stream_policy": {
            "canonical": {
                "name": "set_stream_policy",
                "description": "Bind one optional stream policy to this readable API view.",
                "is_constructor": False,
            },
            "input": ApiViewSetStreamPolicyInput,
            "output": ApiViewSetStreamPolicyOutput,
        },
        "bind_capability_endpoint": {
            "canonical": {
                "name": "bind_capability_endpoint",
                "description": "Bind one service-callable API capability endpoint to this readable API view.\n\nContract:\n- API view actions are endpoint-backed.\n- `endpoint_ref` is the authored stable API endpoint reference.\n- No endpointless view action rail exists at API level.",
                "is_constructor": False,
            },
            "input": ApiViewBindCapabilityEndpointInput,
            "output": ApiViewBindCapabilityEndpointOutput,
        },
        "create_via_api": {
            "canonical": {
                "name": "create_via_api",
                "description": "Create one deterministic API view-state contract under Api.\n\nContract:\n- `ApiView.id` is deterministic for `(api_id, object_projection_graph_observable_id, name)`.\n- `view_ref` is the service/experience-facing stable API view reference.\n- `view_key` is optional renderer-facing shorthand and is not endpoint identity.",
                "is_constructor": True,
            },
            "input": ApiViewCreateViaApiInput,
            "output": ApiViewCreateViaApiOutput,
        },
    },
}

__all__ = [
    "ApiView",
    "ApiViewSetStreamPolicyInput",
    "ApiViewSetStreamPolicyOutput",
    "ApiViewBindCapabilityEndpointInput",
    "ApiViewBindCapabilityEndpointOutput",
    "ApiViewCreateViaApiInput",
    "ApiViewCreateViaApiOutput",
    "FUNCTIONS",
]
