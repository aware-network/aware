"""Original Code tracker mechanics, not bootstrap or execution-hook qualification.

Only fixed Code assembly may install this participant and call its underscore
operation hooks. Every real positive entrance must be wired before integrated
publication can rely on it. No caller-supplied count or completion flag exists.
"""

import inspect
import os
from dataclasses import dataclass, field
from threading import RLock, get_ident
from weakref import WeakKeyDictionary, ref

from aware_code_semantic_contract_runtime.catalog_epoch_interfaces import (
    DirectInvocationExpectation,
)
from aware_code_semantic_contract_runtime.catalog_host_leg import (
    _epoch_key,
    _freeze_epoch,
    _freeze_publication,
    _publication_key,
)
from aware_code_semantic_contract_runtime.contracts import ContractViolation

from .direct_host import _capture, _Entrance, _Opaque


class _EpochUse(_Opaque):
    _participant: object

    def __init_subclass__(cls, **kwargs):
        raise TypeError("epoch use is sealed")


@dataclass
class _UseState:
    epoch_key: object
    status: str = "pending"
    thread_id: int = field(default_factory=get_ident)


@dataclass
class _State:
    parent: object
    invocation: DirectInvocationExpectation
    guard_validator: _Entrance
    epoch_validator: _Entrance
    pid: int
    lock: object = field(default_factory=RLock)
    uses: dict = field(default_factory=dict)
    epochs: dict = field(default_factory=dict)
    closed: bool = False
    origin: tuple = field(init=False)

    def __post_init__(self):
        self.origin = (
            self.invocation.invocation_identity,
            self.invocation.lifetime_epoch_identity,
            self.pid,
        )

    def _origin_intact(self):
        if (
            self.invocation.invocation_identity is not self.origin[0]
            or self.invocation.lifetime_epoch_identity is not self.origin[1]
            or type(self.invocation.process_id) is not int
            or self.invocation.process_id != self.origin[2]
        ):
            raise ContractViolation("original invocation changed")

    def guard(self, guard):
        if self.pid != os.getpid() or self.closed:
            raise ContractViolation("epoch participant unavailable")
        self._origin_intact()
        result = self.guard_validator.call(
            guard, parent=self.parent, expected=self.invocation
        )
        if result is not None:
            raise ContractViolation("original guard validator returned non-None")
        self._origin_intact()
        if self.invocation.process_id != self.pid:
            raise ContractViolation("invocation expectation changed")

    def epoch(self, epoch, expected):
        key = _epoch_key(expected)
        invocation = self.invocation
        if (
            key.identities[0] is not invocation.invocation_identity
            or key.identities[1] is not invocation.lifetime_epoch_identity
            or key.values[0] != self.pid
        ):
            raise ContractViolation("foreign epoch invocation")
        argument = _freeze_epoch(expected)
        result = self.epoch_validator.call(epoch, expected=argument)
        if result is not None or not key.matches(_epoch_key(argument)):
            raise ContractViolation("original epoch validation differs")
        return key


_STATES = WeakKeyDictionary()
_INSTALLATIONS = WeakKeyDictionary()
_INSTALL_LOCK = RLock()


def _state(participant):
    if type(participant) is not CodeEpochParticipation:
        raise TypeError("exact Code epoch participant required")
    for name, original in _HOOKS.items():
        if inspect.getattr_static(participant, name) is not original:
            raise ContractViolation("original participant entrance substituted")
    state = _STATES.get(participant)
    if state is None or state.pid != os.getpid() or state.closed:
        raise ContractViolation("foreign or closed epoch participant")
    return state


