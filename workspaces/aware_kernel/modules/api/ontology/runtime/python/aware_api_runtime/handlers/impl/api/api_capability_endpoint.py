from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Api Ontology
from aware_api_ontology.api.api_capability_endpoint_stream_enums import ApiCapabilityEndpointStreamMode
from aware_api_ontology.api.api_call import ApiCall
from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
from aware_api_ontology.api.api_capability_endpoint_function import ApiCapabilityEndpointFunction
from aware_api_ontology.api.api_capability_endpoint_request_config import ApiCapabilityEndpointRequestConfig
from aware_api_ontology.api.api_capability_endpoint_response_config import ApiCapabilityEndpointResponseConfig
from aware_api_ontology.api.api_capability_endpoint_stream_config import ApiCapabilityEndpointStreamConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
import inspect

from aware_api_ontology.stable_ids import stable_api_capability_endpoint_id
from aware_orm.registry import ORMModelRegistry
from aware_api_runtime.invocation.materialization.context import (
    current_api_call_materialization_input,
    scoped_api_call_materialization_input,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta.runtime.handler_context import (
    current_handler_index,
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create_call(
    api_capability_endpoint: ApiCapabilityEndpoint, call_key: UUID, description: str | None = None
) -> ApiCall:
    """
    Create one stage-one API call receipt anchored on this endpoint.
    """

    # --- AWARE: LOGIC START create_call
    request_config = api_capability_endpoint.request_config
    if inspect.isawaitable(request_config):
        request_config = await request_config
    if request_config is None:
        raise ValueError("ApiCapabilityEndpoint.request_config must exist before ApiCall can be created")
    materialization_input = current_api_call_materialization_input()
    if materialization_input is not None and materialization_input.request_class_config is not None:
        request_class_config = materialization_input.request_class_config
        if request_class_config.id is None:
            raise ValueError(
                "ApiCapabilityEndpoint.create_call received materialization request ClassConfig without id"
            )
        if request_class_config.id != request_config.class_config_id:
            raise ValueError(
                "ApiCapabilityEndpoint.create_call received mismatched request ClassConfig in "
                "materialization context: "
                f"expected_request_class_config_id={request_config.class_config_id} "
                f"got_request_class_config_id={request_class_config.id}"
            )
    else:
        request_class_config = request_config.class_config
        if inspect.isawaitable(request_class_config):
            request_class_config = await request_class_config
        if request_class_config is None:
            session = current_handler_session()
            request_class_config = session.imap_get(
                ClassConfig,
                request_config.class_config_id,
            )
        if request_class_config is None:
            request_class_config = current_handler_index().class_configs_by_id.get(request_config.class_config_id)
            if request_class_config is not None:
                current_handler_session().imap_add(request_class_config)
        if request_class_config is None:
            orm_class = ORMModelRegistry.get_class_by_class_config_id(request_config.class_config_id)
            if orm_class is not None:
                request_class_config = orm_class.get_class_config()
        if request_class_config is None or request_class_config.id is None:
            raise ValueError(
                "ApiCapabilityEndpoint.create_call requires request_config.class_config to resolve through "
                "the endpoint request-contract portal before ApiCall can be created"
            )
    with scoped_api_call_materialization_input(
        request_payload=(materialization_input.request_payload if materialization_input is not None else {}),
        request_class_config=request_class_config,
        request_class_configs_by_id=(
            materialization_input.request_class_configs_by_id if materialization_input is not None else None
        ),
    ):
        return await ApiCall.create_via_api_capability_endpoint(
            api_capability_endpoint_id=api_capability_endpoint.id,
            call_key=call_key,
            request_class_config_id=request_class_config.id,
            description=description,
        )
    # --- AWARE: LOGIC END create_call


async def create_function(
    api_capability_endpoint: ApiCapabilityEndpoint,
    name: str,
    api_graph_capability_function_id: UUID,
    description: str | None = None,
) -> ApiCapabilityEndpointFunction:
    """
    Create one named endpoint-owned callable binding to one graph-scoped capability function.
    """

    # --- AWARE: LOGIC START create_function
    return await ApiCapabilityEndpointFunction.create_via_api_capability_endpoint(
        api_capability_endpoint_id=api_capability_endpoint.id,
        name=name,
        api_graph_capability_function_id=api_graph_capability_function_id,
        description=description,
    )
    # --- AWARE: LOGIC END create_function


async def ensure_request_config(
    api_capability_endpoint: ApiCapabilityEndpoint, request_class_config_id: UUID, description: str | None = None
) -> ApiCapabilityEndpointRequestConfig:
    """
    Ensure the required request contract beneath this endpoint.

    Contract:
    - Endpoint creation must materialize this rail already.
    - This function exists so the endpoint -> request_config relationship remains
      an explicit containment propagation rail in canonical `.aware`.
    """

    # --- AWARE: LOGIC START ensure_request_config
    existing = api_capability_endpoint.request_config
    if inspect.isawaitable(existing):
        existing = await existing
    if existing is not None:
        if existing.class_config_id != request_class_config_id:
            raise ValueError(
                "ApiCapabilityEndpoint.ensure_request_config found mismatched request contract: "
                f"endpoint_id={api_capability_endpoint.id} "
                f"expected_class_config_id={request_class_config_id} "
                f"got_class_config_id={existing.class_config_id}"
            )
        return existing

    created = await ApiCapabilityEndpointRequestConfig.build_via_api_capability_endpoint(
        api_capability_endpoint_id=api_capability_endpoint.id,
        class_config_id=request_class_config_id,
        description=description,
    )
    api_capability_endpoint.request_config = created
    return created
    # --- AWARE: LOGIC END ensure_request_config


async def create_response_config(
    api_capability_endpoint: ApiCapabilityEndpoint, class_config_id: UUID, description: str | None = None
) -> ApiCapabilityEndpointResponseConfig:
    """
    Create one optional response contract beneath this endpoint's request contract.
    """

    # --- AWARE: LOGIC START create_response_config
    request_config = api_capability_endpoint.request_config
    if inspect.isawaitable(request_config):
        request_config = await request_config
    if request_config is None:
        raise ValueError("ApiCapabilityEndpoint.request_config must exist before response_config can be created")
    return await request_config.create_response_config(
        class_config_id=class_config_id,
        description=description,
    )
    # --- AWARE: LOGIC END create_response_config


async def create_stream_config(
    api_capability_endpoint: ApiCapabilityEndpoint,
    stream_mode: ApiCapabilityEndpointStreamMode,
    description: str | None = None,
) -> ApiCapabilityEndpointStreamConfig:
    """
    Create one optional stream contract beneath this endpoint's request contract.
    """

    # --- AWARE: LOGIC START create_stream_config
    request_config = api_capability_endpoint.request_config
    if inspect.isawaitable(request_config):
        request_config = await request_config
    if request_config is None:
        raise ValueError("ApiCapabilityEndpoint.request_config must exist before stream_config can be created")
    return await request_config.create_stream_config(
        stream_mode=stream_mode,
        description=description,
    )
    # --- AWARE: LOGIC END create_stream_config


async def create_via_api_capability(
    api_capability_id: UUID, name: str, request_class_config_id: UUID, description: str | None = None
) -> ApiCapabilityEndpoint:
    """
    Create one deterministic external/public endpoint rail under ApiCapability
    and materialize its required request contract in the same constructor path.
    """

    # --- AWARE: LOGIC START create_via_api_capability
    endpoint_id = stable_api_capability_endpoint_id(
        api_capability_id=api_capability_id,
        name=name,
    )
    existing = ApiCapabilityEndpoint.get_by_id_sync(endpoint_id)
    if existing is not None:
        if existing.api_capability_id != api_capability_id:
            raise ValueError(
                "ApiCapabilityEndpoint.create_via_api_capability id collision with mismatched api_capability_id: "
                f"id={endpoint_id} expected_api_capability_id={api_capability_id} "
                f"got_api_capability_id={existing.api_capability_id}"
            )
        existing_request_config = existing.request_config
        if inspect.isawaitable(existing_request_config):
            existing_request_config = await existing_request_config
        if existing_request_config is None:
            raise ValueError(
                "ApiCapabilityEndpoint.create_via_api_capability found existing endpoint "
                "without required request_config: "
                f"endpoint_id={endpoint_id}"
            )
        if existing_request_config.class_config_id != request_class_config_id:
            raise ValueError(
                "ApiCapabilityEndpoint.create_via_api_capability id collision with mismatched request contract: "
                f"endpoint_id={endpoint_id} expected_class_config_id={request_class_config_id} "
                f"got_class_config_id={existing_request_config.class_config_id}"
            )
        return existing

    request_config = await ApiCapabilityEndpointRequestConfig.build_via_api_capability_endpoint(
        api_capability_endpoint_id=endpoint_id,
        class_config_id=request_class_config_id,
    )
    endpoint = ApiCapabilityEndpoint(
        id=endpoint_id,
        api_capability_id=api_capability_id,
        name=name,
        description=description,
    )
    endpoint.request_config = request_config
    return endpoint
    # --- AWARE: LOGIC END create_via_api_capability
