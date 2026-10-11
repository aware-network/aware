"""Original source-projection handles and the fixed Workspace SDK entrance."""

from __future__ import annotations

from pathlib import Path
from weakref import WeakKeyDictionary

from .repository_source_projection_values import (
    WorkspaceSourceProjectionRefusalEvidence,
)

_CLIENTS = WeakKeyDictionary()
_HANDLES = WeakKeyDictionary()


class WorkspaceSourceProjectionRefusal(ValueError):
    def __init__(self, code, *, observation=None, cleanup=None, diagnostics=()):
        self.code = code
        self.evidence = WorkspaceSourceProjectionRefusalEvidence(
            code, observation, cleanup, False, tuple(diagnostics)
        )
        super().__init__(code)


class _Original:
    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("Use the original Workspace source projection owner")

    def __copy__(self):
        raise TypeError("Source projection handles cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("Source projection handles cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("Source projection handles cannot be serialized")


class WorkspaceSourceProjectionPlan(_Original):
    __slots__ = ()


class WorkspaceSourceProjectionAdmission(_Original):
    __slots__ = ()


def _issue_handle(owner, kind):
    from aware_workspace_runtime.repository_source_projection import (
        WorkspaceRepositorySourceProjectionRuntime,
    )

    if type(owner) is not WorkspaceRepositorySourceProjectionRuntime:
        raise WorkspaceSourceProjectionRefusal("original_workspace_owner_required")
    handle = object.__new__(kind)
    _HANDLES[handle] = owner
    return handle


def _original_owner(handle):
    owner = (
        _HANDLES.get(handle)
        if type(handle)
        in (WorkspaceSourceProjectionPlan, WorkspaceSourceProjectionAdmission)
        else None
    )
    if owner is None:
        raise WorkspaceSourceProjectionRefusal("source_projection_not_issued")
    owner.check_current()
    return owner


class WorkspaceRepositorySourceProjectionClient(_Original):
    __slots__ = ()

    @classmethod
    def filesystem(cls, *, repository_root: Path, state_root: Path, execution_id: str):
        if cls is not WorkspaceRepositorySourceProjectionClient:
            raise WorkspaceSourceProjectionRefusal("original_workspace_owner_required")
        from aware_workspace_fs_adapter.repository_source_projection import (
            FilesystemSourceProjectionPort,
        )
        from aware_workspace_runtime.repository_source_projection import (
            WorkspaceRepositorySourceProjectionRuntime,
        )

        runtime = WorkspaceRepositorySourceProjectionRuntime(
            FilesystemSourceProjectionPort(
                repository_root=repository_root,
                state_root=state_root,
                execution_id=execution_id,
            )
        )
        client = object.__new__(cls)
        _CLIENTS[client] = runtime
        return client

    @property
    def _owner(self):
        owner = (
            _CLIENTS.get(self)
            if type(self) is WorkspaceRepositorySourceProjectionClient
            else None
        )
        if owner is None:
            raise WorkspaceSourceProjectionRefusal(
                "source_projection_client_not_issued"
            )
        owner.check_current()
        return owner

    async def observe_source(self, *, target_path):
        return await self._owner.observe_source(target_path=target_path)

    async def retain_projection_body(
        self, content, *, expected_content_digest, expected_size_bytes
    ):
        return await self._owner.retain_body(
            content,
            expected_content_digest=expected_content_digest,
            expected_size_bytes=expected_size_bytes,
        )

    async def prepare_source_projection(self, request):
        return await self._owner.prepare(request)

    def observe_source_projection_plan(self, plan):
        return self._owner.observe_plan(plan)

    def verify_source_projection_plan(self, plan, *, expected_binding):
        return self._owner.verify_plan(plan, expected_binding=expected_binding)

    async def enroll_issue_projection(self, plan, *, issue_admission):
        return await self._owner.enroll(plan, issue_admission=issue_admission)

    async def project_source(self, plan, *, admission):
        return await self._owner.project(plan, admission=admission)

    def observe_source_projection(self, admission):
        return self._owner.observe(admission)

    async def resolve_source_projection_receipt(self, admission):
        return await self._owner.resolve(admission)

    async def release_source_projection(self):
        return await self._owner.release()


__all__ = (
    "WorkspaceRepositorySourceProjectionClient",
    "WorkspaceSourceProjectionAdmission",
    "WorkspaceSourceProjectionPlan",
    "WorkspaceSourceProjectionRefusal",
)
