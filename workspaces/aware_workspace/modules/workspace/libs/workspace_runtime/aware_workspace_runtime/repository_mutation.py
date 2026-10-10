from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Protocol

from aware_file_system.confined_mutation import (
    DEFAULT_CONFINED_MUTATION_MAX_BYTES,
    ConfinedFileMutationRequest,
    ConfinedFileMutationResult,
    ConfinedMutationKind,
    ConfinedMutationOutcome,
    ConfinedMutationProfile,
    ConfinedTextReplacement,
    mutate_confined_file,
)

from .change_evidence import (
    RepositoryBodyAvailability,
    RepositoryChangedEntryKind,
    RepositoryEvidenceCoordinateKind,
    RepositoryEvidencePosture,
    RepositoryEvidenceResolutionState,
    RepositoryMutationKind,
    RepositoryMutationOutcome,
    WorkspaceRepositoryChangedEntry,
    WorkspaceRepositoryChangeEvidence,
    WorkspaceRepositoryEvidenceCoordinate,
    WorkspaceRepositoryMutationReceipt,
    WorkspaceRepositoryPhysicalEffect,
    repository_change_evidence_ref,
    repository_changed_entry_ref,
    repository_mutation_receipt_ref,
)
from .contracts import (
    ObservationChangeKind,
    RepositorySnapshotEntry,
    WorkspaceRepositoryObservationBatch,
    WorkspaceRepositoryObservationSnapshot,
)
from .observation import (
    WorkspaceRepositoryObservationSession,
    WorkspaceRepositorySerializedEffect,
)
from .repository_access import (
    WORKSPACE_REPOSITORY_VISIBILITY_POLICY_REF,
    RepositoryEntryKind,
    RepositoryObservationCoordinate,
    repository_entry_ref,
)
from .repository_diff import (
    WorkspaceRepositoryOperationalBodyStore,
    WorkspaceRepositoryOperationalChange,
)

DEFAULT_MUTATION_RECEIPT_CAPACITY = 1024
MAX_MUTATION_RECEIPT_CAPACITY = 4096


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryTextReplacement:
    old_text: str
    new_text: str

    def __post_init__(self) -> None:
        if not isinstance(self.old_text, str) or not self.old_text:
            raise ValueError("Workspace text replacement old_text must be non-empty")
        if not isinstance(self.new_text, str):
            raise ValueError("Workspace text replacement new_text must be text")


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryMutationRequest:
    operation_ref: str
    idempotency_key: str
    mutation_kind: RepositoryMutationKind
    expected_coordinate: WorkspaceRepositoryEvidenceCoordinate
    target_path: str
    expected_exists: bool
    expected_content_digest: str | None
    content: bytes | None = None
    text_replacements: tuple[WorkspaceRepositoryTextReplacement, ...] = ()
    maximum_bytes: int = DEFAULT_CONFINED_MUTATION_MAX_BYTES
    context_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        operation_ref = _required(self.operation_ref, "operation_ref")
        idempotency_key = _required(self.idempotency_key, "idempotency_key")
        path = _relative_path(self.target_path)
        digest = _optional_digest(self.expected_content_digest)
        content = None if self.content is None else bytes(self.content)
        replacements = tuple(self.text_replacements)
        if len(replacements) > 64:
            raise ValueError("Mutation text replacements exceed bound")
        if (
            isinstance(self.maximum_bytes, bool)
            or not 0 < self.maximum_bytes <= DEFAULT_CONFINED_MUTATION_MAX_BYTES
        ):
            raise ValueError("Mutation byte bound is invalid")
        if content is not None and len(content) > self.maximum_bytes:
            raise ValueError("Mutation content exceeds byte bound")
        context_refs = tuple(
            dict.fromkeys(
                _required(value, "context_ref") for value in self.context_refs
            )
        )
        if len(context_refs) > 64:
            raise ValueError("Mutation context refs exceed bound")
        if (
            self.expected_coordinate.kind
            is not RepositoryEvidenceCoordinateKind.OBSERVATION
        ):
            raise ValueError("Mutation expectation must be an observation coordinate")
        if self.mutation_kind is RepositoryMutationKind.CREATE:
            if (
                self.expected_exists
                or digest is not None
                or content is None
                or replacements
            ):
                raise ValueError("Create requires absent baseline and content")
        elif self.mutation_kind is RepositoryMutationKind.UPDATE:
            if (
                not self.expected_exists
                or digest is None
                or ((content is None) == (not replacements))
            ):
                raise ValueError(
                    "Update requires exact baseline and either content or text replacements"
                )
        elif self.mutation_kind is RepositoryMutationKind.DELETE and (
            not self.expected_exists
            or digest is None
            or content is not None
            or replacements
        ):
            raise ValueError("Delete requires exact baseline and no content")
        object.__setattr__(self, "operation_ref", operation_ref)
        object.__setattr__(self, "idempotency_key", idempotency_key)
        object.__setattr__(self, "target_path", path)
        object.__setattr__(self, "expected_content_digest", digest)
        object.__setattr__(self, "content", content)
        object.__setattr__(self, "text_replacements", replacements)
        object.__setattr__(self, "context_refs", context_refs)


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryAuthorizedMutation:
    receipt: WorkspaceRepositoryMutationReceipt
    evidence: WorkspaceRepositoryChangeEvidence | None

    def __post_init__(self) -> None:
        if self.receipt.outcome is RepositoryMutationOutcome.APPLIED:
            if self.evidence is None:
                raise ValueError("Applied mutation requires authorized evidence")
        elif self.evidence is not None:
            raise ValueError("Unapplied mutation cannot carry authorized evidence")


