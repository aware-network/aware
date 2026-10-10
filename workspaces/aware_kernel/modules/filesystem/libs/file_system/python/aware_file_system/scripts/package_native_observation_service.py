from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from aware_file_system.native_observation_service import (
    MAINTAINED_OBSERVATION_SCHEMA,
    MAINTAINED_OBSERVATION_SERVICE_PROTOCOL,
    RUST_OBSERVATION_SERVICE_BINARY,
    NativeObservationService,
    NativeObservationServiceError,
    ObservationWatchMode,
)

NATIVE_OBSERVATION_PACKAGE_SCHEMA = "aware.file_system.native_observation_package.v1"


def package_native_observation_service(
    *,
    artifact_root: Path,
    target_dir: Path,
    cargo_path: Path | None = None,
    manifest_path: Path | None = None,
    build_timeout_s: float = 300.0,
    verify_runtime_without_cargo: bool = True,
    source_revision: str | None = None,
    evidence_run_id: str | None = None,
) -> dict[str, Any]:
    if build_timeout_s <= 0:
        raise ValueError("build_timeout_s must be positive")
    evidence_coordinate = _evidence_coordinate(
        source_revision=source_revision,
        evidence_run_id=evidence_run_id,
    )
    cargo = _resolve_executable("cargo", cargo_path)
    rustc = _resolve_executable("rustc", None)
    manifest = (
        manifest_path.expanduser().resolve()
        if manifest_path is not None
        else _default_manifest_path()
    )
    build_root = target_dir.expanduser().resolve()
    output_root = artifact_root.expanduser().resolve()
    target_triple = _rustc_host(rustc)
    command = [
        str(cargo),
        "build",
        "--locked",
        "--release",
        "--manifest-path",
        str(manifest),
        "--bin",
        RUST_OBSERVATION_SERVICE_BINARY,
    ]
    build_env = os.environ.copy()
    build_env["CARGO_TARGET_DIR"] = str(build_root)
    started_at = datetime.now(UTC)
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        env=build_env,
        timeout=build_timeout_s,
    )
    if completed.returncode != 0:
        raise NativeObservationServiceError(
            "Locked native observation package build failed: "
            f"{completed.stderr.strip() or completed.stdout.strip()}"
        )
    built_binary = build_root / "release" / RUST_OBSERVATION_SERVICE_BINARY
    if os.name == "nt":
        built_binary = built_binary.with_suffix(".exe")
    if not built_binary.is_file():
        raise NativeObservationServiceError(
            f"Locked build did not produce observation binary: {built_binary}"
        )

    artifact_dir = output_root / target_triple
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_binary = artifact_dir / built_binary.name
    shutil.copy2(built_binary, artifact_binary)
    if os.name != "nt":
        artifact_binary.chmod(artifact_binary.stat().st_mode | 0o111)
    binary_bytes = artifact_binary.read_bytes()
    runtime_verification = (
        _verify_runtime_without_cargo(artifact_binary)
        if verify_runtime_without_cargo
        else None
    )
    receipt: dict[str, Any] = {
        "schema": NATIVE_OBSERVATION_PACKAGE_SCHEMA,
        "created_at": started_at.isoformat(),
        "target_triple": target_triple,
        "binary_name": artifact_binary.name,
        "binary_path": artifact_binary.as_posix(),
        "binary_sha256": hashlib.sha256(binary_bytes).hexdigest(),
        "binary_bytes": len(binary_bytes),
        "platform": {
            "sys_platform": sys.platform,
            "os_name": os.name,
            "machine": platform.machine(),
        },
        "service_protocol": MAINTAINED_OBSERVATION_SERVICE_PROTOCOL,
        "observation_schema": MAINTAINED_OBSERVATION_SCHEMA,
        "build": {
            "locked": True,
            "release": True,
            "cargo_version": _version_output(cargo),
            "rustc_version": _version_output(rustc),
            "command_shape": "cargo build --locked --release --bin",
        },
        "runtime_verification": runtime_verification,
        "production_route_authorized": False,
    }
    if evidence_coordinate is not None:
        receipt["evidence_coordinate"] = evidence_coordinate
    manifest_output = artifact_dir / "aware-file-system-native-observation.json"
    receipt["manifest_path"] = manifest_output.as_posix()
    manifest_output.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt


