"""Reviewed A1 joins and retention orchestration over original owner operations."""

from __future__ import annotations

import hashlib
import json
import os
import threading
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any, NoReturn, Protocol, cast

from aware_issue_sdk import operation as issue
from aware_issue_sdk.operation_codec import encode_issue_request, encode_issue_result
from aware_workspace_sdk import architecture_setup_review_values as v
from aware_workspace_sdk.architecture_setup_command_values import (
    WorkspaceSetupA1CommandEvidence,
    WorkspaceSetupA1CommandRequest,
    command_value_to_payload,
)
from aware_workspace_sdk.architecture_setup_review_codec import (
    SetupReviewValueError,
    review_value_digest,
    review_value_to_json,
    review_value_to_payload,
)

if TYPE_CHECKING:
    from aware_file_system.private_directory import (
        PrivateDirectoryCleanup,
        PrivateDirectoryObservation,
        PrivateFileReadResult,
    )


class _ReviewStorage(Protocol):
    """The selected adapter retains custody; runtime never supplies physical IO."""

    root: Path
    identity: v.DirectoryIdentity
    reads: list[PrivateFileReadResult]
    intent: v.SetupEvidenceRef | None
    cleanup: PrivateDirectoryCleanup | None

    def begin(self) -> None: ...
    def current(self) -> PrivateDirectoryObservation: ...
    def read_issue(self, tag: str) -> issue.IssueReadProjectionResolveResult: ...
    def write_metadata(self, name: str, raw: bytes) -> None: ...
    def write_capture(
        self, raw: bytes, *, attempt: str, kind: v.CaptureKind
    ) -> v.SetupCaptureDescriptor: ...
    def read(self, name: str, *, size: int, sha256: str) -> bytes: ...
    def read_capture(
        self, capture: v.SetupCaptureDescriptor, *, attempt: str
    ) -> bytes: ...
    def failed(self, error: BaseException) -> None: ...
    def retention(self) -> v.RetentionEvidence: ...
    def release(self) -> PrivateDirectoryCleanup | None: ...


_BINDING_KEEP = (
    "repository_root",
    "repository_identity",
    "operation",
    "request_sha256",
    "plan_sha256",
    "input_bindings",
    "file_transitions",
    "ancestor_guards",
    "scratch_policy",
    "limits",
    "confinement_profile",
    "mode_policy",
)
_STEP_KEEP = (
    "ordinal",
    "file_ordinal",
    "kind",
    "primary_path",
    "auxiliary_paths",
    "preconditions",
    "mode_policy",
    "requested_mode",
    "candidate_sha256",
    "candidate_size_bytes",
)


def _refuse(code) -> NoReturn:
    raise SetupReviewValueError(code)


class _CurrentInputRefusal(Exception):
    """Issued only by the original comparisons before a product dispatch."""

    def __init__(self, code, *, record, reference, observed_issue, sources=None):
        self.code = code
        self.record = record
        self.reference = reference
        self.observed_issue = observed_issue
        self.sources = sources
        self.scope_decision: v.SetupScopeDecision | None = None
        self.apply_decision: v.SetupApplyDecision | None = None
        self.inputs_ref: v.SetupEvidenceRef | None = None
        super().__init__(code)


def _digest(body):
    return "sha256:" + hashlib.sha256(body).hexdigest()


def review_attempt_key(execution: str, intent: str) -> str:
    for value in (execution, intent):
        if (
            type(value) is not str
            or not value
            or len(value.encode("utf-8")) > 1024
            or "\0" in value
        ):
            _refuse("invalid_attempt_component")
    return hashlib.sha256(
        b"aware.setup-review.attempt.v1\0"
        + execution.encode("utf-8")
        + b"\0"
        + intent.encode("utf-8")
    ).hexdigest()


def review_action_key(action: str, reviewed_digest: str) -> str:
    if type(action) is not str or action not in ("scope", "apply"):
        _refuse("invalid_dispatch_action")
    if (
        type(reviewed_digest) is not str
        or len(reviewed_digest) != 71
        or not reviewed_digest.startswith("sha256:")
        or any(c not in "0123456789abcdef" for c in reviewed_digest[7:])
    ):
        _refuse("invalid_review_digest")
    return _digest(
        b"aware.setup-review.intent.v1\0"
        + action.encode("ascii")
        + b"\0"
        + reviewed_digest.encode("ascii")
    )


