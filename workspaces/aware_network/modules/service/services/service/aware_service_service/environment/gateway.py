from __future__ import annotations

from aware_environment_sdk import EnvironmentGeneratedApiClient
from aware_environment_service_dto.environment.environment import (
    InvokeFunctionCallTarget as EnvironmentApiInvokeFunctionCallTarget,
    InvokeFunctionRequest as EnvironmentApiInvokeFunctionRequest,
)
from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphInvokeFunctionRequest,
    MetaGraphInvokeFunctionResponse,
)
from aware_service_runtime.api_ingress.host_context import (
    current_service_api_host_context,
)
from aware_service_runtime.contracts import ServiceGraphGateway


class EnvironmentSdkGraphGateway(ServiceGraphGateway):
    """Remote Environment API graph backend for standalone Service host."""

    def __init__(self, *, api_client: EnvironmentGeneratedApiClient) -> None:
        self._api_client = api_client

    async def invoke_function(
        self,
        *,
        request: MetaGraphInvokeFunctionRequest,
        graph_context: object | None = None,
    ) -> MetaGraphInvokeFunctionResponse:
        _ = graph_context
        host_context = current_service_api_host_context()
        environment_context = (
            host_context.environment_context if host_context is not None else None
        )
        if environment_context is None:
            raise RuntimeError(
                "Environment SDK graph gateway requires explicit Environment "
                "operation context from Service API host context."
            )
        api_request = EnvironmentApiInvokeFunctionRequest(
            actor_id=request.actor_id,
            environment_id=environment_context.environment_id,
            process_id=environment_context.process_id,
            thread_id=environment_context.thread_id,
            branch_id=request.domain_branch_id,
            projection_hash=request.domain_projection_hash,
            call_target=EnvironmentApiInvokeFunctionCallTarget(
                request.call_target.value
            ),
            object_id=request.target_object_id,
            object_projection_graph_id=request.object_projection_graph_id,
            function_id=request.function_id,
            args=request.args,
            kwargs=request.kwargs,
            expected_graph_hash_pre=request.expected_graph_hash_pre,
            expected_head_commit_id=request.expected_head_commit_id,
            commit=request.commit,
            publish=request.publish,
        )
        api_response = await self._api_client.environment.function_call.invoke_function(
            api_request
        )
        return MetaGraphInvokeFunctionResponse(
            status=api_response.status,
            actor_id=api_response.actor_id,
            domain_branch_id=api_response.branch_id,
            domain_projection_hash=api_response.projection_hash,
            payload=api_response.payload,
            error=api_response.error,
            logs=api_response.logs,
            execution_time_ms=api_response.execution_time_ms,
            root_object_id=api_response.root_object_id,
            graph_hash_pre=api_response.graph_hash_pre,
            graph_hash_post=api_response.graph_hash_post,
            changes=api_response.changes,
            domain_commit_id=api_response.commit_id,
            object_instance_graph_commit_id=(
                api_response.object_instance_graph_commit_id
            ),
            function_call_id=api_response.function_call_id,
            function_call_response_id=api_response.function_call_response_id,
        )


__all__ = ["EnvironmentSdkGraphGateway"]
