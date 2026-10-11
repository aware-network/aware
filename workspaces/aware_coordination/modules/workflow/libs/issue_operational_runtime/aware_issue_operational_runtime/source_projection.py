"""Issue semantics and genuine admission composed through Workspace SDK ports."""

from __future__ import annotations

import asyncio
import os
import threading
from dataclasses import dataclass

from aware_issue_sdk.operation import (
    IssueMutationOutcome,
    IssueMutationResult,
    IssueStartProgressRequest,
)
from aware_issue_sdk.source_projection import (
    IssueSourceProjectionAdmission,
    IssueSourceProjectionConsumption,
    IssueSourceProjectionRefusal,
    IssueStartProgressProjectionPlan,
    _issue_handle,
    _owner,
)
from aware_workspace_sdk.repository_source_projection import (
    WorkspaceRepositorySourceProjectionClient,
)
from aware_workspace_sdk.repository_source_projection_values import (
    WorkspaceSourceProjectionRequest,
)

from .contracts import StartIssueProgressIntent, TransitionOutcome
from .state_machine import apply_issue_intent


@dataclass
class _PlanRecord:
    request: IssueStartProgressRequest
    capture: tuple
    projection: object
    workspace: WorkspaceRepositorySourceProjectionClient
    workspace_plan: object
    binding: object
    rendered: bytes
    phase: str = "prepared"
    admission: object = None
    workspace_admission: object = None
    consumption: object = None
    observation: object = None


