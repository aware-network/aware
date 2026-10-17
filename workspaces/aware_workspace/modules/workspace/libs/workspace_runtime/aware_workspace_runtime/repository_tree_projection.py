"""Original source-first C preparation. No replacement tree writer or admission."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import threading
from collections.abc import Callable
from contextvars import copy_context
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any, cast
from uuid import uuid4
from weakref import ref

from aware_issue_sdk import source_projection as _ISSUE_SDK
from aware_issue_sdk.repository_tree_projection_values import (
    IssueTreeAdmissionObservation,
)
from aware_issue_sdk.source_projection import (
    IssueTreeProjectionAdmission,
    IssueTreeProjectionConsumption,
)
from aware_workspace_sdk.repository_delta_retention import (
    WorkspaceRepositoryDeltaRetentionFactory,
)
from aware_workspace_sdk.repository_tree_projection import (
    WorkspaceTreeProjectionAdmission,
    WorkspaceTreeProjectionPlan,
    WorkspaceTreeProjectionRefusal,
    WorkspaceTreeProjectionResult,
    _issue_handle,
    _require_handle,
)
from aware_workspace_sdk.repository_tree_projection_codec import (
    repository_tree_projection_value_clone,
    repository_tree_projection_value_digest,
)
from aware_workspace_sdk.repository_tree_projection_values import (
    CleanupState,
    PlanPhase,
    ResourceOwnership,
    ScratchKind,
    ScratchRole,
    WorkspaceTreeAncestorTransition,
    WorkspaceTreeEntryPin,
    WorkspaceTreeFileTransition,
    WorkspaceTreePhysicalEffect,
    WorkspaceTreeProjectionBinding,
    WorkspaceTreeProjectionCleanupObservation,
    WorkspaceTreeProjectionObservation,
    WorkspaceTreeProjectionPlanObservation,
    WorkspaceTreeProjectionResolution,
    WorkspaceTreeResourceCleanup,
    WorkspaceTreeScratchEffect,
    WorkspaceTreeTargetRead,
    WorkspaceTreeTransitionReceipt,
)
from aware_workspace_sdk.repository_workflow import (
    observe_original_repository_workflow_source,
    read_original_repository_workflow_source,
    verify_original_repository_workflow_source,
    verify_original_repository_workflow_source_paths,
)

from .observation import WorkspaceRepositoryObservationSession
from .repository_tree_capacity import (
    TreeCapacityBound,
    capacity_bound,
    enforce_capacity,
    require_forecast_origin,
)
from .repository_tree_preparation_copy import (
    copy_preparation_observation as _copy_preparation_observation,
)

_PREPARATION_COPIER = (
    _copy_preparation_observation,
    _copy_preparation_observation.__code__,
    _copy_preparation_observation.__defaults__,
    _copy_preparation_observation.__kwdefaults__,
)

_CAPACITY_ENTRANCES = tuple(
    (name, function, function.__code__, function.__defaults__, function.__kwdefaults__)
    for name, function in (
        ("require_forecast_origin", require_forecast_origin),
        ("capacity_bound", capacity_bound),
        ("enforce_capacity", enforce_capacity),
    )
)


def _digest(body):
    return "sha256:" + hashlib.sha256(body).hexdigest()


def _exception_kind(error):
    # Advisory diagnostic label, not a replacement for the original exception.
    # Read the exact built-in name descriptor without exception-metaclass behavior.
    name = type.__dict__["__name__"].__get__(type(error), type)
    if (
        len(name) <= 128
        and name.isascii()
        and all(character.isalnum() or character == "_" for character in name)
    ):
        return name
    return (
        "exception-type:sha256:"
        + hashlib.sha256(name.encode("utf-8", errors="surrogatepass")).hexdigest()
    )


class WorkspaceRepositoryTreeProjectionRuntime:
    def __init__(self, physical):
        from aware_workspace_fs_adapter.repository_source_projection import (
            FilesystemSourceProjectionPort,
        )

        if type(physical) is not FilesystemSourceProjectionPort:
            raise WorkspaceTreeProjectionRefusal("original_owner_required")
        self.physical = physical
        self.physical_class = FilesystemSourceProjectionPort
        self.physical_methods = {
            name: vars(FilesystemSourceProjectionPort)[name]
            for name in (
                "check_execution",
                "read_tree_entry",
                "retain_tree_preparation",
                "create_tree_session",
                "create_tree_receipt_store",
                "read_tree_receipt_store_cleanup",
            )
        }
        self.receipt_cleanup_reader = self.physical_methods[
            "read_tree_receipt_store_cleanup"
        ]
        self.receipt_cleanup_reader_code = self.receipt_cleanup_reader.__code__
        self.receipt_cleanup_observed = False
        self.physical_fields = dict(vars(physical))
        self.pid = os.getpid()
        self.thread = threading.get_ident()
        self.generation = uuid4().hex
        self.parent: Any = None
        self.sdk_record: Any = None
        self.phase = "allocated"
        self.lock = asyncio.Lock()
        self.source = None
        self.request = None
        self.retention = None
        self.retention_methods = None
        self.preparation = None
        self.preparation_methods = None
        self.preparation_observation = None
        self.capacity_forecast = None
        self.capacity_bound = None
        self.session: WorkspaceRepositoryObservationSession | None = None
        self.session_methods = None
        self.plan = None
        self.issue_admission = None
        self.issue_consumption = None
        self.issue_admission_ref = None
        self.issue_consumption_ref = None
        self.enrollment = None
        self.coordinator = None
        self.transitions = []
        self.physical_observation = None
        self.final_observation = None
        self.result_handle = None
        self.index_state = "not_attempted"
        self.receipt_store = None
        self.canonical_results = {}
        self.deltas = {}
        self.capture = None
        self.capture_owner = None
        self.execution_error = None
        self.binding: WorkspaceTreeProjectionBinding | None = None
        self.repository_binding = None
        self.files = ()
        self.ancestors = ()
        self.cleanup = WorkspaceTreeProjectionCleanupObservation(
            None, (), (), "not_attempted", True, ()
        )

    def retire(self):
        # Receiver storage is retained independently of mutable method dispatch.
        state = _RUNTIME_STORAGE.__get__(self, WorkspaceRepositoryTreeProjectionRuntime)
        state["phase"] = "held"
        resources = [
            row
            for row in state["cleanup"].resources
            if row.kind != "observation_session"
        ]
        try:
            if (
                state["receipt_store"] is not None
                and not state["receipt_cleanup_observed"]
            ):
                # Spend the observation before dispatch. This is cleanup data,
                # not publication/currentness authority or another disposal.
                state["receipt_cleanup_observed"] = True
                known, diagnostics = False, ("receipt_index_origin_unknown",)
                reader = state["receipt_cleanup_reader"]
                physical = state["physical"]
                try:
                    if (
                        type(physical) is not state["physical_class"]
                        or vars(state["physical_class"]).get(
                            "read_tree_receipt_store_cleanup"
                        )
                        is not reader
                        or reader.__code__ is not state["receipt_cleanup_reader_code"]
                        or any(
                            vars(physical).get(name) is not value
                            for name, value in state["physical_fields"].items()
                        )
                    ):
                        raise ValueError("Original receipt cleanup reader required")
                    returned = reader(
                        physical, state["repository_binding"], state["receipt_store"]
                    )
                    if (
                        reader.__code__ is not state["receipt_cleanup_reader_code"]
                        or vars(state["physical_class"]).get(
                            "read_tree_receipt_store_cleanup"
                        )
                        is not reader
                        or type(returned) is not tuple
                        or len(returned) != 2
                        or type(returned[0]) is not bool
                        or type(returned[1]) is not tuple
                        or len(returned[1]) > 3
                        or any(
                            type(label) is not str or len(label) > 64
                            for label in returned[1]
                        )
                    ):
                        raise ValueError("Original receipt cleanup result required")
                    known, diagnostics = returned
                except BaseException as cleanup_error:  # noqa: BLE001 -- preserve original execution failure
                    diagnostics = (_exception_kind(cleanup_error),)
                if not known:
                    resources.append(
                        WorkspaceTreeResourceCleanup(
                            "receipt-index:" + state["generation"],
                            "repository_index_metadata",
                            None,
                            "owned",
                            True,
                            "unknown",
                            diagnostics,
                        )
                    )
            preparation = state["preparation"]
            if preparation is not None:
                state["preparation"] = None
                try:
                    released = state["preparation_methods"]["release"](preparation)
                    resources.extend(
                        WorkspaceTreeResourceCleanup(
                            row.resource_ref,
                            row.kind,
                            row.path,
                            row.ownership,
                            row.cleanup_attempted,
                            row.cleanup_state,
                            row.diagnostics,
                        )
                        for row in released.resources
                    )
                except BaseException as error:  # noqa: BLE001 - drain independent body custody
                    resources.append(
                        WorkspaceTreeResourceCleanup(
                            "physical:" + state["generation"],
                            "physical_preparation",
                            None,
                            "unknown",
                            True,
                            "unknown",
                            (_exception_kind(error),),
                        )
                    )
            retained = state["retention"]
            if retained is not None:
                method = state["retention_methods"]["release_retention"]
                state["retention"] = None
                try:
                    method(retained)
                    cleanup_state, diagnostics = "completed", ()
                except BaseException as error:  # noqa: BLE001 - preserve cleanup uncertainty
                    cleanup_state, diagnostics = "unknown", (_exception_kind(error),)
                resources.append(
                    WorkspaceTreeResourceCleanup(
                        "retention:" + state["generation"],
                        "body_retention",
                        None,
                        "owned",
                        True,
                        cleanup_state,
                        diagnostics,
                    )
                )
            state["source"] = state["request"] = state["capacity_forecast"] = None
            # Borrowed Issue originals belong to their supplier; never release them.
            state["issue_admission"] = state["issue_consumption"] = None
            state["coordinator"] = None
            state["files"] = state["ancestors"] = ()
            if state["session"] is not None:
                resources.append(
                    WorkspaceTreeResourceCleanup(
                        "observation:" + state["generation"],
                        "observation_session",
                        None,
                        "owned",
                        False,
                        "not_attempted",
                        (),
                    )
                )
            known = state["cleanup"].ledger_complete and all(
                row.cleanup_state != "unknown" for row in resources
            )
            overall = (
                "unknown"
                if not known
                else (
                    "incomplete"
                    if state["cleanup"].residual_scratch
                    or any(row.cleanup_state != "completed" for row in resources)
                    else "completed"
                )
            )
            if resources or state["cleanup"].cleanup_state == "not_attempted":
                state["cleanup"] = WorkspaceTreeProjectionCleanupObservation(
                    state["binding"].binding_ref if state["binding"] else None,
                    tuple(resources),
                    state["cleanup"].residual_scratch,
                    overall,
                    known,
                    state["cleanup"].diagnostics,
                )
        finally:
            state["source"] = state["request"] = None

    async def release(self):
        _origin(self)
        async with self.lock:
            _RETIRE(self)
            await _stop_session(self)
            self.phase = "released"
            return repository_tree_projection_value_clone(self.cleanup)

    async def prepare(self, request, source_delivery):
        source_observation = batch = bodies = targets = original = None
        retained_bodies = []
        specifications = []
        try:
            _active(self)
            async with self.lock:
                _active(self)
                if self.phase != "allocated":
                    raise WorkspaceTreeProjectionRefusal("retired")
                self.phase = "preparing"
                self.request = repository_tree_projection_value_clone(request)
                request = self.request
                source_observation = observe_original_repository_workflow_source(
                    source_delivery
                )
                verify_original_repository_workflow_source(
                    source_delivery, expected_binding=request.expected_source_binding
                )
                actual = source_observation.binding
                if (
                    actual.execution_id != self.physical_fields["execution_id"]
                    or tuple(actual.target_root_identity)
                    != self.physical_fields["root_identity"]
                    or actual.target_repository_root
                    != str(self.physical_fields["root"])
                ):
                    raise WorkspaceTreeProjectionRefusal("target_authority_mismatch")
                from .contracts import WorkspaceRepositoryBinding

                # Workflow and v0 observation refs have different namespaces.
                # Derive this association only after original source/root checks.
                self.repository_binding = WorkspaceRepositoryBinding(
                    self.physical_fields["root"],
                    binding_key=actual.target_repository_binding_ref,
                )
                self.source = source_delivery
                originals = {row.output_path: row for row in source_observation.files}
                outputs = tuple(
                    sorted(
                        {
                            row.source_output_path
                            for row in request.files
                            if row.source_output_path is not None
                        }
                    )
                )
                if any(path not in originals for path in outputs):
                    raise WorkspaceTreeProjectionRefusal("source_unavailable")
                # Overlap cannot be admitted from the public checkout mapping alone:
                # source membership/declaration guards are private to its original owner.
                target_root, source_root = (
                    Path(actual.target_repository_root),
                    Path(actual.source_repository_root),
                )
                if target_root.is_relative_to(
                    source_root
                ) or source_root.is_relative_to(target_root):
                    raise WorkspaceTreeProjectionRefusal(
                        "target_authority_mismatch",
                        diagnostics=("overlapping_source_guard_coverage_unavailable",),
                    )
                bodies = {}
                if outputs:
                    batch = read_original_repository_workflow_source(
                        source_delivery,
                        expected_binding=request.expected_source_binding,
                        output_paths=outputs,
                    )
                    bodies = {row.file.output_path: row for row in batch.bodies}
                if set(bodies) != set(outputs):
                    raise WorkspaceTreeProjectionRefusal("source_unavailable")
                targets = {}
                for row in request.files:
                    targets[row.path] = _physical_call(
                        self,
                        "read_tree_entry",
                        row.path,
                        maximum_bytes=request.limits.maximum_file_bytes,
                    )
                for row in request.ancestors:
                    targets[row.path] = _physical_call(
                        self,
                        "read_tree_entry",
                        row.path,
                        maximum_bytes=request.limits.maximum_file_bytes,
                    )
                total_bytes = 0
                retained_bodies = []
                specifications = []
                for row in request.files:
                    target = targets[row.path]
                    before = target.entry
                    if before.exists != (row.kind != "CREATE") or (
                        before.exists
                        and (before.content_digest is None or before.link_count != 1)
                    ):
                        raise WorkspaceTreeProjectionRefusal("stale_target")
                    successor = None
                    original = None
                    if row.kind != "DELETE":
                        original = originals[row.source_output_path]
                        supplied = bodies[row.source_output_path]
                        successor = supplied.body
                        if (
                            supplied.file != original
                            or type(successor) is not bytes
                            or len(successor) != original.size_bytes
                            or _digest(successor) != original.content_digest
                        ):
                            raise WorkspaceTreeProjectionRefusal("stale_source")
                    before_index = successor_index = None
                    if target.body is not None:
                        before_index = len(retained_bodies)
                        retained_bodies.append(target.body)
                    if successor is not None:
                        successor_index = len(retained_bodies)
                        retained_bodies.append(successor)
                    total_bytes += (
                        len(target.body) if target.body is not None else 0
                    ) + (len(successor) if successor is not None else 0)
                    if (
                        max(
                            before.size_bytes or 0,
                            len(successor) if successor is not None else 0,
                        )
                        > request.limits.maximum_file_bytes
                    ):
                        raise WorkspaceTreeProjectionRefusal("quota_exceeded")
                    specifications.append(
                        (row, before, original, before_index, successor_index)
                    )
                if (
                    total_bytes > request.limits.maximum_combined_body_bytes
                    or len(set(retained_bodies))
                    > request.limits.maximum_retained_bodies
                ):
                    raise WorkspaceTreeProjectionRefusal("quota_exceeded")
                ancestor_rows = []
                for row in request.ancestors:
                    before = targets[row.path].entry
                    if (
                        before.exists != (row.intent == "preserve")
                        or before.content_digest is not None
                    ):
                        raise WorkspaceTreeProjectionRefusal("stale_target")
                    ancestor_rows.append(
                        WorkspaceTreeAncestorTransition(
                            row.path, row.intent, before, row.requested_mode
                        )
                    )
                # The original SDK owns this optional representation ABI. Older
                # SDKs retain their original constructor; provider/authority
                # selection never comes from this metadata representation.
                format_abi = vars(WorkspaceRepositoryDeltaRetentionFactory).get(
                    "repository_index_format_abi"
                )
                format_arguments = (
                    {"index_format": "auto"}
                    if type(format_abi) is int and format_abi == 2
                    else {}
                )
                self.retention = WorkspaceRepositoryDeltaRetentionFactory.filesystem(
                    state_root=self.physical_fields["state_root"]
                    / ("tree-retention-" + self.generation),
                    **format_arguments,
                ).allocate_delta_retention()
                self.retention_methods = {
                    name: vars(type(self.retention))[name]
                    for name in (
                        "initialize_delta_retention",
                        "record_bodies",
                        "resolve_body",
                        "record_capture",
                        "record_delta",
                        "resolve_capture",
                        "resolve_delta",
                        "verify_repository_binding",
                        "record_body",
                        "release_retention",
                    )
                }
                self.retention_methods["initialize_delta_retention"](
                    self.retention,
                    repository_binding_ref=actual.target_repository_binding_ref,
                    body_capacity=request.limits.maximum_retained_bodies,
                    maximum_bytes=request.limits.maximum_combined_body_bytes,
                    capture_capacity=request.limits.maximum_retained_captures,
                    delta_capacity=request.limits.maximum_retained_deltas,
                )
                refs = self.retention_methods["record_bodies"](
                    self.retention, tuple(retained_bodies)
                )
                rows = []
                for (
                    row,
                    before,
                    original,
                    before_index,
                    successor_index,
                ) in specifications:
                    rows.append(
                        WorkspaceTreeFileTransition(
                            row.path,
                            row.kind,
                            row.source_output_path,
                            original.source_path if original is not None else None,
                            before,
                            refs[before_index] if before_index is not None else None,
                            refs[successor_index]
                            if successor_index is not None
                            else None,
                            original.content_digest if original is not None else None,
                            original.size_bytes if original is not None else None,
                            row.requested_mode,
                        )
                    )
                self.files = tuple(rows)
                self.ancestors = tuple(ancestor_rows)
                _verify_source_and_bodies(self)
                await _prepare_original_plan(self)
                self.phase = "prepared"
                plan = _issue_handle(self, WorkspaceTreeProjectionPlan)
                self.plan = ref(plan)
                return plan
        except BaseException as error:
            _RETIRE(self)
            await _stop_session(self)
            if isinstance(
                error, (KeyboardInterrupt, SystemExit, asyncio.CancelledError)
            ):
                raise
            if isinstance(error, WorkspaceTreeProjectionRefusal):
                raise WorkspaceTreeProjectionRefusal(
                    error.code,
                    cleanup=self.cleanup,
                    diagnostics=error.evidence.diagnostics,
                ) from error
            code = (
                "physical_unavailable"
                if isinstance(error, (ImportError, ModuleNotFoundError))
                else "physical_refused"
            )
            raise WorkspaceTreeProjectionRefusal(
                code, cleanup=self.cleanup, diagnostics=(_exception_kind(error),)
            ) from error
        finally:
            request = source_delivery = source_observation = batch = bodies = (
                targets
            ) = original = None
            retained_bodies.clear()
            specifications.clear()
            if "successor" in locals():
                successor = None
            if "supplied" in locals():
                supplied = None
            if "target" in locals():
                target = None

    def observe_plan(self, plan):
        try:
            _active(self)
            _require_handle(self, plan, WorkspaceTreeProjectionPlan)
            _verify_source_and_bodies(self)
            _verify_preparation(self)
            if self.binding is None:
                raise WorkspaceTreeProjectionRefusal("physical_unavailable")
            return repository_tree_projection_value_clone(
                WorkspaceTreeProjectionPlanObservation(
                    self.binding, cast(PlanPhase, self.phase), self.cleanup, True, ()
                )
            )
        except BaseException as error:
            # Unknown/foreign handles never retire unrelated recognized families.
            if self.phase == "prepared" and self.plan and plan is self.plan():
                _RETIRE(self)
            if isinstance(
                error,
                (
                    KeyboardInterrupt,
                    SystemExit,
                    asyncio.CancelledError,
                    WorkspaceTreeProjectionRefusal,
                ),
            ):
                raise
            raise WorkspaceTreeProjectionRefusal(
                "physical_refused",
                cleanup=self.cleanup,
                diagnostics=(_exception_kind(error),),
            ) from error
        finally:
            plan = None

    def verify_plan(self, plan, expected_binding):
        try:
            observed = _OBSERVE_PLAN(self, plan)
            if observed.binding != repository_tree_projection_value_clone(
                expected_binding
            ):
                raise WorkspaceTreeProjectionRefusal("retired", cleanup=self.cleanup)
            return observed
        except BaseException as error:
            if self.plan and plan is self.plan():
                _RETIRE(self)
            if isinstance(
                error,
                (
                    KeyboardInterrupt,
                    SystemExit,
                    asyncio.CancelledError,
                    WorkspaceTreeProjectionRefusal,
                ),
            ):
                raise
            raise WorkspaceTreeProjectionRefusal(
                "retired", cleanup=self.cleanup
            ) from error
        finally:
            plan = expected_binding = None

    async def enroll(self, plan, issue_admission):
        _active(self)
        _require_handle(self, plan, WorkspaceTreeProjectionPlan)
        try:
            async with self.lock:
                _active(self)
                if self.phase != "prepared":
                    raise WorkspaceTreeProjectionRefusal(
                        "retired", cleanup=self.cleanup
                    )
                _OBSERVE_PLAN(self, plan)
                _check_issue_ports(self)
                if type(issue_admission) is not IssueTreeProjectionAdmission:
                    raise WorkspaceTreeProjectionRefusal("issue_refused")
                observed = _ISSUE_PORTS["verify_tree_projection_admission"](
                    issue_admission,
                    expected_binding=self.binding,
                )
                _check_issue_ports(self)
                _check_issue_observation(self, observed, "admitted")
                _OBSERVE_PLAN(self, plan)
                self.issue_admission = issue_admission
                self.issue_admission_ref = observed.admission_ref
                self.phase = "enrolled"
                enrollment = _issue_handle(self, WorkspaceTreeProjectionAdmission)
                self.enrollment = ref(enrollment)
                return enrollment
        except BaseException as error:
            _RETIRE(self)
            await _stop_session(self)
            if isinstance(
                error, (KeyboardInterrupt, SystemExit, asyncio.CancelledError)
            ):
                raise
            raise WorkspaceTreeProjectionRefusal(
                "issue_refused",
                cleanup=self.cleanup,
                diagnostics=(_exception_kind(error),),
            ) from error
        finally:
            plan = issue_admission = observed = enrollment = None

    async def project(self, plan, admission):
        controller: Any = None
        _active(self)
        _require_handle(self, plan, WorkspaceTreeProjectionPlan)
        _require_handle(self, admission, WorkspaceTreeProjectionAdmission)
        try:
            async with self.lock:
                _active(self)
                if (
                    self.phase != "enrolled"
                    or not self.enrollment
                    or admission is not self.enrollment()
                ):
                    raise WorkspaceTreeProjectionRefusal(
                        "retired", cleanup=self.cleanup
                    )
                from .repository_diff import WorkspaceRepositoryOperationalBodyStore
                from .repository_mutation import WorkspaceRepositoryMutationCoordinator

                session, binding = self.session, self.binding
                if session is None or binding is None:
                    raise WorkspaceTreeProjectionRefusal("retired")
                self.receipt_store = _physical_call(
                    self,
                    "create_tree_receipt_store",
                    self.repository_binding,
                    capacity=binding.limits.maximum_file_transitions,
                )
                self.coordinator = WorkspaceRepositoryMutationCoordinator(
                    session=session,
                    body_store=WorkspaceRepositoryOperationalBodyStore(
                        capacity=binding.limits.maximum_file_transitions,
                        maximum_bytes=binding.limits.maximum_combined_body_bytes,
                    ),
                    receipt_capacity=binding.limits.maximum_file_transitions,
                    result_store=self.receipt_store,
                )

                async def _controller_step(snapshot):
                    consumption = observed = None
                    try:
                        _active(self)
                        _OBSERVE_PLAN(self, plan)
                        if snapshot.epoch != binding.observation_coordinate.epoch:
                            raise WorkspaceTreeProjectionRefusal("stale_target")
                        _check_issue_ports(self)
                        _verify_pre_spend_capacity(self)
                        self.phase = "spending"  # Irreversible Workspace attempt before supplier spend.
                        try:
                            consumption = _ISSUE_PORTS[
                                "consume_tree_projection_admission"
                            ](self.issue_admission, binding=self.binding)
                        except (KeyboardInterrupt, SystemExit, asyncio.CancelledError):
                            raise
                        except Exception as error:
                            raise WorkspaceTreeProjectionRefusal(
                                "issue_refused"
                            ) from error
                        _check_issue_ports(self)
                        if type(consumption) is not IssueTreeProjectionConsumption:
                            raise WorkspaceTreeProjectionRefusal("issue_refused")
                        self.issue_consumption = consumption
                        observed = _verify_issue_boundary(self)
                        self.issue_consumption_ref = observed.consumption_ref
                        self.phase = "spent"
                        _verify_source_and_bodies(self)
                        _verify_preparation(self)
                        from .observation import WorkspaceRepositorySerializedEffect

                        _prepare_capture(self, snapshot)
                        try:
                            for ordinal in range(binding.transition_count):
                                _verify_issue_boundary(self)
                                _verify_ordinal_source_and_bodies(self, ordinal)
                                _verify_preparation(self, next_ordinal=True)
                                await _settled_physical(self, "apply_next_transition")
                            _verify_issue_boundary(self)
                            _verify_source_and_bodies(self)
                            finished = await _settled_physical(self, "finish")
                            _accept_physical_observation(self, finished)
                            if (
                                finished is None
                                or finished.phase != "consumed"
                                or finished.completed_prefix != binding.transition_count
                                or finished.pending_ordinal is not None
                                or not finished.ledger_complete
                                or len(self.transitions) != binding.transition_count
                                or any(
                                    row.completion_state != "complete"
                                    for row in self.transitions
                                )
                            ):
                                raise WorkspaceTreeProjectionRefusal("physical_refused")
                            await _settled_physical(self, "validate_consumed_current")
                            _verify_issue_boundary(self)
                        except BaseException as error:  # noqa: BLE001 - observe effects before terminal cleanup
                            # Settle and observe the applied prefix even if the return
                            # or a subsequent owner check failed. Never dispatch again.
                            self.execution_error = error
                            _read_physical_history(self)
                        return WorkspaceRepositorySerializedEffect(
                            value=None, poll_after=True
                        )
                    finally:
                        consumption = observed = snapshot = None

                controller = _controller_step
                transition = await _COORDINATOR_TREE(self.coordinator, controller)
                _join_canonical_evidence(self, transition)
                if self.execution_error is not None:
                    error, self.execution_error = self.execution_error, None
                    raise error
                _verify_issue_boundary(self)
                _verify_source_and_bodies(self)
                await _settled_physical(self, "validate_consumed_current")
                _release_physical(self)
                state = _RUNTIME_STORAGE.__get__(
                    self, WorkspaceRepositoryTreeProjectionRuntime
                )
                resources = list(self.cleanup.resources)
                if (
                    state["receipt_store"] is not None
                    and not state["receipt_cleanup_observed"]
                ):
                    # Spend the observation before dispatch. This is cleanup data,
                    # not publication/currentness authority or another disposal.
                    state["receipt_cleanup_observed"] = True
                    known, diagnostics = False, ("receipt_index_origin_unknown",)
                    reader = state["receipt_cleanup_reader"]
                    physical = state["physical"]
                    try:
                        if (
                            type(physical) is not state["physical_class"]
                            or vars(state["physical_class"]).get(
                                "read_tree_receipt_store_cleanup"
                            )
                            is not reader
                            or reader.__code__
                            is not state["receipt_cleanup_reader_code"]
                            or any(
                                vars(physical).get(name) is not value
                                for name, value in state["physical_fields"].items()
                            )
                        ):
                            raise ValueError("Original receipt cleanup reader required")
                        returned = reader(
                            physical,
                            state["repository_binding"],
                            state["receipt_store"],
                        )
                        if (
                            reader.__code__ is not state["receipt_cleanup_reader_code"]
                            or vars(state["physical_class"]).get(
                                "read_tree_receipt_store_cleanup"
                            )
                            is not reader
                            or type(returned) is not tuple
                            or len(returned) != 2
                            or type(returned[0]) is not bool
                            or type(returned[1]) is not tuple
                            or len(returned[1]) > 3
                            or any(
                                type(label) is not str or len(label) > 64
                                for label in returned[1]
                            )
                        ):
                            raise ValueError("Original receipt cleanup result required")
                        known, diagnostics = returned
                    except BaseException as cleanup_error:  # noqa: BLE001 -- preserve original execution failure
                        diagnostics = (_exception_kind(cleanup_error),)
                    if not known:
                        resources.append(
                            WorkspaceTreeResourceCleanup(
                                "receipt-index:" + state["generation"],
                                "repository_index_metadata",
                                None,
                                "owned",
                                True,
                                "unknown",
                                diagnostics,
                            )
                        )
                if len(resources) != len(self.cleanup.resources):
                    self.cleanup = replace(
                        self.cleanup,
                        resources=tuple(resources),
                        cleanup_state="unknown",
                        ledger_complete=False,
                    )
                self.phase = "complete"
                self.final_observation = _tree_observation(self, "complete")
                result = _issue_handle(self, WorkspaceTreeProjectionResult)
                self.result_handle = ref(result)
                return result
        except BaseException as error:
            _read_physical_history(self)
            try:
                self.final_observation = (
                    _tree_observation(self, "held") if self.binding else None
                )
            except Exception:  # noqa: BLE001 - evidence encoding must not strand effect custody
                self.final_observation = None
            finally:
                _RETIRE(self)
                await _stop_session(self)
            self.execution_error = None
            if self.final_observation is not None:
                self.final_observation = replace(
                    self.final_observation,
                    cleanup=self.cleanup,
                    body_retention_state="unavailable",
                    receipts=tuple(
                        replace(row, body_retention_state="unavailable")
                        for row in self.final_observation.receipts
                    ),
                )
            if isinstance(
                error, (KeyboardInterrupt, SystemExit, asyncio.CancelledError)
            ):
                raise
            if isinstance(error, WorkspaceTreeProjectionRefusal):
                raise WorkspaceTreeProjectionRefusal(
                    error.code,
                    observation=self.final_observation,
                    cleanup=self.cleanup,
                    diagnostics=error.evidence.diagnostics,
                ) from (error.__cause__ or error)
            raise WorkspaceTreeProjectionRefusal(
                "physical_refused",
                observation=self.final_observation,
                cleanup=self.cleanup,
                diagnostics=(_exception_kind(error),),
            ) from error
        finally:
            plan = admission = controller = None

    async def resolve(self, admission):
        _origin(self)
        _require_handle(self, admission, WorkspaceTreeProjectionAdmission)
        if self.final_observation is None:
            raise WorkspaceTreeProjectionRefusal("index_unavailable")
        return WorkspaceTreeProjectionResolution(
            repository_tree_projection_value_clone(self.final_observation),
            "known" if _verify_receipt_index(self) else "incomplete",
            False,
        )

    def read_result(self, result, expected_binding):
        _active(self)
        _require_handle(self, result, WorkspaceTreeProjectionResult)
        if (
            self.final_observation is None
            or self.binding != repository_tree_projection_value_clone(expected_binding)
        ):
            raise WorkspaceTreeProjectionRefusal("original_owner_required")
        _verify_source_and_bodies(self)
        _verify_retained_evidence(self)
        return repository_tree_projection_value_clone(self.final_observation)


def _origin(runtime):
    state = _RUNTIME_STORAGE.__get__(runtime, WorkspaceRepositoryTreeProjectionRuntime)
    record = state["sdk_record"]
    if type(runtime) is not WorkspaceRepositoryTreeProjectionRuntime or any(
        vars(record[1]).get(name) is not method for name, method in record[2].items()
    ):
        record[2]["retire"](runtime)
        raise WorkspaceTreeProjectionRefusal("retired", cleanup=state["cleanup"])
    if runtime.pid != os.getpid() or runtime.thread != threading.get_ident():
        raise WorkspaceTreeProjectionRefusal("original_owner_required")


def _active(runtime):
    _origin(runtime)
    if runtime.phase in ("held", "released") or runtime.parent() is None:
        raise WorkspaceTreeProjectionRefusal("retired", cleanup=runtime.cleanup)
    _physical_check(runtime)


def _physical_check(runtime):
    physical = runtime.physical
    if (
        type(physical) is not runtime.physical_class
        or any(
            vars(runtime.physical_class).get(name) is not method
            or name in vars(physical)
            for name, method in runtime.physical_methods.items()
        )
        or any(
            vars(physical).get(name) is not value
            for name, value in runtime.physical_fields.items()
        )
    ):
        _RETIRE(runtime)
        raise WorkspaceTreeProjectionRefusal("retired", cleanup=runtime.cleanup)
    try:
        runtime.physical_methods["check_execution"](physical)
    except (ValueError, OSError) as error:
        _RETIRE(runtime)
        raise WorkspaceTreeProjectionRefusal(
            "retired", cleanup=runtime.cleanup
        ) from error


def _physical_call(runtime, name, *args, **kwargs):
    result = None
    try:
        _physical_check(runtime)
        result = runtime.physical_methods[name](runtime.physical, *args, **kwargs)
        if name == "retain_tree_preparation":
            runtime.preparation = result
        if name == "create_tree_session":
            runtime.session = result
        _physical_check(runtime)
        if name == "read_tree_entry" and (
            type(result) is not WorkspaceTreeTargetRead
            or result.root_identity != runtime.physical_fields["root_identity"]
        ):
            raise WorkspaceTreeProjectionRefusal("physical_refused")
        return result
    except BaseException as error:
        if name == "retain_tree_preparation":
            from aware_file_system.confined_mutation import (
                ConfinedTreeCleanupObservation,
                ConfinedTreeResourceCleanup,
            )
            from aware_file_system.retained_tree_projection import (
                RetainedPhysicalTreeProjectionRefusal,
            )

            if (
                type(error) is RetainedPhysicalTreeProjectionRefusal
                and type(error.cleanup) is ConfinedTreeCleanupObservation
            ):
                original = error.cleanup
                if all(
                    type(row) is ConfinedTreeResourceCleanup
                    for row in original.resources
                ):
                    runtime.cleanup = WorkspaceTreeProjectionCleanupObservation(
                        None,
                        tuple(
                            WorkspaceTreeResourceCleanup(
                                row.resource_ref,
                                row.kind,
                                row.path,
                                cast(ResourceOwnership, row.ownership),
                                row.cleanup_attempted,
                                cast(CleanupState, row.cleanup_state),
                                row.diagnostics,
                            )
                            for row in original.resources
                        ),
                        original.residual_scratch,
                        cast(CleanupState, original.cleanup_state),
                        original.ledger_complete,
                        original.diagnostics,
                    )
        raise
    finally:
        runtime = result = None
        original = None
        args = ()
        kwargs = {}


def _verify_source_and_bodies(runtime):
    verify_original_repository_workflow_source(
        runtime.source, expected_binding=runtime.request.expected_source_binding
    )
    for row in runtime.files:
        for reference, digest, size in (
            (row.before_body_ref, row.before.content_digest, row.before.size_bytes),
            (row.successor_body_ref, row.successor_digest, row.successor_size_bytes),
        ):
            if reference is not None:
                body = runtime.retention_methods["resolve_body"](
                    runtime.retention, reference
                )
                if (
                    type(body) is not bytes
                    or len(body) != size
                    or _digest(body) != digest
                ):
                    raise WorkspaceTreeProjectionRefusal("retention_unavailable")


def _verify_ordinal_source_and_bodies(runtime, ordinal):
    # Binding order is the original ancestors followed by the original files.
    offset = ordinal - len(runtime.ancestors)
    row = runtime.files[offset] if offset >= 0 else None
    output_paths = (
        (row.source_output_path,)
        if row is not None and row.source_output_path is not None
        else ()
    )
    verify_original_repository_workflow_source_paths(
        runtime.source,
        expected_binding=runtime.request.expected_source_binding,
        output_paths=output_paths,
    )
    if row is None:
        return
    for reference, digest, size in (
        (row.before_body_ref, row.before.content_digest, row.before.size_bytes),
        (row.successor_body_ref, row.successor_digest, row.successor_size_bytes),
    ):
        if reference is not None:
            body = runtime.retention_methods["resolve_body"](
                runtime.retention, reference
            )
            if type(body) is not bytes or len(body) != size or _digest(body) != digest:
                raise WorkspaceTreeProjectionRefusal("retention_unavailable")


def _execution_origin(runtime):
    from aware_file_system.retained_tree_projection import (
        RetainedPhysicalTreeProjection,
    )

    _active(runtime)
    if type(runtime.preparation) is not RetainedPhysicalTreeProjection or any(
        vars(RetainedPhysicalTreeProjection).get(name) is not method
        for name, method in runtime.preparation_methods.items()
    ):
        raise WorkspaceTreeProjectionRefusal("physical_refused")


async def _settled_physical(runtime, name):
    _execution_origin(runtime)
    receiver, selected = runtime.preparation, runtime.preparation_methods[name]

    def dispatch():
        try:
            return cast(Any, selected)(receiver), None
        except BaseException as error:  # noqa: BLE001 - settle the actual worker before disposal
            return None, error

    worker = asyncio.get_running_loop().run_in_executor(
        None, copy_context().run, dispatch
    )
    cancelled = None
    try:
        while True:
            try:
                value, error = await asyncio.shield(worker)
                break
            except asyncio.CancelledError as interruption:
                if worker.cancelled():
                    raise  # cancelled before executor dispatch; no live worker to drain
                cancelled = interruption
        _read_physical_history(runtime)
        if name == "apply_next_transition":
            if error is None:
                _accept_transition(runtime, value, len(runtime.transitions))
            else:
                from aware_file_system.retained_tree_projection import (
                    RetainedPhysicalTreeProjectionRefusal,
                )

                if (
                    type(error) is RetainedPhysicalTreeProjectionRefusal
                    and error.transition is not None
                ):
                    _accept_transition(
                        runtime, error.transition, len(runtime.transitions)
                    )
        if cancelled is not None:
            if error is not None:
                raise cancelled from error
            raise cancelled
        if error is not None:
            raise error
        _execution_origin(runtime)
        return value
    finally:
        runtime = receiver = selected = worker = value = error = None


def _accept_physical_observation(runtime, observed):
    from aware_file_system.confined_mutation import ConfinedTreeEffectObservation

    if type(observed) is not ConfinedTreeEffectObservation or (
        observed.preparation_ref != runtime.binding.physical_preparation_ref
        or observed.request_ref != runtime.binding.physical_request_ref
        or not 0 <= observed.completed_prefix <= runtime.binding.transition_count
    ):
        raise WorkspaceTreeProjectionRefusal("physical_refused")
    runtime.physical_observation = observed


def _read_physical_history(runtime):
    if runtime.preparation is None:
        return
    try:
        _execution_origin(runtime)
        observed = runtime.preparation_methods["observe_effects"](runtime.preparation)
        _accept_physical_observation(runtime, observed)
    except BaseException:  # noqa: BLE001 - history loss must not replace the primary failure
        return


def _accept_transition(runtime, returned, ordinal):
    from aware_file_system.confined_mutation import ConfinedTreeTransitionResult

    order = tuple(
        (row.path, "directory_" + row.intent) for row in runtime.ancestors
    ) + tuple((row.path, row.kind) for row in runtime.files)
    if type(returned) is not ConfinedTreeTransitionResult or (
        returned.preparation_ref != runtime.binding.physical_preparation_ref
        or returned.request_ref != runtime.binding.physical_request_ref
        or returned.ordinal != ordinal
        or (returned.path, returned.kind) != order[ordinal]
    ):
        raise WorkspaceTreeProjectionRefusal("physical_refused")
    runtime.transitions.append(returned)


def _tree_cleanup(native, cache=None):
    if cache is None:
        cache = {}

    def convert(row):
        key = id(row)
        if key not in cache:
            cache[key] = WorkspaceTreeResourceCleanup(
                row.resource_ref,
                row.kind,
                row.path,
                row.ownership,
                row.cleanup_attempted,
                row.cleanup_state,
                row.diagnostics,
            )
        return cache[key]

    return WorkspaceTreeProjectionCleanupObservation(
        None,
        tuple(convert(row) for row in native.resources),
        native.residual_scratch,
        native.cleanup_state,
        native.ledger_complete,
        native.diagnostics,
    )


def _tree_observation(runtime, phase):
    physical = runtime.physical_observation
    receipts = []
    cleanup_cache = {}
    for original in runtime.transitions:
        canonical = runtime.canonical_results.get(original.ordinal)
        delta = runtime.deltas.get(original.path)
        receipts.append(
            WorkspaceTreeTransitionReceipt(
                runtime.binding.binding_ref,
                runtime.binding.invocation_ref,
                runtime.issue_consumption_ref,
                original.preparation_ref,
                original.ordinal,
                original.path,
                original.kind,
                tuple(
                    WorkspaceTreePhysicalEffect(
                        row.effect_ref,
                        row.ordinal,
                        row.path,
                        row.role,
                        row.kind,
                        row.state.value,
                        row.before_identity,
                        row.after_identity,
                        row.before_digest,
                        row.after_digest,
                        row.before_size_bytes,
                        row.after_size_bytes,
                        row.before_mode,
                        row.after_mode,
                        row.durability_confirmed,
                        row.error_ref,
                    )
                    for row in original.effects
                ),
                WorkspaceTreeEntryPin(**asdict(original.before)),
                WorkspaceTreeEntryPin(**asdict(original.after))
                if original.after is not None
                else None,
                canonical.receipt.mutation_receipt_ref if canonical else None,
                delta.capture_ref if delta else None,
                delta.delta_ref if delta else None,
                original.effect_state.value,
                original.completion_state,
                original.durability_confirmed,
                original.convergence_state,
                "retained",
                runtime.index_state,
                tuple(row.error_ref for row in original.effects if row.error_ref),
                _tree_cleanup(original.cleanup, cleanup_cache),
            )
        )
    effects = () if physical is None else physical.effects
    state = (
        "unknown"
        if any(row.state.value == "unknown" for row in effects)
        else (
            "applied"
            if any(row.state.value == "applied" for row in effects)
            else "none"
        )
    )
    # Preserve the complete original physical postimage ledger, including
    # root/ancestor pins. A portable array does not confer currentness authority.
    final = (
        ()
        if physical is None
        else tuple(
            WorkspaceTreeEntryPin(**asdict(pin)) for _, pin in physical.final_entries
        )
    )
    observed = WorkspaceTreeProjectionObservation(
        "workspace-tree-result:" + runtime.generation,
        runtime.binding,
        runtime.issue_consumption_ref,
        tuple(receipts),
        0 if physical is None else physical.completed_prefix,
        0
        if physical is None and runtime.binding.transition_count
        else (None if physical is None else physical.pending_ordinal),
        phase,
        final,
        "verified",
        "verified" if phase == "complete" else "unknown",
        "verified" if phase == "complete" else "unknown",
        "retained",
        runtime.index_state,
        state,
        runtime.cleanup,
        physical is not None
        and physical.ledger_complete
        and runtime.cleanup.ledger_complete,
        (() if physical is None else physical.diagnostics)
        + (() if runtime.index_state == "persisted" else ("receipt_index_incomplete",)),
    )
    return repository_tree_projection_value_clone(observed)


def _prepare_capture(runtime, snapshot):
    from .repository_delta import WorkspaceRepositoryDeltaCapturePolicy
    from .repository_delta_capture import WorkspaceRepositoryDeltaCaptureCoordinator

    paths = tuple(
        row.path
        for row in runtime.files
        if row.kind == "DELETE" or row.before.content_digest != row.successor_digest
    )
    if not paths:
        return
    limits = runtime.binding.limits
    runtime.capture_owner = WorkspaceRepositoryDeltaCaptureCoordinator(
        binding=runtime.repository_binding, store=runtime.retention
    )
    runtime.capture = runtime.capture_owner.prepare(
        snapshot=snapshot,
        selected_paths=paths,
        policy=WorkspaceRepositoryDeltaCapturePolicy(
            maximum_selected_files=limits.maximum_file_transitions,
            maximum_selected_bytes=limits.maximum_combined_body_bytes,
            maximum_body_bytes=min(
                limits.maximum_file_bytes, limits.maximum_combined_body_bytes
            ),
            maximum_retained_changes=limits.maximum_retained_deltas,
            maximum_retained_bytes=limits.maximum_combined_body_bytes,
        ),
        context_refs=(runtime.binding.binding_ref, runtime.issue_consumption_ref),
    )
    states = {row.path: row for row in runtime.capture.path_states}
    for row in runtime.files:
        if (
            row.path in states
            and states[row.path].content_digest != row.before.content_digest
        ):
            raise WorkspaceTreeProjectionRefusal("stale_target")


def _join_canonical_evidence(runtime, transition):
    from .repository_delta import RepositoryContentDeltaState

    if runtime.capture_owner is not None:
        for delta in runtime.capture_owner.observe(transition.batch):
            runtime.deltas[delta.new_path or delta.old_path] = delta
    by_path = {row.path: row for row in runtime.files}
    runtime.index_state = "persisted"
    for returned in runtime.transitions:
        row = by_path.get(returned.path)
        if (
            row is None
            or returned.completion_state != "complete"
            or returned.after is None
            or returned.before.content_digest == returned.after.content_digest
        ):
            continue  # Directory and mode-only evidence stay in the original tree receipt.
        delta = runtime.deltas.get(returned.path)
        if (
            delta is None
            or delta.state
            not in (
                RepositoryContentDeltaState.AVAILABLE,
                RepositoryContentDeltaState.BINARY,
            )
            or (delta.old_content_digest, delta.new_content_digest)
            != (returned.before.content_digest, returned.after.content_digest)
        ):
            raise WorkspaceTreeProjectionRefusal("retention_unavailable")
        before_body = (
            None
            if row.before_body_ref is None
            else runtime.retention_methods["resolve_body"](
                runtime.retention, row.before_body_ref
            )
        )
        after_body = (
            None
            if row.successor_body_ref is None
            else runtime.retention_methods["resolve_body"](
                runtime.retention, row.successor_body_ref
            )
        )
        result = _COORDINATOR_RECORD(
            runtime.coordinator,
            returned=returned,
            before=transition.before,
            after=transition.after,
            batch=transition.batch,
            before_content=before_body,
            after_content=after_body,
            binding=runtime.binding,
            consumption_ref=runtime.issue_consumption_ref,
        )
        runtime.canonical_results[returned.ordinal] = result
        if runtime.coordinator.result_store_error is not None:
            runtime.index_state = "unavailable"
    _verify_retained_evidence(runtime)


def _verify_retained_evidence(runtime):
    _verify_source_and_bodies(runtime)
    for delta in runtime.deltas.values():
        actual = runtime.retention_methods["resolve_delta"](
            runtime.retention, delta.delta_ref
        )
        capture = runtime.retention_methods["resolve_capture"](
            runtime.retention, delta.capture_ref
        )
        if (
            actual != delta
            or capture is None
            or capture.capture_ref != runtime.capture.capture_ref
        ):
            raise WorkspaceTreeProjectionRefusal("retention_unavailable")


def _verify_receipt_index(runtime):
    if runtime.index_state != "persisted" or runtime.receipt_store is None:
        return False
    return all(
        runtime.receipt_store.resolve(result.receipt.mutation_receipt_ref)
        == (runtime.binding.binding_ref + ":" + str(ordinal), result)
        for ordinal, result in runtime.canonical_results.items()
    )


def _release_physical(runtime):
    from aware_file_system.confined_mutation import (
        ConfinedTreeCleanupObservation,
        ConfinedTreeEffectObservation,
        ConfinedTreeResourceCleanup,
    )
    from aware_file_system.retained_tree_projection import (
        RetainedPhysicalTreeProjectionRefusal,
    )

    preparation = runtime.preparation
    if preparation is None:
        return
    try:
        runtime.preparation = None  # irreversible cleanup spending before owner call
        native = runtime.preparation_methods["release"](preparation)
        runtime.cleanup = replace(
            _tree_cleanup(native), binding_ref=runtime.binding.binding_ref
        )
    except BaseException as error:  # preserve once-only disposal evidence
        native = (
            error.cleanup
            if type(error) is RetainedPhysicalTreeProjectionRefusal
            else None
        )
        if (
            type(native) is ConfinedTreeCleanupObservation
            and native.preparation_ref == runtime.binding.physical_preparation_ref
            and native.request_ref == runtime.binding.physical_request_ref
            and all(
                type(row) is ConfinedTreeResourceCleanup for row in native.resources
            )
        ):
            runtime.cleanup = replace(
                _tree_cleanup(native), binding_ref=runtime.binding.binding_ref
            )
        else:
            runtime.cleanup = replace(
                runtime.cleanup,
                resources=(
                    *runtime.cleanup.resources,
                    WorkspaceTreeResourceCleanup(
                        "physical:" + runtime.generation,
                        "physical_preparation",
                        None,
                        "unknown",
                        True,
                        "unknown",
                        (_exception_kind(error),),
                    ),
                ),
                cleanup_state="unknown",
                ledger_complete=False,
            )
        observed = (
            error.observation
            if type(error) is RetainedPhysicalTreeProjectionRefusal
            else None
        )
        if (
            type(observed) is ConfinedTreeEffectObservation
            and observed.preparation_ref == runtime.binding.physical_preparation_ref
            and observed.request_ref == runtime.binding.physical_request_ref
            and 0 <= observed.completed_prefix <= runtime.binding.transition_count
        ):
            _accept_physical_observation(runtime, observed)
        raise
    if runtime.cleanup.cleanup_state != "completed":
        raise WorkspaceTreeProjectionRefusal("cleanup_unknown", cleanup=runtime.cleanup)


_owner_json_handoff: tuple[Any, ...] | None = None


def _canonical(value):
    callee = json.dumps
    if _owner_json_handoff is None:
        text = callee(
            value,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
    else:
        native: Any = "_OWNER_JSON_NATIVE_CALL_"
        context: Any = "_OWNER_JSON_NATIVE_CONTEXT_"
        keyword_names: Any = "_OWNER_JSON_NATIVE_KEYWORDS_"
        text = native(context(), callee, value, json, keyword_names)
    return text.encode("utf-8")


try:
    from aware_workspace_sdk._tree_native_binding import (
        bind_owner_json as _bind_owner_json,
    )
except ImportError:
    pass
else:
    _owner_json_handoff = _bind_owner_json(globals(), "_canonical")


async def _prepare_original_plan(runtime):
    from aware_file_system.confined_mutation import (
        ConfinedMutationKind,
        ConfinedTreeAncestorTransition,
        ConfinedTreeEntryPin,
        ConfinedTreeFileTransition,
        ConfinedTreeLimits,
        ConfinedTreePreparationObservation,
        ConfinedTreeProjectionRequest,
    )
    from aware_file_system.retained_tree_projection import (
        RetainedPhysicalTreeProjection,
    )
    from aware_workspace_sdk.repository_source_projection_values import (
        RepositoryObservationCoordinate,
    )

    from .observation import WorkspaceRepositoryObservationSession
    from .repository_mutation import _coordinate

    try:
        request = runtime.request
        native = ConfinedTreeProjectionRequest(
            "workspace-tree-request:" + runtime.generation,
            runtime.physical_fields["root_identity"],
            tuple(
                ConfinedTreeFileTransition(
                    row.path,
                    ConfinedMutationKind[row.kind],
                    ConfinedTreeEntryPin(**asdict(row.before)),
                    runtime.retention_methods["resolve_body"](
                        runtime.retention, row.successor_body_ref
                    )
                    if row.successor_body_ref is not None
                    else None,
                    row.successor_digest,
                    row.successor_size_bytes,
                    row.requested_mode,
                )
                for row in runtime.files
            ),
            tuple(
                ConfinedTreeAncestorTransition(
                    row.path,
                    row.intent,
                    ConfinedTreeEntryPin(**asdict(row.before)),
                    row.requested_mode,
                )
                for row in runtime.ancestors
            ),
            ConfinedTreeLimits(
                **{
                    name: getattr(request.limits, name)
                    for name in vars(ConfinedTreeLimits)["__dataclass_fields__"]
                }
            ),
        )
        descriptor = asdict(native)
        for row in descriptor["files"]:
            row["content"] = None
        expected_digest = _digest(_canonical(descriptor))
        runtime.preparation_methods = {
            name: vars(RetainedPhysicalTreeProjection)[name]
            for name in (
                "observe_preparation",
                "observe_capacity_forecast",
                "validate_current",
                "validate_next_current",
                "release",
                "apply_next_transition",
                "observe_effects",
                "finish",
                "validate_consumed_current",
            )
        }
        preparation = _physical_call(runtime, "retain_tree_preparation", native)
        if type(preparation) is not RetainedPhysicalTreeProjection or any(
            vars(RetainedPhysicalTreeProjection).get(name) is not method
            for name, method in runtime.preparation_methods.items()
        ):
            raise WorkspaceTreeProjectionRefusal("physical_refused")
        observed = runtime.preparation_methods["observe_preparation"](preparation)
        expected_order = tuple(
            (i, row.path, "directory_" + row.intent)
            for i, row in enumerate(runtime.ancestors)
        ) + tuple(
            (i, row.path, row.kind)
            for i, row in enumerate(runtime.files, len(runtime.ancestors))
        )
        if type(observed) is not ConfinedTreePreparationObservation or (
            observed.request_ref != native.request_ref
            or observed.request_digest != expected_digest
            or observed.root_identity != native.root_identity
            or observed.transition_order != expected_order
            or observed.resource_bound != native.limits.maximum_live_descriptors
        ):
            raise WorkspaceTreeProjectionRefusal("physical_refused")
        pins = dict(observed.read_pins)
        expected = {row.path: row.before for row in (*native.ancestors, *native.files)}
        scratch_paths = {row.path for row in observed.scratch_effects}
        if (
            set(pins) != set(expected) | scratch_paths
            or any(type(pin) is not ConfinedTreeEntryPin for pin in pins.values())
            or any(pins[path] != pin for path, pin in expected.items())
            or any(pins[path].exists for path in scratch_paths)
        ):
            raise WorkspaceTreeProjectionRefusal("physical_refused")
        copier, code, defaults, keyword_defaults = _PREPARATION_COPIER
        if (
            _copy_preparation_observation is not copier
            or copier.__code__ is not code
            or copier.__defaults__ is not defaults
            or copier.__kwdefaults__ is not keyword_defaults
        ):
            raise WorkspaceTreeProjectionRefusal("physical_refused")
        runtime.preparation_observation = _canonical(copier(observed))
        _verify_preparation(runtime)
        runtime.session_methods = {
            name: vars(WorkspaceRepositoryObservationSession)[name]
            for name in ("start", "stop")
        }
        runtime.session = _physical_call(
            runtime, "create_tree_session", runtime.repository_binding
        )
        if type(runtime.session) is not WorkspaceRepositoryObservationSession or any(
            vars(WorkspaceRepositoryObservationSession).get(name) is not method
            for name, method in runtime.session_methods.items()
        ):
            raise WorkspaceTreeProjectionRefusal("physical_refused")
        snapshot = await runtime.session_methods["start"](
            runtime.session, background=False
        )
        _active(runtime)
        coordinate = _coordinate(snapshot, runtime.session).observation
        if coordinate is None:
            raise WorkspaceTreeProjectionRefusal("physical_refused")
        scratch = tuple(
            WorkspaceTreeScratchEffect(
                row.path,
                cast(ScratchRole, row.role),
                row.ordinal,
                cast(ScratchKind, row.kind),
                row.requested_mode,
            )
            for row in observed.scratch_effects
        )
        effects = tuple(
            sorted(
                {row.path for row in runtime.files}
                | {row.path for row in runtime.ancestors if row.intent == "create"}
                | scratch_paths
            )
        )
        guards = tuple(
            sorted({row.path for row in runtime.ancestors if row.intent == "preserve"})
        )
        binding = WorkspaceTreeProjectionBinding(
            "workspace-tree-plan:" + runtime.generation,
            "aware.workspace.repository-tree-projection.fs.v1",
            runtime.generation,
            runtime.physical_fields["execution_id"],
            runtime.pid,
            runtime.thread,
            runtime.repository_binding.binding_key,
            native.root_identity,
            request.expected_source_binding,
            RepositoryObservationCoordinate(**asdict(coordinate)),
            request.workflow_ref,
            request.layout_ref,
            request.invocation_ref,
            repository_tree_projection_value_digest(request),
            observed.preparation_ref,
            observed.request_ref,
            observed.request_digest,
            _digest(_canonical(observed.transition_order)),
            len(expected_order),
            runtime.files,
            runtime.ancestors,
            scratch,
            effects,
            guards,
            request.limits,
            "pending",
        )
        payload = asdict(binding)
        del payload["binding_ref"]
        runtime.binding = repository_tree_projection_value_clone(
            replace(binding, binding_ref=_digest(_canonical(payload)))
        )
        _verify_source_and_bodies(runtime)
        _verify_preparation(runtime)
    finally:
        runtime = request = native = descriptor = preparation = observed = None
        binding = payload = row = snapshot = coordinate = None


def _verify_pre_spend_capacity(runtime):
    handle, methods = runtime.preparation, runtime.preparation_methods
    selected = methods["observe_capacity_forecast"]
    try:
        for name, original, code, defaults, kwdefaults in _CAPACITY_ENTRANCES:
            if (
                globals().get(name) is not original
                or original.__code__ is not code
                or original.__defaults__ is not defaults
                or original.__kwdefaults__ is not kwdefaults
            ):
                raise WorkspaceTreeProjectionRefusal("physical_refused")
        origin = cast(Callable[[object], None], _CAPACITY_ENTRANCES[0][1])
        calculate = cast(
            Callable[[object, WorkspaceTreeProjectionBinding], TreeCapacityBound],
            _CAPACITY_ENTRANCES[1][1],
        )
        check = cast(
            Callable[[TreeCapacityBound, int], None], _CAPACITY_ENTRANCES[2][1]
        )
        _execution_origin(runtime)
        origin(selected)
        forecast = selected(handle)
        origin(selected)
        _execution_origin(runtime)
        bound = calculate(forecast, runtime.binding)
        check(bound, runtime.binding.limits.maximum_metadata_bytes)
        # These are descriptive, command-retained evidence. A fresh calculation
        # inside this controller is mandatory; neither value authorizes replay.
        runtime.capacity_forecast = forecast
        runtime.capacity_bound = bound
    finally:
        runtime = handle = methods = selected = forecast = bound = None


def _verify_preparation(runtime, *, next_ordinal=False):
    from aware_file_system.retained_tree_projection import (
        RetainedPhysicalTreeProjection,
    )

    handle = runtime.preparation
    methods = runtime.preparation_methods
    if (
        type(handle) is not RetainedPhysicalTreeProjection
        or methods is None
        or any(
            vars(RetainedPhysicalTreeProjection).get(name) is not method
            for name, method in methods.items()
        )
    ):
        raise WorkspaceTreeProjectionRefusal("physical_refused")
    methods["validate_next_current" if next_ordinal else "validate_current"](handle)
    observed = methods["observe_preparation"](handle)
    from aware_file_system.confined_mutation import ConfinedTreePreparationObservation

    if type(observed) is not ConfinedTreePreparationObservation:
        raise WorkspaceTreeProjectionRefusal("physical_refused")
    copier, code, defaults, keyword_defaults = _PREPARATION_COPIER
    if (
        _copy_preparation_observation is not copier
        or copier.__code__ is not code
        or copier.__defaults__ is not defaults
        or copier.__kwdefaults__ is not keyword_defaults
    ):
        raise WorkspaceTreeProjectionRefusal("physical_refused")
    if _canonical(copier(observed)) != runtime.preparation_observation:
        raise WorkspaceTreeProjectionRefusal("physical_refused")


async def _stop_session(runtime):
    from .observation import WorkspaceRepositoryObservationSession

    session = runtime.session
    if session is None:
        return
    runtime.session = None
    try:
        if type(session) is not WorkspaceRepositoryObservationSession:
            raise WorkspaceTreeProjectionRefusal("original_owner_required")
        await runtime.session_methods["stop"](session)
        state, diagnostics = "completed", ()
    except BaseException as error:  # noqa: BLE001 - retain independent cleanup uncertainty
        state, diagnostics = "unknown", (_exception_kind(error),)
    resources = tuple(
        row for row in runtime.cleanup.resources if row.kind != "observation_session"
    ) + (
        WorkspaceTreeResourceCleanup(
            "observation:" + runtime.generation,
            "observation_session",
            None,
            "released" if state == "completed" else "unknown",
            True,
            state,
            diagnostics,
        ),
    )
    known = runtime.cleanup.ledger_complete and state != "unknown"
    complete = (
        known
        and all(row.cleanup_state == "completed" for row in resources)
        and not runtime.cleanup.residual_scratch
    )
    runtime.cleanup = WorkspaceTreeProjectionCleanupObservation(
        runtime.binding.binding_ref if runtime.binding else None,
        resources,
        runtime.cleanup.residual_scratch,
        "completed" if complete else "unknown",
        known,
        runtime.cleanup.diagnostics + diagnostics,
    )


_RUNTIME_STORAGE = vars(WorkspaceRepositoryTreeProjectionRuntime)["__dict__"]

_RETIRE = vars(WorkspaceRepositoryTreeProjectionRuntime)["retire"]
_OBSERVE_PLAN = vars(WorkspaceRepositoryTreeProjectionRuntime)["observe_plan"]


_ISSUE_PORTS = {
    name: vars(_ISSUE_SDK)[name]
    for name in (
        "verify_tree_projection_admission",
        "consume_tree_projection_admission",
        "verify_tree_projection_consumption",
    )
}


def _check_issue_ports(runtime):
    if any(
        vars(_ISSUE_SDK).get(name) is not original
        for name, original in _ISSUE_PORTS.items()
    ):
        raise WorkspaceTreeProjectionRefusal("issue_refused")
    _active(runtime)


def _check_issue_observation(runtime, observed, phase):
    if type(observed) is not IssueTreeAdmissionObservation or (
        observed.phase != phase
        or observed.binding is None
        or observed.binding.workspace_binding_ref != runtime.binding.binding_ref
        or observed.binding.workspace_plan_ref != runtime.binding.plan_ref
        or observed.binding.execution_id != runtime.physical_fields["execution_id"]
        or observed.admission_ref is None
        or (
            runtime.issue_admission_ref is not None
            and observed.admission_ref != runtime.issue_admission_ref
        )
        or (
            phase == "spent"
            and (
                observed.consumption_state != "spent"
                or observed.consumption_ref is None
            )
        )
        or (
            runtime.issue_consumption_ref is not None
            and observed.consumption_ref != runtime.issue_consumption_ref
        )
    ):
        raise WorkspaceTreeProjectionRefusal("issue_refused")


def _verify_issue_boundary(runtime):
    _check_issue_ports(runtime)
    if type(runtime.issue_consumption) is not IssueTreeProjectionConsumption:
        raise WorkspaceTreeProjectionRefusal("issue_refused")
    observed = _ISSUE_PORTS["verify_tree_projection_consumption"](
        runtime.issue_consumption,
        expected_binding=runtime.binding,
    )
    _check_issue_ports(runtime)
    _check_issue_observation(runtime, observed, "spent")
    return observed


from .repository_mutation import WorkspaceRepositoryMutationCoordinator

_COORDINATOR_TREE = vars(WorkspaceRepositoryMutationCoordinator)["_run_tree_projection"]
_COORDINATOR_RECORD = vars(WorkspaceRepositoryMutationCoordinator)[
    "_record_tree_byte_return"
]
