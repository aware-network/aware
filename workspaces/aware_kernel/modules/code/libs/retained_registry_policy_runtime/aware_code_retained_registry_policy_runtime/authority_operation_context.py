"""Nominal authority source context, not execution or predecessor admission.

Depends on the coordinated original demand/product implementation. The original
Workspace issuer consumes the retained validator; no owner imports or callbacks
are accepted here. Public expectations remain non-authorizing comparison values.
"""

import inspect
import os
from contextvars import ContextVar
from copy import deepcopy
from dataclasses import dataclass, fields, replace
from weakref import WeakKeyDictionary, ref

from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.retained_admission_interfaces import (
    RetainedSemanticAdmissionExpectation,
)
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    RegistryPackageInputCodec,
    retained_projection_body,
)

from . import dependency_admission_origin as products
from . import dependency_operation_validator as comparison
from . import direct_epoch_tracking as hooks
from . import direct_host as hosts
from . import epoch_participation as epochs
from . import operation_context as planning_contexts
from . import planning_completion
from . import retained_demand_operation as demands
from .operation_derivation import _derive_stage


class AuthorityOperationContext(hosts._Opaque):
    def __init_subclass__(cls, **kwargs):
        raise TypeError("authority context is sealed")


@dataclass(frozen=True)
class _Record:
    host: object
    validator: object
    products: object
    product_record: object
    product_reader: object
    product_coordinate: object
    product_wire: bytes
    demand: object
    demand_result: bytes
    planning_coordinate: object
    planning_wire: bytes
    stage: object
    stage_record: object
    completion: object
    completion_snapshot: object
    registration: object
    request: object
    expected: object
    use: object
    token: object
    pid: int


_CONTEXTS = WeakKeyDictionary()
_BY_SOURCE = WeakKeyDictionary()
_VALIDATORS = WeakKeyDictionary()
_ORIGINS = WeakKeyDictionary()
_ACTIVE_VALIDATIONS: ContextVar[tuple[tuple[object, bool, bool], ...]] = ContextVar(
    "aware_code_active_authority_validations", default=()
)


def _same_expected(actual, expected):
    if type(actual) is not RetainedSemanticAdmissionExpectation:
        raise TypeError("exact retained semantic expectation required")
    for field in fields(expected):
        a, b = getattr(actual, field.name), getattr(expected, field.name)
        differs = (
            (a is not b)
            if field.name in comparison._IDENTITY_FIELDS
            else not comparison._same_portable(a, b)
        )
        if differs:
            raise ContractViolation("authority expectation differs")


def _detached(expected):
    return replace(
        expected,
        **{
            f.name: deepcopy(getattr(expected, f.name))
            for f in fields(expected)
            if f.name not in comparison._IDENTITY_FIELDS
        },
    )


def _identity(record, guard):
    """Identity/liveness only, called under original epoch exclusion."""
    if record.pid != os.getpid():
        raise ContractViolation("foreign authority context process")
    host = hosts._state(record.host)
    if _validator_host(record.validator) is not record.host:
        raise ContractViolation("original authority context validator differs")
    record.product_reader.check()
    if products._product_record(record.products) is not record.product_record:
        raise ContractViolation("original authority products substituted")
    if (
        record.product_record.wire != record.product_wire
        or not comparison._same_portable(
            record.product_record.coordinate, record.product_coordinate
        )
    ):
        raise ContractViolation("retained product bytes or coordinate changed")
    origin = products._ORIGINS.get(record.product_record.origin)
    if origin is None or origin.host is not record.host:
        raise ContractViolation("foreign authority product origin")
    origin.identity()
    demand = demands._record(record.product_record.operation)
    if demand is not record.demand or demand.host is not record.host:
        raise ContractViolation("foreign authority demand")
    demand.check_locked(guard)
    stage = record.stage
    if (
        demand.stage is not stage
        or stage.record is not record.stage_record
        or planning_contexts._CONTEXTS.get(stage.context) is not record.stage_record
        or demand.status != "returned"
        or demand.result_bytes != record.demand_result
        or demand.planning_input_bytes != record.planning_wire
        or not comparison._same_portable(
            demand.planning_input_coordinate, record.planning_coordinate
        )
        or stage.result_body.canonical_body != record.planning_wire
        or not comparison._same_portable(
            stage.result_body.coordinate, record.planning_coordinate
        )
        or stage.completion is not record.completion
        or stage.completion_snapshot is not record.completion_snapshot
        or _BY_SOURCE.get(stage.context) is not record.token
        or hooks._BINDINGS.get(record.host) is not demand.binding
    ):
        raise ContractViolation("original authority lineage changed")
    planning_completion._original_retention(stage)
    if (
        record.completion is not None
        and not stage.record.expected.runtime.owns_completion(record.completion)
    ):
        raise ContractViolation("original planning completion revoked")
    if record.completion is not None:
        # Runtime publication snapshot checks admitted bytes only, without owner
        # codecs/source callbacks. Recheck it under the final exclusion guard.
        snapshot = stage.record.expected.runtime.snapshot_completion(record.completion)
        if snapshot != record.completion_snapshot:
            raise ContractViolation("original planning publication bytes changed")
    if host.stage_retention is None:
        raise ContractViolation("original authority stage unavailable")
    host.stage_retention.check_identities()
    tracker = epochs._state(demand.binding.participant)
    with tracker.lock:
        use = tracker.uses.get(record.use)
        if use is None or use.status not in ("pending", "running"):
            raise ContractViolation("original authority reservation unavailable")


