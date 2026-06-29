from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Literal, Protocol, runtime_checkable


SEMANTIC_FUNCTION_CALL_EXECUTION_CONFIG_KEY = (
    "semantic_function_call_execution"
)

SemanticFunctionCallExecutionStatus = Literal[
    "invoked",
    "skipped_noop",
    "blocked",
    "failed",
]

SemanticFunctionCallExecutionResolutionStatus = Literal[
    "create_root",
    "create_child",
    "noop_existing",
    "needs_ref_resolution",
    "unresolved_receiver",
    "unresolved_argument_ref",
    "unsupported_function",
]

_SAFE_INVOKE_STATUSES = frozenset({"create_root", "create_child"})
_BLOCKED_STATUSES = frozenset(
    {
        "needs_ref_resolution",
        "unresolved_receiver",
        "unresolved_argument_ref",
        "unsupported_function",
    }
)


@dataclass(frozen=True, slots=True)
class SemanticFunctionCallExecutionConfig:
    enabled: bool = False
    continue_on_failure: bool = False

    def evidence_payload(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "continue_on_failure": self.continue_on_failure,
        }

    @classmethod
    def from_materialization_context(
        cls,
        context: Mapping[str, object],
    ) -> "SemanticFunctionCallExecutionConfig":
        payload = context.get(SEMANTIC_FUNCTION_CALL_EXECUTION_CONFIG_KEY)
        if not isinstance(payload, Mapping):
            return cls()
        return cls(
            enabled=_bool_payload(payload.get("enabled")),
            continue_on_failure=_bool_payload(payload.get("continue_on_failure")),
        )


@dataclass(frozen=True, slots=True)
class SemanticFunctionCallExecutionStep:
    status: SemanticFunctionCallExecutionStatus
    resolution_status: str
    function_ref: str
    semantic_key: str | None = None
    result_object_id: str | None = None
    receiver_object_id: str | None = None
    reason: str | None = None
    error: str | None = None
    evidence: Mapping[str, object] = field(default_factory=dict)

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "status": self.status,
            "resolution_status": self.resolution_status,
            "function_ref": self.function_ref,
            "evidence": dict(self.evidence),
        }
        if self.semantic_key is not None:
            payload["semantic_key"] = self.semantic_key
        if self.result_object_id is not None:
            payload["result_object_id"] = self.result_object_id
        if self.receiver_object_id is not None:
            payload["receiver_object_id"] = self.receiver_object_id
        if self.reason is not None:
            payload["reason"] = self.reason
        if self.error is not None:
            payload["error"] = self.error
        return payload


@dataclass(frozen=True, slots=True)
class SemanticFunctionCallExecutionResult:
    steps: tuple[SemanticFunctionCallExecutionStep, ...]

    @property
    def invoked_count(self) -> int:
        return self._status_count("invoked")

    @property
    def skipped_count(self) -> int:
        return self._status_count("skipped_noop")

    @property
    def blocked_count(self) -> int:
        return self._status_count("blocked")

    @property
    def failed_count(self) -> int:
        return self._status_count("failed")

    @property
    def status_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for step in self.steps:
            counts[step.status] = counts.get(step.status, 0) + 1
        return dict(sorted(counts.items()))

    def evidence_payload(self) -> dict[str, object]:
        return {
            "step_count": len(self.steps),
            "status_counts": self.status_counts,
            "steps": tuple(step.evidence_payload() for step in self.steps),
        }

    def _status_count(self, status: SemanticFunctionCallExecutionStatus) -> int:
        return sum(1 for step in self.steps if step.status == status)


@runtime_checkable
class SemanticFunctionCallExecutionResolution(Protocol):
    @property
    def status(self) -> str: ...

    @property
    def result_semantic_key(self) -> str | None: ...

    @property
    def result_object_id(self) -> str | None: ...

    @property
    def receiver_object_id(self) -> str | None: ...

    @property
    def reason(self) -> str | None: ...

    def evidence_payload(self) -> dict[str, object]: ...


@runtime_checkable
class SemanticFunctionCallExecutionAdapter(Protocol):
    async def execute_create_root(
        self,
        resolution: SemanticFunctionCallExecutionResolution,
    ) -> SemanticFunctionCallExecutionStep: ...

    async def execute_create_child(
        self,
        resolution: SemanticFunctionCallExecutionResolution,
    ) -> SemanticFunctionCallExecutionStep: ...


