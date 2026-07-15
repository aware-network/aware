from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import BaseModel
from _service_runtime_test_paths import REPO_ROOT
from aware_meta_service.local_sdk import load_local_meta_graph_context

from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphInvokeFunctionRequest,
    MetaGraphInvokeFunctionResponse,
)
from aware_meta_service_dto.graph.instance.function_call_target import (
    MetaGraphFunctionCallTarget,
)
from aware_service_runtime.api_ingress.gateway_execution import (
    build_gateway_service_api_execution_backend,
)
from aware_service_runtime.api_ingress.graph_execution import (
    ServiceApiGraphExecutionBinding,
    ServiceApiGraphExecutionPlan,
)
from aware_service_runtime.api_ingress.target_resolution import service_graph_catalog
from aware_service_runtime.contracts import (
    ServiceGraphContextLike,
    ServiceGraphGateway,
    ServiceOperationContext,
)


class _CreateApiRequest(BaseModel):
    name: str
    description: str | None = None


class _CreateCapabilityRequest(BaseModel):
    name: str


class _RecordingGraphGateway(ServiceGraphGateway):
    def __init__(self, *, expected_graph_context: ServiceGraphContextLike) -> None:
        self._expected_graph_context = expected_graph_context
        self.requests: list[MetaGraphInvokeFunctionRequest] = []

    async def invoke_function(
        self,
        *,
        request: MetaGraphInvokeFunctionRequest,
        graph_context: ServiceGraphContextLike | None = None,
    ) -> MetaGraphInvokeFunctionResponse:
        assert graph_context is self._expected_graph_context
        self.requests.append(request)
        return MetaGraphInvokeFunctionResponse(
            actor_id=request.actor_id,
            status="succeeded",
            domain_branch_id=request.domain_branch_id,
            domain_projection_hash=request.domain_projection_hash,
            payload={},
        )


def _service_operation_context() -> ServiceOperationContext:
    return ServiceOperationContext(
        actor_id=uuid4(),
        branch_id=uuid4(),
        projection_hash="service-proof-projection",
    )


def _execution_plan(
    *,
    graph_function_python_ref: str,
    graph_function_runtime_target: str,
    fulfillment_name: str,
    request_object: object,
    call_target_kind: str | None = None,
    exact_output_field_name: str | None = None,
) -> ServiceApiGraphExecutionPlan:
    return ServiceApiGraphExecutionPlan(
        service_operation_id=uuid4(),
        service_id=uuid4(),
        service_operation_config_id=uuid4(),
        service_operation_config_api_endpoint_id=uuid4(),
        api_call_id=uuid4(),
        endpoint_ref="openai.door.open",
        request_object=request_object,
        bindings=(
            ServiceApiGraphExecutionBinding(
                service_operation_config_api_endpoint_function_id=uuid4(),
                api_capability_endpoint_function_id=uuid4(),
                name=fulfillment_name,
                graph_target="aware_api",
                graph_capability_function_name=fulfillment_name,
                graph_function_python_ref=graph_function_python_ref,
                graph_function_runtime_target=graph_function_runtime_target,
                call_target_kind=call_target_kind,
                exact_output_field_name=exact_output_field_name,
            ),
        ),
    )


def _resolve_function_binding(
    *, graph_context: ServiceGraphContextLike, class_fqn: str, function_name: str
):
    graph_catalog = service_graph_catalog(graph_context)
    matches = [
        (class_config, link)
        for class_config in graph_catalog.class_configs_by_id.values()
        if (class_config.class_fqn or "").strip() == class_fqn
        for link in class_config.class_config_function_configs
        if link.function_config is not None
        and (link.function_config.name or "").strip() == function_name
    ]
    assert len(matches) == 1
    return matches[0]


def _service_api_graph_context_package_manifest_paths(
    repo_root: Path,
) -> tuple[Path, ...]:
    return (
        repo_root
        / "workspaces/aware_kernel/modules/storage/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/code/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/history/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/ontology/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/api/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/sdk/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/attention/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/economy/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/identity/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/environment/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/experience/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/service/ontology/structure/aware.toml",
    )


async def _load_service_api_graph_context() -> ServiceGraphContextLike:
    return await load_local_meta_graph_context(
        package_manifest_paths=_service_api_graph_context_package_manifest_paths(
            REPO_ROOT
        ),
        repo_root=REPO_ROOT,
    )