def _request(stage, retained):
    runtime, registration, entry = retained.authority_stage_for(
        stage.record.registration
    )
    registry = RegistryPackageInputCodec().decode(
        stage.record.retained.registry_package.canonical_body
    )
    profile = runtime.profile
    # These are proposals until _derive_stage independently checks every field
    # against the retained declaration, original policy, catalog and registration.
    registry = replace(
        registry,
        profile_ref=profile.profile_ref,
        profile_version=profile.version,
        profile_digest=profile.digest,
        binding=entry[3],
    )
    request = replace(
        stage.record.retained, registry_package=retained_projection_body(registry)
    )
    return registration, request


def _validate(record, *, read_products=False, rederive=False):
    active = _ACTIVE_VALIDATIONS.get()
    retained = next((value for value in active if value[0] is record), None)
    if retained is not None:
        if (read_products and not retained[1]) or (rederive and not retained[2]):
            raise ContractViolation("nested authority validation escalation")
        # The outer validation owns full product/source currentness. Recursive
        # expectation checks retain exact lineage and epoch identity only.
        with hooks._guard(record.demand.binding) as guard:
            _identity(record, guard)
        return record.expected
    token = _ACTIVE_VALIDATIONS.set(active + ((record, read_products, rederive),))
    binding = record.demand.binding
    try:
        with hooks._guard(binding) as guard:
            _identity(record, guard)
        if read_products:
            with demands.dependency_resolution_validation_session(
                record.product_record.operation
            ):
                body = record.product_reader.call()
            if (
                body.canonical_body != record.product_wire
                or not comparison._same_portable(
                    body.coordinate, record.product_coordinate
                )
            ):
                raise ContractViolation("original authority product body changed")
        snapshot = planning_completion._validate_retained_completion(record.stage)
        if snapshot != record.completion_snapshot:
            raise ContractViolation("original planning completion snapshot changed")
        current = record.expected
        if rederive:
            current = _derive_stage(
                record.host,
                record.stage_record.policy,
                record.registration,
                record.request,
                record.expected.operation_identity,
                stage="authority_derivation",
            )
            _same_expected(current, record.expected)
        with hooks._guard(binding) as guard:
            _identity(record, guard)
        return current
    finally:
        _ACTIVE_VALIDATIONS.reset(token)


