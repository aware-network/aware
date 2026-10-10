from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from aware_workspace_runtime import (
    ObservationChangeKind,
    RepositoryDiffBinaryPolicy,
    RepositoryDiffLineKind,
    RepositoryDiffPageState,
    RepositoryEvidenceCoordinateKind,
    RepositoryEvidencePosture,
    RepositoryMutationKind,
    RepositoryObservationChange,
    RepositoryObservationCoordinate,
    RepositoryProviderObservation,
    RepositoryReportedChangeKind,
    RepositorySnapshotEntry,
    WorkspaceRepositoryBinding,
    WorkspaceRepositoryChangeEvidenceResolver,
    WorkspaceRepositoryDeltaCaptureCoordinator,
    WorkspaceRepositoryDeltaCapturePolicy,
    WorkspaceRepositoryDiffRequest,
    WorkspaceRepositoryEvidenceCoordinate,
    WorkspaceRepositoryExactDiffProvider,
    WorkspaceRepositoryExternalEvidenceRef,
    WorkspaceRepositoryMutationCoordinator,
    WorkspaceRepositoryMutationRequest,
    WorkspaceRepositoryObservationSession,
    WorkspaceRepositoryOperationalBodyStore,
    WorkspaceRepositoryOperationalDiffProvider,
    WorkspaceRepositoryReportedChange,
    repository_diff_request_ref,
)
from test_repository_delta_retention_client import retained


def _digest(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


class _Provider:
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._entries: tuple[RepositorySnapshotEntry, ...] = ()

    @property
    def root_path(self) -> Path:
        return self._root

    async def initialize(self) -> RepositoryProviderObservation:
        self._entries = self._scan()
        return self._observation(self._entries)

    async def poll(self) -> RepositoryProviderObservation:
        current = self._scan()
        before = {entry.path: entry for entry in self._entries}
        after = {entry.path: entry for entry in current}
        changes = []
        for path in sorted(before.keys() | after.keys()):
            if path not in before:
                changes.append(
                    RepositoryObservationChange(
                        ObservationChangeKind.CREATE, path, after[path]
                    )
                )
            elif path not in after:
                changes.append(
                    RepositoryObservationChange(ObservationChangeKind.DELETE, path)
                )
            elif before[path] != after[path]:
                changes.append(
                    RepositoryObservationChange(
                        ObservationChangeKind.UPDATE, path, after[path]
                    )
                )
        self._entries = current
        return self._observation(current, tuple(changes))

    def _scan(self) -> tuple[RepositorySnapshotEntry, ...]:
        values = []
        for path in sorted(self._root.rglob("*")):
            if path.is_file():
                body = path.read_bytes()
                values.append(
                    RepositorySnapshotEntry(
                        path=path.relative_to(self._root).as_posix(),
                        size_bytes=len(body),
                        modified_ns=path.stat().st_mtime_ns,
                        content_digest=_digest(body),
                    )
                )
        return tuple(values)

    @staticmethod
    def _observation(entries, changes=()):
        return RepositoryProviderObservation(
            observed_at=datetime.now(UTC), entries=entries, changes=changes
        )


def _coordinate(
    session: WorkspaceRepositoryObservationSession,
) -> WorkspaceRepositoryEvidenceCoordinate:
    snapshot = session.current_snapshot
    binding_ref = session.binding.binding_key
    assert binding_ref is not None
    observation = RepositoryObservationCoordinate(
        repository_binding_ref=binding_ref,
        epoch=snapshot.epoch,
        cursor=snapshot.cursor,
        snapshot_digest=snapshot.snapshot_digest,
        visibility_policy_ref="aware.workspace.repository-visibility.canonical-source.v1",
        visibility_policy_version=session.binding.filter_version,
    )
    return WorkspaceRepositoryEvidenceCoordinate(
        kind=RepositoryEvidenceCoordinateKind.OBSERVATION,
        repository_binding_ref=binding_ref,
        state_digest=snapshot.snapshot_digest,
        observation=observation,
    )


async def _authorized_update(
    tmp_path: Path,
    *,
    before: bytes,
    after: bytes,
    store: WorkspaceRepositoryOperationalBodyStore | None = None,
):
    source = tmp_path / "source.txt"
    source.write_bytes(before)
    provider = _Provider(tmp_path)
    session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path), provider=provider
    )
    await session.start(background=False)
    body_store = store or WorkspaceRepositoryOperationalBodyStore()
    coordinator = WorkspaceRepositoryMutationCoordinator(
        session=session, body_store=body_store
    )
    result = await coordinator.mutate(
        WorkspaceRepositoryMutationRequest(
            operation_ref=f"operation:{hashlib.sha256(after).hexdigest()[:8]}",
            idempotency_key=f"submission:{hashlib.sha256(before + after).hexdigest()[:8]}",
            mutation_kind=RepositoryMutationKind.UPDATE,
            expected_coordinate=_coordinate(session),
            target_path="source.txt",
            expected_exists=True,
            expected_content_digest=_digest(before),
            content=after,
        )
    )
    assert result.evidence is not None
    return result, body_store


