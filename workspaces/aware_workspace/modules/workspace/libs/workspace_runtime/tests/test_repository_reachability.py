from __future__ import annotations

import os
import subprocess
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from aware_workspace_runtime import (
    RepositoryPathQuery,
    RepositoryProviderObservation,
    RepositoryProviderQueryObservation,
    WorkspaceRepositoryBinding,
    WorkspaceRepositoryObservationSession,
    WorkspaceRepositoryReachabilityAuthorityGrade,
    WorkspaceRepositoryReachabilityError,
    WorkspaceRepositoryReachabilityPosture,
    WorkspaceRepositoryReachabilityReader,
    WorkspaceRepositoryReachabilityRequest,
    WorkspaceRepositoryRevisionPosture,
    WorkspaceRepositoryRevisionReachability,
)
from aware_workspace_runtime import repository_reachability as reachability_module


class _Provider:
    def __init__(self, root_path: Path) -> None:
        self._root_path = root_path.resolve()

    @property
    def root_path(self) -> Path:
        return self._root_path

    async def initialize(self) -> RepositoryProviderObservation:
        return RepositoryProviderObservation(observed_at=datetime.now(UTC), entries=())

    async def poll(self) -> RepositoryProviderObservation:
        return RepositoryProviderObservation(observed_at=datetime.now(UTC), entries=())

    async def query(
        self, request: RepositoryPathQuery
    ) -> RepositoryProviderQueryObservation:
        del request
        raise AssertionError("repository reachability does not use provider query")

    async def close(self) -> None:
        return None


def _git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ("git", "-C", str(root), *arguments),
        check=True,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        env={
            **os.environ,
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": os.devnull,
            "LC_ALL": "C",
        },
    )
    return completed.stdout.decode("utf-8").strip()


def _repository(root: Path) -> tuple[str, str]:
    root.mkdir()
    _git(root, "init", "--quiet", "--initial-branch=main")
    (root / "tracked.txt").write_text("one\n", encoding="utf-8")
    _git(root, "add", "tracked.txt")
    _git(
        root,
        "-c",
        "user.name=Aware Test",
        "-c",
        "user.email=aware@example.invalid",
        "commit",
        "--quiet",
        "-m",
        "initial",
    )
    head = _git(root, "rev-parse", "HEAD")
    tree = _git(root, "rev-parse", "HEAD^{tree}")
    orphan = _git(
        root,
        "-c",
        "user.name=Aware Test",
        "-c",
        "user.email=aware@example.invalid",
        "commit-tree",
        tree,
        "-m",
        "unreferenced",
    )
    assert orphan != head
    return head, orphan


async def _session(root: Path) -> WorkspaceRepositoryObservationSession:
    binding = WorkspaceRepositoryBinding(root)
    session = WorkspaceRepositoryObservationSession(
        binding=binding,
        provider=_Provider(root),
    )
    await session.start(background=False)
    return session


def _request(*revisions: str) -> WorkspaceRepositoryReachabilityRequest:
    return WorkspaceRepositoryReachabilityRequest(
        request_ref="repository-reachability-request:focused-proof",
        revision_refs=tuple(sorted(revisions)),
    )


