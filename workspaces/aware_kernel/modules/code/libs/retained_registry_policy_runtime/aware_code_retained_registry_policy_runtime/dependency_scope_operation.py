"""Original Code running-use validation, not a bootstrap or source issuer.

Private retention requires the fixed host's authenticated source-context handoff.
Supplying an expectation to this internal entrance does not authenticate its caller
or source membership. Public host wiring and both-stage migration remain separate.
"""

from __future__ import annotations

import inspect
import os
from dataclasses import dataclass
from threading import get_ident
from weakref import WeakKeyDictionary

from aware_code_semantic_contract_runtime.catalog_host_leg import _epoch_key
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.dependency_scope_interfaces import (
    RetainedDependencyScopeExpectation,
)

from . import direct_host as direct
from . import epoch_participation as epochs
from .direct_epoch_tracking import _BINDINGS


@dataclass(frozen=True)
class _UseBinding:
    record: object
    expected: tuple
    purpose: str
    thread: int


@dataclass
class _ValidatorState:
    host: object
    host_state: object
    binding: object
    operations: dict


_STATES = WeakKeyDictionary()
_IDENTITIES = (
    "parent_identity",
    "epoch_identity",
    "operation_identity",
    "repository_membership_identity",
    "closure_runtime_identity",
)
_PURPOSES = (
    "policy_calculation",
    "policy_validation",
    "source_planning",
    "authority_derivation",
    "operation_local_read_session",
)


def _context(expected):
    if type(expected) is not RetainedDependencyScopeExpectation:
        raise TypeError("exact dependency scope expectation required")
    expected.__post_init__()
    if any(getattr(expected, name) is None for name in _IDENTITIES):
        raise ContractViolation("original context identities required")
    return tuple(getattr(expected, name) for name in _IDENTITIES) + (
        expected.process_id,
        expected.consumer_scope_key,
    )


def _same(actual, retained):
    return (
        all(a is b for a, b in zip(actual[:5], retained[:5], strict=True))
        and actual[5:] == retained[5:]
    )


def _state(validator):
    if type(validator) is not OriginalDependencyScopeOperationValidator:
        raise TypeError("exact original Code use validator required")
    if (
        inspect.getattr_static(validator, "validate_dependency_scope_operation")
        is not _VALIDATE
    ):
        raise ContractViolation("original Code use validator substituted")
    state = _STATES.get(validator)
    if state is None:
        raise ContractViolation("foreign Code use validator")
    host = state.host_state
    binding = state.binding
    if (
        host.pid != os.getpid()
        or host.closed
        or direct._HOSTS.get(state.host) is not host
        or _BINDINGS.get(state.host) is not binding
        or binding.state is not host
    ):
        raise ContractViolation("original policy host/binding unavailable")
    tracker = epochs._state(binding.participant)
    if tracker is not binding.tracker:
        raise ContractViolation("original policy tracker substituted")
    tracker._origin_intact()
    current = host.expected
    if (
        any(
            a is not b
            for a, b in zip(
                (
                    current.invocation_identity,
                    current.epoch_identity,
                    current.runtime,
                    current.catalog,
                ),
                host.identities,
                strict=True,
            )
        )
        or current.process_id != host.pid
    ):
        raise ContractViolation("original host context substituted")
    if len(current.resources) != len(host.resources):
        raise ContractViolation("original host resource count changed")
    for actual, (role, resource, disposition) in zip(
        current.resources, host.resources, strict=True
    ):
        if (
            actual.role != role
            or actual.resource is not resource
            or actual.disposition != disposition
        ):
            raise ContractViolation("original host resources substituted")
    if (
        current.composition_implementation,
        current.composition_configuration,
        current.policy_implementation,
        current.policy_configuration,
    ) != host.coordinates:
        raise ContractViolation("original host coordinates substituted")
    for method in host.methods.values():
        method.check()  # Descriptor/receiver identity only, no owner invocation.
    binding.parent_binding.check()
    return state, tracker


def _running(state, tracker, operation, expected):
    if (
        type(operation) is not epochs._EpochUse
        or operation._participant is not state.binding.participant
    ):
        raise ContractViolation("original epoch use required")
    if (
        expected.operation_identity is not operation
        or expected.parent_identity is not tracker.parent
        or expected.epoch_identity is not state.binding.epoch
        or expected.process_id != os.getpid()
    ):
        raise ContractViolation("operation parent/epoch/process differs")
    with tracker.lock:
        record = tracker.uses.get(operation)
        registered = tracker.epochs.get(state.binding.expected.publication_identity)
        if (
            record is None
            or record.thread_id != get_ident()
            or record.status != "running"
            or not record.epoch_key.matches(_epoch_key(state.binding.expected))
            or registered is None
            or registered[0] is not state.binding.epoch
            or not registered[1].matches(record.epoch_key)
        ):
            raise ContractViolation("original running epoch use unavailable")
    return record


class OriginalDependencyScopeOperationValidator(direct._Opaque):
    """Original method identity only; fixed composition authenticates this instance."""

    def __init_subclass__(cls, **kwargs):
        raise TypeError("Code use validator is sealed")

    def validate_dependency_scope_operation(self, operation, *, expected):
        state, tracker = _state(self)
        context = _context(expected)
        retained = state.operations.get(operation)
        if (
            retained is None
            or retained.thread != get_ident()
            or not _same(context, retained.expected)
        ):
            raise ContractViolation("original retained operation context unavailable")
        record = _running(state, tracker, operation, expected)
        if record is not retained.record:
            raise ContractViolation("original use record substituted")
        _state(self)


_VALIDATE = (
    OriginalDependencyScopeOperationValidator.validate_dependency_scope_operation
)


def _create_dependency_scope_operation_validator(host):
    """Fixed assembly only, after original epoch binding; not caller authentication."""
    state = direct._HOSTS.get(host)
    binding = _BINDINGS.get(host)
    if state is None or binding is None or binding.state is not state:
        raise ContractViolation("original epoch-bound host required")
    result = object.__new__(OriginalDependencyScopeOperationValidator)
    _STATES[result] = _ValidatorState(host, state, binding, {})
    _state(result)
    return result


def _retain_dependency_scope_operation(validator, operation, *, expected, purpose):
    """Fixed Code entrance only, after authenticated source-context correspondence.

    No public method invokes this from caller supplied expectations. The later
    qualified host supplies context/purpose from its retained source and call site.
    """
    state, tracker = _state(validator)
    context = _context(expected)
    if type(purpose) is not str or purpose not in _PURPOSES:
        raise ContractViolation("fixed operation purpose required")
    record = _running(state, tracker, operation, expected)
    if operation in state.operations or len(state.operations) >= 4096:
        raise ContractViolation("duplicate or excessive operation binding")
    state.operations[operation] = _UseBinding(record, context, purpose, get_ident())


def _release_dependency_scope_operation(validator, operation):
    """Retire private bookkeeping even after host/use revocation; no source cleanup."""
    if type(validator) is not OriginalDependencyScopeOperationValidator:
        raise TypeError("exact original Code use validator required")
    state = _STATES.get(validator)
    if (
        state is None
        or state.host_state.pid != os.getpid()
        or operation not in state.operations
    ):
        raise ContractViolation("original operation binding unavailable")
    if state.operations[operation].thread != get_ident():
        raise ContractViolation("operation cleanup belongs to original thread")
    state.operations.pop(operation)
