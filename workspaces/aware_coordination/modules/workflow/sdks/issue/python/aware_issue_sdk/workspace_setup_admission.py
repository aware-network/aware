"""Original local A1 issuer ports. No decoded value or caller verifier is authority."""

from __future__ import annotations

import importlib
import weakref
from pathlib import Path


class IssueWorkspaceSetupRefusal(ValueError):
    def __init__(self, code, *, evidence=None):
        self.code = code
        self.evidence = evidence
        super().__init__(code)


class _Original:
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls):
        raise TypeError("original_issue_setup_owner_required")

    def __copy__(self):
        raise TypeError("issue_setup_authority_cannot_be_copied")

    def __deepcopy__(self, memo):
        raise TypeError("issue_setup_authority_cannot_be_copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("issue_setup_authority_cannot_be_serialized")


class IssueWorkspaceSetupAdmissionPlan(_Original):
    __slots__ = ()


class IssueWorkspaceSetupAdmission(_Original):
    __slots__ = ()


class IssueWorkspaceSetupEnrollment(_Original):
    __slots__ = ()


class IssueWorkspaceSetupConsumption(_Original):
    __slots__ = ()


_CLIENTS = {}
_HANDLES = {}


def _issue(owner, kind, record):
    IssueWorkspaceSetupRuntime = importlib.import_module(
        "aware_issue_operational_runtime.workspace_setup_admission"
    ).IssueWorkspaceSetupRuntime

    if type(owner) is not IssueWorkspaceSetupRuntime:
        raise IssueWorkspaceSetupRefusal("original_issue_setup_runtime_required")
    handle = object.__new__(kind)
    _HANDLES[id(handle)] = (weakref.ref(handle), owner, record)
    return handle


def _row(handle, *, cleanup=False):
    if type(handle) not in (
        IssueWorkspaceSetupAdmissionPlan,
        IssueWorkspaceSetupAdmission,
        IssueWorkspaceSetupEnrollment,
        IssueWorkspaceSetupConsumption,
    ):
        raise IssueWorkspaceSetupRefusal("original_issue_setup_authority_required")
    row = _HANDLES.get(id(handle))
    if row is None or row[0]() is not handle:
        raise IssueWorkspaceSetupRefusal("original_issue_setup_authority_required")
    guard_original_runtime = importlib.import_module(
        "aware_issue_operational_runtime.workspace_setup_admission"
    ).guard_original_runtime

    if not cleanup:
        guard_original_runtime(row[1])
    if not cleanup:
        try:
            row[1].current()
        except BaseException:
            row[2].phase = "retired"
            raise
    return row[1], row[2]


def enroll_workspace_setup_admission(admission, *, workspace_plan, expected_binding):
    owner, record = _row(admission)
    return owner.enroll(record, workspace_plan, expected_binding)


def consume_workspace_setup_admission(enrollment, *, expected_binding):
    owner, record = _row(enrollment)
    return owner.consume(record, expected_binding)


def verify_workspace_setup_consumption(
    consumption, *, expected_binding, next_effect_ordinal
):
    owner, record = _row(consumption)
    return owner.verify_consumption(record, expected_binding, next_effect_ordinal)


class IssueWorkspaceSetupAdmissionClient(_Original):
    __slots__ = ()

    @classmethod
    def filesystem(
        cls,
        *,
        repository_root: Path,
        execution_id: str,
        authority_manifest_locator: str,
    ):
        if cls is not IssueWorkspaceSetupAdmissionClient:
            raise IssueWorkspaceSetupRefusal("original_issue_setup_client_required")
        FilesystemIssueSetupPort = importlib.import_module(
            "aware_issue_fs_adapter.workspace_setup_admission"
        ).FilesystemIssueSetupPort
        IssueWorkspaceSetupRuntime = importlib.import_module(
            "aware_issue_operational_runtime.workspace_setup_admission"
        ).IssueWorkspaceSetupRuntime

        owner = IssueWorkspaceSetupRuntime(
            FilesystemIssueSetupPort(
                repository_root=repository_root,
                execution_id=execution_id,
                authority_manifest_locator=authority_manifest_locator,
            )
        )
        client = object.__new__(cls)
        _CLIENTS[id(client)] = (weakref.ref(client), owner)
        weakref.finalize(client, owner.release)
        return client

    @property
    def _owner(self):
        row = (
            _CLIENTS.get(id(self))
            if type(self) is IssueWorkspaceSetupAdmissionClient
            else None
        )
        if row is None or row[0]() is not self:
            raise IssueWorkspaceSetupRefusal("original_issue_setup_client_required")
        guard_original_runtime = importlib.import_module(
            "aware_issue_operational_runtime.workspace_setup_admission"
        ).guard_original_runtime

        guard_original_runtime(row[1])
        return row[1]

    def observe_authority_sources(self, *, issue_ref):
        return self._owner.observe_sources(issue_ref)

    def prepare_setup_admission(self, request, *, workspace_plan, expected_binding):
        return self._owner.prepare(request, workspace_plan, expected_binding)

    def admit_setup(self, plan):
        owner, record = _row(plan)
        if (
            owner is not self._owner
            or type(plan) is not IssueWorkspaceSetupAdmissionPlan
        ):
            raise IssueWorkspaceSetupRefusal("issue_setup_foreign_plan")
        return owner.admit(record)

    def observe_setup_admission(self, handle):
        owner, record = _row(handle, cleanup=True)
        if owner is not self._owner:
            raise IssueWorkspaceSetupRefusal("issue_setup_foreign_owner")
        return owner.observe(record)

    def release_setup_admission(self, handle):
        owner, record = _row(handle, cleanup=True)
        row = _CLIENTS.get(id(self))
        if row is None or row[0]() is not self or owner is not row[1]:
            raise IssueWorkspaceSetupRefusal("issue_setup_foreign_owner")
        _RUNTIME_METHODS = importlib.import_module(
            "aware_issue_operational_runtime.workspace_setup_admission"
        )._RUNTIME_METHODS

        method = next(
            method for name, method, _ in _RUNTIME_METHODS if name == "release_record"
        )
        return method(owner, record)

    def observe_client_cleanup(self):
        return self._owner.client_cleanup

    def release_client(self):
        row = _CLIENTS.get(id(self))
        if (
            type(self) is not IssueWorkspaceSetupAdmissionClient
            or row is None
            or row[0]() is not self
        ):
            raise IssueWorkspaceSetupRefusal("original_issue_setup_client_required")
        _RUNTIME_METHODS = importlib.import_module(
            "aware_issue_operational_runtime.workspace_setup_admission"
        )._RUNTIME_METHODS

        method = next(
            method for name, method, _ in _RUNTIME_METHODS if name == "release"
        )
        return method(row[1])
