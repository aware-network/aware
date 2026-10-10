"""Original process-local publication handles and owner-dispatched SDK ports.

Values/codecs remain detached evidence. These objects cannot be constructed,
copied or decoded into an original owner's capability.
"""

from __future__ import annotations

import re
from weakref import WeakKeyDictionary

from .codec import (
    repository_publication_value_from_payload,
    repository_publication_value_to_payload,
)
from .values import (
    WorkspaceRepositoryCommitRequest,
    WorkspaceRepositoryPlanVerificationRequest,
)

_OWNERS = WeakKeyDictionary()
_CLIENT_PROVIDERS = WeakKeyDictionary()
_ENROLLMENT_CLIENTS = WeakKeyDictionary()


class WorkspacePublicationHandleRefusal(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


class _OriginalHandle:
    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("Use the original Workspace publication provider")

    def __copy__(self):
        raise TypeError("Workspace publication handles cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("Workspace publication handles cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("Workspace publication handles cannot be serialized")

    @property
    def phase(self):
        return _owner(self)._snapshot_handle(self).phase


class WorkspaceRepositoryCommitPlan(_OriginalHandle):
    __slots__ = ()

    @property
    def binding(self):
        return _owner(self)._snapshot_handle(self).binding

    @property
    def observation(self):
        return _owner(self)._snapshot_handle(self).observation


class WorkspacePublicationWorkAdmission(_OriginalHandle):
    __slots__ = ()

    @property
    def phase(self):
        return _owner(self)._work_admission_phase(self)


def _owner(handle):
    owner = (
        _OWNERS.get(handle)
        if type(handle)
        in (
            WorkspaceRepositoryCommitPlan,
            WorkspacePublicationWorkAdmission,
        )
        else None
    )
    if owner is None:
        raise WorkspacePublicationHandleRefusal("workspace_plan_not_issued")
    return owner


def _issue_plan(owner):
    from aware_workspace_runtime.repository_publication import (
        WorkspaceRepositoryPublicationRuntime,
    )

    if type(owner) is not WorkspaceRepositoryPublicationRuntime:
        raise WorkspacePublicationHandleRefusal("original_workspace_provider_required")
    plan = object.__new__(WorkspaceRepositoryCommitPlan)
    _OWNERS[plan] = owner
    return plan


def _issue_work_admission(owner):
    from aware_workspace_runtime.repository_publication import (
        WorkspaceRepositoryPublicationRuntime,
    )

    if type(owner) is not WorkspaceRepositoryPublicationRuntime:
        raise WorkspacePublicationHandleRefusal("original_workspace_provider_required")
    admission = object.__new__(WorkspacePublicationWorkAdmission)
    _OWNERS[admission] = owner
    return admission


class WorkspaceIssuePublicationEnrollmentClient:
    """Explicit supplying-SDK selection; detached bindings are not admission."""

    __slots__ = ("__weakref__",)

    def __init__(self, *, workspace_client, issue_client):
        from aware_issue_sdk.repository_publication import (
            IssueRepositoryPublicationClient,
        )

        if type(workspace_client) is not WorkspaceRepositoryPublicationClient:
            raise TypeError("Original Workspace SDK client required")
        if type(issue_client) is not IssueRepositoryPublicationClient:
            raise TypeError("Original supplying Issue SDK client required")
        _ENROLLMENT_CLIENTS[self] = (workspace_client, issue_client)

    def enroll_issue_repository_publication(self, plan, admission):
        selected = _ENROLLMENT_CLIENTS.get(self)
        if selected is None:
            raise WorkspacePublicationHandleRefusal(
                "workspace_enrollment_client_not_issued"
            )
        workspace, issue = selected
        return workspace._provider.enroll_issue_repository_publication(
            plan, admission, issue_client=issue
        )


class WorkspaceRepositoryPublicationClient:
    """Selected original runtime; request validation never grants authority.

    Plans, genuine Issue enrollment and original-writer publication are owner
    dispatched. Values are detached; original handles remain process-local.
    """

    __slots__ = ("__weakref__",)

    def __init__(self, provider):
        from aware_workspace_runtime.repository_publication import (
            WorkspaceRepositoryPublicationRuntime,
        )

        if type(provider) is not WorkspaceRepositoryPublicationRuntime:
            raise TypeError("Original Workspace publication runtime required")
        _CLIENT_PROVIDERS[self] = provider

    @classmethod
    def filesystem(cls, *, repository_root):
        """Explicitly select our original FS provider, without a foreign registrar.

        Selection creates the existing owner; it neither admits Issue work nor
        captures a plan or invokes the Git writer. Reader imports remain lazy.
        Root validation belongs to that original physical provider: do not
        silently resolve a symlink or select a different repository here.
        """
        if cls is not WorkspaceRepositoryPublicationClient:
            raise TypeError("Original Workspace SDK client required")
        from aware_workspace_fs_adapter.repository_publication import (
            FilesystemRepositoryCandidatePort,
        )
        from aware_workspace_runtime.repository_publication import (
            WorkspaceRepositoryPublicationRuntime,
        )

        return cls(
            WorkspaceRepositoryPublicationRuntime(
                FilesystemRepositoryCandidatePort(repository_root=repository_root)
            )
        )

    @property
    def _provider(self):
        provider = _CLIENT_PROVIDERS.get(self)
        if provider is None:
            raise WorkspacePublicationHandleRefusal("workspace_sdk_client_not_issued")
        return provider

    def plan_repository_commit(self, request: WorkspaceRepositoryCommitRequest):
        request = repository_publication_value_from_payload(
            WorkspaceRepositoryCommitRequest,
            repository_publication_value_to_payload(request),
        )
        if type(request) is not WorkspaceRepositoryCommitRequest:
            raise TypeError("Exact WorkspaceRepositoryCommitRequest required")
        return self._provider.plan_repository_commit(request)

    def plan_repository_index_reconciliation(self, request):
        from .ports import WorkspaceRepositoryIndexReconcileRequest

        if type(request) is not WorkspaceRepositoryIndexReconcileRequest:
            raise TypeError("Exact WorkspaceRepositoryIndexReconcileRequest required")
        return self._provider.plan_repository_index_reconciliation(
            self._detached(request)
        )

    def verify_repository_index_reconciliation_plan(self, request):
        if type(request) is not WorkspaceRepositoryPlanVerificationRequest:
            raise TypeError("Exact WorkspaceRepositoryPlanVerificationRequest required")
        return self._detached(
            self._provider.verify_repository_index_reconciliation_plan(
                self._detached(request)
            )
        )

    def reconcile_repository_index(self, request, admission):
        from .ports import WorkspaceRepositoryIndexReconcileRequest

        if type(request) is not WorkspaceRepositoryIndexReconcileRequest:
            raise TypeError("Exact WorkspaceRepositoryIndexReconcileRequest required")
        return self._detached(
            self._provider.reconcile_repository_index(
                self._detached(request), admission
            )
        )

    def verify_repository_plan(
        self, request: WorkspaceRepositoryPlanVerificationRequest
    ):
        if type(request) is not WorkspaceRepositoryPlanVerificationRequest:
            raise TypeError("Exact WorkspaceRepositoryPlanVerificationRequest required")
        request = repository_publication_value_from_payload(
            type(request), repository_publication_value_to_payload(request)
        )
        return self._provider.verify_repository_plan(request)

    def observe_repository_attempt(self, request):
        from .values import WorkspaceRepositoryAttemptObserveRequest

        if type(request) is not WorkspaceRepositoryAttemptObserveRequest:
            raise TypeError("Exact WorkspaceRepositoryAttemptObserveRequest required")
        request = repository_publication_value_from_payload(
            type(request), repository_publication_value_to_payload(request)
        )
        value = self._provider.observe_repository_attempt(request)
        return self._detached(value)

    def observe_repository_publication(self, request):
        from .codec import WorkspacePublicationValueError
        from .ports import WorkspaceRepositoryPublicationObserveRequest

        if type(request) is not WorkspaceRepositoryPublicationObserveRequest:
            raise TypeError(
                "Exact WorkspaceRepositoryPublicationObserveRequest required"
            )
        request = self._detached(request)
        if (
            not request.repository_ref
            or re.fullmatch(
                r"git:(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})",
                request.publication_receipt_ref,
            )
            is None
            or request.expected_binding_ref == ""
        ):
            raise WorkspacePublicationValueError(
                "workspace_publication_observe_request_invalid"
            )
        return self._detached(self._provider.observe_repository_publication(request))

    def release_repository_plan(self, plan: WorkspaceRepositoryCommitPlan):
        return self._provider.release_repository_plan(plan)

    def publish_repository_commit(self, plan, admission):
        return self._detached(self._provider.publish_repository_commit(plan, admission))

    def finish_repository_publication(self, admission):
        return self._detached(self._provider.finish_repository_publication(admission))

    @staticmethod
    def _detached(value):
        return repository_publication_value_from_payload(
            type(value), repository_publication_value_to_payload(value)
        )

    def release_publication_work_admission(self, admission):
        return self._provider.release_publication_work_admission(admission)
