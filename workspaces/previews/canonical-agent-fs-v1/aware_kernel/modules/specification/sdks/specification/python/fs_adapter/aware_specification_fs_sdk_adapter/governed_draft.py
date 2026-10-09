"""Optional source-only composition of original owners, never a second writer.

Ownership transfers after genuine Issue admission. A failed issuance may have
already attempted physical cleanup; unavailable owner knowledge stays unknown.
"""

from __future__ import annotations

import copy
import hashlib
import os
import secrets
import threading
from contextlib import AbstractContextManager
from dataclasses import replace
from importlib import import_module
from typing import Any, cast

from aware_specification_runtime import SpecificationSnapshot
from aware_specification_sdk import (
    SPECIFICATION_DRAFT_CLEANUP_PROFILE,
    SpecificationDraftCleanupEvidence,
    SpecificationDraftCleanupInvocation,
    SpecificationDraftCleanupLedger,
    SpecificationDraftCleanupRequest,
    SpecificationDraftEvidence,
    SpecificationDraftInputCustodyObservation,
    SpecificationDraftInputResourceObservation,
    SpecificationDraftIssueCleanup,
    SpecificationDraftMemberBinding,
    SpecificationDraftPhysicalCleanup,
    SpecificationDraftPhysicalEffect,
    SpecificationDraftRequest,
    SpecificationDraftResult,
    SpecificationObserveRequest,
    SpecificationOperationError,
    SpecificationSdkClient,
)
from aware_specification_sdk.draft_cleanup import (
    require_cleanup_extension,
    snapshot_draft_cleanup,
)

from .draft import render_draft
from .provider import SpecificationFsSdkProvider


def _digest(body: bytes) -> str:
    return "sha256:" + hashlib.sha256(body).hexdigest()


