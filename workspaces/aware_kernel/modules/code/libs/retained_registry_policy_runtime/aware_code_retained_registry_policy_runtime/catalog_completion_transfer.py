"""One-use authority completion transfer into Workspace's prepared successor.

Workspace owns the paired preparation, parent exclusion and publication record.
Code retains the exact authority completion and operation lineage, then retires
that operation under the same original guard while sealing a nominal transfer.
No catalog publication or independent consumed flag exists here.
"""

from __future__ import annotations

import inspect
import os
from collections.abc import Callable
from dataclasses import dataclass
from threading import RLock
from typing import Any
from weakref import WeakKeyDictionary, ref

from aware_code_semantic_contract_runtime.catalog_epoch_interfaces import (
    CatalogCompletionTransferExpectation,
)
from aware_code_semantic_contract_runtime.catalog_host_leg import (
    _epoch_key,
    _freeze_publication,
    _publication_key,
)
from aware_code_semantic_contract_runtime.contracts import ContractViolation


class CatalogCompletionTransfer:
    """Nominal provisional/sealed evidence; never current catalog authority."""

    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("catalog completion transfers are Code-issued")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("catalog completion transfers are sealed")

    def __reduce__(self):
        raise TypeError("catalog completion transfers are process-local")


@dataclass(frozen=True)
class _Entrance:
    receiver: object
    name: str
    descriptor: object
    method: Callable[..., Any]

    @classmethod
    def capture(cls, receiver, name):
        descriptor = inspect.getattr_static(receiver, name)
        method = getattr(receiver, name)
        if (
            not inspect.ismethod(method)
            or method.__self__ is not receiver
            or method.__func__ is not descriptor
        ):
            raise TypeError("original catalog publication entrance required")
        return cls(receiver, name, descriptor, method)

    def check(self):
        if inspect.getattr_static(self.receiver, self.name) is not self.descriptor:
            raise ContractViolation("catalog publication entrance substituted")
        current = getattr(self.receiver, self.name)
        if (
            not inspect.ismethod(current)
            or current.__self__ is not self.receiver
            or current.__func__ is not self.descriptor
        ):
            raise ContractViolation("catalog publication entrance substituted")

    def call(self, *args, **kwargs):
        self.check()
        result = self.method(*args, **kwargs)
        self.check()
        return result


@dataclass
class _RuntimeState:
    host: object
    publication_owner: object
    binding: Any
    prepared: _Entrance
    guarded: _Entrance
    committed: _Entrance
    current: _Entrance
    successor_guard: _Entrance
    catalog_reader: _Entrance
    pid: int
    lock: Any
    reservations: WeakKeyDictionary


@dataclass
class _TransferState:
    runtime: object
    binding: Any
    context: object
    context_record: Any
    execution_stage: Any
    completion: object
    completion_snapshot: object
    preparation: object
    expected: CatalogCompletionTransferExpectation
    publication: Any
    publication_key: object
    status: str
    pid: int


class AuthorityCatalogCompletionTransferRuntime:
    """Fixed Code runtime bound to one original host and Workspace owner."""

    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("completion-transfer runtimes are fixed-assembly issued")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("completion-transfer runtime is sealed")

    def prepare_catalog_completion_transfer(
        self, operation_context, completion, preparation, *, expected
    ):
        return _prepare(self, operation_context, completion, preparation, expected)

    def validate_catalog_completion_transfer(self, transfer, *, expected):
        _validate(self, transfer, expected, full=True)

    def seal_catalog_completion_transfer(self, transfer, guard, *, expected):
        _seal(self, transfer, guard, expected)

    def validate_committed_catalog_completion_transfer(self, transfer, *, expected):
        _validate_committed(self, transfer, expected)

    def discard_catalog_completion_transfer(self, transfer):
        _discard(self, transfer)


_RUNTIMES = WeakKeyDictionary()
_BY_HOST = WeakKeyDictionary()
_TRANSFERS = WeakKeyDictionary()
_LOCK = RLock()


def _runtime(runtime):
    if type(runtime) is not AuthorityCatalogCompletionTransferRuntime:
        raise TypeError("exact completion-transfer runtime required")
    state = _RUNTIMES.get(runtime)
    if state is None or state.pid != os.getpid():
        raise ContractViolation("foreign completion-transfer runtime/process")
    for entrance in (
        state.prepared, state.guarded, state.committed, state.current,
        state.successor_guard, state.catalog_reader,
    ):
        entrance.check()
    from . import direct_epoch_tracking as hooks
    from . import direct_host as hosts

    if hosts._HOSTS.get(state.host) is not state.binding.state:
        raise ContractViolation("original transfer host changed")
    if hooks._BINDINGS.get(state.host) is not state.binding:
        raise ContractViolation("original transfer epoch binding changed")
    return state