@pytest.mark.asyncio
async def test_reads_complete_ref_membership_and_nonmembership_without_effects(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repository"
    head, orphan = _repository(root)
    missing = "f" * 40
    session = await _session(root)
    reader = WorkspaceRepositoryReachabilityReader(session)

    result = await reader.observe(_request(head, orphan, missing))

    assert result.posture is WorkspaceRepositoryReachabilityPosture.COMPLETE
    assert (
        result.authority_grade
        is WorkspaceRepositoryReachabilityAuthorityGrade.PORTABLE_INPUT
    )
    assert not hasattr(result, "admission")
    entries = {entry.revision_ref: entry for entry in result.entries}
    assert entries[head].posture is WorkspaceRepositoryRevisionPosture.REACHABLE
    assert "HEAD" in entries[head].retaining_ref_names
    assert "refs/heads/main" in entries[head].retaining_ref_names
    assert entries[head].object_type == "commit"
    assert entries[head].object_size is not None
    assert entries[orphan].posture is WorkspaceRepositoryRevisionPosture.NOT_REACHABLE
    assert entries[missing].posture is WorkspaceRepositoryRevisionPosture.NOT_REACHABLE
    assert result.counters.repository_writes == 0
    assert result.counters.workspace_writes == 0
    assert "root_path" not in result.canonical_bytes().decode("utf-8")
    assert "git_directory" not in result.canonical_bytes().decode("utf-8")

    replay = await reader.observe(result.request)
    assert replay is not result
    assert replay.canonical_bytes() == result.canonical_bytes()
    reader.close()
    assert reader._workspace_coordinate_snapshot is None
    with pytest.raises(
        WorkspaceRepositoryReachabilityError,
        match="repository_reachability_reader_closed",
    ):
        await reader.observe(result.request)
    await session.stop()


def test_contracts_reject_invalid_construction_and_evidence() -> None:
    with pytest.raises(ValueError, match="revisions_invalid"):
        WorkspaceRepositoryReachabilityRequest(
            "repository-reachability-request:invalid",
            ("f" * 40, "a" * 40),
        )
    with pytest.raises(ValueError, match="evidence_digest_invalid"):
        WorkspaceRepositoryRevisionReachability(
            "a" * 40,
            WorkspaceRepositoryRevisionPosture.NOT_REACHABLE,
            None,
            None,
            (),
            "sha256:" + ("0" * 64),
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("poison", "blocker"),
    [
        ("shallow", "repository_shallow_boundary_ambiguous"),
        ("alternates", "repository_alternates_present"),
        ("grafts", "repository_grafts_present"),
        ("replace", "repository_replace_refs_present"),
    ],
)
async def test_ambiguous_git_authority_returns_typed_blocked_result(
    tmp_path: Path,
    poison: str,
    blocker: str,
) -> None:
    root = tmp_path / poison
    head, orphan = _repository(root)
    git_dir = Path(_git(root, "rev-parse", "--absolute-git-dir"))
    common_dir = Path(_git(root, "rev-parse", "--git-common-dir"))
    if not common_dir.is_absolute():
        common_dir = (root / common_dir).resolve()
    if poison == "shallow":
        (git_dir / "shallow").write_text(f"{head}\n", encoding="ascii")
    elif poison == "alternates":
        path = common_dir / "objects" / "info" / "alternates"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("/foreign/objects\n", encoding="utf-8")
    elif poison == "grafts":
        path = common_dir / "info" / "grafts"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{head} {orphan}\n", encoding="ascii")
    else:
        _git(root, "update-ref", f"refs/replace/{head}", orphan)
    session = await _session(root)

    result = await WorkspaceRepositoryReachabilityReader(session).observe(
        _request(head)
    )

    assert result.posture is WorkspaceRepositoryReachabilityPosture.BLOCKED
    assert result.blocker_codes == (blocker,)
    assert (
        result.authority_grade
        is WorkspaceRepositoryReachabilityAuthorityGrade.PORTABLE_INPUT
    )
    assert result.counters.repository_writes == 0
    assert result.counters.workspace_writes == 0
    await session.stop()


@pytest.mark.asyncio
async def test_ref_movement_between_snapshots_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "movement"
    head, orphan = _repository(root)
    session = await _session(root)
    original = reachability_module._repository_snapshot
    calls = 0

    def moving_snapshot(
        repository_root: Path,
        counters: reachability_module._ReadCounters,
    ) -> reachability_module._RepositorySnapshot:
        nonlocal calls
        calls += 1
        if calls == 2:
            _git(repository_root, "update-ref", "refs/heads/moved", orphan)
        return original(repository_root, counters)

    monkeypatch.setattr(reachability_module, "_repository_snapshot", moving_snapshot)
    result = await WorkspaceRepositoryReachabilityReader(session).observe(
        _request(head)
    )
    assert result.posture is WorkspaceRepositoryReachabilityPosture.BLOCKED
    assert result.blocker_codes == ("repository_reachability_repository_moved",)
    await session.stop()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "movement",
    ["repository", "snapshot", "epoch", "restart", "binding"],
)
async def test_portable_replay_revalidates_authority_movement(
    tmp_path: Path,
    movement: str,
) -> None:
    root = tmp_path / movement
    head, orphan = _repository(root)
    session = await _session(root)
    reader = WorkspaceRepositoryReachabilityReader(session)
    result = await reader.observe(_request(head))

    if movement == "repository":
        _git(root, "update-ref", "refs/heads/moved-after-admission", orphan)
        replay = await reader.observe(result.request)
        assert replay.posture is WorkspaceRepositoryReachabilityPosture.BLOCKED
        assert replay.blocker_codes == ("repository_reachability_evidence_moved",)
    elif movement == "snapshot":
        object.__setattr__(session, "_snapshot", replace(session.current_snapshot))
        with pytest.raises(
            WorkspaceRepositoryReachabilityError,
            match="repository_reachability_workspace_moved",
        ):
            await reader.observe(result.request)
    elif movement == "epoch":
        object.__setattr__(session, "_epoch", "a" * 32)
        with pytest.raises(
            WorkspaceRepositoryReachabilityError,
            match="repository_reachability_workspace_moved",
        ):
            await reader.observe(result.request)
    elif movement == "restart":
        await session.stop()
        initial_epoch = result.workspace_epoch
        await session.start(background=False)
        assert session.epoch != initial_epoch
        with pytest.raises(
            WorkspaceRepositoryReachabilityError,
            match="repository_reachability_workspace_moved",
        ):
            await reader.observe(result.request)
    else:
        object.__setattr__(session.binding, "filter_version", "foreign-filter-v1")
        with pytest.raises(
            WorkspaceRepositoryReachabilityError,
            match="repository_reachability_workspace_unavailable",
        ):
            await reader.observe(result.request)
    if session.authority_admitted:
        await session.stop()


