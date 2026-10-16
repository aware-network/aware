"""Original C handles and fixed dispatch. Portable metadata grants no authority."""

from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any
from weakref import WeakKeyDictionary, ref

from .repository_tree_projection_values import (
    WorkspaceTreeProjectionCleanupObservation,
    WorkspaceTreeProjectionRefusalEvidence,
)

if TYPE_CHECKING:
    from aware_issue_sdk.source_projection import IssueTreeProjectionAdmission

    from .repository_tree_projection_values import (
        WorkspaceTreeProjectionBinding,
        WorkspaceTreeProjectionObservation,
        WorkspaceTreeProjectionPlanObservation,
        WorkspaceTreeProjectionRequest,
        WorkspaceTreeProjectionResolution,
    )
    from .repository_workflow import WorkspaceRepositoryWorkflowSource

_PID = os.getpid()
_CLIENTS: WeakKeyDictionary[Any, Any] = WeakKeyDictionary()
_HANDLES: WeakKeyDictionary[Any, Any] = WeakKeyDictionary()


class WorkspaceTreeProjectionRefusal(ValueError):
    def __init__(
        self, code, *, observation=None, cleanup=None, result=None, diagnostics=()
    ):
        cleanup = cleanup or WorkspaceTreeProjectionCleanupObservation(
            None, (), (), "not_attempted", True, ()
        )
        self.evidence = WorkspaceTreeProjectionRefusalEvidence(
            code, observation, cleanup, tuple(diagnostics), False
        )
        self.result = result
        self.code = code
        super().__init__(code)


