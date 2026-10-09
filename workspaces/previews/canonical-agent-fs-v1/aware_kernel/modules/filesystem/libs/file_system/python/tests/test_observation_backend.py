from __future__ import annotations

from pathlib import Path

import pytest

from aware_file_system.native_observation_service import (
    RustObservationServiceBuildConfig,
    prepare_rust_observation_service_binary,
)
from aware_file_system.observation_backend import (
    ObservationBackendMode,
    build_observation_backend,
)


@pytest.fixture(scope="module")
def observation_service_binary(tmp_path_factory: pytest.TempPathFactory) -> Path:
    target_dir = tmp_path_factory.mktemp("observation-backend-target")
    return prepare_rust_observation_service_binary(
        RustObservationServiceBuildConfig(target_dir=target_dir)
    )


def test_backend_selection_is_explicit(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    with pytest.raises(ValueError, match="unsupported observation backend mode"):
        build_observation_backend(
            mode="auto",
            workspace_root=root,
            cache_path=tmp_path / "cache",
        )
    with pytest.raises(ValueError, match="binary_path is required"):
        build_observation_backend(
            mode=ObservationBackendMode.RUST_PRIMARY,
            workspace_root=root,
            cache_path=tmp_path / "cache",
        )


def test_rust_primary_backend_reuses_maintained_snapshot_without_idle_scan(
    tmp_path: Path,
    observation_service_binary: Path,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "source.txt").write_text("source\n", encoding="utf-8")
    backend = build_observation_backend(
        mode=ObservationBackendMode.RUST_PRIMARY,
        workspace_root=root,
        cache_path=tmp_path / "cache",
        binary_path=observation_service_binary,
    )
    try:
        initial = backend.initialize("initial")
        assert initial.report["status"] == "exact"
        idle = backend.poll("idle")
        assert idle.report["status"] == "maintained"
        assert idle.report["scan_ns"] == 0
        assert idle.snapshot is initial.snapshot
        assert idle.snapshot.inventory_digest == initial.snapshot.inventory_digest
    finally:
        backend.close()


def test_rust_shadow_backend_uses_one_shot_reference_without_second_watcher(
    tmp_path: Path,
    observation_service_binary: Path,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    source = root / "source.txt"
    source.write_text("before\n", encoding="utf-8")
    backend = build_observation_backend(
        mode=ObservationBackendMode.RUST_SHADOW,
        workspace_root=root,
        cache_path=tmp_path / "cache",
        binary_path=observation_service_binary,
        shadow_sample_every=1,
    )
    try:
        initial = backend.initialize("initial")
        assert initial.shadow_receipt is not None
        assert initial.shadow_receipt["exact_parity"] is True
        assert initial.shadow_receipt["second_watcher_started"] is False

        source.write_text("after-with-new-size\n", encoding="utf-8")
        changed = backend.poll("changed")
        assert changed.report["modified"] == ["source.txt"]
        assert changed.shadow_receipt is not None
        assert changed.shadow_receipt["exact_parity"] is True
    finally:
        backend.close()
