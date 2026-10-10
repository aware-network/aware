from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from aware_workspace_runtime import (
    ObservationChangeKind,
    RepositoryObservationChange,
    RepositoryProviderObservation,
    RepositorySnapshotEntry,
    WorkspaceRepositoryBinding,
)


def test_repository_binding_normalizes_root_and_has_stable_operational_key(
    tmp_path: Path,
) -> None:
    binding = WorkspaceRepositoryBinding(root_path=tmp_path / ".")
    same = WorkspaceRepositoryBinding(root_path=tmp_path)

    assert binding.root_path == tmp_path.resolve()
    assert binding.binding_key == same.binding_key
    assert binding.binding_key and binding.binding_key.startswith("local-root:")


@pytest.mark.parametrize("path", ["", "/absolute.txt", "../escape.txt"])
def test_snapshot_entry_rejects_unconfined_paths(path: str) -> None:
    with pytest.raises(ValueError, match="confined and relative"):
        RepositorySnapshotEntry(path=path, size_bytes=1, modified_ns=1)


def test_provider_observation_is_sorted_unique_and_digest_stable() -> None:
    alpha = RepositorySnapshotEntry(path="alpha.txt", size_bytes=1, modified_ns=1)
    zeta = RepositorySnapshotEntry(path="zeta.txt", size_bytes=2, modified_ns=2)
    first = RepositoryProviderObservation(
        observed_at=datetime.now(UTC),
        entries=(zeta, alpha),
    )
    second = RepositoryProviderObservation(
        observed_at=datetime.now(UTC),
        entries=(alpha, zeta),
    )

    assert first.entries == (alpha, zeta)
    assert first.snapshot_digest == second.snapshot_digest

    with pytest.raises(ValueError, match="paths must be unique"):
        RepositoryProviderObservation(
            observed_at=datetime.now(UTC),
            entries=(alpha, alpha),
        )


def test_change_target_contract_is_explicit() -> None:
    entry = RepositorySnapshotEntry(path="target.txt", size_bytes=1, modified_ns=1)
    RepositoryObservationChange(
        kind=ObservationChangeKind.CREATE,
        path="target.txt",
        entry=entry,
    )
    RepositoryObservationChange(
        kind=ObservationChangeKind.DELETE,
        path="target.txt",
    )

    with pytest.raises(ValueError, match="matching target"):
        RepositoryObservationChange(
            kind=ObservationChangeKind.UPDATE,
            path="other.txt",
            entry=entry,
        )
    with pytest.raises(ValueError, match="cannot carry"):
        RepositoryObservationChange(
            kind=ObservationChangeKind.DELETE,
            path="target.txt",
            entry=entry,
        )
