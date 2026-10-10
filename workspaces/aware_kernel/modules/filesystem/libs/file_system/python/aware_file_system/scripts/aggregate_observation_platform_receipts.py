from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aware_file_system.observation_platform_contract import (
    CROSS_PLATFORM_RECEIPT_SET_SCHEMA,
    PLATFORM_RECEIPT_SCHEMA,
    SUPPORTED_PLATFORM_CLASSES,
    architecture_class,
)

SERVICE_PROTOCOL = "aware.file_system.maintained_observation_service.v2"
MAX_RECEIPT_BYTES = 16 * 1024 * 1024
REQUIRED_PLATFORM_COORDINATES = SUPPORTED_PLATFORM_CLASSES
REQUIRED_PLATFORM_GATE_CHECKS = frozenset(
    {
        "supported_platform",
        "package_coordinate",
        "evidence_coordinate",
        "four_distinct_roots",
        "multi_root_exact",
        "multi_root_watchers_active",
        "platform_watch_budget",
        "multi_root_no_orphans",
        "portable_mutations_exact",
        "restart_distribution",
        "restart_exact",
        "restart_p99",
        "restart_no_orphans",
        "restart_no_reader_leaks",
        "reconciliation_only_exact",
        "interrupted_cache_recovered",
        "truncated_cache_rebuilt",
        "journal_torn_tail_recovered",
        "journal_checkpoint_recovered",
    }
)


def aggregate_platform_receipts(
    receipt_paths: Mapping[str, Path],
    *,
    created_at: datetime | None = None,
) -> dict[str, Any]:
    required = set(REQUIRED_PLATFORM_COORDINATES)
    actual = set(receipt_paths)
    if actual != required:
        raise ValueError(
            "platform receipt set differs; "
            f"missing={sorted(required - actual)} "
            f"unexpected={sorted(actual - required)}"
        )

    receipts: dict[str, dict[str, Any]] = {}
    source_revisions: set[str] = set()
    evidence_run_ids: set[str] = set()
    for platform_key in REQUIRED_PLATFORM_COORDINATES:
        path = receipt_paths[platform_key].expanduser().resolve()
        raw = _read_bounded(path)
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"{platform_key} receipt is not valid JSON: {error.msg}"
            ) from error
        if not isinstance(value, dict):
            raise TypeError(f"{platform_key} receipt must be a JSON object")
        _validate_platform_receipt(platform_key, value)
        platform = _mapping(value, "platform", platform_key)
        artifact = _mapping(value, "artifact", platform_key)
        restart = _mapping(value, "crash_restart", platform_key)
        evidence = _mapping(value, "evidence_coordinate", platform_key)
        source_revision = str(evidence["source_revision"])
        evidence_run_id = str(evidence["run_id"])
        source_revisions.add(source_revision)
        evidence_run_ids.add(evidence_run_id)
        receipts[platform_key] = {
            "receipt_sha256": hashlib.sha256(raw).hexdigest(),
            "receipt_bytes": len(raw),
            "sys_platform": platform["sys_platform"],
            "os_name": platform["os_name"],
            "machine": platform["machine"],
            "architecture_class": platform["architecture_class"],
            "python": platform["python"],
            "target_triple": artifact["target_triple"],
            "binary_name": artifact["binary_name"],
            "binary_sha256": artifact["binary_sha256"],
            "binary_bytes": artifact["binary_bytes"],
            "service_protocol": artifact["service_protocol"],
            "restart_sample_count": restart["restart_sample_count"],
            "restart_p99_s": _mapping(restart, "duration_s", platform_key)["p99"],
            "source_revision": source_revision,
            "evidence_run_id": evidence_run_id,
            "supported_platform_class": value["supported_platform_class"],
        }

    if len(source_revisions) != 1:
        raise ValueError("platform source revisions differ")
    if len(evidence_run_ids) != 1:
        raise ValueError("platform evidence run ids differ")
    source_revision = next(iter(source_revisions))
    evidence_run_id = next(iter(evidence_run_ids))

    timestamp = created_at or datetime.now(UTC)
    return {
        "schema": CROSS_PLATFORM_RECEIPT_SET_SCHEMA,
        "created_at": timestamp.astimezone(UTC).isoformat(),
        "required_platforms": list(REQUIRED_PLATFORM_COORDINATES),
        "validated_platforms": list(receipts),
        "evidence_coordinate": {
            "source_revision": source_revision,
            "run_id": evidence_run_id,
        },
        "receipts": receipts,
        "receipt_set_gate": {
            "passed": True,
            "checks": {
                "exact_platform_set": True,
                "platform_identity_exact": True,
                "target_identity_exact": True,
                "individual_platform_gates_passed": True,
                "required_platform_checks_present": True,
                "workload_floors_preserved": True,
                "individual_routes_not_self_authorized": True,
                "input_receipts_digest_bound": True,
                "source_revision_exact": True,
                "evidence_run_exact": True,
            },
        },
        "production_route_authorized": False,
        "production_gate_passed": False,
        "authorization_blocker": (
            "Cross-platform evidence is complete but routing remains a separate "
            "explicit release decision."
        ),
    }