def _same_epoch(left, right):
    return _epoch_key(left).matches(_epoch_key(right))


def _check_expected(state, context_record, expected, binding):
    from . import authority_operation_context as contexts

    if type(expected) is not CatalogCompletionTransferExpectation:
        raise TypeError("exact completion-transfer expectation required")
    contexts._same_expected(expected.operation.operation, context_record.expected)
    publication = expected.publication
    frozen = _freeze_publication(publication)
    key = _publication_key(frozen)
    if (
        publication.predecessor is None
        or not _same_epoch(expected.operation.publication, binding.expected)
        or not _same_epoch(publication.predecessor, binding.expected)
        or publication.successor.invocation.invocation_identity
        is not binding.expected.invocation.invocation_identity
        or publication.successor.invocation.lifetime_epoch_identity
        is not binding.expected.invocation.lifetime_epoch_identity
        or publication.successor.invocation.process_id != os.getpid()
    ):
        raise ContractViolation("completion-transfer epoch lineage differs")
    if context_record.demand.binding is not binding:
        raise ContractViolation("completion-transfer context host differs")
    return frozen, key


def bind_catalog_completion_transfer_runtime(host):
    """Bind Code to the original Workspace epoch owner retained by fixed assembly."""

    from . import direct_epoch_tracking as hooks
    from . import epoch_participation as epochs

    binding = hooks._BINDINGS.get(host)
    if binding is None:
        raise ContractViolation("original epoch-bound Code host required")
    tracker = epochs._state(binding.participant)
    owner = tracker.epoch_validator.receiver
    if owner is not binding.tracker.epoch_validator.receiver:
        raise ContractViolation("original Workspace epoch owner differs")
    with _LOCK:
        existing = _BY_HOST.get(host)
        if existing is not None:
            runtime = existing()
            if runtime is None:
                raise ContractViolation("original transfer runtime was released")
            _runtime(runtime)
            return runtime
        runtime = object.__new__(AuthorityCatalogCompletionTransferRuntime)
        state = _RuntimeState(
            host,
            owner,
            binding,
            _Entrance.capture(owner, "validate_prepared_catalog_publication"),
            _Entrance.capture(owner, "validate_catalog_epoch_publication_guard"),
            _Entrance.capture(owner, "validate_committed_catalog_publication"),
            _Entrance.capture(owner, "validate_current_catalog_epoch"),
            _Entrance.capture(owner, "validate_committed_successor_epoch_guard"),
            _Entrance.capture(owner, "read_code_catalog_for_epoch"),
            os.getpid(),
            RLock(),
            WeakKeyDictionary(),
        )
        _RUNTIMES[runtime] = state
        _BY_HOST[host] = ref(runtime)
    _runtime(runtime)
    return runtime


def _prepare(runtime, context, completion, preparation, expected):
    from . import authority_execution as executions
    from . import authority_operation_context as contexts

    state = _runtime(runtime)
    record = contexts._CONTEXTS.get(context)
    stage = executions._PREPARED.get(context)
    if (
        record is None
        or stage is None
        or stage.context_record is not record
        or stage.status != "completed"
        or stage.completion is not completion
    ):
        raise ContractViolation("original completed authority operation required")
    if record.demand.binding is not state.binding:
        raise ContractViolation("completion-transfer predecessor is not current")
    frozen, key = _check_expected(state, record, expected, state.binding)
    if state.prepared.call(preparation, expected=frozen) is not None:
        raise ContractViolation("prepared catalog validator returned a value")
    if executions.read_authority_completion(context) is not completion:
        raise ContractViolation("original authority completion differs")
    snapshot = record.expected.runtime.snapshot_completion(completion)
    if snapshot != stage.completion_snapshot:
        raise ContractViolation("authority completion snapshot differs")
    if state.prepared.call(preparation, expected=frozen) is not None:
        raise ContractViolation("prepared catalog validator returned a value")
    with state.lock:
        if completion in state.reservations:
            raise ContractViolation("authority completion already reserved")
        transfer = object.__new__(CatalogCompletionTransfer)
        transfer_state = _TransferState(
            runtime,
            state.binding,
            context,
            record,
            stage,
            completion,
            snapshot,
            preparation,
            CatalogCompletionTransferExpectation(expected.operation, frozen),
            expected.publication,
            key,
            "provisional",
            os.getpid(),
        )
        _TRANSFERS[transfer] = transfer_state
        state.reservations[completion] = transfer
    try:
        _validate(runtime, transfer, expected, full=True)
    except BaseException:
        with state.lock:
            state.reservations.pop(completion, None)
            _TRANSFERS.pop(transfer, None)
        raise
    return transfer