class WorkspaceRepositoryMutationResultStore(Protocol):
    """Durable metadata authority used by the mutation coordinator."""

    def resolve(
        self, receipt_ref: str
    ) -> tuple[str, WorkspaceRepositoryAuthorizedMutation] | None: ...

    def record(
        self,
        *,
        fingerprint: str,
        result: WorkspaceRepositoryAuthorizedMutation,
    ) -> None: ...


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryMutationReceiptResolution:
    requested_receipt_refs: tuple[str, ...]
    resolved: tuple[WorkspaceRepositoryAuthorizedMutation, ...]
    missing_receipt_refs: tuple[str, ...]


class WorkspaceRepositoryMutationCoordinator:
    """Workspace admission/evidence over an explicit physical guarantee.

    The default preserves descriptor-profile V1 receipts and fingerprints. It
    does not authenticate continuous containment under external topology changes.
    Selecting the stronger profile currently yields a typed unavailable result;
    this coordinator never downgrades it to the legacy physical writer.
    """

    def __init__(
        self,
        *,
        session: WorkspaceRepositoryObservationSession,
        body_store: WorkspaceRepositoryOperationalBodyStore,
        receipt_capacity: int = DEFAULT_MUTATION_RECEIPT_CAPACITY,
        result_store: WorkspaceRepositoryMutationResultStore | None = None,
        confinement_profile: ConfinedMutationProfile = (
            ConfinedMutationProfile.DESCRIPTOR_WALK_V1
        ),
    ) -> None:
        if type(confinement_profile) is not ConfinedMutationProfile:
            raise TypeError("Workspace mutation confinement profile must be exact")
        if (
            isinstance(receipt_capacity, bool)
            or not 0 < receipt_capacity <= MAX_MUTATION_RECEIPT_CAPACITY
        ):
            raise ValueError("Mutation receipt capacity is invalid")
        self._session = session
        self._body_store = body_store
        self._receipt_capacity = receipt_capacity
        self._result_store = result_store
        self._confinement_profile: ConfinedMutationProfile = confinement_profile
        self._result_store_error: str | None = None
        self._lock = asyncio.Lock()
        self._results: dict[str, tuple[str, WorkspaceRepositoryAuthorizedMutation]] = {}

    @property
    def session(self) -> WorkspaceRepositoryObservationSession:
        return self._session

    @property
    def body_store(self) -> WorkspaceRepositoryOperationalBodyStore:
        return self._body_store

    @property
    def result_store_error(self) -> str | None:
        return self._result_store_error

    async def mutate(
        self, request: WorkspaceRepositoryMutationRequest
    ) -> WorkspaceRepositoryAuthorizedMutation:
        confinement_profile = self._confinement_profile
        binding_ref = _required(
            self._session.binding.binding_key,
            "repository_binding_ref",
        )
        if request.expected_coordinate.repository_binding_ref != binding_ref:
            raise ValueError("Mutation request binding differs from session")
        receipt_ref = repository_mutation_receipt_ref(
            repository_binding_ref=binding_ref,
            operation_ref=request.operation_ref,
            idempotency_key=request.idempotency_key,
        )
        fingerprint = _request_fingerprint(
            request, confinement_profile=confinement_profile
        )
        async with self._lock:
            existing = self._results.get(receipt_ref)
            if existing is None and self._result_store is not None:
                existing = self._result_store.resolve(receipt_ref)
            if existing is not None:
                if existing[0] != fingerprint:
                    raise ValueError(
                        "Idempotency identity cannot change mutation request"
                    )
                return existing[1]
            if self._result_store_error is not None:
                raise RuntimeError("Mutation receipt metadata store is unavailable")

            physical_result: ConfinedFileMutationResult | None = None

            async def effect(
                snapshot: WorkspaceRepositoryObservationSnapshot,
            ) -> WorkspaceRepositorySerializedEffect[ConfinedFileMutationResult | str]:
                nonlocal physical_result
                if _coordinate(snapshot, self._session) != request.expected_coordinate:
                    return WorkspaceRepositorySerializedEffect(
                        value="stale_coordinate",
                        poll_after=False,
                    )
                snapshot_entry = _entry_for(snapshot, request.target_path)
                if (snapshot_entry is not None) != request.expected_exists:
                    return WorkspaceRepositorySerializedEffect(
                        value="snapshot_existence_mismatch",
                        poll_after=False,
                    )
                if (
                    snapshot_entry is not None
                    and snapshot_entry.content_digest is not None
                    and snapshot_entry.content_digest != request.expected_content_digest
                ):
                    return WorkspaceRepositorySerializedEffect(
                        value="snapshot_content_digest_mismatch",
                        poll_after=False,
                    )
                retained_size = (
                    0 if snapshot_entry is None else snapshot_entry.size_bytes
                ) + _maximum_result_size(request, snapshot_entry)
                if not self._body_store.can_retain(retained_size):
                    return WorkspaceRepositorySerializedEffect(
                        value="body_retention_capacity_exceeded",
                        poll_after=False,
                    )
                if (
                    request.mutation_kind is RepositoryMutationKind.UPDATE
                    and not request.text_replacements
                    and _content_digest(request.content or b"")
                    == request.expected_content_digest
                ):
                    return WorkspaceRepositorySerializedEffect(
                        value="no_content_change",
                        poll_after=False,
                    )
                physical_result = await asyncio.to_thread(
                    mutate_confined_file,
                    root=self._session.binding.root_path,
                    request=_physical_request(request),
                    confinement_profile=confinement_profile,
                )
                if (
                    type(physical_result.confinement_profile) is not ConfinedMutationProfile
                    or physical_result.confinement_profile is not confinement_profile
                ):
                    # Do not converge or issue evidence for a downgraded or
                    # unknown physical result, even if its outcome says applied.
                    return WorkspaceRepositorySerializedEffect(
                        value="filesystem_confinement_profile_mismatch",
                        poll_after=False,
                    )
                return WorkspaceRepositorySerializedEffect(
                    value=physical_result,
                    poll_after=(
                        physical_result.outcome is ConfinedMutationOutcome.APPLIED
                    ),
                    observation_paths=(
                        (request.target_path,)
                        if physical_result.outcome is ConfinedMutationOutcome.APPLIED
                        else None
                    ),
                )

            try:
                transition = await self._session.run_serialized_transition(effect)
            except Exception:  # noqa: BLE001 - failure becomes a typed receipt
                result = _failed_result(
                    request=request,
                    binding_ref=binding_ref,
                    receipt_ref=receipt_ref,
                    physical=physical_result,
                    error_code=(
                        "observer_convergence_failed"
                        if physical_result is not None
                        and physical_result.outcome is ConfinedMutationOutcome.APPLIED
                        else "mutation_execution_failed"
                    ),
                )
            else:
                effect_value = transition.effect
                if isinstance(effect_value, str):
                    outcome = (
                        RepositoryMutationOutcome.STALE
                        if effect_value == "stale_coordinate"
                        else RepositoryMutationOutcome.FAILED
                        if effect_value == "filesystem_confinement_profile_mismatch"
                        else RepositoryMutationOutcome.CONFLICT
                    )
                    result = _unapplied_result(
                        request=request,
                        binding_ref=binding_ref,
                        receipt_ref=receipt_ref,
                        outcome=outcome,
                        error_code=effect_value,
                    )
                elif effect_value.outcome is not ConfinedMutationOutcome.APPLIED:
                    result = _unapplied_result(
                        request=request,
                        binding_ref=binding_ref,
                        receipt_ref=receipt_ref,
                        outcome=_mutation_outcome(effect_value.outcome),
                        error_code=effect_value.error_code
                        or "filesystem_effect_failed",
                        physical=effect_value,
                    )
                elif not _converged(
                    request, effect_value, transition.batch, transition.after
                ):
                    result = _failed_result(
                        request=request,
                        binding_ref=binding_ref,
                        receipt_ref=receipt_ref,
                        error_code="observer_convergence_mismatch",
                        physical=effect_value,
                    )
                else:
                    result = _authorized_result(
                        request=request,
                        binding_ref=binding_ref,
                        receipt_ref=receipt_ref,
                        physical=effect_value,
                        batch=transition.batch,
                        before=transition.before,
                        after=transition.after,
                    )
                    assert result.evidence is not None
                    self._body_store.record(
                        WorkspaceRepositoryOperationalChange(
                            receipt=result.receipt,
                            evidence=result.evidence,
                            before_content=effect_value.before_content,
                            after_content=effect_value.after_content,
                        )
                    )
            self._results[receipt_ref] = (fingerprint, result)
            if self._result_store is not None:
                try:
                    self._result_store.record(
                        fingerprint=fingerprint,
                        result=result,
                    )
                except Exception as error:  # noqa: BLE001 - effect already happened
                    self._result_store_error = f"{type(error).__name__}: {error}"
            while len(self._results) > self._receipt_capacity:
                self._results.pop(next(iter(self._results)))
            return result

    async def resolve_receipts(
        self,
        receipt_refs: tuple[str, ...],
    ) -> WorkspaceRepositoryMutationReceiptResolution:
        confinement_profile = self._confinement_profile
        if type(confinement_profile) is not ConfinedMutationProfile:
            raise TypeError("Workspace mutation confinement profile must be exact")
        requested = tuple(
            dict.fromkeys(_required(value, "mutation_receipt_ref") for value in receipt_refs)
        )
        if not requested or len(requested) > 128 or len(requested) != len(receipt_refs):
            raise ValueError(
                "Mutation receipt request requires 1..128 unique receipt refs"
            )
        resolved: list[WorkspaceRepositoryAuthorizedMutation] = []
        missing: list[str] = []
        async with self._lock:
            for receipt_ref in requested:
                record = self._results.get(receipt_ref)
                if record is None and self._result_store is not None:
                    record = self._result_store.resolve(receipt_ref)
                if record is None:
                    missing.append(receipt_ref)
                else:
                    # V1 receipt bodies do not encode stronger confinement.
                    # Their issuing request metadata must agree with this
                    # coordinator even on read-only historical restoration.
                    expected_domain = (
                        "workspace-repository-mutation-request:sha256:"
                        if confinement_profile is ConfinedMutationProfile.DESCRIPTOR_WALK_V1
                        else "workspace-repository-mutation-request-profile:sha256:"
                    )
                    if not record[0].startswith(expected_domain):
                        raise ValueError(
                            "Mutation receipt confinement profile differs from coordinator"
                        )
                    resolved.append(record[1])
        return WorkspaceRepositoryMutationReceiptResolution(
            requested_receipt_refs=requested,
            resolved=tuple(resolved),
            missing_receipt_refs=tuple(missing),
        )


