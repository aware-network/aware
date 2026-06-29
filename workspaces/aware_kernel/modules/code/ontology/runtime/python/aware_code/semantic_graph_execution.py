from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal, Protocol, runtime_checkable


SEMANTIC_GRAPH_EXECUTION_BACKEND_CONTEXT_KEY = "semantic_graph_execution_backend"
SEMANTIC_GRAPH_EXECUTION_BACKEND_BY_PROVIDER_CONTEXT_KEY = (
    "semantic_graph_execution_backend_by_provider"
)

SemanticGraphFunctionInvocationTarget = Literal["constructor", "instance"]
SemanticGraphExecutionAdapterKind = Literal["local", "remote"]


@dataclass(frozen=True, slots=True)
class SemanticGraphFunctionInvocation:
    call_target: SemanticGraphFunctionInvocationTarget
    function_ref: str
    arguments: Mapping[str, object]
    receiver_object_id: str | None = None
    result_semantic_key: str | None = None
    provider_key: str | None = None
    evidence: Mapping[str, object] = field(default_factory=dict)

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "call_target": self.call_target,
            "function_ref": self.function_ref,
            "arguments": dict(self.arguments),
            "evidence": dict(self.evidence),
        }
        if self.provider_key is not None:
            payload["provider_key"] = self.provider_key
        if self.receiver_object_id is not None:
            payload["receiver_object_id"] = self.receiver_object_id
        if self.result_semantic_key is not None:
            payload["result_semantic_key"] = self.result_semantic_key
        return payload


@dataclass(frozen=True, slots=True)
class SemanticGraphResolvedFunctionTarget:
    function_ref: str
    call_target: SemanticGraphFunctionInvocationTarget
    provider_key: str | None = None
    function_runtime_target: str | None = None
    function_id: str | None = None
    projection_hash: str | None = None
    object_projection_graph_id: str | None = None
    receiver_object_id: str | None = None
    evidence: Mapping[str, object] = field(default_factory=dict)

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "function_ref": self.function_ref,
            "call_target": self.call_target,
            "evidence": dict(self.evidence),
        }
        if self.provider_key is not None:
            payload["provider_key"] = self.provider_key
        if self.function_runtime_target is not None:
            payload["function_runtime_target"] = self.function_runtime_target
        if self.function_id is not None:
            payload["function_id"] = self.function_id
        if self.projection_hash is not None:
            payload["projection_hash"] = self.projection_hash
        if self.object_projection_graph_id is not None:
            payload["object_projection_graph_id"] = self.object_projection_graph_id
        if self.receiver_object_id is not None:
            payload["receiver_object_id"] = self.receiver_object_id
        return payload


@dataclass(frozen=True, slots=True)
class SemanticGraphFunctionInvocationResult:
    object_id: str
    commit_id: str | None = None
    head_commit_id: str | None = None
    branch_id: str | None = None
    projection_hash: str | None = None
    adapter_kind: SemanticGraphExecutionAdapterKind | None = None
    evidence: Mapping[str, object] = field(default_factory=dict)

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "object_id": self.object_id,
            "evidence": dict(self.evidence),
        }
        if self.commit_id is not None:
            payload["commit_id"] = self.commit_id
        if self.head_commit_id is not None:
            payload["head_commit_id"] = self.head_commit_id
        if self.branch_id is not None:
            payload["branch_id"] = self.branch_id
        if self.projection_hash is not None:
            payload["projection_hash"] = self.projection_hash
        if self.adapter_kind is not None:
            payload["adapter_kind"] = self.adapter_kind
        return payload


@dataclass(frozen=True, slots=True)
class SemanticGraphCurrentHeadResolution:
    provider_key: str
    current_semantic_object_ids: Mapping[str, str] = field(default_factory=dict)
    resolved_argument_ref_object_ids: Mapping[str, str] = field(default_factory=dict)
    evidence: Mapping[str, object] = field(default_factory=dict)

    def evidence_payload(self) -> dict[str, object]:
        return {
            "provider_key": self.provider_key,
            "current_semantic_object_ids": dict(
                sorted(self.current_semantic_object_ids.items())
            ),
            "resolved_argument_ref_object_ids": dict(
                sorted(self.resolved_argument_ref_object_ids.items())
            ),
            "evidence": dict(self.evidence),
        }


@runtime_checkable
class SemanticGraphFunctionInvocationBackend(Protocol):
    async def invoke(
        self,
        invocation: SemanticGraphFunctionInvocation,
    ) -> SemanticGraphFunctionInvocationResult: ...


@runtime_checkable
class SemanticGraphFunctionTargetResolver(Protocol):
    async def resolve_target(
        self,
        invocation: SemanticGraphFunctionInvocation,
    ) -> SemanticGraphResolvedFunctionTarget: ...


@runtime_checkable
class SemanticGraphCurrentHeadResolver(Protocol):
    async def resolve_current_head(
        self,
        *,
        provider_key: str,
        semantic_keys: tuple[str, ...],
        argument_refs: Mapping[str, str],
    ) -> SemanticGraphCurrentHeadResolution: ...


def semantic_graph_execution_backend_from_context(
    context: Mapping[str, object],
    *,
    provider_key: str | None = None,
) -> SemanticGraphFunctionInvocationBackend | None:
    if provider_key is not None:
        provider_backends = context.get(
            SEMANTIC_GRAPH_EXECUTION_BACKEND_BY_PROVIDER_CONTEXT_KEY
        )
        if isinstance(provider_backends, Mapping):
            backend = provider_backends.get(provider_key)
            if isinstance(backend, SemanticGraphFunctionInvocationBackend):
                return backend
    backend = context.get(SEMANTIC_GRAPH_EXECUTION_BACKEND_CONTEXT_KEY)
    if isinstance(backend, SemanticGraphFunctionInvocationBackend):
        return backend
    return None


__all__ = [
    "SEMANTIC_GRAPH_EXECUTION_BACKEND_BY_PROVIDER_CONTEXT_KEY",
    "SEMANTIC_GRAPH_EXECUTION_BACKEND_CONTEXT_KEY",
    "SemanticGraphCurrentHeadResolution",
    "SemanticGraphCurrentHeadResolver",
    "SemanticGraphExecutionAdapterKind",
    "SemanticGraphFunctionInvocation",
    "SemanticGraphFunctionInvocationBackend",
    "SemanticGraphFunctionInvocationResult",
    "SemanticGraphFunctionInvocationTarget",
    "SemanticGraphFunctionTargetResolver",
    "SemanticGraphResolvedFunctionTarget",
    "semantic_graph_execution_backend_from_context",
]
