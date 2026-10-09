from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

import pytest
from aware_file_system.observation_platform_contract import (
    PLATFORM_RECEIPT_SCHEMA,
    SUPPORTED_PLATFORM_CLASSES,
)
from aware_file_system.scripts.aggregate_observation_platform_receipts import (
    CROSS_PLATFORM_RECEIPT_SET_SCHEMA,
    REQUIRED_PLATFORM_GATE_CHECKS,
    aggregate_platform_receipts,
    main,
)


def _receipt(platform_key: str) -> dict[str, object]:
    machines = {
        "linux": "x86_64",
        "macos": "arm64",
        "windows": "AMD64",
    }
    coordinate = SUPPORTED_PLATFORM_CLASSES[platform_key]
    digest_character = {"linux": "a", "macos": "b", "windows": "c"}[platform_key]
    return {
        "schema": PLATFORM_RECEIPT_SCHEMA,
        "platform": {
            "key": platform_key,
            "sys_platform": coordinate.sys_platform,
            "os_name": coordinate.os_name,
            "machine": machines[platform_key],
            "architecture_class": coordinate.architecture_class,
            "python": "3.12.0",
        },
        "supported_platform_class": coordinate.as_receipt(),
        "artifact": {
            "target_triple": coordinate.target_triple,
            "binary_name": "aware-file-system-native-observation-service",
            "binary_sha256": digest_character * 64,
            "binary_bytes": 1234,
            "service_protocol": ("aware.file_system.maintained_observation_service.v2"),
        },
        "evidence_coordinate": {
            "source_revision": "d" * 40,
            "run_id": "test-run-123",
        },
        "multi_repository": {
            "repository_count": 4,
            "exact_mutation_count": 4,
            "orphan_process_ids": [],
            "watcher_health": [{"state": "active"} for _ in range(4)],
        },
        "crash_restart": {
            "restart_sample_count": 30,
            "success_count": 30,
            "duration_s": {"p99": 0.25},
            "orphan_process_ids": [],
            "leaked_reader_threads": [],
        },
        "portable_mutations": {"passed": True, "burst_file_count": 64},
        "journal_tail": {
            "passed": True,
            "first_generation": 2,
            "second_generation": 3,
            "recovered_generation": 2,
            "first_journal_bytes": 271,
            "recovered_journal_bytes": 271,
            "tail_bytes_removed": 264,
            "expected_tail_bytes_removed": 264,
            "digest_stable": True,
            "digest_backend_kind": "rustcrypto_sha2_asm_optimized",
        },
        "journal_checkpoint": {
            "passed": True,
            "mutation_sample_count": 128,
            "journal_append_count": 127,
            "checkpoint_count": 1,
            "checkpoint_sample_indices": [127],
            "maximum_journal_frame_count": 127,
            "maximum_journal_bytes": 32768,
            "journal_bytes_after_checkpoint": 0,
            "checkpoint_generation": 129,
            "recovered_generation": 129,
            "digest_stable": True,
            "digest_backend_kind": "rustcrypto_sha2_asm_optimized",
        },
        "platform_gate": {
            "passed": True,
            "checks": dict.fromkeys(REQUIRED_PLATFORM_GATE_CHECKS, True),
            "platforms_authorized": [],
            "production_route_authorized": False,
        },
        "production_gate_passed": False,
    }


def _write_receipts(root: Path) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for platform_key in ("linux", "macos", "windows"):
        path = root / f"{platform_key}.json"
        path.write_text(json.dumps(_receipt(platform_key)), encoding="utf-8")
        paths[platform_key] = path
    return paths


def test_aggregate_requires_and_binds_three_exact_platform_receipts(
    tmp_path: Path,
) -> None:
    paths = _write_receipts(tmp_path)
    created_at = datetime(2026, 8, 20, 16, 0, tzinfo=UTC)

    receipt = aggregate_platform_receipts(paths, created_at=created_at)

    assert receipt["schema"] == CROSS_PLATFORM_RECEIPT_SET_SCHEMA
    assert receipt["required_platforms"] == ["linux", "macos", "windows"]
    assert receipt["validated_platforms"] == ["linux", "macos", "windows"]
    assert receipt["receipt_set_gate"]["passed"] is True  # type: ignore[index]
    assert receipt["production_route_authorized"] is False
    assert receipt["production_gate_passed"] is False
    assert receipt["evidence_coordinate"] == {
        "source_revision": "d" * 40,
        "run_id": "test-run-123",
    }
    assert all(
        len(value["receipt_sha256"]) == 64
        for value in receipt["receipts"].values()  # type: ignore[union-attr]
    )