def _authorized_result(
    *,
    request: WorkspaceRepositoryMutationRequest,
    binding_ref: str,
    receipt_ref: str,
    physical: ConfinedFileMutationResult,
    batch: WorkspaceRepositoryObservationBatch | None,
    before: WorkspaceRepositoryObservationSnapshot,
    after: WorkspaceRepositoryObservationSnapshot,
) -> WorkspaceRepositoryAuthorizedMutation:
    assert batch is not None
    before_coordinate = request.expected_coordinate
    expected_observation = request.expected_coordinate.observation
    assert expected_observation is not None
    after_coordinate = _coordinate_from_snapshot(
        after,
        binding_ref,
        expected_observation.visibility_policy_version,
    )
    kind = RepositoryChangedEntryKind(request.mutation_kind.value)
    old_path = (
        None if kind is RepositoryChangedEntryKind.CREATE else request.target_path
    )
    new_path = (
        None if kind is RepositoryChangedEntryKind.DELETE else request.target_path
    )
    old_entry_ref = (
        None
        if old_path is None
        else repository_entry_ref(
            binding_ref=binding_ref,
            snapshot_digest=before.snapshot_digest,
            path=old_path,
            kind=RepositoryEntryKind.REGULAR_FILE,
        )
    )
    new_entry_ref = (
        None
        if new_path is None
        else repository_entry_ref(
            binding_ref=binding_ref,
            snapshot_digest=after.snapshot_digest,
            path=new_path,
            kind=RepositoryEntryKind.REGULAR_FILE,
        )
    )
    request_body_ref = (
        None
        if request.content is None
        else _body_ref(receipt_ref, "request", _content_digest(request.content))
    )
    result_body_ref = (
        None
        if physical.after_content_digest is None
        else _body_ref(receipt_ref, "result", physical.after_content_digest)
    )
    delta_ref = _digest_ref("workspace-repository-operational-delta", receipt_ref)
    receipt = WorkspaceRepositoryMutationReceipt(
        mutation_receipt_ref=receipt_ref,
        repository_binding_ref=binding_ref,
        operation_ref=request.operation_ref,
        idempotency_key=request.idempotency_key,
        mutation_kind=request.mutation_kind,
        expected_coordinate=request.expected_coordinate,
        target_path=request.target_path,
        expected_exists=request.expected_exists,
        expected_content_digest=request.expected_content_digest,
        outcome=RepositoryMutationOutcome.APPLIED,
        context_refs=request.context_refs,
        result_coordinate=after_coordinate,
        result_entry_ref=new_entry_ref,
        result_content_digest=physical.after_content_digest,
        result_size_bytes=physical.after_size_bytes,
        request_body_evidence_ref=request_body_ref,
        result_body_evidence_ref=result_body_ref,
        delta_evidence_ref=delta_ref,
    )
    changed_entry = WorkspaceRepositoryChangedEntry(
        changed_entry_ref=repository_changed_entry_ref(
            repository_binding_ref=binding_ref,
            before_coordinate=before_coordinate,
            after_coordinate=after_coordinate,
            kind=kind,
            old_path=old_path,
            new_path=new_path,
        ),
        kind=kind,
        posture=RepositoryEvidencePosture.WORKSPACE_AUTHORIZED,
        before_coordinate=before_coordinate,
        after_coordinate=after_coordinate,
        old_path=old_path,
        new_path=new_path,
        old_entry_ref=old_entry_ref,
        new_entry_ref=new_entry_ref,
        old_content_digest=physical.before_content_digest,
        new_content_digest=physical.after_content_digest,
        old_size_bytes=physical.before_size_bytes,
        new_size_bytes=physical.after_size_bytes,
        old_body_availability=(
            RepositoryBodyAvailability.UNAVAILABLE
            if old_path is None
            else RepositoryBodyAvailability.AVAILABLE
        ),
        new_body_availability=(
            RepositoryBodyAvailability.UNAVAILABLE
            if new_path is None
            else RepositoryBodyAvailability.AVAILABLE
        ),
    )
    evidence_key = f"mutation:{receipt_ref}"
    evidence = WorkspaceRepositoryChangeEvidence(
        evidence_ref=repository_change_evidence_ref(
            repository_binding_ref=binding_ref,
            evidence_key=evidence_key,
        ),
        evidence_key=evidence_key,
        revision=0,
        repository_binding_ref=binding_ref,
        posture=RepositoryEvidencePosture.WORKSPACE_AUTHORIZED,
        resolution_state=RepositoryEvidenceResolutionState.RESOLVED,
        observed_at=batch.observed_at,
        before_coordinate=before_coordinate,
        after_coordinate=after_coordinate,
        changed_entries=(changed_entry,),
        mutation_receipt_refs=(receipt_ref,),
        resolved_at=batch.observed_at,
    )
    return WorkspaceRepositoryAuthorizedMutation(receipt=receipt, evidence=evidence)


