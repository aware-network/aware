"""Consumer interfaces for original existing-branch Subject reads.

These non-runtime-checkable protocols freeze calls, not an issuer or a wire.
Structural conformity, equal coordinates and copied observations never prove
original issuance. Infrastructure must supply the qualified Ontology receiver;
neither applications nor this module appoint a provider or verifier.

The first profile is a current, existing branch. No constructor, historical
selection, provisioning, Object acquisition or canonical-history claim follows.
"""
# pyright: strict

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from enum import StrEnum
from types import TracebackType
from typing import Literal, Protocol

from .subject_reference import SubjectReference


class SubjectReadFailure(StrEnum):
    """Owner-reported failures, not caller-supplied authority/currentness flags."""

    UNAVAILABLE = "subject_read_unavailable"
    NOT_FOUND = "subject_not_found"
    AMBIGUOUS = "subject_ambiguous"
    UNSUPPORTED = "subject_profile_unsupported"
    DENIED = "subject_read_denied"
    STALE = "subject_read_stale"
    INVALIDATED = "subject_read_invalidated"
    RELEASED = "subject_read_released"
    FOREIGN_EXECUTION = "subject_read_foreign_execution"
    RESERVATION_BUSY = "subject_publication_busy"
    CLEANUP_UNRESOLVED = "subject_cleanup_unresolved"


class SubjectReadError(RuntimeError):
    """No usable read/result is returned on failure; cleanup is not retry right."""

    code: SubjectReadFailure

    def __init__(self, code: SubjectReadFailure) -> None:
        if type(code) is not SubjectReadFailure:
            raise TypeError("exact SubjectReadFailure required")
        self.code = code
        super().__init__(code.value)


class SubjectTarget(Protocol, metaclass=ABCMeta):
    """Read-only owner-projected target facts; not a transferable capability.

    All requested fields must match independently verified originals. Runtime
    coordinates below are authenticated outputs, not aliases of config UUIDs.
    ``node_refs`` preserves complete declared target coverage and owner order;
    it must not silently reduce a multi-node Observable to its root. Coordinates
    are opaque: consumers neither parse nor independently recalculate them.
    """

    @property
    @abstractmethod
    def reference(self) -> SubjectReference: ...

    @property
    @abstractmethod
    def root_identity_ref(self) -> str: ...

    @property
    @abstractmethod
    def root_object_ref(self) -> str: ...

    @property
    @abstractmethod
    def root_type_ref(self) -> str: ...

    @property
    @abstractmethod
    def projection_ref(self) -> str: ...

    @property
    @abstractmethod
    def observable_ref(self) -> str: ...

    @property
    @abstractmethod
    def observable_branch_ref(self) -> str: ...

    @property
    @abstractmethod
    def configuration_ref(self) -> str: ...

    @property
    @abstractmethod
    def source_association_ref(self) -> str: ...

    @property
    @abstractmethod
    def node_refs(self) -> tuple[str, ...]: ...


class SubjectInput(Protocol, metaclass=ABCMeta):
    """One consumed input/evidence scope, including its exact evidence profile.

    The issuer preserves the complete bounded inventory from all participating
    owners. A prefix, full body, manifest or inventory witness must keep its own
    profile; an evidence reference is not automatically a full-content digest.
    These diagnostic coordinates cannot be replayed to reconstruct authority.
    """

    @property
    @abstractmethod
    def owner_ref(self) -> str: ...

    @property
    @abstractmethod
    def owner_generation(self) -> str: ...

    @property
    @abstractmethod
    def profile_ref(self) -> str: ...

    @property
    @abstractmethod
    def input_ref(self) -> str: ...

    @property
    @abstractmethod
    def revision_ref(self) -> str: ...


class SubjectObservation(Protocol, metaclass=ABCMeta):
    """Immutable owner-projected facts, never domain state or read permission.

    A revision qualifies this read, not stable identity forever. A fresh read
    after a compatible state advance may retain identity; this read cannot be
    refreshed/rebound to another revision, root, branch or configuration.
    """

    @property
    @abstractmethod
    def target(self) -> SubjectTarget: ...

    @property
    @abstractmethod
    def revision_ref(self) -> str: ...

    @property
    @abstractmethod
    def inputs(self) -> tuple[SubjectInput, ...]: ...


class SubjectPublicationReservation(Protocol, metaclass=ABCMeta):
    """Original short writer reservation, never a reconstructed/current flag.

    The owning context performs final original qualification and retains every
    required writer exclusion through exit. ``observation`` is that final
    immutable result, not another read. ``require_current`` validates original
    custody/loss at the publication point, never re-resolves or advances HEAD.
    Every nested owner call must be included in the receiver's qualified budget.
    """

    @property
    @abstractmethod
    def observation(self) -> SubjectObservation: ...

    @abstractmethod
    def require_current(self) -> None: ...


class SubjectPublicationContext(Protocol, metaclass=ABCMeta):
    """Synchronous, single-use, non-reentrant final-publication interval.

    Entry returns only after original final verification under actual upstream
    protection. No await, Service fulfillment or target lookup is allowed inside.
    Foreign process/thread/Task exit refuses BEFORE consuming context state;
    owner cleanup remains available. Exit never suppresses an exception. Owner
    teardown must release exclusions even with an inherited child descriptor.
    Cleanup uncertainty remains explicit, not success or a new attempt.
    """

    @abstractmethod
    def __enter__(self) -> SubjectPublicationReservation: ...

    @abstractmethod
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]: ...


class SubjectRead(Protocol, metaclass=ABCMeta):
    """Original operation-scoped borrower, not a freely constructible Subject.

    The issuer binds process/thread/Task, original request and owner generations.
    Every use revalidates originals and detects mutation, copies and substitution.
    Observed stale/lost authority permanently invalidates this read, including
    after change-and-restore; no field restoration or cached result revives it.
    A lock is never held across asynchronous fulfillment.
    """

    @property
    @abstractmethod
    def reference(self) -> SubjectReference: ...

    @abstractmethod
    def read(self) -> SubjectObservation:
        """Validate and return this read's original immutable target/inventory."""
        ...

    @abstractmethod
    def require_current(self) -> None:
        """Validate this original read, not just matching coordinates/digests."""
        ...

    @abstractmethod
    def reserve_publication(self) -> SubjectPublicationContext:
        """Create a final context without acquiring a lock until its entry."""
        ...

    @abstractmethod
    def release(self) -> None:
        """Permanently end borrower use; never retire a borrowed owner.

        Legitimate owner release is idempotent after settled cleanup. Foreign
        release refuses without changing custody. Active reservations must be
        exited by their owner before release; release cannot dismantle them.
        Failure must disclose uncertain cleanup, never silently retry an effect.
        """
        ...


class SubjectReader(Protocol, metaclass=ABCMeta):
    """Explicitly delivered original Ontology receiver; no SDK discovery/default.

    Appointing an implementation is infrastructure's independently qualified
    operation. Conforming to this protocol proves no enrollment or permission.
    Attention permission and Service View-entry remain separate admissions.
    """

    @abstractmethod
    async def acquire(self, reference: SubjectReference, /) -> SubjectRead:
        """Authenticate one existing branch with complete original coverage.

        Join Meta/config, actual source and namespace/worldline/branch authority
        before issuing a borrower. Never trust nomination fields or UUID equality
        instead. Unsupported/missing originals refuse without partial issuance;
        exceptions/cancellation settle only owned partial acquisitions. Reads
        provision nothing. Returned custody belongs to the awaiting Task, not a
        worker or child Task. Acquisition needs no already-published View.
        """
        ...
