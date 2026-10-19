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

    @staticmethod
    def observe_filesystem_initial_git_identity(*, repository_root):
        """Explicit concrete readiness observation, never write/actor authority.

        Does not select or configure author metadata. Git interpretation stays
        with the original filesystem provider, not the neutral SDK/runtime.
        """
        from aware_workspace_fs_adapter.git_identity import observe_initial_git_identity

        return observe_initial_git_identity(repository_root=repository_root)

    def enroll_initial_authoring(self, preparation_client):
        """Explicit local-policy enrollment from this original fresh-root creator.

        Does not create an exact-effect admission, Issue lease or commit plan.
        """
        from aware_workspace_runtime.initial_authoring import (
            enroll_from_original_preparation,
        )

        return enroll_from_original_preparation(self._provider, preparation_client)

    def restore_initial_authoring_enrollment(self):
        """Reverify original retained enrollment, not reenroll an existing root."""
        from aware_workspace_runtime.initial_authoring import (
            restore_original_enrollment,
        )

        return restore_original_enrollment(self._provider)

    def observe_initial_authoring_request(self, kind):
        """Original retained request/result selection, never restored permission."""
        from aware_workspace_runtime.initial_authoring_selection import (
            observe_initial_authoring_request,
        )

        return observe_initial_authoring_request(self._provider, kind)

    def plan_initial_configuration(self, enrollment, protocol_plan, *, idempotency_key):
        from aware_workspace_runtime.initial_authoring import plan_initial_configuration

        return plan_initial_configuration(
            self._provider, enrollment, protocol_plan, idempotency_key
        )

    def admit_initial_configuration(self, plan):
        from aware_workspace_runtime.initial_authoring import (
            admit_initial_configuration,
        )

        return admit_initial_configuration(self._provider, plan)

    def publish_initial_configuration(self, admission):
        from aware_workspace_runtime.initial_authoring import (
            publish_initial_configuration,
        )

        return publish_initial_configuration(self._provider, admission)

    def recover_initial_configuration(self, protocol_plan, *, idempotency_key):
        from aware_workspace_runtime.initial_authoring import (
            recover_initial_configuration,
        )

        return recover_initial_configuration(
            self._provider, protocol_plan, idempotency_key
        )

    def project_initial_configuration(self, protocol_plan, *, idempotency_key):
        """Project only the retained original publication; never republish it.

        A partial projection remains uncertain and cannot be retried by adopting
        matching bytes. Protocol admission is a separate, subsequent operation.
        """
        from aware_workspace_runtime.initial_authoring import (
            project_initial_configuration,
        )

        return project_initial_configuration(
            self._provider, protocol_plan, idempotency_key
        )

    def observe_initial_configuration_projection(
        self, protocol_plan, *, idempotency_key
    ):
        from aware_workspace_runtime.initial_authoring import (
            project_initial_configuration,
        )

        return project_initial_configuration(
            self._provider, protocol_plan, idempotency_key, read_only=True
        )

    def plan_initial_project(self, source, *, idempotency_key):
        from aware_workspace_runtime.initial_authoring import plan_initial_project

        return plan_initial_project(self._provider, source, idempotency_key)

    def plan_initial_goal(self, source):
        from aware_workspace_runtime.initial_goal_publication import plan_initial_goal

        return plan_initial_goal(self._provider, source)

    def admit_initial_goal(self, plan):
        from aware_workspace_runtime.initial_goal_publication import admit_initial_goal

        return admit_initial_goal(self._provider, plan)

    def publish_initial_goal(self, admission):
        from aware_workspace_runtime.initial_goal_publication import (
            publish_initial_goal,
        )

        return publish_initial_goal(self._provider, admission)

    def recover_initial_goal(self, request):
        from aware_workspace_runtime.initial_goal_publication import (
            recover_initial_goal,
        )

        return recover_initial_goal(self._provider, request)

    def project_initial_goal(self, request):
        from aware_workspace_runtime.initial_goal_publication import (
            recover_initial_goal,
        )

        return recover_initial_goal(self._provider, request, project=True)

    def observe_initial_goal_projection(self, request):
        from aware_workspace_runtime.initial_goal_publication import (
            recover_initial_goal,
        )

        return recover_initial_goal(
            self._provider, request, project=True, read_only=True
        )

    def observe_initial_goal_source(
        self, project_request, *, resolver_capability, target_path
    ):
        """Read-only original-source context, never a creation admission."""
        from aware_workspace_runtime.initial_goal_source import (
            observe_initial_goal_source,
        )

        return observe_initial_goal_source(
            self._provider, project_request, resolver_capability, target_path
        )

    def authorize_initial_goal_intent(
        self, context, *, intent_payload, idempotency_key
    ):
        """Explicit intent permission, not exact-postimage/CAS work admission."""
        from aware_workspace_runtime.initial_goal_intent import (
            authorize_initial_goal_intent,
        )

        return authorize_initial_goal_intent(
            self._provider, context, intent_payload, idempotency_key
        )

    def observe_initial_goal_intent(self, context, *, intent_payload, idempotency_key):
        """Reread original issuance; never restore or extend live permission."""
        from aware_workspace_runtime.initial_goal_intent import (
            observe_initial_goal_intent,
        )

        return observe_initial_goal_intent(
            self._provider, context, intent_payload, idempotency_key
        )

    def prepare_initial_project_source(
        self,
        descriptor,
        *,
        resolver_capability,
        protocol_plan,
        configuration_idempotency_key,
    ):
        """Qualify an exact byte effect; Project independently owns its meaning."""
        from aware_workspace_runtime.initial_authoring import (
            prepare_initial_project_source,
        )

        return prepare_initial_project_source(
            self._provider,
            self,
            descriptor,
            resolver_capability,
            protocol_plan,
            configuration_idempotency_key,
        )

    def admit_initial_project(self, plan):
        from aware_workspace_runtime.initial_authoring import (
            admit_initial_configuration,
        )

        return admit_initial_configuration(self._provider, plan, _project=True)

    def publish_initial_project(self, admission):
        from aware_workspace_runtime.initial_authoring import (
            publish_initial_configuration,
        )

        return publish_initial_configuration(self._provider, admission, _project=True)

    def recover_initial_project(self, request):
        from aware_workspace_runtime.initial_authoring import recover_initial_project

        return recover_initial_project(self._provider, request)

    def project_initial_project(self, request):
        from aware_workspace_runtime.initial_authoring import recover_initial_project

        return recover_initial_project(self._provider, request, project=True)

    def observe_initial_project_projection(self, request):
        from aware_workspace_runtime.initial_authoring import recover_initial_project

        return recover_initial_project(
            self._provider, request, project=True, read_only=True
        )

    def plan_initial_membership(self, source, *, idempotency_key):
        """Plan exact initial member bytes; no admission or publication effect."""
        from aware_workspace_runtime.initial_membership import plan_initial_membership

        return plan_initial_membership(
            self._provider, source, idempotency_key=idempotency_key
        )

    def admit_initial_membership(self, plan):
        """Durably admit one exact effect; dispatch remains explicit."""
        from aware_workspace_runtime.initial_membership import admit_initial_membership

        return admit_initial_membership(self._provider, plan)

    def publish_initial_membership(self, admission):
        """Publish the admitted Project replacement; never install it."""
        from aware_workspace_runtime.initial_membership import (
            publish_initial_membership,
        )

        return publish_initial_membership(self._provider, admission)

    def recover_initial_membership(self, request):
        """Read original receipts; never restore permission or redispatch."""
        from aware_workspace_runtime.initial_membership import (
            recover_initial_membership,
        )

        return recover_initial_membership(self._provider, request)

    def project_initial_membership(self, request):
        from aware_workspace_runtime.initial_membership import (
            recover_initial_membership,
        )

        return recover_initial_membership(self._provider, request, project=True)

    def observe_initial_membership_projection(self, request):
        from aware_workspace_runtime.initial_membership import (
            recover_initial_membership,
        )

        return recover_initial_membership(
            self._provider, request, project=True, read_only=True
        )

    def observe_initial_membership_admission(self, request):
        """Observe original retention; never restore a live admission."""
        from aware_workspace_runtime.initial_membership import (
            observe_initial_membership_admission,
        )

        return observe_initial_membership_admission(self._provider, request)

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
