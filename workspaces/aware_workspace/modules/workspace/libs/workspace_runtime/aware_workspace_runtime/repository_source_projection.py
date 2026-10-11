"""Issue-authorized projection over the original mutation and delta owners.

Cross-domain verification/consumption goes only through the fixed Issue SDK.
Descriptive values never reconstruct a plan, enrollment or authority.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import threading
from dataclasses import dataclass, fields, replace
from uuid import uuid4

from aware_workspace_sdk.repository_delta_retention import (
    WorkspaceRepositoryDeltaRetentionFactory,
)
from aware_workspace_sdk.repository_source_projection import (
    WorkspaceSourceProjectionAdmission,
    WorkspaceSourceProjectionPlan,
    WorkspaceSourceProjectionRefusal,
    _issue_handle,
    _original_owner,
)
from aware_workspace_sdk.repository_source_projection_codec import (
    repository_source_projection_value_to_payload,
)
from aware_workspace_sdk.repository_source_projection_values import (
    RepositoryObservationCoordinate,
    WorkspaceRepositoryMutationExecutionEvidence,
    WorkspaceSourceFileIdentity,
    WorkspaceSourceObservation,
    WorkspaceSourcePhysicalEffect,
    WorkspaceSourceProjectionBinding,
    WorkspaceSourceProjectionCleanupObservation,
    WorkspaceSourceProjectionObservation,
    WorkspaceSourceProjectionPlanObservation,
    WorkspaceSourceProjectionRequest,
    WorkspaceSourceProjectionRetentionObservation,
    WorkspaceSourceProviderBinding,
)

from .change_evidence import RepositoryMutationKind
from .repository_delta import (
    RepositoryContentDeltaState,
    RepositoryDeltaCapturePathState,
    WorkspaceRepositoryDeltaCapturePolicy,
)
from .repository_delta_capture import WorkspaceRepositoryDeltaCaptureCoordinator
from .repository_diff import WorkspaceRepositoryOperationalBodyStore
from .repository_mutation import (
    WorkspaceRepositoryMutationCoordinator,
    WorkspaceRepositoryMutationRequest,
    _coordinate,
    repository_mutation_receipt_ref,
)


def _digest(body):
    return "sha256:" + hashlib.sha256(body).hexdigest()


def _mirror(kind, value):
    return kind(**{f.name: getattr(value, f.name) for f in fields(kind)})


def _empty_retention():
    return WorkspaceSourceProjectionRetentionObservation(
        "not_attempted", None, None, None, None, None, None, None, True, ()
    )


def _empty_cleanup():
    return WorkspaceSourceProjectionCleanupObservation(
        "not_attempted", "not_attempted", "not_attempted", "not_attempted", True, ()
    )


@dataclass
class _PlanRecord:
    binding: WorkspaceSourceProjectionBinding
    mutation: WorkspaceRepositoryMutationRequest
    capture: object
    phase: str = "prepared"
    issue_admission: object = None
    admission: object = None
    observation: WorkspaceSourceProjectionObservation | None = None


class WorkspaceRepositorySourceProjectionRuntime:
    def __init__(self, physical):
        from aware_workspace_fs_adapter.repository_source_projection import (
            FilesystemSourceProjectionPort,
        )

        if type(physical) is not FilesystemSourceProjectionPort:
            raise TypeError("original Workspace source physical port required")
        self.physical = physical
        self.provider = WorkspaceSourceProviderBinding(
            "aware.workspace.source-projection.fs.v0",
            uuid4().hex,
            physical.execution_id,
            os.getpid(),
            threading.get_ident(),
        )
        self.session = None
        self.retention = None
        self.coordinator = None
        self.capture_owner = None
        self.sources = {}
        self.plans = {}
        self.admissions = {}
        self.cleanup = _empty_cleanup()
        self.released = False
        self.lock = asyncio.Lock()

    def check_current(self):
        if (
            os.getpid() != self.provider.original_process_id
            or threading.get_ident() != self.provider.original_thread_id
        ):
            raise WorkspaceSourceProjectionRefusal("source_projection_origin_mismatch")
        try:
            self.physical.check_execution()
        except BaseException as error:
            raise WorkspaceSourceProjectionRefusal(
                "source_projection_execution_mismatch"
            ) from error

    def _active(self):
        self.check_current()
        if self.released:
            raise WorkspaceSourceProjectionRefusal(
                "source_projection_retired", cleanup=self.cleanup
            )

    async def _start(self):
        self._active()
        if self.session is not None and self.coordinator is not None:
            return
        try:
            self.session = self.physical.create_session()
            await self.session.start(background=False)
            self.retention = WorkspaceRepositoryDeltaRetentionFactory.filesystem(
                state_root=self.physical.state_root / "retention"
            ).allocate_delta_retention()
            self.retention.initialize_delta_retention(
                repository_binding_ref=self.physical.binding.binding_key,
            )
            self.capture_owner = WorkspaceRepositoryDeltaCaptureCoordinator(
                binding=self.physical.binding,
                store=self.retention,
            )
            self.coordinator = WorkspaceRepositoryMutationCoordinator(
                session=self.session,
                body_store=WorkspaceRepositoryOperationalBodyStore(),
                result_store=self.physical.create_receipt_store(),
            )
        except BaseException as error:
            cleanup = await self._release_owned()
            raise WorkspaceSourceProjectionRefusal(
                "source_projection_initialization_failed",
                cleanup=cleanup,
                diagnostics=(type(error).__name__,),
            ) from error

    async def observe_source(self, *, target_path):
        async with self.lock:
            await self._start()
            try:
                body, root, target = self.physical.read_source(target_path)
                await self.session.observe_paths_once((target_path,))
                coordinate = _coordinate(
                    self.session.current_snapshot, self.session
                ).observation
                repeated, repeated_root, repeated_target = self.physical.read_source(
                    target_path
                )
                if (body, root, target) != (repeated, repeated_root, repeated_target):
                    raise ValueError("source_changed_during_observation")
                body_ref = self.retention.record_body(body)
                self._require_body(body_ref, _digest(body), len(body))
                observation = WorkspaceSourceObservation(
                    "workspace-source-observation:" + uuid4().hex,
                    self.provider,
                    self.physical.binding.binding_key,
                    target_path,
                    WorkspaceSourceFileIdentity(*root),
                    WorkspaceSourceFileIdentity(*target),
                    _mirror(RepositoryObservationCoordinate, coordinate),
                    _digest(body),
                    len(body),
                    body_ref,
                )
                self.sources[observation.observation_ref] = observation
                return observation
            except BaseException as error:
                raise WorkspaceSourceProjectionRefusal(
                    "source_observation_failed", diagnostics=(type(error).__name__,)
                ) from error

    def _require_body(self, ref, digest, size):
        self.retention.verify_repository_binding(
            expected_binding_ref=self.physical.binding.binding_key
        )
        body = self.retention.resolve_body(ref)
        if type(body) is not bytes or _digest(body) != digest or len(body) != size:
            raise WorkspaceSourceProjectionRefusal("projection_body_unavailable")
        return body

    async def retain_body(
        self, content, *, expected_content_digest, expected_size_bytes
    ):
        if (
            type(content) is not bytes
            or type(expected_size_bytes) is not int
            or expected_size_bytes < 0
            or len(content) != expected_size_bytes
            or type(expected_content_digest) is not str
            or _digest(content) != expected_content_digest
            or len(content) > 4 * 1024 * 1024
        ):
            raise WorkspaceSourceProjectionRefusal(
                "projection_body_correlation_mismatch"
            )
        async with self.lock:
            await self._start()
            try:
                ref = self.retention.record_body(content)
                if (
                    self._require_body(
                        ref, expected_content_digest, expected_size_bytes
                    )
                    != content
                ):
                    raise WorkspaceSourceProjectionRefusal(
                        "projection_body_correlation_mismatch"
                    )
                return ref
            except BaseException as error:
                raise WorkspaceSourceProjectionRefusal(
                    "projection_body_retention_unavailable",
                    diagnostics=(type(error).__name__,),
                ) from error

    def _fresh(self, record):
        self._active()
        binding = record.binding
        body, root, target = self.physical.read_source(binding.target_path)
        if (
            WorkspaceSourceFileIdentity(*root) != binding.root_identity
            or WorkspaceSourceFileIdentity(*target) != binding.target_identity
            or _digest(body) != binding.expected_content_digest
            or _mirror(
                RepositoryObservationCoordinate,
                _coordinate(self.session.current_snapshot, self.session).observation,
            )
            != binding.expected_coordinate
        ):
            raise WorkspaceSourceProjectionRefusal("source_projection_stale")
        source = self.sources[binding.source_observation_ref]
        self._require_body(
            binding.preimage_body_ref, source.content_digest, source.size_bytes
        )
        self._require_body(
            binding.projected_body_ref,
            binding.projected_content_digest,
            binding.projected_size_bytes,
        )

    async def prepare(self, request):
        if type(request) is not WorkspaceSourceProjectionRequest:
            raise TypeError("exact Workspace source projection request required")
        repository_source_projection_value_to_payload(request)
        async with self.lock:
            await self._start()
            source = self.sources.get(request.source.observation_ref)
            if (
                source is None
                or source != request.source
                or source.provider != self.provider
            ):
                raise WorkspaceSourceProjectionRefusal("source_observation_not_issued")
            if request.physical_guarantee != "descriptor_walk_v1":
                raise WorkspaceSourceProjectionRefusal(
                    "continuous_root_backend_unavailable"
                )
            if (request.operation_ref, request.profile_ref) != (
                "issue_sdk.start_issue_progress",
                "issue_start_progress_v0",
            ):
                raise WorkspaceSourceProjectionRefusal(
                    "source_projection_profile_unavailable"
                )
            body = self._require_body(
                request.projected_body_ref,
                request.projected_content_digest,
                request.projected_size_bytes,
            )
            binding = WorkspaceSourceProjectionBinding(
                "workspace-source-binding:" + uuid4().hex,
                "workspace-source-attempt:" + uuid4().hex,
                self.provider,
                request.operation_ref,
                request.domain_target_ref,
                request.profile_ref,
                source.observation_ref,
                source.repository_binding_ref,
                source.target_path,
                source.root_identity,
                source.target_identity,
                source.coordinate,
                source.content_digest,
                request.projected_content_digest,
                request.projected_size_bytes,
                source.body_ref,
                request.projected_body_ref,
                request.physical_guarantee,
            )
            mutation = WorkspaceRepositoryMutationRequest(
                operation_ref=binding.operation_ref,
                idempotency_key=binding.attempt_ref,
                mutation_kind=RepositoryMutationKind.UPDATE,
                expected_coordinate=_coordinate(
                    self.session.current_snapshot, self.session
                ),
                target_path=binding.target_path,
                expected_exists=True,
                expected_content_digest=binding.expected_content_digest,
                content=body,
                context_refs=(binding.domain_target_ref, binding.attempt_ref),
            )
            record = _PlanRecord(binding, mutation, None)
            self._fresh(record)
            record.capture = self.capture_owner.prepare(
                snapshot=self.session.current_snapshot,
                selected_paths=(source.target_path,),
                policy=WorkspaceRepositoryDeltaCapturePolicy(),
                context_refs=(binding.domain_target_ref, binding.attempt_ref),
            )
            coverage = record.capture.path_states[0]
            if (
                coverage.state is not RepositoryDeltaCapturePathState.COVERED
                or coverage.body_ref != source.body_ref
                or coverage.content_digest != source.content_digest
            ):
                raise WorkspaceSourceProjectionRefusal("source_capture_uncovered")
            plan = _issue_handle(self, WorkspaceSourceProjectionPlan)
            self.plans[plan] = record
            return plan

    def _record(self, handle):
        if _original_owner(handle) is not self:
            raise WorkspaceSourceProjectionRefusal("source_projection_foreign_owner")
        record = (
            self.plans.get(handle)
            if type(handle) is WorkspaceSourceProjectionPlan
            else self.admissions.get(handle)
        )
        if record is None:
            raise WorkspaceSourceProjectionRefusal("source_projection_not_issued")
        return record

    def observe_plan(self, plan):
        record = self._record(plan)
        return WorkspaceSourceProjectionPlanObservation(
            record.binding, record.phase, True, ()
        )

    def verify_plan(self, plan, *, expected_binding):
        record = self._record(plan)
        if record.phase != "prepared" or expected_binding != record.binding:
            raise WorkspaceSourceProjectionRefusal(
                "source_plan_binding_or_phase_mismatch"
            )
        self._fresh(record)
        return self.observe_plan(plan)

    async def enroll(self, plan, *, issue_admission):
        from aware_issue_sdk.source_projection import verify_source_projection_admission

        async with self.lock:
            record = self._record(plan)
            self.verify_plan(plan, expected_binding=record.binding)
            try:
                verify_source_projection_admission(
                    issue_admission, expected_binding=record.binding
                )
            except BaseException as error:
                raise WorkspaceSourceProjectionRefusal(
                    "issue_projection_enrollment_refused"
                ) from error
            admission = _issue_handle(self, WorkspaceSourceProjectionAdmission)
            record.issue_admission, record.admission, record.phase = (
                issue_admission,
                admission,
                "enrolled",
            )
            self.admissions[admission] = record
            return admission

    def _consume_under_transaction(self, plan):
        from aware_issue_sdk.source_projection import (
            consume_source_projection_admission,
        )

        record = self._record(plan)
        if record.phase != "spent":
            raise WorkspaceSourceProjectionRefusal("source_projection_not_spent")
        self._fresh(record)
        # Fixed supplying SDK. Issue must not call Workspace here.
        consume_source_projection_admission(
            record.issue_admission, binding=record.binding
        )

    async def project(self, plan, *, admission):
        async with self.lock:
            record = self._record(plan)
            if self._record(admission) is not record or record.phase != "enrolled":
                raise WorkspaceSourceProjectionRefusal(
                    "source_projection_spent_or_mismatched",
                    observation=record.observation,
                )
            self._active()
            record.phase = "spent"
            error = None
            result = None
            try:
                result = await self.coordinator._mutate_source_projection(
                    record.mutation, plan=plan
                )
            except BaseException as caught:  # noqa: BLE001 - retain the terminal owner evidence
                error = caught
                try:
                    result = await self._resolve_record(record)
                except BaseException as resolution_error:  # noqa: BLE001 - neither absence nor a retry grant
                    resolution_diagnostic = (
                        f"receipt_resolution:{type(resolution_error).__name__}"
                    )
                else:
                    resolution_diagnostic = None
            else:
                resolution_diagnostic = None
            record.phase = "terminal"
            retention = _empty_retention()
            diagnostics = (
                [] if error is None else [f"projection:{type(error).__name__}"]
            )
            if resolution_diagnostic is not None:
                diagnostics.append(resolution_diagnostic)
            if result is not None and result.evidence is not None:
                try:
                    retention = await self._retain_delta(record, result)
                except BaseException as caught:  # noqa: BLE001 - preserve the known source effect
                    retention = replace(
                        retention,
                        state="unknown",
                        ledger_complete=False,
                        diagnostics=(f"canonical_retention:{type(caught).__name__}",),
                    )
            physical = result.receipt.physical_effect if result is not None else None
            execution = result.execution_evidence if result is not None else None
            source_state = (
                physical.state
                if physical is not None
                else (
                    "unknown"
                    if result is None
                    or execution is None
                    or execution.physical_return_state == "unavailable"
                    else "none"
                )
            )
            convergence = (
                "converged"
                if result is not None and result.evidence is not None
                else (
                    "unknown"
                    if source_state == "unknown"
                    else "failed"
                    if source_state == "applied"
                    else "not_attempted"
                )
            )
            complete = (
                result is not None
                and execution is not None
                and execution.ledger_complete
                and self.coordinator.result_store_error is None
                and retention.ledger_complete
                and error is None
            )
            if self.coordinator.result_store_error is not None:
                diagnostics.append("mutation_receipt_index_unavailable")
            record.observation = WorkspaceSourceProjectionObservation(
                record.binding,
                record.phase,
                source_state,
                result.receipt.mutation_receipt_ref if result is not None else None,
                _mirror(WorkspaceSourcePhysicalEffect, physical)
                if physical is not None
                else None,
                _mirror(WorkspaceRepositoryMutationExecutionEvidence, execution)
                if execution is not None
                else None,
                convergence,
                retention,
                self.cleanup,
                bool(complete),
                tuple(diagnostics),
            )
            if error is not None:
                raise WorkspaceSourceProjectionRefusal(
                    "source_projection_interrupted",
                    observation=record.observation,
                    diagnostics=tuple(diagnostics),
                ) from error
            return record.observation

    async def _retain_delta(self, record, result):
        before, after = (
            result.evidence.before_coordinate.observation,
            result.evidence.after_coordinate.observation,
        )
        replay = await self.session.replay(
            after_cursor=before.cursor, epoch=before.epoch
        )
        if replay.gap is not None:
            raise WorkspaceSourceProjectionRefusal("canonical_delta_gap")
        batches = [
            b
            for b in replay.batches
            if (
                b.cursor == after.cursor
                and b.before_snapshot_digest == before.snapshot_digest
                and b.after_snapshot_digest == after.snapshot_digest
            )
        ]
        if len(batches) != 1 or len(batches[0].changes) != 1:
            raise WorkspaceSourceProjectionRefusal("canonical_delta_ambiguous")
        deltas = self.capture_owner.observe(batches[0])
        matches = [d for d in deltas if d.capture_ref == record.capture.capture_ref]
        if len(matches) != 1:
            raise WorkspaceSourceProjectionRefusal("canonical_delta_unavailable")
        delta = matches[0]
        if (
            delta.state is not RepositoryContentDeltaState.AVAILABLE
            or delta.before_coordinate != before
            or delta.after_coordinate != after
            or delta.old_body_ref != record.binding.preimage_body_ref
            or delta.new_body_ref != record.binding.projected_body_ref
            or self.retention.resolve_delta(delta.delta_ref) != delta
        ):
            raise WorkspaceSourceProjectionRefusal("canonical_delta_uncovered")
        self._require_body(
            delta.old_body_ref, delta.old_content_digest, delta.old_size_bytes
        )
        self._require_body(
            delta.new_body_ref, delta.new_content_digest, delta.new_size_bytes
        )
        observed = self.retention.observe_retention()
        return WorkspaceSourceProjectionRetentionObservation(
            "retained",
            observed.retention_ref,
            delta.old_body_ref,
            delta.new_body_ref,
            delta.capture_ref,
            delta.delta_ref,
            _mirror(RepositoryObservationCoordinate, before),
            _mirror(RepositoryObservationCoordinate, after),
            True,
            (),
        )

    def observe(self, admission):
        record = self._record(admission)
        if record.observation is None:
            return WorkspaceSourceProjectionObservation(
                record.binding,
                record.phase,
                "none",
                None,
                None,
                None,
                "not_attempted",
                _empty_retention(),
                self.cleanup,
                True,
                (),
            )
        return replace(
            record.observation,
            phase=record.phase,
            cleanup=self.cleanup,
            ledger_complete=record.observation.ledger_complete
            and self.cleanup.ledger_complete,
        )

    async def _resolve_record(self, record):
        ref = repository_mutation_receipt_ref(
            repository_binding_ref=record.binding.repository_binding_ref,
            operation_ref=record.binding.operation_ref,
            idempotency_key=record.binding.attempt_ref,
        )
        resolution = await self.coordinator.resolve_receipts((ref,))
        return resolution.resolved[0] if resolution.resolved else None

    async def resolve(self, admission):
        record = self._record(admission)
        if self.coordinator is None:
            return None
        return await self._resolve_record(record)

    async def release(self):
        async with self.lock:
            return await self._release_owned()

    async def _release_owned(self):
        self.check_current()
        if self.released:
            return self.cleanup
        self.released = True
        for record in self.plans.values():
            record.phase = "retired"
        states = ["not_attempted", "not_attempted"]
        diagnostics = []
        if self.session is not None:
            try:
                await self.session.stop()
                states[0] = "completed"
            except BaseException as error:  # noqa: BLE001 - attempt independent resource cleanup
                states[0] = "unknown"
                diagnostics.append(f"observer_cleanup:{type(error).__name__}")
        if self.retention is not None:
            try:
                observation = self.retention.release_retention()
                states[1] = (
                    "completed" if observation.phase == "released" else "unknown"
                )
            except BaseException as error:  # noqa: BLE001 - cleanup completion stays unknown
                states[1] = "unknown"
                diagnostics.append(f"retention_cleanup:{type(error).__name__}")
        complete = "unknown" not in states
        self.cleanup = WorkspaceSourceProjectionCleanupObservation(
            "completed" if complete else "unknown",
            *states,
            "not_attempted",
            complete,
            tuple(diagnostics),
        )
        return self.cleanup


def consume_original_projection_plan(plan, *, coordinator, request):
    """Fixed original-owner guard, called only at the writer transaction seam."""
    owner = _original_owner(plan)
    record = owner._record(plan)
    if owner.coordinator is not coordinator or record.mutation is not request:
        raise WorkspaceSourceProjectionRefusal(
            "original_projection_transaction_required"
        )
    owner._consume_under_transaction(plan)