class _Original:
    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("Use the original Workspace tree projection owner")

    def __copy__(self):
        raise TypeError("Tree projection handles cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("Tree projection handles cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("Tree projection handles cannot be serialized")


class WorkspaceTreeProjectionPlan(_Original):
    __slots__ = ()


class WorkspaceTreeProjectionAdmission(_Original):
    __slots__ = ()


class WorkspaceTreeProjectionResult(_Original):
    __slots__ = ()


def _record(value, registry, expected):
    original = record = runtime = None
    try:
        # Fork refusal precedes inherited owner locks, cleanup and lookup dispatch.
        if os.getpid() != _PID:
            raise WorkspaceTreeProjectionRefusal("original_owner_required")
        for original, record in registry.items():
            if original is value:
                runtime, runtime_class, entrances = record[:3]
                if type(runtime) is not runtime_class:
                    entrances["retire"](runtime)
                    raise WorkspaceTreeProjectionRefusal("retired")
                if (
                    runtime.pid != os.getpid()
                    or runtime.thread != threading.get_ident()
                ):
                    raise WorkspaceTreeProjectionRefusal("original_owner_required")
                if type(value) is not expected or any(
                    vars(runtime_class).get(name) is not method
                    for name, method in entrances.items()
                ):
                    entrances["retire"](runtime)
                    raise WorkspaceTreeProjectionRefusal(
                        "retired", cleanup=runtime.cleanup
                    )
                return record
        raise WorkspaceTreeProjectionRefusal("original_owner_required")
    finally:
        original = record = runtime = value = registry = None


def _issue_handle(runtime, kind):
    from aware_workspace_runtime.repository_tree_projection import (
        WorkspaceRepositoryTreeProjectionRuntime,
    )

    if type(runtime) is not WorkspaceRepositoryTreeProjectionRuntime:
        raise WorkspaceTreeProjectionRefusal("original_owner_required")
    if (
        runtime.phase not in ("prepared", "enrolled", "complete")
        or runtime.binding is None
    ):
        raise WorkspaceTreeProjectionRefusal("physical_unavailable")
    record = runtime.sdk_record
    if type(runtime) is not record[1] or kind not in (
        WorkspaceTreeProjectionPlan,
        WorkspaceTreeProjectionAdmission,
        WorkspaceTreeProjectionResult,
    ):
        raise WorkspaceTreeProjectionRefusal("original_owner_required")
    value = object.__new__(kind)
    _HANDLES[value] = record
    return value


def _require_handle(runtime, handle, kind):
    original = record = None
    try:
        for original, record in _HANDLES.items():
            if original is handle:
                # A foreign family must not retire either original owner.
                if record[0] is not runtime:
                    raise WorkspaceTreeProjectionRefusal("original_owner_required")
                _record(handle, _HANDLES, kind)
                return
        raise WorkspaceTreeProjectionRefusal("original_owner_required")
    finally:
        original = record = handle = runtime = None


async def _invoke_async(client, name, *arguments):
    runtime = entrances = None
    try:
        runtime, _, entrances = _record(
            client, _CLIENTS, WorkspaceRepositoryTreeProjectionClient
        )
        return await entrances[name](runtime, *arguments)
    finally:
        client = runtime = entrances = None
        arguments = ()


def _invoke(client, name, *arguments):
    runtime = entrances = None
    try:
        runtime, _, entrances = _record(
            client, _CLIENTS, WorkspaceRepositoryTreeProjectionClient
        )
        return entrances[name](runtime, *arguments)
    finally:
        client = runtime = entrances = None
        arguments = ()


class WorkspaceRepositoryTreeProjectionClient(_Original):
    __slots__ = ()

    @classmethod
    def filesystem(
        cls, *, repository_root: Path, state_root: Path, execution_id: str
    ) -> WorkspaceRepositoryTreeProjectionClient:
        runtime = client = None
        try:
            if (
                cls is not WorkspaceRepositoryTreeProjectionClient
                or os.getpid() != _PID
            ):
                raise WorkspaceTreeProjectionRefusal("original_owner_required")
            if (
                type(repository_root) is not type(Path())
                or type(state_root) is not type(Path())
                or type(execution_id) is not str
            ):
                raise WorkspaceTreeProjectionRefusal("malformed_request")
            from aware_workspace_fs_adapter.repository_source_projection import (
                FilesystemSourceProjectionPort,
            )
            from aware_workspace_runtime.repository_tree_projection import (
                WorkspaceRepositoryTreeProjectionRuntime,
            )

            try:
                physical = FilesystemSourceProjectionPort(
                    repository_root=repository_root,
                    state_root=state_root,
                    execution_id=execution_id,
                )
                runtime = WorkspaceRepositoryTreeProjectionRuntime(physical)
            except (ValueError, OSError) as error:
                raise WorkspaceTreeProjectionRefusal(
                    "target_authority_mismatch"
                ) from error
            entrances = {
                name: vars(WorkspaceRepositoryTreeProjectionRuntime)[name]
                for name in (
                    "prepare",
                    "observe_plan",
                    "verify_plan",
                    "enroll",
                    "project",
                    "resolve",
                    "release",
                    "retire",
                    "read_result",
                )
            }
            client = object.__new__(cls)
            record = (runtime, WorkspaceRepositoryTreeProjectionRuntime, entrances)
            runtime.sdk_record = record
            runtime.parent = ref(client)
            _CLIENTS[client] = record
            return client
        finally:
            runtime = client = None
            del repository_root, state_root, execution_id

    async def prepare_tree_projection(
        self,
        request: WorkspaceTreeProjectionRequest,
        *,
        source_delivery: WorkspaceRepositoryWorkflowSource,
    ) -> WorkspaceTreeProjectionPlan:
        try:
            return await _invoke_async(self, "prepare", request, source_delivery)
        finally:
            del self, request, source_delivery

    def observe_tree_projection_plan(
        self, plan: WorkspaceTreeProjectionPlan
    ) -> WorkspaceTreeProjectionPlanObservation:
        try:
            return _invoke(self, "observe_plan", plan)
        finally:
            del self, plan

    def verify_tree_projection_plan(
        self,
        plan: WorkspaceTreeProjectionPlan,
        *,
        expected_binding: WorkspaceTreeProjectionBinding,
    ) -> WorkspaceTreeProjectionPlanObservation:
        try:
            return _invoke(self, "verify_plan", plan, expected_binding)
        finally:
            del self, plan, expected_binding

    async def enroll_issue_tree_projection(
        self,
        plan: WorkspaceTreeProjectionPlan,
        *,
        issue_admission: IssueTreeProjectionAdmission,
    ) -> WorkspaceTreeProjectionAdmission:
        try:
            return await _invoke_async(self, "enroll", plan, issue_admission)
        finally:
            del self, plan, issue_admission

    async def project_tree(
        self,
        plan: WorkspaceTreeProjectionPlan,
        *,
        admission: WorkspaceTreeProjectionAdmission,
    ) -> WorkspaceTreeProjectionResult:
        try:
            return await _invoke_async(self, "project", plan, admission)
        finally:
            del self, plan, admission

    async def resolve_tree_projection_receipts(
        self, admission: WorkspaceTreeProjectionAdmission
    ) -> WorkspaceTreeProjectionResolution:
        try:
            return await _invoke_async(self, "resolve", admission)
        finally:
            del self, admission

    async def release_tree_projection(
        self,
    ) -> WorkspaceTreeProjectionCleanupObservation:
        try:
            return await _invoke_async(self, "release")
        finally:
            del self


def read_original_tree_projection_result(
    result: WorkspaceTreeProjectionResult,
    *,
    expected_binding: WorkspaceTreeProjectionBinding,
) -> WorkspaceTreeProjectionObservation:
    runtime = entrances = None
    try:
        runtime, _, entrances = _record(result, _HANDLES, WorkspaceTreeProjectionResult)
        return entrances["read_result"](runtime, result, expected_binding)
    finally:
        del result, expected_binding
        runtime = entrances = None


def validate_original_tree_projection_result(
    result: WorkspaceTreeProjectionResult,
    *,
    expected_binding: WorkspaceTreeProjectionBinding,
) -> None:
    try:
        read_original_tree_projection_result(result, expected_binding=expected_binding)
    finally:
        del result, expected_binding


__all__ = (
    "WorkspaceRepositoryTreeProjectionClient",
    "WorkspaceTreeProjectionAdmission",
    "WorkspaceTreeProjectionPlan",
    "WorkspaceTreeProjectionRefusal",
    "WorkspaceTreeProjectionResult",
    "read_original_tree_projection_result",
    "validate_original_tree_projection_result",
)
