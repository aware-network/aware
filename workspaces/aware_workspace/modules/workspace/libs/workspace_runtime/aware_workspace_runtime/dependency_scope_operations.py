"""Per-use source associations. Private origin installation is not bootstrap trust."""

from __future__ import annotations

import inspect
import os
from dataclasses import dataclass
from threading import get_ident

from aware_code_semantic_contract_runtime.dependency_scope_interfaces import (
    RetainedDependencyScopeExpectation,
)

from .complete_scope_observation import _performance_phase
from .dependency_scope_declarations import refuse


@dataclass(frozen=True)
class _Association:
    source_record: object
    expected: RetainedDependencyScopeExpectation
    thread: int


class _OperationOrigin:
    def __init__(self, validator, epoch):
        self.validator = validator
        self.method = validator.validate_dependency_scope_operation
        self.descriptor = inspect.getattr_static(
            validator, "validate_dependency_scope_operation"
        )
        self.epoch = epoch
        self.pid = os.getpid()
        self.active = {}
        self.retired = {}
        self.used = set()
        self.check()

    def check(self):
        if (
            self.pid != os.getpid()
            or not inspect.ismethod(self.method)
            or self.method.__self__ is not self.validator
            or self.method.__func__ is not self.descriptor
            or inspect.getattr_static(
                self.validator, "validate_dependency_scope_operation"
            )
            is not self.descriptor
        ):
            refuse("dependency_operation_validator_changed")

    def validate(self, expected):
        self.check()
        result = self.method(expected.operation_identity, expected=expected)
        self.check()
        if result is not None:
            refuse("dependency_operation_validator_result")


def _install_operation_origin(runtime, *, validator, epoch):
    """Fixed composition only; it must authenticate validator/epoch before calling.

    This private mechanics entrance grants no trust from Protocol conformance.
    There is intentionally no public factory/registration or bind-time callback.
    The current application assembly does not call it yet.
    """
    runtime._origin()
    if epoch is None:
        refuse("dependency_operation_epoch_unavailable")
    origin = _OperationOrigin(validator, epoch)
    with runtime._exclusion.mutation():
        runtime._origin()
        if runtime._operation_origin is not None:
            refuse("dependency_operation_origin_already_bound")
        runtime._operation_origin = origin


def _origin(runtime):
    runtime._origin()
    origin = runtime._operation_origin
    if type(origin) is not _OperationOrigin:
        refuse("dependency_operation_origin_unavailable")
    origin.check()
    return origin


def prepare(
    runtime, source, *, parent_identity, epoch_identity, operation_identity, process_id
):
    """Input-only source context: Code still authenticates its use and epoch.

    No Code validator, operation origin or association is required or installed.
    Fixed composition must retain this original runtime/method and source handle.
    """
    record = runtime._record(source)
    if (
        parent_identity is not runtime._exclusion._parent
        or epoch_identity is None
        or operation_identity is None
        or type(process_id) is not int
        or process_id != os.getpid()
    ):
        refuse("dependency_preparation_coordinates_mismatch")
    runtime.read_preliminary_closure(source)
    with runtime._exclusion.mutation() as guard:
        runtime._origin()
        if runtime._records.get(source) is not record:
            refuse("dependency_preparation_source_changed")
        runtime._check_constituents(record, guard)
        # Only source-owned coordinates are derived here. The supplied Code epoch
        # and use remain input proposals until Code validates its original records.
        return RetainedDependencyScopeExpectation(
            runtime._exclusion._parent,
            epoch_identity,
            operation_identity,
            os.getpid(),
            record.observation,
            runtime,
            record.consumer,
        )


def _context(runtime, record, origin, expected):
    if type(expected) is not RetainedDependencyScopeExpectation:
        raise TypeError("exact dependency scope expectation required")
    expected.__post_init__()
    if (
        expected.parent_identity is not runtime._exclusion._parent
        or expected.epoch_identity is not origin.epoch
        or expected.operation_identity is None
        or expected.process_id != os.getpid()
        or expected.repository_membership_identity is not record.observation
        or expected.closure_runtime_identity is not runtime
        or expected.consumer_scope_key != record.consumer
    ):
        refuse("dependency_operation_source_context_mismatch")
    return RetainedDependencyScopeExpectation(
        expected.parent_identity,
        expected.epoch_identity,
        expected.operation_identity,
        expected.process_id,
        expected.repository_membership_identity,
        expected.closure_runtime_identity,
        expected.consumer_scope_key,
    )