def _validate_platform_receipt(
    platform_key: str,
    value: Mapping[str, Any],
) -> None:
    coordinate = REQUIRED_PLATFORM_COORDINATES[platform_key]
    if value.get("schema") != PLATFORM_RECEIPT_SCHEMA:
        raise ValueError(f"{platform_key} receipt schema differs")
    platform = _mapping(value, "platform", platform_key)
    if platform.get("key") != platform_key:
        raise ValueError(f"{platform_key} receipt label differs")
    if platform.get("sys_platform") != coordinate.sys_platform:
        raise ValueError(f"{platform_key} sys.platform coordinate differs")
    if platform.get("os_name") != coordinate.os_name:
        raise ValueError(f"{platform_key} OS family coordinate differs")
    if not _non_empty_string(platform.get("machine")) or not _non_empty_string(
        platform.get("python")
    ):
        raise ValueError(f"{platform_key} host coordinate is incomplete")
    host_architecture = architecture_class(str(platform["machine"]))
    if (
        platform.get("architecture_class") != host_architecture
        or host_architecture != coordinate.architecture_class
    ):
        raise ValueError(f"{platform_key} architecture class differs")
    if value.get("supported_platform_class") != coordinate.as_receipt():
        raise ValueError(f"{platform_key} supported platform class differs")

    evidence = _mapping(value, "evidence_coordinate", platform_key)
    source_revision = evidence.get("source_revision")
    evidence_run_id = evidence.get("run_id")
    if not isinstance(source_revision, str) or not _is_source_revision(source_revision):
        raise ValueError(f"{platform_key} source revision is invalid")
    if (
        not _non_empty_string(evidence_run_id)
        or len(str(evidence_run_id).encode("utf-8")) > 128
        or any(character in str(evidence_run_id) for character in "\r\n")
    ):
        raise ValueError(f"{platform_key} evidence run id is invalid")

    artifact = _mapping(value, "artifact", platform_key)
    target = artifact.get("target_triple")
    if target != coordinate.target_triple:
        raise ValueError(f"{platform_key} target triple differs")
    if artifact.get("service_protocol") != SERVICE_PROTOCOL:
        raise ValueError(f"{platform_key} service protocol differs")
    digest = artifact.get("binary_sha256")
    if not isinstance(digest, str) or not _is_sha256(digest):
        raise ValueError(f"{platform_key} binary digest is invalid")
    if (
        not isinstance(artifact.get("binary_bytes"), int)
        or artifact["binary_bytes"] <= 0
    ):
        raise ValueError(f"{platform_key} binary byte count is invalid")
    if not _non_empty_string(artifact.get("binary_name")):
        raise ValueError(f"{platform_key} binary name is invalid")

    gate = _mapping(value, "platform_gate", platform_key)
    checks = _mapping(gate, "checks", platform_key)
    if (
        gate.get("passed") is not True
        or not checks
        or not REQUIRED_PLATFORM_GATE_CHECKS.issubset(checks)
        or not all(check is True for check in checks.values())
    ):
        raise ValueError(f"{platform_key} platform gate did not pass exactly")
    if (
        gate.get("production_route_authorized") is not False
        or gate.get("platforms_authorized") != []
        or value.get("production_gate_passed") is not False
    ):
        raise ValueError(f"{platform_key} receipt attempted to self-authorize")

    multi = _mapping(value, "multi_repository", platform_key)
    repository_count = multi.get("repository_count")
    if (
        not isinstance(repository_count, int)
        or repository_count < 4
        or multi.get("exact_mutation_count") != repository_count
        or multi.get("orphan_process_ids") != []
    ):
        raise ValueError(f"{platform_key} multi-repository workload is incomplete")
    watcher_health = multi.get("watcher_health")
    if not isinstance(watcher_health, list) or len(watcher_health) != repository_count:
        raise ValueError(f"{platform_key} watcher health cardinality differs")
    if any(
        not isinstance(health, dict) or health.get("state") != "active"
        for health in watcher_health
    ):
        raise ValueError(f"{platform_key} watcher did not remain active")

    restart = _mapping(value, "crash_restart", platform_key)
    sample_count = restart.get("restart_sample_count")
    duration = _mapping(restart, "duration_s", platform_key)
    if (
        not isinstance(sample_count, int)
        or sample_count < 30
        or restart.get("success_count") != sample_count
        or restart.get("orphan_process_ids") != []
        or restart.get("leaked_reader_threads") != []
        or not isinstance(duration.get("p99"), (int, float))
        or duration["p99"] > 2.0
    ):
        raise ValueError(f"{platform_key} restart workload is incomplete")

    mutations = _mapping(value, "portable_mutations", platform_key)
    if (
        mutations.get("passed") is not True
        or not isinstance(mutations.get("burst_file_count"), int)
        or mutations["burst_file_count"] < 64
    ):
        raise ValueError(f"{platform_key} portable mutation workload is incomplete")

    journal_tail = _mapping(value, "journal_tail", platform_key)
    first_generation = journal_tail.get("first_generation")
    second_generation = journal_tail.get("second_generation")
    recovered_generation = journal_tail.get("recovered_generation")
    first_journal_bytes = journal_tail.get("first_journal_bytes")
    recovered_journal_bytes = journal_tail.get("recovered_journal_bytes")
    tail_bytes_removed = journal_tail.get("tail_bytes_removed")
    expected_tail_bytes_removed = journal_tail.get("expected_tail_bytes_removed")
    if (
        journal_tail.get("passed") is not True
        or not isinstance(first_generation, int)
        or second_generation != first_generation + 1
        or recovered_generation != first_generation
        or not isinstance(first_journal_bytes, int)
        or first_journal_bytes <= 0
        or recovered_journal_bytes != first_journal_bytes
        or not isinstance(tail_bytes_removed, int)
        or tail_bytes_removed <= 0
        or expected_tail_bytes_removed != tail_bytes_removed
        or journal_tail.get("digest_stable") is not True
        or not _non_empty_string(journal_tail.get("digest_backend_kind"))
    ):
        raise ValueError(f"{platform_key} journal tail recovery is incomplete")

    journal_checkpoint = _mapping(value, "journal_checkpoint", platform_key)
    checkpoint_generation = journal_checkpoint.get("checkpoint_generation")
    if (
        journal_checkpoint.get("passed") is not True
        or journal_checkpoint.get("mutation_sample_count") != 128
        or journal_checkpoint.get("journal_append_count") != 127
        or journal_checkpoint.get("checkpoint_count") != 1
        or journal_checkpoint.get("checkpoint_sample_indices") != [127]
        or journal_checkpoint.get("maximum_journal_frame_count") != 127
        or journal_checkpoint.get("journal_bytes_after_checkpoint") != 0
        or not isinstance(checkpoint_generation, int)
        or journal_checkpoint.get("recovered_generation") != checkpoint_generation
        or journal_checkpoint.get("digest_stable") is not True
        or not _non_empty_string(journal_checkpoint.get("digest_backend_kind"))
    ):
        raise ValueError(f"{platform_key} journal checkpoint recovery is incomplete")


