"""Nominal read-only source transport, not permission or a Goal evaluator."""

from __future__ import annotations

from weakref import WeakKeyDictionary

_CONTEXTS = WeakKeyDictionary()
_PINS = WeakKeyDictionary()
_STATE_TYPES = set()


class InitialGoalSourceContext:
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls):
        raise TypeError("use original Workspace observe_initial_goal_source")

    def __copy__(self):
        raise TypeError("initial_goal_context_not_copyable")

    def __deepcopy__(self, memo):
        raise TypeError("initial_goal_context_not_copyable")

    def __reduce_ex__(self, protocol):
        raise TypeError("initial_goal_context_not_serializable")

    def to_wire(self):
        """Detached historical source facts; not a portable currentness token."""
        return _state(self).observe(current=False)

    def require_current(self):
        return _state(self).observe(current=True)


def _state(handle):
    state = _CONTEXTS.get(handle) if type(handle) is InitialGoalSourceContext else None
    pins = _PINS.get(handle) if type(handle) is InitialGoalSourceContext else None
    if (
        state is None
        or type(state) not in _STATE_TYPES
        or pins is None
        or state.pins() != pins
    ):
        raise ValueError("initial_goal_context_not_issued_or_mutated")
    return state


def _issue(owner, state):
    from .authority import _selected_owner

    if (
        type(state) not in _STATE_TYPES
        or state.owner is not owner
        or not _selected_owner(owner)
    ):
        raise ValueError("original_initial_goal_context_required")
    handle = object.__new__(InitialGoalSourceContext)
    _CONTEXTS[handle] = state
    _PINS[handle] = state.pins()
    state.observe(current=True)
    return handle