def _request(
    result,
    *,
    maximum_lines: int = 100,
    maximum_bytes: int = 100_000,
    continuation_ref: str | None = None,
    binary_policy: RepositoryDiffBinaryPolicy = RepositoryDiffBinaryPolicy.METADATA_ONLY,
    cancellation_ref: str | None = None,
    baseline=None,
    target=None,
    correlation_ref: str = "test:diff",
) -> WorkspaceRepositoryDiffRequest:
    evidence = result.evidence
    assert evidence is not None
    baseline = baseline or evidence.before_coordinate
    target = target or evidence.after_coordinate
    assert baseline is not None and target is not None
    values = {
        "evidence_ref": evidence.evidence_ref,
        "repository_binding_ref": evidence.repository_binding_ref,
        "baseline": baseline,
        "target": target,
        "changed_entry_ref": evidence.changed_entries[0].changed_entry_ref,
        "continuation_ref": continuation_ref,
        "maximum_files": 1,
        "maximum_lines": maximum_lines,
        "maximum_bytes": maximum_bytes,
        "context_lines": 1,
        "binary_policy": binary_policy,
    }
    return WorkspaceRepositoryDiffRequest(
        request_ref=repository_diff_request_ref(**values),
        cancellation_ref=cancellation_ref,
        correlation_ref=correlation_ref,
        **values,
    )


@pytest.mark.asyncio
async def test_exact_text_diff_has_stable_ranges_and_lines(tmp_path: Path) -> None:
    result, store = await _authorized_update(
        tmp_path,
        before=b"alpha\nbeta\ngamma\n",
        after=b"alpha\nBETA\ngamma\ndelta\n",
    )
    provider = WorkspaceRepositoryOperationalDiffProvider(body_store=store)
    page = provider.diff(_request(result))

    assert page.state is RepositoryDiffPageState.AVAILABLE
    assert page.complete is True
    assert page.total_file_count == 1
    assert (
        page.files[0].changed_entry_ref
        == result.evidence.changed_entries[0].changed_entry_ref
    )
    kinds = [line.kind for hunk in page.files[0].hunks for line in hunk.lines]
    assert RepositoryDiffLineKind.DELETION in kinds
    assert RepositoryDiffLineKind.ADDITION in kinds
    assert all(hunk.hunk_ref for hunk in page.files[0].hunks)


@pytest.mark.asyncio
async def test_resident_provider_delta_renders_exact_lazy_diff(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_bytes(b"before\n")
    provider = _Provider(tmp_path)
    session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path), provider=provider
    )
    await session.start(background=False)
    binding_ref = session.binding.binding_key
    assert binding_ref is not None
    delta_store = retained(
        repository_binding_ref=binding_ref,
        state_root=tmp_path.parent / f".state-{tmp_path.name}",
    )
    coordinator = WorkspaceRepositoryDeltaCaptureCoordinator(
        binding=session.binding,
        store=delta_store,
    )
    coordinator.prepare(
        snapshot=session.current_snapshot,
        selected_paths=("source.txt",),
        context_refs=("issue:one",),
        policy=WorkspaceRepositoryDeltaCapturePolicy(),
    )
    observed_at = datetime.now(UTC)
    source.write_bytes(b"after\n")
    batch = await session.poll_once()
    assert batch is not None
    deltas = coordinator.observe(batch)
    assert len(deltas) == 1
    resolver = WorkspaceRepositoryChangeEvidenceResolver(
        session=session,
        consumer_key="resident-diff",
    )
    evidence = await resolver.correlate_external(
        WorkspaceRepositoryExternalEvidenceRef(
            evidence_ref="provider-edit:one",
            source_namespace="provider.edit.v1",
            source_contract_version="1",
            observed_at=observed_at,
            changes=(
                WorkspaceRepositoryReportedChange(
                    path="source.txt",
                    kind=RepositoryReportedChangeKind.UPDATE,
                ),
            ),
            context_refs=("work:one",),
            complete=True,
            correlation_started_at=observed_at - timedelta(minutes=1),
            correlation_ended_at=observed_at + timedelta(minutes=1),
        )
    )
    exact = WorkspaceRepositoryExactDiffProvider(
        body_store=WorkspaceRepositoryOperationalBodyStore(),
        delta_store=delta_store,
        evidence_resolver=resolver,
    )
    assert delta_store.snapshot().metrics.body_read_count == 0
    page = exact.diff(
        _request(
            SimpleNamespace(evidence=evidence),
            correlation_ref=None,
        )
    )
    assert page.state is RepositoryDiffPageState.AVAILABLE
    assert page.posture is RepositoryEvidencePosture.PROVIDER_CORRELATED
    lines = [line.text for hunk in page.files[0].hunks for line in hunk.lines]
    assert lines == ["before", "after"]
    assert delta_store.snapshot().metrics.body_read_count == 2
    await session.stop()


