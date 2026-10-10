"""Original parent participation for source records; never bootstrap authority."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

from aware_code_semantic_contract_runtime.catalog_epoch_interfaces import (
    DirectInvocationExpectation,
)

from .command_lifetime import (
    WorkspaceCatalogEpochExclusionGuard,
    WorkspaceCommandLifetimeRuntime,
    WorkspaceDirectInvocationParent,
)
from .source_observation_io import SourceObservationUnavailable


@dataclass(frozen=True, slots=True, init=False)
class WorkspaceSourceExclusion:
    """Fixed composition supplies one original instance before record creation.

    Participating runtimes borrow this object and their parent. Construction proves
    only parent mechanics; Code must authenticate the original fixed assembly.
    """

    _runtime: WorkspaceCommandLifetimeRuntime
    _parent: WorkspaceDirectInvocationParent
    _expected: DirectInvocationExpectation

    def __init__(
        self,
        *,
        runtime: WorkspaceCommandLifetimeRuntime,
        parent: WorkspaceDirectInvocationParent,
        expected: DirectInvocationExpectation,
    ) -> None:
        if type(runtime) is not WorkspaceCommandLifetimeRuntime:
            raise TypeError("exact command lifetime runtime required")
        runtime.validate_direct_invocation_parent(parent, expected=expected)
        object.__setattr__(self, "_runtime", runtime)
        object.__setattr__(self, "_parent", parent)
        # Frozen context copied so a caller cannot later mutate our expected value.
        original = DirectInvocationExpectation(
            expected.invocation_identity,
            expected.lifetime_epoch_identity,
            expected.process_id,
        )
        object.__setattr__(self, "_expected", original)

    def check_live(self) -> None:
        # Full source work must never acquire parent exclusion under source locks.
        # This preliminary check is NOT the final guarded publication check.
        self._runtime._process()
        self._runtime._check_direct_invocation_parent(
            self._parent, expected=self._expected
        )

    def check_locked(self, guard: WorkspaceCatalogEpochExclusionGuard) -> None:
        self._runtime.validate_catalog_epoch_exclusion(
            guard, parent=self._parent, expected=self._expected
        )

    @contextmanager
    def mutation(
        self, *, retiring: bool = False
    ) -> Iterator[WorkspaceCatalogEpochExclusionGuard]:
        guard = self._runtime._acquire_source_record_exclusion(
            self._parent, expected=self._expected, retiring=retiring
        )
        try:
            yield guard
        finally:
            self._runtime.release_catalog_epoch_exclusion(guard)


def require_same_exclusion(
    actual: WorkspaceSourceExclusion | None,
    expected: WorkspaceSourceExclusion | None,
) -> None:
    if actual is not expected or (
        actual is not None and type(actual) is not WorkspaceSourceExclusion
    ):
        raise SourceObservationUnavailable("source_exclusion_origin_mismatch")
