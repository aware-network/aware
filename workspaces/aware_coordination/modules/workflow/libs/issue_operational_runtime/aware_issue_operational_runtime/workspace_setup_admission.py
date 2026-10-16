"""Original single-use Issue A1 issuer; at-use checks do not call Workspace."""

from __future__ import annotations

import importlib
import os
import threading
import weakref
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from aware_issue_sdk.workspace_setup_admission import (
    IssueWorkspaceSetupAdmission,
    IssueWorkspaceSetupAdmissionPlan,
    IssueWorkspaceSetupConsumption,
    IssueWorkspaceSetupEnrollment,
    IssueWorkspaceSetupRefusal,
    _issue,
)
from aware_issue_sdk.workspace_setup_admission_codec import (
    issue_setup_value_from_payload,
    issue_setup_value_to_payload,
)
from aware_issue_sdk.workspace_setup_admission_values import (
    IssueWorkspaceSetupAdmissionRefusalEvidence,
    IssueWorkspaceSetupBinding,
    IssueWorkspaceSetupCleanup,
    IssueWorkspaceSetupClientCleanup,
    IssueWorkspaceSetupObservation,
    IssueWorkspaceSetupRequest,
    IssueWorkspaceSetupSourcesObservation,
)
from aware_workspace_sdk.architecture_setup_admission_codec import setup_value_to_json
from aware_workspace_sdk.architecture_setup_admission_values import (
    WorkspaceSetupPrimaryFailure,
)

from .source_scope_policy import evaluate_issue_source_scope

_NONE = WorkspaceSetupPrimaryFailure("none", None, None, None, None, False)


@dataclass
class _Record:
    request: object
    capture: tuple[Any, ...]
    workspace: weakref.ReferenceType[Any]
    binding: IssueWorkspaceSetupBinding
    expected_wire: str
    phase: str = "prepared"
    consumption_ref: str | None = None
    verified_ordinal: int | None = None
    enrollment: object = None
    primary: object = _NONE
    cleanup: object = None


