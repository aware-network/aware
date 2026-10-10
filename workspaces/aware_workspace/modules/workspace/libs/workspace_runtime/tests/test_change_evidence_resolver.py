from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from aware_workspace_runtime import (
    ObservationChangeKind,
    RepositoryBodyAvailability,
    RepositoryChangedEntryKind,
    RepositoryEvidencePosture,
    RepositoryObservationChange,
    RepositoryProviderObservation,
    RepositoryReportedChangeKind,
    RepositorySnapshotEntry,
    WorkspaceRepositoryBinding,
    WorkspaceRepositoryChangeEvidenceResolver,
    WorkspaceRepositoryEvidenceResetRequired,
    WorkspaceRepositoryEvidenceResolverState,
    WorkspaceRepositoryEvidenceResolverStateError,
    WorkspaceRepositoryExternalEvidenceRef,
    WorkspaceRepositoryObservationSession,
    WorkspaceRepositoryReportedChange,
    repository_evidence_projection_digest,
)

START = datetime(2026, 8, 22, 4, 40, tzinfo=UTC)


class FakeProvider:
    def __init__(self, root_path: Path, initial: RepositoryProviderObservation) -> None:
        self._root_path = root_path.resolve()
        self.initial = initial
        self.polls: deque[RepositoryProviderObservation] = deque()
        self.initialize_calls = 0
        self.poll_calls = 0

    @property
    def root_path(self) -> Path:
        return self._root_path

    async def initialize(self) -> RepositoryProviderObservation:
        self.initialize_calls += 1
        return self.initial

    async def poll(self) -> RepositoryProviderObservation:
        self.poll_calls += 1
        return self.polls.popleft()


def _entry(path: str, version: int) -> RepositorySnapshotEntry:
    return RepositorySnapshotEntry(
        path=path,
        size_bytes=version,
        modified_ns=version,
        content_digest=f"content:{path}:{version}",
    )


def _observation(
    observed_at: datetime,
    entries: tuple[RepositorySnapshotEntry, ...],
    changes: tuple[RepositoryObservationChange, ...] = (),
) -> RepositoryProviderObservation:
    return RepositoryProviderObservation(
        observed_at=observed_at,
        entries=entries,
        changes=changes,
    )


def _create(entry: RepositorySnapshotEntry) -> RepositoryObservationChange:
    return RepositoryObservationChange(
        kind=ObservationChangeKind.CREATE,
        path=entry.path,
        entry=entry,
    )


def _update(entry: RepositorySnapshotEntry) -> RepositoryObservationChange:
    return RepositoryObservationChange(
        kind=ObservationChangeKind.UPDATE,
        path=entry.path,
        entry=entry,
    )


def _delete(path: str) -> RepositoryObservationChange:
    return RepositoryObservationChange(
        kind=ObservationChangeKind.DELETE,
        path=path,
    )


def _external(
    *,
    evidence_ref: str,
    path: str,
    kind: RepositoryReportedChangeKind,
    started_at: datetime | None = START,
    ended_at: datetime | None = START + timedelta(seconds=10),
    new_path: str | None = None,
) -> WorkspaceRepositoryExternalEvidenceRef:
    return WorkspaceRepositoryExternalEvidenceRef(
        evidence_ref=evidence_ref,
        source_namespace="codex.app-server",
        source_contract_version="2026-08-22",
        observed_at=START,
        changes=(
            WorkspaceRepositoryReportedChange(
                path=path,
                kind=kind,
                new_path=new_path,
            ),
        ),
        context_refs=("agent-session:1", "issue:42"),
        correlation_started_at=started_at,
        correlation_ended_at=ended_at,
    )


async def _session(
    tmp_path: Path,
    *,
    initial_entries: tuple[RepositorySnapshotEntry, ...] = (),
    journal_capacity: int = 8,
) -> tuple[WorkspaceRepositoryObservationSession, FakeProvider]:
    provider = FakeProvider(tmp_path, _observation(START, initial_entries))
    session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path),
        provider=provider,
        journal_capacity=journal_capacity,
    )
    await session.start(background=False)
    return session, provider


