"""Genuine Issue source-projection admission; values do not issue authority."""

from __future__ import annotations

from pathlib import Path
from weakref import WeakKeyDictionary

_CLIENTS = WeakKeyDictionary()
_HANDLES = WeakKeyDictionary()


class IssueSourceProjectionRefusal(ValueError):
    def __init__(self, code, *, observation=None, diagnostics=()):
        self.code = code
        self.observation = observation
        self.diagnostics = tuple(diagnostics)
        super().__init__(code)


class _Original:
    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("Use the original Issue source projection owner")

    def __copy__(self):
        raise TypeError("Issue projection authority cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("Issue projection authority cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("Issue projection authority cannot be serialized")


class IssueStartProgressProjectionPlan(_Original):
    __slots__ = ()


class IssueSourceProjectionAdmission(_Original):
    __slots__ = ()


class IssueSourceProjectionConsumption(_Original):
    __slots__ = ()


def _issue_handle(owner, kind):
    from aware_issue_operational_runtime.source_projection import (
        IssueSourceProjectionRuntime,
    )

    if type(owner) is not IssueSourceProjectionRuntime:
        raise IssueSourceProjectionRefusal("original_issue_owner_required")
    handle = object.__new__(kind)
    _HANDLES[handle] = owner
    return handle


def _owner(handle):
    owner = (
        _HANDLES.get(handle)
        if type(handle)
        in (
            IssueStartProgressProjectionPlan,
            IssueSourceProjectionAdmission,
            IssueSourceProjectionConsumption,
        )
        else None
    )
    if owner is None:
        raise IssueSourceProjectionRefusal("issue_projection_not_issued")
    owner.check_current()
    return owner


def verify_source_projection_admission(admission, *, expected_binding):
    return _owner(admission).verify(admission, expected_binding=expected_binding)


def consume_source_projection_admission(admission, *, binding):
    return _owner(admission).consume(admission, binding=binding)


class IssueStartProgressProjectionClient(_Original):
    __slots__ = ()

    @classmethod
    def filesystem(cls, *, repository_root: Path, execution_id: str):
        if cls is not IssueStartProgressProjectionClient:
            raise IssueSourceProjectionRefusal("original_issue_owner_required")
        from aware_issue_fs_adapter.source_projection import (
            FilesystemIssueProjectionPort,
        )
        from aware_issue_operational_runtime.source_projection import (
            IssueSourceProjectionRuntime,
        )

        owner = IssueSourceProjectionRuntime(
            FilesystemIssueProjectionPort(
                repository_root=repository_root, execution_id=execution_id
            )
        )
        client = object.__new__(cls)
        _CLIENTS[client] = owner
        return client

    @property
    def _owner(self):
        owner = (
            _CLIENTS.get(self)
            if type(self) is IssueStartProgressProjectionClient
            else None
        )
        if owner is None:
            raise IssueSourceProjectionRefusal("issue_projection_client_not_issued")
        owner.check_current()
        return owner

    async def prepare_start_progress_projection(self, request, *, workspace_client):
        return await self._owner.prepare(request, workspace_client=workspace_client)

    async def admit_start_progress_projection(self, plan):
        return await self._owner.admit(plan)

    async def execute_start_progress_projection(self, plan, *, admission):
        return await self._owner.execute(plan, admission=admission)


__all__ = (
    "IssueSourceProjectionAdmission",
    "IssueSourceProjectionConsumption",
    "IssueSourceProjectionRefusal",
    "IssueStartProgressProjectionClient",
    "IssueStartProgressProjectionPlan",
    "consume_source_projection_admission",
    "verify_source_projection_admission",
)
