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
from .source_scope_policy import evaluate_issue_source_scope
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


@dataclass
class _TreeRecord:
    request: object
    request_ref: str
    workspace: object = None
    workspace_plan: object = None
    binding: object = None
    binding_observation: object = None
    capture: object = None
    generation: str | None = None
    admission_ref: str | None = None
    consumption_ref: str | None = None
    phase: str = "prepared"
    consumption_state: str = "not_spent"
    cleanup_state: str = "not_attempted"
    ledger_complete: bool = True
    diagnostics: tuple = ()
    cleanup: object = None


class IssueTreeProjectionRuntime:
    """C authority only. Physical reads are own; cross-domain calls use SDKs."""

    def __init__(self, physical):
        from weakref import WeakKeyDictionary

        from aware_issue_fs_adapter.source_projection import (
            FilesystemIssueProjectionPort,
        )

        if type(physical) is not FilesystemIssueProjectionPort:
            raise TypeError("original Issue physical owner required")
        self.physical = physical
        self.physical_type = FilesystemIssueProjectionPort
        self.physical_methods = {
            name: vars(FilesystemIssueProjectionPort)[name]
            for name in ("check_execution", "read", "read_tree_authority")
        }
        self.physical_fields = dict(vars(physical))
        self.pid, self.thread = os.getpid(), threading.get_ident()
        self.records = WeakKeyDictionary()
        self.lock = threading.RLock()
        self.sdk_record = None

    def check_current(self):
        from aware_issue_sdk.source_projection import IssueTreeProjectionRefusal

        if self.pid != os.getpid() or self.thread != threading.get_ident():
            raise IssueTreeProjectionRefusal("issue_tree_origin_mismatch")
        if (
            type(self.physical) is not self.physical_type
            or any(
                vars(self.physical_type).get(name) is not method
                for name, method in self.physical_methods.items()
            )
            or vars(self.physical) != self.physical_fields
        ):
            self.retire_all()
            raise IssueTreeProjectionRefusal("issue_tree_physical_owner_changed")

    def retire_all(self):
        # Called through the original SDK capture even if runtime methods change.
        for record in tuple(self.records.values()):
            _tree_retire(record)

    def _record(self, handle, kind=None):
        from aware_issue_sdk.source_projection import (
            IssueTreeProjectionAdmission,
            IssueTreeProjectionAdmissionPlan,
            IssueTreeProjectionConsumption,
            IssueTreeProjectionRefusal,
        )

        kinds = (
            IssueTreeProjectionAdmissionPlan,
            IssueTreeProjectionAdmission,
            IssueTreeProjectionConsumption,
        )
        original = record = None
        try:
            for original, record in self.records.items():
                if original is handle:
                    if type(handle) not in kinds or (
                        kind is not None and type(handle) is not kind
                    ):
                        _tree_retire(record)
                        raise _tree_refusal(record, "issue_tree_handle_kind_changed")
                    return record
            # A foreign input never disposes a recognized unrelated family.
            raise IssueTreeProjectionRefusal("issue_tree_foreign_handle")
        finally:
            # Client-directed unknown lookup has the same traceback-custody
            # boundary as the public SDK registry. Preserve diagnostics only.
            original = record = handle = None

    def _fresh(self, record):
        try:
            capture, projection = self.physical.read_tree_authority(record.request)
        except BaseException as error:
            if getattr(error, "code", None) == "issue_read_descriptor_cleanup_failed":
                record.ledger_complete = False
                record.diagnostics = (*record.diagnostics, "issue_read_cleanup_unknown")
            raise
        if record.capture is not None and capture != record.capture:
            from aware_issue_sdk.source_projection import IssueTreeProjectionRefusal

            raise IssueTreeProjectionRefusal("issue_tree_authority_changed")
        _tree_authorize(self, record, capture, projection)
        return capture

    async def prepare(self, request, workspace, workspace_plan, expected_binding):
        from uuid import uuid4

        from aware_issue_sdk.repository_tree_projection_values import (
            IssueTreeProjectionRequest,
        )
        from aware_issue_sdk.source_projection import (
            IssueTreeProjectionAdmissionPlan,
            _tree_handle,
        )

        self.check_current()
        try:
            request = _tree_clone(request)
        except (ValueError, TypeError) as error:
            from aware_issue_sdk.source_projection import IssueTreeProjectionRefusal

            raise IssueTreeProjectionRefusal("issue_tree_malformed_request") from error
        if type(request) is not IssueTreeProjectionRequest:
            raise TypeError("original Issue tree request required")
        record = _TreeRecord(request, "issue-tree-request:" + uuid4().hex)
        try:
            record.workspace, record.workspace_plan = workspace, workspace_plan
            record.binding = _tree_workspace_binding(
                workspace, workspace_plan, expected_binding
            )
            record.binding_observation = _tree_binding_observation(record.binding)
            record.capture = self._fresh(record)
            record.generation = self.physical.digest(
                record.capture[1] + record.capture[4]
            )
            plan = _tree_handle(self, IssueTreeProjectionAdmissionPlan)
            with self.lock:
                self.records[plan] = record
            return plan
        except BaseException as error:
            _tree_retire(record)
            raise _tree_refusal(
                record, getattr(error, "code", "issue_tree_preparation_failed"), error
            ) from error

    async def admit(self, plan):
        from uuid import uuid4

        from aware_issue_sdk.source_projection import (
            IssueTreeProjectionAdmission,
            IssueTreeProjectionAdmissionPlan,
            _tree_handle,
        )

        record = self._record(plan, IssueTreeProjectionAdmissionPlan)
        with self.lock:
            if record.phase != "prepared":
                raise _tree_refusal(record, "issue_tree_admission_spent")
            record.phase = "admitted"
        # Supplier calls never hold the Issue registry lock.
        try:
            _tree_workspace_binding(
                record.workspace, record.workspace_plan, record.binding
            )
            self._fresh(record)
            admission = _tree_handle(self, IssueTreeProjectionAdmission)
            record.admission_ref = "issue-tree-admission:" + uuid4().hex
            with self.lock:
                self.records[admission] = record
            return admission
        except BaseException as error:
            _tree_retire(record)
            raise _tree_refusal(
                record, getattr(error, "code", "issue_tree_admission_failed"), error
            ) from error

    def observe(self, handle):
        return _tree_observation(self._record(handle))

    async def release(self, handle):
        record = self._record(handle)
        with self.lock:
            _tree_retire(record, released=True)
            return _tree_clone(record.cleanup)

    def verify(self, admission, expected_binding):
        from aware_issue_sdk.source_projection import IssueTreeProjectionAdmission

        record = self._record(admission, IssueTreeProjectionAdmission)
        with self.lock:
            if record.phase != "admitted":
                raise _tree_refusal(record, "issue_tree_admission_spent")
            try:
                _tree_expected(record, expected_binding)
                self._fresh(record)
                return _tree_observation(record)
            except BaseException as error:
                _tree_retire(record)
                raise _tree_refusal(
                    record,
                    getattr(error, "code", "issue_tree_verification_failed"),
                    error,
                ) from error

    def consume(self, admission, binding):
        from uuid import uuid4

        from aware_issue_sdk.source_projection import (
            IssueTreeProjectionAdmission,
            IssueTreeProjectionConsumption,
            _tree_handle,
        )

        record = self._record(admission, IssueTreeProjectionAdmission)
        with self.lock:
            if record.phase != "admitted":
                raise _tree_refusal(record, "issue_tree_admission_spent")
            # Irreversible spend precedes every fallible freshness/correlation check.
            record.phase, record.consumption_state = "spending", "spent"
            try:
                _tree_expected(record, binding)
                self._fresh(record)
                consumption = _tree_handle(self, IssueTreeProjectionConsumption)
                record.consumption_ref = "issue-tree-consumption:" + uuid4().hex
                self.records[consumption] = record
                record.phase = "spent"
                return consumption
            except BaseException as error:
                _tree_retire(record)
                raise _tree_refusal(
                    record,
                    getattr(error, "code", "issue_tree_consumption_failed"),
                    error,
                ) from error

    def verify_consumption(self, consumption, expected_binding):
        from aware_issue_sdk.source_projection import IssueTreeProjectionConsumption

        record = self._record(consumption, IssueTreeProjectionConsumption)
        with self.lock:
            if record.phase != "spent" or record.consumption_state != "spent":
                raise _tree_refusal(record, "issue_tree_consumption_retired")
            try:
                _tree_expected(record, expected_binding)
                self._fresh(record)
                return _tree_observation(record)
            except BaseException as error:
                _tree_retire(record)
                raise _tree_refusal(
                    record, getattr(error, "code", "issue_tree_ordinal_refused"), error
                ) from error