@pytest.mark.asyncio
async def test_observation_batches_project_exact_coordinates_and_honest_entries(
    tmp_path: Path,
) -> None:
    initial = _entry("old.txt", 1)
    session, provider = await _session(tmp_path, initial_entries=(initial,))
    updated = _entry("old.txt", 2)
    created = _entry("new.txt", 1)
    provider.polls.append(
        _observation(
            START + timedelta(seconds=1),
            (updated, created),
            (_update(updated), _create(created)),
        )
    )
    await session.poll_once()
    resolver = WorkspaceRepositoryChangeEvidenceResolver(
        session=session,
        consumer_key="issue-evidence",
    )

    projected = await resolver.refresh()

    assert len(projected) == 1
    evidence = projected[0]
    assert evidence.posture is RepositoryEvidencePosture.WORKSPACE_OBSERVED
    assert evidence.before_coordinate is not None
    assert evidence.after_coordinate is not None
    assert evidence.before_coordinate.observation.cursor == 0
    assert evidence.after_coordinate.observation.cursor == 1
    assert [item.kind for item in evidence.changed_entries] == [
        RepositoryChangedEntryKind.CREATE,
        RepositoryChangedEntryKind.UPDATE,
    ]
    update = next(
        item
        for item in evidence.changed_entries
        if item.kind is RepositoryChangedEntryKind.UPDATE
    )
    assert update.old_content_digest is None
    assert update.old_body_availability is RepositoryBodyAvailability.MISSING_PREIMAGE
    assert update.new_content_digest == "content:old.txt:2"
    assert resolver.checkpoint is not None
    assert resolver.checkpoint.accepted_cursor == 1
    assert provider.poll_calls == 1
    await session.stop()


@pytest.mark.asyncio
async def test_bounded_provider_report_advances_to_correlation_but_never_authority(
    tmp_path: Path,
) -> None:
    session, provider = await _session(tmp_path)
    resolver = WorkspaceRepositoryChangeEvidenceResolver(
        session=session,
        consumer_key="agent-evidence",
    )
    external = _external(
        evidence_ref="codex:file-change:1",
        path="src/main.py",
        kind=RepositoryReportedChangeKind.CREATE,
    )

    reported = await resolver.correlate_external(external)
    assert reported.posture is RepositoryEvidencePosture.PROVIDER_REPORTED
    created = _entry("src/main.py", 1)
    provider.polls.append(
        _observation(
            START + timedelta(seconds=2),
            (created,),
            (_create(created),),
        )
    )
    await session.poll_once()

    correlated = await resolver.correlate_external(external)
    assert correlated.posture is RepositoryEvidencePosture.PROVIDER_CORRELATED
    assert correlated.revision == 1
    assert correlated.external_evidence_refs == (external.evidence_ref,)
    assert correlated.mutation_receipt_refs == ()
    assert all(
        item.posture is RepositoryEvidencePosture.PROVIDER_CORRELATED
        for item in correlated.changed_entries
    )
    assert await resolver.correlate_external(external) == correlated
    await session.stop()


@pytest.mark.asyncio
async def test_path_without_interval_or_change_shape_is_only_provider_reported(
    tmp_path: Path,
) -> None:
    session, provider = await _session(tmp_path)
    created = _entry("same.txt", 1)
    provider.polls.append(
        _observation(
            START + timedelta(seconds=1),
            (created,),
            (_create(created),),
        )
    )
    await session.poll_once()
    resolver = WorkspaceRepositoryChangeEvidenceResolver(
        session=session,
        consumer_key="bounded-correlation",
    )
    without_interval = _external(
        evidence_ref="provider:no-window",
        path="same.txt",
        kind=RepositoryReportedChangeKind.CREATE,
        started_at=None,
        ended_at=None,
    )
    wrong_kind = _external(
        evidence_ref="provider:wrong-kind",
        path="same.txt",
        kind=RepositoryReportedChangeKind.DELETE,
    )

    assert (
        await resolver.correlate_external(without_interval)
    ).posture is RepositoryEvidencePosture.PROVIDER_REPORTED
    assert (
        await resolver.correlate_external(wrong_kind)
    ).posture is RepositoryEvidencePosture.PROVIDER_REPORTED
    await session.stop()


