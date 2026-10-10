"""Dependency-scope comparison and validation signatures, never admission.

Workspace owns original closure handles and resources. Code must authenticate the
original instance and retain each method before invocation. Structural conformance,
a constructed expectation or a successful no-op callback supplies no authority.
The reader returns portable evidence, never original membership authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TypeVar

from .contracts import ContentDigest, ContractViolation
from .dependency_scope_closure import CodeRetainedDependencyScopeClosure
from .dependency_scope_closure_v2 import CodeRetainedDependencyScopeClosureV2
from .semantic_candidates import _path


@dataclass(frozen=True, slots=True, eq=False)
class RetainedDependencyScopeExpectation:
    """Freely constructible comparison values; originals must be checked by owner.

    Identity fields compare by ``is`` at the original validator. Constructor
    checks only shape; it does not authenticate the process, epoch or resources.
    This value has no wire codec and cannot be pickled or copied into authority.
    """

    parent_identity: object
    epoch_identity: object
    operation_identity: object
    process_id: int
    repository_membership_identity: object
    closure_runtime_identity: object
    consumer_scope_key: str

    def __post_init__(self) -> None:
        if type(self.process_id) is not int:
            raise ContractViolation("dependency scope process must be exact integer")
        _path(self.consumer_scope_key)

    def __reduce__(self):
        raise TypeError("dependency scope expectation is not serializable")

    def __reduce_ex__(self, protocol):
        raise TypeError("dependency scope expectation is not serializable")


_Closure_contra = TypeVar("_Closure_contra", contravariant=True)


class DependencyScopeValidator(Protocol[_Closure_contra]):
    """Full original repository/scope/edge validation outside publication locks."""

    def validate_dependency_scope_closure(
        self,
        closure: _Closure_contra,
        *,
        expected: RetainedDependencyScopeExpectation,
        closure_digest: ContentDigest | None = None,
    ) -> None:
        """Validate all original resources, then final records and lifetime.

        Before reading, omit the digest. After policy calculation, supply the
        consumed digest; the original owner recomputes it from retained evidence.
        A portable closure or caller digest never substitutes for original handles.
        Repeated validation neither caches currentness nor admits execution.
        """
        ...


class DependencyScopeLockedValidator(Protocol[_Closure_contra]):
    """Bounded original record check under the already-held parent exclusion."""

    def check_dependency_scope_closure_locked(
        self,
        closure: _Closure_contra,
        *,
        expected: RetainedDependencyScopeExpectation,
        closure_digest: ContentDigest,
        guard: object,
    ) -> None:
        """Check original guard, operation/epoch, records, digest and lifetime.

        No lock/guard reacquisition, source reads, blocking cleanup or arbitrary
        callbacks. This cannot replace full pre/post source validation. Concrete
        constituent retirement must share the same original parent exclusion;
        implementing this Protocol does not establish that participation.
        """
        ...


class DependencyScopeReader(Protocol[_Closure_contra]):
    """Original reader must be retained/authenticated by fixed composition."""

    def read_dependency_scope_closure(
        self, closure: _Closure_contra, *, expected: RetainedDependencyScopeExpectation
    ) -> CodeRetainedDependencyScopeClosure:
        """Mechanically project original scopes and edges, without policy or grants."""
        ...


class DependencyScopeReaderV2(Protocol[_Closure_contra]):
    """Fixed composition pins v2 and original validators; no version fallback."""

    def read_dependency_scope_closure(
        self, closure: _Closure_contra, *, expected: RetainedDependencyScopeExpectation
    ) -> CodeRetainedDependencyScopeClosureV2:
        """Project original profile associations in the retained path domain.

        Full validators revalidate original consumer status and all retained bodies.
        This signature cannot authenticate an instance, handle or callable.
        """
        ...


class DependencyScopeOperationBinding(Protocol[_Closure_contra]):
    """Original owner installs/retires a per-use association on an existing source."""

    def bind_dependency_scope_operation(
        self, source: _Closure_contra, *, expected: RetainedDependencyScopeExpectation
    ) -> None:
        """Validate the original Code use; duplicate binding refuses."""
        ...

    def release_dependency_scope_operation(
        self, source: _Closure_contra, *, expected: RetainedDependencyScopeExpectation
    ) -> None:
        """Retire only this association; allow cleanup after revocation."""
        ...


class DependencyScopeOperationValidator(Protocol):
    """Code's original validator must be authenticated by fixed composition."""

    def validate_dependency_scope_operation(
        self, operation: object, *, expected: RetainedDependencyScopeExpectation
    ) -> None:
        """Check original running use and retained context, without owner calls."""
        ...
