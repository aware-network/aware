from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass, replace
from datetime import UTC, datetime

from .change_evidence import (
    RepositoryBodyAvailability,
    RepositoryChangedEntryKind,
    RepositoryEvidenceCoordinateKind,
    RepositoryEvidencePosture,
    RepositoryEvidenceResolutionState,
    RepositoryReportedChangeKind,
    WorkspaceRepositoryChangedEntry,
    WorkspaceRepositoryChangeEvidence,
    WorkspaceRepositoryEvidenceCheckpoint,
    WorkspaceRepositoryEvidenceCoordinate,
    WorkspaceRepositoryExternalEvidenceRef,
    WorkspaceRepositoryReportedChange,
    repository_change_evidence_ref,
    repository_changed_entry_ref,
    validate_repository_change_evidence_advance,
)
from .contracts import (
    ObservationChangeKind,
    RepositoryObservationChange,
    WorkspaceRepositoryObservationBatch,
)
from .observation import WorkspaceRepositoryObservationSession
from .repository_access import (
    WORKSPACE_REPOSITORY_VISIBILITY_POLICY_REF,
    RepositoryEntryKind,
    RepositoryObservationCoordinate,
    repository_entry_ref,
)

WORKSPACE_REPOSITORY_EVIDENCE_RESOLVER_STATE_REF = (
    "aware.workspace.repository-change-evidence-resolver-state.v1"
)
WORKSPACE_REPOSITORY_EVIDENCE_RESOLVER_STATE_VERSION = "1"
DEFAULT_EVIDENCE_RESOLVER_CAPACITY = 256
MAX_EVIDENCE_RESOLVER_CAPACITY = 4096


class WorkspaceRepositoryEvidenceResolverError(RuntimeError):
    pass


class WorkspaceRepositoryEvidenceResolverStateError(
    WorkspaceRepositoryEvidenceResolverError
):
    pass


class WorkspaceRepositoryEvidenceResetRequired(
    WorkspaceRepositoryEvidenceResolverError
):
    pass


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryObservedEvidence:
    evidence: WorkspaceRepositoryChangeEvidence
    coalesced: bool = False

    def __post_init__(self) -> None:
        if self.evidence.posture not in {
            RepositoryEvidencePosture.WORKSPACE_OBSERVED,
            RepositoryEvidencePosture.GAP,
        }:
            raise ValueError("Observer projection must be observed or gap evidence")


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryExternalResolution:
    external_evidence: WorkspaceRepositoryExternalEvidenceRef
    evidence: WorkspaceRepositoryChangeEvidence

    def __post_init__(self) -> None:
        if (
            self.external_evidence.evidence_ref
            not in self.evidence.external_evidence_refs
        ):
            raise ValueError(
                "External resolution does not retain its provider evidence ref"
            )
        if self.evidence.posture not in {
            RepositoryEvidencePosture.PROVIDER_REPORTED,
            RepositoryEvidencePosture.PROVIDER_CORRELATED,
            RepositoryEvidencePosture.AMBIGUOUS,
            RepositoryEvidencePosture.GAP,
        }:
            raise ValueError("Resolver external evidence posture is unsupported")


