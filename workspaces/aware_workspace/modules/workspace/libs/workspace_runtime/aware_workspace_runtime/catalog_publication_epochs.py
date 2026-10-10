"""Private record mechanics for the sole Workspace joint catalog host.

No catalog issuer, host factory, provider admission or publication entrance lives
here. The joint host must authenticate/prepare both legs and validate/seal Code's
original completion before its internal commit call. Marker-based unit tests prove
records only. This module is deliberately not a consumer Protocol implementation.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass

from aware_code_semantic_contract_runtime.catalog_epoch_interfaces import (
    CatalogPairEpochExpectation,
    CatalogPublicationExpectation,
    DirectInvocationExpectation,
)
from aware_code_semantic_contract_runtime.contracts import ContentDigest

from .command_lifetime import WorkspaceCommandLifetimeRuntime


class _Preparation:
    __slots__ = ()

    def __new__(cls):
        raise TypeError("joint owner issues preparations")

    def __reduce__(self):
        raise TypeError("preparations are process-local")


@dataclass(frozen=True, eq=False)
class _Key:
    identities: tuple[object, ...]
    values: tuple[object, ...]

    def matches(self, other: _Key) -> bool:
        return (
            len(self.identities) == len(other.identities)
            and all(a is b for a, b in zip(self.identities, other.identities))
            and self.values == other.values
        )


def _digest(value):
    if type(value) is not ContentDigest:
        raise TypeError("exact digest required")
    return ContentDigest(value.value).value


def _invocation(value):
    if (
        type(value) is not DirectInvocationExpectation
        or type(value.process_id) is not int
    ):
        raise TypeError("exact invocation comparison required")
    return _Key(
        (value.invocation_identity, value.lifetime_epoch_identity), (value.process_id,)
    )


def _epoch(value):
    if type(value) is not CatalogPairEpochExpectation:
        raise TypeError("exact epoch comparison required")
    invocation = _invocation(value.invocation)
    return _Key(
        (*invocation.identities, value.publication_identity),
        (
            *invocation.values,
            _digest(value.code_catalog_digest),
            _digest(value.membership_catalog_digest),
            _digest(value.contribution_digest),
        ),
    )


@dataclass(frozen=True, eq=False)
class _Attempt:
    identity: object
    predecessor: _Key | None
    successor: _Key
    entry_digest: str
    pair: tuple[object, object]


@dataclass(frozen=True, eq=False)
class _CommittedPublication:
    preparation: _Preparation
    attempt: _Attempt
    transfer: object | None
    previous: _CommittedPublication | None


class _CatalogPublicationRecords:
    """Owner-only bounded records; callers must already hold the original guard.

    One immutable linked record is the publication decision. Pending bookkeeping
    does not decide currentness or transfer consumption. No cleanup callbacks run.
    """

    def __init__(self, *, owner, parent, invocation):
        if type(owner) is not WorkspaceCommandLifetimeRuntime:
            raise TypeError("original Workspace command runtime required")
        owner.validate_direct_invocation_parent(parent, expected=invocation)
        self._parent_descriptor = inspect.getattr_static(
            owner, "validate_direct_invocation_parent"
        )
        self._validate_parent = owner.validate_direct_invocation_parent
        self._owner = owner
        self._parent = parent
        self._invocation = DirectInvocationExpectation(
            invocation.invocation_identity,
            invocation.lifetime_epoch_identity,
            invocation.process_id,
        )
        self._invocation_key = _invocation(invocation)
        name = "validate_catalog_epoch_exclusion"
        self._descriptor = inspect.getattr_static(owner, name)
        self._validate = getattr(owner, name)
        if (
            not inspect.ismethod(self._validate)
            or self._validate.__self__ is not owner
            or self._validate.__func__ is not self._descriptor
        ):
            raise TypeError("original bound exclusion validator required")
        self._attempts: dict[_Preparation, _Attempt] = {}
        self._discarded: set[_Preparation] = set()
        self._current: _CommittedPublication | None = None
        self._closed = False

    def _guard(self, guard):
        if self._closed:
            raise RuntimeError("epoch records closed")
        name = "validate_catalog_epoch_exclusion"
        if inspect.getattr_static(self._owner, name) is not self._descriptor:
            raise RuntimeError("original exclusion validator substituted")
        result = self._validate(guard, parent=self._parent, expected=self._invocation)
        if (
            result is not None
            or inspect.getattr_static(self._owner, name) is not self._descriptor
        ):
            raise RuntimeError("original exclusion validator differs")

    def _history(self):
        current = self._current
        while current is not None:
            yield current
            current = current.previous

    def _expected(self, expected):
        if type(expected) is not CatalogPublicationExpectation:
            raise TypeError("exact publication comparison required")
        successor = _epoch(expected.successor)
        if not _invocation(expected.successor.invocation).matches(self._invocation_key):
            raise RuntimeError("foreign invocation")
        predecessor = (
            None if expected.predecessor is None else _epoch(expected.predecessor)
        )
        return predecessor, successor, _digest(expected.entry_inputs_digest)

    def _predecessor(self, predecessor):
        current = self._current
        if predecessor is None:
            if current is not None:
                raise RuntimeError("initial publication already exists")
        elif current is None or not predecessor.matches(current.attempt.successor):
            raise RuntimeError("stale predecessor")

    def _prepare(self, guard, *, expected, pair):
        self._guard(guard)
        if len(self._attempts) >= 128:
            raise RuntimeError("preparation capacity exhausted")
        if type(pair) is not tuple or len(pair) != 2 or any(x is None for x in pair):
            raise TypeError("both original prepared legs required")
        predecessor, successor, digest = self._expected(expected)
        self._predecessor(predecessor)
        for old in self._attempts.values():
            if (
                old.identity is expected.preparation_identity
                or old.successor.identities[-1] is successor.identities[-1]
            ):
                raise RuntimeError("preparation or publication identity replay")
        preparation = object.__new__(_Preparation)
        self._attempts[preparation] = _Attempt(
            expected.preparation_identity, predecessor, successor, digest, pair
        )
        return preparation

    def _pending(self, preparation, expected):
        attempt = self._attempts.get(preparation)
        if attempt is None or preparation in self._discarded:
            raise RuntimeError("foreign or discarded preparation")
        if any(record.preparation is preparation for record in self._history()):
            raise RuntimeError("publication replay")
        predecessor, successor, digest = self._expected(expected)
        if (
            attempt.identity is not expected.preparation_identity
            or not attempt.successor.matches(successor)
            or attempt.entry_digest != digest
            or (attempt.predecessor is None) != (predecessor is None)
            or (
                predecessor is not None
                and attempt.predecessor is not None
                and not attempt.predecessor.matches(predecessor)
            )
        ):
            raise RuntimeError("prepared publication substituted")
        self._predecessor(attempt.predecessor)
        return attempt

    def _commit(self, guard, preparation, *, expected, transfer):
        """Joint host final step after real Code sealing; no authentication here."""
        self._guard(guard)
        attempt = self._pending(preparation, expected)
        if (attempt.predecessor is None) != (transfer is None):
            raise RuntimeError("initial/successor transfer shape differs")
        if transfer is not None and any(
            r.transfer is transfer for r in self._history()
        ):
            raise RuntimeError("completion transfer replay")
        record = _CommittedPublication(preparation, attempt, transfer, self._current)
        # Single linearization point: no secondary consumed/current/retired flags.
        self._current = record
        return record

    def _read_current(self, guard, *, expected):
        self._guard(guard)
        return self._current_for(expected)

    def _read_current_for_parent(self, *, expected):
        """Read only under the original parent lock; never grants publication.

        Code may already hold the command publication guard while checking catalog
        liveness. Both guards share this lock; currentness must not mint a nested
        epoch guard. Mutation methods retain their original epoch-guard requirement.
        """

        def validate():
            if (
                self._closed
                or inspect.getattr_static(
                    self._owner, "validate_direct_invocation_parent"
                )
                is not self._parent_descriptor
            ):
                raise RuntimeError("original parent unavailable")
            result = self._validate_parent(self._parent, expected=self._invocation)
            if (
                result is not None
                or inspect.getattr_static(
                    self._owner, "validate_direct_invocation_parent"
                )
                is not self._parent_descriptor
            ):
                raise RuntimeError("original parent validator differs")

        # The original validator checks process identity before entering the lock.
        validate()
        with self._owner._lock:
            validate()
            return self._current_for(expected)

    def _current_for(self, expected):
        if self._current is None or not self._current.attempt.successor.matches(
            _epoch(expected)
        ):
            raise RuntimeError("epoch not current")
        return self._current

    def _read_committed(self, guard, preparation, *, transfer):
        self._guard(guard)
        for record in self._history():
            if record.preparation is preparation and record.transfer is transfer:
                return record
        raise RuntimeError("exact committed transfer unavailable")

    def _discard(self, guard, preparation):
        self._guard(guard)
        if preparation not in self._attempts:
            raise RuntimeError("foreign preparation")
        if any(r.preparation is preparation for r in self._history()):
            raise RuntimeError("committed preparation cannot be discarded")
        self._discarded.add(preparation)

    def _close(self, guard):
        self._guard(guard)
        self._closed = True