def _unapplied_result(
    *,
    request: WorkspaceRepositoryMutationRequest,
    binding_ref: str,
    receipt_ref: str,
    outcome: RepositoryMutationOutcome,
    error_code: str,
    physical: ConfinedFileMutationResult | None = None,
) -> WorkspaceRepositoryAuthorizedMutation:
    receipt = WorkspaceRepositoryMutationReceipt(
        mutation_receipt_ref=receipt_ref,
        repository_binding_ref=binding_ref,
        operation_ref=request.operation_ref,
        idempotency_key=request.idempotency_key,
        mutation_kind=request.mutation_kind,
        expected_coordinate=request.expected_coordinate,
        target_path=request.target_path,
        expected_exists=request.expected_exists,
        expected_content_digest=request.expected_content_digest,
        outcome=outcome,
        context_refs=request.context_refs,
        request_body_evidence_ref=(
            None
            if request.content is None
            else _body_ref(receipt_ref, "request", _content_digest(request.content))
        ),
        error_code=error_code,
        physical_effect=(None if physical is None else WorkspaceRepositoryPhysicalEffect(
            state=physical.effect_state.value,
            durability_confirmed=physical.durability_confirmed,
            before_exists=physical.before_exists,
            before_content_digest=physical.before_content_digest,
            before_size_bytes=physical.before_size_bytes,
            after_exists=physical.after_exists,
            after_content_digest=physical.after_content_digest,
            after_size_bytes=physical.after_size_bytes,
        )),
    )
    return WorkspaceRepositoryAuthorizedMutation(receipt=receipt, evidence=None)