def test_service_api_graph_context_does_not_use_root_module_discovery() -> None:
    source = Path(__file__).read_text(encoding="utf-8")

    assert "module" + "_ids" not in source


@pytest.mark.asyncio
async def test_gateway_backend_routes_constructor_binding_through_service_graph_gateway() -> (
    None
):
    graph_context = await _load_service_api_graph_context()
    graph_gateway = _RecordingGraphGateway(expected_graph_context=graph_context)
    context = _service_operation_context()

    backend = build_gateway_service_api_execution_backend(
        execution_plan=_execution_plan(
            graph_function_python_ref="aware_api_ontology.api.api.Api.create",
            graph_function_runtime_target="aware_api.api.Api.create",
            fulfillment_name="create_api",
            request_object=_CreateApiRequest(name="api"),
            call_target_kind="constructor",
        ),
        graph_context=graph_context,
        graph_gateway=graph_gateway,
        operation_context=context,
    )

    response = await backend.invoke_fulfillment(
        fulfillment_name="create_api",
        request=_CreateApiRequest(name="graph-proof"),
    )

    assert response == {}
    assert len(graph_gateway.requests) == 1
    request = graph_gateway.requests[0]
    assert request.call_target is MetaGraphFunctionCallTarget.opg_constructor
    assert request.domain_branch_id is None
    assert request.kwargs == {"name": "graph-proof", "description": None}

    class_config, function_link = _resolve_function_binding(
        graph_context=graph_context,
        class_fqn="aware_api.api.Api",
        function_name="create",
    )
    assert request.function_id == function_link.function_config.id
    assert request.object_projection_graph_id is not None
    graph_catalog = service_graph_catalog(graph_context)
    projection = graph_catalog.opg_by_id[request.object_projection_graph_id]
    assert request.domain_projection_hash == projection.projection_hash
    assert any(
        bool(node.is_root) and node.class_config_id == class_config.id
        for node in projection.object_projection_graph_nodes
    )
    assert any(
        entry.function_constructor_id == function_link.id
        for entry in projection.object_projection_graph_constructors
    )


@pytest.mark.asyncio
async def test_gateway_backend_fails_closed_on_projection_read_target_binding() -> None:
    graph_context = await _load_service_api_graph_context()
    graph_gateway = _RecordingGraphGateway(expected_graph_context=graph_context)
    context = _service_operation_context()

    backend = build_gateway_service_api_execution_backend(
        execution_plan=_execution_plan(
            graph_function_python_ref=(
                "aware_api_ontology.api.api.Api.create_capability"
            ),
            graph_function_runtime_target=("aware_api.api.Api.create_capability"),
            fulfillment_name="create_capability",
            request_object=_CreateCapabilityRequest(name="territory"),
            call_target_kind="opg_read",
        ),
        graph_context=graph_context,
        graph_gateway=graph_gateway,
        operation_context=context,
    )

    with pytest.raises(
        RuntimeError,
        match="no longer invokes ontology projection reads",
    ):
        await backend.invoke_fulfillment(
            fulfillment_name="create_capability",
            request=_CreateCapabilityRequest(name="territory"),
        )

    assert graph_gateway.requests == []


@pytest.mark.asyncio
async def test_gateway_backend_fails_closed_on_instance_target_without_identity() -> (
    None
):
    graph_context = await _load_service_api_graph_context()
    graph_gateway = _RecordingGraphGateway(expected_graph_context=graph_context)
    context = _service_operation_context()

    backend = build_gateway_service_api_execution_backend(
        execution_plan=_execution_plan(
            graph_function_python_ref="aware_api_ontology.api.api.Api.create_capability",
            graph_function_runtime_target="aware_api.api.Api.create_capability",
            fulfillment_name="create_capability",
            request_object=_CreateCapabilityRequest(name="door"),
        ),
        graph_context=graph_context,
        graph_gateway=graph_gateway,
        operation_context=context,
    )

    with pytest.raises(
        RuntimeError,
        match="cannot invoke instance targets yet",
    ):
        await backend.invoke_fulfillment(
            fulfillment_name="create_capability",
            request=_CreateCapabilityRequest(name="door"),
        )

    assert graph_gateway.requests == []
