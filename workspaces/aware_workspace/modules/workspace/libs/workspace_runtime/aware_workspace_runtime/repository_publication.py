"""Workspace-owned original plan registry; no foreign implementation imports.

Receipt-free verification and attempt observation read the retained ledger,
never repository freshness or a repository mutation lock. The original physical
writer composes single-use Issue work through its SDK; completion follows
confirmed physical release. Source qualification is not consumer installation.
"""

from __future__ import annotations

import os
import threading
from dataclasses import astuple, dataclass, replace
from uuid import uuid4
from weakref import WeakKeyDictionary, ref

from aware_workspace_sdk.repository_publication.authority import (
    WorkspacePublicationHandleRefusal,
    WorkspacePublicationWorkAdmission,
    WorkspaceRepositoryCommitPlan,
    _issue_plan,
    _issue_work_admission,
)
from aware_workspace_sdk.repository_publication.values import (
    WorkspacePublicationCleanupObservation,
    WorkspacePublicationPlanObservation,
    WorkspaceRepositoryAttemptObservation,
    WorkspaceRepositoryPlanVerification,
    WorkspaceRepositoryPublicationBinding,
)

_CANDIDATE_PORT_TYPES = set()
_PHYSICAL_CLAIMS = WeakKeyDictionary()


class _ExecutionClaim:
    def __new__(cls):
        raise TypeError("Original Workspace execution claim required")

    def __copy__(self):
        raise TypeError("Workspace execution claims cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("Workspace execution claims cannot be serialized")


@dataclass(frozen=True)
class _PhysicalAuthorization:
    receipt_ref: str
    issue_ref: str


def spend_repository_physical_claim(physical, transaction, claim):
    state = _PHYSICAL_CLAIMS.get(claim) if type(claim) is _ExecutionClaim else None
    if state is None:
        raise WorkspacePublicationHandleRefusal(
            "workspace_original_execution_claim_required"
        )
    owner, work, original_physical, original_transaction, authorization = state
    owner._current()
    with owner._lock:
        if (
            original_physical is not physical
            or original_transaction is not transaction
            or work.phase != "publishing"
        ):
            raise WorkspacePublicationHandleRefusal(
                "workspace_physical_claim_correlation_mismatch"
            )
        del _PHYSICAL_CLAIMS[claim]
        return authorization


def validate_repository_issue_scope(
    *, issue_owner, issue_status, scope_paths, actor_ref, effect_paths
):
    """Compatibility composition through the supplying Issue SDK only."""
    from aware_issue_sdk.repository_publication import evaluate_repository_source_scope

    refusal, offending = evaluate_repository_source_scope(
        issue_owner=issue_owner,
        issue_status=issue_status,
        scope_paths=scope_paths,
        actor_ref=actor_ref,
        effect_paths=effect_paths,
    )
    if refusal == "issue_owner_mismatch":
        raise ValueError(
            f"Issue owner mismatch: issue owner is {issue_owner!r}, command owner is {actor_ref!r}."
        )
    if refusal == "issue_status_invalid":
        raise ValueError(
            f"Issue status must be In Progress for commit rail, found: {issue_status!r}."
        )
    if refusal == "issue_source_out_of_scope":
        raise ValueError(
            f"Requested path is outside ownership scope: {offending} (scope={list(scope_paths)})"
        )
    if refusal is not None:
        raise ValueError("issue_source_scope_unrecognized_refusal")


def repository_issue_scope_covers_path(*, path, scope_paths):
    from aware_issue_sdk.repository_publication import (
        repository_source_scope_covers_path,
    )

    return repository_source_scope_covers_path(path=path, scope_paths=scope_paths)


def publication_execution():
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
        raise WorkspacePublicationHandleRefusal(
            "provider_execution_identity_unavailable"
        )
    return "-".join(identities[0])


@dataclass
class _PlanState:
    binding: WorkspaceRepositoryPublicationBinding
    observation: WorkspacePublicationPlanObservation
    phase: str = "planned"
    capture: object = None
    result: object = None
    purpose: str = "repository_publication"
    reconciliation_request: object = None


@dataclass
class _WorkAdmissionState:
    plan: WorkspaceRepositoryCommitPlan
    issue_client: object
    issue_admission: object
    enrollment: object = None
    phase: str = "enrolling"
    cleanup_state: str = "not_attempted"
    diagnostics: tuple[str, ...] = ()
    transaction: object = None
    lease: object = None
    issue_ref: str | None = None
    completion_in_progress: bool = False
    purpose: str = "repository_publication"


class WorkspaceRepositoryPublicationRuntime:
    def __init__(self, physical):
        if type(physical) not in _CANDIDATE_PORT_TYPES:
            raise TypeError("Selected original Workspace physical port required")
        self._physical = physical
        self._pid = os.getpid()
        self._execution = publication_execution()
        self._provider_ref = "workspace-publication:" + uuid4().hex
        self._generation = uuid4().hex
        self._lock = threading.RLock()
        self._plans = WeakKeyDictionary()
        self._bindings = {}
        self._attempts = {}
        self._work_admissions = WeakKeyDictionary()
        self._work_by_plan = WeakKeyDictionary()

    def _current(self):
        if self._pid != os.getpid():
            raise WorkspacePublicationHandleRefusal("workspace_cross_process_refused")
        if publication_execution() != self._execution:
            raise WorkspacePublicationHandleRefusal("workspace_execution_changed")

    def _snapshot_handle(self, plan):
        self._current()
        with self._lock:
            state = (
                self._plans.get(plan)
                if type(plan) is WorkspaceRepositoryCommitPlan
                else None
            )
            if state is None:
                raise WorkspacePublicationHandleRefusal(
                    "workspace_original_plan_required"
                )
            return replace(state)

    def plan_repository_commit(self, request):
        return self._plan_repository_operation(request)

    def plan_repository_index_reconciliation(self, request):
        from aware_workspace_sdk.repository_publication.ports import (
            WorkspaceRepositoryIndexReconcileRequest,
        )
        from aware_workspace_sdk.repository_publication.values import (
            WorkspaceRepositoryCommitRequest,
        )

        if type(request) is not WorkspaceRepositoryIndexReconcileRequest:
            raise TypeError("Exact WorkspaceRepositoryIndexReconcileRequest required")
        return self._plan_repository_operation(
            WorkspaceRepositoryCommitRequest(
                request.repository_ref,
                request.target_paths,
                "Reconcile existing index: " + request.publication_receipt_ref,
                request.attempt_ref,
            ),
            reconciliation=request,
        )

    def _plan_repository_operation(self, request, *, reconciliation=None):
        from aware_workspace_sdk.repository_publication.codec import (
            repository_publication_value_from_payload,
            repository_publication_value_to_payload,
        )
        from aware_workspace_sdk.repository_publication.values import (
            WorkspaceRepositoryCommitRequest,
        )

        if type(request) is not WorkspaceRepositoryCommitRequest:
            raise TypeError("Exact WorkspaceRepositoryCommitRequest required")
        request = repository_publication_value_from_payload(
            type(request), repository_publication_value_to_payload(request)
        )
        self._current()
        with self._lock:
            if request.attempt_ref in self._attempts:
                raise WorkspacePublicationHandleRefusal(
                    "workspace_attempt_already_recorded"
                )
            # Own physical port supplies observations only. No authority is
            # constructed from capture values and no Git writer is invoked.
            captured = (
                self._physical.capture_candidate(request)
                if reconciliation is None
                else self._physical.capture_reconciliation(request, reconciliation)
            )
            self._current()
            binding = WorkspaceRepositoryPublicationBinding(
                binding_ref="workspace-plan:" + uuid4().hex,
                attempt_ref=request.attempt_ref,
                repository_ref=captured.repository_ref,
                publication_reference=captured.publication_reference,
                expected_head=captured.expected_head,
                target_paths=request.target_paths,
                postimages_digest=captured.postimages_digest,
                message_digest=captured.message_digest,
                provider_generation=self._generation,
                provider_ref=self._provider_ref,
                execution_id=self._execution,
            )
            observation = WorkspacePublicationPlanObservation(
                binding.binding_ref,
                binding.attempt_ref,
                "owned",
                "not_attempted",
                True,
                (),
                (),
            )
            plan = _issue_plan(self)
            self._plans[plan] = _PlanState(
                binding,
                observation,
                capture=captured,
                purpose="repository_publication"
                if reconciliation is None
                else "index_reconciliation",
                reconciliation_request=reconciliation,
            )
            self._bindings[binding.binding_ref] = (binding, ref(plan))
            self._attempts[binding.attempt_ref] = binding.binding_ref
            return plan

    def verify_repository_plan(self, request):
        return self._verify_repository_plan(request, reconciliation=False)

    def verify_repository_index_reconciliation_plan(self, request):
        return self._verify_repository_plan(request, reconciliation=True)

    def _verify_repository_plan(self, request, *, reconciliation):
        self._current()
        with self._lock:
            retained = self._bindings.get(request.binding.binding_ref)
            plan = (
                retained[1]() if retained and retained[0] == request.binding else None
            )
            state = self._plans.get(plan) if plan is not None else None
            recognized = (
                state is not None
                and state.phase == "planned"
                and (state.purpose == "index_reconciliation") == reconciliation
            )
            return WorkspaceRepositoryPlanVerification(
                request.binding,
                recognized,
                state.phase if state else "unrecognized",
                "workspace-plan-observation:" + uuid4().hex,
                () if recognized else ("workspace_original_current_plan_required",),
            )

    def observe_repository_attempt(self, request):
        self._current()
        with self._lock:
            retained = self._bindings.get(request.binding_ref)
            binding = retained[0] if retained else None
            recognized = binding is not None and (
                binding.repository_ref,
                binding.binding_ref,
                binding.attempt_ref,
                binding.provider_ref,
                binding.provider_generation,
                binding.execution_id,
            ) == (
                request.repository_ref,
                request.binding_ref,
                request.attempt_ref,
                request.provider_ref,
                request.provider_generation,
                request.execution_id,
            )
            plan = retained[1]() if recognized else None
            state = self._plans.get(plan) if plan is not None else None
            work = self._work_by_plan.get(plan) if plan is not None else None
            diagnostics = work.diagnostics if work is not None else ()
            return WorkspaceRepositoryAttemptObservation(
                request,
                "workspace-attempt-observation:" + uuid4().hex,
                recognized,
                state.observation if state else None,
                state.result if state else None,
                state.result.lock_release if state and state.result else None,
                state is not None
                and (work is None or work.cleanup_state != "unknown")
                and (state.result is None or state.result.ledger_complete),
                diagnostics
                if state is not None
                else ("workspace_plan_ledger_unavailable",),
            )

    def observe_repository_publication(self, request):
        from aware_workspace_sdk.repository_publication.ports import (
            WorkspaceRepositoryPublicationObservation,
        )

        self._current()
        try:
            physical = self._physical.observe_publication_receipt(request)
        except BaseException as error:  # noqa: BLE001 - unavailable read does not erase retained publication
            physical = {
                "receipt_state": "unknown",
                "reachability_state": "unknown",
                "commit_hash": None,
                "diagnostics": (
                    "workspace_receipt_observation:" + type(error).__name__,
                ),
            }
        self._current()
        with self._lock:
            # Receipt presence and reachability are physical observations, not
            # a reconstruction of an original plan or proof that CAS returned.
            requested_hash = request.publication_receipt_ref[4:].lower()
            matches = [
                (state.binding, state.result)
                for state in self._plans.values()
                if state.binding.repository_ref == request.repository_ref
                and state.purpose != "index_reconciliation"
                and state.result is not None
                and requested_hash
                in {state.result.commit_hash, state.result.candidate_commit}
            ]
            binding, result = matches[0] if len(matches) == 1 else (None, None)
            expected_matches = (
                binding.binding_ref == request.expected_binding_ref
                if binding is not None and request.expected_binding_ref is not None
                else None
            )
            diagnostics = physical["diagnostics"] + (
                ("workspace_publication_ledger_ambiguous",)
                if len(matches) > 1
                else ("workspace_publication_ledger_unavailable",)
                if not matches
                else ()
            )
            return WorkspaceRepositoryPublicationObservation(
                request,
                "workspace-publication-observation:" + uuid4().hex,
                self._provider_ref,
                self._generation,
                physical["receipt_state"],
                physical["reachability_state"],
                physical["commit_hash"],
                binding,
                expected_matches,
                result,
                result is not None
                and result.ledger_complete
                and physical["receipt_state"] == "present"
                and physical["reachability_state"] != "unknown"
                and expected_matches is not False,
                diagnostics,
            )

    def release_repository_plan(self, plan):
        self._current()
        with self._lock:
            self._snapshot_handle(plan)
            state = self._plans[plan]
            work = self._work_by_plan.get(plan)
            if work is not None and work.phase in {
                "publishing",
                "consuming",
                "finishing",
            }:
                raise WorkspacePublicationHandleRefusal("workspace_plan_in_use")
            state.phase = "released"
            state.observation = WorkspacePublicationPlanObservation(
                state.binding.binding_ref,
                state.binding.attempt_ref,
                "released",
                "completed",
                True,
                (),
                (),
            )
            return WorkspacePublicationCleanupObservation(
                state.binding.binding_ref,
                state.binding.attempt_ref,
                "completed",
                None,
                True,
                (),
                (),
            )

    def _work_state(self, admission):
        self._current()
        state = (
            self._work_admissions.get(admission)
            if type(admission) is WorkspacePublicationWorkAdmission
            else None
        )
        if state is None:
            raise WorkspacePublicationHandleRefusal(
                "workspace_original_work_admission_required"
            )
        return state

    def _work_admission_phase(self, admission):
        with self._lock:
            return self._work_state(admission).phase

    def enroll_issue_repository_publication(self, plan, admission, *, issue_client):
        from aware_issue_sdk.repository_publication import (
            IssueRepositoryPublicationBinding,
            IssueRepositoryPublicationClient,
            IssueRepositoryPublicationEnrollmentRequest,
        )

        if type(issue_client) is not IssueRepositoryPublicationClient:
            raise TypeError("Original supplying Issue SDK client required")
        self._current()
        with self._lock:
            original = self._snapshot_handle(plan)
            if original.phase != "planned":
                raise WorkspacePublicationHandleRefusal("workspace_plan_terminal")
            if plan in self._work_by_plan:
                raise WorkspacePublicationHandleRefusal(
                    "workspace_plan_already_enrolled"
                )
            state = _WorkAdmissionState(plan, issue_client, admission)
            # Reserve locally before reciprocal verification. No SDK callback
            # while the Workspace registry or repository transaction is held.
            self._work_by_plan[plan] = state
        enrollment_invoked = False
        try:
            observation = issue_client.observe_repository_publication_admission(
                admission
            )
            state.issue_ref = observation.issue_ref
            state.purpose = observation.purpose
            binding = IssueRepositoryPublicationBinding(*astuple(original.binding))
            if (
                observation.binding != binding
                or observation.execution_id != self._execution
                or observation.phase != "admitted"
                or observation.consumption_state != "not_consumed"
                or not observation.ledger_complete
                or observation.purpose
                not in {
                    "repository_publication",
                    "issue_closeout_publication",
                    "index_reconciliation",
                }
                or (observation.purpose == "index_reconciliation")
                != (original.purpose == "index_reconciliation")
            ):
                raise WorkspacePublicationHandleRefusal(
                    "workspace_issue_admission_correlation_mismatch"
                )
            enrollment_invoked = True
            state.enrollment = issue_client.enroll_repository_publication(
                admission,
                IssueRepositoryPublicationEnrollmentRequest(
                    binding, self._provider_ref, state.purpose
                ),
            )
            with self._lock:
                self._current()
                if self._plans[plan].phase != "planned":
                    raise WorkspacePublicationHandleRefusal("workspace_plan_terminal")
                work = _issue_work_admission(self)
                state.phase = "enrolled"
                self._work_admissions[work] = state
                return work
        except BaseException as error:
            # Retire this reservation even after interruption. Only a returned
            # genuine enrollment can authorize its own cleanup; never release
            # the caller's admission or infer ownership from a failure value.
            state.phase = "refused"
            state.diagnostics += (getattr(error, "code", type(error).__name__),)
            if enrollment_invoked and state.enrollment is None:
                state.cleanup_state = "unknown"
                state.diagnostics += ("issue_enrollment_return_unavailable",)
            if state.enrollment is not None:
                try:
                    cleanup = issue_client.release_repository_publication_enrollment(
                        state.enrollment
                    )
                    state.cleanup_state = cleanup.cleanup_state
                    state.diagnostics += cleanup.diagnostics
                except BaseException as cleanup_error:  # noqa: BLE001
                    # Preserve the original refusal; an interrupted cleanup
                    # cannot justify retry or be reported as complete.
                    state.cleanup_state = "unknown"
                    state.diagnostics += (type(cleanup_error).__name__,)
            raise

    def release_publication_work_admission(self, admission):
        with self._lock:
            state = self._work_state(admission)
            binding = self._plans[state.plan].binding
            if state.phase in {"publishing", "consuming", "finishing"}:
                raise WorkspacePublicationHandleRefusal(
                    "workspace_work_admission_in_use"
                )
            if state.phase == "releasing":
                raise WorkspacePublicationHandleRefusal(
                    "workspace_work_admission_release_in_progress"
                )
            if state.phase == "released":
                return self._work_cleanup(state, binding)
            state.phase = "releasing"
        try:
            cleanup = state.issue_client.release_repository_publication_enrollment(
                state.enrollment
            )
            state.cleanup_state = cleanup.cleanup_state
            state.diagnostics += cleanup.diagnostics
        except BaseException as error:
            state.cleanup_state = "unknown"
            state.diagnostics += (getattr(error, "code", type(error).__name__),)
            raise
        finally:
            with self._lock:
                state.phase = "released"
        return self._work_cleanup(state, binding)

    def publish_repository_commit(self, plan, admission):
        return self._execute_repository_operation(plan, admission)

    def reconcile_repository_index(self, request, admission):
        from aware_workspace_sdk.repository_publication.ports import (
            WorkspaceRepositoryIndexReconcileResult,
        )

        with self._lock:
            state = self._work_state(admission)
            original = self._plans[state.plan]
            if (
                original.purpose != "index_reconciliation"
                or original.reconciliation_request != request
            ):
                raise WorkspacePublicationHandleRefusal(
                    "workspace_original_reconciliation_request_required"
                )
            plan = state.plan
        result = self._execute_repository_operation(
            plan, admission, reconciliation=True
        )
        projection = result.index_projection
        return WorkspaceRepositoryIndexReconcileResult(
            request,
            "workspace-index-observation:" + uuid4().hex,
            self._provider_ref,
            self._generation,
            original.binding.binding_ref,
            result.work_admission_receipt_ref,
            projection
            if projection in {"applied", "failed", "unknown"}
            else "not_attempted",
            result,
            result.lock_release,
            result.effects,
            result.ledger_complete,
            result.diagnostics,
        )

    def _execute_repository_operation(self, plan, admission, *, reconciliation=False):
        from aware_issue_sdk.repository_publication import (
            IssueRepositoryPublicationConsumeRequest,
        )

        self._current()
        with self._lock:
            state = self._work_state(admission)
            original = self._plans.get(plan)
            if (
                state.plan is not plan
                or original is None
                or original.phase != "planned"
                or (original.purpose == "index_reconciliation") != reconciliation
            ):
                raise WorkspacePublicationHandleRefusal(
                    "workspace_original_enrolled_plan_required"
                )
            if state.phase != "enrolled":
                raise WorkspacePublicationHandleRefusal(
                    "workspace_work_admission_terminal"
                )
            state.phase, original.phase = "consuming", "publishing"
            binding = original.binding
        report = None
        diagnostics = ()
        try:
            # Own physical revalidation holds the actual repository lock before
            # fresh Issue consumption. Consumption never calls back here.
            state.transaction = self._physical.begin(original.capture, binding)
            self._current()
            state.lease = state.issue_client.consume_repository_publication(
                state.enrollment,
                IssueRepositoryPublicationConsumeRequest(
                    binding.binding_ref,
                    binding.attempt_ref,
                    binding.provider_ref,
                    binding.provider_generation,
                    binding.execution_id,
                    self._provider_ref,
                    state.purpose,
                ),
            )
            with self._lock:
                self._current()
                state.phase = "publishing"
                claim = object.__new__(_ExecutionClaim)
                _PHYSICAL_CLAIMS[claim] = (
                    self,
                    state,
                    self._physical,
                    state.transaction,
                    _PhysicalAuthorization(state.lease.receipt_ref, state.issue_ref),
                )
            report = (
                self._physical.reconcile(state.transaction, claim)
                if reconciliation
                else self._physical.publish(state.transaction, claim)
            )
        except BaseException as error:  # noqa: BLE001 - preserve spent authority on interruption
            diagnostics = (getattr(error, "code", type(error).__name__), str(error))
        finally:
            if "claim" in locals():
                _PHYSICAL_CLAIMS.pop(claim, None)
            if state.transaction is not None:
                try:
                    physical = self._physical.release(state.transaction)
                except BaseException as error:  # noqa: BLE001 - disposal return may be unavailable
                    diagnostics += ("physical_release_return:" + type(error).__name__,)
                    try:
                        physical = self._physical.observe_transaction(state.transaction)
                    except BaseException as observation_error:  # noqa: BLE001 - retain known publication without release evidence
                        diagnostics += (
                            "physical_release_observation:"
                            + type(observation_error).__name__,
                        )
                        # The original writer report remains evidence of any
                        # known publication. Neither failed return establishes
                        # disposal or unlock, and neither permits another write.
                        physical = {
                            "transaction_ref": "workspace-unavailable:"
                            + binding.attempt_ref,
                            "lock_release": "unknown",
                            "cleanup_state": "unknown",
                            # A report can precede an interrupted CAS return.
                            # Only an established CAS outcome removes that
                            # uncertainty when physical evidence is unavailable.
                            "publication_unknown": report is None
                            or report.get("reference_update")
                            not in {"cas_applied", "cas_failed"},
                            "projection_unknown": reconciliation
                            and (
                                report is None
                                or report.get("shared_index_projection")
                                not in {"applied", "failed"}
                            ),
                            "diagnostics": (
                                "workspace_release_observation_unavailable",
                            ),
                            "report": None,
                        }
                report = physical["report"] or report
            else:
                # No returned physical holder: do not infer confirmed release
                # from an unavailable begin result.
                physical = {
                    "transaction_ref": "workspace-unavailable:" + binding.attempt_ref,
                    "lock_release": "unknown",
                    "cleanup_state": "unknown",
                    "projection_unknown": reconciliation,
                    "diagnostics": ("workspace_transaction_return_unavailable",),
                }
            with self._lock:
                state.phase = "spent"
                original.phase = "spent"
                original.result = self._publication_result(
                    binding, state, report, physical, diagnostics
                )
                if reconciliation:
                    # This operation did not publish a reference, regardless
                    # of the existing receipt's presence/reachability. Keep
                    # prior attempts' CAS evidence untouched in their ledgers.
                    original.result = replace(
                        original.result,
                        outcome="applied"
                        if original.result.index_projection == "applied"
                        else "failed",
                        publication_state="not_published",
                        reference_update="not_run",
                        candidate_commit=None,
                        commit_hash=original.reconciliation_request.publication_receipt_ref[
                            4:
                        ],
                        index_reconciliation_pending=original.result.index_projection
                        != "applied",
                        effects=tuple(
                            effect
                            for effect in original.result.effects
                            if effect.kind != "repository_reference_update"
                        ),
                    )
        if state.lease is None:
            return original.result
        try:
            return self.finish_repository_publication(admission)
        except BaseException as error:  # noqa: BLE001 - late execution refusal preserves the invoked attempt
            with self._lock:
                original.result = replace(
                    original.result,
                    admission_completion="unknown",
                    diagnostics=original.result.diagnostics
                    + (getattr(error, "code", type(error).__name__),),
                )
                return original.result

    @staticmethod
    def _publication_result(binding, state, report, physical, diagnostics):
        from aware_workspace_sdk.repository_publication.codec import (
            repository_publication_value_from_payload,
            repository_publication_value_to_payload,
        )
        from aware_workspace_sdk.repository_publication.values import (
            WorkspaceRepositoryCommitResult,
            WorkspaceRepositoryLockReleaseObservation,
            WorkspaceRepositoryWriterObservation,
        )

        lock = WorkspaceRepositoryLockReleaseObservation(
            binding.binding_ref,
            binding.attempt_ref,
            binding.provider_ref,
            binding.provider_generation,
            physical["transaction_ref"],
            "workspace-lock-release:" + uuid4().hex,
            physical["lock_release"],
            physical["diagnostics"],
        )
        writer = (
            repository_publication_value_from_payload(
                WorkspaceRepositoryWriterObservation,
                repository_publication_value_to_payload(
                    WorkspaceRepositoryWriterObservation(**report)
                ),
            )
            if report is not None
            else None
        )
        published = writer is not None and writer.reference_update == "cas_applied"
        publication_unknown = physical.get("publication_unknown", writer is None)
        projection_unknown = physical.get("projection_unknown", False)
        effects = []
        from aware_workspace_sdk.repository_publication.values import (
            WorkspaceRepositoryPhysicalEffect,
        )

        if writer is not None and (
            published or publication_unknown or writer.reference_update == "cas_failed"
        ):
            effects.append(
                WorkspaceRepositoryPhysicalEffect(
                    "workspace-effect:" + uuid4().hex,
                    binding.publication_reference,
                    "repository_reference_update",
                    "applied"
                    if published
                    else "unknown"
                    if publication_unknown
                    else "failed",
                    binding.expected_head,
                    writer.commit_hash if published else None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    (),
                )
            )
        if projection_unknown or (
            writer is not None
            and writer.shared_index_projection
            in {
                "applied",
                "failed",
            }
        ):
            effects.append(
                WorkspaceRepositoryPhysicalEffect(
                    "workspace-effect:" + uuid4().hex,
                    binding.repository_ref,
                    "shared_index_projection",
                    "unknown" if projection_unknown else writer.shared_index_projection,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    (writer.shared_index_projection_error,)
                    if writer is not None and writer.shared_index_projection_error
                    else (),
                )
            )
        return WorkspaceRepositoryCommitResult(
            binding.binding_ref,
            binding.attempt_ref,
            "applied" if published else "refused" if writer is None else "failed",
            "published"
            if published
            else "unknown"
            if publication_unknown
            else "not_published",
            binding.expected_head,
            writer.candidate_commit if writer else None,
            writer.commit_hash if writer else None,
            writer.updated_reference if writer else None,
            writer.reference_update if writer else "unknown",
            "unknown"
            if projection_unknown
            else writer.shared_index_projection
            if writer
            else "unknown",
            physical["cleanup_state"],
            lock,
            "pending" if state.lease is not None else "not_attempted",
            writer is not None
            and not publication_unknown
            and not projection_unknown
            and physical["cleanup_state"] == "completed",
            state.lease.receipt_ref if state.lease is not None else None,
            writer.transaction_mode if writer else "not_run",
            writer.shared_index_unchanged if writer else None,
            writer.index_reconciliation_pending if writer else None,
            writer,
            tuple(effects),
            diagnostics + physical["diagnostics"],
        )

    def finish_repository_publication(self, admission):
        from aware_issue_sdk.repository_publication import (
            IssueRepositoryPublicationBinding,
            IssueRepositoryPublicationEffectObservation,
        )
        from aware_issue_sdk.repository_publication import (
            repository_publication_value_from_payload as issue_value_from_payload,
        )
        from aware_workspace_sdk.repository_publication.codec import (
            repository_publication_value_to_payload,
        )

        with self._lock:
            state = self._work_state(admission)
            original = self._plans[state.plan]
            result = original.result
            if result is None:
                raise WorkspacePublicationHandleRefusal(
                    "workspace_original_attempt_required"
                )
            if result.admission_completion in {"completed", "unknown"}:
                return result
            if state.phase != "spent" or state.completion_in_progress:
                raise WorkspacePublicationHandleRefusal(
                    "workspace_original_spent_attempt_required"
                )
            if (
                state.lease is None
                or result.lock_release is None
                or result.lock_release.repository_lock_release != "confirmed_released"
                or not result.ledger_complete
            ):
                return result
            state.phase = "finishing"
            state.completion_in_progress = True
        payload = repository_publication_value_to_payload(result)
        payload.pop("outcome")
        payload.pop("original_writer_report")
        payload.pop("binding_ref")
        payload.pop("attempt_ref")
        payload["binding"] = {
            field: value
            for field, value in zip(
                IssueRepositoryPublicationBinding.__dataclass_fields__,
                astuple(original.binding),
                strict=True,
            )
        }
        payload["binding"]["target_paths"] = list(payload["binding"]["target_paths"])
        payload["workspace_observation_ref"] = "workspace-finish:" + uuid4().hex
        payload["publication_receipt_ref"] = (
            "git:" + result.commit_hash if result.commit_hash else None
        )
        try:
            observation = issue_value_from_payload(
                IssueRepositoryPublicationEffectObservation, payload
            )
            finished = state.issue_client.finish_repository_publication(
                state.lease, observation
            )
            if finished.completion_state != "completed":
                raise WorkspacePublicationHandleRefusal(
                    "issue_completion_not_confirmed"
                )
            original.result = replace(result, admission_completion="completed")
        except BaseException as error:  # noqa: BLE001 - finish return cannot erase publication
            original.result = replace(
                result,
                admission_completion="unknown",
                diagnostics=result.diagnostics
                + (getattr(error, "code", type(error).__name__),),
            )
        finally:
            with self._lock:
                state.phase = "spent"
                state.completion_in_progress = False
        return original.result

    def _work_cleanup(self, state, binding):
        result = self._plans[state.plan].result
        return WorkspacePublicationCleanupObservation(
            binding.binding_ref,
            binding.attempt_ref,
            state.cleanup_state,
            result.lock_release if result else None,
            state.cleanup_state == "completed"
            and (result is None or result.ledger_complete),
            result.effects if result else (),
            state.diagnostics + (result.diagnostics if result else ()),
        )
