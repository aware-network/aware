from __future__ import annotations

from dataclasses import dataclass, replace
import json
import os
from pathlib import Path
import threading
from typing import Final
from uuid import UUID


@dataclass(frozen=True)
class HostedEnvironmentRecord:
    """In-memory control-plane view of an environment hosted (or managed) by a node."""

    environment_id: UUID
    environment_config_id: UUID
    environment_config_title: str | None
    environment_title: str | None
    environment_endpoint: str | None
    environment_port: int | None
    ocg_hash: str | None
    opg_hashes: tuple[str, ...]
    status: str
    bundle_manifest_path: str | None = None
    runtime_artifact_refs_json: str | None = None
    service_api_provider_refs_json: str | None = None
    environment_key: str | None = None
    outer_wrapper_kind: str = "environment"
    environment_handle: str | None = None
    workspace_root: str | None = None
    workspace_toml_path: str | None = None
    workspace_id: str | None = None
    workspace_package_id: str | None = None
    workspace_build_invocation_id: str | None = None
    workspace_build_receipt_path: str | None = None
    workspace_build_latest_path: str | None = None
    workspace_target_latest_path: str | None = None
    workspace_target_ref: str | None = None
    error: str | None = None
    process_id: UUID | None = None
    thread_id: UUID | None = None
    branch_id: UUID | None = None
    readiness_receipt: dict[str, object] | None = None
    network_node_environment_receipt: dict[str, object] | None = None
    pid: int | None = None


