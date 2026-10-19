"""Neutral enrollment correlation; filesystem policy and durability stay in FS.

Enrollment is a prerequisite, not exact-effect publication admission. Only the
distinct configuration admission can enter the selected shared writer branch;
neither enrollment nor configuration admission can spend an Issue lease.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any

from aware_workspace_sdk.initial_authoring.values import (
    InitialAuthoringEnrollmentEvidence,
    InitialConfigurationRequest,
)
from aware_workspace_sdk.repository_publication.authority import (
    WorkspaceRepositoryCommitPlan,
)


class InitialAuthoringEnrollmentState:
    def __init__(self, owner, evidence):
        self._owner = owner
        self._evidence = InitialAuthoringEnrollmentEvidence.from_wire(
            evidence.to_wire()
        )

    def observe(self):
        self._owner._current()
        evidence = self._owner._physical.observe_initial_authoring_enrollment()
        if evidence != self._evidence:
            raise ValueError("initial_authoring_original_enrollment_changed")
        return InitialAuthoringEnrollmentEvidence.from_wire(evidence.to_wire())


def enroll_from_original_preparation(owner, preparation_client):
    from aware_workspace_sdk.initial_authoring.authority import (
        _issue_enrollment_claim,
        _issue_initial_enrollment,
        _retire_enrollment_claim,
    )

    owner._current()
    # The SDK supplies its retained successful original dispatch. Neither a
    # decoded preparation result nor runtime.last_original_result is accepted.
    claim = _issue_enrollment_claim(owner, preparation_client)
    try:
        evidence = owner._physical.enroll_initial_authoring(claim)
    finally:
        _retire_enrollment_claim(claim)
    owner._current()
    return _issue_initial_enrollment(
        owner, InitialAuthoringEnrollmentState(owner, evidence)
    )


def restore_original_enrollment(owner):
    from aware_workspace_sdk.initial_authoring.authority import (
        _issue_initial_enrollment,
    )

    owner._current()
    evidence = owner._physical.observe_initial_authoring_enrollment(
        confirm_durability=True
    )
    if evidence.execution_id != owner._execution:
        raise ValueError("initial_authoring_execution_mismatch")
    owner._current()
    return _issue_initial_enrollment(
        owner, InitialAuthoringEnrollmentState(owner, evidence)
    )


from aware_workspace_sdk.initial_authoring.authority import _STATE_TYPES

_STATE_TYPES.add(InitialAuthoringEnrollmentState)


def _configuration(owner, protocol_plan):
    # The explicitly selected original physical provider qualifies the concrete
    # producer. Neutral orchestration does not import a filesystem/Protocol rail.
    return owner._physical.require_initial_configuration_source(protocol_plan)


@dataclass
class InitialConfigurationState:
    owner: Any
    workspace_plan: WorkspaceRepositoryCommitPlan
    protocol_plan: object
    request: InitialConfigurationRequest
    frozen_wire: bytes
    frozen_binding: bytes
    phase: str = "planned"
    work: object = None
    admission_wire: bytes | None = None
    expires_monotonic: float | None = None

    def validate(self):
        from aware_workspace_sdk.initial_authoring.values import _canonical

        self.owner._current()
        if (
            type(self.request) is not InitialConfigurationRequest
            or self.owner._snapshot_handle(self.workspace_plan).purpose
            != "initial_configuration"
            or _canonical(self.request.to_wire()) != self.frozen_wire
            or _canonical(self.owner._detached_binding(self.workspace_plan.binding))
            != self.frozen_binding
            or self.workspace_plan.binding.provider_ref != self.owner._provider_ref
            or self.workspace_plan.binding.provider_generation != self.owner._generation
            or self.workspace_plan.binding.execution_id != self.owner._execution
            or _configuration(self.owner, self.protocol_plan).to_wire()
            != self.request.to_wire()["configuration"]
        ):
            raise ValueError("initial_configuration_plan_mutated")


def plan_initial_configuration(owner, enrollment, protocol_plan, idempotency_key):
    from aware_workspace_sdk.initial_authoring.authority import (
        _ENROLLMENTS,
        InitialAuthoringEnrollment,
        InitialConfigurationPlan,
        _issue_configuration_handle,
    )
    from aware_workspace_sdk.initial_authoring.values import (
        _canonical,
        configuration_request,
    )
    from aware_workspace_sdk.repository_publication.values import (
        WorkspaceRepositoryCommitRequest,
    )

    owner._current()
    state = (
        _ENROLLMENTS.get(enrollment)
        if type(enrollment) is InitialAuthoringEnrollment
        else None
    )
    if state is None or state._owner is not owner:
        raise ValueError("original_initial_authoring_enrollment_required")
    evidence = state.observe()
    config = _configuration(owner, protocol_plan)
    if config.repository_root != evidence.repository_root:
        raise ValueError("initial_configuration_root_mismatch")
    request = configuration_request(evidence, config, idempotency_key)
    workspace_plan = owner._plan_repository_operation(
        WorkspaceRepositoryCommitRequest(
            config.repository_root,
            ("aware.protocol.toml",),
            "Initialize Project-capable Protocol configuration",
            request.request_ref,
        ),
        initial_configuration=config.content,
    )
    result = InitialConfigurationState(
        owner,
        workspace_plan,
        protocol_plan,
        request,
        _canonical(request.to_wire()),
        _canonical(owner._detached_binding(workspace_plan.binding)),
    )
    return _issue_configuration_handle(owner, result, InitialConfigurationPlan)


def admit_initial_configuration(owner, plan, *, _project=False):
    from aware_workspace_sdk.initial_authoring.authority import (
        InitialConfigurationAdmission,
        InitialConfigurationPlan,
        InitialProjectAdmission,
        InitialProjectPlan,
        _configuration_state,
        _issue_configuration_handle,
        _issue_configuration_reservation,
        _retire_configuration_reservation,
    )
    from aware_workspace_sdk.initial_authoring.values import _canonical

    state = _configuration_state(
        owner, plan, InitialProjectPlan if _project else InitialConfigurationPlan
    )
    if _project:
        owner._physical.require_initial_project_source(state.source_plan, current=True)
    if state.phase != "planned" or state.workspace_plan.phase != "planned":
        raise ValueError("initial_configuration_plan_terminal")
    # Reserve intent before issuing the distinct live admission. A failed or
    # interrupted reservation is never silently rewritten or redispatched.
    state.phase = "reserving"
    state.expires_monotonic = time.monotonic() + 300
    reservation = _issue_configuration_reservation(owner, state)
    try:
        record = (
            owner._physical.reserve_initial_project(reservation)
            if _project
            else owner._physical.reserve_initial_configuration(reservation)
        )
    finally:
        _retire_configuration_reservation(reservation)
    if record["request"] != state.request.to_wire() or record[
        "binding"
    ] != owner._detached_binding(state.workspace_plan.binding):
        raise ValueError("initial_admission_original_return_mismatch")
    state.admission_wire = _canonical(record)
    state.work = owner._initial_configuration_work(state.workspace_plan)
    if _project:
        state.work.purpose = "initial_project"
    owner._work_by_plan[state.workspace_plan] = state.work
    state.phase = "admitted"
    return _issue_configuration_handle(
        owner,
        state,
        InitialProjectAdmission if _project else InitialConfigurationAdmission,
    )


def require_initial_configuration_work(owner, admission):
    from aware_workspace_sdk.initial_authoring.authority import (
        InitialConfigurationAdmission,
        _configuration_state,
    )

    state = _configuration_state(owner, admission, InitialConfigurationAdmission)
    if state.phase != "publishing":
        raise ValueError("initial_configuration_dispatch_not_admitted")
    return state.work


def publish_initial_configuration(owner, admission, *, _project=False):
    from dataclasses import replace

    from aware_workspace_sdk.initial_authoring.authority import (
        InitialConfigurationAdmission,
        InitialProjectAdmission,
        _configuration_state,
    )
    from aware_workspace_sdk.initial_authoring.values import _canonical

    state = _configuration_state(
        owner,
        admission,
        InitialProjectAdmission if _project else InitialConfigurationAdmission,
    )
    result = None
    try:
        context = (
            owner._physical.initial_project_attempt(state.request)
            if _project
            else owner._physical.initial_configuration_attempt(state.request)
        )
        with context as attempt:
            if _canonical(attempt.record) != state.admission_wire:
                raise ValueError("initial_admission_retained_content_changed")
            recovered = attempt.recover()
            if recovered["disposition"] == "recorded":
                result = recovered["original_result"]
                return result
            if state.phase != "admitted" or recovered["disposition"] != "pending":
                raise ValueError("initial_configuration_uncertain_no_redispatch")
            if (
                state.expires_monotonic is None
                or time.monotonic() >= state.expires_monotonic
            ):
                raise ValueError("initial_configuration_admission_expired")
            state.phase = "publishing"
            state.work.enrollment = attempt
            try:
                result = owner._execute_repository_operation(
                    state.workspace_plan,
                    admission,
                    initial_configuration=not _project,
                    initial_project=_project,
                )
                return result
            finally:
                state.phase = "spent"
    except BaseException as error:
        if result is None:
            raise
        return replace(
            result,
            ledger_complete=False,
            admission_completion="unknown",
            diagnostics=result.diagnostics
            + ("initial_attempt_terminal_fence_failed", type(error).__name__),
        )


def recover_initial_configuration(owner, protocol_plan, idempotency_key):
    from aware_workspace_sdk.initial_authoring.values import configuration_request

    owner._current()
    evidence = owner._physical.observe_initial_authoring_enrollment(_attempt=True)
    if evidence.execution_id != owner._execution:
        raise ValueError("initial_authoring_execution_mismatch")
    config = _configuration(owner, protocol_plan)
    request = configuration_request(evidence, config, idempotency_key)
    with owner._physical.initial_configuration_attempt(request) as attempt:
        result = attempt.recover()
        owner._current()
        return result


def project_initial_configuration(
    owner, protocol_plan, idempotency_key, *, read_only=False
):
    from aware_workspace_sdk.initial_authoring.values import configuration_request

    owner._current()
    evidence = owner._physical.observe_initial_authoring_enrollment(_attempt=True)
    if evidence.execution_id != owner._execution:
        raise ValueError("initial_authoring_execution_mismatch")
    config = _configuration(owner, protocol_plan)
    request = configuration_request(evidence, config, idempotency_key)
    original = None
    projected = None
    try:
        with owner._physical.initial_configuration_attempt(request) as attempt:
            recovered = attempt.recover()
            if recovered["disposition"] != "recorded":
                raise ValueError("initial_projection_original_result_required")
            original = recovered
            projected = attempt.project_configuration(read_only=read_only)
            owner._current()
    except (ValueError, OSError, RuntimeError) as error:
        if original is None:
            raise
        # Never erase a known CAS receipt when projection/terminal qualification
        # fails. This response grants neither redispatch nor Protocol admission.
        return {
            **original,
            "projection_state": "uncertain",
            "projection": None,
            "original_projection_result": projected,
            "diagnostics": (str(error),),
        }
    return {**original, "configuration_request": request.to_wire(), **projected}


@dataclass
class InitialProjectState:
    owner: Any
    workspace_plan: WorkspaceRepositoryCommitPlan
    source_plan: object
    request: Any
    frozen_wire: bytes
    frozen_binding: bytes
    phase: str = "planned"
    work: object = None
    admission_wire: bytes | None = None
    expires_monotonic: float | None = None

    def validate(self):
        from aware_workspace_sdk.initial_authoring.values import (
            InitialProjectRequest,
            _canonical,
        )

        self.owner._current()
        if (
            type(self.request) is not InitialProjectRequest
            or self.owner._snapshot_handle(self.workspace_plan).purpose
            != "initial_project"
            or _canonical(self.request.to_wire()) != self.frozen_wire
            or _canonical(self.owner._detached_binding(self.workspace_plan.binding))
            != self.frozen_binding
            or self.workspace_plan.binding.provider_ref != self.owner._provider_ref
            or self.workspace_plan.binding.provider_generation != self.owner._generation
            or self.workspace_plan.binding.execution_id != self.owner._execution
            or _canonical(
                self.owner._physical.require_initial_project_source(self.source_plan)
            )
            != _canonical(self.request.source)
        ):
            raise ValueError("initial_project_plan_mutated")


def plan_initial_project(owner, source, idempotency_key):
    from aware_workspace_sdk.initial_authoring.authority import (
        InitialProjectPlan,
        _issue_configuration_handle,
    )
    from aware_workspace_sdk.initial_authoring.values import _canonical, project_request
    from aware_workspace_sdk.repository_publication.values import (
        WorkspaceRepositoryCommitRequest,
    )

    owner._current()
    supplied = owner._physical.require_initial_project_source(source, current=True)
    request = project_request(supplied, idempotency_key)
    plan = owner._plan_repository_operation(
        WorkspaceRepositoryCommitRequest(
            supplied["repository_root"],
            (supplied["target_path"],),
            "Create initial Project context",
            request.request_ref,
        ),
        initial_project=supplied,
    )
    if plan.binding.expected_head != supplied["expected_head"]:
        raise ValueError("initial_project_source_advanced")
    state = InitialProjectState(
        owner,
        plan,
        source,
        request,
        _canonical(request.to_wire()),
        _canonical(owner._detached_binding(plan.binding)),
    )
    return _issue_configuration_handle(owner, state, InitialProjectPlan)


def require_initial_project_work(owner, admission):
    from aware_workspace_sdk.initial_authoring.authority import (
        InitialProjectAdmission,
        _configuration_state,
    )

    state = _configuration_state(owner, admission, InitialProjectAdmission)
    if state.phase != "publishing":
        raise ValueError("initial_project_dispatch_not_admitted")
    return state.work


@dataclass
class InitialProjectSourceState:
    owner: Any
    workspace: Any
    capability: object
    protocol_plan: object
    configuration_key: str
    descriptor: dict[str, Any]
    sealed: bytes
    pid: int

    def observe(self, physical, *, current=False):
        from aware_workspace_sdk.initial_authoring.values import (
            _canonical,
            project_request,
        )
        from aware_workspace_sdk.repository_publication.authority import (
            _CLIENT_PROVIDERS,
        )

        self.owner._current()
        if (
            self.pid != os.getpid()
            or _CLIENT_PROVIDERS.get(self.workspace) is not self.owner
            or self.owner._physical is not physical
            or _canonical(self.descriptor) != self.sealed
        ):
            raise ValueError("initial_project_source_not_issued_or_mutated")
        project_request(self.descriptor, "source-verification")
        physical.qualify_initial_project_source(
            self.descriptor, self.capability, current=current
        )
        if current:
            observed = project_initial_configuration(
                self.owner, self.protocol_plan, self.configuration_key, read_only=True
            )
            from aware_workspace_sdk.repository_publication.values import (
                WorkspaceRepositoryCommitResult,
            )

            result, publication, projection = (
                observed.get("original_result"),
                observed.get("publication"),
                observed.get("projection"),
            )
            if (
                type(result) is not WorkspaceRepositoryCommitResult
                or type(publication) is not dict
                or type(projection) is not dict
            ):
                raise ValueError("initial_project_source_not_current")
            if (
                observed.get("projection_state") != "installed"
                or result.commit_hash != self.descriptor["expected_head"]
                or publication["publication_ref"]
                != self.descriptor["configuration_publication_ref"]
                or projection["projection_ref"]
                != self.descriptor["configuration_projection_ref"]
                or _canonical(observed["configuration_request"])
                != _canonical(self.descriptor["configuration_request"])
            ):
                raise ValueError("initial_project_source_not_current")
        physical.qualify_initial_project_source(
            self.descriptor, self.capability, current=current
        )
        self.owner._current()
        return json.loads(self.sealed)


def prepare_initial_project_source(
    owner, workspace, descriptor, capability, protocol_plan, configuration_key
):
    from aware_workspace_sdk.initial_authoring.authority import (
        _issue_initial_project_source,
    )
    from aware_workspace_sdk.initial_authoring.values import _canonical, project_request

    request = project_request(descriptor, "source-preparation")
    if request.execution_id != owner._execution:
        raise ValueError("initial_project_source_execution_mismatch")
    state = InitialProjectSourceState(
        owner,
        workspace,
        capability,
        protocol_plan,
        configuration_key,
        json.loads(_canonical(descriptor)),
        _canonical(descriptor),
        os.getpid(),
    )
    return _issue_initial_project_source(owner, state)


def require_initial_project_source(physical, source, *, current=False):
    from aware_workspace_sdk.initial_authoring.authority import (
        _PROJECT_SOURCE_BINDINGS,
        _PROJECT_SOURCES,
        InitialProjectSource,
    )

    state = (
        _PROJECT_SOURCES.get(source) if type(source) is InitialProjectSource else None
    )
    pins = (
        _PROJECT_SOURCE_BINDINGS.get(source)
        if type(source) is InitialProjectSource
        else None
    )
    if (
        state is None
        or pins is None
        or pins[0] is not state.workspace
        or pins[1] is not state.capability
        or pins[2] is not state.protocol_plan
        or pins[3:5] != (state.configuration_key, state.pid)
        or pins[5] != state.sealed
    ):
        raise ValueError("initial_project_source_not_issued_or_mutated")
    return state.observe(physical, current=current)


def recover_initial_project(owner, request, *, project=False, read_only=False):
    from aware_workspace_sdk.initial_authoring.values import InitialProjectRequest

    owner._current()
    if type(request) is not InitialProjectRequest:
        raise ValueError("exact_initial_project_request_required")
    if request.execution_id != owner._execution:
        raise ValueError("initial_authoring_execution_mismatch")
    # Revalidation at consumption never repairs a mutated supplied object.
    request.to_wire()
    original = projected = None
    try:
        with owner._physical.initial_project_attempt(request) as attempt:
            original = attempt.recover()
            if project:
                if original["disposition"] != "recorded":
                    raise ValueError("initial_project_original_result_required")
                projected = attempt.project_project(read_only=read_only)
            owner._current()
    except (ValueError, OSError, RuntimeError) as error:
        if not project or original is None:
            raise
        return {
            **original,
            "projection_state": "uncertain",
            "projection": None,
            "original_projection_result": projected,
            "diagnostics": (str(error),),
        }
    if original is None:
        raise ValueError("initial_project_original_observation_unavailable")
    if not project:
        return original
    if projected is None:
        raise ValueError("initial_project_projection_observation_unavailable")
    return {**original, **projected}


from aware_workspace_sdk.initial_authoring.authority import _CONFIGURATION_TYPES

_CONFIGURATION_TYPES.add(InitialConfigurationState)
_CONFIGURATION_TYPES.add(InitialProjectState)
