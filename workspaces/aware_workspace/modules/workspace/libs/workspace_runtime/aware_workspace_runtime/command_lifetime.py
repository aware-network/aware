"""Owner-local lifetime mechanics. Construction is not Code bootstrap admission."""

from __future__ import annotations

import copy
import os
import threading
from uuid import uuid4

from aware_code_semantic_contract_runtime.catalog_epoch_interfaces import (
    DirectInvocationExpectation,
)
from aware_code_semantic_contract_runtime.direct_origin_interfaces import (
    DirectCommandExpectedContext,
)

_Context = tuple[
    tuple[tuple[str, object, str], ...],
    tuple[object, ...],
    tuple[tuple[str, object, object], ...],
]


class WorkspaceCommandLifetimeUnavailable(RuntimeError):
    pass


class WorkspaceDirectInvocationParent:
    __slots__ = ()

    def __new__(cls):
        raise TypeError("original runtime issues invocation parents")

    def __reduce__(self):
        raise TypeError("invocation parents cannot be copied or serialized")


class WorkspaceCatalogEpochExclusionGuard:
    __slots__ = ()

    def __new__(cls):
        raise TypeError("original runtime issues exclusion guards")

    def __reduce__(self):
        raise TypeError("exclusion guards cannot be copied or serialized")


class WorkspaceCommandLifetime:
    __slots__ = ()

    def __new__(cls):
        raise TypeError("original runtime issues command lifetimes")

    def __reduce__(self):
        raise TypeError("command lifetimes cannot be copied or serialized")


class WorkspaceCommandPublicationGuard:
    __slots__ = ()

    def __new__(cls):
        raise TypeError("original runtime issues publication guards")

    def __reduce__(self):
        raise TypeError("publication guards cannot be copied or serialized")


