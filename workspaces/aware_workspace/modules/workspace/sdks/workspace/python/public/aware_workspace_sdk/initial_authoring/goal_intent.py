"""Original-provider intent permission transport; never publication admission.

Detached records are historical data. Only the live owner's retained handle
can require current intent permission. No Goal decision or filesystem logic.
"""

from __future__ import annotations

import os
import threading
from weakref import WeakKeyDictionary

from .authority import _selected_owner
from .goal_source import _state as _source_state
from .values import _canonical

_PERMISSIONS = WeakKeyDictionary()
_PINS = WeakKeyDictionary()
_STATE_TYPES = set()
_CLAIMS = WeakKeyDictionary()
_LOCK = threading.Lock()


class InitialGoalIntentPermission:
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls):
        raise TypeError("use original Workspace authorize_initial_goal_intent")

    def __copy__(self):
        raise TypeError("initial_goal_intent_permission_not_copyable")

    def __deepcopy__(self, memo):
        raise TypeError("initial_goal_intent_permission_not_copyable")

    def __reduce_ex__(self, protocol):
        raise TypeError("initial_goal_intent_permission_not_serializable")

    def to_wire(self):
        """Historical issuance only; this does not prove present permission."""
        return _state(self).observe(current=False)

    def require_current(self):
        return _state(self).observe(current=True)


class _IntentClaim:
    pass


def _state(handle):
    state = (
        _PERMISSIONS.get(handle)
        if type(handle) is InitialGoalIntentPermission
        else None
    )
    pins = _PINS.get(handle) if type(handle) is InitialGoalIntentPermission else None
    if (
        state is None
        or type(state) not in _STATE_TYPES
        or pins is None
        or state.pins() != pins
    ):
        raise ValueError("initial_goal_intent_not_issued_or_mutated")
    return state


def _issue(owner, state):
    if (
        not _selected_owner(owner)
        or type(state) not in _STATE_TYPES
        or state.owner is not owner
    ):
        raise ValueError("original_initial_goal_intent_required")
    state.observe(current=True)
    handle = object.__new__(InitialGoalIntentPermission)
    _PERMISSIONS[handle] = state
    _PINS[handle] = state.pins()
    return handle


def _claim(owner, context, payload, key, facts):
    if not _selected_owner(owner) or _source_state(context).owner is not owner:
        raise ValueError("original_initial_goal_source_required")
    claim = _IntentClaim()
    with _LOCK:
        _CLAIMS[claim] = (
            owner,
            context,
            payload,
            key,
            _canonical(facts),
            os.getpid(),
            owner._provider_ref,
            owner._generation,
        )
    return claim


def _spend_claim(physical, claim):
    with _LOCK:
        value = _CLAIMS.pop(claim, None) if type(claim) is _IntentClaim else None
    if value is None:
        raise ValueError("original_initial_goal_intent_claim_required")
    owner, context, payload, key, facts, pid, provider, generation = value
    owner._current()
    if (
        not _selected_owner(owner)
        or owner._physical is not physical
        or pid != os.getpid()
        or owner._provider_ref != provider
        or owner._generation != generation
        or _source_state(context).owner is not owner
        or _canonical(context.require_current()) != facts
    ):
        raise ValueError("initial_goal_intent_claim_binding_mismatch")
    return context, payload, key, provider, generation


def _retire_claim(claim):
    with _LOCK:
        _CLAIMS.pop(claim, None)
