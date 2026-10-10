"""Original Code demand validation. Construction is not bootstrap authentication."""

import inspect
import os
from copy import deepcopy
from dataclasses import fields, is_dataclass, replace
from weakref import WeakKeyDictionary, ref

from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.dependency_admission_interfaces import (
    RetainedDependencyResolutionExpectation,
)
from aware_code_semantic_contract_runtime.materialization_planning_codec import (
    decode_semantic_dependency_demand_set,
)
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    DependencyPlanningInputCodec,
)

from . import direct_epoch_tracking as hooks
from . import direct_host as hosts
from . import retained_demand_operation as demands

_IDENTITY_FIELDS = frozenset(
    (
        "runtime",
        "generation_identity",
        "operation_identity",
        "selected_provider_registration",
    )
)
_ORIGINS = WeakKeyDictionary()
_VALIDATORS = WeakKeyDictionary()


def _same_portable(actual, original):
    """Strict original shape, not caller-defined equality or a new wire codec."""
    if type(actual) is not type(original):
        return False
    if is_dataclass(original):
        return all(
            _same_portable(getattr(actual, f.name), getattr(original, f.name))
            for f in fields(original)
        )
    if type(original) is tuple:
        return len(actual) == len(original) and all(
            _same_portable(a, b) for a, b in zip(actual, original, strict=True)
        )
    if type(original) in (str, int, bool, bytes, type(None)):
        return actual == original
    raise TypeError("unsupported original portable comparison shape")


def _snapshot(record, operation):
    original = record.stage.record.expected
    source = replace(
        original,
        **{
            f.name: deepcopy(getattr(original, f.name))
            for f in fields(original)
            if f.name not in _IDENTITY_FIELDS
        },
    )
    return RetainedDependencyResolutionExpectation(
        parent_identity=record.binding.tracker.parent,
        epoch_identity=record.binding.epoch,
        demand_operation_identity=operation,
        source_planning=source,
        planning_input_coordinate=deepcopy(record.planning_input_coordinate),
        planning_input=DependencyPlanningInputCodec().decode(
            record.planning_input_bytes
        ),
        planning_context=deepcopy(record.context),
        catalog_match=deepcopy(record.match),
        catalog_match_admission=deepcopy(record.match_admission),
        demand_set=decode_semantic_dependency_demand_set(
            record.result_bytes, **record.demand_context()
        ),
    )


def _compare(actual, expected):
    if type(actual) is not RetainedDependencyResolutionExpectation:
        raise TypeError("exact dependency resolution expectation required")
    for name in ("parent_identity", "epoch_identity", "demand_operation_identity"):
        if getattr(actual, name) is not getattr(expected, name):
            raise ContractViolation("dependency operation identity differs")
    left, right = actual.source_planning, expected.source_planning
    if type(left) is not type(right):
        raise TypeError("exact source-planning expectation required")
    for f in fields(right):
        a, b = getattr(left, f.name), getattr(right, f.name)
        if (a is not b) if f.name in _IDENTITY_FIELDS else not _same_portable(a, b):
            raise ContractViolation("dependency source-planning expectation differs")
    for name in (
        "planning_input_coordinate",
        "planning_input",
        "planning_context",
        "catalog_match",
        "catalog_match_admission",
        "demand_set",
    ):
        if not _same_portable(getattr(actual, name), getattr(expected, name)):
            raise ContractViolation("dependency operation evidence differs")


def _identity(validator):
    if type(validator) is not OriginalDependencyOperationValidator:
        raise TypeError("exact original Code dependency validator required")
    state = _ORIGINS.get(validator)
    if state is None or state[1] != os.getpid():
        raise ContractViolation("foreign dependency validator/process")
    host = state[0]
    if _VALIDATORS.get(host, lambda: None)() is not validator:
        raise ContractViolation("original dependency validator unavailable")
    for name, method in _METHODS.items():
        if inspect.getattr_static(validator, name) is not method:
            raise ContractViolation("original dependency validator method substituted")
    return host


def _operation(validator, operation):
    host = _identity(validator)
    record = demands._record(operation)
    if (
        record.host is not host
        or record.pid != os.getpid()
        or record.status != "returned"
    ):
        raise ContractViolation("foreign or unreturned dependency operation")
    return record


class OriginalDependencyOperationValidator(hosts._Opaque):
    def __init_subclass__(cls, **kwargs):
        raise TypeError("dependency operation validator is sealed")

    def expectation(self, operation):
        record = _operation(self, operation)
        record.validate()
        value = _snapshot(record, operation)
        with hooks._guard(record.binding) as guard:
            _identity(self)
            record.check_locked(guard)
            _compare(value, _snapshot(record, operation))
        return value

    def validate_retained_dependency_operation(self, operation, *, expected):
        record = _operation(self, operation)
        # Reject caller substitutions before invoking source/currentness readers.
        _compare(expected, _snapshot(record, operation))
        record.validate()
        with hooks._guard(record.binding) as guard:
            _identity(self)
            record.check_locked(guard)
            _compare(expected, _snapshot(record, operation))


_METHODS = {
    name: inspect.getattr_static(OriginalDependencyOperationValidator, name)
    for name in ("expectation", "validate_retained_dependency_operation")
}


def retained_dependency_operation_validator(host):
    """Resolve one original host-bound instance; fixed composition retains it.

    This original Code factory does not authenticate its caller or the application
    bootstrap. Losing the installed instance never authorizes reconstruction.
    """
    hosts._state(host)
    with hosts._LOCK:
        existing = _VALIDATORS.get(host)
        if existing is not None:
            value = existing()
            if value is None:
                raise ContractViolation("original dependency validator was released")
            _identity(value)
            return value
        value = object.__new__(OriginalDependencyOperationValidator)
        _ORIGINS[value] = (host, os.getpid())
        _VALIDATORS[host] = ref(value)
        return value