def _failed_result(**kwargs) -> WorkspaceRepositoryAuthorizedMutation:
    return _unapplied_result(outcome=RepositoryMutationOutcome.FAILED, **kwargs)


def _physical_request(
    request: WorkspaceRepositoryMutationRequest,
) -> ConfinedFileMutationRequest:
    return ConfinedFileMutationRequest(
        kind=ConfinedMutationKind(request.mutation_kind.value),
        path=request.target_path,
        expected_exists=request.expected_exists,
        expected_content_digest=request.expected_content_digest,
        content=request.content,
        text_replacements=tuple(
            ConfinedTextReplacement(
                old_text=replacement.old_text,
                new_text=replacement.new_text,
            )
            for replacement in request.text_replacements
        ),
        maximum_bytes=request.maximum_bytes,
    )


def _converged(
    request: WorkspaceRepositoryMutationRequest,
    physical: ConfinedFileMutationResult,
    batch: WorkspaceRepositoryObservationBatch | None,
    after: WorkspaceRepositoryObservationSnapshot,
) -> bool:
    if batch is None:
        return False
    expected_kind = ObservationChangeKind(request.mutation_kind.value)
    changes = tuple(
        change
        for change in batch.changes
        if change.path == request.target_path and change.kind is expected_kind
    )
    if len(changes) != 1:
        return False
    entry = _entry_for(after, request.target_path)
    if request.mutation_kind is RepositoryMutationKind.DELETE:
        return entry is None
    return (
        entry is not None
        and entry.size_bytes == physical.after_size_bytes
        and (
            entry.content_digest is None
            or entry.content_digest == physical.after_content_digest
        )
    )


