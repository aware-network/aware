"""Qualified consumption in the existing host/policy rail, not bootstrap trust.

Fixed Workspace assembly supplies the original source at epoch binding and
installs the returned original validator before exposing this host.
"""

from contextlib import contextmanager
from copy import deepcopy
from contextvars import ContextVar
from dataclasses import dataclass
from os import getpid
from threading import get_ident
from weakref import WeakKeyDictionary

from aware_code_semantic_contract_runtime.contracts import ContractViolation

from . import direct_host as hosts
from .dependency_scope_operation import _create_dependency_scope_operation_validator
from .dependency_source_binding import (
    _bind_dependency_source,
    _capture_dependency_source,
)
from .direct_epoch_tracking import _BINDINGS, _STARTED, _guard, _policy_epoch_use
from .qualified_calculation import calculate_qualified_registry_policy


class _OperationLocalReadSession(hosts._Opaque):
    """Opaque detached-source reuse bound to one original Code operation.

    The session is an acceleration handle, not an authority value. It is issued
    only by ``operation_local_read_session`` and keeps the original source use
    active until its context closes. Consumer calls still run the original
    Workspace validator before and after each use; only the detached closure
    read is reused.
    """

    def __init_subclass__(cls, **kwargs):
        raise TypeError("operation-local read sessions are sealed")


@dataclass
class _ReadSessionRecord:
    session: object
    host: object
    admission: object
    policy_record: tuple
    state: object
    retained: object
    binding: object
    operation: object
    bound: object
    digest: object
    closure: object
    pid: int
    thread: int
    closed: bool = False


_READ_SESSIONS = WeakKeyDictionary()
_ACTIVE_READ_SESSION = ContextVar(
    "aware_code_operation_local_read_session", default=None
)


def _retain_qualified_source(host, source):
    """Called once by original epoch assembly under its guard; no source I/O."""
    state = hosts._HOSTS.get(host)
    if (
        state is None
        or not state.qualified
        or state.dependency_binding is not None
        or host in _STARTED
        or host not in _BINDINGS
    ):
        raise ContractViolation("qualified source binding unavailable or replayed")
    validator = _create_dependency_scope_operation_validator(host)
    state.dependency_binding = _capture_dependency_source(validator, source)


def _qualified_dependency_validator(host):
    """Fixed composition consumes this original instance; no validator nomination."""
    state = hosts._HOSTS.get(host)
    if state is None or not state.qualified or state.dependency_binding is None:
        raise ContractViolation("qualified source origin unavailable")
    state.dependency_binding.check()
    return state.dependency_binding.validator


def _retained(host):
    state = hosts._state(host)
    retained = state.dependency_binding
    if not state.qualified or retained is None:
        raise ContractViolation("original qualified source unavailable")
    if retained.check().host is not host:
        raise ContractViolation("foreign qualified source host")
    return state, retained


def _read_session_record(session, host, admission):
    """Authenticate the original session and its current policy lineage."""
    if type(session) is not _OperationLocalReadSession:
        raise ContractViolation("exact operation-local read session required")
    record = _READ_SESSIONS.get(session)
    if record is None or record.closed:
        raise ContractViolation("operation-local read session unavailable")
    if record.pid != getpid() or record.thread != get_ident():
        raise ContractViolation("operation-local read session process or thread changed")
    if record.host is not host or record.admission is not admission:
        raise ContractViolation("operation-local read session host or policy differs")
    current = hosts._POLICIES.get(admission)
    if current is not record.policy_record:
        raise ContractViolation("operation-local policy lineage changed")
    state, retained = _retained(host)
    if state is not record.state or retained is not record.retained:
        raise ContractViolation("operation-local source lineage changed")
    record.retained.check()
    return record


def _active_read_session(host, admission, explicit):
    active = explicit
    ambient = _ACTIVE_READ_SESSION.get()
    if active is None:
        active = ambient
    elif ambient is not active:
        raise ContractViolation("operation-local read session context differs")
    if active is None:
        return None
    return _read_session_record(active, host, admission)