@dataclass(frozen=True, slots=True)
class WorkspaceRepositoryEvidenceResolverState:
    consumer_key: str
    repository_binding_ref: str
    evidence_capacity: int
    checkpoint: WorkspaceRepositoryEvidenceCheckpoint | None
    observed_evidence: tuple[WorkspaceRepositoryObservedEvidence, ...] = ()
    external_resolutions: tuple[WorkspaceRepositoryExternalResolution, ...] = ()
    history_truncated: bool = False
    contract_ref: str = WORKSPACE_REPOSITORY_EVIDENCE_RESOLVER_STATE_REF
    contract_version: str = WORKSPACE_REPOSITORY_EVIDENCE_RESOLVER_STATE_VERSION

    def __post_init__(self) -> None:
        consumer_key = _required(self.consumer_key, "consumer_key")
        binding_ref = _required(self.repository_binding_ref, "repository_binding_ref")
        _capacity(self.evidence_capacity)
        if self.contract_ref != WORKSPACE_REPOSITORY_EVIDENCE_RESOLVER_STATE_REF:
            raise ValueError("Resolver state contract ref is unsupported")
        if (
            self.contract_version
            != WORKSPACE_REPOSITORY_EVIDENCE_RESOLVER_STATE_VERSION
        ):
            raise ValueError("Resolver state contract version is unsupported")
        observed = tuple(self.observed_evidence)
        resolutions = tuple(self.external_resolutions)
        if (
            len(observed) > self.evidence_capacity
            or len(resolutions) > self.evidence_capacity
        ):
            raise ValueError("Resolver state exceeds configured evidence capacity")
        observed_refs = tuple(value.evidence.evidence_ref for value in observed)
        external_refs = tuple(
            value.external_evidence.evidence_ref for value in resolutions
        )
        if len(observed_refs) != len(set(observed_refs)):
            raise ValueError("Resolver observed evidence refs must be unique")
        if len(external_refs) != len(set(external_refs)):
            raise ValueError("Resolver external evidence refs must be unique")
        for value in observed:
            if value.evidence.repository_binding_ref != binding_ref:
                raise ValueError("Resolver observed evidence binding differs")
        for value in resolutions:
            if value.evidence.repository_binding_ref != binding_ref:
                raise ValueError("Resolver external evidence binding differs")
        checkpoint = self.checkpoint
        if checkpoint is None and (observed or resolutions or self.history_truncated):
            raise ValueError("Resolver evidence state requires a checkpoint")
        if checkpoint is not None:
            if checkpoint.consumer_key != consumer_key:
                raise ValueError("Resolver checkpoint consumer differs")
            if checkpoint.repository_binding_ref != binding_ref:
                raise ValueError("Resolver checkpoint binding differs")
            expected_digest = repository_evidence_projection_digest(
                consumer_key=consumer_key,
                repository_binding_ref=binding_ref,
                observer_epoch=checkpoint.observer_epoch,
                accepted_cursor=checkpoint.accepted_cursor,
                evidence_revision=checkpoint.evidence_revision,
                reset_required=checkpoint.reset_required,
                observed_evidence=observed,
                external_resolutions=resolutions,
                history_truncated=self.history_truncated,
            )
            if checkpoint.projection_digest != expected_digest:
                raise ValueError("Resolver state projection digest differs")
        object.__setattr__(self, "consumer_key", consumer_key)
        object.__setattr__(self, "repository_binding_ref", binding_ref)
        object.__setattr__(self, "observed_evidence", observed)
        object.__setattr__(self, "external_resolutions", resolutions)