def _tree_clone(value):
    from aware_issue_sdk.repository_tree_projection_codec import (
        _tree_projection_value_clone,
    )

    return _tree_projection_value_clone(value)


def _tree_workspace_binding(client, plan, expected):
    from aware_issue_sdk.source_projection import IssueTreeProjectionRefusal
    from aware_workspace_sdk.repository_tree_projection import (
        WorkspaceRepositoryTreeProjectionClient,
        WorkspaceTreeProjectionPlan,
    )
    from aware_workspace_sdk.repository_tree_projection_codec import (
        repository_tree_projection_value_clone,
    )

    if (
        type(client) is not WorkspaceRepositoryTreeProjectionClient
        or type(plan) is not WorkspaceTreeProjectionPlan
    ):
        raise IssueTreeProjectionRefusal("issue_tree_original_workspace_required")
    if any(
        vars(WorkspaceRepositoryTreeProjectionClient).get(name) is not method
        for name, method in _TREE_WORKSPACE_PORTS.items()
    ):
        raise IssueTreeProjectionRefusal("issue_tree_workspace_port_changed")
    expected = repository_tree_projection_value_clone(expected)
    observed = _TREE_WORKSPACE_PORTS["observe_tree_projection_plan"](client, plan)
    verified = _TREE_WORKSPACE_PORTS["verify_tree_projection_plan"](
        client, plan, expected_binding=expected
    )
    if (
        observed.binding != expected
        or verified != observed
        or observed.phase != "prepared"
        or not observed.ledger_complete
    ):
        raise IssueTreeProjectionRefusal("issue_tree_workspace_binding_mismatch")
    return repository_tree_projection_value_clone(observed.binding)


