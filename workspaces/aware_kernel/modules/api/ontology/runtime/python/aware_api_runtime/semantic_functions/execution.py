from __future__ import annotations

from collections.abc import Mapping

from aware_api_runtime.semantic_functions.resolution import (
    ApiSemanticFunctionCallResolution,
)
from aware_api_runtime.semantic_function_refs import (
    API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF,
    API_CREATE_CAPABILITY_FUNCTION_REF,
    API_CREATE_FUNCTION_REF,
)
from aware_code.semantic_function_call_execution import (
    SemanticFunctionCallExecutionResult,
    SemanticFunctionCallExecutionStep,
    execute_semantic_function_call_resolutions,
)
from aware_code.semantic_graph_execution import (
    SemanticGraphFunctionInvocation,
    SemanticGraphFunctionInvocationBackend,
    SemanticGraphFunctionInvocationResult,
    SemanticGraphFunctionInvocationTarget,
    semantic_graph_execution_backend_from_context,
)
from aware_code.semantic_materialization import (
    SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY,
)


API_SEMANTIC_FUNCTION_CALL_EXECUTION_BACKEND_CONTEXT_KEY = (
    "api_semantic_function_call_execution_backend"
)
ApiSemanticFunctionCallInvocationTarget = SemanticGraphFunctionInvocationTarget
ApiSemanticFunctionCallInvocation = SemanticGraphFunctionInvocation
ApiSemanticFunctionCallInvocationResult = SemanticGraphFunctionInvocationResult
ApiSemanticFunctionCallInvocationBackend = SemanticGraphFunctionInvocationBackend


class ApiSemanticFunctionCallExecutionAdapter:
    def __init__(
        self,
        *,
        backend: ApiSemanticFunctionCallInvocationBackend,
    ) -> None:
        self._backend = backend
        self._planned_result_object_ids: dict[str, str] = {}

    async def execute_create_root(
        self,
        resolution: object,
    ) -> SemanticFunctionCallExecutionStep:
        api_resolution = _expect_api_resolution(resolution)
        if api_resolution.plan.function_ref != API_CREATE_FUNCTION_REF:
            raise ValueError(
                "Unsupported API root semantic function ref: "
                + api_resolution.plan.function_ref
            )
        invocation = ApiSemanticFunctionCallInvocation(
            call_target="constructor",
            function_ref=api_resolution.plan.function_ref,
            arguments=dict(api_resolution.plan.arguments),
            provider_key="aware_api",
            result_semantic_key=api_resolution.result_semantic_key,
            evidence=api_resolution.evidence_payload(),
        )
        result = await self._backend.invoke(invocation)
        self._remember_result(
            resolution=api_resolution,
            result=result,
        )
        return _invoked_step(
            resolution=api_resolution,
            invocation=invocation,
            result=result,
        )

    async def execute_create_child(
        self,
        resolution: object,
    ) -> SemanticFunctionCallExecutionStep:
        api_resolution = _expect_api_resolution(resolution)
        receiver_object_id = self._receiver_object_id(api_resolution)
        invocation = ApiSemanticFunctionCallInvocation(
            call_target="instance",
            function_ref=api_resolution.plan.function_ref,
            receiver_object_id=receiver_object_id,
            arguments=_child_arguments(api_resolution),
            provider_key="aware_api",
            result_semantic_key=api_resolution.result_semantic_key,
            evidence=api_resolution.evidence_payload(),
        )
        result = await self._backend.invoke(invocation)
        self._remember_result(
            resolution=api_resolution,
            result=result,
        )
        return _invoked_step(
            resolution=api_resolution,
            invocation=invocation,
            result=result,
        )

    def _receiver_object_id(
        self,
        resolution: ApiSemanticFunctionCallResolution,
    ) -> str:
        receiver_object_id = _clean_optional(resolution.receiver_object_id)
        if receiver_object_id is not None:
            return receiver_object_id
        receiver_semantic_key = _clean_optional(resolution.receiver_semantic_key)
        if receiver_semantic_key is not None:
            planned_object_id = self._planned_result_object_ids.get(
                receiver_semantic_key
            )
            if planned_object_id is not None:
                return planned_object_id
        raise ValueError(
            "API child semantic function execution requires a receiver object id "
            "from current head context or an earlier planned batch result."
        )

    def _remember_result(
        self,
        *,
        resolution: ApiSemanticFunctionCallResolution,
        result: ApiSemanticFunctionCallInvocationResult,
    ) -> None:
        result_semantic_key = _clean_optional(resolution.result_semantic_key)
        result_object_id = _clean_optional(result.object_id)
        if result_semantic_key is not None and result_object_id is not None:
            self._planned_result_object_ids[result_semantic_key] = result_object_id


