from __future__ import annotations

from dataclasses import dataclass

import pytest

from aware_code.semantic_graph_execution import (
    SEMANTIC_GRAPH_EXECUTION_BACKEND_BY_PROVIDER_CONTEXT_KEY,
    SEMANTIC_GRAPH_EXECUTION_BACKEND_CONTEXT_KEY,
    SemanticGraphCurrentHeadResolution,
    SemanticGraphFunctionInvocation,
    SemanticGraphFunctionInvocationBackend,
    SemanticGraphFunctionInvocationResult,
    SemanticGraphResolvedFunctionTarget,
    semantic_graph_execution_backend_from_context,
)


class RecordingSemanticGraphBackend:
    def __init__(self) -> None:
        self.invocations: list[SemanticGraphFunctionInvocation] = []

    async def invoke(
        self,
        invocation: SemanticGraphFunctionInvocation,
    ) -> SemanticGraphFunctionInvocationResult:
        self.invocations.append(invocation)
        return SemanticGraphFunctionInvocationResult(
            object_id="created-object-id",
            commit_id="commit-id",
            head_commit_id="head-id",
            adapter_kind="local",
            evidence={"ordinal": len(self.invocations)},
        )


@dataclass(frozen=True, slots=True)
class NotABackend:
    value: str = "not-a-backend"


def test_semantic_graph_invocation_evidence_is_provider_neutral() -> None:
    invocation = SemanticGraphFunctionInvocation(
        provider_key="aware_api",
        call_target="instance",
        function_ref="aware_api.default.api.Api.create_capability",
        receiver_object_id="api-id",
        arguments={"name": "read_demo"},
        result_semantic_key="api:demo/capability:read_demo",
        evidence={"semantic_key": "api:demo"},
    )

    assert invocation.evidence_payload() == {
        "provider_key": "aware_api",
        "call_target": "instance",
        "function_ref": "aware_api.default.api.Api.create_capability",
        "receiver_object_id": "api-id",
        "arguments": {"name": "read_demo"},
        "result_semantic_key": "api:demo/capability:read_demo",
        "evidence": {"semantic_key": "api:demo"},
    }


@pytest.mark.asyncio
async def test_semantic_graph_backend_protocol_records_commit_evidence() -> None:
    backend = RecordingSemanticGraphBackend()
    assert isinstance(backend, SemanticGraphFunctionInvocationBackend)

    result = await backend.invoke(
        SemanticGraphFunctionInvocation(
            provider_key="aware_api",
            call_target="constructor",
            function_ref="aware_api.default.api.Api.create",
            arguments={"name": "demo"},
            result_semantic_key="api:demo",
        )
    )

    assert result.evidence_payload() == {
        "object_id": "created-object-id",
        "commit_id": "commit-id",
        "head_commit_id": "head-id",
        "adapter_kind": "local",
        "evidence": {"ordinal": 1},
    }
    assert backend.invocations[0].provider_key == "aware_api"


def test_semantic_graph_context_resolves_provider_specific_backend_first() -> None:
    fallback_backend = RecordingSemanticGraphBackend()
    api_backend = RecordingSemanticGraphBackend()

    resolved = semantic_graph_execution_backend_from_context(
        {
            SEMANTIC_GRAPH_EXECUTION_BACKEND_CONTEXT_KEY: fallback_backend,
            SEMANTIC_GRAPH_EXECUTION_BACKEND_BY_PROVIDER_CONTEXT_KEY: {
                "aware_api": api_backend,
            },
        },
        provider_key="aware_api",
    )

    assert resolved is api_backend


def test_semantic_graph_context_falls_back_to_shared_backend() -> None:
    fallback_backend = RecordingSemanticGraphBackend()

    resolved = semantic_graph_execution_backend_from_context(
        {SEMANTIC_GRAPH_EXECUTION_BACKEND_CONTEXT_KEY: fallback_backend},
        provider_key="aware_interface",
    )

    assert resolved is fallback_backend


def test_semantic_graph_context_ignores_invalid_backend() -> None:
    assert (
        semantic_graph_execution_backend_from_context(
            {SEMANTIC_GRAPH_EXECUTION_BACKEND_CONTEXT_KEY: NotABackend()}
        )
        is None
    )


def test_semantic_graph_resolved_target_evidence_is_serializable() -> None:
    target = SemanticGraphResolvedFunctionTarget(
        provider_key="aware_api",
        call_target="constructor",
        function_ref="aware_api.default.api.Api.create",
        function_runtime_target="aware_api.default.api.Api.create",
        function_id="function-id",
        projection_hash="projection-hash",
        object_projection_graph_id="opg-id",
        evidence={"resolver": "local-index"},
    )

    assert target.evidence_payload() == {
        "provider_key": "aware_api",
        "call_target": "constructor",
        "function_ref": "aware_api.default.api.Api.create",
        "function_runtime_target": "aware_api.default.api.Api.create",
        "function_id": "function-id",
        "projection_hash": "projection-hash",
        "object_projection_graph_id": "opg-id",
        "evidence": {"resolver": "local-index"},
    }


def test_semantic_graph_current_head_resolution_evidence_sorts_context() -> None:
    resolution = SemanticGraphCurrentHeadResolution(
        provider_key="aware_api",
        current_semantic_object_ids={
            "api:demo/capability:read": "capability-id",
            "api:demo": "api-id",
        },
        resolved_argument_ref_object_ids={
            "Z": "z-id",
            "A": "a-id",
        },
        evidence={"source": "workspace-revision"},
    )

    assert resolution.evidence_payload() == {
        "provider_key": "aware_api",
        "current_semantic_object_ids": {
            "api:demo": "api-id",
            "api:demo/capability:read": "capability-id",
        },
        "resolved_argument_ref_object_ids": {
            "A": "a-id",
            "Z": "z-id",
        },
        "evidence": {"source": "workspace-revision"},
    }
