from __future__ import annotations

import hashlib
import os
import stat
from datetime import UTC, datetime
from pathlib import Path

import aware_file_system.confined_mutation as physical
import aware_workspace_runtime.repository_mutation as mutations
import pytest
from aware_workspace_fs_adapter.repository_mutation_store import (
    WorkspaceRepositoryMutationStore,
    WorkspaceRepositoryMutationStoreCorrupt,
)
from aware_workspace_runtime import (
    ObservationChangeKind,
    RepositoryBodyAvailability,
    RepositoryChangedEntryKind,
    RepositoryEvidenceCoordinateKind,
    RepositoryEvidencePosture,
    RepositoryMutationKind,
    RepositoryMutationOutcome,
    RepositoryObservationChange,
    RepositoryObservationCoordinate,
    RepositoryProviderObservation,
    RepositorySnapshotEntry,
    WorkspaceRepositoryBinding,
    WorkspaceRepositoryChangeEvidenceResolver,
    WorkspaceRepositoryEvidenceCoordinate,
    WorkspaceRepositoryMutationCoordinator,
    WorkspaceRepositoryMutationRequest,
    WorkspaceRepositoryObservationSession,
    WorkspaceRepositoryOperationalBodyStore,
    WorkspaceRepositoryTextReplacement,
)


def _digest(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


class ScanningProvider:
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._entries: tuple[RepositorySnapshotEntry, ...] = ()
        self.poll_calls = 0
        self.observe_paths_calls: list[tuple[str, ...]] = []

    @property
    def root_path(self) -> Path:
        return self._root

    async def initialize(self) -> RepositoryProviderObservation:
        self._entries = self._scan()
        return RepositoryProviderObservation(
            observed_at=datetime.now(UTC),
            entries=self._entries,
        )

    async def poll(self) -> RepositoryProviderObservation:
        self.poll_calls += 1
        current = self._scan()
        before = {entry.path: entry for entry in self._entries}
        after = {entry.path: entry for entry in current}
        changes = []
        for path in sorted(before.keys() | after.keys()):
            if path not in before:
                changes.append(
                    RepositoryObservationChange(
                        kind=ObservationChangeKind.CREATE,
                        path=path,
                        entry=after[path],
                    )
                )
            elif path not in after:
                changes.append(
                    RepositoryObservationChange(
                        kind=ObservationChangeKind.DELETE,
                        path=path,
                    )
                )
            elif before[path] != after[path]:
                changes.append(
                    RepositoryObservationChange(
                        kind=ObservationChangeKind.UPDATE,
                        path=path,
                        entry=after[path],
                    )
                )
        self._entries = current
        return RepositoryProviderObservation(
            observed_at=datetime.now(UTC),
            entries=current,
            changes=tuple(changes),
        )

    async def observe_paths(
        self, paths: tuple[str, ...]
    ) -> RepositoryProviderObservation:
        self.observe_paths_calls.append(paths)
        before = {entry.path: entry for entry in self._entries}
        after = dict(before)
        changes: list[RepositoryObservationChange] = []
        for path in paths:
            source = self._root / path
            prior = before.get(path)
            if source.is_file():
                content = source.read_bytes()
                metadata = source.stat()
                current = RepositorySnapshotEntry(
                    path=path,
                    size_bytes=len(content),
                    modified_ns=metadata.st_mtime_ns,
                    content_digest=_digest(content),
                )
                after[path] = current
                if prior is None:
                    changes.append(
                        RepositoryObservationChange(
                            kind=ObservationChangeKind.CREATE,
                            path=path,
                            entry=current,
                        )
                    )
                elif prior != current:
                    changes.append(
                        RepositoryObservationChange(
                            kind=ObservationChangeKind.UPDATE,
                            path=path,
                            entry=current,
                        )
                    )
            elif prior is not None:
                after.pop(path)
                changes.append(
                    RepositoryObservationChange(
                        kind=ObservationChangeKind.DELETE,
                        path=path,
                    )
                )
        self._entries = tuple(after[path] for path in sorted(after))
        return RepositoryProviderObservation(
            observed_at=datetime.now(UTC),
            entries=self._entries,
            changes=tuple(changes),
        )

    def _scan(self) -> tuple[RepositorySnapshotEntry, ...]:
        values = []
        for path in sorted(self._root.rglob("*")):
            if not path.is_file():
                continue
            content = path.read_bytes()
            metadata = path.stat()
            values.append(
                RepositorySnapshotEntry(
                    path=path.relative_to(self._root).as_posix(),
                    size_bytes=len(content),
                    modified_ns=metadata.st_mtime_ns,
                    content_digest=_digest(content),
                )
            )
        return tuple(values)


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


async def _runtime(tmp_path: Path):
    provider = ScanningProvider(tmp_path)
    session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path),
        provider=provider,
    )
    await session.start(background=False)
    store = WorkspaceRepositoryOperationalBodyStore()
    coordinator = WorkspaceRepositoryMutationCoordinator(
        session=session,
        body_store=store,
    )
    return provider, session, store, coordinator