class WorkspaceRepositoryChangeEvidenceResolver:
    """Bounded evidence projection over one injected observation session."""

    def __init__(
        self,
        *,
        session: WorkspaceRepositoryObservationSession,
        consumer_key: str,
        evidence_capacity: int = DEFAULT_EVIDENCE_RESOLVER_CAPACITY,
        restored_state: WorkspaceRepositoryEvidenceResolverState | None = None,
    ) -> None:
        self._session = session
        self._consumer_key = _required(consumer_key, "consumer_key")
        self._binding_ref = _required(
            session.binding.binding_key, "repository_binding_ref"
        )
        _capacity(evidence_capacity)
        self._evidence_capacity = evidence_capacity
        self._lock = asyncio.Lock()
        self._checkpoint: WorkspaceRepositoryEvidenceCheckpoint | None = None
        self._observed: list[WorkspaceRepositoryObservedEvidence] = []
        self._external: dict[str, WorkspaceRepositoryExternalResolution] = {}
        self._history_truncated = False
        self._evidence_revision = 0
        if restored_state is not None:
            self._restore(restored_state)

    @property
    def consumer_key(self) -> str:
        return self._consumer_key

    @property
    def repository_binding_ref(self) -> str:
        return self._binding_ref

    @property
    def session(self) -> WorkspaceRepositoryObservationSession:
        return self._session

    @property
    def checkpoint(self) -> WorkspaceRepositoryEvidenceCheckpoint | None:
        return self._checkpoint

    @property
    def observed_evidence(self) -> tuple[WorkspaceRepositoryObservedEvidence, ...]:
        return tuple(self._observed)

    @property
    def external_resolutions(
        self,
    ) -> tuple[WorkspaceRepositoryExternalResolution, ...]:
        return tuple(self._external.values())

    def retained_external_resolution(
        self, evidence_ref: str
    ) -> WorkspaceRepositoryExternalResolution | None:
        """Resolve one retained Workspace evidence identity without body I/O."""

        exact_ref = _required(evidence_ref, "evidence_ref")
        matches = tuple(
            value
            for value in self._external.values()
            if value.evidence.evidence_ref == exact_ref
        )
        if len(matches) > 1:
            raise WorkspaceRepositoryEvidenceResolverStateError(
                "Resolver retained duplicate Workspace evidence identities"
            )
        return matches[0] if matches else None

    def snapshot_state(self) -> WorkspaceRepositoryEvidenceResolverState:
        return WorkspaceRepositoryEvidenceResolverState(
            consumer_key=self._consumer_key,
            repository_binding_ref=self._binding_ref,
            evidence_capacity=self._evidence_capacity,
            checkpoint=self._checkpoint,
            observed_evidence=tuple(self._observed),
            external_resolutions=tuple(self._external.values()),
            history_truncated=self._history_truncated,
        )

    async def refresh(
        self, *, wait_timeout: float | None = None
    ) -> tuple[WorkspaceRepositoryChangeEvidence, ...]:
        async with self._lock:
            return await self._refresh_locked(wait_timeout=wait_timeout)

    async def correlate_external(
        self,
        external_evidence: WorkspaceRepositoryExternalEvidenceRef,
        *,
        wait_timeout: float | None = None,
    ) -> WorkspaceRepositoryChangeEvidence:
        async with self._lock:
            existing = self._external.get(external_evidence.evidence_ref)
            if existing is not None and existing.external_evidence != external_evidence:
                raise WorkspaceRepositoryEvidenceResolverStateError(
                    "External evidence ref cannot change its source contract"
                )
            await self._refresh_locked(wait_timeout=wait_timeout)
            self._ensure_reset_accepted()
            candidate = self._resolve_external(
                external_evidence,
                previous=None if existing is None else existing.evidence,
            )
            if existing is not None and _same_evidence_projection(
                existing.evidence, candidate
            ):
                return existing.evidence
            if existing is not None:
                validate_repository_change_evidence_advance(
                    existing.evidence, candidate
                )
            self._external[external_evidence.evidence_ref] = (
                WorkspaceRepositoryExternalResolution(
                    external_evidence=external_evidence,
                    evidence=candidate,
                )
            )
            if len(self._external) > self._evidence_capacity:
                self._external.pop(next(iter(self._external)))
            self._evidence_revision += 1
            self._write_checkpoint(
                observer_epoch=self._session.current_snapshot.epoch,
                accepted_cursor=self._session.current_snapshot.cursor,
                reset_required=False,
            )
            return candidate

    async def accept_reset(self) -> WorkspaceRepositoryEvidenceCheckpoint:
        async with self._lock:
            checkpoint = self._checkpoint
            if checkpoint is None or not checkpoint.reset_required:
                raise WorkspaceRepositoryEvidenceResolverStateError(
                    "Resolver has no pending evidence reset"
                )
            self._write_checkpoint(
                observer_epoch=checkpoint.observer_epoch,
                accepted_cursor=checkpoint.accepted_cursor,
                reset_required=False,
            )
            return _require_checkpoint(self._checkpoint)

    async def _refresh_locked(
        self, *, wait_timeout: float | None
    ) -> tuple[WorkspaceRepositoryChangeEvidence, ...]:
        self._ensure_reset_accepted()
        checkpoint = self._checkpoint
        requested_epoch = (
            checkpoint.observer_epoch if checkpoint is not None else self._session.epoch
        )
        after_cursor = checkpoint.accepted_cursor if checkpoint is not None else 0
        replay = await self._session.replay(
            after_cursor=after_cursor,
            epoch=requested_epoch,
            wait_timeout=wait_timeout,
        )
        if replay.gap is not None:
            gap = replay.gap
            self._observed.clear()
            self._external.clear()
            self._history_truncated = True
            evidence = _gap_evidence(
                consumer_key=self._consumer_key,
                binding_ref=self._binding_ref,
                available_epoch=gap.available_epoch,
                requested_epoch=gap.requested_epoch,
                requested_after_cursor=gap.requested_after_cursor,
                current_cursor=gap.current_cursor,
                reason=gap.reason.value,
                observed_at=gap.reset_snapshot.observed_at,
            )
            self._append_observed(
                WorkspaceRepositoryObservedEvidence(evidence=evidence)
            )
            self._evidence_revision += 1
            self._write_checkpoint(
                observer_epoch=gap.available_epoch,
                accepted_cursor=gap.current_cursor,
                reset_required=True,
            )
            return (evidence,)

        projected: list[WorkspaceRepositoryChangeEvidence] = []
        for batch in replay.batches:
            evidence = _observed_evidence(batch)
            self._append_observed(
                WorkspaceRepositoryObservedEvidence(
                    evidence=evidence,
                    coalesced=batch.coalesced,
                )
            )
            self._evidence_revision += 1
            projected.append(evidence)
        if checkpoint is None or replay.batches:
            self._write_checkpoint(
                observer_epoch=replay.epoch,
                accepted_cursor=replay.current_cursor,
                reset_required=False,
            )
        return tuple(projected)

    def _append_observed(self, value: WorkspaceRepositoryObservedEvidence) -> None:
        if any(
            item.evidence.evidence_ref == value.evidence.evidence_ref
            for item in self._observed
        ):
            raise WorkspaceRepositoryEvidenceResolverStateError(
                "Observation replay emitted duplicate evidence"
            )
        self._observed.append(value)
        if len(self._observed) > self._evidence_capacity:
            self._observed.pop(0)
            self._history_truncated = True

    def _resolve_external(
        self,
        external: WorkspaceRepositoryExternalEvidenceRef,
        *,
        previous: WorkspaceRepositoryChangeEvidence | None,
    ) -> WorkspaceRepositoryChangeEvidence:
        revision = 0 if previous is None else previous.revision + 1
        evidence_key = f"external:{external.evidence_ref}"
        common = {
            "evidence_ref": repository_change_evidence_ref(
                repository_binding_ref=self._binding_ref,
                evidence_key=evidence_key,
            ),
            "evidence_key": evidence_key,
            "revision": revision,
            "repository_binding_ref": self._binding_ref,
            "observed_at": external.observed_at,
            "external_evidence_refs": (external.evidence_ref,),
        }
        if (
            external.correlation_started_at is None
            or external.correlation_ended_at is None
            or not external.changes
        ):
            return WorkspaceRepositoryChangeEvidence(
                **common,
                posture=RepositoryEvidencePosture.PROVIDER_REPORTED,
                resolution_state=RepositoryEvidenceResolutionState.REPORTED,
            )
        candidates = tuple(
            item
            for item in self._observed
            if item.evidence.posture is RepositoryEvidencePosture.WORKSPACE_OBSERVED
            and external.correlation_started_at
            <= item.evidence.observed_at
            <= external.correlation_ended_at
            and _changes_match(external.changes, item.evidence.changed_entries)
        )
        if previous is not None and previous.posture in {
            RepositoryEvidencePosture.AMBIGUOUS,
            RepositoryEvidencePosture.PROVIDER_CORRELATED,
        }:
            previous_coordinate = previous.after_coordinate
            if previous.posture is RepositoryEvidencePosture.AMBIGUOUS:
                return previous
            if (
                previous_coordinate is not None
                and any(
                    item.evidence.after_coordinate == previous_coordinate
                    for item in candidates
                )
                and len(candidates) == 1
            ):
                return previous
        if len(candidates) == 1 and not candidates[0].coalesced:
            observed = candidates[0].evidence
            entries = tuple(
                replace(
                    item,
                    posture=RepositoryEvidencePosture.PROVIDER_CORRELATED,
                )
                for item in observed.changed_entries
            )
            return WorkspaceRepositoryChangeEvidence(
                **common,
                posture=RepositoryEvidencePosture.PROVIDER_CORRELATED,
                resolution_state=RepositoryEvidenceResolutionState.RESOLVED,
                before_coordinate=observed.before_coordinate,
                after_coordinate=observed.after_coordinate,
                changed_entries=entries,
                resolved_at=datetime.now(UTC),
            )
        if candidates:
            reason = (
                "matching observer batch is coalesced"
                if len(candidates) == 1
                else f"{len(candidates)} observer batches match the external interval"
            )
            return WorkspaceRepositoryChangeEvidence(
                **common,
                posture=RepositoryEvidencePosture.AMBIGUOUS,
                resolution_state=RepositoryEvidenceResolutionState.AMBIGUOUS,
                reason=reason,
                resolved_at=datetime.now(UTC),
            )
        if self._external_window_may_be_truncated(external):
            return WorkspaceRepositoryChangeEvidence(
                **common,
                posture=RepositoryEvidencePosture.GAP,
                resolution_state=RepositoryEvidenceResolutionState.GAP,
                reason="observer evidence retention does not cover the external interval",
                resolved_at=datetime.now(UTC),
            )
        return WorkspaceRepositoryChangeEvidence(
            **common,
            posture=RepositoryEvidencePosture.PROVIDER_REPORTED,
            resolution_state=RepositoryEvidenceResolutionState.REPORTED,
        )

    def _external_window_may_be_truncated(
        self, external: WorkspaceRepositoryExternalEvidenceRef
    ) -> bool:
        if not self._history_truncated or external.correlation_ended_at is None:
            return False
        observed = tuple(
            item.evidence.observed_at
            for item in self._observed
            if item.evidence.posture is RepositoryEvidencePosture.WORKSPACE_OBSERVED
        )
        if not observed:
            return (
                external.correlation_ended_at
                <= self._session.current_snapshot.observed_at
            )
        return external.correlation_ended_at < min(observed)

    def _write_checkpoint(
        self,
        *,
        observer_epoch: str,
        accepted_cursor: int,
        reset_required: bool,
    ) -> None:
        digest = repository_evidence_projection_digest(
            consumer_key=self._consumer_key,
            repository_binding_ref=self._binding_ref,
            observer_epoch=observer_epoch,
            accepted_cursor=accepted_cursor,
            evidence_revision=self._evidence_revision,
            reset_required=reset_required,
            observed_evidence=tuple(self._observed),
            external_resolutions=tuple(self._external.values()),
            history_truncated=self._history_truncated,
        )
        observer_checkpoint = self._session.acknowledge(
            consumer_key=self._consumer_key,
            epoch=observer_epoch,
            cursor=accepted_cursor,
            projection_digest=digest,
        )
        self._checkpoint = WorkspaceRepositoryEvidenceCheckpoint(
            consumer_key=self._consumer_key,
            repository_binding_ref=self._binding_ref,
            observer_epoch=observer_checkpoint.epoch,
            accepted_cursor=observer_checkpoint.cursor,
            evidence_revision=self._evidence_revision,
            projection_digest=digest,
            accepted_at=observer_checkpoint.accepted_at,
            reset_required=reset_required,
        )

    def _restore(self, state: WorkspaceRepositoryEvidenceResolverState) -> None:
        if state.consumer_key != self._consumer_key:
            raise WorkspaceRepositoryEvidenceResolverStateError(
                "Restored resolver consumer differs"
            )
        if state.repository_binding_ref != self._binding_ref:
            raise WorkspaceRepositoryEvidenceResolverStateError(
                "Restored resolver binding differs"
            )
        if state.evidence_capacity != self._evidence_capacity:
            raise WorkspaceRepositoryEvidenceResolverStateError(
                "Restored resolver capacity differs"
            )
        self._checkpoint = state.checkpoint
        self._observed = list(state.observed_evidence)
        self._external = {
            value.external_evidence.evidence_ref: value
            for value in state.external_resolutions
        }
        self._history_truncated = state.history_truncated
        self._evidence_revision = (
            0 if state.checkpoint is None else state.checkpoint.evidence_revision
        )

    def _ensure_reset_accepted(self) -> None:
        if self._checkpoint is not None and self._checkpoint.reset_required:
            raise WorkspaceRepositoryEvidenceResetRequired(
                "Resolver evidence reset must be accepted before continuing"
            )