@pytest.mark.asyncio
async def test_multiple_batches_and_coalesced_batch_remain_ambiguous(
    tmp_path: Path,
) -> None:
    session, provider = await _session(tmp_path)
    first = _entry("shared.txt", 1)
    second = _entry("shared.txt", 2)
    provider.polls.extend(
        (
            _observation(
                START + timedelta(seconds=1),
                (first,),
                (_create(first),),
            ),
            _observation(
                START + timedelta(seconds=2),
                (second,),
                (_update(second),),
            ),
        )
    )
    await session.poll_once()
    await session.poll_once()
    resolver = WorkspaceRepositoryChangeEvidenceResolver(
        session=session,
        consumer_key="ambiguous",
    )
    await resolver.refresh()
    unknown = _external(
        evidence_ref="provider:ambiguous",
        path="shared.txt",
        kind=RepositoryReportedChangeKind.UNKNOWN,
    )
    assert (
        await resolver.correlate_external(unknown)
    ).posture is RepositoryEvidencePosture.AMBIGUOUS

    base_state = resolver.snapshot_state()
    assert base_state.checkpoint is not None
    coalesced = (replace(base_state.observed_evidence[-1], coalesced=True),)
    checkpoint = replace(
        base_state.checkpoint,
        projection_digest=repository_evidence_projection_digest(
            consumer_key=base_state.consumer_key,
            repository_binding_ref=base_state.repository_binding_ref,
            observer_epoch=base_state.checkpoint.observer_epoch,
            accepted_cursor=base_state.checkpoint.accepted_cursor,
            evidence_revision=base_state.checkpoint.evidence_revision,
            reset_required=base_state.checkpoint.reset_required,
            observed_evidence=coalesced,
            external_resolutions=(),
            history_truncated=False,
        ),
    )
    state = WorkspaceRepositoryEvidenceResolverState(
        consumer_key=base_state.consumer_key,
        repository_binding_ref=base_state.repository_binding_ref,
        evidence_capacity=base_state.evidence_capacity,
        checkpoint=checkpoint,
        observed_evidence=coalesced,
    )
    coalesced_resolver = WorkspaceRepositoryChangeEvidenceResolver(
        session=session,
        consumer_key="ambiguous",
        restored_state=state,
    )
    exact_update = _external(
        evidence_ref="provider:coalesced",
        path="shared.txt",
        kind=RepositoryReportedChangeKind.UPDATE,
    )
    assert (
        await coalesced_resolver.correlate_external(exact_update)
    ).posture is RepositoryEvidencePosture.AMBIGUOUS
    await session.stop()


@pytest.mark.asyncio
async def test_later_matching_writer_revises_correlation_to_ambiguity(
    tmp_path: Path,
) -> None:
    session, provider = await _session(tmp_path)
    first = _entry("contended.txt", 1)
    provider.polls.append(
        _observation(
            START + timedelta(seconds=1),
            (first,),
            (_create(first),),
        )
    )
    await session.poll_once()
    resolver = WorkspaceRepositoryChangeEvidenceResolver(
        session=session,
        consumer_key="concurrent-writer",
    )
    external = _external(
        evidence_ref="provider:contended",
        path="contended.txt",
        kind=RepositoryReportedChangeKind.UNKNOWN,
    )
    correlated = await resolver.correlate_external(external)
    assert correlated.posture is RepositoryEvidencePosture.PROVIDER_CORRELATED

    second = _entry("contended.txt", 2)
    provider.polls.append(
        _observation(
            START + timedelta(seconds=2),
            (second,),
            (_update(second),),
        )
    )
    await session.poll_once()
    ambiguous = await resolver.correlate_external(external)
    assert ambiguous.posture is RepositoryEvidencePosture.AMBIGUOUS
    assert ambiguous.revision == correlated.revision + 1
    assert ambiguous.mutation_receipt_refs == ()
    await session.stop()


