from __future__ import annotations

import json
import os
import queue
import shutil
import subprocess
import threading
import time
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, BinaryIO, Self

RUST_OBSERVATION_SERVICE_BINARY = "aware-file-system-native-observation-service"
MAINTAINED_OBSERVATION_SERVICE_PROTOCOL = (
    "aware.file_system.maintained_observation_service.v2"
)
MAINTAINED_OBSERVATION_SCHEMA = "aware.file_system.maintained_observation.v1"
MAX_OBSERVATION_RESPONSE_BYTES = 256 * 1024 * 1024


class NativeObservationServiceError(RuntimeError):
    pass


class ObservationWatchMode(StrEnum):
    NATIVE_HINTS = "native_hints"
    RECONCILIATION_ONLY = "reconciliation_only"


@dataclass(frozen=True, slots=True)
class RustObservationServiceBuildConfig:
    cargo_path: Path | None = None
    manifest_path: Path | None = None
    target_dir: Path | None = None
    release: bool = False
    timeout_s: float = 240.0


def prepare_rust_observation_service_binary(
    config: RustObservationServiceBuildConfig | None = None,
) -> Path:
    resolved = config or RustObservationServiceBuildConfig()
    cargo = (
        resolved.cargo_path.expanduser()
        if resolved.cargo_path is not None
        else _resolve_cargo()
    )
    manifest = (
        resolved.manifest_path.expanduser().resolve()
        if resolved.manifest_path is not None
        else _default_manifest_path()
    )
    target_dir = (
        resolved.target_dir.expanduser().resolve()
        if resolved.target_dir is not None
        else None
    )
    command = [
        str(cargo),
        "build",
        "--quiet",
        "--manifest-path",
        str(manifest),
        "--bin",
        RUST_OBSERVATION_SERVICE_BINARY,
    ]
    if resolved.release:
        command.append("--release")
    env = os.environ.copy()
    if target_dir is not None:
        env["CARGO_TARGET_DIR"] = str(target_dir)
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        env=env,
        timeout=resolved.timeout_s,
    )
    if completed.returncode != 0:
        raise NativeObservationServiceError(
            "Rust observation service build failed: "
            f"{completed.stderr.strip() or completed.stdout.strip()}"
        )
    profile = "release" if resolved.release else "debug"
    build_root = target_dir or manifest.parent / "target"
    binary = build_root / profile / RUST_OBSERVATION_SERVICE_BINARY
    if os.name == "nt":
        binary = binary.with_suffix(".exe")
    if not binary.is_file():
        raise NativeObservationServiceError(
            f"Rust observation service binary is missing: {binary}"
        )
    return binary.resolve()


