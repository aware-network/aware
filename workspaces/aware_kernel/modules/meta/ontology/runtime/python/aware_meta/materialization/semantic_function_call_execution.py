from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

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
from aware_meta.materialization.semantic_function_call_resolution import (
    META_OCG_BUILD_FUNCTION_REF,
    META_OCG_CREATE_NODE_FUNCTION_REF,
    META_OCG_PACKAGE_ATTACH_GRAPH_FUNCTION_REF,
    META_OCG_PACKAGE_BUILD_FUNCTION_REF,
    MetaSemanticFunctionCallResolution,
)


@dataclass(frozen=True, slots=True)
class _PlannedResult:
    object_id: str
    commit_id: str | None = None
    head_commit_id: str | None = None
    branch_id: str | None = None
    projection_hash: str | None = None
    object_instance_graph_commit_id: str | None = None


MetaSemanticFunctionCallInvocationTarget = SemanticGraphFunctionInvocationTarget
MetaSemanticFunctionCallInvocation = SemanticGraphFunctionInvocation
MetaSemanticFunctionCallInvocationResult = SemanticGraphFunctionInvocationResult
MetaSemanticFunctionCallInvocationBackend = SemanticGraphFunctionInvocationBackend


class MetaSemanticFunctionCallExecutionAdapter:
    def __init__(
        self,
        *,
        backend: MetaSemanticFunctionCallInvocationBackend,
    ) -> None:
        self._backend = backend
        self._planned_result_object_ids: dict[str, str] = {}
        self._planned_results_by_key: dict[str, _PlannedResult] = {}

    async def execute_create_root(
        self,
        resolution: object,
    ) -> SemanticFunctionCallExecutionStep:
        meta_resolution = _expect_meta_resolution(resolution)
        if meta_resolution.plan.function_ref not in {
            META_OCG_PACKAGE_BUILD_FUNCTION_REF,
            META_OCG_BUILD_FUNCTION_REF,
        }:
            raise ValueError(
                "Unsupported Meta root semantic function ref: "
                + meta_resolution.plan.function_ref
            )
        invocation = MetaSemanticFunctionCallInvocation(
            call_target="constructor",
            function_ref=meta_resolution.plan.function_ref,
            arguments=self._root_arguments(meta_resolution),
            provider_key="aware_meta",
            result_semantic_key=meta_resolution.result_semantic_key,
            evidence=meta_resolution.evidence_payload(),
        )
        result = await self._backend.invoke(invocation)
        self._remember_result(resolution=meta_resolution, result=result)
        return _invoked_step(
            resolution=meta_resolution,
            invocation=invocation,
            result=result,
        )

    async def execute_create_child(
        self,
        resolution: object,
    ) -> SemanticFunctionCallExecutionStep:
        meta_resolution = _expect_meta_resolution(resolution)
        if meta_resolution.plan.function_ref not in {
            META_OCG_CREATE_NODE_FUNCTION_REF,
            META_OCG_PACKAGE_ATTACH_GRAPH_FUNCTION_REF,
        }:
            raise ValueError(
                "Unsupported Meta child semantic function ref: "
                + meta_resolution.plan.function_ref
            )
        evidence = meta_resolution.evidence_payload()
        receiver_result = self._receiver_planned_result(meta_resolution)
        if receiver_result is not None:
            evidence = {
                **evidence,
                "branch_id": receiver_result.branch_id,
                "projection_hash": receiver_result.projection_hash,
            }
        invocation = MetaSemanticFunctionCallInvocation(
            call_target="instance",
            function_ref=meta_resolution.plan.function_ref,
            receiver_object_id=self._receiver_object_id(meta_resolution),
            arguments=self._child_arguments(meta_resolution),
            provider_key="aware_meta",
            result_semantic_key=meta_resolution.result_semantic_key,
            evidence=evidence,
        )
        result = await self._backend.invoke(invocation)
        self._remember_result(resolution=meta_resolution, result=result)
        return _invoked_step(
            resolution=meta_resolution,
            invocation=invocation,
            result=result,
        )

    def _receiver_object_id(
        self,
        resolution: MetaSemanticFunctionCallResolution,
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
            "Meta child semantic function execution requires a receiver object id "
            "from current head context or an earlier planned batch result."
        )

    def _remember_result(
        self,
        *,
        resolution: MetaSemanticFunctionCallResolution,
        result: MetaSemanticFunctionCallInvocationResult,
    ) -> None:
        result_semantic_key = _clean_optional(resolution.result_semantic_key)
        result_object_id = _clean_optional(result.object_id)
        if result_semantic_key is not None and result_object_id is not None:
            self._planned_result_object_ids[result_semantic_key] = result_object_id
            self._planned_results_by_key[result_semantic_key] = _planned_result(
                result=result
            )

    def _root_arguments(
        self,
        resolution: MetaSemanticFunctionCallResolution,
    ) -> dict[str, object]:
        arguments = dict(resolution.plan.arguments)
        function_ref = resolution.plan.function_ref
        if function_ref == META_OCG_PACKAGE_BUILD_FUNCTION_REF:
            package_arguments = {
                "package_name": arguments.get("package_name"),
                "fqn_prefix": arguments.get("fqn_prefix"),
            }
            graph_result = self._planned_result_for_metadata_key(
                resolution=resolution,
                key="object_config_graph_semantic_key",
            )
            if graph_result is not None:
                package_arguments["object_config_graph_id"] = graph_result.object_id
                graph_commit_id = (
                    graph_result.object_instance_graph_commit_id
                    or graph_result.head_commit_id
                    or graph_result.commit_id
                )
                if graph_commit_id is not None:
                    package_arguments[
                        "object_config_graph_object_instance_graph_commit_id"
                    ] = graph_commit_id
            return package_arguments
        if function_ref == META_OCG_BUILD_FUNCTION_REF:
            return {
                "name": arguments.get("name"),
                "hash": arguments.get("hash"),
                "fqn_prefix": arguments.get("fqn_prefix"),
                "language": arguments.get("language"),
            }
        raise ValueError(f"Unsupported Meta root semantic function ref: {function_ref}")

    def _child_arguments(
        self,
        resolution: MetaSemanticFunctionCallResolution,
    ) -> dict[str, object]:
        if resolution.plan.function_ref == META_OCG_CREATE_NODE_FUNCTION_REF:
            return _create_node_arguments(resolution)
        if resolution.plan.function_ref == META_OCG_PACKAGE_ATTACH_GRAPH_FUNCTION_REF:
            graph_result = self._planned_result_for_metadata_key(
                resolution=resolution,
                key="object_config_graph_semantic_key",
            )
            if graph_result is None:
                raise ValueError(
                    "Meta package attach execution requires a planned ObjectConfigGraph result."
                )
            payload: dict[str, object] = {
                "object_config_graph_id": graph_result.object_id,
            }
            graph_commit_id = (
                graph_result.object_instance_graph_commit_id
                or graph_result.head_commit_id
                or graph_result.commit_id
            )
            if graph_commit_id is not None:
                payload[
                    "object_config_graph_object_instance_graph_commit_id"
                ] = graph_commit_id
            return payload
        raise ValueError(
            "Unsupported Meta child semantic function ref: "
            + resolution.plan.function_ref
        )

    def _planned_result_for_metadata_key(
        self,
        *,
        resolution: MetaSemanticFunctionCallResolution,
        key: str,
    ) -> _PlannedResult | None:
        semantic_key = _clean_optional(resolution.plan.metadata.get(key))
        if semantic_key is None:
            return None
        return self._planned_results_by_key.get(semantic_key)

    def _receiver_planned_result(
        self,
        resolution: MetaSemanticFunctionCallResolution,
    ) -> _PlannedResult | None:
        receiver_semantic_key = _clean_optional(resolution.receiver_semantic_key)
        if receiver_semantic_key is None:
            return None
        return self._planned_results_by_key.get(receiver_semantic_key)