@contextmanager
def operation_local_read_session(host, admission):
    """Hold one original qualified source use for one operation-local scope.

    This context manager is intentionally opt-in. A session starts with a full
    source read and closes with the same final currentness/exclusion proof used
    by ordinary policy consumers. Nested sessions and reuse outside this
    context are rejected.
    """
    from . import operation_context as contexts

    state, retained = _retained(host)
    if type(admission) is not hosts.AdmittedRegistryPolicy:
        raise TypeError("exact policy admission required")
    policy_record = hosts._POLICIES.get(admission)
    if (
        policy_record is None
        or policy_record[0] is not host
        or policy_record[1] is not retained.source
    ):
        raise ContractViolation("original qualified policy unavailable")
    if _ACTIVE_READ_SESSION.get() is not None:
        raise ContractViolation("nested operation-local read session")
    session = object.__new__(_OperationLocalReadSession)
    record = None
    token = None
    try:
        with _policy_epoch_use(host) as pair:
            if pair is None:
                raise ContractViolation("qualified host requires original epoch")
            binding, use = pair
            with _bind_dependency_source(
                retained, use, purpose="operation_local_read_session"
            ) as bound:
                with contexts._performance_phase("code.operation_local_session_start"):
                    closure = bound.read()
                if closure.closure_digest != policy_record[2]:
                    raise ContractViolation("operation-local policy digest differs")
                record = _ReadSessionRecord(
                    session,
                    host,
                    admission,
                    policy_record,
                    state,
                    retained,
                    binding,
                    use,
                    bound,
                    closure.closure_digest,
                    closure,
                    getpid(),
                    get_ident(),
                )
                _READ_SESSIONS[session] = record
                token = _ACTIVE_READ_SESSION.set(session)
                body_failed = False
                try:
                    yield session
                except BaseException:
                    body_failed = True
                    state.closed = True
                    raise
                finally:
                    if token is not None:
                        _ACTIVE_READ_SESSION.reset(token)
                    if not body_failed:
                        try:
                            with contexts._performance_phase(
                                "code.operation_local_session_close"
                            ):
                                with _final(
                                    host,
                                    state,
                                    retained,
                                    bound,
                                    binding,
                                    digest=record.digest,
                                    admission=admission,
                                    record=policy_record,
                                ):
                                    pass
                        except BaseException:
                            state.closed = True
                            raise
                    record.closed = True
                    _READ_SESSIONS.pop(session, None)
                    token = None
    except BaseException:
        state.closed = True
        if record is not None:
            record.closed = True
            _READ_SESSIONS.pop(session, None)
        if token is not None:
            try:
                _ACTIVE_READ_SESSION.reset(token)
            except (ValueError, RuntimeError):
                pass
        raise


@contextmanager
def _final(
    host, state, retained, bound, binding, *, digest, admission=None, record=None
):
    from . import operation_context as contexts

    # Full owner/catalog currentness is checked before exclusion. Under the guard,
    # Code and Workspace perform only original identity/liveness checks.
    with contexts._performance_phase("code.policy_final_prevalidation"):
        bound.validate(closure_digest=digest)
        state.check(read_catalog=False)
    with contexts._performance_phase("code.policy_final_exclusion"):
        with _guard(binding) as guard:
            bound.check_locked(closure_digest=digest, guard=guard)
            if (
                hosts._HOSTS.get(host) is not state
                or state.closed
                or state.dependency_binding is not retained
                or _BINDINGS.get(host) is not binding
                or (
                    admission is not None
                    and hosts._POLICIES.get(admission) is not record
                )
            ):
                raise ContractViolation("qualified policy lineage changed")
            if state.stage_retention is not None:
                state.stage_retention.check_identities()
            yield guard


