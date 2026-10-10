from __future__ import annotations

from pathlib import Path

import pytest

from aware_file_system.native_observation_service import NativeObservationServiceError
from aware_file_system.scripts.package_native_observation_service import (
    NATIVE_OBSERVATION_PACKAGE_SCHEMA,
    assert_reproducible_native_packages,
    package_native_observation_service,
)


def test_locked_native_package_launches_without_cargo_on_runtime_path(
    tmp_path: Path,
) -> None:
    receipt = package_native_observation_service(
        artifact_root=tmp_path / "artifacts",
        target_dir=tmp_path / "target",
    )

    assert receipt["schema"] == NATIVE_OBSERVATION_PACKAGE_SCHEMA
    assert receipt["build"]["locked"] is True
    assert receipt["build"]["release"] is True
    assert len(receipt["binary_sha256"]) == 64
    assert receipt["binary_bytes"] > 0
    assert receipt["platform"]["sys_platform"]
    assert receipt["platform"]["machine"]
    assert Path(receipt["binary_path"]).is_file()
    assert Path(receipt["manifest_path"]).is_file()
    assert receipt["runtime_verification"] == {
        "passed": True,
        "cargo_available_on_path": False,
        "watch_mode": "reconciliation_only",
        "snapshot_entry_count": 1,
    }
    assert receipt["production_route_authorized"] is False


def test_reproducibility_assertion_rejects_digest_drift() -> None:
    first = {
        "schema": NATIVE_OBSERVATION_PACKAGE_SCHEMA,
        "target_triple": "test-target",
        "binary_name": "observer",
        "binary_sha256": "a" * 64,
        "binary_bytes": 10,
        "service_protocol": "protocol",
        "observation_schema": "schema",
    }
    second = dict(first, binary_sha256="b" * 64)

    with pytest.raises(NativeObservationServiceError, match="not reproducible"):
        assert_reproducible_native_packages(first, second)


def test_package_binds_and_reproduces_exact_evidence_coordinate(
    tmp_path: Path,
) -> None:
    coordinate = {
        "source_revision": "a" * 40,
        "run_id": "run-123",
    }
    first = package_native_observation_service(
        artifact_root=tmp_path / "one",
        target_dir=tmp_path / "target-one",
        source_revision=coordinate["source_revision"],
        evidence_run_id=coordinate["run_id"],
    )
    second = package_native_observation_service(
        artifact_root=tmp_path / "two",
        target_dir=tmp_path / "target-two",
        source_revision=coordinate["source_revision"],
        evidence_run_id=coordinate["run_id"],
    )

    assert first["evidence_coordinate"] == coordinate
    assert second["evidence_coordinate"] == coordinate
    assert_reproducible_native_packages(first, second)

    drifted = dict(second, evidence_coordinate=dict(coordinate, run_id="run-456"))
    with pytest.raises(NativeObservationServiceError, match="evidence_coordinate"):
        assert_reproducible_native_packages(first, drifted)


def test_package_rejects_partial_or_malformed_evidence_coordinate(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="provided together"):
        package_native_observation_service(
            artifact_root=tmp_path / "partial",
            target_dir=tmp_path / "partial-target",
            source_revision="a" * 40,
        )
    with pytest.raises(ValueError, match="40- or 64-character"):
        package_native_observation_service(
            artifact_root=tmp_path / "malformed",
            target_dir=tmp_path / "malformed-target",
            source_revision="not-a-revision",
            evidence_run_id="run-123",
        )