def _entry_for(
    snapshot: WorkspaceRepositoryObservationSnapshot, path: str
) -> RepositorySnapshotEntry | None:
    return next((entry for entry in snapshot.entries if entry.path == path), None)


def _coordinate(
    snapshot: WorkspaceRepositoryObservationSnapshot,
    session: WorkspaceRepositoryObservationSession,
) -> WorkspaceRepositoryEvidenceCoordinate:
    return _coordinate_from_snapshot(
        snapshot,
        _required(session.binding.binding_key, "repository_binding_ref"),
        session.binding.filter_version,
    )


def _coordinate_from_snapshot(
    snapshot: WorkspaceRepositoryObservationSnapshot,
    binding_ref: str,
    filter_version: str,
) -> WorkspaceRepositoryEvidenceCoordinate:
    observation = RepositoryObservationCoordinate(
        repository_binding_ref=binding_ref,
        epoch=snapshot.epoch,
        cursor=snapshot.cursor,
        snapshot_digest=snapshot.snapshot_digest,
        visibility_policy_ref=WORKSPACE_REPOSITORY_VISIBILITY_POLICY_REF,
        visibility_policy_version=filter_version,
    )
    return WorkspaceRepositoryEvidenceCoordinate(
        kind=RepositoryEvidenceCoordinateKind.OBSERVATION,
        repository_binding_ref=binding_ref,
        state_digest=snapshot.snapshot_digest,
        observation=observation,
    )