class WorkspaceCommandLifetimeRuntime:
    """One invocation, one complete binding, one terminal close.

    Resource references are borrowed here. Fixed composition owns cleanup and Code
    owns dependent policies. Neither callbacks nor guessed cleanup methods run here.
    Code must authenticate this original runtime and its callables separately.
    """

    def __init__(self) -> None:
        self._pid = os.getpid()
        self._invocation = object()
        self._epoch = object()
        self._direct_epoch_ref = f"workspace-command-epoch:{uuid4()}"
        self._direct_parent_ref: str | None = None
        self._direct_operation_ref: str | None = None
        self._lock = threading.RLock()
        self._closed = False
        self._parent: WorkspaceDirectInvocationParent | None = None
        self._lifetime: WorkspaceCommandLifetime | None = None
        self._context: _Context | None = None
        self._guard: (
            WorkspaceCommandPublicationGuard
            | WorkspaceCatalogEpochExclusionGuard
            | None
        ) = None
        self._thread: threading.Thread | None = None

    @property
    def invocation_identity(self) -> object:
        return self._invocation

    @property
    def epoch_identity(self) -> object:
        return self._epoch

    def _process(self) -> None:
        # Check before locking: inherited locks may be held by vanished threads.
        if os.getpid() != self._pid:
            raise WorkspaceCommandLifetimeUnavailable("command_process_changed")

    def _retain_direct_invocation_parent(self) -> WorkspaceDirectInvocationParent:
        """Pre-catalog assembly mechanism; not bootstrap authentication."""
        self._process()
        with self._lock:
            if self._closed or self._parent is not None or self._lifetime is not None:
                raise WorkspaceCommandLifetimeUnavailable("command_parent_unavailable")
            self._parent = object.__new__(WorkspaceDirectInvocationParent)
            self._direct_parent_ref = f"workspace-command-parent:{uuid4()}"
            return self._parent

    def issue_direct_source_operation_coordinates(
        self,
        parent: WorkspaceDirectInvocationParent,
        *,
        expected: DirectInvocationExpectation,
    ) -> tuple[str, str, str]:
        """Detach one operation identity only while the original parent is live.

        These coordinates document issuance; they cannot validate or reopen the
        nominal parent, epoch, source admission, or a later graph operation.
        """
        self._process()
        with self._lock:
            self._check_direct_invocation_parent(parent, expected=expected)
            if self._direct_operation_ref is not None or self._direct_parent_ref is None:
                raise WorkspaceCommandLifetimeUnavailable("direct_operation_already_issued")
            self._direct_operation_ref = f"workspace-materialize-operation:{uuid4()}"
            return (
                self._direct_operation_ref,
                self._direct_parent_ref,
                self._direct_epoch_ref,
            )

    def validate_direct_invocation_parent(
        self,
        parent: WorkspaceDirectInvocationParent,
        *,
        expected: DirectInvocationExpectation,
    ) -> None:
        self._process()
        with self._lock:
            self._check_direct_invocation_parent(parent, expected=expected)

    def _check_direct_invocation_parent(
        self,
        parent: WorkspaceDirectInvocationParent,
        *,
        expected: DirectInvocationExpectation,
        retiring: bool = False,
    ) -> None:
        """Identity checks only; caller already holds original exclusion."""
        if (
            (self._closed and not retiring)
            or self._parent is None
            or type(parent) is not WorkspaceDirectInvocationParent
            or parent is not self._parent
        ):
            raise WorkspaceCommandLifetimeUnavailable("command_parent_not_live")
        if (
            type(expected) is not DirectInvocationExpectation
            or type(expected.process_id) is not int
            or expected.process_id != self._pid
            or expected.invocation_identity is not self._invocation
            or expected.lifetime_epoch_identity is not self._epoch
        ):
            raise WorkspaceCommandLifetimeUnavailable("command_parent_context_differs")

    def validate_direct_invocation_context_binding(
        self,
        parent: WorkspaceDirectInvocationParent,
        lifetime: WorkspaceCommandLifetime,
        *,
        invocation: DirectInvocationExpectation,
        expected: DirectCommandExpectedContext,
    ) -> None:
        self._process()
        with self._lock:
            self.validate_direct_invocation_parent(parent, expected=invocation)
            self.validate_command_lifetime(lifetime, expected=expected)

    def acquire_catalog_epoch_exclusion(
        self,
        parent: WorkspaceDirectInvocationParent,
        *,
        expected: DirectInvocationExpectation,
    ) -> WorkspaceCatalogEpochExclusionGuard:
        return self._acquire_source_record_exclusion(parent, expected=expected)

    def _acquire_source_record_exclusion(
        self,
        parent: WorkspaceDirectInvocationParent,
        *,
        expected: DirectInvocationExpectation,
        retiring: bool = False,
    ) -> WorkspaceCatalogEpochExclusionGuard:
        """Same exclusion; retirement may clean records after parent closure."""
        self._process()
        self._lock.acquire()
        try:
            self._check_direct_invocation_parent(
                parent, expected=expected, retiring=retiring
            )
            if self._guard is not None:
                raise WorkspaceCommandLifetimeUnavailable("command_guard_nested")
            guard = object.__new__(WorkspaceCatalogEpochExclusionGuard)
            self._guard = guard
            self._thread = threading.current_thread()
            return guard
        except BaseException:
            self._lock.release()
            raise

    def validate_catalog_epoch_exclusion(
        self,
        guard: WorkspaceCatalogEpochExclusionGuard,
        *,
        parent: WorkspaceDirectInvocationParent,
        expected: DirectInvocationExpectation,
    ) -> None:
        self._process()
        if (
            type(guard) is not WorkspaceCatalogEpochExclusionGuard
            or guard is not self._guard
            or self._thread is not threading.current_thread()
        ):
            raise WorkspaceCommandLifetimeUnavailable("command_guard_foreign")
        self._check_direct_invocation_parent(parent, expected=expected)

    def release_catalog_epoch_exclusion(
        self, guard: WorkspaceCatalogEpochExclusionGuard
    ) -> None:
        self._release_guard(guard, WorkspaceCatalogEpochExclusionGuard)

    def _context_key(self, expected: DirectCommandExpectedContext) -> _Context:
        if type(expected) is not DirectCommandExpectedContext:
            raise TypeError("exact Code expected context required")
        expected.__post_init__()
        if (
            expected.process_id != self._pid
            or expected.invocation_identity is not self._invocation
            or expected.epoch_identity is not self._epoch
        ):
            raise WorkspaceCommandLifetimeUnavailable("command_identity_mismatch")
        if (
            next(b.resource for b in expected.resources if b.role == "lifetime_runtime")
            is not self
        ):
            raise WorkspaceCommandLifetimeUnavailable("command_runtime_mismatch")
        # Pin portable coordinates by value; retain original objects by identity.
        return (
            tuple((b.role, b.resource, b.disposition) for b in expected.resources),
            copy.deepcopy(
                (
                    expected.composition_implementation,
                    expected.composition_configuration,
                    expected.policy_implementation,
                    expected.policy_configuration,
                )
            ),
            tuple(
                (b.stage, b.runtime, b.registration)
                for b in expected.stage_runtime_bindings
            ),
        )

    def bind_command_lifetime(
        self, *, expected: DirectCommandExpectedContext
    ) -> WorkspaceCommandLifetime:
        """Called once after full assembly; does not authenticate the assembly."""
        self._process()
        with self._lock:
            if self._closed or self._lifetime is not None:
                raise WorkspaceCommandLifetimeUnavailable("command_binding_replay")
            context = self._context_key(expected)
            self._context = context
            self._lifetime = object.__new__(WorkspaceCommandLifetime)
            return self._lifetime

    def validate_command_lifetime(
        self,
        lifetime: WorkspaceCommandLifetime,
        *,
        expected: DirectCommandExpectedContext,
    ) -> None:
        self._process()
        with self._lock:
            if self._closed or self._lifetime is None or lifetime is not self._lifetime:
                raise WorkspaceCommandLifetimeUnavailable("command_not_live")
            current = self._context_key(expected)
            assert self._context is not None
            original_resources, original_coordinates, original_stages = self._context
            resources, coordinates, stages = current
            if (
                len(resources) != len(original_resources)
                or len(stages) != len(original_stages)
                or any(
                    a != b or ar is not br or ag is not bg
                    for (a, ar, ag), (b, br, bg) in zip(original_stages, stages)
                )
                or coordinates != original_coordinates
                or any(
                    ar != br or ao is not bo or ad != bd
                    for (ar, ao, ad), (br, bo, bd) in zip(original_resources, resources)
                )
            ):
                raise WorkspaceCommandLifetimeUnavailable("command_context_substituted")

    def acquire_command_publication_guard(
        self,
        lifetime: WorkspaceCommandLifetime,
        *,
        expected: DirectCommandExpectedContext,
    ) -> WorkspaceCommandPublicationGuard:
        self._process()
        self._lock.acquire()
        try:
            self.validate_command_lifetime(lifetime, expected=expected)
            if self._guard is not None:
                raise WorkspaceCommandLifetimeUnavailable("command_guard_nested")
            guard = object.__new__(WorkspaceCommandPublicationGuard)
            self._guard = guard
            self._thread = threading.current_thread()
            return guard
        except BaseException:
            self._lock.release()
            raise

    def validate_command_publication_guard(
        self,
        guard: WorkspaceCommandPublicationGuard,
        *,
        lifetime: WorkspaceCommandLifetime,
        expected: DirectCommandExpectedContext,
    ) -> None:
        self._process()
        if (
            type(guard) is not WorkspaceCommandPublicationGuard
            or guard is not self._guard
            or self._thread is not threading.current_thread()
        ):
            raise WorkspaceCommandLifetimeUnavailable("command_guard_foreign")
        self.validate_command_lifetime(lifetime, expected=expected)

    def release_command_publication_guard(
        self, guard: WorkspaceCommandPublicationGuard
    ) -> None:
        self._release_guard(guard, WorkspaceCommandPublicationGuard)

    def _release_guard(self, guard, kind) -> None:
        self._process()
        if (
            type(guard) is not kind
            or guard is not self._guard
            or self._thread is not threading.current_thread()
        ):
            raise WorkspaceCommandLifetimeUnavailable("command_guard_foreign")
        self._guard = None
        self._thread = None
        self._lock.release()

    def close(self) -> None:
        """Revoke before owner cleanup; borrowed resources are never closed here."""
        self._process()
        with self._lock:
            self._closed = True
            self._context = None