def repository_evidence_projection_digest(
    *,
    consumer_key: str,
    repository_binding_ref: str,
    observer_epoch: str,
    accepted_cursor: int,
    evidence_revision: int,
    reset_required: bool,
    observed_evidence: tuple[WorkspaceRepositoryObservedEvidence, ...],
    external_resolutions: tuple[WorkspaceRepositoryExternalResolution, ...],
    history_truncated: bool,
) -> str:
    digest = hashlib.sha256()
    values = (
        _required(consumer_key, "consumer_key"),
        _required(repository_binding_ref, "repository_binding_ref"),
        _required(observer_epoch, "observer_epoch"),
        str(accepted_cursor),
        str(evidence_revision),
        str(reset_required),
        str(history_truncated),
        *(
            f"{item.evidence.evidence_ref}@{item.evidence.revision}:{item.coalesced}"
            for item in observed_evidence
        ),
        *(
            f"{item.evidence.evidence_ref}@{item.evidence.revision}"
            for item in external_resolutions
        ),
    )
    for value in values:
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return f"workspace-repository-evidence-projection:sha256:{digest.hexdigest()}"


def _observed_evidence(
    batch: WorkspaceRepositoryObservationBatch,
) -> WorkspaceRepositoryChangeEvidence:
    before = _observation_coordinate(
        binding_ref=batch.binding_key,
        epoch=batch.epoch,
        cursor=batch.cursor - 1,
        snapshot_digest=batch.before_snapshot_digest,
    )
    after = _observation_coordinate(
        binding_ref=batch.binding_key,
        epoch=batch.epoch,
        cursor=batch.cursor,
        snapshot_digest=batch.after_snapshot_digest,
    )
    entries = tuple(
        _changed_entry(batch, before, after, item) for item in batch.changes
    )
    evidence_key = f"observation:{batch.epoch}:{batch.cursor}"
    return WorkspaceRepositoryChangeEvidence(
        evidence_ref=repository_change_evidence_ref(
            repository_binding_ref=batch.binding_key,
            evidence_key=evidence_key,
        ),
        evidence_key=evidence_key,
        revision=0,
        repository_binding_ref=batch.binding_key,
        posture=RepositoryEvidencePosture.WORKSPACE_OBSERVED,
        resolution_state=RepositoryEvidenceResolutionState.RESOLVED,
        observed_at=batch.observed_at,
        before_coordinate=before,
        after_coordinate=after,
        changed_entries=entries,
        resolved_at=batch.observed_at,
    )