async def execute_api_semantic_function_call_resolutions(
    *,
    resolutions: tuple[ApiSemanticFunctionCallResolution, ...],
    backend: ApiSemanticFunctionCallInvocationBackend,
    continue_on_failure: bool = False,
) -> SemanticFunctionCallExecutionResult:
    return await execute_semantic_function_call_resolutions(
        resolutions=resolutions,
        adapter=ApiSemanticFunctionCallExecutionAdapter(backend=backend),
        continue_on_failure=continue_on_failure,
    )


def api_semantic_function_call_execution_backend_from_context(
    context: Mapping[str, object],
) -> ApiSemanticFunctionCallInvocationBackend | None:
    durable_backend = _api_execution_backend_from_durable_inputs(context=context)
    if durable_backend is not None:
        return durable_backend
    backend = context.get(API_SEMANTIC_FUNCTION_CALL_EXECUTION_BACKEND_CONTEXT_KEY)
    if isinstance(backend, ApiSemanticFunctionCallInvocationBackend):
        return backend
    return semantic_graph_execution_backend_from_context(
        context,
        provider_key="aware_api",
    )


def _api_execution_backend_from_durable_inputs(
    *,
    context: Mapping[str, object],
) -> ApiSemanticFunctionCallInvocationBackend | None:
    payload = context.get(SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY)
    if not isinstance(payload, Mapping):
        return None
    provider_inputs = payload.get("provider_inputs")
    if not isinstance(provider_inputs, Mapping):
        return None
    backend = provider_inputs.get(
        API_SEMANTIC_FUNCTION_CALL_EXECUTION_BACKEND_CONTEXT_KEY
    )
    if isinstance(backend, ApiSemanticFunctionCallInvocationBackend):
        return backend
    return semantic_graph_execution_backend_from_context(
        provider_inputs,
        provider_key="aware_api",
    )


def _expect_api_resolution(
    resolution: object,
) -> ApiSemanticFunctionCallResolution:
    if isinstance(resolution, ApiSemanticFunctionCallResolution):
        return resolution
    raise TypeError(
        "API semantic function-call execution requires "
        "ApiSemanticFunctionCallResolution objects."
    )


def _child_arguments(
    resolution: ApiSemanticFunctionCallResolution,
) -> dict[str, object]:
    function_ref = resolution.plan.function_ref
    arguments = dict(resolution.plan.arguments)
    if function_ref == API_CREATE_CAPABILITY_FUNCTION_REF:
        return arguments
    if function_ref == API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF:
        request_class_config_id = resolution.resolved_argument_refs.get(
            "request_class_config_id"
        )
        if not request_class_config_id:
            raise ValueError(
                "API endpoint semantic function execution requires resolved "
                "request_class_config_id."
            )
        arguments["request_class_config_id"] = request_class_config_id
        return arguments
    raise ValueError(f"Unsupported API child semantic function ref: {function_ref}")


def _clean_optional(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _invoked_step(
    *,
    resolution: ApiSemanticFunctionCallResolution,
    invocation: ApiSemanticFunctionCallInvocation,
    result: ApiSemanticFunctionCallInvocationResult,
) -> SemanticFunctionCallExecutionStep:
    return SemanticFunctionCallExecutionStep(
        status="invoked",
        resolution_status=resolution.status,
        function_ref=resolution.plan.function_ref,
        semantic_key=resolution.result_semantic_key,
        receiver_object_id=invocation.receiver_object_id,
        result_object_id=result.object_id,
        evidence={
            "resolution": resolution.evidence_payload(),
            "invocation": invocation.evidence_payload(),
            "result": result.evidence_payload(),
        },
    )


__all__ = [
    "API_SEMANTIC_FUNCTION_CALL_EXECUTION_BACKEND_CONTEXT_KEY",
    "ApiSemanticFunctionCallExecutionAdapter",
    "ApiSemanticFunctionCallInvocation",
    "ApiSemanticFunctionCallInvocationBackend",
    "ApiSemanticFunctionCallInvocationResult",
    "ApiSemanticFunctionCallInvocationTarget",
    "api_semantic_function_call_execution_backend_from_context",
    "execute_api_semantic_function_call_resolutions",
]