@pytest.mark.asyncio
@pytest.mark.parametrize("uncertain", [False, True])
async def test_failed_target_effect_survives_receipt_replay_and_codec(
    tmp_path, monkeypatch, uncertain
):
    from aware_workspace_runtime.change_evidence_codec import (
        repository_authorized_mutation_from_payload,
        repository_authorized_mutation_payload,
    )

    target = tmp_path / "manifest"
    target.write_bytes(b"before")
    provider, session, store, coordinator = await _runtime(tmp_path)
    result_store = WorkspaceRepositoryMutationStore(
        repository_binding_ref=session.binding.binding_key,
        state_root=tmp_path / "state",
    )
    coordinator = WorkspaceRepositoryMutationCoordinator(
        session=session,
        body_store=store,
        result_store=result_store,
    )
    request = WorkspaceRepositoryMutationRequest(
        operation_ref="test.effect",
        idempotency_key="effect-failure",
        mutation_kind=RepositoryMutationKind.UPDATE,
        expected_coordinate=_coordinate(session),
        target_path="manifest",
        expected_exists=True,
        expected_content_digest=_digest(b"before"),
        content=b"after",
    )
    if uncertain:
        original_replace = os.replace

        def replace_then_fail(*args, **kwargs):
            original_replace(*args, **kwargs)
            raise OSError("unknown completion")

        monkeypatch.setattr(os, "replace", replace_then_fail)
    else:
        original_fsync = os.fsync

        def fail_directory_sync(fd):
            if (
                stat.S_ISDIR(os.fstat(fd).st_mode)
                and os.fstat(fd).st_ino == tmp_path.stat().st_ino
            ):
                raise OSError("durability failed")
            return original_fsync(fd)

        monkeypatch.setattr(os, "fsync", fail_directory_sync)
    result = await coordinator.mutate(request)
    assert target.read_bytes() == b"after"
    assert result.receipt.outcome is RepositoryMutationOutcome.FAILED
    assert result.evidence is None and result.receipt.result_coordinate is None
    effect = result.receipt.physical_effect
    assert effect is not None
    assert effect.state == ("unknown" if uncertain else "applied")
    assert not effect.durability_confirmed
    assert effect.before_content_digest == _digest(b"before")
    assert effect.after_content_digest == (None if uncertain else _digest(b"after"))
    assert await coordinator.mutate(request) == result
    payload = repository_authorized_mutation_payload(result)
    assert payload["value"]["receipt"]["contract_version"] == "2"
    assert repository_authorized_mutation_from_payload(payload) == result
    monkeypatch.undo()
    restored_store = WorkspaceRepositoryMutationStore(
        repository_binding_ref=session.binding.binding_key,
        state_root=tmp_path / "state",
    )
    restored = WorkspaceRepositoryMutationCoordinator(
        session=session,
        body_store=store,
        result_store=restored_store,
    )
    assert await restored.mutate(request) == result
    from copy import deepcopy

    legacy = deepcopy(payload)
    legacy_receipt = legacy["value"]["receipt"]
    legacy_receipt["contract_version"] = "1"
    legacy_receipt["value"].pop("physical_effect")
    assert (
        repository_authorized_mutation_from_payload(legacy).receipt.physical_effect
        is None
    )
    with pytest.raises(ValueError, match="requires version 2"):
        legacy_receipt["value"]["physical_effect"] = payload["value"]["receipt"][
            "value"
        ]["physical_effect"]
        repository_authorized_mutation_from_payload(legacy)
    await session.stop()


