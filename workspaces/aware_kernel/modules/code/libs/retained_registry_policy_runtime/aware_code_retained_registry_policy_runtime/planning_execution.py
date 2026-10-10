"""Original planning-stage adoption, not Workspace admission or completion sealing.

This prefix retains the result of the exact selected call, but never labels it an
ExecutionCompletion. Successful and uncertain stages remain publication-blocking
until the original dependency/authority/completion lineage is implemented.
"""

import inspect
import os
from dataclasses import dataclass
from typing import Any
from weakref import WeakKeyDictionary

from aware_code_semantic_contract_runtime import selected_provider as selected
from aware_code_semantic_contract_runtime.contracts import (
    ContractViolation,
    TypedEmptyCoordinate,
)
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    DeclarationTargetInventoryCodec,
    DependencyPlanningInputCodec,
    retained_projection_body,
)

from . import direct_epoch_tracking as hooks
from . import direct_host as host_runtime
from . import epoch_participation as epochs
from . import operation_context as contexts
from . import retained_input_admission as admissions


@dataclass
class _Stage:
    context: object
    record: Any
    status: str = "running"
    result: object = None
    result_body: Any = None
    source_origin: Any = None
    source_admission: Any = None
    invocation_digest: Any = None
    completion: Any = None
    completion_snapshot: Any = None


class _PlanningExecutionOrigin(host_runtime._Opaque):
    def __init_subclass__(cls, **kwargs):
        raise TypeError("planning execution origin is sealed")

    def adopt(self, context):
        if type(context) is not contexts.SourcePlanningOperationContext:
            raise TypeError("exact planning context required")
        host, registration, stages = _origin(self)
        record = contexts._CONTEXTS.get(context)
        if (
            record is None
            or record.host is not host
            or record.registration is not registration
            or record.reservation is None
        ):
            raise ContractViolation("original epoch-bound planning context required")
        binding = record.reservation.binding
        with hooks._guard(binding) as guard:
            hooks._original(binding, host, guard)
            if context in stages or contexts._CONTEXTS.get(context) is not record:
                raise ContractViolation("planning execution replay or revoked context")
            stage = _Stage(context, record, status="adopting")
            stages[context] = stage
        try:
            stage.source_origin, stage.source_admission = (
                admissions._consume_for_planning(host, context, stage)
            )
            with hooks._guard(binding) as guard:
                hooks._original(binding, host, guard)
                if contexts._CONTEXTS.get(context) is not record:
                    raise ContractViolation("planning context revoked during adoption")
                binding.participant._start_epoch_use(guard, record.reservation.use)
                stage.status = "running"
        except BaseException:
            stage.status = "rejected"
            raise
        return stage

    def validate(self, stage, closure):
        host, registration, stages = _origin(self)
        # Issuance and execution are separate calls. The selected source can
        # change between them, so every entrance needs fresh currentness before
        # provider contact. An open validation window cannot cross that gap.
        _check_stage(
            host,
            registration,
            stages,
            stage,
            validate_source=True,
        )
        request = stage.record.retained
        expected = stage.record.expected
        if type(closure) is not selected.SelectedProviderInvocationClosure:
            raise ContractViolation("exact retained planning closure required")
        closure.__post_init__()
        invocation = closure.invocation
        if (
            tuple(sorted(closure.input_bodies, key=lambda b: b.coordinate.role))
            != tuple(sorted(contexts._bodies(request), key=lambda b: b.coordinate.role))
            or invocation.profile_ref != expected.profile.profile_ref
            or invocation.profile_digest != expected.profile.digest
            or invocation.target_package != expected.package
            or type(invocation.predecessor) is not TypedEmptyCoordinate
            or closure.predecessor_body is not None
            or invocation.dependencies
        ):
            raise ContractViolation(
                "selected closure differs from original planning context"
            )

        digest = invocation.digest
        if stage.invocation_digest is not None and stage.invocation_digest != digest:
            raise ContractViolation("planning invocation changed")
        stage.invocation_digest = digest

    def complete(self, stage, result):
        host, registration, stages = _origin(self)
        _check_stage(host, registration, stages, stage)
        from .planning_completion import _prepare_completion

        lifecycle = selected._registration_state(registration).execution_lifecycle
        completion = completion_snapshot = None
        if lifecycle.terminal_mode == "runtime_completion":
            completion = result
            completion_snapshot, result = _prepare_completion(stage, completion)
        body = _planning_body(stage.record, result)
        snapshot = DependencyPlanningInputCodec().decode(body.canonical_body)
        binding = stage.record.reservation.binding
        with hooks._guard(binding) as guard:
            hooks._original(binding, host, guard)
            if stage.status != "running" or result != snapshot:
                raise ContractViolation("planning result changed before retention")
            # No retirement: this is the original selected result, not yet an
            # admitted planning/dependency/authority completion chain.
            if completion is not None:
                runtime = stage.record.expected.runtime
                if not runtime.owns_completion(completion):
                    raise ContractViolation(
                        "planning completion revoked before retention"
                    )
            if completion is not None:
                _ORIGINS[self][4][stage.context] = (
                    stage,
                    completion,
                    completion_snapshot,
                )
            stage.completion = completion
            stage.completion_snapshot = completion_snapshot
            stage.result = result
            stage.result_body = body
            stage.status = "returned"

    def fail(self, stage):
        _host, _registration, stages = _origin(self)
        if type(stage) is not _Stage or stages.get(stage.context) is not stage:
            raise ContractViolation("foreign planning execution stage")
        binding = stage.record.reservation.binding
        with hooks._guard(binding) as guard:
            if stage.status == "uncertain":
                return
            binding.participant._mark_epoch_use_uncertain(
                guard, stage.record.reservation.use
            )
            stage.status = "uncertain"