def _same(a, b):
    return all(
        getattr(a, k) is getattr(b, k)
        for k in (
            "parent_identity",
            "epoch_identity",
            "operation_identity",
            "repository_membership_identity",
            "closure_runtime_identity",
        )
    ) and (a.process_id, a.consumer_scope_key) == (b.process_id, b.consumer_scope_key)


def _association(runtime, source, expected):
    origin = _origin(runtime)
    record = runtime._record(source)
    context = _context(runtime, record, origin, expected)
    item = origin.active.get((source, context.operation_identity))
    if (
        item is None
        or item.source_record is not record
        or item.thread != get_ident()
        or not _same(context, item.expected)
    ):
        refuse("dependency_operation_association_unavailable")
    return origin, record, item


def bind(runtime, source, *, expected):
    origin = _origin(runtime)
    record = runtime._record(source)
    context = _context(runtime, record, origin, expected)
    origin.validate(context)
    runtime.read_preliminary_closure(source)
    origin.validate(context)
    key = (source, context.operation_identity)
    with runtime._exclusion.mutation() as guard:
        if _origin(runtime) is not origin or runtime._records.get(source) is not record:
            refuse("dependency_operation_source_changed")
        runtime._check_constituents(record, guard)
        if key in origin.used or len(origin.used) >= 4096:
            refuse("dependency_operation_duplicate_or_capacity")
        origin.active[key] = _Association(record, context, get_ident())
        origin.used.add(key)


def check_locked(runtime, source, *, expected, closure_digest, guard):
    # All helpers are identity/shape checks; no Code invocation or source reads.
    runtime._exclusion.check_locked(guard)
    _, record, _ = _association(runtime, source, expected)
    if closure_digest != record.digest:
        refuse("dependency_operation_digest_mismatch")
    runtime._check_constituents(record, guard)


def read(runtime, source, *, expected):
    origin, record, item = _association(runtime, source, expected)
    origin.validate(item.expected)
    result = runtime.read_preliminary_closure(source)
    origin.validate(item.expected)
    with runtime._exclusion.mutation() as guard:
        check_locked(
            runtime,
            source,
            expected=expected,
            closure_digest=result.closure_digest,
            guard=guard,
        )
        if origin.active.get((source, expected.operation_identity)) is not item:
            refuse("dependency_operation_association_changed")
    return result


def validate(runtime, source, *, expected, closure_digest=None):
    """Validate an already-read closure without rebuilding its projection.

    The validation belongs to the same single-use operation association as the
    preceding read.  It revalidates the original observation and every retained
    scope through Workspace's original validators, then performs the existing
    operation/epoch/identity checks.  It does not retain a closure beyond this
    association and never serves a different operation.
    """
    origin, record, item = _association(runtime, source, expected)
    if closure_digest is not None and closure_digest != record.digest:
        refuse("dependency_operation_digest_mismatch")
    origin.validate(item.expected)
    with _performance_phase("workspace.preliminary_closure_validation"):
        runtime.validate_preliminary_closure(source)
    origin.validate(item.expected)
    with runtime._exclusion.mutation() as guard:
        check_locked(
            runtime,
            source,
            expected=expected,
            closure_digest=record.digest,
            guard=guard,
        )
        if origin.active.get((source, expected.operation_identity)) is not item:
            refuse("dependency_operation_association_changed")


def release(runtime, source, *, expected):
    # Retirement does not invoke a validator which may already be revoked.
    origin = runtime._operation_origin
    if type(origin) is not _OperationOrigin or origin.pid != os.getpid():
        refuse("dependency_operation_origin_unavailable")
    if type(expected) is not RetainedDependencyScopeExpectation:
        raise TypeError("exact dependency scope expectation required")
    key = (source, expected.operation_identity)
    with runtime._exclusion.mutation(retiring=True):
        item = origin.active.get(key) or origin.retired.get(key)
        if (
            item is None
            or item.thread != get_ident()
            or not _same(item.expected, expected)
        ):
            refuse("dependency_operation_association_unavailable")
        origin.active.pop(key, None)
        origin.retired.pop(key, None)
        # Retain replay tombstones for this bounded origin lifetime.


def retire_source_locked(runtime, source):
    origin = runtime._operation_origin
    if origin is not None:
        for key in tuple(origin.used):
            if key[0] is source:
                item = origin.active.pop(key, None)
                if item is not None:
                    origin.retired[key] = item