class CodeEpochParticipation(_Opaque):
    """No constructor. Original instance/method must be bound by fixed assembly."""

    def __init_subclass__(cls, **kwargs):
        raise TypeError("epoch participant is sealed")

    def _register_epoch(self, guard, epoch, *, expected):
        expected = _freeze_epoch(expected)
        state = _state(self)
        state.guard(guard)
        key = state.epoch(epoch, expected)
        state.guard(guard)
        with state.lock:
            old = state.epochs.get(key.identities[2])
            if old is not None and (old[0] is not epoch or not key.matches(old[1])):
                raise ContractViolation("epoch registration substituted")
            state.epochs[key.identities[2]] = (epoch, key, _freeze_epoch(expected))

    def _begin_epoch_use(self, guard, epoch, *, expected):
        expected = _freeze_epoch(expected)
        _state(self)
        _REGISTER(self, guard, epoch, expected=expected)
        state = _state(self)
        state.guard(guard)
        with state.lock:
            if len(state.uses) >= 4096:
                raise ContractViolation("epoch operation capacity exhausted")
            use = object.__new__(_EpochUse)
            # Retain the participant while work is outstanding. Dropping the
            # caller's handle must not make an active obligation disappear.
            use._participant = self
            state.uses[use] = _UseState(_epoch_key(expected))
            return use

    def _transition(self, guard, use, before, after):
        state = _state(self)
        state.guard(guard)
        if type(use) is not _EpochUse:
            raise TypeError("exact epoch use required")
        with state.lock:
            record = state.uses.get(use)
            if record is None or record.status not in before:
                raise ContractViolation("foreign, replayed or unresolved epoch use")
            epoch, _, expected = state.epochs[record.epoch_key.identities[2]]
        # Cross-owner validation happens with no Code-local lock held.
        state.epoch(epoch, expected)
        state.guard(guard)
        with state.lock:
            if after is None:
                state.uses.pop(use)
            else:
                record.status = after

    def _start_epoch_use(self, guard, use):
        _TRANSITION(self, guard, use, ("pending",), "running")

    def _abandon_unstarted_epoch_use(self, guard, use):
        _TRANSITION(self, guard, use, ("pending",), None)

    def _finish_epoch_use(self, guard, use):
        """Original owner only, after actual synchronous/async work has ended."""
        _TRANSITION(self, guard, use, ("running",), None)

    def _mark_epoch_use_uncertain(self, guard, use):
        _TRANSITION(self, guard, use, ("running",), "uncertain")

    def validate_catalog_publication_exclusion(self, guard, *, expected):
        if (
            inspect.getattr_static(self, "validate_catalog_publication_exclusion")
            is not _VALIDATE
        ):
            raise ContractViolation("original Code exclusion entrance substituted")
        state = _state(self)
        state.guard(guard)
        expected = _freeze_publication(expected)
        _publication_key(expected)
        successor = expected.successor.invocation
        if (
            successor.invocation_identity is not state.invocation.invocation_identity
            or successor.lifetime_epoch_identity
            is not state.invocation.lifetime_epoch_identity
            or successor.process_id != state.pid
        ):
            raise ContractViolation("foreign publication invocation")
        if expected.predecessor is not None:
            key = _epoch_key(expected.predecessor)
            with state.lock:
                registered = state.epochs.get(key.identities[2])
                if registered is None or not registered[1].matches(key):
                    raise ContractViolation("original predecessor not registered")
            state.epoch(registered[0], expected.predecessor)
        with state.lock:
            if state.uses:
                raise ContractViolation("active or unresolved epoch operation")
            if expected.predecessor is None and state.epochs:
                raise ContractViolation(
                    "initial publication cannot replace registered epochs"
                )
        state.guard(guard)

    def _close_under_exclusion(self, guard):
        """Original parent close sequence only; revocation is not quiescence."""
        state = _state(self)
        state.guard(guard)
        with state.lock:
            state.closed = True
            state.uses.clear()
            state.epochs.clear()


_VALIDATE = CodeEpochParticipation.validate_catalog_publication_exclusion
_REGISTER = CodeEpochParticipation._register_epoch
_TRANSITION = CodeEpochParticipation._transition
_HOOKS = {
    name: inspect.getattr_static(CodeEpochParticipation, name)
    for name in (
        "_register_epoch",
        "_begin_epoch_use",
        "_transition",
        "_start_epoch_use",
        "_finish_epoch_use",
        "_abandon_unstarted_epoch_use",
        "_mark_epoch_use_uncertain",
        "_close_under_exclusion",
        "validate_catalog_publication_exclusion",
    )
}


def _assemble_code_epoch_participation(
    *, owner, parent, invocation, epoch_owner, guard
):
    """Privileged fixed Code assembly, never authentication of supplied owners.

    This mechanics installer must not be exposed as command input. It cannot prove
    that real runtime/provider entrances are already connected to the tracker.
    """
    if type(invocation) is not DirectInvocationExpectation:
        raise TypeError("exact invocation expectation required")
    if type(invocation.process_id) is not int or invocation.process_id != os.getpid():
        raise ContractViolation("wrong invocation process")
    if (
        invocation.invocation_identity is None
        or invocation.lifetime_epoch_identity is None
    ):
        raise ContractViolation("original invocation identities required")
    expected = DirectInvocationExpectation(
        invocation.invocation_identity,
        invocation.lifetime_epoch_identity,
        invocation.process_id,
    )
    state = _State(
        parent,
        expected,
        _capture(owner, "validate_catalog_epoch_exclusion"),
        _capture(epoch_owner, "validate_current_catalog_epoch"),
        os.getpid(),
    )
    state.guard(guard)
    with _INSTALL_LOCK:
        if owner in _INSTALLATIONS:
            raise ContractViolation("Code participant installation replay")
        result = object.__new__(CodeEpochParticipation)
        _STATES[result] = state
        _INSTALLATIONS[owner] = ref(result)
        return result