def _transfer(runtime, transfer):
    state = _runtime(runtime)
    if type(transfer) is not CatalogCompletionTransfer:
        raise TypeError("exact catalog completion transfer required")
    record = _TRANSFERS.get(transfer)
    if (
        record is None
        or record.runtime is not runtime
        or record.pid != os.getpid()
        or record.status == "discarded"
    ):
        raise ContractViolation("foreign or discarded completion transfer")
    if state.reservations.get(record.completion) is not transfer:
        raise ContractViolation("completion-transfer reservation changed")
    if not record.publication_key.matches(_publication_key(record.publication)):
        raise ContractViolation("original publication expectation changed")
    return state, record


def _validate(runtime, transfer, expected, *, full):
    from . import authority_execution as executions
    from . import authority_operation_context as contexts

    state, record = _transfer(runtime, transfer)
    frozen, key = _check_expected(
        state, record.context_record, expected, record.binding
    )
    if not record.publication_key.matches(key):
        raise ContractViolation("completion-transfer expectation changed")
    if record.status == "provisional" and full:
        if state.prepared.call(record.preparation, expected=frozen) is not None:
            raise ContractViolation("prepared catalog validator returned a value")
        if (
            executions.read_authority_completion(record.context)
            is not record.completion
        ):
            raise ContractViolation("authority completion changed")
        if contexts._CONTEXTS.get(record.context) is not record.context_record:
            raise ContractViolation("authority context association changed")
        if state.prepared.call(record.preparation, expected=frozen) is not None:
            raise ContractViolation("prepared catalog validator returned a value")
    elif record.status not in ("provisional", "sealed"):
        raise ContractViolation("completion transfer unavailable")
    return state, record, frozen


def _seal(runtime, transfer, guard, expected):
    from . import authority_execution as executions
    from . import authority_operation_context as contexts
    from . import epoch_participation as epochs

    state, record, frozen = _validate(runtime, transfer, expected, full=False)
    if record.status == "sealed":
        raise ContractViolation("completion transfer seal replay")
    stage = executions._PREPARED.get(record.context)
    if (
        stage is None
        or stage is not record.execution_stage
        or stage.status != "completed"
        or stage.completion is not record.completion
        or stage.completion_snapshot != record.completion_snapshot
        or contexts._CONTEXTS.get(record.context) is not record.context_record
    ):
        raise ContractViolation("authority completion changed before seal")
    if (
        state.guarded.call(guard, preparation=record.preparation, expected=frozen)
        is not None
    ):
        raise ContractViolation("publication guard validator returned a value")
    tracker = epochs._state(record.binding.participant)
    tracker.guard(guard)
    planning_use = record.context_record.stage.record.reservation.use
    authority_use = record.context_record.use
    with tracker.lock:
        expected_uses = {planning_use, authority_use}
        if set(tracker.uses) != expected_uses:
            raise ContractViolation(
                "authority lineage is not the complete sealable use set"
            )
        for use_handle in (planning_use, authority_use):
            use = tracker.uses.get(use_handle)
            if (
                use is None
                or use.status != "running"
                or not use.epoch_key.matches(_epoch_key(frozen.predecessor))
            ):
                raise ContractViolation("authority lineage use is not sealable")
    # The authority result depends on the retained planning result. Retire the
    # child first, then its source, using only original guard/epoch validation.
    record.binding.participant._finish_epoch_use(guard, authority_use)
    record.binding.participant._finish_epoch_use(guard, planning_use)
    record.binding.participant.validate_catalog_publication_exclusion(
        guard, expected=frozen
    )
    if (
        state.guarded.call(guard, preparation=record.preparation, expected=frozen)
        is not None
    ):
        raise ContractViolation("publication guard validator returned a value")
    with state.lock:
        if record.status != "provisional":
            raise ContractViolation("completion transfer changed during seal")
        stage.status = "transferred"
        record.status = "sealed"
        record.binding.state.pending_successor = transfer


def _validate_committed(runtime, transfer, expected):
    state, record, frozen = _validate(runtime, transfer, expected, full=False)
    if record.status != "sealed":
        raise ContractViolation("sealed completion transfer required")
    if state.committed.call(record.preparation, transfer, expected=frozen) is not None:
        raise ContractViolation("committed publication validator returned a value")
    if (
        record.execution_stage.completion is not record.completion
        or record.execution_stage.completion_snapshot != record.completion_snapshot
    ):
        raise ContractViolation("committed completion evidence changed")


def _discard(runtime, transfer):
    state = _runtime(runtime)
    if type(transfer) is not CatalogCompletionTransfer:
        raise TypeError("exact catalog completion transfer required")
    record = _TRANSFERS.get(transfer)
    if record is None or record.runtime is not runtime or record.pid != os.getpid():
        raise ContractViolation("foreign completion transfer")
    with state.lock:
        if record.status == "discarded":
            return
        # A sealed reservation has already retired the exact predecessor use. It
        # remains historical evidence but cannot be restamped or executed again.
        record.status = "discarded"
        state.reservations.pop(record.completion, None)
