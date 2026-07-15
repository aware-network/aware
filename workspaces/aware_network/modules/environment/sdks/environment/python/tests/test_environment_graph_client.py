from __future__ import annotations

from typing import Any, cast
from uuid import uuid4

import pytest

from aware_types import JsonObject
from aware_environment_sdk import (
    EnvironmentGraphClient,
    EnvironmentGraphContext,
)
from aware_environment_service_dto.environment.environment import (
    InvokeFunctionCallTarget,
)
from aware_environment_service_dto.environment.environment import (
    InvokeFunctionRequest,
)
from aware_environment_service_dto.environment.environment import (
    InvokeFunctionResponse,
)
from aware_environment_service_dto.environment.environment import (
    ResolveRuntimeRefsRequest,
)
from aware_environment_service_dto.environment.environment import (
    ResolveRuntimeRefsResponse,
)
from aware_environment_service_dto.environment.environment import (
    ResolvedRuntimeFunctionTarget,
)


class _RecordingRuntimeRefClient:
    def __init__(self) -> None:
        self.requests: list[ResolveRuntimeRefsRequest] = []
        self.function_id = uuid4()
        self.opg_id = uuid4()
        self.opgi_id = uuid4()

    async def resolve_runtime_refs(
        self,
        request: ResolveRuntimeRefsRequest,
    ) -> ResolveRuntimeRefsResponse:
        self.requests.append(request)
        query = request.function_targets[0]
        return ResolveRuntimeRefsResponse(
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
            branch_id=request.branch_id,
            projection_hash=request.projection_hash,
            status="succeeded",
            function_targets=[
                ResolvedRuntimeFunctionTarget(
                    query_key=query.query_key,
                    status="resolved",
                    function_ref=query.function_ref,
                    call_target=query.call_target,
                    class_config_id=uuid4(),
                    class_fqn="aware_api_ontology.api.api.Api",
                    function_id=self.function_id,
                    function_name="create",
                    projection_hash="api-projection",
                    object_projection_graph_id=self.opg_id,
                    object_projection_graph_identity_id=self.opgi_id,
                    evidence=cast(JsonObject, {"resolver": "test"}),
                )
            ],
            evidence=cast(JsonObject, {"resolver": "test"}),
        )


class _RecordingFunctionCallClient:
    def __init__(self) -> None:
        self.requests: list[InvokeFunctionRequest] = []
        self.object_id = uuid4()
        self.object_instance_graph_id = uuid4()
        self.object_instance_graph_identity_id = uuid4()
        self.object_instance_graph_branch_id = uuid4()

    async def invoke_function(
        self,
        request: InvokeFunctionRequest,
    ) -> InvokeFunctionResponse:
        self.requests.append(request)
        return InvokeFunctionResponse(
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
            branch_id=request.branch_id,
            projection_hash=request.projection_hash,
            status="succeeded",
            payload=cast(Any, {"id": str(self.object_id)}),
            commit_id=uuid4(),
            object_instance_graph_commit_id=uuid4(),
            object_projection_graph_id=request.object_projection_graph_id,
            object_projection_graph_identity_id=(
                request.object_projection_graph_identity_id
            ),
            object_instance_graph_id=self.object_instance_graph_id,
            object_instance_graph_identity_id=self.object_instance_graph_identity_id,
            object_instance_graph_branch_id=self.object_instance_graph_branch_id,
            graph_hash_post="post",
        )


class _RecordingEnvironmentApiClient:
    def __init__(self) -> None:
        self.runtime_ref = _RecordingRuntimeRefClient()
        self.function_call = _RecordingFunctionCallClient()


class _RecordingGeneratedApiClient:
    def __init__(self) -> None:
        self.environment = _RecordingEnvironmentApiClient()


def _context() -> EnvironmentGraphContext:
    return EnvironmentGraphContext(
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        branch_id=uuid4(),
        projection_hash="sdk-test",
    )


@pytest.mark.asyncio
async def test_environment_graph_client_resolves_target_over_generated_api() -> None:
    api_client = _RecordingGeneratedApiClient()
    context = _context()
    client = EnvironmentGraphClient(
        api_client=api_client,
        context=context,
    )

    target = await client.resolve_function_target(
        function_ref="aware_api_ontology.api.api.Api.create",
        call_target="constructor",
        projection_hash_hint="api-projection",
    )

    assert target.function_id == api_client.environment.runtime_ref.function_id
    assert (
        target.object_projection_graph_id == api_client.environment.runtime_ref.opg_id
    )
    assert (
        target.object_projection_graph_identity_id
        == api_client.environment.runtime_ref.opgi_id
    )
    assert target.projection_hash == "api-projection"
    assert target.evidence["resolver"] == "environment_sdk.generated_api_runtime_ref"
    request = api_client.environment.runtime_ref.requests[0]
    assert request.environment_id == context.environment_id
    assert request.function_targets[0].function_ref == (
        "aware_api_ontology.api.api.Api.create"
    )
    assert request.function_targets[0].projection_hash_hint == "api-projection"
    assert (
        request.function_targets[0].call_target
        is InvokeFunctionCallTarget.opg_constructor
    )


@pytest.mark.asyncio
async def test_environment_graph_client_invokes_function_ref_over_generated_api() -> (
    None
):
    api_client = _RecordingGeneratedApiClient()
    context = _context()
    client = EnvironmentGraphClient(
        api_client=api_client,
        context=context,
    )
    receiver_id = uuid4()

    receipt = await client.invoke_function_ref(
        function_ref="aware_api_ontology.api.api.Api.create_capability",
        call_target="instance",
        receiver_object_id=receiver_id,
        kwargs={"name": "read_demo"},
    )

    assert receipt.object_id == str(api_client.environment.function_call.object_id)
    assert receipt.commit_id is not None
    request = api_client.environment.function_call.requests[0]
    assert request.environment_id == context.environment_id
    assert request.branch_id == context.branch_id
    assert request.object_id == receiver_id
    assert (
        request.object_projection_graph_id == api_client.environment.runtime_ref.opg_id
    )
    assert (
        request.object_projection_graph_identity_id
        == api_client.environment.runtime_ref.opgi_id
    )
    assert request.call_target is InvokeFunctionCallTarget.instance
    assert request.function_id == api_client.environment.runtime_ref.function_id
    assert request.kwargs == {"name": "read_demo"}
    assert receipt.object_projection_graph_identity_id == str(
        api_client.environment.runtime_ref.opgi_id
    )
    assert receipt.object_projection_graph_id == str(
        api_client.environment.runtime_ref.opg_id
    )
    assert receipt.object_instance_graph_id == str(
        api_client.environment.function_call.object_instance_graph_id
    )
    assert receipt.object_instance_graph_identity_id == str(
        api_client.environment.function_call.object_instance_graph_identity_id
    )
    assert receipt.object_instance_graph_branch_id == str(
        api_client.environment.function_call.object_instance_graph_branch_id
    )