def assert_reproducible_native_packages(
    first: dict[str, Any],
    second: dict[str, Any],
) -> None:
    for coordinate in (
        "schema",
        "target_triple",
        "binary_name",
        "binary_sha256",
        "binary_bytes",
        "service_protocol",
        "observation_schema",
        "evidence_coordinate",
    ):
        if first.get(coordinate) != second.get(coordinate):
            raise NativeObservationServiceError(
                "Native observation package is not reproducible at "
                f"{coordinate}: {first.get(coordinate)!r} != "
                f"{second.get(coordinate)!r}"
            )


def _verify_runtime_without_cargo(binary_path: Path) -> dict[str, Any]:
    runtime_env = os.environ.copy()
    runtime_env["PATH"] = ""
    with TemporaryDirectory(prefix="aware-fs-packaged-runtime-") as raw_root:
        root = Path(raw_root) / "workspace"
        root.mkdir()
        (root / "source.txt").write_text("source\n", encoding="utf-8")
        with NativeObservationService(
            binary_path=binary_path,
            workspace_root=root,
            cache_path=Path(raw_root) / "state.cache",
            watch_mode=ObservationWatchMode.RECONCILIATION_ONLY,
            process_env=runtime_env,
        ) as service:
            initialized = service.initialize_observation("package-verification")
            health = service.health()["watcher"]
    return {
        "passed": initialized["status"] == "exact"
        and initialized["snapshot_entry_count"] == 1
        and health["state"] == "reconciliation_only",
        "cargo_available_on_path": shutil.which("cargo", path="") is not None,
        "watch_mode": health["state"],
        "snapshot_entry_count": initialized["snapshot_entry_count"],
    }


def _rustc_host(rustc: Path) -> str:
    completed = subprocess.run(
        [str(rustc), "-vV"],
        check=True,
        capture_output=True,
        text=True,
    )
    for line in completed.stdout.splitlines():
        if line.startswith("host: "):
            return line.removeprefix("host: ").strip()
    raise NativeObservationServiceError("rustc -vV did not report a host triple")


def _version_output(executable: Path) -> str:
    return subprocess.run(
        [str(executable), "--version"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _evidence_coordinate(
    *,
    source_revision: str | None,
    evidence_run_id: str | None,
) -> dict[str, str] | None:
    if source_revision is None and evidence_run_id is None:
        return None
    if source_revision is None or evidence_run_id is None:
        raise ValueError(
            "source_revision and evidence_run_id must be provided together"
        )
    revision = source_revision.strip().lower()
    run_id = evidence_run_id.strip()
    if len(revision) not in {40, 64} or any(
        character not in "0123456789abcdef" for character in revision
    ):
        raise ValueError("source_revision must be a 40- or 64-character hex digest")
    if not run_id or len(run_id.encode("utf-8")) > 128 or any(
        character in run_id for character in "\r\n"
    ):
        raise ValueError("evidence_run_id must contain 1..128 bytes without newlines")
    return {"source_revision": revision, "run_id": run_id}


def _resolve_executable(name: str, explicit: Path | None) -> Path:
    if explicit is not None:
        resolved = explicit.expanduser().resolve()
        if not resolved.is_file():
            raise NativeObservationServiceError(
                f"{name} executable does not exist: {resolved}"
            )
        return resolved
    discovered = shutil.which(name)
    if discovered is None:
        raise NativeObservationServiceError(f"{name} is not available on PATH")
    return Path(discovered)


def _default_manifest_path() -> Path:
    file_system_root = Path(__file__).resolve().parents[3]
    return file_system_root / "rust" / "aware_file_system_native" / "Cargo.toml"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build and verify the locked native observation artifact."
    )
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--target-dir", type=Path, required=True)
    parser.add_argument("--cargo-path", type=Path)
    parser.add_argument("--manifest-path", type=Path)
    parser.add_argument("--build-timeout-s", type=float, default=300.0)
    parser.add_argument("--skip-runtime-verification", action="store_true")
    parser.add_argument("--source-revision")
    parser.add_argument("--evidence-run-id")
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args(argv)
    receipt = package_native_observation_service(
        artifact_root=args.artifact_root,
        target_dir=args.target_dir,
        cargo_path=args.cargo_path,
        manifest_path=args.manifest_path,
        build_timeout_s=args.build_timeout_s,
        verify_runtime_without_cargo=not args.skip_runtime_verification,
        source_revision=args.source_revision,
        evidence_run_id=args.evidence_run_id,
    )
    print(json.dumps(receipt, indent=None if args.compact else 2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