class NativeObservationService:
    def __init__(
        self,
        *,
        binary_path: Path,
        workspace_root: Path,
        cache_path: Path,
        request_timeout_s: float = 5.0,
        reconciliation_interval_s: float = 30.0,
        watch_mode: ObservationWatchMode | str = ObservationWatchMode.NATIVE_HINTS,
        process_env: Mapping[str, str] | None = None,
    ) -> None:
        binary = binary_path.expanduser().resolve()
        root = workspace_root.expanduser().resolve()
        cache = cache_path.expanduser().resolve()
        if not binary.is_file():
            raise NativeObservationServiceError(
                f"Prepared observation service binary does not exist: {binary}"
            )
        if not root.is_dir():
            raise NativeObservationServiceError(
                f"Observation workspace root is not a directory: {root}"
            )
        if request_timeout_s <= 0:
            raise ValueError("request_timeout_s must be positive")
        if reconciliation_interval_s <= 0:
            raise ValueError("reconciliation_interval_s must be positive")
        try:
            selected_watch_mode = ObservationWatchMode(watch_mode)
        except ValueError as error:
            allowed = ", ".join(mode.value for mode in ObservationWatchMode)
            raise ValueError(f"watch_mode must be one of: {allowed}") from error
        reconciliation_interval_ms = max(1, round(reconciliation_interval_s * 1000))
        self.binary_path = binary
        self.workspace_root = root
        self.cache_path = cache
        self.request_timeout_s = request_timeout_s
        self.reconciliation_interval_s = reconciliation_interval_s
        self.watch_mode = selected_watch_mode
        self._request_lock = threading.Lock()
        self._responses: queue.Queue[Mapping[str, Any] | BaseException] = queue.Queue()
        self._process = subprocess.Popen(
            [
                str(binary),
                str(root),
                str(cache),
                str(reconciliation_interval_ms),
                selected_watch_mode.value,
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=dict(process_env) if process_env is not None else None,
        )
        self._reader_thread = threading.Thread(
            target=self._read_response_loop,
            name=f"aware-fs-observation-{self._process.pid}",
            daemon=True,
        )
        self._reader_thread.start()

    @property
    def process_id(self) -> int:
        return self._process.pid

    def ping(self) -> Mapping[str, Any]:
        response = self._request("PING")
        if response.get("protocol") != MAINTAINED_OBSERVATION_SERVICE_PROTOCOL:
            raise NativeObservationServiceError("Observation service protocol mismatch")
        if response.get("ready") is not True:
            raise NativeObservationServiceError("Observation service is not ready")
        return response

    def observe(self, request_id: str) -> Mapping[str, Any]:
        return self._observation_request("OBSERVE", request_id)

    def initialize_observation(self, request_id: str) -> Mapping[str, Any]:
        return self._observation_request("INITIALIZE", request_id)

    def poll(self, request_id: str) -> Mapping[str, Any]:
        return self._observation_request("POLL", request_id)

    def health(self) -> Mapping[str, Any]:
        response = self._request("HEALTH")
        if response.get("protocol") != MAINTAINED_OBSERVATION_SERVICE_PROTOCOL:
            raise NativeObservationServiceError("Observation health protocol mismatch")
        return response

    def wait_for_watcher_ready(
        self,
        *,
        timeout_s: float = 30.0,
        request_id: str = "watcher-ready",
    ) -> Mapping[str, Any]:
        if timeout_s <= 0:
            raise ValueError("timeout_s must be positive")
        deadline = time.monotonic() + timeout_s
        while True:
            health = self.health()
            state = str(health.get("watcher", {}).get("state"))
            if state == "active":
                report = self.poll(request_id)
                if report.get("reconciliation_cause") != "watcher_ready":
                    raise NativeObservationServiceError(
                        "Watcher became active without readiness reconciliation"
                    )
                return report
            if state == "reconciliation_only":
                report = self.poll(request_id)
                if report.get("reconciliation_cause") != "watch_unavailable":
                    raise NativeObservationServiceError(
                        "Reconciliation-only mode did not perform exact observation"
                    )
                return report
            if state == "degraded":
                raise NativeObservationServiceError(
                    f"Observation watcher is degraded: {health.get('watcher')}"
                )
            if time.monotonic() >= deadline:
                raise NativeObservationServiceError(
                    f"Observation watcher readiness timed out after {timeout_s:.3f}s"
                )
            time.sleep(0.01)

    def _observation_request(
        self,
        operation: str,
        request_id: str,
    ) -> Mapping[str, Any]:
        if not request_id or len(request_id.encode("utf-8")) > 256:
            raise ValueError("request_id must contain 1..256 UTF-8 bytes")
        if any(character in request_id for character in "\r\n"):
            raise ValueError("request_id cannot contain line breaks")
        response = self._request(f"{operation} {request_id}")
        if response.get("schema") != MAINTAINED_OBSERVATION_SCHEMA:
            raise NativeObservationServiceError("Observation result schema mismatch")
        return response

    def snapshot(self) -> Mapping[str, Any]:
        return self._request("SNAPSHOT")

    def close(self) -> None:
        if self._process.poll() is None:
            try:
                self._request("EXIT")
            except NativeObservationServiceError:
                pass
        if self._process.poll() is None:
            try:
                self._process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                self._process.terminate()
                try:
                    self._process.wait(timeout=5.0)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                    self._process.wait(timeout=5.0)
        self._reader_thread.join(timeout=1.0)
        for pipe in (self._process.stdin, self._process.stdout, self._process.stderr):
            if pipe is not None:
                pipe.close()

    def terminate_immediately(self) -> None:
        """Force-stop the native child without protocol shutdown or restart."""
        if self._process.poll() is not None:
            return
        self._process.kill()
        try:
            self._process.wait(timeout=5.0)
        except subprocess.TimeoutExpired as error:
            raise NativeObservationServiceError(
                "Observation service did not exit after forced termination"
            ) from error

    def __enter__(self) -> Self:
        self.ping()
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def _request(self, command: str) -> Mapping[str, Any]:
        with self._request_lock:
            stdin = _required_pipe(self._process.stdin, "stdin")
            if self._process.poll() is not None:
                raise NativeObservationServiceError(self._terminated_message())
            try:
                stdin.write(command.encode("utf-8") + b"\n")
                stdin.flush()
            except (BrokenPipeError, OSError) as error:
                raise NativeObservationServiceError(
                    self._terminated_message()
                ) from error
            try:
                response = self._responses.get(timeout=self.request_timeout_s)
            except queue.Empty as error:
                self._terminate_process()
                raise NativeObservationServiceError(
                    "Observation service request timed out after "
                    f"{self.request_timeout_s:.3f}s: {command.split(' ', 1)[0]}"
                ) from error
            if isinstance(response, BaseException):
                if isinstance(response, NativeObservationServiceError):
                    raise response
                raise NativeObservationServiceError(
                    f"Observation response reader failed: {response}"
                ) from response
            return response

    def _read_response_loop(self) -> None:
        stdout = self._process.stdout
        if stdout is None:
            self._responses.put(
                NativeObservationServiceError(
                    "Observation service stdout pipe is unavailable"
                )
            )
            return
        while True:
            try:
                self._responses.put(_read_response_frame(stdout))
            except BaseException as error:  # noqa: BLE001 - cross-thread totalization
                self._responses.put(error)
                return

    def _terminate_process(self) -> None:
        if self._process.poll() is not None:
            return
        self._process.terminate()
        try:
            self._process.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait(timeout=1.0)

    def _terminated_message(self) -> str:
        stderr = self._process.stderr
        detail = b""
        if stderr is not None and self._process.poll() is not None:
            detail = stderr.read()
        suffix = detail.decode("utf-8", errors="replace").strip()
        return "Observation service terminated" + (f": {suffix}" if suffix else "")


def _read_response_frame(stdout: BinaryIO) -> Mapping[str, Any]:
    header = stdout.readline(4096)
    if not header:
        raise NativeObservationServiceError("Observation response stream ended")
    try:
        raw_status, raw_length = header.rstrip(b"\r\n").split(b" ", 1)
        status = raw_status.decode("ascii")
        length = int(raw_length.decode("ascii"))
    except (UnicodeError, ValueError) as error:
        raise NativeObservationServiceError(
            f"Invalid observation response frame header: {header!r}"
        ) from error
    if length < 0 or length > MAX_OBSERVATION_RESPONSE_BYTES:
        raise NativeObservationServiceError(
            f"Observation response length is out of bounds: {length}"
        )
    payload = _read_exact(stdout, length)
    if stdout.read(1) != b"\n":
        raise NativeObservationServiceError(
            "Observation response frame is missing its terminator"
        )
    try:
        decoded = json.loads(payload)
    except json.JSONDecodeError as error:
        raise NativeObservationServiceError(
            "Observation response payload is not valid JSON"
        ) from error
    if not isinstance(decoded, Mapping):
        raise NativeObservationServiceError(
            "Observation response payload must be a JSON object"
        )
    if status == "ERR":
        raise NativeObservationServiceError(str(decoded.get("error") or decoded))
    if status != "OK":
        raise NativeObservationServiceError(
            f"Unsupported observation response status: {status!r}"
        )
    return decoded


def _read_exact(stream: BinaryIO, length: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < length:
        chunk = stream.read(length - len(chunks))
        if not chunk:
            raise NativeObservationServiceError(
                "Observation response ended before the declared frame length"
            )
        chunks.extend(chunk)
    return bytes(chunks)


def _required_pipe(pipe: BinaryIO | None, label: str) -> BinaryIO:
    if pipe is None:
        raise NativeObservationServiceError(
            f"Observation service {label} pipe is unavailable"
        )
    return pipe


def _default_manifest_path() -> Path:
    file_system_root = Path(__file__).resolve().parents[2]
    return file_system_root / "rust" / "aware_file_system_native" / "Cargo.toml"


def _resolve_cargo() -> Path:
    discovered = shutil.which("cargo")
    if discovered:
        # Keep the cargo/rustup proxy path intact. Resolving its symlink changes
        # argv[0] from `cargo` to `rustup`, which reinterprets `build` as a
        # toolchain selector instead of a Cargo subcommand.
        return Path(discovered)
    cargo = Path.home() / ".cargo" / "bin" / "cargo"
    if cargo.is_file():
        return cargo
    raise NativeObservationServiceError("cargo is not available on PATH")
