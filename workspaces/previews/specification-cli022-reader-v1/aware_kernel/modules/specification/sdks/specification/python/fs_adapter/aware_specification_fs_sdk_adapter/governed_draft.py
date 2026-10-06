"""Optional source-only composition of original owners, never a second writer.

Ownership of target/plan transfers after genuine Issue admission. Before that,
rejected inputs remain caller-owned. Metadata/installed qualification is separate.
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
    SpecificationDraftEvidence,
    SpecificationDraftMemberBinding,
    SpecificationDraftPhysicalEffect,
    SpecificationDraftRequest,
    SpecificationDraftResult,
    SpecificationObserveRequest,
    SpecificationOperationError,
    SpecificationSdkClient,
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
    ) -> None:
        try:
            if type(request) is not SpecificationDraftRequest:
                raise ValueError("invalid_draft_request")
            request.__post_init__()
            self.request = copy.deepcopy(request)
            self.members = tuple(sorted(render_draft(self.request).items()))
        except (AttributeError, TypeError, ValueError) as error:
            raise SpecificationOperationError("invalid_draft_request") from error
        self.issue_provider = issue_provider
        self.issue_ref = issue_ref
        self.issue_sha256 = expected_issue_sha256
        self.target = protocol_draft_target
        self.plan = physical_package_plan
        self.client_intent_id = client_intent_id
        self.attempt_ref = "specification-draft:" + secrets.token_hex(16)
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
        self.diagnostics: list[str] = []

    def __enter__(self) -> SpecificationSdkClient:
        with self.lock:
            if self.entered or self.closed or self.pid != os.getpid():
                raise SpecificationOperationError("governed_draft_context_terminal")
            self.entered = True
            try:
                try:
                    self.physical = import_module("aware_file_system.retained_package")
                    self.protocol = import_module("aware_protocol_fs_adapter")
                    issue = import_module("aware_issue_fs_adapter")
                    sdk = import_module("aware_issue_sdk.draft_package")
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
                if (
                    self.physical.require_retained_package_plan(self.plan)
                    is not self.plan
                ):
                    raise SpecificationOperationError("original_physical_plan_required")
                target = self.protocol.require_specification_draft_target(self.target)
                if target is not self.target:
                    raise SpecificationOperationError(
                        "original_protocol_target_required"
                    )
                plan = self.physical.observe_package_plan(self.plan)
                if (
                    plan.ordered_members != self.members
                    or plan.target_path != target.target_locator
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
                    scratch_locator=plan.scratch_path,
                    ordered_members=self.members,
                    authoring_intent_ref=self.request.authoring_intent_ref,
                    client_intent_id=self.client_intent_id,
                )
                issuer = cast(Any, self.issue_provider)
                self.admission = issuer.admit_draft_package(
                    request, protocol_target=self.target, physical_plan=self.plan
                )
                issuer.validate_draft_package(self.admission)
                self.binding = issuer.observe_draft_package_binding(self.admission)
                if self.binding.request != request:
                    raise SpecificationOperationError("draft_initial_binding_mismatch")
                self.observe_draft_evidence()
                return SpecificationSdkClient(self, draft_evidence_reader=self)
            except BaseException as error:
                self._close()
                raise self._refusal(error) from error

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
            )
        return SpecificationOperationError(
            getattr(error, "code", "governed_draft_failed"),
            effect="unknown"
            if getattr(error, "effect", None) == "unknown"
            or self.staged_cleanup_uncertain
            or (evidence is not None and not evidence.ledger_complete)
            else "none"
            if evidence is None
            else evidence.package_outcome,
            evidence=evidence,
        )

    def _validate_staged(self) -> None:
        lens = self.admission.lend_staged_source()
        self.physical.validate_staged_package_source(self.plan, lens)
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
            self.physical.validate_staged_package_source(self.plan, lens)
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
        self.protocol.require_specification_selection(self.selection)
        observed = SpecificationSdkClient(self.reader).observe(request)
        if observed.snapshot != SpecificationSnapshot((self.request.definition,)):
            raise SpecificationOperationError("draft_meaning_mismatch")
        self.protocol.require_specification_selection(self.selection)
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
                self.physical.require_retained_package_postimage(image, plan=self.plan)
                self.published = True
                self.observe_draft_evidence()
                self.selection = self.protocol.admit_specification_draft_published_read(
                    self.target, physical_postimage=image
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
                self.admission.release()
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
        if self.admission is None:
            return  # No ownership transfer: never release rejected caller inputs.
        for label, cleanup in (
            ("issue_release", self.admission.release),
            ("spec_reader_close", None if self.reader is None else self.reader.close),
            (
                "protocol_read_release",
                None
                if self.selection is None
                else lambda: self.protocol.release_specification_selection(
                    self.selection
                ),
            ),
            (
                "protocol_target_release",
                lambda: self.protocol.release_specification_draft_target(self.target),
            ),
        ):
            if cleanup is None:
                continue
            try:
                cleanup()
            except BaseException as error:  # noqa: BLE001 - attempt every owner cleanup after interruption
                self.completed = False
                self.diagnostics.append(f"{label}_failed:{type(error).__name__}")

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
    )