def review_correspondence(evidence: WorkspaceSetupA1CommandEvidence) -> str:
    """Select exact stable fields; never recursively strip similarly named data."""
    payload = cast(dict[str, Any], command_value_to_payload(evidence))
    observation = payload["workspace_observation"]
    if (
        observation is None
        or observation["value"]["binding"] is None
        or payload["request"] is None
    ):
        _refuse("complete_original_plan_required")
    binding = observation["value"]["binding"]["value"]
    selected = {key: binding[key] for key in _BINDING_KEEP}
    selected["ordered_effects"] = [
        {key: step["value"][key] for key in _STEP_KEEP}
        for step in binding["ordered_effects"]
    ]
    canonical = {
        "architecture_request": payload["request"]["value"]["architecture_request"],
        "binding": selected,
    }
    return _digest(
        json.dumps(
            canonical,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    )


def reviewed_path_sets(evidence: WorkspaceSetupA1CommandEvidence):
    command_value_to_payload(evidence)
    observation = evidence.workspace_observation
    if observation is None or observation.binding is None:
        _refuse("complete_original_plan_required")
    binding = observation.binding
    physical = tuple(
        sorted(
            {
                path
                for step in binding.ordered_effects
                for path in (step.primary_path, *step.auxiliary_paths)
            }
        )
    )
    final = tuple(row.path for row in binding.file_transitions)
    if not set(final) <= set(physical):
        _refuse("final_files_missing_from_physical_scope")
    return physical, final


def validate_review_capture(
    record: v.SetupReviewRecord, evidence: WorkspaceSetupA1CommandEvidence
):
    """Correlate complete captured owners before a retaining driver uses a record."""
    review_value_to_payload(record)
    encoded = command_value_to_payload(evidence)
    request = record.request
    target = request.target
    if request.architecture_request.operation != "repository":
        _refuse("review_profile_repository_only")
    if (
        evidence.command_status != "preview_completed"
        or not evidence.completion_verified
        or not evidence.ledger_complete
        or evidence.mode != "preview"
        or evidence.primary_failure.state != "none"
        or evidence.request is None
        or evidence.issue_sources_observation is None
        or not record.ready_for_decision
    ):
        _refuse("successful_complete_original_preview_required")
    original = evidence.request
    if (
        original.architecture_request != request.architecture_request
        or original.repository_root != target.repository_root
        or original.issue_ref != target.issue_path
        or original.authority_manifest_locator != target.authority_manifest_locator
        or original.execution_ref != request.execution_ref
        or original.client_intent_id != request.client_intent_id
        or evidence.review_guards != record.review_guards
        or original.issue_request is None
        or original.issue_request.actor_ref != request.actor_ref
        or original.issue_request.actor_evidence_ref != request.actor_evidence_ref
    ):
        _refuse("review_original_request_mismatch")
    read = record.issue_read
    encode_issue_result(read)
    projection = read.projection
    if (
        type(read) is not issue.IssueReadProjectionResolveResult
        or read.outcome is not issue.IssueReadProjectionResolveOutcome.FOUND
        or projection is None
        or read.issue_ref != target.issue_tag
        or projection.issue_ref != target.issue_tag
        or projection.tag != target.issue_tag
        or projection.source_path
        not in (
            target.issue_path,
            str(PurePosixPath(target.repository_root) / target.issue_path),
        )
        or projection.source_digest != record.review_guards.issue_source_sha256
        or projection.owner_ref != request.execution_ref
        or projection.status != "in_progress"
        or evidence.issue_sources_observation.issue_source.content_sha256
        != projection.source_digest
    ):
        _refuse("review_issue_source_mismatch")
    if tuple(projection.ownership_scope) != record.existing_scope:
        _refuse("review_existing_scope_mismatch")
    physical, final = reviewed_path_sets(evidence)
    if (
        physical != record.physical_scope
        or final != record.final_files
        or review_correspondence(evidence) != record.correspondence_sha256
    ):
        _refuse("review_plan_correspondence_mismatch")
    raw = json.dumps(
        encoded,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    if (
        record.capture.kind != "command_v1"
        or len(raw) != record.capture.byte_count
        or _digest(raw) != record.capture.sha256
    ):
        _refuse("review_command_capture_mismatch")


def _review_reference(record, reference):
    review_value_to_payload(record)
    review_value_to_payload(reference)
    if (
        reference.target != record.request.target
        or reference.record_contract != v.REVIEW_SCHEMA_IDS[v.SetupReviewRecord]
        or reference.record_sha256 != review_value_digest(record)
        or reference.record_bytes != len(review_value_to_json(record).encode("utf-8"))
    ):
        _refuse("review_reference_mismatch")


def scope_input_record(
    record: v.SetupReviewRecord,
    reference: v.SetupEvidenceRef,
    decision: v.SetupScopeDecision,
) -> v.SetupScopeInputRecord:
    """Build original Issue request data; caller must not dispatch before intent."""
    _review_reference(record, reference)
    review_value_to_payload(decision)
    request = record.request
    if (
        decision.review != reference
        or decision.execution_ref != request.execution_ref
        or not record.ready_for_decision
        or record.scope_outcome_ref is not None
    ):
        _refuse("scope_decision_mismatch")
    # Omitted declared actors can be read as history but cannot become a scope request.
    if request.actor_ref is None or request.actor_evidence_ref is None:
        _refuse("explicit_scope_actor_metadata_required")
    paths = tuple(
        sorted(
            set(record.existing_scope)
            | set(record.physical_scope)
            | (
                {request.target.issue_path}
                if request.include_issue_lifecycle
                else set()
            )
        )
    )
    original = issue.IssueBindScopePathsRequest(
        request.target.issue_tag,
        _complete_guards(record)[0],
        decision.client_intent_id,
        request.actor_ref,
        request.actor_evidence_ref,
        paths,
    )
    encode_issue_request(original)
    result = v.SetupScopeInputRecord(decision, paths, original)
    review_value_to_payload(result)
    return result


def apply_input_record(
    record: v.SetupReviewRecord,
    reference: v.SetupEvidenceRef,
    decision: v.SetupApplyDecision,
) -> v.SetupApplyInputRecord:
    _review_reference(record, reference)
    review_value_to_payload(decision)
    if (
        decision.review != reference
        or decision.execution_ref != record.request.execution_ref
        or not record.ready_for_decision
        or record.scope_outcome_ref is None
    ):
        _refuse("second_review_apply_decision_required")
    from aware_issue_sdk.workspace_setup_admission_values import (
        IssueWorkspaceSetupRequest,
    )

    request = record.request
    issue_digest, manifest_digest, _ = _complete_guards(record)
    guards = record.review_guards
    original_issue = IssueWorkspaceSetupRequest(
        request.target.issue_path,
        issue_digest,
        request.actor_ref,
        request.actor_evidence_ref,
        decision.client_intent_id,
        "workspace_setup_a1_v1",
        manifest_digest,
    )
    original = WorkspaceSetupA1CommandRequest(
        request.architecture_request,
        original_issue,
        request.target.repository_root,
        request.target.authority_manifest_locator,
        request.target.issue_path,
        request.execution_ref,
        decision.client_intent_id,
    )
    result = v.SetupApplyInputRecord(decision, record.final_files, guards, original)
    review_value_to_payload(result)
    return result


def validate_scope_result(
    record: v.SetupReviewRecord,
    inputs: v.SetupScopeInputRecord,
    result: issue.IssueMutationResult,
):
    """Check the actual original return; later reads cannot manufacture this join."""
    review_value_to_payload(record)
    review_value_to_payload(inputs)
    if type(result) is not issue.IssueMutationResult:
        _refuse("original_scope_result_required")
    encode_issue_result(result)
    expected = scope_input_record(record, inputs.decision.review, inputs.decision)
    if inputs != expected:
        _refuse("original_scope_inputs_mismatch")
    before = record.issue_read
    projection = result.projection
    if before.projection is None:
        _refuse("original_review_projection_required")
    if (
        result.outcome
        not in (
            issue.IssueMutationOutcome.APPLIED,
            issue.IssueMutationOutcome.IDEMPOTENT,
        )
        or result.operation_ref != issue.ISSUE_BIND_SCOPE_OPERATION_REF
        or result.issue_ref != inputs.request.issue_ref
        or (result.provider_ref, result.provider_distribution, result.provider_version)
        != (before.provider_ref, before.provider_distribution, before.provider_version)
        or result.source_sha256_before != inputs.request.expected_source_sha256
        or result.source_sha256_after is None
        or projection is None
        or projection.issue_ref != before.issue_ref
        or projection.tag != record.request.target.issue_tag
        or projection.source_path != before.projection.source_path
        or projection.source_digest != result.source_sha256_after
        or tuple(sorted(projection.ownership_scope)) != inputs.scope_paths
        or projection.owner_ref != record.request.execution_ref
        or projection.status != "in_progress"
    ):
        _refuse("complete_correlated_scope_postimage_required")
    return result


def _complete_guards(record: v.SetupReviewRecord) -> tuple[str, str, str]:
    guards = record.review_guards
    if (
        guards.issue_source_sha256 is None
        or guards.authority_manifest_sha256 is None
        or guards.plan_sha256 is None
    ):
        _refuse("complete_original_guards_required")
    return (
        guards.issue_source_sha256,
        guards.authority_manifest_sha256,
        guards.plan_sha256,
    )


class WorkspaceSetupReviewRuntime:
    """Retain exact owner returns; only the original A1 driver can apply setup."""

    def __init__(
        self,
        *,
        repository_root,
        evidence_root,
        execution_id,
        authority_manifest_locator,
        storage_factory,
    ):
        self.repository = repository_root
        self.execution = execution_id
        self.manifest = authority_manifest_locator
        self.pid, self.thread = os.getpid(), threading.get_ident()
        self._lock = threading.Lock()
        self._closed = None
        self._terminal = False
        self._scope_inputs = {}
        self._apply_inputs = {}
        self._continuations = {}
        self._decisions = set()
        self._completed_scope = set()
        self._applied = set()
        self._workspace_cleanup = self._issue_cleanup = None
        self._issue_cleanup_diagnostics = ()
        self._outcome = self._reference = self._target = None
        self._store: _ReviewStorage | None = None
        try:
            review_attempt_key(execution_id, "factory")
            review_value_to_payload(
                v.SetupTarget(
                    str(repository_root),
                    "selection",
                    "selection",
                    authority_manifest_locator,
                )
            )
            self._store = storage_factory(
                repository_root=repository_root,
                evidence_root=evidence_root,
                authority_manifest_locator=authority_manifest_locator,
            )
        except BaseException as error:  # noqa: BLE001 - typed construction failure includes interruptions
            self._raise_failure(error, "construction")

    @property
    def store(self) -> _ReviewStorage:
        if self._store is None:
            _refuse("review_storage_not_constructed")
        return self._store

    def _retention(self):
        if self._store is None:
            return v.RetentionEvidence(
                "not_attempted", None, None, (), (), None, False, (), None
            )
        return self.store.retention()

    def _raise_failure(self, error, phase):
        retention_error = None
        refusal = None
        primary = error
        owner_cleanup_error = getattr(error, "setup_review_issue_cleanup_failure", None)
        if (
            type(error) is _CurrentInputRefusal
            and phase in ("read_review", "record_review_decision", "apply_reviewed")
            and self._outcome is None
        ):
            # The refusal is distinct from the physical attempt to retain it.
            # Do not clear prior uncertainty or label unwritten bytes captured.
            self._reference = error.reference
            try:
                refusal = v.SetupRefusalRecord(
                    error.reference,
                    error.record.request,
                    error.code,
                    phase,
                    error.observed_issue,
                    error.sources,
                    self._issue_cleanup if error.sources is not None else None,
                    tuple(self.store.reads),
                    error.scope_decision,
                    error.apply_decision,
                    error.inputs_ref,
                    "not_invoked",
                    False,
                )
                if isinstance(owner_cleanup_error, BaseException) and not isinstance(
                    owner_cleanup_error, Exception
                ):
                    raise owner_cleanup_error
                self._reference_for(
                    refusal,
                    attempt=error.reference.attempt_ref,
                    kind="refusal",
                    target=error.reference.target,
                )
            except BaseException as capture_error:  # noqa: BLE001 - preserve primary denial and capture interruption separately
                self._terminal = True
                retention_error = (
                    capture_error if capture_error is not owner_cleanup_error else None
                )
                self.store.failed(capture_error)
                if not isinstance(capture_error, Exception):
                    error = capture_error
                    BaseException.__setattr__(
                        error, "setup_review_primary_failure", primary
                    )
        elif self._store is not None:
            self.store.failed(error)
        retention = self._retention()
        if self._store is None:
            from aware_file_system.private_directory import (
                PrivateDirectoryCleanup,
                PrivateDirectoryRefusal,
            )

            physical = (
                error.evidence if type(error) is PrivateDirectoryRefusal else None
            )
            cleanup = getattr(error, "private_directory_cleanup", None)
            if type(cleanup) is not PrivateDirectoryCleanup:
                cleanup = (
                    physical.cleanup
                    if physical is not None
                    and type(physical.cleanup) is PrivateDirectoryCleanup
                    else None
                )
            retention = v.RetentionEvidence(
                "incomplete"
                if physical is not None or cleanup is not None
                else "not_attempted",
                None,
                None,
                (),
                (),
                cleanup,
                False,
                (),
                physical,
            )
            if cleanup is not None:
                self._closed = v.SetupReviewClientCleanup(
                    None, None, cleanup, cleanup.release == "confirmed", ()
                )
        code = getattr(primary, "code", None)
        if (
            type(error) is SetupReviewValueError
            and error.args
            and type(error.args[0]) is str
        ):
            code = error.args[0]
        if type(code) is not str or not code or len(code.encode("utf-8")) > 128:
            code = "setup_review_failed"
        cleanup = self._closed
        if cleanup is None and self._issue_cleanup_diagnostics:
            # A missing owner return cannot inherit a prior client's confirmed
            # release or be upgraded by later private-directory cleanup.
            cleanup = v.SetupReviewClientCleanup(
                self._workspace_cleanup,
                self._issue_cleanup,
                self.store.cleanup,
                False,
                self._issue_cleanup_diagnostics,
            )
        failure = v.SetupReviewFailure(
            code,
            phase,
            self._target,
            self._outcome,
            self._reference,
            retention,
            cleanup,
            not isinstance(error, Exception),
            tuple(self.store.reads) if self._store is not None else (),
            refusal,
        )
        if not isinstance(error, Exception):
            BaseException.__setattr__(error, "setup_review_failure", failure)
            if retention_error is not None:
                BaseException.__setattr__(
                    error, "setup_review_retention_error", retention_error
                )
            raise error
        raise v.SetupReviewError(
            code, failure=failure, retention_error=retention_error
        ) from error

    @contextmanager
    def _action(self, phase):
        acquired = False
        try:
            if (self.pid, self.thread) != (os.getpid(), threading.get_ident()):
                _refuse("original_review_execution_required")
            if self._closed is not None or self._store is None or self._terminal:
                _refuse("review_client_released")
            acquired = self._lock.acquire(blocking=False)
            if not acquired:
                _refuse("review_action_in_progress")
            self.store.begin()
            self._outcome = self._reference = self._target = None
            self.store.current()
            yield
        except BaseException as error:
            if acquired:
                self._raise_failure(error, phase)
            # A rejected foreign/reentrant caller must not mutate the active
            # action's retention state or borrow its result/cleanup authority.
            code = (
                error.args[0]
                if type(error) is SetupReviewValueError
                else "review_action_unavailable"
            )
            failure = v.SetupReviewFailure(
                code,
                phase,
                None,
                None,
                None,
                v.RetentionEvidence(
                    "not_attempted", None, None, (), (), None, False, (), None
                ),
                None,
                not isinstance(error, Exception),
            )
            if not isinstance(error, Exception):
                BaseException.__setattr__(error, "setup_review_failure", failure)
                raise
            raise v.SetupReviewError(code, failure=failure) from error
        finally:
            if acquired:
                self._lock.release()

    def _check_target(self, target):
        review_value_to_payload(target)
        if (
            target.repository_root != str(self.repository)
            or target.authority_manifest_locator != self.manifest
        ):
            _refuse("review_target_mismatch")
        self._target = target

    def _reference_for(self, record, *, attempt, kind, target):
        raw = review_value_to_json(record).encode("utf-8")
        wire = v.REVIEW_SCHEMA_IDS[type(record)]
        if wire is None:
            _refuse("serializable_original_review_type_required")
        name = f"a1-{attempt}-{kind}.json"
        self.store.write_metadata(name, raw)
        reference = v.SetupEvidenceRef(
            str(self.store.root),
            self.store.identity,
            name,
            wire,
            _digest(raw),
            len(raw),
            attempt,
            target,
        )
        review_value_to_payload(reference)
        self._reference = reference
        return reference

    def _load(self, reference, *, expected_target):
        from aware_workspace_sdk.architecture_setup_review_codec import (
            review_value_from_json,
        )

        self._check_target(expected_target)
        review_value_to_payload(reference)
        if (
            reference.target != expected_target
            or reference.evidence_root != str(self.store.root)
            or reference.root_identity != self.store.identity
            or len(reference.attempt_ref) != 64
            or any(c not in "0123456789abcdef" for c in reference.attempt_ref)
        ):
            _refuse("review_reference_target_mismatch")
        catalog = {
            v.REVIEW_SCHEMA_IDS[cls]: (cls, kind)
            for cls, kind in (
                (v.SetupReviewRecord, "review"),
                (v.SetupScopeInputRecord, "scope-input"),
                (v.SetupApplyInputRecord, "apply-input"),
                (v.SetupScopeOutcomeRecord, "scope-outcome"),
                (v.SetupOutcomeRecord, "outcome"),
                (v.SetupDispatchIntent, "intent"),
                (v.SetupRefusalRecord, "refusal"),
            )
        }
        if reference.record_contract not in catalog:
            _refuse("unsupported_review_record")
        cls, kind = catalog[reference.record_contract]
        if (
            kind != "intent"
            and reference.locator != f"a1-{reference.attempt_ref}-{kind}.json"
        ):
            _refuse("review_record_locator_mismatch")
        raw = self.store.read(
            reference.locator,
            size=reference.record_bytes,
            sha256=reference.record_sha256,
        )
        value = review_value_from_json(cls, raw.decode("utf-8"))
        if kind == "intent" and (
            type(value) is not v.SetupDispatchIntent
            or reference.locator != f"a1-{value.action_key[7:]}-intent.json"
        ):
            _refuse("review_intent_locator_mismatch")
        return value, raw

    def _current_issue(self, record, reference):
        current = self.store.read_issue(record.request.target.issue_tag)
        if current.outcome not in (
            issue.IssueReadProjectionResolveOutcome.FOUND,
            issue.IssueReadProjectionResolveOutcome.ABSENT,
        ):
            _refuse("review_issue_read_incomplete")
        # The owner wire intentionally excludes raw Markdown. Compare the exact
        # owner projection, including its source digest, rather than treating
        # the decoder's intentionally absent raw body as source drift.
        if encode_issue_result(current) != encode_issue_result(record.issue_read):
            raise _CurrentInputRefusal(
                "review_issue_changed",
                record=record,
                reference=reference,
                observed_issue=current,
            )
        # Reuse the original source owner; do not read or reconstruct authority.
        from aware_issue_sdk.workspace_setup_admission import (
            IssueWorkspaceSetupAdmissionClient,
        )

        issuer = None
        primary = None
        try:
            issuer = IssueWorkspaceSetupAdmissionClient.filesystem(
                repository_root=self.repository,
                execution_id=self.execution,
                authority_manifest_locator=self.manifest,
            )
            self._issue_cleanup = None
            sources = issuer.observe_authority_sources(
                issue_ref=record.request.target.issue_path
            )
            if not sources.ledger_complete:
                _refuse("review_authority_sources_incomplete")
            if (
                sources.issue_source.content_sha256
                != record.review_guards.issue_source_sha256
                or sources.authority_manifest_source.content_sha256
                != record.review_guards.authority_manifest_sha256
            ):
                raise _CurrentInputRefusal(
                    "review_authority_sources_changed",
                    record=record,
                    reference=reference,
                    observed_issue=current,
                    sources=sources,
                )
        except BaseException as error:
            primary = error
            raise
        finally:
            if issuer is not None:
                diagnostic = "issue_client_cleanup_unavailable"
                try:
                    # Exactly one release attempt, even when its return is lost.
                    self._issue_cleanup = issuer.release_client()
                    diagnostic = "issue_client_cleanup_incomplete"
                    if (
                        self._issue_cleanup.outcome != "confirmed"
                        or not self._issue_cleanup.ledger_complete
                    ):
                        _refuse("review_issue_cleanup_incomplete")
                except BaseException as cleanup_error:
                    self._terminal = True
                    self._issue_cleanup_diagnostics = (diagnostic,)
                    original = primary if primary is not None else cleanup_error
                    BaseException.__setattr__(
                        original, "setup_review_issue_cleanup_failure", cleanup_error
                    )
                    BaseException.__setattr__(
                        original, "setup_review_issue_cleanup", self._issue_cleanup
                    )
                    if primary is None:
                        raise

    def _read_review(self, reference, *, expected_target, purpose):
        from aware_workspace_sdk.architecture_setup_command_values import (
            command_value_from_json,
        )

        if purpose not in ("history", "current_use"):
            _refuse("explicit_review_purpose_required")
        record, _ = self._load(reference, expected_target=expected_target)
        if type(record) is not v.SetupReviewRecord:
            _refuse("original_review_record_required")
        if reference.attempt_ref != review_attempt_key(
            record.request.execution_ref, record.request.client_intent_id
        ):
            _refuse("review_attempt_mismatch")
        raw = self.store.read_capture(record.capture, attempt=reference.attempt_ref)
        evidence = command_value_from_json(
            WorkspaceSetupA1CommandEvidence, raw.decode("utf-8")
        )
        validate_review_capture(record, evidence)
        _review_reference(record, reference)
        if purpose == "current_use":
            if record.request.execution_ref != self.execution:
                _refuse("fresh_execution_review_required")
            self._current_issue(record, reference)
        return v.SetupReviewRead(
            reference,
            record,
            evidence,
            purpose,
            self.store.current(),
            tuple(self.store.reads),
        )

    def read_review(self, reference, *, expected_target, purpose):
        with self._action("read_review"):
            return self._read_review(
                reference, expected_target=expected_target, purpose=purpose
            )

    def _run_driver(self, request, *, mode, guards, final=()):
        from .architecture_setup_a1_driver import run_setup_a1

        try:
            evidence, _ = run_setup_a1(
                request, mode=mode, review_guards=guards, allowed_final_files=final
            )
        except BaseException as error:
            evidence = getattr(error, "setup_command_evidence", None)
            if type(evidence) is WorkspaceSetupA1CommandEvidence:
                self._remember_command(evidence)
            raise
        self._remember_command(evidence)
        return evidence

    def _remember_command(self, evidence):
        self._workspace_cleanup = evidence.client_cleanup.workspace
        self._issue_cleanup = evidence.client_cleanup.issue
        self._outcome = v.SetupCommandOutcome(
            evidence.command_status, evidence, None, self._retention(), (), False
        )

    def preview_review(self, request, *, scope_continuation=None):
        from aware_workspace_sdk.architecture_setup_command_values import (
            WorkspaceSetupA1ReviewGuards,
            command_value_to_json,
        )

        with self._action("preview_review"):
            review_value_to_payload(request)
            self._check_target(request.target)
            if (
                request.execution_ref != self.execution
                or request.architecture_request.operation != "repository"
            ):
                _refuse("review_profile_or_execution_mismatch")
            first = None
            if scope_continuation is not None:
                retained = self._continuations.get(id(scope_continuation))
                if retained is not scope_continuation:
                    _refuse("original_scope_continuation_required")
                first = self._read_review(
                    scope_continuation.first_review,
                    expected_target=request.target,
                    purpose="history",
                ).record
                validate_scope_result(
                    first,
                    scope_continuation.scope_inputs.record,
                    scope_continuation.original_result,
                )
                old = first.request
                if (
                    request.target,
                    request.architecture_request,
                    request.execution_ref,
                    request.actor_ref,
                    request.actor_evidence_ref,
                    request.include_issue_lifecycle,
                ) != (
                    old.target,
                    old.architecture_request,
                    old.execution_ref,
                    old.actor_ref,
                    old.actor_evidence_ref,
                    old.include_issue_lifecycle,
                ):
                    _refuse("scope_continuation_request_mismatch")
                if request.client_intent_id == old.client_intent_id:
                    _refuse("distinct_second_preview_intent_required")
            read = self.store.read_issue(request.target.issue_tag)
            if read.projection is None:
                _refuse("original_issue_projection_required")
            if (
                scope_continuation is not None
                and read.projection != scope_continuation.original_result.projection
            ):
                _refuse("scope_postimage_changed")
            original = WorkspaceSetupA1CommandRequest(
                request.architecture_request,
                None,
                request.target.repository_root,
                self.manifest,
                request.target.issue_path,
                self.execution,
                request.client_intent_id,
            )
            # Explicit declared actor metadata is carried by the original driver.
            from .architecture_setup_a1_driver import run_setup_a1

            try:
                evidence, _ = run_setup_a1(
                    original,
                    mode="preview",
                    review_guards=WorkspaceSetupA1ReviewGuards(None, None, None),
                    actor_ref=request.actor_ref,
                    actor_evidence_ref=request.actor_evidence_ref,
                )
            except BaseException as error:
                partial = getattr(error, "setup_command_evidence", None)
                if type(partial) is WorkspaceSetupA1CommandEvidence:
                    self._remember_command(partial)
                raise
            self._remember_command(evidence)
            if (
                evidence.command_status != "preview_completed"
                or not evidence.completion_verified
            ):
                _refuse("complete_original_preview_required")
            correspondence = review_correspondence(evidence)
            if first is not None and (
                correspondence != first.correspondence_sha256
                or evidence.review_guards.authority_manifest_sha256
                != first.review_guards.authority_manifest_sha256
                or evidence.review_guards.plan_sha256 != first.review_guards.plan_sha256
            ):
                _refuse("second_review_plan_changed")
            attempt = review_attempt_key(self.execution, request.client_intent_id)
            raw = command_value_to_json(evidence).encode("utf-8")
            capture = self.store.write_capture(raw, attempt=attempt, kind="command_v1")
            physical, final = reviewed_path_sets(evidence)
            record = v.SetupReviewRecord(
                request,
                capture,
                read,
                evidence.review_guards,
                tuple(read.projection.ownership_scope),
                physical,
                final,
                correspondence,
                None
                if scope_continuation is None
                else scope_continuation.scope_outcome_ref,
                True,
                (),
            )
            validate_review_capture(record, evidence)
            reference = self._reference_for(
                record, attempt=attempt, kind="review", target=request.target
            )
            return self._read_review(
                reference, expected_target=request.target, purpose="current_use"
            )

    def _intent(self, action, reference, inputs_ref, decision):
        key = review_action_key(action, reference.record_sha256)
        intent = v.SetupDispatchIntent(
            action,
            reference,
            inputs_ref,
            self.execution,
            decision.client_intent_id,
            key,
            False,
        )
        raw = review_value_to_json(intent).encode("utf-8")
        name = f"a1-{key[7:]}-intent.json"
        self.store.write_metadata(name, raw)
        result = v.SetupEvidenceRef(
            str(self.store.root),
            self.store.identity,
            name,
            "aware.workspace.setup-review.setup-dispatch-intent.v1",
            _digest(raw),
            len(raw),
            review_attempt_key(self.execution, decision.client_intent_id),
            reference.target,
        )
        self.store.intent = result
        return result

    def record_review_decision(self, reference, *, decision):
        with self._action("record_review_decision"):
            review_value_to_payload(decision)
            if type(decision) not in (v.SetupScopeDecision, v.SetupApplyDecision):
                _refuse("explicit_original_decision_required")
            try:
                review = self._read_review(
                    reference, expected_target=reference.target, purpose="current_use"
                )
            except _CurrentInputRefusal as error:
                if type(decision) is v.SetupScopeDecision:
                    error.scope_decision = decision
                else:
                    error.apply_decision = decision
                raise
            action = "scope" if type(decision) is v.SetupScopeDecision else "apply"
            key = review_action_key(action, reference.record_sha256)
            if key in self._decisions or len(self._decisions) >= 128:
                _refuse("review_decision_spent_or_capacity_exceeded")
            self._decisions.add(key)
            attempt = review_attempt_key(self.execution, decision.client_intent_id)
            if type(decision) is v.SetupScopeDecision:
                record = scope_input_record(review.record, reference, decision)
                inputs_ref = self._reference_for(
                    record, attempt=attempt, kind="scope-input", target=reference.target
                )
                intent_ref = self._intent(action, reference, inputs_ref, decision)
                result = v.ReviewedSetupScopeInputs(inputs_ref, record, intent_ref)
                self._scope_inputs[id(result)] = result
            else:
                if type(decision) is not v.SetupApplyDecision:
                    _refuse("explicit_original_decision_required")
                record = apply_input_record(review.record, reference, decision)
                inputs_ref = self._reference_for(
                    record, attempt=attempt, kind="apply-input", target=reference.target
                )
                result = v.ReviewedSetupApplyInputs(inputs_ref, record)
                self._apply_inputs[id(result)] = result
            return result

    def record_scope_outcome(self, scope_inputs, *, outcome):
        with self._action("record_scope_outcome"):
            if (
                self._scope_inputs.get(id(scope_inputs)) is not scope_inputs
                or id(scope_inputs) in self._completed_scope
            ):
                _refuse("original_unconsumed_scope_inputs_required")
            if type(outcome) not in (
                issue.IssueMutationResult,
                issue.IssueMutationError,
                v.SetupUnknownScopeOutcome,
            ):
                _refuse("original_scope_outcome_required")
            try:
                return self._finish_scope_outcome(scope_inputs, outcome=outcome)
            except BaseException as error:
                self.store.failed(error)
                completion = v.SetupScopeCompletion(
                    "incomplete",
                    None,
                    outcome,
                    None,
                    self._retention(),
                    ("scope_outcome_retention_incomplete",),
                )
                if not isinstance(error, Exception):
                    BaseException.__setattr__(
                        error, "setup_scope_completion", completion
                    )
                    raise
                return completion

    def _finish_scope_outcome(self, scope_inputs, *, outcome):
        from aware_issue_sdk.operation_codec import encode_issue_result

        if (
            self._scope_inputs.get(id(scope_inputs)) is not scope_inputs
            or id(scope_inputs) in self._completed_scope
        ):
            _refuse("original_unconsumed_scope_inputs_required")
        self._completed_scope.add(id(scope_inputs))
        reference = scope_inputs.record.decision.review
        first = self._read_review(
            reference, expected_target=reference.target, purpose="history"
        ).record
        stored, _ = self._load(scope_inputs.reference, expected_target=reference.target)
        intent, _ = self._load(
            scope_inputs.intent_ref, expected_target=reference.target
        )
        if (
            type(intent) is not v.SetupDispatchIntent
            or stored != scope_inputs.record
            or intent.inputs_ref != scope_inputs.reference
            or intent.review != reference
        ):
            _refuse("scope_input_intent_mismatch")
        capture = unknown = None
        attempt = scope_inputs.reference.attempt_ref
        if type(outcome) is issue.IssueMutationResult:
            raw = json.dumps(
                encode_issue_result(outcome),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
            kind = "result"
            capture = self.store.write_capture(
                raw, attempt=attempt, kind="issue_result_v1"
            )
        elif type(outcome) is issue.IssueMutationError:
            raw = json.dumps(
                outcome.to_wire(),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
            kind = "failure"
            capture = self.store.write_capture(
                raw, attempt=attempt, kind="issue_failure_v1"
            )
        elif type(outcome) is v.SetupUnknownScopeOutcome:
            review_value_to_payload(outcome)
            kind, unknown = "unknown", outcome
        else:
            _refuse("original_scope_outcome_required")
        record = v.SetupScopeOutcomeRecord(
            scope_inputs.reference,
            scope_inputs.intent_ref,
            kind,
            capture,
            unknown,
            False,
        )
        result_ref = self._reference_for(
            record, attempt=attempt, kind="scope-outcome", target=reference.target
        )
        continuation = None
        status = "refused"
        diagnostics = ()
        if type(outcome) is issue.IssueMutationResult:
            try:
                validate_scope_result(first, scope_inputs.record, outcome)
            except (ValueError, TypeError):
                diagnostics = ("scope_result_not_continuable",)
            else:
                continuation = v.SetupScopeContinuation(
                    reference,
                    scope_inputs,
                    result_ref,
                    scope_inputs.record.request,
                    outcome,
                )
                self._continuations[id(continuation)] = continuation
                status = "continuation_ready"
        return v.SetupScopeCompletion(
            status,
            result_ref,
            outcome,
            continuation,
            self._retention(),
            diagnostics,
        )

    def apply_reviewed(self, inputs, *, client_intent_id):
        from aware_workspace_sdk.architecture_setup_command_values import (
            command_value_to_json,
        )

        with self._action("apply_reviewed"):
            if (
                self._apply_inputs.get(id(inputs)) is not inputs
                or id(inputs) in self._applied
            ):
                _refuse("original_unconsumed_apply_inputs_required")
            if client_intent_id != inputs.record.decision.client_intent_id:
                _refuse("apply_intent_mismatch")
            self._applied.add(id(inputs))
            reference = inputs.record.decision.review
            try:
                review = self._read_review(
                    reference, expected_target=reference.target, purpose="current_use"
                )
            except _CurrentInputRefusal as error:
                error.apply_decision = inputs.record.decision
                error.inputs_ref = inputs.reference
                raise
            stored, _ = self._load(inputs.reference, expected_target=reference.target)
            if (
                type(stored) is not v.SetupApplyInputRecord
                or stored != inputs.record
                or stored
                != apply_input_record(review.record, reference, stored.decision)
            ):
                _refuse("original_apply_inputs_mismatch")
            intent = self._intent(
                "apply", reference, inputs.reference, inputs.record.decision
            )
            evidence = self._run_driver(
                inputs.record.request,
                mode="apply",
                guards=inputs.record.review_guards,
                final=inputs.record.final_files,
            )
            # Keep the original outcome accessible before any fallible retention.
            self._outcome = v.SetupCommandOutcome(
                evidence.command_status, evidence, None, self._retention(), (), False
            )
            raw = command_value_to_json(evidence).encode("utf-8")
            capture = self.store.write_capture(
                raw, attempt=inputs.reference.attempt_ref, kind="command_v1"
            )
            record = v.SetupOutcomeRecord(
                inputs.reference,
                intent,
                evidence.command_status,
                capture,
                self._retention(),
                False,
            )
            result_ref = self._reference_for(
                record,
                attempt=inputs.reference.attempt_ref,
                kind="outcome",
                target=reference.target,
            )
            self._outcome = v.SetupCommandOutcome(
                evidence.command_status,
                evidence,
                result_ref,
                self._retention(),
                (),
                False,
            )
            return self._outcome

    def read_evidence(self, reference, *, expected_target):
        with self._action("read_evidence"):
            value, raw = self._load(reference, expected_target=expected_target)
            capture = getattr(value, "capture", None)
            if capture is not None:
                raw = self.store.read_capture(capture, attempt=reference.attempt_ref)
            return v.SetupEvidenceRead(
                reference, raw, self.store.current(), tuple(self.store.reads)
            )

    def release_client(self):
        if self._closed is not None:
            return self._closed
        if (self.pid, self.thread) != (
            os.getpid(),
            threading.get_ident(),
        ) or not self._lock.acquire(blocking=False):
            _refuse("original_idle_review_client_required")
        try:
            complete = True
            diagnostics = self._issue_cleanup_diagnostics
            cleanup = None
            try:
                cleanup = self.store.release()
                complete = (
                    cleanup is not None
                    and cleanup.release == "confirmed"
                    and cleanup.observation.ledger_complete
                    and not self._issue_cleanup_diagnostics
                    and all(
                        owner is None
                        or owner.outcome == "confirmed"
                        and owner.ledger_complete
                        for owner in (self._workspace_cleanup, self._issue_cleanup)
                    )
                )
            except BaseException as error:  # noqa: BLE001 - preserve interruption after once-only release
                complete = False
                diagnostics += ("private_directory_cleanup_unavailable",)
                cleanup = self.store.cleanup
                self._closed = v.SetupReviewClientCleanup(
                    self._workspace_cleanup,
                    self._issue_cleanup,
                    cleanup,
                    False,
                    diagnostics,
                )
                self._raise_failure(error, "release_client")
            finally:
                self._scope_inputs.clear()
                self._apply_inputs.clear()
                self._continuations.clear()
            self._closed = v.SetupReviewClientCleanup(
                self._workspace_cleanup,
                self._issue_cleanup,
                cleanup,
                complete,
                diagnostics,
            )
            return self._closed
        finally:
            self._lock.release()
