"""Paired-publication consumer signatures; no parent, epoch or transfer issuer.

All expectation values are freely constructible comparison data. Concrete handles
stay with their owning runtimes. Fixed assembly must authenticate the original
instances and retain their original callable entrances before any Protocol call.
Successful callbacks, matching digests and Protocol conformance grant nothing.
"""

from dataclasses import dataclass
from typing import Protocol, TypeVar

from .contracts import ContentDigest
from .direct_origin_interfaces import DirectCommandExpectedContext
from .materialization_catalog import AdmittedCodeSemanticContractCatalog
from .retained_admission_interfaces import RetainedSemanticAdmissionExpectation
from .runtime import ExecutionCompletion


@dataclass(frozen=True, slots=True, eq=False)
class DirectInvocationExpectation:
    """Pre-catalog identity comparisons; original owner retains resource evidence."""

    invocation_identity: object
    lifetime_epoch_identity: object
    process_id: int


@dataclass(frozen=True, slots=True, eq=False)
class CatalogPairEpochExpectation:
    """Both snapshots under one nominal publication identity, never a generation."""

    invocation: DirectInvocationExpectation
    publication_identity: object
    code_catalog_digest: ContentDigest
    membership_catalog_digest: ContentDigest
    contribution_digest: ContentDigest


@dataclass(frozen=True, slots=True, eq=False)
class CatalogPublicationExpectation:
    """Initial publication has no predecessor; successor transfer requires one.

    entry_inputs_digest binds Workspace's exact authenticated entry-input closure.
    Code does not parse that closure or issue its membership authority.
    """

    preparation_identity: object
    predecessor: CatalogPairEpochExpectation | None
    successor: CatalogPairEpochExpectation
    entry_inputs_digest: ContentDigest


@dataclass(frozen=True, slots=True, eq=False)
class EpochSemanticOperationExpectation:
    """Operation lifetime and publication lifetime are separate comparisons.

    operation.generation_identity remains the original lifetime epoch. Its
    runtime is the original admitted stage runtime, not a caller replacement.
    """

    operation: RetainedSemanticAdmissionExpectation
    publication: CatalogPairEpochExpectation


@dataclass(frozen=True, slots=True, eq=False)
class CatalogCompletionTransferExpectation:
    """Expected original operation and exact target preparation; not a handoff."""

    operation: EpochSemanticOperationExpectation
    publication: CatalogPublicationExpectation


_Parent_contra = TypeVar("_Parent_contra", contravariant=True)
_Lifetime_contra = TypeVar("_Lifetime_contra", contravariant=True)
_Epoch_contra = TypeVar("_Epoch_contra", contravariant=True)
_Preparation_contra = TypeVar("_Preparation_contra", contravariant=True)
_Guard_contra = TypeVar("_Guard_contra", contravariant=True)
_Context_contra = TypeVar("_Context_contra", contravariant=True)
_Transfer = TypeVar("_Transfer")


class DirectInvocationParentValidator(Protocol[_Parent_contra, _Lifetime_contra]):
    def validate_direct_invocation_parent(
        self, parent: _Parent_contra, *, expected: DirectInvocationExpectation
    ) -> None:
        """Original process/live parent, identities and retained resources only."""
        ...

    def validate_direct_invocation_context_binding(
        self,
        parent: _Parent_contra,
        lifetime: _Lifetime_contra,
        *,
        invocation: DirectInvocationExpectation,
        expected: DirectCommandExpectedContext,
    ) -> None:
        """Original once-only pre/full-context correspondence, not a new lifetime.

        Check invocation and lifetime epoch identities by identity, and process
        exactly. Initial catalog/resources must have been genuinely assembled.
        This never treats a retired initial catalog as current epoch authority.
        """
        ...


class CatalogEpochPublicationValidator(
    Protocol[_Epoch_contra, _Preparation_contra, _Guard_contra]
):
    def validate_current_catalog_epoch(
        self, epoch: _Epoch_contra, *, expected: CatalogPairEpochExpectation
    ) -> None:
        """Require original current paired epoch and live parent; reject retired use."""
        ...

    def read_code_catalog_for_epoch(
        self, epoch: _Epoch_contra, *, expected: CatalogPairEpochExpectation
    ) -> AdmittedCodeSemanticContractCatalog:
        """Return only the exact published Code admission from the original pair.

        No prepared admission is exposed. Caller revalidates currentness and
        Code's admission; a digest match alone is insufficient.
        """
        ...

    def validate_prepared_catalog_publication(
        self,
        preparation: _Preparation_contra,
        *,
        expected: CatalogPublicationExpectation,
    ) -> None:
        """Original unconsumed preparation and both exact snapshots/entry inputs."""
        ...

    def validate_catalog_epoch_publication_guard(
        self,
        guard: _Guard_contra,
        *,
        preparation: _Preparation_contra,
        expected: CatalogPublicationExpectation,
    ) -> None:
        """Original thread/process guard under joint parent synchronization.

        No I/O: require live parent, current predecessor, exact preparation and
        owner-side exclusion of incompatible admitted operations. No callback
        result can stand in for this original nominal guard.
        """
        ...

    def validate_committed_catalog_publication(
        self,
        preparation: _Preparation_contra,
        completion_transfer: object,
        *,
        expected: CatalogPublicationExpectation,
    ) -> None:
        """Require the exact transfer in the original committed publication record.

        Read the joint linearization record, not a separately toggled Code flag.
        No predecessor liveness is required after its lawful retirement. This
        records history only; current successor use needs its currentness check.
        """
        ...