async def execute_semantic_function_call_resolutions(
    *,
    resolutions: Sequence[SemanticFunctionCallExecutionResolution],
    adapter: SemanticFunctionCallExecutionAdapter,
    continue_on_failure: bool = False,
) -> SemanticFunctionCallExecutionResult:
    steps: list[SemanticFunctionCallExecutionStep] = []
    for resolution in resolutions:
        try:
            step = await _execute_resolution(
                resolution=resolution,
                adapter=adapter,
            )
        except Exception as exc:
            step = _failed_step(resolution=resolution, error=exc)
            steps.append(step)
            if not continue_on_failure:
                break
            continue
        steps.append(step)
        if step.status == "failed" and not continue_on_failure:
            break
    return SemanticFunctionCallExecutionResult(steps=tuple(steps))


async def _execute_resolution(
    *,
    resolution: SemanticFunctionCallExecutionResolution,
    adapter: SemanticFunctionCallExecutionAdapter,
) -> SemanticFunctionCallExecutionStep:
    resolution_status = str(resolution.status).strip()
    if resolution_status == "noop_existing":
        return _noop_step(resolution=resolution)
    if resolution_status in _BLOCKED_STATUSES:
        return _blocked_step(resolution=resolution)
    if resolution_status == "create_root":
        return await adapter.execute_create_root(resolution)
    if resolution_status == "create_child":
        return await adapter.execute_create_child(resolution)
    return _blocked_step(
        resolution=resolution,
        reason=f"Unsupported semantic function-call resolution status: {resolution_status}",
    )


def _noop_step(
    *,
    resolution: SemanticFunctionCallExecutionResolution,
) -> SemanticFunctionCallExecutionStep:
    return SemanticFunctionCallExecutionStep(
        status="skipped_noop",
        resolution_status=str(resolution.status),
        function_ref=_function_ref(resolution),
        semantic_key=resolution.result_semantic_key,
        result_object_id=resolution.result_object_id,
        receiver_object_id=resolution.receiver_object_id,
        reason=resolution.reason or "Semantic result already exists.",
        evidence=resolution.evidence_payload(),
    )


def _blocked_step(
    *,
    resolution: SemanticFunctionCallExecutionResolution,
    reason: str | None = None,
) -> SemanticFunctionCallExecutionStep:
    return SemanticFunctionCallExecutionStep(
        status="blocked",
        resolution_status=str(resolution.status),
        function_ref=_function_ref(resolution),
        semantic_key=resolution.result_semantic_key,
        result_object_id=resolution.result_object_id,
        receiver_object_id=resolution.receiver_object_id,
        reason=reason or resolution.reason or "Resolution is not executable.",
        evidence=resolution.evidence_payload(),
    )


def _failed_step(
    *,
    resolution: SemanticFunctionCallExecutionResolution,
    error: Exception,
) -> SemanticFunctionCallExecutionStep:
    return SemanticFunctionCallExecutionStep(
        status="failed",
        resolution_status=str(resolution.status),
        function_ref=_function_ref(resolution),
        semantic_key=resolution.result_semantic_key,
        result_object_id=resolution.result_object_id,
        receiver_object_id=resolution.receiver_object_id,
        error=f"{type(error).__name__}: {error}",
        evidence=resolution.evidence_payload(),
    )


def _function_ref(resolution: SemanticFunctionCallExecutionResolution) -> str:
    evidence = resolution.evidence_payload()
    value = evidence.get("function_ref")
    if value is None:
        return ""
    return str(value)


def _bool_payload(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().casefold() in {"1", "true", "yes", "on"}
    return False


__all__ = [
    "SEMANTIC_FUNCTION_CALL_EXECUTION_CONFIG_KEY",
    "SemanticFunctionCallExecutionAdapter",
    "SemanticFunctionCallExecutionConfig",
    "SemanticFunctionCallExecutionResolution",
    "SemanticFunctionCallExecutionResolutionStatus",
    "SemanticFunctionCallExecutionResult",
    "SemanticFunctionCallExecutionStatus",
    "SemanticFunctionCallExecutionStep",
    "execute_semantic_function_call_resolutions",
]