# Retention lives on the original selected registration via its lifecycle origin.
# No ambient selection, portable token decoder, or alternate provider registry.
_ORIGINS = WeakKeyDictionary()


def _origin(origin):
    if type(origin) is not _PlanningExecutionOrigin:
        raise TypeError("exact planning origin required")
    value = _ORIGINS.get(origin)
    if value is None or value[3] != os.getpid():
        raise ContractViolation("foreign planning origin/process")
    return value[:3]


def _check_stage(
    host,
    registration,
    stages,
    stage,
    *,
    status="running",
    validate_source=True,
):
    if type(stage) is not _Stage or stages.get(stage.context) is not stage:
        raise ContractViolation("foreign planning execution stage")
    record = stage.record
    if stage.status != status or contexts._CONTEXTS.get(stage.context) is not record:
        raise ContractViolation("planning stage unavailable")
    admissions._validate_consumption_identity(
        stage.source_origin, stage.source_admission, stage.context, stage
    )
    if validate_source:
        stage.source_origin.validate(stage.source_admission)
    if record.request != record.retained:
        raise ContractViolation("planning source request changed")
    # The original joined-input validator ends with fresh context derivation.
    # Keep final nominal checks here instead of deriving that same context again.
    binding = record.reservation.binding
    with hooks._guard(binding) as guard:
        hooks._original(binding, host, guard)
        admissions._validate_consumption_identity(
            stage.source_origin, stage.source_admission, stage.context, stage
        )
        if (
            stages.get(stage.context) is not stage
            or contexts._CONTEXTS.get(stage.context) is not record
            or stage.status != status
            or record.registration is not registration
        ):
            raise ContractViolation("planning stage changed during source validation")
        tracker = epochs._state(binding.participant)
        with tracker.lock:
            use = tracker.uses.get(record.reservation.use)
            if use is None or use.status != "running":
                raise ContractViolation("original running reservation unavailable")