@pytest.mark.asyncio
async def test_replay_rejects_missing_previously_reachable_ancestor(
    tmp_path: Path,
) -> None:
    root = tmp_path / "missing-ancestor"
    first, _ = _repository(root)
    (root / "tracked.txt").write_text("two\n", encoding="utf-8")
    _git(root, "add", "tracked.txt")
    _git(
        root,
        "-c",
        "user.name=Aware Test",
        "-c",
        "user.email=aware@example.invalid",
        "commit",
        "--quiet",
        "-m",
        "second",
    )
    session = await _session(root)
    reader = WorkspaceRepositoryReachabilityReader(session)
    initial = await reader.observe(_request(first))
    assert initial.entries[0].posture is WorkspaceRepositoryRevisionPosture.REACHABLE

    object_path = root / ".git" / "objects" / first[:2] / first[2:]
    object_path.unlink()
    replay = await reader.observe(initial.request)

    assert replay.posture is WorkspaceRepositoryReachabilityPosture.BLOCKED
    assert replay.blocker_codes == ("repository_reachability_evidence_moved",)
    await session.stop()


@pytest.mark.asyncio
async def test_caller_created_session_produces_no_nominal_admission(
    tmp_path: Path,
) -> None:
    root = tmp_path / "caller-session"
    head, _ = _repository(root)
    session = await _session(root)
    reader = WorkspaceRepositoryReachabilityReader(session)

    result = await reader.observe(_request(head))

    assert (
        result.authority_grade
        is WorkspaceRepositoryReachabilityAuthorityGrade.PORTABLE_INPUT
    )
    assert not hasattr(reachability_module, "WorkspaceRepositoryReachabilityAdmission")
    assert not hasattr(reader, "require")
    assert not hasattr(result, "admission")
    await session.stop()


def test_production_contains_only_closed_git_read_operations() -> None:
    source = Path(reachability_module.__file__).read_text(encoding="utf-8")
    assert "def _git(" not in source
    assert "def _git_status(" not in source
    assert "def _git_result(" not in source
    assert "*arguments" not in source
    for mutation in ("update-ref", "checkout", "reset", "commit-tree", "hash-object"):
        assert mutation not in source


@pytest.mark.asyncio
async def test_git_environment_cannot_redirect_observation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "retained"
    foreign = tmp_path / "foreign"
    head, _ = _repository(root)
    _repository(foreign)
    (foreign / "foreign.txt").write_text("foreign\n", encoding="utf-8")
    _git(foreign, "add", "foreign.txt")
    _git(
        foreign,
        "-c",
        "user.name=Aware Test",
        "-c",
        "user.email=aware@example.invalid",
        "commit",
        "--quiet",
        "-m",
        "foreign",
    )
    foreign_head = _git(foreign, "rev-parse", "HEAD")
    monkeypatch.setenv("GIT_DIR", str(foreign / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(foreign))
    monkeypatch.setenv("GIT_REPLACE_REF_BASE", "refs/foreign/")
    session = await _session(root)

    result = await WorkspaceRepositoryReachabilityReader(session).observe(
        _request(*sorted((head, foreign_head)))
    )

    entries = {entry.revision_ref: entry for entry in result.entries}
    assert entries[head].posture is WorkspaceRepositoryRevisionPosture.REACHABLE
    assert (
        entries[foreign_head].posture
        is WorkspaceRepositoryRevisionPosture.NOT_REACHABLE
    )
    await session.stop()


@pytest.mark.asyncio
async def test_linked_worktree_uses_exact_common_git_directory(tmp_path: Path) -> None:
    root = tmp_path / "source"
    head, _ = _repository(root)
    worktree = tmp_path / "linked"
    _git(root, "worktree", "add", "--quiet", "--detach", str(worktree), head)
    session = await _session(worktree)

    result = await WorkspaceRepositoryReachabilityReader(session).observe(
        _request(head)
    )

    assert result.posture is WorkspaceRepositoryReachabilityPosture.COMPLETE
    assert result.entries[0].posture is WorkspaceRepositoryRevisionPosture.REACHABLE
    assert result.git_common_directory_digest.startswith("sha256:")
    await session.stop()