def _mutation_outcome(value: ConfinedMutationOutcome) -> RepositoryMutationOutcome:
    return {
        ConfinedMutationOutcome.CONFLICT: RepositoryMutationOutcome.CONFLICT,
        ConfinedMutationOutcome.DENIED: RepositoryMutationOutcome.DENIED,
        ConfinedMutationOutcome.FAILED: RepositoryMutationOutcome.FAILED,
    }[value]


def _request_fingerprint(
    request: WorkspaceRepositoryMutationRequest,
    *,
    confinement_profile: ConfinedMutationProfile = ConfinedMutationProfile.DESCRIPTOR_WALK_V1,
) -> str:
    if type(confinement_profile) is not ConfinedMutationProfile:
        raise TypeError("Workspace mutation confinement profile must be exact")
    legacy_fingerprint = _digest_ref(
        "workspace-repository-mutation-request",
        request.operation_ref,
        request.idempotency_key,
        request.mutation_kind.value,
        request.expected_coordinate.state_digest,
        str(request.expected_coordinate.observation),
        request.target_path,
        str(request.expected_exists),
        request.expected_content_digest or "",
        _content_digest(request.content) if request.content is not None else "",
        str(request.maximum_bytes),
        *(
            value
            for replacement in request.text_replacements
            for value in (replacement.old_text, replacement.new_text)
        ),
        *request.context_refs,
    )
    if confinement_profile is ConfinedMutationProfile.DESCRIPTOR_WALK_V1:
        return legacy_fingerprint
    # Preserve all V1 fingerprints, but prevent stronger-profile admission
    # from replaying a legacy success through either memory or durable metadata.
    return _digest_ref(
        "workspace-repository-mutation-request-profile",
        legacy_fingerprint,
        confinement_profile.value,
    )


def _maximum_result_size(
    request: WorkspaceRepositoryMutationRequest,
    snapshot_entry: RepositorySnapshotEntry | None,
) -> int:
    if request.content is not None:
        return len(request.content)
    if not request.text_replacements:
        return 0
    baseline_size = 0 if snapshot_entry is None else snapshot_entry.size_bytes
    growth = sum(
        max(
            0,
            len(replacement.new_text.encode("utf-8"))
            - len(replacement.old_text.encode("utf-8")),
        )
        for replacement in request.text_replacements
    )
    return baseline_size + growth


def _body_ref(receipt_ref: str, role: str, content_digest: str) -> str:
    return _digest_ref(
        "workspace-repository-body-evidence", receipt_ref, role, content_digest
    )


def _digest_ref(namespace: str, *values: str) -> str:
    digest = hashlib.sha256()
    for value in values:
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return f"{namespace}:sha256:{digest.hexdigest()}"


def _content_digest(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def _optional_digest(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if not normalized.startswith("sha256:") or len(normalized) != 71:
        raise ValueError("Expected content digest must be sha256-prefixed")
    if any(character not in "0123456789abcdef" for character in normalized[7:]):
        raise ValueError("Expected content digest must be hexadecimal")
    return normalized


def _relative_path(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("Mutation target path must be POSIX relative")
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value or ".." in path.parts:
        raise ValueError("Mutation target path must remain below root")
    return value


def _required(value: str | None, field_name: str) -> str:
    if value is None or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value.strip()