def test_cli_writes_one_atomic_compact_receipt_set(tmp_path: Path) -> None:
    paths = _write_receipts(tmp_path)
    output = tmp_path / "aggregate" / "receipt-set.json"

    assert (
        main(
            [
                *(
                    item
                    for key, path in paths.items()
                    for item in ("--receipt", f"{key}={path}")
                ),
                "--output",
                str(output),
                "--compact",
            ]
        )
        == 0
    )

    receipt = json.loads(output.read_text(encoding="utf-8"))
    assert receipt["receipt_set_gate"]["passed"] is True
    assert not tuple(output.parent.glob(f".{output.name}.*.tmp"))


def test_aggregate_rejects_missing_or_unexpected_platform(tmp_path: Path) -> None:
    paths = _write_receipts(tmp_path)
    paths.pop("windows")
    paths["linux-copy"] = paths["linux"]

    with pytest.raises(ValueError, match="missing=.*windows.*unexpected=.*linux-copy"):
        aggregate_platform_receipts(paths)


@pytest.mark.parametrize(
    ("platform_key", "mutation", "message"),
    (
        (
            "macos",
            lambda value: value["platform"].__setitem__("sys_platform", "linux"),
            "sys.platform coordinate differs",
        ),
        (
            "windows",
            lambda value: value["artifact"].__setitem__(
                "target_triple", "x86_64-pc-windows-gnu"
            ),
            "target triple differs",
        ),
        (
            "macos",
            lambda value: value["platform"].update(
                machine="x86_64", architecture_class="x86_64"
            ),
            "architecture class differs",
        ),
        (
            "linux",
            lambda value: value["supported_platform_class"].__setitem__(
                "key", "linux_arm64"
            ),
            "supported platform class differs",
        ),
        (
            "linux",
            lambda value: value["platform_gate"].__setitem__(
                "production_route_authorized", True
            ),
            "attempted to self-authorize",
        ),
        (
            "linux",
            lambda value: value["crash_restart"].__setitem__(
                "restart_sample_count", 29
            ),
            "restart workload is incomplete",
        ),
        (
            "windows",
            lambda value: value["platform_gate"]["checks"].pop(
                "journal_torn_tail_recovered"
            ),
            "platform gate did not pass exactly",
        ),
        (
            "macos",
            lambda value: value["journal_tail"].__setitem__("recovered_generation", 3),
            "journal tail recovery is incomplete",
        ),
        (
            "windows",
            lambda value: value["journal_checkpoint"].__setitem__(
                "checkpoint_sample_indices", [126]
            ),
            "journal checkpoint recovery is incomplete",
        ),
    ),
)
def test_aggregate_rejects_substitution_authorization_and_reduced_workload(
    tmp_path: Path,
    platform_key: str,
    mutation: object,
    message: str,
) -> None:
    paths = _write_receipts(tmp_path)
    value = deepcopy(_receipt(platform_key))
    mutation(value)  # type: ignore[operator]
    paths[platform_key].write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        aggregate_platform_receipts(paths)


@pytest.mark.parametrize(
    ("platform_key", "coordinate_key", "coordinate_value", "message"),
    (
        ("macos", "source_revision", "e" * 40, "source revisions differ"),
        ("windows", "run_id", "different-run", "evidence run ids differ"),
        ("linux", "source_revision", "not-a-revision", "source revision is invalid"),
        ("linux", "run_id", "", "evidence run id is invalid"),
    ),
)
def test_aggregate_rejects_cross_revision_or_cross_run_receipts(
    tmp_path: Path,
    platform_key: str,
    coordinate_key: str,
    coordinate_value: str,
    message: str,
) -> None:
    paths = _write_receipts(tmp_path)
    value = deepcopy(_receipt(platform_key))
    value["evidence_coordinate"][coordinate_key] = coordinate_value
    paths[platform_key].write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        aggregate_platform_receipts(paths)