class HostedEnvironmentRegistry:
    """Registry for provisioned environments (control-plane).

    v0 defaults to in-memory, but can be configured to persist records to disk so
    `environment_id` (territory routing key) survives node restarts.
    """

    def __init__(self) -> None:
        self._by_id: dict[UUID, HostedEnvironmentRecord] = {}
        self._processes: dict[UUID, object] = {}
        self._persistence_path: Path | None = None
        self._lock = threading.Lock()

    def enable_persistence(self, *, path: Path, strict: bool = True) -> None:
        """Enable persistence to a JSON file.

        When `strict=True`, invalid/corrupt registry files raise and should prevent the node from starting.
        """
        with self._lock:
            self._persistence_path = path
            if not path.exists():
                return
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                version = payload.get("version")
                if version != 1:
                    raise ValueError(f"unsupported registry version: {version!r}")
                records = payload.get("records", [])
                if not isinstance(records, list):
                    raise ValueError("records must be a list")
                loaded: dict[UUID, HostedEnvironmentRecord] = {}
                for raw in records:
                    if not isinstance(raw, dict):
                        continue
                    record = self._record_from_json(raw)
                    loaded[record.environment_id] = record
                self._by_id = loaded
            except Exception:
                if strict:
                    raise
                self._by_id = {}

    def get(self, environment_id: UUID) -> HostedEnvironmentRecord | None:
        return self._by_id.get(environment_id)

    def list_records(self) -> tuple[HostedEnvironmentRecord, ...]:
        return tuple(self._by_id.values())

    def upsert(self, record: HostedEnvironmentRecord) -> HostedEnvironmentRecord:
        with self._lock:
            self._by_id[record.environment_id] = record
            self._persist_locked()
            return record

    def update(
        self, environment_id: UUID, **updates: object
    ) -> HostedEnvironmentRecord:
        with self._lock:
            existing = self._by_id.get(environment_id)
            if existing is None:
                raise KeyError(environment_id)
            record = replace(existing, **updates)
            self._by_id[environment_id] = record
            self._persist_locked()
            return record

    def set_process(self, environment_id: UUID, process: object) -> None:
        self._processes[environment_id] = process

    def get_process(self, environment_id: UUID) -> object | None:
        return self._processes.get(environment_id)

    def register(
        self,
        *,
        environment_id: UUID,
        environment_config_id: UUID,
        environment_config_title: str | None,
        environment_key: str | None = None,
        environment_title: str | None = None,
        environment_endpoint: str | None,
        environment_port: int | None,
        ocg_hash: str | None,
        opg_hashes: tuple[str, ...],
        status: str,
        bundle_manifest_path: str | None = None,
        runtime_artifact_refs_json: str | None = None,
        service_api_provider_refs_json: str | None = None,
        outer_wrapper_kind: str = "environment",
        environment_handle: str | None = None,
        workspace_root: str | None = None,
        workspace_toml_path: str | None = None,
        workspace_id: str | None = None,
        workspace_package_id: str | None = None,
        workspace_build_invocation_id: str | None = None,
        workspace_build_receipt_path: str | None = None,
        workspace_build_latest_path: str | None = None,
        workspace_target_latest_path: str | None = None,
        workspace_target_ref: str | None = None,
        error: str | None = None,
        process_id: UUID | None = None,
        thread_id: UUID | None = None,
        branch_id: UUID | None = None,
        readiness_receipt: dict[str, object] | None = None,
        network_node_environment_receipt: dict[str, object] | None = None,
        pid: int | None = None,
    ) -> HostedEnvironmentRecord:
        record = HostedEnvironmentRecord(
            environment_id=environment_id,
            environment_key=environment_key,
            environment_config_id=environment_config_id,
            environment_config_title=environment_config_title,
            environment_title=environment_title,
            bundle_manifest_path=bundle_manifest_path,
            environment_endpoint=environment_endpoint,
            environment_port=environment_port,
            ocg_hash=ocg_hash,
            opg_hashes=opg_hashes,
            status=status,
            runtime_artifact_refs_json=runtime_artifact_refs_json,
            service_api_provider_refs_json=service_api_provider_refs_json,
            outer_wrapper_kind=outer_wrapper_kind,
            environment_handle=environment_handle,
            workspace_root=workspace_root,
            workspace_toml_path=workspace_toml_path,
            workspace_id=workspace_id,
            workspace_package_id=workspace_package_id,
            workspace_build_invocation_id=workspace_build_invocation_id,
            workspace_build_receipt_path=workspace_build_receipt_path,
            workspace_build_latest_path=workspace_build_latest_path,
            workspace_target_latest_path=workspace_target_latest_path,
            workspace_target_ref=workspace_target_ref,
            error=error,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=branch_id,
            readiness_receipt=readiness_receipt,
            network_node_environment_receipt=network_node_environment_receipt,
            pid=pid,
        )
        return self.upsert(record)

    def _persist_locked(self) -> None:
        if self._persistence_path is None:
            return
        path = self._persistence_path
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "records": [self._record_to_json(r) for r in self._by_id.values()],
        }
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        with open(tmp_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
        try:
            dir_fd = os.open(str(path.parent), os.O_DIRECTORY)
        except Exception:
            return
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)

    @staticmethod
    def _record_to_json(record: HostedEnvironmentRecord) -> dict[str, object]:
        return {
            "environment_id": str(record.environment_id),
            "environment_key": record.environment_key,
            "environment_config_id": str(record.environment_config_id),
            "environment_config_title": record.environment_config_title,
            "environment_title": record.environment_title,
            "bundle_manifest_path": record.bundle_manifest_path,
            "environment_endpoint": record.environment_endpoint,
            "environment_port": record.environment_port,
            "ocg_hash": record.ocg_hash,
            "opg_hashes": list(record.opg_hashes),
            "status": record.status,
            "runtime_artifact_refs_json": record.runtime_artifact_refs_json,
            "service_api_provider_refs_json": record.service_api_provider_refs_json,
            "outer_wrapper_kind": record.outer_wrapper_kind,
            "environment_handle": record.environment_handle,
            "workspace_root": record.workspace_root,
            "workspace_toml_path": record.workspace_toml_path,
            "workspace_id": record.workspace_id,
            "workspace_package_id": record.workspace_package_id,
            "workspace_build_invocation_id": record.workspace_build_invocation_id,
            "workspace_build_receipt_path": record.workspace_build_receipt_path,
            "workspace_build_latest_path": record.workspace_build_latest_path,
            "workspace_target_latest_path": record.workspace_target_latest_path,
            "workspace_target_ref": record.workspace_target_ref,
            "error": record.error,
            "process_id": str(record.process_id) if record.process_id else None,
            "thread_id": str(record.thread_id) if record.thread_id else None,
            "branch_id": str(record.branch_id) if record.branch_id else None,
            "readiness_receipt": record.readiness_receipt,
            "network_node_environment_receipt": record.network_node_environment_receipt,
            "pid": record.pid,
        }

    @staticmethod
    def _record_from_json(raw: dict[str, object]) -> HostedEnvironmentRecord:
        def _req_str(value: object, *, field: str) -> str:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"expected non-empty string for {field}")
            return value

        def _uuid(value: object) -> UUID:
            if not isinstance(value, str) or not value.strip():
                raise ValueError("expected uuid string")
            return UUID(value)

        def _opt_uuid(value: object) -> UUID | None:
            if value is None:
                return None
            if not isinstance(value, str) or not value.strip():
                return None
            return UUID(value)

        def _opt_str(value: object) -> str | None:
            if value is None:
                return None
            if isinstance(value, str):
                return value
            return str(value)

        def _opt_dict(value: object) -> dict[str, object] | None:
            if isinstance(value, dict):
                return dict(value)
            return None

        opg_hashes_raw = raw.get("opg_hashes", [])
        opg_hashes: tuple[str, ...]
        if isinstance(opg_hashes_raw, list):
            opg_hashes = tuple(str(item) for item in opg_hashes_raw)
        else:
            opg_hashes = ()

        environment_port: int | None = None
        port_raw = raw.get("environment_port")
        if isinstance(port_raw, int):
            environment_port = port_raw
        elif isinstance(port_raw, str) and port_raw.isdigit():
            environment_port = int(port_raw)

        pid: int | None = None
        pid_raw = raw.get("pid")
        if isinstance(pid_raw, int):
            pid = pid_raw
        elif isinstance(pid_raw, str) and pid_raw.isdigit():
            pid = int(pid_raw)

        return HostedEnvironmentRecord(
            environment_id=_uuid(raw.get("environment_id")),
            environment_key=_opt_str(raw.get("environment_key")),
            environment_config_id=_uuid(raw.get("environment_config_id")),
            environment_config_title=_opt_str(raw.get("environment_config_title")),
            environment_title=_opt_str(raw.get("environment_title")),
            environment_endpoint=_opt_str(raw.get("environment_endpoint")),
            environment_port=environment_port,
            ocg_hash=_opt_str(raw.get("ocg_hash")),
            opg_hashes=opg_hashes,
            status=_req_str(raw.get("status"), field="status"),
            bundle_manifest_path=_opt_str(raw.get("bundle_manifest_path")),
            runtime_artifact_refs_json=_opt_str(raw.get("runtime_artifact_refs_json")),
            service_api_provider_refs_json=_opt_str(
                raw.get("service_api_provider_refs_json")
            ),
            outer_wrapper_kind=_opt_str(raw.get("outer_wrapper_kind")) or "environment",
            environment_handle=_opt_str(raw.get("environment_handle")),
            workspace_root=_opt_str(raw.get("workspace_root")),
            workspace_toml_path=_opt_str(raw.get("workspace_toml_path")),
            workspace_id=_opt_str(raw.get("workspace_id")),
            workspace_package_id=_opt_str(raw.get("workspace_package_id")),
            workspace_build_invocation_id=_opt_str(
                raw.get("workspace_build_invocation_id")
            ),
            workspace_build_receipt_path=_opt_str(
                raw.get("workspace_build_receipt_path")
            ),
            workspace_build_latest_path=_opt_str(
                raw.get("workspace_build_latest_path")
            ),
            workspace_target_latest_path=_opt_str(
                raw.get("workspace_target_latest_path")
            ),
            workspace_target_ref=_opt_str(raw.get("workspace_target_ref")),
            error=_opt_str(raw.get("error")),
            process_id=_opt_uuid(raw.get("process_id")),
            thread_id=_opt_uuid(raw.get("thread_id")),
            branch_id=_opt_uuid(raw.get("branch_id")),
            readiness_receipt=_opt_dict(raw.get("readiness_receipt")),
            network_node_environment_receipt=_opt_dict(
                raw.get("network_node_environment_receipt")
            ),
            pid=pid,
        )


environment_registry: Final[HostedEnvironmentRegistry] = HostedEnvironmentRegistry()