@pytest.mark.asyncio
async def test_continuous_confinement_is_denied_without_workspace_evidence(
    tmp_path: Path,
) -> None:
    provider, session, store, _ = await _runtime(tmp_path)
    coordinator = WorkspaceRepositoryMutationCoordinator(
        session=session,
        body_store=store,
        confinement_profile=physical.ConfinedMutationProfile.CONTINUOUS_ROOT_V1,
    )
    request = WorkspaceRepositoryMutationRequest(
        operation_ref="operation:continuous",
        idempotency_key="submission:continuous",
        mutation_kind=RepositoryMutationKind.CREATE,
        expected_coordinate=_coordinate(session),
        target_path="missing/goal.md",
        expected_exists=False,
        expected_content_digest=None,
        content=b"after",
    )
    result = await coordinator.mutate(request)
    assert result.receipt.outcome is RepositoryMutationOutcome.DENIED
    assert result.receipt.error_code == "continuous_root_confinement_unavailable"
    assert result.evidence is None
    assert store.retained_count == 0
    assert provider.poll_calls == 0 and provider.observe_paths_calls == []
    assert not (tmp_path / "missing").exists()
    assert await coordinator.mutate(request) == result
    await session.stop()


@pytest.mark.parametrize("invalid", ["continuous_root_v1", "unknown", True, None])
@pytest.mark.asyncio
async def test_workspace_refuses_unqualified_profile_tokens(
    tmp_path: Path, invalid
) -> None:
    _provider, session, store, _ = await _runtime(tmp_path)
    with pytest.raises(TypeError, match="profile must be exact"):
        WorkspaceRepositoryMutationCoordinator(
            session=session,
            body_store=store,
            confinement_profile=invalid,
        )
    assert store.retained_count == 0
    await session.stop()


@pytest.mark.parametrize("fault", ["downgraded", "unknown", "text_profile"])
@pytest.mark.asyncio
async def test_workspace_refuses_a_mismatched_applied_physical_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
) -> None:
    provider, session, store, _ = await _runtime(tmp_path)
    coordinator = WorkspaceRepositoryMutationCoordinator(
        session=session,
        body_store=store,
        confinement_profile=physical.ConfinedMutationProfile.CONTINUOUS_ROOT_V1,
    )

    def wrong_result(**kwargs):
        assert (
            kwargs["confinement_profile"]
            is physical.ConfinedMutationProfile.CONTINUOUS_ROOT_V1
        )
        result = physical.ConfinedFileMutationResult(
            kind=physical.ConfinedMutationKind.CREATE,
            path="goal.md",
            outcome=physical.ConfinedMutationOutcome.APPLIED,
            before_exists=False,
            before_content_digest=None,
            before_size_bytes=None,
            after_exists=True,
            after_content_digest=_digest(b"after"),
            after_size_bytes=5,
            after_content=b"after",
        )
        if fault != "downgraded":
            object.__setattr__(
                result,
                "confinement_profile",
                True if fault == "unknown" else "continuous_root_v1",
            )
        return result

    monkeypatch.setattr(mutations, "mutate_confined_file", wrong_result)
    result = await coordinator.mutate(
        WorkspaceRepositoryMutationRequest(
            operation_ref="operation:wrong-result",
            idempotency_key="submission:wrong-result",
            mutation_kind=RepositoryMutationKind.CREATE,
            expected_coordinate=_coordinate(session),
            target_path="goal.md",
            expected_exists=False,
            expected_content_digest=None,
            content=b"after",
        )
    )
    assert result.receipt.outcome is RepositoryMutationOutcome.FAILED
    assert result.receipt.error_code == "filesystem_confinement_profile_mismatch"
    assert result.evidence is None and store.retained_count == 0
    assert provider.poll_calls == 0 and provider.observe_paths_calls == []
    assert not (tmp_path / "goal.md").exists()
    await session.stop()