def bind_planning_execution_origin(host, registration, *, terminal_mode="owner_value"):
    """Fixed original Code host composition; no caller-provided factory/validator."""
    state = host_runtime._state(host)
    binding = hooks._BINDINGS.get(host)
    if binding is None:
        raise ContractViolation("original epoch host required")
    registration_state = selected._registration_state(registration)
    retained = state.stage_retention
    matches = (
        [
            runtime
            for name, runtime, original in retained.stages
            if name == "source_planning" and original is registration
        ]
        if retained is not None
        else [state.expected.runtime]
    )
    if len(matches) != 1 or registration_state.runtime is not matches[0]:
        raise ContractViolation("foreign planning registration runtime")
    if terminal_mode == "runtime_completion":
        profile = matches[0].profile
        declaration = profile.providers[0]
        if (
            len(profile.steps) != 1
            or declaration.result_role.contract != DependencyPlanningInputCodec.contract
            or declaration.terminal_statuses != ("delta",)
            or not declaration.allows_typed_empty
            or declaration.predecessor_required
            or not profile.terminal_output_roles
        ):
            raise ContractViolation(
                "planning completion requires exact DELTA/output profile"
            )
    origin = object.__new__(_PlanningExecutionOrigin)
    with hooks._guard(binding) as guard:
        hooks._original(binding, host, guard)
        _ORIGINS[origin] = (host, registration, {}, os.getpid(), {})
        try:
            selected._bind_selected_execution_lifecycle(
                matches[0],
                registration,
                origin,
                terminal_mode=terminal_mode,
            )
        except BaseException:
            _ORIGINS.pop(origin, None)
            raise
    return origin


def _planning_body(record, result):
    """Check owner-derived meaning against retained input correspondence only."""
    codec = DependencyPlanningInputCodec()
    body = retained_projection_body(result)
    if body.coordinate.contract != codec.contract:
        raise ContractViolation("selected planning result contract differs")
    value = codec.decode(body.canonical_body)
    expected = record.expected
    if expected.provider_declaration.result_role.contract != codec.contract:
        raise ContractViolation(
            "selected profile does not declare planning result contract"
        )
    if (
        value.package != expected.package
        or value.source_identity_digest != expected.source_identity_digest
    ):
        raise ContractViolation("planning result package/source differs")
    inventory = DeclarationTargetInventoryCodec().decode(
        record.retained.declaration_inventory.canonical_body
    )
    entries = {(e.dependency_kind, e.dependency_ref): e for e in inventory.entries}
    for dependency in value.dependencies:
        entry = entries.get((dependency.dependency_kind, dependency.dependency_ref))
        if (
            entry is None
            or dependency.targets != entry.targets
            or dependency.target_constraints != entry.target_constraints
        ):
            raise ContractViolation(
                "planning dependency differs from retained inventory"
            )
    return body


_ORIGINAL_METHODS = {
    name: inspect.getattr_static(_PlanningExecutionOrigin, name)
    for name in ("adopt", "validate", "complete", "fail")
}


def _validate_consumed_context(host, context, reservation):
    """Authenticate running context from original adopted lineage, without I/O."""
    record = contexts._CONTEXTS.get(context)
    if (
        record is None
        or record.host is not host
        or record.reservation is not reservation
    ):
        raise ContractViolation("original consumed planning context unavailable")
    lifecycle = selected._registration_state(record.registration).execution_lifecycle
    if lifecycle is None:
        raise ContractViolation("original planning lifecycle unavailable")
    origin = lifecycle.origin
    original_host, registration, stages = _origin(origin)
    if original_host is not host or registration is not record.registration:
        raise ContractViolation("foreign planning lifecycle")
    for name, method in _ORIGINAL_METHODS.items():
        if inspect.getattr_static(origin, name) is not method:
            raise ContractViolation("original planning lifecycle substituted")
    stage = stages.get(context)
    if (
        type(stage) is not _Stage
        or stage.record is not record
        or stage.context is not context
        or stage.status not in ("running", "returned")
    ):
        raise ContractViolation("original running planning stage unavailable")
    admissions._validate_consumption_identity(
        stage.source_origin, stage.source_admission, context, stage
    )