def _changed_entry(
    batch: WorkspaceRepositoryObservationBatch,
    before: WorkspaceRepositoryEvidenceCoordinate,
    after: WorkspaceRepositoryEvidenceCoordinate,
    change: RepositoryObservationChange,
) -> WorkspaceRepositoryChangedEntry:
    kind = {
        ObservationChangeKind.CREATE: RepositoryChangedEntryKind.CREATE,
        ObservationChangeKind.UPDATE: RepositoryChangedEntryKind.UPDATE,
        ObservationChangeKind.DELETE: RepositoryChangedEntryKind.DELETE,
    }[change.kind]
    old_path = None if change.kind is ObservationChangeKind.CREATE else change.path
    new_path = None if change.kind is ObservationChangeKind.DELETE else change.path
    target = change.entry
    old_entry_ref = (
        None
        if old_path is None
        else repository_entry_ref(
            binding_ref=batch.binding_key,
            snapshot_digest=batch.before_snapshot_digest,
            path=old_path,
            kind=RepositoryEntryKind.REGULAR_FILE,
        )
    )
    new_entry_ref = (
        None
        if new_path is None
        else repository_entry_ref(
            binding_ref=batch.binding_key,
            snapshot_digest=batch.after_snapshot_digest,
            path=new_path,
            kind=RepositoryEntryKind.REGULAR_FILE,
        )
    )
    return WorkspaceRepositoryChangedEntry(
        changed_entry_ref=repository_changed_entry_ref(
            repository_binding_ref=batch.binding_key,
            before_coordinate=before,
            after_coordinate=after,
            kind=kind,
            old_path=old_path,
            new_path=new_path,
        ),
        kind=kind,
        posture=RepositoryEvidencePosture.WORKSPACE_OBSERVED,
        before_coordinate=before,
        after_coordinate=after,
        old_path=old_path,
        new_path=new_path,
        old_entry_ref=old_entry_ref,
        new_entry_ref=new_entry_ref,
        old_content_digest=None,
        new_content_digest=None if target is None else target.content_digest,
        old_size_bytes=None,
        new_size_bytes=None if target is None else target.size_bytes,
        old_body_availability=(
            RepositoryBodyAvailability.UNAVAILABLE
            if old_path is None
            else RepositoryBodyAvailability.MISSING_PREIMAGE
        ),
        new_body_availability=RepositoryBodyAvailability.UNAVAILABLE,
    )