def _mapping(
    value: Mapping[str, Any], key: str, platform_key: str
) -> Mapping[str, Any]:
    candidate = value.get(key)
    if not isinstance(candidate, dict):
        raise TypeError(f"{platform_key} receipt field {key!r} is invalid")
    return candidate


def _read_bounded(path: Path) -> bytes:
    if not path.is_file():
        raise ValueError(f"platform receipt is unavailable: {path}")
    size = path.stat().st_size
    if size <= 0 or size > MAX_RECEIPT_BYTES:
        raise ValueError(f"platform receipt byte count is invalid: {path}")
    return path.read_bytes()


def _non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(
        character in "0123456789abcdef" for character in value
    )


def _is_source_revision(value: str) -> bool:
    return len(value) in {40, 64} and all(
        character in "0123456789abcdef" for character in value
    )


def _receipt_argument(value: str) -> tuple[str, Path]:
    platform_key, separator, raw_path = value.partition("=")
    if not separator or not platform_key or not raw_path:
        raise argparse.ArgumentTypeError("receipt must use PLATFORM=PATH")
    return platform_key, Path(raw_path)


def main(arguments: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Aggregate exact Linux/macOS/Windows observation receipts."
    )
    parser.add_argument(
        "--receipt",
        action="append",
        required=True,
        type=_receipt_argument,
        metavar="PLATFORM=PATH",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--compact", action="store_true")
    values = parser.parse_args(arguments)
    receipt_paths: dict[str, Path] = {}
    for platform_key, path in values.receipt:
        if platform_key in receipt_paths:
            parser.error(f"duplicate platform receipt: {platform_key}")
        receipt_paths[platform_key] = path
    try:
        receipt = aggregate_platform_receipts(receipt_paths)
    except (TypeError, ValueError) as error:
        parser.error(str(error))
    encoded = (
        json.dumps(
            receipt,
            indent=None if values.compact else 2,
            sort_keys=True,
            separators=(",", ":") if values.compact else None,
        )
        + "\n"
    )
    output = values.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(encoded, encoding="utf-8")
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