def _tree_expected(record, expected):
    from aware_issue_sdk.source_projection import IssueTreeProjectionRefusal

    # Literal descriptive SDK validation only, never reciprocal owner callbacks.
    validator = _TREE_WORKSPACE_VALIDATE_EQUAL
    if (
        vars(_TreeWorkspaceCodec).get("repository_tree_projection_value_validate_equal")
        is not validator
        or validator.__code__ is not _TREE_WORKSPACE_VALIDATE_EQUAL_CODE
    ):
        raise IssueTreeProjectionRefusal(
            "issue_tree_workspace_binding_validator_changed"
        )
    try:
        validator(expected, expected_value=record.binding)
    except _TREE_WORKSPACE_VALUE_ERROR as error:
        raise IssueTreeProjectionRefusal("issue_tree_binding_mismatch") from error
    if (
        vars(_TreeWorkspaceCodec).get("repository_tree_projection_value_validate_equal")
        is not validator
        or validator.__code__ is not _TREE_WORKSPACE_VALIDATE_EQUAL_CODE
    ):
        raise IssueTreeProjectionRefusal(
            "issue_tree_workspace_binding_validator_changed"
        )


def _tree_binding_observation(binding):
    from aware_issue_sdk.repository_tree_projection_values import (
        IssueTreeBindingObservation,
    )

    return _tree_clone(
        IssueTreeBindingObservation(
            binding.plan_ref,
            binding.provider_ref,
            binding.provider_generation,
            binding.binding_ref,
            binding.target_repository_binding_ref,
            binding.target_root_identity,
            binding.execution_id,
            binding.process_id,
            binding.thread_id,
            binding.workflow_ref,
            binding.layout_ref,
            binding.source_binding.delivery_ref,
            binding.physical_preparation_ref,
            binding.transition_sequence_digest,
            binding.transition_count,
            binding.effect_paths,
            binding.read_guard_paths,
            tuple(sorted({row.path for row in binding.scratch_effects})),
        )
    )


