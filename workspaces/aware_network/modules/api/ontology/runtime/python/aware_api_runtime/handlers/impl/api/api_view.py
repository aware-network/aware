from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Api Ontology
from aware_api_ontology.api.api_view_stream_enums import ApiViewStreamMode
from aware_api_ontology.api.api_view import ApiView
from aware_api_ontology.api.api_view_capability_endpoint import ApiViewCapabilityEndpoint
from aware_api_ontology.api.api_view_stream_policy import ApiViewStreamPolicy

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def set_stream_policy(
    api_view: ApiView, stream_mode: ApiViewStreamMode, description: str | None = None
) -> ApiViewStreamPolicy:
    """
    Bind one optional stream policy to this readable API view.
    """

    # --- AWARE: LOGIC START set_stream_policy
    return await ApiViewStreamPolicy.build_via_api_view(
        api_view_id=api_view.id,
        stream_mode=stream_mode,
        description=description,
    )
    # --- AWARE: LOGIC END set_stream_policy


async def bind_capability_endpoint(
    api_view: ApiView,
    action_key: str,
    api_capability_endpoint_id: UUID,
    endpoint_ref: str,
    description: str | None = None,
) -> ApiViewCapabilityEndpoint:
    """
    Bind one service-callable API capability endpoint to this readable API view.

    Contract:
    - API view actions are endpoint-backed.
    - `endpoint_ref` is the authored stable API endpoint reference.
    - No endpointless view action rail exists at API level.
    """

    # --- AWARE: LOGIC START bind_capability_endpoint
    return await ApiViewCapabilityEndpoint.build_via_api_view(
        api_view_id=api_view.id,
        action_key=action_key,
        api_capability_endpoint_id=api_capability_endpoint_id,
        endpoint_ref=endpoint_ref,
        description=description,
    )
    # --- AWARE: LOGIC END bind_capability_endpoint


async def create_via_api(
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

    # --- AWARE: LOGIC START create_via_api
    return ApiView(
        api_id=api_id,
        object_projection_graph_observable_id=object_projection_graph_observable_id,
        name=name,
        state_model_id=state_model_id,
        view_ref=view_ref,
        view_key=view_key,
        description=description,
    )
    # --- AWARE: LOGIC END create_via_api