class CodeCatalogCompletionTransferRuntime(
    Protocol[_Context_contra, _Preparation_contra, _Guard_contra, _Transfer]
):
    def prepare_catalog_completion_transfer(
        self,
        operation_context: _Context_contra,
        completion: ExecutionCompletion,
        preparation: _Preparation_contra,
        *,
        expected: CatalogCompletionTransferExpectation,
    ) -> _Transfer:
        """Retain original authority-stage completion and exact prepared successor.

        Require original runtime snapshot/operation/provider/policy lineage and
        planning/dependency predecessor evidence; portable results never suffice.
        This issues provisional evidence, not current successor authority.
        """
        ...

    def validate_catalog_completion_transfer(
        self, transfer: _Transfer, *, expected: CatalogCompletionTransferExpectation
    ) -> None:
        """Pre-publication rereads of original completion, context and preparation."""
        ...

    def seal_catalog_completion_transfer(
        self,
        transfer: _Transfer,
        guard: _Guard_contra,
        *,
        expected: CatalogCompletionTransferExpectation,
    ) -> None:
        """No I/O: freeze the exact transfer under original joint exclusion.

        Sealing is not consumption/publication. The single Workspace publication
        record must atomically bind this transfer, replace both legs and retire
        predecessor authority. No independent Code commit callback is provided.
        """
        ...

    def validate_committed_catalog_completion_transfer(
        self, transfer: _Transfer, *, expected: CatalogCompletionTransferExpectation
    ) -> None:
        """Original committed joint record and retained completion, not new execution.

        Check live parent and current successor for successor use. Validate frozen
        original completion evidence without trying to revive predecessor context.
        """
        ...

    def discard_catalog_completion_transfer(self, transfer: _Transfer) -> None:
        """Retire this provisional/sealed attempt only; never undo a committed winner.

        Repeated discard of this already-discarded original is harmless. Foreign
        or committed handles reject. Cleanup failure cannot restore authority.
        """
        ...


_ExclusionGuard = TypeVar("_ExclusionGuard")


class CatalogEpochExclusionRuntime(Protocol[_Parent_contra, _ExclusionGuard]):
    """Workspace's same original parent lock for operation and publication admission."""

    def acquire_catalog_epoch_exclusion(
        self, parent: _Parent_contra, *, expected: DirectInvocationExpectation
    ) -> _ExclusionGuard:
        """Acquire original parent lock, then validate; unwind internally on failure.

        Return an original process/thread-bound, single-use guard. This is the
        same exclusion used by close and publication, not a Code-local lock.
        """
        ...

    def validate_catalog_epoch_exclusion(
        self,
        guard: _ExclusionGuard,
        *,
        parent: _Parent_contra,
        expected: DirectInvocationExpectation,
    ) -> None:
        """No I/O: require original active guard, live parent and exact identities."""
        ...

    def release_catalog_epoch_exclusion(self, guard: _ExclusionGuard) -> None:
        """Release original guard in finally, including after parent revocation.

        Require original process/acquiring thread and retire once. Failed
        liveness must not prevent unlocking. Foreign/replayed releases reject.
        """
        ...


class CodeCatalogEpochExclusionParticipant(Protocol[_Guard_contra]):
    """Original Code host participant; registering a no-op cannot grant safety."""

    def validate_catalog_publication_exclusion(
        self, guard: _Guard_contra, *, expected: CatalogPublicationExpectation
    ) -> None:
        """No I/O: authenticate original parent guard, then inspect Code state.

        Require exact parent/predecessor/preparation and no incompatible active
        reservations or unresolved execution. Final sealing calls this entrance
        under the same guard. Absence of a participant is a refusal, never zero
        activity. Source reads, callbacks executing owner semantics, awaiting and
        physical cleanup cannot occur here. Parent lock precedes Code-local lock.
        """
        ...