class IssueWorkspaceSetupRuntime:
    def __init__(self, physical):
        FilesystemIssueSetupPort = importlib.import_module(
            "aware_issue_fs_adapter.workspace_setup_admission"
        ).FilesystemIssueSetupPort

        if type(physical) is not FilesystemIssueSetupPort:
            raise IssueWorkspaceSetupRefusal("original_issue_setup_physical_required")
        self.physical = physical
        self.pid = os.getpid()
        self.thread = threading.get_ident()
        self.closed = False
        self.ref = "aware.issue.setup-a1.v1"
        self.client_ref = "issue-setup-client:" + uuid4().hex
        self.records = []
        self.client_cleanup = IssueWorkspaceSetupClientCleanup(
            self.ref,
            self.physical.generation,
            self.client_ref,
            (),
            False,
            "not_attempted",
            _NONE,
            (),
            True,
        )

    def current(self):
        if self.closed or (self.pid, self.thread) != (
            os.getpid(),
            threading.get_ident(),
        ):
            raise IssueWorkspaceSetupRefusal("issue_setup_owner_not_current")
        self.physical.current()

    def observe_sources(self, issue_ref):
        self.current()
        _, _, issue, manifest = self.physical.read_sources(issue_ref)
        return IssueWorkspaceSetupSourcesObservation(
            issue_ref=issue_ref,
            authority_manifest_locator=self.physical.locator,
            execution_ref=self.physical.execution,
            issue_source=issue,
            authority_manifest_source=manifest,
            authority_grade="filesystem_harness_observed_v1",
            actor_metadata_grade="declared_metadata_v1",
            primary_failure=_NONE,
            ledger_complete=self.physical.ledger_complete,
        )

    def _policy(self, record, binding=None):
        capture, projection, _, _ = self.physical.read_sources(record.request.issue_ref)
        if capture != record.capture:
            raise IssueWorkspaceSetupRefusal("issue_setup_authority_drift")
        if record.workspace() is None:
            raise IssueWorkspaceSetupRefusal("issue_setup_workspace_lifetime_expired")
        decision = evaluate_issue_source_scope(
            issue_owner=projection.owner_ref or "",
            issue_status=projection.status,
            scope_paths=projection.ownership_scope,
            actor_ref=self.physical.execution,
            effect_paths=record.binding.effect_paths,
        )
        if not decision.allowed:
            raise IssueWorkspaceSetupRefusal(str(decision.refusal))
        if binding is not None and setup_value_to_json(binding) != record.expected_wire:
            raise IssueWorkspaceSetupRefusal("issue_setup_binding_mismatch")

    def _stop(self, record, error, stage):
        record.phase = "retired"
        if record.primary.state == "none":
            record.primary = WorkspaceSetupPrimaryFailure(
                "observed",
                self.ref,
                stage,
                getattr(error, "code", "issue_setup_refused"),
                type(error).__name__,
                not isinstance(error, Exception),
            )
        evidence = IssueWorkspaceSetupAdmissionRefusalEvidence(
            getattr(error, "code", "issue_setup_refused"),
            type(error).__name__,
            record.binding,
            self.observe(record),
            None,
            record.cleanup,
            record.primary,
            self.physical.ledger_complete,
            self.client_cleanup,
        )
        return IssueWorkspaceSetupRefusal(evidence.code, evidence=evidence)

    def prepare(self, request, workspace_plan, expected_binding):
        self.current()
        if type(request) is not IssueWorkspaceSetupRequest:
            raise IssueWorkspaceSetupRefusal("original_issue_setup_request_required")
        request = issue_setup_value_from_payload(
            IssueWorkspaceSetupRequest, issue_setup_value_to_payload(request)
        )
        from aware_workspace_sdk.architecture_setup_admission import (
            verify_original_setup_plan,
        )

        view = verify_original_setup_plan(
            workspace_plan, expected_binding=expected_binding
        )
        binding = view.binding
        if binding is None:
            raise IssueWorkspaceSetupRefusal("original_workspace_binding_required")
        capture, _projection, issue, manifest = self.physical.read_sources(
            request.issue_ref
        )
        if (
            binding.repository_root != str(self.physical.root)
            or binding.repository_identity != self.physical.identity
            or (binding.process_id, binding.thread_id) != (self.pid, self.thread)
        ):
            raise IssueWorkspaceSetupRefusal("issue_setup_workspace_origin_mismatch")
        if (
            issue.content_sha256 != request.expected_issue_source_sha256
            or manifest.content_sha256 != request.expected_authority_manifest_sha256
        ):
            raise IssueWorkspaceSetupRefusal("issue_setup_review_guard_mismatch")
        held = sum(
            len(row.capture[0]) + len(row.capture[2])
            for row in self.records
            if row.capture
        )
        if held + len(capture[0]) + len(capture[2]) > 2097152:
            raise IssueWorkspaceSetupRefusal("issue_setup_retained_body_limit")
        effects = []
        for step in binding.ordered_effects:
            for path in (step.primary_path, *step.auxiliary_paths):
                if path not in effects:
                    effects.append(path)
        for path in effects:
            for protected in (request.issue_ref, self.physical.locator):
                if path == protected or protected.startswith(path + "/"):
                    raise IssueWorkspaceSetupRefusal(
                        "issue_setup_authority_effect_forbidden"
                    )
        declaration = IssueWorkspaceSetupBinding(
            self.ref,
            self.physical.generation,
            self.physical.execution,
            request.issue_ref,
            issue.content_sha256,
            self.physical.locator,
            manifest.content_sha256,
            request.client_intent_id,
            binding,
            tuple(effects),
            "filesystem_harness_observed_v1",
            "declared_metadata_v1",
        )
        record = _Record(
            request,
            capture,
            weakref.ref(workspace_plan),
            declaration,
            setup_value_to_json(binding),
        )
        try:
            self._policy(record, binding)
        except BaseException as error:
            raise self._stop(record, error, "preparation") from error
        self.records.append(record)
        return _issue(self, IssueWorkspaceSetupAdmissionPlan, record)

    def admit(self, record):
        self.current()
        try:
            if record.phase != "prepared":
                raise IssueWorkspaceSetupRefusal("issue_setup_admission_replay")
            self._policy(record)
            record.phase = "admitted"
            return _issue(self, IssueWorkspaceSetupAdmission, record)
        except BaseException as error:
            raise self._stop(record, error, "admission") from error

    def enroll(self, record, workspace_plan, binding):
        self.current()
        try:
            if record.phase != "admitted" or record.workspace() is not workspace_plan:
                raise IssueWorkspaceSetupRefusal(
                    "issue_setup_foreign_or_replayed_enrollment"
                )
            from aware_workspace_sdk.architecture_setup_admission import (
                verify_original_setup_plan,
            )

            verify_original_setup_plan(workspace_plan, expected_binding=binding)
            self._policy(record, binding)
            record.phase = "enrolled"
            enrollment = _issue(self, IssueWorkspaceSetupEnrollment, record)
            record.enrollment = weakref.ref(enrollment)
            return enrollment
        except BaseException as error:
            raise self._stop(record, error, "enrollment") from error

    def consume(self, record, binding):
        self.current()
        try:
            if record.phase != "enrolled":
                raise IssueWorkspaceSetupRefusal("issue_setup_consumption_replay")
            # Spend before the fallible fresh source check. No restoration or retry.
            record.phase = "spent"
            record.consumption_ref = "issue-setup-consumption:" + uuid4().hex
            self._policy(record, binding)
            return _issue(self, IssueWorkspaceSetupConsumption, record)
        except BaseException as error:
            raise self._stop(record, error, "consumption") from error

    def verify_consumption(self, record, binding, ordinal):
        self.current()
        try:
            if (
                record.phase not in ("spent", "executing")
                or type(ordinal) is not int
                or ordinal
                != (
                    0
                    if record.verified_ordinal is None
                    else record.verified_ordinal + 1
                )
                or ordinal >= len(record.binding.workspace_binding.ordered_effects)
            ):
                raise IssueWorkspaceSetupRefusal(
                    "issue_setup_ordinal_replay_or_mismatch"
                )
            # No reciprocal Workspace/FS call under the operation lease.
            self._policy(record, binding)
            record.verified_ordinal = ordinal
            record.phase = "executing"
            return self.observe(record)
        except BaseException as error:
            raise self._stop(record, error, "ordinal") from error

    def observe(self, record):
        return IssueWorkspaceSetupObservation(
            record.binding,
            record.phase,
            record.consumption_ref,
            record.verified_ordinal,
            (),
            self.physical.ledger_complete,
            tuple(self.physical.resources),
            record.primary,
        )

    def release_record(self, record):
        if record.cleanup is None:
            record.phase = "retired"
            record.request = None
            record.capture = ()
            record.cleanup = IssueWorkspaceSetupCleanup(
                record.binding,
                "released",
                True,
                "confirmed",
                (),
                self.physical.ledger_complete,
                tuple(self.physical.resources),
                record.primary,
            )
        return record.cleanup

    def release(self):
        if not self.closed:
            self.closed = True
            for record in self.records:
                _ORIGINAL_RELEASE_RECORD(self, record)
            resources, complete = _ORIGINAL_PHYSICAL_RELEASE(self.physical)
            self.client_cleanup = IssueWorkspaceSetupClientCleanup(
                self.ref,
                self.physical.generation,
                self.client_ref,
                resources,
                True,
                "confirmed" if complete else "unknown",
                _NONE,
                (),
                complete,
            )
        return self.client_cleanup


# Original issuer methods, not caller-supplied callbacks or serialized expectations.
_RUNTIME_METHODS = tuple(
    (name, method, method.__code__)
    for name, method in vars(IssueWorkspaceSetupRuntime).items()
    if type(method) is type(lambda: None)
)


def guard_original_runtime(owner):
    if type(owner) is not IssueWorkspaceSetupRuntime or (owner.pid, owner.thread) != (
        os.getpid(),
        threading.get_ident(),
    ):
        raise IssueWorkspaceSetupRefusal("original_issue_setup_runtime_required")
    if any(
        vars(IssueWorkspaceSetupRuntime).get(name) is not method
        or method.__code__ is not code
        for name, method, code in _RUNTIME_METHODS
    ):
        # Revocation does not invoke the replaced method.
        for record in owner.records:
            record.phase = "retired"
        raise IssueWorkspaceSetupRefusal("issue_setup_original_method_changed")


_ORIGINAL_RELEASE_RECORD = IssueWorkspaceSetupRuntime.release_record
FilesystemIssueSetupPort = importlib.import_module(
    "aware_issue_fs_adapter.workspace_setup_admission"
).FilesystemIssueSetupPort

_ORIGINAL_PHYSICAL_RELEASE = FilesystemIssueSetupPort.release