@pytest.mark.parametrize("first_strict", [False, True])
@pytest.mark.asyncio
async def test_confinement_policy_cannot_change_on_durable_retry_or_resolution(
    tmp_path: Path,
    first_strict: bool,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    _, first_session, _, _ = await _runtime(repository)
    binding = first_session.binding.binding_key
    assert binding is not None
    first_profile = (
        physical.ConfinedMutationProfile.CONTINUOUS_ROOT_V1
        if first_strict
        else physical.ConfinedMutationProfile.DESCRIPTOR_WALK_V1
    )
    second_profile = (
        physical.ConfinedMutationProfile.DESCRIPTOR_WALK_V1
        if first_strict
        else physical.ConfinedMutationProfile.CONTINUOUS_ROOT_V1
    )
    state_root = tmp_path / "state"
    first = WorkspaceRepositoryMutationCoordinator(
        session=first_session,
        body_store=WorkspaceRepositoryOperationalBodyStore(),
        result_store=WorkspaceRepositoryMutationStore(
            repository_binding_ref=binding, state_root=state_root
        ),
        confinement_profile=first_profile,
    )
    request = WorkspaceRepositoryMutationRequest(
        operation_ref="operation:profile-restart",
        idempotency_key="submission:profile-restart",
        mutation_kind=RepositoryMutationKind.CREATE,
        expected_coordinate=_coordinate(first_session),
        target_path="goal.md",
        expected_exists=False,
        expected_content_digest=None,
        content=b"after",
    )
    original = await first.mutate(request)
    assert original.receipt.outcome is (
        RepositoryMutationOutcome.DENIED
        if first_strict
        else RepositoryMutationOutcome.APPLIED
    )
    await first_session.stop()
    _, second_session, second_store, _ = await _runtime(repository)
    before = (
        (repository / "goal.md").read_bytes()
        if (repository / "goal.md").exists()
        else None
    )
    second = WorkspaceRepositoryMutationCoordinator(
        session=second_session,
        body_store=second_store,
        result_store=WorkspaceRepositoryMutationStore(
            repository_binding_ref=binding, state_root=state_root
        ),
        confinement_profile=second_profile,
    )
    with pytest.raises(ValueError, match="cannot change mutation request"):
        await second.mutate(request)
    with pytest.raises(ValueError, match="confinement profile differs"):
        await second.resolve_receipts((original.receipt.mutation_receipt_ref,))
    assert second_store.retained_count == 0
    after = (
        (repository / "goal.md").read_bytes()
        if (repository / "goal.md").exists()
        else None
    )
    assert after == before
    await second_session.stop()


@pytest.mark.asyncio
async def test_continuous_refusal_replays_exactly_after_durable_restart(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    _, first_session, _, _ = await _runtime(repository)
    binding = first_session.binding.binding_key
    assert binding is not None
    state_root = tmp_path / "state"
    first = WorkspaceRepositoryMutationCoordinator(
        session=first_session,
        body_store=WorkspaceRepositoryOperationalBodyStore(),
        result_store=WorkspaceRepositoryMutationStore(
            repository_binding_ref=binding,
            state_root=state_root,
        ),
        confinement_profile=physical.ConfinedMutationProfile.CONTINUOUS_ROOT_V1,
    )
    request = WorkspaceRepositoryMutationRequest(
        operation_ref="operation:strict-restart",
        idempotency_key="submission:strict-restart",
        mutation_kind=RepositoryMutationKind.CREATE,
        expected_coordinate=_coordinate(first_session),
        target_path="missing/goal.md",
        expected_exists=False,
        expected_content_digest=None,
        content=b"after",
    )
    original = await first.mutate(request)
    assert original.receipt.outcome is RepositoryMutationOutcome.DENIED
    await first_session.stop()
    provider, second_session, second_store, _ = await _runtime(repository)
    second = WorkspaceRepositoryMutationCoordinator(
        session=second_session,
        body_store=second_store,
        result_store=WorkspaceRepositoryMutationStore(
            repository_binding_ref=binding,
            state_root=state_root,
        ),
        confinement_profile=physical.ConfinedMutationProfile.CONTINUOUS_ROOT_V1,
    )
    assert await second.mutate(request) == original
    resolution = await second.resolve_receipts((original.receipt.mutation_receipt_ref,))
    assert resolution.resolved == (original,)
    assert second_store.retained_count == 0
    assert provider.poll_calls == 0 and provider.observe_paths_calls == []
    assert not (repository / "missing").exists()
    await second_session.stop()


@pytest.mark.asyncio
async def test_policy_change_during_request_conversion_cannot_downgrade_effect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider, session, store, _ = await _runtime(tmp_path)
    coordinator = WorkspaceRepositoryMutationCoordinator(
        session=session,
        body_store=store,
        confinement_profile=physical.ConfinedMutationProfile.CONTINUOUS_ROOT_V1,
    )
    convert = mutations._physical_request

    def convert_then_change_policy(request):
        result = convert(request)
        coordinator._confinement_profile = (
            physical.ConfinedMutationProfile.DESCRIPTOR_WALK_V1
        )
        return result

    monkeypatch.setattr(mutations, "_physical_request", convert_then_change_policy)
    result = await coordinator.mutate(
        WorkspaceRepositoryMutationRequest(
            operation_ref="operation:policy-race",
            idempotency_key="submission:policy-race",
            mutation_kind=RepositoryMutationKind.CREATE,
            expected_coordinate=_coordinate(session),
            target_path="goal.md",
            expected_exists=False,
            expected_content_digest=None,
            content=b"after",
        )
    )
    assert result.receipt.outcome is RepositoryMutationOutcome.DENIED
    assert result.receipt.error_code == "continuous_root_confinement_unavailable"
    assert result.evidence is None and store.retained_count == 0
    assert provider.poll_calls == 0 and provider.observe_paths_calls == []
    assert not (tmp_path / "goal.md").exists()
    await session.stop()


@pytest.mark.asyncio
async def test_legacy_fingerprint_is_preserved_and_strict_profile_is_distinct(
    tmp_path: Path,
) -> None:
    _, session, _, _ = await _runtime(tmp_path)
    request = WorkspaceRepositoryMutationRequest(
        operation_ref="operation:fingerprint",
        idempotency_key="submission:fingerprint",
        mutation_kind=RepositoryMutationKind.CREATE,
        expected_coordinate=_coordinate(session),
        target_path="goal.md",
        expected_exists=False,
        expected_content_digest=None,
        content=b"after",
    )
    expected = mutations._digest_ref(
        "workspace-repository-mutation-request",
        request.operation_ref,
        request.idempotency_key,
        request.mutation_kind.value,
        request.expected_coordinate.state_digest,
        str(request.expected_coordinate.observation),
        request.target_path,
        str(request.expected_exists),
        "",
        _digest(request.content),
        str(request.maximum_bytes),
    )
    assert mutations._request_fingerprint(request) == expected
    assert (
        mutations._request_fingerprint(
            request,
            confinement_profile=physical.ConfinedMutationProfile.CONTINUOUS_ROOT_V1,
        )
        != expected
    )
    await session.stop()


@pytest.mark.asyncio
async def test_create_is_authorized_exact_and_idempotent(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    provider, session, store, coordinator = await _runtime(tmp_path)
    request = WorkspaceRepositoryMutationRequest(
        operation_ref="operation:create",
        idempotency_key="submission:1",
        mutation_kind=RepositoryMutationKind.CREATE,
        expected_coordinate=_coordinate(session),
        target_path="src/app.py",
        expected_exists=False,
        expected_content_digest=None,
        content=b"print('aware')\n",
        context_refs=("work:issue-1", "actor:agent-1"),
    )

    first = await coordinator.mutate(request)
    repeated = await coordinator.mutate(request)

    assert repeated == first
    assert provider.poll_calls == 0
    assert provider.observe_paths_calls == [("src/app.py",)]
    assert first.receipt.outcome is RepositoryMutationOutcome.APPLIED
    assert first.receipt.context_refs == request.context_refs
    assert first.evidence is not None
    assert first.evidence.posture is RepositoryEvidencePosture.WORKSPACE_AUTHORIZED
    assert first.evidence.mutation_receipt_refs == (first.receipt.mutation_receipt_ref,)
    entry = first.evidence.changed_entries[0]
    assert entry.kind is RepositoryChangedEntryKind.CREATE
    assert entry.new_body_availability is RepositoryBodyAvailability.AVAILABLE
    assert store.resolve(first.evidence.evidence_ref) is not None
    assert (tmp_path / "src/app.py").read_bytes() == request.content


@pytest.mark.asyncio
async def test_mutation_receipt_and_idempotency_survive_restart(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repo"
    repository_root.mkdir()
    (repository_root / "src").mkdir()
    state_root = tmp_path / "state"
    provider = ScanningProvider(repository_root)
    first_session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(repository_root),
        provider=provider,
    )
    await first_session.start(background=False)
    binding_ref = first_session.binding.binding_key
    assert binding_ref is not None
    first_store = WorkspaceRepositoryMutationStore(
        repository_binding_ref=binding_ref,
        state_root=state_root,
    )
    first_coordinator = WorkspaceRepositoryMutationCoordinator(
        session=first_session,
        body_store=WorkspaceRepositoryOperationalBodyStore(),
        result_store=first_store,
    )
    request = WorkspaceRepositoryMutationRequest(
        operation_ref="operation:durable",
        idempotency_key="submission:durable",
        mutation_kind=RepositoryMutationKind.CREATE,
        expected_coordinate=_coordinate(first_session),
        target_path="src/durable.py",
        expected_exists=False,
        expected_content_digest=None,
        content=b"durable = True\n",
        context_refs=("work-context:durable",),
    )

    applied = await first_coordinator.mutate(request)
    await first_session.stop()

    second_session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(repository_root),
        provider=ScanningProvider(repository_root),
    )
    await second_session.start(background=False)
    second_store = WorkspaceRepositoryMutationStore(
        repository_binding_ref=binding_ref,
        state_root=state_root,
    )
    second_coordinator = WorkspaceRepositoryMutationCoordinator(
        session=second_session,
        body_store=WorkspaceRepositoryOperationalBodyStore(),
        result_store=second_store,
    )

    assert await second_coordinator.mutate(request) == applied
    resolution = await second_coordinator.resolve_receipts(
        (applied.receipt.mutation_receipt_ref, "mutation:missing")
    )
    assert resolution.resolved == (applied,)
    assert resolution.missing_receipt_refs == ("mutation:missing",)
    changed_request = WorkspaceRepositoryMutationRequest(
        operation_ref=request.operation_ref,
        idempotency_key=request.idempotency_key,
        mutation_kind=request.mutation_kind,
        expected_coordinate=request.expected_coordinate,
        target_path=request.target_path,
        expected_exists=request.expected_exists,
        expected_content_digest=request.expected_content_digest,
        content=b"durable = False\n",
        context_refs=request.context_refs,
    )
    with pytest.raises(ValueError, match="cannot change mutation request"):
        await second_coordinator.mutate(changed_request)
    await second_session.stop()


def test_mutation_store_rejects_corrupt_metadata(tmp_path: Path) -> None:
    index_path = tmp_path / "repository_mutations" / "index.json"
    index_path.parent.mkdir(parents=True)
    index_path.write_text("not-json", encoding="utf-8")

    with pytest.raises(WorkspaceRepositoryMutationStoreCorrupt):
        WorkspaceRepositoryMutationStore(
            repository_binding_ref="repository:test",
            state_root=tmp_path,
        )


@pytest.mark.asyncio
async def test_update_and_delete_preserve_exact_preimage(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_bytes(b"before\n")
    provider, session, store, coordinator = await _runtime(tmp_path)
    update = await coordinator.mutate(
        WorkspaceRepositoryMutationRequest(
            operation_ref="operation:update",
            idempotency_key="submission:2",
            mutation_kind=RepositoryMutationKind.UPDATE,
            expected_coordinate=_coordinate(session),
            target_path="source.txt",
            expected_exists=True,
            expected_content_digest=_digest(b"before\n"),
            content=b"after\n",
        )
    )
    assert update.evidence is not None
    retained = store.resolve(update.evidence.evidence_ref)
    assert retained is not None
    assert retained.before_content == b"before\n"
    assert retained.after_content == b"after\n"

    deleted = await coordinator.mutate(
        WorkspaceRepositoryMutationRequest(
            operation_ref="operation:delete",
            idempotency_key="submission:3",
            mutation_kind=RepositoryMutationKind.DELETE,
            expected_coordinate=_coordinate(session),
            target_path="source.txt",
            expected_exists=True,
            expected_content_digest=_digest(b"after\n"),
        )
    )
    assert deleted.evidence is not None
    assert deleted.evidence.changed_entries[0].kind is RepositoryChangedEntryKind.DELETE
    assert deleted.receipt.result_entry_ref is None
    assert not source.exists()
    assert provider.poll_calls == 0
    assert provider.observe_paths_calls == [
        ("source.txt",),
        ("source.txt",),
    ]


@pytest.mark.asyncio
async def test_text_replacements_authorize_exact_preimage_and_path_only(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.txt"
    before = b"alpha one\nbeta two\n"
    source.write_bytes(before)
    provider, session, store, coordinator = await _runtime(tmp_path)

    applied = await coordinator.mutate(
        WorkspaceRepositoryMutationRequest(
            operation_ref="operation:text-replacements",
            idempotency_key="submission:text-replacements",
            mutation_kind=RepositoryMutationKind.UPDATE,
            expected_coordinate=_coordinate(session),
            target_path="source.txt",
            expected_exists=True,
            expected_content_digest=_digest(before),
            text_replacements=(
                WorkspaceRepositoryTextReplacement("alpha", "aware"),
                WorkspaceRepositoryTextReplacement("two", "three"),
            ),
            maximum_bytes=1024,
        )
    )

    assert applied.receipt.outcome is RepositoryMutationOutcome.APPLIED
    assert applied.evidence is not None
    retained = store.resolve(applied.evidence.evidence_ref)
    assert retained is not None
    assert retained.before_content == before
    assert retained.after_content == b"aware one\nbeta three\n"
    assert source.read_bytes() == retained.after_content
    assert provider.poll_calls == 0
    assert provider.observe_paths_calls == [("source.txt",)]

    ambiguous = await coordinator.mutate(
        WorkspaceRepositoryMutationRequest(
            operation_ref="operation:text-ambiguous",
            idempotency_key="submission:text-ambiguous",
            mutation_kind=RepositoryMutationKind.UPDATE,
            expected_coordinate=_coordinate(session),
            target_path="source.txt",
            expected_exists=True,
            expected_content_digest=_digest(retained.after_content),
            text_replacements=(WorkspaceRepositoryTextReplacement("e", "E"),),
            maximum_bytes=1024,
        )
    )
    assert ambiguous.receipt.outcome is RepositoryMutationOutcome.CONFLICT
    assert ambiguous.receipt.error_code == "text_replacement_not_unique"
    assert ambiguous.evidence is None
    assert source.read_bytes() == retained.after_content
    assert provider.observe_paths_calls == [("source.txt",)]


@pytest.mark.asyncio
async def test_stale_and_physical_conflicts_never_authorize(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_bytes(b"before")
    provider, session, store, coordinator = await _runtime(tmp_path)
    stale_coordinate = _coordinate(session)
    source.write_bytes(b"external")
    await session.poll_once()
    stale = await coordinator.mutate(
        WorkspaceRepositoryMutationRequest(
            operation_ref="operation:stale",
            idempotency_key="submission:4",
            mutation_kind=RepositoryMutationKind.UPDATE,
            expected_coordinate=stale_coordinate,
            target_path="source.txt",
            expected_exists=True,
            expected_content_digest=_digest(b"before"),
            content=b"ours",
        )
    )
    assert stale.receipt.outcome is RepositoryMutationOutcome.STALE
    assert stale.evidence is None

    current = _coordinate(session)
    source.write_bytes(b"unobserved")
    conflict = await coordinator.mutate(
        WorkspaceRepositoryMutationRequest(
            operation_ref="operation:conflict",
            idempotency_key="submission:5",
            mutation_kind=RepositoryMutationKind.UPDATE,
            expected_coordinate=current,
            target_path="source.txt",
            expected_exists=True,
            expected_content_digest=_digest(b"external"),
            content=b"ours",
        )
    )
    assert conflict.receipt.outcome is RepositoryMutationOutcome.CONFLICT
    assert conflict.evidence is None
    assert source.read_bytes() == b"unobserved"
    assert store.retained_count == 0
    assert provider.poll_calls == 1


@pytest.mark.asyncio
async def test_direct_external_write_remains_observed_not_authorized(
    tmp_path: Path,
) -> None:
    _provider, session, store, _coordinator = await _runtime(tmp_path)
    resolver = WorkspaceRepositoryChangeEvidenceResolver(
        session=session,
        consumer_key="external-proof",
    )
    (tmp_path / "human.txt").write_bytes(b"human")
    await session.poll_once()
    evidence = await resolver.refresh()

    assert len(evidence) == 1
    assert evidence[0].posture is RepositoryEvidencePosture.WORKSPACE_OBSERVED
    assert evidence[0].mutation_receipt_refs == ()
    assert store.retained_count == 0


@pytest.mark.asyncio
async def test_idempotency_ref_rejects_changed_request(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    _provider, session, _store, coordinator = await _runtime(tmp_path)
    common = {
        "operation_ref": "operation:same",
        "idempotency_key": "same-key",
        "mutation_kind": RepositoryMutationKind.CREATE,
        "expected_coordinate": _coordinate(session),
        "target_path": "src/new.txt",
        "expected_exists": False,
        "expected_content_digest": None,
    }
    await coordinator.mutate(
        WorkspaceRepositoryMutationRequest(**common, content=b"one")
    )
    with pytest.raises(ValueError, match="Idempotency"):
        await coordinator.mutate(
            WorkspaceRepositoryMutationRequest(**common, content=b"two")
        )


@pytest.mark.asyncio
async def test_body_retention_is_admitted_before_filesystem_effect(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.txt"
    source.write_bytes(b"old")
    provider = ScanningProvider(tmp_path)
    session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path),
        provider=provider,
    )
    await session.start(background=False)
    coordinator = WorkspaceRepositoryMutationCoordinator(
        session=session,
        body_store=WorkspaceRepositoryOperationalBodyStore(maximum_bytes=5),
    )
    result = await coordinator.mutate(
        WorkspaceRepositoryMutationRequest(
            operation_ref="operation:retention",
            idempotency_key="submission:retention",
            mutation_kind=RepositoryMutationKind.UPDATE,
            expected_coordinate=_coordinate(session),
            target_path="source.txt",
            expected_exists=True,
            expected_content_digest=_digest(b"old"),
            content=b"newer",
        )
    )

    assert result.receipt.outcome is RepositoryMutationOutcome.CONFLICT
    assert result.receipt.error_code == "body_retention_capacity_exceeded"
    assert result.evidence is None
    assert source.read_bytes() == b"old"
    assert provider.poll_calls == 0
