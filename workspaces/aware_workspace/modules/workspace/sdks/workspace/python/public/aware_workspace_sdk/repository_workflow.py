"""Original neutral workflow SDK ports; journal authority is a separate supplier."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, NoReturn, Self, SupportsIndex
from weakref import WeakKeyDictionary

from .repository_workflow_source_values import (
    WorkspaceWorkflowSourceBinding,
    WorkspaceWorkflowSourceObservation,
    WorkspaceWorkflowSourceRead,
)
from .repository_workflow_values import (
    WorkflowCleanup,
    WorkflowPersistence,
    WorkflowRefusalCode,
    WorkflowStage,
    WorkspaceRepositoryWorkflowAttemptObservation,
    WorkspaceRepositoryWorkflowAttemptObserveRequest,
    WorkspaceRepositoryWorkflowCleanupObservation,
    WorkspaceRepositoryWorkflowEvidenceAppendRequest,
    WorkspaceRepositoryWorkflowEvidenceWriteObservation,
    WorkspaceRepositoryWorkflowPlanObservation,
    WorkspaceRepositoryWorkflowRefusalEvidence,
    WorkspaceRepositoryWorkflowRequest,
    WorkspaceWorkflowEvidenceReference,
)

if TYPE_CHECKING:
    from aware_workspace_runtime.repository_workflow import (
        WorkspaceRepositoryWorkflowRuntime,
    )

# Exact original entries, captured at selection; lookup never hashes a foreign holder.
_CLIENTS: WeakKeyDictionary[
    WorkspaceRepositoryWorkflowClient,
    tuple[WorkspaceRepositoryWorkflowRuntime, type, dict[str, Callable[..., Any]]],
] = WeakKeyDictionary()

_SOURCES: WeakKeyDictionary[
    WorkspaceRepositoryWorkflowSource,
    tuple[WorkspaceRepositoryWorkflowRuntime, type, dict[str, Callable[..., Any]]],
] = WeakKeyDictionary()


class WorkspaceRepositoryWorkflowRefusal(ValueError):
    def __init__(
        self,
        code: WorkflowRefusalCode,
        *,
        stage: WorkflowStage = "source_capture",
        diagnostics: tuple[str, ...] = (),
        persistence: WorkflowPersistence = "not_written",
        cleanup: WorkflowCleanup = "completed",
        attempt_binding_ref: str | None = None,
        original_evidence_refs: tuple[WorkspaceWorkflowEvidenceReference, ...] = (),
    ) -> None:
        self.code: WorkflowRefusalCode = code
        self.evidence = WorkspaceRepositoryWorkflowRefusalEvidence(
            code,
            stage,
            original_evidence_refs,
            persistence,
            WorkspaceRepositoryWorkflowCleanupObservation(
                attempt_binding_ref, cleanup, ()
            ),
            diagnostics,
        )
        super().__init__(code)


class _Original:
    __slots__ = ("__weakref__",)

    def __new__(cls) -> Self:
        raise TypeError("Use the original Workspace workflow owner")

    def __copy__(self) -> _Original:
        raise TypeError("Workflow handles cannot be copied")

    def __deepcopy__(self, memo: object) -> _Original:
        raise TypeError("Workflow handles cannot be copied")

    def __reduce_ex__(self, protocol: SupportsIndex) -> NoReturn:
        raise TypeError("Workflow handles cannot be serialized")


class WorkspaceRepositoryWorkflowPlan(_Original):
    __slots__ = ()


class WorkspaceRepositoryWorkflowAttempt(_Original):
    __slots__ = ()


class WorkspaceRepositoryWorkflowSource(_Original):
    __slots__ = ()


class WorkspaceRepositoryWorkflowClient(_Original):
    __slots__ = ()

    @classmethod
    def filesystem(
        cls,
        *,
        source_repository_root: Path,
        target_repository_root: Path,
        state_root: Path,
        execution_id: str,
    ) -> WorkspaceRepositoryWorkflowClient:
        if cls is not WorkspaceRepositoryWorkflowClient:
            raise WorkspaceRepositoryWorkflowRefusal("foreign_or_retired_handle")
        from aware_workspace_runtime.repository_workflow import (
            WorkspaceRepositoryWorkflowRuntime,
        )

        runtime = WorkspaceRepositoryWorkflowRuntime(
            source_repository_root=source_repository_root,
            target_repository_root=target_repository_root,
            state_root=state_root,
            execution_id=execution_id,
        )
        entrances = {
            name: value
            for name, value in vars(WorkspaceRepositoryWorkflowRuntime).items()
            if callable(value)
        }
        client = object.__new__(cls)
        _CLIENTS[client] = runtime, WorkspaceRepositoryWorkflowRuntime, entrances
        return client

    def plan_repository_workflow(
        self, request: WorkspaceRepositoryWorkflowRequest
    ) -> WorkspaceRepositoryWorkflowPlan:
        return _invoke(self, "plan", request)

    def observe_repository_workflow_plan(
        self, plan: WorkspaceRepositoryWorkflowPlan
    ) -> WorkspaceRepositoryWorkflowPlanObservation:
        return _invoke(self, "observe_plan", plan)

    def open_repository_workflow_attempt(
        self, plan: WorkspaceRepositoryWorkflowPlan
    ) -> WorkspaceRepositoryWorkflowAttempt:
        return _invoke(self, "open_attempt", plan)

    def append_repository_workflow_evidence(
        self,
        attempt: WorkspaceRepositoryWorkflowAttempt,
        request: WorkspaceRepositoryWorkflowEvidenceAppendRequest,
    ) -> WorkspaceRepositoryWorkflowEvidenceWriteObservation:
        return _invoke(self, "append_evidence", attempt, request)

    def observe_repository_workflow_attempt(
        self, request: WorkspaceRepositoryWorkflowAttemptObserveRequest
    ) -> WorkspaceRepositoryWorkflowAttemptObservation:
        return _invoke(self, "observe_attempt", request)

    def release_repository_workflow(
        self, attempt: WorkspaceRepositoryWorkflowAttempt
    ) -> WorkspaceRepositoryWorkflowCleanupObservation:
        return _invoke(self, "release_attempt", attempt)

    def retain_repository_workflow_source(
        self, attempt: WorkspaceRepositoryWorkflowAttempt
    ) -> WorkspaceRepositoryWorkflowSource:
        source = None
        try:
            source = _invoke(self, "retain_source", attempt)
            _SOURCES[source] = _CLIENTS[self]
            return source
        finally:
            del self, attempt, source


def _invoke_source(source: object, name: str, *args: object) -> Any:
    original = runtime = runtime_class = entrances = None
    try:
        for original, (runtime, runtime_class, entrances) in _SOURCES.items():
            if original is source:
                # Foreign process rejection precedes inherited owner cleanup and IO.
                import os
                import threading

                if (
                    runtime.pid != os.getpid()
                    or runtime.thread != threading.get_ident()
                ):
                    raise WorkspaceRepositoryWorkflowRefusal(
                        "foreign_or_retired_handle"
                    )
                if type(runtime) is not runtime_class or any(
                    vars(runtime_class).get(key) is not method
                    for key, method in entrances.items()
                ):
                    entrances["release_source"](runtime, source)
                    raise WorkspaceRepositoryWorkflowRefusal(
                        "foreign_or_retired_handle"
                    )
                return entrances[name](runtime, source, *args)
        raise WorkspaceRepositoryWorkflowRefusal("foreign_or_retired_handle")
    finally:
        original = runtime = runtime_class = entrances = source = None
        args = ()


def observe_original_repository_workflow_source(
    source: WorkspaceRepositoryWorkflowSource,
) -> WorkspaceWorkflowSourceObservation:
    try:
        return _invoke_source(source, "observe_source")
    finally:
        del source


def verify_original_repository_workflow_source(
    source: WorkspaceRepositoryWorkflowSource,
    *,
    expected_binding: WorkspaceWorkflowSourceBinding,
) -> None:
    try:
        _invoke_source(source, "verify_source", expected_binding)
    finally:
        del source, expected_binding


def read_original_repository_workflow_source(
    source: WorkspaceRepositoryWorkflowSource,
    *,
    expected_binding: WorkspaceWorkflowSourceBinding,
    output_paths: tuple[str, ...],
) -> WorkspaceWorkflowSourceRead:
    try:
        return _invoke_source(source, "read_source", expected_binding, output_paths)
    finally:
        del source, expected_binding, output_paths


def verify_original_repository_workflow_source_paths(
    source: WorkspaceRepositoryWorkflowSource,
    *,
    expected_binding: WorkspaceWorkflowSourceBinding,
    output_paths: tuple[str, ...],
) -> None:
    """Validate original selected leaves; does not replace full source validation."""
    try:
        _invoke_source(source, "verify_source_paths", expected_binding, output_paths)
    finally:
        del source, expected_binding, output_paths


def release_original_repository_workflow_source(
    source: WorkspaceRepositoryWorkflowSource,
) -> WorkspaceRepositoryWorkflowCleanupObservation:
    try:
        return _invoke_source(source, "release_source")
    finally:
        del source


def _invoke(client: object, name: str, *args: object) -> Any:
    original = runtime = runtime_class = entrances = None
    try:
        for original, (runtime, runtime_class, entrances) in _CLIENTS.items():
            if original is client:
                if (
                    type(client) is not WorkspaceRepositoryWorkflowClient
                    or type(runtime) is not runtime_class
                    or any(
                        vars(runtime_class).get(key) is not method
                        for key, method in entrances.items()
                    )
                ):
                    entrances["retire"](runtime)
                    raise WorkspaceRepositoryWorkflowRefusal(
                        "foreign_or_retired_handle"
                    )
                entrances["check_current"](runtime)
                return entrances[name](runtime, *args)
        raise WorkspaceRepositoryWorkflowRefusal("foreign_or_retired_handle")
    finally:
        # Held foreign lookup errors must not pin unrelated clients/plans.
        original = runtime = runtime_class = entrances = client = None
        args = ()


__all__ = (
    "WorkspaceRepositoryWorkflowAttempt",
    "WorkspaceRepositoryWorkflowClient",
    "WorkspaceRepositoryWorkflowPlan",
    "WorkspaceRepositoryWorkflowRefusal",
    "WorkspaceRepositoryWorkflowSource",
    "observe_original_repository_workflow_source",
    "read_original_repository_workflow_source",
    "release_original_repository_workflow_source",
    "verify_original_repository_workflow_source",
    "verify_original_repository_workflow_source_paths",
)