@pytest.mark.asyncio
async def test_diff_pages_are_bounded_and_continuations_are_exact(
    tmp_path: Path,
) -> None:
    before = "".join(f"old-{index}\n" for index in range(12)).encode()
    after = "".join(f"new-{index}\n" for index in range(12)).encode()
    result, store = await _authorized_update(tmp_path, before=before, after=after)
    provider = WorkspaceRepositoryOperationalDiffProvider(body_store=store)
    first = provider.diff(_request(result, maximum_lines=3))
    assert first.state is RepositoryDiffPageState.PARTIAL
    assert first.continuation_ref is not None
    assert sum(len(hunk.lines) for hunk in first.files[0].hunks) <= 3

    pages = [first]
    continuation = first.continuation_ref
    while continuation is not None:
        page = provider.diff(
            _request(result, maximum_lines=3, continuation_ref=continuation)
        )
        pages.append(page)
        continuation = page.continuation_ref
    assert pages[-1].state is RepositoryDiffPageState.AVAILABLE
    assert pages[-1].complete is True
    assert sum(len(hunk.lines) for page in pages for hunk in page.files[0].hunks) == 24


@pytest.mark.asyncio
async def test_binary_policy_is_explicit(tmp_path: Path) -> None:
    result, store = await _authorized_update(
        tmp_path, before=b"\x00one", after=b"\x00two"
    )
    provider = WorkspaceRepositoryOperationalDiffProvider(body_store=store)
    metadata = provider.diff(_request(result))
    rejected = provider.diff(
        _request(result, binary_policy=RepositoryDiffBinaryPolicy.REJECT)
    )

    assert metadata.state is RepositoryDiffPageState.BINARY
    assert metadata.files[0].binary is True
    assert metadata.files[0].hunks == ()
    assert rejected.state is RepositoryDiffPageState.UNAVAILABLE
    assert rejected.reason == "binary diff rejected by policy"


@pytest.mark.asyncio
async def test_evicted_bodies_and_stale_coordinates_fail_closed(tmp_path: Path) -> None:
    store = WorkspaceRepositoryOperationalBodyStore(capacity=1)
    # Separate repository roots avoid coordinate interference while sharing the
    # deliberately tiny volatile body store.
    first_root = tmp_path / "one"
    second_root = tmp_path / "two"
    first_root.mkdir()
    second_root.mkdir()
    first, _ = await _authorized_update(
        first_root, before=b"one", after=b"ONE", store=store
    )
    second, _ = await _authorized_update(
        second_root, before=b"two", after=b"TWO", store=store
    )
    provider = WorkspaceRepositoryOperationalDiffProvider(body_store=store)

    evicted = provider.diff(_request(first))
    assert evicted.state is RepositoryDiffPageState.UNAVAILABLE
    stale = provider.diff(
        _request(
            second,
            target=second.evidence.before_coordinate,
        )
    )
    assert stale.state is RepositoryDiffPageState.STALE


@pytest.mark.asyncio
async def test_cancellation_and_unknown_continuation_fail_closed(
    tmp_path: Path,
) -> None:
    result, store = await _authorized_update(
        tmp_path, before=b"before\n", after=b"after\n"
    )
    provider = WorkspaceRepositoryOperationalDiffProvider(
        body_store=store,
        is_cancelled=lambda ref: ref == "cancel:1",
    )
    cancelled = provider.diff(_request(result, cancellation_ref="cancel:1"))
    unknown = provider.diff(_request(result, continuation_ref="unknown:cursor"))
    assert cancelled.state is RepositoryDiffPageState.UNAVAILABLE
    assert cancelled.reason == "diff request cancelled"
    assert unknown.state is RepositoryDiffPageState.UNAVAILABLE
    assert unknown.reason == "diff continuation is unavailable"