async def execute_meta_semantic_function_call_resolutions(
    *,
    resolutions: tuple[MetaSemanticFunctionCallResolution, ...],
    backend: MetaSemanticFunctionCallInvocationBackend,
    continue_on_failure: bool = False,
) -> SemanticFunctionCallExecutionResult:
    return await execute_semantic_function_call_resolutions(
        resolutions=resolutions,
        adapter=MetaSemanticFunctionCallExecutionAdapter(backend=backend),
        continue_on_failure=continue_on_failure,
    )


def meta_semantic_function_call_execution_backend_from_context(
    context: Mapping[str, object],
) -> MetaSemanticFunctionCallInvocationBackend | None:
    return semantic_graph_execution_backend_from_context(
        context,
        provider_key="aware_meta",
    )


def _expect_meta_resolution(
    resolution: object,
) -> MetaSemanticFunctionCallResolution:
    if isinstance(resolution, MetaSemanticFunctionCallResolution):
        return resolution
    raise TypeError(
        "Meta semantic function-call execution requires "
        "MetaSemanticFunctionCallResolution objects."
    )


def _create_node_arguments(
    resolution: MetaSemanticFunctionCallResolution,
) -> dict[str, object]:
    arguments = dict(resolution.plan.arguments)
    return {
        "type": arguments.get("type"),
        "node_key": arguments.get("node_key"),
    }


def _clean_optional(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _planned_result(
    *,
    result: MetaSemanticFunctionCallInvocationResult,
) -> _PlannedResult:
    return _PlannedResult(
        object_id=result.object_id,
        commit_id=result.commit_id,
        head_commit_id=result.head_commit_id,
        branch_id=result.branch_id,
        projection_hash=result.projection_hash,
        object_instance_graph_commit_id=_object_instance_graph_commit_id(
            result=result
        ),
    )


def _object_instance_graph_commit_id(
    *,
    result: MetaSemanticFunctionCallInvocationResult,
) -> str | None:
    response = result.evidence.get("response")
    if not isinstance(response, Mapping):
        return None
    return _clean_optional(response.get("object_instance_graph_commit_id"))


def _invoked_step(
    *,
    resolution: MetaSemanticFunctionCallResolution,
    invocation: MetaSemanticFunctionCallInvocation,
    result: MetaSemanticFunctionCallInvocationResult,
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
    "MetaSemanticFunctionCallExecutionAdapter",
    "MetaSemanticFunctionCallInvocation",
    "MetaSemanticFunctionCallInvocationBackend",
    "MetaSemanticFunctionCallInvocationResult",
    "MetaSemanticFunctionCallInvocationTarget",
    "execute_meta_semantic_function_call_resolutions",
    "meta_semantic_function_call_execution_backend_from_context",
]