def _tree_authorize(owner, record, capture, projection):
    from aware_issue_sdk.source_projection import IssueTreeProjectionRefusal

    request, binding = record.request, record.binding
    if (
        request.actor_ref != owner.physical.execution_id
        or binding.execution_id != request.actor_ref
    ):
        raise IssueTreeProjectionRefusal("issue_owner_execution_mismatch")
    if (binding.process_id, binding.thread_id) != (owner.pid, owner.thread):
        raise IssueTreeProjectionRefusal("issue_tree_origin_mismatch")
    if (
        binding.target_root_identity != owner.physical.root_identity
        or binding.source_binding.target_repository_root != str(owner.physical.root)
    ):
        raise IssueTreeProjectionRefusal("issue_tree_target_authority_mismatch")
    if owner.physical.digest(capture[1]) != request.expected_issue_source_sha256:
        raise IssueTreeProjectionRefusal("issue_tree_source_sha256_mismatch")
    if any(
        path == protected or protected.startswith(path + "/")
        for path in binding.effect_paths
        for protected in (capture[0], "aware.protocol.toml")
    ):
        raise IssueTreeProjectionRefusal("issue_tree_authority_effect_forbidden")
    decision = evaluate_issue_source_scope(
        issue_owner=projection.owner_ref or "",
        issue_status=projection.status,
        scope_paths=projection.ownership_scope,
        actor_ref=request.actor_ref,
        effect_paths=binding.effect_paths,
    )
    if not decision.allowed:
        raise IssueTreeProjectionRefusal(str(decision.refusal))


def _tree_observation(record):
    from aware_issue_sdk.repository_tree_projection_values import (
        IssueTreeAdmissionObservation,
    )

    capture = record.capture
    return _tree_clone(
        IssueTreeAdmissionObservation(
            record.request.issue_ref,
            record.request_ref,
            record.binding_observation,
            capture[0] if capture else None,
            record.request.expected_issue_source_sha256 if capture else None,
            capture[2][:2] if capture else None,
            record.generation,
            record.admission_ref,
            record.consumption_ref,
            record.phase,
            record.consumption_state,
            record.cleanup_state,
            record.ledger_complete,
            record.diagnostics,
            False,
        )
    )


def _tree_retire(record, *, released=False):
    from aware_issue_sdk.repository_tree_projection_values import (
        IssueTreeAdmissionCleanup,
        IssueTreeResourceCleanup,
    )

    if record.cleanup is None:
        resources = tuple(
            IssueTreeResourceCleanup(
                record.request_ref + ":" + kind,
                kind,
                None,
                "borrowed",
                False,
                "not_attempted",
                (),
            )
            for kind, value in (
                ("workspace_client", record.workspace),
                ("workspace_plan", record.workspace_plan),
            )
            if value is not None
        )
        record.workspace = record.workspace_plan = None
        record.cleanup_state = "completed" if record.ledger_complete else "unknown"
        if not record.ledger_complete:
            resources += (
                IssueTreeResourceCleanup(
                    record.request_ref + ":authority-read",
                    "authority_read_descriptors",
                    None,
                    "unknown",
                    True,
                    "unknown",
                    record.diagnostics,
                ),
            )
        record.cleanup = _tree_clone(
            IssueTreeAdmissionCleanup(
                record.request.issue_ref,
                record.request_ref,
                record.admission_ref,
                record.consumption_ref,
                resources,
                record.cleanup_state,
                record.ledger_complete,
                record.diagnostics,
            )
        )
        # Retain historical identities, not the read source body or borrowed handles.
        if record.capture is not None:
            row = record.capture
            record.capture = (row[0], None, row[2], row[3], None, row[5], row[6])
    record.phase = "released" if released else "retired"


def _tree_refusal(record, code, error=None):
    from aware_issue_sdk.source_projection import IssueTreeProjectionRefusal

    if error is not None:
        record.diagnostics = (*record.diagnostics, code)
    return IssueTreeProjectionRefusal(
        code,
        observation=_tree_observation(record),
        cleanup=_tree_clone(record.cleanup) if record.cleanup else None,
        supplier_evidence=getattr(error, "evidence", None),
    )


# Fixed public Workspace SDK entrances, not injected evaluators or FS dispatch.
from aware_workspace_sdk import repository_tree_projection_codec as _TreeWorkspaceCodec
from aware_workspace_sdk.repository_tree_projection import (
    WorkspaceRepositoryTreeProjectionClient as _TreeWorkspaceClient,
)

_TREE_WORKSPACE_PORTS = {
    name: vars(_TreeWorkspaceClient)[name]
    for name in ("observe_tree_projection_plan", "verify_tree_projection_plan")
}

_TREE_WORKSPACE_VALIDATE_EQUAL = (
    _TreeWorkspaceCodec.repository_tree_projection_value_validate_equal
)
_TREE_WORKSPACE_VALIDATE_EQUAL_CODE = _TREE_WORKSPACE_VALIDATE_EQUAL.__code__
_TREE_WORKSPACE_VALUE_ERROR = _TreeWorkspaceCodec.WorkspaceTreeProjectionValueError
