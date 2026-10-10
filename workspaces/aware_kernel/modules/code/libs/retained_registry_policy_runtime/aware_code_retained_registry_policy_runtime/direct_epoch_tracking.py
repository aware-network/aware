"""Original direct policy hooks. No application bootstrap or execution admission.

Fixed assembly binds before exposing the host. Legacy one-shot hosts retain their
existing behavior; no public operation accepts a caller-selected tracking mode.
Only synchronous source-policy work may use this envelope. Provider execution,
planning-context lifetime and completion transfer require their own original hooks.
"""

import os
from contextlib import contextmanager
from dataclasses import dataclass
from functools import wraps
from weakref import WeakKeyDictionary

from aware_code_semantic_contract_runtime.catalog_host_leg import (
    _epoch_key,
    _freeze_epoch,
)
from aware_code_semantic_contract_runtime.contracts import ContractViolation


@dataclass(frozen=True)
class _Binding:
    state: object
    participant: object
    epoch: object
    expected: object
    tracker: object
    acquire: object
    release: object
    parent_binding: object
    catalog: object


_BINDINGS = WeakKeyDictionary()
# Protected by direct_host._LOCK. No parent callback executes under that lock.
_STARTED = WeakKeyDictionary()


@dataclass(slots=True)
class _GuardRelease:
    confirmed: bool = False


@contextmanager
def _guard(binding, *, release_state=None):
    if release_state is not None and type(release_state) is not _GuardRelease:
        raise TypeError("exact Code guard release state required")
    tracker = binding.tracker
    binding.acquire.check()
    guard = binding.acquire.method(tracker.parent, expected=tracker.invocation)
    try:
        binding.acquire.check()
        tracker.guard(guard)
        yield guard
    finally:
        binding.release.method(guard)
        binding.release.check()
        if release_state is not None:
            release_state.confirmed = True


def _bind_direct_policy_epoch(
    host, participant, epoch, *, expected, guard, dependency_source=None,
    declaration_source=None,
):
    """Privileged fixed assembly, once, before any policy entrance is used.

    Reuses the original participant, parent/context correspondence and exact
    admitted catalog. This is not a constructor that authenticates its caller.
    """
    from . import direct_host as direct
    from . import epoch_participation as epochs

    tracker = epochs._state(participant)
    tracker.guard(guard)
    state = direct._HOSTS.get(host)
    if state is None or state.closed:
        raise ContractViolation("original direct host unavailable")
    if state.qualified != (dependency_source is not None):
        raise ContractViolation(
            "exact qualified source required only for qualified host"
        )
    if (state.source_rail == "declaration_v3") != (declaration_source is not None):
        raise ContractViolation("exact v3 declaration preparation required")
    owner = tracker.guard_validator.receiver
    if owner is not state.methods["lifetime"].receiver:
        raise ContractViolation("foreign epoch lifetime owner")
    parent_binding = direct._capture(
        owner, "validate_direct_invocation_context_binding"
    )
    result = parent_binding.call(
        tracker.parent,
        state.lifetime,
        invocation=tracker.invocation,
        expected=state.expected,
    )
    if result is not None:
        raise ContractViolation("original parent binding returned non-None")
    expected = _freeze_epoch(expected)
    key = tracker.epoch(epoch, expected)
    catalog_reader = direct._capture(
        tracker.epoch_validator.receiver, "read_code_catalog_for_epoch"
    )
    if (
        catalog_reader.call(epoch, expected=expected) is not state.expected.catalog
        or not key.matches(_epoch_key(expected))
        or expected.code_catalog_digest != state.catalog_digest
    ):
        raise ContractViolation("epoch catalog differs from original host catalog")
    binding = _Binding(
        state,
        participant,
        epoch,
        _freeze_epoch(expected),
        tracker,
        direct._capture(owner, "acquire_catalog_epoch_exclusion"),
        direct._capture(owner, "release_catalog_epoch_exclusion"),
        parent_binding,
        state.expected.catalog,
    )
    tracker.guard(guard)
    with direct._LOCK:
        if (
            direct._HOSTS.get(host) is not state
            or state.closed
            or host in _STARTED
            or host in _BINDINGS
        ):
            raise ContractViolation("late or replayed policy epoch binding")
    if declaration_source is not None:
        from .declaration_host import _retain_declaration_source_locked

        _retain_declaration_source_locked(host, declaration_source, guard)
    with direct._LOCK:
        if (
            direct._HOSTS.get(host) is not state
            or state.closed
            or host in _STARTED
            or host in _BINDINGS
        ):
            state.closed = True
            raise ContractViolation("late or replayed policy epoch binding")
        _BINDINGS[host] = binding
    if state.qualified:
        from .qualified_host import _retain_qualified_source

        try:
            _retain_qualified_source(host, dependency_source)
        except BaseException:
            state.closed = True
            raise