def begin_authority_operation(host, dependency_products):
    """Reserve one original authority context; no request, provider or validator input."""
    state = hosts._state(host)
    if state.stage_retention is None:
        raise ContractViolation("original authority stage retention required")
    product = products._product_record(dependency_products)
    origin = products._state(product.origin)
    demand = demands._record(product.operation)
    if (
        origin.host is not host
        or demand.host is not host
        or demand.status != "returned"
    ):
        raise ContractViolation("foreign authority dependency lineage")
    validator = _VALIDATORS.get(host, lambda: None)()
    if validator is None or _validator_host(validator) is not host:
        raise ContractViolation(
            "original authority validator must be retained before context admission"
        )
    stage = demand.stage
    binding = demand.binding
    token = object()
    with hooks._guard(binding) as guard:
        demand.check_locked(guard)
        if stage.context in _BY_SOURCE:
            raise ContractViolation("authority context replay")
        use = binding.participant._begin_epoch_use(
            guard, binding.epoch, expected=binding.expected
        )
        _BY_SOURCE[stage.context] = token
    result = None
    try:
        registration, request = _request(stage, state.stage_retention)
        expected = _derive_stage(
            host,
            stage.record.policy,
            registration,
            request,
            object(),
            stage="authority_derivation",
        )
        record = _Record(
            host,
            validator,
            dependency_products,
            product,
            hosts._capture(dependency_products, "read_products"),
            deepcopy(product.coordinate),
            product.wire,
            demand,
            demand.result_bytes,
            deepcopy(demand.planning_input_coordinate),
            demand.planning_input_bytes,
            stage,
            stage.record,
            stage.completion,
            stage.completion_snapshot,
            registration,
            request,
            expected,
            use,
            token,
            os.getpid(),
        )
        _validate(record, read_products=True, rederive=True)
        with hooks._guard(binding) as guard:
            _identity(record, guard)
            result = object.__new__(AuthorityOperationContext)
            _CONTEXTS[result] = record
        return result
    except BaseException:
        if result is not None:
            _CONTEXTS.pop(result, None)
        # No selected authority execution is exposed by this entrance. Only this
        # unpublished pending attempt may abandon its own epoch reservation.
        with hooks._guard(binding) as guard:
            binding.participant._abandon_unstarted_epoch_use(guard, use)
            if _BY_SOURCE.get(stage.context) is token:
                _BY_SOURCE.pop(stage.context, None)
        raise


def _validator_host(validator):
    if type(validator) is not AuthorityContextValidator:
        raise TypeError("exact original authority validator required")
    value = _ORIGINS.get(validator)
    if value is None or value[1] != os.getpid():
        raise ContractViolation("foreign authority validator/process")
    host = value[0]
    if _VALIDATORS.get(host, lambda: None)() is not validator:
        raise ContractViolation("original authority validator unavailable")
    if (
        inspect.getattr_static(
            validator, "validate_retained_semantic_operation_context"
        )
        is not _VALIDATE
    ):
        raise ContractViolation("original authority validator method substituted")
    hosts._state(host)
    return host


class AuthorityContextValidator(hosts._Opaque):
    def __init_subclass__(cls, **kwargs):
        raise TypeError("authority validator is sealed")

    def validate_retained_semantic_operation_context(self, admission, *, expected):
        host = _validator_host(self)
        if type(admission) is not AuthorityOperationContext:
            raise TypeError("exact authority context required")
        record = _CONTEXTS.get(admission)
        if record is None or record.host is not host:
            raise ContractViolation("foreign authority context")
        # Caller mismatch cannot revoke original authority or contact owners.
        _same_expected(expected, record.expected)
        try:
            _validate(record)
            with hooks._guard(record.demand.binding) as guard:
                _validator_host(self)
                _identity(record, guard)
                if _CONTEXTS.get(admission) is not record:
                    raise ContractViolation(
                        "authority context revoked during validation"
                    )
        except BaseException:
            _CONTEXTS.pop(admission, None)
            # Published use remains pending. No completion permits retirement.
            raise


_VALIDATE = AuthorityContextValidator.validate_retained_semantic_operation_context


def authority_context_validator(host):
    """Original host-bound instance; fixed composition must authenticate/retain it."""
    state = hosts._state(host)
    if state.stage_retention is None:
        raise ContractViolation("original authority stage retention required")
    with hosts._LOCK:
        existing = _VALIDATORS.get(host)
        if existing is not None:
            value = existing()
            if value is None:
                raise ContractViolation("original authority validator was released")
        else:
            value = object.__new__(AuthorityContextValidator)
            _ORIGINS[value] = (host, os.getpid())
            _VALIDATORS[host] = ref(value)
    # Original owner validation never runs while holding the Code-local lock.
    _validator_host(value)
    return value


def authority_operation_expectation(host, admission):
    """Detached comparison values, never a substitute for the original context."""
    if type(admission) is not AuthorityOperationContext:
        raise TypeError("exact authority context required")
    record = _CONTEXTS.get(admission)
    if record is None or record.host is not host:
        raise ContractViolation("foreign authority context")
    _VALIDATE(authority_context_validator(host), admission, expected=record.expected)
    return _detached(record.expected)