class _GovernedDraft(AbstractContextManager[SpecificationSdkClient]):
    def __init__(
        self,
        *,
        request: SpecificationDraftRequest,
        issue_provider: object,
        issue_ref: str,
        expected_issue_sha256: str,
        protocol_draft_target: object,
        physical_package_plan: object,
        client_intent_id: str,
        input_custody: object | None = None,
    ) -> None:
        self.attempt_ref = "specification-draft:" + secrets.token_hex(16)
        self.context_ref = "specification-context:" + secrets.token_hex(16)
        self.context_state = "not_entered"
        self.physical_invocation = SpecificationDraftCleanupInvocation(
            "unknown", "not_invoked", ()
        )
        self.protocol_invocation = SpecificationDraftCleanupInvocation(
            "unknown", "not_invoked", ()
        )
        self.cleanup_last: SpecificationDraftCleanupEvidence | None = None
        self.issue_cleanup: SpecificationDraftIssueCleanup | None = None
        self.physical_cleanup: SpecificationDraftPhysicalCleanup | None = None
        self.cleanup_request: SpecificationDraftCleanupRequest | None = None
        self.diagnostics: list[str] = []
        self.issue_provider = issue_provider
        self.issue_ref = issue_ref
        self.issue_sha256 = expected_issue_sha256
        self.target = protocol_draft_target
        self.plan = physical_package_plan
        self.client_intent_id = client_intent_id
        self.pid = os.getpid()
        self.lock = threading.RLock()
        self.entered = self.closed = self.invoked = self.completed = False
        self.published = False
        self.staged_cleanup_uncertain = False
        # Optional owner exports are resolved at runtime, then checked through
        # their original issuers. Static Any here grants no structural authority.
        self.admission: Any = None
        self.binding: Any = None
        self.selection: object | None = None
        self.reader: SpecificationFsSdkProvider | None = None
        self.last: SpecificationDraftEvidence | None = None
        self.input_custody: SpecificationDraftInputCustodyObservation | None = None
        self.context_claim: Any = None
        self.custody_claim_invoked = False
        self.input_binding: Any = None
        try:
            if input_custody is not None:
                issue = import_module("aware_issue_fs_adapter")
                custody = import_module("aware_issue_fs_adapter.draft_package")
                self.custody_sdk = import_module("aware_issue_sdk.draft_input_custody")
                self.issue_sdk = import_module("aware_issue_sdk.draft_package")
                self.physical = import_module("aware_file_system.retained_package")
                if type(issue_provider) is not issue.FilesystemIssueOperationProvider:
                    raise SpecificationOperationError(
                        "original_issue_provider_required"
                    )
                self.custody_claim_invoked = True
                self.context_claim = custody.claim_draft_input_custody(
                    input_custody,
                    provider=issue_provider,
                    protocol_target=protocol_draft_target,
                    physical_plan=physical_package_plan,
                    client_intent_id=client_intent_id,
                    context_ref=self.context_ref,
                )
                # A registry-authenticated context handle, not a snapshot,
                # establishes association before rendering can fail.
                observed = self.context_claim.observe_cleanup()
                self._remember_custody(observed, adopt=True)
                self.input_binding = self.context_claim.observe_inputs()
                if (
                    type(self.input_binding)
                    is not self.custody_sdk.IssueDraftInputBinding
                ):
                    raise ValueError("draft_input_binding_invalid")
                self.input_binding.__post_init__()
                if (
                    self.input_binding.attempt_ref != self.attempt_ref
                    or self.input_binding.context_ref != self.context_ref
                    or self.input_binding.client_intent_id != client_intent_id
                    or self.input_custody is None
                    or self.input_binding.execution_ref
                    != self.input_custody.execution_ref
                ):
                    raise ValueError("draft_input_binding_mismatch")
                self.physical_invocation = replace(
                    self.physical_invocation, responsibility="context"
                )
                self.protocol_invocation = replace(
                    self.protocol_invocation, responsibility="context"
                )
            if type(request) is not SpecificationDraftRequest:
                raise SpecificationOperationError("invalid_draft_request")
            request.__post_init__()
            self.request = copy.deepcopy(request)
            self.members = tuple(sorted(render_draft(self.request).items()))
        except BaseException as error:
            if input_custody is None:
                # No custody transfer or Issue invocation occurred. Preserve
                # this compatibility constructor boundary without owner reads
                # or disposal of caller-supplied holders.
                raise SpecificationOperationError(
                    getattr(error, "code", "invalid_draft_request"),
                    effect="unknown",
                    cleanup_evidence=self._cleanup_value(),
                ) from error
            self._remember_cleanup_error(error)
            self._close()
            raise self._refusal(error) from error

    def __enter__(self) -> SpecificationSdkClient:
        with self.lock:
            if self.entered or self.closed or self.pid != os.getpid():
                raise SpecificationOperationError("governed_draft_context_terminal")
            self.entered = True
            self.context_state = "entering"
            try:
                try:
                    self.physical = import_module("aware_file_system.retained_package")
                    self.protocol = import_module("aware_protocol_fs_adapter")
                    issue = import_module("aware_issue_fs_adapter")
                    sdk = import_module("aware_issue_sdk.draft_package")
                    self.issue_sdk = sdk
                    # Resolve required owner ports before admission or effects.
                    for name in (
                        "require_specification_draft_target",
                        "admit_specification_draft_published_read",
                        "release_specification_draft_target",
                        "release_specification_selection",
                        "require_specification_selection",
                    ):
                        getattr(self.protocol, name)
                    for name in (
                        "require_retained_package_plan",
                        "observe_package_plan",
                        "validate_staged_package_source",
                        "require_retained_package_postimage",
                        "observe_package_cleanup",
                    ):
                        getattr(self.physical, name)
                    if (
                        type(self.issue_provider)
                        is not issue.FilesystemIssueOperationProvider
                    ):
                        raise SpecificationOperationError(
                            "original_issue_provider_required"
                        )
                except (ImportError, AttributeError) as error:
                    raise SpecificationOperationError(
                        "governed_draft_integration_unavailable"
                    ) from error
                if self.context_claim is None and (
                    self.physical.require_retained_package_plan(self.plan)
                    is not self.plan
                ):
                    raise SpecificationOperationError("original_physical_plan_required")
                # The public locator verifies the original registered target
                # and process without currentness validation/retirement. This
                # is identity only, not a fresh target or publication grant.
                if (
                    type(self.target)
                    is not self.protocol.SpecificationDraftTargetSelection
                ):
                    raise SpecificationOperationError(
                        "original_protocol_target_required"
                    )
                original_target_locator = (
                    cast(Any, self.target).target_locator
                    if self.context_claim is None
                    else self.input_binding.target_locator
                )
                # Original identity is not untransferred cleanup ownership.
                # Another context can already own these exact holders. No
                # available public port affirms absence of a prior claim here;
                # responsibility therefore remains unknown before issuance.
                target = (
                    self.protocol.require_specification_draft_target(self.target)
                    if self.context_claim is None
                    else self.input_binding
                )
                if self.context_claim is None and target is not self.target:
                    raise SpecificationOperationError(
                        "original_protocol_target_required"
                    )
                plan = (
                    self.physical.observe_package_plan(self.plan)
                    if self.context_claim is None
                    else self.input_binding
                )
                if (
                    plan.ordered_members != self.members
                    or (
                        plan.target_path
                        if self.context_claim is None
                        else plan.target_locator
                    )
                    != original_target_locator
                ):
                    raise SpecificationOperationError(
                        "draft_candidate_binding_mismatch"
                    )
                request = sdk.IssueDraftPackageRequest(
                    issue_ref=self.issue_ref,
                    expected_issue_sha256=self.issue_sha256,
                    manifest_locator=target.manifest_locator,
                    expected_manifest_sha256=target.manifest_sha256,
                    target_locator=target.target_locator,
                    scratch_locator=plan.scratch_path
                    if self.context_claim is None
                    else plan.scratch_locator,
                    ordered_members=self.members,
                    authoring_intent_ref=self.request.authoring_intent_ref,
                    client_intent_id=self.client_intent_id,
                )
                issuer = cast(Any, self.issue_provider)
                if not callable(getattr(issuer, "observe_draft_package_cleanup", None)):
                    raise SpecificationOperationError(
                        "governed_draft_integration_unavailable"
                    )
                self.cleanup_request = self._map_request(request)
                # From the actual invocation boundary the issuer may have
                # claimed or cleaned inputs even if no admission returns. Only
                # genuine owner disposition may resolve this uncertainty.
                self.physical_invocation = replace(
                    self.physical_invocation, responsibility="unknown"
                )
                self.protocol_invocation = replace(
                    self.protocol_invocation, responsibility="unknown"
                )
                self.admission = issuer.admit_draft_package(
                    request,
                    protocol_target=self.target,
                    physical_plan=self.plan,
                    input_custody=self.context_claim,
                )
                # The accepted transfer boundary precedes subsequent validation.
                self.physical_invocation = replace(
                    self.physical_invocation, responsibility="context"
                )
                self.protocol_invocation = replace(
                    self.protocol_invocation, responsibility="context"
                )
                issuer.validate_draft_package(self.admission)
                self.binding = issuer.observe_draft_package_binding(self.admission)
                if self.binding.request != request:
                    raise SpecificationOperationError("draft_initial_binding_mismatch")
                self.observe_draft_evidence()
                self.context_state = "entered"
                self.observe_draft_cleanup()
                return SpecificationSdkClient(self, draft_evidence_reader=self)
            except BaseException as error:
                self._remember_cleanup_error(error)
                self.observe_draft_cleanup()
                self._close()
                raise self._refusal(error) from error

    def _diagnostic(self, value: str) -> None:
        if value not in self.diagnostics:
            self.diagnostics.append(value)

    def _cleanup_value(self) -> SpecificationDraftCleanupEvidence:
        attempted, outcome = self._protocol_completion(self.input_custody)
        return SpecificationDraftCleanupEvidence(
            SPECIFICATION_DRAFT_CLEANUP_PROFILE,
            self.attempt_ref,
            self.context_state,
            self.issue_cleanup,
            self.physical_cleanup,
            self.physical_invocation,
            self.protocol_invocation,
            attempted,
            outcome,
            tuple(self.diagnostics),
            self.input_custody,
        )

    @staticmethod
    def _protocol_completion(
        custody: SpecificationDraftInputCustodyObservation | None,
    ) -> tuple[bool | None, str]:
        # This data came from the original Issue-owned context/admission read.
        # No release return, phase, physical outcome or fd scan substitutes.
        if (
            custody is None
            or custody.protocol.acquisition != "acquired"
            or any(
                value is None
                for value in (
                    custody.execution_ref,
                    custody.context_ref,
                    custody.root_locator,
                    custody.manifest_locator,
                    custody.manifest_sha256,
                    custody.target_locator,
                    custody.scratch_locator,
                )
            )
        ):
            return None, "unknown"
        return (
            custody.protocol.owner_cleanup_attempted,
            custody.protocol.owner_cleanup_outcome,
        )

    def _remember_custody(self, original: Any, *, adopt: bool = False) -> None:
        if type(original) is not self.custody_sdk.IssueDraftInputCustodyObservation:
            raise ValueError("draft_input_custody_invalid")
        original.__post_init__()
        if (
            original.context_ref != self.context_ref
            or original.client_intent_id != self.client_intent_id
        ):
            raise ValueError("draft_input_custody_context_mismatch")

        def resource(value: Any) -> SpecificationDraftInputResourceObservation:
            if type(value) is not self.custody_sdk.IssueDraftInputResourceObservation:
                raise ValueError("draft_input_resource_invalid")
            return SpecificationDraftInputResourceObservation(
                value.acquisition,
                value.responsibility,
                value.transfer,
                value.release_invocation,
                value.owner_cleanup_attempted,
                value.owner_cleanup_outcome,
                value.diagnostics,
            )

        mapped = SpecificationDraftInputCustodyObservation(
            original.attempt_ref,
            original.client_intent_id,
            original.execution_ref,
            original.custody_state,
            original.root_locator,
            original.manifest_locator,
            original.manifest_sha256,
            original.target_locator,
            original.scratch_locator,
            resource(original.physical),
            resource(original.protocol),
            None
            if original.physical_evidence is None
            else self._map_ledger(original.physical_evidence),
            original.diagnostics,
            original.context_ref,
        )
        if adopt:
            if self.cleanup_last is not None or self.input_custody is not None:
                raise ValueError("draft_custody_attempt_replay")
            self.attempt_ref = mapped.attempt_ref
        attempted, outcome = self._protocol_completion(mapped)
        candidate = replace(
            self._cleanup_value(),
            input_custody=mapped,
            protocol_owner_attempted=attempted,
            protocol_owner_outcome=outcome,
        )
        if self.cleanup_last is not None:
            require_cleanup_extension(self.cleanup_last, candidate)
        self.input_custody = mapped

    @staticmethod
    def _map_request(value: Any) -> SpecificationDraftCleanupRequest:
        return SpecificationDraftCleanupRequest(
            value.issue_ref,
            value.expected_issue_sha256,
            value.manifest_locator,
            value.expected_manifest_sha256,
            value.target_locator,
            value.scratch_locator,
            value.ordered_members,
            value.authoring_intent_ref,
            value.client_intent_id,
            value.intent,
            value.mode_profile,
            value.candidate_sha256,
            value.ordered_effect_paths,
        )

    @staticmethod
    def _map_ledger(
        value: Any, *, physical: bool = False
    ) -> SpecificationDraftCleanupLedger:
        return SpecificationDraftCleanupLedger(
            value.package_outcome,
            tuple(
                SpecificationDraftPhysicalEffect(
                    e.path,
                    e.kind,
                    e.state.value if physical else e.state,
                    e.mode,
                    e.before_digest,
                    e.after_digest,
                    None,
                    e.after_identity,
                    e.durability_confirmed,
                )
                for e in value.effects
            ),
            value.residual_scratch_paths,
            value.cleanup_diagnostics,
            value.durability_confirmed,
            None if physical else value.ledger_complete,
        )

    def _map_issue_cleanup(self, value: Any) -> SpecificationDraftIssueCleanup:
        if type(value) is not self.issue_sdk.IssueDraftPackageCleanupDisposition:
            raise ValueError("draft_cleanup_disposition_invalid")
        mapped = SpecificationDraftIssueCleanup(
            self._map_request(value.request),
            value.execution_ref,
            value.physical_claim,
            value.physical_cleanup_owner,
            value.physical_cleanup_attempted,
            value.physical_cleanup_outcome,
            value.protocol_cleanup_owner,
            None if value.evidence is None else self._map_ledger(value.evidence),
        )
        if self.cleanup_request is None or mapped.request != self.cleanup_request:
            raise ValueError("draft_cleanup_source_mismatch")
        return mapped

    def _remember_cleanup_error(self, error: BaseException) -> None:
        supplied_custody = getattr(error, "input_custody", None)
        if supplied_custody is not None and (
            self.context_claim is not None
            or (
                self.custody_claim_invoked
                and type(error) is self.custody_sdk.IssueDraftInputCustodyRefusal
            )
        ):
            try:
                self._remember_custody(
                    supplied_custody, adopt=self.input_custody is None
                )
            except (AttributeError, TypeError, ValueError):
                self._diagnostic("input_custody_evidence_invalid")
        # An owner can preserve its original refusal as a cause instead of
        # repeating its diagnostic fields. Read only the bounded public chain.
        cause: BaseException | None = error
        seen: set[int] = set()
        for _ in range(16):
            if cause is None or id(cause) in seen:
                break
            seen.add(id(cause))
            diagnostics = getattr(cause, "diagnostics", ())
            if type(diagnostics) is tuple:
                for diagnostic in diagnostics:
                    if type(diagnostic) is str and diagnostic:
                        self._diagnostic(diagnostic)
            cause = cause.__cause__ or cause.__context__
        supplied = getattr(error, "input_cleanup", None)
        if supplied is not None:
            try:
                candidate = replace(
                    self._cleanup_value(),
                    issue_disposition=self._map_issue_cleanup(supplied),
                )
                if self.cleanup_last is not None:
                    require_cleanup_extension(self.cleanup_last, candidate)
                self.issue_cleanup = candidate.issue_disposition
            except (AttributeError, TypeError, ValueError):
                self._diagnostic("issue_cleanup_disposition_invalid")

    def observe_draft_cleanup(self) -> SpecificationDraftCleanupEvidence:
        """Detached historical snapshots; never cleanup, currentness or a grant."""
        with self.lock:
            if self.context_claim is not None:
                try:
                    observer = (
                        self.admission.observe_input_custody
                        if self.admission is not None
                        else self.context_claim.observe_cleanup
                    )
                    self._remember_custody(observer(), adopt=self.input_custody is None)
                except BaseException:  # noqa: BLE001 - retain last valid custody history
                    self._diagnostic("input_custody_observation_unavailable")
            issue = self.issue_cleanup
            physical = self.physical_cleanup
            try:
                if self.admission is not None:
                    issue = self._map_issue_cleanup(self.admission.observe_cleanup())
                elif self.cleanup_request is not None:
                    provider = cast(Any, self.issue_provider)
                    issue = self._map_issue_cleanup(
                        provider.observe_draft_package_cleanup(
                            protocol_target=self.target, physical_plan=self.plan
                        )
                    )
            except BaseException:  # noqa: BLE001 - history lookup cannot replace the primary refusal
                self._diagnostic("issue_cleanup_observation_unavailable")
                # Retain original historical fields; the diagnostic records that
                # this lookup could not establish newer knowledge or completion.
            try:
                original = self.physical.observe_package_cleanup(self.plan)
                if type(original) is not self.physical.PackageCleanupObservation:
                    raise ValueError("physical_cleanup_observation_invalid")
                physical = SpecificationDraftPhysicalCleanup(
                    original.root_locator,
                    original.target_path,
                    original.scratch_path,
                    original.attempted,
                    original.outcome,
                    self._map_ledger(original.evidence, physical=True),
                )
                if self.cleanup_request is not None and (
                    physical.target_path,
                    physical.scratch_path,
                ) != (
                    self.cleanup_request.target_locator,
                    self.cleanup_request.scratch_locator,
                ):
                    raise ValueError("draft_cleanup_source_mismatch")
            except BaseException:  # noqa: BLE001 - physical observation does not grant cleanup or retry
                physical = self.physical_cleanup
                self._diagnostic("physical_cleanup_observation_unavailable")
            candidate = replace(
                self._cleanup_value(),
                issue_disposition=issue,
                physical_observation=physical,
            )
            if (
                self.context_claim is None
                and self.admission is None
                and self.cleanup_request is not None
            ):
                candidate = replace(
                    candidate,
                    physical_invocation=replace(
                        candidate.physical_invocation,
                        responsibility="caller"
                        if issue is not None
                        and issue.physical_claim == "unclaimed"
                        and issue.physical_cleanup_owner == "caller"
                        and issue.physical_cleanup_attempted is False
                        else "unknown",
                    ),
                    protocol_invocation=replace(
                        candidate.protocol_invocation,
                        responsibility="caller"
                        if issue is not None
                        and issue.physical_claim == "unclaimed"
                        and issue.protocol_cleanup_owner == "caller"
                        else "unknown",
                    ),
                )
            try:
                if self.cleanup_last is not None:
                    require_cleanup_extension(self.cleanup_last, candidate)
                self.issue_cleanup = issue
                self.physical_cleanup = physical
                self.physical_invocation = candidate.physical_invocation
                self.protocol_invocation = candidate.protocol_invocation
            except (AttributeError, TypeError, ValueError):
                self._diagnostic("draft_cleanup_history_unavailable")
                candidate = self._cleanup_value()
            self.cleanup_last = snapshot_draft_cleanup(candidate)
            return snapshot_draft_cleanup(self.cleanup_last)

    def _release_issue(self) -> None:
        if self.physical_invocation.invocation_state != "not_invoked":
            return
        # The genuine admission arbitrates once-only disposal of both resources.
        # A detached history lookup is not a prerequisite or a cleanup permit.
        self.physical_invocation = replace(
            self.physical_invocation, invocation_state="invoked"
        )
        self.protocol_invocation = replace(
            self.protocol_invocation, invocation_state="invoked"
        )
        try:
            self.admission.release()
        except BaseException as error:
            diagnostic = f"issue_release_failed:{type(error).__name__}"
            self.physical_invocation = replace(
                self.physical_invocation,
                invocation_state="raised",
                diagnostics=(diagnostic,),
            )
            self._diagnostic(diagnostic)
            self.protocol_invocation = replace(
                self.protocol_invocation,
                invocation_state="raised",
                diagnostics=(diagnostic,),
            )
            raise
        self.physical_invocation = replace(
            self.physical_invocation, invocation_state="returned"
        )
        self.protocol_invocation = replace(
            self.protocol_invocation, invocation_state="returned"
        )

    def _live(self) -> None:
        if not self.entered or self.closed or self.pid != os.getpid():
            raise SpecificationOperationError("governed_draft_context_terminal")

    def observe_draft_evidence(self) -> SpecificationDraftEvidence:
        """Historical original-attempt ledger, not a currentness/write entrance."""
        with self.lock:
            try:
                if self.binding is None or self.admission is None:
                    raise ValueError("draft_binding_unavailable")
                original = self.admission.evidence
                request = self.binding.request
                value = SpecificationDraftEvidence(
                    "specification.draft.fs-evidence.v1",
                    self.attempt_ref,
                    request.issue_ref,
                    self.binding.execution_ref,
                    request.client_intent_id,
                    request.authoring_intent_ref,
                    request.expected_manifest_sha256,
                    request.target_locator,
                    request.scratch_locator,
                    tuple(
                        SpecificationDraftMemberBinding(p, len(b), _digest(b))
                        for p, b in self.members
                    ),
                    original.package_outcome,
                    tuple(
                        SpecificationDraftPhysicalEffect(
                            e.path,
                            e.kind,
                            e.state,
                            e.mode,
                            e.before_digest,
                            e.after_digest,
                            None,
                            e.after_identity,
                            e.durability_confirmed,
                        )
                        for e in original.effects
                    ),
                    original.residual_scratch_paths,
                    (*original.cleanup_diagnostics, *self.diagnostics),
                    original.ledger_complete,
                    self.completed,
                    original.durability_confirmed,
                )
                if self.published and value.package_outcome != "published":
                    raise ValueError("draft_known_publication_regressed")
                if self.last is not None and (
                    value.effects[: len(self.last.effects)] != self.last.effects
                    or (
                        self.last.package_outcome == "published"
                        and value.package_outcome != "published"
                    )
                ):
                    raise ValueError("draft_evidence_history_mismatch")
                self.last = value
                return value
            except BaseException as error:
                self.completed = False
                if self.last is not None:
                    self.last = replace(
                        self.last,
                        package_outcome="published"
                        if self.published or self.last.package_outcome == "published"
                        else "unknown",
                        ledger_complete=False,
                        completion_verified=False,
                    )
                raise SpecificationOperationError(
                    "draft_evidence_unavailable",
                    effect="unknown",
                    evidence=self.last,
                    evidence_diagnostics=("draft_evidence_unavailable",),
                ) from error

    def _refusal(self, error: BaseException) -> SpecificationOperationError:
        self._remember_cleanup_error(error)
        cleanup = self.observe_draft_cleanup()
        try:
            evidence = (
                self.observe_draft_evidence() if self.admission is not None else None
            )
        except SpecificationOperationError as failure:
            evidence = failure.evidence
            return SpecificationOperationError(
                getattr(error, "code", "governed_draft_failed"),
                effect="unknown",
                evidence=evidence,
                evidence_diagnostics=failure.evidence_diagnostics,
                cleanup_evidence=cleanup,
            )
        return SpecificationOperationError(
            getattr(error, "code", "governed_draft_failed"),
            effect="unknown"
            if getattr(error, "effect", None) == "unknown"
            or self.staged_cleanup_uncertain
            or (
                evidence is None
                and (
                    cleanup.cleanup_diagnostics
                    or cleanup.issue_disposition is None
                    or cleanup.issue_disposition.physical_cleanup_outcome
                    in {"unknown", "incomplete"}
                )
            )
            or (evidence is not None and not evidence.ledger_complete)
            else "none"
            if evidence is None
            else evidence.package_outcome,
            evidence=evidence,
            cleanup_evidence=cleanup,
        )

    def _validate_staged(self) -> None:
        lens = self.admission.lend_staged_source()
        fd = lens.duplicate_parent_descriptor()
        provider = None
        primary: BaseException | None = None
        try:
            provider = SpecificationFsSdkProvider(fd, (lens.stage_name,))
            checked = provider._observe_adaptation(SpecificationObserveRequest())
            if checked.lowering.snapshot != SpecificationSnapshot(
                (self.request.definition,)
            ):
                raise SpecificationOperationError("draft_meaning_mismatch")
            actual = tuple(
                sorted(
                    (m.relative_path, m.canonical_body.encode("utf-8"))
                    for m in checked.lowering.closures[0].members
                )
            )
            if actual != self.members:
                raise SpecificationOperationError("draft_source_mismatch")
            # Original lens methods enforce their private bound owner claim;
            # SPEC never reconstructs or extracts it for lower validation.
            if (
                lens.stage_name
                != self.binding.request.scratch_locator.rsplit("/", 1)[-1]
            ):
                raise SpecificationOperationError("draft_stage_binding_mismatch")
            self.admission.validate_current()
        except BaseException as error:
            primary = error
            raise
        finally:
            failures = []
            # Close results may be ambiguous (including a close that applied
            # before raising). Never blindly retry or let cleanup mask meaning.
            for label, cleanup in (
                ("staged_reader_close", None if provider is None else provider.close),
                ("staged_descriptor_close", lambda: os.close(fd)),
            ):
                if cleanup is None:
                    continue
                try:
                    cleanup()
                except BaseException as error:  # noqa: BLE001 - attempt both original cleanups after interruption
                    failures.append(f"{label}_failed:{type(error).__name__}")
            if failures:
                self.completed = False
                self.staged_cleanup_uncertain = True
                self.diagnostics.extend(failures)
                if primary is not None:
                    for diagnostic in failures:
                        primary.add_note(diagnostic)
                    # The pending primary remains the outward refusal; the fixed
                    # evidence reader carries diagnostics and effect uncertainty.
                else:
                    raise SpecificationOperationError(
                        "draft_staged_cleanup_failed", effect="unknown"
                    )

    def _observe_published(self, request: SpecificationObserveRequest):
        if self.reader is None or self.selection is None:
            raise SpecificationOperationError("draft_publication_required")
        self.admission.validate_published_read(self.selection)
        observed = SpecificationSdkClient(self.reader).observe(request)
        if observed.snapshot != SpecificationSnapshot((self.request.definition,)):
            raise SpecificationOperationError("draft_meaning_mismatch")
        self.admission.validate_published_read(self.selection)
        return observed

    def observe(self, request: SpecificationObserveRequest):
        with self.lock:
            self._live()
            if self.reader is None:
                raise SpecificationOperationError("draft_publication_required")
            try:
                return self._observe_published(request)
            except BaseException as error:
                self.completed = False
                self._close()
                raise self._refusal(error) from error

    def create_draft(
        self, request: SpecificationDraftRequest
    ) -> SpecificationDraftResult:
        with self.lock:
            self._live()
            if self.invoked:
                raise SpecificationOperationError("draft_invocation_replay")
            self.invoked = True
            try:
                request.__post_init__()
                if (
                    request != self.request
                    or tuple(sorted(render_draft(request).items())) != self.members
                ):
                    raise SpecificationOperationError("draft_request_binding_mismatch")
                self.admission.validate_current()
                while self.admission.phase != "staged":
                    self.admission.stage_next_effect()
                self._validate_staged()
                image = self.admission.publish_package()
                self.published = True
                self.observe_draft_evidence()
                self.selection = self.admission.admit_published_read(
                    physical_postimage=image
                )
                self.reader = SpecificationFsSdkProvider.from_protocol_selection(
                    self.selection
                )
                self._observe_published(SpecificationObserveRequest())
                receipt = self.admission.finish(
                    physical_postimage=image, read_selection=self.selection
                )
                bound = self.binding.request
                if (
                    receipt.execution_ref != self.binding.execution_ref
                    or receipt.issue_ref != bound.issue_ref
                    or receipt.client_intent_id != bound.client_intent_id
                    or receipt.authoring_intent_ref != bound.authoring_intent_ref
                    or receipt.issue_sha256 != bound.expected_issue_sha256
                    or receipt.manifest_sha256 != bound.expected_manifest_sha256
                    or receipt.candidate_sha256 != bound.candidate_sha256
                    or receipt.ordered_effect_paths != bound.ordered_effect_paths
                ):
                    raise SpecificationOperationError(
                        "draft_completion_binding_mismatch"
                    )
                self.admission.validate_completed_current()
                self._release_issue()
                # Only the independent read remains current after writer release.
                observed = self._observe_published(SpecificationObserveRequest())
                self.completed = True
                evidence = self.observe_draft_evidence()
                return SpecificationDraftResult(
                    observed,
                    tuple(bound.target_locator + "/" + p for p, _ in self.members),
                    self.request.authoring_intent_ref,
                    evidence,
                )
            except BaseException as error:
                self.completed = False
                self._close()
                raise self._refusal(error) from error

    def _close(self) -> None:
        if self.closed:
            return
        self.closed = True
        self.context_state = "closed"
        if self.admission is None:
            if self.context_claim is not None:
                for name in ("physical_invocation", "protocol_invocation"):
                    value = getattr(self, name)
                    setattr(
                        self,
                        name,
                        replace(
                            value, responsibility="context", invocation_state="invoked"
                        ),
                    )
                try:
                    result = self.context_claim.release()
                    self._remember_custody(result, adopt=self.input_custody is None)
                except BaseException as error:  # noqa: BLE001 - preserve primary refusal and no retry
                    self._remember_cleanup_error(error)
                    diagnostic = f"input_custody_release_failed:{type(error).__name__}"
                    self._diagnostic(diagnostic)
                    for name in ("physical_invocation", "protocol_invocation"):
                        setattr(
                            self,
                            name,
                            replace(
                                getattr(self, name),
                                invocation_state="raised",
                                diagnostics=(diagnostic,),
                            ),
                        )
                else:
                    for name in ("physical_invocation", "protocol_invocation"):
                        setattr(
                            self,
                            name,
                            replace(getattr(self, name), invocation_state="returned"),
                        )
            self.observe_draft_cleanup()
            return  # Never retry Issue's cleanup or infer authority over rejected inputs.
        for label, cleanup in (
            ("issue_release", self._release_issue),
            ("spec_reader_close", None if self.reader is None else self.reader.close),
            (
                "protocol_read_release",
                None
                if self.selection is None
                else lambda: self.admission.release_published_read(self.selection),
            ),
        ):
            if cleanup is None:
                continue
            try:
                cleanup()
            except BaseException as error:  # noqa: BLE001 - attempt every owner cleanup after interruption
                self.completed = False
                diagnostic = f"{label}_failed:{type(error).__name__}"
                self._diagnostic(diagnostic)
        self.observe_draft_cleanup()

    def __exit__(self, exc_type, exc, traceback) -> None:
        with self.lock:
            failure = exc
            if failure is None and self.completed:
                try:
                    self._observe_published(SpecificationObserveRequest())
                except BaseException as error:  # noqa: BLE001 - final refusal still requires owner cleanup
                    self.completed = False
                    failure = error
            before = len(self.diagnostics)
            self._close()
            if failure is None and self.diagnostics:
                failure = SpecificationOperationError("draft_cleanup_failed")
            if failure is None and self.invoked and not self.completed:
                failure = SpecificationOperationError("draft_completion_unverified")
            if failure is not None:
                if exc is not None and not isinstance(exc, SpecificationOperationError):
                    for diagnostic in self.diagnostics[before:]:
                        exc.add_note(diagnostic)
                    return  # Preserve user/interrupt exceptions after all cleanup.
                raise self._refusal(failure) from failure


def open_governed_specification_draft(
    *,
    request: SpecificationDraftRequest,
    issue_provider: object,
    issue_ref: str,
    expected_issue_sha256: str,
    protocol_draft_target: object,
    physical_package_plan: object,
    client_intent_id: str,
    input_custody: object | None = None,
) -> AbstractContextManager[SpecificationSdkClient]:
    """Source-only factory; exact installed/version qualification remains held."""
    return _GovernedDraft(
        request=request,
        issue_provider=issue_provider,
        issue_ref=issue_ref,
        expected_issue_sha256=expected_issue_sha256,
        protocol_draft_target=protocol_draft_target,
        physical_package_plan=physical_package_plan,
        client_intent_id=client_intent_id,
        input_custody=input_custody,
    )