def _observation_coordinate(
    *, binding_ref: str, epoch: str, cursor: int, snapshot_digest: str
) -> WorkspaceRepositoryEvidenceCoordinate:
    observation = RepositoryObservationCoordinate(
        repository_binding_ref=binding_ref,
        epoch=epoch,
        cursor=cursor,
        snapshot_digest=snapshot_digest,
        visibility_policy_ref=WORKSPACE_REPOSITORY_VISIBILITY_POLICY_REF,
        visibility_policy_version="canonical-source-v1",
    )
    return WorkspaceRepositoryEvidenceCoordinate(
        kind=RepositoryEvidenceCoordinateKind.OBSERVATION,
        repository_binding_ref=binding_ref,
        state_digest=snapshot_digest,
        observation=observation,
    )


def _gap_evidence(
    *,
    consumer_key: str,
    binding_ref: str,
    available_epoch: str,
    requested_epoch: str | None,
    requested_after_cursor: int,
    current_cursor: int,
    reason: str,
    observed_at: datetime,
) -> WorkspaceRepositoryChangeEvidence:
    evidence_key = ":".join(
        (
            "observer-gap",
            consumer_key,
            requested_epoch or "none",
            available_epoch,
            str(requested_after_cursor),
            str(current_cursor),
        )
    )
    return WorkspaceRepositoryChangeEvidence(
        evidence_ref=repository_change_evidence_ref(
            repository_binding_ref=binding_ref,
            evidence_key=evidence_key,
        ),
        evidence_key=evidence_key,
        revision=0,
        repository_binding_ref=binding_ref,
        posture=RepositoryEvidencePosture.GAP,
        resolution_state=RepositoryEvidenceResolutionState.GAP,
        observed_at=observed_at,
        reason=f"observation replay gap: {reason}",
        resolved_at=observed_at,
    )


