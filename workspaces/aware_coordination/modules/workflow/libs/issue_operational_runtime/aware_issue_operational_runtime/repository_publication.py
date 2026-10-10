"""Issue-owned single-use publication authority through supplying SDK only.

No Workspace implementation or Git IO. Original Workspace plan verification
and retained attempt evidence use its SDK outside the Issue registry lock.
Publication completion correlates the original retained Workspace attempt after
confirmed release. Parent-authorized lifecycle closeout remains separate.
"""

from __future__ import annotations

import hashlib
import os
import stat
import threading
from dataclasses import dataclass
from uuid import uuid4
from weakref import WeakKeyDictionary

from aware_issue_sdk.repository_publication import (
    IssueCloseAdmission,
    IssueCloseoutObservation,
    IssueCloseoutSourceObservation,
    IssuePublicationCleanupObservation,
    IssueRepositoryFileIdentity,
    IssueRepositoryPublicationAdmission,
    IssueRepositoryPublicationAdmissionObservation,
    IssueRepositoryPublicationEnrollment,
    IssueRepositoryPublicationLease,
    IssueRepositoryPublicationRefusal,
    _issue_publication_handle,
)

from .source_scope_policy import evaluate_issue_source_scope

_SOURCE_PORT_TYPES = set()


def _repository_presentation_status(request, result, observation, cleanup, failure):
    """One presentation gate over existing owner evidence, not an admission."""
    complete = (
        failure is None
        and observation is not None
        and observation.ledger_complete
        and all(c.ledger_complete and c.cleanup_state == "completed" for c in cleanup)
        and (
            result is None
            or (
                result.publication_state == "published"
                and result.ledger_complete
                and result.admission_completion == "completed"
                and result.index_projection == "applied"
                and result.index_reconciliation_pending is False
                and result.lock_release is not None
                and result.lock_release.repository_lock_release == "confirmed_released"
                and type(result.commit_hash) is str
                and len(result.commit_hash) in (40, 64)
                and all(c in "0123456789abcdef" for c in result.commit_hash)
            )
        )
    )
    dry_run = getattr(request, "dry_run", False)
    if dry_run and result is not None:
        complete = False
    if not dry_run and (
        result is None
        or observation is None
        or observation.completion_state != "completed"
    ):
        complete = False
    outcome = (
        "refused"
        if failure is not None
        else "planned"
        if complete and dry_run
        else "completed"
        if complete
        else "incomplete"
    )
    return outcome, complete


def validate_repository_operation_result(request, payload):
    """Validate complete presentation through owner codecs without IO or authority.

    This shares the renderer's label gate; it never re-evaluates Issue policy,
    recaptures history, finishes an admission or retries a physical effect.
    """
    from aware_issue_sdk.repository_publication import (
        repository_publication_value_from_payload as issue_value,
    )
    from aware_workspace_sdk.repository_publication import (
        repository_publication_value_from_payload as workspace_value,
    )
    from aware_workspace_sdk.repository_publication.values import (
        WorkspacePublicationCleanupObservation,
        WorkspacePublicationPlanObservation,
        WorkspaceRepositoryAttemptObservation,
        WorkspaceRepositoryCommitResult,
    )

    if type(payload) is not dict or set(payload) != {
        "contract",
        "operation_ref",
        "issue_ref",
        "outcome",
        "code",
        "diagnostics",
        "authorizes_retry",
        "authority_restored",
        "ledger_complete",
        "workspace_result",
        "workspace_observation",
        "issue_observation",
        "cleanup_observations",
    }:
        raise ValueError("repository_presentation_fields_invalid")
    if (
        payload["contract"] != "aware.issue.repository-operation.v2"
        or payload["operation_ref"] != request.operation_ref
        or payload["issue_ref"] != request.issue_ref
        or payload["authorizes_retry"] is not False
        or payload["authority_restored"] is not False
        or type(payload["ledger_complete"]) is not bool
        or type(payload["diagnostics"]) is not list
        or any(type(d) is not str for d in payload["diagnostics"])
        or (
            payload["code"] is not None
            and (type(payload["code"]) is not str or not payload["code"].strip())
        )
        or type(payload["cleanup_observations"]) is not list
    ):
        raise ValueError("repository_presentation_header_invalid")
    result = (
        None
        if payload["workspace_result"] is None
        else workspace_value(
            WorkspaceRepositoryCommitResult, payload["workspace_result"]
        )
    )
    if payload["workspace_observation"] is not None:
        workspace_value(
            WorkspaceRepositoryAttemptObservation, payload["workspace_observation"]
        )
    observation = (
        None
        if payload["issue_observation"] is None
        else issue_value(
            IssueCloseoutObservation
            if request.operation_ref == "issue_sdk.close_issue"
            else IssueRepositoryPublicationAdmissionObservation,
            payload["issue_observation"],
        )
    )
    if observation is not None and observation.issue_ref != request.issue_ref:
        raise ValueError("repository_presentation_issue_correlation_invalid")
    cleanup = []
    for item in payload["cleanup_observations"]:
        # The existing codecs, not a copied schema, distinguish original owners.
        for kind, decode in (
            (IssuePublicationCleanupObservation, issue_value),
            (WorkspacePublicationCleanupObservation, workspace_value),
            (WorkspacePublicationPlanObservation, workspace_value),
        ):
            try:
                decoded = decode(kind, item)
            except ValueError:
                continue
            cleanup.append(decoded)
            break
        else:
            raise ValueError("repository_presentation_cleanup_invalid")
    outcome, complete = _repository_presentation_status(
        request, result, observation, cleanup, payload["code"]
    )
    if payload["outcome"] != outcome or payload["ledger_complete"] is not complete:
        raise ValueError("repository_presentation_outcome_inconsistent")


def _execution():
    identities = [
        (provider, os.environ.get(key, "").strip())
        for provider, key in (
            ("codex", "CODEX_THREAD_ID"),
            ("claude_code", "CLAUDE_CODE_SESSION_ID"),
        )
        if os.environ.get(key, "").strip()
    ]
    if len(identities) != 1 or any(
        c.isspace() for _, value in identities for c in value
    ):
        raise IssueRepositoryPublicationRefusal(
            "provider_execution_identity_unavailable"
        )
    return "-".join(identities[0])


