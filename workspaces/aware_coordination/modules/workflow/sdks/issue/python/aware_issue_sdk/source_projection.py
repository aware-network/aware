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

# C has its own original purpose. No v0 admission converts into tree authority.
_TREE_CLIENTS = WeakKeyDictionary()
_TREE_HANDLES = WeakKeyDictionary()


class IssueTreeProjectionRefusal(ValueError):
    def __init__(self, code, *, observation=None, cleanup=None, supplier_evidence=None):
        self.code = code
        self.observation = observation
        self.cleanup = cleanup
        self.supplier_evidence = supplier_evidence
        super().__init__(code)


class IssueTreeProjectionAdmissionPlan(_Original):
    __slots__ = ()


class IssueTreeProjectionAdmission(_Original):
    __slots__ = ()


class IssueTreeProjectionConsumption(_Original):
    __slots__ = ()


def _tree_record(value, registry, kind):
    import os
    import threading

    original = record = owner = owner_type = entrances = None
    try:
        for original, record in registry.items():
            if original is not value:
                continue
            owner, owner_type, entrances, pid, thread = record
            if pid != os.getpid() or thread != threading.get_ident():
                raise IssueTreeProjectionRefusal("issue_tree_origin_mismatch")
            if (
                type(value) is not kind
                or type(owner) is not owner_type
                or any(
                    vars(owner_type).get(name) is not method
                    for name, method in entrances.items()
                )
            ):
                entrances["retire_all"](owner)
                raise IssueTreeProjectionRefusal("issue_tree_original_changed")
            entrances["check_current"](owner)
            return owner, entrances
        raise IssueTreeProjectionRefusal("issue_tree_not_issued")
    finally:
        # A retained diagnostic frame must not acquire the last scanned family's
        # custody. Clearing references neither retires it nor disposes its owners.
        original = record = owner = owner_type = entrances = None
        value = registry = kind = None


def _tree_handle(owner, kind):
    from aware_issue_operational_runtime.source_projection import (
        IssueTreeProjectionRuntime,
    )

    if type(owner) is not IssueTreeProjectionRuntime or kind not in (
        IssueTreeProjectionAdmissionPlan,
        IssueTreeProjectionAdmission,
        IssueTreeProjectionConsumption,
    ):
        raise IssueTreeProjectionRefusal("issue_tree_original_required")
    value = object.__new__(kind)
    _TREE_HANDLES[value] = owner.sdk_record
    return value


def _tree_invoke(handle, kind, name, *args):
    owner, entrances = _tree_record(handle, _TREE_HANDLES, kind)
    return entrances[name](owner, handle, *args)


def verify_tree_projection_admission(admission, *, expected_binding):
    return _tree_invoke(
        admission, IssueTreeProjectionAdmission, "verify", expected_binding
    )


def consume_tree_projection_admission(admission, *, binding):
    return _tree_invoke(admission, IssueTreeProjectionAdmission, "consume", binding)


def verify_tree_projection_consumption(consumption, *, expected_binding):
    return _tree_invoke(
        consumption,
        IssueTreeProjectionConsumption,
        "verify_consumption",
        expected_binding,
    )


class IssueRepositoryTreeProjectionClient(_Original):
    __slots__ = ()

    @classmethod
    def filesystem(cls, *, repository_root: Path, execution_id: str):
        import os
        import threading

        from aware_issue_fs_adapter.source_projection import (
            FilesystemIssueProjectionPort,
        )
        from aware_issue_operational_runtime.source_projection import (
            IssueTreeProjectionRuntime,
        )

        if cls is not IssueRepositoryTreeProjectionClient:
            raise IssueTreeProjectionRefusal("issue_tree_original_required")
        try:
            owner = IssueTreeProjectionRuntime(
                FilesystemIssueProjectionPort(
                    repository_root=repository_root, execution_id=execution_id
                )
            )
        except BaseException as error:
            raise IssueTreeProjectionRefusal(
                getattr(error, "code", "issue_tree_authority_unavailable")
            ) from error
        entrances = {
            name: vars(IssueTreeProjectionRuntime)[name]
            for name in (
                "check_current",
                "retire_all",
                "prepare",
                "admit",
                "observe",
                "release",
                "verify",
                "consume",
                "verify_consumption",
            )
        }
        owner.sdk_record = (
            owner,
            IssueTreeProjectionRuntime,
            entrances,
            os.getpid(),
            threading.get_ident(),
        )
        client = object.__new__(cls)
        _TREE_CLIENTS[client] = owner.sdk_record
        return client

    async def prepare_tree_projection_admission(
        self, request, *, workspace_client, workspace_plan, expected_binding
    ):
        owner, entrances = _tree_record(
            self, _TREE_CLIENTS, IssueRepositoryTreeProjectionClient
        )
        return await entrances["prepare"](
            owner, request, workspace_client, workspace_plan, expected_binding
        )

    async def admit_tree_projection(self, plan):
        owner, entrances = _tree_record(
            self, _TREE_CLIENTS, IssueRepositoryTreeProjectionClient
        )
        return await entrances["admit"](owner, plan)

    def observe_tree_projection_admission(self, handle):
        owner, entrances = _tree_record(
            self, _TREE_CLIENTS, IssueRepositoryTreeProjectionClient
        )
        return entrances["observe"](owner, handle)

    async def release_tree_projection_admission(self, handle):
        owner, entrances = _tree_record(
            self, _TREE_CLIENTS, IssueRepositoryTreeProjectionClient
        )
        return await entrances["release"](owner, handle)


__all__ += (
    "IssueRepositoryTreeProjectionClient",
    "IssueTreeProjectionAdmission",
    "IssueTreeProjectionAdmissionPlan",
    "IssueTreeProjectionConsumption",
    "IssueTreeProjectionRefusal",
    "consume_tree_projection_admission",
    "verify_tree_projection_admission",
    "verify_tree_projection_consumption",
)