def _changes_match(
    reported: tuple[WorkspaceRepositoryReportedChange, ...],
    observed: tuple[WorkspaceRepositoryChangedEntry, ...],
) -> bool:
    return all(_reported_change_matches(item, observed) for item in reported)


def _reported_change_matches(
    reported: WorkspaceRepositoryReportedChange,
    observed: tuple[WorkspaceRepositoryChangedEntry, ...],
) -> bool:
    if reported.kind is RepositoryReportedChangeKind.RENAME:
        return any(
            item.kind is RepositoryChangedEntryKind.DELETE
            and item.old_path == reported.path
            for item in observed
        ) and any(
            item.kind is RepositoryChangedEntryKind.CREATE
            and item.new_path == reported.new_path
            for item in observed
        )
    candidates = tuple(
        item for item in observed if reported.path in {item.old_path, item.new_path}
    )
    if reported.kind in {
        RepositoryReportedChangeKind.UNKNOWN,
        RepositoryReportedChangeKind.BINARY,
    }:
        return bool(candidates)
    expected = {
        RepositoryReportedChangeKind.CREATE: RepositoryChangedEntryKind.CREATE,
        RepositoryReportedChangeKind.UPDATE: RepositoryChangedEntryKind.UPDATE,
        RepositoryReportedChangeKind.DELETE: RepositoryChangedEntryKind.DELETE,
    }[reported.kind]
    return any(item.kind is expected for item in candidates)


def _same_evidence_projection(
    first: WorkspaceRepositoryChangeEvidence,
    second: WorkspaceRepositoryChangeEvidence,
) -> bool:
    return (
        replace(first, revision=second.revision, resolved_at=second.resolved_at)
        == second
    )


def _capacity(value: int) -> None:
    if isinstance(value, bool) or not 0 < value <= MAX_EVIDENCE_RESOLVER_CAPACITY:
        raise ValueError("Resolver evidence capacity must be positive and bounded")


def _required(value: str | None, field_name: str) -> str:
    if value is None or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value.strip()


def _require_checkpoint(
    value: WorkspaceRepositoryEvidenceCheckpoint | None,
) -> WorkspaceRepositoryEvidenceCheckpoint:
    if value is None:
        raise AssertionError("Resolver checkpoint was not written")
    return value