def _original(binding, host, guard):
    from . import direct_host as direct
    from . import epoch_participation as epochs

    epochs._state(binding.participant)
    binding.parent_binding.check()
    if direct._HOSTS.get(host) is not binding.state or binding.state.closed:
        raise ContractViolation("original policy host closed")
    if (
        binding.parent_binding.call(
            binding.tracker.parent,
            binding.state.lifetime,
            invocation=binding.tracker.invocation,
            expected=binding.state.expected,
        )
        is not None
    ):
        raise ContractViolation("original parent binding returned non-None")
    if binding.state.source_rail == "declaration_v3":
        from .declaration_host import _check_declaration_source_locked

        _check_declaration_source_locked(host, guard)


@contextmanager
def _policy_epoch_use(host):
    """Fixed Code entrances receive the exact running use explicitly.

    Yields None for unchanged legacy unbound hosts, otherwise (original binding,
    original use). Qualified consumers must refuse None. No ambient current-use
    lookup, new token, source admission or caller-selected tracking mode exists.
    """
    from . import direct_host as direct

    # Record even failed use: an already-exposed host cannot later acquire
    # an epoch label and restamp earlier untracked operations.
    if type(host) is not direct.DirectValidationHost:
        raise TypeError("exact direct host required")
    state = direct._HOSTS.get(host)
    if state is not None and state.pid != os.getpid():
        raise ContractViolation("direct process changed")
    with direct._LOCK:
        _STARTED[host] = True
        binding = _BINDINGS.get(host)
    if binding is None:
        yield None
        return
    with _guard(binding) as guard:
        _original(binding, host, guard)
        use = binding.participant._begin_epoch_use(
            guard, binding.epoch, expected=binding.expected
        )
        binding.participant._start_epoch_use(guard, use)
    try:
        # Reads and calculation run outside epoch exclusion. The retained
        # running obligation blocks publication for this entire interval.
        yield binding, use
    except BaseException as error:
        # Preserve both the body error and any failure to finish. An uncertain
        # use cannot be cleared by synchronous stack unwinding.
        try:
            with _guard(binding) as guard:
                binding.participant._finish_epoch_use(guard, use)
        except BaseException as cleanup_error:
            raise error from cleanup_error
        raise
    with _guard(binding) as guard:
        _original(binding, host, guard)
        binding.participant._finish_epoch_use(guard, use)


def _tracked_policy(function):
    @wraps(function)
    def invoke(host, *args, **kwargs):
        with _policy_epoch_use(host):
            return function(host, *args, **kwargs)

    return invoke


def _epoch_closed(function):
    @wraps(function)
    def close(host):
        from . import direct_host as direct

        if type(host) is not direct.DirectValidationHost:
            raise TypeError("exact direct host required")
        state = direct._HOSTS.get(host)
        if state is not None and state.pid != os.getpid():
            raise ContractViolation("direct process changed")
        with direct._LOCK:
            binding = _BINDINGS.get(host)
        from . import product_execution as products

        exclusion_released = False
        try:
            if products._selected_input_exclusion_pending(host):
                raise ContractViolation("selected input exclusion release is unconfirmed")
            if binding is None:
                products._retire_selected_input_host(host)
                result = function(host)
                exclusion_released = True
                return result
            with _guard(binding) as guard:
                # Revoke references under exclusion, dispose them afterward.
                products._retire_selected_input_host(host, binding, exclusion_pending=True)
                binding.participant._close_under_exclusion(guard)
                result = function(host)
                with direct._LOCK:
                    _BINDINGS.pop(host, None)
            exclusion_released = True
            return result
        finally:
            # A failed acquisition/release grants no assurance that exclusion
            # ended. Revoke Code reads independently, defer reference disposal
            # to the fixed composition's confirmed-outside-exclusion cleanup.
            products._retire_selected_input_host(
                host, exclusion_pending=not exclusion_released)
            if exclusion_released:
                products._dispose_retired_selected_inputs(host)

    return close