@pytest.mark.asyncio
async def test_rename_hint_correlates_delete_create_without_inventing_rename(
    tmp_path: Path,
) -> None:
    old = _entry("old.txt", 1)
    session, provider = await _session(tmp_path, initial_entries=(old,))
    new = _entry("new.txt", 1)
    provider.polls.append(
        _observation(
            START + timedelta(seconds=1),
            (new,),
            (_delete("old.txt"), _create(new)),
        )
    )
    await session.poll_once()
    resolver = WorkspaceRepositoryChangeEvidenceResolver(
        session=session,
        consumer_key="rename-hint",
    )
    evidence = await resolver.correlate_external(
        _external(
            evidence_ref="provider:rename",
            path="old.txt",
            new_path="new.txt",
            kind=RepositoryReportedChangeKind.RENAME,
        )
    )
    assert evidence.posture is RepositoryEvidencePosture.PROVIDER_CORRELATED
    assert {item.kind for item in evidence.changed_entries} == {
        RepositoryChangedEntryKind.CREATE,
        RepositoryChangedEntryKind.DELETE,
    }
    await session.stop()


@pytest.mark.asyncio
async def test_resolver_fanout_uses_one_session_with_independent_checkpoints(
    tmp_path: Path,
) -> None:
    session, provider = await _session(tmp_path)
    created = _entry("fanout.txt", 1)
    provider.polls.append(
        _observation(
            START + timedelta(seconds=1),
            (created,),
            (_create(created),),
        )
    )
    await session.poll_once()
    first = WorkspaceRepositoryChangeEvidenceResolver(
        session=session,
        consumer_key="issue",
    )
    second = WorkspaceRepositoryChangeEvidenceResolver(
        session=session,
        consumer_key="agent",
    )

    first_values, second_values = await asyncio.gather(
        first.refresh(), second.refresh()
    )

    assert first_values == second_values
    assert first.checkpoint is not None and first.checkpoint.accepted_cursor == 1
    assert second.checkpoint is not None and second.checkpoint.accepted_cursor == 1
    assert session.checkpoint_for("issue") is not None
    assert session.checkpoint_for("agent") is not None
    assert provider.poll_calls == 1
    await session.stop()


@pytest.mark.asyncio
async def test_same_epoch_state_restores_and_continues_exactly(tmp_path: Path) -> None:
    session, provider = await _session(tmp_path)
    first = _entry("one.txt", 1)
    provider.polls.append(
        _observation(
            START + timedelta(seconds=1),
            (first,),
            (_create(first),),
        )
    )
    await session.poll_once()
    resolver = WorkspaceRepositoryChangeEvidenceResolver(
        session=session,
        consumer_key="restartable",
    )
    await resolver.refresh()
    state = resolver.snapshot_state()
    restored = WorkspaceRepositoryChangeEvidenceResolver(
        session=session,
        consumer_key="restartable",
        restored_state=state,
    )
    assert restored.snapshot_state() == state

    second = _entry("two.txt", 1)
    provider.polls.append(
        _observation(
            START + timedelta(seconds=2),
            (first, second),
            (_create(second),),
        )
    )
    await session.poll_once()
    projected = await restored.refresh()
    assert len(projected) == 1
    assert restored.checkpoint is not None
    assert restored.checkpoint.accepted_cursor == 2
    assert len(restored.observed_evidence) == 2
    await session.stop()