def produce_registry_policy(host, source):
    from . import operation_context as contexts

    contexts._performance_count("code.registry_policy_production")
    result = None
    state, retained = _retained(host)
    if source is not retained.source:
        raise ContractViolation("fixed original qualified source required")
    try:
        with _policy_epoch_use(host) as pair:
            if pair is None:
                raise ContractViolation("qualified host requires original epoch")
            binding, use = pair
            with _bind_dependency_source(
                retained, use, purpose="policy_calculation"
            ) as bound:
                with contexts._performance_phase("code.policy_source_read"):
                    closure = bound.read()
                digest = closure.closure_digest
                with contexts._performance_phase("code.registry_policy_calculation"):
                    policy = calculate_qualified_registry_policy(closure, state.check())
                with (
                    _final(host, state, retained, bound, binding, digest=digest),
                    hosts._LOCK,
                ):
                    if state.closed:
                        raise ContractViolation(
                            "qualified host closed before publication"
                        )
                    result = object.__new__(hosts.AdmittedRegistryPolicy)
                    hosts._POLICIES[result] = (host, source, digest, policy)
        return result
    except BaseException:
        if result is not None:
            hosts._POLICIES.pop(result, None)
        state.closed = True
        raise


@contextmanager
def _session_policy_source(record, *, purpose):
    """Consume detached meaning through an already active read session."""
    from . import operation_context as contexts

    if not isinstance(purpose, str) or purpose not in {
        "policy_calculation",
        "policy_validation",
        "source_planning",
        "authority_derivation",
    }:
        raise ContractViolation("fixed policy source purpose required")
    with contexts._performance_phase("code.operation_local_session_record"):
        record = _read_session_record(record.session, record.host, record.admission)
    # The source validator remains per-use. Only the owner read is reused.
    with contexts._performance_phase(
        "code.operation_local_session_source_validation"
    ):
        record.bound.validate(closure_digest=record.digest)
    try:
        with contexts._performance_phase("code.operation_local_session_consumer"):
            yield record.state, record.closure, record.policy_record[3]
    except BaseException:
        record.state.closed = True
        raise
    try:
        with contexts._performance_phase(
            "code.operation_local_session_finalization"
        ):
            with _final(
                record.host,
                record.state,
                record.retained,
                record.bound,
                record.binding,
                digest=record.digest,
                admission=record.admission,
                record=record.policy_record,
            ):
                pass
    except BaseException:
        record.state.closed = True
        raise


@contextmanager
def policy_source(host, admission, *, purpose, session=None):
    """One fresh original use for policy or stage validation; no local fallback."""
    from . import operation_context as contexts

    contexts._performance_count("code.policy_source")
    active = _active_read_session(host, admission, session)
    if active is not None:
        with contexts._performance_phase("code.operation_local_session_use"):
            with _session_policy_source(active, purpose=purpose) as value:
                yield value
        return
    state, retained = _retained(host)
    if type(admission) is not hosts.AdmittedRegistryPolicy:
        raise TypeError("exact policy admission required")
    record = hosts._POLICIES.get(admission)
    if record is None or record[0] is not host or record[1] is not retained.source:
        raise ContractViolation("original qualified policy unavailable")
    _, _, digest, policy = record
    try:
        with _policy_epoch_use(host) as pair:
            if pair is None:
                raise ContractViolation("qualified host requires original epoch")
            binding, use = pair
            with _bind_dependency_source(retained, use, purpose=purpose) as bound:
                with contexts._performance_phase("code.policy_source_read"):
                    closure = bound.read(closure_digest=digest)
                if policy.declaration_scope_digest != digest:
                    raise ContractViolation("qualified policy digest changed")
                yield state, closure, policy
                with _final(
                    host,
                    state,
                    retained,
                    bound,
                    binding,
                    digest=digest,
                    admission=admission,
                    record=record,
                ):
                    pass
    except BaseException:
        state.closed = True
        raise


def validate_registry_policy(host, admission):
    with policy_source(host, admission, purpose="policy_validation") as (_, _, policy):
        return deepcopy(policy)