@dataclass
class _AdmissionState:
    request: object
    source: object
    receipt: str
    phase: str = "admitted"
    enrollment_receipt: str | None = None
    lease_receipt: str | None = None
    consumer: str | None = None
    purpose: str = "repository_publication"
    consumption: str = "not_consumed"
    completion: str = "not_attempted"
    publication: object = None
    diagnostics: tuple[str, ...] = ()
    released: bool = False
    close_parent: object = None


@dataclass
class _CloseState:
    request: object
    attempt: str
    source: object
    candidate: bytes
    receipt: str
    physical: object = None
    phase: str = "preparing"
    post_source: object = None
    source_observation: object = None
    child: object = None
    completion: str = "not_attempted"
    cleanup: str = "not_attempted"
    cleanup_attempted: bool = False
    diagnostics: tuple[str, ...] = ()
    released: bool = False


@dataclass
class _RepositoryOperation:
    plan: object = None
    binding: object = None
    admission: object = None
    work: object = None
    parent: object = None
    result: object = None
    workspace_observation: object = None
    cleanup: tuple = ()
    publication_invoked: bool = False
    issue_observation: object = None
    diagnostics: tuple[str, ...] = ()


class IssueRepositoryPublicationRuntime:
    def __init__(self, *, source_port, workspace_client):
        from aware_workspace_sdk.repository_publication.authority import (
            WorkspaceRepositoryPublicationClient,
        )

        if type(workspace_client) is not WorkspaceRepositoryPublicationClient:
            raise TypeError("Original supplying Workspace SDK client required")
        if type(source_port) not in _SOURCE_PORT_TYPES:
            raise TypeError("Selected original Issue physical port required")
        self._source = source_port
        self._workspace = workspace_client
        self._execution = _execution()
        self._pid = os.getpid()
        self._ref = "issue-publication:" + uuid4().hex
        self._generation = uuid4().hex
        self._lock = threading.RLock()
        self._handles = WeakKeyDictionary()
        self._attempts = set()
        self._close_handles = WeakKeyDictionary()
        # Retain original, non-reconstructed admissions for subsequent closeout
        # in this exact runtime. This is not a durable/restart authority store.
        self._repository_operations = []

    def _operation_workspace_observation(self, operation):
        from aware_workspace_sdk.repository_publication.values import (
            WorkspaceRepositoryAttemptObserveRequest,
        )

        if operation.binding is None:
            return
        b = operation.binding
        observation = self._workspace.observe_repository_attempt(
            WorkspaceRepositoryAttemptObserveRequest(
                b.repository_ref,
                b.binding_ref,
                b.attempt_ref,
                b.provider_ref,
                b.provider_generation,
                b.execution_id,
            )
        )
        operation.workspace_observation = observation
        if operation.result is None and observation.result is not None:
            operation.result = observation.result

    def _operation_cleanup(self, operation):
        """Release original local holders, never retry transaction cleanup/write.

        Workspace publication owns its transaction and physical release. Its
        work/plan release ports only retire logical authority; they must not be
        confused with retrying an unknown physical release.
        """
        errors = []
        ports = []
        if operation.work is not None:
            ports.append(
                (self._workspace.release_publication_work_admission, operation.work)
            )
        elif operation.admission is not None:
            ports.append(
                (self.release_repository_publication_admission, operation.admission)
            )
        if operation.parent is not None:
            ports.append((self.release_repository_closeout, operation.parent))
        if operation.plan is not None:
            ports.append((self._workspace.release_repository_plan, operation.plan))
        for port, original in ports:
            try:
                operation.cleanup += (port(original),)
            except BaseException as error:  # noqa: BLE001 - cleanup failure never erases publication
                errors.append(error)
        return tuple(errors)

    def _operation_failure(self, operation, error, cleanup_errors):
        diagnostics = tuple(type(item).__name__ for item in cleanup_errors)
        observation = operation.issue_observation
        # A genuine supplier refusal may have captured effects after our last
        # snapshot. Retain that evidence before any fallible owner recapture.
        if (
            isinstance(error, IssueRepositoryPublicationRefusal)
            and error.observation is not None
        ):
            observation = error.observation
        try:
            if operation.parent is not None:
                with self._lock:
                    state = self._close_state(operation.parent)
                    if diagnostics:
                        state.diagnostics += tuple(
                            "orchestration_cleanup:" + code for code in diagnostics
                        )
                    observation = self._close_observation(state)
            elif operation.admission is not None:
                with self._lock:
                    state = self._state(
                        operation.admission, IssueRepositoryPublicationAdmission
                    )
                    if diagnostics:
                        state.diagnostics += tuple(
                            "orchestration_cleanup:" + code for code in diagnostics
                        )
                    observation = self._observation(state)
        except BaseException as capture_error:  # noqa: BLE001 - keep full Workspace evidence
            from dataclasses import replace

            operation.diagnostics += (
                "issue_observation_unavailable:" + type(capture_error).__name__,
            )
            if observation is not None:
                observation = replace(observation, ledger_complete=False)
        code = getattr(error, "code", "issue_repository_orchestration_unavailable")
        return IssueRepositoryPublicationRefusal(
            code,
            observation=observation,
            workspace_observation=operation.workspace_observation,
            workspace_result=operation.result,
            cleanup_observations=operation.cleanup,
            diagnostics=(*operation.diagnostics, *diagnostics),
        )

    def _operation_enroll(self, operation):
        from aware_issue_sdk.repository_publication import (
            IssueRepositoryPublicationClient,
        )
        from aware_workspace_sdk.repository_publication.authority import (
            WorkspaceIssuePublicationEnrollmentClient,
        )

        operation.work = WorkspaceIssuePublicationEnrollmentClient(
            workspace_client=self._workspace,
            issue_client=IssueRepositoryPublicationClient(self),
        ).enroll_issue_repository_publication(operation.plan, operation.admission)

    def _operation_result(self, request, call):
        """Lossless consumer data through original supplying SDK codecs."""
        import json

        from aware_issue_sdk.repository_publication import (
            IssueRepositoryOperationResult,
        )
        from aware_issue_sdk.repository_publication import (
            repository_publication_value_to_payload as issue_payload,
        )
        from aware_workspace_sdk.repository_publication import (
            repository_publication_value_to_payload as workspace_payload,
        )

        failure = None
        workspace_observation = None
        diagnostics = ()
        try:
            result, observation, cleanup = call(request)
        except IssueRepositoryPublicationRefusal as error:
            failure = error.code
            result, observation, cleanup = (
                error.workspace_result,
                error.observation,
                error.cleanup_observations,
            )
            workspace_observation = error.workspace_observation
            diagnostics = error.diagnostics
        outcome, complete = _repository_presentation_status(
            request, result, observation, cleanup, failure
        )
        payload = {
            "contract": "aware.issue.repository-operation.v2",
            "operation_ref": request.operation_ref,
            "issue_ref": request.issue_ref,
            "outcome": outcome,
            "code": failure,
            "diagnostics": list(diagnostics),
            "authorizes_retry": False,
            "authority_restored": False,
            "ledger_complete": complete,
            "workspace_result": None if result is None else workspace_payload(result),
            "workspace_observation": None
            if workspace_observation is None
            else workspace_payload(workspace_observation),
            "issue_observation": None
            if observation is None
            else issue_payload(observation),
            "cleanup_observations": [
                issue_payload(c)
                if type(c) is IssuePublicationCleanupObservation
                else workspace_payload(c)
                for c in cleanup
            ],
        }
        return IssueRepositoryOperationResult(json.dumps(payload, allow_nan=False))

    def commit_workspace_result(self, request):
        return self._operation_result(request, self.commit_workspace)

    def close_issue_result(self, request):
        return self._operation_result(request, self.close_issue)

    def commit_workspace(self, request):
        from aware_issue_sdk.repository_publication import (
            IssueRepositoryPublicationRequest,
        )
        from aware_workspace_sdk.repository_publication.values import (
            WorkspaceRepositoryCommitRequest,
        )

        operation = _RepositoryOperation()
        error = None
        try:
            self._current()
            if request.actor_ref != self._execution:
                raise IssueRepositoryPublicationRefusal(
                    "issue_publication_execution_mismatch"
                )
            source = self._source.observe(request.issue_ref)
            if source.digest != request.expected_issue_source_sha256:
                raise IssueRepositoryPublicationRefusal(
                    "issue_publication_source_stale"
                )
            decision = evaluate_issue_source_scope(
                issue_owner=source.owner,
                issue_status=source.status,
                scope_paths=source.scope,
                actor_ref=self._execution,
                effect_paths=request.target_paths,
            )
            if not decision.allowed:
                raise IssueRepositoryPublicationRefusal(decision.refusal.value)
            operation.plan = self._workspace.plan_repository_commit(
                WorkspaceRepositoryCommitRequest(
                    source.repository_ref,
                    request.target_paths,
                    request.message,
                    "issue-repository-attempt:" + uuid4().hex,
                )
            )
            operation.binding = operation.plan.binding
            operation.admission = self.admit_repository_publication(
                IssueRepositoryPublicationRequest(
                    request.issue_ref,
                    source.digest,
                    self._issue_binding(operation.binding),
                )
            )
            operation.issue_observation = self.observe_repository_publication_admission(
                operation.admission
            )
            if not request.dry_run:
                self._operation_enroll(operation)
                operation.publication_invoked = True
                operation.result = self._workspace.publish_repository_commit(
                    operation.plan, operation.work
                )
                self._operation_workspace_observation(operation)
        except BaseException as caught:  # noqa: BLE001 - terminal read/write failure retains evidence
            error = caught
            try:
                self._operation_workspace_observation(operation)
            except BaseException as read_error:  # noqa: BLE001 - no diagnostic Git fallback
                operation.diagnostics += (
                    "workspace_observation_unavailable:" + type(read_error).__name__,
                )
        cleanup_errors = self._operation_cleanup(operation)
        with self._lock:
            self._repository_operations.append(operation)
        if error is not None or cleanup_errors:
            failure_error = error if error is not None else cleanup_errors[0]
            failure = self._operation_failure(operation, failure_error, cleanup_errors)
            raise failure from failure_error
        try:
            operation.issue_observation = self.observe_repository_publication_admission(
                operation.admission
            )
            return operation.result, operation.issue_observation, operation.cleanup
        except BaseException as capture_error:
            raise self._operation_failure(
                operation, capture_error, ()
            ) from capture_error

    def close_issue(self, request):
        from aware_workspace_sdk.repository_publication.values import (
            WorkspaceRepositoryCommitRequest,
        )

        operation = _RepositoryOperation()
        error = None
        try:
            self._current()
            attempt = "issue-closeout-attempt:" + uuid4().hex
            operation.parent = self.prepare_repository_closeout(request, attempt)
            with self._lock:
                operation.issue_observation = self._close_observation(
                    self._close_state(operation.parent)
                )
            source = self.apply_repository_closeout_source(operation.parent)
            with self._lock:
                state = self._close_state(operation.parent)
                operation.issue_observation = self._close_observation(state)
                repository = state.source.repository_ref
            operation.plan = self._workspace.plan_repository_commit(
                WorkspaceRepositoryCommitRequest(
                    repository,
                    (source.source_path,),
                    "Close " + request.issue_ref,
                    attempt,
                )
            )
            operation.binding = operation.plan.binding
            operation.admission = self.bind_closeout_publication(
                operation.parent, self._issue_binding(operation.binding)
            )
            self._operation_enroll(operation)
            operation.publication_invoked = True
            operation.result = self._workspace.publish_repository_commit(
                operation.plan, operation.work
            )
            self._operation_workspace_observation(operation)
            child = self.observe_repository_publication_admission(operation.admission)
            if (
                child.completion_state == "completed"
                and child.publication is not None
                and child.publication.publication_state == "published"
            ):
                self.finish_repository_closeout(operation.parent, child.publication)
            else:
                with self._lock:
                    self._close_state(operation.parent).completion = "pending"
        except BaseException as caught:  # noqa: BLE001 - source and publication effects survive refusal
            error = caught
            try:
                self._operation_workspace_observation(operation)
            except BaseException as read_error:  # noqa: BLE001 - no source compensation from missing evidence
                operation.diagnostics += (
                    "workspace_observation_unavailable:" + type(read_error).__name__,
                )
        cleanup_errors = self._operation_cleanup(operation)
        with self._lock:
            self._repository_operations.append(operation)
        if error is not None or cleanup_errors:
            failure_error = error if error is not None else cleanup_errors[0]
            failure = self._operation_failure(operation, failure_error, cleanup_errors)
            raise failure from failure_error
        try:
            with self._lock:
                operation.issue_observation = self._close_observation(
                    self._close_state(operation.parent)
                )
            return operation.result, operation.issue_observation, operation.cleanup
        except BaseException as capture_error:
            raise self._operation_failure(
                operation, capture_error, ()
            ) from capture_error

    def _current(self):
        if os.getpid() != self._pid:
            raise IssueRepositoryPublicationRefusal(
                "issue_publication_cross_process_refused"
            )
        if _execution() != self._execution:
            raise IssueRepositoryPublicationRefusal(
                "issue_publication_execution_changed"
            )

    def _state(self, handle, expected):
        if os.getpid() != self._pid:
            raise IssueRepositoryPublicationRefusal(
                "issue_publication_cross_process_refused"
            )
        if type(handle) is not expected or handle not in self._handles:
            raise IssueRepositoryPublicationRefusal(
                "issue_publication_original_handle_required"
            )
        return self._handles[handle]

    def _handle_phase(self, handle):
        with self._lock:
            if type(handle) is IssueCloseAdmission:
                return self._close_state(handle).phase
            return self._state(handle, type(handle)).phase

    def _close_state(self, handle):
        if os.getpid() != self._pid:
            raise IssueRepositoryPublicationRefusal(
                "issue_publication_cross_process_refused"
            )
        if type(handle) is not IssueCloseAdmission or handle not in self._close_handles:
            raise IssueRepositoryPublicationRefusal(
                "issue_closeout_original_parent_required"
            )
        return self._close_handles[handle]

    def _close_observation(self, state):
        child = self._observation(state.child) if state.child is not None else None
        publication = child.publication if child is not None else None
        return IssueCloseoutObservation(
            state.request.issue_ref,
            self._ref,
            self._generation,
            self._execution,
            "issue-closeout-observation:" + uuid4().hex,
            state.attempt,
            state.receipt,
            state.request.publication_receipt_ref,
            publication.publication_receipt_ref if publication is not None else None,
            state.source_observation,
            child,
            state.completion,
            not state.diagnostics
            and (
                state.source_observation is None
                or state.source_observation.ledger_complete
            )
            and (
                child is None
                or (
                    child.ledger_complete
                    and (
                        child.consumption_state == "not_consumed"
                        or (
                            child.publication is not None
                            and child.publication.ledger_complete
                        )
                    )
                )
            ),
            state.diagnostics,
        )

    def _refresh_close_publication(self, state):
        from dataclasses import astuple

        from aware_issue_sdk.repository_publication import (
            IssueRepositoryPublicationEffectObservation,
            repository_publication_value_from_payload,
        )
        from aware_workspace_sdk.repository_publication import (
            WorkspaceRepositoryAttemptObserveRequest,
            repository_publication_value_to_payload,
        )

        child = state.child
        if child is None or child.completion == "completed":
            return
        binding = child.request.binding
        try:
            # Lock-free original-owner observation, outside the Issue lock.
            # This retains failed/unknown results, but never invokes finish.
            original = self._workspace.observe_repository_attempt(
                WorkspaceRepositoryAttemptObserveRequest(
                    binding.repository_ref,
                    binding.workspace_binding_ref,
                    binding.attempt_ref,
                    binding.workspace_provider_ref,
                    binding.workspace_provider_generation,
                    binding.execution_id,
                )
            )
            if not original.attempt_recognized or original.result is None:
                raise IssueRepositoryPublicationRefusal(
                    "issue_closeout_publication_ledger_unavailable"
                )
            payload = repository_publication_value_to_payload(original.result)
            for key in (
                "outcome",
                "original_writer_report",
                "binding_ref",
                "attempt_ref",
            ):
                payload.pop(key)
            payload["binding"] = dict(
                zip(binding.__dataclass_fields__, astuple(binding), strict=True)
            )
            payload["binding"]["target_paths"] = list(
                payload["binding"]["target_paths"]
            )
            payload["workspace_observation_ref"] = original.observation_ref
            payload["publication_receipt_ref"] = (
                "git:" + original.result.commit_hash
                if original.result.commit_hash
                else None
            )
            effect = repository_publication_value_from_payload(
                IssueRepositoryPublicationEffectObservation,
                payload,
            )
            if effect.work_admission_receipt_ref != child.lease_receipt:
                raise IssueRepositoryPublicationRefusal(
                    "issue_closeout_publication_correlation_mismatch"
                )
            with self._lock:
                previous = child.publication
                from dataclasses import replace

                if previous is not None and previous != replace(
                    effect, workspace_observation_ref=previous.workspace_observation_ref
                ):
                    raise IssueRepositoryPublicationRefusal(
                        "issue_closeout_publication_history_changed"
                    )
                child.publication = effect
        except BaseException as error:  # noqa: BLE001 - evidence cannot renew a spent child
            with self._lock:
                state.diagnostics += (
                    getattr(
                        error, "code", "issue_closeout_publication_ledger_unavailable"
                    ),
                )

    def _capture_close_source(self, state):
        previous = state.source_observation
        try:
            effects = state.physical.effects
            effect = next((e for e in reversed(effects) if e.kind == "manifest"), None)
            effect_state = (
                "not_attempted"
                if effect is None
                else {
                    "none": "not_attempted",
                    "applied": "applied",
                    "unknown": "unknown",
                }.get(effect.state.value, "failed")
            )
            after_identity = (
                IssueRepositoryFileIdentity(*effect.after_identity)
                if effect is not None and effect.after_identity is not None
                else None
            )
            cleanup = state.cleanup
            state.source_observation = IssueCloseoutSourceObservation(
                state.request.issue_ref,
                self._ref,
                self._generation,
                self._execution,
                "issue-closeout-source:" + uuid4().hex,
                state.attempt,
                state.receipt,
                state.source.path,
                effect_state,
                state.source.digest,
                effect.after_digest if effect is not None else None,
                IssueRepositoryFileIdentity(*state.source.identity[:2]),
                after_identity,
                stat.S_IMODE(state.source.identity[2]),
                effect.mode if effect is not None else None,
                effect.durability_confirmed if effect is not None else None,
                cleanup,
                effect_state != "unknown" and cleanup != "unknown",
                (),
            )
        except BaseException as error:  # noqa: BLE001 - unknown reads retain prior effects
            # Evidence loss cannot erase an already recorded replacement.
            from dataclasses import replace

            if previous is not None:
                state.source_observation = replace(
                    previous,
                    ledger_complete=False,
                    diagnostics=(
                        *previous.diagnostics,
                        "issue_closeout_source_ledger_unavailable",
                    ),
                )
            else:
                state.source_observation = IssueCloseoutSourceObservation(
                    state.request.issue_ref,
                    self._ref,
                    self._generation,
                    self._execution,
                    "issue-closeout-source:" + uuid4().hex,
                    state.attempt,
                    state.receipt,
                    state.source.path,
                    "unknown",
                    state.source.digest,
                    None,
                    IssueRepositoryFileIdentity(*state.source.identity[:2]),
                    None,
                    stat.S_IMODE(state.source.identity[2]),
                    None,
                    None,
                    "unknown",
                    False,
                    ("issue_closeout_source_ledger_unavailable",),
                )
            state.diagnostics += (
                "issue_closeout_source_ledger_unavailable:" + type(error).__name__,
            )

    def _cleanup_close(self, state):
        if state.cleanup_attempted:
            return
        state.cleanup_attempted = True
        previous = state.cleanup
        state.cleanup = "unknown"
        try:
            if state.physical is not None:
                state.physical.release()
            state.cleanup = "unknown" if previous == "unknown" else "completed"
        except BaseException as error:  # noqa: BLE001 - interrupted disposal is not success
            state.diagnostics += (
                "issue_closeout_cleanup_unavailable:" + type(error).__name__,
            )

    def _refuse_close(self, state, error):
        with self._lock:
            state.phase = "refused"
            code = getattr(error, "code", "issue_closeout_owner_unavailable")
            state.diagnostics += (code,)
            self._cleanup_close(state)
            return IssueRepositoryPublicationRefusal(
                code, observation=self._close_observation(state)
            )

    def prepare_repository_closeout(self, request, attempt_ref):
        from aware_issue_sdk import (
            append_update_line,
            parse_issue_document_text,
            render_issue_document,
            set_header_value,
            set_resolution,
            set_verified_by,
        )
        from aware_workspace_sdk.repository_publication.ports import (
            WorkspaceRepositoryPublicationObserveRequest,
        )

        state = None
        try:
            self._current()
            source = self._source.observe(request.issue_ref)
            if source.digest != request.expected_source_sha256:
                raise IssueRepositoryPublicationRefusal("issue_closeout_source_stale")
            if request.actor_ref != self._execution:
                raise IssueRepositoryPublicationRefusal(
                    "issue_closeout_execution_mismatch"
                )
            decision = evaluate_issue_source_scope(
                issue_owner=source.owner,
                issue_status=source.status,
                scope_paths=source.scope,
                actor_ref=self._execution,
                effect_paths=(source.path,),
            )
            if not decision.allowed:
                raise IssueRepositoryPublicationRefusal(decision.refusal.value)
            # Physical Git facts are necessary but not completion authority.
            original = self._workspace.observe_repository_publication(
                WorkspaceRepositoryPublicationObserveRequest(
                    source.repository_ref,
                    request.publication_receipt_ref,
                    None,
                )
            )
            result = original.result
            if (
                not original.ledger_complete
                or original.binding is None
                or result is None
                or result.publication_state != "published"
                or result.admission_completion != "completed"
                or original.receipt_state != "present"
                or original.reachability_state != "reachable"
            ):
                raise IssueRepositoryPublicationRefusal(
                    "issue_closeout_original_implementation_required"
                )
            with self._lock:
                recognized = any(
                    value.request.issue_ref == request.issue_ref
                    and value.request.binding == self._issue_binding(original.binding)
                    and value.completion == "completed"
                    and value.publication is not None
                    and value.publication.publication_receipt_ref
                    == request.publication_receipt_ref
                    for value in self._handles.values()
                )
                if not recognized:
                    raise IssueRepositoryPublicationRefusal(
                        "issue_closeout_original_issue_completion_required"
                    )
                if attempt_ref in self._attempts:
                    raise IssueRepositoryPublicationRefusal(
                        "issue_publication_attempt_already_admitted"
                    )
                self._attempts.add(attempt_ref)
                document = parse_issue_document_text(text=source.body.decode("utf-8"))
                set_resolution(document=document, resolution=request.resolution)
                set_verified_by(
                    document=document,
                    entries=(*request.verified_by, request.publication_receipt_ref),
                )
                set_header_value(document=document, field="Status", value="Closed")
                append_update_line(
                    document=document,
                    line=(
                        f"- Applied `{request.operation_ref}`. (recorder: `{self._execution}`)"
                    ),
                )
                state = _CloseState(
                    request,
                    attempt_ref,
                    source,
                    render_issue_document(document=document).encode("utf-8"),
                    "issue-close-admission:" + uuid4().hex,
                )
            state.physical = self._source.retain_closeout(source, state.candidate)
            # Retain the genuine original before any subsequent read can
            # refuse, so failed issuance retains cleanup responsibility.
            self._source.validate_closeout(source, state.physical)
            with self._lock:
                self._current()
                handle = _issue_publication_handle(self, IssueCloseAdmission)
                state.phase = "prepared"
                self._close_handles[handle] = state
                return handle
        except BaseException as error:
            if state is not None:
                raise self._refuse_close(state, error) from error
            if isinstance(error, IssueRepositoryPublicationRefusal):
                raise
            raise IssueRepositoryPublicationRefusal(
                getattr(error, "code", "issue_closeout_preparation_unavailable")
            ) from error

    @staticmethod
    def _issue_binding(binding):
        from dataclasses import astuple

        from aware_issue_sdk.repository_publication import (
            IssueRepositoryPublicationBinding,
        )

        return IssueRepositoryPublicationBinding(*astuple(binding))

    def apply_repository_closeout_source(self, close_admission):
        with self._lock:
            state = self._close_state(close_admission)
            if state.phase != "prepared" or state.released:
                raise IssueRepositoryPublicationRefusal(
                    "issue_closeout_parent_terminal",
                    observation=self._close_observation(state),
                )
            state.phase = "applying"
        try:
            self._current()
            state.post_source = self._source.apply_closeout(
                state.source, state.physical
            )
            state.cleanup = "completed"
            self._capture_close_source(state)
            if (
                state.source_observation is None
                or not state.source_observation.ledger_complete
            ):
                raise IssueRepositoryPublicationRefusal(
                    "issue_closeout_complete_source_ledger_required"
                )
            self._validate_close_postimage(state)
            with self._lock:
                self._current()
                if state.phase != "applying" or state.released:
                    raise IssueRepositoryPublicationRefusal(
                        "issue_closeout_application_cancelled"
                    )
                state.phase = "applied"
                return state.source_observation
        except BaseException as error:
            if state.cleanup != "completed":
                state.cleanup = "unknown"
            self._capture_close_source(state)
            raise self._refuse_close(state, error) from error

    def _validate_close_postimage(self, state):
        source = self._source.observe(state.request.issue_ref)
        if (
            state.post_source is None
            or source != state.post_source
            or source.digest != "sha256:" + hashlib.sha256(state.candidate).hexdigest()
            or source.status != "closed"
            or source.owner != state.source.owner
            or source.scope != state.source.scope
            or source.path != state.source.path
            or source.manifest_digest != state.source.manifest_digest
        ):
            raise IssueRepositoryPublicationRefusal("issue_closeout_postimage_stale")
        return source

    def bind_closeout_publication(self, close_admission, binding):
        from aware_issue_sdk.repository_publication import (
            IssueRepositoryPublicationRequest,
        )

        with self._lock:
            state = self._close_state(close_admission)
            if state.phase != "applied" or state.released or state.child is not None:
                raise IssueRepositoryPublicationRefusal(
                    "issue_closeout_parent_terminal",
                    observation=self._close_observation(state),
                )
            if (
                binding.attempt_ref != state.attempt
                or binding.repository_ref != state.source.repository_ref
                or binding.target_paths != (state.source.path,)
                or binding.execution_id != self._execution
            ):
                raise IssueRepositoryPublicationRefusal(
                    "issue_closeout_binding_mismatch"
                )
            state.phase = "binding"
        try:
            self._current()
            self._verify_plan(binding)
            source = self._validate_close_postimage(state)
            with self._lock:
                self._current()
                if state.phase != "binding" or state.released:
                    raise IssueRepositoryPublicationRefusal(
                        "issue_closeout_binding_cancelled"
                    )
                child = _AdmissionState(
                    IssueRepositoryPublicationRequest(
                        state.request.issue_ref, source.digest, binding
                    ),
                    source,
                    "issue-publication-admission:" + uuid4().hex,
                    purpose="issue_closeout_publication",
                    close_parent=state,
                )
                handle = _issue_publication_handle(
                    self, IssueRepositoryPublicationAdmission
                )
                state.child, state.phase = child, "bound"
                self._handles[handle] = child
                return handle
        except BaseException as error:
            raise self._refuse_close(state, error) from error

    def finish_repository_closeout(self, close_admission, observation):
        with self._lock:
            state = self._close_state(close_admission)
        self._refresh_close_publication(state)
        with self._lock:
            state = self._close_state(close_admission)
            child = state.child
            if (
                state.released
                or state.phase not in {"bound", "completed"}
                or child is None
            ):
                raise IssueRepositoryPublicationRefusal(
                    "issue_closeout_parent_terminal",
                    observation=self._close_observation(state),
                )
            if (
                child.completion != "completed"
                or child.publication != observation
                or observation.publication_state != "published"
                or observation.publication_receipt_ref is None
            ):
                state.completion = "pending"
                raise IssueRepositoryPublicationRefusal(
                    "issue_closeout_original_completion_required",
                    observation=self._close_observation(state),
                )
        try:
            self._current()
            # The child completed through genuine original Workspace evidence
            # only after confirmed unlock; this read grants no new publication.
            self._validate_close_postimage(state)
            with self._lock:
                self._current()
                if state.released:
                    raise IssueRepositoryPublicationRefusal(
                        "issue_closeout_completion_cancelled"
                    )
                state.phase, state.completion = "completed", "completed"
                return self._close_observation(state)
        except BaseException as error:
            with self._lock:
                state.completion = "pending"
                state.diagnostics += (getattr(error, "code", type(error).__name__),)
            raise IssueRepositoryPublicationRefusal(
                getattr(error, "code", "issue_closeout_completion_unavailable"),
                observation=self._close_observation(state),
            ) from error

    def release_repository_closeout(self, close_admission):
        with self._lock:
            state = self._close_state(close_admission)
            if state.phase in {"applying", "binding"}:
                raise IssueRepositoryPublicationRefusal(
                    "issue_closeout_effect_in_progress"
                )
        self._refresh_close_publication(state)
        with self._lock:
            state = self._close_state(close_admission)
            if state.phase in {"applying", "binding"}:
                raise IssueRepositoryPublicationRefusal(
                    "issue_closeout_effect_in_progress"
                )
            state.released, state.phase = True, "released"
            if state.child is not None:
                state.child.released, state.child.phase = True, "released"
                if (
                    state.child.consumption == "consumed"
                    and state.child.completion != "completed"
                ):
                    state.child.completion = "pending"
            self._cleanup_close(state)
            if state.completion != "completed" and state.source_observation is not None:
                state.completion = "pending"
            return IssuePublicationCleanupObservation(
                state.request.issue_ref,
                self._ref,
                self._generation,
                self._execution,
                "issue-closeout-cleanup:" + uuid4().hex,
                state.attempt,
                state.receipt,
                "released" if state.cleanup == "completed" else "unknown",
                state.cleanup,
                state.child.publication if state.child is not None else None,
                state.source_observation,
                state.cleanup == "completed"
                and not state.diagnostics
                and (
                    state.child is None
                    or state.child.consumption == "not_consumed"
                    or (
                        state.child.publication is not None
                        and state.child.publication.ledger_complete
                    )
                ),
                state.diagnostics,
            )

    def _lease_receipt(self, lease):
        with self._lock:
            return self._state(lease, IssueRepositoryPublicationLease).lease_receipt

    def _workspace_binding(self, binding):
        from aware_workspace_sdk.repository_publication.values import (
            WorkspaceRepositoryPublicationBinding,
        )

        return WorkspaceRepositoryPublicationBinding(
            binding.workspace_binding_ref,
            binding.attempt_ref,
            binding.repository_ref,
            binding.publication_reference,
            binding.expected_head,
            binding.target_paths,
            binding.postimages_digest,
            binding.message_digest,
            binding.workspace_provider_generation,
            binding.workspace_provider_ref,
            binding.execution_id,
        )

    def _verify_plan(self, binding, *, purpose="repository_publication"):
        from aware_workspace_sdk.repository_publication.values import (
            WorkspaceRepositoryPlanVerificationRequest,
        )

        verification = (
            self._workspace.verify_repository_index_reconciliation_plan
            if purpose == "index_reconciliation"
            else self._workspace.verify_repository_plan
        )
        verified = verification(
            WorkspaceRepositoryPlanVerificationRequest(self._workspace_binding(binding))
        )
        if (
            not verified.original_plan_recognized
            or verified.binding != self._workspace_binding(binding)
        ):
            raise IssueRepositoryPublicationRefusal(
                "issue_publication_original_workspace_plan_required"
            )

    def _observe_source(self, request, original=None):
        source = self._source.observe(request.issue_ref)
        if (
            source.repository_ref != request.binding.repository_ref
            or source.digest != request.expected_issue_source_sha256
        ):
            raise IssueRepositoryPublicationRefusal("issue_publication_source_stale")
        if original is not None and source != original:
            raise IssueRepositoryPublicationRefusal(
                "issue_publication_source_identity_changed"
            )
        if request.binding.execution_id != self._execution:
            raise IssueRepositoryPublicationRefusal(
                "issue_publication_execution_mismatch"
            )
        decision = evaluate_issue_source_scope(
            issue_owner=source.owner,
            issue_status=source.status,
            scope_paths=source.scope,
            actor_ref=self._execution,
            effect_paths=request.binding.target_paths,
        )
        if not decision.allowed:
            raise IssueRepositoryPublicationRefusal(decision.refusal.value)
        return source

    def _observation(self, state):
        return IssueRepositoryPublicationAdmissionObservation(
            state.request.issue_ref,
            state.request.expected_issue_source_sha256,
            self._ref,
            self._generation,
            self._execution,
            "issue-publication-observation:" + uuid4().hex,
            state.request.binding.attempt_ref,
            state.request.binding,
            state.receipt,
            state.enrollment_receipt,
            state.lease_receipt,
            state.consumer,
            state.purpose,
            state.phase,
            state.consumption,
            state.completion,
            state.publication,
            True,
            state.diagnostics,
        )

    def _retire(self, state, error):
        with self._lock:
            state.phase = "released" if state.released else "refused"
            code = getattr(error, "code", "issue_publication_owner_unavailable")
            state.diagnostics += (code,)
            return IssueRepositoryPublicationRefusal(
                code, observation=self._observation(state)
            )

    def admit_repository_publication(self, request):
        return self._admit_repository_operation(request)

    def admit_repository_index_reconciliation(self, request):
        return self._admit_repository_operation(request, purpose="index_reconciliation")

    def _admit_repository_operation(self, request, *, purpose="repository_publication"):
        from aware_issue_sdk.repository_publication import (
            IssueRepositoryPublicationClient,
            IssueRepositoryPublicationRequest,
        )

        request = IssueRepositoryPublicationClient._request(
            IssueRepositoryPublicationRequest, request
        )
        state = None
        try:
            self._current()
            self._verify_plan(request.binding, purpose=purpose)
            source = self._observe_source(request)
            with self._lock:
                self._current()
                if request.binding.attempt_ref in self._attempts:
                    raise IssueRepositoryPublicationRefusal(
                        "issue_publication_attempt_already_admitted"
                    )
                state = _AdmissionState(
                    request,
                    source,
                    "issue-publication-admission:" + uuid4().hex,
                    purpose=purpose,
                )
                handle = _issue_publication_handle(
                    self, IssueRepositoryPublicationAdmission
                )
                self._handles[handle] = state
                self._attempts.add(request.binding.attempt_ref)
                return handle
        except BaseException as error:  # typed boundary includes interruption
            if state is not None:
                raise self._retire(state, error) from error
            if isinstance(error, IssueRepositoryPublicationRefusal):
                raise
            raise IssueRepositoryPublicationRefusal(
                getattr(error, "code", "issue_publication_admission_unavailable")
            ) from error

    def enroll_repository_publication(self, admission, request):
        from aware_issue_sdk.repository_publication import (
            IssueRepositoryPublicationClient,
            IssueRepositoryPublicationEnrollmentRequest,
        )

        request = IssueRepositoryPublicationClient._request(
            IssueRepositoryPublicationEnrollmentRequest, request
        )
        with self._lock:
            state = self._state(admission, IssueRepositoryPublicationAdmission)
            if state.phase != "admitted":
                raise IssueRepositoryPublicationRefusal(
                    "issue_publication_admission_terminal",
                    observation=self._observation(state),
                )
            if (
                request.binding != state.request.binding
                or request.consumer_ref != request.binding.workspace_provider_ref
            ):
                raise IssueRepositoryPublicationRefusal(
                    "issue_publication_enrollment_correlation_mismatch"
                )
            if request.purpose != state.purpose:
                raise IssueRepositoryPublicationRefusal(
                    "issue_publication_purpose_not_implemented"
                )
            state.phase = "enrolling"
        try:
            self._current()
            self._verify_plan(request.binding, purpose=state.purpose)
            with self._lock:
                self._current()
                if state.phase != "enrolling":
                    raise IssueRepositoryPublicationRefusal(
                        "issue_publication_enrollment_cancelled"
                    )
                enrollment = _issue_publication_handle(
                    self, IssueRepositoryPublicationEnrollment
                )
                state.consumer, state.purpose = request.consumer_ref, request.purpose
                state.enrollment_receipt = "issue-publication-enrollment:" + uuid4().hex
                state.phase = "enrolled"
                self._handles[enrollment] = state
                return enrollment
        except BaseException as error:  # terminal enrollment failure
            raise self._retire(state, error) from error

    def consume_repository_publication(self, enrollment, request):
        from aware_issue_sdk.repository_publication import (
            IssueRepositoryPublicationClient,
            IssueRepositoryPublicationConsumeRequest,
        )

        request = IssueRepositoryPublicationClient._request(
            IssueRepositoryPublicationConsumeRequest, request
        )
        with self._lock:
            state = self._state(enrollment, IssueRepositoryPublicationEnrollment)
            if state.phase != "enrolled":
                raise IssueRepositoryPublicationRefusal(
                    "issue_publication_enrollment_terminal",
                    observation=self._observation(state),
                )
            binding = state.request.binding
            if (
                request.workspace_binding_ref,
                request.attempt_ref,
                request.workspace_provider_ref,
                request.workspace_provider_generation,
                request.execution_id,
                request.consumer_ref,
                request.purpose,
            ) != (
                binding.workspace_binding_ref,
                binding.attempt_ref,
                binding.workspace_provider_ref,
                binding.workspace_provider_generation,
                binding.execution_id,
                state.consumer,
                state.purpose,
            ):
                raise IssueRepositoryPublicationRefusal(
                    "issue_publication_consume_correlation_mismatch"
                )
            state.phase = "consuming"
        try:
            self._current()
            # Consumption runs under Workspace's repository transaction lock.
            # Original-plan verification belongs to admission/enrollment and
            # Workspace's own at-use transaction check, never a reciprocal SDK
            # callback here. Retained enrollment and fresh Issue authority are
            # this owner's checks before the irreversible spend.
            if state.close_parent is None:
                self._observe_source(state.request, state.source)
            else:
                parent = state.close_parent
                if (
                    parent.released
                    or parent.phase != "bound"
                    or parent.child is not state
                ):
                    raise IssueRepositoryPublicationRefusal(
                        "issue_closeout_original_parent_required"
                    )
                self._validate_close_postimage(parent)
            with self._lock:
                self._current()
                if state.phase != "consuming":
                    raise IssueRepositoryPublicationRefusal(
                        "issue_publication_consumption_cancelled"
                    )
                lease = _issue_publication_handle(self, IssueRepositoryPublicationLease)
                state.lease_receipt = "issue-publication-work:" + uuid4().hex
                state.consumption, state.phase = "consumed", "consumed"
                self._handles[lease] = state
                return lease
        except BaseException as error:  # interruption permanently prevents replay
            raise self._retire(state, error) from error

    def finish_repository_publication(self, lease, observation):
        from dataclasses import astuple

        from aware_issue_sdk.repository_publication import (
            IssueRepositoryPublicationBinding,
            IssueRepositoryPublicationClient,
            IssueRepositoryPublicationEffectObservation,
            repository_publication_value_from_payload,
        )
        from aware_workspace_sdk.repository_publication import (
            WorkspaceRepositoryAttemptObserveRequest,
            repository_publication_value_to_payload,
        )

        observation = IssueRepositoryPublicationClient._request(
            IssueRepositoryPublicationEffectObservation, observation
        )
        with self._lock:
            state = self._state(lease, IssueRepositoryPublicationLease)
            if state.completion == "completed":
                if observation != state.publication:
                    raise IssueRepositoryPublicationRefusal(
                        "issue_completion_replay_mismatch"
                    )
                return self._observation(state)
            if (
                state.consumption != "consumed"
                or state.phase != "consumed"
                or state.released
            ):
                raise IssueRepositoryPublicationRefusal(
                    "issue_publication_spent_lease_required"
                )
            binding = state.request.binding
            state.phase = "finishing"
        try:
            self._current()
            # The original owner exposes this retained ledger without taking
            # the repository lock. No receipt-free caller value grants finish.
            original = self._workspace.observe_repository_attempt(
                WorkspaceRepositoryAttemptObserveRequest(
                    binding.repository_ref,
                    binding.workspace_binding_ref,
                    binding.attempt_ref,
                    binding.workspace_provider_ref,
                    binding.workspace_provider_generation,
                    binding.execution_id,
                )
            )
            result = original.result
            if (
                not original.attempt_recognized
                or not original.ledger_complete
                or result is None
                or not result.ledger_complete
                or result.lock_release is None
                or result.lock_release.repository_lock_release != "confirmed_released"
            ):
                raise IssueRepositoryPublicationRefusal(
                    "issue_publication_original_released_ledger_required"
                )
            payload = repository_publication_value_to_payload(result)
            for key in (
                "outcome",
                "original_writer_report",
                "binding_ref",
                "attempt_ref",
            ):
                payload.pop(key)
            payload["binding"] = dict(
                zip(
                    IssueRepositoryPublicationBinding.__dataclass_fields__,
                    astuple(binding),
                    strict=True,
                )
            )
            payload["binding"]["target_paths"] = list(
                payload["binding"]["target_paths"]
            )
            payload["workspace_observation_ref"] = observation.workspace_observation_ref
            payload["publication_receipt_ref"] = (
                "git:" + result.commit_hash if result.commit_hash else None
            )
            expected = repository_publication_value_from_payload(
                IssueRepositoryPublicationEffectObservation, payload
            )
            if (
                observation != expected
                or observation.binding != binding
                or observation.work_admission_receipt_ref != state.lease_receipt
            ):
                raise IssueRepositoryPublicationRefusal(
                    "issue_publication_completion_evidence_mismatch"
                )
            with self._lock:
                self._current()
                if state.phase != "finishing" or state.released:
                    raise IssueRepositoryPublicationRefusal(
                        "issue_publication_completion_cancelled"
                    )
                state.publication = expected
                state.completion = "completed"
                state.phase = "completed"
                return self._observation(state)
        except BaseException as error:
            with self._lock:
                state.completion = "pending"
                if not state.released:
                    state.phase = "consumed"
                state.diagnostics += (getattr(error, "code", type(error).__name__),)
            raise IssueRepositoryPublicationRefusal(
                getattr(error, "code", type(error).__name__),
                observation=self._observation(state),
            ) from error

    def observe_repository_publication_admission(self, admission):
        with self._lock:
            return self._observation(
                self._state(admission, IssueRepositoryPublicationAdmission)
            )

    def _release(self, handle, expected):
        with self._lock:
            state = self._state(handle, expected)
            state.released = True
            state.phase = "released"
            if state.consumption == "consumed" and state.completion != "completed":
                state.completion = "pending"
            return IssuePublicationCleanupObservation(
                state.request.issue_ref,
                self._ref,
                self._generation,
                self._execution,
                "issue-publication-cleanup:" + uuid4().hex,
                state.request.binding.attempt_ref,
                state.receipt,
                "released",
                "completed",
                state.publication,
                None,
                True,
                state.diagnostics,
            )

    def release_repository_publication_admission(self, admission):
        return self._release(admission, IssueRepositoryPublicationAdmission)

    def release_repository_publication_enrollment(self, enrollment):
        return self._release(enrollment, IssueRepositoryPublicationEnrollment)
