"""Original source-planning context; not semantic or execution admission.

The validator must be retained by fixed application assembly. Constructing a
request grants nothing. Authority-stage runtime/completion composition is absent.
"""

import inspect
import os
from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
from dataclasses import dataclass, fields, replace
from time import perf_counter_ns, process_time_ns
from weakref import WeakKeyDictionary, ref

from aware_code_semantic_contract_runtime.contracts import (
    ContractViolation,
)
from aware_code_semantic_contract_runtime.retained_admission_interfaces import (
    RetainedSemanticAdmissionExpectation,
)

from . import direct_epoch_tracking as epoch_hooks
from . import direct_host, epoch_participation
from .operation_derivation import (
    RetainedSourcePlanningRequest,
    _bodies,
    _decode,  # noqa: F401 - preserve existing private consumers
    _derive,
)


class SourcePlanningOperationContext(direct_host._Opaque):
    def __init_subclass__(cls, **kwargs):
        raise TypeError("planning context is sealed")


@dataclass(frozen=True)
class _Record:
    host: object
    policy: object
    registration: object
    request: RetainedSourcePlanningRequest
    retained: RetainedSourcePlanningRequest
    expected: RetainedSemanticAdmissionExpectation
    reservation: object = None


_CONTEXTS: WeakKeyDictionary = WeakKeyDictionary()
_VALIDATORS: WeakKeyDictionary = WeakKeyDictionary()
_ORIGINS: WeakKeyDictionary = WeakKeyDictionary()
_PERFORMANCE_PROBE: ContextVar[object | None] = ContextVar(
    "aware_code_performance_probe", default=None
)
_PERFORMANCE_SPAN_STACK: ContextVar[tuple[dict[str, int], ...]] = ContextVar(
    "aware_code_performance_span_stack", default=()
)
_PERFORMANCE_SPAN_SEQUENCE: ContextVar[int] = ContextVar(
    "aware_code_performance_span_sequence", default=0
)
_ACTIVE_CONTEXT_VALIDATIONS: ContextVar[tuple[object, ...]] = ContextVar(
    "aware_code_active_context_validations", default=()
)


def set_performance_probe(probe):
    """Install an optional diagnostic sink for the current execution context.

    The probe receives ``record(kind=..., name=..., **fields)`` calls. It is
    observational only and is never read by authority validation.
    """

    return _PERFORMANCE_PROBE.set(probe)


def reset_performance_probe(token) -> None:
    _PERFORMANCE_PROBE.reset(token)


def _performance_record(kind: str, name: str, **fields) -> None:
    probe = _PERFORMANCE_PROBE.get()
    if probe is None:
        return
    record = getattr(probe, "record", None)
    if record is None:
        return
    try:
        record(kind=kind, name=name, **fields)
    except Exception:
        # Diagnostics must never alter authority behavior.
        return


def _performance_count(name: str, amount: int = 1) -> None:
    _performance_record("counter", name, amount=amount)


@contextmanager
def _performance_phase(name: str):
    probe = _PERFORMANCE_PROBE.get()
    if probe is None or getattr(probe, "record", None) is None:
        yield
        return
    start = perf_counter_ns()
    cpu_start = process_time_ns()
    parent_stack = _PERFORMANCE_SPAN_STACK.get()
    span_id = _PERFORMANCE_SPAN_SEQUENCE.get() + 1
    _PERFORMANCE_SPAN_SEQUENCE.set(span_id)
    frame: dict[str, int] = {
        "span_id": span_id,
        "child_wall_ns": 0,
        "child_cpu_ns": 0,
    }
    stack_token = _PERFORMANCE_SPAN_STACK.set(parent_stack + (frame,))
    _performance_record(
        "phase_start",
        name,
        span_id=span_id,
        parent_span_id=(parent_stack[-1]["span_id"] if parent_stack else None),
    )
    try:
        yield
    finally:
        elapsed_ns = perf_counter_ns() - start
        cpu_ns = process_time_ns() - cpu_start
        child_wall_ns = int(frame["child_wall_ns"])
        child_cpu_ns = int(frame["child_cpu_ns"])
        _performance_record(
            "phase_end",
            name,
            span_id=span_id,
            parent_span_id=(parent_stack[-1]["span_id"] if parent_stack else None),
            elapsed_seconds=elapsed_ns / 1_000_000_000,
            exclusive_seconds=max(0, elapsed_ns - child_wall_ns) / 1_000_000_000,
            cpu_seconds=cpu_ns / 1_000_000_000,
            exclusive_cpu_seconds=max(0, cpu_ns - child_cpu_ns) / 1_000_000_000,
        )
        if parent_stack:
            parent_stack[-1]["child_wall_ns"] = (
                int(parent_stack[-1]["child_wall_ns"]) + elapsed_ns
            )
            parent_stack[-1]["child_cpu_ns"] = (
                int(parent_stack[-1]["child_cpu_ns"]) + cpu_ns
            )
        _PERFORMANCE_SPAN_STACK.reset(stack_token)
        if not parent_stack:
            _PERFORMANCE_SPAN_SEQUENCE.set(0)


