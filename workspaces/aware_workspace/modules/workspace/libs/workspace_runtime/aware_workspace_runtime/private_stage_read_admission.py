"""Private original-node read lifecycle; unavailable V5 authority refuses.

This cut installs no approval issuer or claim-construction entrance. Its
original factory methods can be retained by Code, but cannot succeed until
the protected V5 reader and owner-produced input association are installed.
No caller callback, detached claim or V4 observation can open that gate.
"""

from __future__ import annotations

import inspect
import os
from dataclasses import dataclass, field
from threading import current_thread
from weakref import WeakKeyDictionary, ref


@dataclass(slots=True)
class _InputFamily:
    semantic_input: object | None
    terminal: bool = False


@dataclass(slots=True)
class _RuntimeState:
    factory: ref
    process_id: int
    thread: object
    full_descriptor: object
    locked_descriptor: object
    families: WeakKeyDictionary = field(default_factory=WeakKeyDictionary)
    live: bool = True


_RUNTIMES: WeakKeyDictionary = WeakKeyDictionary()


def _registered_family(state, operation_use):
    # A registered use may have changed class. Never hash, compare or inspect
    # the caller to find the original family, including during terminal cleanup.
    for retained_use, family in state.families.items():
        if retained_use is operation_use:
            return family
    return None


class _WorkspacePrivateStageReadRuntime:
    """Process-local state created only by the fixed Workspace factory."""

    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("fixed Workspace private-read assembly required")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("Workspace private-read runtime is final")

    def __reduce_ex__(self, protocol):
        raise TypeError("Workspace private-read runtime is process-local")

    def _state(self):
        from .direct_command_composition import (
            _ORIGIN_FACTORIES,
            _DirectWorkspaceOriginFactory,
        )

        if type(self) is not _WorkspacePrivateStageReadRuntime:
            raise TypeError("original Workspace private-read runtime required")
        state = _RUNTIMES.get(self)
        if state is None or not state.live:
            raise RuntimeError("Workspace private-read runtime retired")
        factory = state.factory()
        if (
            type(factory) is not _DirectWorkspaceOriginFactory
            or factory not in _ORIGIN_FACTORIES
            or inspect.getattr_static(factory, "_private_reads", None) is not self
            or state.process_id != os.getpid()
            or state.thread is not current_thread()
            or inspect.getattr_static(factory, "validate_selected_graph_node_use")
            is not state.full_descriptor
            or inspect.getattr_static(factory, "check_selected_graph_node_use_locked")
            is not state.locked_descriptor
        ):
            self.close()
            raise RuntimeError("Workspace private-read origin changed")
        return state, factory

    def _family(self, operation_use, semantic_input, *, create=True):
        from .direct_command_composition import _CommandOwnedGraphNodeSourceSession

        state, factory = self._state()
        family = _registered_family(state, operation_use)
        if type(operation_use) is not _CommandOwnedGraphNodeSourceSession:
            if family is not None:
                self._retire_local(operation_use)
            raise TypeError("original command-owned private-stage use required")
        if family is not None and family.terminal:
            raise RuntimeError("Workspace private-read family terminal")
        try:
            factory._selected_graph_node_record(operation_use)
        except BaseException:
            if family is not None:
                self._retire_local(operation_use)
            raise
        if family is None:
            if not create:
                operation_use.close()
                raise RuntimeError("workspace_private_stage_read_preparation_unavailable")
            family = _InputFamily(semantic_input)
            state.families[operation_use] = family
        elif family.semantic_input is not semantic_input:
            self._retire_local(operation_use)
            raise RuntimeError("Workspace private-stage input substituted")
        return state, factory, family

    def validate(self, operation_use, semantic_input) -> None:
        """Revalidate original source outside exclusion; absent approval refuses."""
        _, factory, _ = self._family(operation_use, semantic_input)
        try:
            if factory._owner._guard is not None:
                raise RuntimeError("private-read full validation requires released guard")
            factory.validate_selected_graph_node_use(operation_use)
            # No original V5 approval or admitted private-input association is
            # installed. Source liveness alone must never authorize this input.
            raise RuntimeError("workspace_private_stage_v5_approval_unavailable")
        except BaseException:
            self.abort(operation_use)
            raise

    def prepare(self, operation_use, semantic_input) -> None:
        """No claim or approval is synthesized by preparation."""
        self.validate(operation_use, semantic_input)

    def check_locked(self, operation_use, semantic_input, guard) -> None:
        """Original in-place node/guard checks; no source or store traversal."""
        _, factory, _ = self._family(operation_use, semantic_input, create=False)
        try:
            factory._command.sources.exclusion.check_locked(guard)
            factory.check_selected_graph_node_use_locked(operation_use)
            raise RuntimeError("workspace_private_stage_v5_approval_unavailable")
        except BaseException:
            self._retire_local(operation_use)
            raise

    def spend_locked(self, operation_use, semantic_input, guard) -> None:
        """An absent original prepared approval cannot be spent."""
        self.check_locked(operation_use, semantic_input, guard)

    def _retire_local(self, operation_use) -> None:
        """Only local state changes; safe inside exclusion, no owner routing."""
        from .direct_command_composition import (
            _CommandOwnedGraphNodeSourceSession,
            _retire_command_node_session_by_identity,
        )

        state = _RUNTIMES.get(self)
        if state is None:
            raise RuntimeError("original Workspace private-read runtime required")
        family = _registered_family(state, operation_use)
        if family is not None:
            # Release the input before owner cleanup, even if cleanup fails.
            family.terminal = True
            family.semantic_input = None
            _retire_command_node_session_by_identity(operation_use)
        elif type(operation_use) is not _CommandOwnedGraphNodeSourceSession:
            raise TypeError("original command-owned private-stage use required")

    def abort(self, operation_use) -> None:
        """Original owner-cleanup entrance, called outside parent exclusion."""
        self._retire_local(operation_use)
        # There is no installed Meta attempt association to abort here. Never
        # accept a callback/handle to manufacture one; the fixed join owns it.

    def close(self) -> None:
        state = _RUNTIMES.get(self)
        if state is None:
            raise RuntimeError("original Workspace private-read runtime required")
        state.live = False
        errors = []
        for operation_use in tuple(state.families):
            try:
                self._retire_local(operation_use)
            except BaseException as error:  # noqa: BLE001 - finish every family's cleanup before raising
                errors.append(error)
        if errors:
            raise BaseExceptionGroup("Workspace private-read cleanup failed", errors)


def _assemble_private_stage_read_runtime(factory):
    from .direct_command_composition import (
        _ORIGIN_FACTORIES,
        _DirectWorkspaceOriginFactory,
    )

    if type(factory) is not _DirectWorkspaceOriginFactory or factory not in _ORIGIN_FACTORIES:
        raise TypeError("original fixed Workspace factory required")
    if inspect.getattr_static(factory, "_private_reads", None) is not None:
        raise RuntimeError("Workspace private-read assembly replay")
    runtime = object.__new__(_WorkspacePrivateStageReadRuntime)
    _RUNTIMES[runtime] = _RuntimeState(
        ref(factory), os.getpid(), current_thread(),
        inspect.getattr_static(factory, "validate_selected_graph_node_use"),
        inspect.getattr_static(factory, "check_selected_graph_node_use_locked"),
    )
    return runtime
