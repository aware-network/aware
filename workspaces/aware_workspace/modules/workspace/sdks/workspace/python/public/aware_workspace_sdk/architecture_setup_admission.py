"""Original Workspace A1 custody and fixed supplier joins; values are not permits."""

from __future__ import annotations

import os
import threading
import weakref
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from . import architecture_setup_admission_values as v
from .architecture_setup import (
    ArchitectureSetupError,
    ArchitectureSetupReceipt,
)
from .architecture_setup_admission_codec import (
    setup_value_from_payload,
    setup_value_to_json,
    setup_value_to_payload,
)


class _Original:
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls):
        raise TypeError("original_workspace_setup_owner_required")

    def __copy__(self):
        raise TypeError("workspace_setup_authority_cannot_be_copied")

    def __deepcopy__(self, memo):
        raise TypeError("workspace_setup_authority_cannot_be_copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("workspace_setup_authority_cannot_be_serialized")


class WorkspaceSetupPlan(_Original):
    __slots__ = ()


class WorkspaceSetupAdmission(_Original):
    __slots__ = ()


@dataclass
class _Client:
    runtime: weakref.ReferenceType[Any]
    physical: object
    provider_ref: str
    generation: str
    client_ref: str
    pid: int
    thread: int
    plans: list[Any]
    cleanup: object = None


@dataclass
class _Plan:
    client: _Client
    derivation: object
    sequence: object
    binding: object
    phase: str = "prepared"
    next_ordinal: int = 0
    enrollment: object = None
    consumption: object = None
    result: object = None
    cleanup: object = None
    primary: object = None


_CLIENTS = {}
_PLANS = {}
_ADMISSIONS = {}
_NONE = v.WorkspaceSetupPrimaryFailure("none", None, None, None, None, False)
_supplier_entries: tuple[Any, ...] | None = None


def _capture_suppliers():
    global _supplier_entries
    if _supplier_entries is None:
        from aware_file_system import retained_file_sequence as fs
        from aware_issue_sdk import workspace_setup_admission as issue

        _supplier_entries = tuple(
            (module, name, getattr(module, name), getattr(module, name).__code__)
            for module, names in (
                (
                    fs,
                    (
                        "retain_confined_file_sequence",
                        "observe_confined_file_sequence",
                        "verify_confined_file_sequence",
                        "execute_next_confined_file_step",
                        "release_confined_file_sequence",
                    ),
                ),
                (
                    issue,
                    (
                        "enroll_workspace_setup_admission",
                        "consume_workspace_setup_admission",
                        "verify_workspace_setup_consumption",
                    ),
                ),
            )
            for name in names
        )


def _supplier(name, *, cleanup=False):
    _capture_suppliers()
    assert _supplier_entries is not None
    module, _, method, code = next(row for row in _supplier_entries if row[1] == name)
    if method.__code__ is not code or (
        not cleanup and getattr(module, name) is not method
    ):
        raise ArchitectureSetupError("original_setup_supplier_changed")
    return method


def _register_setup_client(client, runtime):
    from aware_workspace_runtime.architecture_setup import ArchitectureSetupRuntime

    if type(runtime) is not ArchitectureSetupRuntime:
        raise ArchitectureSetupError("original_setup_runtime_required")
    _capture_suppliers()
    state = _Client(
        weakref.ref(runtime),
        runtime.physical,
        "aware.workspace.setup-a1.v1",
        "setup-generation:" + uuid4().hex,
        "setup-client:" + uuid4().hex,
        os.getpid(),
        threading.get_ident(),
        [],
    )
    _CLIENTS[id(client)] = (weakref.ref(client), state)
    weakref.finalize(client, _release_client_state, state)


def _client(client, *, cleanup=False):
    from .architecture_setup import WorkspaceSetupClient

    if type(client) is WorkspaceSetupClient:
        registered = _CLIENTS.get(id(client))
        if registered is None or registered[0]() is None:
            _register_setup_client(client, client._runtime)
    row = _CLIENTS.get(id(client)) if type(client) is WorkspaceSetupClient else None
    if row is None or row[0]() is not client:
        raise ArchitectureSetupError("original_setup_client_required")
    state = row[1]
    if (state.pid, state.thread) != (os.getpid(), threading.get_ident()):
        raise ArchitectureSetupError("setup_origin_mismatch")
    if not cleanup and (state.cleanup is not None or state.runtime() is None):
        raise ArchitectureSetupError("setup_client_retired")
    return state


def _plan(plan, *, cleanup=False):
    if type(plan) is not WorkspaceSetupPlan:
        raise ArchitectureSetupError("original_setup_plan_required")
    row = _PLANS.get(id(plan))
    if row is None or row[0]() is not plan:
        raise ArchitectureSetupError("original_setup_plan_required")
    state = row[1]
    if (state.client.pid, state.client.thread) != (os.getpid(), threading.get_ident()):
        raise ArchitectureSetupError("setup_origin_mismatch")
    if not cleanup and (state.cleanup is not None or state.client.cleanup is not None):
        raise ArchitectureSetupError("setup_plan_retired")
    return state


def _fs():
    from aware_file_system import retained_file_sequence

    return retained_file_sequence


def _project_native(value) -> Any:
    native = _fs()
    payload = native.confined_sequence_value_to_payload(value)
    names = {
        native.ConfinedSequenceFileObservation: v.WorkspaceSetupFileObservation,
        native.ConfinedSequenceDirectoryObservation: v.WorkspaceSetupDirectoryObservation,
        native.ConfinedSequenceAncestorGuard: v.WorkspaceSetupAncestorGuard,
        native.ConfinedSequenceFileBinding: v.WorkspaceSetupFileTransition,
        native.ConfinedSequenceStep: v.WorkspaceSetupPhysicalStep,
        native.ConfinedSequencePreconditions: v.WorkspaceSetupPreconditions,
        native.ConfinedSequenceResourceEvidence: v.WorkspaceSetupResourceEvidence,
        native.ConfinedSequencePhysicalEffect: v.WorkspaceSetupPhysicalEffect,
    }
    ids = {
        native._WIRE_IDS[cls]: v.SETUP_SCHEMA_IDS[target]
        for cls, target in names.items()
    }

    def convert(item):
        if type(item) is dict:
            if set(item) == {"contract", "value"}:
                return {
                    "contract": ids[item["contract"]],
                    "value": convert(item["value"]),
                }
            return {key: convert(child) for key, child in item.items()}
        if type(item) is list:
            return [convert(child) for child in item]
        return item

    return setup_value_from_payload(names[type(value)], convert(payload))


def _resources(state):
    return tuple(
        _project_native(row)
        for row in _supplier("observe_confined_file_sequence")(state.sequence).resources
    )


def _observation(state):
    return v.WorkspaceSetupPlanObservation(
        state.binding,
        state.phase,
        state.next_ordinal,
        _resources(state),
        state.primary or _NONE,
        _supplier("observe_confined_file_sequence")(state.sequence).ledger_complete,
    )


def _runtime(state):
    runtime = state.client.runtime()
    if runtime is None:
        raise ArchitectureSetupError("setup_owner_lifetime_expired")
    return runtime


def _verify(state):
    from aware_workspace_runtime.architecture_setup import _verify_setup_derivation

    if state.phase not in ("prepared", "enrolled"):
        raise ArchitectureSetupError("setup_plan_not_pre_dispatch")
    _verify_setup_derivation(_runtime(state), state.derivation)
    _supplier("verify_confined_file_sequence")(
        state.sequence,
        expected_binding=_supplier("observe_confined_file_sequence")(
            state.sequence
        ).binding,
    )


def _verify_effect_inputs(state):
    from aware_workspace_runtime.architecture_setup import _setup_derivation_state

    core = _setup_derivation_state(_runtime(state), state.derivation)
    native = _fs()
    physical = _supplier("observe_confined_file_sequence")(state.sequence)
    published = {
        effect.primary_path
        for effect in physical.effects
        if effect.kind in ("target_link", "target_replace")
        and effect.dispatch_state == "returned"
    }
    outputs = dict(core.outputs)
    for path, body in core.inputs:
        _observed, actual = native._snapshot(
            _runtime(state).physical.root, path, native._issued(state.sequence)
        )
        if actual != (outputs[path] if path in published else body):
            raise ArchitectureSetupError("setup_input_drift:" + path)


def observe_original_setup_plan(plan):
    return _observation(_plan(plan, cleanup=True))


def verify_original_setup_plan(plan, *, expected_binding):
    state = _plan(plan)
    try:
        if type(
            expected_binding
        ) is not v.WorkspaceSetupPlanBinding or setup_value_to_json(
            expected_binding
        ) != setup_value_to_json(state.binding):
            raise ArchitectureSetupError("setup_binding_mismatch")
        _verify(state)
        return _observation(state)
    except BaseException:
        state.phase = "retired"
        raise


def prepare_setup(client, request, *, expected_plan_sha256):
    from aware_file_system.confined_mutation import (
        ConfinedFileMutationRequest,
        ConfinedMutationKind,
        ConfinedMutationProfile,
    )
    from aware_workspace_runtime.architecture_setup import (
        _capture_setup_derivation,
        _release_setup_derivation,
        _verify_setup_derivation,
    )

    state = _client(client)
    runtime = state.runtime()
    state.physical._a1_record_reads = True
    native = _fs()
    derivation = None
    sequence = None
    try:
        derivation = _capture_setup_derivation(
            runtime, request, expected_plan_sha256=expected_plan_sha256
        )
        core = _verify_setup_derivation(runtime, derivation)
        if core.request is None:
            raise ArchitectureSetupError("original_setup_request_expired")
        requests = []
        from aware_workspace_runtime.architecture_setup import digest

        for path, body in core.outputs:
            before = dict(core.inputs).get(path)
            requests.append(
                ConfinedFileMutationRequest(
                    ConfinedMutationKind.CREATE
                    if before is None
                    else ConfinedMutationKind.UPDATE,
                    path,
                    before is not None,
                    digest(before),
                    body,
                    maximum_bytes=1048576,
                )
            )
        sequence = _supplier("retain_confined_file_sequence")(
            root=runtime.physical.root,
            requests=tuple(requests),
            limits=native.ConfinedSequenceLimits(**native._LIMIT_CAPS),
            confinement_profile=ConfinedMutationProfile.DESCRIPTOR_WALK_V1,
        )
        physical = _supplier("observe_confined_file_sequence")(sequence).binding
        inputs = []
        for path, body in core.inputs:
            actual, actual_body = native._snapshot(
                runtime.physical.root, path, native._issued(sequence)
            )
            if actual_body != body:
                raise ArchitectureSetupError("setup_input_drift")
            inputs.append(v.WorkspaceSetupInputBinding(path, _project_native(actual)))
        binding = v.WorkspaceSetupPlanBinding(
            state.provider_ref,
            state.generation,
            str(runtime.physical.root),
            runtime.physical.identity,
            "setup-plan:" + uuid4().hex,
            "setup-attempt:" + uuid4().hex,
            core.request.operation,
            core.request_sha256,
            core.plan_sha256,
            tuple(inputs),
            tuple(_project_native(row) for row in physical.files),
            tuple(_project_native(row) for row in physical.ancestor_guards),
            tuple(_project_native(row) for row in physical.ordered_steps),
            v.WorkspaceSetupScratchPolicy(
                "prepared_once_v1",
                "retire_without_reselection",
                "original_identity_only_no_rollback",
                1,
            ),
            v.WorkspaceSetupLimits(**v.WORKSPACE_SETUP_LIMIT_CAPS),
            physical.provider_ref,
            physical.provider_generation,
            physical.preparation_ref,
            state.pid,
            state.thread,
            "descriptor_walk_v1",
            "legacy_kernel_umask_restore_existing_v1",
        )
        setup_value_to_payload(binding)
        plan = object.__new__(WorkspaceSetupPlan)
        record = _Plan(state, derivation, sequence, binding, primary=_NONE)
        _PLANS[id(plan)] = (weakref.ref(plan), record)
        state.plans.append(record)
        weakref.finalize(plan, _release_plan_state, record)
        return plan
    except BaseException:
        if sequence is not None:
            _supplier("release_confined_file_sequence", cleanup=True)(sequence)
        if derivation is not None:
            _release_setup_derivation(runtime, derivation)
        raise


def enroll_setup_admission(client, plan, *, issue_admission):
    state = _plan(plan)
    if state.client is not _client(client):
        raise ArchitectureSetupError("setup_foreign_plan")
    try:
        _verify(state)
        enrollment = _supplier("enroll_workspace_setup_admission")(
            issue_admission, workspace_plan=plan, expected_binding=state.binding
        )
        state.enrollment = enrollment
        state.phase = "enrolled"
        admission = object.__new__(WorkspaceSetupAdmission)
        _ADMISSIONS[id(admission)] = (weakref.ref(admission), weakref.ref(plan), state)
        return admission
    except BaseException:
        state.phase = "retired"
        raise


def _result(state):
    physical = _supplier("observe_confined_file_sequence")(state.sequence)
    effects = tuple(_project_native(effect) for effect in physical.effects)
    written = []
    for effect in physical.effects:
        if (
            effect.kind in ("target_link", "target_replace")
            and effect.dispatch_state == "returned"
            and effect.primary_path not in written
        ):
            written.append(effect.primary_path)
    receipt = ArchitectureSetupReceipt(
        state.binding.operation,
        state.binding.plan_sha256,
        ("succeeded" if effects else "unchanged")
        if state.phase == "completed"
        else "uncertain",
        tuple(written),
        tuple(
            row.path
            for row in state.binding.file_transitions
            if row.path not in written
        ),
        (),
    )
    return v.WorkspaceAuthorizedSetupResult(
        state.binding,
        receipt,
        effects,
        state.binding.ordered_effects[state.next_ordinal :],
        physical.scratch_residue,
        "unknown",
        "confirmed" if state.phase == "completed" else "unknown",
        (),
        physical.ledger_complete,
        _resources(state),
        state.primary or _NONE,
    )


def apply_setup_plan(client, plan, *, admission):
    state = _plan(plan)
    row = (
        _ADMISSIONS.get(id(admission))
        if type(admission) is WorkspaceSetupAdmission
        else None
    )
    if (
        state.client is not _client(client)
        or row is None
        or row[0]() is not admission
        or row[1]() is not plan
        or row[2] is not state
    ):
        raise ArchitectureSetupError("original_setup_admission_required")
    if state.phase != "enrolled":
        raise ArchitectureSetupError("setup_admission_replay")
    try:
        _verify(state)
        with _runtime(state).physical.lease_a1():
            _verify(state)
            state.phase = "spent"
            state.consumption = _supplier("consume_workspace_setup_admission")(
                state.enrollment, expected_binding=state.binding
            )
            for step in state.binding.ordered_effects:
                _verify_effect_inputs(state)
                _supplier("verify_confined_file_sequence")(
                    state.sequence,
                    expected_binding=_supplier("observe_confined_file_sequence")(
                        state.sequence
                    ).binding,
                )
                _supplier("verify_workspace_setup_consumption")(
                    state.consumption,
                    expected_binding=state.binding,
                    next_effect_ordinal=step.ordinal,
                )
                state.next_ordinal = step.ordinal + 1
                _supplier("execute_next_confined_file_step")(
                    state.sequence, expected_ordinal=step.ordinal
                )
            _verify_effect_inputs(state)
            state.phase = "completed"
        state.result = _result(state)
        setup_value_to_payload(state.result)
        return state.result
    except BaseException as error:
        state.phase = "retired"
        state.primary = v.WorkspaceSetupPrimaryFailure(
            "observed",
            state.client.provider_ref,
            "apply",
            getattr(error, "code", "setup_apply_failed"),
            type(error).__name__,
            not isinstance(error, Exception),
        )
        state.result = _result(state)
        failure = ArchitectureSetupError("setup_apply_failed")
        failure.result = state.result
        raise failure from error


def observe_setup_result(client, result):
    state = _client(client, cleanup=True)
    for record in state.plans:
        if record.result is result:
            return setup_value_from_payload(
                type(result), setup_value_to_payload(result)
            )
    raise ArchitectureSetupError("original_setup_result_required")


def _release_plan_state(state):
    if state.cleanup is not None:
        return state.cleanup
    state.phase = "retired"
    cleanup = _supplier("release_confined_file_sequence", cleanup=True)(state.sequence)
    runtime = state.client.runtime()
    if runtime is not None:
        from aware_workspace_runtime.architecture_setup import _release_setup_derivation

        _release_setup_derivation(runtime, state.derivation)
    state.cleanup = v.WorkspaceSetupCleanup(
        state.binding,
        "retired",
        tuple(_project_native(row) for row in cleanup.resources),
        cleanup.scratch_residue,
        cleanup.release,
        cleanup.diagnostics,
        cleanup.ledger_complete,
    )
    return state.cleanup


def release_setup_plan(client, plan):
    state = _plan(plan, cleanup=True)
    if state.client is not _client(client, cleanup=True):
        raise ArchitectureSetupError("setup_foreign_plan")
    return _release_plan_state(state)


def _release_client_state(state):
    if state.cleanup is not None:
        return state.cleanup
    complete = True
    resources = []
    for plan in state.plans:
        try:
            cleanup = _release_plan_state(plan)
            resources.extend(cleanup.resources)
            complete = (
                complete and cleanup.ledger_complete and cleanup.release == "confirmed"
            )
        except BaseException:  # noqa: BLE001 - preserve independent cleanup after interruption
            complete = False
    runtime = state.runtime()
    physical = state.physical
    primary = _NONE
    if physical is not None:
        try:
            physical.release_a1_root()
            if runtime is not None:
                runtime.close()
        except BaseException as error:  # noqa: BLE001 - retain interrupted effect/cleanup evidence
            complete = False
            primary = v.WorkspaceSetupPrimaryFailure(
                "observed",
                state.provider_ref,
                "client_release",
                "setup_client_release_unknown",
                type(error).__name__,
                not isinstance(error, Exception),
            )
        resources.append(physical._a1_root_resource)
        resources.extend(physical._a1_lease_resources)
        resources.extend(physical._a1_read_resources)
        complete = complete and physical._a1_read_complete
        complete = complete and all(
            row.release_outcome == "confirmed" and row.ownership == "released"
            for row in (
                *physical._a1_lease_resources,
                physical._a1_root_resource,
            )
        )
    state.cleanup = v.WorkspaceSetupClientCleanup(
        state.provider_ref,
        state.generation,
        state.client_ref,
        tuple(resources),
        True,
        "confirmed" if complete else "unknown",
        primary,
        (),
        complete,
    )
    return state.cleanup


def observe_client_cleanup(client):
    state = _client(client, cleanup=True)
    return state.cleanup or v.WorkspaceSetupClientCleanup(
        state.provider_ref,
        state.generation,
        state.client_ref,
        (),
        False,
        "not_attempted",
        _NONE,
        (),
        True,
    )


def release_client(client):
    return _release_client_state(_client(client, cleanup=True))


def _has_setup_plans(client):
    row = _CLIENTS.get(id(client))
    return row is not None and row[0]() is client and bool(row[1].plans)