@dataclass(frozen=True)
class _PlanningReservation:
    binding: object
    use: object


def _reserve_planning_epoch(host):
    # _state checks process identity before the Code lock. Mark all attempts so
    # an exposed one-shot host cannot subsequently be relabelled epoch-bound.
    direct_host._state(host)
    with direct_host._LOCK:
        epoch_hooks._STARTED[host] = True
        binding = epoch_hooks._BINDINGS.get(host)
    if binding is None:
        return None
    with epoch_hooks._guard(binding) as guard:
        epoch_hooks._original(binding, host, guard)
        use = binding.participant._begin_epoch_use(
            guard, binding.epoch, expected=binding.expected
        )
    return _PlanningReservation(binding, use)


def _validate_planning_epoch(host, reservation, *, context=None):
    if reservation is None:
        return
    binding = reservation.binding
    epoch_participation._state(binding.participant)
    with epoch_hooks._guard(binding) as guard:
        epoch_hooks._original(binding, host, guard)
        binding.participant._register_epoch(
            guard, binding.epoch, expected=binding.expected
        )
        tracker = epoch_participation._state(binding.participant)
        with tracker.lock:
            use = tracker.uses.get(reservation.use)
            if use is None:
                raise ContractViolation("original planning reservation unavailable")
            if use.status == "running" and context is not None:
                from .planning_execution import _validate_consumed_context

                _validate_consumed_context(host, context, reservation)
            elif use.status != "pending":
                raise ContractViolation("original planning reservation unavailable")


def _abandon_unpublished_planning_epoch(reservation):
    if reservation is None:
        return
    binding = reservation.binding
    epoch_participation._state(binding.participant)
    with epoch_hooks._guard(binding) as guard:
        binding.participant._abandon_unstarted_epoch_use(guard, reservation.use)


def _equal(actual, expected):
    if type(actual) is not RetainedSemanticAdmissionExpectation:
        raise TypeError("exact planning expectation required")
    identities = {
        "runtime",
        "generation_identity",
        "operation_identity",
        "selected_provider_registration",
    }
    for field in fields(expected):
        left, right = getattr(actual, field.name), getattr(expected, field.name)
        if (left is not right) if field.name in identities else (left != right):
            raise ContractViolation("planning expectation differs")


class SourcePlanningContextValidator(direct_host._Opaque):
    """Original instance must be authenticated and retained by fixed assembly."""

    def __init_subclass__(cls, **kwargs):
        raise TypeError("planning validator is sealed")

    def validate_retained_semantic_operation_context(self, admission, *, expected):
        _performance_count("code.source_context_validation")
        if (
            inspect.getattr_static(self, "validate_retained_semantic_operation_context")
            is not _VALIDATOR_METHOD
        ):
            raise ContractViolation("original planning validator method substituted")
        host = _ORIGINS.get(self)
        if host is None or (_VALIDATORS.get(host, lambda: None)()) is not self:
            raise ContractViolation("foreign planning validator")
        if type(admission) is not SourcePlanningOperationContext:
            raise TypeError("exact planning context required")
        record = _CONTEXTS.get(admission)
        if record is None or record.host is not host:
            raise ContractViolation("foreign planning context")
        if record.expected.process_id != os.getpid():
            raise ContractViolation("planning context process changed")
        active = _ACTIVE_CONTEXT_VALIDATIONS.get()
        if admission in active:
            try:
                _performance_count("code.source_context_validation_nominal")
                # Owner validation reached back into the same Code expectation
                # while its outer derivation is active. Check nominal lineage
                # without recursive source I/O; failure poisons the outer use.
                _validate_planning_epoch(host, record.reservation, context=admission)
                if record.request != record.retained:
                    raise ContractViolation("original planning request changed")
                _equal(expected, record.expected)
                with direct_host._LOCK:
                    if _CONTEXTS.get(admission) is not record:
                        raise ContractViolation(
                            "planning context revoked during validation"
                        )
            except BaseException:
                with direct_host._LOCK:
                    _CONTEXTS.pop(admission, None)
                raise
            return
        _performance_count("code.source_context_validation_complete")
        token = _ACTIVE_CONTEXT_VALIDATIONS.set(active + (admission,))
        try:
            _validate_planning_epoch(host, record.reservation, context=admission)
            if record.request != record.retained:
                raise ContractViolation("original planning request changed")
            current = _derive(
                host,
                record.policy,
                record.registration,
                record.request,
                record.expected.operation_identity,
            )
            _equal(current, record.expected)
            _equal(expected, record.expected)
            _validate_planning_epoch(host, record.reservation, context=admission)
            with direct_host._LOCK:
                if _CONTEXTS.get(admission) is not record:
                    raise ContractViolation(
                        "planning context revoked during validation"
                    )
        except BaseException:
            # Refusal revokes the context. Its issued epoch obligation remains:
            # no completion/execution evidence permits retirement here.
            with direct_host._LOCK:
                _CONTEXTS.pop(admission, None)
            raise
        finally:
            _ACTIVE_CONTEXT_VALIDATIONS.reset(token)