class IssueSourceProjectionRuntime:
    def __init__(self, physical):
        from aware_issue_fs_adapter.source_projection import (
            FilesystemIssueProjectionPort,
        )

        if type(physical) is not FilesystemIssueProjectionPort:
            raise TypeError("original Issue projection physical port required")
        self.physical = physical
        self.pid = os.getpid()
        self.thread = threading.get_ident()
        self.plans = {}
        self.admissions = {}
        self.consumptions = {}
        self.lock = threading.RLock()
        self.execute_lock = asyncio.Lock()

    def check_current(self):
        if self.pid != os.getpid() or self.thread != threading.get_ident():
            raise IssueSourceProjectionRefusal("issue_projection_origin_mismatch")
        self.physical.check_execution()

    def _record(self, handle):
        if _owner(handle) is not self:
            raise IssueSourceProjectionRefusal("issue_projection_foreign_owner")
        record = (
            self.plans.get(handle)
            if type(handle) is IssueStartProgressProjectionPlan
            else self.admissions.get(handle)
        )
        if record is None:
            raise IssueSourceProjectionRefusal("issue_projection_not_issued")
        return record

    def _authorize(self, request, capture, projection):
        if request.actor_ref != self.physical.execution_id:
            raise IssueSourceProjectionRefusal("issue_owner_execution_mismatch")
        if projection.owner_ref != request.actor_ref:
            raise IssueSourceProjectionRefusal("issue_owner_mismatch")
        if self.physical.digest(capture[1]) != request.expected_source_sha256:
            raise IssueSourceProjectionRefusal("issue_projection_stale")
        if projection.status != "open":
            raise IssueSourceProjectionRefusal("issue_start_progress_requires_open")
        state, context = self.physical.operational_inputs(
            request, projection, capture[0]
        )
        transition = apply_issue_intent(
            state,
            StartIssueProgressIntent(context=context, issue_ref=request.issue_ref),
        )
        if transition.outcome is not TransitionOutcome.APPLIED:
            raise IssueSourceProjectionRefusal(
                transition.blocker_code or "issue_start_progress_refused"
            )

    def _fresh(self, record):
        capture, projection = self.physical.read(record.request)
        if capture != record.capture:
            raise IssueSourceProjectionRefusal("issue_projection_authority_changed")
        self._authorize(record.request, capture, projection)

    async def prepare(self, request, *, workspace_client):
        self.check_current()
        if type(request) is not IssueStartProgressRequest:
            raise TypeError("original Issue start progress request required")
        if type(workspace_client) is not WorkspaceRepositorySourceProjectionClient:
            raise TypeError("original Workspace source projection SDK client required")
        capture, projection = self.physical.read(request)
        self._authorize(request, capture, projection)
        source = await workspace_client.observe_source(target_path=capture[0])
        if (
            source.provider.execution_id != self.physical.execution_id
            or source.content_digest != request.expected_source_sha256
            or (source.root_identity.device, source.root_identity.inode)
            != self.physical.root_identity
            or (source.target_identity.device, source.target_identity.inode)
            != capture[2][:2]
        ):
            raise IssueSourceProjectionRefusal("workspace_source_correlation_mismatch")
        rendered = self.physical.render(request, capture[1])
        ref = await workspace_client.retain_projection_body(
            rendered,
            expected_content_digest=self.physical.digest(rendered),
            expected_size_bytes=len(rendered),
        )
        workspace_plan = await workspace_client.prepare_source_projection(
            WorkspaceSourceProjectionRequest(
                source,
                request.operation_ref,
                request.issue_ref,
                "issue_start_progress_v0",
                self.physical.digest(rendered),
                len(rendered),
                ref,
                "descriptor_walk_v1",
            )
        )
        binding = workspace_client.observe_source_projection_plan(
            workspace_plan
        ).binding
        workspace_client.verify_source_projection_plan(
            workspace_plan, expected_binding=binding
        )
        record = _PlanRecord(
            request,
            capture,
            projection,
            workspace_client,
            workspace_plan,
            binding,
            rendered,
        )
        self._fresh(record)
        plan = _issue_handle(self, IssueStartProgressProjectionPlan)
        with self.lock:
            self.plans[plan] = record
        return plan

    async def admit(self, plan):
        record = self._record(plan)
        with self.lock:
            if record.phase != "prepared":
                raise IssueSourceProjectionRefusal("issue_projection_admission_spent")
            try:
                self._fresh(record)
                record.workspace.verify_source_projection_plan(
                    record.workspace_plan, expected_binding=record.binding
                )
            except BaseException:
                # A refused original attempt cannot revive when bytes return.
                # Resolve ownership before this boundary; never retire a foreign plan.
                record.phase = "retired"
                raise
            admission = _issue_handle(self, IssueSourceProjectionAdmission)
            self.admissions[admission] = record
            record.admission, record.phase = admission, "admitted"
        try:
            record.workspace_admission = await record.workspace.enroll_issue_projection(
                record.workspace_plan, issue_admission=admission
            )
        except BaseException as error:
            record.phase = "retired"
            raise IssueSourceProjectionRefusal(
                "issue_projection_enrollment_failed"
            ) from error
        return admission

    def verify(self, admission, *, expected_binding):
        record = self._record(admission)
        with self.lock:
            if record.phase != "admitted" or record.binding != expected_binding:
                raise IssueSourceProjectionRefusal(
                    "issue_projection_binding_or_phase_mismatch"
                )
            self._fresh(record)
            return record.binding

    def consume(self, admission, *, binding):
        record = self._record(admission)
        with self.lock:
            if record.phase != "admitted" or record.binding != binding:
                raise IssueSourceProjectionRefusal(
                    "issue_projection_consumed_or_mismatched"
                )
            # No reciprocal Workspace call. Original enrollment + fresh Issue
            # semantics are checked while Workspace owns its transaction.
            record.phase = "spent"
            self._fresh(record)
            consumption = _issue_handle(self, IssueSourceProjectionConsumption)
            self.consumptions[consumption] = record
            record.consumption = consumption
            return consumption

    async def execute(self, plan, *, admission):
        async with self.execute_lock:
            record = self._record(plan)
            if self._record(admission) is not record or record.phase != "admitted":
                raise IssueSourceProjectionRefusal(
                    "issue_projection_consumed_or_mismatched",
                    observation=record.observation,
                )
            try:
                observation = await record.workspace.project_source(
                    record.workspace_plan, admission=record.workspace_admission
                )
            except BaseException as error:
                record.phase = "terminal"
                try:
                    record.observation = record.workspace.observe_source_projection(
                        record.workspace_admission
                    )
                except BaseException:  # noqa: BLE001 - use the original refusal carrier, never infer no effects
                    record.observation = getattr(
                        getattr(error, "evidence", None), "observation", None
                    )
                raise IssueSourceProjectionRefusal(
                    "issue_projection_execution_failed", observation=record.observation
                ) from error
            record.phase, record.observation = "terminal", observation
            if self.consumptions.get(record.consumption) is not record:
                raise IssueSourceProjectionRefusal(
                    "issue_projection_consumption_unconfirmed", observation=observation
                )
            if (
                not observation.ledger_complete
                or observation.source_effect_state == "unknown"
                or (
                    observation.source_effect_state == "applied"
                    and observation.retention.state != "retained"
                )
            ):
                raise IssueSourceProjectionRefusal(
                    "issue_projection_evidence_incomplete", observation=observation
                )
            outcome = (
                IssueMutationOutcome.APPLIED
                if observation.source_effect_state == "applied"
                else IssueMutationOutcome.CONFLICT
                if observation.source_effect_state == "none"
                else IssueMutationOutcome.AUTHORITY_UNAVAILABLE
            )
            # Original domain projection is derived from its rendered postimage
            # only when the original owner confirms the exact applied digest.
            if outcome is IssueMutationOutcome.APPLIED and (
                observation.physical_effect is None
                or observation.physical_effect.after_content_digest
                != self.physical.digest(record.rendered)
            ):
                raise IssueSourceProjectionRefusal(
                    "issue_projection_postimage_unconfirmed", observation=observation
                )
            try:
                projection = (
                    self.physical.projected_read(
                        record.request, record.capture[0], record.rendered
                    )
                    if outcome is IssueMutationOutcome.APPLIED
                    else None
                )
                return IssueMutationResult(
                    operation_ref=record.request.operation_ref,
                    outcome=outcome,
                    issue_ref=record.request.issue_ref,
                    provider_ref="aware.issue.source-projection.fs.v0",
                    provider_distribution="aware-issue-fs-adapter",
                    provider_version="source-v0",
                    source_sha256_before=record.request.expected_source_sha256,
                    source_sha256_after=self.physical.digest(record.rendered)
                    if outcome is IssueMutationOutcome.APPLIED
                    else None,
                    projection=projection,
                    evidence=tuple(
                        value
                        for value in (
                            observation.binding.attempt_ref,
                            observation.mutation_receipt_ref,
                            observation.retention.capture_ref,
                            observation.retention.content_delta_ref,
                            f"source_effect:{observation.source_effect_state}",
                            f"canonical_retention:{observation.retention.state}",
                            f"ledger_complete:{str(observation.ledger_complete).lower()}",
                        )
                        if value
                    ),
                    diagnostics=(
                        *observation.diagnostics,
                        *observation.retention.diagnostics,
                    ),
                )
            except BaseException as error:
                # Result validation/return cannot erase the settled owner's evidence.
                # The attempt is already terminal; do not recapture, undo or replay.
                raise IssueSourceProjectionRefusal(
                    "issue_projection_result_failed", observation=observation
                ) from error
