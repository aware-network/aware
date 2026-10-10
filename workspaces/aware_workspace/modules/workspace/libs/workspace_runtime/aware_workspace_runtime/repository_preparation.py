"""Neutral preparation lifecycle; paths, Git and descriptors belong to FS.

Execution correlation is provider-native, not authenticated actor issuance.
Only the registered owning physical port is admitted. Detached observations and
decoded values cannot supply authority. There are no consumer guard callbacks.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import uuid
from dataclasses import dataclass
from typing import Any
from weakref import WeakKeyDictionary

from aware_workspace_sdk.repository_preparation.authority import (
    RepositoryPreparationAdmission,
    RepositoryPreparationPlan,
)
from aware_workspace_sdk.repository_preparation.codec import (
    detached,
    repository_preparation_value_to_payload,
)
from aware_workspace_sdk.repository_preparation.values import (
    RepositoryPreparationError,
    RepositoryPreparationErrorEvidence,
    RepositoryPreparationPlanObservation,
    RepositoryPrepareRequest,
    RepositoryPrepareResult,
)

_PREPARATION_PORT_TYPES = set()


def _execution():
    candidates = [
        prefix + os.environ[name].strip()
        for name, prefix in (
            ("CODEX_THREAD_ID", "codex-"),
            ("CLAUDE_CODE_SESSION_ID", "claude_code-"),
        )
        if os.environ.get(name, "").strip()
    ]
    if len(candidates) != 1 or any(
        character.isspace() for item in candidates for character in item
    ):
        raise ValueError("unambiguous_provider_execution_required")
    return candidates[0]


@dataclass
class _PlanState:
    request: RepositoryPrepareRequest
    physical: Any
    plan_ref: str
    plan_sha256: str
    phase: str = "planned"
    attempt_ref: str | None = None
    provider_invoked: bool = False


class WorkspaceRepositoryPreparationRuntime:
    def __init__(self, *, physical: Any, repository_root: str, execution_id: str):
        if not any(type(physical) is declared for declared in _PREPARATION_PORT_TYPES):
            raise TypeError("original_preparation_physical_owner_required")
        if _execution() != execution_id:
            raise ValueError("provider_execution_mismatch")
        self.physical = physical
        self.repository_root = repository_root
        self.execution_id = execution_id
        self.pid = os.getpid()
        self.generation = uuid.uuid4().hex
        self.lock = threading.RLock()
        self.plans: WeakKeyDictionary[Any, _PlanState] = WeakKeyDictionary()
        self.admissions: WeakKeyDictionary[Any, Any] = WeakKeyDictionary()
        self.last_evidence: RepositoryPreparationErrorEvidence | None = None
        self.last_original_result: RepositoryPrepareResult | None = None

    def _current(self):
        if os.getpid() != self.pid or _execution() != self.execution_id:
            raise ValueError("preparation_execution_changed")

    def _request(self, request: RepositoryPrepareRequest) -> RepositoryPrepareRequest:
        request = detached(request)
        if request.repository_root != self.repository_root:
            raise ValueError("preparation_request_root_mismatch")
        return request

    def _error(
        self,
        request: RepositoryPrepareRequest,
        code: str,
        phase: str,
        state: _PlanState | None = None,
        *,
        reported_result=None,
        cleanup_state=None,
    ):
        physical = state.physical if state is not None else None
        # A malformed invocation cannot erase the genuine admission's request.
        if state is not None:
            request = state.request
        evidence = RepositoryPreparationErrorEvidence(
            request=request,
            code=code,
            phase=phase,
            execution_id=self.execution_id,
            attempt_ref=state.attempt_ref if state is not None else None,
            effects=tuple(physical.effects) if physical is not None else (),
            cleanup_state=cleanup_state
            or (physical.cleanup_state if physical is not None else "not_attempted"),
            ledger_complete=False,
            provider_invoked=state.provider_invoked if state is not None else False,
            reported_result=reported_result,
            diagnostics=(code,),
        )
        self.last_evidence = detached(evidence)
        return RepositoryPreparationError(evidence=detached(evidence))

    def _retire(self, state: _PlanState):
        state.phase = "retired"
        state.physical.release()

    def plan_repository_preparation(self, request: RepositoryPrepareRequest):
        from aware_workspace_sdk.repository_preparation.authority import _issue_plan

        request = self._request(request)
        with self.lock:
            try:
                self._current()
                physical = self.physical.retain(request)
            except BaseException as error:
                raise self._error(
                    request, "repository_plan_failed", "plan", cleanup_state="unknown"
                ) from error
            try:
                payload = {
                    "request": repository_preparation_value_to_payload(request),
                    "physical_digest": physical.plan_digest(),
                    "execution_id": self.execution_id,
                    "generation": self.generation,
                }
                plan = _issue_plan(self)
                state = _PlanState(
                    request,
                    physical,
                    "repository-plan:" + uuid.uuid4().hex,
                    "sha256:"
                    + hashlib.sha256(
                        json.dumps(
                            payload, sort_keys=True, separators=(",", ":")
                        ).encode()
                    ).hexdigest(),
                )
                self.plans[plan] = state
                return plan
            except BaseException as error:  # noqa: BLE001 -- retire retained custody on interrupted plan construction
                try:
                    physical.release()
                finally:
                    unpublished = _PlanState(request, physical, "unissued", "unissued")
                    raise self._error(
                        request, "repository_plan_failed", "plan", unpublished
                    ) from error

    def observe_plan(self, plan):
        if type(plan) is not RepositoryPreparationPlan:
            raise ValueError("original_preparation_plan_required")
        with self.lock:
            state = self.plans.get(plan)
            if state is None:
                raise ValueError("original_preparation_plan_required")
            if state.phase not in ("retired", "consumed"):
                try:
                    self._current()
                    state.physical.validate_current()
                except BaseException as error:  # noqa: BLE001 -- freshness interruption terminally retires custody
                    try:
                        self._retire(state)
                    finally:
                        raise self._error(
                            state.request, "repository_plan_stale", "observation", state
                        ) from error
            return detached(
                RepositoryPreparationPlanObservation(
                    state.request,
                    state.plan_ref,
                    state.plan_sha256,
                    self.execution_id,
                    state.phase,
                    state.physical.ordered_effect_paths(),
                    tuple(state.physical.snapshot["diagnostics"]),
                )
            )

    def release_plan(self, plan):
        if type(plan) is not RepositoryPreparationPlan:
            raise ValueError("original_preparation_plan_required")
        with self.lock:
            state = self.plans.get(plan)
            if state is not None and state.phase != "consumed":
                try:
                    self._retire(state)
                except BaseException as error:
                    raise self._error(
                        state.request, "repository_cleanup_unverified", "cleanup", state
                    ) from error

    def release_admission(self, admission):
        if type(admission) is not RepositoryPreparationAdmission:
            raise ValueError("original_preparation_admission_required")
        with self.lock:
            plan = self.admissions.pop(admission, None)
            if plan is not None:
                self.release_plan(plan)

    def admit_repository_preparation(self, plan):
        from aware_workspace_sdk.repository_preparation.authority import (
            _issue_admission,
        )

        if type(plan) is not RepositoryPreparationPlan:
            raise ValueError("original_preparation_plan_required")
        with self.lock:
            state = self.plans.get(plan)
            if state is None:
                raise ValueError("original_preparation_plan_required")
            try:
                self._current()
                if state.phase != "planned" or state.request.dry_run:
                    raise ValueError("preparation_plan_not_admittable")
                state.physical.validate_current()
                admission = _issue_admission(self)
                self.admissions[admission] = plan
                state.phase = "admitted"
                return admission
            except BaseException as error:  # noqa: BLE001 -- original admission must retire on interrupted freshness
                try:
                    self._retire(state)
                finally:
                    raise self._error(
                        state.request,
                        "repository_admission_refused",
                        "admission",
                        state,
                    ) from error

    def prepare_repository(self, request: RepositoryPrepareRequest, *, admission=None):
        with self.lock:
            self.last_evidence = None
            self.last_original_result = None
            # Resolve/spend the original capability before any freshness or
            # request failure. A mismatched invocation cannot leave it live.
            plan = (
                self.admissions.pop(admission, None)
                if type(admission) is RepositoryPreparationAdmission
                else None
            )
            state = self.plans.get(plan) if plan is not None else None
            if admission is not None and state is None:
                raise self._error(
                    request, "original_preparation_admission_required", "admission"
                )
            if state is not None:
                previous_phase = state.phase
                state.phase = "spent"
                state.attempt_ref = "repository-attempt:" + uuid.uuid4().hex
            else:
                previous_phase = None
            try:
                request = self._request(request)
                self._current()
                if request.dry_run:
                    if admission is not None:
                        raise ValueError("preview_cannot_consume_apply_admission")
                    plan = self.plan_repository_preparation(request)
                    state = self.plans[plan]
                    state.phase = "spent"
                elif state is None:
                    raise ValueError("repository_apply_admission_required")
                elif previous_phase != "admitted" or state.request != request:
                    raise ValueError("repository_admission_request_mismatch")
                state.physical.validate_current()
                state.provider_invoked = not request.dry_run
                if request.dry_run:
                    observed = state.physical.snapshot
                else:
                    from aware_workspace_sdk.repository_preparation.authority import (
                        _issue_physical_claim,
                    )

                    claim = _issue_physical_claim(self, plan)
                    try:
                        observed = state.physical.prepare(claim=claim)
                    finally:
                        claim.release()
                state.physical.release()
                if state.physical.cleanup_state != "completed":
                    raise ValueError("repository_cleanup_unverified")
                result = RepositoryPrepareResult(
                    request=request,
                    outcome=observed["outcome"],
                    repository_root=request.repository_root,
                    head=observed["head"],
                    diagnostics=tuple(observed["diagnostics"]),
                    execution_id=self.execution_id,
                    attempt_ref=state.attempt_ref,
                    effects=tuple(state.physical.effects),
                    cleanup_state="completed",
                    ledger_complete=True,
                    provider_invoked=state.provider_invoked,
                )
                # Preserve original owner evidence BEFORE consumer validation.
                self.last_evidence = detached(
                    RepositoryPreparationErrorEvidence(
                        state.request,
                        "repository_result_invalid",
                        "result",
                        self.execution_id,
                        state.attempt_ref,
                        tuple(state.physical.effects),
                        "completed",
                        False,
                        state.provider_invoked,
                        None,
                        ("repository_result_invalid",),
                    )
                )
                state.phase = "consumed"
                self.last_original_result = detached(result)
                return detached(result)
            except BaseException as error:
                if state is not None:
                    try:
                        self._retire(state)
                    except BaseException:  # noqa: BLE001 -- retain original failure and unknown cleanup
                        state.phase = "retired"  # No cleanup outcome upgrade.
                if isinstance(error, RepositoryPreparationError):
                    raise
                raise self._error(
                    request, "repository_preparation_failed", "prepare", state
                ) from error

    def result_failure(self, request: RepositoryPrepareRequest, reported_result):
        with self.lock:
            evidence = self.last_evidence
            # This ledger belongs to the original dispatch under the same
            # lock. A mismatched caller/report cannot replace its history.
            if evidence is None:
                evidence = self._error(
                    request, "repository_result_invalid", "result"
                ).evidence
            from dataclasses import replace

            return RepositoryPreparationError(
                evidence=detached(
                    replace(
                        evidence,
                        code="repository_result_invalid",
                        phase="result",
                        reported_result=reported_result,
                        ledger_complete=False,
                    )
                )
            )


from aware_workspace_sdk.repository_preparation.authority import _RUNTIME_TYPES

_RUNTIME_TYPES.add(WorkspaceRepositoryPreparationRuntime)