_VALIDATOR_METHOD = (
    SourcePlanningContextValidator.validate_retained_semantic_operation_context
)


def source_planning_context_validator(host):
    """Return original host-bound validator; this is not bootstrap authentication."""
    direct_host._state(host)
    with direct_host._LOCK:
        validator = _VALIDATORS.get(host, lambda: None)()
        if validator is None:
            validator = object.__new__(SourcePlanningContextValidator)
            _VALIDATORS[host] = ref(validator)
            _ORIGINS[validator] = host
        if (
            inspect.getattr_static(
                validator, "validate_retained_semantic_operation_context"
            )
            is not _VALIDATOR_METHOD
        ):
            raise ContractViolation("original planning validator method substituted")
        return validator


@contextmanager
def _synchronous_validation_window(host, context):
    """Bracket one synchronous owner operation with complete validation.

    The original host and context determine the validator and expectation.
    Nested owner callbacks retain nominal lineage and epoch checks; the window
    always completes with a fresh full validation after synchronous contact.
    """

    record = _CONTEXTS.get(context)
    if record is None or record.host is not host:
        raise ContractViolation("original planning context unavailable")
    active = _ACTIVE_CONTEXT_VALIDATIONS.get()
    if context in active:
        yield
        return
    validator = source_planning_context_validator(host)
    validator.validate_retained_semantic_operation_context(
        context, expected=record.expected
    )
    token = _ACTIVE_CONTEXT_VALIDATIONS.set(active + (context,))
    try:
        yield
    finally:
        _ACTIVE_CONTEXT_VALIDATIONS.reset(token)
        validator.validate_retained_semantic_operation_context(
            context, expected=record.expected
        )


def begin_source_planning_operation(host, policy, registration, request):
    """Issue a fresh request-bound planning context, without executing the provider."""
    reservation = _reserve_planning_epoch(host)
    try:
        return _publish_source_planning_operation(
            host, policy, registration, request, reservation
        )
    except BaseException:
        # No context returned and no provider execution began through this call.
        # Only this unpublished attempt may abandon its still-pending reservation.
        _abandon_unpublished_planning_epoch(reservation)
        raise


def _publish_source_planning_operation(
    host, policy, registration, request, reservation
):
    _bodies(request)
    retained = deepcopy(request)
    expected = _derive(host, policy, registration, request, object())
    current = _derive(host, policy, registration, request, expected.operation_identity)
    _equal(current, expected)
    _validate_planning_epoch(host, reservation)
    state = direct_host._state(host)
    methods = state.methods
    methods["acquire"].check()
    guard = methods["acquire"].method(state.lifetime, expected=state.expected)
    result = None
    try:
        methods["acquire"].check()
        methods["guard"].call(guard, lifetime=state.lifetime, expected=state.expected)
        # Final exclusion checks retained identity/liveness only. Source reads
        # and semantic rederivation were completed before acquiring this guard.
        state.check(read_catalog=False)
        if request != retained:
            raise ContractViolation("planning request changed during publication")
        with direct_host._LOCK:
            if state.closed:
                raise ContractViolation("host closed during context publication")
            result = object.__new__(SourcePlanningOperationContext)
            _CONTEXTS[result] = _Record(
                host, policy, registration, request, retained, expected, reservation
            )
    finally:
        try:
            methods["release"].method(guard)
            methods["release"].check()
        except BaseException:
            if result is not None:
                with direct_host._LOCK:
                    _CONTEXTS.pop(result, None)
            raise
    return result


def source_planning_expectation(host, admission):
    """Return detached comparison values while preserving original identity handles."""
    _performance_count("code.source_context_expectation")
    record = _CONTEXTS.get(admission)
    if record is None or record.host is not host:
        raise ContractViolation("foreign planning context")
    expected = record.expected
    source_planning_context_validator(
        host
    ).validate_retained_semantic_operation_context(
        admission,
        expected=expected,
    )
    identity_fields = {
        "runtime",
        "generation_identity",
        "operation_identity",
        "selected_provider_registration",
    }
    return replace(
        expected,
        **{
            f.name: deepcopy(getattr(expected, f.name))
            for f in fields(expected)
            if f.name not in identity_fields
        },
    )