@pytest.mark.asyncio
async def test_observer_retention_and_restart_require_explicit_reset(
    tmp_path: Path,
) -> None:
    session, provider = await _session(tmp_path, journal_capacity=1)
    first = _entry("one.txt", 1)
    second = _entry("two.txt", 1)
    provider.polls.extend(
        (
            _observation(
                START + timedelta(seconds=1),
                (first,),
                (_create(first),),
            ),
            _observation(
                START + timedelta(seconds=2),
                (first, second),
                (_create(second),),
            ),
        )
    )
    await session.poll_once()
    await session.poll_once()
    resolver = WorkspaceRepositoryChangeEvidenceResolver(
        session=session,
        consumer_key="retained",
    )
    gap = await resolver.refresh()
    assert gap[0].posture is RepositoryEvidencePosture.GAP
    assert resolver.checkpoint is not None and resolver.checkpoint.reset_required
    with pytest.raises(WorkspaceRepositoryEvidenceResetRequired):
        await resolver.refresh()
    accepted = await resolver.accept_reset()
    assert accepted.reset_required is False

    state = resolver.snapshot_state()
    await session.stop()
    await session.start(background=False)
    restarted = WorkspaceRepositoryChangeEvidenceResolver(
        session=session,
        consumer_key="retained",
        restored_state=state,
    )
    restart_gap = await restarted.refresh()
    assert restart_gap[0].posture is RepositoryEvidencePosture.GAP
    assert "epoch_mismatch" in str(restart_gap[0].reason)
    await session.stop()


@pytest.mark.asyncio
async def test_bounded_projection_reports_gap_for_evicted_external_window(
    tmp_path: Path,
) -> None:
    session, provider = await _session(tmp_path)
    first = _entry("first.txt", 1)
    second = _entry("second.txt", 1)
    provider.polls.extend(
        (
            _observation(
                START + timedelta(seconds=1),
                (first,),
                (_create(first),),
            ),
            _observation(
                START + timedelta(seconds=3),
                (first, second),
                (_create(second),),
            ),
        )
    )
    await session.poll_once()
    await session.poll_once()
    resolver = WorkspaceRepositoryChangeEvidenceResolver(
        session=session,
        consumer_key="bounded",
        evidence_capacity=1,
    )
    await resolver.refresh()
    external = _external(
        evidence_ref="provider:evicted",
        path="first.txt",
        kind=RepositoryReportedChangeKind.CREATE,
        started_at=START,
        ended_at=START + timedelta(seconds=2),
    )
    assert (
        await resolver.correlate_external(external)
    ).posture is RepositoryEvidencePosture.GAP
    await session.stop()


@pytest.mark.asyncio
async def test_external_ref_and_state_digest_tampering_fail_closed(
    tmp_path: Path,
) -> None:
    session, _provider = await _session(tmp_path)
    resolver = WorkspaceRepositoryChangeEvidenceResolver(
        session=session,
        consumer_key="tamper",
    )
    external = _external(
        evidence_ref="provider:stable",
        path="file.txt",
        kind=RepositoryReportedChangeKind.UNKNOWN,
    )
    await resolver.correlate_external(external)
    changed = replace(
        external,
        source_contract_version="different",
    )
    with pytest.raises(
        WorkspaceRepositoryEvidenceResolverStateError,
        match="cannot change",
    ):
        await resolver.correlate_external(changed)

    state = resolver.snapshot_state()
    assert state.checkpoint is not None
    with pytest.raises(ValueError, match="projection digest"):
        WorkspaceRepositoryEvidenceResolverState(
            consumer_key=state.consumer_key,
            repository_binding_ref=state.repository_binding_ref,
            evidence_capacity=state.evidence_capacity,
            checkpoint=replace(
                state.checkpoint,
                projection_digest="tampered",
            ),
            observed_evidence=state.observed_evidence,
            external_resolutions=state.external_resolutions,
            history_truncated=state.history_truncated,
        )
    await session.stop()
